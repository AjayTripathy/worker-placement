# deal_cycle — IPO/M&A deal-cycle frontrun stack (the DFIN catalyst)

Built 2026-06-27. Detects (does **not** forecast) the deal-cycle turn via leading indicators, and tests
whether they actually frontrun DFIN's stock. READ-ONLY — prints/logs, never an order.

## Modules
| File | What it pulls | Role |
|---|---|---|
| `edgar_pipeline.py` | EDGAR master.idx monthly counts: DRS/S-1 (IPO), 424B4 (pricing), S-4/DEFM14A (M&A), Form D (private) | the DIRECT pipeline — DFIN's forward revenue. Censored by filing Date-Filed (no look-ahead). |
| `conditions.py` | FRED HY OAS / IG OAS / VIX | the financing GATE (necessary condition) |
| `bdc_originations.py` | BDC 10-Q Schedule-of-Investments (reuses `engine/bdc_soi.py`) | private-credit deployment = M&A financing supply (best-effort, quarterly) |
| `lead_lag.py` | composite vs DFIN forward returns | **the decisive frontrun test** |
| `monitor.py` | all of the above | regime gauge (FROZEN/THAWING/OPEN-BUT-LATE/OPEN) + DFIN trigger; appends `deal_cycle_log.jsonl` |

Run: `python3 -m verticals.frontrun_engine.deal_cycle.monitor [--no-bdc]`

## The honest finding (lead_lag.run, 2021–2026, n=37 months)
**The deal-pipeline does NOT positively frontrun DFIN's stock.** Correlation of the pipeline-composite's
monthly change vs DFIN forward returns is weakly **NEGATIVE at every lag** (−0.13 at 1m → −0.40 at 6m).
Interpretation: DFIN's equity already prices the deal-cycle narrative, so a filings SURGE is a late-cycle
/ buy-the-top signal, not a buy. If anything the relationship is **contrarian** — the better DFIN entry is
gate-open + pipeline **depressed/troughing**, not surging. Same outcome class as the MAUDE pilot (public
stream doesn't lead the price). Caveats: modest sample, dominated by the 2021 IPO boom-bust, single name.

**Consequence:** the monitor's regime gauge is a valid **revenue/context** tool, but there is **no validated
equity frontrun trigger** — `equity_frontrun_validated = False`. The trigger is therefore framed
contrarian/honest (AVOID-CHASE on a hot pipeline; WATCH-FOR-TROUGH when the funnel thins).

## Live read (2026-06-27)
GATE **OPEN** (HY 2.78%, VIX 18.9) · IPO-lead trend −15%, **DRS funnel THINNING −15%**, M&A −19% →
**REGIME: OPEN-BUT-LATE** · DFIN: **WATCH-FOR-TROUGH**. Financing is wide open (so the deal-freeze is
cyclical, not a credit problem — supports DFIN's risk being reversible unlike BAH), but the forward funnel
is thinning, so it's late in *this* leg — don't chase; the contrarian entry sets up as the funnel troughs.

## Three tests, all negative for a tradeable equity edge (the honest full result)
1. **`lead_lag.py` (stock):** pipeline-composite change vs DFIN forward returns — weakly NEGATIVE at every
   lag (−0.13 → −0.40). Not a frontrun; the stock already prices the cycle.
2. **`revenue_test.py` (pipeline → DFIN REVENUE):** pipeline-YoY vs DFIN total-revenue-YoY ≈ 0 at all
   lags (+0.09 / +0.02 / −0.21 / −0.03, n≈30 quarters). **No lead even on revenue** — but CAVEAT: this used
   TOTAL revenue, which is dominated by recurring software (~47%) + the secular print decline + the
   Investment-Companies segment, so the deal-driven *transactional* slice is drowned out. The fair test is
   the **Capital-Markets transactional segment** (dimensioned XBRL) — still open; though DFIN's own
   share-loss to its software products may mean even the segment won't track market-wide filing volume.
3. **`contrarian_test.py` (more cycles, 2017-26, point-in-time trailing-36m rank):** depressed-vs-hot
   pipeline tercile → DFIN fwd returns **conflict across horizons**: fwd 3mo & 6mo favor the HOT tercile
   (+11.5% / +19.4% vs depressed +2.5% / +10.4% = mild *momentum*), 12mo mildly favors depressed (+42% vs
   +36%), and the gate-conditioned subsample flips contrarian (+11.7% vs −11.1%) but on n=6/13. Signs
   conflict, buckets are small, 2021 dominates → **NOT robust** in either direction.

**Net:** the pipeline is a clean DESCRIPTIVE regime gauge but has **no validated tradeable edge on DFIN** —
not as a stock frontrun, not on total revenue, not as a contrarian/momentum timing signal. `monitor.py`
therefore emits NO equity trigger, only the regime. This is the 4th frontrun pilot to die on its lead-lag
gate — the discipline working as designed (we built it, tested it three ways, and it honestly says "no edge").

## What IS validated / usable
- The financing GATE (HY/VIX) and pipeline counts are clean, real, censoring-correct.
- The REGIME read has standalone value: GATE OPEN (financing available) means a deal-slowdown is CYCLICAL,
  not a credit freeze — which is the evidence that DFIN's risk is reversible, unlike BAH's structural reset.
- Remaining open thread (low priority): the Capital-Markets *transactional-segment* revenue test (#2 done
  right). Everything else is honestly closed.
