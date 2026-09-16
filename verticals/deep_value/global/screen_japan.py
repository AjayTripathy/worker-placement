"""screen_japan — Japan leg of the global value screen: EDINET store -> same composite +
guards as the US screen (score.py is imported and reused, not reimplemented), plus the
Japan-specific columns.

  python3 screen_japan.py [--top N] [--min-mcap 3e9] [--max-mcap 4e11] [--refresh-px]

Universe = the crawled edinet_store joined to the EDINET code list (industry / listing) and
to yfinance ``<code>.T`` prices for mcap. Everything stays in NATIVE JPY — the composite is
ratio-only; the single FX bridge is the display of mcap in $M (static screening rate, same
table ifrs_fundamentals uses; name the metric, never conflate — the TEY lesson).

Japan-specific columns (never silent exclusion):
  PFIC   — pfic_screen.pfic_risk proxy. The Japan value shelf is cash-heavy; a large slice
           of net-nets fails the §1297 asset test. A COLUMN for the taxable US buyer.
  IFRS   — accounting standard. JP-GAAP puts 特別利益 below EBIT (one-time-gain guard is
           structurally satisfied); IFRS filers keep the exposure, so they carry the flag.
  lot¥k  — Japan trades in 100-share board lots; min ticket = 100 x price (position sizing
           floor for the small book).
  TSE improvement-plan status (below-book cohort): TODO — JPX publishes the monthly
  「資本コストや株価を意識した経営」 disclosure list (English xlsx) at
  https://www.jpx.co.jp/english/equities/follow-up/index.html ; join on securities code
  when we automate it. Left None here — deriving it cheaply needs that one file, nothing else.
"""
from __future__ import annotations
import argparse, json, os, sys, time, zipfile, io, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))                 # verticals/deep_value for score.py
import score as S                                          # noqa: E402  (the US composite, reused)
import pfic_screen as P                                    # noqa: E402
import edinet_fundamentals as EF                           # noqa: E402

DATA = os.path.join(HERE, "data")
PX_CACHE = os.path.join(DATA, "japan_px_cache.json")
SHORTLIST = os.path.join(DATA, "japan_shortlist.json")
CODELIST = os.path.join(DATA, "Edinetcode.zip")
JPY_USD = 0.0064                                          # static screening FX (display only)
PX_STALE_DAYS = 7

# TSE 33-industry names we exclude (mirror of the US screen's Finance/Real Estate carve-out)
FINANCIAL_INDUSTRIES = {"銀行業", "保険業", "証券、商品先物取引業", "その他金融業", "不動産業"}
IND_EN = {"水産・農林業": "Fishery/Agri", "鉱業": "Mining", "建設業": "Construction",
          "食料品": "Foods", "繊維製品": "Textiles", "パルプ・紙": "Pulp/Paper",
          "化学": "Chemicals", "医薬品": "Pharma", "石油・石炭製品": "Oil/Coal",
          "ゴム製品": "Rubber", "ガラス・土石製品": "Glass/Ceramics", "鉄鋼": "Steel",
          "非鉄金属": "Nonferrous", "金属製品": "Metal Prods", "機械": "Machinery",
          "電気機器": "Electric Appl", "輸送用機器": "Transport Eq", "精密機器": "Precision",
          "その他製品": "Other Prods", "電気・ガス業": "Utilities", "陸運業": "Land Transp",
          "海運業": "Marine Transp", "空運業": "Air Transp", "倉庫・運輸関連業": "Warehousing",
          "情報・通信業": "Info/Comm", "卸売業": "Wholesale", "小売業": "Retail",
          "サービス業": "Services"}


def load_codelist() -> dict:
    """EDINET code -> {sec_code, industry, listed} from the public code-list CSV."""
    z = zipfile.ZipFile(CODELIST)
    txt = z.read(z.namelist()[0]).decode("cp932", errors="replace")
    lines = txt.splitlines()
    rows = list(csv.reader(io.StringIO("\n".join(lines[1:]))))   # line 0 = download banner
    hdr = rows[0]
    ix = {k: hdr.index(k) for k in ("ＥＤＩＮＥＴコード", "上場区分", "提出者業種", "証券コード", "提出者名（英字）")}
    out = {}
    for r in rows[1:]:
        if len(r) <= max(ix.values()):
            continue
        out[r[ix["ＥＤＩＮＥＴコード"]]] = {
            "sec_code": r[ix["証券コード"]].strip(), "listed": r[ix["上場区分"]] == "上場",
            "industry": r[ix["提出者業種"]].strip(), "name_en": r[ix["提出者名（英字）"]].strip()}
    return out


