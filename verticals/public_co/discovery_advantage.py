"""
Discovery_advantage scoring for forward-bet emission gating.

Motivation
----------
The framework's Truth_signal (R - f(M) divergence) tells us whether a
company's filings diverge from observable reality. It does NOT tell us
whether the bear case is *novel* — already-crowded shorts (high SI,
existing short-seller reports, high analyst coverage) are real signals
with no extractable alpha. The defense-tech cohort flagged this
explicitly: RCAT 20% short float and ONDS 33% short float scored high
on Truth_signal but the bears already found them; AIRO at 10.88% short
float was the genuinely novel discovery.

This module adds the second-pass: compute per-ticker discovery_advantage
from short interest + institutional ownership + sell-side coverage. The
shared forward_bet_emission.py gates emission on (composite >= threshold)
AND (discovery_advantage_tier IN {HIGH, MED}).

Source
------
finviz.com publishes free per-ticker quote pages with a stable HTML
snapshot table containing Short Float, Short Ratio, Inst Own, Recom
(consensus analyst recommendation 1-5), Avg Volume, Market Cap, Price.
Rate-limited but adequate for cohort-scale runs (5 names per cohort).

Tiering
-------
  HIGH (novel)    — short_float < 10% AND (inst_own < 60% OR no_analyst_rec)
  MED  (some left) — short_float < 20%
  LOW  (crowded)  — short_float >= 20% OR (inst_own > 80% AND analyst_rec)
  UNKNOWN         — finviz didn't return parseable data
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

HERE = Path(__file__).parent
CACHE = HERE / "data" / "_discovery_advantage_cache"


def _parse_pct(v: str) -> float | None:
    """'10.88%' -> 0.1088; '-' -> None."""
    v = (v or "").strip()
    if not v or v == "-":
        return None
    m = re.match(r"-?[\d.]+", v)
    if not m:
        return None
    try:
        return float(m.group()) / 100.0
    except ValueError:
        return None


def _parse_float(v: str) -> float | None:
    v = (v or "").strip()
    if not v or v == "-":
        return None
    m = re.match(r"-?[\d.]+", v)
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


_SUFFIX_MULT = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}


def _parse_magnitude(v: str) -> float | None:
    """Parse strings like '1.05B', '780.00M', '25.00K'. Returns raw number."""
    v = (v or "").strip().replace(",", "")
    if not v or v == "-":
        return None
    m = re.match(r"^(-?[\d.]+)\s*([KMBT]?)", v)
    if not m:
        return None
    try:
        num = float(m.group(1))
    except ValueError:
        return None
    mult = _SUFFIX_MULT.get(m.group(2), 1.0)
    return num * mult


def fetch_finviz(ticker: str) -> dict | None:
    """Scrape finviz.com/quote?t={TK} key-stats table. Returns parsed dict or None."""
    url = f"https://finviz.com/quote?t={ticker.upper()}"
    try:
        with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as c:
            r = c.get(url)
            if r.status_code != 200:
                return None
            html = r.text
    except httpx.HTTPError:
        return None

    # finviz snapshot table: alternating <div class="snapshot-td-label">LABEL</div>
    # and <div class="snapshot-td-content">VALUE</div> blocks. Capture both, then
    # zip adjacent label/content pairs.
    label_re = re.compile(r'<div class="snapshot-td-label[^"]*">(.*?)</div>', re.DOTALL)
    content_re = re.compile(r'<div class="snapshot-td-content[^"]*">(.*?)</div>', re.DOTALL)

    labels   = [re.sub(r"<[^>]+>", "", l).strip() for l in label_re.findall(html)]
    contents = [re.sub(r"<[^>]+>", "", c).strip() for c in content_re.findall(html)]

    if not labels or not contents:
        return None

    raw: dict[str, str] = {}
    for label, value in zip(labels, contents):
        if label and value:
            raw[label] = value

    return {
        "ticker":             ticker.upper(),
        "price":              _parse_float(raw.get("Price")),
        "market_cap":         _parse_magnitude(raw.get("Market Cap")),
        "market_cap_str":     raw.get("Market Cap"),
        "avg_volume":         _parse_magnitude(raw.get("Avg Volume")),
        "avg_volume_str":     raw.get("Avg Volume"),
        "beta":               _parse_float(raw.get("Beta")),
        "short_float_pct":    _parse_pct(raw.get("Short Float")),
        "short_ratio":        _parse_float(raw.get("Short Ratio")),
        "inst_own_pct":       _parse_pct(raw.get("Inst Own")),
        "inst_trans_pct":     _parse_pct(raw.get("Inst Trans")),
        "recom":              _parse_float(raw.get("Recom")),
        "perf_year":          _parse_pct(raw.get("Perf Year")),
        "raw":                raw,
    }


def compute_discovery_advantage(ticker: str, *, cache: bool = True) -> dict:
    """Return {tier, short_float_pct, inst_own_pct, recom, reasons[], source}."""
    cache_path = CACHE / f"{ticker.upper()}.json"
    if cache and cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except json.JSONDecodeError:
            pass

    data = fetch_finviz(ticker)
    if not data:
        result = {
            "ticker": ticker.upper(),
            "tier": "UNKNOWN",
            "short_float_pct": None,
            "inst_own_pct": None,
            "recom": None,
            "reasons": ["finviz fetch failed"],
            "source": "finviz.com/quote.ashx (unreachable)",
        }
    else:
        sf  = data.get("short_float_pct")
        io  = data.get("inst_own_pct")
        rec = data.get("recom")

        reasons: list[str] = []
        if sf is None and io is None and rec is None:
            tier = "UNKNOWN"
            reasons.append("no parseable short_float / inst_own / recom")
        elif sf is not None and sf >= 0.20:
            tier = "LOW"
            reasons.append(f"short_float {sf*100:.1f}% >= 20% (crowded short)")
        elif io is not None and io >= 0.80 and rec is not None:
            tier = "LOW"
            reasons.append(f"inst_own {io*100:.0f}% + analyst coverage (well-followed)")
        elif sf is not None and sf < 0.10 and (io is None or io < 0.60 or rec is None):
            tier = "HIGH"
            if sf < 0.10:
                reasons.append(f"short_float {sf*100:.2f}% < 10% (under-shorted)")
            if io is not None and io < 0.60:
                reasons.append(f"inst_own {io*100:.0f}% < 60% (lightly held)")
            if rec is None:
                reasons.append("no analyst coverage")
        elif sf is not None and sf < 0.20:
            tier = "MED"
            reasons.append(f"short_float {sf*100:.1f}% in [10, 20) (some discovery)")
        else:
            tier = "MED"
            reasons.append("insufficient data for HIGH; default MED")

        result = {
            "ticker":          data["ticker"],
            "tier":            tier,
            "short_float_pct": sf,
            "inst_own_pct":    io,
            "recom":           rec,
            "short_ratio":     data.get("short_ratio"),
            "price":           data.get("price"),
            "perf_year":       data.get("perf_year"),
            "beta":            data.get("beta"),
            "market_cap":      data.get("market_cap"),
            "avg_volume":      data.get("avg_volume"),
            "reasons":         reasons,
            "source":          "finviz.com/quote.ashx",
        }

    if cache:
        CACHE.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(result, indent=2))
    return result


def main():
    """Usage: python3 -m verticals.public_co.discovery_advantage TK1 [TK2 ...]"""
    if len(sys.argv) < 2:
        print("usage: python3 -m verticals.public_co.discovery_advantage TK1 [TK2 ...]", file=sys.stderr)
        sys.exit(2)
    tickers = sys.argv[1:]
    for tk in tickers:
        r = compute_discovery_advantage(tk, cache=True)
        sf = r.get("short_float_pct")
        io = r.get("inst_own_pct")
        sf_s = f"{sf*100:.2f}%" if sf is not None else "?"
        io_s = f"{io*100:.0f}%" if io is not None else "?"
        print(f"{r['ticker']:>6}  tier={r['tier']:<7}  short_float={sf_s:>7}  inst_own={io_s:>5}  recom={r.get('recom')}  reasons: {'; '.join(r['reasons'])}")
        time.sleep(0.4)


if __name__ == "__main__":
    main()
