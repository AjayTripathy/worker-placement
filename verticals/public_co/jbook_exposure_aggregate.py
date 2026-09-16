"""
Aggregate the J-Book exposure subagent outputs into a single cohort matrix.

Reads the `<TICKER>.jbook.input.json` + `<TICKER>.jbook.scores.json` files
in data/_local/ (note the `.jbook` infix — keeps these runs separate from
the general defense_cohort run which uses bare `<TICKER>.input.json`).
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from .jbook_exposure_cohort import COHORT, CUTOFF

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_jbook_exposure_cohort"


SEVERITY_ORDER = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY",
                  "RED_FLAG_NEGATIVE", "UNVERIFIABLE", "NOT_IN_FILING"]

SEVERITY_WEIGHT = {
    "PASS":                    0.0,
    "UNVERIFIABLE":            0.0,
    "NOT_IN_FILING":           0.0,
    "MODERATE_UNDERDELIVERY":  1.0,
    "SEVERE_UNDERDELIVERY":    2.0,
    "RED_FLAG_NEGATIVE":       3.0,
}

# Severities excluded from the composite denominator. UNVERIFIABLE = M-source
# coverage gap (we couldn't measure). NOT_IN_FILING = the claim itself isn't
# in the issuer's filing — typically a cohort-attributed program tag added
# by the cohort builder. Scoring a claim that isn't actually made by the
# issuer is methodologically wrong; both buckets are removed from composite.
EXCLUDED_FROM_COMPOSITE = {"UNVERIFIABLE", "NOT_IN_FILING"}

# Heuristic recognizers for cohort-attributed claims that should be
# re-bucketed to NOT_IN_FILING regardless of how they were originally scored.
# These match patterns used by the LLM subagent when the program tag came
# from cohort metadata rather than the 10-K.
_NOT_IN_FILING_PATTERNS = (
    "cohort-attributed",
    "not named in 10-k",
    "not named in 10k",
    "not in 10-k",
    "not in 10k",
    "cohort-attributed but not named",
    "the 10-k does not name",
    "the 10-k does not mention",
)


def _is_not_in_filing(score: dict) -> bool:
    """Detect cohort-attributed claims that the issuer never made.

    Such claims should be excluded from the composite denominator because
    the framework's job is to verify the issuer's representations, not
    cohort-supplementary program tags.
    """
    text = " ".join([
        str(score.get("claim_text") or ""),
        str(score.get("interpretation") or ""),
    ]).lower()
    return any(pat in text for pat in _NOT_IN_FILING_PATTERNS)


def effective_severity(score: dict) -> str:
    """Severity to use for composite computation.

    Re-buckets cohort-attributed-not-in-filing claims to NOT_IN_FILING,
    leaves all other severities as-is.
    """
    declared = score.get("severity", "UNKNOWN")
    if _is_not_in_filing(score):
        return "NOT_IN_FILING"
    return declared


def load_ticker(ticker: str) -> dict | None:
    inp_path = LOCAL / f"{ticker}.jbook.input.json"
    sco_path = LOCAL / f"{ticker}.jbook.scores.json"
    if not inp_path.exists() or not sco_path.exists():
        return None
    return {
        "input":  json.loads(inp_path.read_text()),
        "scores": json.loads(sco_path.read_text()),
    }


def severity_counts(scores: list[dict]) -> dict[str, int]:
    c = Counter(effective_severity(s) for s in scores)
    return {k: c.get(k, 0) for k in SEVERITY_ORDER}


def composite_score(scores: list[dict]) -> float:
    counted = [s for s in scores if effective_severity(s) not in EXCLUDED_FROM_COMPOSITE]
    if not counted:
        return 0.0
    return sum(SEVERITY_WEIGHT.get(effective_severity(s), 0)
                for s in counted) / max(1, len(counted))


def jbook_hit_count(scores: list[dict]) -> int:
    """Count how many scored claims used pentagon_jbook as the M-source."""
    n = 0
    for s in scores:
        m_check = (s.get("M_check") or "").lower()
        if "pentagon_jbook" in m_check or "jbook" in m_check:
            n += 1
    return n


def build_matrix() -> list[dict]:
    out = []
    for m in COHORT:
        d = load_ticker(m.ticker)
        if not d:
            out.append({
                "ticker": m.ticker, "cik": m.cik, "company": m.name,
                "status": "NOT_RUN",
            })
            continue
        scores = d["scores"].get("scores", [])
        out.append({
            "ticker":           m.ticker,
            "cik":              m.cik,
            "company":          m.name,
            "status":           "OK",
            "n_claims":         len(d["input"].get("claims", [])),
            "n_scores":         len(scores),
            "n_jbook_hits":     jbook_hit_count(scores),
            "severity_counts":  severity_counts(scores),
            "composite_score":  composite_score(scores),
            "filing":           d["input"].get("filing"),
            "red_flag_claims":  [s for s in scores if s.get("severity") == "RED_FLAG_NEGATIVE"],
            "severe_claims":    [s for s in scores if s.get("severity") == "SEVERE_UNDERDELIVERY"],
            "moderate_claims":  [s for s in scores if s.get("severity") == "MODERATE_UNDERDELIVERY"],
        })
    # Sort: completed runs first by composite (desc), then NOT_RUN
    out.sort(key=lambda r: (
        0 if r.get("status") == "OK" else 1,
        -(r.get("composite_score") or 0),
    ))
    return out


def write_report(matrix: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    w = lines.append

    completed = [r for r in matrix if r.get("status") == "OK"]
    pending   = [r for r in matrix if r.get("status") != "OK"]

    w("# J-Book Exposure Cohort — Forward-Test Predictions\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z — cutoff {CUTOFF}_\n")
    w(f"_Tickers: {len(completed)} completed, {len(pending)} pending_\n")

    w("## Methodology\n")
    w(
        "Each ticker is analyzed by an isolated, **blinded** Claude Code "
        "subagent that focuses on the J-BOOK EXPOSURE DIVERGENCE PATTERN: "
        "company makes a material claim about a named Pentagon program → "
        "pentagon_jbook M-source returns the program's forward funding "
        "status from a 410-program corpus (DARPA + MDA + SOCOM + OSD + "
        "AF RDT&E Vol I-IV + Space Force RDT&E + selected procurement). "
        "Severity tiers map directly from J-Book status:\n"
        "- FUNDED_GROWING / FUNDED_STEADY → PASS\n"
        "- FUNDED_SHRINKING → MODERATE_UNDERDELIVERY\n"
        "- UNFUNDED_THIS_YEAR → SEVERE_UNDERDELIVERY\n"
        "- UNFUNDED_TWO_PLUS_YEARS / TERMINATED → RED_FLAG_NEGATIVE\n"
        "- NOT_FOUND → UNVERIFIABLE (coverage gap)\n"
    )

    w("## Composite ranking\n")
    w("Composite = weighted-mean severity per non-UNVERIFIABLE claim "
      "(PASS=0, MODERATE=1, SEVERE=2, RED=3).\n")
    w("| Rank | Ticker | Company | Claims | JBook hits | PASS | MOD | SEVE | RED | UNV | Composite |")
    w("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for i, r in enumerate(completed, 1):
        sc = r["severity_counts"]
        w(f"| {i} | {r['ticker']} | {r['company'][:35]} | {r['n_claims']} | "
          f"{r['n_jbook_hits']} | {sc['PASS']} | {sc['MODERATE_UNDERDELIVERY']} | "
          f"{sc['SEVERE_UNDERDELIVERY']} | {sc['RED_FLAG_NEGATIVE']} | "
          f"{sc['UNVERIFIABLE']} | {r['composite_score']:.2f} |")
    w("")
    if pending:
        w("### Pending (subagent not yet run)")
        for r in pending:
            w(f"- {r['ticker']} — {r['company']}")
        w("")

    w("## Per-ticker forward predictions\n")
    for r in completed:
        w(f"### {r['ticker']} — {r['company']}\n")
        w(f"- **Filing analyzed:** `{r['filing']}`")
        w(f"- **Claims extracted:** {r['n_claims']}  (J-Book M-source fired on {r['n_jbook_hits']})")
        sc = r['severity_counts']
        w(f"- **Severity distribution:** PASS={sc['PASS']}, MODERATE={sc['MODERATE_UNDERDELIVERY']}, "
          f"SEVERE={sc['SEVERE_UNDERDELIVERY']}, RED_FLAG={sc['RED_FLAG_NEGATIVE']}, "
          f"UNVERIFIABLE={sc['UNVERIFIABLE']}")
        w(f"- **Composite severity:** {r['composite_score']:.2f}\n")
        if r["red_flag_claims"]:
            w("#### 🔴 RED_FLAG_NEGATIVE claims")
            for s in r["red_flag_claims"]:
                w(f"- **{s.get('claim_id','?')}** — {s.get('claim_text','')[:250]}")
                w(f"  - M-check: `{s.get('M_check','?')}`")
                w(f"  - M-value: {str(s.get('M_value',''))[:300]}")
                w(f"  - Interpretation: {s.get('interpretation','')[:400]}\n")
        if r["severe_claims"]:
            w("#### 🟠 SEVERE_UNDERDELIVERY claims")
            for s in r["severe_claims"]:
                w(f"- **{s.get('claim_id','?')}** — {s.get('claim_text','')[:250]}")
                w(f"  - Interpretation: {s.get('interpretation','')[:400]}\n")
        if r["moderate_claims"]:
            w("#### 🟡 MODERATE_UNDERDELIVERY claims")
            for s in r["moderate_claims"]:
                w(f"- **{s.get('claim_id','?')}** — {s.get('claim_text','')[:200]}\n")
        w("")

    (OUT / "PREDICTIONS.md").write_text("\n".join(lines))
    (OUT / "matrix.json").write_text(json.dumps(matrix, indent=2, default=str))
    print(f"Wrote {OUT}/PREDICTIONS.md ({len(completed)} completed, {len(pending)} pending)")


def main():
    matrix = build_matrix()
    write_report(matrix)


if __name__ == "__main__":
    main()
