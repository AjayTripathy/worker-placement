# PITCH — DDOG — VERDICT
**ADJUDICATED 2026-08-07 — DECLINE: no long, no short, no premium selling; the name reopens only on the November print or at $155, and it has since traded *away* from us ($231.33 at adjudication → $245.30 today).**

---

## What we believe

Datadog is a genuinely good business that we are being asked to pay a very high price for, at a moment when it has just told us — in the fine print of its own quarterly filing — that its single biggest customer started buying less.

Three things we hold with reasonable confidence:

1. **The business underneath is accelerating, not decaying.** Revenue growth went from 28.1% → 35.6% year-over-year across the last five quarters. Strip out the "AI-native" group of customers entirely and the *rest* of the business still went from 18.1% to 27.1% growth. Contracted-but-not-yet-recognized revenue (the forward order book) grew 43.1% year over year, faster than revenue itself. This is not a company falling apart.
2. **The specific risk is real, unmeasured, and only five weeks old.** The 10-Q filed 2026-08-06 says the largest customer reduced its usage starting in Q3 2026 and that this "may cause a deceleration in revenue growth." Datadog has never disclosed how big that customer is as a share of revenue. We do not know its name. We could not close either gap.
3. **Price is the binding constraint, not the customer.** At $245.30 the enterprise is valued at roughly $84B, about 18.8× this year's guided revenue and roughly 219× free cash flow *after* charging for stock issued to employees. Even our optimistic scenario compounds at only ~9%/year from here. We would be paying full price for an outcome we can't yet verify.

**So: the reason we're out is valuation and unverifiability, not a belief that the business is broken.** That distinction determines how we grade this later.

## What the market believes

The market believes the reduction is temporary belt-tightening by one customer, not a permanent move to a competitor or in-house tooling.

We can put a number on that belief. Working backward from three scenarios out to 2028 and discounting at 10%:

| Scenario | 2028 revenue | Free-cash margin | Exit multiple | Implied price | Present value | vs. $231.33 (court date) |
|---|---|---|---|---|---|---|
| Good — customer optimizes then grows again; base holds 27% | $7.2B | 32% | 50× | $332 | $274 | +19% |
| Middle — customer usage halves; growth settles ~22% | $6.6B | 31% | 40× | $239 | $198 | −15% |
| Bad — the customer is genuinely leaving; growth falls to ~15% | $6.0B | 29% | 28× | $147 | $121 | −48% |

At the court-date price of $231.33 the market was already assigning about a **69% chance to the good case**. At today's $245.30 it is assigning more. To make money we would have to be *more confident than the market already is* — on five weeks of data, about a customer nobody has named, whose size nobody has disclosed.

The options market agrees it doesn't know: the November straddle was pricing a **27% move** in either direction over 105 days.

## Why we might have edge

- **We read the filing, not the press release.** The company's headline that day was upbeat ("customers are building and deploying with AI"). The bad sentence sat in the risk factors and in the management discussion. The stock fell 19.03% on 2026-08-06 (close $283.17 → $229.29) — the market repriced on the *document*, not the press release. Our habit of reading the primary filing is what put us in front of the real cause.
- **We tracked the same sentence across seven quarterly filings.** The AI-native customer group's contribution to growth went 5 → 6 → 10 → 8 → 7 → high-single → high-single percentage points. That means it **peaked a year ago**, while total growth was accelerating. Almost nobody does this comparison, and it flips the popular story ("all the growth is one AI customer") on its head.
- **We checked whether the insider selling meant anything.** It didn't — see the table below. Most people will read $286M of proposed insider sales into the high and conclude something. We read the actual filings and found pre-scheduled plans.
- **We know exactly what would change our mind, and it has a date on it.** That is worth more than a view.

## Why it might be priced in

Honestly: most of it probably is.

