import sys, re, json, time, datetime
sys.path.insert(0,".")
import emma_scraper as E
CUSIPS=["870462TJ7","13049WAX3","547541LJ9","168520PA6","223093TK1","079113DY9"]
s=E._session()
def fetch(cu):
    url=E.BASE+"/Security/Details/"+cu
    t=s.get(url,headers={"Referer":E.BASE+"/"},timeout=40).text
    if "yesButton" in t:
        s.post(E.BASE+"/Disclaimer.aspx",
          data={"__VIEWSTATE":E._hidden("__VIEWSTATE",t),"__VIEWSTATEGENERATOR":E._hidden("__VIEWSTATEGENERATOR",t),
                "__EVENTVALIDATION":E._hidden("__EVENTVALIDATION",t),
                "ctl00$mainContentArea$disclaimerContent$yesButton":"Accept"},
          headers={"Content-Type":"application/x-www-form-urlencoded","Origin":E.BASE,"Referer":url},timeout=40)
        time.sleep(1); t=s.get(url,headers={"Referer":E.BASE+"/"},timeout=40).text
    return t
tapes={}
for cu in CUSIPS:
    t=fetch(cu)
    m=re.search(r"var tradeData = (\{.*?\});", t, re.S)
    rows=json.loads(m.group(1)).get("data",[]) if m else []
    tapes[cu]=rows
    print(cu,"trades",len(rows),flush=True)
    time.sleep(1.2)
json.dump(tapes, open("outputs/buylist_dd/_agent4_tapes.json","w"), default=str)
print("saved")
