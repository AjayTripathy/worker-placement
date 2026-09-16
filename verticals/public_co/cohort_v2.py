"""Cohort confusion matrix from per-company tailored configs.

Reads each company's divergence_findings.json (produced by per-name config
runs that simulate LLM-driven M-source picking) and aggregates to a single
severity score. Then computes precision/recall/specificity vs known outcomes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"


# (ticker, outcome, outcome_detail) — same as cohort_screen.py COHORT
COHORT = [
    ("nkla",  "FRAUD",    "Hindenburg 2020-09; Trevor Milton convicted"),
    ("ride",  "FRAUD",    "Hindenburg 2021-03; bankrupt 2023-06; SEC enforcement"),
    ("hyzn",  "FRAUD",    "Blue Orca 2021-09; SEC charges 2024; bankrupt 2024-12"),
    ("muln",  "FRAUD",    "Hindenburg 2023-04; multiple short reports"),

    ("fsr",   "BANKRUPT", "Bankruptcy 2024-06"),
    ("goev",  "BANKRUPT", "Bankruptcy 2025-01"),
    ("arvl",  "BANKRUPT", "Bankruptcy 2024-02"),
    ("lev",   "BANKRUPT", "Bankruptcy 2024-12"),
    ("ptra",  "BANKRUPT", "Bankruptcy 2023-08"),
    ("ffie",  "BANKRUPT", "Penny stock; near-bankruptcy"),

    ("rivn",  "ALIVE",    "Producing R1T/R1S/EDV at scale"),
    ("lcid",  "ALIVE",    "Producing Air; PIF backing"),
    ("chpt",  "ALIVE",    "Charging network operating"),
    ("evgo",  "ALIVE",    "Charging network operating"),
    ("qs",    "ALIVE",    "Solid-state battery R&D; survived Scorpion 2021 short report"),
]


# Severity weights for the per-company aggregate score.
SEV_WEIGHT = {
    "RED_FLAG_NEGATIVE": 4.0,
    "SEVERE_UNDERDELIVERY": 3.0,
    "MODERATE_UNDERDELIVERY": 1.5,
    "UNVERIFIABLE": 0.0,
    "PASS": 0.0,
}


def aggregate(ticker: str) -> dict:
    p = DATA / ticker / "divergence_findings.json"
    if not p.exists():
        return {"ticker": ticker, "error": "no findings"}
    findings = json.loads(p.read_text())
    counts: dict[str, int] = {}
    for f in findings:
        sev = str(f.get("severity"))
        counts[sev] = counts.get(sev, 0) + 1
    score = sum(SEV_WEIGHT.get(s, 0) * n for s, n in counts.items())
    n_claims = len(findings)
    n_contradicted = sum(1 for f in findings if f.get("M_supports_claim") is False)
    # Normalize per-claim so different config sizes are comparable
    score_per_claim = score / n_claims if n_claims else 0.0
    return {
        "ticker": ticker,
        "n_claims": n_claims,
        "n_contradicted": n_contradicted,
        "severity_score": round(score, 1),
        "score_per_claim": round(score_per_claim, 2),
        "counts": counts,
    }


def confusion_matrix(rows: list[dict], threshold: float, label: str,
                     positive_set: set) -> None:
    tp = sum(1 for r in rows if r["score_per_claim"] >= threshold and r["outcome"] in positive_set)
    fp = sum(1 for r in rows if r["score_per_claim"] >= threshold and r["outcome"] not in positive_set)
    tn = sum(1 for r in rows if r["score_per_claim"] < threshold and r["outcome"] not in positive_set)
    fn = sum(1 for r in rows if r["score_per_claim"] < threshold and r["outcome"] in positive_set)
    n = tp + fp + tn + fn
    p = tp / (tp + fp) if (tp + fp) else 0.0
    rc = tp / (tp + fn) if (tp + fn) else 0.0
    sp = tn / (tn + fp) if (tn + fp) else 0.0
    print(f"  threshold={threshold}/claim  {label}:")
    print(f"    TP={tp} FP={fp} TN={tn} FN={fn}  (n={n})")
    print(f"    Precision={p:.0%}  Recall={rc:.0%}  Specificity={sp:.0%}")


def main() -> None:
    rows = []
    for ticker, outcome, detail in COHORT:
        agg = aggregate(ticker)
        agg["outcome"] = outcome
        agg["detail"] = detail
        rows.append(agg)

    rows_sorted = sorted(rows, key=lambda r: -r["score_per_claim"])

    print()
    print("=" * 110)
    print(f"{'Ticker':<7} {'Outcome':<9} {'Claims':<7} {'Contra':<7} {'Score':<7} {'/claim':<7} {'Counts'}")
    print("-" * 110)
    for r in rows_sorted:
        if "error" in r:
            print(f"{r['ticker']:<7} {r['outcome']:<9} ERROR: {r['error']}")
            continue
        cstr = ", ".join(f"{k.split('_')[0][:4]}={v}" for k, v in sorted(r["counts"].items()))
        print(f"{r['ticker'].upper():<7} {r['outcome']:<9} {r['n_claims']:<7} "
              f"{r['n_contradicted']:<7} {r['severity_score']:<7} {r['score_per_claim']:<7} {cstr}")
    print("=" * 110)

    print("\nConfusion matrices at multiple thresholds (using per-claim score):")
    for threshold in [0.5, 1.0, 1.5, 2.0]:
        print()
        confusion_matrix(rows, threshold, "Strict (FRAUD only)", {"FRAUD"})
        confusion_matrix(rows, threshold, "Loose (FRAUD+BANKRUPT)", {"FRAUD", "BANKRUPT"})


if __name__ == "__main__":
    main()
