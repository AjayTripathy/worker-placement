Write is disabled in this session, so the deck is below in full — copy it to `desk/reports/NCLH_PITCH_DECK_20260818.md`.

---

# PITCH — NCLH — VERDICT
**ADJUDICATED 2026-08-18 — WATCH** (conviction 7/10; no position, no orders, size zero today; reopen requires BOTH a price of $13 or lower AND a positive forward-booking number at the Q3 report)

---

## What we believe

Norwegian Cruise Line's ships are full and its prices are broken, and the damage is still in front of it rather than behind it.

The cleanest evidence is the money customers have already paid for cruises they have not yet taken — "advance ticket sales," a real audited liability on the balance sheet, not a management talking point. That number has gone the wrong way for three straight quarters, and the deterioration is getting worse, not better:

| Quarter ending | Advance ticket sales | Change vs. same quarter a year earlier |
|---|---|---|
| 2025-12-31 | $3,200,593K | **+3.05%** |
| 2026-03-31 | $3,718,873K | **−1.15%** |
| 2026-06-30 | $3,651,201K | **−4.76%** |

That is a straight line down, and it dates the turn to the first quarter of 2026. It is worse than it looks, because the fleet grew over the same period — roughly 4–6% more capacity days by the company's own full-year guidance. Adjusting for that, the forward book is down somewhere around **9–11% per berth**. Deposits are collected two to three quarters before the sailing shows up in reported revenue, so this is a preview of 2027, not a description of 2026. Management effectively conceded it: it says it is "below its optimal booked position for the next 12 months."

The second thing we believe is that this is Norwegian's problem, not the industry's. In the same quarter, under the same geopolitics, Royal Caribbean **raised** its year (adjusted EPS to $17.73–17.87, net yields reaffirmed at +1.75% to +2.25%). Norwegian **cut** its year — and cut it hard. Its own guidance went from ~$2.95B adjusted EBITDA / $2.38 adjusted EPS / roughly flat yields on 2026-03-02, to ~$2.5B / $1.50 / **−5% yields** on 2026-07-30. That is 15% of EBITDA and 37% of EPS removed by the company itself in five months, while the closest comparable company went the other way. Norwegian's own release attributes it to "company-specific execution challenges."

The third thing we believe — and this is why the answer is "watch" and not "never" — is that **this is a pricing problem, not a solvency problem.** Occupancy was 102.4% in Q2 and is guided to ~102.3% for the year. The ships sail full; the company just isn't getting paid enough per passenger. And the frightening-looking shipbuilding bill is mostly already financed by someone else (details in the table below). So the equity is a leveraged claim on a real, recoverable asset base that is currently earning too little — not a company at risk of not existing.

This court was convened to answer a specific question carried over from our Lindblad work: does "expansion getting absorbed at full fare" in expedition cruising tell us anything about mainstream cruising? **It does not, and the reason is structural.** Expedition operators add ships opportunistically when demand shows up. Mainstream operators order hulls from shipyards years ahead under binding contracts; that supply arrives whether the demand does or not. Lindblad shows zero fare cuts with 59.6% of departures sold out. Norwegian shows full ships and collapsing prices. Same industry family, opposite reading.

## What the market believes

Roughly what we believe. The stock is down 33% from its 52-week high, and the consensus numbers for this year are the company's own guided-down figures — about $2.5B of adjusted EBITDA and about $1.50 of adjusted EPS. The market has read the July guidance cut, believes it, and has repriced for it.

At $18.18 the market is paying about $8.35B for the equity (459,158,514 shares) on top of roughly $14.8B of net debt, so about **$23.2B of enterprise value — about 9.3x the guided-down EBITDA**, at 5.3x net leverage. That is not a distressed price and it is not an obviously cheap one. It is a price that says: the decline is real, the company survives it, and normalization arrives around 2028 — which is, word for word, what management is guiding to.

Worth noting: the stock is already **+25% off its 52-week low of $14.53**. Whatever the moment of maximum pessimism was, we missed it, and the tape has partly recovered from it.

## Why we might have edge

Honestly assessed, we have **process** edge here, not **estimate** edge.