def fetch_prices(tickers: list[str], shares: dict, refresh=False) -> dict:
    """Latest closes via BULK yf.download (one request per ~150-name chunk), mcap = close x
    issued shares from the filing itself. Per-name fast_info rate-limited to ~40 names per
    4 min at universe scale — bulk closes don't. Shares include treasury stock, so mcap is
    slightly OVERstated = conservative for a cheapness screen. Cached hard; a stale price is
    FLAGGED downstream, never silently reused as fresh."""
    cache = json.load(open(PX_CACHE)) if os.path.exists(PX_CACHE) else {}
    now = time.time()
    todo = [t for t in tickers
            if refresh or t not in cache or not cache[t].get("px")
            or (now - cache[t].get("ts", 0)) > PX_STALE_DAYS * 86400]
    if todo:
        import yfinance as yf
        print(f"bulk-fetching {len(todo)} closes via yfinance (cached: {len(tickers)-len(todo)})")
        for i in range(0, len(todo), 150):
            chunk = todo[i:i + 150]
            try:
                df = yf.download(chunk, period="5d", interval="1d", progress=False,
                                 auto_adjust=False, threads=True)["Close"]
                for t in chunk:
                    try:
                        s = df[t].dropna() if len(chunk) > 1 else df.dropna()
                        px = float(s.iloc[-1]) if len(s) else None
                    except Exception:
                        px = None
                    sh = shares.get(t)
                    cache[t] = {"px": px, "mcap": (px * sh if px and sh else None),
                                "ts": now, "mcap_basis": "close x issued-shares(filing)"}
            except Exception as ex:
                print(f"  chunk {i} failed: {ex}")
            json.dump(cache, open(PX_CACHE, "w"))
            time.sleep(2)
    json.dump(cache, open(PX_CACHE, "w"))
    return cache


def apply_japan_guards(r: dict, f: dict, yq_mcap=None) -> dict:
    """Batch-2 guards (screen_defects.jsonl 2026-08-06); golden-tested with the caught names.
    1. MCAP CROSS-CHECK (5 of 8 batch-2 mcaps materially wrong — treasury/stale counts):
       filing-shares mcap vs Yahoo marketCap; >15% divergence -> take the LARGER (bias
       against fake cheapness), flag mcap_suspect, and NULL the mcap-derived ratios so the
       wrong number never ranks. Re-strike happens at trap-verification, not silently here.
    2. FCF-NO-CAPEX (6626: FCFy '12%' printed off CFO alone): capex missing on an
       industrial -> fcfy=None, never CFO-as-FCF.
    3. CONTRACT LIABILITIES (7122: 'net cash 105%' was customer advances): where tagged,
       subtract from net-cash; >30% of cash -> flag."""
    r["mcap_suspect"] = False
    if yq_mcap and r.get("mktcap"):
        div = abs(r["mktcap"] / yq_mcap - 1)
        if div > 0.15:
            r["mcap_suspect"] = True
            r["mcap_yahoo"] = yq_mcap
            r["mktcap"] = max(r["mktcap"], yq_mcap)
            for k in ("am", "pb", "ncash_r", "ncav_r", "fcfy"):
                r[f"{k}_asis"] = r.get(k)
                r[k] = None                    # a ratio on a disputed denominator never ranks
    r["fcf_no_capex"] = False
    if f.get("PaymentsToAcquirePropertyPlantAndEquipment") is None and r.get("fcfy") is not None:
        r["fcfy_asis"] = r.get("fcfy")
        r["fcfy"] = None
        r["fcf_no_capex"] = True
    cl = f.get("_ContractLiabilities")
    cash = f.get("CashAndCashEquivalentsAtCarryingValue")
    r["contract_liab_adj"] = False
    if cl and cash and cl > 0.3 * cash and r.get("ncash_r") is not None and r.get("mktcap"):
        r["ncash_r_asis"] = r.get("ncash_r")
        r["ncash_r"] = r["ncash_r"] - cl / r["mktcap"]
        r["contract_liab_adj"] = True
    return r


