import json, re, datetime
OUT = "/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/buylist_dd"
CUSIPS = ["95330PHH1","032591TU3","17132CDL9","358233ED2","777387AH4","607735CA3"]

def field(up, label):
    # pull text after "LABEL :" up to next double-space-ish boundary
    m = re.search(re.escape(label) + r"\s*:?\s*([A-Z0-9 ,./%\-\(\)$]+?)(?:  |\bTAX |\bDATED |\bMATURITY |\bISSUE |\bCALL |\bSERIES |$)", up)
    return m.group(1).strip() if m else None

for cu in CUSIPS:
    t = open(f"{OUT}/raw_{cu}.html").read()
    up = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).upper()
    print("="*90)
    print("CUSIP", cu)
    # Issue description / title
    for lbl in ["ISSUE DESCRIPTION", "SECURITY DESCRIPTION", "OFFICIAL STATEMENT", "ISSUER NAME", "TAX STATUS", "FEDERAL TAX STATUS", "BANK QUALIFIED", "DATED DATE", "MATURITY DATE", "INTEREST RATE", "PRICE", "DENOMINATIONS"]:
        idx = up.find(lbl)
        if idx >= 0:
            print(f"  [{lbl}] ...{up[idx:idx+120]}")
    # taxable detection (same logic as verify)
    taxable = bool(re.search(r"TAX STATUS\s*:\s*TAXABLE", up) or "FEDERALLY TAXABLE" in up
                   or re.search(r"\(TAXABLE\)", up) or " TAXABLE LIMITED" in up
                   or " TAXABLE GENERAL" in up)
    # broader tax-exempt confirm
    exempt = "TAX-EXEMPT" in up or "TAX EXEMPT" in up or "FEDERALLY TAX-EXEMPT" in up
    amt = "ALTERNATIVE MINIMUM TAX" in up or "SUBJECT TO AMT" in up or " (AMT)" in up
    print(f"  TAXABLE_FLAG={taxable}  EXEMPT_MENTION={exempt}  AMT_MENTION={amt}")
    # call features
    for kw in ["CALLABLE", "REDEMPTION", "OPTIONAL REDEMPTION", "NON-CALLABLE", "NOT CALLABLE"]:
        idx = up.find(kw)
        if idx >= 0:
            print(f"  CALL[{kw}] ...{up[idx:idx+90]}")
    # tradeData
    m = re.search(r"var tradeData = (\{.*?\});", t, re.S)
    if m:
        try:
            data = json.loads(m.group(1)).get("data", [])
            print(f"  TRADES n={len(data)}")
            for r in data[:6]:
                print(f"    TD={r.get('TD','')[:10]} TT={r.get('TT')} PX={r.get('PX')} YX={r.get('YX')} PAR={r.get('PA') or r.get('PAR') or r.get('SZ')}")
        except Exception as ex:
            print("  tradeData parse err", ex)
    else:
        print("  NO tradeData")
