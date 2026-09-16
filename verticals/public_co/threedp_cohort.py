"""3D printing OEM cohort — held-out blinded backtest.

Eight industrial 3D printing companies, uniform 2024-03-31 cutoff. Selected as
a HELD-OUT validation cohort: the analyst running extraction + scoring works
through a subagent that does NOT have access to outcome labels. Outcomes live
in a separate file (`_threedp_outcomes.py`) that is only consulted at
confusion-matrix time.

This module deliberately omits outcome labels from COHORT tuples to prevent
hindsight contamination in the input.json / scores.json generation step.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import edgar
from .analysis_types import CompanyAnalysis
from .providers import LocalProvider
from .unified_runner import analyze_company


HERE = Path(__file__).parent
DATA = HERE / "data"
LOCAL_ROOT = DATA / "_local"
COHORT_OUT = DATA / "_threedp_cohort"
COHORT_OUT.mkdir(exist_ok=True, parents=True)


# US-listed industrial / aerospace / defense / auto counterparties whose
# disclosure of an issuer's claimed orders/partnerships is testable.
COMMON_CIKS = {
    "Boeing (BA)":              "0000012927",
    "Lockheed Martin (LMT)":    "0000936468",
    "Raytheon Tech (RTX)":      "0000101829",
    "General Dynamics (GD)":    "0000040533",
    "Northrop Grumman (NOC)":   "0001133421",
    "General Electric (GE)":    "0000040545",
    "Honeywell (HON)":          "0000773840",
    "Caterpillar (CAT)":        "0000018230",
    "Ford (F)":                 "0000037996",
    "General Motors (GM)":      "0001467858",
    "BMW ADR":                  "0001074929",
    "Toyota Motor (TM ADR)":    "0001094517",
    "Stratasys (SSYS)":         "0001517396",
    "Nano Dimension (NNDM)":    "0001643303",
    "Materialise (MTLS)":       "0001091223",
}


# (ticker, cik, cutoff, region_hint, priority_forms)  — NO outcome label.
COHORT = [
    ("vld",  "0001825079", "2024-03-31", "CA",
        {"10-K", "10-Q", "8-K", "DEF 14A", "S-1"}),
    ("vjet", "0001582581", "2024-03-31", "DE-Germany",
        {"20-F", "6-K", "F-1"}),
    ("dm",   "0001754820", "2024-03-31", "MA",
        {"10-K", "10-Q", "8-K", "DEF 14A", "S-1"}),
    ("mkfg", "0001816613", "2024-03-31", "MA",
        {"10-K", "10-Q", "8-K", "DEF 14A", "S-1"}),
    ("ssys", "0001517396", "2024-03-31", "IL-Israel",
        {"20-F", "6-K", "F-1"}),
    ("mtls", "0001091223", "2024-03-31", "BE-Belgium",
        {"20-F", "6-K", "F-1"}),
    ("nndm", "0001643303", "2024-03-31", "IL-Israel",
        {"20-F", "6-K", "F-1"}),
    ("xmtr", "0001657573", "2024-03-31", "MD",
        {"10-K", "10-Q", "8-K", "S-1"}),
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


def confusion_matrix(rows, threshold: float, label: str, positive_set: set,
                     outcomes: dict) -> None:
    valid = [r for r in rows if r.findings_by_claim]
    def is_pos(r): return outcomes.get(r.ticker, ("?", ""))[0] in positive_set
    tp = sum(1 for r in valid if r.score_per_claim() >= threshold and is_pos(r))
    fp = sum(1 for r in valid if r.score_per_claim() >= threshold and not is_pos(r))
    tn = sum(1 for r in valid if r.score_per_claim() < threshold and not is_pos(r))
    fn = sum(1 for r in valid if r.score_per_claim() < threshold and is_pos(r))
    p = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    sp = tn / (tn + fp) if (tn + fp) else 0.0
    print(f"  thr={threshold:.1f}/claim {label}: TP={tp} FP={fp} TN={tn} FN={fn}  P={p:.0%} R={rec:.0%} Sp={sp:.0%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["local", "api"], default="local")
    ap.add_argument("--tickers", nargs="*")
    ap.add_argument("--stage", choices=["pull", "score"], default="score")
    ap.add_argument("--reveal-outcomes", action="store_true",
                    help="Load _threedp_outcomes.py and compute confusion matrix.")
    args = ap.parse_args()

    provider: object
    if args.provider == "local":
        provider = LocalProvider(LOCAL_ROOT)
    else:
        from .providers import ApiProvider
        provider = ApiProvider()

    priority_ordered = ["DEFM14A", "S-4", "F-4", "S-1", "S-1/A", "F-1",
                        "424B4", "10-K", "20-F", "10-Q"]

    rows: list[CompanyAnalysis] = []
    for ticker, cik, cutoff, _region, priority_forms in COHORT:
        if args.tickers and ticker not in args.tickers:
            continue
        out_dir = ensure_filings(ticker, cik, cutoff, priority_forms)
        if args.stage == "pull":
            continue
        filing = pick_filing(out_dir, priority_ordered)
        if filing is None:
            print(f"!! {ticker} no filing found", file=sys.stderr)
            continue
        text = filing.read_text(errors="ignore")
        try:
            analysis = analyze_company(
                ticker=ticker, cutoff_date=cutoff, filing_text=text,
                provider=provider, cik=cik, outcome=None,
                outcome_detail="", filing_name=filing.name,
                hint_ciks=COMMON_CIKS, out_dir=COHORT_OUT,
                max_workers=4,
            )
            rows.append(analysis)
        except FileNotFoundError as e:
            print(f"!! {ticker} skipped: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"!! {ticker} pipeline error: {e}", file=sys.stderr)
            continue

    if args.stage == "pull":
        return

    print()
    print("=" * 110)
    if args.reveal_outcomes:
        from ._threedp_outcomes import OUTCOMES
        for r in rows:
            outc, _ = OUTCOMES.get(r.ticker, ("?", ""))
            r.outcome = outc
        header_outcome = "Outcome (revealed)"
    else:
        header_outcome = "Outcome (BLIND)"

    print(f"{'Ticker':<7} {header_outcome:<22} {'Claims':<7} {'Contra':<7} {'Score':<7} {'/claim':<7} {'Counts'}")
    print("-" * 110)
    for r in sorted(rows, key=lambda x: -x.score_per_claim()):
        cstr = ", ".join(f"{k.split('_')[0][:4]}={v}" for k, v in sorted(r.severity_counts().items()))
        print(f"{r.ticker.upper():<7} {(r.outcome or '?'):<22} {len(r.claims):<7} "
              f"{r.n_contradicted():<7} {r.severity_score():<7.1f} "
              f"{r.score_per_claim():<7.2f} {cstr}")
    print("=" * 110)
    print(f"\nProvider: {provider.name}    Tickers: {len(rows)}")

    if args.reveal_outcomes:
        from ._threedp_outcomes import OUTCOMES
        for thr in [0.5, 1.0, 1.5]:
            for label, pos in [
                ("BANKRUPT only", {"BANKRUPT"}),
                ("Loose (BANKRUPT + DISTRESSED)",
                 {"BANKRUPT", "ACQUIRED_DISTRESSED", "DELISTED"}),
            ]:
                confusion_matrix(rows, thr, label, pos, OUTCOMES)


if __name__ == "__main__":
    main()
