"""Season watch — the two remaining physical/behavioral tripwires nothing polled.

1. NHC Atlantic storms (HRTG order resting + EG; season peak Aug-Oct): free
   CurrentStorms.json; alert once per named hurricane while any Atlantic
   hurricane is active. The HRTG/EG frozen season call (no-major 62%) and the
   nat-cat sizing both key off this.
2. ONON promo tripwire (COURT-MANDATED weekly): a second deep broad-assortment
   promo event before the Aug-11 print CANCELS the T2 auto-add. on.com blocks
   scrapers erratically, so this is fetch-with-fallback: a successful fetch
   greps for sitewide-sale markers; a failed fetch degrades to a Monday
   REMINDER alert so the check happens manually — the tripwire may not
   silently lapse either way.

Runs from the sentinel: NHC every run (cheap), ONON Mondays. READ-ONLY.
    python3 -m desk.season_watch [--dry]
"""
from __future__ import annotations

import datetime
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "season_watch_state.json"
NHC = "https://www.nhc.noaa.gov/CurrentStorms.json"
CHROME = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
          "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-US,en;q=0.9"}


def _nhc(state: dict) -> list[str]:
    fired = []
    try:
        with urllib.request.urlopen(NHC, timeout=20) as r:
            js = json.load(r)
        seen = set(state.get("storms_alerted", []))
        for s in js.get("activeStorms", []):
            if s.get("classification") == "HU" and "AL" in (s.get("binNumber") or s.get("id", "")).upper():
                name = s.get("name", "?")
                if name not in seen:
                    fired.append(f"NHC: Atlantic hurricane {name} active (intensity {s.get('intensity','?')}kt) "
                                 "— review HRTG/EG exposure + the no-major season call")
                    seen.add(name)
        state["storms_alerted"] = sorted(seen)
    except Exception as e:
        fired.append(f"NHC watch: feed failed ({type(e).__name__}) — check manually in season")
    return fired


def _onon_promo(state: dict) -> list[str]:
    if datetime.date.today().weekday() != 0:      # Mondays only
        return []
    wk = datetime.date.today().isoformat()
    if state.get("onon_last_check") == wk:
        return []
    state["onon_last_check"] = wk
    try:
        req = urllib.request.Request("https://www.on.com/en-us/collections/sale", headers=CHROME)
        with urllib.request.urlopen(req, timeout=25) as r:
            html = r.read(400_000).decode(errors="ignore").lower()
        deep = any(m in html for m in ("30% off", "40% off", "50% off", "sitewide"))
        if deep:
            return [f"ONON PROMO TRIPWIRE: deep-discount markers on on.com sale page ({wk}) — "
                    "verify breadth (prior-season outlet vs broad assortment); a second deep broad "
                    "event CANCELS the Aug-11 T2 auto-add per the court"]
        return []
    except Exception:
        return [f"ONON promo weekly check ({wk}): on.com fetch blocked — run the manual check "
                "(SimplyCodes cadence + Wayback 'Last Season' breadth); the court's tripwire must not lapse"]


def main(dry: bool = False) -> list[str]:
    state = json.load(open(STATE)) if STATE.exists() else {}
    fired = _nhc(state) + _onon_promo(state)
    if not dry:
        json.dump(state, open(STATE, "w"), indent=1)
        if fired:
            from desk.gauntlet_sentinel import _notify
            _notify(" | ".join(fired)[:900])
    for f in fired:
        print("[season_watch] FIRE:", f)
    if not fired:
        print("[season_watch] quiet (no active Atlantic hurricane; ONON check not due/clean)")
    return fired


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
