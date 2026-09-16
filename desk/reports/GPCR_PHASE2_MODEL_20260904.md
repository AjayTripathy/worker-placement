# ALENIGLIPRON vs ELECOGLIPRON — PHASE 2 MATHEMATICAL MODEL + THE LIVER POST-MORTEM
**2026-09-04 · Desk analysis (FABLE). Inputs: ACCESS/ACCESS-II 8-Ks + Nature Medicine table,
AZ H1-26 6-K (VISTA/SOLSTICE), FDA labels, gap-sweep primaries. Items sourced from stable
pre-2026 knowledge rather than this session's pulls are tagged [K].**

## PART A — What actually killed the small-molecule livers

Five oral small-molecule GLP-1 agonists now have meaningful human exposure. The scoreboard:

| Molecule | Max daily dose | Liver outcome |
|---|---|---|
| Orforglipron (Lilly) | 17.2mg commercial / 36mg trial | CLEAN — approved label has zero hepatic warnings |
| Elecoglipron (AZ) | 75mg (top Ph2) | UNDISCLOSED (efficacy-only release; 24k-pt Ph3 = indirect confidence) |
| Aleniglipron (Structure) | 180mg Ph3 / 240mg tested | No DILI at n>625; 8 transient ≥3×ULN, 1 ≥5×, 0 ≥10× (≈1.3% excursion rate, all resolving ON drug) |
| Danuglipron (Pfizer) | ~400mg/day (200mg BID) [K] | KILLED Apr-2025: one asymptomatic potential DILI, resolved; Pfizer cited "totality... input from regulators" |
| Lotiglipron (Pfizer) | — [K] | KILLED Jun-2023 on transaminase elevations [K] |
| TERN-601 (Terns) | ~740mg/day at top [K-approx] | KILLED Oct-2025: 3 grade-3 elevations, **2 adjudicated DILI** (1 biopsy-confirmed) |

