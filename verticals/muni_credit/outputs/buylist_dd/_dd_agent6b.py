import re, json, time
import emma_scraper as E

CU = "270198BY9"; ISSUE = "ER377812"
SID = "AFC45051F75B0067FB8AA10AC31E2DBB2"
s = E._session()
# re-accept disclaimer at issue level
det = f"{E.BASE}/IssueView/Details/{ISSUE}"
html = s.get(det, headers={"Referer": E.BASE + "/"}, timeout=40).text
if "yesButton" in html:
    s.post(f"{E.BASE}/Disclaimer.aspx",
           data={"__VIEWSTATE": E._hidden("__VIEWSTATE", html),
                 "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", html),
                 "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", html),
                 "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"},
           headers={"Content-Type": "application/x-www-form-urlencoded", "Origin": E.BASE, "Referer": det}, timeout=40)
    time.sleep(1)

aj = {"X-Requested-With": "XMLHttpRequest", "Referer": det}

# 1) final scale data -> per-CUSIP coupon/maturity/yield/price/call
try:
    r = s.get(f"{E.BASE}/IssueView/GetFinalScaleData/{ISSUE}", headers=aj, timeout=40)
    scale = r.json()
    rows = scale if isinstance(scale, list) else scale.get("data", scale)
    mine = [x for x in (rows or []) if str(x.get("CUSIP", x.get("Cusip", ""))).upper() == CU]
    print("=== FINAL SCALE (this CUSIP) ===")
    print(json.dumps(mine, indent=1, default=str)[:2000])
    if not mine:
        print("KEYS:", list((rows or [{}])[0].keys()) if rows else "empty")
        print("sample:", json.dumps((rows or [])[:1], default=str)[:1500])
except Exception as e:
    print("scale ERR", e)
time.sleep(1)

# 2) try security details AJAX endpoints
for ep in [f"/Security/GetSecurityDetails?securityId={SID}",
           f"/Security/SecurityDetailsPartialView?securityId={SID}",
           f"/Security/Details/{CU}?securityId={SID}"]:
    try:
        r = s.get(E.BASE + ep, headers=aj, timeout=40)
        body = r.text
        flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
        hits = re.findall(r"(Tax Status|Federally|Callable|Next Call Date|Next Call Price|Dated Date|Maturity Date|Coupon|Principal Amount at Issuance|Ad Valorem|Unlimited|General Obligation)[^A-Za-z0-9]{0,4}([A-Za-z0-9 ,./%\-\$]{0,40})", flat, re.I)
        if hits:
            print(f"\n=== {ep} ({len(body)} bytes) ===")
            for k, v in hits[:30]:
                print(" ", k, "=>", v.strip()[:50])
            break
    except Exception as e:
        print(ep, "ERR", e)
    time.sleep(1)
