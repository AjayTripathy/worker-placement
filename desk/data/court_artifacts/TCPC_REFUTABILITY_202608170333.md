## Context

The pack ships `COHORT: ?` (cohorts.json unreadable from this session — permission not granted), so I triaged against the narrative the event context implies: a Finance-sector drawdown cohort priced on *"private-credit marks are fiction and the BDC dividend is fake."* TCPC's most recent print landed **2026-08-06** (10-Q + 8-K + Q2 PR) and carries an unusual asset for this test — a **dated third-party transaction price on 40% of the book**, which is the rare external same-event anchor that makes a mark-integrity claim falsifiable.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| TCPC | **DAMAGE-ARRIVING** | **Adjusted NII/share at post-transaction leverage** (≥$0.17 covering the dividend at ≤0.4x net leverage would refute); secondary: NAV/share vs the $5.90 pro-forma floor | NII $0.22 GAAP / $0.21 adj in Q2'26 = 124% coverage — **but at 1.38x leverage on a $1.3B book that is now $671M pro forma at <0.3x**. NAV $6.58 (6/30/26) ← $6.72 (3/31/26) ← $7.07 (12/31/25) ← ~$8.73 (9/30/25); company-disclosed transaction NAV hit **−10.4% / −$0.68** lands in Q3 → pro forma **~$5.90**. Non-accruals **improving**: 1.6% FV (2.8% Q1) but **7.4% at cost** (7.6% Q1). Regular dividend $0.34 (2024) → $0.29 (2025) → $0.25 (Q4'25) → **$0.17** (2026). [8-K 2026-08-06, acc. 0001193125-26-336845](https://www.sec.gov/Archives/edgar/data/1370755/000119312526336845/) · [10-Q 2026-08-06, acc. 0001193125-26-336794](https://www.sec.gov/Archives/edgar/data/1370755/000119312526336794/) | **2026-11-05 — yfinance-derived, UNCONFIRMED** | Damage is *arriving through the fix*: the deleveraging that repaired the balance sheet also removed ~half the earning assets. Magnitude unresolved because the Q3 10-Q is the first clean look at post-deal run-rate NII and at whether the retained 132 names carry the same ~10% over-mark the Pantheon trade implied. |

**Citation caveat (honest):** direct `sec.gov` document fetches 403'd from this harness (fingerprint-blocked). The **transaction terms are quoted from the primary 8-K text in the evidence pack**. The NAV / non-accrual / yield / pro-forma figures are triangulated across three independent reproductions of the same 8/6 press release and slide deck — [stocktitan](https://www.stocktitan.net/news/TCPC/black-rock-tcp-capital-corp-announces-second-quarter-2026-financial-llf53ex2g658.html), [investing.com slide summary](https://www.investing.com/news/company-news/blackrock-tcp-capital-q2-2026-slides-523m-portfolio-sale-cuts-leverage-93CH-4843790), [Q2'26 call transcript](https://www.investing.com/news/transcripts/earnings-call-transcript-blackrock-tcp-capital-posts-mixed-q2-2026-results-93CH-4843591) — and agree to the cent. A court must re-pull `tcpc-ex99_1.htm` and Ex-2.1 from EDGAR directly.

## The decisive reconstruction (pre-Q3, from public data only)

The bull and bear claims both resolve on one number nobody has printed yet: **post-transaction earning power.**

Calibrating on Q2 actuals — total investment income $40.0M/q on a $1.3B book (12.3% all-in), NII $18.1M → opex $21.9M/q, net debt ~$770M at 1.38x on $559M equity:

| | Q2'26 actual | Pro forma at <0.3x | Fully redeployed to 1.0x |
|---|---|---|---|
| Portfolio | $1.3B | **$671M** (co. stated) | ~$976M (+$305M capacity, co. stated) |
| Investment income /q | $40.0M | $17.6–20.6M | $26–29M |
| Interest + base fee + opex /q | $21.9M | $9.2–9.4M | $15.6M |
| **NII / share** | **$0.22** | **~$0.10–0.13** | **~$0.13–0.16** |
| vs $0.17 dividend | 124% | **59–78%** | **78–94%** |

**The $0.17 dividend does not survive the deleveraging** — not at 0.3x, and not even after 2–4 quarters of flawless redeployment back to 1.0x with zero new credit losses. Re-levering past 1.0x is precisely what the transaction was built to undo. A cut to ~$0.12–0.13 is the base case, and BDC dividend cuts de-rate price, which is why this is DAMAGE-ARRIVING rather than DAMAGE-ABSENT.

**The offsetting fact, and it is real:** Pantheon Ventures — an actual institutional buyer, not a mark — took $523M across 78 portfolio companies at *"95% of the gross fair value as of December 31, 2025."* Back-solving the disclosed −$0.68/share (−$57.8M) NAV hit against a $523M sale says the slice cleared at roughly **89–95 cents on TCPC's own carrying value** (the range depends on how much of the $58M is transaction expense versus mark haircut — unresolvable without Ex-2.1). The stock at $4.08 trades at **0.62x reported NAV / 0.69x pro-forma NAV**. An external buyer paid ~0.9x for 40% of the book; the tape pays 0.69x for the rest. That gap is the entire mispricing candidate, and it is anchored externally rather than to management's own marks.

## COURT-WORTHY (damage-absent, ranked):

**None.** TCPC does not clear the damage-absent bar. The narrative's predicted damage is present and measurable in the primary record: NAV −32% in four quarters, three dividend cuts in five, 7.4% of the book at cost on non-accrual, and a self-inflicted −10.4% NAV event booked into Q3. The one damage-absent *fragment* — non-accruals halving at fair value (2.8% → 1.6%) — is a marks artifact, not a recovery: the cost basis barely moved (7.6% → 7.4%), meaning the improvement is ~78% write-downs plus one $3.7M Thrasio restoration, not repayment.

It is nonetheless court-worthy on the **dispersion** leg, which is what this triage is for. TCPC is the cohort member where the narrative and a hard external contradiction of it are stapled together in the same 8-K, and where a discrete corporate action — the KBW strategic review, explicitly scoped to *"returning capital to shareholders, pursuing strategic combinations"* — can force the gap closed rather than waiting on it.

**What a court must resolve (all answerable from primary documents, none from opinion):**
1. **Mark integrity of the stub.** Compare the 78 CV names against the retained 132 in the 10-Q schedule of investments. Average CV position = $6.7M vs $13.9M retained — the vehicle took the *tail*, not a good-bank/bad-bank split. If the tail cleared at 0.9x, apply that to the concentrated stub and pro-forma NAV goes from $5.90 toward ~$4.90, at which point $4.08 is 0.83x and most of the discount is gone.
2. **The alignment tripwire, and it is damning so far.** With NAV at $6.58 and the stock at $3.78, TCPC repurchased **156,370 shares for $2.9M against a $50M authorization** in Q2. Buying back at 0.57x NAV is the single most accretive act available to this board, and they did ~6% of it. Post-transaction they hold $152M+ at <0.3x leverage. If the Q3 10-Q shows the same token pace, the strategic review is theater and the discount is the correct price of an externally-managed fee stream — fees accrue on *gross* assets, which redeployment restores and a return of capital destroys.
3. **The advisor conflict.** KBW is simultaneously the retained strategic-review banker and publishes a **$4.00 price target** (upgraded to Market Perform from Underperform on the news). Research is walled off in theory; a court should note that the only Street anchor on the name is set by the firm paid to find the exit.

**PRINT PROXIMITY: 2026-11-05 — yfinance-derived, UNCONFIRMED (no company PR names it; consistent with TCPC's 2026-05-07 and 2026-08-06 print cadence). ~56 trading days out, NOT within 5 trading days — the decisive print already landed 2026-08-06 and the stock has re-rated +10.3% on it (to $3.86, now $4.08).** No pre-print reconstruction is owed under the TEAM rule; the run-rate math above is supplied anyway because it is the number the November print will settle.

**Stance if forced today: FLAT.** No position is held, the catalyst is a bankers' process with *"no specific timetable,"* and the next hard datapoint — first post-transaction NII and the Q3 buyback pace — is ~11 weeks out. Nothing is lost by waiting for the one print that resolves the coverage question, and a 16.7% headline yield that the balance sheet cannot earn is a reason to wait, not to reach.

**COURT-WORTHINESS TCPC: 7/10** — a dated external transaction price on 40% of the book contradicts a 0.69x-pro-forma-NAV tape while the post-deleveraging NII math breaks the dividend, so the court's output swings the decision between never-own and a ~45%-to-NAV strategic-review event rather than merely re-rating an already-obvious discount.