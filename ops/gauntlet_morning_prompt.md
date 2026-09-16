GAUNTLET MORNING ADJUDICATION (headless). Read desk/data/gauntlet_flags.json (today's detected prints)
and desk/data/resolution_packs.json. For each detected print: (1) fetch the actual filing/PR and extract
the numbers the pack's adjudication spec names; (2) grade the frozen calibration call in
desk/data/calibration_ledger.jsonl (append resolution + which premises held); (3) determine the branch and
write desk/data/gauntlet_verdicts.json: {ticker, verdict, branch, order_params: {side, qty, limit_cap, tif}
if the branch implies an order, else null, reasoning: 2 sentences}; (4) run python3 -m desk.catalyst_mispricing
and python3 -m desk.consistency_check; (5) send the ntfy notification (desk/data/ntfy_topic.txt) with the
verdict + order params. DO NOT place or stage orders (broker tools unavailable/prohibited headless) — the
user or the interactive session executes from gauntlet_verdicts.json. Never revise frozen predictions.

FUZZY-EVENT ESCALATION RULE (added 2026-07-20, the CIB lesson): a resolution pack tagged
`event_class` starting "POLITICAL/MACRO" — or ANY event whose outcome is not a crisp published
number (a coalition forming, a levy "effectively dying", a court window) — must NOT be force-graded
HIT/MISS. Instead: write it to gauntlet_verdicts.json with verdict="ESCALATE" + the facts you found +
the recommended resolution date, and DO NOT touch its calibration_ledger row. Only auto-grade calls
whose outcome is a crisp scrapeable number (company comps/organic-growth/EPS vs the pack's stated
threshold; a deal closing yes/no; a monthly data print vs a band). Crisp -> grade; fuzzy -> escalate.
