# COMMODITY COURT — ENERGY (OIL + NATGAS)
**Date:** 2026-08-14 · **Analyst:** SignalOS · **Question:** does COMMODITY-level energy exposure
(futures/ETPs) earn a slot the book's energy EQUITIES do not already fill?

**Book as held (IBKR poll, 2026-08-14 live):** XOM 64 sh @ $159.90 = $10,250 · SU 159 sh @ $65.90 =
$10,499 · EQT 95 sh @ $54.55 = $5,198 · short EQT Sep18'26 52.5 put ×1. Energy sleeve **$25,947 =
3.2%** of an ~$805k book (3.9% pro-forma if the put is assigned). Sleeve is **80% oil-levered
(XOM+SU) / 20% gas (EQT)**.

---

## VERDICT — SPLIT, and the split is the finding

| Leg | Score | Verdict |
|---|---|---|
| **NATURAL GAS commodity (NG futures / UNG)** | **1 / 10** | **DISQUALIFY.** Carry, fundamentals and the curve-vs-forecast gap all point the same way. |
| **OIL commodity (CL futures / USO)** | **4 / 10** | **NOT REDUNDANT — but badly timed.** Real, proven tail mechanism the equities do not deliver; wrong entry price today. |
| Net recommendation | — | **No new commodity position today.** Keep the equity expression. Revisit oil on the trigger in the catalyst table. |

The headline instruction assumed both legs would die of roll bleed. **Half of that is wrong, and the
wrong half is the interesting half.** Oil's curve currently *pays* a long; gas's *charges* one. The
oil leg dies for a different reason than expected, and it dies only on price, not on merit.

---

## MODE B — FIRST PRINCIPLES (leading, per doctrine)

Ignoring the framing entirely, three questions decide this. Two of them invert the received wisdom.

### B1. "Commodity ETPs bleed from contango" is a stale generalisation. Check the actual curve.

**Curve source: NYMEX settlement prices for 2026-08-14, pulled per-expiry from IBKR historical bars
(`get_price_history`, FUT, ONE_DAY, exchange=NYMEX).** Live futures quotes were **blocked — the
account has no NYMEX market-data entitlement** (snapshot returns open interest only). Settles are
the authority used throughout; labelled as such.

**WTI (CL), $/bbl — steep BACKWARDATION**

| Expiry | Settle | vs front |
|---|---|---|
| Sep-26 (front) | 82.27 | — |
| Oct-26 | 81.43 | −1.0% |
| Dec-26 | 78.39 | −4.7% |
| Jan-27 | 76.98 | −6.4% |
| Jun-27 | 72.79 | −11.5% |
| **Sep-27 (12mo)** | **71.44** | **−13.2%** |
| Dec-27 | 70.55 | −14.2% |
| Dec-28 | 68.01 | −17.3% |

Static-curve roll yield to a long: **+15.2%/yr**.

**Henry Hub (NG), $/MMBtu — steep CONTANGO**

| Expiry | Settle | vs front |
|---|---|---|
| Sep-26 (front) | 2.721 | — |
| Dec-26 | 3.538 | +30.0% |
| Jan-27 | 3.951 | +45.2% |
| Mar-27 | 2.927 | +7.6% |
| Apr-27 | 2.805 | +3.1% |
| **Sep-27 (12mo)** | **3.210** | **+18.0%** |
| Dec-27 | 4.183 | +53.7% |
| Jan-28 | 4.630 | +70.2% |

Static-curve roll yield to a long: **−15.2%/yr**. Winter-to-winter Jan-27 → Jan-28: **+17.2%**.

**Realised, not theoretical — 5yr (Aug-2021 → Aug-2026, IBKR monthly closes):**

- **USO +163.3%** vs WTI front ~$68.00 → $82.27 = **+21.0%**. Excess **+117.6% cumulative =
  +16.8%/yr** of roll + T-bill collateral. The oil ETP *beat the commodity by 2.4×*.
- **UNG −83.8%** vs Henry Hub ~$4.00 → $2.721 = **−32.0%**. Shortfall **−76.2% cumulative =
  −24.9%/yr** structural drag. UNG destroyed three-quarters of capital *independent of price
  direction*. (UNG also did a 1-for-4 reverse split 2024-01-23 — USCF fund page.)

**Finding:** the roll-bleed disqualification is **REFUTED for oil, CONFIRMED and severe for gas.**

