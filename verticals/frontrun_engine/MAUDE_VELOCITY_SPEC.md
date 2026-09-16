# Frontrun Engine — MAUDE Complaint-Velocity → Class I Device Recall · PRE-REGISTERED SPEC

**Status: LOCKED 2026-06-25, before any analysis data is gathered.** Third sibling to
`PILOT_SPEC.md` (CEF/BDC — FAILED, input already priced) and `GOV_CONTRACT_SPEC.md`
(award-flow — FAILED, transmission broken). Motivated by the PODD/Insulet Omnipod recall
post-mortem: the recall *announcement* priced same-day (latency ~0) and the openFDA
*classification* posts weeks late (negative latency) — the only channel with *potentially*
positive, tradeable latency is the public **MAUDE adverse-event complaint stream** that
accumulates *before* a firm decides to recall. This spec tests whether that stream actually
leads the recall, and for which recall subset.

## 0. The v2 filter (why this candidate)

A real frontrun needs an input **observable to us but NOT continuously priced, with no faster
channel.** Public MAUDE (openFDA `device/event`) qualifies *in form*: adverse-event reports
accrue continuously, nobody prices them per-name, and they precede the recall decision. The
**open empirical question this spec answers**: is MAUDE's own *reporting lag* small enough,
relative to the defect's burn rate, that the public velocity spike LEADS the recall
announcement with positive, material latency — or is the public stream too lagged (the
firm sees its un-lagged internal complaint inflow; we see a censored shadow)? Prior belief
(stated in the post-mortem): **positive lead for slow-burn defect modes, ~0/negative for
sudden lot defects (PODD-type).** This is a falsification test of that belief.

## 1. Hypothesis (pre-registered)

> For Class I medical-device recalls, the **point-in-time public MAUDE complaint-velocity
> spike** (trailing surge in adverse-event reports for the (manufacturer × product-code)
> cell, censored by `date_received`) **leads the recall announcement by a positive, material
> lead time**, and that lead is **materially larger for slow-burn defect modes than for
> sudden lot/manufacturing defects.** Confirmation requires BOTH a positive median lead AND
> an acceptable false-positive (precision) rate — a velocity monitor that also fires
> constantly absent a recall is not tradeable.

Directional sub-hypothesis (the PODD belief): bucket recalls by root-cause signature into
SLOW-BURN (design/wear/software/chronic-malfunction — complaints compound over months) vs
SUDDEN (single-lot manufacturing/contamination defect — step function). Predict
`lead(slow-burn) > lead(sudden)` and `lead(sudden) ≈ 0`.

## 2. Universe (objective, point-in-time)

- **Recall ground truth:** all **Class I** device recalls from openFDA `device/enforcement`
  with `recall_initiation_date` in **2015-01-01 .. 2024-12-31** (MAUDE coverage is dense
  post-2015; leave ≥6mo for the announcement to be unambiguous). Class I only — highest
  signal, cleanest event.
- **Join key (manufacturer × product_code):** each recall carries `recalling_firm` and
  `product_code`. The MAUDE stream is queried by `device.openfda.product_code` AND a fuzzy
  `device.manufacturer_d_name` token match to the recalling firm. A recall is INCLUDED only
  if the join resolves a non-trivial MAUDE history (≥ a pre-set minimum baseline volume so a
  "spike" is definable); otherwise EXCLUDED as UNRESOLVED (logged, not silently dropped).
- **De-duplication:** multiple recall lots/numbers sharing one (firm, product_code,
  initiation-month) collapse to ONE event (the earliest initiation date) — avoids
  multiple-counting one recall campaign.
- **Tradeability is a SECOND filter, not a universe gate.** Lead-time is a property of the
  DATA CHANNEL; measure it on the full resolvable recall set (maximizes N). Separately tag
  which recalling firms map to a US-listed public equity (tradeable subset) and report lead
  for that subset too.

## 3. Signal — point-in-time MAUDE velocity (pre-registered)

- **Time axis = `date_received`** (the date FDA received the MDR = the date it becomes
  publicly observable). **NEVER `date_of_event`** (leaks the reporting lag → look-ahead).
  This is the single biggest correctness item — the direct analogue of the gov-contract
  **G-4 load-date censoring** rule. The series indexed by `date_received` IS the point-in-time
  series by construction: as-of date D, the observable trailing count is exactly the reports
  with `date_received ∈ (D−w, D]`. No backfill, no look-ahead.
- **Velocity** = trailing **30-day** count of MDRs received for the cell.
- **Baseline** = the cell's own trailing **365-day** mean 30-day rate, lagged so it ends
  ≥ 90 days before the test date (pre-spike regime), with a robust floor (min 3 reports/30d
  baseline, else cell is too sparse → UNRESOLVED).
- **Spike date `D*`** = the **first** date in the 365 days before the announcement at which
  the trailing-30d count ≥ **max(baseline × 3, baseline + 3·sqrt(baseline))** (Poisson-style
  3-sigma OR 3× multiplier, whichever is higher — guards both sparse and dense cells).
- **Lead** = `announcement_date − D*` in calendar days. Positive = MAUDE led; ≤0 = no edge.

## 4. What we measure

Per resolved recall event:
1. `lead_days` = announcement − D* (NaN if no spike fired in the 365d pre-window → "no signal").
2. `fired` (bool): did any spike fire pre-announcement?
3. `root_cause_bucket` ∈ {SLOW_BURN, SUDDEN, AMBIGUOUS} from `reason_for_recall` /
   `root_cause_description` keyword classifier (LOCKED keyword lists in §5).
4. `public` (bool) + ticker if the firm maps to a US-listed equity.