- The 19% drop on the day was the market pricing the disclosure. The *measurable* damage — the gap between the guided Q3 and normal seasonal growth — is worth roughly $25–45M a year of revenue, or $0.4–0.8B of value. The market erased **$19.3B**. So the market did not price the arithmetic; it priced the *uncertainty about the unnamed customer's size*. That is exactly the thing we also cannot resolve. We have no informational advantage on it.
- The forward order book, the accelerating base, and the clean insider record are all publicly available and cheap to find.
- Our two edges (reading filings, tracking sentence-level disclosure changes) tell us what the risk *is*. Neither tells us how it *resolves*. Resolution requires the November print.

**The uncomfortable summary: our reviewer's reasoning had several errors, but the conclusion survived on a ground the reviewer never actually argued — even the good case is nearly fully priced.**

## What we checked ourselves

Including, plainly, where our own reviewers got it wrong. The red team argued to reject; the blue team was assigned to attack the red team's work. The adjudication outranks both.

| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| The stock fell ~19% on the print | IBKR daily bars | $283.17 → $229.29 = −19.03% | **Yes** |
| "The company cut guidance and the market overreacted" | Compared the May and August guidance releases | **False.** Full-year guidance was *raised* from $4.30–4.34B to $4.45–4.47B, +$140M | **Yes — and it's bullish** |
| Red team's use of that fact | Read red's own write-up | **RED ERROR.** Red established there was no guidance cut, then filed it as a point *against* the stock. The raise put $93.5M *above* the prior second-half path, announced in the same document as the bad news — that is a company leaning in, not bracing. Red never processed it. | **Bench error** |
| Largest customer is reducing usage | 10-Q, 2026-08-06 | Confirmed, and it appears in **three** places including management discussion twice — not buried in one risk factor. Exact words: usage reduction "which may cause a deceleration in revenue growth" | **Yes** |
| "That customer's group drove the acceleration, so this kills the story" | Pulled the same disclosure from 7 filings, paired with revenue | **RED ERROR (partial).** Arithmetically the group is ~24% of growth, but its contribution *peaked in Q2-2025 at 10pp and has fallen since*, while total growth accelerated. The acceleration came from everything else. Red's causality was backwards. | **Weakened, not overturned** |
| Q3 guidance is far below normal seasonality | Recomputed using Datadog's own recent September quarters | **RED ERROR (size).** Red said the gap was ~5pp. Using Datadog's actual last two September quarters (+6.93%, +7.13%) and its own beat pattern, the gap is **0.5–1.1pp**. Red's 31-quarter median came from the hypergrowth era and doesn't fit a $4.5B company. | **Overstated ~5×** |
| Q3 guidance is a *separate* problem from the customer | Checked the timing | **RED ERROR (double-count).** Guidance was set 2026-08-06, five weeks into Q3, with the reduction already known. The weak guide *is* the customer. Counting both inflated the case. | **Redundant** |
| "The beat streak is narrowing" | Looked at the four numbers | +4.53 / +4.08 / +4.72 / +3.84 — noise, not a trend | **Unsupported** |
| Valuation ~290× cash flow after stock compensation | Recomputed from XBRL | **RED ERROR.** Red doubled first-half cash flow, but first half is ~44% of the year, not 50%; and used $433.2M of stock comp when the filed figure is $417.1M. Corrected: **~219×**, not 290×. Red overstated by ~32%. | **Corrected — conclusion still holds** |
| Is charging for stock comp double-counting? | Checked periods | No. And it's *generous*: share count grew 3.43% in a year (~$2.8B of real dilution vs. $915M of accounting charge) and there is **no buyback at all** | **Confirmed against us** |
| Profitability trend | XBRL operating income | Revenue +74% over two years; GAAP operating income went **$12.6M → $5.5M**, full-year 2025 was **−$44.4M** | **Yes — this is the strongest bearish fact and neither reviewer could break it** |
| "Stock is +121% off the April low of $132" | IBKR weekly bars and 26-week statistics | **RED ERROR — in red's own favor.** The 2026 low was **$98.01** (week of 2026-02-17). The real move was **+199%**. Red understated its own point. | **Yes** |
| Is that run multiple expansion? | Compared multiples at two highs | Partly not: at the Dec-2024 high the stock was ~16.6× forward sales; at $231 it was 17.7× — nearly the same multiple at a 36% higher price, because revenue compounded. But the week of **2026-04-27 gapped +42% with no earnings in it** and **blue could not source why**. | **Split — one leg unexplained** |
| Prior drawdown precedents (−69%, −52%) | Multiple history | The 2021–23 −69% started from ~60× sales — doesn't transfer. The 2025 **−52%** started from ~16.6× forward sales — **essentially today's multiple**. That one stands. | **One of two survives** |
| $286M of insider selling into the high | Parsed all 43 Form 4 filings since 2026-06-01 | **RED ERROR — overturned.** 25 reference pre-set 10b5-1 plans adopted **5–14 months earlier**, when the stock was roughly half the sale price (CEO's plan dated 2025-12-15 at ~$138; CTO's 2025-06-13 at ~$120–127). Total = **0.34%** of market value. Zero timing information. | **Overturned** |
| "Forward order book is flat — only +$10.2M in six months" | XBRL remaining-performance-obligation series | **RED ERROR.** Red compared across the Q4 renewal bulge. Year over year it is **+43.1%, and accelerating** (from +35.3%). *Conceded:* the first-half build was genuinely softer (+0.3% vs +6.7% last year) — real, but far smaller than "flat." | **Refuted as stated** |
| "Net revenue retention up from mid-110% to ~120%" | 10-Q text | Filing says **"low-120%'s"** now vs. **"about 120%"** a year ago. Improvement is smaller than red claimed. | **Mis-stated** |
| Largest customer's size and identity | Filings, XBRL, search | **Not disclosed anywhere.** Our shipment-data tool cannot help — software leaves no customs record. Search budget exhausted. | **No — open gap, reported not skipped** |
| Our own machine-built evidence pack | Cross-checked against the 10-Q | **OUR TOOLING ERRED.** The pack's revenue series stops at 2025-06-30 ($826.8M) — it lags a full year, so every current-quarter figure had to come from the filing directly. The pack also lists the Q2 10-Q under accession 0001628280-26-054458 while the working citation is 0001561550-26-000255; **unresolved**. | **Pack partially stale** |
| Next earnings date | Pack | 2026-11-05, derived from a market-data feed, **not from a company announcement** | **Unconfirmed** |

