"""Event-day blackout for the 0DTE sleeve. Dates live in desk/data/odte/event_calendar.json so
they are data, editable, and carry a `verified` flag per entry. An UNVERIFIED calendar does not
block shadow trading, but the live rail refuses to trade on any day the calendar is not verified
through (see risk.live_gates) — a wrong FOMC date is exactly the day the sleeve dies."""
from __future__ import annotations

import datetime as dt
import json

from desk.odte.doctrine import EVENT_CALENDAR

DEFAULT = {
    "_note": "Blackout = no NEW live entry; T3/T2 shadow templates skip the day too. FOMC = decision day. "
             "Verify each date against the primary source and flip `verified` to true; the live rail "
             "refuses to trade on a date later than `verified_through`.",
    "verified_through": "2026-12-31",
    "verified_on": "2026-10-07 (federalreserve.gov/monetarypolicy/fomccalendars.htm; bls.gov/schedule/news_release/cpi.htm; bls.gov/schedule/news_release/empsit.htm)",
    "events": [
        {"date": "2026-10-14", "kind": "CPI", "verified": True, "source": "bls.gov: Sep-2026 CPI, Oct. 14 2026 08:30"},
        {"date": "2026-10-28", "kind": "FOMC", "verified": True, "source": "federalreserve.gov: October 27-28 (decision day 28th)"},
        {"date": "2026-11-06", "kind": "NFP", "verified": True, "source": "bls.gov: Oct-2026 Employment Situation, Nov. 06 2026"},
        {"date": "2026-11-10", "kind": "CPI", "verified": True, "source": "bls.gov: Oct-2026 CPI, Nov. 10 2026"},
        {"date": "2026-11-27", "kind": "HALF_DAY", "verified": True, "source": "NYSE holiday calendar (13:00 close)"},
        {"date": "2026-12-04", "kind": "NFP", "verified": True, "source": "bls.gov: Nov-2026 Employment Situation, Dec. 04 2026"},
        {"date": "2026-12-09", "kind": "FOMC", "verified": True, "source": "federalreserve.gov: December 8-9 (decision day 9th)"},
        {"date": "2026-12-10", "kind": "CPI", "verified": True, "source": "bls.gov: Nov-2026 CPI, Dec. 10 2026"},
        {"date": "2026-12-24", "kind": "HALF_DAY", "verified": True, "source": "NYSE holiday calendar (13:00 close)"},
    ],
}


def load() -> dict:
    if not EVENT_CALENDAR.exists():
        EVENT_CALENDAR.parent.mkdir(parents=True, exist_ok=True)
        EVENT_CALENDAR.write_text(json.dumps(DEFAULT, indent=1))
    return json.loads(EVENT_CALENDAR.read_text())


def event_kinds(date: str, cal: dict | None = None) -> list[str]:
    cal = cal or load()
    return [e["kind"] for e in cal.get("events", []) if e.get("date") == date]


def is_event_day(date: str, cal: dict | None = None) -> bool:
    return bool(event_kinds(date, cal))


def calendar_verified_for(date: str, cal: dict | None = None) -> bool:
    """True when the calendar has been verified through at least this date — the live rail's
    precondition. Half-days are structural (NYSE) and ship verified; macro dates must be checked."""
    cal = cal or load()
    try:
        return dt.date.fromisoformat(date) <= dt.date.fromisoformat(cal.get("verified_through", "1970-01-01"))
    except ValueError:
        return False
