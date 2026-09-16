# PITCH — SPIR — VERDICT

**PROPOSED — PENDING ADJUDICATION** — no capital, no orders, no entry at $12.04; the file reopens only on the 11/12 print against the numeric bands below.

*Position today: NO POSITION, NO ORDERS. Tape $12.04 (52-wk $6.60–$25.90; −53.5% from the high, +82% off the low). Both benches came out FLAT for different reasons; neither wants to own it before the Q3 print.*

---

## What we believe

Spire Global sells data collected from its own small satellites — weather, ship tracking, aircraft tracking — mostly to governments and agencies on multi-year contracts. Two things are true about it at once, and the whole argument is about which one matters more.

The **money leg is genuinely damaged**. In the first half of 2026 the company burned $49.6M running the business and another $13.4M building satellites — $63.0M of cash out the door in six months. That is 14% *worse* than the same period a year earlier, and roughly three times the burn of the immediately preceding half-year. Against about $91.7M of liquidity and no debt, that is roughly three and a half quarters of cash, so a capital raise sometime in the first half of 2027 is the base case, not a tail. There is no committed credit line standing behind it.

The **demand leg is damaged but not dead**, and this is where our own red bench overreached. Contracted future revenue (RPO) fell $50.3M in one quarter — from $184.8M to $134.5M. Read as a total, that looks like customers walking away. Read by maturity band, $36.9M of the $50.3M — 73% — came out of the 13-to-36-month buckets, which are buckets that *ordinary revenue recognition cannot drain*. That is the signature of one contract being removed, not of demand decaying. The contract is identifiable: the Canadian Space Agency terminated Spire's C$71.8M WildFireSat program for convenience on 23 April 2026, and Spire names that cancellation in its own Q2 release as the cause of the gross-margin drop from 52% to 38%. Strip it out and the residual booking decay is roughly −$13M, which is bad but ordinary.

So: we believe the RPO headline overstates the demand problem by about four times, we believe the burn problem is exactly as bad as it looks, and we believe **neither belief is worth capital at $12.04**, because of the third thing we believe — the upside is capped. At today's price the whole company is valued at about $397M net of cash, roughly 5x this year's revenue guidance. If you hand Spire all the money it needs for free and let it grow to $110M of revenue in 2027, the same 5x multiple gets you about $12.69 a share after the dilution — 5% above the current price. You need the multiple to expand past 6x forward sales to make 27%. **The binding constraint on this stock is not financing. It's the valuation roof.** A name where the fully-funded bull case pays under 30% is not a name you buy while its cash is running out.

## What the market believes

Sell-side price targets sit around $20.88 — roughly 70% above the tape — and the sell side anchors on the company's own FY2026 guidance of $75–85M in revenue and on the "85% of the full-year guide is already contracted" framing. The bull story is: the maritime business was sold to Kpler for $241M, the balance sheet is debt-free, the government weather-data franchise is real and growing, WildFireSat was a one-off, and the burn normalizes as the satellite build cycle rolls off.

The stock, meanwhile, is down 53% from its 52-week high and fell 9.4% in the week of 25 August. That is not a market that believes the $20.88 targets. Our read of the recent tape is that it is **supply, not information**: on 13 August the company registered 8.2M shares for resale — a 5.0M-share April private placement struck at $14.00 (now 14% underwater) plus a separate 3.16M-share block. That is 20.2% of the 40.6M shares outstanding, and it is about **8.8 times the average daily volume**. Six insider Form 4s and a Form 144 cluster on 24–25 August, immediately before the drop. Registered stock that can now legally be sold is hitting a thin tape.

Where we differ from the street: they treat contracted backlog as a quality signal and quote its *level*. We watch its *direction and composition*. And we sit at the low end of the guide — $75M, not the $80M midpoint — because of the band math below.

## Why we might have edge

Three specific pieces of work, all of which came out of the court rather than from a screen:

1. **The band decomposition.** Almost nobody re-derives an RPO decline against its own maturity buckets. Doing it turns a "customers are leaving" headline into "one government cancelled one program in April, and everyone already knew." Our blue bench built this into a reusable detector (`rpo_time_band_decomposition`): when more than 60% of a backlog decline lands beyond 12 months, it's a contract removal, not demand decay — and the *inverse* firing, decline concentrated in the near band with long bands intact, is the genuinely dangerous reading.