Primary sources: 10-Q for the quarter ended 2026-06-30 — https://www.sec.gov/Archives/edgar/data/1561550/000156155026000255/ddog-20260630.htm ; XBRL concept series — https://data.sec.gov/api/xbrl/companyconcept/CIK0001561550/us-gaap/RevenueRemainingPerformanceObligation.json

## PROPOSED ENTRY BANDS

**There is no entry. The verdict is DECLINE — no long, no short, no option premium selling.** The two reopen gates below are reproduced from the adjudication and are the only conditions under which this name comes back to court.

**Reopen gate 1 — information (the November print).**
> Q3 print (Nov): revenue ≥ **$1,190M** AND AI-native customer-group contribution ≥ **7 percentage points** AND largest customer **sized or disclosed** as a share of contracted revenue → re-court.

All three must hold together. $1,190M is roughly +34% year over year and is what the historical beat pattern implies off the guided $1,145M high end; hitting it *despite* the customer reduction is what proves the rest of the business absorbed the hit. The sizing requirement is what converts an unbounded risk into a bounded one — without it, we would be re-underwriting the same unknown.

**Reopen gate 2 — price.**
> Price ≤ **$155** (about 11× next-year revenue) → re-court on valuation. **Alert only, not a resting buy order.**

The reason it is an alert: a good-till-cancelled buy sitting 37% below market on a name with an undisclosed customer concentration is a trap — the only way it fills is on news we don't have yet, and we'd be the one buying from whoever does. We have made that mistake before and we are not repeating it.

