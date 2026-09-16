"""euronext_shelf — the EURONEXT/NORDIC leg of the global value screen.

================================ README ================================
WHAT IT SCREENS
  Overlooked small-cap value on the eight venues the ESEF leg does NOT reach with a
  current vintage:
      Euronext   Paris (.PA) / Amsterdam (.AS) / Brussels (.BR) / Lisbon (.LS) / Oslo (.OL)
      Nasdaq Nordic  Helsinki (.HE) / Stockholm (.ST) / Copenhagen (.CO)
  (`deep_value/global/screen_europe.py` covers GB/PL/SE/FI/DK/NO off filings.xbrl.org, but
  that feed stops at FY2024 for SE/NO and FY2023 for PL, and has NO coverage at all of
  FR/NL/BE/PT. This module is the current-vintage sibling, sourced from Yahoo rather than
  ESEF — a UNIVERSE + RANKING engine, never the source of record. Anything that reaches a
  court re-derives from the primary filing, same rule as every other leg.)

META-THESIS — COVERAGE-ECONOMICS ARBITRAGE
  Post-MiFID-II research is unbundled: below roughly EUR 300M of market cap no sell-side
  desk can fund coverage. The screen therefore carries `n_analysts` as a first-class column
  and flags `orphan` (0-1 analysts). That is the pond VRLA.PA and KALMAR.HE came out of.

SCORING — identical to the Japan/Korea/ESEF legs, NOT reimplemented
  `deep_value/score.py` is imported: composite = mean of rank-percentiles across
  {EV/EBIT, FCF-yield, P/B, net-cash/mktcap, NCAV/mktcap}, plus its guards (sub-cash,
  cash-burner, holdco/NCI, MLP-artifact, negative equity, WC-driven FCF).

HOW TO RE-RUN
  # 1. refresh the static universe (Yahoo screener sweep, 8 venues x 11 sectors) — slow,
  #    do it monthly; writes data/EURONEXT_UNIVERSE.json
  python3 euronext_shelf.py --refresh-universe
  # 2. score (fundamentals cached in data/euronext_fund_cache.json; --refresh-fund to redo)
  python3 euronext_shelf.py --top 30
  # 3. narrower / wider band
  python3 euronext_shelf.py --min-mcap-usd 3e7 --max-mcap-usd 2e9 --min-adv-usd 75e3
  Outputs: data/EURONEXT_SHELF.json  ({meta, rows}) — full scored universe.

IBKR CONIDS
  Conids are resolved OUT OF BAND (the IBKR MCP `search_contracts` tool) and merged in from
  data/euronext_conids.json — {"<yahoo sym>": {"conid":.., "ibkr_symbol":.., "exchange":..,
  "currency":.., "verified_utc":..}}. Missing = "not yet verified", never "not executable".

GUARDS (each is a COLUMN — nothing is silently excluded except funds/financials)
  (a) IFRS CONSOLIDATION. Yahoo statements are the consolidated group where one exists.
      `consol_unverified` fires when neither a Minority Interest nor a Total-Equity-Gross-
      Minority-Interest row is present (the Fujitsu parent-only trap from the Japan leg has
      no direct analogue here, but absence of the NCI block is the same tell). `holdco`
      (score.py) fires on material NCI; `mlp_artifact` on NCI > equity.
  (b) CURRENCY / UNIT PLANES — the priceMagnifier lesson. Two currencies exist per name and
      they are NOT the same: the QUOTE currency (EUR/NOK/SEK/DKK) and the REPORTING
      currency Yahoo files the statements in (`financialCurrency`). They diverge constantly
      on these venues — EQNR.OL quotes NOK / reports USD; ABI.BR quotes EUR / reports USD;
      AZN.ST quotes SEK / reports USD. Market cap is bridged into the REPORTING currency
      exactly once, in `_to_fin_ccy()`, and every ratio is then single-plane. USD appears
      only as the display column and the $-floors. A per-venue median-P/B plane check runs
      before anything prints and HARD-FAILS on a 100x-class error.
  (c) FREE-FLOAT + ADV FLOORS — a scanner ask is not an acquirable position (the muni
      liquidity-gate lesson). `--min-adv-usd` (default $75k/day, 3-month average) and
      `--min-float` (default 15% of shares out) gate the shelf; `thin` flags ADV < $300k.
  (d) FINANCIALS EXCLUDED FROM THE GRAHAM SCORE. Banks/insurers/asset managers/REITs carry
      different balance-sheet semantics — "net cash" is meaningless for a deposit-taker.
      Financial Services + Real Estate sectors, fund/trust names, and balance-shape
      investment vehicles are dropped from the scored shelf; counts are reported and the
      rows stay in the universe file.
  (e) PFIC — deliberately NOT screened. §1297 is a US-holder issue on the Japan/Korea legs;
      EU/EEA operating companies in this band are not a PFIC population. Skipped by design.
  (f) TRUST / CLIENT-CASH (inherited from the OTB.L catch on the ESEF leg): travel, betting,
      payments, ticketing, insurance-broking and estate-agency models hold ring-fenced
      CUSTOMER float on the face of the balance sheet. Netting it manufactures phantom EV.
      Flagged names are scored on the TRUST-SAFE variant (EV with no cash netting).
  (g) DUAL-LINE / NON-EQUITY HYGIENE. These venues list bond lines, ETPs and second
      currency lines of the same issuer that Yahoo tags quoteType=EQUITY (e.g. "ACCOR USD",
      "Credit Agricole 1.4% BDS 20/07/2027"). Filtered by name pattern, and deduped by
      normalized issuer name keeping the most liquid line. Nordic A/B/C share classes are
      deduped the same way (identical fundamentals, one issuer) keeping the liquid class.
  (h) EARNINGS DURABILITY — `durability_suspect`, the guard this build was written around.
      score.py's one-time-gain guard reads an UNUSUAL-ITEMS tag, and Yahoo's operating income
      is already normalized to exclude those. A windfall that arrives as REVENUE therefore
      passes both untouched, and one year of windfall EBIT against a collapsed market cap is
      arithmetically indistinguishable from a bargain — so these names sort to the TOP.
      Caught on the first run and verified against primary filings:
        * CANTA.ST (Cantargia) ranked #4 on EV/EBIT 1.2 and 35% FCF yield. Its year-end
          report shows FY2025 net sales SEK 316.7M against SEK 0.0 the prior year and
          operating +154.1M against -168.6M — a CAN10 partnership upfront. Q4 standalone was
          still -28.4M, and in May/June 2026 it raised SEK 124M of equity plus a SEK 75M
          loan. Profitable on the tape, burning in reality.
        * LKFT.AS ranked sub-cash on EBIT +EUR 596M while operating cash flow ran -EUR 302M.
      Three tests, any of which fires: revenue appearing from ~zero or tripling year on year;
      EBIT flipping from a prior-year loss; EBIT positive while FCF is negative (the mirror
      of score.py's `wc_fcf`). Flagged names are DEMOTED from the printed table and kept in
      the JSON with `durability_why` — they are not necessarily bad businesses, but their
      cheapness is an artifact of one year and a human must read the prior year first.

  (i) MELTING ICE CUBE — `melting` / `ebit_trend`. The composite is a SNAPSHOT: a collapsing
      multiple scores identically to a cheap one. `ebit_trend` = current EBIT divided by the
      oldest annual EBIT Yahoo carries (usually 4 years back), and `melting` fires below
      0.5x. Catena Media tops the first run at EV/EBIT 1.4 with EBIT down EUR 37M -> 6.8M
      over four years — the multiple "improved" because the business shrank. This is
      INFORMATIONAL, never a demotion: a trough multiple on a cyclical is the buy and on a
      structural decliner is the trap, and only a human reading the business can tell which.

KNOWN LIMITATIONS
  * The durability guard is a ONE-YEAR test by design and a second sustained year clears it.
    SANION.ST (Saniona) passes on revenue 16.8 -> 334.7 -> 434.4 SEK M: the step-change is
    two years old and has repeated, so it is no longer a single-year artifact by this test.
    That is the intended boundary, but a licensing-driven P&L can stay lumpy for years —
    read `rev_hist`/`ebit_hist` in the cache before trusting any biotech on this shelf.
  * The composite does not penalise DECLINE (see guard (i)) and does not look at leverage
    beyond EV. Rank order is cheapness, not quality.
  * Yahoo is a SECONDARY source. It is fine for ranking a universe; it is not evidence.
    Every name that reaches a court must be re-derived from the primary filing.
  * Yahoo's `Operating Income` is NORMALIZED — it excludes unusual items (verified
    2026-08-02: VRLA.PA 312.8M = 246.3M as-reported + 83.6M of charges added back), so
    `OneTimeGain_ttm` is fed 0 rather than double-counting the add-back. The gap is emitted
    as `unusual_r` (unusual items / EBIT) and `ebit_reported`; a large negative `unusual_r`
    on a serial restructurer means the screen's EBIT is more flattering than the filed one.
    NOTE this normalization is exactly WHY guard (h) exists: it strips unusual items but
    NOT one-time revenue, so the unusual-items path cannot see a licensing upfront at all.
  * Yahoo's fundamentals were NOT found to be sign-inverted or scale-broken on this
    universe. That hypothesis was raised by the biotech cluster at the top of the first run
    and REFUTED against Cantargia's primary year-end report, which matched Yahoo line for
    line. The problem was economic (one-time revenue), not a data bug — worth recording so
    the next reader does not re-litigate it. Aggregator cross-checks are NOT independent
    here: stockanalysis.com returned Yahoo's figures to the decimal, i.e. same vendor.
  * IFRS-16 LEASE LIABILITIES sit inside Yahoo's Total Debt, so EV is overstated for
    lease-heavy models (retail, shipping). Bias is conservative (bigger EV -> worse
    multiple -> the screen will not manufacture a false bargain), and `lease_debt` is
    emitted so the reader can back it out.
  * Balance sheet is the latest available (quarterly preferred when it is newer AND
    complete); flows are TTM where Yahoo has them, else the latest annual. `bs_date`,
    `flow_date`, `ttm` and `fy_stale` carry the vintage; a period mismatch between a
    year-end balance sheet and TTM flows is normal and flagged, never hidden.
  * Free float is Yahoo's `floatShares` — an estimate. Absent for a real slice of these
    names (`float_unknown`), in which case the float gate cannot bind and only ADV does.
  * The universe is a STATIC snapshot; a delisted or newly listed name is invisible until
    `--refresh-universe`. Yahoo's screener also caps each stream, which is why the sweep is
    run per (exchange x sector) rather than per exchange.
  * WHT is the statutory rate. FR 25%, NL 15%, BE 30%, PT 28%, NO 25%, FI 35%, SE 30%,
    DK 27% — most treaty-reclaimable to 15%, but the reclaim is paperwork and months of
    float. BE at 30% and FI at 35% are the ones that actually change an income case.
  * No French FTT modelling. France levies 0.3% on buys of FR-incorporated issuers with
    market cap > EUR 1bn (annual list); `fr_ftt_likely` is a market-cap PROXY, not the list.
========================================================================
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
# reuse the US composite + guards (never reimplemented) — verticals/deep_value/score.py
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "deep_value"))
import score as S                                              # noqa: E402

DATA = os.path.join(HERE, "data")
UNIVERSE = os.path.join(DATA, "EURONEXT_UNIVERSE.json")
FUND_CACHE = os.path.join(DATA, "euronext_fund_cache.json")
CONIDS = os.path.join(DATA, "euronext_conids.json")
OUT = os.path.join(DATA, "EURONEXT_SHELF.json")

# venue -> (yahoo region, yahoo exchange code, suffix, IBKR exchange, quote ccy, WHT)
VENUES = {
    "PAR": {"region": "fr", "sfx": ".PA", "ibkr": "SBF",  "ccy": "EUR", "wht": "25%r", "mkt": "Euronext Paris"},
    "AMS": {"region": "nl", "sfx": ".AS", "ibkr": "AEB",  "ccy": "EUR", "wht": "15%",  "mkt": "Euronext Amsterdam"},
    "BRU": {"region": "be", "sfx": ".BR", "ibkr": "ENEXT.BE", "ccy": "EUR", "wht": "30%r", "mkt": "Euronext Brussels"},
    "LIS": {"region": "pt", "sfx": ".LS", "ibkr": "BVL",  "ccy": "EUR", "wht": "28%r", "mkt": "Euronext Lisbon"},
    "OSL": {"region": "no", "sfx": ".OL", "ibkr": "OSE",  "ccy": "NOK", "wht": "25%r", "mkt": "Euronext Oslo Bors"},
    "HEL": {"region": "fi", "sfx": ".HE", "ibkr": "HEX",  "ccy": "EUR", "wht": "35%r", "mkt": "Nasdaq Helsinki"},
    "STO": {"region": "se", "sfx": ".ST", "ibkr": "SFB",  "ccy": "SEK", "wht": "30%r", "mkt": "Nasdaq Stockholm"},
    "CPH": {"region": "dk", "sfx": ".CO", "ibkr": "CPH",  "ccy": "DKK", "wht": "27%r", "mkt": "Nasdaq Copenhagen"},
}
SECTORS = ["Basic Materials", "Energy", "Technology", "Healthcare", "Communication Services",
           "Consumer Cyclical", "Consumer Defensive", "Industrials", "Utilities",
           "Financial Services", "Real Estate"]
FIN_SECTORS = {"Financial Services", "Real Estate"}

# static screening FX -> USD (fallback; refreshed live at run time and stamped into meta)
FX_FALLBACK = {"USD": 1.0, "EUR": 1.16, "NOK": 0.099, "SEK": 0.105, "DKK": 0.156,
               "GBP": 1.34, "CHF": 1.25, "PLN": 0.27, "ISK": 0.0082, "CAD": 0.73, "JPY": 0.0066}
FX_PAIRS = {"EUR": "EURUSD=X", "NOK": "NOKUSD=X", "SEK": "SEKUSD=X", "DKK": "DKKUSD=X",
            "GBP": "GBPUSD=X", "CHF": "CHFUSD=X", "PLN": "PLNUSD=X", "CAD": "CADUSD=X",
            "JPY": "JPYUSD=X"}

# (g) non-equity / duplicate-line hygiene: bond lines, ETPs, second-currency lines
NON_EQUITY = re.compile(
    r"(\d\s?[.,]?\d*\s?%|\bBDS?\b|\bOBLIG|\bEMTN\b|\bWARRANT|\bCERTIFICAT|\bTURBO\b"
    r"|\bETP\b|\bETF\b|\bETN\b|\bDAILY (LONG|SHORT)|LEVERAGED|WISDOMTREE|\bAMUNDI .*(ETP|ETC)"
    r"|\bSUBSCRIPTION RIGHT|\bSTRIP\b|\bZC\b|\bTRACKER\b)", re.I)
DUP_CCY_LINE = re.compile(r"\b(USD|EUR|CHF|GBP|SEK|NOK|DKK)\s*$", re.I)
# Nordic venues list A/B/C share classes as separate lines of the SAME issuer with the SAME
# fundamentals (Volvo A/B, Novo Nordisk A/B, Ericsson A/B...). Scoring both double-counts the
# issuer and floods the shelf; the dedup keeps the most liquid class, which is also the one
# that is actually acquirable. Stripped from the dedup key only — the surviving row keeps its
# real name and ticker.
SHARE_CLASS = re.compile(r"\b(CLASS|SER(IE[SR]?)?\.?|SERIE)\s+[A-Z]\b|\b[A-C]\s+(SHARES?|AKTIER)\b",
                         re.I)
# (d) fund / trust / investment-vehicle names the sector tag misses
FUNDISH = re.compile(
    r"(SICAV|SICAF|\bFUND\b|FONDEN|FONDS\b|\bAIF\b|INVESTMENT TRUST|INVESTMENT COMPANY"
    r"|PRIVATE EQUITY|\bREIT\b|SIIC\b|\bSPAC\b|ACQUISITION CORP|\bBEVEK\b|\bGVV\b|\bSIR\b"
    r"|\bOPCI\b|\bSCPI\b|CLOSED[- ]END)", re.I)
# (f) trust / client-cash models (the OTB.L catch, inherited from the ESEF leg)
TRUST_INDUSTRY = re.compile(
    r"(Travel|Tour|Lodging|Airlines|Gambling|Casino|Betting|Insurance Broker|Ticket"
    r"|Payment|Real Estate Services|Financial Conglomerates)", re.I)
TRUST_NAME = re.compile(
    r"(TRAVEL|TOUR OPERATOR|\bTOURS?\b|HOLIDAYS?\b|CRUISE|\bVOYAGE|REIS\b|\bRESOR\b|TICKET"
    r"|\bBET\b|BETTING|GAMING|CASINO|LOTTER|BOOKMAK|INSURANCE BROK|ESTATE AGEN|COURTAGE"
    r"|PAYMENTS?\b|PAYTECH|\bBETSSON|\bKINDRED)", re.I)
LEGAL_SFX = re.compile(
    r"\b(S\.?A\.?S?\.?|N\.?V\.?|B\.?V\.?|ASA|AS|A/S|AB|OYJ|ABP|OY|PLC|SE|SCA|SPA|GROUP|GROUPE"
    r"|HOLDING(S|EN)?|KONSERN|GRUPPEN|COMPAGNIE|CIE|PUBL|AKTIEBOLAG)\b\.?", re.I)

PX_STALE_DAYS = 7
BS_KEYS = ("Total Assets", "Current Assets", "Total Liabilities Net Minority Interest",
           "Stockholders Equity", "Cash And Cash Equivalents")


# ----------------------------------------------------------------- universe assembly
def refresh_universe(pause=0.4) -> dict:
    """Yahoo screener sweep: one paginated stream per (exchange x sector).

    Per-exchange streams alone get truncated by the screener's result cap, so the sweep is
    sliced by sector — which also hands us the sector tag the screener does not otherwise
    return. Writes the static universe file; re-run monthly (listings/delistings only move
    at that pace) or whenever a name is expected and missing.
    """
    import yfinance as yf
    rows, seen = {}, 0
    for ex, v in VENUES.items():
        got = 0
        for sec in SECTORS:
            off = 0
            while True:
                q = yf.EquityQuery("and", [
                    yf.EquityQuery("eq", ["region", v["region"]]),
                    yf.EquityQuery("is-in", ["exchange", ex]),
                    yf.EquityQuery("is-in", ["sector", sec])])
                try:
                    r = yf.screen(q, size=250, offset=off, sortField="intradaymarketcap",
                                  sortAsc=False)
                except Exception as e:
                    print(f"  {ex}/{sec} off={off} FAILED: {e}")
                    break
                qs = r.get("quotes") or []
                for x in qs:
                    if x.get("quoteType") != "EQUITY":
                        continue
                    sym = x.get("symbol")
                    if not sym or sym in rows:
                        continue
                    rows[sym] = {
                        "sym": sym, "venue": ex, "country": v["region"].upper(),
                        "sector": sec,
                        "name": (x.get("longName") or x.get("shortName") or "").strip(),
                        "px": x.get("regularMarketPrice"),
                        "px_ccy": x.get("currency"),
                        "fin_ccy": x.get("financialCurrency"),
                        "mcap_q": x.get("marketCap"),
                        "shares": x.get("sharesOutstanding"),
                        "adv3m": x.get("averageDailyVolume3Month"),
                        "pb_yahoo": x.get("priceToBook"),
                        "px_ts": x.get("regularMarketTime"),
                        "first_trade_ms": x.get("firstTradeDateMilliseconds"),
                    }
                    got += 1
                seen += len(qs)
                off += 250
                total = r.get("total") or 0
                time.sleep(pause)
                if off >= total or not qs:
                    break
        print(f"  {ex} ({VENUES[ex]['mkt']}): {got} equity lines")
    os.makedirs(DATA, exist_ok=True)
    payload = {"meta": {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "venues": list(VENUES), "sectors": SECTORS,
                        "raw_quotes_seen": seen,
                        "refresh": "python3 euronext_shelf.py --refresh-universe"},
               "rows": list(rows.values())}
    json.dump(payload, open(UNIVERSE, "w"), ensure_ascii=False, indent=1)
    print(f"universe written: {len(rows)} lines -> {UNIVERSE}")
    return payload


def load_universe() -> dict:
    if not os.path.exists(UNIVERSE):
        raise SystemExit(f"no universe file — run: python3 {os.path.basename(__file__)} "
                         f"--refresh-universe")
    return json.load(open(UNIVERSE))


# ----------------------------------------------------------------- FX
def live_fx() -> tuple[dict, str]:
    """Live -> USD rates for the quote/reporting currencies in play; static fallback."""
    fx = dict(FX_FALLBACK)
    basis = "static fallback"
    try:
        import yfinance as yf
        got = 0
        for ccy, pair in FX_PAIRS.items():
            try:
                p = yf.Ticker(pair).fast_info["last_price"]
                if p and p > 0:
                    fx[ccy] = float(p)
                    got += 1
            except Exception:
                pass
        if got:
            basis = f"live yfinance FX ({got}/{len(FX_PAIRS)} pairs)"
    except ImportError:
        pass
    return fx, basis


def _to_fin_ccy(amount, quote_ccy, fin_ccy, fx):
    """Bridge a QUOTE-currency amount into the REPORTING currency — the single place any
    currency plane is crossed (the priceMagnifier lesson: never mix units in a ratio).
    Sub-unit quoting (GBp/ZAc-class) is handled here too, should a line ever carry it."""
    if amount is None or not quote_ccy or not fin_ccy:
        return None
    if quote_ccy in ("GBp", "GBX"):
        amount, quote_ccy = amount / 100.0, "GBP"
    if quote_ccy in ("ZAc", "ILA"):
        amount, quote_ccy = amount / 100.0, ("ZAR" if quote_ccy == "ZAc" else "ILS")
    fq, ff = fx.get(quote_ccy), fx.get(fin_ccy)
    if not fq or not ff:
        return None
    return amount * fq / ff


# ----------------------------------------------------------------- fundamentals
def _row(df, *labels):
    """First present label's most-recent value from a yfinance statement frame."""
    if df is None or getattr(df, "empty", True):
        return None
    for lb in labels:
        if lb in df.index:
            try:
                v = df.loc[lb].iloc[0]
            except Exception:
                continue
            if v is not None and v == v:            # not NaN
                return float(v)
    return None


