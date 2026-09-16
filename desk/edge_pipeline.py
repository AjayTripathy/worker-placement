"""edge_pipeline — the repeatable RISK → QUANTIFY → SKEPTIC process for classifying what a position
actually pays you for, and whether any claimed information-asymmetry is REAL.

The discipline (generator/evaluator separation applied to edge-vs-risk-premium):

  STAGE 1  ENUMERATE      (first-principles)  — decompose the thesis into every discrete risk you are
                                                being PAID TO BEAR. Exhaustive, before any quantification,
                                                so nothing is hand-waved. Independent of the quant so we
                                                don't only list risks we can conveniently size.
  STAGE 2  QUANTIFY        (SignalOS generator) — for each risk: size it from PRIMARY sources and CLASSIFY:
                                                RISK_PREMIUM (disclosed + already priced) | CANDIDATE_ASYMMETRY
                                                (a masking mechanism / a Mode-B-derived datum / a mispricing
                                                the market has NOT incorporated) | DILIGENCE_CONFIRMED
                                                (we merely verified a known fact — prevents a mistake, not edge).
  STAGE 3  SKEPTIC        (default-REJECT evaluator) — ONLY the CANDIDATE_ASYMMETRY items. An INDEPENDENT
                                                skeptic, fresh context, tries to REFUTE that it's asymmetric.
                                                Default verdict NOT_ASYMMETRY unless convinced. Only a
                                                skeptic-SURVIVED asymmetry earns the EDGE tag.

EDGE has TWO species (NOT just hidden information):
  EDGE:INFO      — a non-public datum / masking mechanism the market can't see (honesty-alpha, Mode-B).
  EDGE:PRICING   — a FULLY VISIBLE risk the market MIS-SIZES. If the priced premium >> the warranted
                   risk, you are OVERPAID to bear it = alpha even though everyone sees the risk. This is
                   why "it's a risk premium" is NOT an automatic rejection — an OVERBLOWN premium is edge.

So every risk premium must be QUANTIFIED and CONNECTED TO PRICING (Stage 2b):
  premium_priced     — what the market charges for the risk (reverse-DDM implied CoE, credit spread,
                       valuation discount, multiple gap vs a clean peer) — cite the pricing.
  premium_warranted  — what the actual risk justifies (base rates, the realized natural experiment,
                       comparable hazards, historical loss given the event).
  gap verdict:
    RP_OVERBLOWN   priced >> warranted  -> EDGE:PRICING (you're overpaid; long the mispricing)
    RP_FAIR        priced ~= warranted  -> RISK_PREMIUM (true beta, no edge)
    RP_UNDERPRICED priced << warranted  -> TRAP (you're underpaid; avoid / short)

Taxonomy that lands on the ledger (`thesis_type`):
  EDGE          — a skeptic-confirmed asymmetry, EITHER EDGE:INFO (hidden datum) OR EDGE:PRICING
                  (a quantified, overblown risk premium). Tag which species.
  RISK_PREMIUM  — the premium is FAIRLY sized vs the warranted risk (factor/beta, no edge).
  TRAP          — the premium is UNDER-sized vs the warranted risk (you're underpaid — avoid/short).
  DILIGENCE     — SignalOS's value was preventing a mistake (verified a number / killed a trap).

Run it with two agents (signalos-quant-analyst for 1+2, an independent skeptic for 3); persist the
verdict to desk/data/edge_classifications/<ticker>.json and write thesis_type back to the ledger.
This module is the single source of truth for the prompts, schemas, and the skeptic rubric.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
OUT = ROOT / "desk" / "data" / "edge_classifications"

# ---- structured contracts (also reusable as JSON Schema for a Workflow run) ----
RISK_SCHEMA = {
    "risks": [{"id": "str", "description": "what could go wrong / what you bear",
               "category": "cyclical|credit|liquidity|governance|political|execution|valuation|fx|regulatory|demand|other",
               "is_disclosed": "bool — is this in the filings / known to the Street?",
               "why_paid": "the compensation you receive for bearing it",
               "asymmetry_hypothesis": "could the market be MISPRICING this? if so, the specific reason it might be unpriced; else 'none — plain risk premium'"}]
}
QUANT_SCHEMA = {
    "assessed": [{"id": "str", "magnitude": "sized from PRIMARY sources (cite)", "primary_source": "filing/page/figure",
                  "classification": "RISK_PREMIUM | CANDIDATE_ASYMMETRY | DILIGENCE_CONFIRMED",
                  "asymmetry_claim": "if CANDIDATE: precisely WHAT the market is missing + WHY it isn't priced (the masking mechanism / the derived datum) + how it resolves to price",
                  "already_priced_check": "evidence on whether the current price already reflects it"}]
}
SKEPTIC_SCHEMA = {
    "verdicts": [{"id": "str", "verdict": "REAL_ASYMMETRY | NOT_ASYMMETRY",
                  "reasoning": "why it survives or fails the rubric",
                  "failure_mode": "if NOT: already-priced | publicly-known | verification-not-edge | arbitraged-away | risk-premium-misframed | unfalsifiable",
                  "what_would_change_mind": "the disconfirming evidence that would flip the verdict"}],
    "overall_thesis_type": "EDGE | RISK_PREMIUM | DILIGENCE",
    "surviving_asymmetries": ["ids that earned EDGE"]
}

# ---- the skeptic's default-REJECT rubric (the asymmetry tests) ----
EM_EQUITY_CHECK = """For ANY same-country EM equity whose premium is political/sovereign in nature, ALSO run the
BOND-DOMINANCE FLOOR test (desk.bond_dominance): the SENIOR sovereign hard-currency eurobond spread floors the
political premium the JUNIOR equity must offer. Compare the equity's POLITICAL-COMPONENT premium (after debiting
non-political warranted discounts) to the sovereign spread × ~2 cushion. If the equity pays LESS than the bond →
BOND_DOMINATES (pass the equity as a premium-harvest, buy the bond). This is SEPARATE from the edge test: a name
can clear the bond floor yet have no edge (TBC clears at ~530 vs ~152, but failed the alpha test). Do NOT compare
the residual alpha gap to the bond spread — that mixes a mispricing with a risk premium; compare LEVEL to LEVEL."""

SKEPTIC_RUBRIC = """You are an INDEPENDENT skeptic. Your default verdict is NOT_ASYMMETRY. A claimed
information-asymmetry only survives if it passes ALL of these — fail any one → NOT_ASYMMETRY:
  1. NON-PUBLIC / UNDERWEIGHTED: is the information genuinely not in the filings every analyst reads, or
     a structural masking mechanism the market can't easily see? If it's in sell-side notes → FAIL (publicly-known).
  2. NOT ALREADY PRICED: does the current valuation NOT yet reflect it? If the price already embeds it
     (e.g. the discount/premium is already there) → FAIL (already-priced).
  3. EDGE, NOT VERIFICATION: did SignalOS DISCOVER/DERIVE something, or merely CONFIRM a disclosed fact?
     Verifying that a cheap stock is really cheap is diligence → FAIL (verification-not-edge).
  4. DURABLE / NOT ARBITRAGED: would the edge persist, or does cheap public data close it → FAIL (arbitraged-away).
  5. NOT A RISK PREMIUM IN DISGUISE: is the expected return compensation for a real, disclosed risk
     rather than a mispricing? If you're simply paid to bear a known risk → FAIL (risk-premium-misframed).
  6. FALSIFIABLE: state what would prove it WRONG. If unfalsifiable → FAIL.