- **We read the right number.** The advance-ticket-sales series is in the audited liability, not the press release, and it is not the number the sell side leads with. Getting the monotonic three-quarter deterioration — and dating the turn to Q1 2026 — from the primary XBRL data is real work most desks skip. We turned it into a reusable detector (deposits falling in dollars while berths grow).
- **We forced the comparison.** Putting Norwegian's cut next to Royal Caribbean's raise, in the same quarter under the same conditions, is what converts "cruise stocks are down" into "this specific operator is losing share." A sector mean-reversion screen would have flagged this as a bargain. It isn't one.
- **We corrected our own framing.** The transferability question — does Lindblad's full-fare absorption tell us anything about Norwegian — was answered with a mechanism (contracted vs. opportunistic supply), not an analogy. That mechanism is now reusable.
- **The one place a future edge could live** is the brand mix. Norwegian disclosed record bookings at Oceania and Regent's best booking month ever. If the luxury brands are genuinely strengthening while the mainstream brand is the whole problem, the blended numbers understate the good part of the business. **We could not check this, because our own connector broke** (see below). That is an open, findable edge — not a claimed one.

## Why it might be priced in

Mostly because it is.

The decisive test we apply to every idea is whether we hold a number that differs from the market's for the period that matters. **We do not.** We agree with the street on this year. Our own attempt at a forward bridge — recovering yields to 2025 levels by 2028, ~28.5M capacity days, $100M of announced cost savings — gets to about $3.0–3.2B of EBITDA, worth roughly **$31/share** on the same 9.3x multiple. If nothing recovers and EBITDA stays flat at $2.5B, the stock is worth about **$20**. Against $18.18 today, that is roughly +10% for being right about the base case. That is not enough compensation for 5.3x leverage.

And our own recovery case rests on a yield rebound that **the deposit series actively contradicts**. We are, in effect, arguing against our own strongest finding when we build the bull bridge. That deserves to be said out loud.

Two more reasons to expect no free lunch: the name is heavily covered and heavily owned (our crowding measure reads DISCOVERED_CROWDED, attention 0.874, institutional ownership 1.0), and the price is 25% above the low. There is no informational vacuum here.

## What we checked ourselves

| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| Forward bookings are deteriorating | Pulled `ContractWithCustomerLiabilityCurrent` directly from SEC XBRL (both benches pulled independently) | $3.651B vs $3.834B = −4.76% YoY; prior quarters −1.15% and +3.05% — a monotone three-quarter decline | **YES — this is the leg the verdict stands on** |
| Could the deposit drop be a promotion, not lost demand? | Ran the artifact test: a "low deposit" promotion shrinks the liability with no booking loss. Checked against management's own language | Fails to rescue it — "below its optimal booked position" is a statement about volume, not deposit terms. **Had management not said that sentence, this finding would have been ungradeable** | YES, with that caveat stated |
| "Down 11.5% per capacity day" | Re-derived from FY26 capacity guidance (26.25M days) rather than from revenue arithmetic | True range is ~−9% to −11%. Red bench's −11.5% was derived, not disclosed, and was at the aggressive end | Directionally yes, **red overstated the precision** |
| It's the sector, not the company | Compared to Royal Caribbean's same-quarter release | RCL raised (EPS $17.73–17.87, yields +1.75–2.25%); NCLH cut to −5% yields and named its own execution | YES |
| The company can't fund its shipbuilding | Read the issuer's own capex table, gross and net | **RED BENCH ERROR — the solvency case is wrong.** Red compared $7.6B of *gross* newbuild capex to three years of EBITDA. The issuer's own table shows gross ~$7.2B, **committed export-credit financing $5.0B**, **net $2.3B** — a ~3x overstatement of the cash drain. Roughly 70% pre-financed | **NO — refuted, and struck from the verdict** |
| "The cash is the customers'" ($218M cash vs $3.65B deposits) | Compared to peer capital structures | **RED BENCH ERROR (soft).** Deposit float is universal to the cruise model — Royal Caribbean and Carnival look identical. It is the transmission channel for the deposit finding, counted a second time as though it were independent evidence | NO — merged into the deposit finding |
| "No divergence from the street" as a reason to kill | Doctrine audit | **RED BENCH ERROR (method).** Red killed on the *absence* of its own estimate — that is the test not being run, not the test failing. Blue then actually ran it and got $20 no-recovery / $31 on recovery, which still doesn't clear the bar | Kill survives — **but on the estimate, not on the silence** |
| Satellite check on the Caribbean demand fix (Great Stirrup Cay) | Sentinel-2 buildout detector, 25.823 / −77.901 | **OUR OWN DETECTOR WAS MISAPPLIED.** It reported `construction_activity=False`, but the built-up index it uses cannot see marine pier construction, and the baseline scene (2021-02-11) is a COVID-idle island. Meanwhile the company names a dated, checkable milestone: **"Great Tides Waterpark," opening 2026-09-04** | NO — the "no ground truth" finding is withdrawn |
| Booking-site read on Norwegian's own brands | `expedition_inventory` connector, two dispatches (ncl.com and rssc.com) | **OUR CONNECTOR RETURNED THE WRONG COMPANY'S DATA.** Both dispatches returned byte-identical output — 1,986 departures, 59.6% sold out — which is *Lindblad's* book. The connector silently defaulted to LIND on any input it didn't recognize, so a bench asking about Norwegian received Lindblad's numbers dressed as Norwegian's. Real-looking numbers for the wrong issuer is strictly worse than a crash | **NO — defect. Fixed this session** (no default; unknown/missing operator now fails loudly; smoke test gained an assertion that an empty request must never return success) |
| Crowding as a reason to kill | Doctrine audit | **RED BENCH ERROR (method).** Red conceded crowding only sizes and times a position, then stacked it back onto the kill anyway. Struck from the kill; retained as an instruction that any eventual entry is tranched | NO as a kill; YES as a constraint |
| "No dilution to report" | Read the S-8 filed 2026-08-03 | **RED BENCH ERROR (minor).** There is dilution: 8,807,000 shares registered (~1.9%) under the amended 2013 plan. Below the level that would change anything, but red asserted none existed | NO — small but real |
| The evidence pack's own financial data | Sanity-checked the pack's XBRL block | **THE PACK WAS BAD AND BOTH BENCHES CAUGHT IT.** Revenue series ends in 2017; operating cash flow and stock comp are annual figures stamped as quarterly; diluted share count is non-monotonic (514.9M at 2024-09-30 vs 431.0M at 2024-03-31). Both benches discarded it and re-pulled from SEC primary | NO — pack superseded by primary sources |
| Cap structure before any per-share claim | 10-Q cover page | 459,158,514 shares × $18.18 = $8.35B market cap ✓ | YES |
| Is the next earnings date real? | Checked provenance | 2026-11-04 is derived from a data vendor, **not confirmed by a company announcement** | NOT CONFIRMED — treat as approximate |
| Unread filings | Filing inventory audit | The 8-K/A of 2026-08-12 and the 8-Ks of 2026-06-16 and 2026-05-29 were **read by neither bench**. Seven Form 4s (2026-05-11 → 06-03) also unparsed | **NO — open coverage gap** |

