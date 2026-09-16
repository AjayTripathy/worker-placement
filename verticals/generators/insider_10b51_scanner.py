"""insider_10b51_scanner — Stage 0b INFO/nowcast: insider BUY CLUSTERS + Rule 10b5-1 PLAN TERMINATIONS (EDGAR).

Primary-source nowcast off two SEC channels that LEAD the tape:

  (a) OPEN-MARKET BUY CLUSTERS (primary leg — structured, reliable). Recent Form 4s (EFTS forms=4 feed) ->
      fetch the ownership XML -> parse nonDerivativeTransaction code 'P' / acquired 'A' open-market buys ->
      cluster by issuer: a CLUSTER = >=2 DISTINCT reporting owners buying within a ~10-day window. Each buy is
      tagged with the Rule 10b5-1 indicator (<aff10b5One> checkbox + a "Rule 10b5-1" footnote) — a CLUSTER of
      NON-plan (discretionary) buys is the stronger conviction tell; plan-driven buys are pre-scheduled and carry
      less signal. USD-sized, small/mid-cap focus (mega-cap insider buys are noise the whole market already sees).

  (b) 10b5-1 PLAN TERMINATIONS (v1 / best-effort). An insider KILLING a pre-set trading plan (disclosed as
      free-text under Reg S-K Item 408 in 10-Q/10-K, and on 8-K) is a notable tell — plans are disproportionately
      terminated AHEAD of material events. EFTS full-text search on 10-Q/10-K/8-K for the "Rule 10b5-1" + a
      terminate-stem co-occurrence, returned as issuer + filing url + snippet. Item 408 language is unstructured,
      so this leg is explicitly v1 — a REVIEW queue (resolve the plan holder + the event in DD), not a fire.

HONESTY DOCTRINE (inherited from insider_cluster_scanner, the priced-in debate + the 2026-07-02 drift backtest =
NULL for small-cap clusters): Form 4s are maximally public — NO clean informational edge is claimed. The value is
(1) ATTENTION ALLOCATION — point scarce diligence at conditioned subsets; (2) the 10b5-1 DIMENSION this scanner
adds on top of the plain cluster scanner: discretionary-vs-plan tagging + the termination REVIEW queue. Narrow &
high-precision by design (recall-floor discipline): a handful of genuine clusters + real terminations beats a wall
of single-insider / plan-driven noise. The scanner proposes; it never sizes and never orders.

    python3 verticals/generators/insider_10b51_scanner.py [--days 10] [--pages 4]
Writes data/INSIDER_10B51.json. READ-ONLY.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "INSIDER_10B51.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

EFTS = "https://efts.sec.gov/LATEST/search-index"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

MIN_BUY_USD = 50_000        # per reporting-owner floor — below this is not a conviction buy
CLUSTER_WINDOW_D = 10       # >=2 distinct owners within this trailing window = a cluster
CLUSTER_MAX_MCAP_HINT = None  # mktcap gating is a v2 overlay (see caveats); here we drop obvious mega-caps by name
# free-text terminate stems paired with "Rule 10b5-1" for the (b) leg. Kept TIGHT (co-occurrence, not just "plan").
TERM_QUERY = '%22Rule+10b5-1%22+terminated'
TERM_FORMS = "10-Q,10-K,8-K"
# fund/LP Form 4s are mechanics, not insider conviction — same guard the plain cluster scanner uses
FUND_MARKERS = (" FUND", " L.P", " LP,", " LP ", "CAPITAL INCOME", "INFRASTRUCTURE STRATEGIES", " TRUST ")
# crude mega-cap drop by issuer name so the cluster leg stays small/mid focused (the capacity niche)
MEGA_MARKERS = ()  # intentionally empty — we gate by USD/name-fund only; mktcap gating is a v2 yfinance overlay


def _get(url: str, retries: int = 2, timeout: int = 30) -> bytes | None:
    for _ in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            time.sleep(1.2)     # be polite to EDGAR on 429/timeout
    return None


def _get_json(url: str, retries: int = 2) -> dict:
    raw = _get(url, retries=retries)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _ticker_map() -> dict:
    """CIK(int) -> {'ticker','title'} from the SEC canonical map."""
    d = _get_json(TICKERS_URL)
    out = {}
    for _, row in (d or {}).items():
        try:
            out[int(row["cik_str"])] = {"ticker": row["ticker"].upper(), "title": row["title"]}
        except Exception:
            continue
    return out


def _efts_form4_hits(days: int, pages: int) -> list[dict]:
    """Recent Form 4 filings from the EFTS full-text index (dated window, bounded pages)."""
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=days)).isoformat()
    end = today.isoformat()
    hits, seen = [], set()
    for page in range(pages):
        params = {"q": '"purchase"', "forms": "4", "startdt": start, "enddt": end}
        if page:
            params["from"] = page * 100     # EFTS returns up to 100/page
        # NOTE: do NOT mark '"' safe — a raw quote in the URL 400s; urlencode must escape it to %22
        url = EFTS + "?" + urllib.parse.urlencode(params)
        d = _get_json(url)
        page_hits = (((d or {}).get("hits") or {}).get("hits")) or []
        if not page_hits:
            break
        for h in page_hits:
            adsh = (h.get("_source") or {}).get("adsh")
            _id = h.get("_id", "")
            if _id in seen:
                continue
            seen.add(_id)
            hits.append(h)
        time.sleep(0.4)
    return hits


def _accession_xml_url(hit: dict) -> str | None:
    """Build the primary-doc XML URL from an EFTS hit (_id = 'accession:document.xml')."""
    src = hit.get("_source") or {}
    ciks = src.get("ciks") or []
    adsh = src.get("adsh") or ""
    _id = hit.get("_id") or ""
    doc = _id.split(":", 1)[1] if ":" in _id else ""
    if not (adsh and doc and ciks):
        return None
    acc_nodash = adsh.replace("-", "")
    # the FILER CIK (the reporting owner) is usually the last in ciks; the archives path works off any of them,
    # but the doc lives under the filing's own accession dir — try each cik until one resolves.
    for cik in ciks:
        yield_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{doc}"
        return yield_url  # first cik path is canonical for Form 4 ownership docs
    return None


def _parse_form4(xml_bytes: bytes) -> dict | None:
    """Open-market (code-P / acquired-A) purchase summary from one Form 4 ownership XML, or None."""
    txt = xml_bytes.decode("latin-1", "ignore")
    # ownership.xml is bare XML; some legacy docs wrap in <XML>..</XML>
    m = re.search(r"<XML>(.*?)</XML>", txt, re.S | re.I)
    body = m.group(1).strip() if m else txt.strip()
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None
    issuer = (root.findtext(".//issuerName") or "").strip()
    sym = (root.findtext(".//issuerTradingSymbol") or "").upper().strip()
    owner = (root.findtext(".//rptOwnerName") or "").strip()
    officer = (root.findtext(".//isOfficer") or "0") in ("1", "true")
    director = (root.findtext(".//isDirector") or "0") in ("1", "true")
    date = (root.findtext(".//periodOfReport") or "").strip()
    buy_usd = 0.0
    for tr in root.iter("nonDerivativeTransaction"):
        code = tr.findtext(".//transactionCode") or ""
        acq = tr.findtext(".//transactionAcquiredDisposedCode/value") or ""
        if code == "P" and acq == "A":
            sh = float(tr.findtext(".//transactionShares/value") or 0)
            px = float(tr.findtext(".//transactionPricePerShare/value") or 0)
            buy_usd += sh * px
    if buy_usd < MIN_BUY_USD or not sym or sym in ("NONE", "N/A", "NA", "-"):
        return None
    if any(k in issuer.upper() for k in FUND_MARKERS):
        return None
    # Rule 10b5-1 indicator: the aff10b5One checkbox OR a "Rule 10b5-1" footnote. Discretionary (NOT plan) buys
    # are the stronger conviction tell; a plan-driven buy is pre-scheduled and carries less signal.
    aff = (root.findtext(".//aff10b5One") or "").strip().lower()
    fn_10b51 = bool(re.search(r"rule\s*10b5[- ]?1", txt, re.I))
    under_10b51 = aff in ("true", "1") or fn_10b51
    return {"symbol": sym, "issuer": issuer[:60], "owner": owner[:40],
            "role": "officer" if officer else "director" if director else "10%+",
            "buy_usd": round(buy_usd), "date": date, "under_10b51": under_10b51}


def _scan_buy_clusters(days: int, pages: int) -> tuple[list[dict], int, int]:
    """Return (clusters, n_form4_parsed, n_buys). A cluster = >=2 distinct owners, code-P, within the window."""
    tmap = _ticker_map()
    hits = _efts_form4_hits(days, pages)
    buys = []
    for i, h in enumerate(hits):
        url = _accession_xml_url(h)
        if not url:
            continue
        raw = _get(url)
        if not raw:
            continue
        r = _parse_form4(raw)
        if r:
            # confirm ticker/name via the SEC map when the XML symbol is thin
            src = h.get("_source") or {}
            for cik in src.get("ciks") or []:
                info = tmap.get(int(cik))
                if info and (not r["symbol"] or r["symbol"] in ("NONE", "NA")):
                    r["symbol"] = info["ticker"]
                    break
            buys.append(r)
        if i % 6 == 5:
            time.sleep(0.4)     # SEC-safe pace
    # dedupe (owner/symbol/date/usd) — EFTS can surface the same doc twice
    seen, uniq = set(), []
    for b in buys:
        key = (b["symbol"], b["owner"], b["date"], b["buy_usd"])
        if key not in seen:
            seen.add(key)
            uniq.append(b)
    # cluster within the window
    win = (datetime.date.today() - datetime.timedelta(days=CLUSTER_WINDOW_D)).isoformat()
    recent = [b for b in uniq if (b["date"] or "9999") >= win]
    by_sym: dict[str, list] = {}
    for b in recent:
        by_sym.setdefault(b["symbol"], []).append(b)
    clusters = []
    for sym, bs in by_sym.items():
        owners = {b["owner"] for b in bs}
        if len(owners) < 2:
            continue
        dates = sorted(b["date"] for b in bs if b["date"])
        n_plan = sum(1 for b in bs if b["under_10b51"])
        clusters.append({
            "ticker": sym, "name": bs[0]["issuer"], "n_insiders": len(owners),
            "total_usd": sum(b["buy_usd"] for b in bs),
            "first": dates[0] if dates else "", "last": dates[-1] if dates else "",
            "under_10b51": n_plan,           # how many of the buys were plan-driven (lower conviction)
            "roles": sorted({b["role"] for b in bs}),
            "note": ("DISCRETIONARY cluster (no 10b5-1 tag) — stronger conviction tell"
                     if n_plan == 0 else
                     f"{n_plan}/{len(bs)} buys were 10b5-1 plan-driven (pre-scheduled, weaker tell)"),
            "buys": sorted(bs, key=lambda x: -x["buy_usd"])[:6],
        })
    # discretionary clusters first, then by size — the recall-floor: precision over count
    clusters.sort(key=lambda c: (c["under_10b51"] > 0, -c["n_insiders"], -c["total_usd"]))
    return clusters, len(uniq), len(recent)


def _scan_terminations(days: int) -> list[dict]:
    """v1/best-effort: EFTS full-text 'Rule 10b5-1' + terminate-stem on 10-Q/10-K/8-K -> issuer + url + snippet."""
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=days)).isoformat()
    end = today.isoformat()
    url = (EFTS + "?" + urllib.parse.urlencode(
        {"forms": TERM_FORMS, "startdt": start, "enddt": end}, safe="") + f"&q={TERM_QUERY}")
    d = _get_json(url)
    hits = (((d or {}).get("hits") or {}).get("hits")) or []
    out, seen = [], set()
    for h in hits:
        src = h.get("_source") or {}
        names = src.get("display_names") or []
        name = names[0] if names else ""
        # pull the ticker out of "NAME  (TICK)  (CIK ...)" when present
        tm = re.search(r"\(([A-Z.\-]{1,6})\)", name)
        ticker = tm.group(1) if tm else ""
        adsh = src.get("adsh") or ""
        _id = h.get("_id") or ""
        if adsh in seen:
            continue
        seen.add(adsh)
        doc = _id.split(":", 1)[1] if ":" in _id else ""
        ciks = src.get("ciks") or []
        acc_nodash = adsh.replace("-", "")
        filing_url = (f"https://www.sec.gov/Archives/edgar/data/{int(ciks[0])}/{acc_nodash}/{doc}"
                      if ciks and doc else
                      f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&filenum=&accession_number={adsh}")
        out.append({
            "ticker": ticker, "name": re.sub(r"\s*\(.*", "", name).strip()[:60],
            "form": src.get("form", ""), "date": src.get("file_date", ""), "url": filing_url,
            "snippet": "co-occurrence of 'Rule 10b5-1' + 'terminated' in this filing — resolve the plan holder + "
                       "the pending event in DD (Item 408 language is free-text; verify it is a plan TERMINATION, "
                       "not a routine adoption/expiry).",
        })
    out.sort(key=lambda r: (r["date"] or ""), reverse=True)
    return out


def scan(days: int, pages: int) -> dict:
    today = datetime.date.today()
    clusters, n_parsed, n_buys = _scan_buy_clusters(days, pages)
    terms = _scan_terminations(days)
    return {
        "asof": today.isoformat(), "window_days": CLUSTER_WINDOW_D, "lookback_days": days,
        "form4_buys_in_window": n_buys, "n_buy_clusters": len(clusters), "n_plan_terminations": len(terms),
        "buy_clusters": clusters, "plan_terminations": terms,
        "note": "TWO SEC-primary legs. (a) BUY CLUSTERS: >=2 distinct insiders, code-P open-market, >=$50k each, "
                f"within {CLUSTER_WINDOW_D}d; each buy tagged with the Rule 10b5-1 indicator — a DISCRETIONARY "
                "(non-plan) cluster is the stronger conviction tell (under_10b51 counts the plan-driven buys). "
                "(b) PLAN TERMINATIONS (v1/best-effort): EFTS full-text 'Rule 10b5-1'+'terminated' on 10-Q/10-K/8-K "
                "-> a REVIEW queue (Item 408 is free-text; DD must confirm it is a termination, not adoption/expiry). "
                "DOCTRINE: Form 4s are maximally public — no clean informational edge; value = attention allocation + "
                "the 10b5-1 dimension. Narrow/high-precision by design. Proposes, never sizes. READ-ONLY.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=10, help="lookback window (days) for Form 4s + terminations")
    ap.add_argument("--pages", type=int, default=4, help="EFTS Form 4 pages to pull (100/page, bounded)")
    a = ap.parse_args()
    res = scan(a.days, a.pages)
    print(f"=== INSIDER 10b5-1 SCANNER  {res['asof']}  "
          f"({res['form4_buys_in_window']} code-P buys in the {res['window_days']}d window; "
          f"{res['n_buy_clusters']} clusters; {res['n_plan_terminations']} 10b5-1 termination hits) ===")
    if res["buy_clusters"]:
        print(f"  BUY CLUSTERS (>=2 distinct insiders, >=${MIN_BUY_USD/1000:.0f}k each — DISCRETIONARY first):")
        for c in res["buy_clusters"][:12]:
            tag = "DISCR" if c["under_10b51"] == 0 else f"{c['under_10b51']}x-plan"
            print(f"   {c['ticker']:<6} {c['name'][:34]:<34} {c['n_insiders']} insiders  "
                  f"${c['total_usd']:>10,}  [{tag:<7}] {c['first']}..{c['last']}  ({'/'.join(c['roles'])})")
    else:
        print("  no buy clusters in the window (honest null — single-insider buys are not surfaced)")
    if res["plan_terminations"]:
        print("  10b5-1 PLAN TERMINATION hits (v1/best-effort — REVIEW queue, confirm in DD):")
        for t in res["plan_terminations"][:10]:
            tk = t["ticker"] or "?"
            print(f"   {tk:<6} {t['name'][:34]:<34} {t['form']:<5} {t['date']}  {t['url']}")
    else:
        print("  no 'Rule 10b5-1'+'terminated' filing hits in the window")
    print("  PROMOTE: trap-screen the DISCRETIONARY small/mid clusters first; termination hits -> DD resolves the")
    print("  plan holder + the pending event. DOCTRINE: no edge claimed on public Form 4s; attention-allocation + the")
    print("  10b5-1 dimension. The scanner proposes; it never sizes.")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
