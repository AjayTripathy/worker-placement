"""
bdc_convergence.py — price/discount convergence + control-arm helpers for the Phase-2
spread-driven frontrun backtest (PILOT_SPEC §5, §6 confound control, §7 primary edge(A)-edge(B)).

Given a daily price series per BDC (from IBKR get_price_history, ONE_DAY bars) and the panel
(printed NAV per quarter, filing dates), it measures the frontrun mechanic:

For quarter T (signal computable at quarter-end qe = T's period_end):
  - last printed NAV = printed NAV(T-1) [the STALE number the market sees during the lag];
  - derived NAV(T)   = re-marked (from run_bdc_backtest), the not-yet-printed estimate;
  - prem_at_qend     = price(qe) / printed NAV(T-1) - 1   [discount vs the STALE NAV];
  - prem_at_print    = price(filing_date) / printed NAV(T) - 1 [discount vs the NEW NAV];
  - CONVERGENCE: did price move toward derived NAV during [qe, filing_date] BEFORE the print?
    measured as the fraction of the (price-implied gap to derived NAV) closed pre-print.

CONFOUND (the central honesty control): BDC price co-moves with credit risk-off, so part of any
move is the market being forward-looking, not a frontrun of the precise mark. We separate:
  - "already priced": price already reflected the spread move at qe (discount vs stale NAV had
    already widened/narrowed in the signal's direction) -> NO edge;
  - "lagged the mark": price at qe still sat near the stale NAV and only converged after -> EDGE.

This module returns the raw measurements; the verdict logic lives in run_bdc_backtest aggregation.
NO look-ahead: prices used are dated >= qe (post-quarter-end, in the public lag window).
"""
import json, os
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))


def nearest_bar(bars, target, side='on_or_after'):
    """bars: list of {date:'YYYY-MM-DD', close:float}. Return the bar on/after (or on/before)."""
    t = date.fromisoformat(target)
    cand = None
    if side == 'on_or_after':
        for b in sorted(bars, key=lambda x: x['date']):
            if date.fromisoformat(b['date']) >= t:
                return b
    else:
        for b in sorted(bars, key=lambda x: x['date'], reverse=True):
            if date.fromisoformat(b['date']) <= t:
                return b
    return cand


def convergence_row(bars, period_end, filing_date, printed_prior, printed_now, derived):
    """All point-in-time prices are within the lag window [period_end, filing_date]."""
    qe = nearest_bar(bars, period_end, 'on_or_after')
    fp = nearest_bar(bars, filing_date, 'on_or_before')
    if not qe or not fp or not printed_prior or not printed_now:
        return None
    p_qe = qe['close']; p_fp = fp['close']
    # discount vs the STALE NAV the market officially sees at quarter-end (frontrun premise)
    prem_stale_qe = p_qe / printed_prior - 1.0
    # price-implied "fair" if it tracked derived NAV
    gap_to_derived_qe = (derived - p_qe) / p_qe if p_qe else None   # +: price below derived
    # at the print, the NEW official NAV is known
    prem_new_fp = p_fp / printed_now - 1.0
    # how much did PRICE move over the lag, and was it toward derived?
    px_move_pct = (p_fp - p_qe) / p_qe if p_qe else None
    # convergence captured pre-print = price move toward derived as frac of qe gap to derived
    conv_frac = None
    if gap_to_derived_qe not in (None, 0):
        conv_frac = (px_move_pct / gap_to_derived_qe) if px_move_pct is not None else None
    return {
        'p_qe_date': qe['date'], 'p_qe': p_qe,
        'p_filing_date': fp['date'], 'p_filing': p_fp,
        'printed_prior': printed_prior, 'printed_now': printed_now, 'derived': derived,
        'prem_vs_stale_qe_pct': round(100*prem_stale_qe, 2),
        'prem_vs_new_print_pct': round(100*prem_new_fp, 2),
        'price_move_lag_pct': round(100*px_move_pct, 2) if px_move_pct is not None else None,
        'gap_to_derived_qe_pct': round(100*gap_to_derived_qe, 2) if gap_to_derived_qe is not None else None,
        'conv_frac_preprint': round(conv_frac, 3) if conv_frac is not None else None,
    }
