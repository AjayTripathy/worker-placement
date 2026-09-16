"""Live (present-day) single-ticker diligence: progressive corpus + freshness guard.

The blinded backtest path (ripo_fetch_filings + ripo_subagent_prompt) deliberately
freezes the corpus at the IPO date and downloads ONLY prospectus forms -- correct
for a forward-looking backtest. A LIVE diligence (cutoff = today) must NOT reuse
that prospectus-only corpus: every post-IPO 10-K/10-Q/8-K/proxy that resolves a
disclosed risk would be missing, and the report would re-flag already-resolved
issues as active (the Caris going-concern bug).

This module is the live counterpart:
  - prepare_corpus(): pull the FULL filing series through the cutoff, including
    periodic + current reports, and write a chronological filing_timeline.json.
  - freshness_check(): refuse to silently run stale -- flag when a live-cutoff run
    has no recent periodic report on disk.
  - build_live_prompt(): a non-blinded, cross-series diligence prompt that reads
    the prospectus for the ORIGINAL claims and the later filings to RESOLVE them,
    emitting a per-claim resolution_trail.

Run:  python3 -m verticals.public_co.live_dd CAI                 # cutoff = today
      python3 -m verticals.public_co.live_dd CAI --cutoff 2026-05-29
      python3 -m verticals.public_co.live_dd CAI --cik 0002019410
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

from . import edgar

DATA = Path(__file__).parent / "data"

# Prospectus/registration families (the original-claim source) ...
PROSPECTUS_FORMS = {
    "S-1", "S-1/A", "F-1", "F-1/A",
    "424B1", "424B2", "424B3", "424B4", "424B5",
}
# ... plus the periodic + current + governance reports that RESOLVE disclosed
# risks over time. This is the set a live diligence must have on disk.
PERIODIC_FORMS = {
    "10-K", "10-K/A", "10-Q", "10-Q/A",
    "8-K", "8-K/A",
    "20-F", "40-F", "6-K",
    "DEF 14A", "DEFA14A",
}
LIVE_FORMS = PROSPECTUS_FORMS | PERIODIC_FORMS

# A cutoff within this many days of "today" is treated as a LIVE run (vs a
# historical/backtest cutoff), which is what triggers the freshness discipline.
LIVE_WINDOW_DAYS = 7
# A live corpus is stale if its newest periodic report (10-K/10-Q) is older than
# this many days before the cutoff -- companies file at least quarterly, so a gap
# this large means post-cutoff filings were never pulled.
STALE_PERIODIC_DAYS = 135


def _today() -> str:
    return _dt.date.today().isoformat()


def _parse(d: str) -> _dt.date:
    return _dt.date.fromisoformat(d)


def _index_path(out_dir: Path) -> Path:
    return out_dir / "filings_index.json"


def corpus_coverage(out_dir: Path) -> dict:
    """Read what is actually on disk and report the coverage window.

    Returns {newest_overall, newest_periodic, newest_periodic_form, n_index,
    downloaded_dates: {...}} or {} if no index. `newest_periodic` is the load-
    bearing field for the staleness guard: it is the date of the most recent
    10-K/10-Q/8-K/proxy whose TEXT is downloaded into filings/.
    """
    idx_p = _index_path(out_dir)
    if not idx_p.exists():
        return {}
    rows = json.loads(idx_p.read_text())
    by_acc = {r["accession"]: r for r in rows}
    filings_dir = out_dir / "filings"
    downloaded = {}
    if filings_dir.exists():
        for f in filings_dir.glob("*.txt"):
            acc = f.name.split("_")[0]
            r = by_acc.get(acc)
            if r:
                downloaded[acc] = r
    newest_overall = max((r["filing_date"] for r in rows), default=None)
    periodic = [r for r in downloaded.values() if r["form"] in PERIODIC_FORMS]
    periodic.sort(key=lambda r: r["filing_date"])
    newest_periodic = periodic[-1]["filing_date"] if periodic else None
    newest_periodic_form = periodic[-1]["form"] if periodic else None
    return {
        "newest_overall": newest_overall,
        "newest_periodic": newest_periodic,
        "newest_periodic_form": newest_periodic_form,
        "n_index": len(rows),
        "n_downloaded": len(downloaded),
    }


def freshness_check(out_dir: Path, cutoff: str) -> dict:
    """Decide whether the on-disk corpus is fresh enough for the given cutoff.

    A run is LIVE if cutoff is within LIVE_WINDOW_DAYS of today. A live corpus is
    STALE if it has no periodic report (10-K/10-Q/8-K/proxy) within
    STALE_PERIODIC_DAYS of the cutoff -- i.e. post-IPO filings were never pulled.
    Historical (backtest) cutoffs are never marked stale here.
    """
    cov = corpus_coverage(out_dir)
    cutoff_d = _parse(cutoff)
    is_live = (_dt.date.today() - cutoff_d).days <= LIVE_WINDOW_DAYS
    newest_periodic = cov.get("newest_periodic")
    gap_days = None
    if newest_periodic:
        gap_days = (cutoff_d - _parse(newest_periodic)).days
    stale = bool(
        is_live and (newest_periodic is None or (gap_days is not None and gap_days > STALE_PERIODIC_DAYS))
    )
    advice = ""
    if stale:
        if newest_periodic is None:
            advice = ("LIVE cutoff but NO periodic report (10-K/10-Q) on disk -- "
                      "corpus is prospectus-only. Run prepare_corpus() before diligencing.")
        else:
            advice = (f"LIVE cutoff but newest periodic report is {newest_periodic} "
                      f"({gap_days}d before cutoff > {STALE_PERIODIC_DAYS}d). "
                      "Refresh the corpus before diligencing.")
    return {
        "cutoff": cutoff,
        "is_live_cutoff": is_live,
        "newest_overall": cov.get("newest_overall"),
        "newest_periodic": newest_periodic,
        "newest_periodic_form": cov.get("newest_periodic_form"),
        "gap_days": gap_days,
        "stale": stale,
        "advice": advice,
    }


def write_timeline(out_dir: Path) -> Path:
    """Emit a chronological filing_timeline.json from the (already-written) index."""
    rows = json.loads(_index_path(out_dir).read_text())
    timeline = sorted(
        (
            {
                "filing_date": r["filing_date"],
                "form": r["form"],
                "accession": r["accession"],
                "report_date": r.get("report_date"),
                "primary_document": r.get("primary_document", ""),
                "downloaded": (out_dir / "filings" / f"{r['accession']}_{r['form'].replace('/', '_').replace(' ', '_')}.txt").exists(),
            }
            for r in rows
        ),
        key=lambda x: x["filing_date"],
    )
    p = out_dir / "filing_timeline.json"
    p.write_text(json.dumps(timeline, indent=2))
    return p


def prepare_corpus(ticker: str, *, cutoff: str | None = None,
                   cik: str | None = None) -> dict:
    """Pull the progressive live corpus for a ticker through `cutoff`.

    Resolves the CIK (SEC map, or the `cik` override), downloads LIVE_FORMS into
    data/<ticker>/filings, writes filing_timeline.json, and runs freshness_check.
    Returns the freshness report (already fresh after this call).
    """
    cutoff = cutoff or _today()
    cik = edgar.cik_for(ticker, override=cik)
    out_dir = DATA / ticker.lower()
    print(f"=== live corpus: {ticker} cik={cik} cutoff={cutoff} ===", file=sys.stderr)
    edgar.pull(cik, cutoff, LIVE_FORMS, out_dir)
    write_timeline(out_dir)
    fresh = freshness_check(out_dir, cutoff)
    cov = corpus_coverage(out_dir)
    print(f"  coverage: {cov.get('n_downloaded')} docs on disk, "
          f"newest periodic {cov.get('newest_periodic')} "
          f"({cov.get('newest_periodic_form')}), index through {cov.get('newest_overall')}",
          file=sys.stderr)
    if fresh["stale"]:
        print(f"  !! STALE: {fresh['advice']}", file=sys.stderr)
    else:
        print("  fresh: corpus covers the cutoff.", file=sys.stderr)
    return fresh


# --------------------------------------------------------------------------- #
# Live (non-blinded) cross-series diligence prompt.
# --------------------------------------------------------------------------- #
LIVE_PROMPT = """\
You are running a LIVE, present-day forensic-disclosure diligence on {ticker} as
of {cutoff}. This is NOT a blinded backtest: you MAY use current public registries,
WebSearch, and WebFetch, and you SHOULD read the company's full filing history
through the cutoff -- not just the IPO prospectus.

