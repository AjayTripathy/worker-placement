# Phase 2 — Gov-Contract Award-Flow Frontrun: Scoring Backtest

**As-of 2026-06-24. Pre-registered spec: `GOV_CONTRACT_SPEC.md` (LOCKED) + amendments G-1..G-4.**
Locked params unchanged: ≤5/≥15 analyst cuts, 10% materiality, A/B split, §6 success criteria.

## Verdict (§6): FAILED — no real, tradeable, beta-hedged edge. Arm A is also LOW-POWER.

The civilian USASpending award-flow surprise, computed point-in-time before earnings and censored by
load date (G-4), does **not** predict the revenue-surprise direction in Arm A (hit-rate **40.7%**, *below*
the 50% coin-flip and far below the 65% bar), does **not** produce significant beta-hedged drift, and the
primary `edge(A) − edge(B)` is **negative on hit-rate (−0.26)** — the *opposite* sign the thesis required.
This collapses the same way the CEF pilot did, but for a sharper reason: the buried-award signal is real
and observable, yet for the thinly-covered civilian names it is **not a leading indicator of recognized
revenue** — obligations (contract ceilings) and outlays (revenue) decoupled in the post-2023 gov-services
de-scope regime. Negative result; encodes the signal-to-price latency for gov-contract data.

---

## 1. The G-4 censoring method + leak-check (THE correctness item)

**How the panel was censored.** USASpending exposes, per *award*, a mutable summary **`Last Modified Date`**
= the date of that award's most-recent posted modification. This is the only public load-date proxy.
For each (name, decision-date D) I pulled every family award whose **action_date** fell in the trailing
window, then split the obligation total two ways:

- **Load-date-censored (the valid panel):** keep only awards with **`Last Modified Date ≤ D`** — i.e., the
  awards that had actually posted to USASpending by the decision date. This is what we would have seen live.
- **Action-date (leaky) panel:** keep all awards action-dated in the window, regardless of when they posted
  — the naive backtest that leaks the posting lag.

Both the current and the prior comparison window are censored at the same D, so the level bias from
conservative censoring (an award re-modified after D is dropped) differences out of the QoQ signal. Censoring
by the *latest* modification is the safe direction: it can only *exclude* a genuinely-available award, never
*include* a future one — it cannot leak. The live signal is restricted to **civilian awarding agencies (G-1)**;
the award rows carry Awarding Agency, so the civilian filter is applied exactly (defense kept as a measured
diagnostic only — its ~98-day posting lag, per Phase 1, makes it untradeable as a lead).

**Leak-check (the gap IS the look-ahead we avoided).** Across the 107-row panel the action-date version sees
obligation flow the censored version does not:

| | Arm A firing events | Arm B firing events | Median per-decision look-ahead gap | Max gap |
|---|---|---|---|---|
| **Censored (valid)** | 27 | 21 | — | — |
| **Action-date (leaky)** | **31** | **27** | **$122M** | $2.56B |

The action-date panel manufactures **8 extra firing events** (A +4, B +6) — signals that fired on awards not
yet posted at the decision date. Worked example (ICFI): at D=2025-04-11 the **leaky** signal fired strongly
(+26.4% of gov-rev) while the **censored** signal did not fire (+8.3%), a **$285M** gap of awards whose
`Last Modified` was after D. And the leak *inflates the apparent edge*: Arm A's leaky directional drift is
**+2.3% (placebo p=0.10)** vs the censored **+1.6% (p=0.25)** — using action_date would have turned a null
into a marginal-looking signal. That is the seductive false positive G-4 exists to kill, and it is exactly
the magnitude Phase 1 predicted from the civilian-vs-defense posting-lag split.

---

## 2. The panel + N (survivorship-aware, point-in-time)

**Tradeable Arm-A universe = 2 names (DLHC, ICFI).** This is the honest power constraint and the headline
caveat. The Phase-1 VERIFIED Arm-A set was DLHC, ICFI plus three survivorship names (NCI→Empower AI,
ManTech→Carlyle, Vertex→V2X). The survivorship names were taken private/acquired in 2017–2022 and have **no
live equity** over the price-data era (mid-2021 on) — they contribute to the obligation-flow panel but
generate **zero tradeable drift events**. VSEC/CMTL were excluded by the G-3 tie-out gate in Phase 1. So the
intersection of (≤5 analysts) × (civilian-tilted) × (VERIFIED entity-resolution) × (live equity 2021+) is two
names. That is a real finding about where the moat could even exist — and it is too thin to confirm an edge.

