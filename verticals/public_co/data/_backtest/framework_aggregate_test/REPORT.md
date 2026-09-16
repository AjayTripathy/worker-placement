# Framework Aggregate Alpha Test — Preliminary

_Test run 2026-05-18. Methodology: each of the 18 dual-gate + DA-filtered
emit names from current cohort matrices, paired against its sector ETF
using yfinance.info.sector classification, return measured from 10-K
filing date to 2026-05-18._

## Caveat upfront

This is a **short-window preliminary read, not a validated 12-month
forward test.** Forward windows range from 11 to 160 days (most 50-100
days). Annualized figures included for context only — they're not
statistically meaningful at these horizons.

The proper version of this test requires either (a) waiting 8-11 months
for the 12-month windows to complete, or (b) re-running the full
Phase 1 → 2 → 3 pipeline at a historical cutoff (e.g., May 2025) so the
emit list is generated AS OF the historical date, which is a meaningful
LLM/API budget.

## Results

n=16 emit names (2 dropped — SAVA and LAC had no available filing date
via EDGAR submissions API).

| TK    | cohort    | ETF  | days | name_R   | etf_R  | pair P&L  | annualized |
|-------|-----------|------|-----:|---------:|-------:|----------:|-----------:|
| ARQQ  | quantum   | XLK  |  160 | -57.9%   | +17.2% | **+75.1%** | +258.9%   |
| MVST  | ssbattery | XLY  |   63 | -46.5%   |  +4.0% | +50.6%    | +970.5%   |
| KSCP  | robotics  | XLI  |   52 | -40.7%   |  +6.9% | +47.6%    | +1438.2%  |
| SES   | ssbattery | XLY  |   75 | -39.8%   |  +0.3% | +40.0%    | +415.0%   |
| RGTI  | quantum   | XLK  |   75 |  -9.0%   | +23.9% | +32.9%    | +299.3%   |
| QBTS  | quantum   | XLK  |   81 |  -8.1%   | +22.8% | +30.9%    | +236.8%   |
| SLDP  | ssbattery | XLY  |   82 | -27.6%   |  -0.3% | +27.3%    | +192.4%   |
| AIRO  | defense   | XLI  |   48 | -20.9%   |  +5.2% | +26.1%    | +483.6%   |
| CIFR  | dcpivot   | XLK  |   83 |  +7.2%   | +23.5% | +16.2%    | +93.6%    |
| IREN  | dcpivot   | XLF  |   11 | -13.8%   |  -0.0% | +13.8%    | +7189.9%  |
| AEVA  | lidar     | XLK  |   59 | +33.5%   | +28.0% | -5.4%     | -29.1%    |
| EDIT  | cellgene  | XBI  |   70 |  +9.5%   |  +0.5% | -9.0%     | -38.7%    |
| OUST  | lidar     | XLK  |   77 | +44.4%   | +24.1% | -20.3%    | -65.8%    |
| RDW   | space     | XLI  |   80 | +51.8%   |  -3.7% | -55.5%    | -97.5%    |
| BLDP  | hydrogen  | XLI  |   67 | +67.0%   |  +3.2% | **-63.7%**| -99.6%    |
| FCEL  | hydrogen  | XLI  |  151 | +79.1%   | +10.8% | **-68.4%**| -93.8%    |

**Summary stats:**
- Hit rate: **10/16 = 62.5%** (10 names underperformed their sector)
- Mean pair P&L: **+8.65%**
- Median pair P&L: **+21.2%**
- 3 catastrophic losers (BLDP, FCEL, RDW all >−55%)
- 5 substantial winners (>+30%)

## What this suggests

1. **The framework's emit list has a real positive directional signal**
   over a short forward window. 62.5% hit rate and +21% median pair P&L
   over 2-3 months is meaningfully better than random.

2. **Hydrogen / fuel-cell names are a structural failure mode.** Both
   BLDP and FCEL were strong-conviction emits (composite 1.22 and
   1.00, with hard contradictions: BLDP's Weichai exit, FCEL's 2-SEVERE
   pattern). Both went up +67% and +79% against +3-11% sector ETFs.
   The framework was correct about fundamentals but wrong about
   sector narrative — H2/fuel-cell stocks have rallied on AI/data-
   center power demand narratives in 2026, regardless of the bear
   thesis on disclosure quality or operational underdelivery.

3. **Catalyst-rally sectors are the consistent risk pattern.** This
   matches the AIRO-signature backtest's biotech blowup (IMMX +375%,
   ARDX +590%): the framework's disclosure-quality signal can't see
   sector-wide narrative tailwinds. Same mechanism, different sector
   each year.

4. **The basket-level portfolio number at 3% cap** = 0.03 × 16 × +8.65%
   ≈ **+4.15%** over the average 2-3 month window. Comparable to long
   IWM (~+10-15% over same period). So we're not beating the index
   even with the median signal working — the hydrogen blowups
   compress the mean to "below benchmark with downside risk."

## What it doesn't yet establish

- **Statistical significance.** n=16 with noisy short windows isn't
  enough to distinguish "framework has alpha" from "small-cap shorts
  generally mean-revert in 2-3 months after 10-K filings."
- **12-month durability.** ARQQ at +75% in 160 days could be lucky
  timing; the proper test is at 365 days.
- **Survivorship.** No names from the emit list have delisted in
  this window (yet); the proper test needs to handle eventual
  bankruptcies.

## The proper test, if you want to commit

To rigorously distinguish "framework alpha" from "factor exposure":

**Option A — Wait.** Lock in the emit list as of today (which we've
just done in `emit_list.json`). Re-measure at 2027-05-18 with full
12-month forward data. Single point with no historical replication.

**Option B — Historical re-run.** Pick a cutoff that's >12 months ago
(e.g., May 2025), use SEC submissions API to find each cohort
ticker's most recent 10-K before that date, run the full Phase 1
(planner LLM) → Phase 2 (M-source queries) → Phase 3 (scoring) pipeline
against those historical filings, apply the current emission rule, and
measure 2025-05 → 2026-05 returns.

Option B is the cleanest. Cost: 20-30 ticker × planner subagent + M-source
queries + scoring + forward-return fetch. Estimated 1-2 hours of LLM
parallelization + budget for EDGAR / FDIC / EPA API calls.

## Tentative interpretation

The short-window snapshot is *mildly encouraging* — 62% hit rate and
+21% median pair P&L suggest the framework's aggregate emit list isn't
pure factor noise. But the 3 catastrophic losers (FCEL, BLDP, RDW)
demonstrate that disclosure-quality + operational-capacity signals
can't predict sector-narrative rallies. The framework's edge is
real-but-modest, and only matters if you can survive the narrative
blowup risk via tight per-name size caps.

The +4% portfolio P&L vs IWM +10-15% over the same window says: the
framework as currently calibrated **underperforms the broad index**
even with sector hedging. To be deployable, it'd need either:
- A better mechanism for filtering out narrative-rally-vulnerable
  cohorts (hydrogen 2026, biotech 2024, AI/quantum 2025)
- Combination with other alpha sources to lift the mean above index
- Acceptance that this is one factor in a larger model, not a
  standalone strategy

The honest characterization remains what we said earlier: this is a
**deployable risk factor with modest positive expected return**, not
a market-beating strategy on its own.
