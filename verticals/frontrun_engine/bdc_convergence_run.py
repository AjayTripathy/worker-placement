"""
bdc_convergence_run.py — convergence + control-arm test (PILOT_SPEC §5b/§5c, §6 confound, §7).

Two questions the spread-vs-NAV null still leaves open, answered here from primary prices:

 Q-CONV (the frontrun mechanic). At quarter-end T the market officially sees the STALE printed
   NAV(T-1) for ~30-45 days. Did the price/discount LAG the (small) spread-driven mark and then
   converge at the print (=edge), or had the discount ALREADY moved with the spread before the
   print (=no edge, market already forward-looking)? Test: correlation of the CONTEMPORANEOUS
   quarterly price move with the quarterly spread move. High contemporaneous |corr| => the
   discount tracks credit in real time => nothing to frontrun.

 Q-CTRL (the §7 primary). The liquid-equity CEFs ADX/USA carry daily NAV that already embeds any
   holding move; there is no quarterly-filing-lag NAV at all. We confirm their discount shows NO
   relationship to the HY-OAS spread move (the BDC driver) => edge(control) ~ 0 by construction.

Prices: outputs/bdc_prices/month_end.json (IBKR). Spread: /tmp/hy_oas.csv (FRED). NAV: panel.
"""
import json, os, csv, math, statistics as st
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'outputs')

QENDS = ['2024-06-30','2024-09-30','2024-12-31','2025-03-31','2025-06-30',
         '2025-09-30','2025-12-31','2026-03-31']
# month-end proxy: the month-start session whose close we use for each quarter-end + lag point
QE_PX_DATE = {'2024-06-30':'2024-07-01','2024-09-30':'2024-10-01','2024-12-31':'2025-01-02',
              '2025-03-31':'2025-04-01','2025-06-30':'2025-07-01','2025-09-30':'2025-10-01',
              '2025-12-31':'2026-01-02','2026-03-31':'2026-04-01'}


def load_prices():
    d = json.load(open(os.path.join(OUT, 'bdc_prices', 'month_end.json')))
    dates = d['dates']; idx = {dt: i for i, dt in enumerate(dates)}
    return d['close'], idx


def load_spread():
    rows = [(dt, float(v)) for dt, v in csv.reader(open('/tmp/hy_oas.csv'))
            if dt[:1].isdigit() and v not in ('.', '')]
    rows.sort()
    def asof(t):
        c = [r for r in rows if r[0] <= t]
        return c[-1][1] if c else None
    return asof


def corr(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x-mx)**2 for x in xs); syy = sum((y-my)**2 for y in ys)
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    return sxy/math.sqrt(sxx*syy) if (sxx and syy) else None


def run():
    close, idx = load_prices()
    sp = load_spread()
    panel = json.load(open(os.path.join(OUT, 'bdc_panel.json')))
    # printed NAV per (bdc, quarter-end)
    nav = {}
    for tk, qs in panel.items():
        for q in qs:
            nav[(tk, q['period_end'])] = q['nav_per_share_filed']

    # spread quarter move (bp), contemporaneous
    spr_move = {}
    prev = None
    for qe in ['2024-03-31'] + QENDS:
        s = sp(qe)
        if prev is not None:
            spr_move[qe] = (s - prev[1]) * 100
        prev = (qe, s)

    out = {'contemporaneous_price_vs_spread': {}, 'control': {}, 'discount_table': {}}

    # ---- BDC: contemporaneous quarterly PRICE return vs spread move ----
    for tk in ['ARCC','GBDC','OBDC','PSEC','FSK','MAIN']:
        prs, sprs, discs = [], [], []
        disc_rows = []
        prev_px = None
        for qe in QENDS:
            pxd = QE_PX_DATE[qe]
            if pxd not in idx:
                continue
            px = close[tk][idx[pxd]]
            navv = nav.get((tk, qe))
            disc = (px/navv - 1)*100 if navv else None
            if prev_px is not None and qe in spr_move:
                prs.append((px-prev_px)/prev_px*100)
                sprs.append(spr_move[qe])
            disc_rows.append({'qe': qe, 'px_date': pxd, 'px': px, 'printed_nav': navv,
                              'discount_pct': round(disc,2) if disc is not None else None})
            prev_px = px
        out['contemporaneous_price_vs_spread'][tk] = {
            'corr_qret_vs_spreadmove': round(corr(sprs, prs), 3) if corr(sprs, prs) is not None else None,
            'n': len(prs),
            'mean_discount_pct': round(st.mean([r['discount_pct'] for r in disc_rows
                                                if r['discount_pct'] is not None]), 2),
        }
        out['discount_table'][tk] = disc_rows

    # ---- CONTROL ADX/USA: quarterly price return vs the SAME spread move ----
    for tk in ['ADX','USA']:
        prs, sprs = [], []
        prev_px = None
        for qe in QENDS:
            pxd = QE_PX_DATE[qe]
            if pxd not in idx:
                continue
            px = close[tk][idx[pxd]]
            if prev_px is not None and qe in spr_move:
                prs.append((px-prev_px)/prev_px*100)
                sprs.append(spr_move[qe])
            prev_px = px
        out['control'][tk] = {
            'corr_qret_vs_spreadmove': round(corr(sprs, prs), 3) if corr(sprs, prs) is not None else None,
            'n': len(prs),
            'note': 'liquid-equity CEF: daily NAV embeds holding moves; no quarterly-filing-lag NAV exists, so no analogous frontrun window (edge=0 by construction)'
        }
    return out


if __name__ == '__main__':
    r = run()
    print("CONTEMPORANEOUS quarterly PRICE-return vs HY-OAS spread move (the confound test):")
    print("  high |corr| => discount tracks credit in REAL TIME => no lag to frontrun\n")
    print(f"  {'BDC':6}{'corr':>8}{'n':>4}{'meanDisc%':>11}")
    for tk, v in r['contemporaneous_price_vs_spread'].items():
        print(f"  {tk:6}{(v['corr_qret_vs_spreadmove'] if v['corr_qret_vs_spreadmove'] is not None else float('nan')):>8.3f}"
              f"{v['n']:>4}{v['mean_discount_pct']:>11.2f}")
    print("\n  CONTROL (liquid-equity CEFs):")
    for tk, v in r['control'].items():
        print(f"  {tk:6}{(v['corr_qret_vs_spreadmove'] if v['corr_qret_vs_spreadmove'] is not None else float('nan')):>8.3f}{v['n']:>4}")
    json.dump(r, open(os.path.join(OUT, 'phase2_bdc_convergence.json'),'w'), indent=1, default=str)
    print("\n-> outputs/phase2_bdc_convergence.json")
