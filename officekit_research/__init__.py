"""officekit_research — the desk-native evidence layer, promoted (F1 of the
court unification, principal-directed 2026-09-04: "bring the desk-native court
architecture to the app; stop using anything ad-hoc").

The desk's court postmortems established the dataroom isomorphism: benches
argue JUDGMENT; a deterministic pass assembles the FACTS once, correctly, for
both sides. This package is that pass, productized as an @evidence_source
registry (same pattern as sync connectors and model providers):

    filings   EDGAR submissions inventory — kills "no filing since X" errors
    xbrl      last 8 quarters of revenue/SBC/diluted shares/OCF — kills
              double-count fights
    tape      live price + 52wk hi/lo + drawdown anchors — kills stale-anchor
              courts (free-endpoint default; a broker plugin can override)
    book      the office's OWN sleeves/holdings/adjudications for the symbol —
              kills phantom-position adjudications
    print     latest periodic-filing recency — print-proximity awareness

Every source degrades LOUD: a failed fetch is an errors[] entry the benches
see, never a silent absence. SEC fair access requires a contact User-Agent —
tenant-supplied (OFFICEKIT_CONTACT env or the `contact` argument), never a
baked-in identity (plane-2 discipline).
"""
from __future__ import annotations

import datetime
import json
import os
import re
import urllib.request

SOURCES = {}


def evidence_source(name):
    def deco(fn):
        SOURCES[name] = fn
        return fn
    return deco


def _contact(contact=None):
    from officekit.runtime import credential
    c = contact or credential("OFFICEKIT_CONTACT")
    if not c:
        raise RuntimeError("evidence: SEC fair-access needs a contact — set OFFICEKIT_CONTACT "
                           "or pass contact= (an email or URL identifying the operator)")
    return c


