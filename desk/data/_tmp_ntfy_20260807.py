import urllib.request

topic = open('desk/data/ntfy_topic.txt').read().strip()
title = 'Gauntlet 08-07: WEN MISS (outlook pulled + div cut), MBGL MISS (guide trimmed, gate removed) - no orders'
body = (
    "2 prints detected+adjudicated from primary EDGAR exhibits; NO orders implied by either branch.\n\n"
    "WEN: MISS/UNFAVORABLE - adj EPS $0.18 beat and US SSS -7.0% seq-better than Q1 -7.8%, but SSS ran worse "
    "than the guided MSD decline, the FY26 outlook was WITHDRAWN and the dividend CUT to $0.07/qtr ($0.28 ann). "
    "New CEO (Bob Wright) turnaround reset; Trian 13D/A still live in risk factors. p=0.45 NEUTRAL graded "
    "UNFAVORABLE (Brier 0.203). Watch-only stays watch-only; the dividend leg of the thesis is moot.\n\n"
    "MBGL: MISS - branch 'guide cut/withdrawn': the 12-May 7.5-9% FY26 organic cc guide was NOT reaffirmed at "
    "print one; replaced with $1,870-1,885M / 6.9-7.7% 'to reflect H1' (H1 +7%, below old low end). CARFAX +8.0% "
    "cleared the 6.5% floor but conditions are conjunctive -> PASS hardens, GATE REMOVED, starter envelopes never "
    "stage. Stand-up costs $36M Q2/$57M H1 (no >$100M FY quant). p=0.55 graded UNFAVORABLE (Brier 0.303).\n\n"
    "Not gradeable this morning: SILICON2/8750.T/ACEL/TCNNF/FNF-ADOPTERNULL/ELV/6804.T/6626.T print later; "
    "EC + IVN are fuzzy POLITICAL/MACRO (escalate-on-substance, no print detected); 8750.T-STK needs close+5d. "
    "FNF/HBB/MCK-REVIEW + 4 EXITREV = interactive-session ops items. Details in desk/data/gauntlet_verdicts.json."
)
req = urllib.request.Request(
    f'https://ntfy.sh/{topic}',
    data=body.encode(),
    headers={'Title': title, 'Priority': 'default', 'Tags': 'balance_scale'},
)
print(urllib.request.urlopen(req, timeout=30).status)
