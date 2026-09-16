import re, json, time
import emma_scraper as E

CU = "270198BY9"; ISSUE = "ER377812"
SID = "AFC45051F75B0067FB8AA10AC31E2DBB2"
s = E._session()
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
body = s.get(f"{E.BASE}/Security/Details/{CU}?securityId={SID}", headers=aj, timeout=40).text
open("outputs/buylist_dd/_raw_270198BY9_detail.html", "w").write(body)
flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))

def grab(label, stop):
    m = re.search(label + r"\s*:?\s*(.*?)\s*(?:" + stop + ")", flat, re.I)
    return m.group(1).strip() if m and m.group(1) else None

fields = {
 "issuer_desc": grab("Issuer Name", "Issuer Type|State|Dated|Maturity|Security Description"),
 "security_desc": grab("Security Description", "Purpose|Sector|Coupon|Dated|Tax"),
 "tax_status": grab("Tax Status", "Coupon|Maturity|Dated|Security|Purpose|Insurance|Principal|Time|Initial|High|Low|Bank"),
 "coupon": grab("Coupon\\s*\\(%\\)|Coupon", "Coupon Type|Maturity|Dated|Tax"),
 "maturity_date": grab("Maturity Date", "Coupon|Initial|Dated|Tax|High|Low|Type"),
 "dated_date": grab("Dated Date", "Initial|Coupon|Maturity|Principal|Tax|Time"),
 "principal": grab("Principal Amount at Issuance", "Time|Security|Coupon|Maturity|Dated"),
 "callable": grab("Callable", "Next Call|Coupon|Maturity"),
 "next_call_date": grab("Next Call Date", "Next Call Price|Coupon|Maturity|Tax"),
 "next_call_price": grab("Next Call Price", "Coupon|Maturity|Tax|High|Low|Type"),
 "purpose": grab("Purpose/Sector|Purpose", "Coupon|Maturity|Dated|Tax|Security"),
 "insurance": grab("Insurance|Bond Insurance|Credit Enhancement", "Coupon|Maturity|Tax|Dated"),
}
print(json.dumps(fields, indent=1))

# show raw window around Next Call Date and Tax Status for accuracy
for kw in ["Next Call Date", "Tax Status", "Callable", "Issuer Name", "Initial Offering Price", "Bond Insurance", "Insurance"]:
    m = re.search(".{0,10}" + re.escape(kw) + ".{0,70}", flat, re.I)
    print("  WIN", kw, "::", m.group(0).strip() if m else None)