**Distance and drift.** At adjudication the price gate was 33% below market. Today the stock is $245.30 and the gate is **36.8% below**. The name has moved against the decision by 6.0% in twelve days. That is recorded, not rationalized.

**Sizing.** Zero today. Neither reviewer set a position size for the reopen case; blue specified only "first tranche" at $155. **Size is deliberately left unset and must be decided at re-court** — writing a number here would be inventing authority the courts didn't grant.

**Exits/trims.** Not applicable — we own nothing.

**Catalyst dates.** Q3 earnings, estimated **2026-11-05** (derived from a market-data feed; **no company announcement has confirmed it** — verify when Datadog issues the date). The dated review pack is filed against **2026-11-20**.

**Why not short, given all the bearish findings.** The business is accelerating underneath, the order book is growing 43%, the insiders are clean, guidance was raised, the options market prices a 27% move, and the stock is fresh off a 199% run — crowded, not undiscovered. That is squeeze fuel, not a short.

**Why no option premium selling despite ~91% implied volatility.** This is a taxable account. Premium collected is short-term ordinary income with no ability to defer it. Not worth it.

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- price alert: fires below 155.0 (deck-provisional: ~11x FY27 revenue; re-court on valuation. ALERT ONLY — a GTC 37% below market on an undisclosed-custom)
- filing watch: 10-Q,10-K,8-K until 2027-02-15 (deck-provisional: Diff the AI-native / largest-customer disclosure sentences against the prior filing; alert on any chan)
- dated pack DDOG|2026-11-20: DDOG Q3 print (early Nov; date est. — verify when announced) + court reopen gate. HIT = revenue >= $1,190M AND AI-native cohort contribution
- dated pack DDOG|2026-11-05: DDOG: Q3 2026 earnings (feed-derived, no company announcement); reopen gate = revenue >= $1,190M AND AI-native cohort >= 7pp AND largest cus


## What remains unverified

- **Who the largest customer is.** Unknown. Search budget was exhausted. Our shipment-tracking tools are useless here — software ships no containers.
- **How big that customer is.** Not disclosed in any filing. This is the single number that decides the case, and neither reviewer could obtain it.
- **Whether the reduction is belt-tightening or departure.** The filing says "reduce their usage" — it never says churn, never says migrate. Five weeks of observation. Genuinely open.
- **Why the stock gapped +42% in the week of 2026-04-27** with no earnings in that week. Unexplained by either reviewer. It is the largest single unexplained leg of the run we are declining to buy into.
- **The Q3 earnings date.** Feed-derived, not company-confirmed.
- **Which accession number is the authoritative Q2 10-Q** — our pack and our citation disagree. The document content was verified; the pointer was not.
- **How much of the stock-comp charge understates true cost.** Grants were struck far below today's price, so the accounting charge is likely too low — but by how much, we did not quantify.

```json
{"price_gates": [{"level": 155.0, "direction": "below", "basis": "~11x FY27 revenue; re-court on valuation. ALERT ONLY — a GTC 37% below market on an undisclosed-customer-concentration name is adverse selection."}], "event_gates": [{"forms": ["10-Q", "10-K", "8-K"], "why": "Diff the AI-native / largest-customer disclosure sentences against the prior filing; alert on any change in stated contribution or first-time sizing of the largest customer — the 19% drop repriced on the filing text, not the press release."}, {"forms": ["4"], "why": "Alert only on 10b5-1 plans ADOPTED on or after 2026-08-06; existing plans were set 5-14 months earlier at ~half current prices and carry zero timing information."}], "catalyst_dates": [{"date": "2026-11-05", "what": "Q3 2026 earnings (feed-derived, no company announcement); reopen gate = revenue >= $1,190M AND AI-native cohort >= 7pp AND largest customer sized as % of ARR — all three required", "confirmed": false}, {"date": "2026-11-20", "what": "Dated review pack for DDOG — court reopen adjudication window", "confirmed": false}], "immediate_entry": null}
```