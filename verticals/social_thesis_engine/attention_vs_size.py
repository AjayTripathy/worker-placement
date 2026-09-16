"""attention_vs_size — rank social-surfaced names by ATTENTION RELATIVE TO SIZE.

Mega-caps dominate raw Reddit mention counts but that's not a dislocation. The edge is where
mentions are LARGE relative to a SMALL market cap — attention that can actually move the name, and
where overstatement/pump dynamics (the honesty detector's wheelhouse) live. Metric:
attention_per_bil = mentions / market_cap($B). Filter to small/micro caps, rank by that.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from verticals.buyside_dd.connectors import reddit_mentions


def _mcap(ticker: str):
    """Market cap via yfinance — fast_info first (cheap), .info fallback (fast_info.market_cap
    is frequently None). Guard against absurd values (yfinance data errors)."""
    import yfinance as yf
    mc = None
    try:
        fi = yf.Ticker(ticker).fast_info
        mc = fi.get("market_cap") if hasattr(fi, "get") else getattr(fi, "market_cap", None)
    except Exception:
        mc = None
    if not mc:
        try:
            mc = yf.Ticker(ticker).info.get("marketCap")
        except Exception:
            mc = None
    if not mc or mc <= 0 or mc > 5e12:   # > $5T = data error
        return None
    return float(mc)


def run(scan_top: int = 80, cap_ceiling_bil: float = 5.0, min_mentions: int = 8) -> dict:
    social = reddit_mentions.scan()
    items = list(social["tickers"].items())[:scan_top]
    print(f"[social] {social['n_tickers']} tickers; pulling market cap for top {len(items)} ...",
          flush=True)
    rows = []
    for t, a in items:
        if (a.get("mentions") or 0) < min_mentions:
            continue
        mc = _mcap(t)
        if mc is None:
            continue
        cap_bil = mc / 1e9
        rows.append({
            "ticker": t, "name": a.get("name"), "mentions": a["mentions"],
            "velocity": a.get("velocity"), "spike": a.get("spike"),
            "market_cap_bil": round(cap_bil, 3),
            "attn_per_bil": round(a["mentions"] / cap_bil, 1) if cap_bil else None,
        })
    small = [r for r in rows if r["market_cap_bil"] and r["market_cap_bil"] <= cap_ceiling_bil]
    small.sort(key=lambda r: r["attn_per_bil"], reverse=True)

    print(f"\n=== ATTENTION-EXCEEDS-SIZE (cap <= ${cap_ceiling_bil}B), ranked by mentions/$B ===")
    print(f"{'TICK':7}{'MENT':>5}{'VEL':>5}{'SPK':>4}{'CAP$B':>8}{'ATT/$B':>8}  NAME")
    for r in small[:25]:
        print(f"{r['ticker']:7}{r['mentions']:>5}{str(r['velocity']):>5}"
              f"{'▲' if r['spike'] else '':>4}{r['market_cap_bil']:>8.2f}{r['attn_per_bil']:>8.1f}"
              f"  {(r['name'] or '')[:26]}")
    out = {"asof": social["asof"], "cap_ceiling_bil": cap_ceiling_bil, "candidates": small}
    json.dump(out, open(HERE / "outputs" / "attention_vs_size.json", "w"), indent=2, default=str)
    print(f"\n[{len(small)} small/micro-cap names; wrote outputs/attention_vs_size.json]")
    return out


if __name__ == "__main__":
    ceil = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    run(cap_ceiling_bil=ceil)
