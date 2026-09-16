"""convert_screener — systematizes species-1 convex carry: busted converts with
fundamental-change puts, ACCESSIBILITY-FIRST (the FUBO lesson: a Mudrick private
placement is unownable at any attractiveness).

Pipeline:
  stage 1  UNIVERSE   EDGAR full-text search: recent 10-Q/10-K mentioning convertible
                      senior notes (every modern indenture carries an FC put at par —
                      the differentiators are bustedness, control situation, access)
  stage 2  TERMS      per issuer, pull the filing and extract: coupon, principal,
                      conversion price, maturity year, PIK language (taxable poison),
                      "private/exchange placement" language (access poison)
  stage 3  BUSTED     conversion price vs live stock (paced quotes, cached):
                      OTM >= 40% = busted -> the equity option is dead, the put+coupon
                      carry the value
  stage 4  CONTROL    text heuristics: controlled company / majority holder /
                      strategic alternatives / going-private — the FC-put trigger fuel
  stage 5  OUTPUT     ranked JSON + report; --enqueue routes top-K to TRAP_VERIFY with
                      a species-1 brief. IBKR bond-line accessibility = a per-name
                      CHECK column (connector-dependent; verified at trap-verify).

  python3 -m desk.convert_screener [--max-issuers 40] [--no-quotes] [--enqueue K]
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desk" / "data" / "convert_screen.json"
QCACHE = ROOT / "desk" / "data" / "convert_screen_quotes.json"
UA = "SignalOS research desk (contact: 4tripathy@gmail.com)"
BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0"

CONTROL_PATTERNS = [
    (r"controlled company", 3), (r"strategic alternatives", 3), (r"going.?private", 3),
    (r"majority of (?:our|the) (?:outstanding|voting)", 2), (r"principal stockholder", 1),
    (r"beneficially owns? (?:approximately )?[5-9]\d(?:\.\d+)?%", 3),
    (r"tender offer", 2), (r"merger agreement", 3),
]
ACCESS_POISON = [r"privately negotiated", r"exchange agreement with", r"144A(?! *registered)"]
PIK_PAT = re.compile(r"\bPIK\b|payment.?in.?kind", re.I)


def _curl(url: str, ua: str = UA, timeout: int = 25) -> str:
    r = subprocess.run(["curl", "-s", "--max-time", str(timeout), url, "-H", f"User-Agent: {ua}"],
                       capture_output=True, text=True)
    return r.stdout


def universe(max_issuers: int) -> list[dict]:
    """EDGAR FTS for issuers with live convert language in recent quarterlies."""
    seen, out = set(), []
    for frm in range(0, max(1, max_issuers // 10) * 10, 10):
        import datetime as _dt
        start = (_dt.date.today() - _dt.timedelta(days=120)).isoformat()
        js = _curl("https://efts.sec.gov/LATEST/search-index?q=%22convertible%20senior%20notes%22"
                   f"&forms=10-Q&dateRange=custom&startdt={start}&enddt={_dt.date.today().isoformat()}&from={frm}")
        try:
            hits = json.loads(js)["hits"]["hits"]
        except Exception:
            break
        if not hits:
            break
        for h in hits:
            src = h.get("_source", {})
            ciks = src.get("ciks", [])
            names = src.get("display_names", [])
            if not ciks:
                continue
            cik = ciks[0]
            if cik in seen:
                continue
            seen.add(cik)
            m = re.search(r"\(([A-Z][A-Z0-9.\-]{0,6})\)", names[0] if names else "")
            out.append({"cik": cik, "name": (names[0] if names else "?").split("  (CIK")[0],
                        "ticker": m.group(1) if m else None, "adsh": src.get("adsh"),
                        "file_date": src.get("file_date")})
            if len(out) >= max_issuers:
                return out
        time.sleep(0.4)
    return out


def extract_terms(cik: str, adsh: str) -> dict:
    acc = adsh.replace("-", "")
    idx = _curl(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/index.json")
    try:
        items = json.loads(idx)["directory"]["item"]
        doc = next(i["name"] for i in items
                   if i["name"].endswith(".htm") and not i["name"].startswith(("R", "report"))
                   and "ex" not in i["name"][:4].lower())
    except Exception:
        return {"error": "no primary doc"}
    txt = _curl(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{doc}", timeout=40)
    t = re.sub(r"<[^>]+>", " ", txt)
    t = re.sub(r"\s+", " ", t)
    o: dict = {}
    m = re.search(r"conversion price of approximately \$\s?([\d,]+\.?\d*)", t)
    if m:
        o["conversion_price"] = float(m.group(1).replace(",", ""))
    m = re.search(r"(\d\.\d{1,3})\s?%\s?[Cc]onvertible [Ss]enior", t)
    if m:
        o["coupon"] = float(m.group(1))
    m = re.search(r"[Cc]onvertible [Ss]enior (?:[Ss]ecured )?[Nn]otes due (20\d\d)", t)
    if m:
        o["maturity"] = int(m.group(1))
    m = re.search(r"\$\s?([\d,]+(?:\.\d+)?)\s?million (?:aggregate )?principal amount of (?:the |our |its )?"
                  r"(?:new )?[\d.]*\s?%?\s?[Cc]onvertible", t)
    if m:
        o["principal_musd"] = float(m.group(1).replace(",", ""))
    o["secured"] = bool(re.search(r"[Cc]onvertible [Ss]enior [Ss]ecured", t))
    o["pik"] = bool(PIK_PAT.search(t))
    o["access_poison"] = [p for p in ACCESS_POISON if re.search(p, t, re.I)]
    o["control_score"] = sum(w for pat, w in CONTROL_PATTERNS if re.search(pat, t, re.I))
    o["control_hits"] = [pat for pat, _ in CONTROL_PATTERNS if re.search(pat, t, re.I)]
    return o


def quote(ticker: str, cache: dict) -> float | None:
    if ticker in cache:
        return cache[ticker]
    time.sleep(1.5)
    js = _curl(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1d",
               ua=BROWSER_UA)
    try:
        px = json.loads(js)["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception:
        px = None
    cache[ticker] = px
    return px


def run(max_issuers: int, no_quotes: bool, enqueue_k: int) -> dict:
    uni = universe(max_issuers)
    print(f"[convert_screener] universe: {len(uni)} issuers with live convert language")
    try:
        qc = json.loads(QCACHE.read_text())
    except Exception:
        qc = {}
    rows = []
    for u in uni:
        time.sleep(0.3)
        terms = extract_terms(u["cik"], u["adsh"])
        row = {**u, **terms}
        if not no_quotes and u.get("ticker") and terms.get("conversion_price"):
            px = quote(u["ticker"], qc)
            if px:
                row["px"] = px
                row["otm_pct"] = round(1 - px / terms["conversion_price"], 3)
        # score: busted (OTM>=40%) + coupon + control - poisons
        s = 0.0
        if row.get("otm_pct", 0) >= 0.40: s += 3
        s += min(row.get("coupon", 0), 8) / 2
        s += min(row.get("control_score", 0), 6)
        if row.get("secured"): s += 1
        if row.get("pik"): s -= 2                      # taxable poison
        if row.get("access_poison"): s -= 4            # the FUBO lesson
        row["score"] = round(s, 2)
        rows.append(row)
    rows.sort(key=lambda r: -r["score"])
    QCACHE.write_text(json.dumps(qc, indent=1))
    res = {"asof": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "n_universe": len(uni), "rows": rows}
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[convert_screener] top: " + "; ".join(
        f"{r.get('ticker') or r['name'][:14]} s={r['score']} otm={r.get('otm_pct')} cpn={r.get('coupon')} ctl={r.get('control_score')}"
        for r in rows[:8]))
    if enqueue_k:
        from desk.court_queue import enqueue_candidates
        cands = [{"ticker": r["ticker"], "context":
                  f"SPECIES-1 convert candidate (convert_screener {res['asof']}): coupon {r.get('coupon')}%, "
                  f"conv px {r.get('conversion_price')}, OTM {r.get('otm_pct')}, control hits {r.get('control_hits')}, "
                  f"secured={r.get('secured')}. VERIFY: (1) IBKR bond line EXISTS (accessibility first — no private "
                  f"placements), (2) FC-put at par verbatim from the indenture/10-Q, (3) TRACE prints near par, "
                  f"(4) no company-option PIK, (5) the control situation is real and dated. No timing axiom — "
                  f"contractual convexity doesn't decay."}
                 for r in rows[:enqueue_k] if r.get("ticker") and r["score"] >= 4 and not r.get("access_poison")]
        if cands:
            n = enqueue_candidates(cands, source=f"convert_screener/{datetime.date.today().isoformat()}",
                                   stage="TRAP_VERIFY", allow_ledger=True)
            print(f"[convert_screener] enqueued: {n}")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-issuers", type=int, default=40)
    ap.add_argument("--no-quotes", action="store_true")
    ap.add_argument("--enqueue", type=int, default=0)
    a = ap.parse_args()
    run(a.max_issuers, a.no_quotes, a.enqueue)
