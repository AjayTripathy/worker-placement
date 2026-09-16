"""Whole-universe fundamentals from the SEC XBRL frames API + TTM.

frames returns ONE concept across EVERY filer per call, so ~45 calls assemble the
entire cross-section (vs ~1,800 per-company companyfacts calls).

TTM (rolling 12 months ending the latest common quarter) is computed from frames as
  TTM_flow = annual(CY2025) - quarter(CY2025Q1) + quarter(CY2026Q1)
with graceful fallback to the latest available annual when a quarter is missing.
Balance-sheet instants take the freshest available period per filer.

LIMITATION: frames only include filers whose period aligns with the CALENDAR frame, so
off-fiscal-year companies are absent; `companyfacts_inputs()` is the per-CIK fallback
used for shortlist recompute.
"""
from __future__ import annotations
import json, time, urllib.request, urllib.error

HDRS = {"User-Agent": "signalos-deepvalue research 4tripathy@gmail.com"}

# freshest-first; per concept we keep the first (freshest) value seen per CIK
ANNUAL = "CY2025"
Q_OLD = "CY2025Q1"        # stale quarter to subtract
Q_NEW = "CY2026Q1"        # fresh quarter to add  (rolling TTM end = Mar-2026)
ANNUAL_FALLBACK = ["CY2025", "CY2024"]
INSTANTS = ["CY2026Q1I", "CY2025Q4I", "CY2025Q3I", "CY2024Q4I"]

FLOW_CONCEPTS = ["OperatingIncomeLoss", "NetCashProvidedByUsedInOperatingActivities",
                 "PaymentsToAcquirePropertyPlantAndEquipment", "Revenues"]

# One-time / non-operating GAIN tags that can inflate reported EBIT (the BKE litigation-settlement hole:
# the inflection guard read a settlement-inflated +37% as growth). We strip the POSITIVE (gain) portion
# from quarterly EBIT before the inflection/earn-yield gates. Restricted to items that plausibly sit
# INSIDE OperatingIncomeLoss (litigation settlement, asset/business disposition, bargain purchase,
# unusual/infrequent, other-nonrecurring) — NOT below-the-line items (debt extinguishment) which aren't
# in EBIT anyway. RECALL IS PARTIAL: many filers bury settlements in SG&A with no discrete tag — so this
# is backstopped by a run-rate-spike check in quality.py, and the per-name DD remains the final filter.
ONE_TIME_GAIN_CONCEPTS = ["GainLossRelatedToLitigationSettlement", "GainLossOnSaleOfBusiness",
                          "GainLossOnDispositionOfAssets", "GainLossOnDispositionOfAssetsNet1",
                          "BusinessCombinationBargainPurchaseGainRecognizedAmount",
                          "UnusualOrInfrequentItemGainNet", "OtherNonrecurringIncome",
                          # divestiture-gain tags — the AMPY hole (DV5 integrity check 2026-07-20:
                          # +$93.5M East-TX/OK/LA sale gains inside OperatingIncomeLoss made an
                          # ex-items-negative drillco print "EV/EBIT 3.8")
                          "GainLossOnSaleOfOilAndGasProperty", "GainsLossesOnSalesOfAssets",
                          "GainLossOnSaleOfPropertyPlantEquipment",
                          "DisposalGroupNotDiscontinuedOperationGainLossOnDisposal"]
INSTANT_CONCEPTS = ["AssetsCurrent", "Liabilities", "LiabilitiesCurrent", "StockholdersEquity",
                    "CashAndCashEquivalentsAtCarryingValue", "ShortTermInvestments",
                    # passive-asset concepts for the PFIC asset test (foreign filers)
                    "LongTermInvestments", "OtherLongTermInvestments", "MarketableSecuritiesNoncurrent",
                    "AvailableForSaleSecuritiesNoncurrent",
                    "LongTermDebtNoncurrent", "LongTermDebt", "DebtCurrent",
                    # broadened debt tags — the COLL miss (convertibles + custom term-loan not under
                    # standard LongTermDebt); bias to over-state debt = conservative for a value screen
                    "LongTermDebtAndCapitalLeaseObligations", "LongTermDebtAndCapitalLeaseObligationsNoncurrent",
                    "ConvertibleLongTermNotesPayable", "ConvertibleNotesPayable",
                    "DebtLongtermAndShorttermCombinedAmount", "NotesPayable",
                    # current-bucket debt tags — the HAIN miss (100% of $549.8M reclassified CURRENT at the
                    # Dec-2026 maturity wall -> every noncurrent tag read 0 and the screen printed "net cash"
                    # on a going-concern name) + the SSTK $158M current-debt miss, both 2026-07-15
                    "LongTermDebtCurrent", "LinesOfCreditCurrent", "ShortTermBorrowings",
                    "OtherShortTermBorrowings", "SecuredDebtCurrent",
                    # convert variants + M&A earnouts — the CRMD hole (DV5 integrity check 2026-07-20:
                    # $144.9M converts under ConvertibleDebtNoncurrent + $105.6M Melinta contingent
                    # consideration -> screen said 2.2x, true 3.8x). Earnouts are debt-like in EV.
                    "ConvertibleDebtNoncurrent", "ConvertibleDebtCurrent", "ConvertibleDebt",
                    "BusinessCombinationContingentConsiderationLiabilityNoncurrent",
                    "BusinessCombinationContingentConsiderationLiabilityCurrent",
                    "MinorityInterest", "Assets"]


def _get(url, timeout=45):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout))


