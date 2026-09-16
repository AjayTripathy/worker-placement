# The Sovereign Barbell — the "Risk Mitigation" doc, run as a hedge fund
*2026-08-07 revisit. Source: the shared planning doc (tangibles/intangibles/profit/wargames). Method: translate every line into fund-holdable form or explicitly park it as personal prep; red-bench the concept honestly; wire the one mechanizable signal today.*

## The mandate the doc already contains
A two-sided barbell: **(1) a tail sleeve** that survives US-asset-freeze / capital-control / hot-war scenarios with recoverable value abroad, sized so that **(2) the core book** can be run at full aggression — including buying panics ("be greedy when others are fearful") — because the tail is paid for. The doc's own profit section is the core mandate; its tangibles/intangibles list is the tail sleeve; its wargames are the scenario tests. That is a fund.

## Sleeve architecture

**Sleeve 1 — the aggressive core (≈75–85%).** This is the existing desk: courts, dislocation detection, orphan value across five jurisdictions. The doc's "buy the S&P when down on saber-rattling" is already doctrine here in sharper form — the cause-check discipline (beta-bleed vs dislocation; velocity → triage → court) exists precisely to distinguish saber-rattling dips (buy) from fundamental breaks (don't). No new machinery needed; the core is built and running.

**Sleeve 2 — jurisdictional survival (≈10–15%).** The doc's international ETFs/REITs/stocks/CHF, made fund-holdable with three hard rules:
- **Direct foreign lines, never foreign funds** — foreign ETFs are PFICs for US persons (the desk's standing trap catalog); the Japan/Korea/EU/LSE books we already run are the right instruments. The international value books double as this sleeve *if custody is arranged correctly*.
- **Custody venue ≠ listing venue** — the axis that matters in the freeze scenario. A Tokyo line held at a US custodian freezes with the custodian. Diligence item: split custody across a non-US IBKR entity or a second non-US prime; classify every position on three axes (issuer / listing / **custody** jurisdiction). New field for edge_classifications.
- CHF T-bills and allocated Swiss gold for ballast; BTC in geographically-split multi-sig cold storage as the only true bearer asset (the doc is right that it "just sits around" — that's the job).
- Honest history check: Swiss institutions have complied with US orders before. Sleeve 2 hedges *market and custodian* failure, not the reach of law upon the person. Nothing in a fund wrapper changes citizenship-based jurisdiction — everything stays reported and compliant (FBAR/8938/PFIC); the hedge is against freeze-by-chaos, not a tool against process.

**Sleeve 3 — the de-globalization gauge (signal, ~0% capital).** The doc's exchange-arbitrage line, mechanized: monitor dual-listed fungibility spreads (TSM/2330.TW, SHEL/SHEL.L, RIO/RIO.L, UL/ULVR.L, BP/BP.L) daily. These arbitrage to ~0 while capital moves freely; a sustained blowout beyond arb cost *is* the market pricing capital controls — no historical precedent required, exactly as the doc says. Wired today as `desk/fungibility_watch.py` (state + thresholds; ≥2% notable, ≥5% alarm). This is the fund's regime dial: sleeve sizes shift when the gauge moves, not when headlines do.

**Sleeve 4 — convexity (1–2%/yr premium budget).** The doc's survival-kit logic applied to markets: the tail sleeve as drawn is *linear* (it survives the tail; it doesn't pay for the reload). The "rebuy the new world" plan requires convex instruments: long-dated CHF/gold calls against USD, deep SPX tails timed to the gauge, duration for the deflationary branch. Budgeted as insurance, never graded as edge — carry cost stated annually, the way the doc prices chickens.

**Leverage policy (the doc's best financial idea):** "borrow USD, repay in inflated dollars" translates to **term, fixed-rate, non-callable liabilities only** — leverage that cannot be margin-called in the exact scenario it's designed for. No repo, no callable lines. The safe-harbor tax float (110% of prior year, invest the difference) is legitimate personal cash management, not fund structure — and per the doc's own footnote, confirm with a tax attorney; the withholding-to-zero variant is not that.

## Scenario map (the doc's wargames → sleeves)
| Wargame | Answer |
|---|---|
| US assets frozen, person free | Sleeve 2 custody abroad + BTC; recovery value per position is a tracked field |
| Internet down / intranets | Ops, not portfolio: the desk is already local-first (SignalOS runs on a laptop); add offline replicas of books/records + the doc's local-LLM node — the "Oracle" bullet is an ops-resilience line item, and the comment thread's local-LLM build is exactly right |
| Exchanges float apart (TSMC) | Sleeve 3 detects it; sleeve 2 already holds the local lines, not the ADRs |
| Martial law / enemy-of-state | Governance: offshore administrator, independent directors, split custody — and the honest limit above |
| War with a nuclear state | Sleeve 4 pays; sleeve 2 survives; core reloads per the doc's "be greedy" |

## Parked as personal prep (not fund assets)
Health, skills, kits, armor, chickens, boats, planes, NZ bunkers, the SF blast table, land-as-refuge (though the doc's conservation-easement instinct just proved out at Woods Lane as *permit currency* — same tool, different game). Guns: the doc's own ambivalence is the answer. Gold in a go-bag is personal; vaulted allocated gold is fund.

## Red-bench honesty (what kills or bounds the concept)
1. **Carry drag is the certain cost**: sleeve 2 underperforms the base case (FX drag, withholding, custody fees) and sleeve 4 bleeds premium — in the likely world this fund trails a naive book by the insurance bill. That's the price of the barbell; state it, don't hide it.
2. **Linear hedges don't reload**: without sleeve 4's convexity the doc's "rebuy at the beginning of the new world" is underfunded — survival ≠ dry powder. This was the doc's one structural gap.
3. **Correlation in the true tail**: foreign custodians comply, exchanges close together, and the only assets that clear are bearer (BTC keys, vaulted metal) — so the bearer fraction, small as it is, is the real backstop and carries its own key-loss/duress risks.
4. **The gauge can false-positive** (ADR fees, FX settlement quirks, index events) — thresholds are set above arb-cost noise, and any firing gets a cause-check before sleeves move. Detector discipline: narrow and high-precision, per the union doctrine.

## What runs today
The desk already operates the core (sleeve 1), holds the raw material for sleeve 2 (HSBK.L, EDINET/DART books, EU orphans — pending the custody-axis classification), and as of tonight runs sleeve 3 (`fungibility_watch`). Sleeve 4 and the custody split are the genuine new builds — sized, budgeted, and gated like any other court decision.

## Addendum — the convex-carry sleeve (principal, 2026-08-07)
Sleeve 4's fix: instruments that PAY in the base case and are STRUCTURALLY convex in the tail. Three species pass: (1) event-putted credit near par (the FUBO-2029 pattern — contractual par exit on the crisis event; taxable-book haircut ~50% on the coupon, so wrapper-dependent); (2) real-asset operators whose cash flows spike in crisis — tankers, LNG, defense/sovereign-infrastructure backlog (qualified-dividend carry at 23.8% = tax-preferred; ETL already held is this species); (3) trend replication (sleeve decision, not a court). Failing the test: cat bonds (tail IS the impairment), EM FX carry (tail-short), all short-vol (banned anyway). The one-question test: does the crisis RAISE the instrument's cash flows? Courtable candidates FRO/INSW/WPM/SAAB-B.ST enqueued to the conveyor 2026-08-07 with species-specific trap checks (carry-at-mid-cycle, crowding gates); each faces the standard rigor — carry graded RP_FAIR only if fairness verifies, convexity priced as the option it is.

**Sleeve update 2026-08-08 — the timing axiom, learned by verification:** the trap layer killed all three species-2 candidates. FRO's verdict is the doctrine: Hormuz closed in March, VLCC rates printed all-time highs, and the 'convex carry' on offer was post-crisis carry at 1.6x NAV with management time-chartering OUT the spike. AXIOM: species-2 convex carry requires the convexity UNFIRED — after the event, crisis-cashflow operators are cyclical beta at the highs (mid-cycle carry test: FRO 3.4-5%). The sleeve buys tail exposure where the tail premium is ABSENT, or it buys nothing. Live candidates tonight: the FUBO 2029 event-putted convert (species 1, in court); SAAB retrying (crowding gate = the same axiom for defense). Screen fixes filed: INSW/WPM geo/venue mis-tags; conveyor US-branch bug fixed.

**Sleeve verification complete 2026-08-08 — species-2 slate 0-for-4:** SAAB killed on the crowding gate (48x trailing, 0.38% yield — 'the carry premise does not exist'), joining FRO/INSW (post-Hormuz, 1.6x NAV) and WPM. META-FINDING: every listed crisis-cashflow operator is already re-priced for its tail — the market agrees with this memo's worldview, which is precisely why the sleeve cannot be built from listed operators today. Standing state: species-1 carries the sleeve (FUBO 2029 convert survived court as the only ownable expression — pending an access/liquidity screen), species-3 (fungibility gauge) watches for the regime turn, and species-2 stays EMPTY until a tail is found unfired. An empty sleeve at honest prices beats a full sleeve at fired ones.

## Wave 2 — the fired/unfired map (2026-08-08, principal-directed expansion)
The timing axiom applied to the whole war-convexity universe:

| Tail cluster | State | Evidence | Sleeve action |
|---|---|---|---|
| Gulf chokepoint (crude/product tankers, LPG) | **FIRED** (Hormuz closed Mar-26; VLCC ATH $423k/day) | FRO/INSW kills | Band-watch re-entry only (FRO $18-22, INSW conditional) |
| European defense | **FIRED** (rearmament re-rate; SAAB 48x/0.38%) | SAAB kill | Excluded; BAE courted as the possible carry-leg exception |
| Precious-metals margin | **FIRED** (WPM margin +65% y/y at record gold) | WPM kill | Convexity-frame re-entry at $95 w/ conditions |
| US defense primes | **plausibly UNFIRED** (lagged Europe badly; LMT ~16-17x after fixed-price charges) | courting | LMT trap-verify dispatched |
| Ag/potash/grain | **RE-SET** (2022 spike fully deflated — a tail that reloaded) | courting | NTR + BG dispatched |
| US export midstream | **carry-first, convexity partially REALIZES in cash flows** (arbs widen on disruption without needing a re-rate) | courting | EPD + ET dispatched (ROC tax-deferral = taxable-book-native carry) |
| LNG carriers | **CONTESTED** — newbuild glut vs Qatar-through-Hormuz; the courts' first task is establishing which force won | courting | FLEX + CLCO dispatched with the rate-state verification mandatory |
| Species-1 event credit | n/a (contractual, non-decaying) | FUBO court | The 2029 convert — access/liquidity screen owed |

All eight wave-2 trap-verifies dispatched 2026-08-08 with the timing axiom as a hard gate and retry-once-with-feedback inline.

## Convexity theses beyond war (2026-08-08)
| Thesis | Tail state | Carry leg | Instrument | Status |
|---|---|---|---|---|
| AI-disappointment (displaced-quality longs = cheap calls on AI underdelivering) | UNFIRED — nobody positioned for it | FCF/buybacks at 5-8% yields | The existing dislocation-court book: TEAM@126 gate, GTLB@31.50, DOCU billings gate, ADBE-class | ALREADY COURTED — reframe only |
| Yen mean-reversion via unhedged Japan value book | verify JPY level | net-net dividends (EDINET shelf) | Japan book held unhedged | Tag the book; one FX verification |
| Deflation/duration | UNFIRED (world positioned for inflation) | ~positive (curve) | long zeros/strips, small | Sleeve-4 sizing decision |
| Busted-convert screener (systematize FUBO: near-par + CoC puts) | manufactured on demand | coupons (wrapper-dependent) | screen EDGAR indentures × control-situation overlay | BUILD SPEC — highest value |
| Litigation revival (BUR: YPF marked ~zero post-reversal) | binary, unpriced | portfolio realizations at 1.38x TBV | BUR equity | in queue (red retrying) |
| Pandemic-platform residue | deeply unfired, decade-scale | NEGATIVE (burn) | cash-rich platform survivors only, tiny | option-budget only; trap catalog applies |
| Ukraine peace (Step-Up B ~58c) | live | accrual structure | held framework position | existing precedent |
| REJECTED: grid (fired), uranium/SMR (courted+killed), gold miners (fired), index vol (bleed), CRE-distress (knife carry) | | | | |

**Wave-2 verdict (2026-08-08): 0-for-8, sleeve education complete — SPECIES-2 IS BOUGHT IN PEACETIME.** Mid-crisis (Hormuz live), every crisis-linked operator either carries the windfall in its run-rate (EPD: ~$200M/qtr — buying now = SHORT the reopening, payoff sign inverted), has re-rated (BA.L, LMT — even the 'lagging' US primes), decays against scheduled supply (NTR vs Jansen), or lacks the contingent leg entirely (ET -> plain-carry reroute). Plus two entity-resolution failures in our own enqueue (FLEX=electronics not LNG; CLCO dead) — the AIIO discipline now applies to sleeve enqueues too. Standing sleeve: species-1 (FUBO convert + the busted-convert screener build), species-3 (gauge), and NINE armed re-entry bands (FRO 18-22, INSW cond., WPM 95, BA.L 1700p, LMT 16x-cond., BG 80, NTR post-2028, FLNG corrected-entity in court) that constitute the PEACETIME SHOPPING LIST. The sleeve's job until the tails deflate: watch, don't reach.
