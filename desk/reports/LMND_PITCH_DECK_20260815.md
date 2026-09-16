Both benches landed REJECT — no position either way — so this deck is a no-entry deck with reopen conditions rather than entry bands. Writing it now from the court record. (One admin note: the claude.ai Gmail/Calendar/Drive connectors still need authorization in your claude.ai connector settings before those tools work in these sessions; IBKR market-data calls were also permission-denied in both benches, which the deck flags as an open gap.)

---

# PITCH — LMND — PROPOSED VERDICT (PROPOSED — PENDING ADJUDICATION): REJECT — no position, long or short; re-open the case five trading days before the confirmed Q3 earnings date

## What we believe

Lemonade the business is genuinely improving, and we should say so plainly: the adjusted operating loss halved year-over-year (−$18.7M this quarter vs −$40.9M a year ago), and real cash flow — the plain GAAP kind, not the company's adjusted version — improved from −$41.7M to −$4.0M for the first half. The second half of 2025 already produced +$25.2M of GAAP operating cash. This is not a company hiding deterioration behind adjusted metrics; the two measures are converging, in the right direction.

What we do *not* believe is that we have any information advantage today. The entire investment question hinges on one promise: management held its full-year loss guidance, which arithmetically requires the fourth quarter to swing from a −$19M quarterly loss to roughly +$8M positive — their own stated number. That swing has to happen across a hurricane-season third quarter in which the company *chose* to keep more of its own catastrophe risk (it cut the share of premiums passed to reinsurers from ~20% to ~18%, effective July 1). The single best analytical point either bench made: keeping more premium is not outside validation of the business — it's management leaning harder into its own promise, which *widens* the range of outcomes in exactly the quarters the promise must be kept. The extra retained premium is only ~$7M per quarter, but the tail risk it retains is hurricane-shaped.

So: improving business, one clearly-dated make-or-break event ~55 trading days away, and nothing we know that the market doesn't. That's a calendar reminder, not a trade.

## What the market believes

