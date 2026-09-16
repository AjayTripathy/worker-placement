"""
build_bdc_panel.py — assemble the point-in-time BDC NAV/spread panel for the Phase-2
spread-driven frontrun backtest (PILOT_SPEC §1, §4, A-4/A-5).

For each clean BDC (ARCC, GBDC, OBDC, PSEC; FSK/MAIN included with a tie-out caveat) we
enumerate every 10-Q/10-K, parse its Schedule of Investments from primary inline-XBRL, and
record per quarter:
  period_end, filing_date, filing_lag_days, printed NAV/share (net_assets/shares),
  L3% (moat metric, A-1), n_holdings, debt-vs-equity FV split (for the spread channel).

The HY OAS spread series (FRED BAMLH0A0HYM2) is loaded once and the quarter-end + prior-print
level recorded so the derived-NAV re-mark (engine.bdc_soi.remark_book) can be applied.

NO LOOK-AHEAD: each quarter uses only its own filing; the spread driver for quarter T uses the
move from the PRIOR print's period-end to T's period-end (both observable at/just-after T's
quarter-end, before T's 10-Q is filed ~30-45 days later).

Output: outputs/bdc_panel.json
"""
import sys, os, json, csv, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import bdc_soi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'outputs')
PANEL_DIR = os.path.join(OUT, 'bdc_holdings_panel')
os.makedirs(PANEL_DIR, exist_ok=True)

BDCS = ['ARCC', 'GBDC', 'OBDC', 'PSEC', 'FSK', 'MAIN']
# how many most-recent quarters to pull (8-12 per spec)
MAX_Q = 12
# spread history only goes back to ~2023-06 (FRED free CSV 3yr window); restrict panel start
SPREAD_START = '2023-06-26'


def load_spread(path='/tmp/hy_oas.csv'):
    rows = [(d, float(v)) for d, v in csv.reader(open(path))
            if d[:1].isdigit() and v not in ('.', '')]
    rows.sort()
    return rows


def spread_asof(rows, target):
    cand = [r for r in rows if r[0] <= target]
    return cand[-1][1] if cand else None


def all_filings(ticker):
    cik = bdc_soi.BDC_CIK[ticker]
    j = bdc_soi.submissions(cik)
    rec = j['filings']['recent']
    rows = []
    for i, f in enumerate(rec['form']):
        if f in ('10-Q', '10-K'):
            rows.append({'filing_date': rec['filingDate'][i], 'form': f,
                         'accession': rec['accessionNumber'][i],
                         'primary': rec['primaryDocument'][i],
                         'report_date': rec['reportDate'][i]})
    rows.sort(key=lambda r: r['report_date'], reverse=True)
    return rows, cik


def datediff(d1, d0):
    from datetime import date
    a = date.fromisoformat(d1); b = date.fromisoformat(d0)
    return (a - b).days


def debt_equity_split(parsed):
    debt = equity = other = 0.0
    for h in parsed['holdings']:
        t = h['investment_type']
        v = h['fair_value']
        if t in ('1st_lien', '2nd_lien', 'subordinated', 'structured'):
            debt += v
        elif t == 'equity':
            equity += v
        else:
            other += v
    tot = debt + equity + other
    return {'debt_fv': debt, 'equity_fv': equity, 'other_fv': other,
            'debt_pct': 100*debt/tot if tot else None,
            'equity_pct': 100*equity/tot if tot else None}


def build():
    spread = load_spread()
    panel = {}
    for tk in BDCS:
        filings, cik = all_filings(tk)
        filings = [f for f in filings if f['report_date'] >= '2023-03-31'][:MAX_Q+1]
        quarters = []
        for f in filings:
            acc = f['accession']; pdoc = f['primary']
            try:
                xml = bdc_soi._get(bdc_soi._xbrl_instance_url(cik, acc, pdoc)).text
                p = bdc_soi.parse_soi(xml)
            except Exception as e:
                print(f"  {tk} {f['report_date']} PARSE-ERR {e}")
                continue
            shares = p['shares_outstanding']; na = p['net_assets']
            navps = p['nav_per_share_filed'] or (na/shares if (na and shares) else None)
            lag = datediff(f['filing_date'], f['report_date'])
            row = {
                'period_end': p['period'] or f['report_date'],
                'report_date': f['report_date'],
                'filing_date': f['filing_date'],
                'filing_lag_days': lag,
                'form': f['form'],
                'accession': acc,
                'nav_per_share_filed': round(navps, 4) if navps else None,
                'net_assets': na,
                'shares_outstanding': shares,
                'l3_pct_invest': round(p['l3_pct_invest'], 2) if p['l3_pct_invest'] else None,
                'n_holdings': p['n_holdings'],
                'total_fair_value': p['total_fair_value'],
                'tie_pct': round(p['tie_out']['pct_diff'], 2) if p['tie_out']['pct_diff'] is not None else None,
                'debt_equity': debt_equity_split(p),
                'hy_oas_qend': spread_asof(spread, f['report_date']),
            }
            quarters.append(row)
            # cache slim holdings for the re-mark step
            slim = {k: p[k] for k in ('period','holdings','net_assets','shares_outstanding',
                                      'nav_per_share_filed','total_fair_value','l3_pct_invest')}
            json.dump(slim, open(os.path.join(PANEL_DIR, f"{tk}_{row['period_end']}.json"),'w'),
                      default=str)
            print(f"  {tk} {row['period_end']} {f['form']:5} NAV={row['nav_per_share_filed']} "
                  f"L3={row['l3_pct_invest']} lag={lag}d tie={row['tie_pct']}% spr={row['hy_oas_qend']}")
        quarters.sort(key=lambda r: r['period_end'])
        # attach prior-print spread + qoq move
        for i, q in enumerate(quarters):
            if i == 0:
                q['hy_oas_prior'] = None; q['hy_oas_qoq_bp'] = None
                q['nav_qoq_pct'] = None
            else:
                pr = quarters[i-1]
                q['hy_oas_prior'] = pr['hy_oas_qend']
                q['hy_oas_qoq_bp'] = (round((q['hy_oas_qend']-pr['hy_oas_qend'])*100, 1)
                                      if (q['hy_oas_qend'] and pr['hy_oas_qend']) else None)
                q['nav_qoq_pct'] = (round(100*(q['nav_per_share_filed']-pr['nav_per_share_filed'])
                                          /pr['nav_per_share_filed'], 3)
                                    if (q['nav_per_share_filed'] and pr['nav_per_share_filed']) else None)
        panel[tk] = quarters
    return panel


if __name__ == '__main__':
    print("Building BDC panel (point-in-time, primary XBRL)...")
    panel = build()
    json.dump(panel, open(os.path.join(OUT, 'bdc_panel.json'), 'w'), indent=1, default=str)
    n = sum(len(v) for v in panel.values())
    print(f"\nPanel: {len(panel)} BDCs, {n} quarter-rows -> outputs/bdc_panel.json")