### B2. Is the oil backwardation a real physical signal, or a speculative risk premium?

Real — and the cause is dated and enormous.

**Authority: EIA Short-Term Energy Outlook, released 2026-08-11** (`eia.gov/outlooks/steo/`, global
oil section):

- Strait of Hormuz throughput collapsed from **21.6 mb/d pre-conflict (Q4-2025) to 4.9 mb/d in
  Q2-2026** — a 77% reduction.
- **Production shut-ins averaged 5.5 mb/d in July 2026.**
- OPEC liquids output **29.3 (2025) → 24.0 (2026) → 29.7 mb/d (2027)**.
- Global inventories drew **4.2 mb/d in Q2-2026**, another **3.8 mb/d expected in Q3-2026**.
- US commercial crude inventories forecast to **stay below the 5-year LOW through end-2026**.

So the backwardation is corroborated by physical draws, not sentiment. **But the same authority
kills the trade's edge:** EIA expects Hormuz flows to rise **from September 2026**, most shut-in
production restored by **Q1-2027**, and forecasts **Brent $87 (2026) → $69 (2027)**, with Q3-26 $85
and **Q4-26 $78**.

**The forward curve and the EIA agree.** CL Sep-27 at $71.44 vs EIA Brent 2027 $69 is the same view.
That is the decisive point: **the +15.2% carry is not free money — it is exactly the compensation
for the risk that Hormuz reopens on schedule.** Buying the strip today is a bet *against* the
reopening, priced fairly. That is a risk premium, not an edge.

And the timing is poor in a way the carry doesn't fix: **we are ~10 months into the disruption and
past the spike.** USO already ran $81.95 (Feb) → $147.09 (Apr) and has retraced to $126.49. Buying
supply-disruption insurance after the disruption has fired, at a front price ($82.27) 21% above
where the market says normal is ($68.01, Dec-28), is the classic late-hedge error.

### B3. Is the AI-datacenter gas thesis in the data, or only in the pitch?

**It is in the curve, and the operating data is moving the other way.** This is a textbook
marketed-takeaway-vs-data divergence.

**Authority: EIA STEO 2026-08-11, natural gas section, and EIA Weekly Natural Gas Storage Report
for week ending 2026-08-07 (released 2026-08-13):**

- **US dry gas production 111.19 Bcf/d (2026) → 116.04 Bcf/d (2027)** — record and rising.
- **Storage 3,153 Bcf, +198 Bcf / +6.7% ABOVE the 5-year average.** EIA projects **3,985 Bcf by
  end-Oct 2026 — the highest level heading into winter since 2016**, ~5% above the 5-yr average.
- **Henry Hub forecast $3.44 (2026) and $3.31 (2027) — both REVISED DOWN** (from $3.67 and $3.49).
  Q3-26 forecast $2.87.
- LNG exports 17.4 (2026) → 18.6 Bcf/d (2027); 3Q26 only 16.5 Bcf/d on Freeport maintenance.
- **The datacenter leg took a direct hit: "On August 3, the Texas governor announced a pause on new
  data center development, and as a result, we have lowered our forecast for electricity demand in
  Texas." EIA cut Texas load growth from 14% to 6% for 2027.**
- Gas share of generation flat at **40% in both 2026 and 2027** (down from 42% in 2024).

Now set that against the curve: **Dec-27 $4.183 and Jan-28 $4.630 sit far above EIA's $3.31 average
for 2027.** The market is paying up for the structural AI/LNG story precisely as the sponsoring
agency revises the demand side *down* and the supply side *up*.

**Finding:** to own gas at the commodity level you would pay **−15.2%/yr carry** to express a
consensus view **already embedded above the official forecast**, against record supply, the highest
pre-winter storage in a decade, and a policy setback in the single most important datacenter state.
**DISQUALIFY.** This is the clean, high-confidence half of the verdict.

---

## MODE A — CLAIM VERIFICATION

