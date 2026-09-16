"""fungibility_watch — dual-listing arbitrage spreads as a LIVE capital-controls gauge.

From the sovereign-barbell doc (2026-08-07): "you don't even need historical precedent to
look at exchange arbitrage." Dual-listed/fungible pairs arb to ~0 while capital moves
freely; a sustained spread beyond arb cost IS the market pricing capital controls /
de-globalization — a negative-latency regime dial, no prediction required.

Pairs: ADR (USD) vs ordinary (local ccy) with the ADR ratio. premium = ADR / (ord × fx ×
ratio) − 1. Thresholds set ABOVE fee/settlement noise (detector doctrine: narrow,
high-precision): |prem| ≥ 2% NOTABLE, ≥ 5% ALARM (prints CRITICAL FUNGIBILITY-BREAK —
picked up by the monitor rail). State: desk/data/fungibility_state.json.

  python3 -m desk.fungibility_watch          # daily cron
"""
from __future__ import annotations

import datetime
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "fungibility_state.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0"

# adr, ordinary, ord->USD fx quote (yahoo), ordinaries per ADR, ord quote divisor
PAIRS = [
    ("TSM",  "2330.TW", "TWDUSD=X", 5,   1),      # TSMC — the doc's own scenario
    ("SHEL", "SHEL.L",  "GBPUSD=X", 2,   100),    # LSE quotes in pence
    ("RIO",  "RIO.L",   "GBPUSD=X", 1,   100),
    ("UL",   "ULVR.L",  "GBPUSD=X", 1,   100),
    ("BP",   "BP.L",    "GBPUSD=X", 6,   100),
]
NOTABLE, ALARM = 0.02, 0.05


def _px(sym: str, tries: int = 2) -> float | None:
    for i in range(tries):
        time.sleep(1.5)                       # pace under yahoo's IP budget (429 lesson)
        r = subprocess.run(["curl", "-s", "--max-time", "15",
                            f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1d&interval=1d",
                            "-A", UA], capture_output=True, text=True)
        try:
            return json.loads(r.stdout)["chart"]["result"][0]["meta"]["regularMarketPrice"]
        except Exception:
            if "Too Many Requests" in r.stdout and i + 1 < tries:
                time.sleep(20)                # one backoff, then report NODATA loudly
    return None


def sweep() -> list[str]:
    out, rows = [], []
    fx_cache: dict[str, float | None] = {}
    for adr, ordy, fxq, ratio, div in PAIRS:
        a, o = _px(adr), _px(ordy)
        if fxq not in fx_cache:
            fx_cache[fxq] = _px(fxq)
        fx = fx_cache[fxq]
        if not all((a, o, fx)):
            out.append(f"FUNGIBILITY-NODATA: {adr}/{ordy} unpriced (a={a} o={o} fx={fx}) — "
                       f"gauge blind on this pair, not clean")
            continue
        prem = a / (o / div * fx * ratio) - 1
        rows.append({"pair": f"{adr}/{ordy}", "premium": round(prem, 4)})
        if abs(prem) >= ALARM:
            out.append(f"CRITICAL FUNGIBILITY-BREAK: {adr}/{ordy} premium {prem:+.2%} — "
                       f"beyond arb cost; capital-control pricing candidate. CAUSE-CHECK "
                       f"(corporate action? fx settlement? index event?) before regime call.")
        elif abs(prem) >= NOTABLE:
            out.append(f"FUNGIBILITY-NOTABLE: {adr}/{ordy} premium {prem:+.2%}")
    st = {"asof": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z", "pairs": rows}
    try:
        hist = json.loads(STATE.read_text()).get("history", [])
    except Exception:
        hist = []
    hist = (hist + [st])[-250:]
    STATE.write_text(json.dumps({"latest": st, "history": hist}, indent=1))
    return out


if __name__ == "__main__":
    flags = sweep()
    print(f"[fungibility_watch] {datetime.datetime.utcnow().isoformat(timespec='seconds')}Z "
          f"{len(flags)} flag(s)")
    for f in flags:
        print("  " + f)