| Arm | Names scored | Firing events (censored) | Distinct quarter-clusters (effective N) |
|---|---|---|---|
| **A** (≤5 analysts, civilian) | DLHC, ICFI | 27 | **19** |
| **B** (≥15 analysts, primes) | LMT, GD, BAH, LDOS | 21 | 20 |

Decision date D = filing date − 21 calendar days (point-in-time, ~3 weeks pre-earnings). Signal = trailing-1y
civilian family obligations vs the prior year, fires if |Δ| ≥ 10% of the trailing gov-revenue run-rate
(gov-share × trailing-4Q revenue). **Clustered-N:** events cluster by calendar quarter because gov-exposed
names co-move on the federal budget cycle; effective independent N = distinct quarters (**19** for Arm A), not
the 27 raw events — do not pseudo-replicate.

**Labels.** (a) Revenue surprise = next reported quarterly revenue vs a **trailing-4Q run-rate model**
(no sell-side consensus exists for these micro-caps — stated, not faked); direction = sign. (b) Drift =
long-name-vs-ITA beta-hedged return over **+1 to +20 trading days** post-earnings, net of borrow (~2%/yr) and
a round-trip half-spread (DLHC charged its live 2.6% quoted spread; ICFI 0.4%; primes ~5–10 bps).
**Survivorship-aware:** the acquired names are in the obligation panel via their pre-acquisition history;
they simply can't be traded.

**Scored Arm-B note (drift):** LMT, GD, BAH drift computed on verified, distinct daily price series.
**LDOS drift is excluded** — the IBKR contract (134280621) returned Booz Allen's price series/quote this
session (a feed anomaly I caught on a level cross-check: "LDOS" came back $102→$104, but real Leidos trades
~$160+); rather than fabricate a number I dropped LDOS from the drift mean (it still contributes to Arm-B
hit-rate). SAIC and CACI throttled out of the panel build (USASpending rate-limited the heavy family queries
to repeated 500/disconnect); Arm B still spans both G-2 sub-strata — hardware primes (LMT, GD) and
civilian-tilt IT-services (BAH, LDOS) — so the control is intact.

---

## 3. Per-arm results (§5 controls: point-in-time, net of costs, beta-hedged)

All figures on the **load-date-censored** signal (the valid panel). Drift = mean net directional return,
trading the signalled direction, beta-hedged vs ITA.

| | Arm A (DLHC, ICFI) | Arm B (LMT, GD, BAH, LDOS) |
|---|---|---|
| Firing events / effective N | 27 / **19** | 21 / 20 |
| **Revenue-direction hit-rate** | **40.7%** | 66.7% |
| Coin-flip null (placebo) | 50.0% | 49.9% |
| "Always predict majority" base rate | 51.9% | **90.5%** |
| Beats the majority base rate? | **No** | **No** |
| Placebo p (hit-rate ≥ real) | 0.87 | 0.092 |
| **Mean net beta-hedged drift** | **+1.6%** | +0.2% |
| Drift placebo p (sign-flip null) | 0.25 | 0.47 |

**Reading it honestly:**
- **Arm A hit-rate 40.7% is below a coin flip** (87th-percentile *worst* vs the null) and does **not** beat
  the 51.9% "always guess up" base rate. The civilian award-flow surprise carries **no** directional
  information about the next revenue print for these names.
- **Arm B's 66.7% looks higher but is an illusion of base rate:** the primes' revenue almost always beats the
  trailing-4Q model (up-rate 90.5%), so "always predict up" scores 90.5% — the signal's 66.7% is *below* that.
  Arm B has no signal edge either; its raw hit-rate is the growth base rate, not the award-flow signal.
- **Drift is not significant in either arm.** Arm A's +1.6% directional drift has placebo p=0.25 (consistent
  with noise on 19 independent quarters); Arm B's is ~0.

---

## 4. Primary deliverable: edge(A) − edge(B), placebo, clustered-N

| Metric (censored) | edge(A) − edge(B) |
|---|---|
| **Revenue-direction hit-rate** | **−0.26** (Arm A 40.7% − Arm B 66.7%) |
| **Mean net beta-hedged drift** | **+0.014** (+1.4 pp; not significant — Arm A drift placebo p=0.25) |

- **Hit-rate edge is negative** — the uncovered, civilian-tilted tail does *worse* than the covered-prime
  control, the opposite of the registered hypothesis. There is no "uncovered-tail aggregation edge."
