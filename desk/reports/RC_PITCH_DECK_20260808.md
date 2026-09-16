The file reads were declined, but the full court record is in the request, so I'm writing the deck directly from it. One housekeeping note before the deck: the standing close-out step (ledger upsert, entry plan, scanner re-run, dashboard verify) could not run this session — file and IBKR tool permissions were denied — so this deck needs to be flowed into the dashboard when a permitted session picks it up. The JSON fence is last, per the auto-arm convention.

---

# PITCH — RC — PROPOSED VERDICT
**REJECT — no position at $1.71; the original mispricing claim was our own arithmetic error, and the corrected math says the market is pricing exactly a zero-recovery outcome on the bad-loan book, which is defensible. PROPOSED — PENDING ADJUDICATION.**

## What we believe
Ready Capital (RC), a commercial real-estate lender, trades at $1.71 against a stated book value of $6.83 per share — a 75% discount. Our original thesis argued the market was destroying $200–300M more value than the identified bad loans could justify, making the stock an over-punished buy.

That thesis is dead, killed by our own review. The company's Q2 investor supplement (filed as an 8-K exhibit) shows the non-performing loan segment is $994M of unpaid principal carried at $846M — a figure **already net** of $146M in loss reserves. Our reconstruction subtracted the $277M total reserve from that already-net number, which double-counted and manufactured $569M of phantom "unreserved" cushion. Done correctly: a total, zero-recovery loss on the bad-loan book costs $846M, which is $5.12 per share on 165.2M shares — **exactly** the gap between book value ($6.83) and the stock price ($1.71). There is no excess destruction to buy.

What we now believe: RC at $1.71 is a fairly priced bet on continued deterioration, with three structural problems layered on top. First, bad loans are still forming — $133M of new delinquencies last quarter, roughly 8.6% of the performing book migrating per quarter, alongside roughly $40M per quarter of operating losses before realized credit losses. Second, $119.7M of preferred stock (with ~$8M/yr of dividends) sits ahead of common shareholders; in a full-wipeout scenario the common's residual is about $0.99/share — *below* today's price. Third, RC is externally managed by Waterfall Asset Management, whose fees accrue on equity and whose contract carries a termination fee the company's own 10-K says may deter ending the relationship ([10-K](https://www.sec.gov/Archives/edgar/data/1527590/000162828026039527/readycapital-10xkfiledvers.pdf)). Every path that would deliver residual book value to shareholders — liquidation, sale, wind-down — requires the fee-earning manager to fire itself. Management is instead deepening the Waterfall relationship, not exploring alternatives.

## What the market believes
The market is pricing a complete write-off of the non-performing loan book — no more, no less — and treating the discount as compensation for ongoing deterioration rather than a temporary panic. Both of our review benches concluded this is a coherent, defensible view: at the current pace of new delinquencies and operating losses, the remaining book value above the wipeout mark would be consumed within roughly four quarters anyway. Notably, the stock jumped ~10% today ($1.55 → $1.71) on roughly four times normal volume, so some buyers are already repricing the post-earnings picture — the "nobody's looking at this" framing was wrong too.

## Why we might have edge
Honestly: we don't, and this section exists to record what edge *would* look like rather than to claim one.

- If new delinquency formation slows sharply (under ~$50M/quarter for two straight quarters) while operating earnings before realized losses turn non-negative, the "continuation" the market is pricing stops, and the wipeout mark becomes too harsh.
- If the external manager is terminated, internalized, or a strategic-alternatives process is announced, the realization blockage — the strongest single argument against owning this — is removed.
- If the stock fell **below ~$0.99** (the residual value after a full bad-loan wipeout and the preferred claim), the market would then be pricing *more* than total destruction, and the original dispersion logic would apply for real.

None of these is true today.

## Why it might be priced in
It isn't just priced in — the pricing is the finding. The discount equals the full-wipeout loss to the dollar, before counting continued bad-loan formation, operating burn, preferred seniority, or the manager problem. Arguably the market is *generous*: with 1.7× recourse leverage (3.0× total), the downside tail is levered, and refinancing of Q4 2026 maturities is still ahead. Resolution channels also arrive fast — monthly CLO trustee reports and the ~November 5 Q3 print — so there is no long information vacuum in which a mispricing could sit undetected.