Ticker: {ticker}
Cutoff (= today): {cutoff}
Filings dir:   {filings_dir}
Filing timeline: {timeline_path}   (chronological; read this FIRST)

CORE DISCIPLINE -- read across the time series, do not freeze at the prospectus:
1. Read filing_timeline.json. Note the prospectus (424B4 / latest S-1/A or F-1/A)
   AND every later periodic/current report (10-K, 10-Q, 8-K, DEF 14A).
2. Extract the ORIGINAL claims (R) from the prospectus, as usual.
3. For EACH claim -- especially any solvency, liquidity, going-concern, debt-
   maturity, redemption, lock-up, or other DATE-STAMPED forward claim -- the
   authority M is the LATER filing the claim points to, NOT the prospectus's own
   forward-looking language. Ask: as of {cutoff}, what actually happened?
     - going-concern  -> the most recent 10-K audit opinion (is the substantial-
                         doubt language still there, or gone?)
     - debt trigger / maturity / redemption -> later 10-Q/10-K notes + 8-Ks
                         (repaid? refinanced? converted? extended?)
     - lock-up expiry / overhang -> Form 144 / Form 4 around the expiry date
     - ownership / pledge / control -> the latest DEF 14A beneficial-ownership table
4. SANITY RULE: if you are about to describe a dated event (a trigger, maturity,
   redemption, or lock-up) as "upcoming" or "near-term", confirm that date is
   AFTER {cutoff}. If it is in the past, you are reading a stale frame -- go find
   the filing that resolved it.

