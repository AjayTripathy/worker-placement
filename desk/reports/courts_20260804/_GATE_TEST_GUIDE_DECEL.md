# GATE TEST — the GUIDE-DECEL flag (tier-2 consumer/health/comm cohort, 7 names)
Court lane 2026-08-03 (grading for the 08-04 session). Prices: IBKR live/close 2026-08-03.

## What the gate actually computes
From `verticals/generators/quality_drawdown.py` L236-248:

    fwd_rev_growth = revenue_estimate.loc["+1y","growth"]   # consensus FY+1 revenue growth
    trail_rev_growth = info["revenueGrowth"]                # MOST RECENT QUARTER, yoy
    guide_ratio = fwd_rev_growth / trail_rev_growth
    guide_flag = guide_ratio < 0.60

The queue describes it as "forward revenue growth <60% of trailing, so the de-rate may be tracking
estimates down." That is NOT what the code measures. The denominator is a **single quarter's** yoy
growth; the numerator is the **next fiscal year** (12-24 months out). It is a mean-reversion
detector across two non-comparable tenors, not an estimate-revision detector.

Two structural consequences:
1. **It cannot NOT fire on a fast grower.** A 60%-growth quarter requires FY+1 consensus above 36%
   to clear the bar. Consensus never extrapolates 36%+ two years out. RDDT/SE fire mechanically.
2. **Any one-off in the denominator manufactures a fire.** NVO's trailing +24% is a 340B
   rebate-reserve REVERSAL. ELE's +109% is a 160% share issuance for M&A.

## Result — 7/7 fired; on the gate's STATED meaning, 1/7 is a true positive
Estimate trajectory measured from `yfinance eps_trend` (consensus EPS now vs 90 days ago):

| name | trailing (mrq yoy) | fwd FY+1 rev | ratio | FY+1 EPS est, 90d chg | gate's claim true? |
|---|---|---|---|---|---|
| NVO  | +24.0% (Q1'26, 340B reversal) | +2.1%  | 0.09 | -3.1% | INPUT CONTAMINATED |
| REGN | +16.7% (Q2'26) | +8.3%  | 0.50 | **+4.5%** (FY26e +13.4%) | FALSE FIRE |
| SE   | +46.6% (Q1'26) | +21.4% | 0.46 | **+4.9%** | FALSE FIRE |
| RDDT | +61.1% (Q2'26) | +31.4% | 0.51 | **+9.3%** (FY26e +8.0%) | FALSE FIRE |
| DUOL | +26.5% (Q1'26) | +13.9% | 0.53 | **-3.1%** (FY26e -5.4%) | TRUE POSITIVE |
| ELE  | +109% (Q1'26, inorganic) | +6.3% (n=1) | 0.06 | **-37.6%** | right answer, wrong mechanism |
| OTEX | +2.2% (Q3FY26) | +0.6% | 0.25 | **+1.4%** (FY26e +2.1%) | HALF-TRUE (revenue yes, EPS no) |

Precision on "estimates are tracking down": **1/7 clean (14%)**, 2/7 generous (29%).
The gate is doing useful work — it flags *something* — but it is flagging **growth normalisation**,
which is what every fast grower does, not **estimate deterioration**, which is what the
de-rate-vs-derailment test needs.

## Proposed replacement (narrow, high-precision, free)
Swap the tenor-mismatched ratio for the direct measurement:

    DERAIL flag  <=  consensus FY+1 EPS is DOWN more than 3% over the trailing 90 days
    (source: yfinance Ticker.eps_trend, columns current vs 90daysAgo — free, no API key)

On this cohort that flags DUOL (-3.1%), ELE (-37.6%) and marginally NVO (-3.1%), and clears
REGN/RDDT/SE/OTEX — which is exactly the HUBS/CTSH/SAP winner signature the frame is hunting
(multiple compressed on stable-or-rising estimates). Keep the existing ratio as a *separate*
`GROWTH-NORMALISING` note, not as a score penalty (`raw *= 0.65` at L334 is currently penalising
RDDT and SE for the crime of having grown 50-60% last quarter).

## Second defect found in the same pass
`revenue_estimate` is unvalidated. For ELE the current-quarter consensus revenue is **$21,585,000,000**
against an actual quarterly revenue of **$24.3M** — a ~900x error carried straight into the flag.
Add a sanity gate: reject any consensus revenue more than 5x the trailing-twelve-month actual.

## Third: cohort mis-mapping
ELE was queued into "consumer/health/comm". It is **Elemental Royalty Corp**, a precious-metals
royalty company (Basic Materials, Canada, Nasdaq conid 831070874). Sector came from the screen's own
`info["sector"]` field, which was available and says "Basic Materials" — the cohort label was
assigned upstream of it.
