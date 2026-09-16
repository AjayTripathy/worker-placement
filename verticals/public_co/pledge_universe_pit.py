"""Point-in-time S&P 600 universe (survivors + REMOVED names) for the pledge backtest.

WHY THIS EXISTS
---------------
`pledge_backtest.cases_from_prevalence` seeds cases from TODAY's index constituents
only. So the clean (B) `call_low` crossing test came back N=1: a name only reaches
its lower margin-call edge after a ~64% drawdown, and the names that fell that far
and then got REMOVED from the index (mcap trough, bankruptcy) are exactly the cases
a survivor-only seed drops. The survivor that touched the low edge and bounced
(CALY) is all that's left — a sample structurally rigged toward bounces.

This module recovers the missing names. It reads the S&P 600 REMOVAL list
(`survivorship_2025_05/_unblinded/sp600_removals.json`, 83 names tagged by category
+ removal date) and screens each for an AFFIRMATIVE insider pledge AS OF the cutoff,
using the same narrow classifier as the prevalence study. Affirmative hits in the
DOWNSIDE-eligible categories (mcap trough / bankruptcy — not acquired/rebrand/
rebalance, which are cash-out or continuity, not forced-deleverage) are emitted as
`PledgeCase`s for the harness.

PRICE-DATA CAVEAT
-----------------
Names removed on MARKET-CAP TROUGH are usually still LISTED (they fell out of the
index, not off the exchange), so `pledge_margin_call.fetch_price_series` works on
them. Only BANKRUPTCY_OR_LIQUIDATION names are a true price hole; those are reported
separately and can't get a daily forward-return label from the Nasdaq feed.

Cutoff: 2025-05-15 (the survivorship_2025_05 backtest's PIT date).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Optional

from .edgar import _sec_ticker_to_cik_map, fetch_filing_text, list_filings
from .pledge_backtest import PledgeCase
from .pledge_prevalence_sample import _strip, classify

CUTOFF = "2025-05-15"
THROTTLE_S = 0.3   # polite spacing between per-name EDGAR hits (SEC fair-access)
# Categories where a pledge -> forced-deleverage downside is the relevant mechanism.
DOWNSIDE_CATEGORIES = {"MCAP_TROUGH_OR_INDEX_DOWNGRADE", "BANKRUPTCY_OR_LIQUIDATION"}
DEAD_CATEGORIES = {"BANKRUPTCY_OR_LIQUIDATION"}  # true price hole (delisted)

_BASE = Path(__file__).parent / "data"
REMOVALS = _BASE / "_backtest" / "survivorship_2025_05" / "_unblinded" / "sp600_removals.json"
OUT = _BASE / "_smallcap_universe" / "pledge_pit_universe.json"
_MAP_CACHE = _BASE / "_smallcap_universe" / "_sec_ticker_map.json"


def _warm_ticker_map(retries: int = 4) -> dict[str, str]:
    """SEC ticker->CIK map, robust to the 429s that batch EDGAR runs provoke:
    retry with backoff, persist to disk on success, fall back to the disk cache
    if the live fetch stays rate-limited."""
    for i in range(retries):
        try:
            m = _sec_ticker_to_cik_map()
            if len(m) >= 5000:
                _MAP_CACHE.parent.mkdir(parents=True, exist_ok=True)
                _MAP_CACHE.write_text(json.dumps(m))
                return m
        except Exception as e:
            print(f"  ticker-map fetch attempt {i+1}/{retries} failed: {e}",
                  file=sys.stderr)
        _sec_ticker_to_cik_map.cache_clear()
        time.sleep(5 * (i + 1))
    if _MAP_CACHE.exists():
        print("  falling back to on-disk ticker-map cache", file=sys.stderr)
        return json.loads(_MAP_CACHE.read_text())
    raise RuntimeError("could not obtain SEC ticker map (rate-limited, no cache)")


def _load_removals() -> list[dict]:
    d = json.loads(REMOVALS.read_text())
    return d if isinstance(d, list) else next(v for v in d.values() if isinstance(v, list))


def _proxies_asof(cik: str, cutoff: str) -> list[dict]:
    """DEF 14A rows filed on/before `cutoff`, newest first."""
    try:
        _, rows = list_filings(cik)
    except Exception:
        return []
    proxies = [r for r in rows
               if r["form"].startswith("DEF 14A") and r["filing_date"] <= cutoff]
    proxies.sort(key=lambda r: r["filing_date"], reverse=True)
    return proxies


def _classify_proxy(cik: str, row: dict) -> Optional[dict]:
    html = fetch_filing_text(cik, row["accession"], row["primary_document"])
    if not html:
        return None
    return classify(_strip(html))


def _earliest_affirmative_asof(cik: str, cutoff: str) -> Optional[dict]:
    """First (oldest) DEF 14A on/before cutoff that classifies AFFIRMATIVE_PLEDGE —
    the point-in-time first-disclosure date + share count for the case event."""
    proxies = sorted(_proxies_asof(cik, cutoff), key=lambda r: r["filing_date"])
    for r in proxies:
        c = _classify_proxy(cik, r)
        if c and c["category"] == "AFFIRMATIVE_PLEDGE":
            return {"date": r["filing_date"], "shares": c.get("shares_pledged"),
                    "evidence": c.get("evidence")}
    return None


def screen_removed(cutoff: str = CUTOFF, verbose: bool = True) -> list[dict]:
    """Latest-proxy-as-of-cutoff classify for every removed name (matches the
    prevalence study's methodology). Returns one record per name."""
    # Warm + verify the SEC ticker map ONCE up front. cik_for raises on a transient
    # map-fetch failure exactly as it does for a genuinely off-map ticker, so without
    # this guard a single rate-limited fetch silently NO_CIKs every name.
    tmap = _warm_ticker_map()
    out = []
    for rec in _load_removals():
        time.sleep(THROTTLE_S)
        tk, cat = rec["ticker"], rec["category"]
        cik = tmap.get(tk.upper().strip())
        if not cik:  # genuinely off the current SEC map (acquired/deregistered)
            if verbose:
                print(f"  {tk:6} [{cat:32}] OFF_MAP (acquired/delisted)", file=sys.stderr)
            out.append({**rec, "cik": None, "screen": "OFF_SEC_MAP"})
            continue
        proxies = _proxies_asof(cik, cutoff)
        if not proxies:
            out.append({**rec, "cik": cik, "screen": "NO_PROXY_ASOF"})
            continue
        c = _classify_proxy(cik, proxies[0])
        screen = c["category"] if c else "FETCH_FAIL"
        rowout = {**rec, "cik": cik, "proxy_date": proxies[0]["filing_date"],
                  "screen": screen,
                  "shares_pledged": (c or {}).get("shares_pledged"),
                  "n_prohibition": (c or {}).get("n_prohibition")}
        out.append(rowout)
        if verbose:
            flag = "  <-- AFFIRMATIVE" if screen == "AFFIRMATIVE_PLEDGE" else ""
            print(f"  {tk:6} [{cat:32}] {screen}{flag}", file=sys.stderr)
    return out


def screen_removed_file(removals_path: str, cache_path: str,
                        per_name_cutoff: bool = True, fallback_cutoff: str = CUTOFF,
                        verbose: bool = True) -> list[dict]:
    """Screen an arbitrary removals file for affirmative pledges, resumable.

    `per_name_cutoff` screens each name's latest DEF 14A as-of its OWN removal date
    (the correct PIT seam for a multi-year removal set — what was disclosed while the
    name was still in the index). Results are cached per-ticker to `cache_path` so a
    429 mid-run only loses the in-flight name; re-running resumes."""
    removals = json.loads(Path(removals_path).read_text())
    cache = json.loads(Path(cache_path).read_text()) if Path(cache_path).exists() else {}
    tmap = _warm_ticker_map()
    n_done = 0
    for rec in removals:
        key = f"{rec['ticker']}|{rec['date']}"
        if key in cache:
            continue
        time.sleep(THROTTLE_S)
        tk, cat = rec["ticker"], rec["category"]
        cutoff = rec["date"] if per_name_cutoff else fallback_cutoff
        cik = tmap.get(tk.upper().strip())
        if not cik:
            cache[key] = {**rec, "cik": None, "screen": "OFF_SEC_MAP"}
        else:
            proxies = _proxies_asof(cik, cutoff)
            if not proxies:
                cache[key] = {**rec, "cik": cik, "screen": "NO_PROXY_ASOF"}
            else:
                c = _classify_proxy(cik, proxies[0])
                screen = c["category"] if c else "FETCH_FAIL"
                cache[key] = {**rec, "cik": cik, "proxy_date": proxies[0]["filing_date"],
                              "screen": screen,
                              "shares_pledged": (c or {}).get("shares_pledged"),
                              "n_prohibition": (c or {}).get("n_prohibition")}
        n_done += 1
        if verbose:
            s = cache[key]["screen"]
            flag = "  <-- AFFIRMATIVE" if s == "AFFIRMATIVE_PLEDGE" else ""
            print(f"  {tk:6} [{cat:32}] {s}{flag}", file=sys.stderr)
        if n_done % 10 == 0:  # checkpoint periodically
            Path(cache_path).write_text(json.dumps(cache, indent=1))
    Path(cache_path).write_text(json.dumps(cache, indent=1))
    # preserve input order
    return [cache[f"{r['ticker']}|{r['date']}"] for r in removals
            if f"{r['ticker']}|{r['date']}" in cache]


def cases_from_removed(screen: list[dict], cutoff: str = CUTOFF) -> list[PledgeCase]:
    """For affirmative hits in DOWNSIDE categories, walk to the earliest affirmative
    proxy (PIT first-disclosure date) and build a PledgeCase."""
    cases = []
    for r in screen:
        if r.get("screen") != "AFFIRMATIVE_PLEDGE" or r["category"] not in DOWNSIDE_CATEGORIES:
            continue
        first = _earliest_affirmative_asof(r["cik"], cutoff)
        if not first or not first.get("shares"):
            print(f"  {r['ticker']}: affirmative but no datable share count, skip",
                  file=sys.stderr)
            continue
        cases.append(PledgeCase(
            ticker=r["ticker"], cik=r["cik"], insider_name="",
            pledge_observations=[{"date": first["date"],
                                  "pledged_shares": int(first["shares"]),
                                  "source": "DEF 14A", "exact_date": False}],
            disclosure_date=first["date"], approx_inception=True,
            note=(f"RECOVERED removed name [{r['category']}], removed {r['date']}; "
                  f"single-tranche, inception anchored to first-disclosure date")))
    return cases


def build(cutoff: str = CUTOFF, out: Optional[str] = None) -> dict:
    screen = screen_removed(cutoff)
    aff = [r for r in screen if r.get("screen") == "AFFIRMATIVE_PLEDGE"]
    cases = cases_from_removed(screen, cutoff)
    dead_aff = [r for r in aff if r["category"] in DEAD_CATEGORIES]
    result = {
        "cutoff": cutoff,
        "n_removed_screened": len(screen),
        "n_affirmative": len(aff),
        "n_affirmative_downside": sum(1 for r in aff if r["category"] in DOWNSIDE_CATEGORIES),
        "n_cases_emitted": len(cases),
        "affirmative_names": [
            {"ticker": r["ticker"], "category": r["category"], "removed": r["date"],
             "proxy_date": r.get("proxy_date"), "shares_pledged": r.get("shares_pledged"),
             "price_hole_if_delisted": r["category"] in DEAD_CATEGORIES}
            for r in aff],
        "dead_affirmative_price_hole": [r["ticker"] for r in dead_aff],
        "screen": screen,
        "cases": [c.__dict__ for c in cases],
    }
    out = out or str(OUT)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    r = build()
    print(json.dumps({k: v for k, v in r.items() if k not in ("screen", "cases")},
                     indent=2, default=str))
