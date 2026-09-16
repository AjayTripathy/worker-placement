"""
run_bdc_soi.py — batch the A-5 BDC Schedule-of-Investments parser over the 6 high-moat BDCs.

Writes outputs/bdc_holdings/<ticker>_<period>.json and prints a parse-quality table:
  CLEAN     : FV ties balance-sheet total investments within 2%
  USABLE    : within 5% (moat metric + NAV reconstruction reliable; holdings sum has residual)
  NEEDS_WORK: > 5% tie-out residual (subtotal de-duplication incomplete)
The moat metric (L3% from the filed aggregate) and NAV reconstruction (net assets / shares)
do NOT depend on the holdings-sum tie-out, so they are reported for every BDC regardless.
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import bdc_soi

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      'outputs', 'bdc_holdings')


def grade(pct):
    a = abs(pct)
    if a < 2.0:
        return 'CLEAN'
    if a < 5.0:
        return 'USABLE'
    return 'NEEDS_WORK'


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    rows = []
    for tk in ['ARCC', 'FSK', 'GBDC', 'OBDC', 'MAIN', 'PSEC']:
        p = bdc_soi.fetch_parse_soi(tk)
        t = p['tie_out']
        nav_recon = (p['net_assets'] / p['shares_outstanding']
                     if (p['net_assets'] and p['shares_outstanding']) else None)
        nerr = (abs(nav_recon - p['nav_per_share_filed'])
                if (nav_recon and p['nav_per_share_filed']) else None)
        g = grade(t['pct_diff']) if t['pct_diff'] is not None else 'NO_TIE'
        p['parse_grade'] = g
        p['nav_reconstruction'] = {'recon_nav_ps': nav_recon,
                                   'filed_nav_ps': p['nav_per_share_filed'],
                                   'error': nerr}
        fn = os.path.join(OUTDIR, f"{tk}_{p['period']}.json")
        json.dump(p, open(fn, 'w'), indent=1, default=str)
        rows.append((tk, p, t, nav_recon, nerr, g))

    print(f"\n{'TK':5}{'period':12}{'form':6}{'n':>6}{'FV$B':>9}{'BS$B':>9}"
          f"{'tie%':>8}{'L3%':>8}{'NAVf':>8}{'NAVrec':>8}{'err':>8}  grade")
    for tk, p, t, nr, ne, g in rows:
        print(f"{tk:5}{p['period']:12}{p['form']:6}{p['n_holdings']:>6}"
              f"{p['total_fair_value']/1e9:>9.2f}"
              f"{(t['bs_total_investments'] or 0)/1e9:>9.2f}"
              f"{t['pct_diff']:>+8.2f}{(p['l3_pct_invest'] or 0):>8.2f}"
              f"{(p['nav_per_share_filed'] or 0):>8.2f}{(nr or 0):>8.2f}"
              f"{(ne if ne is not None else float('nan')):>8.4f}  {g}")


if __name__ == '__main__':
    main()
