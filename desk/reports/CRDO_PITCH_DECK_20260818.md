# PITCH — CRDO — VERDICT

**PROPOSED — PENDING ADJUDICATION** — Both benches land on *no position*: stay flat through the ~2026-09-01 print, because the one thing that made this look like a mispricing (a "cash-quality anomaly" the market supposedly ignored) does not survive checking, and the company's own last-reported quarter already showed growth breaking down.

---

## What we believe

The original idea was simple: on 2026-08-18 the optical/AI-interconnect complex sold off, and Credo fell about 13% — roughly what the capital-heavy, cash-burning names fell — even though Credo actually generates cash. Astera Labs (ALAB), a nearby chip name, only fell about 5%. The inference was that the market lumped Credo in with the cash-burners and mispriced it.

After adversarial review, what we actually believe is narrower and less flattering:

1. **The 13% drop is explained, not anomalous.** Credo sells optical DSPs that go into pluggable transceivers — it sits at the part of the chain that got marked down hardest. ALAB sells PCIe retimers that live inside the rack, a different part of the chain. Using ALAB as the "control" was the error; it isn't a matched comparison.
2. **Credo's own growth already rolled over.** Reconstructing the quarterly revenue series from audited filings: Q1 FY26 $223.1M → Q2 $268.0M (+20.2%) → Q3 $407.0M (+51.9%) → Q4 $437.0M (**+7.4%**). All four are 13-week quarters, so this is not a calendar artifact. The quarter reported on 2026-06-01 decelerated from +52% to +7% sequentially. The August sell-off did not hit an innocent bystander; it marked to market a company fact that was already on the tape.
3. **The price does not compensate.** ~33x trailing sales, ~113x free cash flow, ~93x EBITDA, and only 20% below a 52-week high the stock reached after roughly tripling off its low.
4. **Nothing here diverges from consensus in our favor.** Where we *do* diverge, it points bearish (point 2).

So: the belief is that Credo is a good business at a price that requires re-acceleration it has not yet shown, ~9 sessions ahead of the print that will settle it.

## What the market believes

The market believes the deceleration is a pause, not a break. Sell-side rating is Strong Buy, average target $283.23 (about 15% above the $245.97 quote), and TD Cowen *raised* its target from $260 to $300 into the sell-off on 2026-08-18. Implied next-twelve-month EPS is roughly $6.15 against FY26 actual of $2.51 — the street is underwriting about a 145% earnings ramp. Short interest is only ~3.6% of float, so almost nobody is positioned against it.

Put plainly: the market believes the +7.4% quarter was a hiccup and hyperscaler demand re-accelerates. We have no evidence that it's wrong — only the observation that this is a large assumption being made at a very high price, and that we would be paying for it rather than being paid for it.

## Why we might have edge

- **The reconstructed Q4 number is not in the headline.** Q4 FY26 revenue isn't reported as a standalone figure; you get it by subtracting the first three quarters from the audited full year ($1,335.12M − $898.11M = $437.00M). Most screens and many summaries carry the full-year growth rate, which looks excellent, and never surface the +7.4% exit rate. That is a real, primary-sourced fact that is under-discussed.
- **Cash generation is genuinely better than the peer group's**, and it survives a fair adjustment (see below). If the print re-accelerates, this is a legitimately high-quality compounder and we'd want to own it — we just want to buy it after the fact, not before.
- **We have a house view that argues against paying up here.** The desk carries a frozen 45% probability of an AI capex break by end-2027. Buying a 33x-sales AI-interconnect name at a 20% drawdown is taking the other side of our own book. Not owning it is coherent; owning it would need an explicit argument that nobody produced.

## Why it might be priced in

- Everything above is available from public filings. The deceleration printed on 2026-06-01 and the stock has had eleven weeks to absorb it.
- The stock is already 20% off its high. Some of the "growth is slowing" adjustment has plausibly happened.
- The complex-wide de-rate is itself the market pricing chain position. We are not seeing something the market missed; we are agreeing with what the market did.
- Consensus is *more* optimistic than we are. That means our differentiated view is a bearish one — and we don't short high-multiple momentum names with 3.6% short interest, so there is no trade in either direction.

## What we checked ourselves

| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| FY26 free cash flow is ~30% of revenue | SEC XBRL company concepts (primary): revenue $1,335,116k, operating cash flow $464,292k, capex $57.3M → FCF ~$407M | 30.5% of revenue. Arithmetic correct. | **Yes** |
| Stock comp makes that FCF look better than it is | Pulled FY26 stock comp: **$182,638k**, up 136% from $77.4M — [data.sec.gov XBRL, ShareBasedCompensation](https://data.sec.gov/api/xbrl/companyconcept/CIK0001807794/us-gaap/ShareBasedCompensation.json). FCF less stock comp = $224.4M = 16.8% of revenue | True as a *level*. **But our red bench applied this adjustment only to Credo and not to the peers it was comparing against** — the exact one-sided-basis error red had just accused the original brief of making. | **Partly — bench error** |
| …so we re-ran it symmetrically | Same XBRL pull for Fabrinet (CIK 1408710) and Astera Labs (CIK 1736297) | Fabrinet FY26 stock comp $34.6M → ex-comp FCF **−0.7%** of revenue. ALAB CY2025 stock comp $160.0M on $852.5M revenue = **18.8% of revenue** vs Credo's 13.7%, putting ALAB at ~14.3% ex-comp FCF/revenue, **below** Credo's 16.8%. The ranking holds and Credo moves *up*. | **Yes — the kill inverted** |
| ALAB is a valid control for "the market graded on cash quality" | Compared beta, EV/sales, price/FCF, forward P/E | ALAB is higher-beta (3.84 vs 3.23), richer (EV/S 42.8 vs 33.3), lower FCF-yielding (P/FCF 190 vs 113) — and fell *less*. Cash quality, valuation and beta all predict the opposite ranking. **Chain position** explains the spread. Control was mis-specified. | **Yes — thesis leg dead** |
| "No company-specific news, so the drop is unexplained" | EDGAR filing index + reconstructed quarterly revenue | No 8-K since 8/4, so the *filing* claim holds. But the last reported quarter decelerated to +7.4% sequential — there was plenty of company-specific news, it was just eleven weeks old. **Our red bench instead attacked this leg by citing an earnings-date press release, which is a scheduling notice, not news, and which the blue bench could not independently verify.** | **Overturned by a better fact** |
| "We agree with the street, therefore no edge" | Counted ratings, price targets, short interest | Correct conclusion, wrong instrument — **counting analysts is coverage, not divergence**, and our own doctrine says a crowded name gets sized and timed differently, never rejected outright. The real divergence is the +7.4% exit rate vs a +145% implied EPS ramp. | **Bench error, verdict survives** |
| Insiders are dumping | Filing inventory: 9 Form 4s and 6 Form 144s in 30 days; FY26 cash flow shows **$743.4M of common stock issued** | Real overhang is the $743.4M primary issuance — the company itself sold equity at these levels. The Form 4 count is largely mechanical vesting given $182.6M of annual stock comp. **Neither bench actually opened a Form 4** — we are reading counts, not intent. | **Partly — overstated** |
| Is there a capitulation/flow signature? | Attempted live price history | **Could not check.** IBKR price tools were permission-denied for both benches. All tape work rests on the evidence pack plus one secondary vendor. | **No — open gap** |
| Detector sweep ran on the right set | Cross-checked the two benches' detector lists against the matched set | Red ran `albuquerque_permits` and `app_review_velocity`, neither of which was in the matched set, and skipped `clinicaltrials_lookup` and `competitor_trial_omission`, which were. All four were non-events here, but **substituting entries is a process failure** and would fail validation. | **Bench error, immaterial to verdict** |
| Export/China exposure | Attempted | **Could not check.** Credo has facilities in Mainland China and Hong Kong; we never pulled the 10-K geographic-revenue and named-customer table or screened it. Both benches flagged this as the highest-value open item — a China order pause would produce exactly the Q4 revenue shape we observed. | **No — open gap** |

## PROPOSED ENTRY BANDS

**Both benches say no entry. There is no immediate buy. What follows are the conditions under which we would reopen the file.**

*Sizing today: 0% of book. No starter, no ladder, no resting order into the print.*

**The binding gate is fundamental, not a price level.** Neither bench would authorize a purchase at any price before the print, because the open question is whether growth re-accelerates and only the print answers it.

**Reopen Gate 1 — the print (required, both must clear):**
- Q1 FY27 revenue ≥ **$524M** (that is +20% sequential off the $437.0M Q4 base — the last quarter before the break ran +20.2% and +51.9%, so +20% is the minimum consistent with the street's ramp, not a stretch), **and**
- the 10-Q shows the $174.0M inventory build is customer-committed (named hyperscaler purchase orders), not speculative.

**Reopen Gate 2 — price (only meaningful after Gate 1 clears):**

Working from the benches' own inputs — ~186.5M shares (market cap $45.87B ÷ $245.97), enterprise value ~$44.46B (33.3x $1.335B revenue), so ~$1.4B net cash — annualizing each post-print run rate gives:

| Post-print run rate | 25x sales | 20x sales | 15x sales |
|---|---|---|---|
| Gate 1 met: $524M/qtr → $2.10B annualized | **$289** | **$232** | **$176** |
| Gate 1 missed: +7.4% again, $469M/qtr → $1.88B | $259 | $209 | **$159** |

Today's $245.97 already pays **~21x** the *bull* run-rate and **~24x** the no-re-acceleration run-rate. Note that the street's $283.23 target lands almost exactly on "Gate 1 clears *and* the market still pays ~25x" — it needs both.

- **Starter authorized only if:** Gate 1 clears **and** the stock is at or below **~$232** (≈20x the achieved bull run-rate). Size **≤0.75% of book**, one tranche.
- **Second tranche at ≤$176** (15x the bull run-rate) if the first is filled and the thesis is intact.
- **If Gate 1 misses:** no entry at any price above **$159**. Below ~$159 the stock is no longer priced for re-acceleration and the name becomes a different, cheaper conversation — re-court from scratch.
- **Trim/exit if entered:** exit on the first sequential quarter back below +10%, or on any disclosure of China-related customer or export restriction. These would be set at entry, not now.

**Catalyst dates:**
- **2026-09-01 — Q1 FY27 earnings.** Derived from historical cadence (Q1 FY26 results 8-K'd 2025-09-03; Q4 FY26 on 2026-06-01) and yfinance. **Not confirmed by a company press release we have read.** One bench cited an ~2026-08-11 company announcement of the call date; the other could not verify it. Treat as ~9 sessions out, date not nailed down.
- **~2026-09-03 to 09-10 — 10-Q filing.** This is where the inventory, receivables, geographic revenue and customer-concentration detail lands. The 10-Q matters more to us than the headline.

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- price alert: fires below 159.0 (deck-provisional: 15x annualized no-re-acceleration run rate; below here the stock stops pricing a ramp — re-court from )
- filing watch: 8-K until 2027-02-14 (deck-provisional: Item 2.02 Q1 FY27 results — confirms the unconfirmed 2026-09-01 date and delivers the sequential-growt)
- dated pack CRDO|2026-09-01: CRDO: Q1 FY27 earnings — derived from cadence (Q1 FY26 on 2025-09-03, Q4 FY26 on 2026-06-01) and yfinance; no company PR verified (date conf
- dated pack CRDO|2026-09-08: CRDO: expected 10-Q filing window — inventory, receivables, geographic revenue, customer concentration (date confirmed=False)


## What remains unverified

- **Live price and volume.** IBKR history was permission-denied for both benches. Every tape statement rests on the evidence pack plus one secondary vendor. We cannot say whether 8/18 had capitulation volume.
- **The print date.** 2026-09-01 is derived from cadence, not read off a company press release we hold. The claimed ~2026-08-11 date announcement and an ~2026-08-10 OCP interconnect announcement are single-secondary-source and unverified.
- **How much of Credo's revenue is optical-DSP / transceiver-attached.** This is now the central explanatory fact and it is *reasoned from product architecture*, not pulled from a segment disclosure. We never found a revenue split.
- **Peer betas and multiples** (ALAB 3.84 / CRDO 3.23, EV/S, P/FCF) come from a single vendor and were never checked against primary filings.
- **The ALAB comparison is calendar-mismatched** — Credo FY26 versus ALAB calendar-2025 annuals, not a matched trailing-twelve-month basis. The direction of the finding is robust; the precise 16.8% vs 14.3% gap is not.
- **Form 4 bodies unread.** Neither bench opened one. The vest-versus-discretionary split is inferred from the size of the stock comp charge.
- **China and Hong Kong exposure.** Facilities exist; customer and geographic concentration were never pulled or screened. This is the single unexamined item most capable of changing the verdict, in either direction.
- **Whether the $174.0M inventory build is customer-committed.** Unknowable until the 10-Q.
- **Detector coverage was procedurally imperfect** — two matched detectors were skipped and two unmatched ones substituted. All four look immaterial here, but the sweep was not clean.

---

```json
{"price_gates": [{"level": 232.0, "direction": "below", "basis": "20x annualized post-print run rate IF Q1 FY27 revenue >= $524M; starter only, <=0.75% of book"}, {"level": 176.0, "direction": "below", "basis": "15x annualized bull run rate; second tranche only if gate 1 cleared and first tranche filled"}, {"level": 159.0, "direction": "below", "basis": "15x annualized no-re-acceleration run rate; below here the stock stops pricing a ramp — re-court from scratch"}, {"level": 302.52, "direction": "above", "basis": "26-week high reclaimed without a print — thesis stale, close the file"}], "event_gates": [{"forms": ["8-K"], "why": "Item 2.02 Q1 FY27 results — confirms the unconfirmed 2026-09-01 date and delivers the sequential-growth answer"}, {"forms": ["10-Q"], "why": "inventory ($174.0M build) and receivables detail, geographic revenue and named-customer concentration — the actual decision inputs"}, {"forms": ["4", "144"], "why": "separate vest-driven sales from discretionary distribution; bodies were never read by either bench"}, {"forms": ["S-3", "424B5"], "why": "$743.4M FY26 primary issuance is the real overhang; a follow-on at these levels would confirm treasury is still monetizing the multiple"}, {"forms": ["10-K"], "why": "run export_control_check on the named-customer and geographic-revenue table against BIS Entity List and Treasury SDN"}], "catalyst_dates": [{"date": "2026-09-01", "what": "Q1 FY27 earnings — derived from cadence (Q1 FY26 on 2025-09-03, Q4 FY26 on 2026-06-01) and yfinance; no company PR verified", "confirmed": false}, {"date": "2026-09-08", "what": "expected 10-Q filing window — inventory, receivables, geographic revenue, customer concentration", "confirmed": false}], "immediate_entry": null}
```