def _yahoo_mcaps(tickers: list[str]) -> dict:
    """Yahoo v7 bulk-quote marketCap for the cross-check — one call per ~150 names (the
    screen_korea transport; per-name fast_info would rate-limit at universe scale)."""
    try:
        from screen_korea import _yahoo_quotes
        qs = _yahoo_quotes(tickers)
        return {t: (qs.get(t) or {}).get("marketCap") for t in tickers}
    except Exception as e:
        print(f"  [mcap cross-check unavailable: {type(e).__name__}: {e} — "
              f"mcap_suspect not evaluated this run]")
        return {}


def run(top=30, min_mcap=3e9, max_mcap=4e11, refresh_px=False):
    store = EF.load_store()
    codes = load_codelist()
    print(f"edinet_store: {len(store)} issuers | codelist: {len(codes)}")

    # universe join: listed, has securities code, ex-financials (US screen's carve-out)
    uni = []
    for ec, f in store.items():
        cl = codes.get(ec, {})
        sec5 = (f.get("sec_code") or cl.get("sec_code") or "").strip()
        if not sec5 or not cl.get("listed", True):
            continue
        ind = cl.get("industry", "")
        if ind in FINANCIAL_INDUSTRIES:
            continue
        uni.append({"edinet": ec, "tkr": sec5[:4] + ".T", "ind_ja": ind,
                    "name": (f.get("name_en") or cl.get("name_en") or f.get("name_ja") or "")[:40]})
    print(f"screenable universe (listed, ex-financials): {len(uni)}")

    shares = {u["tkr"]: store[u["edinet"]].get("_SharesIssued") for u in uni}
    n_sh = sum(1 for v in shares.values() if v)
    print(f"share counts from filings: {n_sh}/{len(uni)}")
    px = fetch_prices([u["tkr"] for u in uni], shares, refresh=refresh_px)
    yq = _yahoo_mcaps([u["tkr"] for u in uni])
    now = time.time()
    recs = []
    for u in uni:
        p = px.get(u["tkr"]) or {}
        # mcap recomputed here (not trusted from cache) so a store rebuild — e.g. a share-count
        # fix — repriced everything without a refetch; fast_info-era cache mcap is the fallback
        mcap = (p["px"] * shares[u["tkr"]]) if (p.get("px") and shares.get(u["tkr"])) \
            else p.get("mcap")
        p = {**p, "mcap": mcap}
        if not p.get("mcap") or not (min_mcap < p["mcap"] < max_mcap):
            continue
        f = store[u["edinet"]]
        urow = {"sym": u["tkr"], "mktcap": p["mcap"], "px": p["px"],
                "sec": IND_EN.get(u["ind_ja"], u["ind_ja"]), "ind": u["name"],
                "country": "Japan"}
        r = S.compute_metrics(urow, f)                     # the US composite's metric builder
        apply_japan_guards(r, f, yq_mcap=yq.get(u["tkr"]))  # batch-2 mcap/FCF/advances guards
        r["foreign"] = True
        r["adr"] = False                                   # local line, not an ADR wrapper
        r["ifrs"] = "IFRS" in (f.get("std") or "")         # one-time-gain exposure flag
        r["consol"] = f.get("_consol", False)
        r["px_stale"] = (now - p.get("ts", 0)) > PX_STALE_DAYS * 86400
        r["lot_cost"] = round(p["px"] * 100) if p.get("px") else None   # 100-share board lot
        r["doc_id"] = f.get("doc_id")
        r["period_end"] = f.get("period_end")
        r["tse_plan"] = None                               # TODO: JPX improvement-plan join (docstring)
        pf = P.pfic_risk(r, f)
        r["pfic"] = pf["pfic"]
        r["pfic_why"] = pf["reason"]
        # FMV-basis overlay (2026-07-20): for PUBLICLY TRADED names the §1297 asset test runs on
        # FMV — denominator ≈ mktcap + liabilities, NOT book assets. Book basis under-flags the
        # below-book shelf (the discount shrinks the FMV denominator: cheapness and PFIC are the
        # same phenomenon). Batch-1 catch: Daishin 39% book → 58% FMV, Eidai 31% → 54%.
        _cash = (f.get("CashAndCashEquivalentsAtCarryingValue") or 0) + (f.get("ShortTermInvestments") or 0)
        _lti = sum((f.get(k) or 0) for k in ("LongTermInvestments", "OtherLongTermInvestments",
                                             "MarketableSecuritiesNoncurrent", "AvailableForSaleSecuritiesNoncurrent"))
        _liab = f.get("Liabilities") or 0
        _fmv = (r.get("mktcap") or 0) + _liab
        if _fmv > 0:
            _share = (_cash + _lti) / _fmv
            r["pfic_fmv_share"] = round(_share, 3)
            if _share >= 0.5 and not r["pfic"]:
                r["pfic"] = True
                r["pfic_why"] = f"FMV-basis passive {_share*100:.0f}% >= 50% (book-basis passed: {r['pfic_why']})"
        recs.append(r)
    print(f"priced + in-band: {len(recs)}")

    scored = S.composite(recs)
    shortlist = S.clean_shortlist(scored, exclude_adr=False)

    os.makedirs(DATA, exist_ok=True)
    keep = ("sym", "ind", "sec", "mktcap", "px", "score", "am", "fcfy", "pb", "ncash_r",
            "mcap_suspect", "mcap_yahoo", "fcf_no_capex", "contract_liab_adj", "ncash_r_asis",
            "ncav_r", "ebit", "fcf", "subcash", "holdco", "neg_equity", "wc_fcf", "pfic",
            "pfic_why", "pfic_fmv_share", "ifrs", "consol", "lot_cost", "px_stale", "doc_id",
            "period_end", "tse_plan", "nmetrics")
    json.dump([{k: r.get(k) for k in keep} for r in shortlist[:120]],
              open(SHORTLIST, "w"), ensure_ascii=False, indent=1)
    # auto-court conveyor (2026-08-06): clean fresh candidates -> TRAP_VERIFY queue (idempotent)
    try:
        import os as _os, sys as _sys
        _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(
            _os.path.dirname(_os.path.abspath(__file__))))))
        from desk.court_queue import enqueue_candidates
        cand = [r for r in shortlist
                if not r.get("pfic") and not r.get("px_stale") and not r.get("mcap_suspect")][:15]
        c = enqueue_candidates([{**r, "ticker": r["sym"]} for r in cand],
                               source=f"screen_japan/{time.strftime('%Y-%m-%d')}")
        print(f"court_queue: {c['added']} new candidates enqueued")
    except Exception as e:
        print(f"court_queue enqueue failed (screen output unaffected): {type(e).__name__}: {e}")

    def fmt(r):
        am = f"{r['am']:.1f}" if r["am"] else ("sub¥" if r["subcash"] else " -")
        fy = f"{r['fcfy']*100:.0f}%" if r["fcfy"] is not None else " -"
        pb = f"{r['pb']:.2f}" if r["pb"] else " -"
        nc = f"{r['ncash_r']:.2f}" if r["ncash_r"] is not None else " -"
        nv = f"{r['ncav_r']:.2f}" if r["ncav_r"] is not None else " -"
        fl = " ".join(t for t, on in [
            ("PFIC", bool(r["pfic"])), ("IFRS", r["ifrs"]), ("WC-FCF", r["wc_fcf"]),
            ("holdco", r["holdco"]), ("neg-eq", r["neg_equity"]),
            ("solo", not r["consol"]), ("stale-px", r["px_stale"])] if on)
        return (f"  {r['sym']:8s}{r['mktcap']/1e9:7.1f} {am:>6s}{fy:>6s}{pb:>6s}{nc:>7s}{nv:>6s}"
                f"  {r['sec'][:13]:13s} {r['ind'][:22]:22s} {fl}")

    npfic = sum(1 for r in shortlist if r["pfic"])
    print(f"\nJAPAN DEEP-VALUE SHORTLIST (annual 有報 season, ex-burners/ex-financials)  "
          f"n={len(shortlist)}  PFIC-flagged={npfic} ({npfic/max(len(shortlist),1)*100:.0f}%)")
    print(f"  {'tkr':8s}{'mc¥B':>7s}{'EV/EBIT':>6s}{'FCFy':>6s}{'P/B':>6s}{'ncash/m':>7s}{'NCAV/m':>6s}"
          f"  {'sector':13s} {'name':22s} flags")
    for r in shortlist[:top]:
        print(fmt(r))
    print(f"\n  (mc¥B x {JPY_USD*1e3:.1f} = $M approx; 100-share lots; "
          f"tse_plan column TODO — JPX follow-up list join)")
    return shortlist


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--min-mcap", type=float, default=3e9)
    ap.add_argument("--max-mcap", type=float, default=4e11)
    ap.add_argument("--refresh-px", action="store_true")
    a = ap.parse_args()
    run(a.top, a.min_mcap, a.max_mcap, a.refresh_px)