def _get_json(url, contact):
    req = urllib.request.Request(url, headers={"User-Agent": f"officekit research {contact}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def _cik(symbol, contact):
    d = _get_json("https://www.sec.gov/files/company_tickers.json", contact)
    for v in d.values():
        if v.get("ticker", "").upper() == symbol.upper():
            return v["cik_str"]
    return None


@evidence_source("filings")
def src_filings(symbol, ctx):
    cik = ctx.get("cik")
    if not cik:
        raise RuntimeError("no CIK resolved (non-SEC-listed symbol?)")
    sub = _get_json(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", ctx["contact"])
    r = sub.get("filings", {}).get("recent", {})
    rows = [{"form": f, "date": d, "acc": a}
            for f, d, a in list(zip(r.get("form", []), r.get("filingDate", []),
                                    r.get("accessionNumber", [])))[:15]]
    return {"entity": sub.get("name"), "recent": rows}


@evidence_source("xbrl")
def src_xbrl(symbol, ctx):
    cik = ctx.get("cik")
    if not cik:
        raise RuntimeError("no CIK resolved")
    tags = [("Revenues", "rev"), ("RevenueFromContractWithCustomerExcludingAssessedTax", "rev"),
            ("ShareBasedCompensation", "sbc"),
            ("WeightedAverageNumberOfDilutedSharesOutstanding", "dil_sh"),
            ("NetCashProvidedByUsedInOperatingActivities", "ocf")]
    out = {}
    for tag, key in tags:
        if key in out:
            continue
        try:
            d = _get_json(f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/us-gaap/{tag}.json",
                          ctx["contact"])
        except Exception:
            continue
        rows = [u for units in d.get("units", {}).values() for u in units
                if u.get("form") in ("10-Q", "10-K", "20-F", "6-K")]
        rows.sort(key=lambda u: u.get("end", ""), reverse=True)
        out[key] = [{"end": u["end"], "val": u["val"], "form": u.get("form")} for u in rows[:8]]
    if not out:
        raise RuntimeError("no XBRL facts found")
    return out


@evidence_source("tape")
def src_tape(symbol, ctx):
    """Free keyless daily closes (Nasdaq historical endpoint — connector-atlas
    doctrine: full browser headers required). A broker plugin can replace this
    source in the registry for live intraday tape."""
    import urllib.request as _u
    today = datetime.date.today()
    frm = today - datetime.timedelta(days=380)
    from officekit_research.funds import FUND_PAGES
    asset_class = "etf" if symbol.upper() in FUND_PAGES else "stocks"
    url = (f"https://api.nasdaq.com/api/quote/{symbol.upper()}/historical"
           f"?assetclass={asset_class}&fromdate={frm}&todate={today}&limit=9999")
    req = _u.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/",
        "Accept": "application/json"})
    with _u.urlopen(req, timeout=20) as r:
        d = json.loads(r.read().decode())
    rows = ((d.get("data") or {}).get("tradesTable") or {}).get("rows") or []
    closes = []
    for row in rows:
        try:
            closes.append((row["date"], float(row["close"].replace("$", "").replace(",", ""))))
        except Exception:
            continue
    if not closes:
        raise RuntimeError("no price rows (endpoint blocked or non-US symbol)")
    last_date, last = closes[0]
    vals = [c for _, c in closes]
    hi, lo = max(vals), min(vals)
    return {"last": last, "as_of": last_date, "wk52_hi": hi, "wk52_lo": lo,
            "off_high_pct": round((last / hi - 1) * 100, 1),
            "off_low_pct": round((last / lo - 1) * 100, 1)}


@evidence_source("book")
def src_book(symbol, ctx):
    """The office's own exposure — from the balance sheet the app already
    holds; no broker needed. Kills phantom-position adjudications."""
    data = ctx.get("office_data") or {}
    sym = symbol.upper()
    hits = []
    for s in data.get("sleeves") or []:
        for h in s.get("holdings") or []:
            if str(h.get("company", "")).upper() == sym:
                hits.append({"sleeve": s.get("name"), "amount": h.get("amount"),
                             "adjudication": (h.get("adjudication") or {}).get("verdict")})
    return {"held": bool(hits), "positions": hits}


@evidence_source("filing_text")
def src_filing_text(symbol, ctx):
    """Plain text of the latest periodic filing (10-Q/10-K/20-F/6-K primary
    doc) — the desk postmortems' lesson that decisive language (comp
    settlement terms, covenant carve-outs) lives in the document, not the
    metadata. Truncation is LOUD."""
    cik = ctx.get("cik")
    if not cik:
        raise RuntimeError("no CIK resolved")
    sub = _get_json(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", ctx["contact"])
    r = sub.get("filings", {}).get("recent", {})
    rows = list(zip(r.get("form", []), r.get("accessionNumber", []), r.get("primaryDocument", []),
                    r.get("filingDate", [])))
    doc = next(((f, a, pdoc, dt) for f, a, pdoc, dt in rows
                if f in ("10-Q", "10-K", "20-F", "6-K") and pdoc), None)
    if not doc:
        raise RuntimeError("no periodic filing with a primary document")
    form, acc, pdoc, dt = doc
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{pdoc}"
    req = urllib.request.Request(url, headers={"User-Agent": f"officekit research {ctx['contact']}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode(errors="replace")
    import html as _html
    txt = re.sub(r"<[^>]+>", " ", raw)
    txt = re.sub(r"\s+", " ", _html.unescape(txt)).strip()
    # 400k chars (~100k tokens) — the LGN verification (2026-09-05) found the
    # 150k cap hid the TRA balance-sheet figures from the benches; a full 10-Q
    # runs ~220k chars, so the cap now only bites genuinely huge documents.
    CAP = 400_000
    truncated = len(txt) > CAP
    return {"form": form, "date": dt, "url": url,
            "chars": len(txt), "truncated": truncated, "text": txt[:CAP]}


def build_pack(symbol, office_data=None, contact=None, sources=None):
    """Assemble the deterministic evidence pack. Degrade-loud: every failed
    source lands in errors[] — the benches SEE what could not be fetched."""
    from officekit_research.funds import FUND_PAGES
    if sources is None and symbol.upper() in FUND_PAGES:
        sources = ["fund_profile", "book", "tape"]
    sec_needed = not sources or bool(set(sources) & {"filings", "xbrl", "filing_text", "print"})
    contact = _contact(contact) if sec_needed else contact
    ctx = {"contact": contact, "office_data": office_data or {}}
    try:
        ctx["cik"] = _cik(symbol, contact) if sec_needed else None
    except Exception as e:
        ctx["cik"] = None
        cik_err = f"cik: {type(e).__name__}: {e}"
    else:
        cik_err = None
    pack = {"symbol": symbol.upper(),
            "built": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "sections": {}, "errors": ([cik_err] if cik_err else [])}
    for name, fn in SOURCES.items():
        if name == "fund_profile" and sources is None and symbol.upper() not in FUND_PAGES:
            continue
        if sources and name not in sources:
            continue
        try:
            pack["sections"][name] = fn(symbol, ctx)
        except Exception as e:
            pack["errors"].append(f"{name}: {type(e).__name__}: {e}")
    return pack


def render_pack(pack):
    """The pack as bench-facing markdown — facts first, failures LOUD."""
    L = [f"## EVIDENCE PACK — {pack['symbol']} (built {pack['built']})",
         "Deterministic machine layer, shared by both benches. Argue JUDGMENT on these facts;",
         "a bench contradicting the pack without a primary source is invalid (court doctrine)."]
    s = pack["sections"]
    if "fund_profile" in s:
        f = s["fund_profile"]
        L.append(f"\n### Primary fund document — {f['url']} (retrieved {f['fetched_at']})")
        L.append(f.get("note", "") + (" EXCERPT TRUNCATED." if f.get("truncated") else ""))
        L.append(f["text"])
    if "program" in s:
        L.append("\n### Proposed program (office facts and analyst assumptions; external terms unverified)")
        L.append(json.dumps(s["program"], ensure_ascii=False))
    if "filings" in s:
        L.append(f"\n### Filings — {s['filings'].get('entity')}")
        L += [f"- {r['form']} {r['date']}" for r in s["filings"]["recent"][:10]]
    if "xbrl" in s:
        L.append("\n### XBRL (last quarters, most recent first)")
        for key, rows in s["xbrl"].items():
            vals = ", ".join(f"{r['end']}: {r['val']:,}" for r in rows[:4])
            L.append(f"- {key}: {vals}")
    if "tape" in s:
        t = s["tape"]
        L.append(f"\n### Tape (as of {t['as_of']}): last {t['last']} · 52wk {t['wk52_lo']}-{t['wk52_hi']} "
                 f"· {t['off_high_pct']}% off high · +{t['off_low_pct']}% off low")
    if "book" in s:
        b = s["book"]
        L.append(f"\n### Book: {'HELD — ' + json.dumps(b['positions']) if b['held'] else 'not held'}")
    if "filing_text" in s:
        ft = s["filing_text"]
        L.append(f"\n### Latest periodic filing — {ft['form']} {ft['date']} "
                 + ("(TRUNCATED at {:,} of {:,} chars — later sections unseen)".format(len(ft["text"]), ft["chars"])
                    if ft["truncated"] else "(full text)"))
        L.append(ft["text"])
    if pack["errors"]:
        L.append("\n### EVIDENCE GAPS (fetch failures — treat these axes as UNVERIFIED, never assume)")
        L += [f"- {e}" for e in pack["errors"]]
    return "\n".join(L)


from officekit_research.funds import fund_profile
evidence_source("fund_profile")(fund_profile)