## PROPOSED ENTRY BANDS

**There is no entry today. Size zero.** This is a rejection as an entry, not as a security — the reopen conditions below are the deliverable, and they are reproduced exactly as the court set them.

**REOPEN GATES — BOTH REQUIRED:**

1. **Fundamental gate:** Advance ticket sales **positive year-over-year per capacity day** at the Q3 10-Q (approximately 2026-11-04). This is the single sufficient statistic; both benches agreed on it independently. Concretely, with capacity up roughly 7%, a flat absolute dollar figure is *not* enough — the number has to grow.
2. **Price gate:** **$13.00 or lower.**

Either one tripping re-opens the court automatically. Both must hold for any capital to move.

**Why $13 and not lower:** at $13, the no-recovery case (EBITDA flat at $2.5B, worth ~$20) is **+50%**, and the 2028 normalization case (~$3.0–3.2B EBITDA, worth ~$31) is **+140%**. That is enough compensation for 5.3x leverage; $18.18 is not. This band **supersedes the red bench's $8–10**, which was built on the gross-capex solvency error corrected above.

**Sizing, if both gates clear:** tranched, never sized on an information claim — the name is crowded, so we cannot argue we know something others don't. *Neither bench produced a position size; the following is desk convention, not court output, and is subject to re-court:* a first tranche no larger than 0.5% of the book, a hard cap of 1.5% until two consecutive quarters of positive per-berth bookings, and no averaging down inside the same quarter.

**Exits / trims:** not applicable — there is no position. If one is ever established, the exit test is the entry test inverted: a single quarter of renewed per-berth deposit decline closes it, regardless of price.

