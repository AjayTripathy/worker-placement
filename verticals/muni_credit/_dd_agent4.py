import sys, re, json, time, datetime, urllib.request
sys.path.insert(0, ".")
import emma_scraper as E

SETTLE = datetime.date(2026, 6, 10)
CUSIPS = ["870462TJ7", "13049WAX3", "547541LJ9", "168520PA6", "223093TK1", "079113DY9"]

# list marks keyed by cusip
LIST = {o["cusip"]: o for o in json.load(open("outputs/BUY_LIST_20260610.json"))["orders"]}

def yrs(mat):
    y,m,d = [int(x) for x in mat.split("-")]
    return (datetime.date(y,m,d) - SETTLE).days/365.25

def tey_aftertax(px, cp, ytw, mat):
    thr = 100 - 0.25*yrs(mat)
    curr = cp/px
    if px < thr:
        return round(curr*2.01 + max(0.0, ytw-curr)*1.0, 4), True, thr
    return round(ytw*2.01, 4), False, thr

def fetch(cu, s):
    url = E.BASE + "/Security/Details/" + cu
    for attempt in range(2):
        try:
            t = s.get(url, headers={"Referer": E.BASE+"/"}, timeout=40).text
            break
        except Exception as ex:
            if attempt==0:
                time.sleep(10); continue
            raise
    if "yesButton" in t:
        s.post(E.BASE+"/Disclaimer.aspx",
               data={"__VIEWSTATE": E._hidden("__VIEWSTATE", t),
                     "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", t),
                     "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", t),
                     "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"},
               headers={"Content-Type":"application/x-www-form-urlencoded","Origin":E.BASE,"Referer":url},
               timeout=40)
        time.sleep(1)
        t = s.get(url, headers={"Referer": E.BASE+"/"}, timeout=40).text
    return t

def openfigi(cu):
    req = urllib.request.Request("https://api.openfigi.com/v3/mapping",
        data=json.dumps([{"idType":"ID_CUSIP","idValue":cu}]).encode(),
        headers={"Content-Type":"application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=30))
        return r
    except Exception as ex:
        return [{"error": str(ex)}]

def textify(t):
    return re.sub(r"\s+"," ", re.sub(r"<[^>]+>"," ", t)).strip()

s = E._session()
out = {}
for cu in CUSIPS:
    print("=== FETCH", cu, "===", flush=True)
    t = fetch(cu, s)
    up = textify(t).upper()
    flat = textify(t)
    # tax status
    taxable = bool(re.search(r"TAX STATUS\s*:\s*TAXABLE", up) or "FEDERALLY TAXABLE" in up
                   or re.search(r"\(TAXABLE\)", up) or " TAXABLE LIMITED" in up or " TAXABLE GENERAL" in up)
    mtax = re.search(r"(FEDERALLY TAX[- ]?EXEMPT|TAX[- ]?EXEMPT|TAXABLE|SUBJECT TO AMT|ALTERNATIVE MINIMUM TAX|FEDERALLY TAXABLE)", up)
    # capture context around "TAX STATUS"
    mctx = re.search(r".{0,40}TAX STATUS.{0,80}", up)
    amt = "ALTERNATIVE MINIMUM TAX" in up or "SUBJECT TO AMT" in up or re.search(r"\bAMT\b", up)
    # issue description / pledge
    mdesc = re.search(r"ISSUE DESCRIPTION\s*:?\s*(.{0,200})", up)
    msec = re.search(r"SECURITY\s*:?\s*(.{0,200})", up)
    # trade tape
    rows = []
    m = re.search(r"var tradeData = (\{.*?\});", t, re.S)
    if m:
        try: rows = json.loads(m.group(1)).get("data", [])
        except Exception: rows = []
    # call features keyword scan
    callable_hits = re.findall(r".{0,30}(CALLABLE|REDEMPTION|REDEEMABLE|NOT CALLABLE|NON-CALLABLE|OPTIONAL REDEMPTION|PRICE TO CALL).{0,30}", up)
    figi = openfigi(cu)
    out[cu] = {
        "taxable_flag": taxable,
        "tax_match": mtax.group(1) if mtax else None,
        "tax_status_ctx": mctx.group(0) if mctx else None,
        "amt": bool(amt),
        "desc_ctx": (mdesc.group(1) if mdesc else None),
        "sec_ctx": (msec.group(1) if msec else None),
        "n_trades": len(rows),
        "trades_head": rows[:8],
        "call_hits": callable_hits[:8],
        "figi": figi,
        "page_len": len(t),
    }
    json.dump(out, open("outputs/buylist_dd/_agent4_raw.json","w"), indent=1, default=str)
    # also dump full flattened text for manual pledge/call inspection
    open(f"outputs/buylist_dd/_raw_{cu}.txt","w").write(flat)
    print("  taxable=%s tax=%s n_trades=%d desc=%s" % (taxable, out[cu]["tax_match"], len(rows), out[cu]["desc_ctx"]), flush=True)
    time.sleep(1.2)

print("DONE")
