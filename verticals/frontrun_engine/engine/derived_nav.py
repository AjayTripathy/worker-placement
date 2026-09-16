"""
derived_nav.py — point-in-time derived-NAV reconstruction (no look-ahead).

Spec §3/§6: at official NAV date T, reconstruct derived_NAV as of T-1 using ONLY info
public at T-1. We model the OFFICIAL mark (the fund's printed convention), NOT fair value.

Mechanics
---------
1. Holdings = most recent NPORT-P filed strictly BEFORE T-1 (engine.nport.fetch_parse_latest
   with before_date). This is the ~60-day-stale book — the central constraint (spec §6).
2. Re-mark each holding at its T-1 price under a marking convention that depends on the
   fund's fair-value level:
     - Level 1 (quoted): mark to the holding's T-1 close. For a liquid-equity CEF this is
       the whole book, so derived_NAV(T-1) reconstructs official NAV up to flows/fees ->
       the Arm-B unit test.
     - Level 2: mark by the observable input move (index/credit spread). Modeled as
       carry-at-last unless a comp series is supplied (Phase-2 wiring).
     - Level 3 (private): the OFFICIAL mark holds the position at its last appraised /
       last-round value between marking events. So the official-number model carries L3 at
       the filed NPORT value UNLESS a mark-able public event fired for that name (an IPO, a
       up/down round, or a public comp/credit move passed through per the fund's policy).
       Those events are supplied via `comp_marks` (name -> multiplier). With no event, L3
       carries flat -> derived == last official for the L3 sleeve. This is deliberate: it
       encodes that the official L3 number only moves on discrete events, which is exactly
       the predictability the moat hypothesis exploits.

The engine returns derived_NAV (total $) and, given shares, derived NAV/share, plus the
implied surprise vs the last official NAV.

NO LOOK-AHEAD GUARANTEES
  - before_date filter on NPORT selection
  - prices passed in by the caller must be T-1 closes; the engine never fetches a price
    dated >= T (caller's responsibility; Phase-2 price loader will enforce).
"""
from engine import nport


def remark(parsed_nport: dict,
           l1_prices: dict = None,
           comp_marks: dict = None,
           l1_price_basis: dict = None):
    """Re-mark a parsed NPORT book.

    parsed_nport : output of engine.nport.parse_nport
    l1_prices    : optional {holding_name -> new_price}. If a Level-1 holding's name maps to
                   a price here AND we know its filed price basis (l1_price_basis), the value
                   is scaled by new/old. If not provided, L1 carries at filed value.
    comp_marks   : optional {holding_name -> multiplier} applied to Level-2/3 holdings to
                   model a discrete marking event (round/IPO/comp move). Absent => carry flat.
    l1_price_basis: optional {holding_name -> filed_price} to enable proportional L1 re-mark.

    Returns dict with derived_net_assets and a per-holding remark trace.
    """
    l1_prices = l1_prices or {}
    comp_marks = comp_marks or {}
    l1_price_basis = l1_price_basis or {}

    derived = 0.0
    trace = []
    for h in parsed_nport['holdings']:
        nm = h['name']
        v0 = h['value']
        lvl = h['level']
        v1 = v0
        method = 'carry'
        if lvl == '1':
            if nm in l1_prices and nm in l1_price_basis and l1_price_basis[nm]:
                v1 = v0 * (l1_prices[nm] / l1_price_basis[nm])
                method = 'l1_reprice'
            else:
                method = 'l1_carry'  # MMF/treasury or no price supplied -> par/last
        elif lvl in ('2', '3'):
            if nm in comp_marks:
                v1 = v0 * comp_marks[nm]
                method = 'comp_mark'
            else:
                method = 'official_carry'  # official number only moves on a discrete event
        derived += v1
        trace.append({'name': nm, 'level': lvl, 'v0': v0, 'v1': v1, 'method': method})

    # preserve non-investment net items (cash/other = netAssets - sum(holdings filed))
    filed_sum = sum(h['value'] for h in parsed_nport['holdings'])
    residual = parsed_nport['net_assets'] - filed_sum  # cash + receivables - liabilities
    derived_net_assets = derived + residual

    return {
        'derived_net_assets': derived_net_assets,
        'filed_net_assets': parsed_nport['net_assets'],
        'residual_non_investment': residual,
        'l3_pct_nav': parsed_nport['l3_pct_nav'],
        'trace': trace,
    }


def derived_nav_per_share(parsed_nport: dict, shares_outstanding: float, **kw):
    r = remark(parsed_nport, **kw)
    r['shares_outstanding'] = shares_outstanding
    r['derived_nav_per_share'] = r['derived_net_assets'] / shares_outstanding if shares_outstanding else None
    r['filed_nav_per_share'] = r['filed_net_assets'] / shares_outstanding if shares_outstanding else None
    return r


def reconstruct(cik: int, t_date: str, shares_outstanding: float = None,
                l1_prices=None, comp_marks=None, l1_price_basis=None):
    """Point-in-time: pull the latest NPORT filed before t_date, re-mark, return derived NAV."""
    book = nport.fetch_parse_latest(cik, before_date=t_date)
    if book is None:
        return None
    if shares_outstanding:
        out = derived_nav_per_share(book, shares_outstanding, l1_prices=l1_prices,
                                    comp_marks=comp_marks, l1_price_basis=l1_price_basis)
    else:
        out = remark(book, l1_prices=l1_prices, comp_marks=comp_marks,
                     l1_price_basis=l1_price_basis)
    out['nport_filing_date'] = book['filing_date']
    out['nport_rep_pd_date'] = book['rep_pd_date']
    out['nport_accession'] = book['accession']
    return out
