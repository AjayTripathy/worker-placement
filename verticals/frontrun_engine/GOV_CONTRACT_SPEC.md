# Frontrun Engine — Gov-Contract Award-Flow · PRE-REGISTERED SPEC

**Status: LOCKED 2026-06-24, before any data is gathered.** Fixes hypothesis, universe, A/B classifier,
signal, threshold, controls, and success criteria in advance. Any change after data is touched = logged
amendment with reason; original preserved. Sibling to `PILOT_SPEC.md` (CEF/BDC, which FAILED — moat real,
already priced). This pilot applies the **v2 filter** that failure taught us.

## 0. The v2 filter (why this candidate, post-CEF)

The CEF engine died because the not-yet-disclosed number (NAV) was a function of **continuously-priced
liquid inputs** (SPCX, credit spreads) → the market priced it through the inputs. A real frontrun needs the
input to be **observable to us but NOT continuously priced, with no faster channel.** A buried federal award
to a thinly-covered name qualifies: it sits in USASpending weeks-to-months before it becomes revenue, with
no proxy, no analyst, no press release. The covered/uncovered split tests the moat directly.

## 1. Hypothesis (pre-registered)

> For gov-exposed public companies, a **USASpending award-flow surprise** (trailing change in obligations to
> the corporate family vs the gov-revenue run-rate), computed *before* earnings, predicts (a) the revenue
> surprise and (b) post-earnings drift — **materially in Arm A (thinly-covered, non-press-released awards)
> and ~not at all in Arm B (large primes, press-released, analyst-tracked).** Confirmation requires
> `edge(A) − edge(B)` significant, not merely `edge(A) > 0`. (If both fire, it's defense-sector beta /
> already priced — the CEF kill case.)

## 2. Universe & A/B classifier (objective)

Gov-exposed US-listed companies (gov revenue ≳20% of total, or material federal obligations). Split:
- **Arm A (HIGH moat):** thinly-covered (≤ ~5 sell-side analysts) AND awards predominantly **civilian-agency
  and/or sub-$7.5M defense** (i.e., NOT in the DoD daily contract announcement, which press-releases every
  defense award ≥ $7.5M same-day). Small/mid-cap IT-services, health-services, professional-services,
  industrial contractors. *The civilian-agency tilt is the real moat — those awards aren't announced.*
- **Arm B (CONTROL):** large primes (LMT, RTX, GD, NOC, LHX, BAH, LDOS, SAIC, …) — heavily covered, awards
  press-released in the DoD daily list and analyst-tracked. Predict: **no edge** (already priced).
- Classifier inputs: analyst count, market cap, and the **share of the family's obligations from civilian
  agencies + sub-threshold defense** (computed from USASpending). Pre-register the coverage cut at **≤5
  analysts** for Arm A and **≥15** for Arm B; exclude the middle.

## 3. Signal (pre-registered)

- **Award-flow** = sum of USASpending **obligations** to the corporate FAMILY (parent + subsidiaries/UEIs —
  the corporate-family roll-up lesson: search the family, not just the ticker) over a trailing window.
- **Obligations LEAD revenue** (money is obligated to a contract quarters before it's outlaid/recognized) —
  the signal is the obligation-flow change as a *leading* indicator.
- **Signal fires** when the trailing-4Q (or QoQ-annualized) change in family obligations ≥ **10%** of trailing
  gov revenue AND diverges from the consensus revenue trajectory. Direction = sign of the flow change.

## 4. What we measure

Per (name, quarter) where the signal fires: (a) did the next earnings **revenue** print beat/miss in the
predicted direction? (hit/miss); (b) post-earnings **price drift** over a defined window, net of borrow +
bid/ask + a sector-beta hedge (long the name vs a gov/defense ETF to strip the budget-cycle beta). Aggregate
→ `edge(A)`, `edge(B)`, `edge(A) − edge(B)`.

## 5. Controls (each a discipline from the CEF post-mortem)

- **Point-in-time USASpending:** use awards **as they were available** at decision time, not backfilled.
  USASpending has its OWN posting lag — measure it; the signal is only valid on data we'd actually have had.
- **Sector-beta confound (the CEF kill):** gov names co-move with budget/CR/shutdown/defense-sentiment. The
  Arm-B prime control + a gov-ETF beta hedge isolate the award-aggregation edge from sector beta. If Arm B
  shows the same signal-return link, it's beta, not us.
- **Survivorship:** include delisted/acquired contractors; build the universe point-in-time.
- **Recipient→ticker entity resolution** is the hard part (UEI/DUNS → parent → ticker) — errors here are the
  main failure mode; require a verified mapping per name, flag UNVERIFIABLE.
- **Crowding check:** note where Gov-data shops (Bloomberg Gov, Govini) likely already cover — that's why the
  edge, if any, lives in Arm A's uncovered tail, captured by the split.
- **No fishing:** §2 cuts, §3 threshold (10%), and the A/B split are LOCKED here, pre-data.

## 6. Success criteria (binary, pre-set)

- **Arm A:** award-flow signal predicts revenue-surprise direction **> 65%** AND positive drift net of
  costs+beta-hedge.
- **Arm B (control):** not significant.
- **Primary:** `edge(A) − edge(B)` significant → real frontrun → scale.
- **Kill:** A ≈ B → defense-sector beta / already priced → stop. A insignificant → no edge → stop. Negative
  result is still the finding (encodes the signal-to-price latency for gov-contract data).

## 7. Phasing

- **Phase 0 (this spec):** locked.
- **Phase 1:** assemble the gov-exposed universe (survivorship-aware); build the A/B classifier (analyst
  count + civilian-agency obligation share); wire the USASpending family award-flow engine (with entity
  resolution); **assess feasibility honestly** — the USASpending posting lag and the recipient→ticker mapping
  are the two make-or-break questions. Report before any scoring.
- **Phase 2:** run both arms; report `edge(A) − edge(B)` with all §5 controls.
- **Phase 3:** scale only if §6 primary holds.

---

## AMENDMENTS (logged 2026-06-24, post-Phase-1, pre-Phase-2 scoring — §0–§7 originals preserved)

- **G-1 (HIGH) — restrict the live Arm-A signal to the CIVILIAN channel.** Phase 1 measured a *bimodal*
  posting lag: civilian agencies post median **0 days** (85% ≤7d, un-announced → tradeable); defense
  (esp. DLA `SPE*` logistics) posts median **~98 days** (batch quarterly → stale). The sub-$7.5M-defense leg
  is obscure but untradeable as a *leading* signal. **Live signal = civilian obligations only; sub-threshold
  defense kept as a measured-only diagnostic.** (Sharpens the moat to where obscurity AND actionability
  overlap; the 10% materiality and ≤5/≥15 cuts are UNCHANGED.)
- **G-2 (MED) — tag Arm-B sub-strata** (hardware primes LMT/RTX/NOC vs IT-services primes BAH/LDOS/SAIC/CACI,
  the latter 44–61% civilian) for a within-control latency test.
- **G-3 — entity-resolution hard gate:** family-obligation tie-out to reported gov revenue must fall in
  **0.4×–2.0×**, else the mapping is UNVERIFIABLE and the name is EXCLUDED (blocks VSEC, CMTL).
- **G-4 (Phase-2 build requirement) — load-date censoring.** The point-in-time panel MUST censor awards by
  **`Last Modified Date` (posting/load date), not `action_date`** — otherwise the backtest leaks the posting
  lag and manufactures a look-ahead edge. This is the single biggest Phase-2 correctness item.
