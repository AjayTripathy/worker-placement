# AIRO short + KTOS long — single-name alpha + sector beta hedge

**Cohort cutoff:** 2026-05-16
**Falsification window:** 2027-05-16 (12 months from cutoff)
**Methodology:** Signal OS blinded-subagent forward test on a 5-name defense-tech cohort (RCAT, UMAC, ONDS, AIRO, KTOS). Subagents had no shared context, no WebSearch / WebFetch access, no outcome labels. Each scored 5-8 R/f/M claims per filing. Full per-ticker outputs in `data/_local/<TICKER>.{input,scores}.json`. Cohort matrix in `data/_defense_cohort/matrix.json`. R/f/M decomposition of all 8 material signals in `data/_defense_cohort/SIGNALS.md`.

After framework scoring, an out-of-band market-positioning check (short interest, analyst consensus, recent contract announcements, known short reports) was applied to each RED/SEVERE signal to separate Truth_signal from Tradable_alpha (per `feedback_truth_vs_alpha.md`). Of three signals that scored high on Truth, only one — AIRO — also scored high on Discovery_advantage (i.e., not already priced in). This document publishes that one.

---

## The alpha thesis — short AIRO

**Ticker:** AIRO (AIRO Group Holdings, Inc.) — CIK 0001927958
**Filing analyzed:** FY2025 10-K (accession 0001493152-26-014116)
**Subagent score:** PASS=3, MOD=0, SEVE=0, **RED=1**, UNVE=4 — composite severity 0.75
**Discovery_advantage:** **HIGH** — short interest ~10.88% of float (vs 33% for ONDS, 20% for RCAT in the same cohort); post-IPO scrutiny has been light; the specific pattern hasn't been published in any short report found via web search; recent May 14, 2026 earnings missed EPS by -41.29% and revenue by -47.44% — fresh negative catalyst not yet digested by sell-side.

### R / f / M

- **R (claim):** Defense roll-up. The S-1 and FY2025 10-K pitch AIRO as "a multi-faceted advanced Aerospace and Defense company operating through four segments: Drones, Avionics, Training, and Electric Air Mobility" — built by consolidating Aspen Avionics, Coastal Defense, Sky-Watch, Jaunt Air Mobility, Agile Defense Systems, and other subsidiaries. The investment narrative is "real defense businesses with real DoD revenue, consolidated through M&A under one public ticker, now scaling."

- **f (relationship):** A real consolidated defense business with real subsidiary cash flows should produce: (i) operating cash flow that does not collapse year-over-year; (ii) effective internal controls over financial reporting (ICFR); (iii) goodwill that is a moderate fraction of total assets; (iv) acquisition consideration paid primarily in cash or assumed debt rather than in equity-for-services at IPO; (v) related-party payments that are arm's-length and not concentrated to a single insider; (vi) customer concentration below 60%.

- **M (observed in the filing itself — not external registry):** Self-disclosure in the financial statements and notes:
  - **Vendor / contingent payables converted to equity at IPO across 5+ subsidiaries:** Jaunt $44.6M → 1.12M shares; Aspen Bridge $17.5M → 440K shares; Coastal Defense $2M → 203K shares. This is the SRFM-Palantir and LILM-style stock-for-services fingerprint that the Signal OS framework has previously identified as a generic distress flag (see `feedback_stock_for_services_flag.md`).
  - **Investor Notes accruing interest at 100-150% of principal payable in stock.** Compounding equity dilution disguised as debt.
  - **20% of Sky-Watch EBITDA payable to single stockholder (Dangroup)** — $5.7M expense in 2025. Related-party concentration on a key segment.
  - **Material weaknesses in ICFR disclosed since FY2023; CEO/CFO concluded controls NOT effective.** Unremediated.
  - **Operating cash flow swung from +$21.5M to -$32.4M year-over-year.** $54M deterioration.
  - **79% of revenue from 2 customers.** Concentration risk.
  - **Goodwill is 74% of total assets ($571.7M).** Marked $38M impairment in 2024 but no impairment in 2025 — implausible given the operating deterioration.
  - **Electric Air Mobility segment: $0 revenue, $7.6M R&D spend.** Pure burn segment.
  - **Accumulated deficit: $210.6M.**
  - **May 14, 2026 earnings:** EPS missed by -41.29%, revenue missed by -47.44%.

