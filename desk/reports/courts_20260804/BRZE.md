> Court lane: tier-2 small/misc EXHAUSTED tail (scores 17-39), COURT_QUEUE_20260804.
> Date 2026-08-03. Price basis: **IBKR daily close 2026-08-03, TRADES/RTH, ib_insync bars**.

# BRZE — Braze | 4/10 WATCH-BAND (the only name in the tail the EXHAUSTED flag nearly buried)
**live 25.69** (IBKR close 08-03) · cap ~$2.90B · 112.77M shares · **next print 2026-09-03 (31 days) — window is clear**

## (a) PATH CHECK — the flag's own input, and where it goes wrong
| metric | value |
|---|---|
| 52w low | 15.79 (2026-02-23) · **161 days** |
| % off 52w low | **+62.7%** |
| **52w high** | 36.19 → **−29.0%** |
| 3y high | 59.73 (2024-02-15) → −57.0% |
| last 1m | +8.7% · 3m +13.1% · YTD −27.3% |

The flag fired on **mode 2 — `HARD_OFF_LOW`: >50% off ANY low, regardless of date or of distance
from the high.** That mode has **no "distance from the high" term.** BRZE is +63% off a five-month-old
low *and still 29% below its 52-week high and 57% below its 3-year high*. Those are not the same
setup, and the flag cannot tell them apart.

**GATE VERDICT: EXHAUSTED = WRONG on BRZE.** This is the cohort's near-miss — the same failure mode
the sibling lane logged for TMUS on the FALLING flag, in a different flag. (Full gate finding and a
3-mode replacement in the batch note below.)

## (b) CAUSE-CHECK — the drawdown is 2024-25 vintage; 2026 is a recovery
Episode decomposition from the 2026-02-23 low → 08-03: **+57.8% total, of which IGV explains +22.7%
(beta 1.29) and +18.4pp is residual (share 0.39).** So the bounce is roughly 60% software tape,
40% company. Motley Fool 07-31: "Why Braze Stock Recovered 15% This Week." No negative event.
The −57% from the Feb-2024 high is the 2024-25 martech/CDP de-rate, already 2+ years old.

## (c) ESTIMATE DIRECTION — de-rate, and the business is INFLECTING
Audited XBRL, `RevenueFromContractWithCustomerExcludingAssessedTax`, fiscal quarters:

| quarter | rev $M | yoy | op income $M | op margin | SBC $M | SBC/rev |
|---|---:|---:|---:|---:|---:|---:|
| Q2 FY26 (May-Jul-25) | 180.1 | +23.8% | −38.8 | −21.5% | 39.5 | 21.9% |
| Q3 FY26 (Aug-Oct-25) | 190.8 | +25.4% | −37.5 | −19.7% | 37.6 | 19.7% |
| **Q1 FY27 (Feb-Apr-26)** | **211.0** | **+30.2%** | **−27.5** | **−13.0%** | 33.6 | **15.9%** |

Growth **accelerating** (23.8 → 25.4 → 30.2%), operating loss margin **halving**, SBC intensity
**falling**, operating cash flow **+$28.1M** and rising. Consensus FY+1 EPS 0.969 vs 0.983 90d ago
= **−1.5%** — essentially flat, clears the DERAIL bar (−3%).
**Ruling: DE-RATE with a live business inflection.** This is the only name in the tail where the
frame's target pattern (multiple compressed, estimates stable, fundamentals improving) is present.

## (d) THE BEAR — GUIDE-DECEL fired here too, and it is the mechanical false-fire
The GUIDE-DECEL gate fires on BRZE for exactly the reason the sibling lane documented: a 30%-growth
quarter in the denominator against a ~14-16% FY+1 consensus in the numerator. **It cannot NOT fire
on a fast grower.** On the direct measure (FY+1 EPS 90d change = −1.5%) BRZE is not derailing.
**GUIDE-DECEL VERDICT: FALSE FIRE** — the fifth in the sibling lane's running tally.

Real bears, honestly stated:
1. **CDP squeeze** — Salesforce/Adobe bundling from above, Klaviyo from below. Braze's answer is the
   OfferFit AI-decisioning bolt-on.
2. **The 30.2% is not decomposed.** OfferFit sits in the base; **organic vs acquired is UNVERIFIED**
   from primary in this pass. If 6-8pp of the acceleration is OfferFit, organic is ~22-24% and the
   inflection is smaller than it looks. **This is the top UNVERIFIABLE and it is load-bearing.**
3. **SBC honesty.** GAAP net loss −$26.6M in Q1 FY27. Reported FCF ~$186.5M against SBC ~$135M/yr —
   **owner FCF (FCF less SBC) is ~$50M, a 2.0% yield on EV, not the 7.3% the headline implies.**
   Diluted shares 106.8M → 110.8M, **rising** (unlike SPSC's falling count).

## Cap structure (before any EV claim)
2026-01-31: cash $124.3M + short-term investments $287.6M = **$411.9M**; total debt **$82.7M** →
**net cash ≈ $329M**. Shares 112.77M (single count; **dual-class Class A/B is consolidated in the
112.77M — checked, no share-count corruption here**). At 25.69: cap **$2.90B**, **EV ≈ $2.57B**.
Revenue run-rate $844M → **EV/S ≈ 3.0x** for a ~30% grower. Rule-of-40 on GAAP op margin: 30 − 13 = 17.

## Scenarios (FY27 revenue ~$860-910M)
| | p | fv | logic |
|---|---|---|---|
| bear | 0.35 | 19.6 | CDP squeeze bites, growth to 18%, 2.2x EV/S |
| base | 0.45 | 27.7 | 24-26% growth, FCF margin improves, 3.2x EV/S |
| bull | 0.20 | 38.5 | OfferFit decisioning lands, 28-30% sustained, 4.5x EV/S |

**e_fv $27.0 vs $25.69 → edge +5.2%. Thin — which is why the band sits below market.**

## PLAN — band + tranche (size below the ruled range; the edge is thin, not the conviction)
- **Entry band $21.00-22.50** (≈2.4-2.6x EV/S; the pre-bounce shelf). **Do not chase at 25.69.**
- Tranche: **0.30% at 22.50, 0.30% at 20.50. Cap 0.60%** of the $3.3M deployable (vs the 1.2% ruled
  cap — deliberately half, because e_fv edge is only +5.2% and the organic decomposition is unverified).
- **Not print-blocked** (09-03 is 31 days out) — but do not add inside the two weeks before it.

## Dated kills
- **2026-09-03 print:** revenue growth <24% yoy → kill the inflection thesis, exit.
- **2026-09-03:** if the 10-Q does not let organic be separated from OfferFit, cap the position at
  the first tranche permanently.
- SBC back above 19% of revenue for two consecutive quarters → kill.
- Diluted share count grows >5% yoy → kill.

## FREEZABLE CALL
**BRZE | 2026-09-03 — bar: reported Q2 FY27 revenue growth ≥25% yoy. our_p 0.72.**
