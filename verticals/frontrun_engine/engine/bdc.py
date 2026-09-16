"""
bdc.py — fair-value-hierarchy extraction for BDCs (which do NOT file NPORT-P).

Load-bearing Phase-1 finding: ARCC/OBDC/FSK/MAIN/PSEC/GBDC are BDCs. They file 10-Q/10-K
(not NPORT-P), so the Level-1/2/3 split and the Schedule of Investments live inside the
10-Q, not in a clean NPORT XML. We approximate the moat score from XBRL companyfacts:

  L3 value  = us-gaap:FairValueMeasurementWithUnobservableInputsReconciliationRecurringBasisAssetValue
              (the ending balance of the Level-3 rollforward — recurring fair-value assets)
  total inv = us-gaap:InvestmentOwnedAtFairValue  (total investment portfolio at fair value)

Moat denominator note (spec §2 says "% of NAV"): for a *levered* BDC, L3/NAV can exceed
100%. The economically meaningful "fraction of the markable book that is hard to aggregate"
is L3 / total-investments, which is what we report as `l3_pct_invest`. We also report
l3_pct_nav (vs net assets) for spec literalism; classification uses l3_pct_invest because
that is the quantity the moat hypothesis is actually about (how much of the portfolio the
market cannot independently re-mark). This is logged as proposed amendment A-1.

CAVEAT: companyfacts is the convenience path. The authoritative figure is the
fair-value-hierarchy table inside each 10-Q; for any fund that goes to Phase 2 the L3 split
should be re-confirmed against the filed 10-Q table (the XBRL reconciliation ending value
can differ from the balance-sheet L3 column by transfers/derivatives). Flagged, not hidden.
"""
import time
import requests

UA = {"User-Agent": "SignalOS Research 4tripathy@gmail.com"}
_SLEEP = 0.15


def _facts(cik: int) -> dict:
    time.sleep(_SLEEP)
    r = requests.get(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
        headers=UA, timeout=60)
    r.raise_for_status()
    return r.json()


def _latest_instant(usg: dict, concept: str, before_date: str = None):
    if concept not in usg:
        return None
    arr = usg[concept]['units'].get('USD', [])
    pts = [x for x in arr if 'end' in x and 'start' not in x]
    if before_date:
        # point-in-time: balance must be as-of a date whose FILING was before before_date
        pts = [x for x in pts if x.get('filed', '9999') < before_date]
    if not pts:
        return None
    pts.sort(key=lambda x: (x['end'], x.get('filed', '')))
    return pts[-1]


def moat_score(cik: int, before_date: str = None) -> dict:
    j = _facts(cik)
    usg = j['facts'].get('us-gaap', {})
    l3 = _latest_instant(usg, 'FairValueMeasurementWithUnobservableInputsReconciliationRecurringBasisAssetValue', before_date)
    tot = _latest_instant(usg, 'InvestmentOwnedAtFairValue', before_date)
    if tot is None:
        tot = _latest_instant(usg, 'InvestmentsFairValueDisclosure', before_date)
    na = _latest_instant(usg, 'StockholdersEquity', before_date) \
        or _latest_instant(usg, 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest', before_date)
    out = {
        'cik': cik,
        'l3_value': l3['val'] if l3 else None,
        'l3_end': l3['end'] if l3 else None,
        'total_invest': tot['val'] if tot else None,
        'total_invest_end': tot['end'] if tot else None,
        'net_assets': na['val'] if na else None,
    }
    if l3 and tot and tot['val']:
        out['l3_pct_invest'] = 100.0 * l3['val'] / tot['val']
    if l3 and na and na['val']:
        out['l3_pct_nav'] = 100.0 * l3['val'] / na['val']
    return out


if __name__ == '__main__':
    import sys, json
    print(json.dumps(moat_score(int(sys.argv[1])), indent=2, default=str))