- **Gap:** The investment narrative ("we consolidated 4 strong defense subsidiaries into a public defense roll-up") does not reconcile with the financial reality ("the subsidiaries had vendor payables we settled in equity at IPO, our internal controls are not effective, our cash burn accelerated $54M YoY, 74% of our balance sheet is goodwill that should have impaired but didn't, our anchor segment generates $0 revenue against $7.6M R&D, and our first reported quarter post-IPO missed revenue by -47%").

### Why this is alpha vs. consensus

The bear pattern is documented in the S-1 and 10-K — anyone reading them would find it. But:

1. **Short interest is only ~10.88% of float** (vs 33% on ONDS, 20% on RCAT). The shorts haven't crowded in.
2. **No published short report** found on AIRO via web search at cutoff.
3. **Sell-side coverage** is thin (recent IPO).
4. **The May 14, 2026 miss** is a fresh catalyst that the market may still be re-rating.
5. **The specific SRFM-LILM stock-for-services pattern** is not a generic distress flag most analysts look for — it requires either reading the right Note section carefully or having seen the same pattern before. The Signal OS framework has built specific recognition of this fingerprint over prior backtests (SRFM, LILM); generic equity analysts have not.

### Falsification criteria (by 2027-05-16)

The thesis is wrong if ANY of the following are true 12 months from cutoff:

1. AIRO has remediated the FY2023 ICFR material weakness and the FY2026 10-K reports effective controls.
2. Operating cash flow has turned positive on a trailing-12-month basis.
3. Goodwill on the balance sheet has not been impaired AND is no longer >50% of total assets (implies real organic growth diluting the goodwill ratio).
4. The Sky-Watch / Dangroup 20%-EBITDA arrangement has been terminated or capped.
5. The stock is within ±20% of cutoff price AND no analyst, short-seller, or journalist has publicly identified the same distress fingerprint.

If at least 3 of these 5 are true, the thesis is decisively wrong. If 1-2 are true, the thesis is partially vindicated. If 0 are true (current state persists or worsens), the thesis is correct.

### Position construction

**Recommended instrument: long-dated puts.** Avoids borrow cost on a recent IPO (borrow availability/rate uncertain), defines maximum loss, and matches the 12-month falsification window.

- **Specific structure (illustrative — confirm liquidity at execution):** 12-month ATM put on AIRO, sized to 1-2% of portfolio. Bear put spread (long ATM put, short 30-delta put) reduces premium cost ~30-40% at the expense of capped downside capture.
- **If options are too illiquid:** physical short, sized to 0.5-1% of portfolio (smaller because of borrow uncertainty + recent-IPO volatility).
- **Do NOT use leverage.** This is a thesis bet, not a high-conviction high-confidence trade. The framework's hit rate on novel-discovery signals is meaningful but not >70%.

### Specific risks acknowledged

- **The cleanest disconfirming catalyst is a successful capital raise.** If AIRO closes a $100M+ financing in the next 12 months that the market interprets as endorsing the defense roll-up story, the stock could rally 30-50% on no fundamental change.
- **Recent-IPO names can squeeze hard** even with bearish fundamentals. The 10.88% short float is low precisely because borrow may be hard to source — if borrow tightens further, an unrelated catalyst could move the stock significantly.
- **Material weakness disclosure is common in recent SPAC/IPO names and doesn't always cascade.** Many companies disclose weaknesses, remediate quietly, and never restate. The thesis specifically depends on the financial deterioration NOT being remediated within the falsification window.
- **The Signal OS framework's hit rate on novel-discovery signals is not yet established.** This is one of the first explicitly novel-vs-crowded forward-tests run; prior backtests (Nikola, Lordstown, SRFM) were on names that subsequently HAD short reports published. AIRO is the first to publish ahead of any external validation.

---

## The beta hedge — long KTOS

**Ticker:** KTOS (Kratos Defense & Security Solutions, Inc.) — CIK 0001069258
**Filing analyzed:** FY2025 10-K (accession 0001069258-26-000013)
**Subagent score:** PASS=7, MOD=0, SEVE=0, RED=0, UNVE=1 — composite severity 0.00

### Why KTOS as the hedge

