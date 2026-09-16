"""financials_screen — the FINANCIALS-SPECIFIC value screen (the sibling deep-value scan #6 CANNOT be).

WHY A SEPARATE SCREEN: the ex-financials deep-value finder (universe.py / score.py) is ex-financials
BY DESIGN — EV/EBIT and NCAV are meaningless for banks and insurers (float, loss reserves, and deposits
are the business, not "debt" to net out; there is no EBIT and current assets ~= the whole balance sheet).
Financials price on P/B (or P/TBV) against ROE, gated by the quality of the earnings — combined ratio and
reserve development for insurers, credit/NPA/capital for banks. This module screens on exactly those metrics.

SCORE = P/B-cheapness  x  ROE-consistency (5yr avg + trend, PENALIZE volatility)  x  quality gates.
  - Cheapness: percentile-rank of P/B (or P/TBV) within the bucket, cheaper = better.
  - ROE-consistency: 5yr average ROE, LESS a volatility penalty (std/mean), PLUS a trend bonus.
      A 12%-ROE compounder that never wobbles beats a 20%-avg name that swings 5->35 (the swing is the
      unpriced tail — a reserve release one year, an adverse-development hole the next).
  - Quality gates (court-stage flags, since the killers live in the 10-K not in frames):
      * insurers: combined ratio <=100 SUSTAINED  +  reserve-development history.  ADVERSE prior-year
        development (PYD) = the KILL flag.  A combined ratio HELD under 100 only by RESERVE RELEASES
        (favorable PYD funding the current-year loss) = the RLI pattern — flag it, don't credit it.
      * banks: NPA trend, CET1, deposit mix (non-interest-bearing %), NIM durability.
      * all: the VALUATION IDENTITY check — ROE / (P/B) should ~= 1 / (P/E).  A large break means the
        book value or the earnings is not what it looks like (the ADR lesson: yfinance priceToBook uses
        the wrong basis for ADRs; CIB read 9,484pp off, BCH 20%-vs-6.3%).  Reconcile or REJECT.
      * all: takeaway-vs-data — the headline EPS vs the underwriting / credit reality underneath it.

DATA (screening tier):
  * universe + market cap + industry: Nasdaq screener (universe.fetch_universe, ex_financials=False).
  * equity / net income / assets: SEC XBRL — frames for the whole cross-section (cheap), then per-CIK
    companyfacts for the 5yr ROE history on the shortlist only.  This is PRIMARY and rate-limit-friendly.
  * P/B convenience ratio: yfinance when reachable, as a CROSS-CHECK only — never load-bearing (the
    Yahoo ratio is untrustworthy for ADRs and is frequently throttled to empty).  Our P/B is computed
    from mcap / statement-equity, which we control.
  * COURT STAGE (combined ratios, reserve triangles, CET1, NIM): pulled per-name from the 10-K.  Frames
    do NOT carry combined-ratio components reliably (insurers use custom / fiscal-misaligned tags: only
    ~100-125 filers tag the standard claims concepts) — so the screen SURFACES insurers with the gates
    as OPEN court items, it does not fabricate a combined ratio it cannot source.

USAGE:
  python3 -m verticals.deep_value.financials_screen [--top N] [--bucket insurer|bank|asset_mgr|all]

Writes data/financials_shortlist.json.
"""
from __future__ import annotations
import argparse, json, os, statistics as st, time, urllib.request, urllib.error
from . import universe as U

DATA = os.path.join(os.path.dirname(__file__), "data")
HDRS = {"User-Agent": "signalos-deepvalue research 4tripathy@gmail.com"}

