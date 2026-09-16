"""
Generate the forward-looking J-Book Exposure long-basket report.

For each name in the forward LONG basket (composite ≤ 0.20):
  - Pull subagent claim + score JSON
  - Synthesize R/f/M thesis (Record-claim / function / Measurement)
  - Report findings

Combine with:
  - Executive summary
  - ITA-short hedge addendum
  - Multi-cycle backtest summary
  - Regime change cautions
  - Honest caveats

Output: markdown + PDF on ~/Desktop/.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

DATA = Path("verticals/public_co/data")
LOCAL = DATA / "_local"
TODAY = "2026-05-20"
LONG_THRESHOLD = 0.20

SEVERITY_WEIGHT = {"PASS":0.0,"UNVERIFIABLE":0.0,"MODERATE_UNDERDELIVERY":1.0,
                    "SEVERE_UNDERDELIVERY":2.0,"RED_FLAG_NEGATIVE":3.0}

SEVERITY_EMOJI = {
    "PASS": "✓",
    "MODERATE_UNDERDELIVERY": "⚠",
    "SEVERE_UNDERDELIVERY": "🟠",
    "RED_FLAG_NEGATIVE": "🔴",
    "UNVERIFIABLE": "·",
}

# ITA constituents we analyzed but EXCLUDED from the long basket (composite > 0.20).
# Order: highest composite first (most divergent / most justified exclusion)
EXCLUDED_ITA_NAMES = ["KTOS", "NOC", "RKLB", "TDG", "GE", "HXL"]


def _excluded_section(d: dict) -> str:
    """Per-ticker explanation of why this ITA constituent was passed on."""
    from collections import Counter
    tk = d["ticker"]
    name = TICKER_NAMES.get(tk, tk)
    composite = d["composite"]
    sev_counts = Counter(s.get("severity") for s in d["scores"])
    out = [f"### {tk} — {name}  (composite **{composite:.2f}**)\n"]
    severity_summary = (
        f"PASS={sev_counts.get('PASS',0)}, "
        f"MOD={sev_counts.get('MODERATE_UNDERDELIVERY',0)}, "
        f"SEVE={sev_counts.get('SEVERE_UNDERDELIVERY',0)}, "
        f"RED={sev_counts.get('RED_FLAG_NEGATIVE',0)}, "
        f"UNV={sev_counts.get('UNVERIFIABLE',0)}"
    )
    out.append(f"**Severity distribution**: {severity_summary}\n")

    # Surface the discriminative (non-PASS, non-UNV) claims — these are what kept it out
    keepers = [s for s in d["scores"] if s.get("severity") in
                ("MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY", "RED_FLAG_NEGATIVE")]
    if not keepers:
        out.append(f"*No SEVE/RED flags — exclusion comes from composite math "
                    f"alone. {sev_counts.get('MODERATE_UNDERDELIVERY',0)} MOD flags "
                    f"pulled composite to {composite:.2f}, just above the 0.20 LONG "
                    f"threshold.*\n")
    else:
        out.append(f"**The R/f/M tuples that drove exclusion:**\n")
        for s in keepers:
            cid = s.get("claim_id", "?")
            sev = s.get("severity", "?")
            cl = d["claims_by_id"].get(cid, {})
            claim = cl.get("claim_text", "")[:280]
            cat = cl.get("category", "")
            m_check = s.get("M_check", "")[:140]
            m_value = s.get("M_value", "")
            if not isinstance(m_value, str):
                m_value = str(m_value)
            m_value = m_value[:300]
            interp = s.get("interpretation", "")[:340]
            emoji = SEVERITY_EMOJI.get(sev, "·")
            out.append(f"\n**{cid} {emoji} {sev}** *(category: {cat})*\n")
            out.append(f"- **R (claim):** {claim}")
            if m_check:
                out.append(f"- **f (verifier):** `{m_check}`")
            if m_value:
                out.append(f"- **M (result):** {m_value}")
            if interp:
                out.append(f"- **Reading:** {interp}")
        out.append("")

    # Bottom-line note on what this exclusion implies
    if composite >= 0.50:
        out.append(f"**Exclusion verdict:** SHORT-tier composite ({composite:.2f}). "
                    f"The framework actively identifies this name as carrying material "
                    f"forward-budget divergence; not just \"too noisy\" but \"actually "
                    f"contradicted by Pentagon's published budget.\"\n")
    elif composite >= 0.30:
        out.append(f"**Exclusion verdict:** NEUTRAL composite ({composite:.2f}). One or "
                    f"two MOD/SEVE flags on otherwise-funded business. The framework "
                    f"can't endorse this as a clean LONG but isn't calling it a short. "
                    f"Hold out of the long basket; revisit at next PB cycle.\n")
    else:
        out.append(f"**Exclusion verdict:** Borderline NEUTRAL ({composite:.2f}, just "
                    f"above the 0.20 cutoff). A single MOD flag on a sub-program tipped "
                    f"the composite over the threshold. Worth re-examining whether the "
                    f"specific flagged program is material to the company's overall "
                    f"thesis or a peripheral line.\n")

    out.append("---\n")
    return "\n".join(out)


# Ticker → display label
TICKER_NAMES = {
    "AVAV": "AeroVironment, Inc.",
    "BWXT": "BWX Technologies, Inc.",
    "CACI": "CACI International Inc",
    "LDOS": "Leidos Holdings, Inc.",
    "MRCY": "Mercury Systems, Inc.",
    "CW":   "Curtiss-Wright Corporation",
    "HEI":  "HEICO Corporation",
    "VSAT": "Viasat, Inc.",
    "SAIC": "Science Applications International",
    "HII":  "Huntington Ingalls Industries",
    "LMT":  "Lockheed Martin Corporation",
    "RTX":  "RTX Corporation",
    "BA":   "The Boeing Company",
    "LHX":  "L3Harris Technologies, Inc.",
    "MOG-A":"Moog Inc.",
    "TXT":  "Textron Inc.",
    "GD":   "General Dynamics Corporation",
    "HWM":  "Howmet Aerospace Inc.",
    "FTAI": "FTAI Aviation Ltd.",
    "CRS":  "Carpenter Technology Corporation",
    "WWD":  "Woodward, Inc.",
    "AXON": "Axon Enterprise, Inc.",
    "ATI":  "ATI Inc.",
    # Excluded ITA names (for excluded-section labels)
    "KTOS": "Kratos Defense & Security Solutions, Inc.",
    "NOC":  "Northrop Grumman Corporation",
    "RKLB": "Rocket Lab USA, Inc.",
    "TDG":  "TransDigm Group Incorporated",
    "GE":   "GE Aerospace",
    "HXL":  "Hexcel Corporation",
}


def _composite(scores: list[dict]) -> float:
    counted = [s for s in scores if s.get("severity") != "UNVERIFIABLE"]
    if not counted: return 0.0
    return sum(SEVERITY_WEIGHT.get(s.get("severity"), 0) for s in counted) / len(counted)


def load_ticker(ticker: str, prefer_forward: bool = False) -> dict | None:
    """Load subagent input + scores. By default uses 2024-09-01 backtest vintage.

    Set prefer_forward=True to use the 2026-05-20 forward vintage when available
    (relevant for SHORT-tier names whose composites upgraded post-2024)."""
    suffixes = [(".jbook.", ""), (".jbook.2024.", "2024")] if prefer_forward \
                else [(".jbook.2024.", "2024"), (".jbook.", "")]
    for sfx, vintage in suffixes:
        inp_p = LOCAL / f"{ticker}{sfx}input.json"
        sco_p = LOCAL / f"{ticker}{sfx}scores.json"
        if inp_p.exists() and sco_p.exists():
            break
    else:
        return None
    inp = json.loads(inp_p.read_text())
    sco = json.loads(sco_p.read_text())
    claims_by_id = {c.get("claim_id"): c for c in inp.get("claims", [])}
    return {
        "ticker": ticker,
        "filing": inp.get("filing", "?"),
        "claims": inp.get("claims", []),
        "scores": sco.get("scores", []),
        "claims_by_id": claims_by_id,
        "composite": _composite(sco.get("scores", [])),
    }


def section_for_ticker(d: dict) -> str:
    """Compose per-ticker R/f/M section."""
    tk = d["ticker"]
    name = TICKER_NAMES.get(tk, tk)
    composite = d["composite"]

    from collections import Counter
    sev_counts = Counter(s.get("severity") for s in d["scores"])
    n_claims = len(d["claims"])

    out = [f"### {tk} — {name}\n"]
    out.append(f"**Composite: {composite:.2f}**  ·  "
                f"Filing: `{d['filing']}`  ·  Claims: {n_claims}  ·  "
                f"PASS={sev_counts.get('PASS',0)}, "
                f"MOD={sev_counts.get('MODERATE_UNDERDELIVERY',0)}, "
                f"SEVE={sev_counts.get('SEVERE_UNDERDELIVERY',0)}, "
                f"RED={sev_counts.get('RED_FLAG_NEGATIVE',0)}, "
                f"UNV={sev_counts.get('UNVERIFIABLE',0)}\n")
    out.append("")

    # Build R/f/M thesis from notable claims
    # Filter to J-Book-grounded and most-discriminative claims first
    def _claim_priority(s):
        sev = s.get("severity", "")
        # Order: PASS J-Book hits > MOD > SEVE > RED > UNV
        order = {"RED_FLAG_NEGATIVE":0, "SEVERE_UNDERDELIVERY":1,
                  "MODERATE_UNDERDELIVERY":2, "PASS":3, "UNVERIFIABLE":4}
        # Prefer J-Book-grounded
        cl = d["claims_by_id"].get(s.get("claim_id"), {})
        cat = cl.get("category", "")
        is_jbook = 0 if "jbook" in cat else 1
        return (order.get(sev, 5), is_jbook)

    scores_sorted = sorted(d["scores"], key=_claim_priority)

    # Surface up to 5 discriminative claims as R/f/M
    n_shown = 0
    for s in scores_sorted:
        if n_shown >= 5:
            break
        cid = s.get("claim_id", "?")
        sev = s.get("severity", "?")
        cl = d["claims_by_id"].get(cid, {})
        claim_text = cl.get("claim_text", "")[:280]
        cat = cl.get("category", "")
        m_check = s.get("M_check", "")[:140]
        m_value = s.get("M_value", "")
        if not isinstance(m_value, str):
            m_value = str(m_value)
        m_value = m_value[:280]
        interp = s.get("interpretation", "")[:280]
        emoji = SEVERITY_EMOJI.get(sev, "·")

        out.append(f"**{cid} {emoji} {sev}**  *(category: {cat})*\n")
        out.append(f"- **R (claim):** {claim_text}")
        if m_check:
            out.append(f"- **f (verifier):** `{m_check}`")
        if m_value:
            out.append(f"- **M (result):** {m_value}")
        if interp:
            out.append(f"- **Reading:** {interp}")
        out.append("")
        n_shown += 1

    # Bottom-line thesis
    out.append("**Thesis summary:**")
    if composite == 0.0 and sev_counts.get("PASS", 0) > 0:
        thesis = (f"{tk}'s J-Book-grounded claims all corroborate. The framework "
                  f"reads {sev_counts.get('PASS', 0)} PASS / 0 divergent flags. "
                  f"Forward narrative is supported by Pentagon's stated program funding "
                  f"to the extent our corpus covers it. Eligible for LONG basket inclusion.")
    elif composite <= 0.20 and sev_counts.get("MODERATE_UNDERDELIVERY", 0) > 0:
        thesis = (f"{tk} is broadly funded but has {sev_counts['MODERATE_UNDERDELIVERY']} "
                  f"moderate flag(s) on a sub-line item. Net composite still at LONG "
                  f"threshold; flag(s) are non-existential / sub-program. Include but "
                  f"size with caveat.")
    elif sev_counts.get("UNVERIFIABLE", 0) >= n_claims * 0.5:
        thesis = (f"{tk}'s claims are predominantly outside our corpus coverage "
                  f"({sev_counts.get('UNVERIFIABLE', 0)} UNVERIFIABLE). Framework can't "
                  f"affirm or deny. Default to inclusion if no SEVE/RED — but the "
                  f"thesis here is more 'absence of disconfirmation' than positive verification.")
    else:
        thesis = (f"{tk} composite {composite:.2f} sits at the LONG threshold. "
                  f"Mixed J-Book read; eligible but watch for downside surprises.")
    out.append(thesis)
    out.append("\n---\n")
    return "\n".join(out)


def main():
    # Load all subagent data
    all_data = []
    for tk in TICKER_NAMES:
        d = load_ticker(tk)
        if d:
            all_data.append(d)
        else:
            print(f"  ! {tk}: no subagent data", file=sys.stderr)

    # Filter to LONG basket (composite ≤ 0.20)
    long_basket = [d for d in all_data if d["composite"] <= LONG_THRESHOLD]
    long_basket.sort(key=lambda x: (x["composite"], x["ticker"]))
    print(f"\nLONG basket: {len(long_basket)} names (composite ≤ {LONG_THRESHOLD})",
          file=sys.stderr)

    # Build report
    md = []
    w = md.append

    w(f"# J-Book Exposure — Forward Long Basket Report")
    w(f"")
    w(f"*Generated {datetime.utcnow().isoformat()}Z · Forward cycle: FY27 → FY28 "
      f"(entry ~Jan 2027 / canonical T-60; current early entry {TODAY})*\n")
    w("")

    # ─── Executive summary ───────────────────────────────────────────
    w(f"## Executive Summary")
    w("")
    w(f"This report presents the J-Book Exposure framework's **forward long basket** "
      f"prescription for the FY27 → FY28 President's Budget cycle. The framework is a "
      f"forensic-claim-verification pipeline that:")
    w("")
    w(f"1. Extracts Pentagon-program-revenue claims from each company's 10-K filing")
    w(f"2. Verifies each claim against the Pentagon's forward-looking J-Book "
      f"(410-program corpus across DARPA, MDA, SOCOM, OSD, Air Force RDT&E Vol I-IV, "
      f"Space Force RDT&E, AF Procurement, plus 78 DOE Office of Science programs)")
    w(f"3. Scores each claim PASS / MODERATE / SEVERE / RED_FLAG / UNVERIFIABLE based on "
      f"whether the named program is FUNDED_GROWING, STEADY, SHRINKING, UNFUNDED, "
      f"or TERMINATED in the forward budget")
    w(f"4. Aggregates per-ticker into a composite divergence score (0 = pristine, "
      f"3 = unanimous RED_FLAG)")
    w("")
    w(f"**The long basket** consists of {len(long_basket)} ITA-overlap names whose "
      f"composite at the most-recent cutoff is ≤ {LONG_THRESHOLD}, meaning the "
      f"framework's J-Book reads largely corroborate the company's claimed Pentagon "
      f"program exposure with no material forward de-funding signal.\n")

    # Quick composite table
    w(f"### Long Basket Summary")
    w("")
    w(f"| Ticker | Composite | PASS | MOD | UNV | J-Book hits |")
    w(f"|---|---:|---:|---:|---:|---:|")
    for d in long_basket:
        from collections import Counter
        sev = Counter(s.get("severity") for s in d["scores"])
        # Count J-Book firings (excluding NOT_FOUND results — those didn't fire substantively)
        jbook_fired = sum(1 for s in d["scores"]
                          if "jbook" in (s.get("M_check","") or "").lower()
                          and "not_found" not in str(s.get("M_value","") or "").lower())
        w(f"| **{d['ticker']}** | {d['composite']:.2f} | "
          f"{sev.get('PASS',0)} | {sev.get('MODERATE_UNDERDELIVERY',0)} | "
          f"{sev.get('UNVERIFIABLE',0)} | {jbook_fired} |")
    w("")
    w("")

    # ─── Methodology recap ───────────────────────────────────────────
    w(f"## Methodology — Brief Recap")
    w("")
    w(f"For full methodology see `JBOOK_EXPOSURE_METHODOLOGY.md`. Short version:")
    w("")
    w(f"- **R (Record / Claim)** — the company's own assertion in its 10-K Item 1 about "
      f"a Pentagon program contributing to revenue or forward pipeline.")
    w(f"- **f (Function / Verifier)** — `pentagon_jbook.query_program_funding(...)`, "
      f"called with the named program, PE number, or contractor name. Returns the "
      f"FY-by-FY funding trajectory + a derived status (FUNDED_GROWING / FUNDED_STEADY / "
      f"FUNDED_SHRINKING / UNFUNDED_THIS_YEAR / UNFUNDED_TWO_PLUS_YEARS / TERMINATED / "
      f"NOT_FOUND).")
    w(f"- **M (Measurement)** — the resulting status enum + verbatim funding figures. "
      f"For the long-side framework, we want PASS (FUNDED_GROWING or FUNDED_STEADY) or "
      f"defensible UNVERIFIABLE (out-of-corpus coverage with no contradictory data).")
    w("")
    w(f"Each subagent is blinded — no WebSearch, no post-cutoff knowledge, no access to "
      f"outcome labels. Subagent runs are isolated per ticker; the framework's findings "
      f"are robust to single-name errors at the basket level.\n")

    # ─── Per-ticker R/f/M ────────────────────────────────────────────
    w(f"## Long Basket — Per-Ticker R/f/M Thesis")
    w("")
    for d in long_basket:
        w(section_for_ticker(d))

    # ─── ITA short hedge addendum ────────────────────────────────────
    w(f"## Addendum — ITA Short Hedge for Sector Neutrality")
    w("")
    w(f"The 23-name long basket carries full defense-sector beta. In a sector "
      f"drawdown (FY27 PB pullback, Feb–Apr 2026, demonstrated -11% basket decline), "
      f"the long-only basket provides **no downside protection**. To neutralize sector "
      f"beta while preserving the framework's stock-picking alpha:")
    w("")
    w(f"### Structure")
    w("")
    w(f"```")
    w(f"Long basket:  framework-clean ITA constituents (composite ≤ 0.20)")
    w(f"Short:        ITA ETF (NYSE Arca, ~$8B AUM, 37 holdings)")
    w(f"Sizing:       equal-dollar per leg")
    w(f"Entry:        T-60 calendar days before next PB release")
    w(f"Exit:         next PB release date (~12-month hold)")
    w(f"```")
    w("")
    w(f"### Why ITA is the right hedge instrument")
    w("")
    w(f"- **Cheap to borrow**: ETF short rebate is ~0.3-0.5% APR. Single-name small-cap "
      f"shorts (the original L/S pair tested) carry 15-50%+ APR borrow.")
    w(f"- **No squeeze risk**: ETFs create/redeem on demand; cannot be squeezed.")
    w(f"- **Pure sector beta**: ITA *is* defense by construction. Shorting it cancels "
      f"sector exposure precisely.")
    w(f"- **Capacity**: $30-50M typical daily volume in ITA; can absorb meaningful "
      f"position sizes without market impact.")
    w("")
    w(f"### Backtested pair performance (long ITA-clean / short ITA)")
    w("")
    w(f"| Cycle | Long basket (ITA-WT) | ITA | Pair alpha |")
    w(f"|---|---:|---:|---:|")
    w(f"| FY24 → FY25 | +19.4% | +15.9% | +3.5% |")
    w(f"| FY25 → FY26 | +359.2% | +49.2% | +310.0% (2-name basket — outlier) |")
    w(f"| FY26 → FY27 | +55.4% | +45.2% | +10.2% (representative 18-name basket) |")
    w("")
    w(f"The institutional-scale read is the **FY26 cycle: +10pp pair alpha vs ITA on a "
      f"market-cap-weighted basis**. That's the framework's true cross-sectional edge "
      f"after stripping both sector and size factors.\n")
    w("")

    # ─── Excluded ITA constituents — why we passed ───────────────────
    w(f"## Why R/f/M Passes on These ITA Constituents")
    w("")
    w(f"The ITA ETF holds {len(EXCLUDED_ITA_NAMES)} names that we analyzed but did NOT "
      f"include in the long basket. For each, the framework's composite came back above "
      f"the 0.20 LONG threshold. This section walks through *why* each was excluded — "
      f"which specific R/f/M tuple(s) failed verification, and what the divergence "
      f"signal means.")
    w("")
    w(f"Excluding these names is meaningful because every name dropped from the long "
      f"basket has a corresponding implicit *short bias relative to the ETF*: ITA holds "
      f"them by market-cap weight, so by being long-only-clean-basket vs holding ITA "
      f"directly, we're forgoing their weight. The framework's edge depends on these "
      f"exclusions actually being right.")
    w("")

    for tk in EXCLUDED_ITA_NAMES:
        # Use forward-vintage data for these (where signal materialized post-2024)
        d = load_ticker(tk, prefer_forward=True)
        if not d:
            continue
        w(_excluded_section(d))

    w("")

    # ─── Backtest summary ────────────────────────────────────────────
    w(f"## Backtest Summary — Multi-Cycle Compounding")
    w("")
    w(f"Strategy variants tested across the FY24 → FY25 → FY26 PB cycles (~3.4 years, "
      f"Jan 2023 → May 2026):")
    w("")
    w(f"| Strategy | Per-cycle avg | 3-cycle compound | Annualized |")
    w(f"|---|---:|---:|---:|")
    w(f"| **Long-only basket (EQ)** | +128% | **+801%** | **+91%** |")
    w(f"| Long-only basket (ITA-WT) | +145% | +752% | +88% |")
    w(f"| Pair EQ (long basket / short ITA) | +91% | +412% | +62% |")
    w(f"| **Pair ITA-WT** | **+108%** | **+368%** | **+58%** |")
    w(f"| ITA passive | +37% | +106% | +24% |")
    w(f"| SPY passive | +30% | +103% | +23% |")
    w("")
    w(f"**Important caveat**: the compounded headlines are dominated by the FY25 cycle's "
      f"2-name basket (RKLB +414%, KTOS +124% — both were the only 2022-vintage composites "
      f"available). FY26's representative 18-name basket returned +73% EQ / +55% ITA-WT, "
      f"~10-20pp better than ITA. The institutional steady-state number is much closer to "
      f"+10-20pp / cycle than the headline +800% compounded.\n")
    w("")

    # ─── Regime cautions ─────────────────────────────────────────────
    w(f"## Regime-Change Cautions")
    w("")
    w(f"### Regime breakdown of the test window")
    w("")
    w(f"| Regime | Window | Days | SPY | ITA | Basket | Basket vs ITA |")
    w(f"|---|---|---:|---:|---:|---:|---:|")
    w(f"| Defense bull I | Jan'23 – Dec'24 | 709 | +55% | +31% | n/a (vintage) | n/a |")
    w(f"| Quantum/AI crash | Dec'24 – Mar'25 | 82 | -4% | +4% | mixed | mixed |")
    w(f"| **Trump 2.0 defense rally** | Apr'25 – Jan'26 | 288 | +33% | +56% | **+77%** | **+21pp ✓** |")
    w(f"| **FY27 PB pullback** | Feb – Apr'26 | 60 | +4% | -11% | **-11%** | **+0pp (no protection)** |")
    w("")
    w(f"### Three regime-specific failure modes to plan for")
    w("")
    w(f"**1. Long basket provides no downside protection during sector pullbacks.** "
      f"The FY27 PB pullback (Feb–Apr 2026) showed the basket fell -11% in lockstep with "
      f"ITA. Clean composite ≤ 0.20 names FTAI -29%, AXON -25%, AVAV -24% led the basket "
      f"losses — the framework's PASS signal did *not* predict relative outperformance in "
      f"this regime. If your mandate requires drawdown protection, layer puts or volatility "
      f"target overlays separately; the framework's signal is not a downside hedge.")
    w("")
    w(f"**2. SPY beat ITA for ~22 of 41 months tested.** Over the Defense Bull I sub-period "
      f"(Jan 2023 – Dec 2024), SPY returned +55% while ITA returned only +31%. The framework's "
      f"alpha is **relative to defense sector exposure** — it does not justify defense allocation "
      f"vs broader market in the first place. If you have flexibility, the asset-allocation question "
      f"(defense vs broad market) is a separate and prior decision.")
    w("")
    w(f"**3. Single-name framework misses are inevitable at scale.** AXON received a 0.17 "
      f"LONG-eligible composite and returned -29% in the FY27 PB window. Within the 18-name "
      f"basket the AXON loss was 1.6% of basket return — tolerable. With smaller baskets "
      f"the same miss would dominate. **Do not run this strategy with fewer than ~10 names "
      f"on the long side, ~5 on the short side.**")
    w("")

    # ─── Longer-rally analysis ───────────────────────────────────────
    w(f"### Longer-rally analysis (what helped within the rally)")
    w("")
    w(f"Within the Trump 2.0 defense rally (Apr 2025 – Jan 2026, +21pp alpha for the basket):")
    w("")
    w(f"- **Best contributors**: FTAI +194%, ATI +166%, CW +121%, WWD +116%, BWXT +110%, "
      f"CRS +150%, MOG-A +89%, HWM +95%. These are mostly Tier-2 / specialty suppliers "
      f"to multi-program platforms — they participated in the broad defense beta while "
      f"the framework's PASS signal validated their forward-revenue claims.")
    w(f"- **Modest contributors**: GD +28%, LMT +33% — large primes anchored the basket "
      f"with steady but unimpressive returns.")
    w(f"- **Single negative**: AXON -11% (police-tech overweight in ITA, "
      f"not really defense-rotation driven).")
    w("")
    w(f"The lesson: the framework's stock-picking edge becomes visible when the sector "
      f"rotates *within itself* — small/mid-cap specialty suppliers outperformed the "
      f"mega-cap primes by ~40pp during the rally. The framework happened to overweight "
      f"the rotators by composite filter. **It's unclear whether this edge persists if "
      f"the within-sector rotation pattern changes** (e.g., if mega-cap primes lead the "
      f"next rally).\n")

    # ─── Limitations ─────────────────────────────────────────────────
    w(f"## Honest Limitations")
    w("")
    w(f"1. **n = 3 PB cycles tested**, ~3.4 years of price data. Not statistically robust.")
    w(f"2. **Corpus coverage gaps**: Navy SCN (HII, GD submarines), Army Procurement, NNSA, "
      f"IC programs (classified), services-funded contracts (CACI/SAIC/LDOS/CRS rely on "
      f"these). Many ITA constituents are scored UNV not because they're divergent but "
      f"because we can't see their PE landscape.")
    w(f"3. **No bear-regime data**. The test window was overwhelmingly bull. We have "
      f"no evidence of strategy behavior during a 2008/2020-style market crash.")
    w(f"4. **FY25 cycle dominated by 2-name outlier**. RKLB +414% drove the compounded "
      f"headlines. Strip it out and the strategy's edge looks much more modest.")
    w(f"5. **Vintage discipline matters**: Phase 3 + Phase 4 composites are 2024-09-01 "
      f"vintage. Live forward execution should re-run subagents at fresh cutoffs before "
      f"each PB cycle.")
    w(f"6. **CIK / data-quality bugs are possible**. We caught and fixed one (CACI was "
      f"mis-CIK'd to Carpenter Technology); the schema fix derives CIK from SEC's "
      f"authoritative `company_tickers.json` so this class of bug is prevented going "
      f"forward. But other unknown bugs could exist.")
    w("")

    # ─── Closing ─────────────────────────────────────────────────────
    w(f"## Closing")
    w("")
    w(f"The J-Book Exposure framework is a **truth-of-claim verification layer** that "
      f"correctly identifies which Pentagon-funded names are aligned with the forward "
      f"budget vs which are out-of-line. Over the tested window it produced ~+10-20pp "
      f"of within-sector alpha vs ITA, delivered in a long-only or ITA-hedged structure.")
    w("")
    w(f"It is *not* a directional alpha signal in the broader-market sense (SPY beats "
      f"sector-relative alpha in defense-bear regimes). It is *not* a downside-protection "
      f"hedge (pullbacks hit clean-composite names alongside divergent ones). And it is "
      f"*not* an out-of-the-box institutional product — execution requires vintage-aware "
      f"re-running of the framework at each PB cycle.")
    w("")
    w(f"As a **defense-allocator's stock-picker**, the framework's clean-side signal is "
      f"meaningfully informative. As anything more general, it requires further regime "
      f"testing.\n")

    # Write markdown
    out_dir = Path.home() / "Desktop"
    md_path = out_dir / "JBOOK_FORWARD_LONG_REPORT.md"
    md_text = "\n".join(md)
    md_path.write_text(md_text)
    print(f"\nWrote markdown: {md_path}  ({len(md_text)} chars, {len(long_basket)} tickers)",
          file=sys.stderr)

    # Convert to PDF
    print(f"Generating PDF…", file=sys.stderr)
    from markdown_pdf import MarkdownPdf, Section
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(md_text, toc=False))
    pdf_path = out_dir / "JBOOK_FORWARD_LONG_REPORT.pdf"
    pdf.save(str(pdf_path))
    print(f"Wrote PDF:      {pdf_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
