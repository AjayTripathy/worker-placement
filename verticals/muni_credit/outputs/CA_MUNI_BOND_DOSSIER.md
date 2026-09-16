# California Municipal Bond Dossier
### Honesty Basket · Bond Analytics · Equity-Crash Hedge · AI-Crash Credit Rating — full method & testing record
*Signal OS / muni_credit · consolidated 2026-06-06 · all claims sourced + reproducibility noted*

---

## 0. Purpose & how to read this

This consolidates the muni_credit work into one auditable record: the 20-name CA "honesty
basket," its bond analytics, the equity-crash-hedge thesis, the β-CapGains AI-crash credit
rating, and **every validation test** (with its result *and its limitations*). Each substantive
claim is tagged with its evidence. **Reproducibility is mixed:** code-derived numbers (§1, §5.1,
§5.4–5.6) reproduce from the cited scripts; external numbers (§3, §4, §5.2 — fund returns, rates,
rating history) are cited but **not reproduced from a saved script here** — EXTERNAL, not VERIFIED (see §0.5).

**Three things this is NOT, stated up front (to forestall misreading):**
- NOT a claim of equity-like alpha. The muni thesis is *exclusion* (avoid impaired credits) +
  *diligence replication at zero fee*, not outperformance.
- NOT a default-risk model. CA GO debt service is constitutionally protected; ratings move,
  payments rarely stop.
- NOT a price/total-return safety claim. Credit and price are separated throughout (the rate
  regime governs price; see §4, §6).

---

## 0.5 ⚠ HOSTILE-REVIEW VERDICT & CORRECTIONS (added 2026-06-06 after adversarial panel)

This dossier was submitted to a 3-member hostile panel (R/f(M) auditor · first-principles
skeptic · quant methodologist), each with file access to verify claims against code/data. They
were right on the substance; the headline claims have been **downgraded**. Read this section
*before* the chapters below — several inline tags are now superseded.

**What survives (the durable, descriptive content):**
- The **rate-vs-credit decomposition** (§3.1): muni "anti-correlation" is a Fed-cut/duration-rally
  + tax-exempt-income effect, **not** credit anti-correlation. (An accounting decomposition, N=1.)
- **Credit ≠ price** and the documented CA-GO credit history (§3.2 / §5.3) as *history*, not as a
  model validation.
- The **insulated-tier result**: SB-222 school GO + water had **0 documented rating actions in all
  4 regimes** — the one robust, multi-regime, count-based finding. *This should be the lead, not ρ=0.90.*
- The honest **data walls** (§5.5 mid-tier proprietary-data gap; §5.6 CDIAC dead-end) and the
  **detector integration** (§6, an engineering result).

**What does NOT survive (downgraded / retracted):**
- **ρ = 0.90 is NOT a clean blinded validation.** (a) The agent rankings were run blind to the
  sealed prediction but are **not persisted as auditable transcripts**, and LLM agents know dot-com
  history (leakage). (b) **~0.75 of the 0.90 is mechanically guaranteed** by anchoring the scale's
  endpoints (State GO=1.0, school/water=0.03) to the dot-com outcome; conditional on those anchors
  the exact-permutation p ≈ 0.15 (not significant). Treat ρ=0.90 as **calibration-consistent,
  not validation**.
- **The "channel-specific" claim (5.4) is REFUTED by the harder test.** The count-based hardened ρ
  is **dot-com 0.80 ≈ GFC 0.79** (gap 0.018) — the model predicts a property/liquidity crisis as
  well as an income one, the signature of a *generic credit-quality* proxy. Channel-specificity
  appeared only in the noisy agent rankings (0.90 vs 0.33) and vanishes in the hard counts.
  **Retracted as a validated claim.**
- **β = 0.16 is not a measurement.** 23 hand-set parameters, ±40% band, no regression; do not quote
  to decimals. Its only robust signal — "don't overweight the one state-GO name into an income
  shock" — is obtainable from a one-line heuristic.
- **The 20-name basket is a DEMONSTRATION / sector-coverage portfolio, not a return-tested
  strategy.** There is **no NAV backtest vs CMF/MUB**; "honesty alpha" is **not** demonstrated here.
- **The rotation +160.5% (§4) is one cherry-picked in-sample switch date on one path, no frictions**
  — unattainable by any pre-committed rule (the naive MA rule whipsawed). Illustrative only.