# ── already-adjudicated financials — EXCLUDE from re-courting (per task; these had P&C/EM-bank courts).
# The screen's job is the names those courts did NOT reach (title/specialty niches, small quality banks,
# credit-adjacent services). Anti-stacking: we already hold ~$50k of P&C (EG/HRTG/KNSL/WRB) — new names
# must DIVERSIFY within financials (different lines / geographies / cycle), not quadruple E&S.
ADJUDICATED = {
    "EG", "HRTG", "KNSL", "WRB",              # held / staged E&S + reinsurance
    "FNF", "RLI", "ACGL", "KMPR", "AFG", "MKL", "SIGI", "ORI", "PLMR", "RNR",  # P&C court verdicts
    "BBD", "HSBK", "WF", "KB", "PEO",         # EM / frontier banks
    # additional financials already carried in research_ledger.json (mostly >$10B so mcap-filtered too,
    # but ERIE/GSHD/RYAN brokers can straddle the cap on a drawdown — belt-and-suspenders):
    "ERIE", "GSHD", "RYAN", "CB", "APO", "OWL", "CIB", "ROOT",
}

# ── industry-bucket map (Nasdaq screener `industry` field -> our line/cycle bucket).  Financials do NOT
# diversify by "financials" — a title insurer, a specialty P&C writer, a community bank, and an asset
# manager are four different cycles.  The bucket is what the anti-stacking diversification test keys on.
INDUSTRY_BUCKET = {
    "Property-Casualty Insurers": "insurer_pc",
    "Specialty Insurers": "insurer_specialty",
    "Life Insurance": "insurer_life",
    "Accident &Health Insurance": "insurer_ah",
    "Major Banks": "bank",
    "Commercial Banks": "bank",
    "Banks": "bank",
    "Savings Institutions": "thrift",
    "Investment Managers": "asset_mgr",
    "Investment Bankers/Brokers/Service": "broker",
    "Finance: Consumer Services": "consumer_finance",
    "Finance Companies": "consumer_finance",
    "Finance/Investors Services": "financial_svcs",
    "Diversified Financial Services": "financial_svcs",
    # Real Estate / Trusts / Blank Checks deliberately UNMAPPED -> dropped (REITs price on FFO/NAV, not
    # P/B-vs-ROE; blank checks are trust-arb, handled elsewhere).
}
INSURER_BUCKETS = {"insurer_pc", "insurer_specialty", "insurer_life", "insurer_ah"}
BANK_BUCKETS = {"bank", "thrift"}

# ── CRITICAL FILTER: SEC's company_tickers.json maps PREFERRED / SUBORDINATED-NOTE / DEPOSITARY-SHARE
# tickers to the PARENT's CIK (AFGB/AFGC/AFGD/AFGE -> the AFG common CIK; PRS/PRH/PFH -> Prudential).
# So a naive screen strikes the tiny preferred market cap against the parent's full common equity and
# manufactures a garbage 0.10-0.35 P/B that DOMINATES the cheapness rank.  The first run surfaced 19 of
# 20 top names as preferreds of already-adjudicated or too-big parents (AFG/SIGI/NTRS/WTFC/BPOP/AIZ/RGA).
# The Nasdaq screener `name` field cleanly identifies these — only genuine common passes.
_NONCOMMON_TOKENS = ("subordinated", "depositary", "depositary shares", "preferred", "notes due",
                     "debentures", "cumulative", "junior subordinated", "capital trust", "trust ",
                     "% fix", "%fix", "fixed-to-floating", "fixed to floating", "fix/float",
                     " pfd", "pref ", "senior notes", "baby bond", "% no", "warrant", " unit",
                     "capital securities", "trust preferred")


def is_common_equity(name: str) -> bool:
    """True only for a genuine common-stock line.  Rejects preferreds / baby bonds / depositary shares
    / trust-preferred whose Nasdaq `name` carries a fixed-rate coupon or a preferred/debt marker."""
    n = (name or "").lower()
    if not n:
        return False
    if "common stock" in n or "common shares" in n or "ordinary" in n:
        return True
    if any(tok in n for tok in _NONCOMMON_TOKENS):
        return False
    # a coupon in the name (e.g. "7.125%") with no "common" marker is a preferred/note
    import re
    if re.search(r"\d+\.\d+\s*%|\d+\s*%", n):
        return False
    return True


# ────────────────────────────────────────────────────────────── SEC XBRL fundamentals ──
def _get(url, timeout=60):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout))


