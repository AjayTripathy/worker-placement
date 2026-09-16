"""
nport.py — primary-source NPORT-P fetch + fair-value-hierarchy / holdings parser.

Source of authority: SEC EDGAR
  - submissions index:  https://data.sec.gov/submissions/CIK##########.json
  - filing directory:   https://www.sec.gov/Archives/edgar/data/<cik>/<acc_nodash>/
  - NPORT-P primary doc: primary_doc.xml

NPORT-P is filed by registered closed-end funds (CEFs / interval funds / BDCs that
elect RIC-fund reporting). NOTE (load-bearing Phase-1 finding): the large public BDCs
(ARCC, OBDC, FSK, MAIN, PSEC, GBDC) DO NOT file NPORT-P — they file 10-Q/10-K with the
fair-value hierarchy in the Schedule of Investments. See bdc.py for that path.

We model the OFFICIAL mark (spec §3/§6), so we read the fund's own reported curMktValue /
valUSD and fairValLevel exactly as filed; we never re-derive fair value here.

UA header is required by SEC. No look-ahead: callers pick the NPORT filed strictly before T-1.
"""
import time
import requests
import xml.etree.ElementTree as ET

UA = {"User-Agent": "SignalOS Research 4tripathy@gmail.com"}
_SLEEP = 0.15  # be polite to EDGAR


def _lname(tag: str) -> str:
    return tag.split('}')[-1]


def _get(url: str, **kw):
    time.sleep(_SLEEP)
    r = requests.get(url, headers=UA, timeout=60, **kw)
    return r


def submissions(cik: int) -> dict:
    r = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    r.raise_for_status()
    return r.json()


def list_nport_filings(cik: int):
    """Return [(filingDate, form, accession)] of NPORT-P (+/A), newest first, from the
    recent block. (Older than ~1yr would need the paginated 'files' shards — added on demand.)"""
    j = submissions(cik)
    rec = j['filings']['recent']
    out = []
    for i, f in enumerate(rec['form']):
        if f in ('NPORT-P', 'NPORT-P/A'):
            out.append((rec['filingDate'][i], f, rec['accessionNumber'][i]))
    return out


def nport_xml_url(cik: int, accession: str) -> str:
    acc = accession.replace('-', '')
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/primary_doc.xml"


def parse_nport(xml_bytes: bytes) -> dict:
    """Parse an NPORT-P primary_doc.xml into a normalized structure.

    Returns: {
      reg_name, series_name, rep_pd_date, net_assets, tot_assets,
      level_mv: {'1','2','3','N/A'},  l3_pct_nav, l1_pct_nav,
      holdings: [{name, value, level, asset_cat, restricted, pct_nav}]
    }
    """
    root = ET.fromstring(xml_bytes)
    gen = {}
    for el in root.iter():
        ln = _lname(el.tag)
        if ln in ('netAssets', 'totAssets', 'totLiabilities', 'repPdDate',
                  'regName', 'seriesName') and ln not in gen:
            gen[ln] = el.text

    level_mv = {'1': 0.0, '2': 0.0, '3': 0.0, 'N/A': 0.0}
    holdings = []
    for inv in root.iter():
        if _lname(inv.tag) != 'invstOrSec':
            continue
        name = title = val = lvl = cat = restricted = None
        pct = None
        for c in inv.iter():
            ln = _lname(c.tag)
            if ln == 'name':
                name = c.text
            elif ln == 'title' and title is None:
                title = c.text
            elif ln == 'valUSD':
                val = c.text
            elif ln == 'curMktValue' and val is None:
                val = c.text
            elif ln == 'fairValLevel':
                lvl = c.text
            elif ln == 'assetCat':
                cat = c.text
            elif ln == 'isRestrictedSec':
                restricted = c.text
            elif ln == 'pctVal':
                pct = c.text
        try:
            v = float(val)
        except (TypeError, ValueError):
            v = 0.0
        key = lvl if lvl in ('1', '2', '3') else 'N/A'
        level_mv[key] += v
        holdings.append({
            'name': name or title, 'value': v, 'level': lvl,
            'asset_cat': cat, 'restricted': restricted,
            'pct_nav_filed': pct,
        })

    na = float(gen.get('netAssets') or 0) or 0.0
    ta = float(gen.get('totAssets') or 0) or 0.0
    l3 = level_mv['3']
    l1 = level_mv['1']
    for h in holdings:
        h['pct_nav'] = (100.0 * h['value'] / na) if na else None

    return {
        'reg_name': gen.get('regName'),
        'series_name': gen.get('seriesName'),
        'rep_pd_date': gen.get('repPdDate'),
        'net_assets': na,
        'tot_assets': ta,
        'level_mv': level_mv,
        'l3_pct_nav': (100.0 * l3 / na) if na else None,
        'l1_pct_nav': (100.0 * l1 / na) if na else None,
        'l2_pct_nav': (100.0 * level_mv['2'] / na) if na else None,
        'holdings': holdings,
    }


def fetch_parse_latest(cik: int, before_date: str = None) -> dict:
    """Fetch + parse the most recent NPORT-P. If before_date (YYYY-MM-DD) given, the most
    recent NPORT-P filed strictly before it (point-in-time / no look-ahead)."""
    filings = list_nport_filings(cik)
    if before_date:
        filings = [f for f in filings if f[0] < before_date]
    if not filings:
        return None
    fdate, form, acc = filings[0]
    xml = _get(nport_xml_url(cik, acc)).content
    res = parse_nport(xml)
    res['filing_date'] = fdate
    res['accession'] = acc
    res['form'] = form
    return res


if __name__ == '__main__':
    import sys, json
    cik = int(sys.argv[1])
    r = fetch_parse_latest(cik)
    print(json.dumps({k: v for k, v in r.items() if k != 'holdings'}, indent=2, default=str))
    print("TOP:")
    for h in sorted(r['holdings'], key=lambda x: -x['value'])[:6]:
        print("  ", h['name'], f"${h['value']:,.0f}", "L"+str(h['level']), h['asset_cat'])