def _colstamp(df):
    try:
        return str(df.columns[0].date())
    except Exception:
        return None


def _hist(df, *labels, n=4):
    """Up to n periods of the first present label, most recent first."""
    if df is None or getattr(df, "empty", True):
        return []
    for lb in labels:
        if lb in df.index:
            out = []
            for v in list(df.loc[lb].values)[:n]:
                out.append(float(v) if (v is not None and v == v) else None)
            return out
    return []


def _map_facts(bs, inc, cf, info, inc_annual=None) -> dict:
    """yfinance statement frames -> the us-gaap key convention score.py consumes.

    Conservative by construction, same bias as score.py: debt is over-captured (Total Debt
    carries IFRS-16 lease liabilities), cash is under-captured (only true cash + short-term
    investments), so EV is if anything too big and the screen cannot manufacture a bargain.
    """
    g = {}
    g["Assets"] = _row(bs, "Total Assets")
    g["AssetsCurrent"] = _row(bs, "Current Assets")
    g["LiabilitiesCurrent"] = _row(bs, "Current Liabilities")
    g["Liabilities"] = _row(bs, "Total Liabilities Net Minority Interest")
    g["StockholdersEquity"] = _row(bs, "Stockholders Equity", "Common Stock Equity")
    g["MinorityInterest"] = _row(bs, "Minority Interest") or 0.0
    g["CashAndCashEquivalentsAtCarryingValue"] = _row(
        bs, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments")
    g["ShortTermInvestments"] = _row(bs, "Other Short Term Investments")
    g["LongTermInvestments"] = _row(bs, "Investments And Advances", "Long Term Equity Investment")
    # debt: prefer the all-in combined tag, exactly the slot score.py floors against
    g["DebtLongtermAndShorttermCombinedAmount"] = _row(bs, "Total Debt")
    # pension is added to the debt slot AFTER it is read (see _pension_obligation below);
    # the adjustment is applied at the end of this function so the raw tag stays auditable
    g["LongTermDebtNoncurrent"] = _row(bs, "Long Term Debt And Capital Lease Obligation",
                                       "Long Term Debt")
    g["DebtCurrent"] = _row(bs, "Current Debt And Capital Lease Obligation", "Current Debt")
    g["_SharesIssued"] = _row(bs, "Ordinary Shares Number", "Share Issued")
    g["_lease_debt"] = (_row(bs, "Capital Lease Obligations") or 0.0)

    # ---- P1 PENSION GUARD (SFPI.PA court, 2026-08-03) --------------------------------
    # IAS-19 book-reserve pensions are DEBT-LIKE and invisible to yfinance's net-cash view.
    # SFPI carried EUR50.6M of unfunded German/French retirement obligations — a Key Audit
    # Matter for BOTH auditors — which turned "39% of the cap in net cash" into 12-18% and
    # EV/EBIT 4.5x into 6.0-6.5x. Standard across German, French and Nordic industrials, so
    # this is a shelf-wide correction, not a one-name fix.
    # yfinance rarely carries an explicit pension tag for European filers; the obligation
    # lands in PROVISIONS instead. SFPI: "Long Term Provisions" = EUR48.9M against the
    # EUR50.6M of IAS-19 retirement obligations the court read out of the annual report —
    # close enough to be the same number, and it is the only machine-readable proxy we have.
    _pens_tag = _row(bs, "Pension And Other Post Retirement Benefit Plans",
                         "Non Current Pension And Other Postretirement Benefit Plans")
    _prov_lt = _row(bs, "Long Term Provisions") or 0.0
    g["_pension_obligation"] = _pens_tag if _pens_tag else _prov_lt
    g["_pension_source"] = ("pension_tag" if _pens_tag else
                            "long_term_provisions_proxy" if _prov_lt else "NONE_FOUND")
    g["_pension_is_proxy"] = bool(not _pens_tag and _prov_lt)
    # a proxy is NOT a verification: provisions also carry warranty, restructuring and
    # litigation. Flag it so the promoter reads the IAS-19 note before sizing.
    g["_pension_note"] = (
        "provisions used as the pension proxy — includes warranty/restructuring/litigation, "
        "so it OVER-captures; verify the IAS-19 split in the annual report before promoting"
        if g["_pension_is_proxy"] else
        ("explicit pension tag" if _pens_tag else
         "NO provisions or pension tag found — for a DE/FR/Nordic industrial treat net cash "
         "as UNVERIFIED rather than clean"))

    if g.get("_pension_obligation"):
        base = g.get("DebtLongtermAndShorttermCombinedAmount") or 0.0
        g["_debt_ex_pension"] = base
        g["DebtLongtermAndShorttermCombinedAmount"] = base + g["_pension_obligation"]

    g["Revenues"] = _row(inc, "Total Revenue", "Operating Revenue")
    g["OperatingIncomeLoss"] = _row(inc, "Operating Income")
    g["_ebit_reported"] = _row(inc, "Total Operating Income As Reported")
    g["_unusual"] = _row(inc, "Total Unusual Items", "Special Income Charges")
    g["_ebit_derived"] = False
    if g["OperatingIncomeLoss"] is None:
        pre, ie, ii = (_row(inc, "Pretax Income"), _row(inc, "Interest Expense"),
                       _row(inc, "Interest Income"))
        if pre is not None and (ie is not None or ii is not None):
            g["OperatingIncomeLoss"] = pre + (ie or 0.0) - (ii or 0.0)
            g["_ebit_derived"] = True
        else:
            g["OperatingIncomeLoss"] = _row(inc, "EBIT")
            g["_ebit_derived"] = g["OperatingIncomeLoss"] is not None
    # Yahoo's Operating Income is NORMALIZED (excludes unusual items — verified on VRLA.PA
    # 2026-08-02), so the one-time-gain guard is structurally satisfied; feeding a non-zero
    # OneTimeGain here would double-count the add-back. See README.
    g["OneTimeGain_ttm"] = 0.0

    g["NetCashProvidedByUsedInOperatingActivities"] = _row(cf, "Operating Cash Flow")
    capx = _row(cf, "Capital Expenditure")
    g["PaymentsToAcquirePropertyPlantAndEquipment"] = abs(capx) if capx is not None else None

    # EARNINGS-DURABILITY inputs: annual revenue/EBIT history. A licensing upfront, an asset
    # sale or a lumpy project completion lands in REVENUE, which Yahoo's operating-income
    # normalization never touches — so the unusual-items logic above cannot see it. The prior
    # year is what exposes it. (Cantargia FY2025: net sales SEK 316.7M against SEK 0.0 the
    # year before, operating +154.1M against -168.6M — a CAN10 partnership upfront, not
    # earnings power; Q4 alone still ran -28.4M and the company raised SEK 124M of equity plus
    # a SEK 75M loan five months later. Verified against the primary year-end report.)
    g["_rev_hist"] = _hist(inc_annual, "Total Revenue", "Operating Revenue")
    g["_ebit_hist"] = _hist(inc_annual, "Operating Income")
    # (a) consolidation: the NCI block is the tell that these are group accounts
    g["_consol_verified"] = ("Minority Interest" in getattr(bs, "index", [])
                             or "Total Equity Gross Minority Interest" in getattr(bs, "index", []))
    g["_float"] = (info or {}).get("floatShares")
    g["_n_analysts"] = (info or {}).get("numberOfAnalystOpinions")
    g["_industry"] = (info or {}).get("industry")
    g["_sector_info"] = (info or {}).get("sector")
    g["_fin_ccy_info"] = (info or {}).get("financialCurrency")
    g["_bs_date"], g["_flow_date"] = _colstamp(bs), _colstamp(inc)
    return g


def _pull_one(sym):
    import yfinance as yf
    t = yf.Ticker(sym)
    bs = None
    try:
        qbs = t.quarterly_balance_sheet
        abs_ = t.balance_sheet
        # prefer the quarterly balance sheet only when it is NEWER and COMPLETE — a half
        # populated interim BS would silently break the net-cash / NCAV legs of the score
        ok_q = (qbs is not None and not qbs.empty
                and all(k in qbs.index for k in BS_KEYS))
        if ok_q and (abs_ is None or abs_.empty
                     or qbs.columns[0] > abs_.columns[0]):
            bs = qbs
        else:
            bs = abs_
    except Exception:
        pass
    # flows: TTM where Yahoo has it (materially fresher on semi-annual EU reporters —
    # KALMAR.HE TTM ran to 2026-06-30 against a 2025-12-31 annual), else the latest annual
    inc, cf, info, ttm_i = None, None, None, False
    try:
        inc_annual = t.income_stmt          # always — the durability guard needs prior years
    except Exception:
        inc_annual = None
    try:
        inc = t.ttm_income_stmt
        ttm_i = inc is not None and not inc.empty
    except Exception:
        pass
    if not ttm_i:
        inc = inc_annual
    try:
        cf = t.ttm_cashflow
        if cf is None or cf.empty:
            cf = t.cashflow
    except Exception:
        try:
            cf = t.cashflow
        except Exception:
            cf = None
    try:
        info = t.info
    except Exception:
        info = {}
    f = _map_facts(bs, inc, cf, info, inc_annual=inc_annual)
    f["_ttm"] = bool(ttm_i)
    f["_fetched"] = time.time()
    return f


MAX_FAILS = 4
BREAKER_N = 25          # consecutive empties that mean "throttled", not "no data"


def yahoo_throttled() -> bool:
    """Probe Yahoo's crumb endpoint directly — the thing that actually rate-limits.

    yfinance asks for a crumb, gets 'Too Many Requests', and then returns EMPTY statement
    frames with no exception. Reading that as "this company has no balance sheet" is how a
    throttle silently deletes whole venues from a shelf, so the pull tests the door first.
    """
    try:
        import yfinance.data as D
        return not bool(D.YfData()._get_cookie_and_crumb()[1])
    except Exception:
        return False


def fetch_fundamentals(syms, refresh=False, workers=2, pace=0.25, batch_pause=5.0) -> dict:
    """Threaded per-name pull (BS + TTM IS + TTM CF + info ~ 1s/name), cached hard.

    YAHOO THROTTLES AT UNIVERSE SCALE and it does so SILENTLY — 200s with EMPTY frames, no
    exception (measured 2026-08-02: the first ~330 names came back clean, then every
    Helsinki/Stockholm/Copenhagen name returned an empty balance sheet; the debug log showed
    "Didn't receive crumb Edge: Too Many Requests"). Two consequences are encoded here:

      1. an empty frame is a RETRYABLE failure, never "this company has no balance sheet";
      2. retrying INTO a live throttle deepens it — every retry re-hits the same crumb
         endpoint that is already refusing. So the pull runs a CIRCUIT BREAKER: after
         BREAKER_N consecutive empties it stops, preserves the cache, and tells the caller
         to re-run later. A partial shelf that KNOWS it is partial beats a full-looking
         shelf that quietly lost three venues.
    """
    cache = json.load(open(FUND_CACHE)) if os.path.exists(FUND_CACHE) else {}
    todo = [s for s in syms
            if refresh or s not in cache
            or (not cache[s].get("Assets") and cache[s].get("_fails", 0) < MAX_FAILS)]
    if not todo:
        return cache
    retries = sum(1 for s in todo if s in cache)
    print(f"pulling fundamentals for {len(todo)} names "
          f"({len(syms)-len(todo)} cached, {retries} retrying), {workers} workers")
    if yahoo_throttled():
        print("  !! Yahoo crumb endpoint is rate-limited RIGHT NOW — skipping the pull "
              "entirely rather than burning the names as failures. Re-run in ~15-30 min; "
              "the cache resumes where it stopped.")
        return cache
    done, streak, tripped = 0, 0, False
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for sym, f in zip(chunk, ex.map(lambda s: _safe(s, pace=pace), chunk)):
                if not f.get("Assets"):
                    streak += 1
                    # NEVER let a throttled empty overwrite a good cached row. On a
                    # --refresh-fund pass a rate-limit would otherwise DELETE working
                    # fundamentals for every name it touched — the refresh would destroy
                    # exactly the data it was run to improve. Keep the old row, count the
                    # failure on it, and let the breaker below stop the pass.
                    old = cache.get(sym)
                    if old and old.get("Assets"):
                        old["_fails"] = old.get("_fails", 0) + 1
                        old["_stale_refresh"] = True
                    else:
                        f["_fails"] = (old or {}).get("_fails", 0) + 1
                        cache[sym] = f
                else:
                    streak = 0
                    cache[sym] = f
                done += 1
        ok = sum(1 for s in todo[:done] if cache.get(s, {}).get("Assets"))
        print(f"  ...{done}/{len(todo)}  ({ok} with a balance sheet)")
        json.dump(cache, open(FUND_CACHE, "w"))
        if streak >= BREAKER_N:
            tripped = True
            break
        if done < len(todo):
            time.sleep(batch_pause)
    json.dump(cache, open(FUND_CACHE, "w"))
    if tripped:
        left = len(todo) - done
        print(f"  !! CIRCUIT BREAKER: {streak} consecutive empty pulls = Yahoo is throttling. "
              f"Stopped with {left} names unpulled (cached, will resume). Re-run in ~15-30 "
              f"min. The shelf below is PARTIAL — check meta.pull_complete in the JSON.")
    return cache


def _safe(sym, tries=2, pace=0.25):
    """One retry on an exception or a silent-empty result; deliberately NOT more, because
    retrying into a live throttle is what deepens it."""
    import random
    last = None
    for k in range(tries):
        try:
            f = _pull_one(sym)
            if f.get("Assets"):
                time.sleep(pace)
                return f
            last = f
        except Exception as e:
            last = {"_error": f"{type(e).__name__}: {e}"}
        time.sleep(pace + (2 ** k) + random.random())
    out = last or {}
    out["_fetched"] = time.time()
    return out


def _norm_name(n):
    s = re.sub(r"[^A-Z0-9 ]", " ", (n or "").upper())
    s = LEGAL_SFX.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


# ----------------------------------------------------------------- the screen
def run(top=30, min_mcap_usd=2.5e7, max_mcap_usd=3e9, min_adv_usd=75e3, min_float=0.15,
        refresh_fund=False, workers=2, limit=None):
    uni = load_universe()
    rows = uni["rows"]
    fx, fx_basis = live_fx()
    print(f"universe: {len(rows)} lines (generated {uni['meta']['generated_utc']}) | FX: {fx_basis}")

    # ---- (g) non-equity + duplicate-line hygiene ----------------------------------
    drop = Counter()
    cand = []
    for r in rows:
        nm = r.get("name") or ""
        if NON_EQUITY.search(nm):
            drop["non_equity_line"] += 1
            continue
        if FUNDISH.search(nm):
            drop["fund_vehicle_name"] += 1
            continue
        cand.append(r)
    # second-currency lines ("ACCOR USD") and A/B share classes of the same issuer: keep the
    # most liquid line — the duplicate carries identical fundamentals and would double-count
    by_issuer = {}
    for r in cand:
        base = SHARE_CLASS.sub(" ", DUP_CCY_LINE.sub("", r.get("name") or ""))
        base = _norm_name(base)
        key = (r["venue"], base)
        cur = by_issuer.get(key)
        if cur is None or (r.get("adv3m") or 0) > (cur.get("adv3m") or 0):
            by_issuer[key] = r
    drop["dup_currency_line"] = len(cand) - len(by_issuer)
    cand = list(by_issuer.values())

    # ---- (d) financials / real estate out of the Graham score ---------------------
    fin_rows = [r for r in cand if r["sector"] in FIN_SECTORS]
    cand = [r for r in cand if r["sector"] not in FIN_SECTORS]
    drop["financials_realestate"] = len(fin_rows)

    # ---- cheap pre-filters before spending a fundamentals call --------------------
    pre = []
    for r in cand:
        px, qccy = r.get("px"), r.get("px_ccy")
        if not px or not qccy or qccy not in fx:
            drop["no_price"] += 1
            continue
        mcap_usd = (r.get("mcap_q") or (px * (r.get("shares") or 0))) * fx[qccy]
        if not mcap_usd or mcap_usd <= 0:
            drop["no_mcap"] += 1
            continue
        r["_mcap_usd_pre"] = mcap_usd
        if not (min_mcap_usd <= mcap_usd <= max_mcap_usd):
            drop["mcap_band"] += 1
            continue
        adv_usd = (r.get("adv3m") or 0) * px * fx[qccy]
        r["_adv_usd"] = adv_usd
        if adv_usd < min_adv_usd:                       # (c) ADV floor — must be buyable
            drop["adv_floor"] += 1
            continue
        pre.append(r)
    print("pre-filter drops: " + ", ".join(f"{k}={v}" for k, v in drop.most_common()))
    print(f"candidates for fundamentals: {len(pre)}")
    if limit:
        pre = sorted(pre, key=lambda r: -(r["_adv_usd"]))[:limit]

    funds = fetch_fundamentals([r["sym"] for r in pre], refresh=refresh_fund, workers=workers)

    now = time.time()
    recs, post = [], Counter()
    for r in pre:
        f = funds.get(r["sym"]) or {}
        if f.get("_error") or not f.get("Assets"):
            post["no_fundamentals"] += 1
            continue
        if f.get("OperatingIncomeLoss") is None and \
           f.get("NetCashProvidedByUsedInOperatingActivities") is None:
            post["no_income_anchor"] += 1
            continue
        # (d) second pass: Yahoo's own industry tag catches financials the sector missed
        ind = f.get("_industry") or ""
        if re.search(r"(Bank|Insurance|Asset Management|Capital Markets|REIT|Credit Services"
                     r"|Mortgage|Closed-End Fund|Shell Compan)", ind, re.I):
            post["financial_industry"] += 1
            continue
        # (d) balance-shape investment vehicle: investments+cash dominate, revenue trivial
        invsum = sum((f.get(k) or 0) for k in ("CashAndCashEquivalentsAtCarryingValue",
                                               "ShortTermInvestments", "LongTermInvestments"))
        if f["Assets"] and invsum / f["Assets"] > 0.85 and (f.get("Revenues") or 0) < 0.05 * f["Assets"]:
            post["balance_shape_vehicle"] += 1
            continue

        # ---- (b) THE CURRENCY PLANE: bridge mcap QUOTE -> REPORTING, exactly once ----
        fccy = f.get("_fin_ccy_info") or r.get("fin_ccy") or r.get("px_ccy")
        qccy = r.get("px_ccy")
        if fccy not in fx or qccy not in fx:
            post["unknown_currency"] += 1
            continue
        px_f = _to_fin_ccy(r["px"], qccy, fccy, fx)
        shares = f.get("_SharesIssued") or r.get("shares")
        if px_f and shares:
            mcap, basis = px_f * shares, ("px*shares(filing)" if f.get("_SharesIssued")
                                          else "px*shares(yahoo)")
        else:
            mcap, basis = _to_fin_ccy(r.get("mcap_q"), qccy, fccy, fx), "yahoo mcap"
        if not mcap or mcap <= 0:
            post["no_mcap_post"] += 1
            continue
        mcap_usd = mcap * fx[fccy]

        v = VENUES[r["venue"]]
        urow = {"sym": r["sym"], "mktcap": mcap, "px": r["px"], "sec": r["sector"],
                "ind": (r.get("name") or "")[:44], "country": r["country"]}
        m = S.compute_metrics(urow, f)                  # the shared composite's metric builder
        m["foreign"], m["adr"] = True, False

        # ---- (f) trust / client-cash guard (the OTB.L catch) ------------------------
        m["trust_cash_suspect"] = bool(TRUST_INDUSTRY.search(ind)
                                       or TRUST_NAME.search(r.get("name") or ""))
        m["am_asis"], m["ncash_r_asis"], m["am_trustsafe"] = m["am"], m["ncash_r"], None
        if m["trust_cash_suspect"]:
            ev_ts = mcap + m["debt"] + m["mi"]          # cash NOT netted — float may be customers'
            m["ev_trustsafe"] = ev_ts
            m["am_trustsafe"] = (ev_ts / m["ebit"]) if (m["ebit"] and m["ebit"] > 0 and ev_ts > 0) else None
            m["am"], m["subcash"] = m["am_trustsafe"], False
            m["ncash_r"] = min(0.0, m["ncash_r"]) if m["ncash_r"] is not None else None

        # ---- venue / tax / execution columns ---------------------------------------
        m["venue"], m["market"] = r["venue"], v["mkt"]
        m["ibkr"], m["wht"] = v["ibkr"], v["wht"]
        m["ccy"], m["px_ccy"] = fccy, qccy
        m["ccy_mismatch"] = fccy != qccy               # (b) the EQNR/ABI/AZN class
        m["mcap_usd"], m["mcap_basis"] = mcap_usd, basis
        m["fr_ftt_likely"] = (r["venue"] == "PAR" and mcap_usd > 1.15e9)   # PROXY, not the list
        # ---- (c) float + ADV -------------------------------------------------------
        m["adv_usd"] = round(r["_adv_usd"])
        m["thin"] = r["_adv_usd"] < 3e5
        flt, sh = f.get("_float"), (f.get("_SharesIssued") or r.get("shares"))
        m["float_shares"], m["float_pct"] = flt, (round(flt / sh, 3) if (flt and sh) else None)
        m["float_unknown"] = m["float_pct"] is None
        m["float_usd"] = round(m["float_pct"] * mcap_usd) if m["float_pct"] else None
        if m["float_pct"] is not None and m["float_pct"] < min_float:
            post["float_floor"] += 1
            continue
        # ---- coverage-economics instrument (the meta-thesis) ------------------------
        m["n_analysts"] = f.get("_n_analysts")
        m["orphan"] = (m["n_analysts"] or 0) <= 1
        # ---- (a) consolidation + vintage -------------------------------------------
        m["consol_unverified"] = not f.get("_consol_verified")
        m["ttm"] = bool(f.get("_ttm"))
        m["bs_date"], m["flow_date"] = f.get("_bs_date"), f.get("_flow_date")
        try:
            m["flow_months"] = round((now - time.mktime(time.strptime(
                m["flow_date"], "%Y-%m-%d"))) / (30.44 * 86400))
        except (TypeError, ValueError):
            m["flow_months"] = None
        m["fy_stale"] = bool(m["flow_months"] and m["flow_months"] > 15)
        m["ebit_derived"] = bool(f.get("_ebit_derived"))
        m["ebit_reported"] = f.get("_ebit_reported")
        m["unusual_r"] = (round(f["_unusual"] / m["ebit"], 3)
                          if (f.get("_unusual") and m.get("ebit")) else None)
        m["lease_debt"] = f.get("_lease_debt")
        m["industry"] = ind

        # ---- EARNINGS-DURABILITY GUARD (the Cantargia / Galapagos catch) ---------------
        # score.py's one-time-gain guard reads an UNUSUAL-ITEMS tag, and Yahoo's normalized
        # operating income has already stripped those — so a windfall that arrives as
        # REVENUE (licensing upfront, milestone, asset sale, lumpy project completion)
        # sails through both and lands at the TOP of a cheapness ranking, because a single
        # year of windfall EBIT against a collapsed market cap is arithmetically identical
        # to a bargain. The prior year is what exposes it.
        rh, eh = (f.get("_rev_hist") or []), (f.get("_ebit_hist") or [])
        rev_prior = rh[1] if len(rh) > 1 else None
        ebit_prior = eh[1] if len(eh) > 1 else None
        cur_rev, cur_ebit, cur_fcf = m.get("rev"), m.get("ebit"), m.get("fcf")
        why = []
        # 1. revenue appears from nothing, or triples — the licensing-upfront shape
        if cur_rev and cur_rev > 0 and rev_prior is not None:
            if rev_prior <= 0.02 * abs(cur_rev):
                why.append(f"revenue from ~0 to {cur_rev/1e6:.0f}M in one year")
            elif cur_rev >= 3 * rev_prior > 0:
                why.append(f"revenue {cur_rev/max(rev_prior,1):.1f}x prior year")
        # 2. EBIT just flipped from a loss — earnings not yet demonstrated as durable
        if cur_ebit and cur_ebit > 0 and ebit_prior is not None and ebit_prior < 0:
            why.append(f"EBIT flipped {ebit_prior/1e6:.0f}M -> {cur_ebit/1e6:.0f}M")
        # 3. accrual gap: profit on paper, cash going the other way (the mirror of wc_fcf —
        #    LKFT/Galapagos-shape: EBIT +596M on operating cash flow -302M)
        if cur_ebit and cur_ebit > 0 and cur_fcf is not None and cur_fcf < 0:
            why.append(f"EBIT +{cur_ebit/1e6:.0f}M but FCF {cur_fcf/1e6:.0f}M")
        m["durability_why"] = "; ".join(why) or None
        m["durability_suspect"] = bool(why)

        # ---- MELTING ICE CUBE: the composite is a SNAPSHOT and rewards a collapsing
        # multiple exactly as much as a cheap one. A business whose EBIT is a third of what
        # it earned three years ago is not cheap, it is shrinking — and this pond is full of
        # them (Catena Media EBIT 37 -> 6.8 EUR M over four years while the multiple "improved"
        # to 1.4x). Informational, NOT a demotion: a trough multiple on a cyclical is a buy
        # and on a structural decliner is a trap, and only a human can tell them apart.
        eh_v = [v for v in eh if v is not None]
        m["ebit_oldest"] = eh_v[-1] if len(eh_v) >= 2 else None
        m["ebit_trend"] = (round(cur_ebit / eh_v[-1], 2)
                           if (cur_ebit and len(eh_v) >= 2 and eh_v[-1] and eh_v[-1] > 0) else None)
        m["melting"] = bool(m["ebit_trend"] is not None and m["ebit_trend"] < 0.5)
        m["px_stale"] = bool(r.get("px_ts") and (now - r["px_ts"]) > PX_STALE_DAYS * 86400)
        recs.append(m)
    print("post-filter drops: " + ", ".join(f"{k}={v}" for k, v in post.most_common()))
    print(f"scored population: {len(recs)}")

    # COVERAGE HONESTY: which venues did the fundamentals pull actually reach? A throttled
    # pull looks identical to a complete one in the printed table — the only tell is that a
    # venue's candidate count and its scored count diverge. Report it per venue, always.
    cand_by_ven = Counter(r["venue"] for r in pre)
    got_by_ven = Counter(r["venue"] for r in pre if (funds.get(r["sym"]) or {}).get("Assets"))
    coverage = {v: {"candidates": cand_by_ven[v], "with_fundamentals": got_by_ven[v],
                    "pct": round(100 * got_by_ven[v] / cand_by_ven[v]) if cand_by_ven[v] else None}
                for v in sorted(cand_by_ven)}
    missing = sum(cand_by_ven.values()) - sum(got_by_ven.values())
    pull_complete = missing == 0
    print("fundamentals coverage by venue: " +
          ", ".join(f"{v} {c['with_fundamentals']}/{c['candidates']}" for v, c in coverage.items()))
    worst = min((c["pct"] for c in coverage.values() if c["pct"] is not None), default=100)
    if missing and (missing > 0.02 * sum(cand_by_ven.values()) or worst < 90):
        print(f"  !! PARTIAL PULL — {missing} candidates have no fundamentals and the worst "
              f"venue is at {worst}%. The shelf UNDER-COVERS those venues; re-run to resume "
              f"(the cache is preserved).")
    elif missing:
        print(f"  ({missing} name(s) have no fundamentals at Yahoo after {MAX_FAILS} tries — "
              f"immaterial at this scale, but they are absent from the shelf, not cheap-free)")

    # ---- (b) PLANE CHECK: a 100x currency error blows the venue median P/B apart ----
    plane_fail = []
    for ven in sorted({r["venue"] for r in recs}):
        pbs = sorted(x["pb"] for x in recs if x["venue"] == ven and x.get("pb"))
        if len(pbs) < 5:
            continue
        med = pbs[len(pbs) // 2]
        ok = 0.05 < med < 50
        print(f"  plane check {ven}: median P/B {med:.2f} on n={len(pbs)} "
              f"{'OK' if ok else '*** FAIL ***'}")
        if not ok:
            plane_fail.append(ven)
    if plane_fail:
        raise SystemExit(f"CURRENCY-PLANE FAILURE on {plane_fail} — refusing to emit a shelf")

    scored = S.composite(recs)
    shelf = S.clean_shortlist(scored, exclude_adr=False)

    # Durability-suspect names are DEMOTED from the printed table but kept (flagged) in the
    # JSON — the ESEF leg's scale_suspect precedent. They are not necessarily bad businesses;
    # they are names whose CHEAPNESS is an artifact of one year's numbers, so they must not
    # be presented as ranked bargains without a human reading the prior year.
    n_dur = sum(1 for r in shelf if r.get("durability_suspect"))
    printable = [r for r in shelf if not r.get("durability_suspect")]

    # ---- IBKR conids, merged from the out-of-band MCP resolution -------------------
    conids = json.load(open(CONIDS)) if os.path.exists(CONIDS) else {}
    for r in shelf:
        c = conids.get(r["sym"]) or {}
        r["conid"] = c.get("conid")
        r["ibkr_symbol"] = c.get("ibkr_symbol")
        r["ibkr_exchange"] = c.get("exchange") or r["ibkr"]
        r["ibkr_verified_utc"] = c.get("verified_utc")

    keep = ("sym", "ind", "industry", "sec", "country", "venue", "market", "ccy", "px_ccy",
            "ccy_mismatch", "mktcap", "mcap_usd", "mcap_basis", "px", "score", "nmetrics",
            "am", "am_asis", "am_trustsafe", "trust_cash_suspect", "fcfy", "pb", "ncash_r",
            "ncash_r_asis", "ncav_r", "ev", "ebit", "ebit_reported", "ebit_derived",
            "unusual_r", "fcf", "rev", "cash", "debt", "lease_debt", "mi", "eq", "netcash",
            "subcash", "holdco", "neg_equity", "wc_fcf", "mlp_artifact", "consol_unverified",
            "n_analysts", "orphan", "adv_usd", "thin", "float_pct", "float_usd",
            "float_unknown", "durability_suspect", "durability_why",
            "melting", "ebit_trend", "ebit_oldest",
            "wht", "fr_ftt_likely", "ibkr", "ibkr_exchange", "ibkr_symbol",
            "conid", "ibkr_verified_utc", "ttm", "bs_date", "flow_date", "flow_months",
            "fy_stale", "px_stale")

    os.makedirs(DATA, exist_ok=True)
    meta = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "module": "verticals/generators/euronext_shelf.py",
        "thesis": "coverage-economics arbitrage — post-MiFID-II research desert, "
                  "Euronext (PAR/AMS/BRU/LIS/OSL) + Nasdaq Nordic (HEL/STO/CPH)",
        "source": "Yahoo screener + Yahoo fundamentals — SECONDARY; re-derive from the "
                  "primary filing before any court",
        "universe_generated_utc": uni["meta"]["generated_utc"],
        "universe_lines": len(rows),
        "fx_basis": fx_basis, "fx": {k: round(v, 5) for k, v in fx.items()},
        "filters": {"min_mcap_usd": min_mcap_usd, "max_mcap_usd": max_mcap_usd,
                    "min_adv_usd": min_adv_usd, "min_float": min_float},
        "prefilter_drops": dict(drop), "postfilter_drops": dict(post),
        "scored": len(recs), "shelf": len(shelf),
        "pull_complete": pull_complete,
        "fundamentals_coverage_by_venue": coverage,
        "candidates_without_fundamentals": missing,
        "scored_by_venue": dict(Counter(r["venue"] for r in recs)),
        "shelf_by_venue": dict(Counter(r["venue"] for r in shelf)),
        "orphans_on_shelf": sum(1 for r in shelf if r["orphan"]),
        "durability_suspect_demoted": n_dur,
        "melting_on_shelf": sum(1 for r in shelf if r.get("melting")),
        "ccy_mismatch_on_shelf": sum(1 for r in shelf if r["ccy_mismatch"]),
        "conids_merged": sum(1 for r in shelf if r.get("conid")),
        "rerun": "python3 euronext_shelf.py --top 30   "
                 "(--refresh-universe monthly; --refresh-fund to re-pull financials)",
        "known_limitations": "see module docstring README",
    }
    json.dump({"meta": meta, "rows": [{k: r.get(k) for k in keep} for r in shelf]},
              open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"\nwrote {OUT}  ({len(shelf)} scored rows)")

    def fmt(r):
        am = f"{r['am']:.1f}" if r["am"] else ("subC" if r["subcash"] else " -")
        fy = f"{r['fcfy']*100:.0f}%" if r["fcfy"] is not None else " -"
        pb = f"{r['pb']:.2f}" if r["pb"] else " -"
        nc = f"{r['ncash_r']:.2f}" if r["ncash_r"] is not None else " -"
        nv = f"{r['ncav_r']:.2f}" if r["ncav_r"] is not None else " -"
        na = str(r["n_analysts"]) if r["n_analysts"] is not None else "-"
        fl = " ".join(t for t, on in [
            ("orphan", r["orphan"]), ("thin", r["thin"]), ("fx!", r["ccy_mismatch"]),
            (f"melting{r['ebit_trend']:.1f}x" if r.get("ebit_trend") is not None else "melting",
             r.get("melting")),
            ("float?", r["float_unknown"]), ("cust-cash?", r["trust_cash_suspect"]),
            ("ebit~", r["ebit_derived"]), ("WC-FCF", r["wc_fcf"]), ("holdco", r["holdco"]),
            ("neg-eq", r["neg_equity"]), ("no-NCI", r["consol_unverified"]),
            ("FTT", r["fr_ftt_likely"]), ("stale-FY", r["fy_stale"]),
            ("conid", bool(r.get("conid")))] if on)
        return (f"  {r['sym']:12s}{r['venue']:4s}{r['mcap_usd']/1e6:7.0f}{r['adv_usd']/1e3:7.0f}"
                f" {am:>6s}{fy:>6s}{pb:>6s}{nc:>7s}{nv:>6s}{na:>3s} {r['ccy']:4s}"
                f"{r['wht']:>5s} {r['ind'][:26]:26s} {fl}")

    print(f"\nEURONEXT / NORDIC DEEP-VALUE SHELF  n={len(shelf)}  "
          f"orphans(<=1 analyst)={meta['orphans_on_shelf']}  "
          f"ccy-mismatch={meta['ccy_mismatch_on_shelf']}  "
          f"durability-demoted={n_dur}")
    print(f"  {'tkr':12s}{'ven':4s}{'mc$M':>7s}{'ADV$k':>7s}{'EV/EBT':>6s}{'FCFy':>6s}"
          f"{'P/B':>6s}{'ncash/m':>7s}{'NCAV/m':>6s}{'an':>3s} {'ccy':4s}{'WHT':>5s}"
          f" {'name':26s} flags")
    for r in printable[:top]:
        print(fmt(r))
    print("\n  (mc/ADV in USD; every RATIO computed in the reporting ccy — 'fx!' = quote ccy "
          "differs from reporting ccy; WHT 'r' = treaty-reclaimable with friction; "
          "EV carries IFRS-16 lease debt)")
    return shelf


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("====")[0])
    ap.add_argument("--refresh-universe", action="store_true",
                    help="re-sweep the Yahoo screener and rewrite the static universe file")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--min-mcap-usd", type=float, default=2.5e7)
    ap.add_argument("--max-mcap-usd", type=float, default=3e9)
    ap.add_argument("--min-adv-usd", type=float, default=75e3)
    ap.add_argument("--min-float", type=float, default=0.15)
    ap.add_argument("--refresh-fund", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=None,
                    help="cap the fundamentals pull to the N most liquid candidates (dev)")
    a = ap.parse_args()
    if a.refresh_universe:
        refresh_universe()
    run(a.top, a.min_mcap_usd, a.max_mcap_usd, a.min_adv_usd, a.min_float,
        a.refresh_fund, a.workers, a.limit)
