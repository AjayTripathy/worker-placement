import urllib.request

topic = open('desk/data/ntfy_topic.txt').read().strip()
title = 'Gauntlet 08-06: MMS MISS (no entry), FOUR MISS (decline vindicated) - no orders'
body = (
    "2 prints detected+adjudicated from primary EDGAR exhibits; NO orders implied by either branch.\n\n"
    "MMS: MISS - FQ3 signed awards ~$337M ($1.25B YTD minus $913M prior) vs the $1.3B gate; the 2% entry "
    "stays shut, NO-GO kept. p=0.40 graded well (Brier 0.16). Tell for next quarter: pending-unsigned "
    "jumped $322M -> $1.35B (delay-not-loss showing pre-signature). FY26 adj-EPS guide trimmed to 7.90-8.20.\n\n"
    "FOUR: MISS - quarter beat both bars (GRLNF $624M vs 615M, adj EBITDA $284M vs ~278M, organic +11%) but "
    "FY26 GRLNF midpoint CUT ~200bps (Mideast travel + FX; FCF conv 42->40%), so the 0.62 BULLISH conjunction "
    "fails (Brier 0.384). Pre-mkt -3.3% to 53.38. Miss channel = Global Blue travel/FX, NOT SMB softness. "
    "Date-mismatch branch closed (8-K primary-confirms Aug-6). Two redate-churn duplicate rows VOIDED (DEDUP).\n\n"
    "Not gradeable this morning: AMV0/G/CACI/TTD/MCHP/ONTO print later today; G-STK/UPBD-STK/CRH-STK need "
    "today's close. CSP-SCAN + EXIT-BAND-SWEEP = interactive-session ops items. "
    "Details in desk/data/gauntlet_verdicts.json."
)
req = urllib.request.Request(
    f'https://ntfy.sh/{topic}',
    data=body.encode(),
    headers={'Title': title, 'Priority': 'default', 'Tags': 'balance_scale'},
)
print(urllib.request.urlopen(req, timeout=30).status)
