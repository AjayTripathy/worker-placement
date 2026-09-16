import re, json, time, datetime, urllib.request
import emma_scraper as E

CU = "270198BY9"
COUPON = 4.0
MAT = "2041-08-01"      # 2041-08 staged; refine from EMMA
MARK = 99.99
LIMIT = 100.49
STAGED_TEY = 8.04
SETTLE = datetime.date(2026, 6, 11)

s = E._session()
url = E.BASE + "/Security/Details/" + CU
t = s.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
if "yesButton" in t:
    s.post(E.BASE + "/Disclaimer.aspx",
           data={"__VIEWSTATE": E._hidden("__VIEWSTATE", t),
                 "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", t),
                 "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", t),
                 "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"},
           headers={"Content-Type": "application/x-www-form-urlencoded", "Origin": E.BASE, "Referer": url},
           timeout=40)
    time.sleep(1)
    t = s.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text

open("outputs/buylist_dd/_raw_270198BY9.html", "w").write(t)
up = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).upper()

# --- title / identity text ---
mt = re.search(r"<title>(.*?)</title>", t, re.S | re.I)
title = re.sub(r"\s+", " ", mt.group(1)).strip() if mt else ""

def field(label):
    # EMMA renders label/value pairs; grab text after the label up to next field
    m = re.search(re.escape(label.upper()) + r"\s*:?\s*([A-Z0-9 ,./%\-\(\)]+?)(?:  |TAX STATUS|DATED DATE|MATURITY DATE|COUPON|ISSUER|ISSUE |CALL|<|$)", up)
    return m.group(1).strip() if m else None

# 1 TAX STATUS
taxable = bool(re.search(r"TAX STATUS\s*:?\s*TAXABLE", up) or "FEDERALLY TAXABLE" in up
               or re.search(r"\(TAXABLE\)", up) or " TAXABLE LIMITED" in up or " TAXABLE GENERAL" in up)
amt = "ALTERNATIVE MINIMUM TAX" in up or " AMT " in up or "SUBJECT TO AMT" in up
tax_status_raw = None
mtx = re.search(r"TAX STATUS\s*:?\s*([A-Z &\-]+?)(?:DATED|MATURITY|COUPON|ISSUE|SECURITY|PRINCIPAL|<|$)", up)
if mtx: tax_status_raw = mtx.group(1).strip()

# 2 PLEDGE / security
pledge_go = bool(re.search(r"UNLIMITED.{0,30}AD ?-?VALOREM", up) or "GENERAL OBLIGATION" in up or "GO BDS" in up or "GO BONDS" in up)
limited = "LIMITED OBLIGATION" in up or "LIMITED TAX" in up
judgment = "JUDGMENT" in up
ground_lease = "CERTIFICATE OF PARTICIPATION" in up or "LEASE REVENUE" in up

# 3 CALL
call_block = ""
mc = re.search(r"(CALL|REDEMPTION).{0,400}", up)
if mc: call_block = mc.group(0)[:400]
callable_yes = bool(re.search(r"CALL DATE", up) or "OPTIONAL REDEMPTION" in up or "REDEEMABLE" in up or "CALLABLE" in up)
# next call date / price
ncd = re.search(r"(\d{2}/\d{2}/\d{4}).{0,40}?(\d{2,3}\.\d{2,3})", call_block) if call_block else None

# 4 TAPE
ytw = pxv = tdate = None
rows = []
m = re.search(r"var tradeData = (\{.*?\});", t, re.S)
if m:
    try: rows = json.loads(m.group(1)).get("data", [])
    except Exception: rows = []
for r in rows:
    r["_d"] = r.get("TD", "")[:10]
rows.sort(key=lambda r: r.get("TD", ""), reverse=True)
last = rows[0] if rows else None
if last:
    ytw = last.get("YX"); pxv = last.get("PX"); tdate = last.get("TD", "")[:10]

# tape metrics
today = SETTLE
def dparse(x): return datetime.date(*[int(z) for z in x[:10].split("-")])
yr = [r for r in rows if r.get("TD") and (today - dparse(r["TD"])).days <= 365]
n365 = len(yr); n90 = sum(1 for r in rows if r.get("TD") and (today - dparse(r["TD"])).days <= 90)
days_since = (today - dparse(last["TD"])).days if last else None
from collections import defaultdict
byday = defaultdict(lambda: {"S": [], "P": []})
for r in yr:
    if r.get("TT") in ("S", "P") and r.get("PX") and r.get("YX") is not None:
        byday[r["TD"][:10]][r["TT"]].append(r)
two_sided = sum(1 for sp in byday.values() if sp["S"] and sp["P"])
sizes = [r.get("TA") for r in yr if r.get("TA")]
import statistics as st
med_block = st.median(sizes) if sizes else None
max_block = max(sizes) if sizes else None
tape_moved = round(abs((pxv if pxv else MARK) - MARK), 4) if pxv is not None else None

# 5 MATH
def yrs_to_mat(mat):
    y, mo, d = [int(x) for x in mat.split("-")]
    return (datetime.date(y, mo, d) - SETTLE).days / 365.25
years = yrs_to_mat(MAT)
demin_thr = round(100 - 0.25 * years, 3)
px_for_math = pxv if pxv is not None else MARK
ytw_pct = (ytw if ytw is not None else None)   # YX is already a percent like 4.05
curr = COUPON / px_for_math * 100   # current yield in percent
if px_for_math < demin_thr and ytw_pct is not None:
    tey = round(curr * 2.01 + max(0.0, ytw_pct - curr) * 1.0, 4)
    demin_breach = True
elif ytw_pct is not None:
    tey = round(ytw_pct * 2.01, 4)
    demin_breach = False
else:
    tey = None; demin_breach = None
tey_div = round(abs(tey - STAGED_TEY), 4) if tey is not None else None

# 6 IDENTITY via OpenFIGI
figi_name = None
try:
    req = urllib.request.Request("https://api.openfigi.com/v3/mapping",
        data=json.dumps([{"idType": "ID_CUSIP", "idValue": CU}]).encode(),
        headers={"Content-Type": "application/json"})
    fr = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if fr and fr[0].get("data"):
        figi_name = fr[0]["data"][0].get("name") or fr[0]["data"][0].get("securityDescription")
except Exception as e:
    figi_name = f"ERR:{e}"

out = {
 "cusip": CU, "title": title, "tax_status_raw": tax_status_raw, "taxable": taxable, "amt": amt,
 "pledge_go": pledge_go, "limited": limited, "judgment": judgment, "lease": ground_lease,
 "callable_yes": callable_yes, "call_block": call_block, "next_call_match": ncd.groups() if ncd else None,
 "ytw": ytw, "last_px": pxv, "last_date": tdate, "n365": n365, "n90": n90,
 "days_since": days_since, "two_sided": two_sided, "med_block": med_block, "max_block": max_block,
 "tape_moved": tape_moved, "years": round(years, 2), "demin_thr": demin_thr,
 "curr_yield_pct": round(curr, 4), "tey_pct": tey, "demin_breach": demin_breach, "tey_div": tey_div,
 "figi_name": figi_name, "n_rows": len(rows),
}
print(json.dumps(out, indent=1, default=str))
json.dump(out, open("outputs/buylist_dd/_agent6_raw.json", "w"), indent=1, default=str)
# dump recent tape for eyeballing
print("--- recent tape ---")
for r in rows[:12]:
    print(r.get("TD"), "TT="+str(r.get("TT")), "PX="+str(r.get("PX")), "YX="+str(r.get("YX")), "TA="+str(r.get("TA")))
