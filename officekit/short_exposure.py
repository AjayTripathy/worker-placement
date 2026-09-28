"""Account/holding lineage for short-risk review; no assumed netting or orders."""
from officekit.model import strategy_tags
from officekit.risk_planning import number


def inventory(m):
    positions, gaps = [], []
    for s in m['assets']:
        meta = s.get('meta') or {}
        holdings = s.get('holdings') or ([meta['custody_row']] if meta.get('custody_row') else [])
        known = 0
        for h in holdings:
            for account in h.get('accounts') or [h]:
                value = number(account.get('value', account.get('mv', account.get('amount'))), None)
                qty = number(account.get('qty', h.get('qty')), None)
                if not ((value is not None and value < 0) or (qty is not None and qty < 0)):
                    continue
                kind = str(account.get('sec_type') or h.get('sec_type') or 'STK').upper()
                gross = abs(value) if value is not None else None
                known += gross or 0
                symbol = str(h.get('symbol') or account.get('symbol') or h.get('company') or 'Ticker unavailable')
                strategies = list(dict.fromkeys(strategy_tags(s) + strategy_tags(h) + strategy_tags(account)))
                borrow = number(account.get('borrow_rate_pct', h.get('borrow_rate_pct')), None)
                positions.append({'symbol': symbol, 'sleeve_id': s.get('id'), 'sleeve': s['name'],
                    'account': account.get('account') or h.get('account') or 'Account not supplied',
                    'strategies': strategies, 'gross': gross, 'qty': qty, 'kind': kind,
                    'as_of': account.get('as_of') or h.get('as_of') or m['d']['as_of'],
                    'borrow_rate_pct': borrow, 'annual_borrow_cost': gross * borrow / 100 if gross is not None and borrow is not None else None,
                    'squeeze_50': gross * .5 if gross is not None and kind in {'STK', 'ETF', 'ADR'} else None,
                    'squeeze_100': gross if gross is not None and kind in {'STK', 'ETF', 'ADR'} else None,
                    'thesis': h.get('thesis') or h.get('rationale') or (h.get('adjudication') or {}).get('verdict'),
                    'source': account.get('source') or h.get('source') or 'Imported office holding',
                    'margin': account.get('margin_requirement')})
        reported = max(abs(number(meta.get('gross_short'))), abs(min(0, s['value'])))
        if reported > known + .01:
            gaps.append({'sleeve': s['name'], 'reported': reported, 'unmapped': reported - known,
                         'detail': 'Request current ticker/account holdings from this manager; aggregate short exposure is not a ticker list.'})
        elif not holdings and (s['category'] == 'alpha_market_neutral' or meta.get('gross_long')):
            gaps.append({'sleeve': s['name'], 'reported': None, 'unmapped': None,
                         'detail': 'Manager look-through is missing; short exposure is unknown, not zero.'})
    return {'positions': sorted(positions, key=lambda p: -(p['gross'] or 0)), 'gaps': gaps,
            'known_gross': sum(p['gross'] or 0 for p in positions),
            'note': 'Stock squeeze losses are price sensitivities before financing and long-book offsets. '
                    'Short options need contract-level repricing. Collateral is account-specific; holdings in another account cannot be assumed to offset a call.'}
