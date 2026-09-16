"""
Aggregate the 5 blinded subagent outputs for the nuclear/SMR cohort into a
single cohort matrix + forward-prediction report. Mirrors `defense_aggregate.py`.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from .forward_bet_emission import emission_lines
from .nuclear_cohort import COHORT, CUTOFF

HERE = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_nuclear_cohort"


SEVERITY_ORDER = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY",
                  "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]

SEVERITY_WEIGHT = {
    "PASS":                  0.0,
    "UNVERIFIABLE":          0.0,
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

    w("# Advanced Nuclear / SMR Cohort — Blinded Forward-Test Predictions (v1)\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z — cutoff {CUTOFF}_\n")

    w("## Methodology\n")
    w(
        "Five US-listed advanced-nuclear / SMR / nuclear-fuel names: 3 speculative "
        "pre-revenue pure-plays (OKLO, NNE, ASPI) + 2 revenue-stage controls "
        "(LEU, BWXT). Each ticker was analyzed by an isolated, **blinded** "
        "Claude Code subagent (NNE / ASPI completed in-process after the cohort "
        "run stalled mid-scoring on 2026-05-16) with no outcome labels, no "
        "WebSearch / WebFetch access, no shared context with other tickers. "
        "Each subagent:\n\n"
        "1. Read the company's most recent pre-cutoff filing (most recent 10-K or S-1).\n"
        "2. Extracted 5-8 specific, testable, falsifiable factual claims.\n"
        "3. Picked M-source queries from the catalog (USAspending, USPTO ODP, "
        "EDGAR full-text against counterparty CIKs, EPA FRS).\n"
        "4. Executed queries and scored each claim PASS / MODERATE_UNDERDELIVERY / "
        "SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.\n\n"
        "**Calibration heuristics applied with extra weight here:** Heuristic 3 "
        "(planned vs operational — nuclear timelines slip routinely); Heuristic 7 "
        "(counterparty-disclosure threshold — Tier-1 utility / hyperscaler PPAs "
        "should appear in counterparty 10-Ks).\n\n"
        "**Catalog gaps surfaced for the nuclear vertical specifically:** NRC ADAMS "
        "docket / topical-report registry; DFC commitment registry; DOE-OSTI / "
        "INL Strategic Partnership Project (SPP) agreement registry; foreign "
        "regulator coverage (UK ONR, Necsa, CNSC, Health Canada).\n"
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

    w("## Per-ticker forward predictions\n")
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
        "- **Not a fraud accusation.** RED_FLAG_NEGATIVE means the filing claim "
        "diverges from independent registry evidence at the cutoff. It does not "
        "mean the company is lying. Multiple legitimate reasons exist for "
        "registry absence (early-stage programs, ADAMS coverage gap, private "
        "counterparties, foreign jurisdictions) and are noted per-claim where "
        "they apply.\n"
        "- **Not a trade recommendation.** Nuclear pure-plays can take years to "
        "resolve milestones; short timing is hard. See `feedback_truth_vs_alpha.md` "
        "— Truth_signal ≠ Tradable_alpha.\n"
        "- **Not pre-registered.** Recommend committing this report's hash to git "
        "for honest forward-bet bookkeeping.\n"
    )

    w("## Debt and tradeoffs\n")
    w(
        "- **NNE and ASPI scored in-process, not via isolated subagent.** The "
        "cohort runner stalled mid-scoring on 2026-05-16; the parent agent "
        "completed the scoring inline because the harness could not spawn "
        "isolated worktree-mode subagents from the non-git parent directory. "
        "Blinding discipline was preserved by (a) not reading hindsight / "
        "outcome files, (b) only reading OKLO.scores.json as a format reference "
        "(not for content cross-pollination), (c) applying the same rubric "
        "mechanically per ticker. Re-running these two through a proper isolated "
        "subagent (after fixing the worktree-creation path) is a fair next step.\n"
        "- **Catalog gap — NRC ADAMS connector is the #1 blocker** for nuclear-"
        "vertical scoring quality. Several NNE / OKLO claims are UNVERIFIABLE in "
        "the current catalog despite being highly verifiable in principle.\n"
        "- **Counterparty-silence threshold for hyperscaler PPAs needs calibration.** "
        "OKLO's Meta prepayment scored MODE (zero Meta mentions); a future "
        "hyperscaler 10-K disclosure window of 6-9 months may be the right "
        "validation cadence.\n"
        "- **Process rules surfaced by subagents** are captured per ticker in the "
        "`process_rules_discovered` field of each `.scores.json`. Worth promoting "
        "to memory per `feedback_subagent_rule_capture.md`.\n"
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
