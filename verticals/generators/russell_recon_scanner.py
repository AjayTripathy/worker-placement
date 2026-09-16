"""russell_recon_scanner — Stage 0b FLOW: the annual Russell reconstitution forced-flow calendar.

The LARGEST mechanical forced-buy/sell event of the year. Every June, FTSE Russell rebuilds the
Russell 1000/2000/3000 from a single rank-day market-cap snapshot. Index funds tracking them MUST
trade the adds / deletes / up-and-down migrations at the effective close — a price-INSENSITIVE
forced trader, exactly the FLOW edge (MFP class): air-pocket at the deletes, pop at the adds, and
a two-sided squeeze on the R2000<->R1000 migration band.

The tradeable structure is the CALENDAR:
  · RANK DAY        — a spring snapshot (historically ~last business day of April); membership is set here
  · PRELIMINARY LISTS — FTSE publishes the adds/deletes ~late May / first Fridays of June (the ~4-week window)
  · EFFECTIVE       — after close on the last Friday of June (funds trade into the close = the flow)
Off-season this generator is a dated COUNTDOWN + the mechanism; in the May-June window it flags that the
prelim lists are live and the migration-band names should be pulled (data = FTSE Russell / press).

    python3 verticals/generators/russell_recon_scanner.py
Writes data/RUSSELL_RECON.json. READ-ONLY. (Live adds/deletes pull is an in-window data step.)
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "RUSSELL_RECON.json"


def _last_business_day(year: int, month: int) -> datetime.date:
    d = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1) if month < 12 else datetime.date(year, 12, 31)
    while d.weekday() >= 5:      # back up off Sat/Sun
        d -= datetime.timedelta(days=1)
    return d


def _last_friday(year: int, month: int) -> datetime.date:
    d = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1) if month < 12 else datetime.date(year, 12, 31)
    while d.weekday() != 4:      # 4 = Friday
        d -= datetime.timedelta(days=1)
    return d


def _schedule(year: int) -> dict:
    """The recon milestones for a given year (dates are the well-known rule; FTSE tweaks by a day/two)."""
    rank = _last_business_day(year, 4)            # rank-day cap snapshot (~end of April)
    effective = _last_friday(year, 6)             # reconstitution effective after this Friday's close
    prelim = effective - datetime.timedelta(days=28)   # prelim add/delete lists ~4 weeks prior (late May/June)
    return {"year": year, "rank_day": rank.isoformat(), "prelim_lists": prelim.isoformat(),
            "effective": effective.isoformat()}


def scan() -> dict:
    today = datetime.date.today()
    # the relevant reconstitution is this year's if its effective date is still ahead, else next year's
    sch = _schedule(today.year)
    if datetime.date.fromisoformat(sch["effective"]) < today:
        sch = _schedule(today.year + 1)
    d_rank = (datetime.date.fromisoformat(sch["rank_day"]) - today).days
    d_prelim = (datetime.date.fromisoformat(sch["prelim_lists"]) - today).days
    d_eff = (datetime.date.fromisoformat(sch["effective"]) - today).days

    # phase: what to do right now
    if d_rank > 0:
        phase = "DORMANT — pre-rank"
        action = f"Nothing to do; the {sch['year']} membership isn't set until rank day ({sch['rank_day']}, {d_rank}d)."
    elif d_prelim > 0:
        phase = "RANK SET — awaiting prelim lists"
        action = ("Membership is snapshotted; the adds/deletes exist but aren't public. Pre-screen the MIGRATION BAND "
                  "(names hovering at the R1000/R2000 cap breakpoint ~$4-6B) — they carry two-sided forced flow.")
    elif d_eff >= 0:
        phase = "⚡ PRELIM WINDOW OPEN — the tradeable ~4 weeks"
        action = ("Prelim adds/deletes are PUBLIC. Pull the FTSE Russell lists: buy the additions' air-pocket into the "
                  "effective close, fade/short the deletions' forced-selling overhang, play the up-migration squeeze. "
                  "Exit is the effective date — a pre-registered mechanical FLOW trade.")
    else:
        phase = "POST-EFFECTIVE"
        action = "Reconstitution done; unwind. Next window opens ~late May."

    return {"asof": today.isoformat(), "reconstitution": sch,
            "days_to": {"rank_day": d_rank, "prelim_lists": d_prelim, "effective": d_eff},
            "phase": phase, "action": action,
            "adds": [], "deletes": [], "migrations": [],   # populated in-window from the FTSE prelim lists
            "note": "FLOW class — the annual Russell reconstitution is the year's biggest price-INSENSITIVE forced flow. "
                    "Off-season = a countdown; in the ~4-week prelim window the adds/deletes/migrations are the trades "
                    "(air-pocket at deletes, pop at adds, squeeze on the R2000<->R1000 migration band). Dates follow the "
                    "well-known rule (rank ~end-Apr, effective ~last Fri of June); confirm FTSE's exact schedule in-year. "
                    "The live adds/deletes list is an in-window pull (FTSE Russell / press) — this scanner times it."}


def main():
    res = scan()
    s = res["reconstitution"]
    print(f"=== RUSSELL RECONSTITUTION  {res['asof']}  ({s['year']} cycle) ===")
    print(f"  PHASE: {res['phase']}")
    print(f"  rank day {s['rank_day']} ({res['days_to']['rank_day']:+d}d) · "
          f"prelim lists {s['prelim_lists']} ({res['days_to']['prelim_lists']:+d}d) · "
          f"EFFECTIVE {s['effective']} ({res['days_to']['effective']:+d}d)")
    print(f"  ACTION: {res['action']}")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