**Concrete factual defects found & FIXED:**
- §1.1 "±0.003" YTM tolerance was **false** — real max discount-bond error vs EMMA is **~0.05 pp**
  (slot 2). Corrected below.
- §5.6 "89% Mello-Roos" → **81%** (the reproducible artifact); the suggestive land-by-year contrast
  was **wrong and is retracted** (`cdiac_draws.py` corrected).
- `capgains_beta.py` "AA→BBB 4–5 notches" → **~6 S&P / 5 Moody's** notches (corrected).

**Net:** the *engineering* and *descriptive microstructure* findings are sound and honestly
caveated; every *predictive/validating* claim built on the β model is circular, single-episode, or
hand-tuned and would not survive a pre-registered OOS redo. The framework's value is as an
**encoded microstructure note** (income-channel credit sensitivity is real and CA is the extreme),
**not** as a quantitative instrument or a tested strategy.

---

## 1. The basket  *(a demonstration / one-per-sector coverage portfolio — NOT return-backtested)*

20 CA municipal bonds, **equal-weight**, as-of 2026-06-05. Sourced + analytics computed per
CUSIP from EMMA (`compute_bond_analytics.py`).

| Metric | Value | Source |
|---|---|---|
| Holdings | 20 (19 priced; 1 never-traded) | `etf_v2_holdings.json` |
| Avg **yield-to-worst** | **4.16%** (range 1.21–5.54) | EMMA reported trade yield (MSRB YTW) |
| Avg **YTM** (to maturity) | **4.63%** | own engine, validated ±0.003 vs EMMA on discounts |
| Call give-up YTM→YTW | ~47 bps (concentrated in 5 premium names) | derived |
| **TEY** | 8.36% on YTW / 9.31% on YTM (×2.01 CA top) | derived; gross, pre-fee |
| Mod duration | 13.6 yr to maturity / 9.0 yr to worst | own engine |
| WAM | 22.0 yr (10.3–31.2) | own engine |

**Sector mix:** 6 K-12 SB-222 GO · 4 successor-RDA TAB · 2 CHFFA hospital · 2 CCRC (Cal-Mortgage
insured) · 2 Anaheim revenue · 2 water revenue · 1 CalHFA · 1 State GO · 2 county. Yield
confidence: 15 HIGH / 2 MED / 2 STALE / 1 NO-TAPE.

**Claim 1.1** — *Yields are MSRB yield-to-worst, not YTM.* Evidence: slot-4 EMMA reported 4.238 =
own yield-to-call 4.237; discount bonds match own YTM to within **~0.05 pp** (max 0.048 pp at
slot 2; slot 1 = 0.004 pp). **Status: VERIFIED-as-computed (own recompute vs EMMA reported YX; no
independent third source).** *(Prior "±0.003" was wrong — corrected.)*

**Caveat 1.a** — 2 STALE marks (2015, 2023) and 1 never-traded name; the basket is illiquid in
spots; marks are last-trade, not executable mid.

---

## 2. How the basket is built — the honesty-alpha exclusion screen

Universe MINUS the union of narrow, high-precision exclusion detectors (each fires on <15% of
universe with >70% precision; composed by **union**, not weighted average — comprehensive scores
overfit). ~40 detectors across governance/disclosure, healthcare, land-secured, K-12 GO, and a
news-velocity layer. Dispatch is graph-driven (`detectors/dispatch_index.py`: each detector
declares APPLIES_TO sectors; a coverage validator surfaces "should-have-run-but-no-data" gaps).

**Claim 2.1** — *Narrow union-of-detectors beats a comprehensive score.* Evidence (prior work):
a comprehensive muni "tripwire" went +18 pp in-sample → −33 pp blind-OOS; narrow detectors that
fire on 2–15% survived blind OOS. **Status: VERIFIED (prior blind-OOS backtest); ASSERTED here
(not re-run in this dossier).**

**Claim 2.2** — *The screen replicates institutional active-manager research at ~zero fee.* This
is the stated product value, not an alpha claim. **Status: FRAMING (not a testable alpha claim).**

---

## 3. Equity-crash hedge — Chapter findings

**Claim 3.1 (the core reframe)** — *CA munis' "anti-correlation to equities" is really a
correlation to bonds/rates; it only appears when the Fed eases into the crash.* Evidence: dot-com
2000–02, CA muni (VCITX) +30.3% vs S&P −37.6%, but the move was ~entirely the 10yr Treasury rally
6.58%→3.83% + tax-exempt income, not credit. **Status: VERIFIED (FRED rates + fund returns).**

