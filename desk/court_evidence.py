"""court_evidence — the deterministic evidence pack every bench gets BEFORE arguing.

Born from the 2026-08-07 campaign postmortem: the blue benches' overturns were almost all
MACHINE-LAYER errors by the reds (grep artifacts, wrong print dates, stale tape anchors,
missed filings, SBC double-counts, a phantom 2.9% position) — facts a deterministic pass
assembles once, correctly, for both benches to share. The dataroom_dd isomorphism: this is
the court's Stage 1-3 (inventory + external battery); benches are Stage 5 (judgment only).

Pack contents (all primary, all dated):
  FILINGS    last 15 EDGAR filings (form/date/accession) — kills "no filing since X" errors
  XBRL       last 8 quarters of revenue, SBC, diluted shares, OCF — kills double-count fights
  TAPE       live px + 52wk hi/lo + drawdown AND pct-off-low + 26wk high — kills stale anchors
  PRINT      next earnings date + confidence label — kills wrong-date courts (print proximity)
  BOOK       do we HOLD it + resting orders — kills phantom-position adjudications (CRM)

  from desk.court_evidence import build_pack, render_pack
  md = render_pack(build_pack("DOCU"))   # injected by court_runner into RED and BLUE prompts
"""
from __future__ import annotations

import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "desk research 4tripathy@gmail.com"
XBRL_TAGS = [
    ("Revenues", "rev"), ("RevenueFromContractWithCustomerExcludingAssessedTax", "rev"),
    ("ShareBasedCompensation", "sbc"),
    ("WeightedAverageNumberOfDilutedSharesOutstanding", "dil_sh"),
    ("NetCashProvidedByUsedInOperatingActivities", "ocf"),
]


