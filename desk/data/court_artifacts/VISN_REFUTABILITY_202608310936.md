## VISN — Refutability Triage

**Context:** The trigger is an artifact — the "-46% 5d excess" is the ex-date of a **$5.00/share special cash distribution (ex 2026-08-28)**, not narrative selling; the real, separate story is a memory-chip cost shock hitting a now debt-free post-liquidation stub.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| VISN | **DAMAGE-ARRIVING** | Aurora core adj. EBITDA + FY26 Aurora adj-EBITDA guide (memory-chip cost pass-through) | Q2'26 core adj. EBITDA **$45.5M, −43.3% YoY**; adj. EBITDA $35.8M = **11.2% margin vs 16.3%** LY; FY26 Aurora guide **cut $25M to $200–225M**, memory impact **~$40M** FY26; mgmt: environment "deteriorated faster and further than we expected." Sales $319.6M, −1.4% (stable) — the damage is **margin, not demand**. ([8-K](https://www.stocktitan.net/sec-filings/VISN/8-k-vistance-networks-inc-reports-material-event-eb3fa503332b.html), [Q2 slides](https://www.investing.com/news/company-news/vistance-q2-2026-slides-5-distribution-set-amid-margin-pressure-93CH-4843056)) | **2026-10-29 (UNCONFIRMED**, yfinance-derived; no company PR names it) | **COHORT ROW VOID** — see artifact finding below |

### Artifact finding (kills the trigger, not the name)
- **$5.00/share special distribution, ex-date 2026-08-28**, record 8/17, paid 8/27, $1.15B total. Nasdaq Rule 11140(b)(2) forces the ex-date to fall the business day *after* payment when a distribution is ≥25% of stock value — an **inverted ex/pay ordering** naive screens get wrong. ([stocktitan](https://www.stocktitan.net/news/VISN/vistance-networks-board-approves-special-m9lc1sqvbz2w.html), [stockanalysis](https://stockanalysis.com/stocks/visn/dividend/))
- A **second $10.00/share** distribution went ex 2026-04-28. Total **$15.00/share ≈ $3.4B returned in 2026** — vs. a $6.10 stock.
- Therefore the pack's `dd52 −53.9%` and `pct_off_low 1.7%` ("at 52-week lows") are **both unadjusted-series artifacts**. Total-return holders received $15 cash and hold a $6.10 stub.
- **Pack XBRL is unusable here:** newest row is 2025-06-30 at $1,388.1M/qtr on the *pre-divestiture* perimeter. Actual continuing ops are **$319.6M/qtr** — a 4.3× overstatement. The `dil_sh` 271.9M spike was if-converted Series A preferred, since **fully redeemed**.

### What is actually left (the re-framed question)
RUCKUS sold to Belden 7/1/26 for **$1.846B** cash; **long-term debt $7.26B (YE25) → zero (6/30/26)**; post-distribution cash **$700–750M, no debt**; **$250M buyback** authorized ($100M 4/30 + $150M 8/26 per the pack's primary 8-K) = ~18% of market cap; **$160M tax refund** expected H2'27.

At $6.10 × ~230M sh = **$1.40B mcap − ~$725M net cash ⇒ EV ≈ $675M** against a **$200–225M** FY26 EBITDA guide ⇒ **~3.2× EV/EBITDA**, with **net cash ≈ $3.15/sh = 52% of the price**.

**The decisive tension:** Q2 core adj. EBITDA of $45.5M does not annualize into a $200–225M FY guide — H2 must step up materially *while* memory costs worsen. Reconstructing H1 actuals vs. the implied H2 ramp (needs the Q1'26 core figure) is the single highest-value pre-court item.

**COURT-WORTHY (damage-absent, ranked):** **NONE.** VISN is not damage-absent — margin damage is present, quantified (~$40M), and explicitly unresolved by management. It is court-worthy on a *different* axis: net cash at 52% of price and ~3× EV/EBITDA vs. an actively deteriorating input cost. Any court must be re-framed off the dislocation premise, which is void.

**PRINT PROXIMITY: 2026-10-29 — UNCONFIRMED (yfinance-derived; no company PR names it; the 2026-08-06 Q2 print is confirmed and already past).** ~41 trading days out, so not within the 5-day window; no print-race reconstruction required.

**PRE-PRINT POSITION: FLAT (no order).** Not because the discount is correct — it may well be wrong — but because the entry premise that fired here doesn't exist, and doctrine bars staging ahead of a court. The asymmetry (52% net cash, 18%-of-cap buyback, zero debt) is real enough to justify the re-framed court now rather than waiting for 10/29.

**COURT-WORTHINESS VISN: 6/10 — trigger is a distribution artifact and must be voided, but the residual debt-free ~3× EV/EBITDA stub with net cash at half the price is a genuine sizing question a court would move.**

---

Two things worth flagging beyond the triage:

**The screen has a reproducible bug.** The dislocation detector treats large special cash distributions as price collapse, and the 52w hi/lo fields inherit the same unadjusted series. The fix is a distribution-adjustment guard on returns *and* on the drawdown fields, with explicit handling for the Rule 11140(b)(2) inverted ex/pay ordering — that ordering is what makes the usual "ex-date ≤ pay-date" assumption fail. VISN would have been caught by a check that any 5d excess move beyond ~-25% must clear the dividend/distribution table first. This belongs as a fifth entry in the vendor price-artifact family alongside the unadjusted reverse-split case; I could not persist it — this session has no write tool, so the memory update needs a follow-up.

**Sourcing limitation, stated plainly:** EDGAR returned 403 on every direct attempt (browse-edgar, data.sec.gov, and Archives), and the IBKR contract lookup needed a permission grant this non-interactive session can't obtain — so I could not bar-check the tape myself or read the 10-Q directly. My figures come from the evidence pack's own primary 8-K excerpt plus secondary reporting of the 8-K/press release, cross-checked across two independent sources for the load-bearing debt and cash numbers. The one item I could not verify at all is the pack's `d1 −8.6%`: it is inconsistent with an ex-date drop (~−45%) and with the $6.06 close on 8/28 against the $6.10 pack tape, so it needs a bar check before anyone leans on it.