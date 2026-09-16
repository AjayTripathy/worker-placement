"""
bdc_soi.py — BDC 10-Q/10-K Schedule-of-Investments parser + derived-NAV re-mark.

PILOT_SPEC amendment A-5: brings the high-moat BDCs (ARCC, FSK, GBDC, OBDC, MAIN, PSEC)
into Arm A at quarterly cadence. These funds do NOT file NPORT-P (load-bearing Phase-1
finding, see engine/bdc.py + engine/nport.py); their holdings live only in the 10-Q/10-K
"Consolidated Schedule of Investments." This module reads that schedule from the PRIMARY
source and computes the moat metric (A-1: L3 / total investments) and a re-markable book.

PARSING STRATEGY (why XBRL, not the HTML table)
-----------------------------------------------
The SoI is rendered in the financial-report R-files (e.g. R5.htm) as a *vertical* XBRL
dump — one (concept, value) cell per axis member — which double-counts issuer subtotals and
is fragile to parse positionally. The authoritative, robust source is the INLINE XBRL
instance (``<accession>/<ticker>-<date>_htm.xml``): every holding is a fact
``us-gaap:InvestmentOwnedAtFairValue`` whose context carries a *typed member* on
``us-gaap:InvestmentIdentifierAxis`` ("<issuer>, <investment type>") and an explicit
``<instant>`` period. We:
  1. parse all contexts (instant + typed identifier + explicit dimensions);
  2. take FV / cost / principal / coupon / spread facts for the CURRENT period instant that
     carry a typed identifier;
  3. drop issuer-rollup subtotals (a typed id H is a subtotal iff another id starts with
     "H," — e.g. "Ivy Hill Asset Management, L.P." rolls up its tranches);
  4. tie the surviving per-holding FV sum to the balance-sheet total investments.

FAIR-VALUE LEVEL (L1/L2/L3) — DATA-QUALITY CAVEAT
-------------------------------------------------
BDCs do NOT tag a fair-value level on each holding the way NPORT does (curMktValue +
fairValLevel per position). The level split is disclosed only at the PORTFOLIO-AGGREGATE
level in the Fair Value footnote — ``InvestmentOwnedAtFairValue`` dimensioned by
``us-gaap:FairValueByFairValueHierarchyLevelAxis`` (Level1/2/3 members). So we report the
AUTHORITATIVE aggregate L3% (the moat metric A-1 needs) and assign each holding a *modeled*
level by structure: quoted public positions (the small L1 sliver) vs the L3 private loan
book. We never fabricate a per-holding level the filing didn't disclose; the per-holding
``level`` field is marked ``modeled`` and the aggregate split is marked ``filed``.

NO LOOK-AHEAD: callers pick the filing filed strictly before T-1; the re-mark uses only
observable drivers dated <= T-1.

Source of authority: SEC EDGAR inline XBRL + financial-report FilingSummary.
"""
import re
import time
import json
import requests
from collections import defaultdict

UA = {"User-Agent": "SignalOS Research 4tripathy@gmail.com"}
_SLEEP = 0.15

# The 6 amendment-A-5 BDCs. (OBDC = ex-ORCC/Owl Rock, renamed 2024.)
BDC_CIK = {
    'ARCC': 1287750, 'FSK': 1422183, 'GBDC': 1476765,
    'OBDC': 1655888, 'MAIN': 1396440, 'PSEC': 1287032,
}


# ----------------------------------------------------------------------------- EDGAR fetch
def _get(url):
    time.sleep(_SLEEP)
    r = requests.get(url, headers=UA, timeout=120)
    r.raise_for_status()
    return r


def submissions(cik):
    return _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()


def latest_periodic(cik, forms=('10-Q', '10-K'), before_date=None):
    """Return (filingDate, form, accession, primaryDoc) of the most recent 10-Q/10-K,
    optionally filed strictly before before_date (point-in-time, no look-ahead)."""
    j = submissions(cik)
    rec = j['filings']['recent']
    rows = []
    for i, f in enumerate(rec['form']):
        if f in forms:
            rows.append((rec['filingDate'][i], f, rec['accessionNumber'][i],
                         rec['primaryDocument'][i]))
    if before_date:
        rows = [r for r in rows if r[0] < before_date]
    rows.sort(reverse=True)
    return rows[0] if rows else None