def frame(concept, period, unit="USD") -> dict[int, float]:
    url = f"https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/{unit}/{period}.json"
    try:
        d = _get(url)
        time.sleep(0.12)
        return {int(r["cik"]): r["val"] for r in d.get("data", [])}
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        time.sleep(0.12)
        return {}


def _freshest(concept, periods) -> dict[int, float]:
    """Merge periods freshest-first; keep the first value seen per CIK."""
    out = {}
    for p in periods:
        for cik, v in frame(concept, p).items():
            out.setdefault(cik, v)
    return out


def build_cross_section() -> dict[int, dict]:
    """{cik: {concept: ttm-or-instant value}} for the whole universe."""
    # flows: annual + the two quarters for rolling TTM
    ann = {c: _freshest(c, ANNUAL_FALLBACK) for c in FLOW_CONCEPTS}
    qo = {c: frame(c, Q_OLD) for c in FLOW_CONCEPTS}
    qn = {c: frame(c, Q_NEW) for c in FLOW_CONCEPTS}
    inst = {c: _freshest(c, INSTANTS) for c in INSTANT_CONCEPTS}
    # one-time gains in the two comparison quarters (the BKE settlement hole)
    otg_qn = {c: frame(c, Q_NEW) for c in ONE_TIME_GAIN_CONCEPTS}
    otg_qo = {c: frame(c, Q_OLD) for c in ONE_TIME_GAIN_CONCEPTS}
    # ...and over the TTM window itself (the SPRO/AMPY hole: a milestone or divestiture gain
    # inside annual EBIT makes an ex-items-negative business print a 2-4x multiple)
    otg_ann = {c: _freshest(c, ANNUAL_FALLBACK) for c in ONE_TIME_GAIN_CONCEPTS}

    def one_time_gain(otg, cik):
        # sum only POSITIVE (gain) contributions; a one-time loss only depresses EBIT (don't add back)
        return sum(max(0.0, otg[c].get(cik) or 0.0) for c in ONE_TIME_GAIN_CONCEPTS)

    ciks = set()
    for d in list(ann.values()) + list(inst.values()):
        ciks |= set(d)

    def ttm(c, cik):
        a, o, n = ann[c].get(cik), qo[c].get(cik), qn[c].get(cik)
        if a is not None and o is not None and n is not None:
            return a - o + n          # rolling TTM ending Mar-2026
        return a                       # fallback: latest annual

    # prior-year flows for the stale-peak / collapsing-EBIT quality gate (the GIII lesson)
    prior_ebit = frame("OperatingIncomeLoss", "CY2024")
    prior_rev = frame("Revenues", "CY2024")

    cs = {}
    for cik in ciks:
        rec = {c: ttm(c, cik) for c in FLOW_CONCEPTS}
        rec.update({c: inst[c].get(cik) for c in INSTANT_CONCEPTS})
        rec["_ttm_rolling"] = qn[FLOW_CONCEPTS[0]].get(cik) is not None  # had a fresh quarter
        rec["OperatingIncomeLoss_prior"] = prior_ebit.get(cik)          # prior-year EBIT (annual trend gate)
        rec["Revenues_prior"] = prior_rev.get(cik)
        # latest-QUARTER EBIT + year-ago quarter — the recent-inflection guard (the UPWK/VITL/PSIX lesson:
        # an annual EBIT screen misses a fresh quarterly collapse)
        rec["OperatingIncomeLoss_q"] = qn["OperatingIncomeLoss"].get(cik)        # CY2026Q1
        rec["OperatingIncomeLoss_q_prior"] = qo["OperatingIncomeLoss"].get(cik)  # CY2025Q1
        rec["OneTimeGain_q"] = one_time_gain(otg_qn, cik)                        # discrete one-time gains in EBIT
        rec["OneTimeGain_q_prior"] = one_time_gain(otg_qo, cik)
        # TTM one-time gain total, same rolling arithmetic as ttm() (floor 0: gains only)
        rec["OneTimeGain_ttm"] = max(0.0, one_time_gain(otg_ann, cik)
                                     - one_time_gain(otg_qo, cik) + one_time_gain(otg_qn, cik))
        cs[cik] = rec
    return cs


_MERGER_FORMS = {"DEFM14A", "PREM14A", "DEFM14C", "PREM14C", "425"}


def merger_pending(cik: int, days: int = 150) -> bool:
    """Pre-filter: a name with a DEFINITIVE/pending acquisition has an equity that's become a merger CLAIM,
    not a value stock (it trades at/near the deal price). The CPRX catch — surfaced 'cheap' only because the
    stock was already re-priced to a $31.50 all-cash takeover. Flags merger PROXIES + tender-offer +
    going-private forms in the trailing ~150 days (one submissions call, reused from is_foreign_filer)."""
    import datetime
    try:
        sub = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        rec = sub.get("filings", {}).get("recent", {})
        forms, dates = rec.get("form", []), rec.get("filingDate", [])
        cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
        for fm, dt in zip(forms, dates):
            if dt < cutoff:
                continue
            if fm in _MERGER_FORMS or fm.startswith("SC TO") or fm.startswith("SC 14D") or fm.startswith("SC 13E"):
                return True
    except Exception:
        return False
    return False


def is_foreign_filer(cik: int) -> bool:
    """Foreign private issuers file 20-F/40-F, not 10-K — a reliable ADR/VIE tell."""
    try:
        sub = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        forms = set(sub.get("filings", {}).get("recent", {}).get("form", []))
        return bool(forms & {"20-F", "40-F", "6-K"}) and not (forms & {"10-K", "10-Q"})
    except Exception:
        return False
