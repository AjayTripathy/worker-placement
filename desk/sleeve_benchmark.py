"""sleeve_benchmark — the IBKR AI sleeve vs the DUMP-IT-IN-PARAMETRIC counterfactual.

The honest opportunity-cost question (user, 2026-07-07): for every dollar wired
to IBKR, what if it had gone into the Parametric 130/30 instead? Counterfactual
model per deposit:

    SPY total-return units bought on the deposit date
  + harvest tax-alpha accrual  (HARVEST_PACE x HARVEST_VALUE, prorated daily —
      pace measured from the real account: ~7%/yr of sleeve realized as ST
      losses; value ~37% = the earmarked netting rate vs the Sept LT gain)
  - the all-in fee (0.91%/yr, prorated daily)

Flows are derived from the IBKR PA series (NAV jump minus same-day return =
external flow), cached in desk/data/sleeve_flows.json — verify/extend as new
deposits land. Output: desk/data/sleeve_benchmark.json + stdout verdict.

    python3 -m desk.sleeve_benchmark        # registered weekly
READ-ONLY. This is the OFFICE THESIS's P&L referee: the AI sleeve must beat
passive-plus-harvest, after honesty about the harvest.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOWS = ROOT / "desk" / "data" / "sleeve_flows.json"
OUT = ROOT / "desk" / "data" / "sleeve_benchmark.json"

HARVEST_PACE = 0.07      # measured: Parametric realized ~7%/yr of sleeve as losses (young acct)
HARVEST_VALUE = 0.371    # earmarked netting rate vs the certain Sept LT gain (LT+NIIT fed + CA)
FEE = 0.0091             # 0.51% Parametric + 0.40% MFO

# flows derived from the IBKR PA NAV/cps series (2026-07-06 pull); amounts are
# external deposits net of same-day P&L. Extend as new wires land.
DEFAULT_FLOWS = [
    ("2026-03-11", 1000), ("2026-03-17", 4000), ("2026-05-21", 3750),
    ("2026-05-28", 46200), ("2026-06-12", 46250), ("2026-06-29", 4950),
    ("2026-07-03", 95660),
]


def main():
    import yfinance as yf
    flows = json.loads(FLOWS.read_text())["flows"] if FLOWS.exists() else DEFAULT_FLOWS
    if not FLOWS.exists():
        FLOWS.write_text(json.dumps({"flows": flows, "note": "date, USD deposit; derived from PA NAV-vs-cps; extend on new wires"}, indent=1))
    start = flows[0][0]
    spy = yf.Ticker("SPY").history(start=start, auto_adjust=True)["Close"]
    spy.index = [d.date().isoformat() for d in spy.index]
    today = spy.index[-1]
    px_today = float(spy.iloc[-1])

    cf_value = 0.0
    total_dep = 0.0
    today_d = datetime.date.fromisoformat(today)
    for dstr, amt in flows:
        total_dep += amt
        # SPY entry px = first close on/after the deposit date
        px_in = next((float(spy[d]) for d in spy.index if d >= dstr), px_today)
        units_val = amt * px_today / px_in
        days = (today_d - datetime.date.fromisoformat(dstr)).days
        carry = (HARVEST_PACE * HARVEST_VALUE - FEE) * days / 365.0
        cf_value += units_val * (1 + carry)

    # actual sleeve NAV: freshest of positions-cache-based or PA pull left to the caller;
    # use the cached account NAV file if present
    nav = None
    sleeve_harvest = 0.0
    try:
        sn = json.loads((ROOT / "desk" / "data" / "sleeve_nav.json").read_text())
        nav = sn["nav"]
        # SYMMETRY (user 2026-07-07: "we will tlh aggressively in our sleeve too"):
        # the sleeve's ACTUAL realized ST losses get the same 37% earmarked value
        # the counterfactual's harvest is credited at. Maintained on desk polls
        # from the IBKR trade log (realized losses only; gains handled by the tax math itself).
        sleeve_harvest = abs(min(0.0, sn.get("realized_st_losses_ytd", 0.0))) * HARVEST_VALUE
    except Exception:
        pass
    out = {"asof": today, "total_deposited": round(total_dep),
           "counterfactual_parametric": round(cf_value),
           "cf_return_pct": round((cf_value / total_dep - 1) * 100, 2),
           "actual_nav": nav,
           "sleeve_harvest_credit": round(sleeve_harvest),
           "alpha_usd": round(nav + sleeve_harvest - cf_value) if nav else None,
           "alpha_note": "actual_nav must be refreshed from IBKR (desk/data/sleeve_nav.json {nav, asof}) — the desk updates it on poll",
           "assumptions": {"harvest_pace": HARVEST_PACE, "harvest_value": HARVEST_VALUE, "fee": FEE}}
    OUT.write_text(json.dumps(out, indent=1))
    print(f"[sleeve_benchmark] deposited ${total_dep:,.0f} -> counterfactual (SPY-TR + harvest - fee): "
          f"${cf_value:,.0f} ({out['cf_return_pct']:+.2f}%)"
          + (f" | ACTUAL ${nav:,.0f} + harvest credit ${sleeve_harvest:,.0f} | ALPHA ${nav + sleeve_harvest - cf_value:+,.0f}" if nav else " | set sleeve_nav.json for the verdict"))


if __name__ == "__main__":
    main()