def _xbrl_instance_url(cik, accession, primary_doc):
    """Inline-XBRL instance = the primary doc base + '_htm.xml' (EDGAR convention)."""
    acc = accession.replace('-', '')
    base = primary_doc.rsplit('.', 1)[0]  # arcc-20260331
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{base}_htm.xml"


# ----------------------------------------------------------------------------- XBRL parse
def _parse_contexts(xml):
    """id -> {instant, ident (typed InvestmentIdentifier), dims {axis:member}}."""
    ctxs = {}
    for m in re.finditer(r'<context id="([^"]+)">(.*?)</context>', xml, re.S):
        cid, body = m.group(1), m.group(2)
        inst = re.search(r'<instant>([\d-]+)</instant>', body)
        dims = dict(re.findall(
            r'dimension="([^"]+)">([^<]+)</xbrldi:explicitMember>', body))
        tm = re.search(
            r'dimension="us-gaap:InvestmentIdentifierAxis">(.*?)</xbrldi:typedMember>',
            body, re.S)
        ident = re.sub('<[^>]+>', '', tm.group(1)).strip() if tm else None
        ctxs[cid] = {'instant': inst.group(1) if inst else None,
                     'ident': ident, 'dims': dims}
    return ctxs


def _facts(xml, tag):
    """All us-gaap:<tag> facts -> list of (contextRef, raw_text)."""
    out = []
    pat = (r'<us-gaap:' + tag + r'\b[^>]*contextRef="([^"]+)"[^>]*>'
           r'([^<]*)</us-gaap:' + tag + '>')
    for m in re.finditer(pat, xml):
        out.append((m.group(1), m.group(2)))
    return out


def _num(s):
    if s is None:
        return None
    s = s.replace(',', '').strip()
    neg = s.startswith('(')
    s = s.strip('()').lstrip('$').strip()
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


_TYPE_TOKENS = (
    'first lien', 'second lien', '1st lien', '2nd lien', 'senior secured', 'lien',
    'loan', 'subordinated', 'revolv', 'delayed draw', 'common stock', 'one stop',
    'preferred', 'warrant', 'equity', 'membership', 'partnership', 'note', 'bond',
    'class a', 'class b', 'class c', 'series a', 'series b', 'series c', 'common units',
    'preferred stock', 'common equity', 'member interest', 'member units', 'certificate',
    'co-invest', 'unsecured', 'mezzanine', 'structured', 'secured debt', 'term loan',
    'llc interest', 'units', 'shares', 'stock', 'warrants',
)
# affiliation / industry markers that are NOT investment types
_NON_TYPE = ('non-affiliated', 'affiliated', 'controlled', 'non-controlled', 'issuer')


def _looks_like_type(part):
    p = part.lower()
    if any(t in p for t in _TYPE_TOKENS):
        return True
    return False


def _split_identifier(ident):
    """Separator-agnostic split of a typed identifier into (issuer, inv_type, industry).

    BDC SoI identifiers come in two layouts:
      - ARCC: '<issuer>, <investment type>'  (comma; issuer itself contains commas)
      - FSK/OBDC/MAIN/GBDC/PSEC: '<issuer> | <field> | <field> ...' (pipe; one field is the
        investment type, sometimes another is the industry / affiliation)
    Field[0] is always the issuer. We scan the remaining fields for an investment-type token
    (and treat a non-type, non-affiliation field as the industry)."""
    import html as _html
    ident = _html.unescape(ident).strip()
    if '|' in ident:
        parts = [p.strip() for p in ident.split('|') if p.strip()]
        issuer = parts[0]
        inv_type = None
        industry = None
        for p in parts[1:]:
            pl = p.lower()
            if any(n in pl for n in _NON_TYPE):
                continue
            if _looks_like_type(p):
                inv_type = p if inv_type is None else inv_type
            elif industry is None and not p.rstrip().rstrip('0123456789').strip()[-1:].isdigit():
                industry = p
        return issuer, inv_type, industry
    # comma layout
    if ',' in ident:
        head, tail = ident.rsplit(',', 1)
        if _looks_like_type(tail):
            return head.strip(), tail.strip(), None
    return ident, None, None


