## BLUE BENCH — CMTG — RED CASE: PARTIALLY OVERTURNED

PACK: acknowledged. Superseded: XBRL block (year-stale, both benches concur). Checks run this session: [earnings-call transcript](https://www.investing.com/news/transcripts/earnings-call-transcript-claros-mortgage-trust-posts-q2-2026-loss-shares-fall-93CH-4825272), [slides summary](https://www.investing.com/news/company-news/claros-mortgage-q2-2026-slides-show-255m-loss-portfolio-cleanup-93CH-4825601), [AOL Ex-99.1 syndication](https://www.aol.com/articles/claros-mortgage-trust-inc-reports-201500000.html), [2026 proxy via StockTitan](https://www.stocktitan.net/sec-filings/CMTG/def-14a-claros-mortgage-trust-inc-definitive-proxy-statement-0b922318dadc.html). SEC direct 403'd; IBKR tape and local desk stores permission-denied — tape leg stays a coverage gap.

1. {45%-severity strawman | proxy + release re-derivation | Fees CONFIRMED: $32.101M mgmt+incentive, $36.255M total 2025. But red's bleed stack double-counts: **distributable loss ex-realized items was −$0.07/sh/q** (release), not $0.36 — the $0.36 GAAP ex-provision figure embeds realized credit losses (the severity already being adjudicated) and non-cash REO items, and the fee sits inside it. Right drag denominator is book: $36.3M/$1.21B ≈ 3.0%/yr ($0.26/sh). Even a generous $2–3/sh NPV of bleed+fees nets the $6.64 gap to ~$3.5–4.5/sh ≈ 15–19pp incremental ≈ **~32–36% implied lifetime severity vs 16.9% reserved** — a real, testable gap | REDUCED: fee-misalignment stands; "gap largely isn't there" overreaches, and "13% of cap" is rhetorical framing}
2. {watchlist decline = migration | transcript + slides | $477M decline/12 loans CONFIRMED; but the call says the four downgrades were **$372M** (release: $447M — UPB/carrying discrepancy, red's near-equality is fragile), management describes the watchlist as the troubled-asset set declining $2.7B→$1.7B→$1.1B, and YTD resolutions of $1.0B at 43%-par mix are the larger H1 driver. Red's back-solve stands: specific-reserve UPB ≈ $517M/0.32 ≈ **$1.6B > $1.2B watchlist**, so the definitional hole is real | REDUCED to SIZING-minor; the 10-Q rating table remains the check}
3. {survivorship in the refuting metric | re-derived | par exits mechanically raise reserve-%-of-UPB with zero new impairment; correct metric = cumulative realized severity on resolutions vs reserve-implied | CONFIRMED — SUSTAINED, red's best finding}
4. {$161.3M unfunded on troubled loans ≈ liquidity | 10-Q unreachable (403), slides/transcript silent | cannot reproduce; also quoted gross — unfunded commitments typically draw matching financing-line advances, so equity cash need < face | REDUCED to PLAUSIBLE; cannot carry weight}
5. {serial provisioning | slides | $2.08/sh H1 CECL CONFIRMED; but **$0.89/sh was general (portfolio-overlay) reserve**, not new name-specific holes | SUSTAINED as TIMING, softened}
6. {priced-in | IBKR/discovery denied again | covered institutional name, not an orphan — orphan discipline doesn't overturn; tag honest | PLAUSIBLE — stands as gap}

Selection judgment: red attacked the strongest leg (the arithmetic) — good selection — but inflated it with a double-count (the desk's own recent reject class).

NEW FINDINGS RED MISSED: (a) −$0.07/sh distributable ex-realized run-rate (CONFIRMED) — the single most bull-favorable number in the print, absent from both benches; (b) January-2026 corporate term loan has repayment priority over any equity-friendly redeploy (call, CONFIRMED) — proceeds waterfall delays every catalyst incl. the mooted buyback; (c) $447M-vs-$372M downgrade discrepancy (CONFIRMED, unresolved); (d) covenant disclosures unverified either way — nobody has read the 10-Q covenant note; reportable gap.

NET POSITION AFTER BOTH BENCHES: **FLAT stands; court-worthiness 5–6/10.** What survives: a genuine ~32–36%-implied vs 16.9%-reserved severity gap, but with no re-rate mechanism (fee drag, term-loan waterfall, no originations, no dividend) and a misspecified refuting metric. Re-entry gate at the Q3 print (~2026-11-04, unconfirmed): blended realized severity on Q3 resolutions ≤ ~15%, distributable ex-realized ≥ breakeven, RR5 adds < resolutions, and the 10-Q rating table read. Conviction: **7/10**.

## DETECTORS CONSULTED
- census_acs — NOT-FIRED: wrong channel (office/construction credit severity, not market rent); planner ruling concurred.
- hud_fmr — NOT-FIRED: same wrong-channel concurrence.
- planet_imagery — UNCHECKABLE: no collateral address schedule in pack or filings read.
- sentinel2_buildout — UNCHECKABLE: same missing collateral addresses.
- tdlr_ihb — NOT-FIRED: no TX modular exposure.
- tenant_credit_watch — NOT-FIRED: lender, not landlord; no named tenants.
- chinese_smallcap_ramp_dump_archetype — NOT-FIRED: MD-domiciled NYSE REIT, no Cayman/Asia features; feature match was spurious.
- common_control_merger_accounting — NOT-FIRED: no common-control absorption in the filing inventory.
- lockup_expiration_calendar — NOT-FIRED: 2026-07-17 S-8 is a comp plan; no follow-on.
- pe_dividend_recap_pre_ipo — NOT-FIRED: no PE-sponsor pre-IPO recap pattern (Mack-affiliated external manager, IPO 2021, no recap in inventory).
- albuquerque_permits — UNCHECKABLE: no named ABQ collateral.
- austin_permits — UNCHECKABLE: no named Austin collateral.
- beauty_velocity_poll — NOT-FIRED: no consumer-virality claim; spurious feature match.
- beauty_virality — NOT-FIRED: same.

Note: red consulted four detectors (bozeman_permits, customer_id, fema_nri_hazard, forest_integrity) not in this case's atlas and skipped four that are (chinese_smallcap_ramp_dump_archetype, pe_dividend_recap_pre_ipo, beauty_velocity_poll, beauty_virality) — dispatch-list drift between benches is itself a validator finding for the runner.

```kg_candidate
{"name": "gaap_ex_provision_bleed_conflation", "kind": "detector", "one_line": "Bear cases on impaired lenders that quote GAAP loss ex-provision as run-rate operating bleed double-count credit: realized losses and non-cash REO items sit inside it, and the management fee gets stacked again separately.", "fires_on": "kill-case citing GAAP ex-provision loss as recurring drag when distributable/adjusted earnings ex-realized items differs by >2x, or fee drag quoted as % of market cap alongside an ex-provision bleed that already expenses the fee", "evidence_here": "CMTG Q2-26: red bench used $0.36/sh/q GAAP ex-provision + 13%-of-cap fee drag; actual distributable loss ex-realized = $0.07/sh/q with fees inside it", "applies_to_guess": {"issuer_features": ["credit_impairment_cycle", "externally_managed", "distributable_earnings_reporter"], "sic_prefixes": ["6798", "6500", "6159", "6022"]}}
```

Closing-step note for the runner: ledger upsert / entry-plan / scanner re-run could not execute this session — no Bash and desk data-dir reads were permission-denied; the adjudicator should apply the standing dashboard rule when merging this verdict.