def frame(concept, period, unit="USD") -> dict[int, float]:
    url = f"https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/{unit}/{period}.json"
    try:
        d = _get(url, 45)
        time.sleep(0.13)
        return {int(r["cik"]): r["val"] for r in d.get("data", [])}
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        time.sleep(0.13)
        return {}


# equity is an INSTANT (period-end); take the freshest available.  net income is a FY flow.
EQUITY_INSTANTS = ["CY2026Q1I", "CY2025Q4I", "CY2025Q3I", "CY2024Q4I"]
NI_ANNUALS = ["CY2025", "CY2024"]


def _freshest(concept, periods) -> dict[int, float]:
    out = {}
    for p in periods:
        for cik, v in frame(concept, p).items():
            out.setdefault(cik, v)
    return out


def build_cross_section() -> dict[int, dict]:
    """{cik: {equity, ni, ni_common, assets}} for the whole universe from frames (cheap: ~8 calls).

    COMMON-EARNINGS CAVEAT (MBIN court, 2026-07-25): StockholdersEquity + NetIncomeLoss are
    preferred-INCLUSIVE (total equity, NI before preferred dividends).  For a financial with a real
    preferred stack this OVERSTATES the ROE-to-common and understates P/B-to-common — the MBIN screen
    ranked #1 on a 16.7% frames-average ROE while NI-AVAILABLE-TO-COMMON had fallen 39% in the latest
    year (the average masked a deteriorating present).  So we also pull ni_common where the issuer tags
    it; score_name/roe use total NI by default (frames coverage is better) but ni_common is surfaced for
    the court, and the standing lesson is: on any sub-book, high-preferred, or mid-teens-avg-ROE name,
    re-rank on NI-available-to-COMMON and its TREND before trusting the composite.  [[feedback_codify_agent_dd_feedback]]"""
    eq = _freshest("StockholdersEquity", EQUITY_INSTANTS)
    ni = _freshest("NetIncomeLoss", NI_ANNUALS)
    ni_c = _freshest("NetIncomeLossAvailableToCommonStockholdersBasic", NI_ANNUALS)
    assets = _freshest("Assets", EQUITY_INSTANTS)
    ciks = set(eq) | set(ni) | set(assets)
    return {c: {"equity": eq.get(c), "ni": ni.get(c), "ni_common": ni_c.get(c),
                "assets": assets.get(c)} for c in ciks}


def companyfacts_history(cik: int) -> dict:
    """Per-CIK 5yr+ history: year-end equity + annual net income + tangible-book components.
    Used on the SHORTLIST only (one companyfacts call per name)."""
    try:
        cf = _get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    except Exception:
        return {}
    usg = cf.get("facts", {}).get("us-gaap", {})

    def yearend(concept):
        out = {}
        for u in usg.get(concept, {}).get("units", {}).get("USD", []):
            end = u.get("end", "")
            if end.endswith("-12-31") and u.get("form") in ("10-K", "20-F"):
                out[int(end[:4])] = u["val"]                    # last write wins (amended > original)
        return out

    def annual_flow(concept):
        out = {}
        for u in usg.get(concept, {}).get("units", {}).get("USD", []):
            fr = u.get("frame", "")
            if fr.startswith("CY") and "Q" not in fr and u.get("form") in ("10-K", "20-F"):
                out[int(fr[2:6])] = u["val"]
            elif not fr:                                        # fall back to FY-tagged full-year rows
                s, e = u.get("start", ""), u.get("end", "")
                if s.endswith("-01-01") and e.endswith("-12-31") and u.get("fp") == "FY" \
                        and u.get("form") in ("10-K", "20-F"):
                    out.setdefault(int(e[:4]), u["val"])
        return out

    def annual_eps():
        """Latest full-year DILUTED EPS (fall back to basic) — for the reported-P/E identity gate.
        Primary XBRL, NOT yfinance (the ADR-priceToBook lesson: control the basis).  Returns {year: eps}."""
        out = {}
        for concept in ("EarningsPerShareDiluted", "EarningsPerShareBasic"):
            for u in usg.get(concept, {}).get("units", {}).get("USD/shares", []):
                fr = u.get("frame", "")
                if fr.startswith("CY") and "Q" not in fr and u.get("form") in ("10-K", "20-F"):
                    out.setdefault(int(fr[2:6]), u["val"])
            if out:
                break
        return out

    eq = yearend("StockholdersEquity")
    ni = annual_flow("NetIncomeLoss")
    gw = yearend("Goodwill")
    intang = yearend("IntangibleAssetsNetExcludingGoodwill") or yearend("FiniteLivedIntangibleAssetsNet")
    eps = annual_eps()
    latest_gw = gw.get(max(gw)) if gw else 0.0
    latest_intang = intang.get(max(intang)) if intang else 0.0
    latest_eps = eps.get(max(eps)) if eps else None
    return {"equity_hist": eq, "ni_hist": ni, "goodwill": latest_gw, "intangibles": latest_intang,
            "eps_latest_fy": latest_eps}