def _classify_type(inv_type):
    """Coarse bucket for the per-holding investment type (drives the re-mark channel)."""
    if not inv_type:
        return 'other'
    t = inv_type.lower()
    if 'first lien' in t or '1st lien' in t:
        return '1st_lien'
    if 'second lien' in t or '2nd lien' in t:
        return '2nd_lien'
    if 'subordinated' in t or 'mezzanine' in t or 'unsecured' in t:
        return 'subordinated'
    if 'one stop' in t or 'unitranche' in t:
        return '1st_lien'        # Golub 'one stop' = unitranche first-lien
    if any(k in t for k in ('common', 'preferred', 'shares', 'units', 'equity',
                            'warrant', 'member interest', 'stock', 'partnership',
                            'llc interest')):
        return 'equity'
    if 'certificate' in t or 'structured' in t:
        return 'structured'
    if 'secured debt' in t or 'term loan' in t or 'loan' in t or 'lien' in t or 'note' in t:
        return '1st_lien'        # generic senior debt fallback
    return 'other'


# --------------------------------------------------------------------- the parser entry pt
def parse_soi(xml, period=None):
    """Parse the Schedule of Investments out of an inline-XBRL instance.

    Returns dict:
      period, total_fair_value (sum of holdings), holdings[],
      level_split {L1,L2,L3,NAV} (filed aggregate), l3_pct_invest (A-1 moat metric),
      net_assets, shares_outstanding, nav_per_share_filed,
      tie_out {bs_total_investments, holdings_sum, abs_diff, pct_diff}.
    """
    ctxs = _parse_contexts(xml)

    # pick current period = the document balance-sheet date = the MAX instant among
    # identified-FV contexts. NOT the modal instant: a filing's SoI comparative period can
    # carry MORE per-name facts than the current period (FSK: 849 prior vs 724 current), so
    # the mode selects the wrong (stale) book. The max instant is the as-of date.
    fv = _facts(xml, 'InvestmentOwnedAtFairValue')
    if period is None:
        insts = [ctxs[cid]['instant'] for cid, _ in fv
                 if cid in ctxs and ctxs[cid]['ident'] and ctxs[cid]['instant']]
        period = max(insts) if insts else None

    def gather(tag):
        out = {}
        for cid, val in _facts(xml, tag):
            ctx = ctxs.get(cid)
            if not ctx or ctx['instant'] != period or not ctx['ident']:
                continue
            v = _num(val)
            # for non-numeric (coupon/spread carry %), keep raw text
            out.setdefault(ctx['ident'], {})['v'] = v
            out[ctx['ident']]['raw'] = val
        return out

    fv_by = gather('InvestmentOwnedAtFairValue')
    cost_by = gather('InvestmentOwnedAtCost')
    prin_by = gather('InvestmentOwnedBalancePrincipalAmount')
    # coupon / spread are percent-typed -> keep raw
    rate_by = gather('InvestmentInterestRate')
    spread_by = gather('InvestmentBasisSpreadVariableRate')

    idents = set(fv_by)

    import re as _re
    fv_val = {k: (v['v'] or 0.0) for k, v in fv_by.items()}

    def _strip_fn(s):
        # drop trailing footnote superscripts the SoI carries on rollup rows: '(c)', '(3)(9)'
        return _re.sub(r'(\([0-9a-z]+\))+\s*$', '', s).strip()

    def _issuer0(s):
        # field-0 issuer, footnote/tranche-number stripped, for issuer-level dup matching
        s = _strip_fn(s)
        s = _re.split(r'\s*\|\s*', s)[0] if '|' in s else s
        return _re.sub(r'\s\d+$', '', s).strip()

    def is_subtotal(h):
        bh = _strip_fn(h)
        has_pipe = '|' in h
        for o in idents:
            if o == h:
                continue
            bo = _strip_fn(o)
            # (1) another identifier extends this one with a field separator:
            #     ARCC comma 'H, <tranche>'  |  pipe 'H | <field>'
            if bo.startswith(bh + ',') or bo.startswith(bh + ' |') or bo.startswith(bh + '|'):
                return True
            # (2) bare-issuer rollup (no pipe) duplicating a piped detail row of the SAME
            #     issuer at an IDENTICAL value (FSK/OBDC: 'Kellermeyer ... LLC 1' bare ==
            #     'Kellermeyer ... LLC | Industry 1' piped; 'Blue Owl Credit SLF LLC(c)' ==
            #     'Blue Owl Credit SLF LLC | LLC Interest | Affiliated'). Value-gated so a
            #     genuine standalone bare holding is never dropped.
            if not has_pipe and '|' in o and _issuer0(o) == _issuer0(h):
                hv, ov = fv_val.get(h, 0.0), fv_val.get(o, 0.0)
                if hv and ov and abs(hv - ov) / max(hv, ov) < 0.01:
                    return True
        # (3) numbered-tranche rollup (MAIN: 'X | Secured Debt' rolls up '... Debt 1/2').
        #     Flag only when >=2 numbered children exist AND H ties their sum within 1%.
        if not _re.search(r'\s\d+$', h):
            kids = [o for o in idents if _re.match(_re.escape(h) + r' \d+$', o)]
            if len(kids) >= 2:
                ksum = sum(fv_val.get(k, 0.0) for k in kids)
                hv = fv_val.get(h, 0.0)
                if ksum and abs(hv - ksum) / ksum < 0.01:
                    return True
        return False

    holdings = []
    for ident, d in fv_by.items():
        if d['v'] is None or is_subtotal(ident):
            continue
        issuer, inv_type, industry = _split_identifier(ident)
        holdings.append({
            'identifier': ident,
            'issuer': issuer,
            'industry': industry,
            'investment_type_raw': inv_type,
            'investment_type': _classify_type(inv_type),
            'fair_value': d['v'],
            'cost': (cost_by.get(ident) or {}).get('v'),
            'principal': (prin_by.get(ident) or {}).get('v'),
            'coupon': (rate_by.get(ident) or {}).get('raw'),
            'spread': (spread_by.get(ident) or {}).get('raw'),
            'level': 'L3_modeled',   # see module docstring: per-holding level not filed
            'level_basis': 'modeled_structural',
        })
    holdings.sort(key=lambda h: -h['fair_value'])
    hold_sum = sum(h['fair_value'] for h in holdings)

    # ---- aggregate level split (the AUTHORITATIVE, filed figure) ----------------
    LVL = {'us-gaap:FairValueInputsLevel1Member': 'L1',
           'us-gaap:FairValueInputsLevel2Member': 'L2',
           'us-gaap:FairValueInputsLevel3Member': 'L3',
           'us-gaap:FairValueMeasuredAtNetAssetValuePerShareMember': 'NAV'}
    HAXIS = 'us-gaap:FairValueByFairValueHierarchyLevelAxis'
    ACLASS = 'us-gaap:FairValueByAssetClassAxis'
    # Axes that signal a *breakout* (valuation-technique / measurement-input / instrument)
    # rather than the portfolio level total — these must NOT be summed into the split.
    BREAKOUT = {'us-gaap:FinancialInstrumentAxis', 'us-gaap:MeasurementInputTypeAxis',
                'us-gaap:ValuationTechniqueAxis', 'us-gaap:RangeAxis'}
    # The level split is disclosed either as a bare per-level total (ARCC) OR only split by
    # asset class (GBDC). Accept configs whose non-hierarchy axes are a subset of {asset
    # class}; sum across asset classes per level. Reject any breakout-axis config.
    level_acc = defaultdict(float)
    level_has = set()
    for cid, val in fv:
        ctx = ctxs.get(cid)
        if not ctx or ctx['instant'] != period or ctx['ident']:
            continue
        dims = ctx['dims']
        if HAXIS not in dims:
            continue
        others = set(dims) - {HAXIS}
        if others & BREAKOUT or (others - {ACLASS}):
            continue  # a breakout or some other axis -> not the portfolio total
        mem = dims[HAXIS]
        if mem not in LVL:
            continue
        v = _num(val)
        if v is None:
            continue
        if not others:                      # a bare per-level total -> authoritative, use it
            level_acc[LVL[mem]] = v
            level_has.add(LVL[mem] + '_bare')
        elif (LVL[mem] + '_bare') not in level_has:   # else sum the asset-class breakout
            level_acc[LVL[mem]] += v
    level_split = dict(level_acc)

    # ---- balance-sheet total investments (tie-out target) ----------------------
    # Several BDCs emit MULTIPLE no-dims InvestmentOwnedAtFairValue facts (e.g. a
    # non-controlled/non-affiliated subtotal AND the grand total). The grand total is the
    # MAX of them. Fall back to the summed level split, then to the holdings sum.
    bs_total = _scalar_max(xml, ctxs, 'InvestmentOwnedAtFairValue', period,
                           require_no_dims=True)
    if bs_total is None:
        bs_total = _scalar_max(xml, ctxs, 'Investments', period, require_no_dims=True)
    lvl_total = sum(v for k, v in level_split.items() if v is not None)
    if bs_total is None and lvl_total:
        bs_total = lvl_total

    # detect scale mismatch: level split / bs_total may be reported in $millions while
    # per-holding facts are full dollars (or vice-versa). Normalize the level split to the
    # per-holding scale using the L1+L2+L3 vs hold_sum ratio.
    lvl_sum = sum(v for k, v in level_split.items() if v is not None)
    scale = 1.0
    if lvl_sum and hold_sum:
        ratio = hold_sum / lvl_sum
        # if ratio ~ 1e6 the split is in $M; round to nearest power of 10
        if ratio > 100:
            scale = round(ratio, -int(len(str(int(ratio))) - 1))
            scale = 10 ** round(__import__('math').log10(ratio))
    level_split_norm = {k: (v * scale if v is not None else None)
                        for k, v in level_split.items()}
    if bs_total is not None and hold_sum and bs_total < hold_sum / 100:
        bs_total *= scale

    l3 = level_split_norm.get('L3')
    total_inv = bs_total if bs_total else hold_sum
    l3_pct = (100.0 * l3 / total_inv) if (l3 and total_inv) else None

    # ---- shares / net assets / filed NAV-per-share -----------------------------
    shares = _scalar(xml, ctxs, 'CommonStockSharesOutstanding', period,
                     require_no_dims=True)
    net_assets = (_scalar(xml, ctxs, 'StockholdersEquity', period, require_no_dims=True)
                  or _scalar(xml, ctxs,
                             'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
                             period, require_no_dims=True))
    navps = _scalar(xml, ctxs, 'NetAssetValuePerShare', period, require_no_dims=True)

    return {
        'period': period,
        'n_holdings': len(holdings),
        'total_fair_value': hold_sum,
        'level_split': level_split_norm,
        'l3_pct_invest': l3_pct,
        'net_assets': net_assets,
        'shares_outstanding': shares,
        'nav_per_share_filed': navps,
        'tie_out': {
            'bs_total_investments': bs_total,
            'holdings_sum': hold_sum,
            'abs_diff': (hold_sum - bs_total) if bs_total else None,
            'pct_diff': (100.0 * (hold_sum - bs_total) / bs_total) if bs_total else None,
        },
        'holdings': holdings,
    }


