"""harvest_ledger — the goal-tracker for the $2.4M tax-loss-harvest loop. Sums realized capital LOSSES
across the program (Parametric SMA + existing carryforward + your DIY IBKR book), measures progress vs
the $2.4M goal, PROJECTS the year-end total at the current run-rate, and SURFACES the gap (no silent cap:
if you're tracking to miss, it says so, in time to add capital or accept the tax).

The harvest must land by Dec 31 2026 (a 2026 gain takes 2026 losses — capital losses carry forward, not
back), so the projection is what matters: are we on pace by year-end?

  python3 -m desk.harvest_ledger          # progress + projection (Desk-ingested)
  echo '{"date":"2026-07-01","loss":12000,"note":"harvested XYZ"}' >> desk/data/diy_harvest.jsonl
"""
from __future__ import annotations
import os, json, sqlite3, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
MSPRIME_DB = os.environ.get("MSPRIME_DB", "/Users/ajay/msprime/app/data/msprime.db")
DIY_LEDGER = HERE / "data" / "diy_harvest.jsonl"   # your DIY IBKR harvests, one json/line {date,loss,note}

GOAL = 5_000_000                   # TRUE 2026 goal (user, 2026-07-01). Prior $2.4M was the stale working target.
# FEASIBILITY (user): the $5M goal is NOT fully reachable this year — the $5M dry powder that could generate
# harvest lots arrives ~SEPTEMBER, leaving only a ~3.5-month Sep→Dec window on fresh basis (realistic fresh-
# capital harvest in a normal-vol window: ~$200-500k). Track the honest gap vs $5M; the deployment DESIGN
# (harvest-density: many lots, high dispersion, weekly lot-level sweeps, wash-sale-clean vs Parametric's ~471
# names) is what maximizes the feasible fraction; the shortfall carries forward as next-year offset capacity.
EXISTING_LOSSES = 300_000          # the carryforward/realizable losses you already have
PARAMETRIC_TARGET = 1_000_000      # your assumed full-year Parametric harvest
YEAR_END = datetime.date(2026, 12, 31)


def parametric_realized(db=MSPRIME_DB) -> float:
    """Net realized capital LOSS YTD from the SMA (positive number = losses harvested)."""
    if not os.path.exists(db):
        return 0.0
    con = sqlite3.connect(db)
    try:
        # DEDUPE (2026-09-08): the MS Prime daily extracts are OVERLAPPING windows — the same
        # closed lot appears in every extract whose window covers it (5,630 rows = 2,608 lots;
        # raw SUM overstated the harvest 2.5x: $1.198M vs $484K). One row per closed lot.
        net = con.execute(
            "SELECT SUM(g) FROM (SELECT MAX(issue_gainloss) AS g FROM gainloss "
            "WHERE date_closed LIKE '2026%' GROUP BY taxlot_id, date_closed, quantity, cusip)"
        ).fetchone()[0] or 0.0
        return max(0.0, -net)        # only count net losses toward the goal
    finally:
        con.close()


def diy_realized() -> float:
    if not DIY_LEDGER.exists():
        return 0.0
    tot = 0.0
    for ln in DIY_LEDGER.read_text().splitlines():
        try:
            tot += float(json.loads(ln).get("loss", 0))
        except Exception:
            pass
    return tot


def snapshot(today: datetime.date | None = None) -> dict:
    today = today or datetime.date.today()
    para = parametric_realized()
    diy = diy_realized()
    realized = para + EXISTING_LOSSES + diy
    # project Parametric to its full-year target (run-rate), DIY linearly off its own pace
    days_done = max(1, (today - datetime.date(today.year, 1, 1)).days)
    days_left = max(0, (YEAR_END - today).days)
    para_proj = max(para, PARAMETRIC_TARGET)                       # assume it reaches the target
    diy_proj = diy * (1 + days_left / days_done) if diy else 0.0   # extrapolate DIY pace
    projected = para_proj + EXISTING_LOSSES + diy_proj
    return {
        "asof": today.isoformat(), "goal": GOAL, "days_left": days_left,
        "realized": round(realized), "projected_year_end": round(projected),
        "components": {"parametric": round(para), "existing": EXISTING_LOSSES, "diy": round(diy)},
        "pct_to_goal_realized": round(realized / GOAL, 2),
        "pct_to_goal_projected": round(projected / GOAL, 2),
        "gap_to_goal": round(GOAL - projected),
        "on_track": projected >= GOAL * 0.95,
    }


def main():
    s = snapshot()
    sev = "MED" if s["on_track"] else "HIGH"
    status = "ON TRACK" if s["on_track"] else f"BEHIND by ${s['gap_to_goal']/1e6:.2f}M"
    ev = (f"harvest ${s['realized']/1e6:.2f}M realized / ${s['projected_year_end']/1e6:.2f}M projected vs "
          f"${GOAL/1e6:.1f}M goal ({s['pct_to_goal_projected']:.0%}) — {status}; {s['days_left']}d left "
          f"[para ${s['components']['parametric']/1e3:.0f}k + existing $300k + DIY ${s['components']['diy']/1e3:.0f}k]")
    print(f"DETFIRE|harvest_goal|HARVEST|{sev}|{ev}")
    print(f"# {ev}")


if __name__ == "__main__":
    main()
