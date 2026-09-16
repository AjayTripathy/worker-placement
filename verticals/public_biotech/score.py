"""Stage 4 (biotech): unblind, score discrimination, render the analyst report.

This is the ONLY module permitted to open _sealed_outcomes.json, and it does so
AFTER predictions are committed to disk (data/<ticker>/prediction.json). Running
it does not change any prediction — it only reveals ground truth and scores the
blind call already made.

Two outputs:
  1. A discrimination scorecard: did the framework's EXCLUSION call separate the
     MISS from the HIT? (The thesis is exclusion, so the test is: MISS flagged,
     HIT left clean — not point-accuracy on one name.)
  2. An analyst-facing report in R / f(M) / Finding form: every material finding
     states the marketing claim (R), the verification method (f), the
     authoritative source consulted as-of cutoff (M), and the adjudicated Finding.
     No framework jargon — the reader is an institutional analyst.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .catalyst_spec import CASES, CatalystCase, SEALED_OUTCOMES, DATA_DIR

# Map the blind directional call to a predicted catalyst label.
_CALL_TO_PRED = {
    "MISS_CANDIDATE (EXCLUDE)": "MISS",
    "ELEVATED_RISK": "MISS",
    "CLEAN (HIT-consistent)": "HIT",
}


def _load_prediction(case: CatalystCase) -> dict:
    p = DATA_DIR / case.case_id / "prediction.json"
    if not p.exists():
        raise FileNotFoundError(f"no prediction for {case.ticker}; run evaluate first")
    return json.loads(p.read_text())


def _load_sealed() -> dict:
    return json.loads(SEALED_OUTCOMES.read_text())["outcomes"]


def score(case_ids: list[str]) -> dict:
    sealed = _load_sealed()
    rows = []
    for cid in case_ids:
        case = CASES[cid]
        pred = _load_prediction(case)
        call = pred["summary"]["call"]
        predicted = _CALL_TO_PRED.get(call, "ABSTAIN")
        actual = sealed[cid]["label"]
        rows.append({
            "case_id": cid, "ticker": case.ticker, "call": call,
            "predicted": predicted, "actual": actual,
            "correct": predicted == actual,
            "honesty_gap": pred["summary"]["honesty_gap_normalized"],
            "decisive": len(pred["summary"]["decisive_refutes_high_precision"]),
            "price_reaction_pct": sealed[cid].get("price_reaction_pct"),
        })
    miss = [r for r in rows if r["actual"] == "MISS"]
    hit = [r for r in rows if r["actual"] == "HIT"]
    discriminates = (all(r["predicted"] == "MISS" for r in miss) and
                     all(r["predicted"] == "HIT" for r in hit) and miss and hit)
    gap_sep = None
    if miss and hit:
        gap_sep = round(min(r["honesty_gap"] for r in miss) -
                        max(r["honesty_gap"] for r in hit), 3)
    return {"rows": rows, "discriminates": discriminates, "gap_separation": gap_sep}


def score_adjudicated(case_ids: list[str]) -> dict:
    """Score the REASONED call (adjudication.json) against sealed outcomes, and
    contrast it with the deterministic gate call. Same exclusion test: did the
    reasoned EXCLUDE/ELEVATED concentrate the MISSes while leaving HITs CLEAN?"""
    sealed = _load_sealed()
    rows = []
    for cid in case_ids:
        case = CASES[cid]
        a = DATA_DIR / cid / "adjudication.json"
        if not a.exists():
            continue
        adj = json.loads(a.read_text())
        actual = sealed[cid]["label"]
        rows.append({
            "case_id": cid, "ticker": case.ticker,
            "reasoned_call": adj["call"], "gate_call": adj.get("gate_call"),
            "predicted": adj["predicted"], "actual": actual,
            "correct": adj["predicted"] == actual,
            "n_drivers": len(adj.get("drivers", [])),
            "price_reaction_pct": sealed[cid].get("price_reaction_pct"),
            "analyst_note": adj.get("analyst_note", ""),
        })
    miss = [r for r in rows if r["actual"] == "MISS"]
    hit = [r for r in rows if r["actual"] == "HIT"]
    flagged = [r for r in rows if r["predicted"] == "MISS"]
    tp = sum(1 for r in flagged if r["actual"] == "MISS")
    fp = sum(1 for r in flagged if r["actual"] == "HIT")
    cm = {
        "n": len(rows), "n_hit": len(hit), "n_miss": len(miss),
        "flagged": len(flagged), "flagged_tp_miss": tp, "flagged_fp_hit": fp,
        "miss_recall": round(tp / len(miss), 3) if miss else None,
        "hit_specificity": round(
            sum(1 for r in hit if r["predicted"] == "HIT") / len(hit), 3) if hit else None,
        "flagged_precision": round(tp / len(flagged), 3) if flagged else None,
        "base_rate_miss": round(len(miss) / len(rows), 3) if rows else None,
        "discriminates": bool(miss and hit
                              and all(r["predicted"] == "MISS" for r in miss)
                              and all(r["predicted"] == "HIT" for r in hit)),
    }
    return {"rows": rows, "confusion": cm}


# ── Analyst report (R / f(M) / Finding) ──────────────────────────────────────

def _fmt_finding(f: dict, status: str = "") -> str:
    sev = f["severity"].upper()
    tag = f"  [{f['channel']}]" + (f"  {status}" if status else "")
    return (
        f"{tag}\n"
        f"  R (claim):   \"{f['R_source_quote'][:240]}\"\n"
        f"               — {Path(f['R_source_doc']).name}\n"
        f"  f (method):  {f['f_method']}\n"
        f"  M (source):  {f['m_source']}\n"
        f"  Finding:     {f['verdict']} ({sev}) — {f.get('rationale','')}\n"
    )


# Reading order for the all-findings dump: decisive first, then demoted/severe
# refutes, then remaining refutes, then affirmed, then unverifiable.
_VERDICT_ORDER = {"REFUTED": 0, "AFFIRMED": 1, "UNVERIFIABLE": 2}


def _finding_status(f: dict, decisive_keys: set, demoted_map: dict) -> tuple[int, str]:
    """Return (sort_rank, human status label) for a finding given the aggregation."""
    key = (f["claim_id"], f["rule_id"])
    if key in decisive_keys:
        return (0, "*** DECISIVE — basis for EXCLUSION ***")
    if key in demoted_map:
        return (1, f"SEVERE (demoted from decisive: {demoted_map[key]})")
    if f["verdict"] == "REFUTED" and f["severity"].upper() in ("SEVERE", "CRITICAL"):
        return (2, "SEVERE refute")
    if f["verdict"] == "REFUTED":
        return (3, "refute")
    if f["verdict"] == "AFFIRMED":
        return (4, "affirmed")
    return (5, "unverifiable")


def render_report(case_ids: list[str], scored: dict) -> str:
    sealed = _load_sealed()
    L: list[str] = []
    L.append("=" * 78)
    L.append("BIOTECH CATALYST HONESTY BACKTEST — R / f(M) / FINDING REPORT")
    L.append("Thesis: exclude programs whose marketing diverges from the authoritative")
    L.append("record. The call is blind; outcomes are unsealed only for scoring.")
    L.append("=" * 78)

    # Scorecard
    L.append("\nDISCRIMINATION SCORECARD")
    L.append("-" * 78)
    L.append(f"{'case':<26}{'CALL':<26}{'pred':<7}{'actual':<8}{'ok'}")
    for r in scored["rows"]:
        L.append(f"{r['case_id']:<26}{r['call']:<26}{r['predicted']:<7}"
                 f"{r['actual']:<8}{'Y' if r['correct'] else 'N'}")
    L.append("")
    L.append(f"Discriminates (MISS flagged, HIT clean): "
             f"{'YES' if scored['discriminates'] else 'NO'}")
    if scored["gap_separation"] is not None:
        L.append(f"Honesty-gap separation (min MISS − max HIT): {scored['gap_separation']:+.3f}")

    # Per-case detail
    for cid in case_ids:
        case = CASES[cid]
        pred = _load_prediction(case)
        s = pred["summary"]
        out = sealed[cid]
        L.append("\n" + "=" * 78)
        L.append(f"{case.company} ({case.ticker}) — {case.program} / {case.indication}")
        L.append(f"Catalyst: {case.catalyst_type}   Cutoff (blind): {case.cutoff}")
        L.append(f"BLIND CALL: {s['call']}   honesty_gap={s['honesty_gap_normalized']:.3f}   "
                 f"findings={s['n_findings']}")
        vc = s["verdict_counts"]
        L.append(f"Verdicts: REFUTED={vc.get('REFUTED',0)}  "
                 f"UNVERIFIABLE={vc.get('UNVERIFIABLE',0)}  AFFIRMED={vc.get('AFFIRMED',0)}")
        prov = pred["m_bundle_provenance"]["ctgov"]
        for nct, pr in prov.items():
            L.append(f"  M as-of cutoff: {nct} v{pr.get('asof_version')} "
                     f"({pr.get('asof_version_date')}); "
                     f"primary_changed={pr.get('primary_endpoint_changed')} "
                     f"completion_slipped={pr.get('primary_completion_slipped')}")

        decisive_keys = {(d["claim_id"], d["rule_id"])
                         for d in s["decisive_refutes_high_precision"]}
        demoted_map = {(d["claim_id"], d["rule_id"]): d["demoted"]
                       for d in s.get("other_severe_refutes", []) if d.get("demoted")}
        if decisive_keys:
            L.append("\n  CALL BASIS: decisive severe high-precision refute(s) — EXCLUDE.")
        else:
            L.append("\n  CALL BASIS: no decisive refute — marketing is consistent with the "
                     "authoritative record on the catalyst-critical claims.")

        # Full audit: render EVERY finding (R / f(M) / Finding), in reading order
        # decisive → demoted-severe → severe → refute → affirmed → unverifiable.
        # The decisive set drives the call; the rest are shown for diligence so a
        # demoted finding still surfaces, just without tripping auto-exclusion.
        L.append(f"\n  ALL FINDINGS ({len(pred['findings'])}):")
        ranked = sorted(
            pred["findings"],
            key=lambda f: (_finding_status(f, decisive_keys, demoted_map)[0],
                           f["channel"], f["claim_id"]))
        for f in ranked:
            _, status = _finding_status(f, decisive_keys, demoted_map)
            L.append("\n" + _fmt_finding(f, status))

        # Unblinded outcome (scoring only)
        L.append(f"  --- UNSEALED OUTCOME ({out['announced']}): {out['label']} "
                 f"({out.get('price_reaction_pct')}%) ---")
        L.append(f"  {out['summary']}")

    return "\n".join(L)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("case_ids", nargs="*", help="case ids (default: all)")
    ap.add_argument("--out", default=None, help="write report to this path")
    args = ap.parse_args()
    cids = args.case_ids or list(CASES.keys())
    scored = score(cids)
    report = render_report(cids, scored)
    print(report)
    out = Path(args.out) if args.out else (DATA_DIR / "_backtest_report.txt")
    out.write_text(report)
    print(f"\n[report -> {out}]", file=sys.stderr)