def _scalar(xml, ctxs, tag, period, require_no_dims=False):
    """First numeric us-gaap:<tag> fact for the current period (optionally no dimensions)."""
    for cid, val in _facts(xml, tag):
        ctx = ctxs.get(cid)
        if not ctx or ctx['instant'] != period:
            continue
        if require_no_dims and (ctx['dims'] or ctx['ident']):
            continue
        v = _num(val)
        if v is not None:
            return v
    return None


def _scalar_max(xml, ctxs, tag, period, require_no_dims=False):
    """Largest numeric us-gaap:<tag> fact for the current period (optionally no dims).
    Used for total-investments: filers emit affiliation subtotals + a grand total; the grand
    total is the max."""
    vals = []
    for cid, val in _facts(xml, tag):
        ctx = ctxs.get(cid)
        if not ctx or ctx['instant'] != period:
            continue
        if require_no_dims and (ctx['dims'] or ctx['ident']):
            continue
        v = _num(val)
        if v is not None:
            vals.append(v)
    return max(vals) if vals else None


def fetch_parse_soi(ticker, before_date=None):
    """Fetch the latest 10-Q/10-K (optionally before before_date) for a BDC and parse its
    Schedule of Investments. Returns the parse dict augmented with filing metadata."""
    cik = BDC_CIK[ticker.upper()]
    f = latest_periodic(cik, before_date=before_date)
    if not f:
        return None
    fdate, form, acc, pdoc = f
    xml = _get(_xbrl_instance_url(cik, acc, pdoc)).text
    res = parse_soi(xml)
    res.update({'ticker': ticker.upper(), 'cik': cik, 'filing_date': fdate,
                'form': form, 'accession': acc})
    return res


