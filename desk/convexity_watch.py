"""convexity_watch — monitors the personal convexity bucket + watchlist for SEPTEMBER prep.

Status = PREPARE, not deploy (the incoming cash tranche is the current convexity;
the bucket deploys AT September). So this watcher's job is READINESS, not entry
triggers: track each name's price + 52-week position (what's cheap to accumulate
in Sept), flag any thesis-integrity break (a name that stops being convex gets
dropped BEFORE Sept), and keep the watchlist visible.

    python3 -m desk.convexity_watch        # registered weekly
READ-ONLY.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "desk" / "data" / "convexity_bucket.json"


def main():
    cfg = json.loads(CFG.read_text())
    names = list(cfg.get("core", {})) + list(cfg.get("satellite", {}))
    watch_extra = ["WPM", "FNV", "AWK", "WTRG", "OPXS"]
    allnm = list(dict.fromkeys(names + watch_extra))
    import yfinance as yf
    print(f"[convexity_watch] PREPARE mode (deploy at September) — {len(allnm)} names\n")
    rows = []
    for t in allnm:
        try:
            h = yf.Ticker(t).history(period="1y")["Close"]
            if len(h) < 2:
                continue
            px, hi, lo = float(h.iloc[-1]), float(h.max()), float(h.min())
            pos = (px - lo) / (hi - lo) * 100 if hi > lo else 50
            rows.append((t, px, pos, hi, lo))
        except Exception:
            pass
    rows.sort(key=lambda r: r[2])  # cheapest-in-range first
    for t, px, pos, hi, lo in rows:
        tier = "core" if t in cfg.get("core", {}) else ("sat" if t in cfg.get("satellite", {}) else "watch")
        zone = "BUY-ZONE (lower third)" if pos < 33 else ("mid" if pos < 66 else "near highs")
        print(f"  {t:6s} [{tier:5s}] ${px:8.2f}  {pos:3.0f}% of 52w range  {zone}")
    print("\n  For Sept accumulation: prefer names in the lower third of their range.")
    print("  Thesis-integrity: re-court WPM/FNV; watch CWCO manufacturing lumpiness; re-run backtest on post-M&A RGLD/VOXR.")


if __name__ == "__main__":
    main()