The market is bearish and crowded-bearish. The stock is at $52.64, down 47% from its 52-week high of $99.90 and only 14% above its 52-week low, after falling 24% on the July 29 earnings day despite an improved loss ratio ([The Insurer](https://www.theinsurer.com/ti/news/lemonade-share-price-drops-over-20-despite-improved-q2-loss-ratio-new-cfo-named-2026-07-29/)). Roughly 27–30% of the freely-trading shares are sold short. The bear story — guidance merely held rather than raised, profitability defined on an adjusted basis that excludes stock compensation, a CFO transition announced the same day — is thoroughly public and thoroughly positioned-for. The stock trades at roughly 3.35× this year's guided revenue, a valuation nobody in this court verified as fair or unfair.

## Why we might have edge

Honestly: today, we don't, and the court's core finding is precisely that. What *could* become edge, and is worth the re-court:

1. **The Q4 hinge is checkable before the market checks it.** Five days before the Q3 print, we can reconstruct retained hurricane-season losses (state-by-state catastrophe exposure × the new 18% retention) and bridge premium-in-force to earned revenue. If that reconstruction says the +$8M Q4 promise is safe or dead, we'd know something the price may not reflect.
2. **The short side is a coiled spring for a long.** With 27–30% of the float short, a clean Q3 plus a confirmed Q4 swing to profit would force heavy short-covering. That mechanical fuel benefits a long entered *before* confirmation — but only if the reconstruction gives us a real reason to believe.
3. **Free leading indicators exist and aren't wired.** App-store review velocity is a usable early read on customer growth ahead of the print. Nobody — us included — has it armed yet.

## Why it might be priced in

The mirror image, stated with equal weight: every bearish fact we found is already consensus and already positioned (that 27–30% short interest cuts both ways — it means "the quarter was worse than the headline" is not news to anyone). Our checks found *no hidden damage at all*: the insider selling dissolved into two officers selling under $700k combined of routine option-exercise stock, and the "adjusted cash flow vs real cash flow" gap turned out to be a disclosed financing-program add-back with GAAP converging toward the adjusted number, not away. When a thorough hostile search finds no concealed problems, the remaining bull case is just management's own promise — which is center-stage in every analyst note and priced by people watching the same calendar we are. And a large piece of the price action remains unexplained: the stock fell ~37% from January to July *before* the earnings drop, and neither bench decomposed that leg (our brokerage data access was denied in both sessions). Buying ahead of understanding that move would be guessing.

## What we checked ourselves

| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| Evidence-pack financials current | Cross-checked pack's XBRL against live SEC data | **Pack was four quarters stale** — its "newest" revenue row was Q2-2025; share count 73.4M vs actual 77.4M. Both benches caught it; all math below uses live SEC data | ✗ pack erred; corrected |
| "Unresolved insider selling" supports caution | Pulled the actual Form 144s and Form 4s from [SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1691421/000195917326005978/primary_doc.xml) | Two officers, <$700k combined, routine option-exercise cadence predating the earnings drop. **Red bench erred first**: called it "one officer" — the 07-06 notice was actually Timothy Bixby, the departing CFO ($118k — noise). Blue corrected the identity; materiality ruling stood | ✓ claim refuted |
| Adjusted cash flow masks GAAP losses | Live [SEC XBRL operating-cash-flow series](https://data.sec.gov/api/xbrl/companyconcept/CIK0001691421/us-gaap/NetCashProvidedByUsedInOperatingActivities.json) | H1-26 GAAP −$4.0M vs −$41.7M prior year; H2-25 was **+$25.2M**. GAAP is converging toward the adjusted metric, not diverging. The gap is a disclosed financing add-back. One honesty footnote: adjusted free cash flow *fell* year-over-year while marketed as a "5th consecutive positive" quarter | ✓ masking refuted; footnote logged |
| Q4 must swing to ~+$8M for guidance to hold | Company's own Q2 report and call transcript | Confirmed — management states it themselves. Cession cut 20%→18% raises retained hurricane-quarter variance (~$7M/qtr extra retained premium) | ✓ |
| 27–30% short interest kills any trade | Three independent short-interest sources | Level confirmed (and falling: 15.3M→14.1M shares). **Red bench erred second**: applied our crowding test as if we were shorting — high short interest is squeeze fuel *for* a long, not proof a long is priced in. Blue reduced it to sizing/path-variance color | ✓ level; ✗ red's inference |
| Dilution ~5.6%/yr | [SEC XBRL shares outstanding](https://data.sec.gov/api/xbrl/companyconcept/CIK0001691421/dei/EntityCommonStockSharesOutstanding.json) | 74.73M (Nov-25) → 77.40M (Aug-26) ≈ **4.8%/yr**; the original thesis mixed two different share-count bases | ✓ direction, ✗ magnitude |
| Nov 4 earnings date | Derived from a data vendor only | **No company announcement names it. Unconfirmed** | ✗ unverified |
| Jan→Jul −37% price leg explainable | Attempted brokerage price history, both benches | Permission denied both times; the court closed with its largest price move never decomposed | ✗ open gap |

## PROPOSED ENTRY BANDS

The court says **no entry at any price today** — the findings are timing findings, and our discipline routes timing to tripwires, not to standing buy limits. There is deliberately no "buy if it gets to $X" level: with no view on direction, a bare price trigger would just buy weakness blind. The reopen bands, from the benches' own math:

- **Primary reopen: confirmed Q3 earnings date minus 5 trading days** (≈ 2026-10-28 if the unconfirmed Nov 4 date holds). Required homework at reopen: (1) retained catastrophe-loss reconstruction — state exposure mix × the new 18% retention; (2) premium-in-force to earned-revenue bridge; (3) decompose the January→July −37% leg (needs working brokerage data access). Only after those three does the long-starter-vs-flat sizing question get asked.
- **Early reopen (bullish path): short interest below ~15% AND a GAAP-operating-cash-positive quarter** — red bench's own stated mind-changer; revives a long on an uncrowded, GAAP-confirmed basis.
- **Early reopen (bearish path): a genuine insider-selling cluster** — any filer selling more than 1% of their own holdings, or multiple officers post-print. Today's <$700k routine sales explicitly do *not* qualify.
- **Early reopen (honesty path): any change in how "adjusted free cash flow" is defined** between quarters — would convert the current footnote into a real integrity finding.
- **Informational only, not an entry: a close below the 52-week low of $46.16** — triggers the price-leg decomposition immediately rather than waiting for the re-court window.
- **Sizing:** zero now. If the re-court sustains a long, it enters as a starter position sized at adjudication — this deck pre-commits no number.
- **Catalyst dates:** Q3 earnings ~2026-11-04 (**unconfirmed** — vendor-derived, no company PR); re-court ≈ 2026-10-28 (derived from it).

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- price alert: fires below 46.16 (deck-provisional: 52-week-low break: triggers immediate decomposition of the undecomposed Jan-Jul price leg, information)
- filing watch: 8-K until 2027-02-11 (deck-provisional: company PR/8-K naming the Q3 earnings date starts the re-court clock (print minus 5 trading days))
- dated pack LMND|2026-11-04: LMND: Q3 earnings — the +$8M Q4-swing guidance hinge; vendor-derived date (date confirmed=False)
- dated pack LMND|2026-10-28: LMND: re-court window opens (print minus 5 trading days, derived from unconfirmed print date) (date confirmed=False)


## What remains unverified

- **The Q3 earnings date itself** (Nov 4 is vendor-derived; no company source). The entire reopen schedule hangs on it.
- **The January→July −37% price decline** — never decomposed; brokerage data access was permission-denied in both bench sessions and must be fixed before the re-court.
- **Whether ~3.35× guided revenue is a fair price** — no bench did valuation work; "no hidden damage" is not the same as "attractively priced."
- **The insured book's state-by-state catastrophe mix under the new 18% retention** — the exact variance that decides the Q4 promise; requires statutory filings work at re-court.
- **Live tradeable quote** — all prices herein are the pack's vendor close ($52.64), not a live broker quote.

```json
{"price_gates": [{"level": 46.16, "direction": "below", "basis": "52-week-low break: triggers immediate decomposition of the undecomposed Jan-Jul price leg, informational not entry"}], "event_gates": [{"forms": ["8-K"], "why": "company PR/8-K naming the Q3 earnings date starts the re-court clock (print minus 5 trading days)"}, {"forms": ["4", "144"], "why": "insider cluster >1% of any filer's holdings or multi-officer post-print selling = bearish early reopen"}], "catalyst_dates": [{"date": "2026-11-04", "what": "Q3 earnings — the +$8M Q4-swing guidance hinge; vendor-derived date", "confirmed": false}, {"date": "2026-10-28", "what": "re-court window opens (print minus 5 trading days, derived from unconfirmed print date)", "confirmed": false}], "immediate_entry": null}
```