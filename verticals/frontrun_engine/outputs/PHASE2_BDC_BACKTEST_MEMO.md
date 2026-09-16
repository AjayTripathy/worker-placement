# Frontrun Engine — Phase 2 BDC spread/event-driven backtest (Arm-A, properly powered)

**As-of 2026-06-24.** PILOT_SPEC §1/§4/§6/§7, amendments A-1/A-2/A-4/A-5. Primary sources: SEC
EDGAR inline XBRL (printed NAV + Schedule of Investments, 10-Q/10-K), FRED BAMLH0A0HYM2 (HY OAS
daily), IBKR (prices, live + monthly history). No fabricated NAVs/spreads/holdings; point-in-time,
no look-ahead. Code: `build_bdc_panel.py`, `run_bdc_backtest.py`, `bdc_controls.py`,
`bdc_convergence_run.py`; engine `engine/bdc_soi.py` (`bdc_derived_nav` / `remark_book`).

## Verdict: §7 FAILED — "moat real, but already priced."

The aggregation/timing **moat is confirmed** (BDC NAV is a quarterly, ~45-day-lagged print with no
continuous mark between filings). But the **spread-driven frontrun edge does not exist**: the
derived-NAV signal does not predict the next printed NAV at the honest sample size, and the discount
reprices with credit in real time — no faster than zero-credit equity CEFs. `edge(BDC) − edge(control)`
is **not positive and not significant**.

## The panel (point-in-time, primary XBRL)

6 BDCs × ~11 quarters = **N = 63 (BDC, quarter) events**; **effective independent N ≈ 11 quarters**
(see confound C2). Window 2023-Q3 .. 2026-Q1.

| BDC | quarters parsed | L3% (moat) | NAV reconstruction |
|-----|----------------:|-----------:|--------------------|
| ARCC | 11 | 96.5–97.8 | filed NAV reproduced to <$0.005 |
| GBDC | 11 | ~100 | clean |
| OBDC | 10 | 93.5–96.4 | clean-to-usable |
| PSEC | 10 | 99.4–99.7 | usable |
| FSK  | 11 | 84.6–89.2 | NAV from balance sheet reliable; holdings-list tie noisy |
| MAIN | 11 | 99.6–100  | NAV reliable; holdings-list tie noisy |

All six classify Arm A (L3 ÷ total investments ≥ 50%). Filing lag confirmed: 10-Q ~34–41d, 10-K
~49–59d — the ~45-day lag the setup describes.

## Materiality gate (A-2 / §4 amendment, logged pre-scoring)

The locked **5% NAV gate is unreachable on the credit channel**: a 5% move on a ~100%-L3 floating-rate
book needs ≈400 bp of quarter-end-to-quarter-end spread move (smoothing 0.5, spread-duration 2.5y). The
**largest QoQ HY-OAS move in 3 years was ~63 bp** (2024-Q4→2025-Q1). It fired **0** real events (the one
"5% fire" is a MAIN holdings-list tie-out artifact, excluded). Logged secondary: a **BDC-scaled 1% gate**
(≈2× a typical quarterly NAV move) fires 23 events. The locked test is preserved and reported.

## (a) Direction hit-rate vs the >65% bar

| measure | hit-rate | N | sign-test p |
|---|---:|---:|---:|
| naive, all events | 61.9% | 63 | 0.077 |
| BDC-scaled 1% subset | 69.6% | 23 | — |
| per-BDC detrended | 68.3% | 63 | 0.005 |
| **honest, quarter-clustered** | **63.6% (7/11)** | **11** | **0.55** |

The naive/detrended numbers are inflated by **pseudo-replication**: the signal is ~monotone in a single
HY-OAS quarter move that is *identical across all 6 BDCs*, so 63 events are really ~11 correlated quarter
bets. At the honest N, the signal got **7 of 11 quarter-directions** right — coin-flip (p=0.55). It **fails
the 65% bar** and fails significance.

## (b) Magnitude — essentially zero

Derived-surprise vs realized printed-NAV move: **corr 0.16, R² 0.03** (detrended corr 0.23). The signal
does not predict the size of the next print.

## (c) Convergence + net P&L — nothing to capture

There is **no spread-driven gap in the lag window to frontrun**. The contemporaneous quarterly
price-return-vs-spread-move correlation is strongly negative — the discount reprices *as spreads move,
before the print*:

| | ARCC | GBDC | OBDC | FSK | MAIN | PSEC | **ADX (ctrl)** | **USA (ctrl)** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| corr(qtr price ret, spread move) | −0.66 | −0.49 | −0.45 | −0.48 | −0.70 | +0.08 | **−0.68** | **−0.82** |

Borrow/bid-ask is moot (no edge); liquidity is fine (ARCC bid/ask ~0.2%, PSEC ~0.4%); BDCs trade at
discounts so the trade would be long-side, no squeeze flag.

## edge(BDC) − edge(control) — the §7 primary

- **edge(control ADX/USA) = 0 by construction** — daily NAV already embeds holding moves; there is no
  quarterly-filing-lag NAV, so no analogous frontrun window.
- **The confound that kills it:** the BDC price→spread correlation (ARCC −0.66, MAIN −0.70) **does not
  exceed** the zero-credit equity CEFs (ADX −0.68, USA −0.82). So "spreads move → BDC price moves" is
  **generic risk-off beta**, not a BDC-NAV computation edge. This is exactly the spec's kill case: it's the
  CEF risk-factor, not our moat.
- **Placebo:** the real quarter hit-rate sits at the **78th percentile** of sign-shuffled spread signals
  (need <5th). Not distinguishable from random.

## Power + confound caveats (stated, not overclaimed)

- **Low power.** 2023–26 spreads were quiet; max QoQ HY-OAS move ~63 bp. The famous April-2025 tariff
  spike (HY OAS 4.61 on 4/07) **round-tripped to 2.96 by quarter-end**, so it never reached a printed
  mark — BDC marks key off quarter-end levels and mean-reverting intra-quarter spikes wash out.
- **Idiosyncratic marks dominate.** The decisive evidence is 2025-Q2: spreads *tightened* 59 bp (signal:
  NAV up) but FSK printed **−6.2%** and PSEC **−9.5%** on name-specific write-downs — the signal was
  **anti-predictive** in the quarter that mattered. A broad spread index cannot see single-name credit
  deterioration, which is where BDC quarterly NAV moves actually come from.

## Microstructure encoded (the durable product)

- **Masking channel:** quarterly printed NAV, ~45-day 10-Q filing lag, no continuous mark.
- **Signal channel:** credit-spread re-mark of the floating-rate loan book (models the official mark).
- **Signal-to-price latency:** ≈ZERO for the spread component — the discount is *already* forward-looking
  and reprices contemporaneously with credit, at no greater rate than a zero-credit equity CEF. The
  exploitable residual (idiosyncratic per-name marks) is **not observable from a spread index**, so it is
  not frontrunnable by this engine. The BDC moat is real but the spread channel is *priced*; any genuine
  BDC frontrun would require per-name private-credit event data (defaults/restructurings/marks), i.e. the
  A-4 event channel applied name-by-name — which the spread index is a poor proxy for.

## Files
- `outputs/bdc_panel.json` — the point-in-time BDC×quarter NAV/L3/spread panel.
- `outputs/phase2_bdc_backtest.json` — verdict + headline stats summary.
- `outputs/phase2_bdc_backtest_full.json` — per-quarter rows + controls + convergence.
- `outputs/phase2_bdc_controls.json` — detrend / cluster / placebo controls.
- `outputs/phase2_bdc_convergence.json` — contemporaneous price-vs-spread + control arm.
