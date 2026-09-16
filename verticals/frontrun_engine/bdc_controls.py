"""
bdc_controls.py — honest-stats + confound controls for the Phase-2 BDC frontrun backtest.

The raw hit-rate (run_bdc_backtest) is CONFOUNDED two ways we must break before claiming edge:

 (C1) NAV DRIFT. BDC NAVs trend (ARCC/MAIN up, PSEC/FSK down). If the derived signal merely
      correlates with a per-BDC trend, the directional hit-rate is spurious. Control: demean
      each BDC's realized NAV move by its OWN sample mean and re-score the hit on the demeaned
      realized vs the demeaned signal. Edge must survive detrending.

 (C2) COMMON-SPREAD / NO-CROSS-SECTION. The derived signal is ~monotone in the single HY-OAS
      quarter move, which is IDENTICAL across all BDCs in a given quarter. So the time-series
      hit-rate is really "does the sign of the common spread move predict the sign of the
      (mostly common) NAV move." There is essentially ONE spread bet per quarter, not 6
      independent ones -> the effective N is the number of QUARTERS (~11), not 64. We report
      both the naive N and the quarter-clustered effective N, and a quarter-level sign test.

 (C3) PLACEBO. Shuffle the sign of the spread move across quarters and re-score; the real
      hit-rate must beat the placebo distribution.

Significance: two-sided sign test (binomial) of hits vs 0.5, at naive N and at clustered N.
"""
import json, os, math, random, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'outputs')


def binom_two_sided_p(k, n, p=0.5):
    """exact two-sided binomial p-value for k successes in n at prob p."""
    if n == 0:
        return None
    from math import comb
    def pmf(i):
        return comb(n, i) * p**i * (1-p)**(n-i)
    obs = pmf(k)
    return min(1.0, sum(pmf(i) for i in range(n+1) if pmf(i) <= obs + 1e-15))


def load():
    return json.load(open(os.path.join(OUT, 'phase2_bdc_backtest.json')))