# ─────────────────────────────────────────────────────────────────────── scorer (pure) ──
def roe_series(equity_hist: dict, ni_hist: dict, years: int = 5) -> list[float]:
    """ROE per year = NI_t / average(equity_t, equity_{t-1}); newest `years` where both are present."""
    out = []
    for y in sorted(ni_hist):
        e0, e1 = equity_hist.get(y), equity_hist.get(y - 1)
        denom = ((e0 + e1) / 2.0) if (e0 and e1) else e0        # avg equity; fall back to year-end
        if denom and denom > 0:
            out.append((y, ni_hist[y] / denom))
    out = out[-years:]
    return [v for _, v in out]


def roe_consistency(roes: list[float]) -> dict:
    """avg ROE, volatility penalty, trend bonus -> a single consistency-adjusted ROE.

    consistency_roe = avg  -  0.5*std  +  0.25*trend
      volatility (std) is charged because the swing IS the unpriced tail (release one year, adverse the
      next); a steady 12% beats a 5->35 average-20%.  trend (slope, newest-minus-oldest / n) rewards a
      book earning its way UP.  Coefficients are deliberate, not fitted (N is tiny) — they encode
      'penalize wobble, reward durable improvement', and are documented so the court can override.
    """
    if not roes:
        return {"avg": None, "std": None, "trend": None, "consistency_roe": None, "n": 0}
    avg = st.mean(roes)
    std = st.pstdev(roes) if len(roes) > 1 else 0.0
    trend = ((roes[-1] - roes[0]) / len(roes)) if len(roes) > 1 else 0.0
    cons = avg - 0.5 * std + 0.25 * trend
    return {"avg": avg, "std": std, "trend": trend, "consistency_roe": cons, "n": len(roes)}


def valuation_identity(pb: float | None, roe_avg: float | None, pe: float | None,
                       tol: float = 0.35) -> dict:
    """ROE / PB should ~= 1 / PE (they are the same thing: earnings-yield on book x book-to-price).
    A large break means book OR earnings is not what it looks like (the ADR priceToBook lesson).
    Returns the implied PE from ROE/PB and the relative gap vs the reported PE; flags if |gap| > tol."""
    if not (pb and pb > 0 and roe_avg and roe_avg != 0):
        return {"implied_pe": None, "gap": None, "flag": False, "reason": "insufficient inputs"}
    implied_pe = pb / roe_avg                                    # PB / ROE = P/E
    if not (pe and pe > 0):
        return {"implied_pe": round(implied_pe, 1), "gap": None, "flag": False,
                "reason": "no reported P/E to reconcile (screen on implied)"}
    gap = (implied_pe - pe) / pe
    flag = abs(gap) > tol
    return {"implied_pe": round(implied_pe, 1), "reported_pe": round(pe, 1), "gap": round(gap, 2),
            "flag": flag,
            "reason": (f"identity BREAK: implied P/E {implied_pe:.1f} vs reported {pe:.1f} "
                       f"({gap:+.0%}) — book or earnings basis suspect (ADR/one-off/AOCI)"
                       if flag else "identity holds")}


