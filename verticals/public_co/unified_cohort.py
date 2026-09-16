"""Unified cohort runner — same code path for any Provider.

Usage:
    python -m verticals.public_co.unified_cohort --provider local
    python -m verticals.public_co.unified_cohort --provider api

The --provider flag swaps providers; everything else (cohort definition,
filing selection, evidence execution, aggregation, confusion matrix) is shared.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .analysis_types import CompanyAnalysis
from . import edgar
from .providers import ApiProvider, LocalProvider
from .unified_runner import analyze_company


HERE = Path(__file__).parent
DATA = HERE / "data"
LOCAL_ROOT = DATA / "_local"
COHORT_OUT = DATA / "_unified_cohort"
COHORT_OUT.mkdir(exist_ok=True, parents=True)


COMMON_CIKS = {
    "AMZN": "0001018724",
    "BUD": "0001668717",
    "GM": "0001467858",
    "Ford": "0000037996",
    "Magna": "0001072627",
    "TotalEnergies": "0000879764",
    "Republic Services": "0001060391",
    "US Xpress": "0001740822",
    "UPS": "0001090727",
    "Walmart": "0000104169",
    "Volkswagen ADR": "0001628280",
}

# (ticker, cik, cutoff, factory_state, outcome, detail, priority_forms_set)
COHORT = [
    ("nkla", "0001731289", "2020-09-09", "AZ", "FRAUD",    "Hindenburg 2020-09; Trevor Milton convicted",
     {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("ride", "0001759546", "2021-03-11", "OH", "FRAUD",    "Hindenburg 2021-03; bankrupt 2023; SEC enforcement",
     {"DEFM14A", "S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("hyzn", "0001716583", "2022-01-15", "NY", "FRAUD",    "Blue Orca 2021-09; SEC charges 2024; bankrupt 2024",
     {"DEFM14A", "S-4", "S-1", "S-1/A", "10-K", "424B4"}),
    ("muln", "0001499961", "2022-05-15", "CA", "FRAUD",    "Hindenburg 2023-04",
     {"S-1", "S-1/A", "10-K", "S-4", "424B4"}),
    ("fsr",  "0001720990", "2021-04-30", "CA", "BANKRUPT", "Bankruptcy 2024-06",
     {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("goev", "0001750153", "2021-06-30", "OK", "BANKRUPT", "Bankruptcy 2025-01",
     {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("arvl", "0001835059", "2021-09-30", "NC", "BANKRUPT", "Bankruptcy 2024-02",
     {"F-4", "F-1", "20-F", "S-4", "S-1"}),
    ("lev",  "0001834974", "2021-11-30", "IL", "BANKRUPT", "Bankruptcy 2024-12",
     {"F-4", "F-1", "20-F", "S-4", "S-1"}),
    ("ptra", "0001820630", "2021-12-31", "CA", "BANKRUPT", "Bankruptcy 2023-08",
     {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("ffie", "0001805521", "2022-01-30", "CA", "BANKRUPT", "Penny stock; near-bankruptcy",
     {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("rivn", "0001874178", "2022-04-30", "IL", "ALIVE",    "Producing R1T/R1S/EDV at scale",
     {"S-1", "S-1/A", "424B4", "10-K"}),
    ("lcid", "0001811210", "2022-03-15", "AZ", "ALIVE",    "Producing Air; PIF backing",
     {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("chpt", "0001777393", "2021-08-30", "CA", "ALIVE",    "Charging network operating",
     {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("evgo", "0001821159", "2022-01-31", "CA", "ALIVE",    "Charging network operating",
     {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
    ("qs",   "0001811414", "2021-05-31", "CA", "ALIVE",    "Survived Scorpion 2021 short report",
     {"S-4", "S-1", "S-1/A", "424B4", "10-K"}),
]


def ensure_filings(ticker: str, cik: str, cutoff: str, priority_forms: set) -> Path:
    out = DATA / ticker
    if not (out / "filings_index.json").exists():
        edgar.pull(cik=cik, cutoff_date=cutoff, priority_forms=priority_forms, out_dir=out)
    return out


def pick_filing(out_dir: Path, priority: list[str]) -> Path | None:
    filings_dir = out_dir / "filings"
    if not filings_dir.exists():
        return None
    fdate: dict[str, str] = {}
    idx = out_dir / "filings_index.json"
    if idx.exists():
        try:
            for r in json.loads(idx.read_text()):
                fdate[r["accession"]] = r.get("filing_date", "")
        except Exception:
            pass
    def date_for(p: Path) -> str:
        return fdate.get(p.name.split("_", 1)[0], "")
    available = sorted(filings_dir.glob("*.txt"))
    for form in priority:
        safe = form.replace("/", "_").replace(" ", "_")
        cands = [p for p in available if f"_{safe}.txt" in p.name and p.stat().st_size > 50_000]
        if cands:
            return sorted(cands, key=date_for, reverse=True)[0]
    return sorted(available, key=lambda p: p.stat().st_size, reverse=True)[0] if available else None


def confusion_matrix(rows: list[CompanyAnalysis], threshold: float, label: str,
                     positive_set: set) -> None:
    valid = [r for r in rows if r.findings_by_claim]
    tp = sum(1 for r in valid if r.score_per_claim() >= threshold and r.outcome in positive_set)
    fp = sum(1 for r in valid if r.score_per_claim() >= threshold and r.outcome not in positive_set)
    tn = sum(1 for r in valid if r.score_per_claim() < threshold and r.outcome not in positive_set)
    fn = sum(1 for r in valid if r.score_per_claim() < threshold and r.outcome in positive_set)
    n = tp + fp + tn + fn
    p = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    sp = tn / (tn + fp) if (tn + fp) else 0.0
    print(f"  thr={threshold:.1f}/claim {label}: TP={tp} FP={fp} TN={tn} FN={fn}  P={p:.0%} R={rec:.0%} Sp={sp:.0%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["local", "api"], default="local")
    ap.add_argument("--tickers", nargs="*", help="restrict to these tickers")
    args = ap.parse_args()

    if args.provider == "local":
        provider = LocalProvider(LOCAL_ROOT)
    else:
        provider = ApiProvider()

    priority_ordered = ["DEFM14A", "S-4", "F-4", "S-1", "S-1/A", "F-1", "424B4", "10-K", "20-F"]

    rows: list[CompanyAnalysis] = []
    for ticker, cik, cutoff, state, outcome, detail, priority_forms in COHORT:
        if args.tickers and ticker not in args.tickers:
            continue
        out_dir = ensure_filings(ticker, cik, cutoff, priority_forms)
        filing = pick_filing(out_dir, priority_ordered)
        if filing is None:
            print(f"!! {ticker} no filing found", file=sys.stderr)
            continue
        text = filing.read_text(errors="ignore")
        try:
            analysis = analyze_company(
                ticker=ticker, cutoff_date=cutoff, filing_text=text,
                provider=provider, cik=cik, outcome=outcome,
                outcome_detail=detail, filing_name=filing.name,
                hint_ciks=COMMON_CIKS, out_dir=COHORT_OUT,
                max_workers=6,
            )
            rows.append(analysis)
        except FileNotFoundError as e:
            print(f"!! {ticker} skipped (LocalProvider needs input.json): {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"!! {ticker} pipeline error: {e}", file=sys.stderr)
            continue

    # Print sorted table
    print()
    print("=" * 110)
    print(f"{'Ticker':<7} {'Outcome':<9} {'Claims':<7} {'Contra':<7} {'Score':<7} {'/claim':<7} {'Counts'}")
    print("-" * 110)
    for r in sorted(rows, key=lambda x: -x.score_per_claim()):
        cstr = ", ".join(f"{k.split('_')[0][:4]}={v}" for k, v in sorted(r.severity_counts().items()))
        print(f"{r.ticker.upper():<7} {r.outcome or '?':<9} {len(r.claims):<7} "
              f"{r.n_contradicted():<7} {r.severity_score():<7.1f} "
              f"{r.score_per_claim():<7.2f} {cstr}")
    print("=" * 110)
    print(f"\nProvider: {provider.name}    Tickers: {len(rows)}")
    for thr in [0.5, 1.0, 1.5]:
        for label, pos in [("Strict (FRAUD)", {"FRAUD"}),
                           ("Loose (FRAUD+BANKRUPT)", {"FRAUD", "BANKRUPT"})]:
            confusion_matrix(rows, thr, label, pos)


if __name__ == "__main__":
    main()