2. **The coverage-ratio artifact.** "85% of the full year is contracted, up from 76%" sounds like improving demand. It rises automatically as the calendar elapses, because revenue you already recognized counts toward the numerator. On an $80M base, the ~$6M recognized between the two disclosures explains about 7.5 of the 9 points of "improvement." Recomputed *forward* — contracted-but-not-yet-recognized against revenue-still-needed — H2 coverage is about 74%, not 85%. Also a reusable detector (`elapsed_time_coverage_ratio_artifact`).

3. **The near-band guide test.** This is the finding that actually matters and it is the *bearish* one, produced by the bench arguing for the stock. The 0–12 month RPO bucket at 30 June was $51.4M, spread over a full twelve months. At the rate Spire actually drew that bucket down last quarter, the second half of 2026 yields roughly $30M from existing contracts against the **$41.1M needed to hit even the low end of guidance**. That is ~$11M of brand-new short-cycle business required in about four months. It's a dated, checkable, gradeable risk of a guidance cut into the November print — and it is not a number the street is quoting.

Honest limit on all three: this is diligence edge, not information edge. Everything above comes from public filings anyone could read.

## Why it might be priced in

The WildFireSat cancellation was public from 29 April 2026 — SpaceNews, SpaceQ, and the retail press all covered it within days, and the stock has had four months to digest it. Our "the tape misread the RPO decline" claim is therefore weak: the tape may have read it correctly the first time and simply not cared by August.

The burn is in every filing. The 20.2% resale registration is a public 424B3. The valuation is arithmetic on a public share count. Our red bench's tally: of its kills, roughly half were **consensus** — things the market plainly knows — and the genuinely novel ones (the coverage-ratio artifact, the near-band guide math) are metric-hygiene findings that change how confident we are, not findings that reveal a hidden asset or a hidden hole.

And the roof argument cuts both ways: if 5x forward sales is simply what the market pays for a sub-scale space-data operator with negative cash flow, then the stock is *correctly* priced at $12 and there is no mispricing to harvest in either direction. We could not verify peer multiples — that is a stated gap, and it is the single input that would most change the roof table.

## What could go wrong

**Failure narrative 1 — we buy the reconciliation and the near band drains too (has a tripwire).** We convince ourselves the $50.3M RPO drop was 73% WildFireSat, take a starter after the November print, and then Q4 and Q1 show the 0–12 month band falling *without* a nameable cancellation behind it. That would mean the residual −$13M was the start of real decay, not noise, and we would have pre-explained away the very evidence that should have stopped us. Tripwire: the 0–12 month band on each subsequent 10-Q. Monitorable, dated, cheap.

**Failure narrative 2 — the raise arrives worse than modeled (has a tripwire).** Cash exhausts on our math around March 2027. If the November print misses and the stock is in the single digits, the equity raise happens at a punitive price into an already-registered overhang, and the dilution assumption in our roof table (~$60M, ~46M shares out) turns out to be optimistic. Tripwire: cash balance and operating burn each quarter; any S-3, ATM, or prospectus supplement. Note a red-bench error here that made this look *worse* than it is: red claimed a live ATM shelf based on a full-text search hit count. The 10-Q carries no ATM disclosure, and the 424B3s are *resale* registrations that put zero dollars into the company. The dilution is coming, but it is not already drawn.

**Failure narrative 3 — another customer terminates for convenience, with no warning at all (NO monitorable tripwire).** WildFireSat was not lost on performance, price, or competition. A sovereign agency exercised a contractual right to walk away, and Spire found out when it found out. NOAA, EUMETSAT, and the other agency programs carry the same clause. **There is no leading indicator for this.** No satellite image, no permit filing, no app-review velocity, no customs record, no insider print tells you a government committee decided to reallocate a budget line. Unknown-unknown class: **counterparty-discretionary program cancellation — sovereign/agency termination-for-convenience risk**. It is not a tail we can instrument; it is a tail we can only size for. It argues that any eventual position is a 0.3–0.5% starter and never a 2% conviction slot, no matter how good the November print looks. A single line item vanishing takes ~25% of forward contracted revenue with it, again, at any moment.