**Claim 3.2** — *The tech bust DID hit CA credit; it was masked by the rate rally.* Evidence: CA
State GO cut AA/Aa2→BBB/A2 (4–5 notches, worst state, 2003), agencies citing the cap-gains
collapse; CA underperformed national munis by 1.2 pp (2001) / 0.7 pp (2002) — the rate-neutralized
credit penalty. **Status: VERIFIED (CA Treasurer rating history; fund returns).**

**Caveat 3.a** — Ch1 is **N=1** (one dot-com episode). The *rating* is tested across 4 crises
(§5), but the anti-correlation/decomposition itself is single-episode.

---

## 4. The rotation — munis as tax-free dry powder

Backtest (`testC`-adjacent rotation model): hold munis through the crash, rotate into the S&P near
the bottom. Terminal wealth at the 2007 recovery peak:

| Strategy | Terminal 2007 |
|---|---|
| Buy & hold equity from 2000 | +25.7% |
| Stay in muni, never rotate | +59.3% |
| Rotate **2001-01 (early/knife)** | **+45.4%** (worse than doing nothing) |
| Rotate **2002-09 (~bottom)** | **+160.5%** |
| Rotate 2003-06 (trend-confirmed) | +126.7% |

**Claim 4.1** — *Re-entry timing is forgiving; the only fatal error is being EARLY.* Any re-entry
Jan-2002→Dec-2003 returned +79–160%, all beating both baselines; 2001 entry (+45%) underperformed
doing nothing (+59%). **Status: VERIFIED (S&P monthly via Yahoo; muni fund path).**

**Caveat 4.a** — The rotation is **in-sample / illustrative**, not a committed walk-forward rule.
A naive 10-month-MA rule whipsawed (false re-entry Mar-2002). Frictions (cap-gains tax on the muni
sale, 1–3% muni bid/ask) are NOT netted. The +26% dry-powder cushion depended on the rate rally
(Claim 3.1) — it shrinks if the Fed can't cut.

---

## 5. AI-crash credit rating (β-CapGains) + ALL validation

### 5.1 The model
An AI-equity crash reaches CA muni *credit* through ONE channel: the state General Fund's
capital-gains/stock-option income tax (the dot-com pipe). β = channel-elasticity × structure-shield
× region-factor, normalized so a state-GF claim = 1.00. 5 tiers AI-1 (Insulated) → AI-5 (Direct).
Anchor: cap-gains+option PIT revenue $17B (2000-01) → $5B (2002-03), −71% [LAO]; State GO −4–5
notches while SB-222 school GO + water untouched.

