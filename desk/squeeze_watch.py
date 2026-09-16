"""Squeeze watch — T+1 covering detector for the SpaceX proxy-hedge basket.

The tender-window hypothesis (pre-registered 2026-07-05): restricted SpaceX
holders proxy-hedge via shorts on the value-correlated space-theme names
(ASTS / LUNR / BKSY); those shorts unwind when SpaceX liquidity events (the
~biannual tenders) let holders de-risk directly. FINRA bi-monthly SI confirms
too late — this watcher reads FINRA's DAILY short-sale volume files (free,
T+1) and flags the covering signature the day after it starts:

  short-volume ratio (short vol / total vol) dropping >=10pp below its own
  20-day mean on >=2 consecutive days, ACROSS >=2 of the 3 basket names.

One name = noise; a synchronized drop = the fingerprint, in time to front-run
the REST of the window (tenders run weeks, covering a basket this size takes
days). Alerts via the sentinel stack. READ-ONLY.
    python3 -m desk.squeeze_watch [--dry]
"""
from __future__ import annotations

import datetime
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "squeeze_watch_state.json"
BASKET = ("ASTS", "LUNR", "BKSY")
URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d}.txt"
LOOKBACK = 22          # trading-day files to keep per name
DROP_PP = 0.10         # ratio must sit >=10pp under the 20d mean
CONSEC = 2             # ...for >=2 consecutive days
NAMES_REQ = 2          # ...on >=2 basket names


def _fetch_day(d: datetime.date) -> dict[str, tuple[int, int]]:
    """{sym: (short_vol, total_vol)} for basket names on date d; {} if no file (holiday/weekend)."""
    try:
        req = urllib.request.Request(URL.format(d=d.strftime("%Y%m%d")),
                                     headers={"User-Agent": "signalos-research 4tripathy@gmail.com"})
        with urllib.request.urlopen(req, timeout=20) as r:
            txt = r.read().decode(errors="ignore")
    except Exception:
        return {}
    out = {}
    for ln in txt.splitlines()[1:]:
        p = ln.split("|")
        if len(p) >= 5 and p[1] in BASKET:
            try:
                out[p[1]] = (float(p[2]), float(p[4]))
            except ValueError:
                pass
    return out


def main(dry: bool = False) -> dict:
    state = json.load(open(STATE)) if STATE.exists() else {"days": {}}
    days = state["days"]
    # backfill up to LOOKBACK trading days
    d = datetime.date.today()
    tried = 0
    while len(days) < LOOKBACK + 4 and tried < 45:
        d -= datetime.timedelta(days=1)
        tried += 1
        k = d.isoformat()
        if k in days:
            continue
        row = _fetch_day(d)
        if row:
            days[k] = {s: v for s, v in row.items()}
    # keep the newest files only
    for k in sorted(days)[:-int(LOOKBACK * 1.6)]:
        days.pop(k, None)
    # per-name ratio series (ascending by date)
    fired, detail = [], {}
    for s in BASKET:
        ser = [(k, v[s][0] / v[s][1]) for k, v in sorted(days.items()) if s in v and v[s][1] > 0]
        if len(ser) < 10:
            detail[s] = "insufficient data"
            continue
        ratios = [r for _, r in ser]
        base = sum(ratios[:-CONSEC]) / len(ratios[:-CONSEC])
        recent = ratios[-CONSEC:]
        covering = all(base - r >= DROP_PP for r in recent)
        detail[s] = {"mean20": round(base, 3), "recent": [round(r, 3) for r in recent],
                     "covering": covering, "last": ser[-1][0]}
        if covering:
            fired.append(s)
    out = {"basket": detail, "synchronized": len(fired) >= NAMES_REQ}
    msgs = []
    if out["synchronized"] and state.get("armed", True):
        msgs.append(f"SQUEEZE FINGERPRINT: synchronized covering on {'+'.join(fired)} "
                    f"(short-vol ratio >=10pp under 20d mean, {CONSEC}d) — the tender-unwind "
                    "hypothesis is EVIDENCED; the front-run window is OPEN (see the pre-registration)")
        state["armed"] = False
    elif not out["synchronized"]:
        state["armed"] = True
    if not dry:
        state["days"] = days
        json.dump(state, open(STATE, "w"), indent=1)
        if msgs:
            from desk.gauntlet_sentinel import _notify
            _notify(" | ".join(msgs)[:900])
    print(f"[squeeze_watch] {'FIRE: ' + msgs[0] if msgs else 'quiet'} | {json.dumps(detail)[:400]}")
    return out


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
