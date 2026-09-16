# RDDT — Reddit Inc. Class A | COURT_QUEUE_20260804 tier-2 (GUIDE-DECEL + falling)
Court 2026-08-03 for the 08-04 session. **Live basis: IBKR $155.20** (conid 692025016, live tick,
is_close=false, 08-03). Do not use the yfinance 07-31 close of $140.67 — that was the crash print.

## 1. CAUSE-CHECK (done first)
| what | source | result |
|---|---|---|
| Q2'26 reported 2026-07-30 after close | stockanalysis quarterly + yf quarterly income stmt | CONFIRMED: rev $804.9M (+61.1% yoy), op income $231.7M (28.8% margin), net $252.9M |
| the drawdown event | yf daily bars | CONFIRMED: 07-30 close 178.04 -> 07-31 close 140.67 = **-21.0% in one session**; 08-03 IBKR 155.20 = **+10.3% rebound** |
| why it fell despite a beat | Google News RSS, CNBC 07-30 / Motley Fool 08-01 / TechStock 07-31 | CONFIRMED: "US daily users went backward"; "85% of net user growth comes from overseas"; management called Google search referrals **"choppy"** |
| ad line | PPC Land 07-31 | CONFIRMED: ad revenue $762M of the $804.9M total -> data-licensing/other ~$43M (~5%) |
| next print | yf calendar | 2026-10-29. **We are POST-print, not inside a print window.** |

The cause is read and it is specific: a beat-and-raise quarter rejected on **one engagement datum**.

## 2. GATE TEST — FALSE FIRE
Gate: FY+1 rev growth (+31.4%) / most-recent-quarter yoy (+61.1%) = 0.51 < 0.60 -> fires.
But the gate's stated meaning is "estimates tracking down". They are tracking **UP**:
FY26e EPS 4.926 (90d ago) -> 5.330 now (**+8.0%**); FY27e 6.328 -> 6.915 (**+9.3%**), and revised up
again in the 7 days *after* the crash (4.982 -> 5.330). See `_GATE_TEST_GUIDE_DECEL.md`.
The gate is penalising RDDT (score x0.65) for having grown 61% last quarter.

## 3. DE-RATE vs DERAILMENT — split verdict, and that is the whole name
- **Estimate axis = DE-RATE.** Consensus up ~9% over 90d while the multiple compressed 45%. This is
  the HUBS/CTSH/SAP winner signature.
- **Input axis = DERAILMENT RISK.** US DAUq went *sequentially negative* for the first time.
  US users carry roughly 5x the ARPU of international. Estimates are revised off *reported* revenue,
  which lags engagement by 1-2 quarters. So "estimates rising" is a **lagging** confirmation and the
  bear metric is a **leading** one. They are not in conflict; they are in sequence.
- Honesty read: management **disclosed** the US DAU decline in the letter and flagged the referral
  volatility unprompted. Marketed takeaway ("beat on revenue, profit AND guidance") does diverge
  from the highlighted datum, but the datum was not buried. **Disclosed = CLEAN, not a masking
  finding.** The 21% is therefore an *informed* discount, not an opacity discount — which materially
  weakens any "market got it wrong" edge claim.

## 4. PATH CHECK
52w high 282.81, 52w low 119.27 (2026-03-27, 129d ago), 13w low **135.28 set 07-31 (2 sessions ago)**.
-45.1% from the 52w high; +30.1% off the 52w low; **+14.7% off the 2-day-old 13w low.**
Not "exhausted" in the 90-day sense, but we are buying two sessions after a -21% gap and one session
after a +10% snapback. Realised vol is the enemy of a single-tranche entry here.

## 5. CAP STRUCTURE (pulled BEFORE any EV claim)
Ordinary shares **192.41M** (all classes, 06-30 balance sheet) — not the 142.0M "sharesOutstanding"
in the quote feed, which is Class A only. Total debt $20.9M. Cash + short-term investments $2,786M.
**Net cash $2.77B. EV = 192.41M x 155.20 - 2.77B = $27.1B.**
SBC $101.0M in Q2 = 12.5% of revenue — but GAAP op margin 28.8% is already *after* SBC, so the
profitability is real, not adjusted-into-existence. Buyback started: $234.6M repurchased in Q2.

Multiples on the live price: EV/S FY26e (rev $3.358B) **8.1x**; FY27e ($4.410B) **6.1x**;
P/E FY27e (EPS 6.915) **22.4x**. (Note: the feed's "forwardPE 16.07" implies EPS $9.63 and matches no
consensus year — do not use it.)

## 6. AI-COMPLEX CONFLICT (frozen house call AI-BREAK|2027-12-31 @ 0.45)
RDDT is **two-sided**, and this is the one place averaging must not happen:
- **Long AI-capex:** data-licensing to model labs, ~5% of revenue and a chunk of the narrative
  multiple. An AI-capex break cuts this leg.
- **Short the AI-search transition:** AI Overviews / answer-engines are precisely what makes Google
  referrals "choppy". An AI slowdown *relieves* the top-of-funnel pressure that caused the -21%.