def _get(url: str) -> dict | None:
    r = subprocess.run(["curl", "-s", "--max-time", "20", url, "-H", f"User-Agent: {UA}"],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def _cik(ticker: str) -> int | None:
    d = _get("https://www.sec.gov/files/company_tickers.json") or {}
    for v in d.values():
        if v.get("ticker", "").upper() == ticker.upper():
            return v["cik_str"]
    return None


def build_pack(ticker: str) -> dict:
    pack = {"ticker": ticker, "built": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"}
    cik = _cik(ticker)
    pack["cik"] = cik
    if cik:
        sub = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json") or {}
        pack["entity"] = sub.get("name")
        r = sub.get("filings", {}).get("recent", {})
        pack["filings"] = [
            {"form": f, "date": d, "acc": a, "doc": p}
            for f, d, a, p in list(zip(r.get("form", []), r.get("filingDate", []),
                                       r.get("accessionNumber", []),
                                       r.get("primaryDocument", [])))[:15]]
        # Primary-doc excerpt via full-fingerprint fetch (wired 2026-08-11 after every bench
        # in the 8/09-8/11 batch reported sec.gov 403s; FVRR cohort ambiguity was resolvable
        # only from the 6-K exhibit text). Degrades LOUD, never silently.
        try:
            from desk.sec_fetch import fetch as _sec_fetch
            import re as _re, html as _html
            sub_doc = next((f for f in pack["filings"]
                            if f["form"] in ("10-Q", "10-K", "6-K", "8-K", "20-F") and f["doc"]), None)
            if sub_doc:
                acc_nodash = sub_doc["acc"].replace("-", "")
                url = (f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                       f"{acc_nodash}/{sub_doc['doc']}")
                raw = _sec_fetch(url)

                def _plain(h):
                    t = _re.sub(r"<[^>]+>", " ", h)
                    return _re.sub(r"\s+", " ", _html.unescape(t)).strip()
                txt = _plain(raw)
                # 6-K/8-K primary docs are often cover shells — the content is in exhibits
                if len(txt) < 3000:
                    ex = _re.search(r'href="([^"]*(?:ex|exhibit)[^"]*\.htm[^"]*)"', raw, _re.I)
                    if ex:
                        ex_url = url.rsplit("/", 1)[0] + "/" + ex.group(1).lstrip("./")
                        txt = _plain(_sec_fetch(ex_url))
                        url = ex_url
                pack["primary_doc_excerpt"] = {"form": sub_doc["form"], "date": sub_doc["date"],
                                               "url": url, "text": txt[:6000]}
        except Exception as e:
            pack["primary_doc_excerpt"] = {"error": f"DEGRADED: {type(e).__name__}: {e}"}
        facts = _get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json") or {}
        gaap = facts.get("facts", {}).get("us-gaap", {})
        series: dict[str, list] = {}
        for tag, label in XBRL_TAGS:
            if label in series or tag not in gaap:
                continue
            units = gaap[tag].get("units", {})
            rows = units.get("USD") or units.get("shares") or []
            q = [x for x in rows if x.get("form") in ("10-Q", "10-K") and x.get("frame") is None
                 and x.get("start") and x.get("end")
                 and 80 <= (datetime.date.fromisoformat(x["end"])
                            - datetime.date.fromisoformat(x["start"])).days <= 100]
            seen, out = set(), []
            for x in sorted(q, key=lambda x: x["end"], reverse=True):
                if x["end"] in seen:
                    continue
                seen.add(x["end"])
                out.append({"end": x["end"], "val": x["val"]})
                if len(out) == 8:
                    break
            series[label] = out
        pack["xbrl_quarterly"] = series
    # tape: gateway first, yahoo fallback
    tape = {}
    try:
        from desk.gw_quotes import bulk_stats
        s = bulk_stats([ticker], verbose=False).get(ticker)
        if s:
            tape = {"px": s["px"], "hi52": s.get("hi52"), "lo52": s.get("lo52"), "src": "ibkr_gw"}
    except Exception:
        pass
    if not tape:
        y = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=6mo&interval=1d")
        try:
            res = y["chart"]["result"][0]
            closes = [c for c in res["indicators"]["quote"][0]["close"] if c]
            m = res["meta"]
            tape = {"px": m.get("regularMarketPrice"),
                    "hi52": m.get("fiftyTwoWeekHigh"), "lo52": m.get("fiftyTwoWeekLow"),
                    "hi26w": round(max(closes), 2), "src": "yahoo"}
        except Exception:
            tape = {"error": "no tape source reachable"}
    if tape.get("px") and tape.get("hi52"):
        tape["dd52"] = round(tape["px"] / tape["hi52"] - 1, 3)
    if tape.get("px") and tape.get("lo52"):
        tape["pct_off_low"] = round(tape["px"] / tape["lo52"] - 1, 3)
    pack["tape"] = tape
    # next print (cached calendar guard helpers)
    try:
        from desk.catalyst_calendar_guard import _next_earnings, _yf_symbol
        nxt = _next_earnings(_yf_symbol(ticker) or ticker)
        pack["next_print"] = {"date": nxt, "confidence": "yfinance-derived — UNCONFIRMED "
                              "unless a company PR names it; state PRINT PROXIMITY accordingly"}
    except Exception:
        pack["next_print"] = {"date": None, "confidence": "unresolvable"}
    # book state (the CRM phantom-position lesson)
    held, orders = None, []
    try:
        pos = json.loads((ROOT / "desk/ui/data/positions_cache.json").read_text())
        for p in pos.get("positions", pos if isinstance(pos, list) else []):
            if str(p.get("ticker") or p.get("symbol")) == ticker:
                held = p
    except Exception:
        pass
    try:
        oc = json.loads((ROOT / "desk/ui/data/orders_cache.json").read_text())
        orders = [o for o in oc.get("orders", []) if str(o.get("ticker")) == ticker]
    except Exception:
        pass
    pack["book"] = {"held": held or "NO POSITION", "resting_orders": orders or "NONE",
                    "note": "verdicts must size against THIS, not any prior record's claim"}
    return pack


def render_pack(pack: dict) -> str:
    L = [f"## EVIDENCE PACK — {pack['ticker']} (machine-built {pack['built']})",
         "Cite this pack for tape/filing/series facts; contradict it only with a primary "
         "source, stating why. Both benches receive the identical pack.",
         f"\nENTITY: {pack.get('entity')} (CIK {pack.get('cik')})",
         f"TAPE [{pack.get('tape', {}).get('src')}]: " + json.dumps(pack.get("tape")),
         f"NEXT PRINT: {json.dumps(pack.get('next_print'))}",
         f"BOOK: held={json.dumps(pack.get('book', {}).get('held'))[:200]} "
         f"orders={json.dumps(pack.get('book', {}).get('resting_orders'))[:200]}",
         "\nRECENT FILINGS (newest first):"]
    for f in pack.get("filings", [])[:15]:
        L.append(f"  {f['date']}  {f['form']:8s} {f['acc']}")
    pde = pack.get("primary_doc_excerpt") or {}
    if pde.get("text"):
        L.append(f"\nPRIMARY DOC EXCERPT ({pde['form']} {pde['date']}, fetched full-fingerprint; "
                 "quote THIS over transcripts/secondary when they conflict):")
        L.append("  " + pde["text"][:4000])
    elif pde.get("error"):
        L.append(f"\nPRIMARY DOC EXCERPT: {pde['error']} — treat filing-text claims as UNVERIFIED")
    L.append("\nXBRL QUARTERLY (audited-filing values; use THESE for SBC/share/OCF math):")
    for label, rows in (pack.get("xbrl_quarterly") or {}).items():
        L.append(f"  {label}: " + ", ".join(f"{r['end']}={r['val']:,}" for r in rows[:8]))
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "DOCU"
    print(render_pack(build_pack(t)))