## What we checked ourselves
| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| Share count / market cap | Q2 press-release balance sheet (SEC direct fetch blocked with 403; via StockTitan mirror) | 165,209,516 shares → ~$282.5M mkt cap. **Our evidence pack's figure (149.8M implied) and XBRL series (170.7M) were both stale — pack error, superseded** | Yes (secondary source) |
| "$200–300M excess destruction beyond identified losses" | Re-derived from the company's filed Q2 supplement ([8-K exhibit](https://www.sec.gov/Archives/edgar/data/0001527590/000162828026054466/readycapital-supplementa.htm)) | The $846M non-performing carry is already net of $146M reserves ($994M principal). **Our own thesis double-counted the reserve, inventing $569M of cushion. Corrected, the market discount = full wipeout exactly** | Refuted — our error |
| Red bench's counter-math ("flow closes the gap") | Blue bench cross-check | Directionally right, but red equated $133M of new delinquencies with $133M of losses — **not the same thing; a red-bench error**, though the kill survives without it | Partially |
| External manager blocks value realization | Company 10-K + [advisor page](https://readycapital.com/about/advisor/) + Q1-26 earnings call | Termination fee disincentive stated in the 10-K; management deepening Waterfall integration, no strategic-alternatives process | Yes |
| Preferred stock senior to common | Q1-26 [10-Q](https://www.sec.gov/Archives/edgar/data/0001527590/000162828026032982/rc-20260331.htm) | $119.7M liquidation preference (Series C $8.4M + Series E $111.4M), ~$0.72/share. **Original thesis never pulled the capital structure — a process failure our checklist exists to prevent** | Yes |
| Delinquency roll figures ($631M stock, $133M new) | Provenance trace | Originate in the company's own SEC-filed supplement, reproduced by a secondary site; direct SEC read blocked (403) | Yes (company-authored, read via secondary) |
| "Stock is flat, waiting costs nothing" | Yahoo daily bars | $1.53/$1.59/$1.54/$1.55 closes → $1.71 today, +10.3% on ~4× normal volume | Refuted — it's moving now |
| Book-value erosion is decelerating | No fitting tool | One data point; partly a timing artifact of discretionary loan sales | **No — unverified** |
| Short interest / crowding | IBKR tools | Permission denied this session | **No — unverified** |
| Original court-worthiness of 7/10 | Both benches | Re-graded to ~3–4/10 — the case never genuinely swung once the arithmetic was fixed | Overstated by us |

## PROPOSED ENTRY BANDS
**No entry at any price today.** Both benches vote REJECT; this is not a valuation gate but a thesis kill. Reopen bands, from the benches' own math:

- **Price reopen — below ~$0.99.** Book $6.83 − full bad-loan wipeout $5.12 − preferred claim $0.72 ≈ $0.99/share of residual value. Below that, the market prices more than total destruction and the case re-opens for court. This is a *re-examine* trigger, not an automatic buy — the ~$40M/quarter operating burn and levered tail still need to be re-weighed at that time.
- **Event reopen (any one):** (1) two consecutive quarters of new delinquency formation under $50M **and** distributable earnings before realized losses at or above zero — first readable at the Q3 print (~Nov 5, unconfirmed) and monthly via CLO trustee reports before that; (2) an announced manager internalization, termination, or strategic-alternatives process; (3) Q4 2026 debt maturities refinanced with no new common shares issued.
- **Sizing:** 0% now. If a reopened court clears it, the prior court's ceiling logic (levered tails, senior preferred) caps this as a small speculative position, not a core holding.
- **Catalyst dates:** ~2026-11-05 Q3 earnings (derived, not company-confirmed); Q4-2026 maturity wall (exact dates not yet pulled from the debt schedule); monthly CLO remittance reports in between.

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- price alert: fires below 0.99 (deck-provisional: book 6.83 minus full NPL wipeout 5.12 minus preferred 0.72 = residual ~0.99; below it the tape prices )
- filing watch: 8-K until 2027-02-04 (deck-provisional: manager internalization/termination, strategic alternatives, or Q4-26 refinancing terms — any one remo)
- dated pack RC|2026-11-05: RC: Q3 2026 earnings (derived date, not company-confirmed) (date confirmed=False)
- dated pack RC|2026-12-31: RC: Q4-2026 debt maturity wall — refinance without common issuance is a reopen trigger; exact dates unpulled (date confirmed=False)


## What remains unverified
- **Direct primary reads of the SEC documents** — data.sec.gov returned 403 throughout; every filing fact above was confirmed via mirrors of company-authored documents, not the originals.
- **Short interest, borrow, and crowding** — IBKR access was denied this session; we do not know who is on the other side of today's 4×-volume bounce.
- **Whether book-value erosion is genuinely slowing** — one data point, contaminated by discretionary loan-sale timing.
- **The Q3 earnings date** and the **exact Q4 maturity schedule** (amounts and dates by facility).
- **Loss content of the $133M new delinquencies** — formation is not the same as loss; severity on the new cohort is unknown.

```json
{"price_gates": [{"level": 0.99, "direction": "below", "basis": "book 6.83 minus full NPL wipeout 5.12 minus preferred 0.72 = residual ~0.99; below it the tape prices more than total destruction — re-court, not auto-buy"}], "event_gates": [{"forms": ["8-K"], "why": "manager internalization/termination, strategic alternatives, or Q4-26 refinancing terms — any one removes a kill leg"}, {"forms": ["10-Q", "8-K"], "why": "Q3 supplement: new delinquency formation under $50M and distributable EPS before realized losses >= 0 (first of two required quarters)"}], "catalyst_dates": [{"date": "2026-11-05", "what": "Q3 2026 earnings (derived date, not company-confirmed)", "confirmed": false}, {"date": "2026-12-31", "what": "Q4-2026 debt maturity wall — refinance without common issuance is a reopen trigger; exact dates unpulled", "confirmed": false}], "immediate_entry": null}
```