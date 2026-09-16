"""Gauntlet 2026-08-14: fetch DGXX Q2'26 filing (acc 0001213900-26-089450), CIK 1854368."""
import json
import sys

sys.path.insert(0, ".")
from desk.sec_fetch import fetch, SecFetchError

CIK = "1854368"
ACC = "0001213900-26-089450"
acc_nodash = ACC.replace("-", "")

# submissions index: confirm form type + list today's filings
body = fetch("https://data.sec.gov/submissions/CIK%s.json" % CIK.zfill(10))
sub = json.loads(body)
rec = sub["filings"]["recent"]
for i in range(min(15, len(rec["accessionNumber"]))):
    print(
        rec["filingDate"][i],
        rec["form"][i],
        rec["accessionNumber"][i],
        rec.get("items", [""] * 99)[i] if rec.get("items") else "",
        rec["primaryDocument"][i],
    )