def run():
    bt = load()
    rows = [r for r in bt['rows'] if r['realized_nav_qoq_pct'] is not None
            and r['derived_surprise_pct'] not in (None, 0)]
    # drop the parse-artifact outlier (MAIN 2024-03-31 derived +8.55% = tie-out noise, not real)
    rows = [r for r in rows if abs(r['derived_surprise_pct']) < 5.0]

    # ---- naive hit-rate ----
    hits = [(1 if (r['derived_surprise_pct'] > 0) == (r['realized_nav_qoq_pct'] > 0) else 0)
            for r in rows]
    naive_hr = sum(hits)/len(hits)
    naive_p = binom_two_sided_p(sum(hits), len(hits))

    # ---- C1: detrend per-BDC realized NAV move, re-score ----
    by_bdc = defaultdict(list)
    for r in rows:
        by_bdc[r['bdc']].append(r)
    bdc_mean_move = {b: st.mean([x['realized_nav_qoq_pct'] for x in v]) for b, v in by_bdc.items()}
    # also demean the SIGNAL per bdc (signal is common across bdcs but has tiny per-bdc scale diffs)
    sig_mean = st.mean([r['derived_surprise_pct'] for r in rows])
    det_hits = []
    for r in rows:
        dr = r['realized_nav_qoq_pct'] - bdc_mean_move[r['bdc']]
        ds = r['derived_surprise_pct'] - sig_mean
        if dr == 0 or ds == 0:
            continue
        det_hits.append(1 if (ds > 0) == (dr > 0) else 0)
    det_hr = sum(det_hits)/len(det_hits) if det_hits else None
    det_p = binom_two_sided_p(sum(det_hits), len(det_hits)) if det_hits else None

    # ---- C2: quarter-clustered effective N + quarter-level sign test ----
    by_q = defaultdict(list)
    for r in rows:
        by_q[r['period_end']].append(r)
    q_rows = []
    for q, v in sorted(by_q.items()):
        sig = st.mean([x['derived_surprise_pct'] for x in v])        # ~common
        real = st.mean([x['realized_nav_qoq_pct'] for x in v])       # cross-BDC avg NAV move
        med_real = st.median([x['realized_nav_qoq_pct'] for x in v])
        hit = 1 if (sig > 0) == (real > 0) else 0
        q_rows.append({'q': q, 'n_bdc': len(v), 'sig_pct': round(sig,3),
                       'avg_real_pct': round(real,3), 'med_real_pct': round(med_real,3),
                       'qhit': hit})
    q_hits = [x['qhit'] for x in q_rows]
    q_hr = sum(q_hits)/len(q_hits) if q_hits else None
    q_p = binom_two_sided_p(sum(q_hits), len(q_hits)) if q_hits else None

    # ---- C2b: detrended quarter-level (demean the avg NAV move across quarters) ----
    qmean = st.mean([x['avg_real_pct'] for x in q_rows])
    qdet_hits = []
    for x in q_rows:
        dr = x['avg_real_pct'] - qmean
        ds = x['sig_pct'] - st.mean([y['sig_pct'] for y in q_rows])
        if dr == 0 or ds == 0:
            continue
        qdet_hits.append(1 if (ds > 0) == (dr > 0) else 0)
    qdet_hr = sum(qdet_hits)/len(qdet_hits) if qdet_hits else None
    qdet_p = binom_two_sided_p(sum(qdet_hits), len(qdet_hits)) if qdet_hits else None

    # ---- C3: placebo (shuffle spread-move sign across quarters), 5000 draws ----
    random.seed(42)
    quarters = sorted(by_q)
    q_signal_sign = {x['q']: (1 if x['sig_pct'] > 0 else -1) for x in q_rows}
    q_real_sign = {x['q']: (1 if x['avg_real_pct'] > 0 else -1) for x in q_rows}
    real_qhr = sum(1 for q in quarters if q_signal_sign[q] == q_real_sign[q]) / len(quarters)
    placebo = []
    signs = list(q_signal_sign.values())
    for _ in range(5000):
        sh = signs[:]; random.shuffle(sh)
        hr = sum(1 for s, q in zip(sh, quarters) if s == q_real_sign[q]) / len(quarters)
        placebo.append(hr)
    pct_beat = sum(1 for h in placebo if h >= real_qhr) / len(placebo)

    # ---- magnitude (detrended) corr ----
    xs = [r['derived_surprise_pct'] - sig_mean for r in rows]
    ys = [r['realized_nav_qoq_pct'] - bdc_mean_move[r['bdc']] for r in rows]
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x-mx)**2 for x in xs); syy = sum((y-my)**2 for y in ys)
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    det_corr = sxy/math.sqrt(sxx*syy) if (sxx and syy) else None

    return {
        'n_events': len(rows),
        'naive_hit_rate': round(naive_hr, 4), 'naive_n': len(hits),
        'naive_sign_test_p': round(naive_p, 4),
        'C1_detrended_hit_rate': round(det_hr, 4) if det_hr is not None else None,
        'C1_detrended_n': len(det_hits), 'C1_detrended_p': round(det_p, 4) if det_p else None,
        'C1_detrended_magnitude_corr': round(det_corr, 4) if det_corr is not None else None,
        'C2_quarter_clustered_hit_rate': round(q_hr, 4) if q_hr is not None else None,
        'C2_n_quarters': len(q_hits), 'C2_quarter_sign_test_p': round(q_p, 4) if q_p else None,
        'C2b_quarter_detrended_hit_rate': round(qdet_hr, 4) if qdet_hr is not None else None,
        'C2b_n': len(qdet_hits), 'C2b_p': round(qdet_p, 4) if qdet_p else None,
        'C3_placebo_real_quarter_hr': round(real_qhr, 4),
        'C3_placebo_pct_beat': round(pct_beat, 4),
        'per_bdc_mean_nav_move_pct': {b: round(m, 3) for b, m in bdc_mean_move.items()},
        'quarter_table': q_rows,
    }


if __name__ == '__main__':
    r = run()
    qt = r.pop('quarter_table')
    print(json.dumps(r, indent=2))
    print("\nQuarter-level (cross-BDC avg) — the effective independent bets:")
    print(f"{'quarter':12}{'nBDC':>5}{'sig%':>9}{'avgNAV%':>10}{'medNAV%':>10}{'hit':>5}")
    for x in qt:
        print(f"{x['q']:12}{x['n_bdc']:>5}{x['sig_pct']:>9.3f}{x['avg_real_pct']:>10.3f}"
              f"{x['med_real_pct']:>10.3f}{x['qhit']:>5}")
    r['quarter_table'] = qt
    json.dump(r, open(os.path.join(OUT, 'phase2_bdc_controls.json'), 'w'), indent=1, default=str)
