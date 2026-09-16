# When Does the AI-Capex Credit Cycle Break? — Ensemble Findings

**2026-07-30 · SignalOS · seven models, seven epistemologies · frozen call: P(credit event by end-2027) = 0.45**

Prompted by the groundbrkr essay *"The Second Derivative"* (Jul-2, 2026), which argues the AI buildout is a credit-financed real-estate cycle that breaks on capex **deceleration** — the 2008 mechanism, where delinquencies turned while home prices were still rising. Rather than argue with one model, we built seven independent ones and read the disagreement.

---

## The board

| Member | Approach | Vote | P(by end-27) | One-line reading |
|---|---|---|---|---|
| **Mechanism** | Refinance-wall constraint + 3 gates + 2008-mapped clock | AMBER | 0.30 | Wall binds 2028 only in the bust regime; Gate A (OpenAI terminal refinance) half-lit — the S-1 targets $730–850B, *below* the $852B last private mark; Gate B unfired |
| **LPPL / critical-point** | Sornette log-periodic fit + critical-slowing stats | **RED** | 0.86* | Qualified super-exponential fits on all 3 series (R² 0.94–0.95, beats baselines on BIC); critical time **t_c ≈ Dec-2026** on the cleanest fit; variance trends rising |
| **Credit-vs-equity basis** | The 2007 ABX signature: equity strong while credit widens | GREEN | — | **No divergence — because the equity leg is already soft.** Equal-weight AI basket −1.6% over 6m vs SOXX +40%; both legs weak together = repricing, not blindness |
| **Reference class** | 8 historical capex manias, survival curve on accel-peak→credit-event | AMBER | 0.46 | Median clock ~8 quarters; telecom (the closest analog) broke in 1–4q *because vendor financing made the suppliers the credit market* — and vendor-financing intensity today is HIGH |
| **Minsky stage** | Financing-quality classifier on real cashflow data | **RED** | — | **AMZN (1.02 capex/OCF) and ORCL (1.74, $40B rising issuance) are Ponzi-stage**; aggregate migrated HEDGE→SPECULATIVE in 3 years; $197B trailing-4Q net debt issuance |
| **Behavior tells** | Union of informed-party tells | AMBER | — | **CRWV insider selling at 10× prior-90d intensity, 82 distinct sellers, 15.8M shares.** 1 of 6 tells fired; 3 UNKNOWN (coverage gaps, honestly labeled) |
| **Network contagion** | Eisenberg-Noe clearing on the counterparty graph | structural | — | Propagation order is invariant: **neoclouds seize first even at a 50% OpenAI payment shock; ORCL secondary-defaults at full shock**; mega-caps bleed, don't break; the Anthropic wrap transmits ~5× less per dollar |

\* Conditional on the LPPL bubble description being correct; t_c dates the end of the super-exponential regime, not necessarily a crash.

**Ensemble vote: 1 GREEN · 3 AMBER · 2 RED (+1 structural). P(break by end-2027): median 0.46, range 0.30–0.86. By end-2028: median 0.74, range 0.60–1.00.**

---

## What independent models agree on (the convergent findings)

**1. CoreWeave is the canary, and it is coughing in three unrelated datasets.** Equity −35% in three months at 94% vol with Merton distance-to-default of 1.6 (credit basis); insider selling at 10× intensity with 82 sellers (behavior tells); first node to breach its buffer in every clearing scenario, even a 50% shock (contagion). Three members, three data sources, one name.

**2. Oracle is the concentrated hyperscaler.** Ponzi-stage financing (Minsky: capex 1.74× operating cash flow, funded by $40B of rising issuance), worst hit-to-buffer ratio in the network (contagion: secondary default on ~17% of its own obligations at a full OpenAI shock), and the equity already knows something (−25.7% over six months while the index rose 40%).

**3. The complex is already repricing beneath the index surface.** SOXX +40% is a cap-weight illusion carried by NVDA/AVGO; the equal-weight basket is *negative* over six months. Whatever "nobody sees it coming" means, it is not true of the levered periphery — the market is repricing the edges while the core melts up, which in past cycles is the *late* configuration, not the early one.

## What they disagree about (the informative part)

**Credit-basis GREEN vs LPPL RED is not a contradiction — it's a sequence.** The 2007 signature (equity blind, credit widening) hasn't formed because the periphery equity is already down; meanwhile the critical-point model says the *core index's* super-exponential regime ends around **December 2026**. Read together: periphery reprices first, core last — and the core's clock, on the one model that dates things, is short.

**The sharpest tension is Mechanism vs Minsky, and it cuts against our own skepticism.** The mechanism model's strongest counter-argument was that the article computes its second derivative on consensus estimates (systematically negative in booms) while *realized* capex acceleration hasn't turned and guides are still being raised — clock unstarted. But the Minsky member replies: the marginal financiers are *already* Ponzi-stage, and in the reference class that is precisely the covariate that selects the **short tail** of the clock. Telecom — the closest analog, right down to vendor financing (Lucent's $8.1B of customer financing then; NVIDIA's equity stakes in its own customers now) — broke 1–4 quarters after its acceleration peak, *while capex was still rising*, because when the suppliers are the credit market, the credit event doesn't wait for the capex cut. That argument moved our number up.

## Synthesis and the frozen call

**P(visible credit event in the AI complex by end-2027) = 0.45; by end-2028 ≈ 0.72.** (Frozen in the calibration ledger: `AI-BREAK|2027-12-31 @ 0.45`, cohort macro. "Credit event" = neocloud default/seizure, major take-or-pay impairment, GPU-ABS downgrade cascade, or RPO counterparty reprice — *not* an equity drawdown.) This sits above the mechanism model's solo 0.30 — the ensemble's net information was that the early tail is fatter than the structural model alone implied — and well below LPPL's conditional 0.86, which we discount for model-conditionality and pinned-parameter fragility.

**Predicted sequence** (contagion, invariant to parameter error): neoclouds → Oracle impairment → the securitized-credit channel (where a neocloud seizure becomes a *credit-complex* event) → hyperscaler margins → equity multiples. **The watch order**: CRWV credit and insiders (already firing), the OpenAI IPO terms (the one dated event — pricing below $852B or slipping past Q1-27 fires Gate A), and the Nash flip (first capex guide-down the tape rewards — still the regime gate; while all five raise guides, near-term break probability stays capped).

## Standing instrumentation

- `desk/ai_capex_watch.py` (registered, weekday): realized capex acceleration (the clock-starter, accumulating quarters) + earnings-day guide checks with the Nash-flip event study.
- `desk/models/ai_*.py`: all seven members runnable; ensemble via `python3 -m desk.models.ai_break_ensemble`. Re-run cadence: quarterly, after hyperscaler prints, and on any Gate A/B/C event.
- `python3 -m desk.models.ai_behavior_tells set T3 fired "..."` to log manual tells (round structure, securitization, depreciation extensions, tenders, metric swaps).

## Limitations, stated plainly

The article's exposure figures (backlog composition, burn rates, the Microsoft April de-support, the securitized CoreWeave facility) are **unverified** and enter contagion and mechanism as parameters — the contagion findings are robust to ±30% per edge, but not to the matrix being wrong in kind. LPPL's probabilities are conditional on its own bubble description and two of three fits have a pinned parameter. The members share underlying data (prices, filings) so their errors are not independent — the vote count overstates effective sample size. Three of six behavior tells are UNKNOWN, which is a coverage gap and must not be read as quiet. And a genuine capability jump that converts recycled capex into independent end-demand revenue falsifies the whole frame — that is the model's kill condition, and it is exactly what the labs are racing to produce before the wall.