| # | Claim under test | Method / authority | Finding |
|---|---|---|---|
| 1 | Book already expresses energy via equities | IBKR `get_account_positions`, 2026-08-14 | **VERIFIED.** $25,947 = 3.2% of book; 80% oil / 20% gas |
| 2 | USO/UNG are K-1 partnerships | USCF fund pages; USO 10-K FY2025 (acc. 0001104659-26-021501, filed 2026-02-27) | **PARTIALLY VERIFIED / K-1 UNVERIFIED.** Both confirmed Delaware LPs and CFTC commodity pools. One USCF page asserted USO does *not* issue a K-1; the 10-K text retrieved contained no "Schedule K-1" language either way, and USCF separately brands SDCI the "No K-1 Fund" (implying the others do). **Contradictory — logged UNVERIFIED. Not load-bearing:** see note below |
| 3 | USO holds front-month WTI and rolls monthly | USO 10-K FY2025, quoted | **VERIFIED.** "Each month over a five-day period, USO changes the Benchmark Oil Futures Contract... that is the near or front month to expire... into the NYMEX futures contract that is the next month contract to expire." Roll shortened from 10-day to 5-day effective 2026-01-01 |
| 4 | Roll structure materially affects ETP return | USO 10-K FY2025, quoted | **VERIFIED — company-admitted.** "natural market forces called contango and backwardation may impact and have impacted the total return on an investment in USO's shares relative to a hypothetical direct investment in crude oil" |
| 5 | USO fees/size | USCF fund page, 2026-08-13 | **VERIFIED.** Total expense ratio **0.86%**; net assets **$2,076,873,746** |
| 6 | UNG fees | USCF fund page | **VERIFIED.** Mgmt fee 0.60% of NAV to $1bn, 0.50% above |
| 7 | Oil ETPs bleed from contango | NYMEX settles + 5yr realised return | **REFUTED for the current regime.** +16.8%/yr structural GAIN |
| 8 | Gas ETPs bleed from contango | NYMEX settles + 5yr realised return | **VERIFIED, severe.** −24.9%/yr structural drag |
| 9 | Futures get §1256 60/40 treatment | IRS instructions not reached within fetch budget | **UNVERIFIED.** Standard treatment for regulated futures contracts is well established but was not confirmed against a primary IRS source in this run — confirm before any tax-driven sizing |
| 10 | CME margin levels for CL/MCL/NG/MNG | not reached within fetch budget | **UNVERIFIED** |

**On the K-1 gap:** it does not move the verdict in either direction. Gas is disqualified on the
roll math (−24.9%/yr) and the fundamentals, which no tax form rescues; oil is deferred on entry
price and redundancy, which no tax form worsens. If oil is ever taken, resolve the K-1 question
first — but it is a sizing/vehicle detail, not the decision.

---

## THE REDUNDANCY QUESTION — the strongest finding in this court

The brief's premise is that "energy is ALREADY expressed via equities." **The tape refutes that for
the tail, and confirms it for the trend.** Both halves matter.

### Test 1 — total return over 5 years: the EQUITIES WIN

| Instrument | 5yr price | + divs (at current yield) | ≈ total |
|---|---|---|---|
| **SU** | +253.0% | +13.3pp | **~+266%** |
| **XOM** | +193.4% | +13.6pp | **~+207%** |
| **EQT** | +197.5% | +6.1pp | **~+204%** |
| USO | +163.3% | none | +163% |
| SPY | +71.9% | +5.8pp | ~+78% |
| **UNG** | **−83.8%** | none | **−84%** |

Over the window where the oil curve delivered its **maximum** positive carry, **all three equities
still beat the commodity** — before counting that USO pays no dividend and adds a tax-reporting
wrapper. For *return*, the commodity is redundant. Confirmed.

### Test 2 — the actual supply shock: the EQUITIES FAILED

Feb-2026 → Apr-2026 peak, the one event that tested the hedge:

| | Feb-26 | Apr-26 | move | **capture vs USO** |
|---|---|---|---|---|
| **USO** | 81.95 | 147.09 | **+79.5%** | — |
| SU | 56.52 | 68.46 | +21.1% | **26.6%** |
| XOM | 152.50 | 154.33 | **+1.2%** | **1.5%** |
| EQT | 61.42 | 60.08 | −2.2% | **−2.7%** |
| SPY | 685.99 | 718.66 | +4.8% | — |

**XOM captured 1.5% of the oil move. EQT captured negative.** The integrated majors are not a
crude-spike vehicle — high crude input costs compress their downstream/refining margins, and the
market refuses to capitalise a disruption it expects to reverse. SU, more upstream-weighted, managed
27%. Nothing in the sleeve delivers the tail.

### Test 3 — diversification and drawdown behaviour (60 monthly returns)

