import json
OUT = "/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/buylist_dd"
PATH = f"{OUT}/agent3.json"
results = json.load(open(PATH))
def add(o):
    results.append(o)
    json.dump(results, open(PATH,"w"), indent=1)
    print("wrote", o["cusip"], o["verdict"])

# 3) 17132CDL9 — Chula Vista ESD SFID No.1 GO Ser C (BAM-insured)
add({
 "cusip":"17132CDL9","verdict":"FLAG",
 "basis":"Chula Vista ESD SFID No.1 GO Ser C (BAM-insured) — unlimited ad-valorem K-12 GO, TAX EXEMPT, AB-1200 clean. FLAG: traded TODAY 99.132, -0.487pt vs list mark (just inside 0.5pt threshold) — refresh limit.",
 "tax_status":"TAX EXEMPT (EMMA field; SOURCE OF REPAYMENT: GENERAL OBLIGATION; no AMT)","pledge_confirmed":True,
 "callable":True,"next_call":"2026-08-01 @ 100 (par)",
 "live_last_trade_px":99.132,"live_last_trade_date":"2026-06-10",
 "tape_moved_pt":-0.487,
 "recomputed_tey_at":0.0819,"tey_divergence_pp":0.0008,
 "issuer_resolved":"Chula Vista Elementary School District, School Facilities Imp Dist No.1, San Diego County (CA) — OpenFIGI 'CHULA VISTA ESD-C-BAM' (BAM bond insurance wrap); matches list",
 "ab1200":"POSITIVE (absent from CDE First & Second 2024-25 Negative/Qualified lists)",
 "notes":"BAM-wrapped — credit floor at BAM (AA) regardless of district. Fresh 06-10 prints 99.132 are -0.487pt below list 99.619; TEY at fresh mark 0.0819 (still ~par, above de-minimis thr 96.21). Limit 100.12 comfortably above fresh — still executable; just lower the working price toward ~99.2-99.4 rather than chasing 100.12."
})

# 4) 358233ED2 — Fresno USD GO Ref Bds 2016F
add({
 "cusip":"358233ED2","verdict":"CLEAR",
 "basis":"Fresno Unified SD (Fresno County) GO Bds Elec-2010 Ser F (2016 refunding) — unlimited ad-valorem K-12 GO, TAX EXEMPT; AB-1200 clean (absent both periods, both spellings); traded TODAY at exact list mark.",
 "tax_status":"TAX EXEMPT (EMMA field; no AMT)","pledge_confirmed":True,
 "callable":True,"next_call":"2026-08-01 @ 100 (par)",
 "live_last_trade_px":83.954,"live_last_trade_date":"2026-06-10",
 "tape_moved_pt":0.0,
 "recomputed_tey_at":0.0808,"tey_divergence_pp":0.0,
 "issuer_resolved":"Fresno Unified School District, Fresno County (CA) — OpenFIGI 'FRESNO USD-F-UNREFD'; matches list. (EMMA title header truncates to 'SNO UNIFIED' in nav crumb but full title = FRESNO UNIFIED SCHOOL DISTRICT)",
 "ab1200":"POSITIVE — Fresno Unified absent from CDE First & Second 2024-25 Negative AND Qualified lists (no Fresno-County district flagged); big-district double-check clean",
 "notes":"Freshest possible: 06-10 customer SALE at 83.954 = list mark exactly. Deep discount, de-minimis breach (thr 96.21). Limit 84.45."
})
print("checkpoint B done")
