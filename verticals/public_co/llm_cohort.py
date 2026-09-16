"""End-to-end LLM-driven cohort run + confusion matrix.

For each cohort member:
  1. Pull EDGAR filings if not already present
  2. Pick the most discriminative filing (S-4 > S-1 > 10-K)
  3. Run llm_pipeline.analyze_company on it
  4. Aggregate to a per-company severity score
  5. Compare to ground-truth outcome label

Output: data/_cohort/llm_cohort_results.json + printed confusion matrix.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from . import edgar
from .llm_pipeline import analyze_company
from .scoring import Severity


HERE = Path(__file__).parent
DATA = HERE / "data"
COHORT_OUT = DATA / "_cohort"
COHORT_OUT.mkdir(exist_ok=True, parents=True)


# Hint CIKs the LLM can use for counterparty queries.
COMMON_CIKS = {
    "AMZN (Amazon)":            "0001018724",
    "AB InBev (Anheuser-Busch)": "0001668717",
    "GM (General Motors)":      "0001467858",
    "Ford":                     "0000037996",
    "Magna International":      "0001072627",
    "TotalEnergies":            "0000879764",
    "Republic Services":        "0001060391",
    "US Xpress":                "0001740822",
    "UPS":                      "0001090727",
    "Hertz":                    "0000047129",
    "Walmart":                  "0000104169",
    "Volkswagen ADR":           "0001628280",
}

# (ticker, cik, cutoff, factory_state, outcome, outcome_detail, priority_forms)
# Priority forms ordered by preference for the LLM analysis input.
COHORT = [
    ("nkla",  "0001731289", "2020-09-09", "AZ", "FRAUD",    "Hindenburg 2020-09; Trevor Milton convicted",
        {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("ride",  "0001759546", "2021-03-11", "OH", "FRAUD",    "Hindenburg 2021-03; bankrupt 2023; SEC enforcement",
        {"S-4", "S-1", "S-1/A", "DEFM14A", "424B4", "10-K"}),
    ("hyzn",  "0001716583", "2022-01-15", "NY", "FRAUD",    "Blue Orca 2021-09; SEC charges 2024; bankrupt 2024",
        {"S-4", "S-1", "S-1/A", "10-K", "424B4"}),
    ("muln",  "0001499961", "2022-05-15", "CA", "FRAUD",    "Hindenburg 2023-04",
        {"S-1", "S-1/A", "10-K", "S-4", "424B4"}),

    ("fsr",   "0001720990", "2021-04-30", "CA", "BANKRUPT", "Bankruptcy 2024-06",
        {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("goev",  "0001750153", "2021-06-30", "OK", "BANKRUPT", "Bankruptcy 2025-01",
        {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("arvl",  "0001835059", "2021-09-30", "NC", "BANKRUPT", "Bankruptcy 2024-02",
        {"F-4", "F-1", "20-F", "S-4", "S-1"}),
    ("lev",   "0001834974", "2021-11-30", "IL", "BANKRUPT", "Bankruptcy 2024-12",
        {"F-4", "F-1", "20-F", "S-4", "S-1"}),
    ("ptra",  "0001820630", "2021-12-31", "CA", "BANKRUPT", "Bankruptcy 2023-08",
        {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("ffie",  "0001805521", "2022-01-30", "CA", "BANKRUPT", "Penny stock; near-bankruptcy",
        {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),

    ("rivn",  "0001874178", "2022-04-30", "IL", "ALIVE",    "Producing R1T/R1S/EDV at scale",
        {"S-1", "S-1/A", "424B4", "10-K"}),
    ("lcid",  "0001811210", "2022-03-15", "AZ", "ALIVE",    "Producing Air; PIF backing",
        {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("chpt",  "0001777393", "2021-08-30", "CA", "ALIVE",    "Charging network operating",
        {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("evgo",  "0001821159", "2022-01-31", "CA", "ALIVE",    "Charging network operating",
        {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("qs",    "0001811414", "2021-05-31", "CA", "ALIVE",    "Solid-state battery R&D; survived Scorpion 2021 short report",
        {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
]


SEV_WEIGHT = {
    "RED_FLAG_NEGATIVE": 4.0,
    "SEVERE_UNDERDELIVERY": 3.0,
    "MODERATE_UNDERDELIVERY": 1.5,
    "UNVERIFIABLE": 0.0,
    "PASS": 0.0,
}


def ensure_filings_pulled(ticker: str, cik: str, cutoff: str, priority_forms: set) -> Path:
    """Pull EDGAR filings if not present. Return path to the data dir."""
    out_dir = DATA / ticker
    if not (out_dir / "filings_index.json").exists():
        edgar.pull(cik=cik, cutoff_date=cutoff,
                   priority_forms=priority_forms, out_dir=out_dir)
    return out_dir


def pick_filing(out_dir: Path, priority_forms_ordered: list[str]) -> Path | None:
    """Pick the most discriminative filing.

    Walk priority_forms_ordered. For each form, look at all filings of that
    form type that are >50KB. Prefer the NEWEST one (by filing_date from
    filings_index.json) — important for SPACs where the early SPAC IPO docs
    are larger but pre-merger and contain only SPAC boilerplate, while the
    smaller post-merger filings contain the operating company's claims.
    """
    filings_dir = out_dir / "filings"
    if not filings_dir.exists():
        return None
    # Build accession -> filing_date map
    filing_date: dict[str, str] = {}
    idx_path = out_dir / "filings_index.json"
    if idx_path.exists():
        try:
            for r in json.loads(idx_path.read_text()):
                filing_date[r["accession"]] = r.get("filing_date", "")
        except Exception:
            pass

    def date_for(p: Path) -> str:
        # Filename: "<accession>_<FORM>.txt"; accession is everything before the first "_"
        acc = p.name.split("_", 1)[0]
        return filing_date.get(acc, "")

    all_filings = sorted(filings_dir.glob("*.txt"))
    for form in priority_forms_ordered:
        form_safe = form.replace("/", "_").replace(" ", "_")
        candidates = [p for p in all_filings
                      if f"_{form_safe}.txt" in p.name and p.stat().st_size > 50_000]
        if candidates:
            return sorted(candidates, key=date_for, reverse=True)[0]
    if all_filings:
        return sorted(all_filings, key=lambda p: p.stat().st_size, reverse=True)[0]
    return None


def run_one(ticker: str, cik: str, cutoff: str, state: str, outcome: str,
            detail: str, priority_forms: set) -> dict:
    print(f"\n{'='*80}\n=== {ticker.upper()} (outcome={outcome}, cutoff={cutoff}) ===\n{'='*80}",
          file=sys.stderr)

    # Pull filings if needed
    out_dir = ensure_filings_pulled(ticker, cik, cutoff, priority_forms)

    # Pick the most discriminative filing. Order by likelihood of containing
    # forward-looking BUSINESS claims about the operating company:
    # - DEFM14A / S-4 / F-4: deSPAC merger docs disclosing target's claims
    # - S-1 / F-1 / S-1/A / 424B4: IPO prospectus (target's first claims to public)
    # - 10-K / 20-F: annual reports (post-deSPAC, mix of historical + forward)
    # SPAC IPO S-1s are usually 100-200 KB of boilerplate; we filter on size.
    priority_ordered = ["DEFM14A", "S-4", "F-4", "S-1", "S-1/A", "F-1", "424B4", "10-K", "20-F"]
    filing_path = pick_filing(out_dir, priority_ordered)
    if filing_path is None:
        return {"ticker": ticker, "outcome": outcome, "detail": detail, "error": "no filing found"}

    print(f"  filing: {filing_path.name} ({filing_path.stat().st_size//1024} KB)", file=sys.stderr)
    text = filing_path.read_text(errors="ignore")

    t0 = time.time()
    try:
        result = analyze_company(
            ticker=ticker.upper(),
            cutoff_date=cutoff,
            filing_text=text,
            hint_ciks=COMMON_CIKS,
            out_dir=DATA / f"{ticker}_llm",
            max_workers=6,
        )
    except Exception as e:
        return {"ticker": ticker, "outcome": outcome, "detail": detail,
                "error": f"pipeline_failed: {e}"}
    elapsed = time.time() - t0

    # Aggregate severity
    counts: dict[str, int] = {}
    score = 0.0
    for f in result["findings"]:
        sev = f["severity"]
        counts[sev] = counts.get(sev, 0) + 1
        score += SEV_WEIGHT.get(sev, 0)
    n_claims = result["n_claims"]
    return {
        "ticker": ticker,
        "outcome": outcome,
        "detail": detail,
        "filing": filing_path.name,
        "n_claims": n_claims,
        "n_contradicted": result["n_contradicted"],
        "severity_score": round(score, 1),
        "score_per_claim": round(score / n_claims, 2) if n_claims else 0.0,
        "counts": counts,
        "elapsed_sec": round(elapsed, 1),
    }


def confusion_matrix(rows: list[dict], threshold: float, label: str,
                     positive_set: set) -> None:
    valid = [r for r in rows if "error" not in r]
    tp = sum(1 for r in valid if r["score_per_claim"] >= threshold and r["outcome"] in positive_set)
    fp = sum(1 for r in valid if r["score_per_claim"] >= threshold and r["outcome"] not in positive_set)
    tn = sum(1 for r in valid if r["score_per_claim"] < threshold and r["outcome"] not in positive_set)
    fn = sum(1 for r in valid if r["score_per_claim"] < threshold and r["outcome"] in positive_set)
    n = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    print(f"  threshold={threshold:.1f}/claim  {label}:")
    print(f"    TP={tp} FP={fp} TN={tn} FN={fn}  (n={n})")
    print(f"    Precision={precision:.0%}  Recall={recall:.0%}  Specificity={specificity:.0%}")


def main() -> None:
    rows = []
    for entry in COHORT:
        rows.append(run_one(*entry))

    # Persist
    (COHORT_OUT / "llm_cohort_results.json").write_text(json.dumps(rows, indent=2, default=str))

    # Print sorted table
    print("\n" + "=" * 110)
    print(f"{'Ticker':<7} {'Outcome':<9} {'Claims':<7} {'Contra':<7} {'Score':<7} {'/claim':<7} {'Time(s)':<8} {'Counts'}")
    print("-" * 110)
    sorted_rows = sorted(rows, key=lambda r: -r.get("score_per_claim", 0))
    for r in sorted_rows:
        if "error" in r:
            print(f"{r['ticker']:<7} {r['outcome']:<9} ERROR: {r['error']}")
            continue
        cstr = ", ".join(f"{k.split('_')[0][:4]}={v}" for k, v in sorted(r["counts"].items()))
        print(f"{r['ticker'].upper():<7} {r['outcome']:<9} {r['n_claims']:<7} "
              f"{r['n_contradicted']:<7} {r['severity_score']:<7} {r['score_per_claim']:<7} "
              f"{r['elapsed_sec']:<8} {cstr}")
    print("=" * 110)

    print("\nConfusion matrices:")
    for threshold in [0.5, 1.0, 1.5, 2.0]:
        print()
        confusion_matrix(rows, threshold, "Strict (FRAUD only)", {"FRAUD"})
        confusion_matrix(rows, threshold, "Loose (FRAUD+BANKRUPT)", {"FRAUD", "BANKRUPT"})


if __name__ == "__main__":
    main()
