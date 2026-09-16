"""
Aggregate the 5 blinded subagent outputs for the quantum cohort into a
single cohort matrix + forward-prediction report. Uses the shared
forward_bet_emission module (v2 threshold + Discovery_advantage gate).
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from .forward_bet_emission import emission_lines
from .quantum_cohort import COHORT, CUTOFF

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_quantum_cohort"


SEVERITY_ORDER = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY",
                  "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]

SEVERITY_WEIGHT = {
    "PASS":                   0.0,
    "UNVERIFIABLE":           0.0,
    "MODERATE_UNDERDELIVERY": 1.0,
    "SEVERE_UNDERDELIVERY":   2.0,
    "RED_FLAG_NEGATIVE":      3.0,
}


def load_ticker(ticker: str) -> dict:
    inp = json.loads((LOCAL / f"{ticker}.input.json").read_text())
    sco = json.loads((LOCAL / f"{ticker}.scores.json").read_text())
    return {"input": inp, "scores": sco}


def severity_counts(scores: list[dict]) -> dict[str, int]:
    c = Counter(s.get("severity", "UNKNOWN") for s in scores)
    return {k: c.get(k, 0) for k in SEVERITY_ORDER}


def composite_score(scores: list[dict]) -> float:
    counted = [s for s in scores if s.get("severity") != "UNVERIFIABLE"]
    if not counted:
        return 0.0
    total = sum(SEVERITY_WEIGHT.get(s.get("severity"), 0) for s in counted)
    return total / max(1, len(counted))


def build_matrix() -> list[dict]:
    out = []
    for m in COHORT:
        try:
            d = load_ticker(m.ticker)
        except FileNotFoundError:
            continue
        scores = d["scores"].get("scores", [])
        out.append({
            "ticker":           m.ticker,
            "cik":              m.cik,
            "company":          m.name,
            "n_claims":         len(d["input"].get("claims", [])),
            "n_scores":         len(scores),
            "severity_counts":  severity_counts(scores),
            "composite_score":  composite_score(scores),
            "filing":           d["input"].get("filing"),
            "red_flag_claims":  [s for s in scores if s.get("severity") == "RED_FLAG_NEGATIVE"],
            "severe_claims":    [s for s in scores if s.get("severity") == "SEVERE_UNDERDELIVERY"],
            "moderate_claims":  [s for s in scores if s.get("severity") == "MODERATE_UNDERDELIVERY"],
        })
    out.sort(key=lambda r: -r["composite_score"])
    return out


def write_report(matrix: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    w = lines.append

    w("# Quantum Computing Cohort — HELD-OUT Blinded Forward-Test Predictions (v1)\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z — cutoff {CUTOFF}_\n")

    w("## Methodology\n")
    w(
        "Five US-listed quantum-computing or QKD pure-plays: RGTI (Rigetti, "
        "superconducting gate-model), IONQ (IonQ, trapped-ion), QBTS "
        "(D-Wave, annealing), ARQQ (Arqit, QKD encryption — UK foreign "
        "private issuer, 20-F), QUBT (Quantum Computing Inc., photonic).\n\n"
        "**This is a HELD-OUT cohort.** The calibration heuristics in the "
        "subagent prompt template were authored from eVTOL, defense, lidar, "
        "and nuclear runs — NOT from any prior quantum-cohort outcomes. "
        "Per TECH_DEBT.md ('Calibration heuristics tuned on a single "
        "cohort are contaminated'), this run tests whether the framework's "
        "discrimination generalizes to a vertical it wasn't tuned on.\n\n"
        "Each ticker was analyzed by an isolated, **blinded** Claude Code "
        "subagent with no outcome labels, no WebSearch / WebFetch access, "
        "no shared context with other tickers. Subagent workflow now "
        "includes checkpointing: input.json written immediately after "
        "claim extraction; scores.json rewritten after each claim is "
        "scored (so a watchdog kill preserves partial work).\n\n"
        "Forward-bet emission uses the shared v3 emitter "
        "(`forward_bet_emission.py`): composite >= 0.6 AND "
        "discovery_advantage_tier IN {HIGH, MED}. Crowded shorts (high SI, "
        "well-followed) are suppressed even when Truth_signal is high.\n"
    )

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

    for line in emission_lines(matrix, CUTOFF):
        w(line)

    w("## What this is NOT\n")
    w(
        "- **Not a fraud accusation.** RED_FLAG_NEGATIVE means filings "
        "diverge from independent registries at the cutoff; legitimate "
        "reasons exist (e.g. confidential cloud-distribution agreements, "
        "early-stage government grants flow-through, foreign-jurisdiction "
        "national-lab work).\n"
        "- **Not a trade recommendation.** Quantum names trade on "
        "narrative cycles; even high-Truth_signal + high-Discovery_"
        "advantage names can squeeze hard.\n"
        "- **Not pre-registered.** Commit this report's hash to git for "
        "honest forward-bet bookkeeping.\n"
    )

    w("## Debt and tradeoffs\n")
    w(
        "- **HELD-OUT cohort = real validation, not perfect.** If the "
        "emission decisions on this cohort match what a discretionary "
        "analyst would have called pre-cutoff, the calibration heuristics "
        "generalize. If they diverge, calibration is overfit to the prior "
        "cohorts and needs refactoring (e.g. extracting per-cohort heuristic "
        "blocks into structured config rather than free-text prompt).\n"
        "- **Coverage gaps surfaced by subagents** will be captured in "
        "`connectors_to_add.md` (NIST quantum-program docket, DARPA "
        "ONISQ program list, AFRL Information Directorate / IARPA "
        "quantum program registries, hyperscaler partner-page scrapes "
        "for AWS Braket / Azure Quantum / GCP Quantum AI).\n"
    )

    report = OUT / "PREDICTIONS.md"
    report.write_text("\n".join(lines))
    (OUT / "matrix.json").write_text(json.dumps(matrix, indent=2, default=str))

    print(f"Wrote {report}")
    print(f"Wrote {OUT / 'matrix.json'}")
    print()
    print("Composite ranking:")
    for r in matrix:
        sc = r["severity_counts"]
        print(f"  {r['ticker']:>5}  comp={r['composite_score']:.2f}  "
              f"PASS={sc['PASS']} MOD={sc['MODERATE_UNDERDELIVERY']} "
              f"SEVE={sc['SEVERE_UNDERDELIVERY']} RED={sc['RED_FLAG_NEGATIVE']} "
              f"UNV={sc['UNVERIFIABLE']}")


def main():
    matrix = build_matrix()
    write_report(matrix)


if __name__ == "__main__":
    main()
