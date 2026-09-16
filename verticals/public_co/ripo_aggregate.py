"""Aggregate the 25 blinded RIPO-cohort subagent outputs into a composite
ranking, then REVEAL the firewalled outcomes and score discrimination.

The whole point: does the blinded R/f(M) diligencer's composite severity separate
the 3 catastrophes (PACS, VG, CHYM) from the 22 survivors WITHIN RIPO's already-
vetted picks? Outcomes are imported here ONLY (subagents never see them).

Run: python3 -m verticals.public_co.ripo_aggregate
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from .ripo_cohort import COHORT
from ._ripo_outcomes import OUTCOMES, CATASTROPHES

HERE = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT = HERE / "data" / "_ripo_cohort"

SEVERITY_ORDER = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY",
                  "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]
SEVERITY_WEIGHT = {"PASS": 0.0, "UNVERIFIABLE": 0.0, "MODERATE_UNDERDELIVERY": 1.0,
                   "SEVERE_UNDERDELIVERY": 2.0, "RED_FLAG_NEGATIVE": 3.0}


def load_ticker(ticker: str) -> dict | None:
    fi = LOCAL / f"{ticker}.input.json"
    fs = LOCAL / f"{ticker}.scores.json"
    if not fs.exists():
        return None
    inp = json.loads(fi.read_text()) if fi.exists() else {"claims": []}
    sco = json.loads(fs.read_text())
    return {"input": inp, "scores": sco}


def severity_counts(scores):
    c = Counter(s.get("severity", "UNKNOWN") for s in scores)
    return {k: c.get(k, 0) for k in SEVERITY_ORDER}


def composite_score(scores):
    counted = [s for s in scores if s.get("severity") != "UNVERIFIABLE"]
    if not counted:
        return 0.0
    return sum(SEVERITY_WEIGHT.get(s.get("severity"), 0) for s in counted) / len(counted)


def build_matrix():
    out = []
    for m in COHORT:
        d = load_ticker(m.ticker)
        if d is None:
            out.append({"ticker": m.ticker, "company": m.name, "missing": True})
            continue
        scores = d["scores"].get("scores", [])
        out.append({
            "ticker": m.ticker, "cik": m.cik, "company": m.name,
            "missing": False,
            "n_claims": len(d["input"].get("claims", [])),
            "n_scores": len(scores),
            "severity_counts": severity_counts(scores),
            "composite_score": composite_score(scores),
            "n_red": severity_counts(scores)["RED_FLAG_NEGATIVE"],
            "n_severe": severity_counts(scores)["SEVERE_UNDERDELIVERY"],
            "filing": d["input"].get("filing"),
            "red_flag_claims": [s for s in scores if s.get("severity") == "RED_FLAG_NEGATIVE"],
            "severe_claims": [s for s in scores if s.get("severity") == "SEVERE_UNDERDELIVERY"],
            "moderate_claims": [s for s in scores if s.get("severity") == "MODERATE_UNDERDELIVERY"],
        })
    done = [r for r in out if not r["missing"]]
    done.sort(key=lambda r: -r["composite_score"])
    missing = [r for r in out if r["missing"]]
    return done + missing


def discrimination(matrix):
    """Reveal outcomes; score whether composite separates catastrophes."""
    scored = [r for r in matrix if not r["missing"]]
    rows = []
    for r in scored:
        lab = OUTCOMES.get(r["ticker"], ("?", None, ""))[0]
        rows.append({**r, "outcome": lab,
                     "is_catastrophe": r["ticker"] in CATASTROPHES})
    cats = [r for r in rows if r["is_catastrophe"]]
    survs = [r for r in rows if not r["is_catastrophe"] and r["outcome"] != "MERGER_CASHOUT"]

    def avg(xs, k):
        return round(sum(x[k] for x in xs) / len(xs), 3) if xs else None

    # Rank-based separation: where do the catastrophes land in the composite order?
    ordered = sorted(rows, key=lambda r: -r["composite_score"])
    n = len(ordered)
    cat_ranks = [i + 1 for i, r in enumerate(ordered) if r["is_catastrophe"]]

    # If we "excluded" the top-k by composite, how many catastrophes caught vs
    # expected by random?  (precision@k for k = number of catastrophes)
    k = len(cats)
    topk = ordered[:k]
    caught = sum(1 for r in topk if r["is_catastrophe"])

    return {
        "n_scored": n,
        "n_catastrophe": len(cats),
        "n_survivor": len(survs),
        "catastrophe_tickers": [r["ticker"] for r in cats],
        "mean_composite_catastrophe": avg(cats, "composite_score"),
        "mean_composite_survivor": avg(survs, "composite_score"),
        "mean_red_catastrophe": avg(cats, "n_red"),
        "mean_red_survivor": avg(survs, "n_red"),
        "catastrophe_ranks_by_composite": cat_ranks,
        "precision_at_k": {"k": k, "caught": caught,
                           "random_expectation": round(k * k / n, 2) if n else None},
        "rows": rows,
    }


def write_report(matrix, disc):
    OUT.mkdir(parents=True, exist_ok=True)
    L = []
    w = L.append
    w("# RIPO-Cohort — Blinded R/f(M) Diligencer Forward Test\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z_\n")
    w("## Methodology\n")
    w("25 names that the Renaissance IPO ETF actually held AND appear in the "
      "survivorship-free 2024-25 primary-IPO backtest. Each scored by an isolated, "
      "**blinded** subagent (no outcome labels, no WebSearch/WebFetch, per-name "
      "cutoff = IPO date) reading ONLY the IPO prospectus. R (claim in the S-1/F-1/"
      "424B4) − f(M, independent registry: USPTO / USAspending / EPA FRS / "
      "ClinicalTrials / openFDA / EDGAR full-text counterparty disclosure).\n")
    w("**The question:** within RIPO's already-vetted picks, does composite severity "
      "separate the 3 catastrophes (PACS, VG, CHYM) from the 22 survivors? This is "
      "the test the buyside_dd structural-screen backtest could not run.\n")

    w("## Composite ranking (OUTCOMES REVEALED)\n")
    w("Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MOD=1, SEVE=2, RED=3).\n")
    w("| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite | Outcome |")
    w("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
    ordered = [r for r in matrix if not r["missing"]]
    for i, r in enumerate(ordered, 1):
        sc = r["severity_counts"]
        lab = OUTCOMES.get(r["ticker"], ("?",))[0]
        tag = "**CATASTROPHE**" if r["ticker"] in CATASTROPHES else lab
        w(f"| {i} | {r['ticker']} | {r['company'][:30]} | {r['n_claims']} | "
          f"{sc['PASS']} | {sc['MODERATE_UNDERDELIVERY']} | {sc['SEVERE_UNDERDELIVERY']} | "
          f"{sc['RED_FLAG_NEGATIVE']} | {sc['UNVERIFIABLE']} | {r['composite_score']:.2f} | {tag} |")
    miss = [r for r in matrix if r["missing"]]
    if miss:
        w(f"\n_Missing (no scores.json): {', '.join(r['ticker'] for r in miss)}_\n")

    w("\n## Discrimination\n")
    w(f"- Catastrophes: {disc['catastrophe_tickers']}")
    w(f"- Mean composite — catastrophes **{disc['mean_composite_catastrophe']}** "
      f"vs survivors **{disc['mean_composite_survivor']}**")
    w(f"- Mean RED flags — catastrophes **{disc['mean_red_catastrophe']}** "
      f"vs survivors **{disc['mean_red_survivor']}**")
    w(f"- Catastrophe ranks by composite (1=highest severity): "
      f"**{disc['catastrophe_ranks_by_composite']}** of {disc['n_scored']}")
    pk = disc["precision_at_k"]
    w(f"- Precision@k (exclude top-{pk['k']} by composite): caught {pk['caught']}/"
      f"{pk['k']} catastrophes vs random expectation {pk['random_expectation']}\n")

    w("## Per-ticker findings (RED / SEVERE / MODERATE)\n")
    for r in ordered:
        if not (r["red_flag_claims"] or r["severe_claims"] or r["moderate_claims"]):
            continue
        w(f"### {r['ticker']} — {r['company']}  (composite {r['composite_score']:.2f})\n")
        for label, key in [("RED_FLAG_NEGATIVE", "red_flag_claims"),
                           ("SEVERE_UNDERDELIVERY", "severe_claims"),
                           ("MODERATE_UNDERDELIVERY", "moderate_claims")]:
            for s in r[key]:
                w(f"- **[{label}] {s.get('claim_id','?')}** — {s.get('claim_text','')[:200]}")
                w(f"  - M: `{s.get('M_check','?')}` → {str(s.get('M_value',''))[:200]}")
                w(f"  - {s.get('interpretation','')[:300]}")
        w("")

    w("## Caveats\n")
    w("- N=25 with only 3 catastrophes is statistically underpowered; read the "
      "separation as anecdote, not significance.\n"
      "- The cohort skews software/fintech/crypto where registry M-sources have "
      "little to cross-check; heavy UNVERIFIABLE on those names is expected and "
      "is itself an honest result (the framework declines to opine rather than "
      "fabricating signal).\n"
      "- PACS is a hard-event catastrophe whose PRICE recovered (+58%); a severity "
      "screen keyed to disclosure honesty may or may not flag it from the "
      "prospectus alone.\n")

    (OUT / "PREDICTIONS.md").write_text("\n".join(L))
    (OUT / "matrix.json").write_text(json.dumps({"matrix": matrix, "discrimination": disc},
                                                indent=2, default=str))
    print(f"Wrote {OUT/'PREDICTIONS.md'}\nWrote {OUT/'matrix.json'}\n")
    print("Composite ranking (outcome in brackets):")
    for i, r in enumerate(ordered, 1):
        sc = r["severity_counts"]
        tag = "CAT" if r["ticker"] in CATASTROPHES else OUTCOMES.get(r["ticker"], ("?",))[0][:4]
        print(f"  {i:>2}. {r['ticker']:>9}  comp={r['composite_score']:.2f}  "
              f"R={sc['RED_FLAG_NEGATIVE']} SE={sc['SEVERE_UNDERDELIVERY']} "
              f"MO={sc['MODERATE_UNDERDELIVERY']} UN={sc['UNVERIFIABLE']}  [{tag}]")
    if miss:
        print(f"  missing: {', '.join(r['ticker'] for r in miss)}")
    print(f"\ncatastrophe mean composite {disc['mean_composite_catastrophe']} "
          f"vs survivor {disc['mean_composite_survivor']}; "
          f"cat ranks {disc['catastrophe_ranks_by_composite']}/{disc['n_scored']}")


def main():
    matrix = build_matrix()
    disc = discrimination(matrix)
    write_report(matrix, disc)


if __name__ == "__main__":
    main()
