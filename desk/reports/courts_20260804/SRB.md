# SRB — Serabi Gold plc (AIM/TSX/OTCQX: SRB, GB00BG5NDX91)
**Court: lse_shelf_20260804 · 2026-08-04 · verdict 4/10 — RISK_PREMIUM, gated. Not an EDGE.**

Identity RESOLVED: **Serabi Gold plc**, Brazilian gold producer (Palito Complex + Coringa Mine, Tapajós, Pará state). Reports in **USD**, trades in **GBp**.

---

## 0. HEADLINE RULING IN ONE LINE

The shelf row is **accurate** — unlike ACSO, nothing in it is a data artifact. 2.3x EV/EBIT, $61.7m net cash, and zero capital commitments are all **CONFIRMED against primaries**. The problem is not the numerator or the data; it is that **the denominator is a gold price, and the cost base has ratcheted up 73% since the last time gold was normal.** This is a levered gold call wearing a value costume — ownable as fairly-paid risk, never as edge.

---

## 1. COMMODITY FRAME TEST (mandated first) — the premise is half right, and the wrong half is the dangerous one

**The presumed trap shape was "gold at all-time-high → peak-cycle earnings on a low multiple." The tape says something more advanced than that.**

| Claim | Method / authority | Finding |
|---|---|---|
| Gold is at an all-time high | IBKR XAUUSD (conid 69067924, IBCMDTY), live 2026-08-04 | **US$4,094.6/oz** (bid 4094.44 / ask 4094.79) — near records but **not at one**. CONFIRMED |
| Serabi's realised price in the quarter that anchors the trailing multiple | Q1-2026 report: revenue $38,749k / 8,029 oz bullion | **US$4,826/oz.** CONFIRMED |
| Therefore… | derived | **Gold is already ~15% BELOW the price that generated the trailing EBIT.** The peak has *already rolled over*. CONFIRMED |

**Realised-price history (AR2025): 2024 $2,407/oz → 2025 $3,481/oz (+44.6%).**

**Now the part the "peak earnings" framing misses — the cost side is the real trap.**

| AISC | Source | $/oz |
|---|---|---|
| 2023 | AR2025 chart + CFO review | **1,326** |
| 2024 | AR2025 | **1,700** (+28.2%) |
| 2025 | AR2025 CFO review (cash cost $1,437) | **1,816** (+6.8%) |
| **Q1-2026** | Q1-26 report / Jun-26 presentation p.4 | **2,293** (**+26.3%**) |

- Q1-26 operating costs **+38% YoY** ($17.41m vs $12.62m) on production +20% and tonnes milled +13% — **unit costs rising faster than volume.** CONFIRMED.
- **FX is a headwind, not a cushion:** BRL averaged **5.26/USD in Q1-26 vs 5.85 in Q1-25** — the real *strengthened*, raising USD-reported costs. Company states the move only *partially* offset cost increases. CONFIRMED. (Company long-term assumption: BRL 5.40.)
- Coringa's 2024 PEA base-case AISC was **$1,241/oz**; actual is **1.85x** that. CONFIRMED.

**THE MECHANISM (this is the finding):** Serabi earned **$2.2m of EBIT in FY2022 at ~$1,800 gold** and **$67.9m in FY2025 at $3,481**. The entire earnings base *is* the gold move. But AISC has ratcheted from $1,326 to $2,293 — **+73%** — and cost ratchets in underground mining (deeper development, labour, a strengthening BRL) do not reverse on the way down. **So a gold reversion does not retrace the old curve; it lands on a much higher cost floor.** At $2,400 gold, AISC consumes ~96% of the price.

**This is why the shelf's `trough_anchored: true` flag (38.8x legacy trend vs 1.24x peak) was pointing at something real.** The intake called it "a base effect," which is correct but understates it: the base effect *is* the gold price, and it is symmetric.

---

## 2. DOES 2.3x SURVIVE A NORMALISED DECK? (the mandated question)

**Basis, all independently recomputed:** 75,734,551 shares (CONFIRMED flat at 31-Mar-26, 31-Dec-25, 31-Mar-25 — no dilution; fully diluted 78.5m; **no warrants in issue**) × **248.0p** live × GBPUSD **1.3444** = mktcap **$252.5m**; less net cash **$61.7m** ⇒ **EV $190.8m**.

**Trailing EBIT reconstructed from primaries:** FY25 operating profit $68,245k + Q1-26 $27,097k − Q1-25 $10,614k = **$84,728k** — *exactly* the shelf's `ebit_reported`. **EV/EBIT = 2.25x. The shelf's 2.28x is CONFIRMED correct.**