**The mechanism is chemistry, not pharmacology.** Three exonerating facts: GLP-1R is not
meaningfully expressed on hepatocytes; the peptide agonists (millions of patient-years) show no
hepatotoxicity — the class *improves* liver fat (semaglutide's MASH program); and the failures
don't share a scaffold with the survivors. What the failures DO share is **daily-dose burden**:
the liver clears these molecules through oxidative metabolism, and idiosyncratic DILI risk
scales with the mass of drug metabolized daily (the classic >100mg/day heuristic [K] —
reactive-metabolite load is roughly proportional to dose). The failures sit at ~400–740mg/day;
the clean approvals at 17–36mg. Danuglipron's BID regimen additionally doubled the
peak-exposure cycles per day. So: **molecule-specific in expression, dose-burden-mediated in
mechanism** — the class is acquitted, but high-milligram members carry structural risk.

**Where that leaves aleniglipron: in the middle, with a bounded but real residual.** 180–240mg
sits 5–10x above orforglipron and 2.4–3.2x above elecoglipron. The clean n>625 record bounds
true DILI incidence below **0.48%** (rule of 3, 95%) — which still permits **up to ~17 cases in
the 3,600-patient ACCOMPLISH-1** consistent with everything seen so far. Note the asymmetry in
what killed danuglipron: ONE asymptomatic resolved case in >1,400 was enough for Pfizer
post-lotiglipron. Aleniglipron already has 8 transient excursions on the record; the difference
between "transient excursion" and "DILI" is persistence and causality adjudication — at Phase 3
scale, with 10x orforglipron's dose burden, this is the honest tail risk the clean headline
doesn't extinguish. It is also why the FDA-label contrast matters so much: orforglipron earned
a §5 with *nothing* hepatic in it; that is the bar.

## PART B — The Phase 2 mathematics, five results

**B1. The 0.2pp "gap" is 0.1σ — unresolvable, permanently, at Phase 2 scale.** Aleniglipron
120mg: −11.3 (CI −13.9, −8.6 → SE ≈1.35pp). Elecoglipron 75mg: −11.5 (no CI disclosed; similar
N → similar SE). SE of the difference ≈1.9pp; the observed 0.2pp difference is **0.10σ**.
Detecting a true 2pp difference at 80% power needs ~250/arm (these ran 56–65); detecting 1pp
needs ~1,000/arm. **No Phase 2 in this class can rank these molecules. Anyone claiming an
efficacy ordering from these trials is reading noise.**

**B2. The weight-gaining placebo is a ~7% event — which is exactly why you don't headline it.**
P(a ~20-patient placebo arm drifts to +1.1% when truth is ≈−0.7%, σ≈5.5%) ≈ **7.2%**. Not
aberrant — a one-in-fourteen draw. But the company's headline (−16.3 adjusted) inherits the full
+1.9pp of placebo divergence. Small-N placebo arms are lottery tickets; ACCESS-II drew a
flattering one.

**B3. Trajectory fitting kills the "no plateau" story as marketed.** Fit W(t)=W∞(1−e^(−t/τ)):
- **Elecoglipron** (26wk 10.5% → 36wk 11.8% absolute, same study): **τ≈17wk, W∞≈13.4%
  absolute** — predicted 76-week value ≈13.3%; the curve is ~90% saturated already.
- **Aleniglipron** cannot be fit within one study (one timepoint). Forcing a fit through the
  56-week open-label 16.2% requires **τ≈60wk and W∞≈27% absolute** — an asymptote no oral or
  injectable mono-agonist has ever approached. The far likelier reading: the OLE point is
  inflated by **completer/survivor bias** (dropouts lose less and exit the denominator) plus
  open-label effects. Correcting to plausible τ (25–35wk), aleniglipron's true asymptote is
  **~15–17% absolute** — better than elecoglipron's ~13.4 if the within-study points are taken
  at face value, but the comparison is τ-model-dependent and elecoglipron has no >36wk data.
  **"No plateau" is what an exponential looks like at t<2τ — both companies say it; neither
  curve supports a claim beyond ordinary saturation kinetics.**

**B4. Two independent methods put aleniglipron-180's true effect at ≈−12.4pp, not −16.3.**
(a) *Dose–response*: ACCESS's own within-study curve (−8.2/−9.8/−11.3 at 45/90/120mg) runs
~2pp per dose-doubling; extrapolating the 0.58 doublings to 180mg → **−12.5pp**.
(b) *Bayesian shrinkage*: prior = the oral class (four independent programs at −11.3/−11.5/
−11.6/−11.8, class σ≈1.0); likelihood = ACCESS-II's −16.3 with SE≈2.0 (n≈20/arm) → posterior
**−12.4pp (SE 0.9)**. Two methods, no shared assumptions, same answer. **The desk's estimate
of aleniglipron-180's true placebo-adjusted effect: −12.4 ± 1.0pp** — modestly above class,
nowhere near the marketed 16.3.

**B5. FROZEN PREDICTION — ACCOMPLISH-1, registered for grading (2028).** Start from −12.4
(B4), add ~+1.5pp for 36→76-week duration (decelerating curve), subtract the estimand haircut
(on-treatment→regulatory ITT: orforglipron's own registry-vs-label gap was 2.5pp at 10–24%
missingness; assume 1.5–2.8pp at aleniglipron's expected discontinuation):
**predicted ACCOMPLISH-1 placebo-adjusted ITT at week 76: −11.1 to −12.4pp, point −11.7,
conditional on no hepatic event** (Part A tail). Versus Foundayo's label −9.0: a real but
modest ~2.5pp edge — enough to matter clinically, nowhere near the 4–7pp the −16.3 framing
implies. If the print lands in-band, the estimand model is validated; below −10, the bear owns
the name; above −13.5, we were wrong in the good direction and the shrinkage prior was too strong.

**Near-term corollary (Q3 pack, gradeable this month):** expect the OLE 72-week release to
headline **≥16.5% absolute** (open-label completer arithmetic makes this near-mechanical,
p≈0.7) — treat that number as NON-decisive regardless of size; the decisive lines remain
mature discontinuation and any hepatic table.

## Bottom line on "which is better"

The molecules are efficacy-tied beyond Phase 2's power to resolve (B1); aleniglipron's headline
premium is placebo-draw + estimand + small-N artifacts (B2–B4) over a true edge of perhaps
~1pp at matched dose-response — bought at 2.4x elecoglipron's dose burden, which is precisely
the axis the class's failures died on (Part A). Elecoglipron's missing tolerability table and
aleniglipron's OLE discontinuation print are the two facts that will actually rank them.


---

## ADDENDUM (2026-09-04): ELECOGLIPRON'S PHASE 3 UNDER THE SAME MODEL + DIRECT COMPARISON

### B6. FROZEN PREDICTION — EMBOLD (elecoglipron Phase 3)

Same machinery, cleaner inputs (N=310, ~60/arm, well-behaved placebo means the shrinkage barely
moves it): elecoglipron-75's posterior true effect is **−11.44 (SE 0.80)** — it sits exactly at
the class mean with better precision than aleniglipron's estimate. But its trajectory is ~90%
saturated (τ≈17wk, W∞≈13.4% absolute → 13.2% by week 72; only +0.4pp of duration uplift left),
so after the same 1.5–2.8pp ITT estimand haircut:

**EMBOLD predicted placebo-adjusted ITT at week 72–76: −9.0 to −10.3, point −9.7 — essentially
a replication of Foundayo's label (−9.0) — CONDITIONAL on 75mg being the top Phase 3 dose.**
The conditional matters: Embold's dose arms are not yet disclosed, and AZ has its own
dose-response curve to climb. At a 100mg top dose the point moves to ~−10.5; at 150mg, ~−11.7 —
identical to our ACCOMPLISH prediction. **The entire modeled Phase 3 gap between these drugs
(~2.0pp in aleniglipron's favor) is a DOSE choice, not a molecule difference** — aleniglipron
"wins" the model only because Structure is running 180mg while AZ disclosed 75mg, and dose is
exactly the axis the class's liver failures died on (Part A).

Registered alongside the ACCOMPLISH prediction; grading a competitor's print is free calibration.

### THE DIRECT COMPARISON

**Trial mathematics:**

| | Aleniglipron (Structure) | Elecoglipron (AZ) |
|---|---|---|
| Powered Ph2 result (adj) | −11.3 @36wk, 120mg (N=230) | −11.5 @36wk, 75mg (N=310) |
| Observed gap | **0.2pp = 0.10σ — pure noise** | |
| Marketed headline | −16.3 (N=85, safety-primary, +1.1% placebo) | none marketed beyond the 6-K |
| Headline honesty | inflated: 7%-probability placebo draw + estimand + n≈20 arms | conservative: single disclosure, clean placebo, unknown estimand |
| Desk true-effect estimate | **−12.4 ± 1.0 (at 180mg)** | **−11.4 ± 0.8 (at 75mg)** |
| Precision of that estimate | worse (small arms, cross-study) | better (one clean study) |
| Trajectory | asymptote ~15–17% abs (OLE 16.2 is survivor-inflated; implied 27% rejected) | asymptote ~13.4% abs, ~90% saturated |
| Dose-response headroom | at 180mg, near its own curve's top | undisclosed above 75mg — real upside optionality |
| Ph3 prediction (frozen) | **−11.1 to −12.4 ITT @76wk** | **−9.0 to −10.3 @75mg** (−11.7 if 150mg) |
| Tolerability disclosed | fully: nausea 65–71%, vomit 32–45%, disc 10.4% (5mg start) / 2–3.4% interim (2.5mg) | **NOTHING — the black box** |
| Ph3 scale | 4,700 pts, 2 trials, obesity+T2D | 24,301 pts, 9 trials, incl. HF + CKD outcomes |

**The molecules** (tagged: much of the chemistry is undisclosed on both sides):

| | Aleniglipron | Elecoglipron |
|---|---|---|
| Daily dose burden | **180–240 mg** — the model's central risk | **75 mg** (2.4–3.2x lower) |
| Liver implication (Part A) | middle of the danger axis; rule-of-3 permits ~17 Ph3 cases | lower burden = structurally lower idiosyncratic-DILI prior; but zero disclosed hepatic data |
| Regimen | once daily, 2.5mg start, 4-week titration steps | once daily [AZ-stated]; titration undisclosed |
| Food effect | **never disclosed** (the cheap open question) | undisclosed |
| Bias/pharmacology claim | "G-protein-biased" — COMPANY-ASSERTED, zero PubMed | partial/biased agonist per AZ framing — likewise undisclosed |
| GI profile as kinetics proxy | nausea 65–71% at efficacious doses — no evidence the bias decoupled aversion | unknown; SOLSTICE held a semaglutide head-to-head AZ hasn't shown |
| Origin / royalty burden | in-house (Gasherbrum); **royalty-free**, 24 patent families to 2041–45 | licensed from Eccogene (China) — economics undisclosed |
| Owner's balance sheet | $1.34B, dilution before data is base case | AZ — no constraint; dapagliflozin combo franchise attached |

**Reading it straight:** as *molecules*, the honest statement is that they are efficacy-
equivalent within measurement power, elecoglipron achieves the class-standard effect at a
third of the metabolic load (the single most important molecular fact on the table given how
this class fails), and aleniglipron's only demonstrated molecular edge — more effect at more
dose — is the expensive kind. As *data packages*, aleniglipron is far more transparent (full
tolerability, published hepatic tables, peer review) while elecoglipron is an efficacy press
release wearing a 24,301-patient vote of confidence. As *bets*, they aren't comparable at all:
one is a $2.1B single-asset equity that must dilute, the other is a rounding error inside AZ.
The two disclosures that re-rank everything: Embold's dose arms (posts to the registry
eventually — watch it), and any elecoglipron tolerability table.