# PITCH — AVPT — PROPOSED VERDICT

**PROPOSED — PENDING ADJUDICATION: REJECT. No position, no size, no price gate armed today.** A healthy 22%-growth software company that is fairly priced, whose two admission tickets into our screen were both artifacts — and which, in the quarter right before this court, beat its revenue guide by $3.2M while cutting its full-year operating-profit guide by 6%.

---

## What we believe

AvePoint sells data management, backup and governance tools that sit on top of Microsoft 365. It is a real business: about $465M of annualized recurring revenue, growing roughly 22% on revenue, $417.3M of cash, no drawn debt, positive operating cash flow, no customer above 10% of billings, 3,443 employees.

We do not believe it is cheap, and we do not believe we found a dislocation.

Our screen (`quality_drawdown`) admitted AVPT on two numbers: a 16.2% return on equity and a 35% three-year drawdown. Both fail on inspection.

- The 16.2% return on equity is not operating profit. It is a tax event. The June-quarter 10-Q says in plain words: *"income tax benefit of $15.6 million, primarily attributable to a $19.9 million release of the valuation allowance."* The company stopped assuming it would never use its old tax losses, and booked the whole benefit at once. Effective tax rate for the quarter: **−129.5%**. Strip it out and return on equity is roughly 11–12%.
- The 35% drawdown is measured from a peak of $19.99 (May 2025) that was itself about 10–11x sales. It has already round-tripped: the stock is **+49.3% off its 52-week low of $8.835** and only **−21.3% off its 52-week high of $16.77**. What the screen caught was a bubble multiple normalizing, and it caught it halfway back up.

At $13.19 the market cap is ~$2.79B; less $417.3M cash and no debt, enterprise value is ~$2.37B, or **~5.1x sales** and **~59–69x taxed GAAP operating earnings**. There is no discount in that price to be the source of a return.

The sharper problem is operational, not just valuation. Between the March-quarter release and the June-quarter release the company **cut** its full-year non-GAAP operating income guidance from $91.5–94.5M to $86.4–88.4M — the midpoint fell from $93.0M to $87.4M, down 6.0% — and nudged the full-year revenue midpoint down $1.9M, while *beating* the June-quarter revenue guide. The mechanism shows up in the GAAP numbers: operating income went from $12.7M on $117.2M of revenue (10.8%) to $10.2M on $124.5M (8.2%). Revenue rose $7.3M and operating profit fell $2.5M. At 5.1x sales the entire bull case is operating leverage, and in the quarter you are being asked to pay for, leverage ran backwards.

## What the market believes

That this is a steady, cash-generative, mid-20s-growth software compounder attached to the Microsoft ecosystem, worth a mid-single-digit sales multiple. Fourteen analysts cover it with an average target near $16.78; institutions hold roughly 60%; average daily dollar volume is about $27.8M. (Those four figures are secondary-source and we did not verify them — see "What remains unverified." They point the same direction either way: this is a well-covered, well-owned name, not something nobody is looking at.)

The market's view is not obviously wrong. Revenue growth of 22%, net revenue retention of 111%, gross retention that has been stable at 88–89% for six straight quarters, and a fortress balance sheet is a reasonable thing to pay 5x sales for. Our disagreement is that we can't find anything we know that the fourteen analysts don't.

## Why we might have edge

Honestly: thin, and mostly in what we *avoided* rather than what we found.

