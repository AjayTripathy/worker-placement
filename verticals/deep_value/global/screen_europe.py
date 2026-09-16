"""screen_europe — Europe (ESEF) leg of the global value screen: esef_store -> same
composite + guards as the US screen (score.py imported and reused, not reimplemented),
plus the Europe-specific columns.

  python3 screen_europe.py [--top N] [--min-mcap-usd 4e7] [--refresh-px]

Universe = the crawled esef_store (GB/PL/SE/FI/DK/NO, latest annual vintage) resolved to
Yahoo tickers by NAME (filings.xbrl.org gives LEI + name, no ticker/ISIN) — the muni
fuzzy-matcher lesson applies: exchange must match the filing country and the name-match
must clear a similarity bar, else the row is UNRESOLVED and logged, never a silent pick.

Fundamentals stay NATIVE per filing currency; the market cap is bridged INTO the filing
currency (static screening FX) so every ratio is single-plane; USD appears only as the
display column + the $40M floor (name the metric — the TEY lesson).

THE GBX/GBP PLANE (the POLI.TA lesson — unit conventions never transfer across venues):
LSE equity quotes are in PENCE (Yahoo currency "GBp"), and Yahoo's own market_cap /
price for .L lines are pence-denominated too (verified 2026-07-21 on KNOS.L: fast_info
market_cap 95.3e9 "GBp" = ~£953M actual). EVERY .L price/mcap is divided by 100 exactly
once, keyed off the reported currency string, and a P/B-plane sanity check runs on the
GB cohort before anything prints (a 100x plane error makes median P/B ~100x off).

Europe columns (never silent exclusion, except funds/financials — see below):
  WHT     — dividend withholding: GB 0% (the sweet spot) / PL 19% / SE 30% / FI 35% /
            DK 27% / NO 25% (Nordics treaty-reclaimable to 15% but reclaim friction is real).
  stamp   — GB charges 0.5% stamp duty (SDRT) on BUYS of main-market UK shares.
  IBKR    — exchange code for order routing (LSE/WSE/SFB/HEX/CPH/OSE).
  orphan  — GB & mcap < $500M: the post-MiFID-II research-desert shelf (the prize).
  PL-state— Warsaw state-controlled names (Treasury de facto control) get a controller note.
  ebit~   — EBIT derived (PBT + net finance costs), not the filer's operating-profit tag.
  PFIC    — book-basis proxy (pfic_screen) AND the FMV-basis test from day one:
            (cash+investments)/(mcap+liabilities) >= 50% flags.

EXCLUDED entirely (like financials in the US screen): investment trusts / closed-end
funds / VCTs / REITs / banks / insurers / asset managers. The UK list is thick with
investment trusts and every one of them is a statutory PFIC — counting them as "cheap"
is noise. Counts are reported, and balance-shape catches the ones name/sector miss.
"""
from __future__ import annotations
import argparse, difflib, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))                 # verticals/deep_value for score.py
import score as S                                          # noqa: E402  (the US composite, reused)
import pfic_screen as P                                    # noqa: E402
import esef_fundamentals as EF                             # noqa: E402

DATA = os.path.join(HERE, "data")
TKR_MAP = os.path.join(EF.CACHE, "ticker_map.json")
PX_CACHE = os.path.join(DATA, "europe_px_cache.json")
SHORTLIST = os.path.join(DATA, "europe_shortlist.json")
PX_STALE_DAYS = 7
HDRS = {"User-Agent": "Mozilla/5.0 (signalos-deepvalue research)"}

# static screening FX -> USD (display + $ floors + quote-ccy -> filing-ccy bridge)
FX = {"USD": 1.0, "GBP": 1.27, "EUR": 1.08, "PLN": 0.25, "SEK": 0.095, "DKK": 0.145,
      "NOK": 0.093, "CHF": 1.12, "ISK": 0.0072}
SUFFIX = {"GB": ".L", "PL": ".WA", "SE": ".ST", "FI": ".HE", "DK": ".CO", "NO": ".OL"}
YX_EXCH = {"GB": {"LSE"}, "PL": {"WSE"}, "SE": {"STO"}, "FI": {"HEL"},
           "DK": {"CPH"}, "NO": {"OSL"}}
