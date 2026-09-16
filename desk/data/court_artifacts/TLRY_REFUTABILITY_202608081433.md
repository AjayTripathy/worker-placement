## CAUSE-CHECK (run first, per event spec)

The −80.9% dd52 is **not** an unexplained blob. Chain, in order:

1. **hi52 $23.20 is split-adjusted.** Tilray executed a **1-for-10 reverse split effective Dec 2, 2025**, taking the count from ~1.16B to ~116M shares, done to cure a Nasdaq $1.00 minimum-bid deficiency (notice received Mar 25, 2025). $23.20 post-split = **$2.32 pre-split**, which places the high *before* the split — in the autumn-2025 rescheduling melt-up, not in 2026. (Exact high date is derived from split arithmetic, **not** tape-verified — the IBKR history/snapshot calls were permission-denied this session; px/hi52/lo52 in the pack are already `ibkr_gw`-sourced.)
2. **The catalyst arrived and was worth ~nothing to this issuer.** Trump's Dec 18, 2025 EO → TLRY +28% intraweek, closed the week **−7.4%**. DOJ implementation ~Apr 22, 2026 rescheduled only FDA-approved and state-regulated *medical* product; rec was untouched. TLRY sells no US THC, so the move was never in its P&L either way.
3. **The de-rate is an option expiring worthless, plus per-share dilution** — see below.

So: the drawdown is a round-trip of a policy option, layered on a mechanical issuance program. Nothing is missing from the cause ledger.

## TRIAGE

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| TLRY | **STRUCTURAL** | Adj. EBITDA **per weighted diluted share**, and FCF **before** working capital | Adj EBITDA/sh **$0.547** FY26 (61.1M/111.8M) vs **$0.620** FY25 (55.0M/88.7M) = **−11.8% YoY**; revenue/sh $8.19 vs $9.30 = **−11.9%** despite "record" +11% revenue. FCF-ex-WC = **−$11.3M** (OCF-before-WC +$18.2M − $29.5M capex). Weighted shares **+26% FY26 to 111.8M**, +18% in Q4 to 115.5M, **131.7M** now outstanding. [FY26 PR, 2026-07-28](https://www.globenewswire.com/news-release/2026/07/28/3334721/0/en/Tilray-Brands-Delivers-Record-Fiscal-2026-Revenue-and-Adjusted-EBITDA-Demonstrating-the-Strength-of-its-Diversified-Global-Platform-Across-Cannabis-Beverage-Hospitality-and-Wellnes.html) · [10-K 0001437749-26-024698](https://www.sec.gov/Archives/edgar/data/1731348/000143774926024698/) | **2026-10-08** (yfinance-derived, UNCONFIRMED — no company PR names it yet) | FY27 guide of $68–75M adj EBITDA is **flat-to-down per share** at a frozen 131.7M count ($0.516–0.569 vs $0.547 FY26, $0.620 FY25). Guided "double-digit growth" does not reach the shareholder. |

**Narrative-substitution finding (the trap on this name).** A literal read of the cohort narrative ("US rescheduling failed → operators impaired") returns a **false DAMAGE-ABSENT** for TLRY. That damage genuinely is *not* in the numbers: cannabis revenue +8% FY26, international cannabis **+34%** (Germany +25%, Poland +73%, Italy +53%), Portugal at ~80% utilization / >30 MT annualized; balance sheet clean at cash $229.3M, total debt $147.4M, **net debt $0.7M**. But the discount is correct for a *different*, true narrative the cohort tag doesn't carry: per-share value is being consumed by issuance faster than EBITDA compounds. Classify on the operative narrative, not the tagged one.

**The live mechanical seller.** An **ATM launched April 2026 authorizes up to $180M**; ~**$87M gross was drawn by late July at an average $6.77/share** — i.e. management is a programmatic seller *above* today's $4.44. The residual ~$93M at $4.44 is **~21M shares = +16%** on the current count. FY26 equity sales raised **$158.0M net** against a $98.6M FCF burn: the issuance funds growth and buys assets, it is not distress, and it is not finished. ⚠️ *These ATM figures are secondary-sourced and trace to the 10-K but were not directly verified — EDGAR 403'd my fetcher. This datum is load-bearing for sizing; confirm from the 10-K equity/subsequent-events note before any action.*

## COURT-WORTHY (damage-absent, ranked):

**NONE.** TLRY does not qualify. It clears the cohort's stated narrative but fails on its own operative one, and the failure is arithmetic rather than contestable: FCF is negative even after stripping *all* working capital, and the guided FY27 EBITDA increase is smaller than the issuance already committed. EV is ~$497M (131.7M × $4.44 + $147.4M debt − $235M cash) = 0.54× sales / 7.0× FY27 guided EBITDA — cheap-looking, but the multiple compresses into a share count that grows ~15–25%/yr. A sum-of-parts on beverage ($254M FY26 rev, Q4 **+61%**) plus EU medical is the only bull leg, and it is unrealizable while management is an acquirer-issuer rather than a seller.

## Evidence-pack defects (fix before the next TLRY pack)

- **XBRL block is pre-reverse-split and stale, and the pack instructs downstream to "use THESE for SBC/share/OCF math."** Last `dil_sh` is 2025-02-28 = 908,342,792 — a *pre-split* count. Any per-share math off this pack is wrong by **~10×**. Correct current values: weighted diluted 115.5M (Q4 FY26), 131.7M outstanding.
- `sbc` rows are 2019–2024 quarterlies; `rev` is **empty** — for a company that printed FY results 11 days before the pack was built.
- `mcap` 517,360,344 is stale; 131.7M × $4.44 = **$585M**.
- Form 4 cluster (6 on 07/30, 4 on 07/31, +08/04, 08/07) with an **S-8 on 07/31** is the routine post-print annual grant cycle, not a signal — consistent with the code-P filter already in `filing_watch`.

**PRINT PROXIMITY: 2026-10-08 — yfinance-derived, UNCONFIRMED (no company PR names it; the Q4/FY26 date was pre-announced by PR on 2026-07-13, so expect a comparable ~3-week pre-announcement).** No print lands within 5 trading days; the decisive print (FY2026 10-K + Q4) already landed **2026-07-28**, 11 days ago, and is fully reflected above — so no pre-print reconstruction is owed. The nearer-dated event is not an earnings date at all: it is the **~$93M of unissued ATM capacity**, which can print on any day.

**COURT-WORTHINESS TLRY: 3/10 — the discount is mechanically correct; a court cannot move sizing off zero while a dated, quantified ATM is still selling above the market and FCF is negative before any working capital.**

*(Below the ≥6 auto-escalation threshold — routing to no-court is intended, not a triage failure.)*