# ===========================================================================
# DERIVED-NAV RE-MARK  (spec §3/§6; A-4/A-5)
# ===========================================================================
# Between quarterly filings a BDC loan book has NO continuous markable NAV (this absence is
# itself the moat — spec A-4). The OFFICIAL mark moves on two channels:
#   (1) observable credit/rate drift the manager passes through at the next mark, and
#   (2) discrete per-name credit EVENTS (a holding goes public / IPO; an upgrade/downgrade;
#       a default/restructuring; a priced secondary).
# We model the OFFICIAL number, not fair value, so the DEFAULT is carry-flat (the manager
# holds private loans at last appraisal between marks). The re-mark only departs from flat
# when a driver is supplied — which is exactly the predictability the frontrun edge exploits.
#
# DRIVER DESIGN (all observable at T-1, no look-ahead):
#   loan_index_bp_change : change in a broad leveraged-loan / HY credit-spread index since
#       the filing (bps). Applied to floating-rate loans via a modeled spread-duration: a
#       widening marks the book DOWN by (spread_dur * d_spread). BDC loans are ~floating so
#       SOFR moves pass through to COUPON not price; only the CREDIT SPREAD repriced the mark.
#   spread_duration_yrs  : modeled effective spread duration of the loan book (default 2.5y;
#       BDC direct loans are short, ~3-5y maturity, often called/repriced).
#   sofr_bp_change       : informational (affects income/coupon, ~not the fair-value mark for
#       a par floater); recorded, not applied to FV by default.
#   name_events          : {issuer -> multiplier} for discrete per-name credit/IPO events
#       (the A-4 primary signal). Applied to that issuer's holdings directly.
#   smoothing            : manager appraisal-lag damping in [0,1] applied to the index
#       channel (default 0.5 — BDC marks are smoothed/lagged vs traded credit).
#
# Output: re-marked total FV, derived net assets (= remarked FV + filed non-investment
# residual), derived NAV/share, and the surprise vs the last filed NAV/share.

