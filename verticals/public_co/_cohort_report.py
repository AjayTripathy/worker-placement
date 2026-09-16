"""
Shared cohort-report rendering. Used by hydrogen / dcpivot / ssbattery /
robotics / (future) aggregators to avoid re-cloning the ~150-line
report-rendering boilerplate from defense_aggregate / lidar_aggregate /
nuclear_aggregate / quantum_aggregate.

Callers provide the per-cohort COHORT list + cutoff + a small dict of
cohort-specific copy strings. This function builds matrix.json +
PREDICTIONS.md, calling forward_bet_emission.emission_lines for the
forward-bet section.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable, Protocol

from .forward_bet_emission import emission_lines


SEVERITY_ORDER = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY",
                  "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]

SEVERITY_WEIGHT = {
    "PASS":                   0.0,
    "UNVERIFIABLE":           0.0,
    "MODERATE_UNDERDELIVERY": 1.0,
    "SEVERE_UNDERDELIVERY":   2.0,
    "RED_FLAG_NEGATIVE":      3.0,
}


class _CohortMemberLike(Protocol):
    ticker: str
    cik:    str
    name:   str


_SEVERITY_ALIASES = {
    "PASS":                   "PASS",
    "MODERATE":               "MODERATE_UNDERDELIVERY",
    "MODERATE_UNDERDELIVERY": "MODERATE_UNDERDELIVERY",
    "MOD":                    "MODERATE_UNDERDELIVERY",
    "MODE":                   "MODERATE_UNDERDELIVERY",
    "SEVERE":                 "SEVERE_UNDERDELIVERY",
    "SEVERE_UNDERDELIVERY":   "SEVERE_UNDERDELIVERY",
    "SEVE":                   "SEVERE_UNDERDELIVERY",
    "RED":                    "RED_FLAG_NEGATIVE",
    "RED_FLAG":               "RED_FLAG_NEGATIVE",
    "RED_FLAG_NEGATIVE":      "RED_FLAG_NEGATIVE",
    "UNVERIFIABLE":           "UNVERIFIABLE",
    "UNVERIFIED":             "UNVERIFIABLE",
    "UNVE":                   "UNVERIFIABLE",
}


def _norm_severity(s: str | None) -> str:
    return _SEVERITY_ALIASES.get((s or "").upper().strip(), "UNKNOWN")


def severity_counts(scores: list[dict]) -> dict[str, int]:
    c = Counter(_norm_severity(s.get("severity")) for s in scores)
    return {k: c.get(k, 0) for k in SEVERITY_ORDER}


def composite_score(scores: list[dict]) -> float:
    counted = [s for s in scores if _norm_severity(s.get("severity")) != "UNVERIFIABLE"]
    if not counted:
        return 0.0
    total = sum(SEVERITY_WEIGHT.get(_norm_severity(s.get("severity")), 0) for s in counted)
    return total / max(1, len(counted))


def build_matrix(cohort: Iterable[_CohortMemberLike], local_dir: Path) -> list[dict]:
    out = []
    for m in cohort:
        try:
            inp = json.loads((local_dir / f"{m.ticker}.input.json").read_text())
            sco = json.loads((local_dir / f"{m.ticker}.scores.json").read_text())
        except FileNotFoundError:
            continue
        scores = sco.get("scores", [])
        out.append({
            "ticker":           m.ticker,
            "cik":              m.cik,
            "company":          m.name,
            "n_claims":         len(inp.get("claims", [])),
            "n_scores":         len(scores),
            "severity_counts":  severity_counts(scores),
            "composite_score":  composite_score(scores),
            "filing":           inp.get("filing"),
            "red_flag_claims":  [s for s in scores if _norm_severity(s.get("severity")) == "RED_FLAG_NEGATIVE"],
            "severe_claims":    [s for s in scores if _norm_severity(s.get("severity")) == "SEVERE_UNDERDELIVERY"],
            "moderate_claims":  [s for s in scores if _norm_severity(s.get("severity")) == "MODERATE_UNDERDELIVERY"],
        })
    out.sort(key=lambda r: -r["composite_score"])
    return out


def write_report(
    *,
    matrix:        list[dict],
    cutoff:        str,
    out_dir:       Path,
    title:         str,
    methodology:   str,
    not_this:      str | None = None,
    debt:          str | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    w = lines.append

    w(f"# {title}\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z — cutoff {cutoff}_\n")

    w("## Methodology\n")
    w(methodology)
    w("")

    w("## Composite ranking\n")
    w("Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).\n")
    w("| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |")
    w("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for i, r in enumerate(matrix, 1):
        sc = r["severity_counts"]
        w(f"| {i} | {r['ticker']} | {r['company'][:35]} | {r['n_claims']} | "
          f"{sc['PASS']} | {sc['MODERATE_UNDERDELIVERY']} | {sc['SEVERE_UNDERDELIVERY']} | "
          f"{sc['RED_FLAG_NEGATIVE']} | {sc['UNVERIFIABLE']} | {r['composite_score']:.2f} |")
    w("")

    w("## Per-ticker findings\n")
    for r in matrix:
        w(f"### {r['ticker']} — {r['company']}\n")
        w(f"- **Filing analyzed:** `{r['filing']}`")
        w(f"- **Claims extracted:** {r['n_claims']}")
        sc = r['severity_counts']
        w(f"- **Severity distribution:** PASS={sc['PASS']}, MODERATE={sc['MODERATE_UNDERDELIVERY']}, "
          f"SEVERE={sc['SEVERE_UNDERDELIVERY']}, RED_FLAG={sc['RED_FLAG_NEGATIVE']}, "
          f"UNVERIFIABLE={sc['UNVERIFIABLE']}")
        w(f"- **Composite severity:** {r['composite_score']:.2f}\n")

        if r["red_flag_claims"]:
            w("#### 🔴 RED_FLAG_NEGATIVE claims")
            for s in r["red_flag_claims"]:
                w(f"- **{s.get('claim_id','?')}** — {s.get('claim_text','')[:200]}")
                w(f"  - M-check: `{s.get('M_check','?')}`")
                w(f"  - M-value: {str(s.get('M_value',''))[:300]}")
                w(f"  - Interpretation: {s.get('interpretation','')[:400]}")
        if r["severe_claims"]:
            w("#### 🟠 SEVERE_UNDERDELIVERY claims")
            for s in r["severe_claims"]:
                w(f"- **{s.get('claim_id','?')}** — {s.get('claim_text','')[:200]}")
                w(f"  - Interpretation: {s.get('interpretation','')[:400]}")
        if r["moderate_claims"]:
            w("#### 🟡 MODERATE_UNDERDELIVERY claims")
            for s in r["moderate_claims"]:
                w(f"- **{s.get('claim_id','?')}** — {s.get('claim_text','')[:200]}")
                w(f"  - Interpretation: {s.get('interpretation','')[:300]}")
        w("")

    for line in emission_lines(matrix, cutoff):
        w(line)

    if not_this:
        w("## What this is NOT\n")
        w(not_this)
    if debt:
        w("## Debt and tradeoffs\n")
        w(debt)

    report = out_dir / "PREDICTIONS.md"
    report.write_text("\n".join(lines))
    (out_dir / "matrix.json").write_text(json.dumps(matrix, indent=2, default=str))

    print(f"Wrote {report}")
    print(f"Wrote {out_dir / 'matrix.json'}")
    print()
    print("Composite ranking:")
    for r in matrix:
        sc = r["severity_counts"]
        print(f"  {r['ticker']:>5}  comp={r['composite_score']:.2f}  "
              f"PASS={sc['PASS']} MOD={sc['MODERATE_UNDERDELIVERY']} "
              f"SEVE={sc['SEVERE_UNDERDELIVERY']} RED={sc['RED_FLAG_NEGATIVE']} "
              f"UNV={sc['UNVERIFIABLE']}")
