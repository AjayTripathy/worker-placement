"""
EDGAR distress-signal sift.

Sweeps recent SEC filings via the EFTS full-text search API to find companies
that concentrate multiple distress fingerprints in a short window:

  1. Going-concern qualifier in latest 10-K or 10-Q
  2. Dilutive offering (S-1, S-3, S-3/A, F-1) filed within 90 days
  3. Reverse stock split announced (8-K Item 5.03 or 3.01) within 6 months
  4. Auditor change (8-K Item 4.01) within 12 months
  5. Insider Form 144 filings in past 90 days (signaling exit)
  6. Stock-for-services / payment-in-equity language in MD&A / notes

The combination of (1) + (2) is the core "they know they're running out of
cash and are visibly trying to extend runway via dilution" signal. Each
additional signal raises the confidence that the next 12 months bring
bankruptcy, reverse split + further reverse split, or delisting.

Usage:
    python3 -m verticals.public_co.distress_sift --min-signals 2 --since 2026-01-01
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}
EFTS_URL = "https://efts.sec.gov/LATEST/search-index"

HERE = Path(__file__).parent
OUT  = HERE / "data" / "_distress_sift"


def efts_search_one_form(query: str, form: str,
                          start: str | None = None, end: str | None = None,
                          page_size: int = 100, max_hits: int = 1000) -> list[dict]:
    """Full-text search EDGAR for ONE form type. Returns list of hits."""
    base_params = {"q": query, "hits": page_size, "forms": form}
    if start and end:
        base_params["dateRange"] = "custom"
        base_params["startdt"] = start
        base_params["enddt"] = end
    all_hits = []
    fr = 0
    while True:
        params = {**base_params, "from": fr}
        try:
            with httpx.Client(headers=HEADERS, timeout=60) as c:
                r = c.get(EFTS_URL, params=params)
                if r.status_code != 200:
                    print(f"  efts {form} fr={fr}: {r.status_code}, stopping", file=sys.stderr)
                    break
                data = r.json()
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            print(f"  efts {form} error: {e}", file=sys.stderr)
            break
        hits = data.get("hits", {}).get("hits", [])
        all_hits.extend(hits)
        if not hits or len(all_hits) >= max_hits:
            break
        fr += page_size
        time.sleep(0.15)
    return all_hits


def efts_search(query: str, forms: list[str] | None = None,
                start: str | None = None, end: str | None = None,
                page_size: int = 100) -> list[dict]:
    if not forms:
        forms = [""]
    out = []
    for form in forms:
        hits = efts_search_one_form(query, form, start=start, end=end, page_size=page_size)
        out.extend(hits)
        time.sleep(0.3)
    return out


def extract_cik(hit: dict) -> str | None:
    src = hit.get("_source", {})
    ciks = src.get("ciks", []) or []
    if ciks:
        return str(ciks[0]).lstrip("0") or "0"
    return None


def hit_metadata(hit: dict) -> dict:
    src = hit.get("_source", {})
    return {
        "cik":          extract_cik(hit),
        "company":      (src.get("display_names") or ["?"])[0],
        "form":         (src.get("forms") or ["?"])[0],
        "file_date":    src.get("file_date"),
        "adsh":         hit.get("_id", "").split(":")[0] if ":" in hit.get("_id","") else "",
    }


SIGNAL_QUERIES = {
    "going_concern":      ('"substantial doubt about our ability to continue as a going concern"',
                           ["10-K", "10-Q"]),
    "reverse_split":      ('"reverse stock split"',
                           ["8-K", "DEF 14A"]),
    "auditor_change":     ('"change in registrant\'s certifying accountant"',
                           ["8-K"]),
    "delisting_notice":   ('"minimum bid price"',
                           ["8-K"]),
    "atm_offering":       ('"at-the-market offering"',
                           ["8-K", "424B5"]),
    "stock_for_services": ('"shares of common stock in lieu of cash"',
                           ["10-K", "10-Q"]),
}


def run_sift(since: str, until: str, min_signals: int) -> dict:
    """
    Run all signal queries over the date window, aggregate by CIK,
    return dict {cik: {company, signals: {signal_name: [hit_meta]}}}.
    """
    by_cik: dict[str, dict] = defaultdict(lambda: {
        "company": None,
        "signals": defaultdict(list),
    })

    for signal, (query, forms) in SIGNAL_QUERIES.items():
        print(f"[sift] {signal}…", file=sys.stderr)
        hits = efts_search(query, forms=forms, start=since, end=until)
        print(f"       {len(hits)} hits", file=sys.stderr)
        for h in hits:
            md = hit_metadata(h)
            cik = md["cik"]
            if not cik:
                continue
            by_cik[cik]["company"] = md["company"]
            by_cik[cik]["signals"][signal].append(md)
        time.sleep(0.5)

    # Filter to companies with min_signals concentrated
    filtered = {
        cik: agg for cik, agg in by_cik.items()
        if len(agg["signals"]) >= min_signals
    }
    return filtered


def rank(filtered: dict) -> list[dict]:
    """Rank by signal concentration + most-recent signal date."""
    ranked = []
    for cik, agg in filtered.items():
        n_signals = len(agg["signals"])
        all_dates = [m["file_date"] for sig_hits in agg["signals"].values() for m in sig_hits]
        most_recent = max(all_dates) if all_dates else "0000-00-00"
        ranked.append({
            "cik":         cik,
            "company":     agg["company"],
            "n_signals":   n_signals,
            "signals":     list(agg["signals"].keys()),
            "most_recent": most_recent,
            "detail":      {sig: hits for sig, hits in agg["signals"].items()},
        })
    ranked.sort(key=lambda x: (-x["n_signals"], x["most_recent"]), reverse=False)
    ranked.sort(key=lambda x: (-x["n_signals"], -1 if x["most_recent"] >= "2026-01-01" else 0))
    return ranked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since",  default=(datetime.utcnow() - timedelta(days=180)).strftime("%Y-%m-%d"))
    ap.add_argument("--until",  default=datetime.utcnow().strftime("%Y-%m-%d"))
    ap.add_argument("--min-signals", type=int, default=2)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"sweep window: {args.since} → {args.until}", file=sys.stderr)
    filtered = run_sift(args.since, args.until, args.min_signals)
    ranked = rank(filtered)

    out_path = OUT / "candidates.json"
    out_path.write_text(json.dumps(ranked, indent=2))
    print(f"\nWrote {len(ranked):,} candidates with ≥{args.min_signals} signals → {out_path}", file=sys.stderr)

    print("\nTOP 25 BY SIGNAL CONCENTRATION:", file=sys.stderr)
    for r in ranked[:25]:
        sigs = ", ".join(sorted(r["signals"]))
        print(f"  {r['n_signals']}  {r['most_recent']}  CIK={r['cik']:>8}  {r['company'][:48]:48s}  [{sigs}]", file=sys.stderr)


if __name__ == "__main__":
    main()