Does the entry REQUIRE the cycle holding? **No** — the 95% ad business is consumer ad spend. Does the
de-rate already price the break? **Partially**: 6.1x FY27 EV/S is not a licensing-euphoria multiple.
Net: RDDT is the rare queue name where the house 45% AI-break call is roughly thesis-neutral. It does
not earn a size uplift, but it does not compound the existing $5.2M/26% household AI exposure either.

## 7. SCENARIOS (FY27 basis, 192.41M sh, $2.77B net cash)
| | p | build | FV |
|---|---|---|---|
| bear | 0.35 | US DAU keeps eroding, referral shift accelerates; FY27 rev $3.9B (consensus low) at 4.5x EV/S | **$105** |
| base | 0.45 | intl volume + US ARPU offset flat US DAU; FY27 rev $4.41B at 6.5x EV/S | **$165** |
| bull | 0.20 | DAU restabilises, licensing scales, guide beats again; FY27 rev $4.87B at 9.0x | **$240** |
**E[FV] = $159.0 vs $155.20 = +2.4pp.** That is FAIR, not edge.
Sensitivity that matters: one quarter of *sequentially flat-or-up US DAU* moves bear to 0.20 and
E[FV] to ~$172 (+11%). The entire edge is contingent on a datum that reports 2026-10-29.

## 8. FOUR-IDEA FRAME
1. **Consensus idea:** best-in-class ad asset, 61% growth, 29% GAAP margins, cheap at 6x forward sales.
2. **Bear idea:** Reddit is a Google traffic derivative; answer-engines break the funnel; US
   monetisable users have already peaked and international is a 5x-lower-ARPU substitute.
3. **Our variant:** the estimate revisions are *lagging* the engagement input, so the bull and bear
   are both currently true; the market repriced the leading indicator in one session and is now
   roughly fairly priced, not mispriced.
4. **The idea that kills ours:** if logged-in (app-native) DAU is growing while only logged-out
   search-referred DAU falls, the ARPU-weighted user base is *improving* and the -21% was a
   headline-metric artifact. We could not separate logged-in from logged-out from public sources
   this pass — **top UNVERIFIABLE**.

## 9. VERIFICATION NOTES / GAPS
- CONFIRMED: Q2 revenue/op income/net income (two independent sources), the -21% tape, the +10.3%
  rebound tape, ad-vs-other revenue split, share count and net cash from the 06-30 balance sheet.
- **UNVERIFIABLE (gaps, not clean):** (a) the actual Q2 DAUq figure and the US/intl split — RSS
  headlines confirm direction but not magnitude; the 10-Q/shareholder letter was not pulled;
  (b) logged-in vs logged-out decomposition; (c) the Q3 guidance range; (d) data-licensing contract
  renewal dates (the OpenAI/Google deals are the ~5% leg and their terms are undisclosed).

## 10. KILLS (dated)
- **K1 (2026-10-29):** Q3 US DAUq declines sequentially for a *second* quarter -> thesis dead, exit.
- **K2 (2026-10-29):** FY27 consensus EPS revised DOWN >3% from today's 6.915 -> the de-rate becomes
  a derailment, exit.
- **K3 (any date):** ad revenue growth decelerates below +35% yoy -> ARPU is no longer covering for
  users, cut by half.
- **K4 (price):** a close below $119.27 (the 52w low) invalidates the "informed-discount-is-enough"
  read; re-court from scratch.

## 11. CATALYST MAP (probability x timing x magnitude)
| catalyst | date | our p | magnitude |
|---|---|---|---|
| Q3'26 print, US DAUq flat-or-up | 2026-10-29 | 0.45 | +15 to +25% |
| Q3'26 print, second sequential US DAU decline | 2026-10-29 | 0.40 | -20 to -30% |
| new/renewed AI data-licensing deal disclosed | H2'26 | 0.30 | +5 to +10% |
| Google core/AI-Overview update visibly cuts referrals (third-party trackers) | any | 0.35 | -10 to -15% |
Leading indicators to watch ahead of the print: third-party Reddit search-visibility trackers,
app-store rank, and the pace of the buyback (a large Q3 repurchase = management's own confidence).

## 12. RULING
**REJECT 4/10.** The gate fired falsely (estimates rising, not falling) and the de-rate is genuine on
the estimate axis — but the modelled edge is +2.4pp, the discount is *informed* rather than opaque,
and the decisive datum has exactly one observation. This is a legitimate watch, not a buy at $155.
If it comes back to the post-print low it becomes a starter.
**Entry band $128-140** (the 07-31 post-crash zone / 13w low $135.28), **0.6% of the $3.3M book**
split 2 tranches (0.3% at 140, 0.3% at 128), hard stop on K4.
**Freezable call: RDDT|2026-10-29 — Q3'26 US daily active uniques >= Q2'26 US DAUq (sequential
stabilisation). our_p = 0.45.**