# Yahoo search ranks by requester region — a US-region query BURIES the home line for
# many names (Experian: FRA/OTC only until region=GB). Hint the filing country's region.
YX_REGION = {"GB": ("GB", "en-GB"), "PL": ("PL", "pl"), "SE": ("SE", "sv"),
             "FI": ("FI", "fi"), "DK": ("DK", "da"), "NO": ("NO", "nb")}
IBKR_EXCH = {"GB": "LSE", "PL": "WSE", "SE": "SFB", "FI": "HEX", "DK": "CPH", "NO": "OSE"}
WHT = {"GB": "0%", "PL": "19%", "SE": "30%r", "FI": "35%r", "DK": "27%r", "NO": "25%r"}
#  "r" = treaty-reclaimable (usually to 15%) but the reclaim is paperwork + months of float

FUNDISH_NAME = re.compile(
    r"(INVESTMENT TRUST|INVESTMENT COMPANY|INVESTMENTTRUST|TRUST PLC|TRUST P\.?L\.?C"
    r"|\bVCT\b|\bREIT\b|SICAV|\bFUND\b|\bFONDEN\b|PRIVATE EQUITY|CAPITAL & INCOME"
    r"|INCOME & GROWTH|RENEWABLES INFRASTRUCTURE|INFRASTRUCTURE INCOME)", re.I)
FIN_SECTORS = {"Financial Services", "Financial", "Real Estate"}
FIN_INDUSTRY = re.compile(r"(Bank|Insurance|Asset Management|Capital Markets|REIT"
                          r"|Credit Services|Mortgage|Closed-End Fund|Exchange Traded Fund"
                          r"|Real Estate)", re.I)
LEGAL_SUFFIX = re.compile(
    r"\b(PLC|P\.L\.C\.?|PUBLIC LIMITED COMPANY|LIMITED|LTD|AB \(PUBL\)|\(PUBL\)|AB|ASA"
    r"|A/S|A\.?S\.?A\.?|OYJ|ABP|OY|S\.?A\.?|SPOLKA AKCYJNA|SP Z O O|HOLDING(S)?|GROUP"
    r"|GRUPPEN|KONCERNEN|COMPANY|CO|AKTIEBOLAG(ET)?|AKTIESELSKAB(ET)?|AKSJESELSKAP(ET)?"
    r"|ALLMENNAKSJESELSKAP(ET)?)\b\.?", re.I)
# Warsaw state-controlled (Treasury de facto control; ex-financials) — controller column
PL_STATE = ("ORLEN", "PGE ", "POLSKA GRUPA ENERGETYCZNA", "TAURON", "ENEA", "KGHM",
            "JASTRZEBSKA", "GRUPA AZOTY", "AZOTY", "PKP CARGO", "ENERGA", "BOGDANKA",
            "POLSKI HOLDING NIERUCHOMOSCI", "GAZ-SYSTEM")

# TRUST/CLIENT-CASH GUARD (the OTB.L Stage-2 catch, 2026-07-21): business models that
# hold large CUSTOMER floats (ATOL/trust-ring-fenced travel money, betting balances,
# client accounts, merchant float) report that cash on the face of the balance sheet,
# and ESEF primary statements never split it out — the split lives in untagged notes.
# Netting it into netcash manufactured a phantom EV on On The Beach (~GBP72m printed vs
# ~GBP282m honest; 6.9x EV/EBIT vs true ~9-14x). Full decomposition isn't screenable, so
# the guard is conservative: FLAG the model, and for flagged names feed the composite the
# TRUST-SAFE variant (EV with NO cash netting; netcash floored at 0). Both variants are
# emitted (`am` = trust-safe for flagged names, `am_asis` keeps the raw one).
TRUST_CASH_INDUSTRY = re.compile(
    r"(Travel|Tour|Lodging|Airlines|Gambling|Casino|Betting|Insurance Broker"
    r"|Ticket|Payment|Specialty Retail.*Travel|Real Estate Services)", re.I)
TRUST_CASH_NAME = re.compile(
    r"(TRAVEL|TOUR OPERATOR|\bTOURS?\b|HOLIDAYS?\b|CRUISE|\bBEACH\b|TICKET|\bBET\b"
    r"|BETTING|GAMING|CASINO|LOTTER|BOOKMAK|INSURANCE BROK|ESTATE AGEN|LETTINGS?\b"
    r"|PAYMENTS?\b|PAYTECH)", re.I)


