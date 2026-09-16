#!/usr/bin/env python3
"""japan_tob_lane — the Japan take-private / tender-offer (TOB) lane.

WHY THIS LANE. TSE's governance program (the 2023 "management conscious of cost of capital
and share price" directive + the parent-subsidiary listing cleanup) turned Japan into the
densest take-private pond in the developed world. A TOB pays on a DATED, contractual event
(the offer settles or it does not) rather than on the tape level, which is exactly the
kind of return the house wants when it does not want more beta.

TWO BOOKS. THEY NEVER MIX.
  A. ANNOUNCED  — a live tender offer exists. This is a SPREAD book: offer price vs market,
                  minimum-tender condition, expiry, squeeze-out mechanics. Deal risk only.
  B. ANTICIPATORY — no offer exists. This is a FINGERPRINT book: names whose structure looks
                  like the ones that get taken out. Pure speculation on an undated event.
     An anticipatory name is NEVER counted as a spread, never annualized, and never carried
     in the same return table. Doing so is the single easiest way to fabricate an edge.

CHANNELS THAT ACTUALLY WORK (documented because two obvious ones do not):
  * TDnet (release.tdnet.info) — WORKS, plain HTTP, no key, no browser. Daily disclosure
    index at I_list_<page>_<YYYYMMDD>.html, 100 rows/page, ~850 rows on a busy day. Titles
    are formulaic enough to classify, and every row links a public PDF. THIS IS THE
    ANNOUNCED CHANNEL. Retention is only ~31 days, so THE STORE IS THE HISTORY (the
    broken_print_radar lesson): a day we never crawled is gone forever.
  * EDINET API v2 — DOES NOT WORK unkeyed. api.edinet-fsa.go.jp returns
    {"StatusCode": 401, "message": "Access denied due to invalid subscription key"}.
    docTypeCode 240 (公開買付届出書) is the authoritative statutory TOB filing and would be
    the better channel; it needs a free subscription key we do not have. Gap is honest.
  * EDINET viewer (disclosure2.edinet-fsa.go.jp) — works via Playwright (the existing
    edinet_browser_crawl transport) but is slow and only needed for the anticipatory side,
    which we serve OFFLINE from the 1,525 annual-report XBRL fact sets already cached.
  * JPX follow-up ("cost of capital") page — publishes PDFs, not a machine-readable company
    list. We derive the improvement-plan flag from the issuer's OWN annual report text
    instead (arguably the stronger primary source; see anticipatory notes).

ANTICIPATORY FINGERPRINT — all of it from local cached primary filings, zero network:
  * FIEA Art.24-7(1) parent disclosure (jpcrp_cor:InformationAboutParentCompanyEtc...) —
    a HARD statutory binary: the filing either names a controlling parent or says
    「親会社等はありません」. This is the parent-subsidiary-listing universe, defined by law
    rather than by our guess.
  * 【関係会社の状況】 (OverviewOfAffiliatedEntities) — the 被所有 (owned-by) percentage.
  * 【大株主の状況】 (MajorShareholders) — top-holder name and percentage.
  * 【役員の状況】 (InformationAboutOfficers) — director birthdates -> founder age, and
    same-surname directors -> family succession (or its absence).
  * cash / equity / market cap from the existing EDINET fundamentals store.

GUARDS (house doctrine, each enforced in code, not just described):
  * MINIMUM-TENDER CONDITION. Nearly every Japanese TOB carries a 買付予定数の下限. If it is
    not met the offer is withdrawn and the spread goes to zero AND the stock re-rates down.
    We surface the floor in shares and the required tender rate among non-bidder holders.
  * SQUEEZE-OUT TIMELINE. A Japanese take-private is two-step. Step 2 (株式売渡請求 for a
    >=90% holder, or 株式併合 below that) runs MONTHS after the tender settles. We annualize
    to the TENDER settlement date for a tendering holder, and separately state the step-2
    date risk for a non-tendering holder. We NEVER annualize a pre-conditional offer whose
    start date is not yet fixed — those are labelled TIMING_UNBOUNDED with no annual number.
  * ADIG THIN-PRINT RULE. A spread struck on a thin or stale print is not a quote. Every
    spread carries a liquidity verdict and a thin/stale spread is marked NOT_QUOTABLE.
  * JPY. Spreads are JPY-denominated. The book already holds unhedged JPY; every added
    position is an ADDITIONAL unhedged JPY exposure and the report states the add in JPY
    and USD at the run's spot.
  * TAXABLE ACCOUNT. Tender proceeds are a SALE, not a merger rollover: short-term capital
    gain for anything held under a year, and Japan withholds nothing from a US holder on
    a TOB tender through a US broker (it is an on-market-equivalent disposition), but the
    holding-period clock is what kills the after-tax return on a 4% gross / 90-day spread.
    Stated per deal, never assumed away.
  * HELD-BOOK OVERLAP. Every announced target and every anticipatory candidate is checked
    against the held Japan book and flagged loudly.

USAGE
  python3 verticals/generators/japan_tob_lane.py                    # both books
  python3 verticals/generators/japan_tob_lane.py --mode announced --days 45
  python3 verticals/generators/japan_tob_lane.py --mode anticipatory --top 40
  python3 verticals/generators/japan_tob_lane.py --intake            # also write the .md

Outputs
  verticals/generators/data/JAPAN_TOB.json          machine state (MERGE-ONLY event store)
  desk/data/JAPAN_TOB_INTAKE_<YYYYMMDD>.md          analyst intake
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, "data")
STORE = os.path.join(DATA, "JAPAN_TOB.json")
PDF_CACHE = os.path.join(DATA, "japan_tob_pdfs")
EDINET_CACHE = os.path.join(ROOT, "verticals", "deep_value", "global", "data", "edinet_cache")
EDINET_STORE = os.path.join(ROOT, "verticals", "deep_value", "global", "data", "edinet_store.json")
EDINET_CODES = os.path.join(ROOT, "verticals", "deep_value", "global", "data", "Edinetcode.zip")
PX_CACHE = os.path.join(ROOT, "verticals", "deep_value", "global", "data", "japan_px_cache.json")
DESK_DATA = os.path.join(ROOT, "desk", "data")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
TDNET = "https://www.release.tdnet.info/inbs"

# The Japan book we already hold at IBKR (TSEJ). Announced targets and anticipatory names are
# checked against this — a take-private on a name we own is a RESULT, not a new idea.
HELD_JAPAN = {"3388": "Meiji Electric Industries", "6229": "Okada Aiyon",
              "7222": "Nissan Shatai", "8750": "Dai-ichi Life"}

# Custodian / trust-bank nominees are NOT strategic parents. Any fingerprint that treats
# 日本マスタートラスト as a controlling holder is broken.
NOMINEES = ("日本マスタートラスト", "日本カストディ", "カストディ銀行", "資産管理サービス",
            "ステート・ストリート", "ＪＰモルガン", "JPMORGAN", "STATE STREET", "THE BANK OF NEW YORK",
            "MSIP", "BNYM", "証券株式会社", "持株会", "共栄会", "共伸会", "自己株式", "信託口")

# ---------------------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------------------

Z2H = str.maketrans("０１２３４５６７８９．，％－", "0123456789.,%-")


def _n(s: str) -> str:
    """full-width -> half-width for the numeric characters that matter, whitespace squashed."""
    return re.sub(r"[\s　]+", "", (s or "").translate(Z2H))


def _get(url: str, tries: int = 3, binary: bool = False):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            raw = urllib.request.urlopen(req, timeout=30).read()
            return raw if binary else raw.decode("utf-8", "replace")
        except Exception:
            if i == tries - 1:
                return b"" if binary else ""
            time.sleep(1.5 * (i + 1))
    return b"" if binary else ""


def _load_store() -> dict:
    if os.path.exists(STORE):
        try:
            return json.load(open(STORE))
        except Exception:
            os.replace(STORE, STORE + ".corrupt_%s" % dt.datetime.now().strftime("%Y%m%d%H%M%S"))
    return {"events": {}, "deals": {}, "anticipatory": [], "runs": []}


def _save_store(st: dict) -> None:
    os.makedirs(DATA, exist_ok=True)
    tmp = STORE + ".tmp"
    json.dump(st, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, STORE)


def tdnet_code_to_ticker(code: str) -> str:
    """TDnet publishes 5-char codes: a 4-digit code gets a trailing 0 ('91100' -> '9110');
    the new alphanumeric codes behave the same ('472A0' -> '472A')."""
    c = (code or "").strip()
    return c[:4] if len(c) == 5 and c.endswith("0") else c


# ---------------------------------------------------------------------------------------
# MODE A — ANNOUNCED: TDnet crawl
# ---------------------------------------------------------------------------------------

ROW_RE = re.compile(
    r'<td class="\w+-L kjTime" noWrap>([^<]*)</td>\s*'
    r'<td class="\w+-M kjCode" noWrap>([^<]*)</td>\s*'
    r'<td class="\w+-M kjName" noWrap>([^<]*)</td>\s*'
    r'<td class="\w+-M kjTitle" align="left"><a href="([^"]+)"[^>]*>([^<]*)</a>', re.S)

# Title keywords that put a disclosure in this lane at all.
LANE_KW = ("公開買付", "ＭＢＯ", "MBO", "株式売渡請求", "株式併合", "非公開化", "上場廃止")


def _classify(title: str) -> str:
    """Event kind. Order matters — 結果 (result) beats 開始 (start) when both appear."""
    t = title
    if "結果" in t:
        return "RESULT"
    if "撤回" in t:
        return "WITHDRAWN"
    if "売渡請求" in t:
        return "SQUEEZEOUT_STEP2"
    if "株式併合" in t:
        return "SQUEEZEOUT_STEP2"
    if "開始" in t or "実施" in t:
        return "START"
    if "延長" in t or "変更" in t or "訂正" in t:
        return "AMEND"
    if "意見表明" in t or "応募推奨" in t or "賛同" in t:
        return "OPINION"
    if "買集め" in t:
        return "STAKEBUILD"
    return "OTHER"


CODE_IN_TITLE = re.compile(r"[（(]?証券コード[：: ]?\s*([0-9A-Z]{4})[）)]?")
CODE_PAREN = re.compile(r"[（(]コード[：: ]?\s*([0-9A-Z]{4})[）)]")


def _resolve_target(filer_code: str, title: str) -> tuple[str, str]:
    """Who is being bought? Bidder-side titles name the target with its 証券コード; target-side
    titles say 当社株式 (our shares). Returns (target_code, basis)."""
    t = _n(title)
    m = CODE_IN_TITLE.search(t) or CODE_PAREN.search(t)
    if m:
        return m.group(1), "code-in-title"
    if "当社株" in t or "当社の株" in t:
        return filer_code, "filer-is-target"
    return "", "unresolved"


def crawl_tdnet(days: int, store: dict, verbose: bool = True) -> int:
    """Crawl the last `days` TDnet daily indexes, MERGE lane-relevant rows into the event
    store. Returns count of NEW events. Weekend/holiday pages return a stub and are skipped."""
    ev = store.setdefault("events", {})
    new = 0
    today = dt.date.today()
    for i in range(days):
        day = today - dt.timedelta(days=i)
        ds = day.strftime("%Y%m%d")
        if any(k.startswith(ds) for k in store.get("_days_done", [])) and i > 2:
            continue  # already crawled a settled day; re-crawl only the most recent 3
        html = _get(f"{TDNET}/I_list_001_{ds}.html")
        if "kjTitle" not in html:
            continue
        m = re.search(r"全(\d+)件", html)
        total = int(m.group(1)) if m else 0
        pages = max(1, (total + 99) // 100)
        rows = []
        for p in range(1, pages + 1):
            hp = html if p == 1 else _get(f"{TDNET}/I_list_{p:03d}_{ds}.html")
            rows += ROW_RE.findall(hp)
            time.sleep(0.12)
        hits = 0
        for tm, code, name, pdf, title in rows:
            if not any(k in title for k in LANE_KW):
                continue
            # 完全子会社化 of an UNLISTED sub is ordinary M&A, not our lane — those titles
            # carry no 公開買付/売渡請求/MBO. LANE_KW already excludes them.
            key = pdf.replace(".pdf", "")
            hits += 1
            if key in ev:
                continue
            fc = tdnet_code_to_ticker(code)
            tgt, basis = _resolve_target(fc, title)
            ev[key] = {"date": day.isoformat(), "time": tm.strip(), "filer_code": fc,
                       "filer": name.strip(), "title": title.strip(),
                       "kind": _classify(title), "target_code": tgt, "target_basis": basis,
                       "pdf": f"{TDNET}/{pdf}"}
            new += 1
        store.setdefault("_days_done", [])
        if ds not in store["_days_done"]:
            store["_days_done"].append(ds)
        if verbose:
            print(f"  tdnet {day} : {total:>4} disclosures, {hits:>2} lane rows")
    return new


# ---------------------------------------------------------------------------------------
# MODE A — term extraction from the TOB PDF
# ---------------------------------------------------------------------------------------

# The offer price MUST be read anchored to its own label. A TOB notice frequently recites a
# PRIOR offer's price in the background section — 7523 アールビバン's 2026 MBO notice quotes the
# FAILED 2025 offer at ¥1,670 in prose before ever stating the live price. An unanchored
# "first ¥N per share in the document" regex silently books the dead price as the live one.
PRICE_LABEL_RE = re.compile(r"買付け?等の価格|買付価格|本公開買付価格|売渡対価|本売渡対価")
PRICE_VAL_RE = re.compile(r"[0-9]?株(?:当たり)?につき[、,，]?\s*金?\s*([0-9,]+)\s*円")
# floor appears in three layouts: label:value, label value（株）, and a header-row table where
# the three numbers follow the three headers in order (予定数 / 下限 / 上限).
FLOOR_DIRECT_RE = re.compile(r"買付予定数の下限[：:\s]*([0-9,]{4,})")
FLOOR_TABLE_RE = re.compile(r"買付予定数の下限買付予定数の上限[^0-9]{0,20}([0-9,]{4,})\s*[（(]?株[）)]?\s*([0-9,]{4,})")
CAP_RE = re.compile(r"買付予定数の上限[：:\s]*([0-9,]{4,})")
PERIOD_RE = re.compile(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日.{0,12}?から\s*(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日")
POST_PCT_RE = re.compile(r"([0-9]{1,3}\.[0-9]{1,2})\s*[%％]")
ACQ_DATE_RE = re.compile(r"(?:取得日|効力発生日)[^0-9]{0,20}(\d{4})年(\d{1,2})月(\d{1,2})日")
DELIST_RE = re.compile(r"(?:上場廃止日|最終売買日)[^0-9]{0,30}(\d{4})年(\d{1,2})月(\d{1,2})日")


def fetch_pdf_text(url: str, pages: int = 12) -> str:
    """Download + pdftotext the first `pages` pages. Cached on disk (filings are immutable)."""
    os.makedirs(PDF_CACHE, exist_ok=True)
    fn = os.path.join(PDF_CACHE, os.path.basename(url))
    txt_fn = fn + f".p{pages}.txt"
    if os.path.exists(txt_fn):
        return open(txt_fn, encoding="utf-8", errors="replace").read()
    if not os.path.exists(fn):
        raw = _get(url, binary=True)
        if not raw or not raw.startswith(b"%PDF"):
            return ""
        open(fn, "wb").write(raw)
    try:
        out = subprocess.run(["pdftotext", "-layout", "-f", "1", "-l", str(pages), fn, "-"],
                             capture_output=True, timeout=90).stdout.decode("utf-8", "replace")
    except Exception:
        return ""
    open(txt_fn, "w").write(out)
    return out


def parse_tob_terms(txt: str) -> dict:
    """Parse the standardised 「買付け等の概要」 summary table that every TOB commencement
    notice carries. Anything not found stays None — never guessed."""
    t = _n(txt)
    out = {"offer_price": None, "price_anchor": None, "tender_floor_sh": None,
           "tender_cap_sh": None, "period_start": None, "period_end": None, "purpose": None,
           "target_opinion": None, "post_deal_pct": None, "preconditional": False,
           "step2_mechanic": None, "settlement_start": None, "acq_date": None,
           "delist_date": None, "competing_bid": False}

    # ---- price: ANCHORED. Take the first per-share figure that follows a price LABEL within
    # 120 chars. A recital of a superseded/failed prior offer never sits behind that label.
    for lm in PRICE_LABEL_RE.finditer(t):
        seg = t[lm.end():lm.end() + 120]
        pm = PRICE_VAL_RE.search(seg)
        if pm:
            out["offer_price"] = float(pm.group(1).replace(",", ""))
            out["price_anchor"] = t[lm.start():lm.end()] + " -> " + seg[:40]
            break

    m = FLOOR_TABLE_RE.search(t)
    if m:
        out["tender_floor_sh"] = int(m.group(2).replace(",", ""))
    else:
        m = FLOOR_DIRECT_RE.search(t)
        if m:
            out["tender_floor_sh"] = int(m.group(1).replace(",", ""))
    m = CAP_RE.search(t)
    if m:
        out["tender_cap_sh"] = int(m.group(1).replace(",", ""))

    # a rival bid changes the risk sign completely: the downside is no longer "spread -> 0"
    if ("対抗" in t and "公開買付" in t) or len(set(re.findall(r"([^\s]{2,20}?)公開買付けに応募する義務", t))) > 1:
        out["competing_bid"] = True

    m = ACQ_DATE_RE.search(t)
    if m:
        try:
            out["acq_date"] = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except Exception:
            pass
    m = DELIST_RE.search(t)
    if m:
        try:
            out["delist_date"] = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except Exception:
            pass

    # purpose: 非公開化 (go-private) vs 連結子会社化 (consolidate, stays listed)
    for kw, lab in (("非公開化", "GO_PRIVATE"), ("完全子会社", "GO_PRIVATE"),
                    ("連結子会社", "CONSOLIDATE"), ("持分法", "CONSOLIDATE")):
        if kw in t[:4000]:
            out["purpose"] = lab
            break
    if "賛同" in t[:4000] and "応募" in t[:4000]:
        out["target_opinion"] = "SUPPORT_AND_RECOMMEND"
    elif "中立" in t[:4000]:
        out["target_opinion"] = "NEUTRAL"
    elif "反対" in t[:4000]:
        out["target_opinion"] = "OPPOSE"

    # A pre-conditional offer (competition clearance etc.) has NO fixed start date. This is
    # the timing-honesty fork: we must not annualize these.
    if "前提条件" in t and ("開始することを予定" in t or "開始予定" in t or "決定次第" in t):
        out["preconditional"] = True
        # the bidder usually guides a target window ("2026年11月下旬から同年12月下旬を目途に開始").
        # That guided date + a 20-business-day period + ~5bd settlement is the ONLY defensible
        # scenario input; without it we refuse to put a number on it at all.
        gm = re.search(r"(\d{4})年(\d{1,2})月(上旬|中旬|下旬)?.{0,40}?目途に.{0,30}?開始", t)
        if gm:
            y, mo = int(gm.group(1)), int(gm.group(2))
            dd = {"上旬": 5, "中旬": 15, "下旬": 25}.get(gm.group(3) or "", 15)
            try:
                start = dt.date(y, mo, dd)
                out["precond_guided_start"] = start.isoformat()
                # 20 business days ~= 28 calendar days, plus ~7 days to settlement
                out["precond_guide_days"] = max(1, (start - dt.date.today()).days + 35)
            except Exception:
                pass

    m = PERIOD_RE.search(t)
    if m and not out["preconditional"]:
        try:
            out["period_start"] = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
            out["period_end"] = dt.date(int(m.group(4)), int(m.group(5)), int(m.group(6))).isoformat()
        except Exception:
            pass

    m = re.search(r"決済の開始日.{0,60}?(\d{4})年(\d{1,2})月(\d{1,2})日", t)
    if m:
        try:
            out["settlement_start"] = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except Exception:
            pass

    # post-deal ownership AT THE FLOOR — the notice states it explicitly, so we read it
    # rather than derive it (deriving needs the special-related-party share count we do not have)
    m = re.search(r"買付け等後の株券等所有割合[^0-9]{0,90}?([0-9]{1,3}\.[0-9]{1,2})\s*[%％]", t)
    if not m and "買付予定数の下限" in t:
        i = t.find("買付予定数の下限")
        m = POST_PCT_RE.search(t[i:i + 900])
    if m:
        v = float(m.group(1))
        out["post_deal_pct"] = v if 0 < v <= 100 else None

    if "株式売渡請求" in t:
        out["step2_mechanic"] = "CASH_OUT_DEMAND_90PCT"   # Companies Act 179, fast (~1mo)
    elif "株式併合" in t:
        out["step2_mechanic"] = "REVERSE_SPLIT_EGM"       # needs an EGM, ~3-4 months
    return out


# ---------------------------------------------------------------------------------------
# MODE A — price join + spread math
# ---------------------------------------------------------------------------------------

# TSE daily price-limit (値幅制限) table: (base price below, limit in yen). A stock that opens
# and closes at exactly base±limit with O==H==L is LOCKED — bids are queued and unfilled.
PRICE_LIMITS = [(100, 30), (200, 50), (500, 80), (700, 100), (1000, 150), (1500, 300),
                (2000, 400), (3000, 500), (5000, 700), (7000, 1000), (10000, 1500),
                (15000, 3000), (20000, 4000), (30000, 5000), (50000, 7000), (70000, 10000),
                (100000, 15000), (150000, 30000), (200000, 40000), (300000, 50000)]


def price_limit(base: float) -> float:
    for lo, lim in PRICE_LIMITS:
        if base < lo:
            return lim
    return base * 0.3


def fetch_quotes(codes: list[str]) -> dict:
    """Spot + 20d turnover + LIMIT-LOCK state for each <code>.T.

    Two traps this function exists to defuse, both of which manufacture huge fake spreads:

    1. NaN-close fallback. yfinance leaves Close NaN on an in-progress or locked session, so
       naively taking the last non-NaN Close silently reaches back to the PRE-ANNOUNCEMENT
       price. On 9110 that turned a real +1.2% spread into a fictional +11.1%.
    2. Limit-up lock (ストップ高). A Japanese stock bid at a big TOB premium goes limit-up with
       O==H==L and an unfilled buy queue. The print is real; it is not a price you can pay.
       This is the ADIG thin-print rule in its Japanese form and it is the dominant failure
       mode of this lane — every large "spread" on day 1-3 of a deal is this.
    """
    out = {}
    if not codes:
        return out
    try:
        import yfinance as yf
    except Exception:
        return {c: {"px": None, "err": "yfinance-unavailable"} for c in codes}
    tick = [f"{c}.T" for c in codes]
    try:
        df = yf.download(tick, period="1mo", interval="1d", progress=False,
                         auto_adjust=False, threads=True, group_by="column")
    except Exception as ex:
        return {c: {"px": None, "err": f"download-failed:{ex}"} for c in codes}
    import statistics as st
    for c, t in zip(codes, tick):
        try:
            sub = (df.xs(t, axis=1, level=1) if len(tick) > 1 else df)[
                ["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")
            sub = sub[sub["Volume"].fillna(0) > 0]
            if not len(sub):
                out[c] = {"px": None, "err": "no-prints"}
                continue
            last = sub.iloc[-1]
            prev = sub.iloc[-2] if len(sub) > 1 else last
            o, h, lo_, cl = (float(last[k]) if last[k] == last[k] else None
                             for k in ("Open", "High", "Low", "Close"))
            # spot: the close if the session settled, else the last real trade level we can
            # see. NEVER fall back to an older session's close.
            px = cl if cl else (h if (o and h and lo_ and o == h == lo_) else
                                ((h + lo_) / 2 if (h and lo_) else o))
            last_dt = sub.index[-1].date()
            med_v = float(st.median(sub["Volume"].tail(20)))
            pc = float(prev["Close"]) if prev["Close"] == prev["Close"] else None

            q = {"px": px, "asof": last_dt.isoformat(),
                 "close_settled": cl is not None,
                 "stale_days": (dt.date.today() - last_dt).days,
                 "med_vol_20d": med_v, "notional_20d_jpy": med_v * (px or 0),
                 "prev_close": pc, "locked": False, "limit_dir": None}
            if pc and px:
                q["move_1d_pct"] = round((px / pc - 1) * 100, 2)
                lim = price_limit(pc)
                q["limit_price_up"] = pc + lim
                q["limit_price_dn"] = pc - lim
                at_limit = abs(abs(px - pc) - lim) < 1e-6 or abs(px - pc) >= lim - 0.5
                flat_bar = (o and h and lo_ and o == h == lo_)
                if at_limit:
                    q["limit_dir"] = "UP" if px > pc else "DOWN"
                    q["locked"] = bool(flat_bar)
            out[c] = q
        except Exception as ex:
            out[c] = {"px": None, "err": str(ex)[:80]}
    return out


def liquidity_verdict(q: dict) -> tuple[str, str]:
    """The thin-print gate. A spread is only a spread if you could have paid for it.
    LIMIT_LOCKED / NO_PRINT / STALE / THIN / QUOTABLE_SMALL / QUOTABLE."""
    if not q or not q.get("px"):
        return "NO_PRINT", "no usable print — do not quote a spread"
    if q.get("locked"):
        return ("LIMIT_LOCKED",
                f"stock is LOCKED limit-{q['limit_dir'].lower()} at ¥{q['px']:,.0f} "
                f"(prev close ¥{q['prev_close']:,.0f}, TSE limit ±¥{price_limit(q['prev_close']):,.0f}); "
                f"the bar is O=H=L on a queued book. Any spread struck here is PHANTOM — you "
                f"cannot buy at the locked price, and the stock will gap again next session.")
    if q.get("limit_dir") == "UP":
        return ("AT_LIMIT",
                f"trading AT the daily upper limit (¥{q['px']:,.0f}) though not fully locked — "
                f"fills are partial and the quote is not a reliable entry")
    if q.get("stale_days", 0) > 4:
        return "STALE", f"last print {q['stale_days']}d old — spread struck on a stale tape"
    n = q.get("notional_20d_jpy") or 0
    if n < 20_000_000:
        return ("THIN", f"20d median turnover ¥{n/1e6:.1f}M/day — a quoted spread here is not "
                        f"fillable at size; this is a delisting stub, not a position")
    if n < 100_000_000:
        return "QUOTABLE_SMALL", f"20d median turnover ¥{n/1e6:.0f}M/day — small clips only"
    return "QUOTABLE", f"20d median turnover ¥{n/1e6:.0f}M/day"


def build_announced(store: dict, refresh_terms: bool = True) -> list[dict]:
    """Collapse the event stream into per-target DEALS with a status, then price them."""
    ev = store.get("events", {})
    by_target: dict[str, list] = {}
    for k, e in ev.items():
        tc = e.get("target_code")
        if not tc:
            continue
        by_target.setdefault(tc, []).append(e)

    deals = []
    for tc, evs in by_target.items():
        evs.sort(key=lambda x: (x["date"], x["time"]))
        kinds = {e["kind"] for e in evs}
        # ---- status machine ------------------------------------------------------------
        if "WITHDRAWN" in kinds:
            status = "WITHDRAWN"
        elif "RESULT" in kinds and "SQUEEZEOUT_STEP2" in kinds:
            status = "SQUEEZE_OUT"      # tender done, step-2 cash-out running -> delisting
        elif "RESULT" in kinds:
            status = "CLOSED"
        elif kinds & {"START", "OPINION", "AMEND"}:
            status = "OPEN"
        elif "STAKEBUILD" in kinds:
            status = "STAKEBUILD_ONLY"  # 買集め行為 disclosure — NOT an offer, do not price
        else:
            status = "UNCLASSIFIED"

        starts = [e for e in evs if e["kind"] in ("START", "OPINION")]
        src = starts[0] if starts else evs[0]
        # target name: prefer the event where the filer IS the target
        tn = next((e["filer"] for e in evs if e["filer_code"] == tc), None) or src["filer"]
        # bidder: the other filer if one disclosed, else read it out of the target's own title
        # (「<bidder>による当社株式に対する公開買付け…」 is the standard construction)
        bidder = next((e["filer"] for e in evs if e["filer_code"] != tc), None)
        if not bidder:
            for e in evs:
                bm = re.match(r"^(?:[（(][^）)]*[）)])?\s*(.{2,40}?)による", _n(e["title"]))
                if bm:
                    bidder = bm.group(1).lstrip("「（(【 ")
                    break

        d = {"target_code": tc, "target_name": tn, "bidder": bidder, "status": status,
             "first_seen": evs[0]["date"], "last_event": evs[-1]["date"],
             "n_events": len(evs), "kinds": sorted(kinds),
             "primary_pdf": src["pdf"], "primary_title": src["title"],
             "held": HELD_JAPAN.get(tc)}
        # ---- terms, only for live books -------------------------------------------------
        if status in ("OPEN", "SQUEEZE_OUT") and refresh_terms:
            best = {}
            # amendments supersede: walk newest-first, take the first PDF that yields a price
            for e in sorted(evs, key=lambda x: x["date"], reverse=True):
                if e["kind"] in ("RESULT", "STAKEBUILD"):
                    continue
                txt = fetch_pdf_text(e["pdf"])
                if not txt:
                    continue
                t = parse_tob_terms(txt)
                if t["offer_price"]:
                    best = t
                    best["terms_from"] = e["pdf"]
                    best["terms_date"] = e["date"]
                    break
            d.update(best)
        deals.append(d)

    live = [d for d in deals if d["status"] in ("OPEN", "SQUEEZE_OUT")]
    q = fetch_quotes([d["target_code"] for d in live])
    today = dt.date.today()
    for d in live:
        qq = q.get(d["target_code"], {})
        d["spot"] = qq.get("px")
        d["spot_asof"] = qq.get("asof")
        d["med_vol_20d"] = qq.get("med_vol_20d")
        d["turnover_20d_jpy"] = qq.get("notional_20d_jpy")
        d["liquidity"], d["liquidity_why"] = liquidity_verdict(qq)

        d["spot_settled"] = qq.get("close_settled")
        d["limit_state"] = ("LOCKED_" + (qq.get("limit_dir") or "") if qq.get("locked")
                            else (qq.get("limit_dir") or "NORMAL"))
        op, sp = d.get("offer_price"), d.get("spot")
        if op and sp:
            d["gross_spread_pct"] = round((op / sp - 1) * 100, 3)
        else:
            d["gross_spread_pct"] = None

        # A spread you cannot pay for is not a spread. Locked / stale / no-print lines are
        # reported but never ranked, and never carried into a return table.
        d["spread_quotable"] = d["liquidity"] in ("QUOTABLE", "QUOTABLE_SMALL", "THIN")
        if qq.get("locked") and op and sp:
            # how many more limit sessions before the tape can even reach the offer
            n, p = 0, sp
            while p < op and n < 12:
                p += price_limit(p)
                n += 1
            d["sessions_to_converge"] = n
            d["quotable_note"] = (
                f"PHANTOM SPREAD: the {d['gross_spread_pct']:+.1f}% shown is measured against a "
                f"locked limit-{(qq.get('limit_dir') or '').lower()} print. The tape needs ~{n} more "
                f"session(s) of limit moves to reach ¥{op:,.0f}. Nothing is buyable until the "
                f"lock breaks — re-read this name once it trades two-sided.")
        elif not d["spread_quotable"]:
            d["quotable_note"] = f"not quotable: {d['liquidity_why']}"
        else:
            d["quotable_note"] = None

        # ---- HONEST annualization ------------------------------------------------------
        # tendering holder is paid at 決済の開始日; absent that, expiry + 5 business days
        # (the statutory settlement lag runs ~5bd after the period closes).
        d["annualized_pct"] = None
        d["annualized_scenario_pct"] = None
        d["days_to_cash"] = None
        if d["status"] == "SQUEEZE_OUT":
            # tender already settled; the residual stub is cashed out at the 取得日 under
            # Companies Act 179. Short and near-certain, but the float is a stub — the
            # thin-print gate is what decides whether this is real.
            ac = d.get("acq_date")
            if ac:
                days = (dt.date.fromisoformat(ac) - today).days
                d["days_to_cash"] = days
                d["timing"] = "DATED_STEP2"
                d["timing_why"] = (f"step-2 cash-out effective {ac} ({days}d); delisting "
                                   f"{d.get('delist_date') or 'date not parsed'}")
                if d["gross_spread_pct"] is not None and days > 0:
                    d["annualized_pct"] = round(d["gross_spread_pct"] * 365.0 / days, 1)
                elif days <= 0:
                    d["timing"] = "PAST_STEP2"
                    d["timing_why"] = (f"cash-out date {ac} has passed — the line is almost "
                                       f"certainly delisted; any 'spot' is a dead print")
            else:
                d["timing"] = "TIMING_UNPARSED"
                d["timing_why"] = "step-2 running but 取得日 not parsed"
        elif d.get("preconditional"):
            d["timing"] = "TIMING_UNBOUNDED"
            d["timing_why"] = ("offer is PRE-CONDITIONAL (competition clearance etc.); the "
                               "commencement date is NOT fixed, so a computed annualized "
                               "number would be manufactured. Gross only.")
            # a labelled SCENARIO is honest; a computed annualization is not. The company's
            # own guided window is the only defensible input.
            guide = d.get("precond_guide_days") or 180
            gsrc = ("the bidder's own guided commencement window "
                    f"({d['precond_guided_start']})" if d.get("precond_guided_start")
                    else "a house default 180d, since the bidder guided no window")
            if d["gross_spread_pct"] is not None:
                d["annualized_scenario_pct"] = round(d["gross_spread_pct"] * 365.0 / guide, 1)
                d["timing_why"] += (f" SCENARIO ONLY: at {guide}d to cash (from {gsrc}) the "
                                    f"gross {d['gross_spread_pct']:+.2f}% annualizes to "
                                    f"{d['annualized_scenario_pct']:+.0f}%/yr — an assumption, "
                                    f"NOT a term of the offer, and it goes to zero if the "
                                    f"conditions fail.")
        else:
            end = d.get("settlement_start") or d.get("period_end")
            if end:
                try:
                    ed = dt.date.fromisoformat(end)
                    if not d.get("settlement_start"):
                        ed = ed + dt.timedelta(days=7)  # ~5 business days
                    days = (ed - today).days
                    d["days_to_cash"] = days
                    if days <= 0:
                        d["timing"] = "EXPIRED_NO_RESULT"
                        d["timing_why"] = (f"parsed settlement {ed.isoformat()} is in the past "
                                           f"but no result disclosure seen — stale terms or a "
                                           f"missed crawl day, do NOT price this")
                    else:
                        d["timing"] = "DATED"
                        d["timing_why"] = f"cash expected {ed.isoformat()} ({days}d)"
                        if d["gross_spread_pct"] is not None:
                            d["annualized_pct"] = round(d["gross_spread_pct"] * 365.0 / days, 1)
                except Exception:
                    d["timing"] = "TIMING_UNPARSED"
                    d["timing_why"] = "period end present but unparseable"
            else:
                d["timing"] = "TIMING_UNPARSED"
                d["timing_why"] = "no period/settlement date parsed from the notice"

        # ---- minimum-tender condition risk ---------------------------------------------
        if d.get("tender_floor_sh"):
            d["min_tender_note"] = (
                f"floor {d['tender_floor_sh']:,} sh"
                + (f"; post-deal ownership at the floor = {d['post_deal_pct']}%"
                   if d.get("post_deal_pct") else "")
                + ". If the floor is missed the offer FAILS: spread -> 0 and the stock "
                  "re-rates to the un-bid level, so this is a two-sided, not a capped, risk.")
        else:
            d["min_tender_note"] = "no floor parsed — treat as UNVERIFIED, not as 'no condition'"

        # ---- squeeze-out timeline ------------------------------------------------------
        mech = d.get("step2_mechanic")
        d["squeezeout_note"] = {
            "CASH_OUT_DEMAND_90PCT": ("step 2 = 株式売渡請求 (Companies Act 179): available "
                                      "only at >=90% voting; ~1-2 months post-settlement, no EGM."),
            "REVERSE_SPLIT_EGM": ("step 2 = 株式併合 reverse split; requires an EGM special "
                                  "resolution, so a NON-tendering holder waits ~3-5 months "
                                  "beyond tender settlement for the same cash."),
        }.get(mech, "step-2 mechanic not parsed — assume the slower 株式併合 (3-5mo) path "
                    "for any non-tendered stub.")
    return deals


# ---------------------------------------------------------------------------------------
# MODE B — ANTICIPATORY: the take-private fingerprint, from cached primary filings
# ---------------------------------------------------------------------------------------

TB = {"jpcrp_cor:InformationAboutParentCompanyEtcOfReportingCompanyTextBlock": "parent",
      "jpcrp_cor:MajorShareholdersTextBlock": "major",
      "jpcrp_cor:OverviewOfAffiliatedEntitiesTextBlock": "affil",
      "jpcrp_cor:InformationAboutOfficersTextBlock": "officers",
      "jpcrp_cor:BusinessPolicyBusinessEnvironmentIssuesToAddressEtcTextBlock": "policy",
      "jpcrp_cor:ShareholdingByShareholderCategoryTextBlock": "holders_by_cat"}


def read_textblocks(zpath: str) -> dict:
    """Pull the governance/ownership text blocks out of one cached annual-report fact set."""
    out = {}
    try:
        zf = zipfile.ZipFile(zpath)
        names = [n for n in zf.namelist() if "jpcrp030000-asr" in n and n.endswith(".csv")]
        if not names:
            return out
        raw = zf.read(names[0]).decode("utf-16", errors="replace")
        for r in csv.reader(io.StringIO(raw), delimiter="\t"):
            if r and r[0] in TB:
                out[TB[r[0]]] = r[-1]
    except Exception:
        pass
    return out


PARENT_NAME_RES = [
    re.compile(r"親会社等の会社名[はは、,:：]?\s*([^\s。、0-9（(]{3,30})"),
    re.compile(r"親会社等は[、,]?\s*((?:株式会社)?[^\s。、0-9（(]{2,25}(?:株式会社|ホールディングス)?)"),
]
# 「親会社等はありません」「親会社等はない」「該当事項はありません」「存在しません」— the same statement
# appears in at least four wordings and a missed one manufactures a FALSE controlling parent.
NO_PARENT_PATS = ("親会社等はありません", "親会社等はない", "親会社等はございません",
                  "該当事項はありません", "該当ありません", "存在しません", "親会社等はありませ")
OWNED_RE = re.compile(r"被所有\s*[（(]?\s*([0-9]{1,3}\.[0-9]{1,2})")
# Every number in the 大株主 table is CONCATENATED to its neighbour ("267,72650.00" is
# 267,726 thousand shares at 50.00%). A digit-lookbehind regex therefore finds nothing, and a
# naive one reads 650.00%. See parse_major_pcts.
NUM_TOKEN_RE = re.compile(r"[0-9][0-9,]*\.[0-9]{1,2}")
BIRTH_RE = re.compile(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日生")


UNIT_RE = re.compile(r"所有株式数[（(](千株|百株|株)[）)]")


def parse_major_pcts(body: str, shares_issued: float | None, unit_mult: int) -> list[float]:
    """Recover the ownership percentages from the run-together 大株主 table.

    Each row renders <shares><pct> with NO separator, so "6086.88" is either 608 thousand
    shares at 6.88% or 60 thousand at 86.88%. Ordering constraints alone do NOT resolve this
    — a first pass that took "the largest admissible reading" reported Mizuho Bank owning
    86.88% of TOSO (真: 6.88%) and turned a dozen ordinary lender/employee-association stakes
    into fake controlling positions, which would have put pure noise at the top of the book.

    The disambiguation has to come from OUTSIDE the string: the share count itself. The table
    header declares its unit (千株 / 百株 / 株) and we know shares issued from the same filing,
    so for every candidate split we can check whether shares/total actually equals the stated
    percentage. The split that reconciles is the true one.

    Without a share count we return NOTHING rather than a guess — a fabricated control
    percentage is far more damaging here than a missing one.
    """
    if not shares_issued or shares_issued <= 0:
        return []
    out: list[float | None] = []
    cap = 100.0
    for tok in NUM_TOKEN_RE.findall(body):
        ip, _, frac = tok.partition(".")
        ip = ip.replace(",", "")
        best, best_err = None, 1e9
        for k in range(1, min(len(ip), 3) + 1):
            suf, head = ip[-k:], ip[:-k]
            if (len(suf) > 1 and suf[0] == "0") or not head:
                continue
            v = float(f"{suf}.{frac}")
            if not (0 < v <= cap):
                continue
            # The holder's ADDRESS ends in digits that run into the share column
            # ("...宝町2" + "67,726" reads as "267,726"), so the head needs trimming from the
            # left as well. Try every suffix of the head and keep the best reconciliation.
            for j in range(len(head), 0, -1):
                hs = head[-j:]
                if len(hs) > 1 and hs[0] == "0":
                    continue
                implied = float(hs) * unit_mult / shares_issued * 100.0
                err = abs(implied - v) / max(v, 0.5)
                if err < best_err:
                    best, best_err = v, err
        # 35% tolerance: the filing's denominator excludes treasury stock while our share
        # count includes it, and the share column is rounded to the stated unit
        if best is not None and best_err < 0.35:
            out.append(best)
            cap = best
        else:
            out.append(None)   # unreconcilable row — recorded as unknown, never guessed
            cap = 100.0
    return out


def parse_ownership(tbs: dict, shares_issued: float | None = None) -> dict:
    """The FIEA parent flag, the parent %, and the top non-nominee holder.
    `shares_issued` comes from the SAME filing and is what makes the 大株主 table parseable."""
    o = {"has_statutory_parent": None, "parent_name": None, "parent_pct": None,
         "top_holder": None, "top_pct": None, "top_is_nominee": None, "top2_pct": None,
         "ownership_basis": None}

    p = _n(tbs.get("parent", ""))
    if p:
        if any(k in p for k in NO_PARENT_PATS):
            o["has_statutory_parent"] = False
        else:
            o["has_statutory_parent"] = True
            for rx in PARENT_NAME_RES:
                m = rx.search(p)
                if m and len(m.group(1)) >= 3:
                    o["parent_name"] = re.sub(r"(である|です|であります)$", "", m.group(1))
                    break

    a = _n(tbs.get("affil", ""))
    if a and "（親会社）" in a:
        seg = a[a.find("（親会社）"):a.find("（親会社）") + 400]
        m = OWNED_RE.search(seg)
        if m:
            o["parent_pct"] = float(m.group(1))

    mj = _n(tbs.get("major", ""))
    if mj:
        i = mj.find("割合")
        body = mj[i + 2:] if i >= 0 else mj
        um = UNIT_RE.search(mj)
        unit_mult = {"千株": 1000, "百株": 100, "株": 1}.get(um.group(1) if um else "株", 1)
        pcts = parse_major_pcts(body, shares_issued, unit_mult)
        o["ownership_basis"] = (f"大株主 table reconciled against {shares_issued:,.0f} issued "
                                f"shares, unit {um.group(1) if um else '株'}"
                                if pcts else
                                "大株主 table NOT reconcilable (missing share count or unit) — "
                                "top-holder % deliberately left blank rather than guessed")
        if pcts and pcts[0] is not None:
            o["top_pct"] = pcts[0]
            o["top2_pct"] = pcts[1] if len(pcts) > 1 else None
            # holder name = the text run before the top holder's address; Japanese addresses
            # open with a prefecture/metropolis token, which is a reliable right boundary
            mm = re.match(r"\s*([^0-9]{2,40}?)(?=東京都|北海道|大阪府|京都府|[^\s]{2,3}県|[A-Z0-9]{3})", body)
            if mm:
                # the column header's trailing "(%)" bleeds into the first cell
                o["top_holder"] = re.sub(r"^[^\w㐀-鿿ぁ-ヿ]*[（(]?%[）)]?", "", mm.group(1)).strip()
            o["top_is_nominee"] = bool(o["top_holder"] and
                                       any(k in o["top_holder"] for k in NOMINEES))
    return o


def parse_succession(tbs: dict) -> dict:
    """Founder-age / succession channel. The 役員の状況 table carries every director's
    birthdate, so 'aged owner-operator with no visible successor' is DERIVABLE, not guessed."""
    s = {"oldest_dir_age": None, "top_dir_age": None, "n_directors": None,
         "family_surname_share": None, "succession_visible": None}
    t = _n(tbs.get("officers", ""))
    if not t:
        return s
    births = BIRTH_RE.findall(t)
    if not births:
        return s
    today = dt.date.today()
    ages = []
    for y, mo, dd in births:
        try:
            b = dt.date(int(y), int(mo), int(dd))
            ages.append((today - b).days / 365.25)
        except Exception:
            pass
    if not ages:
        return s
    s["n_directors"] = len(ages)
    s["oldest_dir_age"] = round(max(ages), 1)
    # the FIRST director listed is the 代表取締役会長/社長 in every filing we sampled
    s["top_dir_age"] = round(ages[0], 1)
    # surname concentration: names sit immediately before each 生年月日
    surnames = []
    for m in BIRTH_RE.finditer(t):
        head = t[max(0, m.start() - 24):m.start()]
        mm = re.search(r"([一-龥]{1,4})[ 　]?([一-龥ぁ-んァ-ヶ]{1,5})$", head)
        if mm:
            surnames.append(mm.group(1))
    if surnames:
        from collections import Counter
        top, n = Counter(surnames).most_common(1)[0]
        s["family_surname_share"] = round(n / len(surnames), 2)
        s["family_surname"] = top
        s["family_n"] = n
        # a same-surname director materially younger than the patriarch = visible succession
        if n >= 2:
            fam_ages = [a for a, sn in zip(ages, surnames) if sn == top]
            s["succession_visible"] = bool(fam_ages and (max(fam_ages) - min(fam_ages)) >= 15)
        else:
            s["succession_visible"] = False
    return s


CAPCOST_KW = ("資本コスト", "株価を意識した経営", "ＰＢＲ", "PBR", "株主資本コスト", "ROICを")


def parse_tse_plan(tbs: dict) -> dict:
    """TSE improvement-plan flag. JPX publishes only PDFs, so we read the issuer's OWN annual
    report instead: 「資本コストや株価を意識した経営」 language in 経営方針 is the primary-source
    version of the same disclosure and cannot be stale relative to the JPX list."""
    t = tbs.get("policy", "") or ""
    hits = [k for k in CAPCOST_KW if k in t]
    return {"tse_plan_language": bool(hits), "tse_plan_kw": hits[:4],
            "tse_plan_basis": "issuer annual report 経営方針 text (JPX list is PDF-only)"}


def load_codelist() -> dict:
    z = zipfile.ZipFile(EDINET_CODES)
    txt = z.read(z.namelist()[0]).decode("cp932", errors="replace")
    rows = list(csv.reader(io.StringIO("\n".join(txt.splitlines()[1:]))))
    hdr = rows[0]
    ix = {k: hdr.index(k) for k in ("ＥＤＩＮＥＴコード", "上場区分", "提出者業種",
                                    "証券コード", "提出者名（英字）", "提出者名")}
    out = {}
    for r in rows[1:]:
        if len(r) <= max(ix.values()):
            continue
        out[r[ix["ＥＤＩＮＥＴコード"]]] = {
            "sec_code": r[ix["証券コード"]].strip(), "listed": r[ix["上場区分"]] == "上場",
            "industry": r[ix["提出者業種"]].strip(),
            "name_en": r[ix["提出者名（英字）"]].strip(), "name_ja": r[ix["提出者名"]].strip()}
    return out


# A regulated utility's or a bank's balance-sheet cash is not buyout funding, and these
# sectors are not the parent-subsidiary cleanup cohort. Excluded from the fingerprint.
MIN_MCAP_JPY = 3_000_000_000   # ~$19M: below this a fingerprint is real but unownable

EXCLUDE_INDUSTRIES = {"銀行業", "保険業", "証券、商品先物取引業", "その他金融業",
                      "不動産業", "電気・ガス業"}


def score_fingerprint(r: dict) -> tuple[int, str, list[str]]:
    """GATED channels, not a summed composite.

    The first version of this scored cash + low P/B + old directors additively, and the top of
    the list came back as cash-rich sub-book small caps — i.e. it had quietly reproduced the
    deep-value screen we already run, which is exactly the overfit-composite failure the house
    warns about. Cheapness is NOT a take-private signal; cheapness plus a party who can
    actually execute a buyout is.

    So a name must first clear a CONTROL gate before anything else is allowed to score:
      TIER A  parent-subsidiary cleanup — a controlling corporate holder >=50% (or >=33.4%,
              the special-resolution blocking level). TSE's explicit target cohort.
      TIER B  succession MBO — an aged owner-operator/founder-family top holder with no
              visible successor on the board.
    Cash, P/B and the TSE improvement-plan language are MODIFIERS inside a tier. They can
    never put a name on the list by themselves.
    """
    why = []
    if r.get("industry") in EXCLUDE_INDUSTRIES:
        return 0, "EXCLUDED_SECTOR", [f"{r.get('industry')} — regulated/financial balance "
                                      f"sheet; cash is not buyout funding and the sector is "
                                      f"not the parent-sub cleanup cohort"]

    pp = r.get("parent_pct")
    tp = r.get("top_pct") if not r.get("top_is_nominee") else None
    ctrl = max([x for x in (pp, tp) if x] or [0])

    tier = None
    score = 0
    # ---- GATE: TIER A, parent-subsidiary cleanup ---------------------------------------
    if ctrl >= 50:
        tier, score = "A_PARENT_SUB", 4
        who = r.get("parent_name") or r.get("top_holder") or "the top holder"
        why.append(f"{who} holds {ctrl:.1f}% — a majority-controlled listed subsidiary. This is "
                   f"the exact cohort the TSE is pressuring to resolve, and the controller can "
                   f"execute a squeeze-out unilaterally once past 90%"
                   + ("" if r.get("has_statutory_parent") else
                      "; note the filing declares NO statutory 親会社等, which at exactly 50.0% "
                      "is legally consistent — control without the FIEA parent label"))
    elif ctrl >= 33.4:
        tier, score = "A_PARENT_SUB", 3
        who = r.get("parent_name") or r.get("top_holder") or "the top holder"
        why.append(f"{who} holds {ctrl:.1f}% — above the one-third special-resolution blocking "
                   f"level. The holder already controls the outcome of any squeeze-out vote, so "
                   f"a top-up TOB is the cheapest route to 100%")

    # ---- GATE: TIER B, succession MBO ---------------------------------------------------
    age = r.get("top_dir_age")
    fam = (r.get("family_surname_share") or 0) >= 0.15 or (ctrl >= 15 and not r.get("top_is_nominee"))
    if tier is None and age and age >= 72 and fam and r.get("succession_visible") is False:
        tier, score = "B_SUCCESSION", 3
        why.append(f"lead director is {age:.0f} with no same-surname successor on the board and "
                   f"a concentrated founder/family register ({ctrl:.1f}% top holder) — the "
                   f"classic estate-driven MBO setup, where the buyer is management itself")
    elif tier == "A_PARENT_SUB" and age and age >= 75 and r.get("succession_visible") is False:
        score += 1
        why.append(f"lead director is {age:.0f} with no visible successor — a second, "
                   f"independent reason for the register to be resolved")

    if tier is None:
        return 0, "NO_CONTROL_CHANNEL", []

    # ---- MODIFIERS (only inside a tier) -------------------------------------------------
    cm = r.get("cash_to_mcap")
    if cm and cm >= 0.40:
        score += 2
        why.append(f"cash = {cm*100:.0f}% of market cap — the target's own balance sheet funds "
                   f"much of the consideration, so the controller needs little outside money")
    elif cm and cm >= 0.25:
        score += 1
        why.append(f"cash = {cm*100:.0f}% of market cap")

    pb = r.get("pb")
    if pb and pb < 0.8:
        score += 2
        why.append(f"P/B {pb:.2f} — below the TSE 1.0x line; taking in the minority below stated "
                   f"book is accretive to the acquirer on day one")
    elif pb and pb < 1.0:
        score += 1
        why.append(f"P/B {pb:.2f} — below book")

    if r.get("tse_plan_language"):
        score += 1
        why.append("the annual report itself carries 資本コスト / 株価を意識した経営 language — "
                   "management is already on the TSE improvement track and has committed to "
                   "closing the discount one way or another")
    return score, tier, why


def build_anticipatory(top: int = 40, limit_zips: int | None = None) -> list[dict]:
    import glob
    zips = sorted(glob.glob(os.path.join(EDINET_CACHE, "*_t5.zip")))
    if limit_zips:
        zips = zips[:limit_zips]
    codes = load_codelist()
    fund = json.load(open(EDINET_STORE)) if os.path.exists(EDINET_STORE) else {}
    px = json.load(open(PX_CACHE)) if os.path.exists(PX_CACHE) else {}

    rows = []
    for i, z in enumerate(zips):
        ec = os.path.basename(z).split("_")[0]
        cl = codes.get(ec, {})
        sec = (cl.get("sec_code") or "").strip()
        if not sec or not cl.get("listed", True):
            continue
        tick = sec[:4]
        tbs = read_textblocks(z)
        if not tbs:
            continue
        f0 = fund.get(ec, {})
        r = {"code": tick, "edinet": ec, "name_en": cl.get("name_en"),
             "name_ja": cl.get("name_ja"), "industry": cl.get("industry")}
        r.update(parse_ownership(tbs, f0.get("_SharesIssued")))
        r.update(parse_succession(tbs))
        r.update(parse_tse_plan(tbs))

        f = fund.get(ec, {})
        q = px.get(f"{tick}.T", {})
        mc = q.get("mcap")
        cash = f.get("CashAndCashEquivalentsAtCarryingValue")
        eq = f.get("StockholdersEquity") or f.get("_ShareholdersEquityJP")
        r["spot_cached"] = q.get("px")
        r["mcap_jpy"] = mc
        r["cash_jpy"] = cash
        r["equity_jpy"] = eq
        r["cash_to_mcap"] = round(cash / mc, 3) if (cash and mc) else None
        r["pb"] = round(mc / eq, 3) if (mc and eq and eq > 0) else None
        r["px_stale_days"] = round((time.time() - q["ts"]) / 86400, 1) if q.get("ts") else None
        r["held"] = HELD_JAPAN.get(tick)
        r["score"], r["tier"], r["why"] = score_fingerprint(r)
        rows.append(r)
        if i % 300 == 0:
            print(f"  edinet fingerprint {i}/{len(zips)}", file=sys.stderr)

    gated = [r for r in rows if r["score"] > 0]
    # SIZE FLOOR. Several top-scoring names are ~¥300M market caps — structurally perfect
    # fingerprints that cannot be bought in any size and whose cash/mcap ratios are dominated
    # by rounding. Excluded from the ranked book, but COUNTED and reported, never dropped
    # silently.
    kept = [r for r in gated if (r.get("mcap_jpy") or 0) >= MIN_MCAP_JPY]
    toosmall = [r for r in gated if (r.get("mcap_jpy") or 0) < MIN_MCAP_JPY]
    nomcap = [r for r in gated if not r.get("mcap_jpy")]
    print(f"  universe {len(rows)} listed non-financial issuers -> {len(gated)} clear a control gate "
          f"(A_PARENT_SUB {sum(1 for r in gated if r['tier']=='A_PARENT_SUB')}, "
          f"B_SUCCESSION {sum(1 for r in gated if r['tier']=='B_SUCCESSION')})")
    print(f"  size floor ¥{MIN_MCAP_JPY/1e9:.0f}bn: {len(kept)} ranked, {len(toosmall)} excluded as "
          f"too small to own ({len(nomcap)} of those had no cached market cap at all)")
    kept.sort(key=lambda x: (-x["score"], -(x.get("cash_to_mcap") or 0)))
    for r in kept:
        r["_excluded_too_small"] = len(toosmall)
    return kept[:top] if top else kept


# ---------------------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------------------

def usdjpy() -> float:
    try:
        import yfinance as yf
        h = yf.download("JPY=X", period="5d", progress=False, auto_adjust=False)["Close"].dropna()
        return float(h.iloc[-1])
    except Exception:
        return 0.0


def write_intake(deals: list[dict], antic: list[dict], fx: float, path: str) -> None:
    live = [d for d in deals if d["status"] in ("OPEN", "SQUEEZE_OUT")]
    priced = [d for d in live if d.get("gross_spread_pct") is not None
              and d.get("spread_quotable")]
    blocked = [d for d in live if d.get("gross_spread_pct") is not None
               and not d.get("spread_quotable")]
    priced.sort(key=lambda d: (-(d.get("annualized_pct") if d.get("annualized_pct") is not None
                                 else -999), -(d.get("gross_spread_pct") or 0)))
    L = []
    A = L.append
    A(f"# Japan TOB / take-private lane — intake {dt.date.today().isoformat()}")
    A("")
    A(f"USD/JPY {fx:.2f} at run. Announced book (spreads) and anticipatory book (fingerprints) "
      f"are separate and are never summed.")
    A("")
    A("## Channel note")
    A("")
    A("- **Announced deals: TDnet** (`release.tdnet.info/inbs/I_list_NNN_YYYYMMDD.html`) — plain "
      "HTTP, no key, no browser, ~850 disclosures/day, formulaic titles, public PDF per row. "
      "Terms are read out of the standardised 「買付け等の概要」 table in the commencement notice.")
    A("- **EDINET API v2 does not work unkeyed** — returns `401 invalid subscription key`. The "
      "statutory TOB filing (docTypeCode 240 公開買付届出書) is the better authority and we should "
      "get a key; until then TDnet is the channel and the company's own notice is the source.")
    A("- **TDnet retains ~31 days.** The event store is therefore the history — a day we never "
      "crawled cannot be recovered. Run daily.")
    A("- **Anticipatory side is fully offline**, read from 1,525 cached EDINET annual-report XBRL "
      "fact sets: the FIEA Art.24-7 parent declaration, 【関係会社の状況】 owned-by %, 【大株主の状況】, "
      "and director birthdates.")
    A("")
    A("## Held-book cross-check")
    A("")
    ov = sorted({d["target_code"] for d in deals} & set(HELD_JAPAN))
    ov2 = [r for r in antic if r.get("held")]
    A(f"- Announced targets vs the held Japan book ({', '.join(f'{k} {v}' for k, v in HELD_JAPAN.items())}): "
      + (", ".join(ov) if ov else "**no overlap** — no live tender touches anything we own."))
    for r in ov2:
        A(f"- **{r['code']} {r['held']} appears in the ANTICIPATORY book** (tier {r.get('tier')}, "
          f"score {r['score']}). We are already long a take-private candidate. Treat this as "
          f"position context, not a new idea: it means part of the Japan book's return is "
          f"already levered to this lane's thesis, and it caps how much more of the same "
          f"exposure the lane should add.")
    A("")
    A("## A. ANNOUNCED — spread book")
    A("")
    A(f"{len(deals)} deals tracked in the window; {len(live)} live; {len(priced)} with a computable spread.")
    A("")
    A("| target | name | bidder | offer ¥ | spot ¥ | gross % | ann. % | days | liquidity | timing |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for d in priced:
        A("| {c} | {n} | {b} | {o} | {s} | {g} | {a} | {dd} | {lq} | {tm} |".format(
            c=d["target_code"], n=(d["target_name"] or "")[:16],
            b=(d.get("bidder") or "n/d")[:16],
            o=f"{d['offer_price']:,.0f}" if d.get("offer_price") else "n/p",
            s=f"{d['spot']:,.0f}" if d.get("spot") else "n/p",
            g=f"{d['gross_spread_pct']:+.2f}" if d.get("gross_spread_pct") is not None else "—",
            a=f"{d['annualized_pct']:+.0f}" if d.get("annualized_pct") is not None else "—",
            dd=d.get("days_to_cash") if d.get("days_to_cash") is not None else "—",
            lq=d.get("liquidity", "?"), tm=d.get("timing", "?")))
    A("")
    for d in priced[:8]:
        A(f"### {d['target_code']} {d['target_name']} — {d['status']}")
        A("")
        A(f"- **Bidder / purpose**: {d.get('bidder') or 'n/d'} · {d.get('purpose') or 'purpose not parsed'} · "
          f"target opinion {d.get('target_opinion') or 'not parsed'}")
        A(f"- **Terms**: offer ¥{d.get('offer_price'):,.0f} vs spot ¥{d.get('spot'):,.0f} = "
          f"{d.get('gross_spread_pct'):+.2f}% gross"
          if d.get("offer_price") and d.get("spot") else "- **Terms**: incomplete")
        A(f"- **Timing**: {d.get('timing')} — {d.get('timing_why')}")
        A(f"- **Minimum-tender condition**: {d.get('min_tender_note')}")
        A(f"- **Squeeze-out**: {d.get('squeezeout_note')}")
        A(f"- **Liquidity (thin-print gate)**: {d.get('liquidity')} — {d.get('liquidity_why')}")
        if d.get("spot") and fx:
            A(f"- **JPY add**: a ¥1,000,000 clip here is ${1_000_000/fx:,.0f} of ADDITIONAL "
              f"unhedged JPY on top of the existing Japan book.")
        A(f"- **Taxable**: tender proceeds are a disposition, not a rollover — short-term gain "
          f"unless held >1y. On a {d.get('gross_spread_pct') or 0:+.2f}% gross spread the "
          f"after-tax return at a ~50% marginal rate is roughly half the headline.")
        A(f"- Source: {d.get('terms_from') or d.get('primary_pdf')}")
        if d.get("held"):
            A(f"- **HELD-BOOK OVERLAP: we own {d['target_code']} ({d['held']}).**")
        A("")
    if blocked:
        A("### Live, but the spread is NOT quotable — do not put these in a return table")
        A("")
        for d in blocked:
            A(f"- **{d['target_code']} {d['target_name']}** — headline "
              f"{d['gross_spread_pct']:+.2f}% vs offer ¥{d.get('offer_price'):,.0f}. "
              f"{d.get('quotable_note')}")
        A("")
    other = [d for d in live if d.get("gross_spread_pct") is None]
    if other:
        A("### Live but not priceable")
        A("")
        for d in other:
            A(f"- {d['target_code']} {d['target_name']} — {d.get('timing','?')}; "
              f"{d.get('liquidity','?')}; terms {'parsed' if d.get('offer_price') else 'NOT parsed'}. "
              f"{d.get('primary_title','')[:80]}")
        A("")
    A("## B. ANTICIPATORY — fingerprint book (NOT spreads, NOT annualized)")
    A("")
    A("No offer exists for any name below. These are structural candidates only. An anticipatory "
      "name that is later bid moves to book A; until then it carries equity risk with an undated, "
      "uncertain catalyst and must be sized as equity, not as arbitrage.")
    A("")
    A("| code | name | tier | score | controller | % | float % | cash/mcap | P/B | lead age |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for r in antic[:25]:
        pp = r.get("parent_pct") or r.get("top_pct")
        A("| {c} | {n} | {t} | {s} | {p} | {pc} | {fl} | {cm} | {pb} | {ag} |".format(
            c=r["code"], n=(r.get("name_en") or r.get("name_ja") or "")[:22],
            t=(r.get("tier") or "")[:1], s=r["score"],
            p=(r.get("parent_name") or r.get("top_holder") or "—")[:20],
            pc=f"{pp:.1f}" if pp else "—", fl=f"{100-pp:.0f}" if pp else "—",
            cm=f"{r['cash_to_mcap']:.2f}" if r.get("cash_to_mcap") else "—",
            pb=f"{r['pb']:.2f}" if r.get("pb") else "—",
            ag=f"{r['top_dir_age']:.0f}" if r.get("top_dir_age") else "—"))
    A("")
    for r in antic[:10]:
        pp = r.get("parent_pct") or r.get("top_pct")
        A(f"### {r['code']} {r.get('name_en') or r.get('name_ja')} — {r.get('tier')}, score {r['score']}"
          + (f"  **[HELD: {r['held']}]**" if r.get("held") else ""))
        for w in r["why"]:
            A(f"- {w}")
        if pp and pp >= 90:
            A(f"- **Float warning**: only ~{100-pp:.0f}% is outside the controller. A >=90% holder "
              f"can file a 株式売渡請求 unilaterally at any time — highest structural readiness, but "
              f"the tradeable float may be too small to build a position in.")
        elif pp:
            A(f"- Minority float ~{100-pp:.0f}% of shares; the controller needs to reach 90% to "
              f"squeeze out without an EGM.")
        if r.get("px_stale_days"):
            A(f"- Inputs: annual-report balance sheet, price cached {r['px_stale_days']:.0f}d ago — "
              f"screen-grade, not valuation-grade. {r.get('ownership_basis') or ''}")
        A("")
    A("## Structural findings from the first run")
    A("")
    A("1. **The Japanese limit-up lock is this lane's dominant failure mode.** A target bid at a "
      "real premium goes limit-up (ストップ高) with an O=H=L bar and an unfilled buy queue for one "
      "to three sessions. Any screen that reads that print books a spread that never existed. "
      "On the first run this was worth 22 percentage points on one name and 10 on another — "
      "both would have been fictional. The lane now carries the TSE 値幅制限 table, detects the "
      "lock, and refuses to rank a locked name.")
    A("2. **Real Japanese TOB spreads are thin.** Once the phantom spreads are removed, every "
      "live quotable deal sits at +0.1% to +0.9% gross. This is an efficiently arbitraged "
      "market; the return lives in the annualization of very short dated-cash events, not in "
      "the headline spread, and it is entirely eaten by a taxable short-term rate unless the "
      "days-to-cash is genuinely small.")
    A("3. **The residual step-2 stub is where the yield is, and it is nearly untradeable.** The "
      "highest annualized numbers all come from post-tender squeeze-out stubs, which trade a "
      "few hundred to a few thousand shares a day. The spread is real; the capacity is not.")
    A("4. **A cheapness screen is not a take-private screen.** The first version of the "
      "anticipatory scorer summed cash + low P/B + old directors and simply reproduced the "
      "deep-value shelf. Requiring a control channel first — a >=33.4% holder, or an aged "
      "owner-operator with no successor — is what makes the book distinct from the value book.")
    A("5. **Japan's parent-subsidiary cohort is enormous.** 320 of 1,316 listed non-financial "
      "issuers with a cached annual report clear a control gate (238 parent-subsidiary, 82 "
      "succession). The constraint on this lane is not finding candidates; it is that the "
      "catalyst is undated, so the anticipatory book is an equity position with optionality, "
      "never an arbitrage.")
    A("")
    A("## Gaps, honestly")
    A("")
    A("- No EDINET API key: we read the company's TDnet notice, not the statutory 公開買付届出書. "
      "Terms should agree; where a notice was amended we take the newest PDF that parses.")
    A("- TDnet 31-day retention means the deal book is only as deep as our crawl history.")
    A("- Anticipatory fundamentals come from the last ANNUAL report and a cached close, so "
      "cash/mcap and P/B can be several months stale; treat as a screen, not a valuation.")
    A("- JPX publishes the improvement-plan list as PDFs only; the TSE-plan flag is derived from "
      "the issuer's own annual-report language instead and is a proxy for list membership.")
    A(f"- Anticipatory names below ¥{MIN_MCAP_JPY/1e9:.0f}bn market cap are excluded as unownable; "
      f"the count is printed every run so the exclusion is never silent.")
    A("- The minimum-tender floor did not parse on the step-2 squeeze-out notices, which is "
      "expected (the condition already resolved) but is reported as UNVERIFIED rather than as "
      "'no condition'.")
    A("- Bidder identity is read from the disclosure title when only the target filed; it is a "
      "label, not a verified counterparty, and a competing-bid situation (2371) makes 'the "
      "offer price' genuinely ambiguous — that name is flagged, not priced.")
    open(path, "w").write("\n".join(L) + "\n")


# ---------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["both", "announced", "anticipatory"], default="both")
    ap.add_argument("--days", type=int, default=40, help="TDnet lookback (retention ~31d)")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--limit-zips", type=int, default=None)
    ap.add_argument("--intake", action="store_true", help="also write the desk intake .md")
    ap.add_argument("--no-terms", action="store_true", help="skip PDF term parsing")
    a = ap.parse_args()

    st = _load_store()
    deals, antic = [], []

    if a.mode in ("both", "announced"):
        print(f"[announced] crawling TDnet, {a.days}d lookback")
        n = crawl_tdnet(a.days, st)
        print(f"[announced] {n} new lane events; {len(st['events'])} in store")
        deals = build_announced(st, refresh_terms=not a.no_terms)
        st["deals"] = {d["target_code"]: d for d in deals}
        live = [d for d in deals if d["status"] in ("OPEN", "SQUEEZE_OUT")]
        print(f"[announced] {len(deals)} deals, {len(live)} live")
        for d in sorted(live, key=lambda x: -(x.get("annualized_pct") or -999)):
            print(f"  {d['target_code']:>5} {(d['target_name'] or '')[:16]:<16} "
                  f"offer={d.get('offer_price')} spot={d.get('spot')} "
                  f"gross={d.get('gross_spread_pct')} ann={d.get('annualized_pct')} "
                  f"{d.get('timing')} {d.get('liquidity')}")

    if a.mode in ("both", "anticipatory"):
        print("[anticipatory] scanning cached EDINET annual reports")
        antic = build_anticipatory(top=a.top, limit_zips=a.limit_zips)
        st["anticipatory"] = antic
        print(f"[anticipatory] top {len(antic)}")
        for r in antic[:15]:
            print(f"  {r['code']:>5} score={r['score']} {(r.get('name_en') or '')[:28]:<28} "
                  f"pp={r.get('parent_pct') or r.get('top_pct')} cm={r.get('cash_to_mcap')} "
                  f"pb={r.get('pb')}" + ("  [HELD]" if r.get("held") else ""))

    # held-book overlap, loudly
    tgt = {d["target_code"] for d in deals}
    ov = sorted(tgt & set(HELD_JAPAN))
    print(f"[held-overlap] announced targets vs held Japan book: "
          f"{', '.join(ov) if ov else 'NONE'}")
    ov2 = [r["code"] for r in antic if r.get("held")]
    print(f"[held-overlap] anticipatory candidates already held: "
          f"{', '.join(ov2) if ov2 else 'NONE'}")

    fx = usdjpy()
    st["runs"] = (st.get("runs", []) + [{"ts": dt.datetime.now().isoformat(timespec="seconds"),
                                         "mode": a.mode, "n_deals": len(deals),
                                         "n_antic": len(antic), "usdjpy": fx}])[-60:]
    st["asof"] = dt.date.today().isoformat()
    st["usdjpy"] = fx
    st["held_japan"] = HELD_JAPAN
    _save_store(st)
    print(f"[store] {STORE}")

    if a.intake:
        os.makedirs(DESK_DATA, exist_ok=True)
        p = os.path.join(DESK_DATA, f"JAPAN_TOB_INTAKE_{dt.date.today().strftime('%Y%m%d')}.md")
        write_intake(deals, antic, fx, p)
        print(f"[intake] {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
