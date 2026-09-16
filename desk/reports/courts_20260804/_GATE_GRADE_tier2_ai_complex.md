# GATE GRADE — tier-2 AI-COMPLEX cohort #1 (PLTR APP ARM MRVL KLAC) | 2026-08-03

Companion to `_GATE_TEST_GUIDE_DECEL.md` and `_GATE_GRADE_tier2_falling.md` (sibling lanes).
Consistent with both; this lane's distinct contribution is **three new gates**, all driven by the
same defect: `quality_drawdown.py` measures a discount to a **price high** and never asks what that
high was, when it was set, or where the resulting **multiple** sits.

---

## The observation that generates all three gates

| name | 3y high | **age of high at screen** | off 52w low (live) | trailing P/S | own 3y P/S range | **percentile** |
|---|---|---|---|---|---|---|
| KLAC | 2026-06-30 | **33 days** | +120.5% | 17.7× | 6.8 – 18.3× | **~95th** |
| ARM  | 2026-06-18 | **46 days** | +141.4% | 50.5× | 20.1 – 54.2× | **~90th** |
| MRVL | 2026-06-04 | **60 days** | +220.6% | 21.1× | 9.0 – 31.1× | ~75th |
| APP  | 2025-12-22 | 224 days | +15.2% | 22.7× | 4.5 – 40.3× | ~50th |
| PLTR | 2025-11-03 | 273 days | +35.7% | 56.2× | 18.8 – 131.8× | ~45th |

The winners the screen was calibrated on (HUBS −77%, MNDY −77%, CTSH −53%, SAP −48%, G −47%,
median −46%) earned their drawdowns over **years**. ARM, MRVL and KLAC earned theirs in **five to
seven weeks**, off a June-2026 melt-up. The `depth` term (0.35 weight, peaking at −46%) cannot tell
the two apart and actively rewards the wrong one.

## GATE 1 — age-of-high (new)

**Reject when the 3-year high is younger than ~180 days.** Cheap, one line, no extra data call:
`h.idxmax()` is already computed. Rejects ARM/MRVL/KLAC; passes APP/PLTR. Correct partition.

## GATE 2 — multiple-percentile (new; the most portable output of this cohort)

**Disqualify when trailing EV/Sales (or P/E) sits in the top quartile of the name's own 3-year
distribution, regardless of drawdown depth.** The screen's whole premise is "quality at a discount
to its **own valuation history**" — and it never computes valuation history. KLAC is the proof: a
genuine, textbook de-rate (beat + a raise to +25% guided revenue, then −17% in two sessions) that
still leaves the stock at ~50× trailing GAAP earnings against a FY17–FY23 median of ~18–19×, and at
the 95th percentile of its own 3-year P/S. **The de-rate mechanism can be true while the level test
fails.** These are separate questions and the screen only asks the first.

Rejects KLAC/ARM (and MRVL on a tighter threshold); passes APP/PLTR.

## GATE 3 — promotional-high (new)

**Flag when the 3-year high was set within 5 sessions of a >3σ single-day advance that has NO
corresponding company filing.** MRVL is the case: +32.5% on 2026-06-02 on 112.6M shares (~3.7×
normal), gapping from a $219.43 close to a $253.46 open, with an **empty EDGAR docket that day** —
attributed by the tape to NVIDIA's CEO calling Marvell "the next trillion-dollar company," nine
weeks after NVIDIA bought **$2.0B of Marvell convertible preferred at a $91.8355 conversion price**
(8-K 0001193125-26-134462). The drawdown denominator was set by an interested party.

This is a **new factor-costume mode**: the existing `factor_costume` test catches sector beta in
disguise (AEM/gold). It does not catch *narrative and index-inclusion flow* in disguise.

## Gates as filed — grade