def remark_book(parsed, loan_index_bp_change=0.0, sofr_bp_change=0.0,
                spread_duration_yrs=2.5, smoothing=0.5, name_events=None):
    name_events = name_events or {}
    d_spread = (loan_index_bp_change / 1e4)         # bps -> decimal
    px_factor_credit = 1.0 - smoothing * spread_duration_yrs * d_spread

    remarked = 0.0
    trace = []
    for h in parsed['holdings']:
        v0 = h['fair_value']
        method = 'carry'
        f = 1.0
        # discrete per-name event takes precedence (A-4 primary signal)
        ev = None
        for nm, mult in name_events.items():
            if nm.lower() in h['issuer'].lower():
                ev = (nm, mult)
                break
        if ev:
            f = ev[1]
            method = f'name_event:{ev[0]}'
        elif h['investment_type'] in ('1st_lien', '2nd_lien', 'subordinated',
                                      'structured', 'other'):
            # credit-spread channel re-marks the debt book
            f = px_factor_credit
            method = 'credit_index'
        else:
            # equity stakes: carry at last appraisal unless a name event fires
            method = 'equity_carry'
        v1 = v0 * f
        remarked += v1
        trace.append({'issuer': h['issuer'], 'type': h['investment_type'],
                      'v0': v0, 'v1': v1, 'method': method})

    filed_fv = parsed['total_fair_value']
    net_assets = parsed['net_assets']
    residual = (net_assets - filed_fv) if net_assets is not None else None  # cash+other-liab
    derived_net_assets = (remarked + residual) if residual is not None else None
    shares = parsed['shares_outstanding']

    out = {
        'period_of_book': parsed['period'],
        'filed_total_fv': filed_fv,
        'remarked_total_fv': remarked,
        'residual_non_investment': residual,
        'derived_net_assets': derived_net_assets,
        'shares_outstanding': shares,
        'drivers': {'loan_index_bp_change': loan_index_bp_change,
                    'sofr_bp_change': sofr_bp_change,
                    'spread_duration_yrs': spread_duration_yrs,
                    'smoothing': smoothing,
                    'credit_px_factor': px_factor_credit,
                    'n_name_events': len(name_events)},
    }
    if shares:
        out['derived_nav_per_share'] = (derived_net_assets / shares
                                        if derived_net_assets is not None else None)
        out['filed_nav_per_share'] = parsed['nav_per_share_filed'] or (
            net_assets / shares if net_assets else None)
        if out.get('derived_nav_per_share') and out['filed_nav_per_share']:
            out['surprise_pct'] = 100.0 * (out['derived_nav_per_share']
                                           - out['filed_nav_per_share']) / out['filed_nav_per_share']
    out['_trace_top'] = sorted(trace, key=lambda x: -abs(x['v1'] - x['v0']))[:10]
    return out


