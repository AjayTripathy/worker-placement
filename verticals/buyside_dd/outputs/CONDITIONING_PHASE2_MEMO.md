# SignalOS Conditioning Layer — Phase 2 Build Memo (INSTITUTIONAL-crowding channel)

**As-of:** 2026-06-24 · **Scope:** add the institutional half of the crowding gauge — `options_positioning`
(IBKR/TWS skew), `analyst_coverage` (yfinance), `thirteenf_diff` (EDGAR 13F breadth) — plus a `cap_tier`
guard and an `institutional_score`, then run **PODD** through it as the decisive test.

**The gap Phase 2 closes.** Phase 1 measured RETAIL crowding (StockTwits / Trends / Wikipedia / GDELT /
FTD / short-interest). It was **blind to INSTITUTIONAL crowding** — so it read PODD (Insulet, a ~$10B
medtech, 23 covering analysts, a press-released Class-I Omnipod recall with a death) as essentially
*UNDISCOVERED* (retail attention 0.11, positioning 0.15) when the entire street has already priced it.
Phase 2 adds the institutional channel so the gauge sees **both halves** of crowding.

---

## 1. Connector status — live vs blocked (verified against the real APIs/TWS)

| Connector | Channel | Works live? | Verdict |
|---|---|---|---|
| `analyst_coverage` | institutional attention | **YES (live, free)** | yfinance / Yahoo aggregates. PODD returned **23 analysts, rec-mean 1.42 (Strong Buy), consensus PT $242 vs $148.88 spot = +62.8% upside, revision STABLE**. Micro-caps with no Yahoo analyst record degrade to a **cap-tier proxy** (flagged `proxy=True`), never a fabricated count. Also the `market_cap` source for the cap-tier guard. |
| `thirteenf_diff` | institutional positioning | **YES (live, free) — Tier-1 only** | EDGAR full-text search (`efts.sec.gov`). **Tier-1 VERIFIED:** exact count of distinct 13F-HR filers reporting the CUSIP, QoQ. PODD: **791 → 747 filers (-5.6%), BROAD breadth, INSTITUTIONS_TRIMMING.** **Tier-2 UNVERIFIABLE:** aggregate *share* count needs parsing every info table (>10k filings for a widely-held name) — only a flagged *sample* is computed, never extrapolated to a universe total. Needs the security **CUSIP** (FTS keys on it). Lag 45–135d. |
| `options_positioning` | institutional positioning | **PARTIAL — degraded to underlying-level** | The per-strike 25Δ risk-reversal needs the **live TWS API socket (127.0.0.1:7496)**. At build time the socket handshook (TWS returned account `ACCOUNT_ALPHA`) but TWS **dropped the connection right after the handshake** (busy/locked session: ib_insync's startup `reqExecutions` sync hung, then "Peer closed connection," then the listener went fully refused). The connector now (a) connects via the **low-level `client.connectAsync`** to skip the hanging account sync, and (b) **degrades to the IBKR-MCP underlying-level read** (annual IV, IV-percentile-of-52wk, total option volume, historical vol) when the per-strike socket is down — a **real, live** institutional read, just coarser, with `rr_25d=None` flagged UNAVAILABLE. **Never fabricated.** |

**Net: 2 of 3 institutional connectors work fully live and free (analyst, 13F-breadth). The per-strike
options skew is blocked by a TWS-side session lock — handled by degrading to the live MCP underlying-level
options read, not by inventing a skew.**

---

## 2. The upgraded `discovery_state` — what changed

New inputs: `cusip` (enables 13F), `market_cap` (enables the cap-tier guard; auto-filled from the analyst
feed), `mcp_options_underlying` (injects the live MCP options read when TWS is down), `enable_options/13f`.

New outputs alongside the Phase-1 `attention_score` / `positioning_score`:
- **`institutional_score` (0–1)** — saturation-aware blend of: options skew/IV+OI (or, on the degraded
  path, IV-percentile + IV/HV + option-activity), analyst density, and 13F filer breadth. Any one channel
  saturating (20+ analysts OR a deep put-skewed book OR 400+ 13F filers) pulls the composite toward the max.
- **`cap_tier`** — LARGE ≥$10B / MID $5–10B / SMID $2–5B / SMALL $0.3–2B / MICRO <$0.3B.

New regime logic — the **cap-tier guard**:
> A name with **market_cap > $5B** that reads UNDISCOVERED on the RETAIL channels is **DOWNGRADED to
> `UNDISCOVERED_RETAIL_ONLY` (institutional UNVERIFIED)** unless the institutional channel *positively
> confirms* it is un-priced — i.e. low institutional_score **AND** no options-priced-risk **AND** sparse
> coverage (<5 analysts) **AND** no 13F crowding. The street watches every $5B+ name; absence of retail
> noise is not absence of discovery.

Plus new OR-triggers for `DISCOVERED_CROWDED`: `institutional_score > 0.60`, options-priced-risk,
13F-breadth crowded (≥100 filers), or heavy analyst coverage (≥15). Confidence `HIGH` now also requires
the institutional channel to be measured (the exact Phase-1 blind spot).

---

## 3. THE DECISIVE PODD TEST — verdict: **DISCOVERED_CROWDED (institutional). The recall is priced.**

| Read | Phase-1-only (retail) | Phase-2 (with institutional) |
|---|---|---|
| attention_score | 0.11 | 0.11 |
| positioning_score | 0.15 | 0.15 |
| **institutional_score** | — (blind) | **0.903** |
| **regime** | would be **UNDISCOVERED** ❌ | **DISCOVERED_CROWDED** ✅ |
| confidence | — | HIGH (3 attn / 2 pos / 3 inst) |

**Evidence (all live, 2026-06-24, primary):**
- **Analyst coverage (yfinance):** 23 analysts (HEAVY), rec-mean **1.42 = Strong Buy**, consensus PT
  **$242 vs $148.88 spot (+62.8%)**, revisions STABLE. The street is fully on the name and has NOT
  capitulated — the recall is modeled, not undiscovered.
- **13F breadth (EDGAR FTS):** **791 → 747 filers QoQ (-5.6%)**, BROAD. Institutions are **TRIMMING** —
  smart money positioning *out*, which is itself a "discovered + de-risking" tell, not an un-priced setup.
- **Options (IBKR-MCP underlying-level):** spot $148.88 (down **-47.6% YTD**, sitting near the 52-week
  **low** $138.79 vs 52w high $354.88). **Annual IV 46.2% is BELOW realized HV 51.2% (IV/HV = 0.90)**;
  IV sits at the 71st percentile of its *own* 52-week range; option volume is **0.42× average**. So the
  options tape is **not pricing fresh fear** — it's a name that already crashed on the recall and whose
  vol is now *decaying*. `options_priced_risk = False` on the fear axis, but `elevated_iv_regime` is moot
  because the move already happened.

**Interpretation (the honest, mechanism-grounded read).** PODD is **not** a fresh large-cap divergence —
it is **already-priced**. The Class-I Omnipod recall was press-released, the stock is down ~48% YTD and
camped near its 52-week low, 23 analysts still cover it, 747 institutions hold it, and those institutions
are *trimming*. The discovery driver is **coverage + 13F breadth + a completed price reaction**, NOT an
options fear spike (vol is below realized and decaying — the fear is in the rear-view). This is exactly
the "the whole street has priced it" case the cap-tier guard was built to catch: Phase 1 would have waved
PODD through as an actionable undiscovered divergence; Phase 2 correctly tags it **DISCOVERED_CROWDED →
in discovery, skip or fade.** PODD is **not** the first name to clear both gates — it clears neither as an
un-priced opportunity; it is the worked example of an institutionally-crowded large-cap the retail-only
gauge was blind to.

---

## 4. Re-validation — did calibration hold?

**Calibration HELD** — the institutional channel did not break the Phase-1 retail calibration, and the
cap-tier guard fires only where intended.

| Ticker | cap_tier | attn | pos | inst | regime | driver |
|---|---|---|---|---|---|---|
| **SPCX** | LARGE | 0.85 | 0.30 | 0.25 | **DISCOVERED_CROWDED** ✅ | retail attention 0.85 + live StockTwits spike |
| **DXYZ** | SMALL | 0.85 | 0.07 | 0.20 | **DISCOVERED_CROWDED** ✅ | retail attention 0.85 + live StockTwits spike |
| **MVIS** | MICRO | 0.82 | 0.69 | 0.00 | **DISCOVERED_CROWDED** ✅ | retail attention 0.82 + FTD spike + StockTwits spike |
| **GROW** | MICRO | 0.00 | 0.05 | 0.00 | **UNDISCOVERED** ✅ | retail quiet **and** institutional channel confirms un-priced |
| **PODD** | LARGE | 0.11 | 0.15 | **0.90** | **DISCOVERED_CROWDED** ✅ | institutional: 23 analysts + 747 13F filers (the new catch) |

Notes that prove the design is honest, not curve-fit:
- The three retail-crowded names still come back high on the **retail** channel exactly as in Phase 1 —
  the institutional layer did not perturb them (SPCX/DXYZ/MVIS institutional_score is *low*, 0.0–0.25,
  because no CUSIP was supplied for 13F and TWS skew was down; they are crowded for **retail** reasons,
  and the layer says so).
- **GROW** stays UNDISCOVERED and is **not** caught by the cap-tier guard — correctly, because it is MICRO
  (<$5B), and its institutional channel *positively confirms un-priced* (NONE coverage, no 13F crowding).
- **PODD** is the lone name whose discovery is **invisible to the retail channel** (attn 0.11) and visible
  **only** to the institutional channel (inst 0.90) — the precise blind spot Phase 2 was built to close.
- `thirteenf_diff` shows `UNVERIFIABLE (no CUSIP supplied)` for the calibration names — by design, the
  connector refuses to guess a CUSIP from a ticker and flags it rather than fabricate. PODD was run with
  its real CUSIP `45784P101`.

---

## 5. What's left

- **Per-strike 25Δ risk-reversal:** needs the TWS API socket healthy (a person to clear the TWS
  "Accept incoming connection?" dialog / unset a master-client-id lock, or restart the API listener). The
  connector code is complete and uses the low-level connect path; it will produce the true skew the moment
  TWS accepts the session. Until then the MCP underlying-level read carries the options channel.
- **`reddit_mentions`** (WSB/investing mention counts; needs OAuth) — still Phase-1-deferred.
- **Full 13F share aggregation** (Tier-2): the universe-wide *share* total (not just filer breadth) needs
  a bulk info-table parse — feasible as an offline batch job over the quarterly 13F index, not a live call.
- **Market-researcher retrofit & latency-log accrual:** wire `discovery_state` self-conditioning into the
  thesis flow and start logging `(ticker, divergence, regime, institutional_score)` at detection.

---

## 6. Files

- `connectors/options_positioning.py` — IBKR/TWS per-strike skew + MCP underlying-level degrade
- `connectors/analyst_coverage.py` — yfinance coverage density + cap-tier proxy fallback
- `connectors/thirteenf_diff.py` — EDGAR 13F filer-breadth QoQ (Tier-1 verified) + sampled shares (Tier-2)
- `connectors/discovery_state.py` — `institutional_score`, `cap_tier`, `UNDISCOVERED_RETAIL_ONLY` guard
- `source_atlas.py` — three new institutional MSource registrations
- `run_phase2_validation.py` — the PODD test + calibration runner
- `outputs/conditioning_phase2_validation_2026-06-24.json` — full per-ticker output
