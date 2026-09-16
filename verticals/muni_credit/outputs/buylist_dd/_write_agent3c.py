import json
OUT = "/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/buylist_dd"
PATH = f"{OUT}/agent3.json"
results = json.load(open(PATH))
def add(o):
    results.append(o)
    json.dump(results, open(PATH,"w"), indent=1)
    print("wrote", o["cusip"], o["verdict"])

# 5) 777387AH4 — ROSELAND Elem (Sonoma), MISBOUND in list as "Rosemead Elementary / Los Angeles"
add({
 "cusip":"777387AH4","verdict":"FLAG",
 "basis":"Bond is a clean TAX-EXEMPT unlimited ad-valorem K-12 GO, but ISSUER MISBOUND: EMMA+OpenFIGI = ROSELAND Elementary SD, SONOMA County — list says 'Rosemead Elementary / Los Angeles'. Fault-zone (LA Basin) and county overlay are wrong; re-credit before buy.",
 "tax_status":"TAX EXEMPT (EMMA field; Bank Qualified; no AMT)","pledge_confirmed":True,
 "callable":True,"next_call":"2026-06-30 @ 100 (par)",
 "live_last_trade_px":98.38,"live_last_trade_date":"2026-06-04",
 "tape_moved_pt":0.566,
 "recomputed_tey_at":0.0841,"tey_divergence_pp":0.0,
 "issuer_resolved":"ROSELAND ELEMENTARY SCHOOL DISTRICT, County of Sonoma (CA), GO Bds Elec-2012 2013 Ser A (Bank Qualified) — OpenFIGI 'ROSELAND ELEM SD-A'. LIST MISLABEL: 'Rosemead Elementary' (Los Angeles) is a DIFFERENT district; identity corrected to Roseland/Sonoma.",
 "ab1200":"POSITIVE — Roseland Elementary absent from CDE First & Second 2024-25 Negative/Qualified lists (Sonoma flagged: Forestville, Santa Rosa Elem/High, Sonoma Valley — Roseland not among them)",
 "notes":"Tape: freshest 06-04 print 98.38 is a dealer PURCHASE (+0.566pt above list 97.814, exceeds 0.5pt flag); last customer SALE 97.814 (04-06, ~2mo). Limit 98.31 is BELOW the 98.38 dealer level — offers likely at/above limit, executability tighter; do not chase. Fault-zone in list (LA Basin) is wrong — Roseland sits in Sonoma (Bay/N San Andreas-Rodgers Creek), re-run wildfire/seismic overlay. Tiny issue ($2.165M) — thin name. Per memory: small-N single-name fault overlay is low-confidence regardless."
})

# 6) 607735CA3 — MODESTO CITY ELEMENTARY (Stanislaus), MISBOUND in list as "Modesto City High"
add({
 "cusip":"607735CA3","verdict":"FLAG",
 "basis":"Bond is a clean TAX-EXEMPT unlimited ad-valorem K-12 GO, but ISSUER MISBOUND: EMMA+OpenFIGI = MODESTO CITY ELEMENTARY SD — list says 'Modesto City High'. Different district (Elementary, not High); both Stanislaus, but credit/AB-1200 must bind to the Elementary district.",
 "tax_status":"TAX EXEMPT (EMMA field; SOURCE OF REPAYMENT: GENERAL OBLIGATION; no AMT)","pledge_confirmed":True,
 "callable":True,"next_call":"2027-08-01",
 "live_last_trade_px":81.404,"live_last_trade_date":"2026-05-22",
 "tape_moved_pt":0.0,
 "recomputed_tey_at":0.083,"tey_divergence_pp":0.0,
 "issuer_resolved":"MODESTO CITY ELEMENTARY SCHOOL DISTRICT, Stanislaus County (CA), GO Bds Elec-2018 Measure E Ser A — OpenFIGI 'MODESTO CITY ESD-A'. LIST MISLABEL: 'Modesto City High' is the separate Modesto City HIGH School District; identity corrected to Modesto City Elementary.",
 "ab1200":"POSITIVE — Modesto City Elementary absent from CDE First & Second 2024-25 Negative/Qualified lists (no Stanislaus district flagged)",
 "notes":"Tape: last print 05-22 (19 days) at 81.404 = list mark; no move, but no print in 19d and list flagged it dated — somewhat thin, work patiently. Deep discount, de-minimis breach (thr 95.72). Limit 81.9. Identity correction does not change the GO/tax-exempt verdict (still a Stanislaus K-12 GO) but the credit overlay should bind to MCESD, not the High district."
})
print("checkpoint C done — all 6 written")
