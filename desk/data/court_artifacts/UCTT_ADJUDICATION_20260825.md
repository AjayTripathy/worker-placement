# ADJUDICATION — UCTT (Ultra Clean Holdings) — 2026-08-25

**VERDICT: MINIMUM STARTER 0.25% (blue's net position sustained), entry laddered below fair value with hard cancel triggers. Red's REJECT does not survive audit.**

Benches: RED 202608241735 (REJECT, 7/10) · BLUE 202608241850 (partial overturn → min starter, 6/10).
Tier-structure re-verification performed at this layer against the Q2 10-Q (accession 0001628280-26-052540, curl-fetched direct from sec.gov this session) and live IBKR tape.

## Primary re-verification (§TIER-STRUCTURE — no rubber-stamp)

| Load-bearing number | Bench claim | Primary says | Ruling |
|---|---|---|---|
| Convert conversion price | $84.75 (both) | **$84.75** ("initial conversion price of approximately $84.75," 42.5% premium to $59.47 on 2/26/26) | VERIFIED |
| Capped call cap | $104.07 | initial strike $84.75, "initial cap price of $104.…" | VERIFIED (strike/cap structure as described) |
| Red's "ATM at ~$92 **below** the $84.75 conversion price" | red's strongest-kill premise | $92 > $84.75 — **inverted comparison, red's kill #3 arithmetic is self-contradictory** | BLUE'S OVERTURN CONFIRMED |
| Cash | $255.9M | **$255.9M** at 6/26/26 (vs $311.8M at 12/26/25) | VERIFIED |
| Undrawn committed | $241.8M | **$230.9M US (net of LCs and $15.0M drawn) + $5.9M Czechia + $5.0M Israel** | VERIFIED (US revolver has $15M DRAWN — a nuance both benches under-reported; liquidity ≈ $497.7M incl. cash) |
| Share count (dilution-gate baseline) | blue 45.1M | **45,277,029 as of 7/29/26** (10-Q cover) | CORRECTED — gate baseline is 45.277M |
| Tape | red $73.25 intraday; blue "8/24 close $71.33" | **IBKR close 8/24: $72.78** | **BOTH BENCH TAPES WRONG** — blue's $71.33 "close" does not match the broker close; multiples herein re-anchored to $72.78 |
| Quarter-end stock price | — | $118.82 on 6/26/26 > 130% of conversion price → **the convert is currently holder-convertible** | NEW FACT at this layer (supply-relevant, see pre-mortem) |

## Rulings on the contested findings

1. **Red #8 (designated FATAL, "we agree with the street") — OVERTURNED.** Divergence-not-coverage: a 5-analyst Strong Buy count is coverage, not correctness. Red's own numbers contain the divergence it denied: street forward PE implies FY27 EPS ≈ $5.13 vs Q3-guide-annualized $3.72 — a 38% gap with no named mechanism. Red's case has **zero surviving FATALs**.
2. **Red #3 (revealed preference, FATAL-adjacent) — REDUCED to SIZING.** The $92-vs-$84.75 comparison is inverted (verified above); ATM capacity is authorization, not issuance (share count still ~45.3M ≈ undrawn); 424B5 "general corporate purposes" is mandatory boilerplate. What survives: $1.0B of paper authorized in two quarters is real overhang. KILL-CLASS re-tagged CONSENSUS (the 8/14 −8.6% priced exactly this).
3. **Red #1/#2 (net debt $359.1M not $520M; distress leg dead on ~$498M liquidity) — SUSTAINED, credited.** Red reporting against itself is the behavior the court wants. The brief's "growth vs distress" binary resolves growth-side.
4. **Red #4 (GM +27bp only; leverage is SG&A) — SUSTAINED as SIZING.** 17.4% incremental GM on +$111.2M is real but shallow; a 10% revenue slip erases EBIT.
5. **Red #5 (wrong customer anchored; LRCX 39.5%) — fact SUSTAINED, direction OVERTURNED.** LRCX supplying the incremental dollar at ~30% QoQ volume growth is a *stronger* demand anchor. 61.3% two-customer concentration is a SIZING term.
6. **Red #9 (gate unexecutable before 11/03) — SUSTAINED, with blue's fix adopted:** monthly share-count is the intervening observable.
7. **Blue's prize table — ACCEPTED with re-anchored tape.** At $72.78: cap ≈ $3.296B, EV ≈ $3.655B (net debt $359.1M). $4.0B run-rate at 7% op margin → ~13.1x EV/EBIT ≈ today's price; at 9% (company's own 2021-22 cycle history, UNVERIFIED at bench, carried as PLAUSIBLE) → ~+30%; +50% clears at ~10.4% margin. The tape prices trough margins on peak revenue — real but margin-dependent asymmetry. Fair ≈ **$71** at the 7% line.

## §CLEAN-COURT application
No surviving finding is a NAMED kill — every survivor is SIZING (concentration, GM shallowness, ATM overhang) or TIMING (gate observable). FLAT would require a named kill; none exists. Kill distribution after audit: **2 NOVEL sizing / 1 CONSENSUS sizing / 0 FATAL.** → **Minimum starter 0.25%** is the doctrine default, sized-not-blocked by the sizing terms.

## PROPOSED ORDER — PROPOSED-NOT-STAGED
- **BUY 37 UCTT LMT $69.50 GTC** (≈$2,571 ≈ 0.25% of $1.04M book), ladder strictly below fair (~$71) and below tape ($72.78) — value-ladder flow gate honored: we sit below predicted ATM supply, never bid into it.
- **Cancel-by 2026-10-30** (before the ~11/03 print; no GTC rides an undated/dated binary).
- **Cancel-early triggers:** (i) evidence of ATM drawdown >2% from the 45,277,029 baseline (monthly share-count / prospectus supplement); (ii) LRCX Sept-quarter guide materially down (the real anchor is LRCX, not AMAT).
- **Position kill (if filled), NAMED:** Q3 print 11/03 shows OCF still negative with inventory/revenue >0.90x → exit. KILL-CLASS: NOVEL.
- Tax note: any exit inside 12m is ST; entry now targets the FY27 LT clock only if the margin thesis proves out — a starter, not a campaign.

**PRINT PROXIMITY: ~2026-11-03 (yfinance-derived, UNCONFIRMED) — ~49 sessions. No pre-print posture required. 8/28 has no UCTT event.**

## What could go wrong (v1.7)
1. **WFE cycle rolls over mid-quarter.** LRCX is 39.5% of revenue; its Sept-quarter guide is the tripwire (dated, watched).
2. **ATM drawn hard into any strength**, capping every re-rating leg. Tripwire: monthly share count vs 45,277,029.
3. **Tripwire-less: a BIS/export-control action on China-shipping end customers cascades through LRCX/AMAT to their 61%-concentrated subsystem supplier.** No feed we run watches Entity-List second-order exposure; both benches flagged the connector gap (export_control_check UNCHECKABLE). Unknown-unknown class: **REGULATORY-CASCADE**.
- **Reflexive/structural leg:** "buy the authorized-dilution overreaction" is the same trade every pod screener runs on ATM filings; if the discount persists anyway, the seller knows something about the $238.9M inventory build (customer-funded or not?) that the 10-Q does not disclose. Our fill would be their exit.
- **If this position loses money, the most likely reason will be** that the semicap cycle turned while we were arguing about the financing, and the 16% gross margin turned a 10% revenue slip into a full EBIT wipeout exactly as red computed.

*Adjudicated on Fable at the session layer; every decisive number above re-pulled from the 10-Q or live IBKR this session. Blue's kg_candidate (authorized_vs_issued_dilution_overreaction) and red's (equity_issued_below_own_capped_call_strike — note: premise partially refuted, the fires_on needs the price comparison fixed) forwarded to KG triage as-is in the bench artifacts.*