**Catalyst dates:**
- **2026-09-04** — Great Tides Waterpark opens at Great Stirrup Cay. Company-named and dated; the one checkable piece of the Caribbean demand remedy.
- **~2026-11-04** — Q3 10-Q and results. Carries the fundamental gate. **Date is vendor-derived and unconfirmed by the company** — verify against a company announcement before relying on it.

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- price alert: fires below 13.0 (deck-provisional: At $13 the no-recovery case (~$20) is +50% and the 2028 normalization case (~$31) is +140% — adequate )
- filing watch: 10-Q until 2027-02-13 (deck-provisional: Q3 10-Q (~2026-11-04) carries advance ticket sales — the single sufficient statistic; must be positive)
- dated pack NCLH|2026-09-04: NCLH: Great Tides Waterpark opens at Great Stirrup Cay — the only dated, checkable piece of the named Caribbean demand remedy; a slipped ope
- dated pack NCLH|2026-11-04: NCLH: Q3 2026 results and 10-Q — carries the advance-ticket-sales reopen gate; date is vendor-derived and NOT confirmed by company announcem


## What remains unverified

- **The luxury brands.** Oceania's record bookings and Regent's best-ever booking month are management statements we never independently checked, because our connector handed us the wrong company's data. If they are true, the mix runs in Norwegian's favor and the blended deposit decline understates the mainstream problem while overstating the whole-company problem.
- **Our own recovery case.** The ~$31 bridge assumes yields return to 2025 levels by 2028. The deposit series says the opposite is happening right now. We are using an assumption our best evidence contradicts.
- **The per-berth adjustment.** Capacity-day growth is guided, not reported quarterly. The −9% to −11% per-berth figure is our arithmetic on a guided denominator, not a disclosed number.
- **The next earnings date.** Vendor-derived. Unconfirmed by the company.
- **Three 8-Ks and seven Form 4s.** Unread by either bench.
- **Great Stirrup Cay.** Our satellite check was the wrong instrument for marine pier work on a COVID-idle baseline. We have no independent ground truth on the single named Caribbean remedy — only a dated opening we can check on 2026-09-04.
- **Whether the crowd is wrong at all.** We agree with the street on this year's numbers. Nothing in this deck claims otherwise.

**Primary sources:** [NCLH 10-Q, filed 2026-08-03, accession 0001104659-26-089657](https://www.sec.gov/Archives/edgar/data/1513761/000110465926089657/) · [SEC XBRL — advance ticket sales (ContractWithCustomerLiabilityCurrent), CIK 1513761](https://data.sec.gov/api/xbrl/companyconcept/CIK0001513761/us-gaap/ContractWithCustomerLiabilityCurrent.json) · [NCLH 8-K exhibit 99.1, 2026-03-02 — original FY26 guidance and the gross / export-credit / net capex table](https://www.sec.gov/Archives/edgar/data/1513761/000117184326001220/exh_991.htm) · [Royal Caribbean Q2 2026 earnings release 8-K, 2026-07-28](https://www.sec.gov/Archives/edgar/data/0000884887/000088488726000036/a2026q2earningsrelease.htm) · [NCLH Q2 2026 results, 2026-07-30](https://www.globenewswire.com/news-release/2026/07/30/3335864/24500/en/Norwegian-Cruise-Line-Holdings-Reports-Second-Quarter-2026-Financial-Results.html)

```json
{"price_gates": [{"level": 13.0, "direction": "below", "basis": "At $13 the no-recovery case (~$20) is +50% and the 2028 normalization case (~$31) is +140% — adequate pay for 5.3x net leverage; supersedes red bench's $8-10, which rested on a gross-capex solvency error."}], "event_gates": [{"forms": ["10-Q"], "why": "Q3 10-Q (~2026-11-04) carries advance ticket sales — the single sufficient statistic; must be positive YoY PER CAPACITY DAY to clear the fundamental gate."}, {"forms": ["8-K"], "why": "Both FY26 guidance actions (2026-03-02 original, 2026-07-30 cut) arrived as 8-K exhibit 99.1; a third revision either way is decision-grade."}, {"forms": ["8-K/A", "4"], "why": "Backfill only: 8-K/A 2026-08-12 plus two further 8-Ks and seven Form 4s were read by neither bench — a known coverage gap."}], "catalyst_dates": [{"date": "2026-09-04", "what": "Great Tides Waterpark opens at Great Stirrup Cay — the only dated, checkable piece of the named Caribbean demand remedy; a slipped opening reads on execution credibility.", "confirmed": true}, {"date": "2026-11-04", "what": "Q3 2026 results and 10-Q — carries the advance-ticket-sales reopen gate; date is vendor-derived and NOT confirmed by company announcement.", "confirmed": false}], "immediate_entry": null}
```

---

Two things to flag: the Write tool is disabled this session, so nothing was saved to disk and no sensor was armed — the JSON fence needs a run of the arming step against a saved file. And the sizing numbers in the entry-bands section are the only figures in the deck that came from neither bench; they are labeled as such.