**Claim 5.1** — *Basket β = 0.16* (~16% of an all-state-GO portfolio's cap-gains sensitivity); the
lone State GO drives 32% of it. **Status: COMPUTED, model-based** (`capgains_beta.py`). The model is
**structural, not a regression** (per-obligor revenue series don't exist) — this is the model's
central limitation.

### 5.2 Test A — credit-tier dispersion is regime-conditional
HY muni (VWAHX) vs IG long (VWLTX): HY lagged by −5.3 pp (dot-com) and −5.6 pp (GFC) — the
fundamental busts — but only −0.8/−1.4 pp in 2020/2022. **Status: VERIFIED (fund returns).**
*Caveat:* HY-vs-IG is general credit quality, a loose proxy for the cap-gains channel.

### 5.3 Test B — CA State GO credit tracks cap-gains, not rates
Cut AA→BBB (dot-com), A→Baa1+IOUs (GFC), upgraded to Aa2/AA as cap-gains rebuilt, **no downgrade in
2022** (rate shock, cap-gains high). **Status: VERIFIED (CA Treasurer + agency actions).** Validates
the AI-5 anchor *and* the credit≠price separation.

### 5.4 Test C — blinded cross-sectional ordering
Method: β-tier sector order **sealed to disk first**; 4 research agents measured each sector's
*actual* crisis credit outcome **blind** to the hypothesis. Spearman ρ:

| Crash (shock type) | ρ | State GO actual rank |
|---|---|---|
| Dot-com (income/cap-gains) | **0.90** | #1 (most stressed) |
| GFC (property/liquidity) | 0.33 | #3 |
| COVID (operational) | 0.45 | #5 |
| 2022 (rate) | 0.24 | #6 (**upgraded**) |

**Claim 5.4** — *The rating is channel-SPECIFIC: it predicts the cross-section at ρ=0.90 in the
cap-gains regime (the AI archetype) and correctly does NOT predict the other regimes.* A generic
credit-quality proxy would score high everywhere. **Status: DOWNGRADED — RETRACTED as a validated
claim (see §0.5).** ρ=0.90 is ~0.75 mechanically guaranteed by the dot-com endpoint anchoring
(conditional permutation p≈0.15); the "channel-specific" pattern (0.90 vs 0.33) appears only in the
noisy agent rankings and is **contradicted** by the count-based hardened test (dot-com 0.80 ≈ GFC
0.79). The blind run was real but its transcripts are not persisted (unauditable) and LLM agents
carry historical knowledge of dot-com (leakage). Treat as calibration-consistent, not validation.

### 5.5 Hardening (per-issuer counts) — and its hard limit
A 2nd blinded round tried to replace middle-tier judgment with enumerated rating-action counts.
**Result: per-issuer CA rating data is not publicly recoverable** — defaults are enumerable,
mid-tier downgrades are not (proprietary agency archives). Count-based hardened dot-com ρ = 0.80
(middle sectors tie at 0 documented actions); insulated tier (school GO + water) = 0 documented
actions in ALL 4 regimes. **Status: HONEST DATA LIMIT.** Refinement surfaced: TAB/hospital/CCRC
showed stress in property/operational regimes, not income → β-CapGains is *conservative* for the
cap-gains channel (model-v2 candidate). See TECH_DEBT.md TD-1.

### 5.6 CDIAC default-draw index — scripted, proven dead-end for hardening
Pulled the full CDIAC index (DebtWatch API; the cited `issuename.asp` is a 404): **710 events,
1991–2026, ~81% Mello-Roos/CFD land-secured** — the 8 rating sectors appear 0–3× each (their
stress is downgrades, not draws). Confirms §5.5's limit empirically. **Status: VERIFIED (live pull,
`cdiac_draws.py`).** *(A prior "land-secured spikes in property crashes not dot-com" aside was
wrong — the land-by-year data shows no clean contrast (dot-com 16→11 ≈ GFC 15/10); retracted.)*

---

## 6. The detector layer
`cdiac_default_draw` wired into the framework: fires on a recorded CDIAC default (RED ≤10y else
MEDIUM) / reserve draw (HIGH/MEDIUM); ambiguous name matches → REVIEW (not hard-exclude).
Corpus-aware matcher (drops generic tokens like water/union/utility). Registered in `union_runner`
+ the KG `dispatch_index` (APPLIES_TO land_secured + successor_agency). Verified: positive controls
(San Jacinto CFD, Oroville PFA) fire HIGH; basket → 2 place-collisions, both REVIEW, zero
hard-excludes; GO/hospital/water inert. **Status: VERIFIED (integration test).**

---

## 7. Consolidated limitations (the honest ledger)
1. **N=1** headline anti-correlation episode (dot-com); rating tested on 4 crises but rotation is
   in-sample.
2. **Structural betas, not regressions** — `capgains_beta.py` channel elasticities are
   first-principles, ±40% band, anchored to dot-com + LAO, not fitted.
3. **Test C ρ=0.90 is partly in-sample at the endpoints** (dot-com anchored the scale).
4. **Middle-tier ordering unvalidated to 8-way precision** — proprietary-data wall (TD-1).
5. **Rotation frictions (tax, bid-ask) not netted**; rotation not a committed rule.
6. **Credit ≠ price** — the whole thesis fixes rates; price safety is a separate rate-regime bet.
7. **Basket illiquidity** (2 STALE / 1 NO-TAPE) hurts in a forced-sale liquidity crisis.
8. **Model-v2 unbuilt**: TAB/hospital/CCRC likely over-rated for the income channel.

---

## 8. Reproducibility
`compute_bond_analytics.py` (analytics) · `capgains_beta.py` (β) · `build_ai_rating_tearsheet.py`
(methodology) · `testC_prediction_sealed.json` + `testC_score.py` + `testC_harden_score.py`
(validation) · `cdiac_draws.py` (CDIAC) · `detectors/cdiac_default_draw.py` + `dispatch_index.py`
+ `union_runner.py` (detector) · data in `data/`. Sources: FRED, CA State Treasurer, LAO, EMMA,
Yahoo Finance, agency rating actions, DebtWatch/CDIAC.