For each claim, in scores.json, add a `resolution_trail`: an ordered list of
  {{"date": "<YYYY-MM-DD>", "filing": "<form>", "status": "raised|unchanged|worsened|resolved",
    "note": "<what this filing showed about the issue>"}}
tracing the issue from the prospectus to its current state. The final `severity`
must reflect the issue's state AS OF {cutoff}, not at IPO.

Everything else (issuer_features, detector_dispatch, the R/f(M) claim structure,
the severity vocabulary) follows the standard public_co diligence contract.
"""


def build_live_prompt(ticker: str, cutoff: str | None = None) -> str:
    cutoff = cutoff or _today()
    out_dir = DATA / ticker.lower()
    return LIVE_PROMPT.format(
        ticker=ticker.upper(),
        cutoff=cutoff,
        filings_dir=str(out_dir / "filings") + "/",
        timeline_path=str(out_dir / "filing_timeline.json"),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare a live progressive corpus for a ticker.")
    ap.add_argument("ticker")
    ap.add_argument("--cutoff", default=None, help="ISO date; defaults to today.")
    ap.add_argument("--cik", default=None, help="10-digit CIK override for foreign/edge tickers.")
    ap.add_argument("--print-prompt", action="store_true", help="Also print the live diligence prompt.")
    args = ap.parse_args()
    fresh = prepare_corpus(args.ticker, cutoff=args.cutoff, cik=args.cik)
    print(json.dumps(fresh, indent=2))
    if args.print_prompt:
        print("\n" + "=" * 70 + "\n")
        print(build_live_prompt(args.ticker, args.cutoff))


if __name__ == "__main__":
    main()
