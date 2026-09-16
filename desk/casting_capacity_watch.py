"""casting_capacity_watch — the HONA courts' named flip-evidence sensor:
'primary evidence (supplier quals, hiring_velocity at casting suppliers) of capacity
landing pre-2027' (red bench, WHAT WOULD CHANGE MY MIND).

Mechanism: aerospace investment-casting capacity is people-constrained (quals run
12-24 months). A hiring WAVE at the casting suppliers = expansion underway; the
TAPER after the wave = capacity landing. Rides the proven hiring_velocity connector
(Stevanato plant-ramp method) across the casting complex — Howmet (public), and the
private majors (PCC/Berkshire, Consolidated Precision Products, Doncasters) whose
postings are visible even though their financials aren't.

v1 accrues weekly snapshots (a single pull is lumpy noise — read the TREND); flags
route through the monitor once a baseline exists (>=6 snapshots): wave = counts
+50% over baseline; taper-after-wave = -30% from the observed peak.

  python3 -m desk.casting_capacity_watch     # weekly cron
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "casting_capacity_state.json"
sys.path.insert(0, str(ROOT))

EMPLOYERS = [
    ("Howmet", ("howmet",)),
    ("Precision Castparts", ("precision castparts", "pcc ")),
    ("Consolidated Precision Products", ("consolidated precision",)),
    ("Doncasters", ("doncasters",)),
]
KEYWORDS = "investment casting"


def snapshot() -> dict:
    from verticals.buyside_dd.connectors.hiring_velocity import fetch_postings
    counts = {}
    for name, filters in EMPLOYERS:
        try:
            rows = fetch_postings(KEYWORDS, "United States", company_filter=filters)
            counts[name] = len(rows)
        except Exception as e:
            counts[name] = None
            print(f"[casting_watch] {name}: fetch failed ({type(e).__name__})")
    return counts


def run() -> list[str]:
    today = datetime.date.today().isoformat()
    try:
        st = json.loads(STATE.read_text())
    except Exception:
        st = {"snapshots": []}
    counts = snapshot()
    st["snapshots"] = [s for s in st["snapshots"] if s["date"] != today] + \
                      [{"date": today, "counts": counts}]
    st["snapshots"] = st["snapshots"][-60:]
    flags = []
    valid = [s for s in st["snapshots"] if any(v is not None for v in s["counts"].values())]
    totals = [sum(v for v in s["counts"].values() if v is not None) for s in valid]
    if len(totals) >= 6:
        base = sum(totals[:3]) / 3
        peak = max(totals)
        cur = totals[-1]
        if base and cur >= base * 1.5:
            flags.append(f"CASTING-WAVE: casting-complex postings {cur} vs baseline ~{base:.0f} "
                         f"(+{cur/base-1:.0%}) — expansion underway (HONA 2027-fix leading indicator)")
        if peak and cur <= peak * 0.7 and peak >= base * 1.3:
            flags.append(f"CASTING-TAPER: postings {cur} vs peak {peak} (-{1-cur/peak:.0%}) after a wave — "
                         f"capacity LANDING; the HONA deferred-not-destroyed thesis strengthens")
    else:
        st["status"] = f"baseline accruing ({len(totals)}/6 snapshots) — NO SIGNAL YET, by design"
    st["latest_flags"] = flags
    STATE.write_text(json.dumps(st, indent=1))
    return flags


if __name__ == "__main__":
    fl = run()
    st = json.loads(STATE.read_text())
    print(f"[casting_capacity_watch] {datetime.date.today()} counts={st['snapshots'][-1]['counts']} "
          f"{st.get('status','')}")
    for f in fl:
        print("  " + f)
