# OPPORTUNITY-ZONE FUNDS AND THE SEPTEMBER GAIN
### What a QOF must return to deserve a slice, and the plan either way
**SignalOS desk · 2026-08-30 · primary-verified against IRS Notice 2026-40 and Rev. Proc. 2026-14 · for CPA review (Harness) before any election**

## 1. The rule that makes this a 2027 decision, not a 2026 one
IRS **Notice 2026-40** (July 2026) settles the transition to the rewritten OZ regime:
- **§.01 — invest during 2026: the deferral is worthless.** Gains invested in a QOF on or before
  12/31/26 are included in income *that same year* (the old inclusion date). Nobody should put
  2026 gains into a QOF in 2026.
- **§.02 — invest on or after 1/1/2027: the new regime applies, even to 2026 gains.** Deferral
  runs **5 years from the investment date** (to ~early 2032), with a **10% basis step-up** at
  year 5 (**30% for rural QOFs**), and the 10-year hold still makes appreciation **federally**
  tax-free.
- Our September gain's 180-day clock (escrow ~9/18) runs to **~mid-March 2027** — so the window
  to elect the new regime is **January–mid-March 2027**, decided with full information.
- **§5 catch:** property a QOF buys after 12/31/26 generally must sit in **newly designated
  zones** (nominations under Rev. Proc. 2026-14, designations effective 2027) or ride a
  grandfathered working-capital pipeline — a hard screen on which funds are even eligible.
- **California never conformed.** The 13.3% CA tax on the gain is due with the 2026 return
  regardless, and CA taxes the QOF's appreciation at exit for a CA resident. Only the federal
  23.8 points play.

## 2. The hurdle: what a fund must actually return
Modeled per dollar of gain, invested March 2027, exited year 10, against the alternative of
paying all tax now and compounding the net in our own book at return r:

| If our book compounds at | Required QOF return, NET of fees (CA resident) | If we've left CA by exit | Rural fund (30% step-up) |
|---|---|---|---|
| 7% | **4.6%** | 4.1% | 4.1% |
| 9% | **6.1%** | 5.5% | 5.7% |
| 11% | **7.7%** | 6.9% | 7.3% |
| 13% | **9.3%** | 8.4% | 8.9% |

Translating net to the **gross** a typical fund (1.5% mgmt + 20% carry over an 8% pref) must earn:
net 5.5% → gross ~7% · net 6.5% → gross ~8% · net 7.5% → gross ~9% · net 8.5% → gross ~10%.

**Reading it honestly:** against an index-like 7–9% alternative, the hurdle is a modest 4.6–6.1%
net — most competent real-estate QOFs clear that on paper, which is why the structure is
genuinely attractive *for dollars that would otherwise sit in beta*. Against our deployed
machine at 11–13%, the hurdle rises to 7.7–9.3% net (~9–10% gross) — **top-quartile development
returns, locked up ten years, judged on a sponsor's pro-forma**. The correct mental frame: an OZ
slice replaces the *index* sleeve, not the alpha sleeve — and on that comparison it can win.

## 3. Cash-flow mechanics per $1M routed (Jan-2027 investment)
- **$238,000 of federal tax comes OFF the 1/15/2027 estimate** — retained and compounding ~5 years.
- **$214,200** federal due ~spring 2032 (the 10% step-up erases $23,800 permanently).
- **$133,000** CA due with the 2026 return no matter what.
- Year-10 exit: federal tax on appreciation $0; CA tax on appreciation ~13.3% unless residency
  has changed (a real variable on a 2037 horizon — the model shows both columns).

## 2b. THE INTEGRATED MODEL (v2, 8/30 — harvest engine endogenous; desk/models/oz_model.py)
The single-period table above treats the year-5 inclusion as a cash event. Modeling the household
year-by-year — gains landing, the harvest engine offsetting what it can, excess losses banking as
carryforwards — changes the picture:

| OZ slice | vs 9% alternative | vs 11% | vs 13% | 2032 inclusion absorbed by banked losses |
|---|---|---|---|---|
| $1.0M | **5.6%** | 7.1% | 8.7% | **100%** |
| $1.5M | **5.6%** | 7.1% | 8.7% | **100%** |
| $2.0M | **5.6%** | 7.1% | 8.7% | **100%** |
| $3.0M | 5.7% | 7.2% | 8.7% | 92% |

Sensitivities: no 2027 tranche → 6.1%/7.1%/8.7% (idle losses help the no-OZ path too, narrowing
the gap); harvest at half pace → 5.7% and 92% absorbed. **Robust range: ~5.6–6.1% net at a 9%
alternative.** Fee translation: 5.6% net ≈ **7.1% gross** at 1.5/20; 7.1% net ≈ 8.6% gross.

