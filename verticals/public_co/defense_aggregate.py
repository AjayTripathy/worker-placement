"""
Aggregate the 5 blinded subagent outputs into a single cohort matrix +
forward-prediction report.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from .defense_cohort import COHORT, CUTOFF
from .forward_bet_emission import emission_lines

HERE = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_defense_cohort"


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
    """Weighted average severity per claim, ignoring UNVERIFIABLE."""
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

    w("# Defense-Tech Cohort — Blinded Forward-Test Predictions (v1)\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z — cutoff {CUTOFF}_\n")

    w("## Methodology\n")
    w(
        "Five US-listed defense-tech / military-drone names. Each ticker was "
        "analyzed by an isolated, **blinded** Claude Code subagent with no "
        "outcome labels, no WebSearch / WebFetch access, no shared context with "
        "other tickers. Each subagent:\n\n"
        "1. Read the company's most recent pre-cutoff filing (most recent 10-K or S-1).\n"
        "2. Extracted 5-8 specific, testable, falsifiable factual claims.\n"
        "3. Picked M-source queries from the catalog (USAspending, USPTO ODP, "
        "EDGAR full-text against counterparty CIKs, EPA FRS).\n"
        "4. Executed queries and scored each claim PASS / MODERATE_UNDERDELIVERY / "
        "SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.\n\n"
        "**This is the Signal OS thesis applied as intended:** R (claim made by "
        "the company in SEC filing) − f(M, where M is an independent registry "
        "the prevailing analysis isn't using). The framework's edge is in M-side "
        "lookups (USAspending for DoD contracts, USPTO ODP for patents, EDGAR "
        "for counterparty disclosure) that ordinary screeners don't perform.\n"
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
        "registry absence (early-stage programs, prime/sub flow-through, foreign "
        "sales, classified IP) and are noted per-claim where they apply.\n"
        "- **Not a trade recommendation.** Most names in this cohort are micro-cap "
        "and may not be cleanly shortable (see prior `_distress_sift/PREDICTIONS.md` "
        "for the shortability methodology — same applies here).\n"
        "- **Not pre-registered.** For the predictions to count as honest "
        "forward bets they need a cryptographic timestamp. Recommend committing "
        "this report's hash to git or an external timestamp service.\n"
    )

    w("## Debt and tradeoffs\n")
    w(
        "- **Subagent variance.** Five independent runs produced slightly "
        "different claim selection per ticker. UMAC's 8 claims overlap only "
        "partially with what RCAT's subagent picked even though both are drone "
        "names. The framework's discrimination depends on the LLM picking the "
        "right claims; a re-run with different temperature could shift the "
        "result.\n"
        "- **USAspending recipient-name matching is fuzzy.** AIRO's subagent "
        "caught the 'Agile Defense LLC' name collision ($1B unrelated IT "
        "contractor); ONDS's subagent caught the 'HONDASHOKAI' substring noise. "
        "Both were correctly excluded but a less careful run might credit the "
        "company with another entity's contracts.\n"
        "- **Coverage gaps surfaced by subagents (queued for `connectors_to_add.md`):**\n"
        "  - DIU Blue UAS Cleared List (no current connector — every drone company's "
        "    core regulatory-milestone claim scores UNVERIFIABLE without it)\n"
        "  - FAA UAS registry (similar)\n"
        "  - Class I freight railroad counterparty CIKs (need to add to common-counterparties)\n"
        "- **Process rules surfaced by subagents are captured to memory** in "
        "`feedback_*.md` files per the subagent-rule-capture rule "
        "(`feedback_subagent_rule_capture.md`).\n"
    )

    report = OUT / "PREDICTIONS.md"
    report.write_text("\n".join(lines))

    # Also dump raw matrix as JSON
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