Be adversarial. Assume the generator is motivated to find edge. Demand the masking mechanism + the
resolution-to-price path. When uncertain, REJECT."""

STAGE1 = """STAGE 1 — RISK ENUMERATION (first-principles, independent of quantification).
Name: {ticker} — {name}. Thesis on the books:
---
{thesis}
---
Decompose this into EVERY discrete risk we are being PAID TO BEAR. Be exhaustive and include risks you
cannot easily quantify (do NOT omit a risk just because it's hard to size). For each, return per RISK_SCHEMA:
id, description, category, is_disclosed, why_paid, and an asymmetry_hypothesis (could the market be MISPRICING
this — and if so the SPECIFIC reason it might be unpriced — else 'none, plain risk premium'). Do not quantify
yet; just enumerate honestly. Read-only."""

STAGE2 = """STAGE 2 — QUANTIFY + CLASSIFY (SignalOS, PRIMARY sources only).
Name: {ticker} — {name}. The enumerated risks:
{risks}
For EACH risk, size it from primary sources (cite filing/page) and classify it RISK_PREMIUM /
CANDIDATE_ASYMMETRY / DILIGENCE_CONFIRMED per QUANT_SCHEMA. For any CANDIDATE_ASYMMETRY you MUST state
precisely what the market is missing, WHY it isn't priced (the masking mechanism or the Mode-B-derived
datum), the resolution-to-price path, and an already_priced_check. Be honest: most risks are RISK_PREMIUM.
A CANDIDATE_ASYMMETRY is a strong, specific claim — only raise it if you can name the mechanism. Read-only."""

STAGE3 = """STAGE 3 — SKEPTIC ADJUDICATION (independent, default-REJECT).
{rubric}

Name: {ticker} — {name}. The generator's CANDIDATE_ASYMMETRY claims to adjudicate:
{candidates}

For EACH candidate return a verdict per SKEPTIC_SCHEMA (REAL_ASYMMETRY | NOT_ASYMMETRY + failure_mode +
what_would_change_mind). Then set overall_thesis_type: EDGE only if >=1 asymmetry SURVIVES; else
RISK_PREMIUM (if the return is compensation for disclosed risk) or DILIGENCE (if SignalOS merely verified).
Verify independently against primary sources where you can. When uncertain, REJECT. Read-only."""


def _thesis(ticker: str) -> dict:
    for n in json.loads(LEDGER.read_text()).get("names", []):
        if n["ticker"] == ticker:
            return n
    raise KeyError(ticker)


def prompts_for(ticker: str) -> dict:
    """Emit the three stage prompts for a name (pulls the live thesis from the ledger)."""
    n = _thesis(ticker)
    base = {"ticker": ticker, "name": n.get("name", "")}
    return {"stage1": STAGE1.format(thesis=n.get("thesis", ""), **base),
            "stage2_template": STAGE2, "stage3_template": STAGE3, "rubric": SKEPTIC_RUBRIC, "ledger": n}


def persist(ticker: str, record: dict):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{ticker}.json").write_text(json.dumps(record, indent=1, ensure_ascii=False))


def set_thesis_type(ticker: str, thesis_type: str, paid_for: str = "", signalos_role: str = ""):
    d = json.loads(LEDGER.read_text())
    for n in d["names"]:
        if n["ticker"] == ticker:
            n["thesis_type"] = thesis_type
            if paid_for:
                n["paid_for"] = paid_for
            if signalos_role:
                n["signalos_role"] = signalos_role
    LEDGER.write_text(json.dumps(d, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    import sys
    p = prompts_for(sys.argv[1] if len(sys.argv) > 1 else "TBCG.L")
    print(p["stage1"])
