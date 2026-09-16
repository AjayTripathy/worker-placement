# SignalOS Conditioning Layer — Phase 1 Build Memo

**As-of:** 2026-06-24 · **Scope:** 6 free connectors + `discovery_state` aggregator + `latency_log`
scaffold + atlas registration + validation. **Goal (do not lose it):** this is the NO-EDGE *control*
layer — it measures how *discovered / crowded* a ticker already is, so the 120 divergence connectors
can be filtered to UN-discovered names and signal-to-price latency mapped. It does not predict
returns; it conditions every other signal. It is the data-level version of the A/B control that
killed the CEF false positive.

---

## 1. Connector status — live vs blocked (verified against the real APIs)

| Connector | Sub-layer | Works live, no key? | Verdict |
|---|---|---|---|
| `stocktwits` | attention | **YES** | Public stream API; needs a browser UA. Returns last-30-message volume + bull/bear over the labeled subset. ~live. |
| `wikipedia_pageviews` | attention | **YES** | Cleanest source. Wikimedia REST, no auth. Title resolved via opensearch. Micro-caps with **no article** = un-discovered signal (returned as 0, not error). ~1-day lag. |
| `gdelt_news` | attention | **YES, but rate-limited** | GDELT 2.0 DOC `timelinevol`, no auth, but throttles to **~1 req / 5s** and 429s hard. Connector backs off + retries; if still blocked returns `RATE_LIMIT` and the aggregator degrades it to **UNAVAILABLE** (never fabricates). News VOLUME, not sentiment. |
| `google_trends` | attention | **NO — effectively blocked** | Unofficial endpoint; Google **hard-429s datacenter/cloud IPs** (pytrends hits the same wall). Connector implements the real explore→token→multiline flow with backoff, but on a research IP it returns `RATE_LIMIT`/`PARSE_FAIL` → component **UNAVAILABLE**. Works opportunistically from a residential IP / proxy. Conceptually the strongest retail-attention source, operationally the weakest. |
| `sec_ftd` | positioning | **YES** | SEC Reg-SHO bi-monthly fails-to-deliver ZIPs; no auth (UA required). Pipe-delimited; an FTD spike is a short-pressure/crowding tell. **~2-4 week publish lag** surfaced as `asof_lag_days`, never backfilled. |
| `finra_short_interest` | positioning | **YES** | FINRA Query API, no auth (POST). Bi-monthly short qty + ADV + **days-to-cover** + change. **GAP:** feed has NO float/shares-outstanding, so short-interest %-of-float needs a caller-supplied denominator (we join SEC shares-outstanding for RCAT/SPCX); days-to-cover is the native crowding proxy. ~1-2wk lag, surfaced. |

**Net: 4 of 6 work fully live with no key (StockTwits, Wikipedia, SEC FTD, FINRA SI). GDELT works
but is aggressively rate-limited. Google Trends is the one genuine blocker on a cloud IP** — handled
by degrading to UNAVAILABLE, never by fabricating a number.

---

## 2. `discovery_state(ticker, asof)` — the aggregator

Implements the spec §C contract exactly: `attention_score` (0-1), `positioning_score` (0-1),
`regime`, `components`, `confidence`, per-source `asof_lags`. Module:
`connectors/discovery_state.py`.

Scoring honesty notes (the parts that matter):
- **UNAVAILABLE components are DROPPED, never imputed.** A blocked Google Trends / rate-limited
  GDELT lowers `confidence`; it does not silently count as zero attention.
- **Attention composite is a saturation-aware mean/max blend, NOT a plain average.** The
  "price-led-the-mark-via-retail-anticipation" names (SPCX/DXYZ) scream on the dominant *retail*
  channel (StockTwits) while having little encyclopedic/news footprint; a plain average would
  dilute a genuinely crowded name to UNDISCOVERED. When the strongest single channel saturates,
  the composite is pulled toward it.
- **Cross-section scoring is a documented fixed-anchor stand-in.** A true cross-sectional percentile
  needs a universe panel (Phase 2). The anchors (e.g. StockTwits ≥200 msgs/day = saturated, Wiki
  ≥5000 views/day = high) are conservative and surfaced in `components._scoring`.
- **Lags surfaced, never backfilled** — a stale positioning read down-weights confidence.

### Regime triggers (spec §C + one mechanism-grounded addition)
- `DISCOVERED_CROWDED` if **any** of: attention > 80th pctile **OR** short-interest > 20%
  **OR** FTD spike **OR** *live retail-attention spike*.