- **Drift edge (+1.4 pp) is not significant** and is not robust: on the *action-date (leaky)* panel it widens
  to +2.0 pp — i.e., what little positive drift difference exists is partly the posting-lag look-ahead, which
  G-4 censoring removes. On the censored panel, Arm A's own drift fails its placebo (p=0.25).
- **Placebo:** neither arm's hit-rate beats its shuffle/base-rate null; Arm A is *below* its null. The "edge"
  does not survive the timing-shuffle/majority-base placebo in either arm.
- **Clustered-N:** Arm A's effective independent N is **19 quarters across 2 names** — genuinely low power. We
  cannot *confirm* an edge at this N, but we *can* reject the registered ≥65% / positive-significant-drift
  claim, because the point estimate is on the wrong side of a coin flip, not merely noisy.

---

## 5. Why it fails — the mechanism (the actual product)

The frontrun thesis needs the obligation flow to **lead recognized revenue**. For the thinly-covered civilian
names that is exactly where it breaks: ICFI's censored civilian obligation flow kept *rising* through
2024–2025 (book-of-business ceilings) while its *recognized revenue fell* ($517M → $437M/qtr) as gov-services
contracts were de-scoped/terminated and outlays lagged or never materialized. Obligation (a ceiling
commitment) and outlay (revenue) **decoupled** in the de-scope regime — so a positive obligation surprise was
*anti*-correlated with the next revenue print (hence sub-coin-flip hit-rate). DLH compounds it: a $180M
micro-cap in steep revenue decline ($101M → $59M/qtr) with a **2.6% live bid/ask** and ~$0.06M/day volume —
even a real signal is uninvestable net of microstructure cost there.

**Encoded microstructure (the knowledge-graph contribution, independent of the failed alpha):**
- **Masking channel:** none — the awards are honestly, near-real-time disclosed (civilian median 0-day post).
- **Signal channel:** USASpending civilian obligation flow, load-date-censored. Observable, un-press-released.
- **Signal-to-price latency:** civilian **~0 days** (tradeable window exists) vs defense **~98 days** (dead).
- **Why no alpha despite a clean fast signal:** the **obligation→revenue transmission** is the broken link —
  for de-scoping services contractors, obligations are a *lagging/ceiling* quantity, not a revenue lead; and
  for the covered primes the same flow is already priced (base-rate growth, no marginal info). The edge would
  require a name where obligations genuinely *convert* to near-term revenue AND coverage is thin AND it's
  liquid enough to trade — an intersection that, in this universe, is empty.

---

## 6. §6 verdict

| §6 criterion | Result |
|---|---|
| Arm A hit-rate > 65% + positive net drift | **NO** — 40.7% hit (below coin flip), drift not significant |
| Arm B not significant | YES (not significant) — but Arm A isn't either |
| `edge(A) − edge(B)` significant & positive | **NO** — hit-rate edge −0.26 (wrong sign); drift edge +1.4 pp insignificant |

**→ FAILED.** It does **not** collapse to "Arm A ≈ Arm B beta" (the CEF kill) — it's worse than that: the
uncovered tail underperforms the control. The civilian gov-contract frontrun has **no real, tradeable,
beta-hedged edge** in this universe, and the tradeable Arm-A surface (2 liquid names, eff-N 19) is too thin to
ever confirm one even if the transmission worked. Reported as **low-power FAILED**, not overclaimed.

The durable output is the mechanism: gov-contract data has a **0-day civilian / 98-day defense posting
latency**, and — decisively — for thinly-covered services contractors the **obligation→revenue link is not a
lead**, so award-flow is not a revenue-frontrun signal there. That, plus the G-4 leak-check (a real $122M
median per-decision look-ahead that fabricates +0.7 pp of phantom drift), is what Phase 2 contributes.

---

### Files
- `outputs/phase2_govcon_backtest.json` — full panel (per name/quarter: censored + leaky signal, leak gap,
  labels, drift), per-arm scores, controls, verdict.
- `outputs/phase2_govcon_controls.json` — placebo (hit + drift), clustered-N, base-rate, edge(A)−edge(B).
- `build_govcon_panel.py` — load-date-censored point-in-time signal engine (G-1 civilian / G-4 censoring).
- `run_govcon_backtest.py` — panel build + labels + beta-hedged drift scorer.
- `run_govcon_controls.py` — placebo + clustered-N + majority-base-rate + edge(A)−edge(B).
- `outputs/px_cache/` — verified daily price series (DLHC, ICFI, ITA, XAR, LMT, GD, BAH; LDOS excluded — feed
  anomaly).
