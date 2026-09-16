"""quality_wishlist — the standing shopping list with prices (fix 4 of the slow-slide review).

Spec: QUALITY_WISHLIST_DESIGN.md, APPROVED 2026-08-13. Principal's rulings that this module
implements literally: A = HYBRID seeding (mechanical screen -> principal culls to ~75 ->
lazy court at first band-fire), B = TWO-BAND (FAIR tranche-1 + CHEAP starter), C = MANUAL
Parametric holdings list with a wash-sale flag at fire time, D = 8% aggregate sleeve cap.

WHY IT EXISTS (the SPGI miss postmortem): every other instrument the desk owns requires
something to FALL. dislocation_sweep, broken_print_radar, class_dislocation and the cohort
layer are all drawdown-triggered. The fourth failure class is the quality name that gets
cheap WITHOUT falling — standing still while earnings grow. No drawdown screen can express
the TINA doctrine ("for quality, fair value IS the entry"). This is a different instrument:
a shopping list with prices, not a dislocation detector.

TWO MODES (the hybrid activation, §2):

  --screen   mechanical quality gate over the S&P 500 + the broad-US universe builder.
             Writes the FULL candidate list to data/QUALITY_WISHLIST_CANDIDATES.json and a
             human-readable cull sheet to desk/reports/QUALITY_WISHLIST_CULL_SHEET_*.md.
             The principal culls that sheet to ~75 names and saves the survivors to
             data/quality_wishlist_active.json. NO BAND-FIRE IS POSSIBLE IN THIS MODE.

  (default)  watch mode. Reads data/quality_wishlist_active.json — the POST-CULL list. Until
             that file exists the wishlist is INACTIVE: the run degrades LOUD, fires nothing,
             and exits clean. An unculled mechanical list must never fire; that is the whole
             point of ruling A (hybrid), and a screen that fires its own raw output is the
             generator grading itself.

  --refresh-fundamentals   weekly XBRL refresh for the active list (registry-scheduled).
  --grade                  fills the SPY-same-window counterfactual on due fires.

THE GATE (§3) — mechanical, from audited XBRL companyfacts (data.sec.gov, plain UA). Over the
trailing 10 fiscal years:
  1. ROIC > 15% in >= 8 years
  2. Revenue grew in >= 8 years          (durability, not velocity — the GARP lesson: trailing
                                          growth-RATE screens are fragile, so there is no
                                          growth-rate minimum anywhere in this module)
  3. Gross margin stable-or-rising       (10yr slope >= 0, OR latest within 300bps of the median)
  4. Net debt / EBITDA < 2.0             (the unlevered-tails carry precondition)
  5. Diluted share count flat or shrinking over the window (owner-alignment; kills serial
                                          diluters and roll-ups whose EPS is acquisition-stepped)
Deliberately absent: any valuation input (that is the band's job) and any growth-rate floor.

ROIC APPROXIMATION — documented because it is an approximation, not a definition:
    NOPAT           = OperatingIncomeLoss x (1 - effective tax rate)
    effective rate  = IncomeTaxExpenseBenefit / pretax income, clamped to [10%, 35%];
                      21% fallback when pretax is missing or non-positive
    invested capital= StockholdersEquity + net debt,
                      net debt = total debt - cash - short-term investments
    ROIC            = NOPAT / invested capital
  Known deviations from a textbook ROIC, all conservative or explicitly flagged:
   - operating leases are NOT capitalised into invested capital (understates the denominator
     for retail/restaurant names, so their ROIC reads HIGH; the gate is therefore generous to
     lease-heavy businesses and the court must re-check them);
   - no excess-cash carve-out beyond netting cash against debt;
   - goodwill is left IN invested capital (an acquisitive compounder is charged for what it
     paid — deliberate, it is the same discipline as the share-count gate);
   - when invested capital is <= 0 (buyback-driven negative equity: MCD/HD/AVGO-class) ROIC is
     mathematically unbounded, not infinite-good. It is recorded as ROIC_UNBOUNDED and counts
     as clearing 15% ONLY if NOPAT > 0, and the name carries the flag into the cull sheet.

THREE TAGGING REPAIRS the extractor makes, each flagged onto the name rather than hidden:
  - SPLIT BASIS. XBRL share counts are restated for splits only in filings made after the split,
    so a naive series shows AAPL's diluted count RISING 173% across the decade. Counts are
    chain-linked through the within-filing ratios instead (`chained_shares`), which is what makes
    criterion 5 and the historical market-cap series mean anything.
  - EBIT COVERAGE. A large minority of filers never tag OperatingIncomeLoss; EBIT falls back to
    pretax + interest expense, flagged EBIT-FROM-PRETAX and reading slightly high.
  - DEBT COVERAGE. Debt hides under NotesPayable (homebuilders), ConvertibleDebtNoncurrent and a
    dozen other concepts, and is often tagged in only some years. Interior gaps are interpolated;
    years before the FIRST reported debt are treated as debt-free (META tags debt only from 2022
    — holding that flat backwards would invent $18bn of leverage); a filer with no debt concept
    at all is debt-free. Operating leases are NOT capitalised into debt or invested capital.

DEGRADED, NEVER SILENT: a name with fewer than 8 years of USABLE history (revenue + EBIT +
equity + diluted shares all present) is reported DEGRADED-INSUFFICIENT-HISTORY. It is never
passed and never failed — it lands in its own section of the cull sheet with the year count.

THE BANDS (§4) — all percentiles are OWN-HISTORY, 10yr weekly, on EV/EBIT and P/E. Never
cross-sectional: the ADR-P/B and conservative-FV lessons both say peer anchors mislead.
  FAIR       combined percentile <= 50  -> tranche-1 proposal (the TINA doctrine mechanized)
  CHEAP      combined percentile <= 20  -> starter proposal
  STANDSTILL percentile fell >= 25 points over 12 months WHILE trailing EPS rose — the
             SPGI-class catch: it got cheap without a drawdown. Fires at any level.
The combined percentile is the MAX of the two multiples' percentiles (both must be cheap for
the name to read cheap), except where guard 3 suppresses P/E.

TRAP GUARDS (§5), each with an offline test:
  1. peak-earnings   latest operating margin > own p90 -> denominator-flattered -> REVIEW
  2. crash-cheapness name is a live dislocation/broken-print hit -> route CAUSE-CHECK-FIRST to
                     the dislocation pipeline; NOT enqueued to court by the wishlist
  3. acq step-up     share count or goodwill +>10% in the trailing year -> P/E suppressed,
                     EV/EBIT-only percentile
  4. value-trap decay >12 months sitting in CHEAP with no court ACCEPT -> mandatory RE-GATE,
                     printed every run (the reference distribution decays as cheap years enter
                     the lookback — a feature, but it must be surfaced, never silent)

PROPOSES ONLY. Every fire routes trap-verify -> red -> blue -> adjudicate through the standard
court conveyor (lazy court: no court spend until a name actually gets cheap). No band-fire
ever places or sizes an order. Sleeve metadata carries the 8% aggregate cap for downstream
sizing; the cap is NOT enforced here (this module does not know the book).

  python3 verticals/generators/quality_wishlist.py --screen [--no-broad] [--max-names N]
  python3 verticals/generators/quality_wishlist.py            # watch (default)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATA = HERE / "data"

CANDIDATES = DATA / "QUALITY_WISHLIST_CANDIDATES.json"
ACTIVE = DATA / "quality_wishlist_active.json"      # POST-CULL list — does not exist until the principal saves it
FACTS = DATA / "quality_wishlist_facts.json"        # extracted XBRL annuals cache (never the raw companyfacts)
STATE = DATA / "quality_wishlist_state.json"        # per-name band state: quiet period, cheap_since
FIRES_REL = "verticals/generators/data/QUALITY_WISHLIST_FIRES.json"   # pre-registered grading log
FIRES = ROOT / FIRES_REL
SP_CONSTITUENTS = DATA / "_sp_constituents.json"
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
PARAMETRIC = ROOT / "desk" / "data" / "parametric_holdings.txt"
CULL_DIR = ROOT / "desk" / "reports"

UA = "signalos-desk 4tripathy@gmail.com"
# Bump whenever annuals_from_facts changes shape or arithmetic: cached records built by an older
# extractor are refetched rather than trusted (the raw payload is not kept, so it cannot be replayed).
EXTRACT_VERSION = 3

# ---- gate thresholds (§3) ------------------------------------------------------------------
LOOKBACK_YEARS = 10
MIN_USABLE_YEARS = 8            # fewer => DEGRADED-INSUFFICIENT-HISTORY, never a pass or a fail
ROIC_MIN = 0.15
ROIC_MIN_YEARS = 8
REV_UP_MIN_YEARS = 8
GM_TOLERANCE_BPS = 300.0        # latest within 300bps of the 10yr median counts as "stable"
MAX_ND_EBITDA = 2.0
SHARE_GROWTH_TOL = 0.02         # "flat" tolerance over the whole decade, not per year
DEFAULT_TAX_RATE = 0.21
TAX_RATE_CLAMP = (0.10, 0.35)

# ---- band thresholds (§4) ------------------------------------------------------------------
FAIR_PCT = 50.0
CHEAP_PCT = 20.0
STANDSTILL_DROP_PTS = 25.0
MIN_BAND_OBS = 200              # ~4 years of weekly observations; below this the band is DEGRADED
QUIET_DAYS = 45                 # re-fire suppression unless the band deepens

# ---- guards (§5) ---------------------------------------------------------------------------
PEAK_MARGIN_PCTILE = 90.0
ACQ_STEPUP = 0.10
VALUE_TRAP_DECAY_DAYS = 365

# ---- sleeve metadata (decision D) -----------------------------------------------------------
SLEEVE = {"name": "quality_wishlist", "aggregate_cap_pct": 8.0,
          "cap_note": "8% of book AGGREGATE across all wishlist-originated positions "
                      "(principal ruling D, 2026-08-13). Per-name sizing is the court's, not "
                      "this module's — the cap is metadata for downstream sizing, NOT enforced here."}

PROPOSES_ONLY = ("PROPOSES ONLY: lazy court — trap-verify -> red -> blue -> adjudicate before "
                 "any staging; the wishlist proposes, the court disposes")


# ============================================================================ small helpers

def _f(x, d=None):
    try:
        v = float(x)
        return d if (v != v or math.isinf(v)) else v
    except Exception:
        return d


def _norm(sym: str) -> str:
    """Ticker family normalization — matches desk.court_queue so ledger exclusion agrees."""
    return re.split(r"[.\s]", str(sym or "").strip())[0].upper()


def _rel(p) -> str:
    """Repo-relative path for human output; falls back to the absolute path under test."""
    try:
        return str(Path(p).relative_to(ROOT))
    except Exception:
        return str(p)


def _read_json(p: Path, default=None):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return default


def pct_rank(series: list[float], value: float) -> float | None:
    """Percentile of `value` within `series` (share of observations <= value, in points).
    `value` is assumed to be a member of the distribution (it is: the current week)."""
    s = [v for v in series if v is not None]
    if not s or value is None:
        return None
    return 100.0 * sum(1 for v in s if v <= value) / len(s)


def _slope(pairs: list[tuple[float, float]]) -> float | None:
    """OLS slope of y on x. Used only for the gross-margin trend."""
    pts = [(x, y) for x, y in pairs if y is not None]
    if len(pts) < 3:
        return None
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    den = sum((p[0] - mx) ** 2 for p in pts)
    if den == 0:
        return None
    return sum((p[0] - mx) * (p[1] - my) for p in pts) / den


# ============================================================================ XBRL extraction

# us-gaap tags in preference order. First tag that yields a value for a fiscal year wins.
FLOW_TAGS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax",
                "RevenueFromContractWithCustomerIncludingAssessedTax",
                "Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet",
                "RevenueFromContractWithCustomerExcludingAssessedTaxMember"],
    "gross_profit": ["GrossProfit"],
    "cogs": ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold", "CostOfServices"],
    "ebit": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "pretax": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
               "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
               "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic"],
    "tax": ["IncomeTaxExpenseBenefit", "IncomeTaxExpenseBenefitContinuingOperations"],
    # EBIT FALLBACK: a large minority of filers (ADM, AES and most conglomerates) never tag
    # OperatingIncomeLoss. Rather than degrade them for a tagging convention, EBIT falls back to
    # pretax income + interest expense, flagged per-year as ebit_from_pretax. The approximation
    # leaves other non-operating income (equity-method, FX, gains) IN EBIT, so it reads slightly
    # HIGH — surfaced on the name, never silent.
    "interest": ["InterestExpense", "InterestExpenseDebt", "InterestExpenseNonoperating",
                 "InterestAndDebtExpense"],
    "dna": ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet",
            "DepreciationAndAmortization", "Depreciation"],
}
SHARE_TAGS = ["WeightedAverageNumberOfDilutedSharesOutstanding",
              "WeightedAverageNumberOfDilutedSharesOutstandingBasicAndDiluted"]
INSTANT_TAGS = {
    "equity": ["StockholdersEquity",
               "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "sti": ["ShortTermInvestments", "MarketableSecuritiesCurrent",
            "AvailableForSaleSecuritiesDebtSecuritiesCurrent"],
    "debt_total": ["DebtLongtermAndShorttermCombinedAmount"],
    # Tag coverage matters more than tag purity here: DHI files its debt as NotesPayable
    # (homebuilder convention) and VRSN as ConvertibleDebtNoncurrent, and either omission reads
    # as a debt-free balance sheet on a levered company — a false PASS on the leverage gate.
    "debt_lt": ["LongTermDebtNoncurrent", "LongTermDebt",
                "LongTermDebtAndCapitalLeaseObligations", "LongTermNotesPayable",
                "NotesPayable", "SeniorNotes", "SeniorLongTermNotes",
                "ConvertibleDebtNoncurrent", "ConvertibleDebt", "ConvertibleNotesPayable",
                "UnsecuredDebt", "SecuredDebt"],
    "debt_cur": ["LongTermDebtCurrent", "DebtCurrent",
                 "LongTermDebtAndCapitalLeaseObligationsCurrent", "ShortTermBorrowings",
                 "OtherShortTermBorrowings", "CommercialPaper", "LinesOfCreditCurrent",
                 "NotesPayableCurrent", "ConvertibleDebtCurrent",
                 "ConvertibleNotesPayableCurrent"],
    "goodwill": ["Goodwill"],
}
ANNUAL_FORMS = ("10-K", "10-K/A")


def _fy_of(end_iso: str) -> int | None:
    """Fiscal-year label from a period-end date. A December-through-May year-end belongs to the
    PRIOR calendar year's fiscal label (an Jan-2026 FYE is FY2025), which is the convention the
    Street uses and keeps off-calendar filers aligned with their peers."""
    try:
        d = dt.date.fromisoformat(end_iso)
    except Exception:
        return None
    return d.year if d.month >= 6 else d.year - 1


def _pick_flow(units: list[dict]) -> dict[int, tuple[float, str, str]]:
    """{fy: (value, end_date, filed)} for a DURATION concept, annual periods from 10-Ks only,
    latest FILED wins (so restatements supersede)."""
    out: dict[int, tuple[float, str, str]] = {}
    for e in units or []:
        if e.get("form") not in ANNUAL_FORMS or not e.get("start") or not e.get("end"):
            continue
        try:
            days = (dt.date.fromisoformat(e["end"]) - dt.date.fromisoformat(e["start"])).days
        except Exception:
            continue
        if not (340 <= days <= 400):
            continue
        fy = _fy_of(e["end"])
        v = _f(e.get("val"))
        if fy is None or v is None:
            continue
        prev = out.get(fy)
        if prev is None or str(e.get("filed", "")) >= prev[2]:
            out[fy] = (v, e["end"], str(e.get("filed", "")))
    return out


def _pick_instant(units: list[dict]) -> dict[int, tuple[float, str, str]]:
    """{fy: (value, end_date, filed)} for an INSTANT concept. A 10-K carries the comparative
    prior-year balance sheet too, which is why 10 years of history needs far fewer than 10 filings."""
    out: dict[int, tuple[float, str, str]] = {}
    for e in units or []:
        if e.get("form") not in ANNUAL_FORMS or e.get("start") or not e.get("end"):
            continue
        fy = _fy_of(e["end"])
        v = _f(e.get("val"))
        if fy is None or v is None:
            continue
        prev = out.get(fy)
        if prev is None or str(e.get("filed", "")) >= prev[2]:
            out[fy] = (v, e["end"], str(e.get("filed", "")))
    return out


def _series(facts: dict, names: list[str], unit: str, instant: bool) -> dict[int, tuple[float, str, str]]:
    gaap = (facts.get("facts") or {}).get("us-gaap") or {}
    merged: dict[int, tuple[float, str, str]] = {}
    for tag in names:
        node = gaap.get(tag)
        if not node:
            continue
        units = (node.get("units") or {}).get(unit)
        if not units:
            continue
        got = _pick_instant(units) if instant else _pick_flow(units)
        for fy, tup in got.items():
            merged.setdefault(fy, tup)     # earlier tag in the preference list wins
    return merged


def chained_shares(facts: dict) -> dict:
    """Diluted share counts on ONE split-adjusted basis, chain-linked filing by filing.

    THE BUG THIS EXISTS FOR: XBRL share counts are restated for splits only in filings made
    AFTER the split. AAPL's FY2016 count sits in the FY2016-18 10-Ks at the pre-split basis and
    its FY2024 count at the post-4:1 basis, so a naive latest-filed-wins series shows Apple's
    diluted share count RISING 173% across the decade — and the owner-alignment gate (criterion
    5) then rejects the most aggressive buyer of its own stock in the index. It also wrecks the
    band engine, because yfinance prices are split-ADJUSTED and market cap is price x shares.

    THE FIX: every 10-K reports two or three fiscal years on ONE internally consistent basis, so
    the RATIO between two years inside a single accession is always split-correct. Anchor on the
    newest filing and chain those within-filing ratios backwards. Splits and restatements both
    fall out for free, and nothing is inferred from a guessed split factor."""
    gaap = (facts.get("facts") or {}).get("us-gaap") or {}
    rows = []
    for tag in SHARE_TAGS:
        node = gaap.get(tag)
        if not node:
            continue
        for e in ((node.get("units") or {}).get("shares") or []):
            if e.get("form") not in ANNUAL_FORMS or not e.get("start") or not e.get("end"):
                continue
            try:
                days = (dt.date.fromisoformat(e["end"]) - dt.date.fromisoformat(e["start"])).days
            except Exception:
                continue
            if not (340 <= days <= 400):
                continue
            fy, v = _fy_of(e["end"]), _f(e.get("val"))
            if fy is None or not v or v <= 0:
                continue
            rows.append((str(e.get("accn", "")), str(e.get("filed", "")), fy, v, e["end"]))
        if rows:
            break
    if not rows:
        return {}
    byacc: dict[str, dict] = {}
    ends: dict[int, str] = {}
    for accn, filed, fy, v, end in rows:
        a = byacc.setdefault(accn, {"filed": filed, "vals": {}})
        a["vals"].setdefault(fy, v)
        ends.setdefault(fy, end)
    order = sorted(byacc.values(), key=lambda a: a["filed"], reverse=True)
    adj = dict(order[0]["vals"])                       # newest filing = the current split basis
    for _ in range(len(order) + 2):
        changed = False
        for a in order:
            common = [fy for fy in a["vals"] if fy in adj]
            if not common:
                continue
            ref = max(common)                          # scale off the most recent shared year
            k = adj[ref] / a["vals"][ref]
            for fy, v in a["vals"].items():
                if fy not in adj:
                    adj[fy] = v * k
                    changed = True
        if not changed:
            break
    return {fy: (adj[fy], ends.get(fy), "") for fy in adj}


def _debt_series(inst: dict, fys: list) -> tuple[dict, str | None]:
    """Total debt per fiscal year, with the two failure modes XBRL debt tagging actually has.

    (1) A genuinely DEBT-FREE filer (ANET) tags no debt concept at all in the window. Treating
        that as unknown would drop the name for having a clean balance sheet, so an empty window
        means zero, flagged NO-DEBT-TAG.
    (2) A LEVERED filer tags debt under a different concept from year to year (ADI moves between
        LongTermDebt, LongTermDebtNoncurrent, DebtCurrent and CommercialPaper), leaving INTERIOR
        holes. Debt is a slow-moving balance-sheet quantity, so interior holes are interpolated
        between the nearest reported years, flagged DEBT-INTERPOLATED. Dropping those years
        instead would degrade half the levered universe on a tagging convention.

    The fill is ASYMMETRIC, and that asymmetry is the point. Years BEFORE the first reported debt
    year are set to ZERO, not held flat backwards: a company starts tagging debt when it issues
    debt. META tags LongTermDebt only from FY2022; holding that ~$18bn flat back to FY2016 would
    invent leverage on a company that had none, and would corrupt both its ROIC denominator and
    its historical EV/EBIT band. Years AFTER the last reported year are held flat, because debt
    does not silently disappear."""
    known = {}
    for fy in fys:
        v = inst["debt_total"].get(fy)
        if v:
            known[fy] = v[0]
            continue
        lt, cur = inst["debt_lt"].get(fy), inst["debt_cur"].get(fy)
        if lt or cur:
            known[fy] = (lt[0] if lt else 0.0) + (cur[0] if cur else 0.0)
    if not known:
        return {fy: 0.0 for fy in fys}, "NO-DEBT-TAG(no debt concept in the window — treated as debt-free)"
    ks = sorted(known)
    out, interp, pre = {}, 0, 0
    for fy in fys:
        if fy in known:
            out[fy] = known[fy]
            continue
        lo = max([k for k in ks if k < fy], default=None)
        hi = min([k for k in ks if k > fy], default=None)
        if lo is None:
            out[fy] = 0.0                      # pre-issuance: untagged means none, not "same as later"
            pre += 1
        elif hi is None:
            out[fy] = known[lo]
        else:
            out[fy] = known[lo] + (known[hi] - known[lo]) * ((fy - lo) / (hi - lo))
            interp += 1
    bits = []
    if interp:
        bits.append(f"{interp} interior year(s) interpolated from adjacent reported years")
    if pre:
        bits.append(f"{pre} year(s) before the first reported debt treated as DEBT-FREE")
    flag = f"DEBT-PARTIAL({'; '.join(bits)}, of {len(fys)} years)" if bits else None
    return out, flag


def annuals_from_facts(facts: dict, lookback: int = LOOKBACK_YEARS + 3) -> list[dict]:
    """Reduce a companyfacts payload to a compact per-fiscal-year record list (ascending).
    The raw payload is never cached — only this."""
    flows = {k: _series(facts, tags, "USD", instant=False) for k, tags in FLOW_TAGS.items()}
    inst = {k: _series(facts, tags, "USD", instant=True) for k, tags in INSTANT_TAGS.items()}
    shares = chained_shares(facts)
    fys = sorted({fy for d in list(flows.values()) + list(inst.values()) + [shares] for fy in d})
    fys = fys[-lookback:]
    debt_by_fy, debt_flag = _debt_series(inst, fys)
    out = []
    for fy in fys:
        def g(d, k=None):
            t = d.get(fy)
            return t[0] if t else None
        rev = g(flows["revenue"])
        gp = g(flows["gross_profit"])
        cogs = g(flows["cogs"])
        if gp is None and rev is not None and cogs is not None:
            gp = rev - cogs
        ebit = g(flows["ebit"])
        ni = g(flows["net_income"])
        pretax = g(flows["pretax"])
        tax = g(flows["tax"])
        dna = g(flows["dna"])
        ebit_from_pretax = False
        if ebit is None and pretax is not None:
            ebit = pretax + (g(flows["interest"]) or 0.0)
            ebit_from_pretax = True
        equity = g(inst["equity"])
        cash = g(inst["cash"]) or 0.0
        sti = g(inst["sti"]) or 0.0
        debt = debt_by_fy.get(fy)
        gw = g(inst["goodwill"])
        sh = g(shares)
        # period end date: prefer the revenue period, fall back to any concept that has one
        end = None
        for d in (flows["revenue"], flows["ebit"], inst["equity"], shares):
            if d.get(fy):
                end = d[fy][1]
                break

        tax_rate = None
        if pretax and pretax > 0 and tax is not None:
            tax_rate = max(TAX_RATE_CLAMP[0], min(TAX_RATE_CLAMP[1], tax / pretax))
        nopat = None if ebit is None else ebit * (1 - (tax_rate if tax_rate is not None else DEFAULT_TAX_RATE))
        net_debt = None if debt is None else debt - cash - sti
        invested = None if (equity is None or net_debt is None) else equity + net_debt
        roic, roic_flag = None, None
        if nopat is not None and invested is not None:
            if invested > 0:
                roic = nopat / invested
            elif nopat > 0:
                roic, roic_flag = float("inf"), "ROIC_UNBOUNDED"   # negative invested capital
            else:
                roic, roic_flag = None, "ROIC_UNDEFINED"
        out.append({
            "fy": fy, "end": end, "revenue": rev, "gross_profit": gp,
            "gross_margin": (gp / rev) if (gp is not None and rev) else None,
            "ebit": ebit, "op_margin": (ebit / rev) if (ebit is not None and rev) else None,
            # EPS is COMPUTED from net income over the chain-linked share count rather than read
            # from EarningsPerShareDiluted, because the reported tag carries the same split-basis
            # inconsistency across filings that `chained_shares` exists to remove. The standstill
            # trigger compares EPS across years, so a consistent basis matters more here than the
            # reported figure's extra precision.
            "net_income": ni, "eps_diluted": (ni / sh) if (ni is not None and sh) else None,
            "tax_rate": tax_rate, "nopat": nopat, "equity": equity, "cash": cash + sti,
            "debt": debt, "net_debt": net_debt, "invested_capital": invested,
            "ebitda": (ebit + dna) if (ebit is not None and dna is not None) else ebit,
            "ebitda_is_ebit_proxy": ebit is not None and dna is None,
            "ebit_from_pretax": ebit_from_pretax, "debt_flag": debt_flag,
            "dil_sh": sh, "goodwill": gw, "roic": roic, "roic_flag": roic_flag,
        })
    return out


# ============================================================================ the quality gate

def _usable(y: dict) -> bool:
    return all(y.get(k) is not None for k in ("revenue", "ebit", "equity", "dil_sh"))


def quality_gate(annuals: list[dict], lookback: int = LOOKBACK_YEARS,
                 min_years: int = MIN_USABLE_YEARS) -> dict:
    """§3. Returns {'status': PASS|FAIL|DEGRADED, 'reasons': [...], 'flags': [...], 'stats': {...}}.

    DEGRADED is a first-class outcome, not a silent skip: fewer than `min_years` usable
    fiscal years means the gate has no opinion and says so.

    WINDOW: `lookback` + 1 annual records, because "revenue grew in >= 8 of the trailing 10
    years" is a statement about 10 year-on-year CHANGES, which needs 11 observations. ROIC is a
    level, so it is counted over the last `lookback` records."""
    win = [y for y in annuals if y.get("fy") is not None][-(lookback + 1):]
    usable = [y for y in win if _usable(y)]
    stats = {"years_in_window": len(win), "usable_years": len(usable),
             "fy_first": win[0]["fy"] if win else None, "fy_last": win[-1]["fy"] if win else None}
    if len(usable) < min_years:
        return {"status": "DEGRADED", "reasons": [f"INSUFFICIENT-HISTORY {len(usable)}/{min_years} usable years"],
                "flags": [], "stats": stats}

    flags, reasons = [], []
    if any(y.get("ebit_from_pretax") for y in win):
        flags.append("EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as "
                     "pretax + interest expense, which leaves other non-operating income in; reads HIGH)")
    dflag = next((y.get("debt_flag") for y in win if y.get("debt_flag")), None)
    if dflag:
        flags.append(dflag)

    # 1. ROIC > 15% in >= 8 of the last 10 years
    roics = [y["roic"] for y in win[-lookback:] if y.get("roic") is not None]
    roic_yrs = sum(1 for r in roics if r > ROIC_MIN)
    if any(y.get("roic_flag") == "ROIC_UNBOUNDED" for y in win):
        flags.append("ROIC_UNBOUNDED(negative invested capital in >=1yr — buyback-driven; court must re-check)")
    stats["roic_yrs"] = roic_yrs
    stats["roic_obs"] = len(roics)
    stats["roic_latest"] = None if not win or win[-1].get("roic") is None else (
        None if win[-1]["roic"] == float("inf") else round(win[-1]["roic"], 4))
    if len(roics) < ROIC_MIN_YEARS:
        # Not a FAIL: a name cannot fail a test that could not be run on it. Missing balance-sheet
        # tags in three of ten years is a coverage gap, and calling it a quality verdict would be
        # exactly the silent-fail this module refuses.
        return {"status": "DEGRADED",
                "reasons": [f"INSUFFICIENT-HISTORY {len(roics)}/{ROIC_MIN_YEARS} computable ROIC years "
                            f"(missing EBIT, equity or debt tags)"],
                "flags": flags, "stats": stats}
    if roic_yrs < ROIC_MIN_YEARS:
        reasons.append(f"ROIC>15% in only {roic_yrs}/{len(roics)}yrs (need {ROIC_MIN_YEARS})")

    # 2. revenue grew in >= 8 years
    revs = [(y["fy"], y["revenue"]) for y in win if y.get("revenue") is not None]
    comps = [(revs[i][1] > revs[i - 1][1]) for i in range(1, len(revs))]
    rev_up = sum(1 for c in comps if c)
    stats["rev_up_yrs"], stats["rev_comparisons"] = rev_up, len(comps)
    if len(comps) < min_years:
        return {"status": "DEGRADED",
                "reasons": [f"INSUFFICIENT-HISTORY {len(comps)}/{min_years} revenue year-on-year comparisons"],
                "flags": flags, "stats": stats}
    if rev_up < REV_UP_MIN_YEARS:
        reasons.append(f"revenue rose in only {rev_up}/{len(comps)}yrs (need {REV_UP_MIN_YEARS})")

    # 3. gross margin stable-or-rising
    gms = [(y["fy"], y["gross_margin"]) for y in win if y.get("gross_margin") is not None]
    if len(gms) < 5:
        # GM is not reported by every filer (many industrials disclose opex only). Not a silent
        # pass: the criterion is WAIVED and the waiver is carried into the cull sheet.
        flags.append("GM-UNAVAILABLE-WAIVED(fewer than 5 reported gross-margin years)")
        stats["gm_latest"] = stats["gm_median"] = stats["gm_slope_bps_per_yr"] = None
    else:
        sl = _slope([(float(fy), v) for fy, v in gms])
        med = statistics.median(v for _, v in gms)
        latest = gms[-1][1]
        stats["gm_latest"] = round(latest, 4)
        stats["gm_median"] = round(med, 4)
        stats["gm_slope_bps_per_yr"] = None if sl is None else round(sl * 1e4, 1)
        ok = (sl is not None and sl >= 0) or ((latest - med) * 1e4 >= -GM_TOLERANCE_BPS)
        if not ok:
            reasons.append(f"gross margin eroding: slope {sl * 1e4:+.0f}bps/yr and latest "
                           f"{(latest - med) * 1e4:+.0f}bps vs 10yr median")

    # 4. net debt / EBITDA < 2.0 (latest usable year)
    last = usable[-1]
    nd, ebitda = last.get("net_debt"), last.get("ebitda")
    if nd is None or ebitda is None or ebitda <= 0:
        stats["nd_ebitda"] = None
        reasons.append("net-debt/EBITDA UNKNOWN (missing debt or non-positive EBITDA) — "
                       "never treated as clean")
    else:
        ratio = 0.0 if nd <= 0 else nd / ebitda
        stats["nd_ebitda"] = round(ratio, 2)
        stats["net_cash"] = nd <= 0
        if last.get("ebitda_is_ebit_proxy"):
            flags.append("EBITDA~EBIT(no D&A tag — conservative, ratio overstated)")
        if ratio >= MAX_ND_EBITDA:
            reasons.append(f"net debt/EBITDA {ratio:.2f}x (max {MAX_ND_EBITDA})")

    # 5. diluted share count flat or shrinking
    shs = [(y["fy"], y["dil_sh"]) for y in win if y.get("dil_sh")]
    if len(shs) < min_years:
        return {"status": "DEGRADED",
                "reasons": [f"INSUFFICIENT-HISTORY {len(shs)}/{min_years} diluted-share years"],
                "flags": flags, "stats": stats}
    chg = shs[-1][1] / shs[0][1] - 1
    stats["share_chg_pct"] = round(chg * 100, 1)
    if chg > SHARE_GROWTH_TOL:
        reasons.append(f"diluted shares +{chg * 100:.1f}% over the window (max +{SHARE_GROWTH_TOL * 100:.0f}%)")

    return {"status": "FAIL" if reasons else "PASS", "reasons": reasons, "flags": flags, "stats": stats}


# ============================================================================ the band engine

def _interp(annuals: list[dict], key: str):
    """Linear interpolation of an annual series between fiscal period-END dates, flat outside.

    HONEST CAVEAT: interpolating BETWEEN two fiscal year-ends uses the later year's reported
    figure inside the earlier year, so a historical weekly point embeds information published
    after that week. This is deliberate and is confined to the REFERENCE DISTRIBUTION (what
    range of multiples this business has traded at). The CURRENT observation — the one that
    fires — is built from the latest REPORTED year only, flat-forward, so no fire depends on
    unpublished data."""
    pts = []
    for y in annuals:
        v, e = y.get(key), y.get("end")
        if v is None or not e:
            continue
        try:
            pts.append((dt.date.fromisoformat(e), float(v)))
        except Exception:
            continue
    pts.sort()
    if not pts:
        return lambda d: None

    def f(d: dt.date):
        if d <= pts[0][0]:
            return pts[0][1]
        if d >= pts[-1][0]:
            return pts[-1][1]
        for i in range(1, len(pts)):
            if d <= pts[i][0]:
                (d0, v0), (d1, v1) = pts[i - 1], pts[i]
                span = (d1 - d0).days or 1
                return v0 + (v1 - v0) * ((d - d0).days / span)
        return pts[-1][1]
    return f


def multiple_series(weekly: list[tuple[dt.date, float]], annuals: list[dict]) -> dict:
    """Weekly EV/EBIT and P/E off interpolated annual fundamentals.
        EV      = price x diluted shares + net debt
        EV/EBIT = EV / EBIT              (dropped when EBIT <= 0 — a negative multiple is not cheap)
        P/E     = market cap / net income (dropped when NI <= 0, same reason)"""
    fsh, febit, fni, fnd = (_interp(annuals, "dil_sh"), _interp(annuals, "ebit"),
                            _interp(annuals, "net_income"), _interp(annuals, "net_debt"))
    ev_ebit, pe = [], []
    for d, px in weekly:
        sh = fsh(d)
        if not sh or px is None or px <= 0:
            continue
        mcap = px * sh
        ebit, ni, nd = febit(d), fni(d), fnd(d)
        if ebit and ebit > 0 and nd is not None:
            ev_ebit.append((d, (mcap + nd) / ebit))
        if ni and ni > 0:
            pe.append((d, mcap / ni))
    return {"ev_ebit": ev_ebit, "pe": pe}


def _pct_now_and_year_ago(pairs: list[tuple[dt.date, float]]) -> tuple[float | None, float | None, float | None]:
    """(current value, current percentile, percentile 52w ago) — both percentiles measured against
    the SAME full-history distribution so the 12-month move is a like-for-like comparison."""
    if len(pairs) < MIN_BAND_OBS:
        return None, None, None
    vals = [v for _, v in pairs]
    cur = vals[-1]
    p_now = pct_rank(vals, cur)
    idx = max(0, len(vals) - 53)
    p_then = pct_rank(vals, vals[idx]) if len(vals) > 53 else None
    return cur, p_now, p_then


def assess_bands(annuals: list[dict], weekly: list[tuple[dt.date, float]],
                 suppress_pe: bool = False) -> dict:
    """Combined own-history percentile. Combined = MAX of the available multiples' percentiles:
    a name only reads cheap when BOTH multiples read cheap (the conservative direction)."""
    ms = multiple_series(weekly, annuals)
    ev, p_ev, p_ev_prev = _pct_now_and_year_ago(ms["ev_ebit"])
    pe, p_pe, p_pe_prev = (None, None, None) if suppress_pe else _pct_now_and_year_ago(ms["pe"])
    parts = [p for p in (p_ev, p_pe) if p is not None]
    prev = [p for p in (p_ev_prev, p_pe_prev) if p is not None]
    return {"ev_ebit": None if ev is None else round(ev, 2),
            "pe": None if pe is None else round(pe, 2),
            "pct_ev_ebit": None if p_ev is None else round(p_ev, 1),
            "pct_pe": None if p_pe is None else round(p_pe, 1),
            "pct": None if not parts else round(max(parts), 1),
            "pct_1y_ago": None if not prev else round(max(prev), 1),
            "n_obs_ev_ebit": len(ms["ev_ebit"]), "n_obs_pe": len(ms["pe"]),
            "pe_suppressed": suppress_pe}


def band_of(pct: float | None) -> str | None:
    if pct is None:
        return None
    if pct <= CHEAP_PCT:
        return "CHEAP"
    if pct <= FAIR_PCT:
        return "FAIR"
    return None


def standstill_trigger(pct_now: float | None, pct_1y_ago: float | None, annuals: list[dict]) -> bool:
    """§4 STANDSTILL: percentile fell >= 25 points over 12 months WHILE trailing EPS rose."""
    if pct_now is None or pct_1y_ago is None:
        return False
    if (pct_1y_ago - pct_now) < STANDSTILL_DROP_PTS:
        return False
    eps = [y.get("eps_diluted") for y in annuals if y.get("eps_diluted") is not None]
    return len(eps) >= 2 and eps[-1] > eps[-2]


# ---- trap guards (§5) -----------------------------------------------------------------------

def guard_peak_earnings(annuals: list[dict]) -> str | None:
    """§5.1 — latest operating margin above its own p90 means the cheap multiple is
    denominator-flattered. Downgrades the fire to REVIEW; the court must normalize."""
    oms = [y["op_margin"] for y in annuals if y.get("op_margin") is not None]
    if len(oms) < 5:
        return None
    p90 = statistics.quantiles(oms, n=10)[8]
    if oms[-1] > p90:
        return (f"PEAK-EARNINGS: latest operating margin {oms[-1] * 100:.1f}% > own p90 "
                f"{p90 * 100:.1f}% — multiple is denominator-flattered, court must normalize")
    return None


def guard_crash_cheapness(ticker: str, dislocated: dict | bool) -> str | None:
    """§5.2 — a falling knife entering its cheap decile is the DISLOCATION pipeline's case, not
    the wishlist's. The fire is emitted for the record but routed to cause-check, and it is NOT
    enqueued to court from here (that would double-court the same name)."""
    if not dislocated:
        return None
    src = dislocated if isinstance(dislocated, str) else (
        dislocated.get(ticker) if isinstance(dislocated, dict) else "dislocation screen")
    return (f"CRASH-CHEAPNESS: live dislocation/broken-print hit ({src}) — CAUSE-CHECK FIRST; "
            f"this is the dislocation pipeline's case, the wishlist stands down")


def guard_acq_stepup(annuals: list[dict]) -> str | None:
    """§5.3 — share count or goodwill up >10% in the trailing year means EPS is acquisition-
    stepped. P/E percentile is suppressed; the band is measured on EV/EBIT only."""
    if len(annuals) < 2:
        return None
    a, b = annuals[-2], annuals[-1]
    bits = []
    if a.get("dil_sh") and b.get("dil_sh") and (b["dil_sh"] / a["dil_sh"] - 1) > ACQ_STEPUP:
        bits.append(f"diluted shares +{(b['dil_sh'] / a['dil_sh'] - 1) * 100:.1f}%")
    ga, gb = a.get("goodwill"), b.get("goodwill")
    if gb:
        if not ga:
            bits.append("goodwill appeared from nil")
        elif (gb / ga - 1) > ACQ_STEPUP:
            bits.append(f"goodwill +{(gb / ga - 1) * 100:.1f}%")
    if not bits:
        return None
    return f"ACQ-STEP-UP: {', '.join(bits)} in the trailing year — P/E percentile SUPPRESSED, EV/EBIT only"


def guard_value_trap_decay(prior: dict | None, today: dt.date) -> str | None:
    """§5.4 — a name that has sat in CHEAP > 12 months with no court ACCEPT gets a mandatory
    re-gate. The band percentile itself decays as cheap years enter the lookback; that is a
    feature (self-correcting reference) but it must be SURFACED, never silent."""
    if not prior or not prior.get("cheap_since"):
        return None
    try:
        since = dt.date.fromisoformat(prior["cheap_since"])
    except Exception:
        return None
    days = (today - since).days
    if days < VALUE_TRAP_DECAY_DAYS:
        return None
    return (f"VALUE-TRAP-DECAY: {days}d in the CHEAP band with no court ACCEPT — MANDATORY RE-GATE "
            f"(is the 10yr multiple history still the right reference, or has the business changed "
            f"regime? the reference distribution is itself decaying as cheap years enter the lookback)")


# ============================================================================ evaluation

def evaluate_name(ticker: str, annuals: list[dict], weekly: list[tuple[dt.date, float]], *,
                  today: dt.date, prior: dict | None = None, dislocated=False,
                  parametric: set | frozenset = frozenset(),
                  quiet_days: int = QUIET_DAYS) -> dict:
    """One name, one verdict. Pure — no I/O — so every band trigger and every trap guard is
    testable offline. Returns a record whose 'status' is FIRE / NO_FIRE / DEGRADED."""
    out = {"ticker": ticker, "asof": today.isoformat(), "guards": [], "notes": []}

    acq = guard_acq_stepup(annuals)
    if acq:
        out["guards"].append(acq)
    bands = assess_bands(annuals, weekly, suppress_pe=bool(acq))
    out.update({k: bands[k] for k in ("ev_ebit", "pe", "pct_ev_ebit", "pct_pe", "pct",
                                      "pct_1y_ago", "n_obs_ev_ebit", "n_obs_pe", "pe_suppressed")})

    decay = guard_value_trap_decay(prior, today)
    if decay:
        out["guards"].append(decay)
        out["value_trap_decay"] = True

    if bands["pct"] is None:
        out["status"] = "DEGRADED"
        out["reason"] = (f"THIN-BAND-HISTORY: {bands['n_obs_ev_ebit']} EV/EBIT and {bands['n_obs_pe']} P/E "
                         f"weekly observations, need {MIN_BAND_OBS} — no band, no fire "
                         f"(silence here is a data gap, NOT 'not cheap')")
        return out

    band = band_of(bands["pct"])
    stand = standstill_trigger(bands["pct"], bands["pct_1y_ago"], annuals)
    out["band"], out["standstill"] = band, stand
    if not band and not stand:
        out["status"] = "NO_FIRE"
        return out

    # quiet period — a name re-fires only when it DEEPENS (FAIR->CHEAP) or newly standstills
    rank = {"FAIR": 1, "CHEAP": 2}
    if prior and prior.get("fired"):
        try:
            age = (today - dt.date.fromisoformat(prior["fired"])).days
        except Exception:
            age = 10 ** 6
        deepened = rank.get(band or "", 0) > rank.get(prior.get("band") or "", 0)
        new_stand = stand and not prior.get("standstill")
        if age < quiet_days and not deepened and not new_stand:
            out["status"] = "NO_FIRE"
            out["notes"].append(f"quiet period: fired {age}d ago at {prior.get('band')}, no deepening")
            return out

    peak = guard_peak_earnings(annuals)
    if peak:
        out["guards"].append(peak)
    crash = guard_crash_cheapness(ticker, dislocated)
    if crash:
        out["guards"].append(crash)

    label = "starter" if band == "CHEAP" else ("tranche-1" if band == "FAIR" else "tranche-1")
    sev = "MED" if (band == "CHEAP" or stand) else "LOW"
    route = "court:TRAP_VERIFY"
    if crash:
        sev, route = "REVIEW", "dislocation_pipeline:cause-check"
    elif peak:
        sev, route = "REVIEW", "court:TRAP_VERIFY(normalize-earnings)"

    if ticker in parametric or _norm(ticker) in parametric:
        out["wash_sale_check"] = True
        out["guards"].append("WASH-SALE-CHECK: held in the household's Parametric direct-indexing "
                             "account — a wishlist buy at IBKR while Parametric harvests the same "
                             "name is the exact interaction the household map warns about")
    else:
        out["wash_sale_check"] = False

    out.update({"status": "FIRE", "severity": sev, "route": route,
                "sizing_label": label, "sleeve": dict(SLEEVE)})
    return out


# ============================================================================ network / caching

_rate_lock = threading.Lock()
_last_call = [0.0]


def _throttle(min_interval: float):
    with _rate_lock:
        wait = min_interval - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()


def _get_json(url: str, timeout: int = 45, min_interval: float = 0.15):
    """data.sec.gov accepts a plain UA (desk/sec_fetch.py is only needed for www.sec.gov/Archives)."""
    _throttle(min_interval)
    r = subprocess.run(["curl", "-s", "--compressed", "--max-time", str(timeout), url,
                        "-H", f"User-Agent: {UA}", "-H", "Accept-Encoding: gzip, deflate"],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


_TICKER_CIK = None


def ticker_cik_map() -> dict:
    global _TICKER_CIK
    if _TICKER_CIK is None:
        d = _get_json("https://www.sec.gov/files/company_tickers.json") or {}
        _TICKER_CIK = {}
        for v in d.values():
            try:
                _TICKER_CIK.setdefault(v["ticker"].upper(), (int(v["cik_str"]), v.get("title", "")))
            except Exception:
                continue
    return _TICKER_CIK


def _sic_of(cik: int) -> tuple[int | None, str | None]:
    sub = _get_json(f"https://data.sec.gov/submissions/CIK{cik:010d}.json") or {}
    try:
        return int(sub.get("sic") or 0) or None, sub.get("sicDescription")
    except Exception:
        return None, sub.get("sicDescription")


def fetch_sic(tickers: list[str], cache: dict, workers: int = 4,
              min_interval: float = 0.15) -> dict:
    """Resolve SIC for a list of tickers into the facts cache. Run BEFORE companyfacts so the
    financial exclusion (§6) happens on a small submissions payload instead of after paying for a
    multi-megabyte companyfacts download on a name we were always going to drop."""
    cmap = ticker_cik_map()
    stats = {"resolved": 0, "cached": 0, "no_cik": [], "failed": []}
    todo = []
    for t in tickers:
        rec = cache["names"].setdefault(t, {})
        if rec.get("sic_checked"):
            stats["cached"] += 1
            continue
        hit = cmap.get(t.upper())
        if not hit:
            stats["no_cik"].append(t)
            continue
        rec["cik"] = hit[0]
        rec.setdefault("entity", hit[1])
        todo.append((t, hit[0]))

    def one(job):
        t, cik = job
        return (t,) + _sic_of(cik)

    if todo:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for t, sic, desc in ex.map(one, todo):
                rec = cache["names"][t]
                if sic is None and desc is None:
                    stats["failed"].append(t)
                    continue
                rec.update({"sic": sic, "sic_desc": desc, "sic_checked": True})
                stats["resolved"] += 1
    return stats


def is_financial(sic: int | None) -> bool:
    """§6 — financials are OUT of v1: ROE is peak-cycle-masked and release-flattered, and the
    financials-screen vertical already covers them with the right tools. SIC 6000-6499 (banks,
    credit, brokers, insurance) and 6700-6799 (holding/investment offices, REITs)."""
    if sic is None:
        return False
    return 6000 <= sic <= 6499 or 6700 <= sic <= 6799


def _load_facts_cache() -> dict:
    d = _read_json(FACTS, {}) or {}
    return d if isinstance(d, dict) and "names" in d else {"asof": None, "names": {}}


def _save_facts_cache(cache: dict):
    cache["asof"] = dt.date.today().isoformat()
    tmp = FACTS.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, separators=(",", ":")))
    tmp.replace(FACTS)


def fetch_annuals(tickers: list[str], cache: dict, max_age_days: int = 7,
                  workers: int = 4, min_interval: float = 0.15) -> dict:
    """companyfacts -> compact annual records, cached. Returns {'fetched':n,'cached':n,'failed':[..]}."""
    cmap = ticker_cik_map()
    today = dt.date.today()
    todo = []
    stats = {"fetched": 0, "cached": 0, "no_cik": [], "failed": []}
    for t in tickers:
        rec = cache["names"].get(t)
        # A cached record can be stale in AGE or in SHAPE. The raw companyfacts payload is never
        # kept, so an extraction-logic change cannot be replayed offline — a version mismatch
        # forces a refetch rather than silently serving records built by older, buggier code.
        if rec and rec.get("fetched") and rec.get("extract_version") == EXTRACT_VERSION:
            try:
                if (today - dt.date.fromisoformat(rec["fetched"])).days <= max_age_days:
                    stats["cached"] += 1
                    continue
            except Exception:
                pass
        hit = cmap.get(t.upper())
        if not hit:
            stats["no_cik"].append(t)
            continue
        todo.append((t, hit[0], hit[1]))

    def one(job):
        t, cik, title = job
        facts = _get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
                          min_interval=min_interval)
        if not facts:
            return t, None
        try:
            return t, {"cik": cik, "entity": facts.get("entityName") or title,
                       "fetched": today.isoformat(), "extract_version": EXTRACT_VERSION,
                       "annuals": annuals_from_facts(facts)}
        except Exception as e:
            return t, {"error": f"{type(e).__name__}: {e}"}

    if todo:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for t, rec in ex.map(one, todo):
                if not rec or rec.get("error"):
                    stats["failed"].append(t)
                    continue
                # MERGE, never replace — the record already carries the SIC resolved earlier in
                # the run, and the desk's recurring overwrite-clobber bug is exactly this line.
                cache["names"].setdefault(t, {}).update(rec)
                stats["fetched"] += 1
    return stats


def weekly_prices(tickers: list[str], years: int = 10, chunk: int = 40,
                  retries: int = 3) -> dict[str, list]:
    """10y WEEKLY closes, batched. Weekly bars are ~1/5 the payload of daily and the bands only
    ever sample weekly, so this is the cheap axis to pull a decade on.

    Yahoo rate-limits by IP and the desk runs several sweeps against the same quota, so a batch
    that comes back rate-limited is RETRIED with backoff and, if it still fails, the names in it
    are simply absent — the caller reports them as DEGRADED. A rate limit must never read as
    'this name has no valuation history'."""
    import yfinance as yf
    out: dict[str, list] = {}
    pending = list(dict.fromkeys(tickers))
    for attempt in range(retries):
        for i in range(0, len(pending), chunk):
            part = pending[i:i + chunk]
            try:
                px = yf.download(part, period=f"{years}y", interval="1wk", progress=False,
                                 auto_adjust=True, threads=True)["Close"]
            except Exception as e:
                print(f"  [quality_wishlist] price batch {i}-{i + len(part)} raised "
                      f"{type(e).__name__} — those names stay pending")
                continue
            for t in part:
                try:
                    s = (px[t] if hasattr(px, "columns") and t in px.columns else px).dropna()
                except Exception:
                    continue
                if len(s) < 30:
                    continue
                out[t] = [(d.date() if hasattr(d, "date") else d, float(v)) for d, v in s.items()]
            time.sleep(1.0)
        pending = [t for t in pending if t not in out]
        if not pending or attempt == retries - 1:
            break
        # yfinance does NOT raise on a rate limit — it prints "Failed downloads" and hands back a
        # frame of NaNs, so a quota breach looks exactly like a delisted ticker. The only reliable
        # detector is the MISSING SET, and the only cure is waiting: Yahoo's IP limit runs for
        # tens of minutes and the desk points several sweeps at the same quota.
        wait = 45 * (attempt + 1) ** 2
        print(f"  [quality_wishlist] {len(pending)} names unpriced after pass {attempt + 1} — "
              f"backing off {wait}s before retrying (a rate limit must never read as 'no history')")
        time.sleep(wait)
    return out


# ============================================================================ context loaders

def ledger_families() -> set:
    rl = _read_json(LEDGER, {}) or {}
    return {_norm(n.get("ticker")) for n in rl.get("names", []) if n.get("ticker")}


def parametric_holdings() -> set:
    """Decision C: a MANUALLY maintained list — the Parametric direct-indexing account is not
    machine-readable to the desk. Created on first run with the one known entry (GOOGL)."""
    if not PARAMETRIC.exists():
        PARAMETRIC.parent.mkdir(parents=True, exist_ok=True)
        PARAMETRIC.write_text(
            "# parametric_holdings.txt — MANUALLY MAINTAINED BY THE PRINCIPAL.\n"
            "#\n"
            "# Decision C of QUALITY_WISHLIST_DESIGN.md (approved 2026-08-13): the household's\n"
            "# Parametric direct-indexing account holds large-cap singles and harvests them for\n"
            "# losses. That account is NOT machine-readable to the desk, so this file is the\n"
            "# desk's only view of it. A manual list is acceptable at n~75 wishlist names.\n"
            "#\n"
            "# WHY IT MATTERS: buying a name at IBKR while Parametric is harvesting the SAME name\n"
            "# creates a wash sale across accounts — the exact interaction the household portfolio\n"
            "# map warns about. Any wishlist band-fire on a name listed here carries a\n"
            "# WASH-SALE-CHECK label. The flag is a CHECK, not a block: skipping these names\n"
            "# outright would surrender the best compounders (principal's ruling C).\n"
            "#\n"
            "# FORMAT: one ticker per line. Blank lines and #-comments ignored.\n"
            "# MAINTENANCE: update whenever the Parametric sleeve's holdings change. A stale list\n"
            "# fails SILENT (a missing name simply carries no flag), so review it at each cull.\n"
            "#\n"
            "GOOGL   # the one KNOWN entry: ~$700k low-basis position, HOLD, no harvesting\n"
            "        # (user-explicit). Everything else in the Parametric sleeve is unlisted\n"
            "        # here until the principal enumerates it.\n")
        print(f"[quality_wishlist] created {PARAMETRIC} (manual Parametric list, GOOGL seeded)")
    out = set()
    for line in PARAMETRIC.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(line.upper())
    return out


def dislocation_hits(days: int = 30) -> dict[str, str]:
    """§5.2 input — names currently live in the drawdown pipelines. Read-only across the sweeps'
    own stores; a missing store is a missing INPUT, reported, never treated as 'no dislocation'."""
    hits, missing = {}, []
    today = dt.date.today()

    def fresh(d):
        try:
            return (today - dt.date.fromisoformat(str(d)[:10])).days <= days
        except Exception:
            return False

    for rel, label in (("verticals/generators/data/DISLOCATION_SWEEP.json", "dislocation_sweep"),
                       ("verticals/generators/data/INTL_DISLOCATION_SWEEP.json", "intl_dislocation_sweep")):
        d = _read_json(ROOT / rel)
        if d is None:
            missing.append(label)
            continue
        for h in (d.get("hits") or []):
            if h.get("ticker") and fresh(h.get("fired") or d.get("asof")):
                hits[h["ticker"]] = f"{label} {h.get('severity', '')}".strip()
    bp = _read_json(ROOT / "desk/data/BROKEN_PRINTS.json")
    if bp is None:
        missing.append("broken_print_radar")
    else:
        # {"sessions": {"YYYY-MM-DD": {"hits": {TICKER: {...}}, ...}}}
        for session, blob in (bp.get("sessions") or {}).items():
            if not fresh(session) or not isinstance(blob, dict):
                continue
            names = blob.get("hits") or {}
            for tk in (names if isinstance(names, dict) else
                       [r.get("ticker") for r in names if isinstance(r, dict)]):
                if tk:
                    hits.setdefault(tk, f"broken_print_radar {session}")
    if missing:
        print(f"[quality_wishlist] crash-cheapness guard INPUT MISSING: {', '.join(missing)} "
              f"— guard 2 is running on partial inputs this run (reported, not hidden)")
    return hits


def cohort_tags(days: int = 21) -> dict:
    """§7 — fires INHERIT the cohort layer's tags, so a wishlist fire during a cohort de-rate
    reads as 'quality dragged with its theme' rather than as an idiosyncratic opportunity. This
    is context on the fire, never a suppression: a compounder cheapened by a theme it does not
    deserve to be in is the best case the wishlist can produce, and the court decides which it is.

    Reads the cohort layer's own output (cohort_dislocation, and class_dislocation's events)
    defensively — an absent file is REPORTED, never fatal, because that layer is a sibling
    module on its own cadence."""
    tags, missing = {}, []
    today = dt.date.today()

    def fresh(d):
        try:
            return (today - dt.date.fromisoformat(str(d)[:10])).days <= days
        except Exception:
            return False

    d = _read_json(DATA / "COHORT_DISLOCATION.json")
    if d is None:
        missing.append("cohort_dislocation")
    elif fresh(d.get("asof")):
        for f in (d.get("fires") or []):
            label = f"{f.get('cohort')} ({f.get('verdict_severity', '')} de-rate, median21 " \
                    f"{f.get('median21')}pp)".strip()
            for m in (f.get("members_by_excess21") or []):
                tk = m[0] if isinstance(m, (list, tuple)) else m
                if tk:
                    tags.setdefault(tk, label)
    ce = _read_json(ROOT / "desk/data/class_dislocation_events.json")
    if ce is None:
        missing.append("class_dislocation")
    else:
        for e in (ce.get("events") or []):
            if not fresh(e.get("detected") or e.get("asof") or e.get("date")):
                continue
            for m in (e.get("members_by_dd") or []):
                tk = m[0] if isinstance(m, (list, tuple)) else m
                if tk:
                    tags.setdefault(tk, f"{e.get('cohort', 'class')} (class dislocation)")
    if missing:
        print(f"[quality_wishlist] cohort tags UNAVAILABLE from {', '.join(missing)} — fires this "
              f"run cannot say whether a theme is dragging the name (reported, not hidden)")
    return tags


def _load_state() -> dict:
    return _read_json(STATE, {}) or {}


def _save_state(st: dict):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1, sort_keys=True))
    tmp.replace(STATE)


# ============================================================================ universe (screen mode)

UNI_CACHE = DATA / "quality_wishlist_universe_cache.json"
UNI_CACHE_DAYS = 14


def _broad_universe(retries: int = 3) -> tuple[list[str], str]:
    """The broad-US leg: broken_print_radar's own cap-ladder builder, REUSED not duplicated.

    Cached for two weeks because the ladder costs eight Yahoo screener calls and the desk points
    several sweeps at the same IP quota. The cache is also the honest fallback: when the live
    build comes back empty (that builder swallows its own per-band rate-limit failures and
    returns a short list rather than raising), a two-week-old universe is a far better answer
    than a silently halved one — and the caller is told which it got."""
    for attempt in range(retries):
        try:
            from desk.broken_print_radar import _us_backfill_universe
            extra = _us_backfill_universe(size=250, min_mktcap=1.5e9)
        except Exception as e:
            print(f"[quality_wishlist] broad-US builder raised {type(e).__name__}: {e}")
            extra = []
        if len(extra) >= 200:
            UNI_CACHE.write_text(json.dumps({"asof": dt.date.today().isoformat(),
                                             "broad": extra}, indent=1))
            return extra, "live cap-ladder"
        if attempt < retries - 1:
            wait = 60 * (attempt + 1)
            print(f"[quality_wishlist] broad-US builder returned only {len(extra)} names "
                  f"(rate limit) — waiting {wait}s and retrying")
            time.sleep(wait)
    cached = _read_json(UNI_CACHE, {}) or {}
    try:
        age = (dt.date.today() - dt.date.fromisoformat(cached.get("asof", ""))).days
    except Exception:
        age = 10 ** 6
    if cached.get("broad") and age <= UNI_CACHE_DAYS:
        print(f"[quality_wishlist] broad-US builder unavailable — falling back to the cached "
              f"universe from {cached['asof']} ({age}d old, {len(cached['broad'])} names)")
        return list(cached["broad"]), f"cache {cached['asof']}"
    return [], "unavailable"


def build_universe(broad: bool = True, max_names: int | None = None) -> tuple[list[str], dict]:
    """S&P 500 constituents + the broken_print_radar US universe builder (REUSED, not duplicated).
    FAILS LOUD on an empty universe — a silent shrink is indistinguishable from 'no candidates'."""
    prov = {"sp500": 0, "broad": 0, "broad_error": None}
    sp = _read_json(SP_CONSTITUENTS, {}) or {}
    names = list((sp.get("indices") or {}).get("500") or [])
    prov["sp500"] = len(names)
    prov["sp_asof"] = sp.get("asof")
    seen = set(names)
    if broad:
        extra, prov["broad_source"] = _broad_universe()
        prov["broad_error"] = None if extra else "broad leg produced NOTHING"
        for t in extra:
            if t not in seen:
                seen.add(t)
                names.append(t)
        prov["broad"] = len(extra)
        if not extra:
            # THE SILENT-SHRINK TRAP: broken_print_radar's cap-ladder builder catches its own
            # per-band failures and returns whatever it got, so a rate-limited screener hands back
            # an EMPTY list rather than raising. A universe that quietly halves is indistinguishable
            # from a market with no candidates — so say it, loudly, in the provenance and on stdout.
            print("DEGRADED-LOUD: the broad-US leg returned ZERO names (cap-ladder screener "
                  "rate-limited or empty, and no usable cache) — this screen covers the S&P 500 "
                  "ONLY and is NARROWER than the design specifies. Re-run when the quota clears "
                  "before treating the candidate list as complete.")
    names = [t for t in names if re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,6}", t)]
    if not names:
        raise SystemExit("SCREEN ABORT: empty universe — this is an INFRA failure, not 'no candidates'")
    if max_names:
        prov["truncated_from"] = len(names)
        names = names[:max_names]
    prov["universe"] = len(names)
    return names, prov


# ============================================================================ screen mode

def run_screen(broad: bool = True, max_names: int | None = None, workers: int = 4,
               min_interval: float = 0.15, cull_date: str | None = None) -> dict:
    t0 = time.time()
    today = dt.date.today()
    uni, prov = build_universe(broad=broad, max_names=max_names)
    led = ledger_families()
    uni = [t for t in uni if _norm(t) not in led]
    prov["after_ledger_exclusion"] = len(uni)
    print(f"[quality_wishlist/screen] universe {prov['universe']} "
          f"(S&P500 {prov['sp500']} + broad {prov['broad']}) -> {len(uni)} after ledger exclusion "
          f"({prov['universe'] - len(uni)} already researched)")

    cache = _load_facts_cache()
    # SIC FIRST (§6). Financials are dropped BEFORE the expensive companyfacts download, so the
    # exclusion costs one small submissions payload per name and saves a multi-megabyte one on
    # every bank and insurer. It also keeps them out of the DEGRADED bucket, where they would
    # otherwise pile up: an insurer has no OperatingIncomeLoss tag, so it reads as missing
    # history when the truth is that it is out of scope.
    ss = fetch_sic(uni, cache, workers=workers, min_interval=min_interval)
    fin, unresolved = [], []
    scope = []
    for t in uni:
        rec = cache["names"].get(t) or {}
        if not rec.get("sic_checked"):
            unresolved.append(t)
            continue
        if is_financial(rec.get("sic")):
            fin.append({"ticker": t, "entity": rec.get("entity"), "sic": rec.get("sic"),
                        "sic_desc": rec.get("sic_desc"),
                        "reasons": [f"FINANCIAL (SIC {rec.get('sic')} {rec.get('sic_desc')}) — "
                                    f"excluded from v1 per §6"]})
        else:
            scope.append(t)
    print(f"[quality_wishlist/screen] SIC: {ss['resolved']} resolved, {ss['cached']} cached · "
          f"financials excluded (§6) {len(fin)} · {len(unresolved)} UNRESOLVED (no CIK / fetch "
          f"failure — kept OUT of scope rather than assumed non-financial) · {len(scope)} in scope")
    _save_facts_cache(cache)

    fs = fetch_annuals(scope, cache, workers=workers, min_interval=min_interval)
    _save_facts_cache(cache)
    print(f"[quality_wishlist/screen] XBRL: {fs['fetched']} fetched, {fs['cached']} cached, "
          f"{len(fs['failed'])} FAILED, {len(fs['no_cik'])} no-CIK")

    passed, failed, degraded = [], [], []
    for t in unresolved:
        degraded.append({"ticker": t, "status": "DEGRADED",
                         "reasons": ["SIC-UNRESOLVED (no CIK or submissions fetch failed — sector "
                                     "unknown, so the financials exclusion cannot be applied)"],
                         "stats": {}})
    for t in scope:
        rec = cache["names"].get(t)
        if not rec or not rec.get("annuals"):
            degraded.append({"ticker": t, "status": "DEGRADED",
                             "reasons": ["NO-XBRL (no companyfacts payload — foreign filer, "
                                         "new listing, or fetch failure)"], "stats": {}})
            continue
        g = quality_gate(rec["annuals"])
        row = {"ticker": t, "entity": rec.get("entity"), "cik": rec.get("cik"),
               "sic": rec.get("sic"), "sic_desc": rec.get("sic_desc"),
               "status": g["status"], "reasons": g["reasons"], "flags": g["flags"], "stats": g["stats"]}
        (passed if g["status"] == "PASS" else degraded if g["status"] == "DEGRADED" else failed).append(row)

    kept = passed
    print(f"[quality_wishlist/screen] gate: {len(passed)} PASS · {len(failed)} FAIL · "
          f"{len(degraded)} DEGRADED (never silently passed or failed)")

    # current band percentile for the cull sheet (screen mode NEVER fires — bands are context only)
    px = weekly_prices([r["ticker"] for r in kept]) if kept else {}
    thin = 0
    for r in kept:
        wk = px.get(r["ticker"])
        if not wk:
            r["band"] = {"pct": None, "note": "NO-PRICE-HISTORY"}
            thin += 1
            continue
        ann = cache["names"][r["ticker"]]["annuals"]
        b = assess_bands(ann, wk, suppress_pe=bool(guard_acq_stepup(ann)))
        r["band"] = b
        r["band_label"] = band_of(b["pct"])
        if b["pct"] is None:
            thin += 1
    print(f"[quality_wishlist/screen] band percentiles priced for {len(kept) - thin}/{len(kept)} "
          f"candidates ({thin} DEGRADED thin/no history)")

    kept.sort(key=lambda r: (r.get("band", {}).get("pct") is None, r.get("band", {}).get("pct") or 999))
    payload = {
        "asof": today.isoformat(),
        "_mode": "SCREEN — mechanical candidates ONLY. NOT ACTIVE, NOT FIREABLE.",
        "_activation": (f"Principal culls this list to ~75 names and saves them to "
                        f"{_rel(ACTIVE)} as {{'asof':..,'tickers':[..]}}. Watch mode "
                        f"reads ONLY that file; until it exists the wishlist fires nothing."),
        "_gate": {"roic_min": ROIC_MIN, "roic_min_years": ROIC_MIN_YEARS,
                  "rev_up_min_years": REV_UP_MIN_YEARS, "gm_tolerance_bps": GM_TOLERANCE_BPS,
                  "max_nd_ebitda": MAX_ND_EBITDA, "share_growth_tol": SHARE_GROWTH_TOL,
                  "lookback_years": LOOKBACK_YEARS, "min_usable_years": MIN_USABLE_YEARS,
                  "roic_approximation": "NOPAT/(equity+net debt); see module docstring for the "
                                        "four documented deviations from a textbook ROIC"},
        "sleeve": dict(SLEEVE), "provenance": prov, "xbrl": fs,
        "counts": {"universe": prov["universe"], "after_ledger_exclusion": prov["after_ledger_exclusion"],
                   "pass": len(passed), "fail": len(failed), "degraded": len(degraded),
                   "financials_excluded": len(fin), "candidates": len(kept),
                   "candidates_without_band": thin},
        "candidates": kept, "financials_excluded": fin, "degraded": degraded,
        "failed": failed,
    }
    CANDIDATES.write_text(json.dumps(payload, indent=1))
    sheet = write_cull_sheet(payload, cull_date or today.strftime("%Y%m%d"))
    print(f"[quality_wishlist/screen] wrote {_rel(CANDIDATES)} and {_rel(sheet)} "
          f"in {time.time() - t0:.0f}s")
    print(f"[quality_wishlist/screen] NOT ACTIVE: no band-fire is possible until the principal "
          f"culls to ~75 and saves {_rel(ACTIVE)}")
    return payload


def _gm_cell(st: dict) -> str:
    if st.get("gm_latest") is None:
        return "n/a"
    sl = st.get("gm_slope_bps_per_yr")
    return f"{st['gm_latest'] * 100:.1f}% ({sl:+.0f}bp/yr)" if sl is not None else f"{st['gm_latest'] * 100:.1f}%"


def write_cull_sheet(payload: dict, datestamp: str) -> Path:
    CULL_DIR.mkdir(parents=True, exist_ok=True)
    p = CULL_DIR / f"QUALITY_WISHLIST_CULL_SHEET_{datestamp}.md"
    c = payload["counts"]
    L = []
    L.append(f"# Quality wishlist — mechanical candidate list for the cull ({payload['asof']})\n")
    L.append("**What this is.** The mechanical half of the hybrid seeding the principal approved on "
             "2026-08-13. Every name below cleared a five-part quality gate on ten years of audited "
             "XBRL. Nothing here has been researched, and nothing here can fire an alert yet.\n")
    L.append("**What to do with it.** Cross out the names you would not own at any price and keep "
             "roughly seventy-five. Save the survivors as a list of tickers to "
             f"`{_rel(ACTIVE)}` in the form `{{\"asof\": \"YYYY-MM-DD\", \"tickers\": "
             "[\"AAA\", \"BBB\"]}`. The daily watch reads that file and only that file. Until it "
             "exists the wishlist is inactive by design — an unculled mechanical list firing its own "
             "output is the generator grading itself.\n")
    L.append("**What happens after the cull.** Each surviving name carries valuation bands measured "
             "against its own ten-year history, not against its peers. When a name reaches the middle "
             "of its own range it proposes a first tranche; when it reaches the cheapest fifth of its "
             "own range it proposes a starter; and if its valuation slid twenty-five percentile points "
             "in a year while earnings per share rose, it proposes on that alone — the case of a good "
             "business that got cheap by standing still. No name is courted until it actually gets "
             "cheap, and no proposal ever places an order.\n")
    L.append("---\n")
    L.append("## How the gate read the tape\n")
    L.append(f"- Universe screened: **{c['universe']}** names (S&P 500 constituents plus the broad "
             f"US market-cap ladder); **{c['universe'] - c['after_ledger_exclusion']}** dropped as "
             f"already in the research ledger.")
    L.append(f"- Cleared the gate: **{c['pass']}**. Failed it: **{c['fail']}**.")
    L.append(f"- Set aside as **{c['degraded']} insufficient-history** names — fewer than eight usable "
             f"years of filings. These were neither passed nor failed; they are listed at the bottom.")
    L.append(f"- Banks, insurers and other financials removed before the gate ran: "
             f"**{c['financials_excluded']}** (they have their own trap catalog and their own screen).")
    if (payload.get("provenance") or {}).get("broad_error"):
        L.append(f"- **Coverage warning.** The broad US market-cap leg of the universe returned "
                 f"nothing on this run, so the list below covers the S&P 500 only and is narrower "
                 f"than the design specifies. Treat it as a first pass, not the finished pond.")
    L.append(f"- **{c['candidates']}** candidates remain, of which **{c['candidates_without_band']}** "
             f"could not be given a valuation percentile for lack of price history.\n")
    L.append("The five columns are the gate itself: how many of the last ten years earned more than "
             "fifteen percent on invested capital; how many years revenue rose; the latest gross margin "
             "and its ten-year trend; net debt against EBITDA; and the change in diluted share count "
             "across the decade. Return on invested capital is an approximation from tagged filing "
             "data — operating profit after an effective tax rate, over book equity plus net debt — and "
             "leases are not capitalised, so lease-heavy retailers read high. The last column is where "
             "the name sits in its own ten-year valuation range today: 0 is the cheapest it has ever "
             "been, 100 the dearest.\n")
    L.append("---\n")
    L.append("## Candidates (cheapest against their own history first)\n")
    L.append("| # | Ticker | Company | Sector | ROIC>15% yrs | Rev-up yrs | Gross margin | ND/EBITDA | Diluted shares | Own-history %ile | Band |")
    L.append("|---|--------|---------|--------|--------------|------------|--------------|-----------|----------------|------------------|------|")
    for i, r in enumerate(payload["candidates"], 1):
        st = r.get("stats", {})
        b = r.get("band", {}) or {}
        pct = b.get("pct")
        nd = st.get("nd_ebitda")
        nd_s = "net cash" if (nd == 0 and st.get("net_cash")) else ("n/a" if nd is None else f"{nd:.2f}x")
        sh = st.get("share_chg_pct")
        L.append(f"| {i} | {r['ticker']} | {(r.get('entity') or '')[:38]} | "
                 f"{(r.get('sic_desc') or '')[:28]} | {st.get('roic_yrs', '?')}/{st.get('roic_obs', '?')} | "
                 f"{st.get('rev_up_yrs', '?')}/{st.get('rev_comparisons', '?')} | {_gm_cell(st)} | {nd_s} | "
                 f"{'n/a' if sh is None else f'{sh:+.1f}%'} | "
                 f"{'—' if pct is None else f'{pct:.0f}'} | {r.get('band_label') or '—'} |")
    flagged = [r for r in payload["candidates"] if r.get("flags")]
    if flagged:
        L.append("\n### Caveats carried by individual names\n")
        for r in flagged:
            L.append(f"- **{r['ticker']}** — {'; '.join(r['flags'])}")
    near = [r for r in payload.get("failed", []) if len(r.get("reasons") or []) == 1]
    if near:
        L.append(f"\n---\n\n## Near misses ({len(near)}) — failed on exactly one of the five tests\n")
        L.append("The gate is deliberately strict, and it produced fewer candidates than the design "
                 "sketch assumed. These are the names it turned away on a single count, with the "
                 "count named, so the shortlist can be widened by JUDGEMENT rather than by quietly "
                 "loosening a threshold. Nothing here has a valuation band computed — adding a name "
                 "to the active list gives it one on the next run.\n")
        groups = {"ROIC": "Return on invested capital cleared 15% in too few years",
                  "revenue": "Revenue fell in more years than the durability test allows",
                  "net debt": "Carries more than two turns of net debt",
                  "diluted": "Diluted share count grew across the decade",
                  "gross margin": "Gross margin eroding"}
        for key, title in groups.items():
            rows = [r for r in near if r["reasons"][0].startswith(key)]
            if not rows:
                continue
            L.append(f"\n**{title}** ({len(rows)})\n")
            for r in sorted(rows, key=lambda x: x["ticker"]):
                L.append(f"- **{r['ticker']}** {(r.get('entity') or '')[:40]} — {r['reasons'][0]}")
    deg = payload.get("degraded", [])
    if deg:
        L.append(f"\n---\n\n## Insufficient history ({len(deg)}) — neither passed nor failed\n")
        L.append("Recent listings, spin-offs, foreign private issuers and names whose tagged filings "
                 "do not reach back eight years. They are excluded from the candidate list because the "
                 "gate has no opinion on them, not because they failed it.\n")
        by_reason: dict[str, list[str]] = {}
        for r in deg:
            key = (r.get("reasons") or ["unknown"])[0].split("(")[0].strip()
            by_reason.setdefault(key, []).append(r["ticker"])
        for k, v in sorted(by_reason.items(), key=lambda kv: -len(kv[1])):
            L.append(f"- **{k}** ({len(v)}): {', '.join(sorted(v))}")
    L.append(f"\n---\n\n*Generated by `verticals/generators/quality_wishlist.py --screen`. "
             f"Sleeve cap for anything that eventually comes out of this list: "
             f"{SLEEVE['aggregate_cap_pct']:.0f}% of the book in aggregate.*\n")
    p.write_text("\n".join(L))
    return p


# ============================================================================ watch mode

def load_active() -> list[str] | None:
    """The POST-CULL list. None = the principal has not culled yet = the wishlist is INACTIVE."""
    if not ACTIVE.exists():
        return None
    d = _read_json(ACTIVE)
    if d is None:
        print(f"DEGRADED-LOUD: {_rel(ACTIVE)} exists but is UNPARSEABLE — treating the "
              f"wishlist as INACTIVE rather than guessing at its contents")
        return None
    if isinstance(d, list):
        rows = d
    else:
        rows = d.get("tickers") or d.get("names") or []
    out = []
    for r in rows:
        t = r.get("ticker") if isinstance(r, dict) else r
        if isinstance(t, str) and t.strip():
            out.append(t.strip().upper())
    return out or None


def _fires_store():
    from desk.store import Store
    if not FIRES.exists():
        FIRES.parent.mkdir(parents=True, exist_ok=True)
        FIRES.write_text(json.dumps({
            "_preregistered": "2026-08-13",
            "_module": "verticals/generators/quality_wishlist.py",
            "_purpose": ("Pre-registered grading log for every quality-wishlist band-fire. Written "
                         "BEFORE the first fire so the measurement cannot be chosen after the fact."),
            "_counterfactual": ("Each fire records the name's price and SPY's price on the fire date. "
                                "Forward returns are filled at 90/180/365 calendar days for BOTH, and "
                                "the excess is the name minus SPY over the SAME window — the desk's "
                                "standard beta-placeholder comparison."),
            "_tina_test": ("The FAIR band (tranche-1) versus CHEAP band (starter) split IS the "
                           "empirical TINA test: does entering a still-compounding business at the "
                           "median of its own history beat waiting for its cheap decile? N>=20 GRADED "
                           "FIRES PER BAND before any claim in either direction. Below that it is "
                           "anecdote — the within-rating-band market-timing lesson says exactly this."),
            "_generator_never_grades_itself": ("This file records outcomes only. The wishlist proposes; "
                                               "the court disposes; grading is a separate pass."),
            "_no_survivorship": ("Every fire is logged at fire time, including fires that were "
                                 "downgraded to REVIEW by a trap guard and fires the court later "
                                 "rejected. Nothing is removed from this file, ever."),
            "fires": []}, indent=1))
    return Store(FIRES_REL, list_path="fires", key=lambda r: f"{r['ticker']}|{r['fired']}")


def run_watch(quiet_days: int = QUIET_DAYS, enqueue: bool = True) -> dict:
    today = dt.date.today()
    active = load_active()
    if not active:
        print(f"[quality_wishlist] INACTIVE — {_rel(ACTIVE)} not present.")
        cand = _read_json(CANDIDATES, {}) or {}
        n = (cand.get("counts") or {}).get("candidates")
        print(f"DEGRADED-LOUD: the wishlist is seeded but NOT ACTIVATED. "
              + (f"{n} mechanical candidates are waiting in "
                 f"{_rel(CANDIDATES)} (screened {cand.get('asof')}); the principal must "
                 f"cull them to ~75 and save the survivors to {_rel(ACTIVE)}."
                 if n else f"Run `--screen` first to produce the candidate list, then cull it to "
                           f"{_rel(ACTIVE)}.")
              + " NO BAND-FIRE IS POSSIBLE UNTIL THEN — this silence is a DESIGN STATE, "
                "not a quiet tape.")
        return {"active": False, "fires": [], "watched": 0}

    print(f"[quality_wishlist] ACTIVE: watching {len(active)} post-cull names")
    cache = _load_facts_cache()
    missing_facts = [t for t in active if not (cache["names"].get(t) or {}).get("annuals")]
    if missing_facts:
        print(f"[quality_wishlist] {len(missing_facts)} active names have no cached fundamentals — "
              f"fetching now: {', '.join(missing_facts[:12])}{'...' if len(missing_facts) > 12 else ''}")
        fetch_annuals(missing_facts, cache)
        _save_facts_cache(cache)
    stale = []
    for t in active:
        f = (cache["names"].get(t) or {}).get("fetched")
        try:
            if not f or (today - dt.date.fromisoformat(f)).days > 10:
                stale.append(t)
        except Exception:
            stale.append(t)
    if stale:
        print(f"DEGRADED-LOUD: {len(stale)} names carry fundamentals older than 10d "
              f"(weekly refresh may not be running): {', '.join(sorted(stale)[:15])}")

    px = weekly_prices(active + ["SPY"])
    spy = px.get("SPY")
    if not spy:
        print("WATCH ABORT: no SPY reference series — the counterfactual field would be empty and a "
              "fire logged without it is ungradeable. This is an INFRA failure, not a quiet tape.")
        return {"active": True, "fires": [], "watched": 0, "error": "no SPY"}
    spy_px = spy[-1][1]

    state = _load_state()
    parametric = parametric_holdings()
    disloc = dislocation_hits()
    cohorts = cohort_tags()
    fires, degraded, decayed = [], [], []
    for t in sorted(active):
        rec = cache["names"].get(t) or {}
        ann = rec.get("annuals") or []
        wk = px.get(t)
        if not ann or not wk:
            degraded.append((t, "no fundamentals" if not ann else "no price history"))
            continue
        res = evaluate_name(t, ann, wk, today=today, prior=state.get(t),
                            dislocated=disloc.get(t), parametric=parametric,
                            quiet_days=quiet_days)
        if res.get("value_trap_decay"):
            decayed.append((t, next((g for g in res["guards"]
                                     if g.startswith("VALUE-TRAP-DECAY")), "")))
        if res["status"] == "DEGRADED":
            degraded.append((t, res.get("reason", "")))
            continue
        prior = state.setdefault(t, {})
        if res.get("band") == "CHEAP":
            prior.setdefault("cheap_since", today.isoformat())
        else:
            prior.pop("cheap_since", None)
        prior.update({"band": res.get("band"), "pct": res.get("pct"),
                      "standstill": res.get("standstill"), "last_seen": today.isoformat()})
        if res["status"] != "FIRE":
            continue
        prior["fired"] = today.isoformat()
        last_px = wk[-1][1]
        res.update({"px": round(last_px, 2), "spy_px": round(spy_px, 2), "fired": today.isoformat(),
                    "entity": rec.get("entity"), "cohort_tag": cohorts.get(t),
                    "generator": "quality_wishlist"})
        fires.append(res)
        band_txt = res.get("band") or "—"
        if res.get("standstill"):
            band_txt += "+STANDSTILL"
        wash = " WASH-SALE-CHECK(Parametric)" if res.get("wash_sale_check") else ""
        coh = (f" | COHORT {res['cohort_tag']} — theme may be dragging the name, not a lone "
               f"opportunity") if res.get("cohort_tag") else ""
        guards = (" | " + " | ".join(g.split(":")[0] for g in res["guards"])) if res["guards"] else ""
        print(f"DETFIRE|quality_wishlist|{t}|{res['severity']}|{band_txt} band: own-10yr percentile "
              f"{res['pct']:.0f} (EV/EBIT {res['ev_ebit']} pct {res['pct_ev_ebit']}, P/E {res['pe']} "
              f"pct {res['pct_pe']}) @ {last_px:.2f} -> {res['sizing_label']} sizing, sleeve cap "
              f"{SLEEVE['aggregate_cap_pct']:.0f}% aggregate{wash}{coh}{guards} — {PROPOSES_ONLY}; "
              f"route={res['route']}")
        for g in res["guards"]:
            print(f"  GUARD {t}: {g}")

    for t, g in decayed:
        print(f"VALUE-TRAP-DECAY {t}: {g}")
    if degraded:
        names = ", ".join("{} ({})".format(t, str(r).split(":")[0]) for t, r in degraded[:15])
        more = "..." if len(degraded) > 15 else ""
        print(f"DEGRADED-LOUD: {len(degraded)} of {len(active)} watched names produced NO band this "
              f"run — {names}{more}. Absence of a fire on these names is a DATA GAP, "
              f"not 'not cheap'.")

    _save_state(state)
    if fires:
        st = _fires_store()
        rows = []
        for f in fires:
            rows.append({
                "ticker": f["ticker"], "fired": f["fired"], "entity": f.get("entity"),
                "band": f.get("band"), "standstill": bool(f.get("standstill")),
                "severity": f["severity"], "sizing_label": f["sizing_label"], "route": f["route"],
                "pct": f.get("pct"), "pct_ev_ebit": f.get("pct_ev_ebit"), "pct_pe": f.get("pct_pe"),
                "pct_1y_ago": f.get("pct_1y_ago"), "ev_ebit": f.get("ev_ebit"), "pe": f.get("pe"),
                "pe_suppressed": f.get("pe_suppressed"),
                "px_at_fire": f["px"], "spy_at_fire": f["spy_px"],
                "wash_sale_check": f.get("wash_sale_check"), "guards": f.get("guards"),
                "cohort_tag": f.get("cohort_tag"), "generator": "quality_wishlist",
                "sleeve": f.get("sleeve"),
                "grade_due": {h: (dt.date.fromisoformat(f["fired"]) + dt.timedelta(days=int(h))).isoformat()
                              for h in ("90", "180", "365")},
                "outcomes": {h: None for h in ("90", "180", "365")},
                "court_verdict": None,
            })
        st.upsert(rows, generated_by="quality_wishlist/watch")
        if enqueue:
            court_rows = [f for f in fires if f["route"].startswith("court:")]
            skipped = [f["ticker"] for f in fires if not f["route"].startswith("court:")]
            if court_rows:
                try:
                    from desk.court_queue import enqueue_candidates
                    c = enqueue_candidates(
                        [{"ticker": f["ticker"], "band": f.get("band"), "pct": f.get("pct"),
                          "sizing_label": f["sizing_label"], "px": f["px"],
                          "guards": f.get("guards"), "sleeve": f.get("sleeve"),
                          "note": "quality wishlist band-fire — LAZY COURT: trap-verify the quality "
                                  "claims (10yr ROIC/revenue/margin/leverage/share count) BEFORE any "
                                  "red or blue bench"}
                         for f in court_rows],
                        source=f"quality_wishlist/{today.isoformat()}")
                    print(f"court_queue: {c['added']} new candidates enqueued (lazy court)")
                except Exception as e:
                    print(f"court_queue enqueue failed (fires unaffected): {type(e).__name__}: {e}")
            if skipped:
                print(f"[quality_wishlist] NOT enqueued to court ({len(skipped)}): "
                      f"{', '.join(skipped)} — routed to the dislocation pipeline's cause-check "
                      f"instead (guard 2: a falling knife is not the wishlist's case)")

    print(f"[quality_wishlist] {today}: {len(active)} watched · {len(fires)} fires "
          f"({sum(1 for f in fires if f.get('band') == 'CHEAP')} CHEAP, "
          f"{sum(1 for f in fires if f.get('band') == 'FAIR')} FAIR, "
          f"{sum(1 for f in fires if f.get('standstill'))} STANDSTILL) · {len(degraded)} degraded")
    return {"active": True, "fires": fires, "watched": len(active), "degraded": degraded}


def run_grade() -> dict:
    """Fill the SPY-same-window counterfactual on fires whose horizons have come due."""
    if not FIRES.exists():
        print("[quality_wishlist/grade] no fire log yet — nothing to grade")
        return {"graded": 0}
    st = _fires_store()
    rows = st.rows()
    today = dt.date.today()
    due = [r for r in rows if any(r.get("outcomes", {}).get(h) is None and
                                  r.get("grade_due", {}).get(h, "9999") <= today.isoformat()
                                  for h in ("90", "180", "365"))]
    if not due:
        print(f"[quality_wishlist/grade] {len(rows)} fires logged, none due")
        return {"graded": 0, "logged": len(rows)}
    px = weekly_prices(sorted({r["ticker"] for r in due}) + ["SPY"], years=3)
    spy = px.get("SPY")
    if not spy:
        print("[quality_wishlist/grade] no SPY series — ABORT (a one-sided grade is not a grade)")
        return {"graded": 0, "error": "no SPY"}

    def at(series, d: dt.date):
        prior = [v for dd, v in series if dd <= d]
        return prior[-1] if prior else None

    n = 0
    for r in due:
        for h in ("90", "180", "365"):
            if r["outcomes"].get(h) is not None or r["grade_due"].get(h, "9999") > today.isoformat():
                continue
            d = dt.date.fromisoformat(r["grade_due"][h])
            p, s = at(px.get(r["ticker"], []), d), at(spy, d)
            if p is None or s is None:
                continue
            ret = (p / r["px_at_fire"] - 1) * 100
            sret = (s / r["spy_at_fire"] - 1) * 100
            r["outcomes"][h] = {"px": round(p, 2), "ret_pct": round(ret, 1),
                                "spy_ret_pct": round(sret, 1), "excess_pp": round(ret - sret, 1)}
            n += 1
    st.upsert(due, generated_by="quality_wishlist/grade")
    graded = [r for r in rows if r["outcomes"].get("365")]
    by_band = {}
    for r in graded:
        by_band.setdefault(r.get("band") or "STANDSTILL", []).append(r["outcomes"]["365"]["excess_pp"])
    print(f"[quality_wishlist/grade] filled {n} horizon outcomes · {len(graded)} fires fully graded")
    for b, xs in sorted(by_band.items()):
        gate = "" if len(xs) >= 20 else f" — BELOW THE N>=20 GATE, no TINA claim permitted"
        print(f"  {b}: n={len(xs)} median excess {statistics.median(xs):+.1f}pp vs SPY{gate}")
    return {"graded": n, "logged": len(rows)}


def run_refresh() -> dict:
    """Weekly fundamentals refresh for the active list (or the candidate list before activation)."""
    active = load_active()
    if not active:
        cand = _read_json(CANDIDATES, {}) or {}
        active = [r["ticker"] for r in (cand.get("candidates") or [])]
        if not active:
            print("[quality_wishlist/refresh] nothing to refresh — no active list and no candidates")
            return {"refreshed": 0}
        print(f"[quality_wishlist/refresh] wishlist not yet activated — refreshing the "
              f"{len(active)} mechanical candidates instead")
    cache = _load_facts_cache()
    fs = fetch_annuals(active, cache, max_age_days=6)
    _save_facts_cache(cache)
    print(f"[quality_wishlist/refresh] {fs['fetched']} refreshed, {fs['cached']} still fresh, "
          f"{len(fs['failed'])} FAILED{': ' + ', '.join(fs['failed'][:10]) if fs['failed'] else ''}")
    if fs["failed"]:
        print("DEGRADED-LOUD: the failed names will watch on STALE fundamentals until the next refresh")
    return fs


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--screen", action="store_true", help="mechanical candidate screen + cull sheet")
    ap.add_argument("--refresh-fundamentals", action="store_true", help="weekly XBRL refresh")
    ap.add_argument("--grade", action="store_true", help="fill SPY-same-window counterfactuals")
    ap.add_argument("--no-broad", action="store_true", help="S&P 500 leg only (skip the broad-US builder)")
    ap.add_argument("--max-names", type=int, default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--min-interval", type=float, default=0.15, help="seconds between SEC calls")
    ap.add_argument("--quiet-days", type=int, default=QUIET_DAYS)
    ap.add_argument("--no-enqueue", action="store_true")
    ap.add_argument("--cull-date", default=None,
                    help="YYYYMMDD stamp on the cull sheet filename (default: today)")
    a = ap.parse_args()
    if a.screen:
        run_screen(broad=not a.no_broad, max_names=a.max_names, workers=a.workers,
                   min_interval=a.min_interval, cull_date=a.cull_date)
    elif a.refresh_fundamentals:
        run_refresh()
    elif a.grade:
        run_grade()
    else:
        run_watch(quiet_days=a.quiet_days, enqueue=not a.no_enqueue)