| | corr to SPY | corr in SPY-DOWN months | beta vs SPY | ann. vol | max DD |
|---|---|---|---|---|---|
| **USO** | **−0.01** | **−0.22** | −0.02 | 37.8% | −29.1% |
| XOM | +0.11 | −0.07 | 0.18 | 27.3% | −19.4% |
| SU | +0.17 | −0.04 | 0.33 | 31.4% | −30.7% |
| EQT | +0.23 | **+0.16** | 0.58 | 40.4% | −33.2% |
| UNG | +0.01 | −0.08 | 0.06 | 65.3% | **−92.2%** |

In the 12 worst SPY months (mean −5.9%): **USO mean +6.6% / median +3.5%**, positive 7/12 — the best
of the set. Excluding the 2026 shock months it still holds at **mean +2.1% / median +2.8%**, so the
result is not an artifact of the one event. XOM is comparable on the median (+3.2%) but, per Test 2,
only in ordinary drawdowns — not in the oil-driven one.

Note **EQT is the *worst* diversifier in the book**: correlation to SPY *rises* to +0.16 in down
months and beta is 0.58. It behaves like a levered equity, not like gas.

**Redundancy verdict:** the equities and the commodity are **complements, not substitutes**. The
equities are the superior *return* vehicle and dominate on 5-year total return. The commodity is the
*only* instrument in the set that pays in an oil supply shock, and is the only genuine
equity-diversifier (−0.22 in down months). The brief's premise is **half true — and the false half
is exactly the ballast use case the brief asked about.**

---

## BALLAST TEST FOR *THIS* BOOK

The book carries war-tail exposure (Ukraine sleeve, the WW3-doc tails) plus 31% in SGOV and a PHYS
gold ballast ($10,634). The mechanism for adding oil is genuine and specific: **a Hormuz
re-escalation is the single tail that would hit the Ukraine sleeve, the equity book and the FX book
simultaneously, and oil is the only asset here that pays into it — the equities demonstrably do
not (1.5% capture).**

Three things stop it from being actionable today:

1. **Price.** Front $82.27 vs Dec-28 $68.01. You are buying insurance 10 months into the claim, at
   21% above the market's own normal. The cheap window was Q3-2025.
2. **Direction of travel.** EIA expects flows rising from **September 2026** and restoration by
   **Q1-2027**. The base case is the hedge decaying.
3. **Granularity.** 1 CL = $82,270 notional = **10.2% of an $805k book** — far too large. Only
   **MCL (Micro WTI, 100 bbl, ~$8,227 = 1.0%)** is sizeable here. **1 NG = $27,210 = 3.4%**, also
   too blunt. Any implementation is micro-contracts or nothing.
4. **Operational gate.** The account currently has **no NYMEX market-data entitlement** — live CL/NG
   quotes returned empty. That must be fixed before trading, not after.

PHYS already occupies part of this slot with no carry, no roll, no expiry and no data entitlement
problem. Oil is the better *specific* Hormuz hedge; gold is the better *generic* one already held.

---

## CATALYST PASS — 12 MONTHS, DATED

| Date | Event | Why it matters | Tripwire |
|---|---|---|---|
| 2026-08-20 | CLU6 expiry | front rolls to Oct-26 ($81.43) | — |
| 2026-08-27 | NGU26 expiry | front rolls to Oct-26 | — |
| **Sep-2026** | **EIA expects Hormuz flows to begin rising** (STEO 2026-08-11) | the core oil catalyst; on-schedule = curve flattens, carry compresses | slippage past Oct-2026 with no flow recovery ⇒ re-open the oil case |
| Sep-2026 | EQT Sep18'26 52.5 put expires; EQT $54.55 | ~$2 OTM; assignment adds $5,250 EQT | manage into expiry |
| Q4-2026 | EIA Brent Q4 $78 vs Q3 $85 | the forecast decline begins | front holding >$85 into Nov ⇒ disruption is stickier than modelled |
| **End-Oct 2026** | **US gas storage projected 3,985 Bcf — highest pre-winter since 2016** | confirms/kills the gas bear | storage <3,700 Bcf ⇒ revisit gas |
| Winter 26-27 | NG Jan-27 $3.951 must be realised | the seasonal is where UNG holders are harvested | a warm winter is the −45% path |
| **Q1-2027** | **EIA: most shut-in production restored** | if it happens, oil converges to ~$69-71 and the trade is dead | non-restoration is the entire bull case |
| 2027 | EIA Brent $69 / HH $3.31 | curve (CL Sep-27 $71.44) agrees on oil; **disagrees on gas** (Dec-27 $4.18 / Jan-28 $4.63) | the gas gap is the thing to watch — it should close downward |

