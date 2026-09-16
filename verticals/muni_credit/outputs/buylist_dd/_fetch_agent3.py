import json, re, time, sys, os, datetime
sys.path.insert(0, "/Users/ajay/exalted/signalos/verticals/muni_credit")
import emma_scraper as E

CUSIPS = ["95330PHH1","032591TU3","17132CDL9","358233ED2","777387AH4","607735CA3"]
OUT = "/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/buylist_dd"
os.makedirs(OUT, exist_ok=True)

s = E._session()

def fetch(cu):
    url = E.BASE + "/Security/Details/" + cu
    for attempt in range(2):
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
                time.sleep(1)
                t = s.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
            return t
        except Exception as ex:
            print(f"  retry {cu}: {ex}", flush=True)
            time.sleep(10)
    return None

for cu in CUSIPS:
    print("FETCH", cu, flush=True)
    t = fetch(cu)
    if t is None:
        print("  FAILED", cu, flush=True); continue
    with open(f"{OUT}/raw_{cu}.html", "w") as f:
        f.write(t)
    print(f"  saved {len(t)} bytes", flush=True)
    time.sleep(1)
print("DONE")