def _norm(name: str) -> str:
    s = re.sub(r"[^A-Z0-9 ]", " ", (name or "").upper())
    s = LEGAL_SUFFIX.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # spaced-out legal suffixes survive the regex ("P L C", "A S") — drop the TRAILING
    # run of single-letter tokens (leading ones like "W H SMITH" are real and kept);
    # ditto a trailing/leading "THE" (registry names come as "...COMPANY(THE)")
    toks = s.split()
    while toks and len(toks[-1]) == 1:
        toks.pop()
    if toks and toks[-1] == "THE":
        toks.pop()
    if toks and toks[0] == "THE":
        toks.pop(0)
    return " ".join(toks)


def _yahoo_search(q: str, region=None):
    p = {"q": q, "quotesCount": 10, "newsCount": 0}
    if region:
        p["region"], p["lang"] = region
    url = "https://query2.finance.yahoo.com/v1/finance/search?" + urllib.parse.urlencode(p)
    req = urllib.request.Request(url, headers=HDRS)
    return json.loads(urllib.request.urlopen(req, timeout=30).read()).get("quotes", [])


def resolve_tickers(rows: list, refresh=False, resolve_new=True, fast=False) -> dict:
    """lei -> {sym, sector, industry, match, quality} via Yahoo search on the entity NAME.
    Query LADDER (the SPCX lesson — absence needs a second query form): normalized name
    then raw name, home-region-hinted then default. Accept only: expected home exchange
    for the filing country AND similarity >= 0.72 (>=0.90 = 'exact', else 'fuzzy').
    Anything else = UNRESOLVED (logged), never a silent pick (muni-matcher lesson)."""
    cache = json.load(open(TKR_MAP)) if os.path.exists(TKR_MAP) else {}
    todo = [r for r in rows if refresh or r["lei"] not in cache]
    if not resolve_new:
        if todo:
            print(f"resolve_new=False: {len(todo)} names left UNRESOLVED-pending "
                  f"(cached: {len(rows)-len(todo)}) — resume with resolve_new=True")
        return cache
    if todo:
        print(f"resolving {len(todo)} names via Yahoo search (cached: {len(rows)-len(todo)})")
    for i, r in enumerate(todo):
        ent = {"sym": None, "sector": None, "industry": None, "match": None, "quality": "UNRESOLVED"}
        want_ex = YX_EXCH.get(r["country"], set())
        region = YX_REGION.get(r["country"])
        nrm = _norm(r["name"])
        queries = []
        for q in (nrm, r["name"]):
            for reg in (region, None):
                if q and (q, reg) not in queries:
                    queries.append((q, reg))
        if fast:
            queries = queries[:2]          # bounded pass: normalized name, hinted + default
        best = (0.0, None)
        for q, reg in queries:
            try:
                quotes = _yahoo_search(q, reg)
            except Exception:
                quotes = []
            time.sleep(0.25)
            for qt in quotes:
                if qt.get("quoteType") != "EQUITY" or qt.get("exchange") not in want_ex:
                    continue
                cand = qt.get("longname") or qt.get("shortname") or ""
                ratio = difflib.SequenceMatcher(None, nrm, _norm(cand)).ratio()
                if ratio > best[0]:
                    best = (ratio, qt)
            if best[0] >= 0.90:
                break                                     # good enough — stop the ladder
        if best[1] is not None and best[0] >= 0.72:
            q = best[1]
            ent = {"sym": q["symbol"], "sector": q.get("sector"), "industry": q.get("industry"),
                   "match": q.get("longname") or q.get("shortname"),
                   "quality": "exact" if best[0] >= 0.90 else f"fuzzy({best[0]:.2f})"}
        cache[r["lei"]] = ent
        if (i + 1) % 50 == 0:
            print(f"  ...{i+1}/{len(todo)}")
            json.dump(cache, open(TKR_MAP, "w"))
    json.dump(cache, open(TKR_MAP, "w"))
    return cache


