# SignalOS Conditioning Layer — Spec

**Purpose.** The 120 existing connectors *find divergences*. This layer measures, per ticker, **how
discovered/crowded a name already is** — the no-edge "consensus" data whose job is **control, not alpha**.
It turns the suite from "find divergences" into "find *un-discovered* divergences, and map their
signal-to-price latency." It operationalizes, as a measured input, the thing we've been inferring by hand
all session ("already priced") and the gov-contract A/B's analyst-coverage axis (a conditioning variable that
worked). It is the **latency axis** of the SignalOS goal (masking × channel × **signal-to-price latency**).

## Architecture — two sub-layers + an aggregator

**A. Attention sub-layer** (retail + news attention; free; no standalone alpha):
- `stocktwits` — per-ticker message volume + bull/bear sentiment (StockTwits public API).
- `google_trends` — search interest (pytrends).
- `wikipedia_pageviews` — daily pageviews of the company's page (Wikimedia REST).
- `gdelt_news` — news-article volume/velocity (GDELT 2.0 DOC API). *Velocity, not sentiment.*
- *(Phase 2: `reddit_mentions` — WSB/investing mention counts; needs OAuth.)*

**B. Positioning sub-layer** (crowding; free; no standalone alpha):
- `sec_ftd` — fails-to-deliver (SEC bi-monthly CSV).
- `finra_short_interest` — reported short interest % of float (FINRA bi-monthly).
- *(Phase 2: `thirteenf_diff` — 13F position-change diff from EDGAR; `options_positioning` — OI/25Δ-skew via IBKR, systematizing the SPCX-by-hand work.)*

**C. The aggregator — `discovery_state(ticker, asof) -> dict`** (the contract every caller uses):
```
{
  "ticker": "RCAT", "asof": "2026-06-24",
  "attention_score": 0..1,      # composite percentile (name's own history + cross-section)
  "positioning_score": 0..1,    # short-interest% + FTD level (+ later 13F/options)
  "regime": "UNDISCOVERED" | "DISCOVERING" | "DISCOVERED_CROWDED",
  "components": { stocktwits:..., google_trends:..., wiki:..., gdelt:..., short_interest_pct:..., ftd:... },
  "confidence": "HIGH|MED|LOW", "asof_lags": {...}   # each source's own staleness
}
```
- **Scoring:** each component z-scored/percentiled vs the *name's own trailing history* AND cross-sectionally; attention_score = composite of A; positioning_score = composite of B.
- **Regime thresholds (pre-set, tunable):** `UNDISCOVERED` = attention <40th pctile AND short-interest <10% AND no FTD spike; `DISCOVERED_CROWDED` = attention >80th pctile OR SI >20% OR FTD spike; else `DISCOVERING`.
- Point-in-time honest: every component carries its own lag (StockTwits ~live; FINRA SI ~2-week lag; FTD ~1-month lag) — surface `asof_lags`, never backfill.

## The retrofit — market-researcher self-conditions

The market-researcher (and any thesis flow) calls `discovery_state` on every divergence candidate and:
1. **Self-filters:** tag a divergence **ACTIONABLE** only if `regime == UNDISCOVERED`; otherwise tag
   **"in discovery — skip or fade"** with the regime + components shown. (This is the data-level version of
   the A/B control that killed the CEF false positive.)
2. **Logs to the latency map** (`outputs/latency_log.jsonl`): every divergence at detection →
   `(ticker, divergence_type, source_connector, detection_date, attention_score, positioning_score, regime)`.
   Later a scoring job appends realized time-to-price. Over time this builds the empirical
   **signal-to-price-latency by (divergence type × regime)** table — the knowledge-graph payoff.

## Validation (Phase 1 acceptance)

Run `discovery_state` on: **SPCX & DXYZ** around their June attention spikes (expect DISCOVERED_CROWDED —
this is the case where price *led* the mark via attention); a deliberately **quiet small-cap** (expect
UNDISCOVERED); and **RCAT** (the live market-researcher candidate — tells us immediately whether the short
is already crowded/discovered or a real un-priced frontrun). The SPCX/DXYZ regime must come back high and the
quiet name low, or the scoring is mis-calibrated.

## Phasing

- **Phase 1 (this build):** the 4 attention + 2 positioning connectors (all free/tractable), the
  `discovery_state` aggregator, `source_atlas` registration, the `latency_log.jsonl` scaffold, and the
  validation above.
- **Phase 2:** add `reddit_mentions`, `thirteenf_diff`, `options_positioning` (IBKR); wire the
  market-researcher retrofit; start accruing the latency map.