**Sensitivity — AISC held at the Q1-26 actual $2,293/oz, EV held at $190.8m:**

| Gold $/oz | Margin/oz | @53koz (FY26 guide, low end) | @46koz (H1 run-rate) | EV/EBIT @53k / @46k |
|---|---|---|---|---|
| 4,826 *(Q1-26 realised)* | 2,533 | $134.2m | $116.5m | **1.4x / 1.6x** |
| **4,095 *(live spot)*** | 1,802 | $95.5m | $82.9m | **2.0x / 2.3x** |
| 3,500 *(company's own LT deck)* | 1,207 | $64.0m | $55.5m | **3.0x / 3.4x** |
| **2,800** | 507 | $26.9m | $23.3m | **7.1x / 8.2x** |
| **2,400** | 107 | $5.7m | $4.9m | **33.5x / 38.9x** |

*(Approximation flagged: (price − AISC) × oz is a pre-tax operating-margin proxy, not statutory EBIT — AISC carries sustaining capex where EBIT carries D&A. Roughly offsetting at this scale.)*

**ANSWER: NO. 2.3x does not survive the $2,400–2,800 deck — it becomes 7x to 39x.**

But the honest full answer has three parts, and only reporting the first would be exactly the kind of framing this desk exists to catch:

1. At **$2,400–2,800**, the multiple runs **7x–39x**. The name is uninvestable there.
2. At the **company's own long-term assumption of $3,500/oz** (AR2025 going-concern note, held to 2035, with BRL 5.40), it is **3.0–3.4x** — still genuinely cheap. **Management does not underwrite spot either.** CONFIRMED.
3. At **live spot $4,095**, it is **2.0–2.3x** — i.e. the trailing multiple is real *at today's gold*, not a trailing illusion, because the volume ramp (44.2koz FY25 → 53koz guided) offsets the margin compression.

**So the market is not mispricing Serabi. The market is pricing a gold reversion, and it is right to.** A 2.25x multiple on a producer whose margin is 100% levered to one commodity is not a discount — it is the correct price of that leverage.

---

## 3. MODE B — the risk the shelf never saw: 62% of production runs on a *trial* permit

This is the largest un-priced item in the name, and no balance-sheet screen reaches it.

| Fact | Authority | Status |
|---|---|---|
| Coringa is "**Full ramp-up expected by end of 2026**"; "**Final permit pending**"; operating "**under 3-yr GUIA licence**" | Jun-2026 corporate presentation p.2 + Coringa asset page | CONFIRMED |
| GUIA is a **trial** mining licence; 3-year extension received **January 2024** | AR2025 | CONFIRMED (extension + date). **Implied expiry ~Jan-2027 is my inference — UNVERIFIED** |
| The **Installation Licence (LI)** remains outstanding; the process involves "relevant authorities, stakeholders and **indigenous groups**" | AR2025 Chairman/CEO review | CONFIRMED |
| Management's position to the auditors: LI issues "**are and will be resolved**… not expected to create any material delay," on Brazilian legal advice | AR2025 critical-judgements note (p.120) | CONFIRMED — **as a management judgement, not as an obtained permit** |
| **Coringa was 62% of group production in Q1-26** (7,450 of 12,043 oz) | Q1-26 report | CONFIRMED |
| Licensing/environmental risk is named principal risk #5; AR notes Brazilian legislation is "amended at short notice in reaction to events at other mining operations" | AR2025 | CONFIRMED |

**A majority of production operating on a trial licence, with the full licence pending indigenous consultation, is a dateable binary that the phrase "verified clean balance sheet" does not touch.** The balance sheet being clean and the *mine being permitted* are independent questions, and the shelf only asked the first.

---

## 4. THE ZERO-COMMITMENTS VERIFICATION — CONFIRMED, and it is genuinely rare

The build lane's claim was flagged as "rare and real." **It is real. Confirmed verbatim, exact note:**

> **AR2025, Note 23 "Commitments and contingencies" → "Capital Purchases": "At 31 December 2025 the Group has not made any commitments for capital purchases."**

Also confirmed: exploration-property contracted commitments over the next 12 months are **$0.02m** (2024: $0.02m) — de minimis. No capital-commitment disclosure was added in the Q1-26 report (absence of restatement CONFIRMED). **This clears the THX-lesson bar: the commitments note was actually read, and it is clean.**

**But the takeaway must be bounded: uncommitted ≠ unnecessary.** The same primary sources disclose planned spend that is not contractually committed but is entirely required to deliver the plan the multiple assumes:

- **$15M underground development in 2026**
- **Ball mill ~$5m** + classification plant **<$10m** for the 650→900tpd expansion (Q4-2026E)
- **$9m exploration programme** 2025–26
- **Coringa PEA sustaining capex $87M over an 11-year life**
- Q1-26 investing outflow was already **$7.56m** in the quarter

So the correct statement is: *the cash is not contractually pre-spent, and Serabi retains the option to stop.* That is a genuine and unusual balance-sheet virtue in a junior miner. It is **not** the statement "the net cash is free and additive to the equity value" — the growth the 53koz→900tpd plan embeds is funded out of that same $61.7m.

**Honesty grade on the build lane's claim: CONFIRMED, correctly scoped, and to its credit it did not overstate.**

---

## 5. BALANCE SHEET & CAP STRUCTURE (pulled before any EV claim, per doctrine)

| Item | Value | Authority |
|---|---|---|
| Cash | **$64,438k** | Q1-26 balance sheet |
| Interest-bearing liabilities | $2,719k ($1,007 current + $1,712 non-current) — **these are LEASE liabilities** | Q1-26 |
| **Net cash** | **$61,719k = 24.4% of market cap = ~60p/share** | CONFIRMED — validates the intake's ~$61.7M |
| Debt | **Zero.** $5.0m Santander working-capital loan (22-Jan-25, 6.16%) **repaid 16-Jan-2026**; "the Group is debt free" | Q1-26 Debt section |
| Warrants / converts / prefs | **"No warrants in issue."** No placing or convertible in the last 18 months | AR2025 |
| Shares | 75,734,551 (fully diluted 78.5m; 2,728,049 conditional share awards) | Q1-26 note 15 |
| Undrawn facility | HSBC unsecured precious-metal leasing facility (≤12m), **never utilised** | Q1-26 |
| Dividend | **Inaugural 5p/share** (~$5.41m = 20% of 2025 FCF); board indicates similar payout range ongoing. **Yield 1.88%** at 248p | AR2025 CFO review |
| Register | Classe Roca Magma FIP **25.0%**, Ruffer 3.8%, Gold 2000 2.4%, River & Mercantile 1.1%, directors 0.7%, retail/other ~67% | Jun-26 presentation |

**Shelf correction:** the row's `netcash` $59.83m deducts a **$2.52m "pension"** that is not a pension — it is the provisions line. The AR shows **no DB scheme**. The shelf's own `pension_note` already warns the proxy over-captures; here it does. The correct figure is **$61.7m** (the addendum's pension-by-hand instruction, executed: no deficit, no surplus, no adjustment warranted).

---

## 6. CAUSE-CHECK + PATH — and a shelf-design finding

**I re-pulled the tape independently (yfinance SRB.L, 254 daily bars) because the agent's IBKR feed for this line was DEGRADED (OHLC identical per bar, zero volume, 130 bars/yr with gaps). The IBKR-derived move dates were partly feed artifacts and are discarded.** Verified figures:

- Live **248.0p** (yfinance close 2026-08-04 **and** IBKR snapshot 248.0p — two independent sources agree; IBKR quotes GBp, `get_price_history` GBP — the 100x convention was checked, not assumed).
- 52w high **359.9p** (2026-03-10, re-tested 359.9p 2026-05-27) · 52w low **187.5p** (2025-08-20).
- **−31.1% from the 52w high · +32.3% off the 52w low.**
- **13-week low = 248.0p = TODAY.** The stock is **AT a fresh 3-month low**, down ~10% in 9 sessions (276p on 22-Jul → 248p) on *rising* volume.
- Moves >8% in the last 6 months: 03-Feb +9.4%, 09-Feb +9.7%, 13-Feb −9.0%, 16-Feb +9.9%, 19-Feb +10.5%, 10-Mar +9.1%, 19-Mar −10.6%. **Nothing since 19-Mar** — the −31% slide has been a grind, not an event.

**Reading:** the February cluster is a gold-volatility regime; the subsequent grind with no >8% day and no company RNS is consistent with **gold rolling over**, not a company-specific derailment. Cause is therefore commodity beta — which is the honest answer, and also the reason this cannot be an edge.

**SHELF-DESIGN FINDING (worth carrying back to the generator):** the row reports `pct_off_52w_low: 0.3227`, `days_since_low: 349`, `fresh_low: false`, `entry_exhausted: false` — all technically correct and all **benign-looking for a name sitting at a fresh 13-week low in an active downtrend**. **The path fields are 52-week-anchored and structurally blind to a fresh 3-month low.** This is the same class of error the intake already fixed on the EBIT anchor (trough-anchored → peak-anchored); the path fields need the identical treatment. Recommend adding `pct_off_13w_low` / `days_since_13w_low`.

---

## 7. PRODUCTION TRAJECTORY — guidance is heavily back-end loaded

| Metric | Value | Authority |
|---|---|---|
| FY2025 production | **44,169 oz** (record, +18%); revenue $155.85m (+65%); EBITDA $77.9m; post-tax profit $53.9m | AR2025 CONFIRMED |
| FY2026 guidance | **53,000–57,000 oz** | AR2025 + Jun-26 presentation CONFIRMED |
| Q1-2026 | **12,043 oz** (Coringa 7,450 / Palito bullion 1,806 / concentrate 2,786); 10,323 oz sold; PBT $27,438k; post-tax $21.0m; EBITDA $29.2m | Q1-26 report CONFIRMED |
| Q2-2026 | **11,007 oz — DOWN sequentially**; guidance "maintained" at **53,000 oz** (bottom of range) | **PLAUSIBLE — secondary only** (Crux Investor / Investing.com / TipRanks, 22–24 Jul 26). Primary RNS body not retrievable |

**H1-2026 = 23,050 oz.** To reach even the 53koz bottom of guidance, **H2 must deliver 29,950 oz = +29.9% vs H1, or +36.0% above the Q2 quarterly rate.** The H1 run-rate annualises to **~46koz**, ~13% below the low end of guidance.

**Q1-26 operating profit $27,097k and net cash ~$61.7m — the two figures the intake asserted — are both CONFIRMED from the Q1-26 primary.**

---

## 8. BRAZIL / JURISDICTION

- **CFEM royalty** applies; FY2025 royalties expense **$2,441k** (2024: $1,226k) ≈1.6% of revenue. CONFIRMED. **No 2026 CFEM rate change found — UNVERIFIABLE either way.**
- **Tailings:** small existing dams; stated policy not to increase the dam footprint; dry-stack/filtration plant at **conceptual** stage only; aligned "toward GISTM expectations" — i.e. **not yet GISTM-conformant**, and the AR concedes expansion "implies the expansion of tailings facilities." Modest Brumadinho-regime exposure, not zero. CONFIRMED.
- **Two fatalities in January 2026** — Coringa 26-Jan (halted local production) and Palito 31-Jan (traffic). **PLAUSIBLE, secondary only.** A safety record like that is a licence-risk input in Pará, and it sits directly adjacent to the pending LI.

---

## 9. SCENARIOS & FAIR VALUE

Fair multiple anchored at **3.5x forward EBIT** (single-district, single-jurisdiction AIM producer with a live permit binary; peers 3–5x). Net cash $61.7m added at face.

| Scenario | p | Assumptions | FV |
|---|---|---|---|
| **Permit fails / material suspension** | 0.15 | Coringa LI refused or GUIA lapses → production to ~18–20koz (Palito only). Floor = net cash + Palito | **135p** |
| **Gold bear, permit OK** | 0.25 | Gold $3,000, AISC ratchets to $2,400, 46koz → EBIT $27.6m | **155p** |
| **Base, permit OK** | 0.38 | Gold $3,800, AISC $2,300, 50koz → EBIT $75.0m | **319p** |
| **Bull, permit granted + rerate** | 0.22 | Gold $4,600, AISC $2,250, 55koz → EBIT $129.3m | **505p** |

**E[FV] ≈ 0.15(135) + 0.25(155) + 0.38(319) + 0.22(505) = 291p** vs live **248p** ⇒ **edge ≈ +17.5%.**

**But classify it correctly.** That +17.5% is not insight — it is compensation for (a) an unhedged gold-price distribution on which this desk has no view, and (b) a Brazilian permit binary. **Classification: RISK_PREMIUM, not EDGE.** Under the fairly-paid-risk doctrine the bar is: fairness verified (yes — 2.25x with 24% net cash is more than fair payment for gold beta), tails bounded and unlevered (yes — debt-free, no warrants, floor ~135p ≈ −45%, not −100%), sleeve-capped (must be), and carry-vs-edge labelled (done, here).

**Downside floor is real:** net cash alone is **60p/share = 24% of the current price**, and it is verified, unlevered, and uncommitted.

---

## 10. RULING — 4/10, RISK_PREMIUM, GATED. Not red-team required.

It clears 4 because the balance sheet is genuinely clean, the multiple is genuinely real at spot, the tails are bounded, and the downside has a verified cash floor. It goes no higher because **we would be buying a gold-price view we do not have, plus a permit binary, and paying 400bp of touch for the privilege.**

**ENTRY IS GATED — no tranche before the H1-2026 financial report.**

Per the contract's nowcast-vs-tape rule: **AISC is the load-bearing variable of the entire thesis and we have exactly ONE quarter of it at $2,293** (vs $1,816 for FY25). Q1 is the Pará wet season, so $2,293 may be a seasonal peak *or* a structural ratchet — and the two lead to 3.0x and 8.2x respectively. **H1/Q2 financials (expected ~mid-to-late Aug 2026, on the Q1 cadence) resolve it.** Buying now is a blind entry inside the print window on the one number that decides the case.

| | |
|---|---|
| **Band** | Tranche 1 ≤ **248p** *(gated: only after H1 shows AISC ≤ $2,100/oz)* · Tranche 2 ≤ **210p** |
| **Size** | **0.4% of $3.3M ≈ $13,200** — deliberately the LOW end of the UK 0.75% cap. This is not a red-team survivor and must not be sized as one |
| **Tranche plan** | 2 × ~$6,600. T1 only on the H1 AISC gate; T2 only on price, never averaging into a permit-negative |
| **Liquidity** | Median ADV **$984k**, 20%-of-prints order cap **$197k/day** — among the best on the AIM top ten. Size is not the constraint |
| **Friction** | **400bp touch — the worst on the AIM top ten**, ~4% round-trip. Stamp **0% (AIM)**. Dividend WHT **0%**. Per the addendum: the 0% WHT is a *holding* edge and must not be used to justify this touch |

## 11. DATED KILLS

| Trigger | Date | Action |
|---|---|---|
| **H1-2026 AISC prints above $2,300/oz** | ~mid-late Aug 2026 | **Do not enter.** Cost ratchet is structural, not seasonal |
| Coringa **Installation Licence refused, or GUIA lapses without renewal** | ~Jan-2027 (inferred) | **Kill outright** — 62% of production |
| FY2026 production guidance cut below 50koz | any | Kill |
| Gold sustained below **$3,200/oz** for one quarter | any | Kill — below the company's own $3,500 LT deck with no cost offset |
| AISC exceeds **$2,600/oz** in any reported period | any | Kill — margin structurally impaired at any plausible gold price |
| New capital commitment, equity placing, or any warrant issue | any | Kill — the zero-commitment/no-dilution premise is the entire balance-sheet case |
| A third fatality or a tailings/GISTM enforcement action | any | Kill — licence risk compounds |

## 12. FREEZABLE CALL

**`SRB | 2026-12-31 | Serabi Gold FY2026 gold production comes in BELOW 53,000 oz (the bottom of guidance) | our_p = 0.70`**

(H1 actual 23,050 oz with Q2 declining sequentially requires +36% above the Q2 rate to clear 53koz. Dependency noted: Q1 12,043 oz is primary-CONFIRMED; Q2 11,007 oz is secondary-PLAUSIBLE.)

## 13. VERIFICATION GAPS — UNVERIFIABLE, listed honestly

1. **Q2-2026 primary RNS text was NOT retrievable** (investegate index returned only two 2020-era placing links; serabigold.com is a JS-rendered shell; no browser available this session). Q2 production, Q2 AISC, cash at 30-Jun-26 and the exact guidance wording rest on **three secondary outlets**, not a primary. This is the single largest gap and it sits under the freezable call.
2. **GUIA expiry ~Jan-2027 is inferred** from "3-year extension in January 2024," not stated in any document read.
3. **One quarter of AISC at $2,293.** Seasonal-vs-structural is genuinely undetermined and cuts both ways.
4. **No cause verified for the 360p→248p slide.** Gold is the strong prior; not confirmed against an RNS.
5. **The two January 2026 fatalities are secondary-sourced only.**
6. **NI 43-101 technical reports filed 11-Jun-2026** for Palito and Coringa were not read; reserves vs the 1.4Moz M&I&I resource were not separated, so **stated reserve life is unverified.**
7. **CFEM / Brazilian fiscal changes for 2026** — no evidence found either way.
8. **Analyst targets not extracted** (3 brokers cover).
9. **IBKR conid for SRB.L is NOT on the shelf** (`conid: null`); the agent resolved 804727363 but the bar feed is degraded (close-only, zero volume). Executability is **DATA-GATED** — verify the line before any order. Account LSE permission is separately proven (BRBY/TW. held).