def score_name(row: dict) -> dict:
    """Pure scorer for ONE name.  row must carry: bucket, mktcap, equity, ni, assets, equity_hist,
    ni_hist, goodwill, intangibles, and optionally pe (reported trailing) + pb_yf (yfinance cross-check).
    Returns the metrics + gate flags; the composite percentile-rank happens across names in rank()."""
    m = row["mktcap"]
    eq = row.get("equity")
    ni = row.get("ni")
    gw = row.get("goodwill") or 0.0
    intang = row.get("intangibles") or 0.0
    tbv = (eq - gw - intang) if eq is not None else None

    pb = (m / eq) if (eq and eq > 0) else None
    ptbv = (m / tbv) if (tbv and tbv > 0) else None
    ttm_roe = (ni / eq) if (eq and eq > 0 and ni is not None) else None

    roes = roe_series(row.get("equity_hist", {}), row.get("ni_hist", {}))
    cons = roe_consistency(roes)
    ident = valuation_identity(pb, cons["avg"], row.get("pe"))

    ni_common = row.get("ni_common")
    r = {
        "sym": row.get("sym"), "cik": row.get("cik"), "bucket": row.get("bucket"),
        "mktcap": m, "equity": eq, "ni": ni, "ni_common": ni_common, "tbv": tbv,
        "pb": pb, "ptbv": ptbv, "ttm_roe": ttm_roe,
        "roe_5y": roes, "roe_avg": cons["avg"], "roe_std": cons["std"], "roe_trend": cons["trend"],
        "consistency_roe": cons["consistency_roe"], "roe_n": cons["n"],
        "identity_implied_pe": ident["implied_pe"], "identity_gap": ident.get("gap"),
        "identity_flag": ident["flag"], "identity_reason": ident["reason"],
        "pb_yf": row.get("pb_yf"),
    }
    # ── structural gates (reject at screen level) ──
    r["neg_equity"] = eq is not None and eq <= 0
    r["neg_tbv"] = tbv is not None and tbv <= 0            # book is all goodwill — P/TBV meaningless
    r["unprofitable"] = ni is not None and ni < 0
    # P/B artifact guard: a solvent, PROFITABLE financial almost never trades below ~0.4x book — a P/B
    # that low on a profitable name is overwhelmingly a mapping artifact (preferred ticker -> parent CIK,
    # or a holdco stub) rather than a real bargain.  Flag; the court reconciles (real sub-book distress
    # exists but is rare and shows an ROE problem, which the consistency score already catches).
    r["pb_artifact_suspect"] = bool(pb is not None and pb < 0.40 and (ni is None or ni > 0))
    # COMMON-EARNINGS gap (the MBIN tell): if NI-available-to-common is materially below total NI, the
    # frames-average ROE (computed off total NI) OVERSTATES the ROE-to-common — the composite rank is
    # then keyed off an inflated number.  Fire when ni_common is >8% below total NI; the court re-ranks
    # on NI-to-common + its trend.  (Only fires when the issuer tags the common concept.)
    if ni_common is not None and ni is not None and ni > 0:
        r["common_earnings_gap"] = (ni - ni_common) / ni > 0.08
    else:
        r["common_earnings_gap"] = False
    # P/B convenience-ratio disagreement: if our computed P/B and yfinance's differ by >40%, the equity
    # basis is ambiguous (ADR / minority-interest / AOCI) -> flag for the court, don't silently trust ours.
    if pb and row.get("pb_yf") and row["pb_yf"] > 0:
        r["pb_disagree"] = abs(pb - row["pb_yf"]) / row["pb_yf"] > 0.40
    else:
        r["pb_disagree"] = False
    # ── court-stage OPEN items (the killers that live in the 10-K, surfaced not fabricated) ──
    if row["bucket"] in INSURER_BUCKETS:
        r["court_open"] = ["combined_ratio<=100_sustained", "reserve_development_history(PYD=kill)",
                           "release_funded_combined_ratio(RLI_pattern)"]
    elif row["bucket"] in BANK_BUCKETS:
        r["court_open"] = ["NPA_trend", "CET1", "deposit_mix(non-int-bearing%)", "NIM_durability"]
    else:
        r["court_open"] = ["fee_durability", "AUM_flows", "balance_sheet_credit_exposure"]
    return r


