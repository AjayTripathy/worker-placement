"""DGXX equity reconciliation: pull Q1'26 balance sheet + share count from XBRL facts."""
import sys, json

sys.path.insert(0, ".")
from desk.sec_fetch import fetch

body = fetch("https://data.sec.gov/api/xbrl/companyfacts/CIK0001854368.json")
j = json.loads(body)
gaap = j["facts"].get("us-gaap", {})
dei = j["facts"].get("dei", {})

def show(tag, src=gaap, n=6):
    if tag not in src:
        print(tag, "-- absent")
        return
    units = src[tag]["units"]
    for u, vals in units.items():
        rows = [v for v in vals if v.get("end", "") >= "2025-12-01"]
        rows.sort(key=lambda v: (v.get("end", ""), v.get("filed", "")))
        for v in rows[-n:]:
            print(tag, u, v.get("end"), v.get("val"), "form", v.get("form"), "filed", v.get("filed"))

for t in ["CashAndCashEquivalentsAtCarryingValue", "StockholdersEquity",
          "CommonStockSharesOutstanding", "CommonStockSharesIssued",
          "ProceedsFromIssuanceOfCommonStock", "Assets"]:
    show(t)
show("EntityCommonStockSharesOutstanding", dei)
