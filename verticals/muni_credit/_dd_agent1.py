import re, json, time, sys, datetime, urllib.request
import emma_scraper as E

SETTLE = datetime.date(2026, 6, 10)

def fetch(cu, s, retries=2):
    url = E.BASE + "/Security/Details/" + cu
    last = None
    for a in range(retries+1):
        try:
            t = s.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
            if "yesButton" in t:
                s.post(E.BASE + "/Disclaimer.aspx",
                       data={"__VIEWSTATE": E._hidden("__VIEWSTATE", t),
                             "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", t),
                             "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", t),
                             "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"},
                       headers={"Content-Type": "application/x-www-form-urlencoded",
                                "Origin": E.BASE, "Referer": url}, timeout=40)
                t = s.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
            return t
        except Exception as e:
            last = e; time.sleep(10)
    raise last

def parse(t):
    up = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).upper()
    out = {}
    # tax status
    out['taxable'] = bool(re.search(r"TAX STATUS\s*:\s*TAXABLE", up) or "FEDERALLY TAXABLE" in up
                          or re.search(r"\(TAXABLE\)", up) or " TAXABLE LIMITED" in up
                          or " TAXABLE GENERAL" in up)
    m = re.search(r"TAX STATUS\s*:?\s*([A-Z \-/]+?)(?: ISSUE| DATED| MATURITY| SOURCE|$)", up)
    out['tax_status_raw'] = m.group(1).strip() if m else None
    out['amt'] = "ALTERNATIVE MINIMUM TAX" in up or "SUBJECT TO AMT" in up or " AMT " in up
    # issue description / title
    # the issue title appears just before "* COUPON:" or "(CA)* COUPON"
    mt = re.search(r"\(CA\)\s*([A-Z0-9 &;/\-\.\(\)']+?)\*?\s*COUPON\s*:", up)
    title = None
    # better: grab the full descriptive title around "BONDS"/"NOTES"/"OBLIGATION"
    mt2 = re.search(r"([A-Z][A-Z0-9 &;/\-\.,'\(\)]{15,140}?(?:BONDS?|NOTES?|OBLIGATIONS?|CERTIFICATES?)[A-Z0-9 &;/\-\.,'\(\)]{0,80}?\(CA\))", up)
    if mt2: title = mt2.group(1).strip()
    out['security_desc'] = title
    out['up_snippet'] = up
    # callable / next call
    out['callable'] = "NEXT CALL DATE" in up or "CALLABLE" in up
    mc = re.search(r"NEXT CALL DATE\s*:?\s*([0-9/]+)", up)
    out['next_call'] = mc.group(1) if mc else None
    mcp = re.search(r"NEXT CALL DATE[^A-Z]*?([0-9/]+)\s*(?:AT\s*)?([0-9.]+)?", up)
    # tradeData
    out['trades'] = []
    m = re.search(r"var tradeData = (\{.*?\});", t, re.S)
    if m:
        try:
            rows = json.loads(m.group(1)).get("data", [])
            out['trades'] = rows
        except Exception:
            pass
    return out

def figi(cu):
    body = json.dumps([{"idType": "ID_CUSIP", "idValue": cu}]).encode()
    req = urllib.request.Request("https://api.openfigi.com/v3/mapping", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=30)
        d = json.loads(r.read())
        return d
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    cu = sys.argv[1]
    s = E._session()
    t = fetch(cu, s)
    p = parse(t)
    print("TAXABLE:", p['taxable'], "| tax_raw:", p['tax_status_raw'], "| amt:", p['amt'])
    print("SECDESC:", p['security_desc'])
    print("CALLABLE:", p['callable'], "| next_call:", p['next_call'])
    print("N_TRADES:", len(p['trades']))
    if p['trades']:
        for r in p['trades'][:6]:
            print("  ", r.get('TD'), "TT=", r.get('TT'), "PX=", r.get('PX'), "YX=", r.get('YX'), "PAR=", r.get('PA') or r.get('PR'))
    # grep tax status context
    for kw in ["TAX STATUS", "TAX-EXEMPT", "TAX EXEMPT", "SECURITY", "GENERAL OBLIGATION", "REVENUE", "LIMITED", "CERTIFICATE", "LEASE", "MELLO", "ALLOCATION", "AD VALOREM", "AMT"]:
        i = p['up_snippet'].find(kw)
        if i >= 0:
            print(f"  [{kw}] ...{p['up_snippet'][max(0,i-40):i+90]}...")