def _pctile(vals, reverse=False):
    xs = sorted(v for v in vals if v is not None)
    n = len(xs) or 1

    def f(v):
        if v is None:
            return None
        rk = sum(1 for x in xs if x <= v) / n
        return (1 - rk) if reverse else rk
    return f


def rank(records: list[dict]) -> list[dict]:
    """Composite = mean of {P/B-cheapness pct (reverse), consistency-ROE pct}, WITHIN the shortlist.
    Prefers P/TBV cheapness where TBV is positive (goodwill-adjusted), else P/B.  Names failing a hard
    structural gate get score=None and sort last."""
    have = [r for r in records if r["consistency_roe"] is not None
            and (r["pb"] is not None or r["ptbv"] is not None)]
    val_metric = {id(r): (r["ptbv"] if (r["ptbv"] and r["ptbv"] > 0) else r["pb"]) for r in have}
    p_val = _pctile(list(val_metric.values()), reverse=True)      # cheaper = higher
    p_roe = _pctile([r["consistency_roe"] for r in have])         # steadier/higher = higher
    for r in have:
        hard_fail = r["neg_equity"] or r["neg_tbv"] or r["unprofitable"]
        if hard_fail:
            r["score"] = None
            continue
        parts = [p_val(val_metric[id(r)]), p_roe(r["consistency_roe"])]
        r["score"] = round(st.mean(parts), 3)
    have.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
    return have


# ───────────────────────────────────────────────────────────────── yfinance cross-check ──
def yf_pb(sym: str) -> float | None:
    """yfinance priceToBook as a CROSS-CHECK only (frequently throttled to empty; never load-bearing)."""
    try:
        import yfinance as yf
        info = yf.Ticker(sym).info
        pb = info.get("priceToBook")
        return float(pb) if pb and pb > 0 else None
    except Exception:
        return None


def yf_pe(sym: str) -> float | None:
    try:
        import yfinance as yf
        info = yf.Ticker(sym).info
        pe = info.get("trailingPE")
        return float(pe) if pe and pe > 0 else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────── orchestrator ──
def build_universe(min_mcap=3e8, max_mcap=1e10, bucket="all") -> list[dict]:
    rows = U.fetch_universe(min_mcap=min_mcap, max_mcap=max_mcap, ex_financials=False)
    out = []
    for u in rows:
        if u["sec"] != "Finance":
            continue
        b = INDUSTRY_BUCKET.get(u["ind"])
        if b is None:
            continue
        if u["sym"] in ADJUDICATED:
            continue
        if not is_common_equity(u.get("name", "")):                 # drop preferreds/notes (the parent-CIK trap)
            continue
        if u.get("country") not in ("United States", "", None):     # US-listed domestic only (ADR lesson)
            continue
        if bucket != "all":
            keep = {"insurer": INSURER_BUCKETS, "bank": BANK_BUCKETS,
                    "asset_mgr": {"asset_mgr", "broker", "financial_svcs"}}.get(bucket, set())
            if b not in keep:
                continue
        out.append({**u, "bucket": b})
    return out


