## SCM — refutability triage

Both framing premises of this re-court fail verification: SCM is **not** at 52-week lows (26.8% above them), and the rate channel the court wants to invert is indexed to **term SOFR**, not to the 30y/10y long end that moved on 9/1. Meanwhile the "easing kill" is no longer prospective — it was realized in two dividend cuts, the second one *during* the long-yield backup.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| SCM | **DAMAGE-ARRIVING** | Regular monthly distribution rate + NII/share coverage (the direct coupon-damage readout) | Cut twice in 2026: $0.1333→$0.1133/mo eff. Jan (Q1 $0.34), →$0.0833/mo eff. Jul (Q3 $0.25); shares −9.4% on 7/17/26. Q2 NII $0.26 vs $0.25 declared = 104% cover, only *after* cutting. CEO on cut #1: "reflects the lower interest rate environment" ([8-K ex-99.1](https://www.sec.gov/Archives/edgar/data/0001551901/000110465926088224/tm2621520d1_ex99-1.htm), [dividend record](https://stockanalysis.com/stocks/scm/dividend/), [247wallst](https://247wallst.com/investing/2026/05/06/stellus-capital-cuts-dividend-15-after-13-year-streak-16-6-yield-masks-coverage-trouble/)) | 2026-11-16 (yfinance-derived, UNCONFIRMED) | Damage is **confirmed and paid**, not absent — but magnitude of the *credit* leg is genuinely unresolved, hence ARRIVING not STRUCTURAL |
| SCM | *(credit sub-leg)* | Non-accruals % of cost / % of FV; risk-rating mix | 5 companies on non-accrual = **8.5% of cost, 5.4% of FV**; one *removed* in Q2, no new additions; 26% of loans rated 3-or-below, "asset quality slightly below plan" ([Q2 call](https://ca.investing.com/news/transcripts/earnings-call-transcript-stellus-capital-posts-mixed-q2-2026-results-shares-rise-93CH-4792642)) | 2026-11-16 | Implied mark on the bad bucket ≈ **60c** (derived, not cited: 5.4%×$970M FV ÷ 8.5%×~$1.015B est. cost) — much of the credit leg is already written down |
| SCM | *(NAV sub-leg — the one genuinely damage-absent metric)* | NAV per share QoQ | **Rose** $12.54 (3/31) → **$12.76–12.84** (6/30), +1.8–2.4% ([Q2 results](https://www.sec.gov/Archives/edgar/data/0001551901/000110465926088224/tm2621520d1_ex99-1.htm)) | 2026-11-16 | Price $8.66 = **0.677× NAV**. The narrative predicted NAV erosion; it did not arrive this quarter |

### The mechanism error that voids the re-court thesis

The event text argues higher-for-longer un-kills SCM by restoring the floating-rate coupon. That chain requires the **front end** to reprice. It cites the **long end** (30y 5.20%, 10y 4.68%).

- SCM's book is **92% floating**, indexed to 1M/3M/6M **Term SOFR** — the evidence pack's own 10-Q XBRL names `ThreeMonthTermSecuredOvernightFinancingRateMember` and `SixMonthTermSecuredOvernightFinancingRateMember`. A bear steepener in 10s/30s does not lift 3M SOFR.
- **Falsifying event:** SCM cut the dividend a second time on **2026-07-16**, i.e. *while* long yields were backing up. If the long-end selloff rescued NII, that cut does not happen when it did. Stated cause was the opposite of the thesis — borrowing costs squeezing spreads (NII $64.1M FY24 → $59.1M FY25).
- Higher-for-longer is **not** clean upside anyway: it lifts SCM's own facility cost and stresses LMM borrowers — the same borrowers already producing 8.5%-of-cost non-accruals.

### Two data traps worth flagging

1. **Screen yield is stale.** Vendors show $1.36 / **15.70%** (trailing, blends two pre-cut rates). Forward is $0.0833×12 = **$1.00 = 11.5%** at $8.66. Any screen ranking SCM on yield overstates it by ~36%.
2. **Tape premise false.** $8.66 close 8/31/26 vs 52w low $6.83 = **+26.8% off the low**, 26w high $10.13. The low was set around the 7/16–7/17 cut; the stock *recovered* on the 8/10 print. The ledger gate "52-week low breached — confirms the repricing is underway" is **stale and should be cleared**.

**COURT-WORTHY (damage-absent, ranked):** *none.* SCM does not qualify — the narrative's predicted damage is affirmatively present in the payout (two cuts) and in the credit book (8.5% of cost). The only damage-absent metric is NAV, which is one quarter of evidence against a multi-quarter thesis.

**COURT-WORTHINESS SCM: 5/10** — real open question at 0.677× NAV with the bad bucket already marked ~60c, but the court *as framed* would adjudicate a transmission channel (long-end → SOFR coupon) that the evidence falsifies, on a covered name (Hold consensus, $10.13 target, cuts widely written up) with no dated catalyst before November.

Below the ≥6 auto-escalate threshold — **do not spawn the full red/blue court on this framing.** Send back for re-specification: the answerable question is "does 0.677× NAV over-pay for a book with 8.5%-of-cost non-accruals already marked at ~60c," which is a credit/diligence court, not a rate-regime court.

**PRINT PROXIMITY: 2026-11-16 — yfinance-derived, UNCONFIRMED (no company PR names it; consistent with the Q2 cadence of a 7/29 preliminary 8-K + 8/10 10-Q). ~52 trading days out, so the ≤5-day print-decisive reconstruction is not triggered.**

Position, unprompted by a print: **FLAT maintained — but the prior FLAT's stated reason was wrong and should be replaced in the ledger.** It was ruled FLAT on prospective easing-driven coupon loss; the correct standing reason is realized coupon loss (−37.5% distribution since end-2025) plus an unresolved 8.5%-of-cost non-accrual book, against a NAV discount that is wide but not obviously mispriced on a crowded name. The genuine next catalyst is the **Q4 dividend declaration (~late October)**, ahead of the print — a third cut confirms STRUCTURAL; a held $0.25 with non-accruals flat is the first real evidence for the damage-absent case.

**Verification caveat:** sec.gov and data.sec.gov both returned HTTP 403 to every fetch in this session, and the IBKR tools were permission-gated, so I could not open the 10-Q or pull a live quote myself. Every figure above traces to the company's own press release/8-K exhibit or the Q2 call via mirrors, plus the 8/31 close from stockanalysis — not to a direct primary read. The evidence pack claims a full-fingerprint SEC fetch succeeded for the pack builder; that path is not available to the bench here, which is worth fixing before the next court.