- **Same sector** (defense tech, mid-cap US-listed). Sector beta cancels naturally.
- **Framework specifically corroborated** KTOS's claims rather than failing to find divergence: 242 DoD contracts / $1.67B (2023-2026) verified in USAspending across 5+ subsidiary name variants; 68 granted patents across Kratos parent + Florida Turbine; 6 CA + 2 AL facilities confirmed in EPA FRS; GE Aerospace partnership corroborated by GE's 8-K filing.
- **The framework's "clean" verdict on KTOS is itself the evidence** — the same M-side queries that flagged AIRO produced PASS on KTOS. The asymmetry is the signal.
- **Liquidity:** $9.8B market cap, normal options chain, no borrow concerns, no fundamental questions. Easy to size and exit.

### Position construction

**Recommended instrument: equity or long-dated calls.** No borrow constraint, no options-skew concern.

- **Specific structure (illustrative):** Equal-dollar long KTOS against the AIRO short. If using options for both, long 12-month ATM call on KTOS at the equivalent dollar notional.
- **Sizing rationale:** Dollar-neutral against the AIRO leg. Defense sector beta cancels. Net exposure is the alpha leg only (AIRO-specific divergence) plus minor idiosyncratic risk on KTOS (which the framework explicitly found low).

### Why this is NOT itself an alpha bet

KTOS is fully priced as a healthy defense contractor. The framework didn't find divergence there. Buying KTOS as a standalone trade adds no edge — it's just defense beta. Its role here is **neutralizing the sector exposure** of the AIRO short, not generating returns of its own.

If you want to express only the AIRO alpha (no hedge), short AIRO unhedged at smaller size. The dollar-neutral pair is the more rigorous expression because it isolates the AIRO-specific divergence from defense-sector beta moves.

---

## The full trade

| Leg | Direction | Ticker | Instrument | Size (illustrative) | Role |
|---|---|---|---|---|---|
| 1 | SHORT | AIRO | 12-month ATM put (or bear put spread) | 1-2% of portfolio premium | **Alpha** (novel divergence) |
| 2 | LONG | KTOS | Equity or 12-month ATM call | Dollar-equivalent to leg 1 | **Hedge** (sector beta neutralizer) |

**Net exposure:** AIRO-specific divergence isolated. Defense sector cancels.
**Max loss:** Total option premium (if puts/calls) or ~50% drawdown on the unhedged sides (if equity short).
**Expected falsification date:** 2027-05-16.

---

## Pre-registration

This document is published at cutoff date **2026-05-16** as a forward-looking, falsifiable prediction. To establish the timestamp:

1. **Local:** commit this file to git with the cohort-cutoff date in the commit message.
2. **External:** hash the file (`shasum -a 256 ALPHA_TRADE.md`) and commit the hash to a public timestamp service (OpenTimestamps, or any public git remote pre-falsification).

The framework's hit rate on this style of single-name novel-discovery forward bet is not established. This is one data point.

---

## What this is NOT

- **Not investment advice.** The author is publishing a methodological forward bet, not a recommendation. Implementation depends on individual risk tolerance, position sizing limits, borrow availability, and broker constraints not analyzed here.
- **Not a fraud accusation.** Every observation about AIRO is sourced from AIRO's own SEC filings. The thesis is about financial deterioration matching a historical distress pattern, not about wrongdoing.
- **Not a high-confidence trade.** The framework discovered a signal that consensus appears to have missed. Whether that discovery translates to >2x return on the option premium is unknown until the falsification date.
- **Not a complete trade ticket.** Actual execution requires checking option strike availability, IV at execution, bid-ask spread, and borrow rate if shorting equity directly.

---

## Provenance

- **Cohort runner:** `verticals/public_co/configs/_defense_pull.py` + `defense_cohort.py`
- **Subagent template:** `verticals/public_co/defense_subagent_prompt.py` (5 blinded runs, one per ticker, no shared context)
- **M-source connector added this session:** `verticals/public_co/m_sources/usaspending.py`
- **Per-ticker raw outputs:** `data/_local/{RCAT,UMAC,ONDS,AIRO,KTOS}.{input,scores}.json`
- **Cohort aggregation:** `data/_defense_cohort/matrix.json`, `PREDICTIONS.md`, `SIGNALS.md`
- **Process rules captured to memory during this run:**
  - `feedback_dod_cohort_calibration.md` (7 calibration refinements from subagents)
  - `feedback_truth_vs_alpha.md` (Discovery_advantage as separate factor from Truth_signal)
- **Architecture references:** Layer 3 operational discipline rules in top-level `ARCHITECTURE.md`; Signal OS divergence framework in `feedback_fraud_signal_model.md`.
