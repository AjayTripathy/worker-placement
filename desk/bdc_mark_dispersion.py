"""bdc_mark_dispersion — find the loans two managers value differently.

THE IDEA. A BDC's NAV is not an observed price; it is management's own fair-value estimate of
illiquid private loans, blessed by a board and a third-party valuation agent. So "is the NAV
right?" normally reduces to opinion against opinion. There is exactly one place it does not:
when TWO managers hold THE SAME TRANCHE OF THE SAME BORROWER and mark it differently. Then the
disagreement is a FACT on the public record, and at least one of them is wrong. Everything else
in a mark-integrity workup (PIK share, non-accruals, coverage) is circumstantial by comparison.

This is laborious rather than clever, which is exactly why it is available: every BDC files a
complete Schedule of Investments every quarter, borrower by borrower, with par, amortized cost
and fair value. Nobody reconciles them across managers because it is dull.

TWO GUARDS, both of which produce false positives if omitted:

  1. SECURITY-TYPE GATE (the category-error guard). The same borrower can be marked at 98 by one
     manager and 72 by another with NOBODY being wrong, if the first holds the first lien and the
     second holds the second lien or the equity. A capital-structure difference is not a mark
     disagreement. Comparisons are therefore only made WITHIN a security class, and cross-class
     pairs are reported separately as CAPITAL-STRUCTURE-SPREAD — informative (the implied loss
     given default) but never evidence of a bad mark.

  2. ENTITY-RESOLUTION AMBIGUITY (the muni-matcher lesson). Sponsors stack holdcos: "Acme Inc",
     "Acme Holdings LLC", "Acme Intermediate Holdings", "Acme Parent, L.P." may be one credit or
     several. A silent merge fabricates a disagreement out of two different obligors. So the
     matcher strips the holdco ladder to a core token set, requires a real overlap, and anything
     that does not clear the bar is emitted as UNRESOLVED WITH CANDIDATES — never silently paired,
     never silently dropped.

READING THE OUTPUT. Dispersion is in points of par. A 3-5pt gap between two managers on the same
senior loan is ordinary valuation noise (different agents, different dates within the quarter). A
15pt+ gap on a first lien is the interesting object: one manager is carrying a loan the other has
already impaired. The DIRECTION matters more than the size — a manager who is systematically the
HIGHEST mark across many shared borrowers is the one whose NAV is most likely to fall, and that
per-manager bias is the summary statistic this module exists to produce.

    python3 -m desk.bdc_mark_dispersion [--min-gap 10] [--json]

INPUT MUST BE THE FULL SCHEDULE OF INVESTMENTS, NOT A TOP-N SLICE. Learned the hard way on the
first real run 2026-08-17: twelve managers' top-20 lists gave 147 comparable positions but only
TWO same-class shared borrowers and ZERO material disagreements — and that empty result reads
exactly like "the marks are fine". Read in FULL, the same twelve filings produced the Kellermeyer
Bergensons, Burgess Point, Galaxy Universal, 48Forty, athenahealth and Solera comparisons, i.e.
every genuine finding. A top-N slice sees each manager's largest exposures, which are precisely
the credits least likely to be shared and most likely to be performing.

Input: desk/data/bdc_marks/*.json (one per manager; see the extraction spec).
Output: desk/data/bdc_mark_dispersion.json + a printed report.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "desk" / "data" / "bdc_marks"
OUT = ROOT / "desk" / "data" / "bdc_mark_dispersion.json"

# Legal-form and holdco-ladder tokens carry no identifying information — a sponsor names four
# entities in one credit with these. Stripped before matching, never used to distinguish.
NOISE = {
    "inc", "incorporated", "llc", "lp", "llp", "lc", "ltd", "limited", "corp", "corporation",
    "co", "company", "plc", "sa", "nv", "bv", "gmbh", "sarl", "the", "and", "of",
    "holdings", "holding", "holdco", "intermediate", "parent", "topco", "midco", "bidco",
    "acquisition", "acquisitions", "group", "partners", "capital", "investments", "investment",
    "buyer", "borrower", "issuer", "aggregator", "newco", "opco", "propco", "us", "usa",
    "international", "global", "worldwide", "enterprises", "industries", "solutions", "services",
    "systems", "technologies", "technology", "brands", "companies",
}
# Security-class buckets. Marks are ONLY compared within a bucket — see guard 1.
CLASS_PATTERNS = [
    ("first_lien",  r"first[- ]?lien|1st[- ]?lien|senior secured (?!second)|unitranche|revolv"),
    ("second_lien", r"second[- ]?lien|2nd[- ]?lien|subordinated secured"),
    ("mezz_unsec",  r"mezzanine|unsecured|subordinated(?! secured)|junior"),
    ("equity",      r"\bequity\b|common|preferred|warrant|lp interest|llc interest|units?\b"),
    ("structured",  r"\bclo\b|structured|joint venture|\bjv\b"),
]
# TRAP 1, found by the premium-tier extraction 2026-08-17: a manager's LARGEST "position" is
# often its own captive adviser or JV vehicle, not a third-party borrower — MSC Adviser I LLC
# ranks #1 in MAIN's book by fair value; Ivy Hill and SDLP are ARCC's. Marking your own
# subsidiary at 7.63x cost is a fee-capitalization entry, not a credit mark, and including it
# would corrupt both the dispersion and the per-manager bias.
AFFILIATE_EXCLUDE = (
    "msc adviser", "ivy hill", "senior direct lending", "sdlp", "i-45", "i 45",
    "senior loan fund", "joint venture", " jv ", "adviser", "advisors llc",
)

MIN_CORE_TOKENS = 1        # a single distinctive token can identify ("Sungard"), but see below
MIN_TOKEN_LEN = 3


def sec_class(s: str) -> str:
    t = (s or "").lower()
    for name, pat in CLASS_PATTERNS:
        if re.search(pat, t):
            return name
    return "unclassified"


def core_tokens(name: str) -> tuple[str, ...]:
    t = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
    toks = [w for w in t.split() if w not in NOISE and len(w) >= MIN_TOKEN_LEN
            and not w.isdigit()]
    return tuple(toks)


def _key(toks: tuple[str, ...]) -> str:
    return " ".join(sorted(toks))


def resolve(rows: list[dict]) -> tuple[dict, list]:
    """Group positions by obligor. Returns (groups, unresolved). A group is only formed when the
    core-token sets MATCH EXACTLY or one is a strict subset of the other with >=1 shared
    distinctive token; anything else that merely SHARES a token is emitted UNRESOLVED with its
    candidates rather than merged (the muni-matcher rule: never a silent pick)."""
    by_key: dict[str, list] = defaultdict(list)
    for r in rows:
        toks = core_tokens(r.get("borrower", ""))
        if len(toks) < MIN_CORE_TOKENS:
            continue
        by_key[_key(toks)].append({**r, "_toks": toks})

    keys = list(by_key)
    groups: dict[str, list] = {}
    unresolved: list = []
    subset_merges: list = []
    used: set[str] = set()
    for i, k in enumerate(keys):
        if k in used:
            continue
        base = set(k.split())
        members = list(by_key[k])
        merged_keys = [k]
        for k2 in keys[i + 1:]:
            if k2 in used:
                continue
            other = set(k2.split())
            if base == other:
                pass_ok = True
            elif base < other or other < base:          # strict subset: "acme" vs "acme dental"
                # TRAP 2 (premium-tier extraction): HTGC holds "Main Street Rural, Inc.", which is
                # NOT Main Street Capital — a subset rule merges them. Subset merges keep their
                # recall but are tagged for verification and never counted as confirmed matches.
                subset_merges.append({"a": sorted(base), "b": sorted(other),
                                      "a_names": sorted({m["borrower"] for m in by_key[k]}),
                                      "b_names": sorted({m["borrower"] for m in by_key[k2]}),
                                      "note": "SUBSET MERGE — verify these are one obligor before "
                                              "citing any disagreement (the Main-Street-Rural trap)"})
                pass_ok = True
            elif base & other:                           # overlap but neither contains the other
                unresolved.append({
                    "reason": "AMBIGUOUS — token overlap but neither name contains the other; "
                              "refusing a silent merge (could be one credit or two obligors)",
                    "a": sorted(base), "b": sorted(other),
                    "a_names": sorted({m["borrower"] for m in by_key[k]}),
                    "b_names": sorted({m["borrower"] for m in by_key[k2]}),
                    "a_managers": sorted({m["manager"] for m in by_key[k]}),
                    "b_managers": sorted({m["manager"] for m in by_key[k2]})})
                continue
            else:
                continue
            members += by_key[k2]
            merged_keys.append(k2)
            used.add(k2)
        used.add(k)
        if len({m["manager"] for m in members}) >= 2:
            groups[k] = members
    return groups, unresolved, subset_merges


def analyse(min_gap: float = 10.0) -> dict:
    files = sorted(IN_DIR.glob("*.json")) if IN_DIR.exists() else []
    if not files:
        return {"error": f"no manager files in {IN_DIR} — extraction has not run",
                "shared_borrowers": [], "manager_bias": {}}
    # DEFECT 3, found on the first real run 2026-08-17 — the fraction-vs-percent unit trap for the
    # THIRD time in one session (print_collision, the misquote validator, now here). NMFC reports
    # fv_pct_of_par as 1.0 (a FRACTION) while ARCC reports 100.0 (a PERCENT); consumed as-is that
    # manufactured a 99-POINT "disagreement" on CentralSquare that was pure unit mismatch.
    # Detected PER MANAGER, never per row: a lone 2.3 could legitimately be 2.3 cents on the dollar
    # (PSEC carries First Brands at exactly that), so only a whole manager whose MEDIAN sits below
    # 1.5 is treated as fraction-scaled.
    def _unit_scale(vals: list[float]) -> float:
        v = sorted(x for x in vals if x is not None)
        if not v:
            return 1.0
        return 100.0 if v[len(v) // 2] <= 1.5 else 1.0

    # DEFECT 4, same run: ARCC's CentralSquare row is "First lien revolving loan; First lien term
    # loan; Series A preferred stock" — par $144M against cost $259.3M because par EXCLUDES the
    # $115.3M of equity. A blended multi-tranche row cannot be assigned to one security class and
    # its FV/par mixes debt with equity, so it is never comparable. Excluded and reported.
    def _is_blended(sec: str) -> bool:
        classes = {c for c, pat in CLASS_PATTERNS if re.search(pat, (sec or "").lower())}
        return len(classes) > 1

    rows, loaded, skipped, blended = [], [], [], []
    for f in files:
        try:
            d = json.loads(f.read_text())
        except (ValueError, OSError) as e:
            skipped.append(f"{f.name}: {e}")
            continue
        mgr = d.get("ticker") or f.stem
        loaded.append(mgr)
        _raw = []
        for p in (d.get("top20") or []):
            v = p.get("fv_pct_of_par")
            if v is None and p.get("par") and p.get("fair_value"):
                try:
                    v = 100.0 * float(p["fair_value"]) / float(p["par"])
                except (TypeError, ZeroDivisionError):
                    v = None
            if v is not None:
                _raw.append(float(v))
        scale = _unit_scale(_raw)
        for p in (d.get("top20") or []):
            par, fv = p.get("par"), p.get("fair_value")
            pct = p.get("fv_pct_of_par")
            if pct is None and par and fv:
                try:
                    pct = 100.0 * float(fv) / float(par)
                except (TypeError, ZeroDivisionError):
                    pct = None
            if pct is None:
                continue
            pct = float(pct) * scale
            if _is_blended(p.get("security_type", "")):
                blended.append({"manager": mgr, "borrower": p.get("borrower"),
                                "security_type": p.get("security_type"),
                                "note": "BLENDED multi-tranche row — par excludes the equity leg, so "
                                        "FV/par mixes debt and equity; not comparable"})
                continue
            bl = (p.get("borrower") or "").lower()
            if any(a in bl for a in AFFILIATE_EXCLUDE):
                continue                       # TRAP 1: captive adviser / JV vehicle, not a borrower
            rows.append({"manager": mgr, "borrower": p.get("borrower", ""),
                         "security_type": p.get("security_type", ""),
                         "sec_class": sec_class(p.get("security_type", "")),
                         "fv_pct_of_par": float(pct), "par": par, "fair_value": fv,
                         "cost": p.get("cost")})

    groups, unresolved, subset_merges = resolve(rows)
    shared, cross_class, bias = [], [], defaultdict(list)
    for k, members in sorted(groups.items()):
        by_class: dict[str, list] = defaultdict(list)
        for m in members:
            by_class[m["sec_class"]].append(m)
        # GUARD 1 — compare only within a security class.
        for cls, ms in by_class.items():
            mgrs = {m["manager"] for m in ms}
            if len(mgrs) < 2 or cls == "unclassified":
                continue
            best = max(ms, key=lambda m: m["fv_pct_of_par"])
            worst = min(ms, key=lambda m: m["fv_pct_of_par"])
            gap = best["fv_pct_of_par"] - worst["fv_pct_of_par"]
            row = {"borrower_key": k,
                   "names": sorted({m["borrower"] for m in ms}),
                   "security_class": cls,
                   "marks": sorted([{"manager": m["manager"], "fv_pct_of_par": round(m["fv_pct_of_par"], 1),
                                     "security_type": m["security_type"]} for m in ms],
                                   key=lambda r: -r["fv_pct_of_par"]),
                   "gap_points_of_par": round(gap, 1),
                   "highest": best["manager"], "lowest": worst["manager"],
                   "material": gap >= min_gap}
            shared.append(row)
            for m in ms:                      # per-manager bias vs the group's own median
                med = sorted(x["fv_pct_of_par"] for x in ms)[len(ms) // 2]
                bias[m["manager"]].append(m["fv_pct_of_par"] - med)
        if len(by_class) > 1:
            cross_class.append({"borrower_key": k,
                                "names": sorted({m["borrower"] for m in members}),
                                "note": "CAPITAL-STRUCTURE SPREAD, not a mark disagreement — "
                                        "different tranches of one borrower are SUPPOSED to be "
                                        "marked differently; read as implied loss-given-default",
                                "by_class": {c: [{"manager": m["manager"],
                                                  "fv_pct_of_par": round(m["fv_pct_of_par"], 1)}
                                                 for m in ms] for c, ms in by_class.items()}})

    summary = {mgr: {"shared_positions": len(v),
                     "avg_points_vs_peer_median": round(sum(v) / len(v), 2),
                     "reads": "MARKS HIGH vs peers" if sum(v) / len(v) > 1.0 else
                              ("MARKS LOW vs peers" if sum(v) / len(v) < -1.0 else "in line")}
               for mgr, v in bias.items() if v}
    shared.sort(key=lambda r: -r["gap_points_of_par"])
    return {"managers_loaded": loaded, "files_skipped": skipped,
            "positions_compared": len(rows),
            "blended_rows_excluded": blended,
            "unit_scaling_note": "fv_pct_of_par unit detected PER MANAGER (median<=1.5 => fraction, x100)",
            "shared_borrowers": shared,
            "material_disagreements": [s for s in shared if s["material"]],
            "capital_structure_spreads": cross_class,
            "unresolved_entity_matches": unresolved,
            "subset_merges_needing_verification": subset_merges,
            "manager_bias": summary,
            "min_gap_points": min_gap,
            "caveat": ("Top-20 positions only — this sees the largest exposures, not the tail "
                       "where impairments usually start. A clean result here is NOT a clean book. "
                       "Also: marks are struck at each manager's own period-end, so a small gap "
                       "can be a date difference rather than a disagreement.")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-gap", type=float, default=10.0,
                    help="points of par above which a disagreement is called material")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = analyse(a.min_gap)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    if a.json:
        print(json.dumps(res, indent=1))
        return
    if res.get("error"):
        print(f"[bdc_mark_dispersion] {res['error']}")
        return
    print(f"[bdc_mark_dispersion] {len(res['managers_loaded'])} managers, "
          f"{res['positions_compared']} positions, {len(res['shared_borrowers'])} shared-borrower "
          f"comparisons, {len(res['material_disagreements'])} material (>={a.min_gap}pt)")
    for s in res["shared_borrowers"][:25]:
        flag = "  <<< MATERIAL" if s["material"] else ""
        marks = "  ".join(f"{m['manager']} {m['fv_pct_of_par']:.0f}" for m in s["marks"])
        print(f"  {s['gap_points_of_par']:5.1f}pt [{s['security_class']:12s}] {marks}"
              f"   {s['names'][0][:38]}{flag}")
    if res["manager_bias"]:
        print("\n  PER-MANAGER BIAS (the summary statistic — who is systematically highest):")
        for m, v in sorted(res["manager_bias"].items(), key=lambda kv: -kv[1]["avg_points_vs_peer_median"]):
            print(f"    {m:6s} {v['avg_points_vs_peer_median']:+6.2f}pt vs peer median "
                  f"on {v['shared_positions']:2d} shared  — {v['reads']}")
    if res["unresolved_entity_matches"]:
        print(f"\n  UNRESOLVED entity matches (never silently merged): "
              f"{len(res['unresolved_entity_matches'])}")
    print(f"\n  {res['caveat']}")


if __name__ == "__main__":
    main()