def fetch_px(syms: list, refresh=False) -> dict:
    """sym -> {px, ccy, shares, mcap_q, ts} via yfinance fast_info (1 name = 1 call,
    cached hard with a staleness stamp — a stale price is FLAGGED downstream, not hidden).
    px/mcap stay in the QUOTE currency ('GBp' = pence!) — the plane fix happens at use."""
    cache = json.load(open(PX_CACHE)) if os.path.exists(PX_CACHE) else {}
    now = time.time()
    todo = [s for s in syms if refresh or s not in cache or not cache[s].get("px")
            or (now - cache[s].get("ts", 0)) > PX_STALE_DAYS * 86400]
    if todo:
        import yfinance as yf
        print(f"fetching {len(todo)} quotes via yfinance fast_info (cached: {len(syms)-len(todo)})")
        for i, s in enumerate(todo):
            row = {"px": None, "ccy": None, "shares": None, "mcap_q": None, "ts": now}
            try:
                fi = yf.Ticker(s).fast_info
                row.update({"px": fi["last_price"], "ccy": fi["currency"],
                            "shares": fi["shares"], "mcap_q": fi["market_cap"]})
            except Exception:
                pass
            cache[s] = row
            time.sleep(0.3)
            if (i + 1) % 40 == 0:
                print(f"  ...{i+1}/{len(todo)}")
                json.dump(cache, open(PX_CACHE, "w"))
    json.dump(cache, open(PX_CACHE, "w"))
    return cache


def _to_filing_ccy(amount_quote, quote_ccy, filing_ccy):
    """Bridge a quote-currency amount into the filing currency (static screening FX).
    GBp -> GBP is the /100 pence plane (POLI.TA lesson) — done HERE, exactly once."""
    if amount_quote is None or not quote_ccy or not filing_ccy:
        return None
    if quote_ccy in ("GBp", "GBX"):
        amount_quote, quote_ccy = amount_quote / 100.0, "GBP"
    fq, ff = FX.get(quote_ccy), FX.get(filing_ccy)
    if not fq or not ff:
        return None
    return amount_quote * fq / ff


_DEBT_TAGS = ("_DebtCurrentBorrowings", "_DebtNoncurrentBorrowings", "_DebtLeaseCurrent",
              "_DebtLeaseNoncurrent", "_DebtCombined", "_DebtLeaseCombined")


def apply_europe_guards(m: dict, r: dict) -> dict:
    """The batch-2 screen-defect fixes (screen_defects.jsonl, 2026-08-06) — each guard is a
    golden-fixture test in tests/test_screen_europe_guards.py; the caught names are the fixtures.

    1. DEBT-BLIND (KSL class): no debt-side tag extracted at all, yet the balance sheet shows
       material noncurrent liabilities -> "no debt evidence" is NOT "no debt". ncash_r and the
       EV multiple both become None (missing debt must never default to zero; KSL printed 7.9x
       on a true 14.3x). A genuinely unlevered filer (small noncurrent liabilities) keeps its
       numbers — zero borrowings tags because zero borrowings exist.
    2. FCF LEASE-BLIND (Tokmanni/VERK/CARD class): lease liabilities on the BS mean lease
       principal sits in financing, outside CFO-capex. Where the filing tags the payment
       (_LeasePayments), subtract it and keep a corrected FCFy; where it doesn't, the yield is
       UNKNOWABLE from tags -> fcfy=None + fcf_lease_blind flag, never the inflated number.
    3. ONE-OFF SUSPECT (VERK/THS class): |dEBIT| > 50% on |dRev| < 10% smells like a gain/
       reversal in operating profit -> flag for the trap-verification step (statutory vs
       comparable EBIT stays a manual judgment)."""
    g = r.get
    # ---- 1: debt evidence ----
    has_debt_tag = any(g(k) is not None for k in _DEBT_TAGS)
    m["debt_blind"] = False
    if not has_debt_tag:
        liab, liab_c = g("Liabilities"), g("LiabilitiesCurrent")
        cash = g("CashAndCashEquivalentsAtCarryingValue") or 0
        assets = g("Assets") or 0
        noncur = (liab - liab_c) if (liab is not None and liab_c is not None) else None
        if noncur is None or noncur > max(cash, 0.10 * assets):
            m["debt_blind"] = True
            m["ncash_r_asis"] = m.get("ncash_r_asis", m.get("ncash_r"))
            m["am_asis"] = m.get("am_asis", m.get("am"))
            m["ncash_r"] = None                    # never default missing debt to zero
            m["am"] = None                         # EV without a debt side is not a multiple
    # ---- 2: lease-aware FCF ----
    has_lease = any(g(k) for k in ("_DebtLeaseCurrent", "_DebtLeaseNoncurrent", "_DebtLeaseCombined"))
    m["fcf_lease_blind"] = False
    if has_lease and m.get("fcf") is not None:
        pay = g("_LeasePayments")
        if pay is not None:
            m["fcf"] = m["fcf"] - abs(pay)
            m["fcfy"] = (m["fcf"] / m["mktcap"]) if m.get("mktcap") else m.get("fcfy")
        else:
            m["fcf_lease_blind"] = True
            m["fcfy"] = None                       # the inflated yield never prints
    # ---- 3: one-off contamination ----
    m["one_off_suspect"] = False
    ebit, ebit_p = g("OperatingIncomeLoss"), g("OperatingIncomeLoss_prior")
    rev, rev_p = g("Revenues"), g("Revenues_prior")
    if all(x not in (None, 0) for x in (ebit, ebit_p, rev, rev_p)):
        if abs(ebit / ebit_p - 1) > 0.50 and abs(rev / rev_p - 1) < 0.10:
            m["one_off_suspect"] = True
    return m


