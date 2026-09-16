"""usdc_supply_watch — instruments CRCL's court gate (2026-08-08 adjudication):
'starter only after 9/16 resolves AND USDC supply >= $72B for 3 consecutive weeks.'
A gate without a sensor is decoration (the FLAT-instrumentation doctrine).

Source: DeFiLlama public stablecoin API (no key). Tracks daily circulating USD supply,
maintains a rolling history, and computes the 21-consecutive-day streak >= $72B.
Routes through the monitor rail via state-file read (GATE-FIRED flag).

  python3 -m desk.usdc_supply_watch      # daily cron (rides the fungibility slot)
"""
from __future__ import annotations

import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "usdc_supply_state.json"
THRESHOLD = 72e9
STREAK_DAYS = 21


def read_supply() -> float | None:
    r = subprocess.run(["curl", "-s", "--max-time", "20",
                        "https://stablecoins.llama.fi/stablecoin/2"],  # id 2 = USDC
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        # newest point in the tokens series; circulating.peggedUSD
        pts = d.get("tokens") or []
        if pts:
            latest = pts[-1]
            return float(latest.get("circulating", {}).get("peggedUSD"))
        return float(d.get("circulating", {}).get("peggedUSD"))
    except Exception:
        return None


def run() -> list[str]:
    out = []
    supply = read_supply()
    today = datetime.date.today().isoformat()
    try:
        st = json.loads(STATE.read_text())
    except Exception:
        st = {"history": []}
    if supply is None:
        out.append("USDC-WATCH-NODATA: DeFiLlama unreachable — the CRCL gate sensor is blind today, not clean")
    else:
        hist = [h for h in st["history"] if h["date"] != today]
        hist.append({"date": today, "supply": supply})
        st["history"] = sorted(hist, key=lambda h: h["date"])[-90:]
        streak = 0
        for h in reversed(st["history"]):
            if h["supply"] >= THRESHOLD:
                streak += 1
            else:
                break
        st["streak_days"] = streak
        st["latest"] = {"date": today, "supply": supply, "above": supply >= THRESHOLD}
        if streak >= STREAK_DAYS:
            out.append(f"CRCL-GATE-FIRED: USDC supply ${supply/1e9:.1f}B — {streak} consecutive days >= $72B "
                       f"(court gate met; the 9/16-cluster condition must ALSO be resolved before any starter)")
        STATE.write_text(json.dumps(st, indent=1))
    return out


if __name__ == "__main__":
    flags = run()
    print(f"[usdc_supply_watch] {datetime.date.today().isoformat()} "
          f"{json.loads(STATE.read_text()).get('latest') if STATE.exists() else 'no state'}")
    for f in flags:
        print("  " + f)
