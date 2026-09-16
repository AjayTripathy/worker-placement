import json, os
OUT = "/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/buylist_dd"
PATH = f"{OUT}/agent3.json"

results = []
def add(o):
    results.append(o)
    with open(PATH, "w") as f:
        json.dump(results, f, indent=1)
    print("wrote", o["cusip"], o["verdict"])

# 1) 95330PHH1 — West Hills CC GO Ref Bds Series B
add({
 "cusip":"95330PHH1","verdict":"CLEAR",
 "basis":"West Hills CCD 2016 GO Refunding Bds Ser B — unlimited ad-valorem CC-district GO (SB-222 class), TAX EXEMPT; tape/TEY reconcile.",
 "tax_status":"TAX EXEMPT (EMMA field; no AMT)","pledge_confirmed":True,
 "callable":True,"next_call":"2026-08-01 @ 100 (par; px<100 so call is upside, no priced-to-call premium giveup)",
 "live_last_trade_px":99.276,"live_last_trade_date":"2026-06-03",
 "tape_moved_pt":0.344,
 "recomputed_tey_at":0.0823,"tey_divergence_pp":0.0,
 "issuer_resolved":"West Hills Community College District (CA) — OpenFIGI 'W HILLS CMNTY CLG-B'; matches list",
 "ab1200":"N/A (community-college district; not under K-12 CDE interim certification) — fiscal status UNVERIFIED, not 'clean'",
 "notes":"Latest 06-03 print 99.276 is a dealer PURCHASE (TT=P); last customer SALE 98.932 (05-21). Limit 99.43 > fresh, executable. Above de-minimis (thr 96.21)."
})

# 2) 032591TU3 — Anaheim Union HSD GO 2019
add({
 "cusip":"032591TU3","verdict":"CLEAR",
 "basis":"Anaheim Union HSD GO Elec-2014 Ser 2019 — unlimited ad-valorem K-12 GO, TAX EXEMPT; AB-1200 clean; tape/TEY reconcile (de-minimis-aware).",
 "tax_status":"TAX EXEMPT (EMMA field; no AMT)","pledge_confirmed":True,
 "callable":True,"next_call":"2027-08-01",
 "live_last_trade_px":83.565,"live_last_trade_date":"2026-05-19",
 "tape_moved_pt":0.0,
 "recomputed_tey_at":0.0813,"tey_divergence_pp":0.0,
 "issuer_resolved":"Anaheim Union High School District, Orange County (CA) — OpenFIGI 'ANAHEIM UNION HSD'; matches list",
 "ab1200":"POSITIVE (absent from CDE First & Second 2024-25 Negative/Qualified lists)",
 "notes":"No print since 05-19 (22 days; under 30d stale flag but thin). Deep discount, de-minimis breach (px 83.57 < thr 96.21) — discount accretion taxed ordinary, TEY uses coupon-yield gross-up only. List px_spread was wide (1.92pt); work the bid patiently. Limit 84.06."
})
print("checkpoint A done")