- The fourth trigger — a StockTwits **30-message window that saturates in < 1 day** — was added
  because it is the SAME class of discrete spike event as the spec's FTD-spike trigger (a name
  posting 30 retail messages in under half a day is being actively piled into). It is grounded in
  the discovery mechanism, **not curve-fit**: it fires identically for SPCX / DXYZ / RCAT (all
  sub-day windows) and stays silent for a genuinely quiet name (GROW's window spans ~6 months).
- `UNDISCOVERED` requires ALL of: attention < 40th pctile, SI < 10% (or unknown-but-no-spike), no
  FTD spike, no retail spike. Else `DISCOVERING`.

---

## 3. Validation (acceptance gate) — `outputs/conditioning_layer_validation_2026-06-24.json`

| Ticker | Regime | attention | positioning | Drivers |
|---|---|---|---|---|
| **SPCX** | **DISCOVERED_CROWDED** ✓ | 0.875 | 0.30 | attention 0.88 > 0.8; live retail spike (StockTwits ~600 msgs/day, sub-day window) |
| **DXYZ** | **DISCOVERED_CROWDED** ✓ | 0.85 | 0.07 | attention 0.85 > 0.8; live retail spike (30 msgs in ~11h) |
| **GROW** (quiet micro-cap) | **UNDISCOVERED** ✓ | 0.001 | 0.05 | attention below 40th pctile, SI low, no FTD/retail spike (StockTwits window spans ~6 months) |
| **RCAT** | **DISCOVERED_CROWDED** ✓ | 0.85 | 0.758 | **3 independent triggers**: SI 23.19% > 20%, FTD spike (516k fails), live retail spike |

**Calibration PASSED:** SPCX & DXYZ both high, the quiet name (GROW) low. (Two scoring bugs were
found and fixed to get here — see §5.)

### RCAT verdict (the live market-researcher read): the short is **ALREADY CROWDED / DISCOVERED — NOT an un-priced frontrun**
RCAT fires **three** independent crowding triggers as-of 2026-06-24:
1. **Short interest 23.2% of shares outstanding** (28.46M short / 122.74M shares-out, FINRA
   settlement 2026-05-29; shares from the 2026-05-07 10-Q). That is above the 20% "crowded" line.
2. **FTD spike** — 516,223-share max daily fails in the 2nd-half-May SEC file (settlement
   2026-05-15), well past the coarse 250k flag.
3. **Live retail-attention spike** — StockTwits posting 30 messages in well under a day (~97
   msgs/day point estimate, saturated window).

Read for the desk: **a fresh short divergence on RCAT is largely already in the price.** ~23% SI +
a half-million-share FTD spike means the easy, discovered part of the short is crowded and
squeeze-prone (note the *low* days-to-cover, 1.39, because recent ADV ballooned to ~20M on the run —
so it is crowded by SIZE but the cover is fast, a squeeze-fuel signature, not a comfortable borrow).
Per the spec retrofit, a market-researcher short candidate on RCAT should be tagged **"in discovery —
skip or fade,"** not ACTIONABLE. This is exactly the control the layer exists to provide.

*Caveat (honest):* StockTwits/GDELT carry ~live/15-min freshness, but the positioning reads lag
(FTD ~26 days, FINRA SI ~26 days as-of). The crowding is confirmed as-of those settlement dates; an
intra-month change in SI is not yet visible — surfaced in `asof_lags`, not backfilled.

---

## 4. Latency log scaffold — `outputs/latency_log.jsonl`

Append-only JSONL; helper `connectors/latency_log.py::log_divergence(...)` stamps each detected
divergence with `(ticker, divergence_type, source_connector, detection_date, attention_score,
positioning_score, regime, confidence)` and leaves `realized_time_to_price_days = null` for the
Phase-2 scoring job to back-fill. Over many rows this builds the empirical
signal-to-price-latency-by-(divergence-type × regime) table — the knowledge-graph payoff.

---

## 5. Calibration bugs found & fixed (faithful failure report)

1. **StockTwits asof-windowing clipped live high-velocity names to zero.** A `asof = today` date
   produced an end-of-day UTC bound that sat *behind* messages timestamped after UTC midnight (it
   was already 03:55 UTC the next calendar day). SPCX came back with 0 messages. Fixed: when the
   asof date is today (in either local/UTC frame) read the live stream with no upper bound;
   only clip for a strictly-past asof.
2. **Plain-average attention composite diluted single-channel retail spikes.** SPCX (StockTwits
   saturated, no Wikipedia article, thin news) averaged to ~0.37 → wrongly UNDISCOVERED. Fixed with
   the saturation-aware mean/max blend + the sub-day-window ceiling rule (a 30-message window
   spanning < 1 day is a censored undercount → treated as saturated attention) + the retail-spike
   OR-trigger.

Neither fix is tuned to a single name; both are mechanism-grounded and were checked against all four
validation names (including the negative control, GROW).

---

## 6. What Phase 2 needs

- **`reddit_mentions`** — WSB/r/investing mention counts (needs Reddit OAuth app credentials; the
  Pushshift-style free firehose is gone, so this is the first one that genuinely needs a key).
- **`thirteenf_diff`** — institutional 13F position-change diff from EDGAR (free; the "smart-money
  crowding" axis the retail attention sources can't see).
- **`options_positioning`** — OI + 25Δ skew via **IBKR** (systematizes the SPCX-by-hand options work;
  needs the live IBKR session, pull a fresh quote first per the live-price rule).
- **Cross-sectional percentile panel** — replace the fixed saturation anchors with an empirical
  universe-wide percentile (run `discovery_state` nightly over a watchlist, persist the panel). This
  is what turns `attention_score` from a "vs own-history + fixed anchor" proxy into a true
  cross-sectional percentile.
- **SEC shares-outstanding auto-join** — wire the `companyfacts` shares-out pull into
  `finra_short_interest` so short-interest %-of-float is computed automatically (today the caller
  supplies it; DXYZ exposed the gap — closed-end funds don't file the standard dei concept, so a
  float fallback is needed).
- **Market-researcher retrofit** — have every divergence candidate call `discovery_state`, self-tag
  ACTIONABLE only when `regime == UNDISCOVERED`, and write the `latency_log` row at detection.

---

### Files
- `connectors/stocktwits.py`, `connectors/wikipedia_pageviews.py`, `connectors/gdelt_news.py`,
  `connectors/google_trends.py`, `connectors/sec_ftd.py`, `connectors/finra_short_interest.py`
- `connectors/discovery_state.py` (aggregator), `connectors/latency_log.py` (scaffold)
- `source_atlas.py` — 6 new `MSource` entries (CONDITIONING LAYER section)
- `outputs/latency_log.jsonl`, `outputs/conditioning_layer_validation_2026-06-24.json`
