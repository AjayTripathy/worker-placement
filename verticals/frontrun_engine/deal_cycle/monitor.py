"""monitor — the deal-cycle regime gauge + DFIN entry trigger. Pulls the whole stack:
  GATE      financial conditions (HY OAS / VIX)            — necessary condition
  PIPELINE  EDGAR IPO (DRS+S-1) & M&A (S-4+proxy) trend    — DFIN's forward revenue
  PRIVATE   Form D velocity                                — earliest pre-IPO funnel
  CREDIT    BDC net deployment (best-effort, quarterly)    — M&A financing supply

Regime: FROZEN / THAWING / OPEN-BUT-LATE / OPEN.  DFIN trigger fires ONLY on a pipeline UP-inflection
with the gate OPEN — the discipline from BAH/DFIN: buy when the catalyst turns, don't pay for the
re-rate on cheapness alone. READ-ONLY: logs + prints, never an order.
"""
from __future__ import annotations
import json, statistics as st
from datetime import datetime, timezone
from pathlib import Path
from . import edgar_pipeline as EP, conditions as CO

LOG = Path(__file__).resolve().parent / "data" / "deal_cycle_log.jsonl"


def _recent_pipeline(n_months=7):
    # last n complete-ish months; flag the current partial month
    from datetime import date
    today = date.today()
    end = today.strftime("%Y-%m")
    y, m = today.year, today.month - n_months
    while m <= 0:
        y, m = y - 1, m + 12
    start = f"{y:04d}-{m:02d}"
    pipe = EP.pipeline_series(start, end)
    return pipe, end


def _trend(series_vals):
    """sign of recent slope: compare last 3 vs prior 3 (ignoring an incomplete tail handled by caller)."""
    if len(series_vals) < 4:
        return 0.0
    recent = st.mean(series_vals[-3:]); prior = st.mean(series_vals[-6:-3] or series_vals[:-3])
    return (recent / prior - 1) if prior else 0.0


def snapshot(include_bdc=True) -> dict:
    asof = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cond = CO.latest()
    gate, gate_note = CO.gate_state(cond)
    pipe, cur_month = _recent_pipeline()
    months = sorted(pipe)
    # exclude the current (partial) month from trend so we don't read a half-month as a collapse
    complete = [m for m in months if m < cur_month]
    ipo_series = [pipe[m]["ipo_lead"] for m in complete]
    drs_series = [pipe[m]["ipo_confidential"] for m in complete]
    ma_series = [pipe[m]["ma_lead"] for m in complete]
    ipo_tr, drs_tr, ma_tr = _trend(ipo_series), _trend(drs_series), _trend(ma_series)

    bdc = None
    if include_bdc:
        try:
            from . import bdc_originations as BD
            bsnap = BD.deployment_snapshot()
            bdc = {"state": BD.deployment_state(bsnap), "agg_pct_qoq": bsnap.get("agg_pct_qoq"),
                   "n_parsed": bsnap.get("n_parsed")}
        except Exception as e:
            bdc = {"error": str(e)}

    # regime synthesis
    forward_thinning = drs_tr < -0.10           # DRS = forward IPO funnel; falling = late-cycle tell
    pipeline_up = ipo_tr > 0.05 or ma_tr > 0.05
    if gate == "FROZEN":
        regime = "FROZEN"
    elif gate in ("OPEN", "TIGHTENING") and pipeline_up and not forward_thinning:
        regime = "THAWING"
    elif gate == "OPEN" and forward_thinning:
        regime = "OPEN-BUT-LATE"      # window open / deals pricing, but the forward funnel is thinning
    elif gate == "OPEN":
        regime = "OPEN"
    else:
        regime = "MIXED"

    # DFIN trigger — HONEST after THREE tests, all negative for a tradeable equity edge:
    #   1. lead_lag (stock):     pipeline-change vs DFIN fwd returns weakly NEGATIVE (−0.13..−0.40)
    #   2. revenue_test:         pipeline-YoY vs DFIN total-revenue-YoY ~0 (no lead; total rev is
    #                            dominated by recurring SW + secular decline — segment test still open)
    #   3. contrarian_test:      depressed-vs-hot pipeline tercile -> conflicting signs across horizons
    #                            (3/6mo favor HOT, gate-conditioned tiny-n favors depressed) = NOT robust
    # => NO validated equity trigger in EITHER direction. The regime gauge is DESCRIPTIVE context only.
    equity_frontrun_validated = False
    dfin_trigger = (f"NO-VALIDATED-TRIGGER (descriptive only; regime={regime}). "
                    "3 tests negative: stock-frontrun, revenue-lead, contrarian all unproven.")

    return {"asof": asof, "gate": gate, "gate_note": gate_note, "conditions": cond,
            "current_partial_month": cur_month,
            "pipeline_complete_months": complete,
            "ipo_lead": ipo_series, "drs": drs_series, "ma_lead": ma_series,
            "trend_ipo": round(ipo_tr, 3), "trend_drs": round(drs_tr, 3), "trend_ma": round(ma_tr, 3),
            "forward_thinning": forward_thinning, "bdc": bdc,
            "regime": regime, "dfin_trigger": dfin_trigger,
            "equity_frontrun_validated": equity_frontrun_validated}


def main(include_bdc=True, log=True):
    s = snapshot(include_bdc=include_bdc)
    print(f"=== DEAL-CYCLE MONITOR {s['asof']}  (READ-ONLY; DFIN frontrun) ===")
    print(f"  GATE: {s['gate']} — {s['gate_note']}")
    c = s["conditions"]
    print(f"        HY OAS {c.get('hy_oas',{}).get('value')}% ({c.get('hy_oas',{}).get('chg_1m'):+}/1m) | "
          f"VIX {c.get('vix',{}).get('value')} ({c.get('vix',{}).get('chg_1m'):+}/1m)")
    print(f"  PIPELINE (complete months {s['pipeline_complete_months'][0]}..{s['pipeline_complete_months'][-1]}):")
    print(f"        IPO lead (DRS+S-1): {s['ipo_lead']}  trend {s['trend_ipo']:+.0%}")
    print(f"        DRS (forward funnel): {s['drs']}  trend {s['trend_drs']:+.0%}  {'THINNING' if s['forward_thinning'] else 'ok'}")
    print(f"        M&A lead (S-4+proxy): {s['ma_lead']}  trend {s['trend_ma']:+.0%}")
    print(f"        (current partial month {s['current_partial_month']} excluded from trend)")
    if s.get("bdc"):
        print(f"  CREDIT (BDC deployment): {s['bdc'].get('state', s['bdc'])}")
    print(f"\n  >>> REGIME: {s['regime']}   |   DFIN trigger: {s['dfin_trigger']}")
    if log:
        with open(LOG, "a") as f:
            f.write(json.dumps({k: v for k, v in s.items() if k != "conditions"}, default=str) + "\n")
        print(f"  [-> {LOG.name}]")
    return s


if __name__ == "__main__":
    import sys
    main(include_bdc=("--no-bdc" not in sys.argv))