**The reflexive and structural leg.** Our own size is not the problem here — a 0.3–0.5% starter is a small fraction of the 928k-share daily volume, and we would not move this tape. The problem is that we are *downstream* of someone else's flow: 8.2M registered shares at 8.8x ADV, with a PIPE block struck at $14.00 that is currently 14% underwater. That block has a natural reason to sell into every rally toward $14 and a natural reason to hold below it. Our value-ladder flow gate — never bid into flow you yourself predicted — was written for our own selling and gives us no protection here; worse, it creates a tempting inversion, "buy the overhang, it's mechanical." It is not mechanical. We cannot see the block's remaining size, and a fresh registration can re-arm it at any time. The doctrine interaction to watch is the other one: our clean-court minimum-starter default says a FLAT verdict requires a *named* kill. We have named kills — the capital leg and the near-band guide math — so this FLAT is legitimate and not a failure of nerve. But the mirror risk is that blue's re-court trigger ("Q3 RPO ≥$130M and Q3 revenue ≥$20M → starter") becomes an automatic buy on 12 November. **Clearing that trigger is necessary, not sufficient.** The roof table has to be re-run at the then-current price before any order exists.

If this position loses money, the most likely reason will be that we accepted the WildFireSat reconciliation as the full explanation for the backlog collapse, sized in after a merely-adequate Q3, and then watched the near-term contracted book drain on its own while 8.2M registered shares sold into every bounce and a dilutive raise landed in the first half of 2027.

## What we checked ourselves

| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| Share count 39.12M | 10-Q cover page | Class A 39,115,046 + Class B 1,507,325 = **40,622,371**; the brief used the A-class only | **NO — brief error, corrected.** Both benches caught it independently |
| Diluted shares fell 147.7M → 20.8M = massive change | Evidence-pack XBRL series | Split-unadjusted artifact of the August 2023 1-for-8 reverse split. Not dilution | **NO — the evidence pack itself was wrong.** Both benches superseded it |
| RPO $184.8M → $134.5M (−$50.3M) | Q1 and Q2 10-Qs, both pulled | Confirmed exactly | YES |
| That decline means ≈−$32M of net bookings (red's central kill) | Blue re-derived it by maturity band | 73% of the decline sits in 13–36mo buckets revenue recognition cannot touch; residual decay ≈−$13M | **NO — red's kill was ~4x overstated.** Red held the WildFireSat fact in its own finding #6 and applied it only to margins, then set its change-my-mind bar at exactly the reconciliation it declined to run |
| "32% operating cash flow improvement" (company framing) | XBRL, quarter and half-year | Q2'26 −$23.4M vs Q2'25 −$35.1M is true; but H1'26 −$49.6M vs H1'25 −$43.5M is **14% worse**, and the prior-year comp quarter burned 4.2x the quarter before it and carried a $7.0M settlement | **Company claim technically true, materially misleading.** Both benches sustained. Best finding in the red case |
| "ATM / S-3 shelf is live (24 EDGAR hits)" | Blue read the 10-Q directly | No ATM disclosure in the filing; the 424B3s are resale registrations raising the company **$0** | **NO — red bench error from a full-text search artifact** |
| "H1 GAAP revenue −21% YoY" (red's closing line) | Blue checked the comp base | H1'25 includes the maritime business sold to Kpler in April 2025. Ex-maritime, Q2 was **+16%** | **NO — red committed the exact base-effect error it had just convicted the brief of** |
| Runway ~3.2 quarters | FCF math, plus contingencies footnote | ~3.2 quarters extends to ~3.6 once you include the **$12.4M NorthStar arbitration award in Spire's favour (31 July 2026)**, which red missed. No going-concern language in the filing | Direction YES, magnitude corrected upward |
| "85% of FY guide contracted" | Searched the Q2 press release | **The 85% figure is not in the Q2 PR** — it is call/deck language. Red's numerator construction is therefore unverified, though the mechanism is sound | Mechanism YES, the specific number **NO** |
| Gross margin 52%→38% proves mix erosion toward low-margin revenue | Cost-of-revenue detail | Cost of revenue rose to $11.89M from $9.81M on 6% *lower* revenue — the signature of writing off a cancelled build, which the company states outright. Normalized margin is unknown | **NO — unproven either way** |
| The August awards (~$39M: NOAA, EUMETSAT) mean the tape ignored good news | Timeline check | Red netted an April event against August awards to explain a decline that happened 25 Aug–1 Sep. The resale registration is the better explanation | **Red's edge claim OVERTURNED on chronology** |
| Live price | IBKR gateway | **Neither bench pulled its own quote.** Both inherited the pack's $12.04; MCP price tools were permission-denied for red | **NO — coverage gap on both sides** |
| Blue's own load-bearing inference | Self-flagged | Spire never quantified the WildFireSat RPO removal. Blue's 73%-of-decline attribution rests on band concentration and magnitude consistency, not on a company disclosure | **Blue states this is the single thing the Q3 print settles** |

Bench conviction: red 9/10 on its kill case, blue 7/10 on "deferred, not dead."

## PROPOSED ENTRY BANDS

**No entry. There is no price near $12.04 at which either bench would stage a starter today.** The following are reopen conditions, not orders. Nothing is to be placed before the November print.

**Reopen gate — fundamental (all three must clear, on the Q3 10-Q):**
- RPO **≥ $130M** total, *and*
- the **0–12 month band ≥ $50M** (this is the test that separates "WildFireSat was the whole story" from "the near book is draining too"), *and*
- Q3 revenue **≥ $20M**.

Any one of these failing → the file is dead, not deferred, and does not get re-courted on a subsequent print.

**Red bench's stricter bar, recorded because the adjudicator may prefer it:** RPO back above **$170M**, H2'26 revenue **≥$46M** with Q3 **≥$22M**, an operating cash flow quarter better than **−$15M**, and the 10-Q footnote showing the Q2 decline was ≥80% WildFireSat de-scoping. Red would not enter on blue's bands.

**If the gate clears:**
- Size: **0.3–0.5% of book**, starter only. Hard cap at 0.5% until a full year of post-raise cash flow exists — this is the termination-for-convenience tail from the pre-mortem, which we cannot instrument and can only size against.
- Staging: **into resale-block exhaustion, not before it.** No bid while the 8.2M registered shares are visibly working (persistent 424B3-linked supply, clustered Form 4/144 activity). We do not have visibility into the block's remaining size, so this is a judgment call at the time, made explicit rather than assumed away.
- Re-run the roof table at the then-current price before any order. At 5x forward sales the fully-funded 2027 bull case is roughly **$12.69** and the 6x case roughly **$15.18**. Entry only makes sense if the tape leaves ≥40% to the $15.18 case, which implies a purchase price around **$10.80 or below** after a clean print — not a chase into a relief rally.

**Reference levels (information gates, not buy triggers):**
- **$14.00** — the April placement strike. Above it the block turns profitable and registered supply should *accelerate*. Any "the overhang is exhausted" entry logic is invalidated above this line.
- **$9.00** — block ~36% underwater; the funded mid case would offer ~+40%. Reopens the file for a pre-print look; still not a buy while the near-band question is open.
- **$6.60** — the 52-week low. A breach reads as financing distress and forces re-underwriting the 2027 raise at a punitive price. This is a *do-not-catch* level, not a dip.

**Catalyst dates:**
- **2026-11-12 — Q3 results and 10-Q. UNCONFIRMED.** This date is vendor-derived (yfinance); no Spire press release names it. Q2 was 12 August 2026 per 8-K 0001193125-26-346835. Confirming this date is itself an open task. It is ~49 trading days out — not print-proximate, so no reconstruction discipline is triggered and the pre-print position is FLAT.
- **~Q1 2027 — modeled cash exhaustion / raise window.** Not a dated event; a drift.
- The resale block has **no expiry** — it is live now, continuously.

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- price alert: fires below 6.6 (deck-provisional: 52-week low breach reads as financing distress into a 2027 raise — do-not-catch, not a dip)
- filing watch: 10-Q until 2027-03-01 (deck-provisional: extract RPO total and the 0-12 / 13-24 / 25-36 month bands — the entire reopen gate is three numbers i)
- dated pack SPIR|2026-11-12: SPIR: Q3 2026 results and 10-Q — the single print that settles the WildFireSat/RPO reconciliation and the reopen gate (RPO >=$130M, 0-12mo b
- dated pack SPIR|2027-03-31: SPIR: modeled cash-exhaustion point at H1'26 burn rates; equity raise window opens ahead of it (date confirmed=False)


## What remains unverified

- **The load-bearing inference.** Spire never quantified how much RPO WildFireSat removed. The 73% attribution is an inference from band concentration and magnitude consistency. If it is wrong, the demand leg really is decaying and the red bench was right.
- **The 85% coverage claim's source and numerator** — absent from the Q2 press release; the mechanism is verified, the specific figure is not.
- **Normalized gross margin.** The 38% print is contaminated by cancellation write-offs. We do not know what the underlying margin is.
- **Direction of the six Form 4s and the Form 144** (24–25 August). Neither bench examined them. They immediately precede a −9.4% day.
- **Peer multiples.** The entire roof argument holds 4.95x constant with nothing to anchor it against.
- **Short interest and peer-drawdown decomposition** — how much of the −53% from the high is SPIR and how much is the space/small-cap cohort.
- **Named-customer concentration.** The 10-Q discloses geographic concentration only. Customs and bill-of-lading triangulation has no rail here — Spire ships no physical goods — so the termination-for-convenience tail cannot be sized by counterparty.
- **Remaining size of the resale block.** Central to staging, and not observable.
- **Whether $12.04 was the actual tape.** Inherited, not independently pulled.

Primary sources: [Q2'26 10-Q](https://www.sec.gov/Archives/edgar/data/0001816017/000119312526347865/spir-20260630.htm) · [Q1'26 10-Q](https://www.sec.gov/Archives/edgar/data/0001816017/000119312526222710/spir-20260331.htm) · [Q2'26 results press release](https://ir.spire.com/news-events/press-releases/detail/309/spire-global-announces-second-quarter-2026-results) · [WildFireSat termination, SpaceQ](https://spaceq.ca/government-of-canada-terminates-spire-global-canadas-72-million-wildfiresat-contract/) · [Kpler maritime sale close, $241M](https://spacenews.com/spire-global-closes-stalled-241-million-maritime-sale/) · XBRL concepts at `data.sec.gov/api/xbrl/companyconcept/CIK0001816017/`.

```json
{"price_gates": [{"level": 14.0, "direction": "above", "basis": "April placement strike; block turns profitable and registered supply should accelerate — invalidates any overhang-exhausted entry logic"}, {"level": 10.8, "direction": "below", "basis": "leaves >=40pct to the 6x funded-prize case of $15.18; the only price at which a post-print starter has adequate asymmetry"}, {"level": 9.0, "direction": "below", "basis": "PIPE block ~36pct underwater and funded mid case offers ~+40pct — reopen the file for a pre-print look, not a buy"}, {"level": 6.6, "direction": "below", "basis": "52-week low breach reads as financing distress into a 2027 raise — do-not-catch, not a dip"}], "event_gates": [{"forms": ["10-Q"], "why": "extract RPO total and the 0-12 / 13-24 / 25-36 month bands — the entire reopen gate is three numbers in this footnote"}, {"forms": ["8-K"], "why": "guidance revision, financing, or another contract termination for convenience"}, {"forms": ["S-3", "S-3ASR", "424B3", "424B5"], "why": "new registration or an actual ATM would re-arm the 20.2pct overhang and change the dilution assumption in the roof table"}, {"forms": ["4", "144"], "why": "insider and affiliate supply clustering, as on 8/24-8/25 immediately before the -9.4pct day"}], "catalyst_dates": [{"date": "2026-11-12", "what": "Q3 2026 results and 10-Q — the single print that settles the WildFireSat/RPO reconciliation and the reopen gate (RPO >=$130M, 0-12mo band >=$50M, revenue >=$20M)", "confirmed": false}, {"date": "2027-03-31", "what": "modeled cash-exhaustion point at H1'26 burn rates; equity raise window opens ahead of it", "confirmed": false}], "immediate_entry": null}
```