def bdc_derived_nav(ticker, asof, loan_index_bp_change=0.0, sofr_bp_change=0.0,
                    spread_duration_yrs=2.5, smoothing=0.5, name_events=None,
                    before_date=None):
    """Point-in-time derived NAV for a BDC as-of `asof` (no look-ahead).

    Pulls the last 10-Q/10-K SoI filed strictly before `before_date or asof`, then re-marks
    it to `asof` using the observable drivers. Models the OFFICIAL mark (carry-flat default),
    NOT fair value.
    """
    parsed = fetch_parse_soi(ticker, before_date=before_date or asof)
    if parsed is None:
        return None
    out = remark_book(parsed, loan_index_bp_change=loan_index_bp_change,
                      sofr_bp_change=sofr_bp_change,
                      spread_duration_yrs=spread_duration_yrs, smoothing=smoothing,
                      name_events=name_events)
    out.update({'ticker': ticker.upper(), 'asof': asof,
                'book_filing_date': parsed['filing_date'], 'book_form': parsed['form'],
                'book_accession': parsed['accession'],
                'l3_pct_invest': parsed['l3_pct_invest']})
    return out


if __name__ == '__main__':
    import sys
    tk = sys.argv[1] if len(sys.argv) > 1 else 'ARCC'
    r = fetch_parse_soi(tk)
    slim = {k: v for k, v in r.items() if k != 'holdings'}
    print(json.dumps(slim, indent=2, default=str))
    print("TOP HOLDINGS:")
    for h in r['holdings'][:8]:
        print(f"  {h['fair_value']:>16,.0f}  {h['investment_type']:<12} {h['issuer'][:48]}")
