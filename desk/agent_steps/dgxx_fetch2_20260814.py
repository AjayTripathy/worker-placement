"""Fetch DGXX 8-K index + exhibits for acc 0001213900-26-089450."""
import sys, re, json

sys.path.insert(0, ".")
from desk.sec_fetch import fetch

CIK = "1854368"
acc_nodash = "000121390026089450"
base = "https://www.sec.gov/Archives/edgar/data/%s/%s/" % (CIK, acc_nodash)
idx = fetch(base + "index.json")
j = json.loads(idx)
for it in j["directory"]["item"]:
    print(it["name"], it.get("size", ""))