**Three conclusions the integration forces:**
1. **The deferred federal tax is probably never a cash event.** Once the escrow tranches stop,
   the machine banks ~$2.2M of carryforwards by 2032 — enough to absorb the inclusion entirely
   at any slice up to ~$2M. The deferral isn't a postponed bill; it's a bill pre-addressed to
   losses that would otherwise idle.
2. **The hurdle stops being the constraint on slice size.** It is flat from $1M to $3M — so how
   much to route is a LIQUIDITY and deployment-strategy decision (10-year lockup vs the machine's
   compounding and the December harvest-relief effect), not a tax-math one. The earlier $1–1.5M
   framing understated the tax-feasible range.
3. **The screen gets easier to pass than first modeled**: verified ~7% gross clears the 9%-
   alternative case; ~8.5–9% gross (with our standard pro-forma haircuts) clears even an 11%
   alternative. Competent industrial/multifamily OZ development commonly claims 8–12% gross —
   the job in January is verifying those claims, not finding unicorns.

## 3b. Scenario B′ — the advisor's reading, modeled (added 8/30 after the tax advisor's contrary opinion)
The principal's tax advisor holds that a 2026 QOF investment defers the gain until the investment
completes — contra Notice 2026-40 §.01 as we read it. Modeled per $1M of gain (8%-net fund, 9%
alternative): January path **+$301k** vs no-OZ with statutory certainty; investing NOW is worth
**+$44k to +$95k more** than January *if the advisor is right* (lite → max variants), and
**−$99k vs January if wrong** (federal due April 2027; still +$202k vs no-OZ because the 10-year
exclusion survives 2026 investments — §.01(3)). Hurdle deltas between now-and-January are 0.1–0.5pp
in every column: the advisor's theory, even if correct, mostly implies January was always fine.
**Ruling frame:** stay with the January default; a 2026 investment is justified only by (a) written
authority against §.01 AND (b) a specifically superior fund with a hard 2026 close — and then as a
bounded sub-slice ($0.5–1M) where the wrong-branch cost (~$99k/M) is an acceptable price of access.
**Open question to the advisor (decisive):** what statute/regulation/guidance supports deferral
beyond 12/31/2026 for a QOF investment made during 2026, against Notice 2026-40 §.01's verbatim
"must be included … the earlier of … December 31, 2026"?

## 4. The plans
**Plan A — the default: do nothing in 2026, decide in January.** Zero QOF dollars this year
(Notice §.01 makes 2026 investment strictly dominated). Between now and January: build the fund
menu (only funds deploying in post-2025-designated zones or grandfathered pipelines; demand the
zone list in writing), and re-run this model with the January tape and the ratified deployment
plan's realized returns.
**Plan B — the conditional allocation: $1.0–1.5M if and only if a fund clears the sheet.** Sized
so the tax reserve and the slots-first deployment are untouched (it substitutes for index-sleeve
dollars). The screen, in order: (1) net-of-fee pro-forma ≥ **7%** with the haircuts we apply to
every sponsor deck (§conservative-FV); (2) **rural QOF preferred** — the 30% step-up lowers the
hurdle ~0.4pp and rural land basis is where the new law is most generous; (3) zone eligibility
verified against the 2027 designation list, not marketing; (4) sponsor with realized (not
projected) prior-fund DPI; (5) fee load ≤ 1.5/15 preferred over 2/20 — at these hurdles fees are
the whole game. Anything that fails two screens dies without a meeting.
**Plan C — the DIY QOF, priced as an option.** Self-certifying a QOF (Form 8996) and buying a
qualifying asset directly (small commercial/industrial in a newly-designated tract; the tail
framework's "productive real assets" tier) keeps the full gross return — the 2–3% annual fee
drag *is* the hurdle gap between B and C. Real costs: our time, concentration, compliance
(90% asset tests, working-capital plans). Worth a desk feasibility memo only if Plan B's menu
comes back weak but the January model still favors deferral.
**Plan D — the explicit no.** If the January menu can't beat ~7% net verified, pay the tax and
deploy per the ratified plan — the machine's own cohort evidence is the bar the sponsor has to
beat, and "no" remains the desk's most-practiced answer.

## 5. What must be verified with the CPA before any election (Harness, January)
The §.02 election mechanics on a 2026-year return filed 2027; estimate-payment treatment of the
deferred federal slice (safe-harbor interaction); the escrow tranche's exact gain-recognition
date (starts the 180 days); CA reporting of the deferral add-back; and the 2032 inclusion-year
liquidity plan (the deferred tax comes due whether or not the fund has distributed).

*Model assumptions: 37.1% combined rate today and at exit; 23.8 federal deferrable; opportunity
cost compounds tax-deferred until exit; 10-year hold from a March-2027 investment; no step-up at
death (which would favor Plan A/D — flag for estate planning). Sensitivity available on request.*
