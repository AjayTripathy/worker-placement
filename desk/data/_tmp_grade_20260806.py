import json

PATH = 'desk/data/calibration_ledger.jsonl'
rows = [json.loads(l) for l in open(PATH)]

mms_res = {
    "date": "2026-08-06",
    "outcome": "UNFAVORABLE",
    "y": 0.0,
    "px_at_resolve": 63.15,
    "px_note": "pre-market last vs 63.33 prior close",
    "note": ("MISS, decisive: FQ3 quarterly signed awards ~= $337M ($1.25B YTD Jun-30 per 8-K ex-99.1 "
             "0001032220-26-000033 minus $913M YTD Mar-31 per the May-7 ex-99.1) vs the $1.3B bar; "
             "quarterly b2b ~0.26x on $1.28B revenue. PREMISES: the frozen central case (PARTIAL recovery "
             "short of $1.3B) held directionally but overstated the recovery — signings barely moved. "
             "The 'delay not loss' shape DID appear one stage earlier: contracts pending (awarded-but-unsigned) "
             "jumped $322M -> $1.35B, i.e. awards are landing but not converting to signature. "
             "Context (not the bar): FY26 revenue guide reiterated (toward low end); adj-EPS guide trimmed to "
             "$7.90-8.20 on a temporary customer-directed contractual modification on a major federal program. "
             "Our p=0.40 on HIT -> Brier 0.16, good skeptical call.")
}

four_res = {
    "date": "2026-08-06",
    "outcome": "UNFAVORABLE",
    "y": 0.0,
    "px_at_resolve": 53.38,
    "px_note": "pre-market last vs 55.20 prior close (-3.3%)",
    "note": ("MISS on the conjunction: 2 of 4 legs PASSED (Q2 GRLNF $624M >= $615M guide, +51% YoY; "
             "adj EBITDA $284M >= ~$278M; organic growth 11%) but the FY26 guide was NOT reaffirmed/nudged-up — "
             "midpoint of FY GRLNF cut ~200bps (~$25M Middle-East travel disruption assumed for Q3 + ~$20M FX), "
             "total GRLNF growth guide 20% -> 19% (organic 25% -> 22%), adj-FCF conversion 42% -> 40% — and the "
             "Global Blue TFS headwind did not hold neutral (Q2 slightly better than feared, but the persisting "
             "conflict drove the forward cut). Source: 8-K ex-99.1 0001794669-26-000042, filed 2026-08-06 07:06 "
             "(date-mismatch branch CLOSED: print date Aug-6 confirmed from primary). PREMISES: the sandbagged-"
             "quarter beat held; the Taylor-era reaffirm/raise pattern FAILED. The miss channel was Global Blue "
             "travel/FX, NOT SMB-restaurant softness (organic +11%) — the fast-casual macro read gets no "
             "confirmation from this print. Our p=0.62 BULLISH -> Brier 0.384.")
}

n_res = n_void = 0
for r in rows:
    if r.get('ticker') == 'MMS' and r.get('cat_date') == '2026-08-06' and r.get('made') == '2026-07-02' and r.get('status') == 'OPEN':
        r['status'] = 'RESOLVED'
        r['resolution'] = mms_res
        n_res += 1
    elif r.get('ticker') == 'FOUR' and r.get('cat_date') == '2026-08-06' and r.get('status') == 'OPEN':
        if r.get('made') == '2026-07-01':
            r['status'] = 'RESOLVED'
            r['resolution'] = four_res
            n_res += 1
        elif r.get('made') in ('2026-08-02', '2026-08-05'):
            r['status'] = 'VOIDED'
            r['voided_on'] = '2026-08-06'
            r['void_reason'] = ("DEDUP: duplicate of the kept FOUR|2026-08-06 (made 2026-07-01, resolved "
                                "UNFAVORABLE 2026-08-06) — redate churn on 08-02/08-05 re-froze the same "
                                "our_p+catalyst as new rows. Voided so the Brier is counted once, not 3x. "
                                "Same DEDUP convention as the 2026-08-05 taxonomy pass.")
            n_void += 1

assert n_res == 2 and n_void == 2, f"unexpected match counts: resolved={n_res} voided={n_void}"

with open(PATH, 'w') as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f"ledger updated: {n_res} resolved, {n_void} voided, {len(rows)} rows total")