Aggregate:
- **Recall (sensitivity):** fraction of recalls where `fired` AND `lead_days > 0`.
- **Lead distribution:** median / IQR of `lead_days` among fired, overall and by bucket.
- **Precision / false-positive rate (the control the naïve framing misses):** in matched
  CONTROL windows — the same cells in calendar periods with NO recall within the following
  180 days — how often does the spike rule fire? `precision = recall_spikes / all_spikes`.
  A monitor that fires monthly on noise is useless however good its lead.

## 5. Controls & locked classifiers (each a discipline from the prior post-mortems)

- **Point-in-time / no look-ahead:** §3 `date_received` censoring. Verified by a leak-check:
  re-run indexed by `date_of_event` and report the inflation in `lead_days` (expected: the
  leaky version manufactures longer phantom leads — the analogue of the gov-contract
  action-date leak that turned a null into a marginal signal).
- **False-positive control:** §4 precision via matched no-recall windows. LOCKED here.
- **Reporting-lag instrumentation (Phase 1 feasibility, like the gov-contract posting-lag):**
  measure the distribution of `date_received − date_of_event` across the MAUDE corpus. If the
  median lag ≫ typical defect burn time, the channel is dead a priori — report before scoring.
- **Survivorship / availability:** use MAUDE as it would have been available — `date_received`
  censoring handles this; do NOT use any record's later-revised fields.
- **Root-cause classifier (LOCKED, no post-hoc tuning):**
  - SUDDEN keywords: `lot`, `manufacturing defect`, `contamination`, `sterility`, `specific
    lots`, `particulate`, `seal`, `leak in`, `single lot`, `out of specification`,
    `component from supplier`, `assembly error`.
  - SLOW_BURN keywords: `software`, `firmware`, `design`, `wear`, `degradation`, `battery`,
    `over time`, `may fail`, `cybersecurity`, `false alarm`, `under-delivery`, `occlusion`,
    `inaccurate`, `algorithm`, `chronic`.
  - Neither / both → AMBIGUOUS (reported separately, not forced).
- **No fishing:** the 30d window, 365d baseline, 3-sigma/3× threshold, 2015–2024 range,
  Class-I-only, and the keyword lists are LOCKED in this file pre-data. Any change after data
  is touched = logged amendment with reason; original preserved.

## 6. Success criteria (binary, pre-set)

- **Tradeable-positive (scale):** median `lead_days` among fired recalls **≥ 21 calendar
  days** (≥ ~3 weeks — enough to act after detection-noise) AND **precision ≥ 0.50** (the
  spike fires ahead of a real recall at least as often as not) AND the public/tradeable
  subset preserves both. Then the monitor is a real leading indicator → build the standing
  monitor + wire through the conditioning layer.
- **Slow-burn-only-positive (narrow build):** the above FAILS overall but HOLDS within the
  SLOW_BURN bucket (median lead ≥ 21d, precision ≥ 0.50) AND SUDDEN bucket shows lead ≈ 0 →
  ship a SLOW-BURN-only monitor; confirms the PODD-type sudden defect is unpredictable.
- **Kill:** median lead ≤ 0 OR precision < 0.50 across the board → the public MAUDE channel
  is too lagged / too noisy to frontrun a recall → STOP. Negative result is still the finding
  (encodes the signal-to-price latency for the device-adverse-event channel — the latency
  axis of the SignalOS goal).

## 7. Phasing

- **Phase 0 (this spec):** LOCKED.
- **Phase 1 (feasibility — report before scoring):** (a) confirm openFDA `device/event` &
  `device/enforcement` field availability for the join; (b) measure the MAUDE reporting lag
  `date_received − date_of_event` distribution; (c) assemble the Class-I recall universe and
  report the resolution rate of the (firm × product_code) join. If the reporting lag is
  fatal or the join resolves < ~30% of recalls, report and reconsider before scoring.
- **Phase 2 (scoring):** run §3 signal + §4 measures + §5 controls; report median lead,
  precision, the slow-burn/sudden split, and the leak-check delta.
- **Phase 3:** build the standing monitor only if §6 holds (overall or slow-burn-only).

---

## AMENDMENTS & VERDICT (logged 2026-06-25, post-run — §0–§7 originals preserved)

- **M-1 (root-cause classifier upgrade):** openFDA `device/recall.json` exposes a STRUCTURED
  `root_cause_description` categorical (e.g. "Device Design", "Nonconforming Material/Component").
  Used it as the primary SLOW_BURN/SUDDEN mapper (`classify_root_cause_structured`); the §5 free-text
  keyword lists are the fallback when the field is "Under Investigation"/"Other"/missing. Strictly
  cleaner than free-text; no other §5 control changed.
- **M-2 (join correction, pre-scoring):** `device/enforcement` carries classification +
  recall_initiation_date but NOT product_code; `device/recall.json` carries product_code + root_cause
  but NOT classification. Joined on the shared Z-number (`enforcement.recall_number ==
  recall.product_res_number`, verified 100%). MAUDE product_code field is
  `device.device_report_product_code` (not `device.openfda.product_code`). Series pulled via openFDA
  `count=date_received` aggregation with a server-side manufacturer token (one call per cell).

**VERDICT: KILL on specificity.** Sensitivity 0.17, precision 0.50 (likelihood ratio ≈ 1.0), median
lead 77d but driven by high-volume reporting cells (artifact). Leak-check on `date_of_event` inflated
the lead +46.5d (censoring validated). Slow-burn directional prior weakly present (median 122d, n=3) but
underpowered and specificity kills it. The public MAUDE stream is too insensitive AND too non-specific to
frontrun a recall, and lags the firm's internal complaint view by ~25d. Engine retained as a diligence
connector, NOT a frontrun strategy. See `outputs/MAUDE_PHASE2_MEMO.md`.
