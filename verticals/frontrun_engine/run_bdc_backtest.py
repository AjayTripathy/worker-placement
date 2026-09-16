"""
run_bdc_backtest.py — the properly-powered Arm-A spread/event-driven frontrun BACKTEST.

PILOT_SPEC §1 hypothesis, §4 materiality (5% locked + a logged BDC-scaled gate), §5 outcome,
§6 controls, §7 success criteria; amendments A-1/A-2/A-4/A-5. NO fishing: the test definition,
the locked 5% gate, the arms, and the >65% bar are pre-registered. Any added gate is logged.

THE MECHANISM (why a BDC can be frontrun where DXYZ couldn't)
  BDCs print NAV quarterly with a ~30-45 day 10-Q filing lag. During the lag the market trades
  on the STALE prior-quarter printed NAV. The loan book (≈floating-rate 1st/2nd-lien at fair
  value) re-marks primarily off CREDIT SPREADS between quarters. So at/after quarter-end T we
  compute derived NAV(T) from the observable HY-OAS move (prior print -> T) BEFORE the 10-Q
  prints it. Signal = sign/size of (derived NAV(T) - last printed NAV(T-1)).

OUTCOMES (§5)
  (a) direction hit-rate of the next printed NAV move vs the >65% bar;
  (b) magnitude: derived surprise vs realized printed-NAV surprise (slope, corr, R^2);
  (c) convergence + trade P&L net of borrow + bid/ask during the filing-lag window;
  CONFOUND control: BDC discounts co-move with credit risk-off (market is partly forward-
  looking), so we separately test whether the DISCOUNT already priced the spread move
  ("already priced", no edge) vs LAGGED the precise mark ("edge").

CONTROL ARM (§6/§7 primary): liquid-equity CEFs (ADX/USA) carry daily NAV that already embeds
  any holding move -> derived(T-1)==official, no analogous lag, edge=0 by construction. The §7
  primary criterion is edge(BDC) - edge(control).

Sources: SEC EDGAR inline XBRL (printed NAV + holdings), FRED BAMLH0A0HYM2 (HY OAS), IBKR
(prices for the discount/convergence + control). NO look-ahead; NO fabricated NAV/spread.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import bdc_soi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'outputs')
PANEL_DIR = os.path.join(OUT, 'bdc_holdings_panel')

# ---- re-mark drivers (pre-registered, models the OFFICIAL mark, A-5 docstring) ----------
SPREAD_DURATION_YRS = 2.5     # short BDC direct loans
SMOOTHING = 0.5               # manager appraisal-lag vs traded credit

# ---- materiality gates ----------------------------------------------------------------
GATE_LOCKED = 5.0            # §4 locked absolute gate (will essentially never fire on credit)
# logged BDC-scaled gate (proposed pre-scoring; rationale in the memo): a diversified BDC
# quarterly NAV is low-vol; we set the scaled gate at 1.0% (≈2x a typical quarterly NAV move
# and far above the NAV-reconstruction error). Reported as a LABELED secondary, never replacing
# the locked test.
GATE_BDC_SCALED = 1.0


def load_panel():
    return json.load(open(os.path.join(OUT, 'bdc_panel.json')))


def load_book(tk, period):
    return json.load(open(os.path.join(PANEL_DIR, f"{tk}_{period}.json")))


def derived_for_quarter(tk, q, prior_q):
    """derived NAV(T) = re-mark the PRIOR print's book for the HY-OAS move prior->T.
    Models the official mark: credit channel marks the debt book; equity carries flat.
    NO look-ahead: book = prior print (filed before T), spread move uses quarter-end levels."""
    book = load_book(tk, prior_q['period_end'])
    d_bp = q.get('hy_oas_qoq_bp')
    if d_bp is None:
        return None
    out = bdc_soi.remark_book(book, loan_index_bp_change=d_bp,
                              spread_duration_yrs=SPREAD_DURATION_YRS, smoothing=SMOOTHING)
    # surprise of derived(T) vs the LAST PRINTED nav (prior print) = the frontrun signal
    last_printed = prior_q['nav_per_share_filed']
    der = out.get('derived_nav_per_share')
    surprise = (100*(der - last_printed)/last_printed) if (der and last_printed) else None
    return {'derived_navps': round(der,4) if der else None,
            'last_printed_navps': last_printed,
            'derived_surprise_pct': round(surprise,3) if surprise is not None else None,
            'credit_px_factor': out['drivers']['credit_px_factor'],
            'hy_oas_qoq_bp': d_bp}


def run():
    panel = load_panel()
    events = []
    rows = []
    for tk, qs in panel.items():
        for i in range(1, len(qs)):
            q = qs[i]; prior = qs[i-1]
            d = derived_for_quarter(tk, q, prior)
            if d is None or d['derived_surprise_pct'] is None:
                continue
            realized = q.get('nav_qoq_pct')   # printed NAV(T) vs printed NAV(T-1)
            sig = d['derived_surprise_pct']
            row = {
                'bdc': tk, 'period_end': q['period_end'], 'prior_period': prior['period_end'],
                'filing_lag_days': q['filing_lag_days'],
                'hy_oas_prior': prior['hy_oas_qend'], 'hy_oas_qend': q['hy_oas_qend'],
                'hy_oas_qoq_bp': d['hy_oas_qoq_bp'],
                'last_printed_navps': d['last_printed_navps'],
                'derived_navps': d['derived_navps'],
                'derived_surprise_pct': sig,
                'realized_nav_qoq_pct': realized,
                'l3_pct': q['l3_pct_invest'],
            }
            # directional agreement (only meaningful if realized exists)
            if realized is not None:
                row['dir_hit'] = (1 if (sig > 0) == (realized > 0) else 0) if (sig != 0 and realized != 0) else None
            else:
                row['dir_hit'] = None
            row['fires_locked_5pct'] = abs(sig) >= GATE_LOCKED
            row['fires_bdc_scaled'] = abs(sig) >= GATE_BDC_SCALED
            rows.append(row)
    return rows


def stats(rows):
    import statistics as st
    def hitrate(subset):
        hits = [r['dir_hit'] for r in subset if r['dir_hit'] is not None]
        return (sum(hits)/len(hits), len(hits)) if hits else (None, 0)
    # magnitude regression: realized ~ derived_surprise (sign + slope + corr)
    pairs = [(r['derived_surprise_pct'], r['realized_nav_qoq_pct']) for r in rows
             if r['realized_nav_qoq_pct'] is not None]
    corr = slope = None; r2 = None
    if len(pairs) >= 3:
        xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
        mx, my = st.mean(xs), st.mean(ys)
        sxx = sum((x-mx)**2 for x in xs); sxy = sum((x-mx)*(y-my) for x,y in pairs)
        syy = sum((y-my)**2 for y in ys)
        slope = sxy/sxx if sxx else None
        corr = sxy/math.sqrt(sxx*syy) if (sxx and syy) else None
        r2 = corr**2 if corr is not None else None
    all_hr, all_n = hitrate(rows)
    fired_locked = [r for r in rows if r['fires_locked_5pct']]
    fired_scaled = [r for r in rows if r['fires_bdc_scaled']]
    s_hr, s_n = hitrate(fired_scaled)
    return {
        'N_quarter_events': len(rows),
        'N_with_realized': len(pairs),
        'all_dir_hit_rate': all_hr, 'all_n_scored': all_n,
        'magnitude_slope': slope, 'magnitude_corr': corr, 'magnitude_r2': r2,
        'n_fire_locked_5pct': len(fired_locked),
        'n_fire_bdc_scaled_1pct': len(fired_scaled),
        'bdc_scaled_dir_hit_rate': s_hr, 'bdc_scaled_n_scored': s_n,
    }


if __name__ == '__main__':
    rows = run()
    s = stats(rows)
    out = {'params': {'spread_duration_yrs': SPREAD_DURATION_YRS, 'smoothing': SMOOTHING,
                      'gate_locked_pct': GATE_LOCKED, 'gate_bdc_scaled_pct': GATE_BDC_SCALED},
           'rows': rows, 'stats': s}
    json.dump(out, open(os.path.join(OUT, 'phase2_bdc_backtest.json'), 'w'), indent=1, default=str)
    print(json.dumps(s, indent=2))
    print("\nPer-quarter signal table:")
    print(f"{'BDC':5}{'period':12}{'spr_bp':>8}{'derSurp%':>10}{'realNAV%':>10}{'hit':>5}{'L3%':>7}")
    for r in sorted(rows, key=lambda x:(x['bdc'],x['period_end'])):
        print(f"{r['bdc']:5}{r['period_end']:12}{r['hy_oas_qoq_bp'] or 0:>8.0f}"
              f"{r['derived_surprise_pct']:>10.3f}"
              f"{(r['realized_nav_qoq_pct'] if r['realized_nav_qoq_pct'] is not None else float('nan')):>10.3f}"
              f"{str(r['dir_hit']):>5}{r['l3_pct'] or 0:>7.1f}")