def run(top=30, min_mcap_usd=4e7, max_mcap_usd=None, refresh_px=False, resolve_new=True):
    store = EF.load_store()
    rows = [r for r in store.values()
            if r.get("country") in SUFFIX and r.get("name") and r.get("currency")]
    print(f"esef_store: {len(store)} issuers | in screen countries: {len(rows)}")

    # -- exclusion pass 1: fund/trust by NAME (before burning Yahoo lookups on them)
    n0 = len(rows)
    rows = [r for r in rows if not FUNDISH_NAME.search(r["name"] or "")]
    excl_name = n0 - len(rows)

    # need something to score: an income/CF anchor + a balance sheet
    rows = [r for r in rows if r.get("Assets")
            and (r.get("OperatingIncomeLoss") is not None
                 or r.get("NetCashProvidedByUsedInOperatingActivities") is not None)]
    print(f"name-level fund/trust excluded: {excl_name} | screenable rows: {len(rows)}")

    tmap = resolve_tickers(rows, resolve_new=resolve_new)
    resolved = [r for r in rows if tmap.get(r["lei"], {}).get("sym")]
    unresolved = len(rows) - len(resolved)

    # -- exclusion pass 2: sector/industry (financials, REITs, asset managers, funds)
    excl_fin = 0
    kept = []
    for r in resolved:
        t = tmap[r["lei"]]
        if (t.get("sector") in FIN_SECTORS) or FIN_INDUSTRY.search(t.get("industry") or ""):
            excl_fin += 1
            continue
        kept.append(r)
    # -- exclusion pass 3: balance-shape investment vehicles Yahoo didn't classify
    #    (investments+cash dominate assets AND revenue is trivial vs assets)
    excl_shape = 0
    ops = []
    for r in kept:
        inv = sum((r.get(k) or 0) for k in ("CashAndCashEquivalentsAtCarryingValue",
                                            "ShortTermInvestments", "LongTermInvestments"))
        rev = r.get("Revenues") or 0
        if r["Assets"] and inv / r["Assets"] > 0.85 and rev < 0.05 * r["Assets"]:
            excl_shape += 1
            continue
        ops.append(r)
    print(f"unresolved tickers: {unresolved} | sector-excluded (fin/RE/funds): {excl_fin} "
          f"| balance-shape fund-like excluded: {excl_shape} | operating cos: {len(ops)}")

    px = fetch_px([tmap[r["lei"]]["sym"] for r in ops], refresh=refresh_px)
    now = time.time()
    recs, dropped_px, dropped_floor = [], 0, 0
    for r in ops:
        t = tmap[r["lei"]]
        p = px.get(t["sym"]) or {}
        fccy = r["currency"]
        # mcap in the FILING currency: prefer px x shares-from-the-FILING; else px x
        # Yahoo shares; else Yahoo market_cap (all bridged through _to_filing_ccy, which
        # owns the GBp/100 plane — POLI.TA: unit conventions never transfer across venues)
        px_f = _to_filing_ccy(p.get("px"), p.get("ccy"), fccy)
        if px_f and r.get("_SharesIssued"):
            mcap, basis = px_f * r["_SharesIssued"], "px*shares(filing)"
        elif px_f and p.get("shares"):
            mcap, basis = px_f * p["shares"], "px*shares(yahoo)"
        else:
            mcap, basis = _to_filing_ccy(p.get("mcap_q"), p.get("ccy"), fccy), "yahoo mcap"
        if not mcap or mcap <= 0:
            dropped_px += 1
            continue
        mcap_usd = mcap * FX[fccy]
        if mcap_usd < min_mcap_usd or (max_mcap_usd and mcap_usd > max_mcap_usd):
            dropped_floor += 1
            continue
        cc = r["country"]
        urow = {"sym": t["sym"], "mktcap": mcap, "px": p.get("px"),
                "sec": (t.get("sector") or "?"), "ind": (r["name"] or "")[:40], "country": cc}
        m = S.compute_metrics(urow, r)                     # the US composite's metric builder
        apply_europe_guards(m, r)                          # the batch-2 defect fixes (see fn)
        m["foreign"], m["adr"] = True, False
        # ---- trust/client-cash guard (see TRUST_CASH_* above; the OTB.L catch) ----
        m["trust_cash_suspect"] = bool(
            TRUST_CASH_INDUSTRY.search(t.get("industry") or "")
            or TRUST_CASH_NAME.search(r["name"] or ""))
        m["am_asis"], m["ncash_r_asis"], m["am_trustsafe"] = m["am"], m["ncash_r"], None
        if m["trust_cash_suspect"]:
            ev_ts = mcap + m["debt"] + m["mi"]             # cash NOT netted — float may be customers'
            m["ev_trustsafe"] = ev_ts
            m["am_trustsafe"] = (ev_ts / m["ebit"]) if (m["ebit"] and m["ebit"] > 0 and ev_ts > 0) else None
            # the composite + sort see the CONSERVATIVE variant for flagged names
            m["am"] = m["am_trustsafe"]
            m["ncash_r"] = min(0.0, m["ncash_r"]) if m["ncash_r"] is not None else None
            m["subcash"] = False                           # phantom sub-cash is exactly the bug
        m["ccy"] = fccy
        m["mcap_usd"] = mcap_usd
        m["mcap_basis"] = basis
        m["px_ccy"] = p.get("ccy")
        m["px_stale"] = (now - p.get("ts", 0)) > PX_STALE_DAYS * 86400
        m["ebit_derived"] = bool(r.get("_ebit_derived"))
        m["consol"] = r.get("_consol", True)               # False = separate-only accounts
        m["wht"] = WHT[cc]
        m["stamp"] = "0.5% buy" if cc == "GB" else "-"
        m["ibkr"] = IBKR_EXCH[cc]
        m["orphan_gb"] = cc == "GB" and mcap_usd < 5e8      # post-MiFID research desert = the prize
        m["pl_state"] = cc == "PL" and any(k in (r["name"] or "").upper() for k in PL_STATE)
        m["match_quality"] = t.get("quality")
        m["fxo_id"], m["filing_url"] = r.get("fxo_id"), r.get("filing_url")
        m["period_end"] = r.get("period_end")
        # fiscal staleness: SE/NO feeds stop at FY2024, PL at FY2023 (filings.xbrl.org
        # lag, measured 2026-07-21) — carry the age visibly instead of hiding it
        try:
            m["fy_months"] = round((now - time.mktime(time.strptime(
                r["period_end"], "%Y-%m-%d"))) / (30.44 * 86400))
        except (TypeError, ValueError):
            m["fy_months"] = None
        m["fy_stale"] = bool(m["fy_months"] and m["fy_months"] > 15)
        pf = P.pfic_risk(m, r)
        m["pfic"], m["pfic_why"] = pf["pfic"], pf["reason"]
        # FMV-basis PFIC from day one: for PUBLIC names the §1297 asset test runs on FMV —
        # denominator ~ mcap + liabilities, not book assets (cheapness and PFIC are the
        # same phenomenon on the below-book shelf; the Japan Daishin/Eidai catch)
        _cash = (r.get("CashAndCashEquivalentsAtCarryingValue") or 0) + (r.get("ShortTermInvestments") or 0)
        _inv = (r.get("LongTermInvestments") or 0)
        _fmv = mcap + (r.get("Liabilities") or 0)
        if _fmv > 0:
            share = (_cash + _inv) / _fmv
            m["pfic_fmv_share"] = round(share, 3)
            if share >= 0.5 and not m["pfic"]:
                m["pfic"] = True
                m["pfic_why"] = f"FMV-basis passive {share*100:.0f}% >= 50% (book passed: {m['pfic_why']})"
        recs.append(m)
    print(f"priced: {len(recs)} (no price: {dropped_px}, under ${min_mcap_usd/1e6:.0f}M floor: {dropped_floor})")

    # GBX plane sanity: a 100x error makes the GB median P/B absurd (POLI.TA-class check)
    gb_pb = sorted(r["pb"] for r in recs if r["country"] == "GB" and r.get("pb"))
    if gb_pb:
        med = gb_pb[len(gb_pb) // 2]
        print(f"GB median P/B = {med:.2f} (plane check: expect ~0.5-5; 100x off = pence bug)")
        if not 0.05 < med < 50:
            raise SystemExit("GBX/GBP PLANE FAILURE — refusing to emit a 100x-off shortlist")

    scored = S.composite(recs)
    shortlist = S.clean_shortlist(scored, exclude_adr=False)

    # OUTPUT-SIDE SCALE VALIDATOR (the Hostelworld catch, 2026-07-21): some ESEF filers
    # mis-scale EVERY monetary fact 10x (HSW tagged FY24 revenue EUR920M vs actual EUR92M
    # — wrong scale attribute in the iXBRL). Fundamentals-only ratios survive, but
    # anything mixing filing values with market cap (FCFy, EV/EBIT, P/B) goes 10x off.
    # Cross-check the TOP of the table against a secondary revenue source; >=3x apart ->
    # scale_suspect: kept in the JSON (flagged), demoted from the printed table.
    try:
        import yfinance as yf
        for r in shortlist[:60]:
            r["scale_suspect"] = False
            if r.get("rev") is None:
                continue
            try:
                info = yf.Ticker(r["sym"]).info
                yrev, yccy = info.get("totalRevenue"), info.get("financialCurrency")
                time.sleep(0.4)
            except Exception:
                continue
            if not yrev or not yccy or yccy not in FX or r["ccy"] not in FX:
                continue
            ratio = (r["rev"] * FX[r["ccy"]]) / (yrev * FX[yccy])
            if ratio >= 3 or ratio <= 1 / 3:
                r["scale_suspect"] = True
                r["scale_note"] = f"filing rev {ratio:.1f}x secondary source — filer scale bug?"
    except ImportError:
        pass
    printable = [r for r in shortlist if not r.get("scale_suspect")]
    susp = [r["sym"] for r in shortlist[:60] if r.get("scale_suspect")]
    if susp:
        print(f"scale-suspect (demoted from print, kept flagged in JSON): {susp}")

    os.makedirs(DATA, exist_ok=True)
    keep = ("sym", "ind", "sec", "country", "ccy", "mktcap", "mcap_usd", "mcap_basis", "px",
            "px_ccy", "score", "am", "am_asis", "am_trustsafe", "trust_cash_suspect",
            "ev_trustsafe", "fcfy", "pb", "ncash_r", "ncash_r_asis", "ncav_r", "ebit", "fcf",
            "subcash", "holdco", "neg_equity", "wc_fcf", "ebit_derived", "consol",
            "debt_blind", "fcf_lease_blind", "one_off_suspect",
            "pfic", "pfic_why",
            "pfic_fmv_share", "wht", "stamp", "ibkr", "orphan_gb", "pl_state",
            "match_quality", "px_stale", "fy_months", "fy_stale", "scale_suspect",
            "scale_note", "fxo_id", "filing_url", "period_end", "nmetrics")
    from collections import Counter as _C
    meta = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "coverage_note": ("filings.xbrl.org feed lag: GB/DK/FI current; SE/NO stop at "
                              "FY2024, PL at FY2023 (fy_stale flags carry it); IE absent"),
            "scored_by_country": dict(_C(r["country"] for r in recs)),
            "shortlist_by_country": dict(_C(r["country"] for r in shortlist)),
            "resume": "python3 esef_fundamentals.py  # resumable: index+facts+store all cached"}
    # auto-court conveyor (2026-08-06 user directive): fresh, clean candidates flow to the
    # TRAP_VERIFY queue unconditionally — enqueue is idempotent + ledger-aware, so re-runs
    # are no-ops. Screens GENERATE; the queue verifies; courts adjudicate (never the screen).
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))  # repo root
        from desk.court_queue import enqueue_candidates
        cand = [r for r in shortlist
                if not r.get("fy_stale") and not r.get("scale_suspect")
                and not r.get("pfic") and not r.get("px_stale")][:15]
        c = enqueue_candidates([{**r, "ticker": r["sym"]} for r in cand],
                               source=f"screen_europe/{time.strftime('%Y-%m-%d')}")
        print(f"court_queue: {c['added']} new candidates enqueued for trap-verification")
    except Exception as e:
        print(f"court_queue enqueue failed (screen output unaffected): {type(e).__name__}: {e}")
    json.dump({"meta": meta, "rows": [{k: r.get(k) for k in keep} for r in shortlist[:150]]},
              open(SHORTLIST, "w"), ensure_ascii=False, indent=1)

    def fmt(r):
        am = f"{r['am']:.1f}" if r["am"] else ("subC" if r["subcash"] else " -")
        fy = f"{r['fcfy']*100:.0f}%" if r["fcfy"] is not None else " -"
        pb = f"{r['pb']:.2f}" if r["pb"] else " -"
        nc = f"{r['ncash_r']:.2f}" if r["ncash_r"] is not None else " -"
        nv = f"{r['ncav_r']:.2f}" if r["ncav_r"] is not None else " -"
        fl = " ".join(t for t, on in [
            ("PFIC", bool(r["pfic"])), ("ebit~", r["ebit_derived"]), ("WC-FCF", r["wc_fcf"]),
            ("DEBT?", r.get("debt_blind")), ("LEASE-FCF?", r.get("fcf_lease_blind")),
            ("1OFF?", r.get("one_off_suspect")),
            ("holdco", r["holdco"]), ("neg-eq", r["neg_equity"]), ("orphan", r["orphan_gb"]),
            ("float?", r.get("trust_cash_suspect")),
            ("PL-state", r["pl_state"]), ("fuzzy", "fuzzy" in (r["match_quality"] or "")),
            ("solo", not r.get("consol", True)), ("stale-px", r["px_stale"]),
            (f"FY{(r.get('period_end') or '????')[2:4]}!", r.get("fy_stale"))] if on)
        return (f"  {r['sym']:12s}{r['country']:3s}{r['mcap_usd']/1e6:7.0f} {am:>6s}{fy:>6s}"
                f"{pb:>6s}{nc:>7s}{nv:>6s} {r['wht']:>4s} {r['ibkr']:4s}"
                f" {r['ind'][:24]:24s} {fl}")

    npfic = sum(1 for r in shortlist if r["pfic"])
    norph = sum(1 for r in shortlist if r["orphan_gb"])
    print(f"\nEUROPE (ESEF) DEEP-VALUE SHORTLIST — annual FY2025 vintage, ex-financials/"
          f"trusts/REITs  n={len(shortlist)}  PFIC-flagged={npfic} "
          f"({npfic/max(len(shortlist),1)*100:.0f}%)  GB-orphans(sub-$500M)={norph}")
    print(f"  {'tkr':12s}{'cc':3s}{'mc$M':>7s}{'EV/EBIT':>6s}{'FCFy':>6s}{'P/B':>6s}"
          f"{'ncash/m':>7s}{'NCAV/m':>6s}{'WHT':>5s} {'IBKR':4s} {'name':24s} flags")
    for r in printable[:top]:
        print(fmt(r))
    print("\n  (GB: 0% WHT + 0.5% stamp on buys; Nordics: WHT treaty-reclaimable to ~15%, "
          "friction real; ebit~ = derived PBT+net-finance, not the filer's tag; "
          "all ratios in native filing ccy)")
    return shortlist


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--min-mcap-usd", type=float, default=4e7)
    ap.add_argument("--max-mcap-usd", type=float, default=None)
    ap.add_argument("--refresh-px", action="store_true")
    ap.add_argument("--no-resolve-new", action="store_true",
                    help="use only cached ticker resolutions (fast partial run)")
    a = ap.parse_args()
    run(a.top, a.min_mcap_usd, a.max_mcap_usd, a.refresh_px, resolve_new=not a.no_resolve_new)
