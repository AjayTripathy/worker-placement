> Court lane: tier-2 small/misc EXHAUSTED tail (scores 17-39), COURT_QUEUE_20260804.
> Date 2026-08-03. Price basis: **IBKR daily close 2026-08-03, TRADES/RTH, ib_insync bars**.

# MUX — McEwen Inc. | 1/10 FRAME-REJECT (93% of the drawdown is GDXJ)
**live 17.83** (IBKR close 08-03) · cap ~$1.07B · **PRINTS 2026-08-05 — ENTRY BLOCKED**

**Name check:** the queue and the lane brief say "McEwen Mining." The entity is now **McEwen Inc.**
(renamed; NYSE MUX). Not material to the analysis, but the screen's label is stale.


## The gold-complex tape (the shared denominator for ARIS / MUX / SII)
Adjusted closes, 2026-08-03 vs the 52-week high:

| | last | 52w high | off high | 3m | 1y |
|---|---:|---:|---:|---:|---:|
| GLD | 371.54 | 495.90 (2026-01-29) | **−25.1%** | −12.2% | +20.2% |
| GDX | 74.10 | 115.84 (2026-02-27) | **−36.0%** | −14.9% | +42.3% |
| GDXJ | 95.39 | 156.19 (2026-02-27) | **−38.9%** | −17.3% | +50.1% |
| SIL | 73.75 | 117.87 (2026-02-27) | −37.4% | −16.7% | +56.9% |
| SLV | 52.36 | 105.60 (2026-01-28) | −50.4% | −23.3% | +55.9% |

**The entire precious-metals complex is 36-39% off a Jan/Feb-2026 spike high.** Every "quality
drawdown" in this cohort's PM names is dated to within a month of the GDX/GDXJ peak (ARIS 02-27 —
*the exact GDX peak day*; SII 03-10; MUX 01-28). Three names, one drawdown.

## (a) THE FRAME TEST — run first, as instructed, and it ends the case
Episode decomposition, **2026-01-28 (the MUX drawdown peak) → 2026-08-03**, pre-window 3y betas:

| proxy | beta (pre) | factor-explained | residual | factor share |
|---|---:|---:|---:|---:|
| GDX | 1.17 | −36.6% | **−2.5%** | **0.90** |
| **GDXJ** | 1.08 | **−37.6%** | **−1.0%** | **0.93** |
| SIL | 1.09 | −37.0% | −1.9% | 0.91 |

Total episode −40.5%. **Residual is −1.0% against GDXJ.** MUX is, to within a rounding error over
this window, a levered GDXJ tracker. **FRAME-REJECT.**

### The screen's method gives the OPPOSITE answer — and this is the sharper version of the ARIS defect
On the 3-year maximum-residual-drawdown method the generator actually runs, MUX scores
**residual share 1.52 vs GDX, 1.54 vs GDXJ, 1.68 vs GLD, 1.40 vs SIL** — i.e. **"anti-costume,"
genuinely idiosyncratic, do not demote.** The truth on the live episode is 0.90-0.93.
**The screen's method does not merely miss the costume on MUX; it certifies the opposite.**
Mechanism: MUX badly underperformed the gold complex in 2023-24 (Argentina/Los Azules-era
write-downs), so its 3-year cumulative residual drew down *more* than its price ever did. The test
is measuring old idiosyncratic pain, not the current drawdown.

**Recommended fix (both names):** compute `factor_costume` on the **drawdown episode window**
(peak date → today) with the beta fitted on data **before** the window, and consult an
**industry**→proxy map (`Gold / Other Precious Metals & Mining → GDXJ`) before the sector map.
Validation targets: ARIS 0.73 → 0.90, MUX 1.54 → 0.93; both then demote by the existing 0.30 factor
and neither reaches the queue.

## (b) PATH CHECK
52w low 9.88 (2025-08-19, 346 days) → **+80.4% off the low**; 52w/3y high 29.05 (2026-01-28) →
**−38.6%**; +5.6% off the 60-day low; 3m −20.2%; YTD −6.6%.
**EXHAUSTED = MECHANICALLY WRONG** (fired on `HARD_OFF_LOW`; MUX is 39% below its high and 6% above
its 60-day low). The reject is the factor, not the path.

## (c) ESTIMATE DIRECTION — the worst in the cohort
FY+1 consensus EPS **3.32 vs 4.99 90 days ago = −33.5%**; FY0 2.13 vs 2.055. The 7-day change is
also negative (3.32 vs 3.395). The `eps_trend` series contains **0.00 placeholders** in the 0q
column at 30d and 90d — thin coverage, so treat the level as noisy while the *direction* is clear.

## (d) BUSINESS — a copper development option inside a gold-miner wrapper, funded by paper
- **McEwen Copper / Los Azules**: a **US$2.4B** development loan being arranged (05-12). This is the
  actual asset value driver and it is a multi-year, financing-dependent, Argentina-jurisdiction call
  option — not a "quality business at a discount to its own history."
- **Serial equity-funded M&A**: Golden Lake Exploration (01-28), Canadian Gold combination with
  **1.53M shares to the CEO** (07-29), an Iconic Minerals JV (04-15), a PhotonAssay lab deal (08-03).
  Consolidation paid in stock at a 39%-off-the-high price.
- Gross margin 36.5% — the screen's `MIN_GROSS_MARGIN 0.35` gate passed this by 1.5 points, on a
  miner, where gross margin is a spot-price artifact rather than a quality signal. **A gross-margin
  quality gate is not meaningful for extractive industries** — worth a sector carve-out.

## Scenarios (gold-price scenarios)
| | p | fv | logic |
|---|---|---|---|
| bear | 0.40 | 11.00 | GDXJ retests, Los Azules financing slips, more stock issued |
| base | 0.40 | 18.00 | metal flat, San José/Gold Bar deliver |
| bull | 0.20 | 30.00 | gold re-rates and Los Azules is financed |

**e_fv $17.60 vs $17.83 → edge −1.3%.**

## VERDICT — 1/10 FRAME-REJECT
Print-blocked (08-05) and frame-rejected. Same routing as ARIS: the gold-complex drawdown is a
sleeve decision, not a stock pick — and if it were a stock pick, a levered developer paying for
acquisitions in discounted stock is the wrong expression.
