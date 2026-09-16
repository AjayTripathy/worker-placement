"""screen_korea — Korea leg of the global value screen: DART store -> same composite +
guards as the US screen (score.py is imported and reused, not reimplemented), plus the
Korea-specific columns.

  python3 screen_korea.py [--top N] [--min-mcap 4e10] [--max-mcap 5e12] [--refresh-px]

Universe = data/dart_store.json (dart_fundamentals bulk build: FY2025 annual, Dec-YE dominant,
consolidated preferred) joined to Yahoo quotes for price/mcap. Everything stays NATIVE KRW —
the composite is ratio-only; the single FX bridge is the display of mcap in $M (static
screening rate; name the metric, never conflate — the TEY lesson).

PRICES: Yahoo v7 bulk quote via yfinance's authed session (marketCap + regularMarketPrice +
regularMarketTime in ONE request per ~200-name chunk — no per-name fast_info rate-limit).
The Korean yfinance feed can lag by DAYS (the krx_value_watch warning), so every quote's OWN
market timestamp is stored and a stale quote is FLAGGED, never silently treated as fresh.
mcap is Yahoo marketCap = COMMON shares only; issuers with preferred lines understate EV by
the pref float (see pref column). In-session authoritative marks: IBKR/KRX cids
(krx_value_watch.py pattern).

Korea landmines encoded here:
  WHT     — dividends carry 22% Korean withholding (15.4% w/ US treaty via IBKR W-8BEN);
            yield-heavy names are structurally worth less to the taxable US buyer.
  SHELF   — ~60% of KOSPI trades below book: below-book alone is the MARKET, not a signal.
            The composite RANKS the whole shelf; thresholding on P/B would return half the
            exchange.
  NO-ACTOR— the Japan no-actor law's Korea analog: below book + NO value-up filing +
            controller >40% = likely PERPETUAL discount. The valueup column is the actor
            signal; controller % stays manual-DD (chaebol column).
  WON     — KRW quotes, single shares trade (no board-lot issue, unlike Japan's 100-lots).

Korea-specific columns (never silent exclusion):
  pfic / pfic_fmv_share — §1297 asset test on FMV basis from day one (the Japan lesson:
            (cash+ST-inv+LT-inv)/(mcap+liabilities); book basis under-flags the below-book
            shelf because cheapness and PFIC are the same phenomenon).
  valueup — KIND 기업가치 제고 계획 disclosure status (PLAN = filed plan / NOTICE = 예고
            advance notice), scraped from kind.krx.co.kr/valueup/disclsstat.do. Below-book
            WITH a filed plan = the catalyst cohort.
  pref    — issuer has listed preferred line(s) (5-digit base + 5/7/9 codes, the 우 suffix /
            Hyundai-pref plane): a cheaper same-cash-flow line may exist; also means Yahoo
            common-only mcap understates EV.
  chaebol — controller/cross-holding note: LEFT MANUAL (None). Resolve in per-name DD.
  fin_ksic— KSIC 649 non-bank holdco (LG/SK plane) — kept, flagged (banks/insurers/securities
            are excluded via the DART file split + KSIC codes below).
  fresh   — False for names already in desk research-ledger Korea sleeves (still scored).
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))                  # verticals/deep_value for score.py
import score as S                                           # noqa: E402  (the US composite, reused)
import pfic_screen as P                                     # noqa: E402
import dart_fundamentals as DF                              # noqa: E402

DATA = os.path.join(HERE, "data")
PX_CACHE = os.path.join(DATA, "korea_px_cache.json")
VU_CACHE = os.path.join(DATA, "korea_valueup.json")
SHORTLIST = os.path.join(DATA, "korea_shortlist.json")
LEDGER = os.path.join(HERE, "..", "..", "..", "desk", "data", "research_ledger.json")
KRW_USD = 0.00072                                          # static screening FX (display only)
PX_STALE_DAYS = 5

MKT_SUFFIX = {"유가증권시장상장법인": ".KS", "코스닥시장상장법인": ".KQ"}   # 기타법인/KONEX dropped
# banks/insurers/securities and their support codes — excluded like the US screen's carve-out.
# NOTE: the DART bulk file split already removes financial-FORMAT filers at source; this KSIC
# belt catches stragglers. 649 (non-bank holdcos: LG=649, SK=649) is KEPT and flagged.
FIN_KSIC = ("641", "642", "643", "65", "660", "661", "662")   # 661 ≈ the SPAC shells too
SPAC_PAT = re.compile(r"기업인수목적|스팩")


def ledger_korea_codes() -> set:
    """6-digit codes already in desk research-ledger Korea sleeves (COSMECCA/HUGEL/LG/SK...) —
    still scored, but not flagged 'fresh'."""
    try:
        names = json.load(open(LEDGER)).get("names", [])
    except Exception:
        return set()
    out = set()
    for n in names:
        for f in (n.get("ticker"), n.get("yf")):
            m = re.match(r"^(\d{6})(\.(KS|KQ))?$", str(f or ""))
            if m:
                out.add(m.group(1))
    return out


# ---------------------------------------------------------------- prices (Yahoo bulk quote)

def _yahoo_quotes(symbols: list[str]) -> dict:
    """One authed v7 quote call per ~200-symbol chunk via yfinance's session (crumb handled
    internally). Returns {sym: quote-dict}. Verified live for .KS/.KQ 2026-07-21."""
    from yfinance.data import YfData
    d = YfData()
    out = {}
    for i in range(0, len(symbols), 200):
        chunk = symbols[i:i + 200]
        try:
            r = d.get("https://query1.finance.yahoo.com/v7/finance/quote",
                      params={"symbols": ",".join(chunk)})
            for q in r.json().get("quoteResponse", {}).get("result", []):
                out[q["symbol"]] = q
        except Exception as ex:
            print(f"  quote chunk {i}: {type(ex).__name__} {str(ex)[:120]}")
        time.sleep(1.0)
    return out


def fetch_prices(tickers: list[str], refresh=False) -> dict:
    """{tkr: {px, mcap, shares, qt, ts}} — qt = the quote's OWN market timestamp (the
    days-lag warning: staleness is judged on qt, not on when we fetched)."""
    cache = json.load(open(PX_CACHE)) if os.path.exists(PX_CACHE) else {}
    now = time.time()
    todo = [t for t in tickers
            if refresh or t not in cache
            or (now - cache[t].get("ts", 0)) > 86400]      # refetch quotes older than a day
    if todo:
        print(f"bulk-quoting {len(todo)} names via Yahoo v7 (cached: {len(tickers)-len(todo)})")
        qs = _yahoo_quotes(todo)
        for t in todo:
            q = qs.get(t) or {}
            cache[t] = {"px": q.get("regularMarketPrice"), "mcap": q.get("marketCap"),
                        "shares": q.get("sharesOutstanding"), "qt": q.get("regularMarketTime"),
                        "ts": now, "mcap_basis": "yahoo marketCap (common shares only)"}
        json.dump(cache, open(PX_CACHE, "w"))
    return cache


def pref_lines(shortlist_codes: list[str], sfx: dict) -> dict:
    """Detect listed preferred lines (우/우B — base5 + 5/7/9 codes) for the shortlist only:
    one extra bulk-quote call, cached in the same px cache."""
    cands = {}
    for c in shortlist_codes:
        for last in ("5", "7", "9"):
            cands.setdefault(c, []).append(c[:5] + last + sfx.get(c, ".KS"))
    flat = [t for ts in cands.values() for t in ts]
    cache = json.load(open(PX_CACHE)) if os.path.exists(PX_CACHE) else {}
    todo = [t for t in flat if t not in cache]
    if todo:
        qs = _yahoo_quotes(todo)
        for t in todo:
            q = qs.get(t) or {}
            cache[t] = {"px": q.get("regularMarketPrice"), "mcap": q.get("marketCap"),
                        "qt": q.get("regularMarketTime"), "ts": time.time(), "pref_probe": True}
        json.dump(cache, open(PX_CACHE, "w"))
    out = {}
    for c, ts in cands.items():
        hits = [(t, cache.get(t, {}).get("px")) for t in ts if cache.get(t, {}).get("px")]
        if hits:
            out[c] = hits
    return out


# ---------------------------------------------------------------- value-up (KIND)

def fetch_valueup(refresh=False) -> dict:
    """기업가치 제고 계획 disclosure list from KIND (no auth) -> {code6: {status, date, name}}.
    status: PLAN (계획 filed) beats NOTICE (예고). Join key: KIND exposes the 5-digit issuer
    code (companysummary_open('24766')); common lines end in 0, so code6 = code5+'0' — name
    match is the fallback. Cached 3 days."""
    if os.path.exists(VU_CACHE) and not refresh \
            and time.time() - os.path.getmtime(VU_CACHE) < 3 * 86400:
        return json.load(open(VU_CACHE))
    url = "https://kind.krx.co.kr/valueup/disclsstat.do"
    body = ("method=valueupDisclsStatSub&forward=valueupDisclsStat_sub&searchCorpName="
            "&repIsuSrtCd=&allRepIsuSrtCd=&isurCd=&searchCodeType=&fromDate=&toDate="
            "&pageIndex=1&currentPageSize=5000")
    req = urllib.request.Request(url, data=body.encode(), headers={
        "User-Agent": DF.HDRS["User-Agent"], "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://kind.krx.co.kr/valueup/disclsstat.do?method=valueupDisclsStatMain",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    try:
        html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    except Exception as ex:
        print(f"  KIND value-up fetch failed ({ex}) — using stale cache if any")
        return json.load(open(VU_CACHE)) if os.path.exists(VU_CACHE) else {}
    rows = re.findall(
        r"companysummary_open\('(\d{5})'\);\s*return false;\"\s*title='([^']+)'.*?"
        r"openDisclsViewer\('(\d{8})\d*','[^']*'\)\"\s*title='([^']+)'", html, re.S)
    out = {}
    for code5, name, ymd, title in rows:
        code6 = code5 + "0"
        status = "NOTICE" if "예고" in title else "PLAN"
        date = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
        old = out.get(code6)
        # PLAN outranks NOTICE; newer date wins within a status
        if old is None or (status == "PLAN" and old["status"] == "NOTICE") \
                or (status == old["status"] and date > old["date"]):
            out[code6] = {"status": status, "date": date, "name": name}
    if out:
        json.dump(out, open(VU_CACHE, "w"), ensure_ascii=False, indent=1)
        print(f"KIND value-up disclosures: {len(rows)} rows -> {len(out)} issuers")
    return out


# ---------------------------------------------------------------- screen

def apply_korea_guards(r: dict, f: dict) -> dict:
    """Batch-2 net-cash attribution guards (screen_defects.jsonl 2026-08-06) — the Korean
    master-defect was four mechanisms making consolidated net-cash inadmissible. Each guard
    is golden-tested in tests/test_screen_jpkr_guards.py with the caught name as fixture.

    1. NCI-HEAVY (ITCen 031820: 129% net-cash -> 39% parent-attributable): when NCI >25% of
       total equity, consolidated cash cannot be attributed to the common — ncash_r=None.
    2. YEAR-END FLOAT (031820 again; Hancom 372910): fiscal-YE cash on SI/distribution/
       procurement names is seasonal float — if the INTERIM BS (already in the store) shows
       cash <75% of the annual figure, the annual net-cash is stale — None + flag.
    3. CONTRACT ADVANCES (372910: 선수금 > total cash): where tagged, subtract from net-cash.
    4. CB TRAIL (Hyunwoo 092300): convertible paper on the BS is both a debt line the code
       tier missed AND the KOSDAQ integrity tell — surface as a column, never silently."""
    g = f.get
    r["ncash_r_asis"] = r.get("ncash_r")
    mi, se = g("MinorityInterest"), g("StockholdersEquity")
    r["nci_heavy"] = bool(mi and se and mi / (se + mi) > 0.25)
    acash = g("CashAndCashEquivalentsAtCarryingValue")
    icash = (g("interim") or {}).get("CashAndCashEquivalentsAtCarryingValue")
    r["ncash_ye_float"] = bool(acash and icash is not None and icash < 0.75 * acash)
    if (r["nci_heavy"] or r["ncash_ye_float"]) and r.get("ncash_r") is not None:
        r["ncash_r"] = None                    # inadmissible, not adjustable — re-strike manually
    adv = g("_ContractAdvances")
    r["contract_adv_adj"] = False
    if adv and acash and adv > 0.3 * acash and r.get("ncash_r") is not None and r.get("mktcap"):
        r["ncash_r"] = r["ncash_r"] - adv / r["mktcap"]
        r["contract_adv_adj"] = True
    r["cb_on_bs"] = bool(g("_DebtCB") or g("_DebtCurSpecificCB"))
    return r


def run(top=30, min_mcap=4e10, max_mcap=5e12, refresh_px=False):
    store = DF.load_store()
    print(f"dart_store: {len(store)} issuers")
    ledger = ledger_korea_codes()
    vu = fetch_valueup()

    uni, n_spac, n_fin = [], 0, 0
    sfx_by_code = {}
    for code, f in store.items():
        sfx = MKT_SUFFIX.get(f.get("market"))
        if not sfx:
            continue                                        # 기타법인 / KONEX — not IBKR-routable
        if SPAC_PAT.search(f.get("name", "")):
            n_spac += 1
            continue
        ksic = f.get("ksic", "")
        if ksic[:3] in FIN_KSIC or ksic[:2] in FIN_KSIC:
            n_fin += 1
            continue
        sfx_by_code[code] = sfx
        uni.append({"code": code, "tkr": code + sfx, "name": f.get("name", "")[:40]})
    print(f"screenable universe (listed, ex-financials, ex-SPAC): {len(uni)} "
          f"(dropped {n_spac} SPACs, {n_fin} financial-KSIC)")

    px = fetch_prices([u["tkr"] for u in uni], refresh=refresh_px)
    now = time.time()
    recs, unpriced = [], 0
    for u in uni:
        p = px.get(u["tkr"]) or {}
        if not p.get("mcap") or not p.get("px"):
            unpriced += 1
            continue
        if not (min_mcap < p["mcap"] < max_mcap):
            continue
        f = store[u["code"]]
        urow = {"sym": u["tkr"], "mktcap": float(p["mcap"]), "px": p["px"],
                "sec": f.get("ksic_nm", "")[:24], "ind": u["name"], "country": "Korea"}
        r = S.compute_metrics(urow, f)                     # the US composite's metric builder
        apply_korea_guards(r, f)                           # batch-2 net-cash attribution guards
        r["foreign"] = True
        r["adr"] = False                                   # local KRX line, not an ADR wrapper
        r["consol"] = f.get("_consol", False)
        r["period_end"] = f.get("period_end")
        r["interim_asof"] = (f.get("interim") or {}).get("period_end")
        r["fin_ksic"] = f.get("ksic", "")[:3] == "649"     # non-bank holdco (LG/SK plane)
        r["px_stale"] = ((now - p["qt"]) > PX_STALE_DAYS * 86400) if p.get("qt") else True
        r["px_asof"] = time.strftime("%Y-%m-%d", time.localtime(p["qt"])) if p.get("qt") else None
        v = vu.get(u["code"])
        r["valueup"] = f"{v['status']} {v['date']}" if v else None
        r["chaebol"] = None                                # controller/cross-holding: manual DD
        r["fresh"] = u["code"] not in ledger
        r["src"] = f.get("src")
        pf = P.pfic_risk(r, f)
        r["pfic"] = pf["pfic"]
        r["pfic_why"] = pf["reason"]
        # FMV-basis PFIC overlay from day one (the Japan lesson): for a PUBLIC name the §1297
        # asset test runs on FMV — denominator ≈ mktcap + liabilities, NOT book assets. The
        # below-book shelf under-flags on book basis because the discount shrinks the FMV
        # denominator: cheapness and PFIC are the same phenomenon.
        _cash = (f.get("CashAndCashEquivalentsAtCarryingValue") or 0) + (f.get("ShortTermInvestments") or 0)
        # LT passive = narrow securities + the over-capture umbrella (the 079960 fix: ₩97bn of
        # 장기투자증권 under EquityInstrumentsHeld was invisible to the original narrow map)
        _lti = (f.get("LongTermInvestments") or 0) + (f.get("OtherLongTermInvestments") or 0)
        _fmv = r["mktcap"] + (f.get("Liabilities") or 0)
        if _fmv > 0:
            share = (_cash + _lti) / _fmv
            r["pfic_fmv_share"] = round(share, 3)
            if share >= 0.5 and not r["pfic"]:
                r["pfic"] = True
                r["pfic_why"] = (f"FMV-basis passive {share*100:.0f}% >= 50% "
                                 f"(book-basis passed: {r['pfic_why']})")
        recs.append(r)
    print(f"priced + in-band ₩{min_mcap/1e9:.0f}B..₩{max_mcap/1e12:.1f}T: {len(recs)} "
          f"(unpriced/no-Yahoo-quote: {unpriced})")

    scored = S.composite(recs)
    shortlist = S.clean_shortlist(scored, exclude_adr=False)

    # preferred-line probe for the saved shortlist only (one extra bulk-quote call)
    prefs = pref_lines([r["sym"][:6] for r in shortlist[:120]], sfx_by_code)
    for r in shortlist[:120]:
        hit = prefs.get(r["sym"][:6])
        r["pref"] = ", ".join(f"{t} ₩{p:,.0f}" for t, p in hit) if hit else None

    os.makedirs(DATA, exist_ok=True)
    keep = ("sym", "ind", "sec", "mktcap", "px", "px_asof", "score", "am", "fcfy", "pb",
            "ncash_r", "ncash_r_asis", "nci_heavy", "ncash_ye_float", "contract_adv_adj",
            "cb_on_bs", "ncav_r", "ebit", "fcf", "subcash", "holdco", "neg_equity", "wc_fcf",
            "pfic", "pfic_why", "pfic_fmv_share", "valueup", "pref", "chaebol", "fin_ksic",
            "consol", "px_stale", "fresh", "period_end", "interim_asof", "src", "nmetrics")
    json.dump([{k: r.get(k) for k in keep} for r in shortlist[:120]],
              open(SHORTLIST, "w"), ensure_ascii=False, indent=1)
    # auto-court conveyor (2026-08-06): clean fresh candidates -> TRAP_VERIFY queue (idempotent)
    try:
        import os as _os, sys as _sys
        _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(
            _os.path.dirname(_os.path.abspath(__file__))))))
        from desk.court_queue import enqueue_candidates
        cand = [r for r in shortlist
                if not r.get("pfic") and not r.get("pref") and not r.get("px_stale")][:15]
        c = enqueue_candidates([{**r, "ticker": r["sym"]} for r in cand],
                               source=f"screen_korea/{time.strftime('%Y-%m-%d')}")
        print(f"court_queue: {c['added']} new candidates enqueued")
    except Exception as e:
        print(f"court_queue enqueue failed (screen output unaffected): {type(e).__name__}: {e}")

    def fmt(r):
        am = f"{r['am']:.1f}" if r["am"] else ("sub₩" if r["subcash"] else " -")
        fy = f"{r['fcfy']*100:.0f}%" if r["fcfy"] is not None else " -"
        pb = f"{r['pb']:.2f}" if r["pb"] else " -"
        nc = f"{r['ncash_r']:.2f}" if r["ncash_r"] is not None else " -"
        nv = f"{r['ncav_r']:.2f}" if r["ncav_r"] is not None else " -"
        vu_s = {"PLAN": "VU-PLAN", "NOTICE": "VU-note"}.get((r["valueup"] or "").split(" ")[0], "")
        fl = " ".join(t for t, on in [
            ("PFIC", bool(r["pfic"])), (vu_s, bool(vu_s)), ("pref", bool(r.get("pref"))),
            ("WC-FCF", r["wc_fcf"]), ("holdco", r["holdco"]), ("649", r["fin_ksic"]),
            ("neg-eq", r["neg_equity"]), ("solo", not r["consol"]),
            ("stale-px", r["px_stale"]), ("known", not r["fresh"])] if on)
        return (f"  {r['sym']:10s}{r['mktcap']/1e9:8.0f} {am:>6s}{fy:>6s}{pb:>6s}{nc:>7s}{nv:>6s}"
                f"  {r['sec'][:14]:14s} {r['ind'][:18]:18s} {fl}")

    npfic = sum(1 for r in shortlist if r["pfic"])
    nvu = sum(1 for r in shortlist if r["valueup"])
    print(f"\nKOREA DEEP-VALUE SHORTLIST (FY2025 annual bulk, ex-financials/ex-SPAC/ex-burners)"
          f"  n={len(shortlist)}  PFIC-flagged={npfic} ({npfic/max(len(shortlist),1)*100:.0f}%)"
          f"  value-up filers={nvu}")
    print(f"  {'tkr':10s}{'mc₩B':>8s}{'EV/EBIT':>6s}{'FCFy':>6s}{'P/B':>6s}{'ncash/m':>7s}{'NCAV/m':>6s}"
          f"  {'sector':14s} {'name':18s} flags")
    for r in shortlist[:top]:
        print(fmt(r))
    print(f"\n  (mc₩B x {KRW_USD*1e3:.2f} = $M approx; single shares trade — no board lots;"
          f" dividends: 22% WHT, 15.4% w/ treaty)")
    print("  ~60% of KOSPI is below book — the rank is the signal, not the below-book fact;")
    print("  below-book + NO valueup + controller>40% (chaebol col = manual DD) = likely perpetual discount.")
    return shortlist


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--min-mcap", type=float, default=4e10)
    ap.add_argument("--max-mcap", type=float, default=5e12)
    ap.add_argument("--refresh-px", action="store_true")
    a = ap.parse_args()
    run(a.top, a.min_mcap, a.max_mcap, a.refresh_px)
