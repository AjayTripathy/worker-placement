"""Hormuz watch — the tanker sleeve's physical-data watcher.

The FRO/STNG/LPG drip sleeve carries a shared triple-kill (7d-avg transits
>40/day AND AWRP <0.4% AND TD3C <$60k, same week) and the FRO|2026-08-31 pack
adjudicates on the same series (7d avg / 84-day baseline >=50% on >=5 of 7).
Until now NOTHING polled the physical data — the kill was a sentence in a pack.

Data: IMF PortWatch daily chokepoint transits (free ArcGIS feed, ~5-day lag).
Alerts (macOS + ntfy + Gmail via the sentinel plumbing), each once per arming:
  - KILL-LEG-1 ARMED: 7d-avg total transits > 40/day  -> manually verify AWRP
    + TD3C before acting (the other two legs have no free feed)
  - PACK EARLY-WARNING: >=50% of the 84/day baseline on >=5 of trailing 7 days
    (the Aug-31 HIT condition printing early)
  - DATA STALE: feed >8 days old (silent-failure guard)

Runs from the gauntlet sentinel (launchd 6:15 + 7:45 weekdays) and by hand:
    python3 -m desk.hormuz_watch [--dry]
READ-ONLY: notifies only; orders are never touched.
"""
from __future__ import annotations

import datetime
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "hormuz_watch_state.json"
BASELINE = 84.0          # pre-closure Jan-2026 total transits/day (the pack's denominator)
KILL_LEG1 = 40.0         # 7d-avg total transits/day
PACK_RATIO = 0.50        # Aug-31 pack HIT bar

FEED = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
        "Daily_Chokepoints_Data/FeatureServer/0/query")


def _series(days: int = 14) -> list[tuple[str, int]]:
    q = urllib.parse.urlencode({
        "where": "portname='Strait of Hormuz'",
        "outFields": "date,n_total",
        "orderByFields": "date DESC",
        "resultRecordCount": days,
        "f": "json",
    })
    with urllib.request.urlopen(f"{FEED}?{q}", timeout=30) as r:
        js = json.load(r)
    rows = [(f["attributes"]["date"], int(f["attributes"]["n_total"]))
            for f in js.get("features", [])]
    return sorted(rows)          # ascending by date


def main(dry: bool = False) -> dict:
    state = json.load(open(STATE)) if STATE.exists() else {}
    rows = _series()
    out = {"ok": bool(rows)}
    fired = []
    if not rows:
        fired.append("HORMUZ WATCH: PortWatch feed returned no data — verify the ArcGIS endpoint")
    else:
        last_date, _ = rows[-1]
        lag = (datetime.date.today() - datetime.date.fromisoformat(last_date)).days
        week = [n for _, n in rows[-7:]]
        avg7 = sum(week) / len(week)
        days_ge_50 = sum(1 for n in week if n / BASELINE >= PACK_RATIO)
        out.update(last=last_date, lag_days=lag, avg7=round(avg7, 1),
                   ratio=round(avg7 / BASELINE, 2), days_ge_50pct=days_ge_50)
        if lag > 8 and state.get("stale_armed", True):
            fired.append(f"HORMUZ WATCH: feed stale — last datum {last_date} ({lag}d old)")
            state["stale_armed"] = False
        elif lag <= 8:
            state["stale_armed"] = True
        if avg7 > KILL_LEG1 and state.get("kill_armed", True):
            fired.append(f"HORMUZ TRIPLE-KILL LEG 1 ARMED: 7d-avg transits {avg7:.0f}/day > 40 "
                         f"({avg7/BASELINE:.0%} of baseline) — VERIFY AWRP <0.4% + TD3C <$60k before "
                         "acting on the FRO/STNG/LPG sleeve")
            state["kill_armed"] = False
        elif avg7 < KILL_LEG1 * 0.9:
            state["kill_armed"] = True     # re-arm on a clear retreat
        if days_ge_50 >= 5 and state.get("pack_armed", True):
            fired.append(f"HORMUZ PACK EARLY-WARNING: >=50% of baseline on {days_ge_50}/7 days — "
                         "the Aug-31 HIT condition is printing early; review the FRO call branches")
            state["pack_armed"] = False
        elif days_ge_50 <= 3:
            state["pack_armed"] = True
    if not dry:
        json.dump(state, open(STATE, "w"), indent=1)
        if fired:
            from desk.gauntlet_sentinel import _notify
            _notify(" | ".join(fired)[:900])
    for f in fired:
        print("[hormuz_watch] FIRE:", f)
    if not fired:
        print(f"[hormuz_watch] quiet: {out}")
    return out


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
