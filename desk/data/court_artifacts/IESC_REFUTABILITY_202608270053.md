## Context

**The event is an artifact, not a dislocation.** IESC distributed a **2-for-1 stock split after the close on Friday 2026-08-21**, first trading split-adjusted on Monday 2026-08-24. The screen's 5-day return crossed that boundary on an **unadjusted** price series, so it booked the split factor as a price collapse. The true 5-day move was about **-10%**, and the company's most recent print was one of the strongest in its history.

**The arithmetic, exactly.** The event blob's `d1: -0.0336` reconstructs as Aug-25 close $313.23 ÷ Aug-24 close $324.12 − 1 = **−3.36%** — so the screen ran as of the Aug 25 close, and its 5-day window opens Aug 19 ($348.69 split-adjusted). Unadjusted, that Aug 19 close is $697.38; against $313.23 that is **−55.1%**, versus the reported `excess_5d` of **−54.9%**. The match is to within 0.2pp — the "excess" is essentially the raw split break, barely beta-adjusted. Split-adjusted, the same window is **−10.2%**.

The internal contradiction was visible before any research: IBKR's (split-adjusted) tape in the pack shows `dd52 = −0.165` and `pct_off_low = +1.046`. A stock that truly fell 55% in five sessions is not 16.5% off its 52-week high and up 105% from its low. Two price series disagreeing by exactly 2.0× is the split.

**Second defect, same root cause:** the blob's `mcap` of $6,240,906,030 ÷ $313.23 = 19.92M shares — the **pre-split** count against a **post-split** price. Post-split shares are ~40.2M (20,104,257 diluted × 2), so true market cap is **~$12.5–13.7B**, understated ~2×. Any valuation screen keying off this field ranked IESC at half its real size.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| IESC | **DAMAGE-ABSENT** — event is a split artifact, cohort membership void | Backlog & operating income (the metrics any demand-destruction narrative must dent) | Backlog **$4.5B, +91%** since FY25 year-end; RPO **$2.8B**; Q3 FY26 revenue **$1,242.7M, +40% YoY**; operating income **$178.5M, +60% YoY** (margin 14.4% vs 12.6%); net income **$153.0M, +98%**; **zero total debt**, $77.3M cash + $310.6M marketable securities. Reported 2026-07-31, quarter ended 6/30/26. Primary: [8-K 0001048268-26-000131](https://www.sec.gov/Archives/edgar/data/0001048268/000104826826000131/q32026pressrelease-june.htm) | **2026-11-20 — UNCONFIRMED** | Revenue cross-checks against the pack's own XBRL: $890,158,000 (2025-06-30) × 1.40 = $1.246B ✓. Damage is not merely absent — every metric is accelerating into a record backlog. |

**Citation note:** sec.gov returned HTTP 403 to automated fetch; the 8-K's contents were read through the GlobeNewswire wire mirror of the identical release ([Manila Times syndication](https://www.manilatimes.net/2026/07/31/tmt-newswire/globenewswire/ies-holdings-reports-fiscal-2026-third-quarter-results-and-announces-two-for-one-stock-split/2395864/amp), [StockTitan](https://www.stocktitan.net/news/IESC/ies-holdings-reports-fiscal-2026-third-quarter-results-and-announces-jh6rq87hw0fp.html)), which is the same document EDGAR indexes. Split-adjusted closes from [stockanalysis.com](https://stockanalysis.com/stocks/iesc/history/).

## COURT-WORTHY (damage-absent, ranked)

**None.** IESC is damage-absent, but it does not qualify as court-worthy, because there is no dispersion-vs-cohort to arbitrage — there was no sell-off to disperse from. Sending this to a red/blue court would have the bench litigating a price move that never happened. Two further reasons the discount isn't there to be captured:

- **The stock is near highs, not dislocated.** $341 against a $408.26 52-week high and $166.63 low. It gapped **+30% on the July 31 print**; the −10% since is ordinary post-run consolidation.
- **On corrected market cap it is not cheap.** At ~$12.5–13.7B against a TTM earnings base in the ~$400–500M range, IESC trades near **~30× earnings** — a richly-priced data-center-electrical compounder. The $6.24B mcap that made it look reasonable was the split error.

**One genuine fundamental item, flagged but out of window:** the 8-K dated 2026-08-11 (event 2026-08-07) discloses IES acquiring **~92% of DBM Global from Innovate Corp for a $650M base price**, part-funded with 215,487 IES shares (pre-split; ~431k post-split, ~$147M). This is a real bear-side consideration — structural steel fabrication is a lower-multiple, more cyclical business than data-center electrical, so it risks multiple dilution and is a capital-allocation question worth asking. It is **not** the cause of the flagged event (Aug 7–11 falls outside the Aug 19–25 window) and does not by itself justify a court.

## PRINT PROXIMITY

**PRINT PROXIMITY: 2026-11-20 — UNKNOWN/UNCONFIRMED.** The pack's date is yfinance-derived and I found **no company press release naming it**; I am not treating it as confirmed. Independently bounded: IES's fiscal year ends **September 30** (confirmed via the release's reference to the Form 10-K for the year ended September 30, 2025), so FY26 Q4/full-year results land in **late November 2026** — roughly 60 trading days out. **No print lands within 5 trading days**, so the print-decisive reconstruction is not triggered and no pre-print position call is required. The recently-signed DBM transaction has no disclosed closing date and could produce an 8-K sooner; that is an unscheduled event, not a print.

**COURT-WORTHINESS IESC: 2/10 — the triggering −55% is an unadjusted-split artifact, so a dislocation court would adjudicate a move that never occurred; the real tape is −10% into record backlog at ~30× on a market cap the screen halved.**

---

## What actually needs fixing

The valuable output here is a screen defect, not a name. This is the third member of the vendor price-artifact family already in memory (alongside PTS after-hours marks and the BYND unadjusted reverse split that read +2538% when the real move was −12%) — same failure, forward direction. Two concrete gaps:

1. **`class_dislocation` computes multi-day returns on an unadjusted series.** A corporate-action check across the return window would have suppressed this event. The `include_corporate_actions` flag on IBKR's `get_price_history` is the ready-made guard.
2. **`mcap` mixes a pre-split share count with a post-split price.** This is the more dangerous of the two, because it silently mis-ranks names in *every* screen keying off market cap, with no −55% flare to make it obvious.

A cheap invariant catches both: **reject any event where `|excess_5d|` is irreconcilable with `dd52`** — you cannot fall 55% in a week and sit 16.5% off the high. That single assertion would have killed this event record before it ever reached a bench.

I did not write the artifact to `BROKEN_PRINTS.json` or patch the detector — both live outside this working directory and the reads were denied in this non-interactive session. Say the word and I'll make those edits. Also worth noting: the `COHORT` and `NARRATIVE` slots in the prompt are literal `?` because `knowledge_graph/cohorts.json` was unreadable, so I tested the damage *implied* by a −55% collapse rather than a named cohort thesis. That doesn't change the finding — the event is void at the tape level, before any narrative applies.