**Fireable catalyst check:** the oil leg has one (Hormuz restoration, dated, falsifiable). The gas
leg's bull catalyst is *back-loaded past the option's life* and just moved the wrong way — no
fireable near-term catalyst, which is dead-money by the desk's own standard.

---

## WHAT WOULD CHANGE THE VERDICT

**Buy oil (MCL, 1-2% of book) if any of:**
- Hormuz restoration slips materially past Q1-2027 with flows still <10 mb/d, **or**
- front WTI mean-reverts toward the deferred ($72-75) while the disruption is *unresolved* — that is
  the same tail at a fair price, **and**
- NYMEX market data is entitled and the K-1/§1256 questions (rows 2 and 9) are closed first.

**Buy gas only if all of:** storage falls below the 5-yr average, production growth stalls below
~112 Bcf/d, and the Texas datacenter pause is reversed with contracted (not announced) load. Until
then the −15.2% carry is paying for someone else's consensus.

---

## MECHANISM ENCODED (for the knowledge graph)

**`commodity_curve_regime_inverts_etp_verdict`** — the "commodity ETPs bleed" heuristic is
regime-conditional, not structural. Same product family, same year: oil +16.8%/yr structural gain,
gas −24.9%/yr structural drag, sign set entirely by curve shape. *Always read the live curve before
grading an ETP; never inherit the generalisation.* Masking channel: a true-but-stale heuristic.
Signal channel: per-expiry settles. Latency: instant, free.

**`equity_proxy_fails_in_the_commodity_tail`** — producer equities track the commodity in ordinary
regimes (USO/SU corr 0.67) but decouple in supply shocks: XOM captured **1.5%** of an 80% crude move
because integrateds are short their own input and the market won't capitalise a disruption it
expects to reverse. *"We already own it via the equities" is valid for trend and invalid for tail —
test the two separately.* Latency: the divergence is visible within the shock month.

**`curve_above_agency_forecast_is_the_consensus_tell`** — when the forward strip sits materially
above the sponsoring agency's own price forecast (NG Dec-27 $4.18 vs EIA 2027 $3.31) while that
agency revises demand down and supply up, the structural story is priced and then some. *Pay carry
to hold a view already above the official forecast = negative expected value.*

---

## SOURCES

- **Curve:** NYMEX settlement prices 2026-08-14, per-expiry via IBKR `get_price_history` (FUT,
  ONE_DAY, exchange=NYMEX). Live snapshots unavailable — no NYMEX entitlement.
- **Returns/correlations:** IBKR `get_price_history` monthly closes, Aug-2021 → Aug-2026, n=60
  monthly returns; IBKR `get_price_snapshot` live 2026-08-14.
- **Positions:** IBKR `get_account_positions`, 2026-08-14.
- EIA Short-Term Energy Outlook, released **2026-08-11** — `eia.gov/outlooks/steo/` (summary, global
  oil, natural gas sections).
- EIA Weekly Natural Gas Storage Report, week ending **2026-08-07**, released 2026-08-13 —
  `ir.eia.gov/ngs/ngs.html`.
- USO Form 10-K FY2025, filed **2026-02-27**, accession 0001104659-26-021501 (CIK 0001327068).
- USCF fund pages for USO and UNG, retrieved 2026-08-14.
- **Not reached within fetch budget (UNVERIFIED):** EIA Weekly Petroleum Status Report inventory
  table (PDF/HTML both failed to parse), IRS §1256 primary source, CME margin tables, EQT Q2-2026
  hedge book and any EQT datacenter agreements.

**Analyst note on the EQT overlap:** the brief asked to quantify how much of the AI-power trade EQT
already carries. EQT's hedge percentage and any power/datacenter contracts were **not verified** —
the IR release did not render and the fetch budget was capped. What *is* established from the tape:
EQT's 5-year return (+197.5%) tracked gas equity beta, its correlation to UNG is 0.59, and it
captured **negative** 2.7% of the oil shock. It is a gas-equity position, not a gas-commodity
position, and it is the book's worst diversifier (SPY beta 0.58, corr rising to +0.16 in down
months). Sizing the AI-power overlap properly requires the hedge book — flagged as open work.
