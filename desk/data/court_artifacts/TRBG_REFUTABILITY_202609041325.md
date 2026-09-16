## TRBG — REFUTABILITY TRIAGE (blob_sweep 2026-09-04)

Context: TRBG is not a drawdown. Turbogen direct-listed existing TASE ordinary shares on Nasdaq **five sessions ago (2026-08-31)**; the "52-week high" of $33.99 is the day-1 unseasoned-float print, and the fungible home line (TASE:TURB) is down only 16.9% from *its* 52-week high — so the cohort's -53pp excess drawdown is a measurement artifact, and the residual is a *premium*, not a discount.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| TRBG | **UNTRIAGEABLE — ARTIFACT (new-listing premium decay, not narrative damage)** | Nasdaq price vs the **fungible TASE:TURB home line** in USD (same ordinary shares, no ADR ratio) — the same-event EXTERNAL anchor | TASE ILA 1,999 (=ILS 19.99) on 2026-09-04, 52w range ILA 1,238–2,404 → home-line dd52 **-16.9%**, +61% off its low; ÷ USDILS 3.0117 = **$6.64** vs Nasdaq $7.86 → Nasdaq still **+18.4% RICH** to parity ([TASE quote](https://www.google.com/finance/quote/TURB:TLV), aggregator-sourced — re-pull from maya.tase.co.il before any action; [6-K primary, 2026-08-31](https://www.sec.gov/Archives/edgar/data/2088375/000121390026095409/): *"ordinary shares will begin trading on Nasdaq on August 31, 2026… will maintain the listing… on the Tel Aviv Stock Exchange under the symbol TURB"*) | **NONE within 5 trading days** (see PRINT PROXIMITY) | Screen dd52 measures 5 days of US float discovery against 52 weeks of Utilities history. Three separate incoherences in the pack itself, below. |

**Why the three-way taxonomy does not apply:** DAMAGE-ABSENT / ARRIVING / STRUCTURAL all presuppose a real discount whose cause is a cohort narrative. There is no discount on the instrument that actually clears — TASE prices Turbogen at ~$169M (25.46M sh × ILS 19.99), and the Nasdaq line is above that. Nothing about grid/power-gen sentiment is being priced here; what is being priced is a thin US float reverting to its home quote alongside a resale registration going effective.

**Mechanism (dated, primary-anchored):**
- 2026-08-28 `EFFECT` + `CERT` — F-1 declared effective (F-1 2026-02-09, four amendments through 2026-08-21); **no 424B on file**, consistent with a *resale* registration, not a priced primary offering.
- 2026-08-31 — **13 Form 3s** filed the same day: Section 16 insiders newly reportable, i.e. the registered holder base is now visible and sellable into a five-day-old US line.
- Tape: day-1 high $33.99 (= **+412% over TASE parity**) → 2026-09-03 close $11.84 (-32.0%) → 2026-09-04 $7.86 (-33.6%). That is registered supply meeting a ~412% premium, not a fundamental repricing.

**Three self-refuting numbers in the evidence pack — pipeline bugs, not findings:**
1. `lo52` 10.79 > `px` 7.86. A 52-week low cannot sit above spot on one series; the ibkr_gw hi/lo window and the last price are not the same series.
2. Pack `dd52` -0.769 vs blob `dd52` -0.652 — two different denominators for one name in one pack.
3. `XBRL QUARTERLY` is **empty**, and EDGAR shows no 20-F and no financials-bearing 6-K. There is no US-filed SBC / share-count / OCF to do the math the template asks for; the only audited financials sit inside F-1/A No. 4 (0001213900-26-092716), unread here. The blob's `[LEVERAGE UNCHECKED]` flag is therefore still unchecked, and that is the sole real work item if anyone wants to go further.

**COURT-WORTHY (damage-absent, ranked):** *none.* No member survives — TRBG's discount does not exist on the fungible instrument, so there is no dispersion for a court to adjudicate.

**COURT-WORTHINESS TRBG: 2/10** — one external-anchor line (TASE parity) already fixes size at zero, so a full red/blue court cannot move the sizing decision.

**PRINT PROXIMITY: NONE — verified as follows.** EDGAR through 2026-08-31 carries no financial-statement 6-K and no scheduled-report announcement; FY-end is 12-31 so the first US annual is a 20-F in 2027; the Israeli Q3 report deadline is ~2026-11-30; the pack's `next print` is null and self-labelled yfinance-derived/UNCONFIRMED, and no company PR names a date. The nearest *dated* event is not a report but the next home-line session, **Sun 2026-09-06** (TASE trades Sun–Thu), which prints the parity mark again.

**PRE-PRINT POSITION: FLAT.** Buying TRBG at $7.86 pays an 18% premium to a directly fungible share that clears at $6.64 in Tel Aviv, into a float whose resale registration went effective six days ago — that is bidding into the exact supply flow that is setting the price (value-ladder flow gate). The mirror-image short is also declined, not on merit but on doctrine: a five-day-old microcap down 66% in two sessions from a +412% spike fails the meme-exclusion gate, and borrow on an unseasoned dual-listed float will not be locatable or priceable.

**Routing:** score < 6 → no auto-escalation. Recommend instead a **detector fix**: `blob_sweep` should suppress any `dd52` whose 52-week window contains fewer than N sessions of venue history (TRBG had 5), and should reject rows where `lo52 > px`. This is the same failure family as the PTS after-hours mark and the unadjusted reverse split — a vendor series stitched across a unit or venue boundary, read as a price move.