1. **We found the guidance cut that nobody framed as a cut.** Both of our own benches, and (per the second bench's read of the releases) the headline framing generally, described the June quarter as a beat-and-raise. The full-year revenue range narrowed, so the "raise" read is understandable — but the midpoint went *down*, and the profit guide went down 6%. That is a real, primary-sourced, two-venue finding. It has been written up as a reusable detector (`beat_and_cut_guidance_divergence`).
2. **We found the tax artifact before we bought it.** A valuation-allowance release inflates reported net income and every return-on-equity screen for exactly four quarters. Our screen admitted the name *at* its release quarter. Also written up as a detector (`valuation_allowance_release_screen_poisoning`).
3. **We found that the screen's return-on-equity input is broken in both directions.** The equity base of $436.9M is 95.5% cash. Goodwill and intangibles are only $47.9M; deferred revenue of $213.1M funds the working capital. Invested capital excluding cash is roughly $20M, so the operating business's return on capital is effectively unbounded. The 16.2% overstates the quality and the "11.8% ex-release" understates it. Neither number should ever have been the ranking variable.

That third point is the durable output of this court: `quality_drawdown` should rank on operating return on capital excluding net cash, not on reported return on equity.

## Why it might be priced in

Almost everything else. Fourteen analysts, 60% institutional ownership, a liquid tape, a quarterly guidance cadence read closely by everyone. The valuation objection — "5.1x sales is too much" — is available to any reader of a screen. The retention numbers are in the press release. The tax benefit is disclosed verbatim in the 10-Q.

The one thing plausibly not priced is the *composition* of the operating-margin decline (N1/N2 above), and even there we have to concede we don't know whether it is deliberate investment, currency, or deterioration — see below. If it is a named, dated investment program, the market will treat it as good news and we will have been early to nothing.

The case *for* the company, which we are not dismissing: near-term committed backlog is growing faster than the guide (current remaining performance obligations $341.2M vs $276.2M, **+23.5%**, against a 22% full-year revenue guide); first-half operating cash flow nearly doubled to $40.2M from $20.8M; the company bought back $110.3M of stock in the first half at an average of about $10.82, which is 18% below today's price, while stock compensation *fell* 19% ($20.8M → $16.8M half-on-half). That is competent capital allocation, not dilution mop-up. This is a good company. It is a bad setup.

## What we checked ourselves

Including — deliberately — every place our own benches got it wrong. Four of the seven rows below are our own errors.

| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| Screen input: return on equity 16.2% reflects operations | Read the Q2 2026 10-Q tax note directly (primary) | *"income tax benefit of $15.6 million, primarily attributable to a $19.9 million release of the valuation allowance"*; effective tax rate −129.5% for the quarter, −50.0% for the half. Underlying ROE ~11–12% | **Yes — screen input refuted.** Both benches agree |
| Setup: a 35% three-year drawdown is an unspent dislocation | Evidence-pack tape, plus recomputing the multiple at the old peak | +49.3% off the low, −21.3% off the high; peak was ~10–11x sales vs 5.1x today. Half-harvested normalization, not compression | **Yes — setup refuted.** Both benches agree |
| Price: "fallen compounder at a discount" | 10-Q plus the earnings exhibit; taxed GAAP operating earnings at the newly-realizable ~25% rate | ~59–69x taxed GAAP operating earnings, ~35x free cash flow before stock comp, 5.1x sales. Second bench specifically hunted for a double-count in the tax leg (the released tax shield is worth ~$20M, about 0.7% of enterprise value — immaterial) | **Yes — no discount exists** |
| Full-year guidance was raised | Compared the March-quarter and June-quarter guidance tables side by side | It was **cut**: non-GAAP operating income midpoint $93.0M → $87.4M (−6.0%); revenue midpoint −$1.9M. GAAP operating income fell $12.7M → $10.2M on $7.3M more revenue | **OUR ERROR — both benches called this a raise.** Neither the first nor the second bench caught it until the second bench re-read the tables. This is now the primary kill |
| "Q4 has to accelerate ~5 points to hit the guide" (our first bench's timing kill) | Recomputed the residual quarter using the company's actual beat history instead of its guided midpoint | The company beat the June guide by $3.2M (above the *high* end by $2.2M) and beat in March too. Applying that pattern, implied Q4 is ~+19.9% — a smooth deceleration of 25.9 → 22.0 → ~21 → ~20 with **no acceleration required** | **OUR ERROR — kill withdrawn**, downgraded to context. Written up as `guided_vs_residual_acceleration_artifact` |
| "89% gross retention is a structural leak nobody priced" (our first bench, sized as a risk) | Pulled six quarters of the company's own results releases | Gross retention: 88, 88, 88, 88, 89, **89** — flat to improving, and already inside the 111% net retention number. Not a leak, not new ([Q2 2025 release](https://www.avepoint.com/news/avepoint-announces-second-quarter-2025-financial-results-250807), [Q4 2025 release](https://www.avepoint.com/news/avepoint-announces-fourth-quarter-and-full-year-2025-financial-results-260226)) | **OUR ERROR — finding withdrawn** |
| Backlog is growing slower than recurring revenue (a warning sign) | Both 10-Qs, then adjusting for currency | Total performance obligations +21.5% vs recurring revenue +27% reported — but recurring revenue is only **+24% adjusted for currency**, and near-term backlog is +23.5%. The gap closes | **OUR ERROR — downgraded from "partial fire" to "not fired"** |
| The two loudest suspicions going in: a $50M venture-fund commitment, and insider selling | 10-Q text; Form 144 filings | Fund: *"In September 2025, the Company decided to discontinue its participation… no portion of the Company's $50.0 million commitment has been called"* — only a $1.6M fee accrual. Insiders: one officer, trust sales of ~50k shares (~$656K) across four filings in July. A trickle | **Both closed clean, against our own case.** Recorded as a positive finding, not an absence |
| Our pre-court brief's inputs: net cash $390.6M; free cash flow −24%; stock comp 7.6% of revenue and rising | 10-Q balance sheet and cash flow statement | Cash is **$417.3M** with nothing drawn (brief was $26.7M low, most likely because it netted lease liabilities — plausible, not confirmed). The −24% free cash flow quarter is a collections-timing artifact: half-year operating cash flow was **+93%**. Stock comp is ~6.9% of revenue and **falling** | **Brief refuted on all three.** A gate we had drafted (Q3 free cash flow > $20M) was built on one lumpy quarter and is dropped |
| Company-specific detector sweep (11 detectors) | Ran each against primary filings | All not-fired or not-applicable, and three of our knowledge-graph tags on this company are **wrong**: `egc_status` (the 10-K cover box is unchecked — the company is not an emerging growth company), `upc_tra_structure` (single class of common, no partnership structure, no tax receivable agreement), `real_estate_development` (leased offices only). Clinical-trial detectors are mis-tagged onto a software company | **Three stale tags to retire.** Filed as desk maintenance |

Two further honest notes. First, **our tape facts rest entirely on one source.** Both benches were permission-denied on the broker connection, so neither could pull an independent quote, multi-year bars, or decompose the $8.835 low into market-driven versus company-specific. That is an infrastructure failure, not a research result, and it recurred across three consecutive benches this session. Second, direct SEC fetches returned 403 for both benches; all primary reads were made through a proxy. The documents are the real documents, but the access path is fragile and should be fixed.

## PROPOSED ENTRY BANDS

**No entry. No position today. No standing price gate armed.**

The reason for "no gate," rather than "gate lower," matters: our own response rules say a *valuation* objection converts to a price gate and nothing else, but an *operations* objection converts to a data question that a price cannot answer. The guidance cut moves this from valuation to operations. Buying it 20% lower without knowing why the profit guide fell 6% would be buying the same unanswered question at a discount.

So the bands below are **reopen conditions**, not orders.

**Reopen gate A — the print, 2026-11-05 (date unconfirmed; see below).** Re-court, do not auto-buy, if the third-quarter release shows *both*:
- the full-year non-GAAP operating income midpoint restored to **≥$93.0M**, *or* an explicit, dated, named investment program that accounts for the $5.6M cut; **and**
- recurring software revenue growing **≥30% year over year** (it went +35.4% in Q1 to +27.4% in Q2 — that deceleration, not the total revenue line, is the real tell).

**Reopen gate B — price, conditional.** **≤$10.50** (≈3.9–4.0x sales at today's share count and cash), **armed only after gate A's first condition resolves favorably.** Unconditional arming is explicitly not proposed.

**Reopen gate C — price, clean.** **≤$9.50** (≈3.4x sales, ≈40x taxed operating earnings). At that price the 22% growth / 111% net retention / $417M net cash profile is a genuine discount rather than a normalization, and it stands on valuation alone without needing gate A. This is the only band either bench was willing to call a clean re-entry.

**Reopen gate D — quality.** Gross retention printing **≥93%** in any subsequent results release. That would convert the model from steady to compounding and change the terminal value, independent of price.

**Sizing:** zero now. Neither bench authorized a size, and none is proposed here; any reopen returns to court for sizing before an order is staged.

**Trims/exits:** not applicable — we hold nothing and have no working orders.

**Catalyst dates:**
- **2026-11-05** — expected third-quarter results. **UNCONFIRMED.** This date is derived from a data vendor; no company announcement names it. It is consistent with the company's own cadence (Q3 2025 reported 2025-11-06, Q2 2026 reported 2026-08-06), so it is a reasonable placeholder, but it should not be treated as fixed until a company press release names it. Roughly 55 trading days out from this court — nowhere near close enough for the print to force a decision today.
- **2026-11-03** — the revolving credit facility matures (per the 10-Q; nothing is drawn on it). If it is replaced with a materially larger facility earmarked for acquisitions, the capital-allocation story changes and the name should be re-courted regardless of price.

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- price alert: fires below 9.5 (deck-provisional: Clean valuation reopen — ~3.4x EV/sales, ~40x taxed GAAP operating earnings; the only price either ben)
- filing watch: 8-K until 2027-02-13 (deck-provisional: Q3 results: compare the guidance table to the prior quarter's — fire if FY non-GAAP operating income m)
- dated pack AVPT|2026-11-05: AVPT: Expected Q3 2026 results — vendor-derived date, consistent with issuer cadence but not named in any company release; the decisive re-c
- dated pack AVPT|2026-11-03: AVPT: Revolving credit facility matures (nothing drawn); a materially larger replacement facility would force a re-court. (date confirmed=Tr


## What remains unverified

Stated plainly, because several of these could soften the verdict:

1. **Why the full-year profit guide was cut.** This is the load-bearing finding and its composition is unread. The March-quarter release flagged explicit currency headwinds; if the $5.6M cut is largely currency, or a named investment program, the operational read weakens materially and this becomes a price-only question again. **This is the single most important open item.**
2. **The print date.** 2026-11-05 is vendor-derived. No company announcement confirms it.
3. **What caused the $8.835 low.** Market-driven or company-specific? Nobody could pull the bars. This is why a bare price gate is unsafe.
4. **The $26.7M cash discrepancy** between our pre-court brief ($390.6M) and the filing ($417.3M). Lease liabilities are the likely explanation but that is inference, not confirmation. Immaterial to the verdict (about 1% of enterprise value), but it means the brief's balance-sheet line was not reproducible.
5. **Whether falling stock compensation is real leverage or accrual relief.** The $20.8M → $16.8M half-on-half decline is confirmed from the cash flow statement, but a performance-award mark-down reverses if targets are later hit. Needs the FY27 grant plan to settle.
6. **Public-sector exposure is unmeasurable with our tools.** Government revenue is cloud seats, not a budget line item, so our defense-budget detectors have nothing to trace. Recorded as uncheckable, not as clean.
7. **Crowding statistics** (14 analysts, $16.78 average target, 59.6% institutional, $27.8M average daily volume) are secondary-source and unverified. They cut in favor of the reject either way.
8. **This is a rejection of the setup, not a short case and not a judgment on the company.** Confidence: the first bench put its kill case at 7/10; the second put the re-founded net position at 8/10, held below 9 precisely because of open item #1.

Primary sources: [Q2 2026 10-Q, filed 2026-08-06](https://www.sec.gov/Archives/edgar/data/1777921/000143774926026267/avpt20260630_10q.htm) · [Q2 2026 results exhibit 99.1](https://www.sec.gov/Archives/edgar/data/1777921/000117184326005319/exh_991.htm)

```json
{"price_gates": [{"level": 10.5, "direction": "below", "basis": "Conditional reopen only — arm ONLY after the Q3 print restores the FY non-GAAP operating income midpoint to >=$93M or names a dated investment program; ~4.0x EV/sales. Currently DISARMED."}, {"level": 9.5, "direction": "below", "basis": "Clean valuation reopen — ~3.4x EV/sales, ~40x taxed GAAP operating earnings; the only price either bench would re-enter on price alone."}], "event_gates": [{"forms": ["8-K"], "why": "Q3 results: compare the guidance table to the prior quarter's — fire if FY non-GAAP operating income midpoint falls again >3% while revenue beats, or if SaaS YoY growth prints <25% or >=30%."}, {"forms": ["8-K"], "why": "Dollar-based gross retention printing >=93% (quality reopen) or <=86% (thesis inverts)."}, {"forms": ["8-K"], "why": "Replacement of the revolving credit facility maturing 2026-11-03 with a materially larger, acquisition-earmarked facility changes the capital-allocation frame."}, {"forms": ["4", "144"], "why": "Insider selling is currently a ~$656K trickle and closed clean; fire on any step change in cadence or size."}, {"forms": ["10-Q", "10-K"], "why": "Confirm whether the 19% decline in stock compensation persists or reverses, and track the deferred-tax valuation-allowance release rolling out of trailing returns (~Q2 2027)."}], "catalyst_dates": [{"date": "2026-11-05", "what": "Expected Q3 2026 results — vendor-derived date, consistent with issuer cadence but not named in any company release; the decisive re-court trigger.", "confirmed": false}, {"date": "2026-11-03", "what": "Revolving credit facility matures (nothing drawn); a materially larger replacement facility would force a re-court.", "confirmed": true}], "immediate_entry": null}
```