| name | flag(s) | right? | note |
|---|---|---|---|
| PLTR | GUIDE-DECEL | **WRONG** | company guides **+82%** FY26 against a 32.9% trailing CAGR. Same root cause the sibling lane found: consensus FY+1 ÷ single-quarter trailing. Additional defect this lane found — the screen never re-checks after a print: PLTR printed 2026-08-03 (+14.9% AH) and now fails **both** the depth band (−30.4%) and the path gate (+35.7% off a 39-day low). |
| APP | GUIDE-DECEL + falling | **both RIGHT** | GUIDE-DECEL right but **benign** — base effect from the 2H-2025 revenue explosion (PEG-distortion mode 1), not decay. `falling` right and meaningful: APP closed 1.0% above its 60-day min on 7/31, the only genuinely-still-falling name here. |
| ARM | EXHAUSTED | **RIGHT** | +141% off the low, ~3× `HARD_OFF_LOW`. Outweighed by `depth`; needs Gate 1. |
| MRVL | EXHAUSTED | **RIGHT** | +221%, the most extreme in the cohort. Needs Gates 1 + 3. |
| KLAC | EXHAUSTED | **right, wrong reason** | the low is 331 days old and the run was a genuine fundamental re-rating. The decisive objection is Gate 2, which the screen does not have. |

## GATE 4 — marginal-mix invalidation of the quality gate (ARM)

`MIN_GROSS_MARGIN = 0.35` admitted ARM on a **98%** blended gross margin. ARM's own marketed growth
leg is the **Arm AGI CPU — production silicon**, demand book raised from $1B to **>$2B** across
FY27–28 with manufacturing capacity already "secured." Silicon carries 30–55% gross margins.

**A gross-margin quality gate is invalid when the company's disclosed growth driver is a move down
the stack.** The gate must read the *marginal* mix, not the trailing blend — and the same disclosure
that reveals the mix shift also reveals that ARM has taken on take-or-pay-shaped capacity
commitments into the exact cycle the house prices at 45% break odds.

## Cohort conflict summary vs AI-BREAK | 2027-12-31 @ 0.45

The house call is a **credit** claim, not an equity-drawdown claim. Sorted by how much of the
earnings stream that credit event actually reaches:

1. **MRVL — total.** Custom XPU, 1.6T optics, 51.2T Ethernet, CPO/NPO, DCI: every driver is a line
   inside a hyperscaler or neocloud capital budget. Plus $4.96B debt and $13.9B of cycle-peak
   goodwill on $18.2B of equity.
2. **ARM — high, with a lag.** Royalties recognise when the licensee *ships*, so data-centre royalty
   tracks server units 1–2 quarters behind the order book; the AGI-CPU capacity commitment converts
   a soft landing into an inventory event.
3. **KLAC — high, with a longer lag.** WFE is ordered 2–4 quarters ahead of the fabs; a 2027 credit
   break hits revenue in late-2027/2028. Which means a −40% fall on rising guidance is exactly what
   a semi-cap cycle top looks like from the inside. Growth is Korea/memory-led (+80%) — the most
   volatile WFE leg — while Taiwan logic is −12%.
4. **PLTR — low on revenue, total on multiple.** 42% US government appropriations, 39% enterprise
   OPEX, $9.2B net cash, zero credit exposure. But ~42× forward sales means ~100% of the price is
   multiple, and the 2025-11 → 2026-06 fall (−48% with estimates rising) is the proof that the
   multiple can halve while the business compounds.
5. **APP — genuinely insulated.** Advertiser ROAS budgets, 11% cost of revenue, **no PP&E purchases
   at all** in the Q1 investing section, net debt 0.15× EBITDA. It is neither a seller into the
   capex cycle nor a buyer of AI infrastructure. The queue's hypothesis is confirmed.

**Household context:** ~$5.2M / 26% AI-complex already, plus a Parametric direct-indexing sleeve
carrying a heavy semiconductor book. KLAC/MRVL/ARM would each concentrate a factor the household
already owns through a vehicle it does not control name-by-name, and would extend the wash-sale
surface beyond the standing Parametric-singles-plus-GOOGL boundary. Recorded here so the next
semi-cap court does not re-derive it.