def run(top=8, bucket="all", enrich=25, yf_check=False):
    uni = build_universe(bucket=bucket)
    print(f"financials universe ($300M-$10B, US-domestic, ex-adjudicated, mapped): {len(uni)}")
    cs = build_cross_section()
    have_fund = [u for u in uni if u["cik"] in cs and cs[u["cik"]].get("equity")]
    print(f"with SEC equity+NI: {len(have_fund)}")

    # first pass: TTM ROE + P/B from frames (no per-CIK calls yet)
    prelim = []
    for u in have_fund:
        f = cs[u["cik"]]
        prelim.append(score_name({**u, **f, "equity_hist": {}, "ni_hist": {}}))
    # rank on TTM-ROE proxy to pick who to enrich (consistency needs history; use ttm_roe as the proxy)
    prelim = [r for r in prelim if not (r["neg_equity"] or r["unprofitable"])]
    prelim.sort(key=lambda r: (r["pb"] or 9e9) / max(r["ttm_roe"] or 1e-6, 1e-6))   # P/B-per-unit-ROE
    to_enrich = prelim[:enrich]

    # enrich the top `enrich` with 5yr history (one companyfacts call each) + optional yfinance cross-check
    by_sym = {u["sym"]: u for u in have_fund}
    enriched = []
    for r in to_enrich:
        u = by_sym[r["sym"]]
        f = cs[u["cik"]]
        hist = companyfacts_history(u["cik"])
        time.sleep(0.12)
        row = {**u, **f, **hist}
        # reported trailing P/E from PRIMARY XBRL EPS x the screener last price (controls the basis — the
        # identity gate the yfinance path left null when throttled).  px is the Nasdaq lastsale.
        eps = hist.get("eps_latest_fy")
        if u.get("px") and eps and eps > 0:
            row["pe"] = u["px"] / eps
        if yf_check:                                    # yfinance as an optional SECOND cross-check only
            row["pb_yf"] = yf_pb(u["sym"])
            row.setdefault("pe", yf_pe(u["sym"]))
        enriched.append(score_name(row))
    ranked = rank(enriched)

    os.makedirs(DATA, exist_ok=True)
    keep = ("sym", "cik", "bucket", "mktcap", "pb", "ptbv", "ttm_roe", "roe_avg", "roe_std",
            "roe_trend", "consistency_roe", "roe_n", "roe_5y", "identity_implied_pe",
            "identity_gap", "identity_flag", "identity_reason", "neg_tbv", "pb_disagree",
            "ni", "ni_common", "common_earnings_gap", "pb_yf", "score", "court_open")
    json.dump([{k: r.get(k) for k in keep} for r in ranked],
              open(os.path.join(DATA, "financials_shortlist.json"), "w"), indent=1)

    def fmt(r):
        pb = f"{r['pb']:.2f}" if r["pb"] else " -"
        pt = f"{r['ptbv']:.2f}" if r["ptbv"] else " -"
        ra = f"{r['roe_avg']*100:.0f}%" if r["roe_avg"] is not None else " -"
        rs = f"{r['roe_std']*100:.0f}%" if r["roe_std"] is not None else " -"
        sc = f"{r['score']:.2f}" if r["score"] is not None else "GATE"
        idf = "!ID" if r["identity_flag"] else ""
        tbf = "!TBV" if r["neg_tbv"] else ""
        pbf = "!PByf" if r["pb_disagree"] else ""
        cef = "!COMMON" if r.get("common_earnings_gap") else ""   # NI-to-common << total NI (the MBIN tell)
        fl = " ".join(x for x in (idf, tbf, pbf, cef) if x)
        return (f"  {r['sym']:6s}{r['mktcap']/1e6:7.0f}  {r['bucket']:18s}"
                f"P/B{pb:>6s} P/TBV{pt:>6s}  ROE{ra:>5s}±{rs:<5s} n{r['roe_n']:<2d} {sc:>5s}  {fl}")

    print(f"\nFINANCIALS VALUE SHORTLIST  (P/B x ROE-consistency)  bucket={bucket}  n_ranked={len(ranked)}")
    print(f"  {'sym':6s}{'mc$M':>7s}  {'bucket':18s}{'P/B':>9s} {'P/TBV':>10s}  {'ROE avg±std':>14s}  {'yrs':>3s} {'score':>5s}")
    for r in ranked[:top]:
        print(fmt(r))
    print("\n  court-open items are the 10-K pulls (combined ratio / PYD / CET1 / NIM) — the screen surfaces,")
    print("  it does NOT fabricate a combined ratio frames cannot source.")
    return ranked


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--bucket", default="all", choices=["all", "insurer", "bank", "asset_mgr"])
    ap.add_argument("--enrich", type=int, default=25)
    ap.add_argument("--yf-check", action="store_true", help="add yfinance P/B & P/E cross-check (throttled)")
    a = ap.parse_args()
    run(a.top, a.bucket, a.enrich, a.yf_check)
