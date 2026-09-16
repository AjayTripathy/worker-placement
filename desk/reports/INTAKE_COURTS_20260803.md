# INTAKE COURTS — 2026-08-03 (CLI court lane; pickup report for the main session)

Slate: `desk/data/DEPLOYMENT_INTAKE_20260803.json` (8 ranked names from the five deployment lanes).
Process: 6 parallel independent Opus courts (v1.3 evidence rule, two-mode disconfirm-first) + 1 fable
blue-team fork on the two positive-edge gates. **No court reached 6/10 → no red bench sat.** 7235.T /
7955.T deferred by the intake's own timing rule (court AFTER their Q1 prints this week).
Positions were polled same-turn before any sleeve claim (WAL 125sh, FSBW 120sh confirmed held).

## Batting line
**0 BUY / 3 gated WATCH / 3 PASS-AVOID.** The lanes sourced correctly-priced or already-resolved
setups; the run's real product is 11 generator/doctrine defects + 3 KG mechanisms + 7 frozen calls.

## Verdicts (full findings in edge_classifications/<ticker>.json; all live on /api/everything)

| Name | Court | Ruling | The one-line reason |
|---|---|---|---|
| SFPI.PA | 4/10 | WATCH → **adjudicated 3-leg entry** | €50.6M IAS-19 pension the screen missed: real economics 6.0-6.5x EV/EBIT, 12-18% net cash (not 4.5x/39%). H2-25 inflection IS real (S1 €5M→S2 €21M, slide-24-only). Honest issuer, not a PFIC. |
| CRVL | 4/10 | WATCH, **zero capital through the 08-05 print** | AI thesis is the wrong thesis (per-bill pricing = vendor keeps efficiency); real finding = Patient Mgmt (62% of rev) at +0.1% growth + the claims-count metric deleted from the 10-K the year it turned. Re-entry 50-53 (≤56 clean). |
| CASS | 2/10 | PASS at spot | +6.4pp "inflection" = 77% one-time base effects + 30% NII; net cost-out NEGATIVE. "Zero AI disclosure" refuted by the 07-23 8-K that already re-rated it +6.5%. Band 44-47 (= mgmt's buyback VWAP), expires 10-22. |
| MBGL | 4/10 | WATCH, **gated on 08-06/07 prints** | Drift edge spent; "initiation wave" catalyst FABRICATED (spins have no quiet period — 5 firms live day 1, mean PT $24.50; the $37 PT is unattributable, discarded). Standing pillar: CARFAX alone > entire EV. |
| PRIC-B.ST | 2/10 | AVOID (+ not executable) | Shrinking #4-of-4 (backlog −33%, Carrefour lost to Vusion); margin "inflection" substantially unhedged USD/SEK on a 90%-USD COGS base. IBKR SFB returned no-market-data on a "verified" line — live-tested. FV below price. |
| RVSB | 4/10 | PASS, edge-dead | Loss = 100% accretive securities restructuring, earn-back COMPLETE and printed 07-28 (5 days before sourcing — stale-input gate needed). Remaining: core PPNR −19.9%, classifieds +135% w/ zero provision. Held FSBW owns this theme from the acquirer side. Re-open <$4.70. |

## Blue-team adjudication (fable fork; principal ACCEPTED both — v1.1 taxonomy corrections)
- **SFPI gate-only OVERTURNED** (regret-negative ~2.7:1; P(touch €1.88 pre-catalyst) ~0.10 regime-conditioned;
  governance risk was triple-counted through a price gate). Adjudicated structure:
  **(1) tranche-now 0.4% @ €2.08-2.12 GTC** (size cut = the correct governance instrument) +
  **(2) Route A 0.75% @ €1.80-1.88 GTC** + **(3) H1-confirm add to 1.25% total, chase-cap €2.35**.
  Cap 1.5%; limits only, ≤20% of prints; 7 kill triggers incl. ANY-M&A->€15M = kill-on-announcement.
- **MBGL gate MODIFIED**: no-entry-before-08-07 upheld; conditions 1+2 conjunctive (guide reaffirmed AND
  CARFAX ≥6.5%); condition 3 (CARS OEM ≥ −12%) demoted to sizing modifier (0.75% clean / 0.5% ugly);
  execution on gate-clear = half limit $20.45 + half marketable chase-cap $21.75.

## Frozen calls (7, in calibration_ledger; packs armed for all ≤30d)
CRVL|08-05 labor-ratio≥47.6% 0.72 · CRVL-PM|08-05 PM<4% 0.75 · MBGL|08-07 guide-reaffirmed 0.55 ·
SFPI.PA|09-30 H1-ROC≥€12M 0.55 · CASS|10-22 opex-ex-recovery≥$38M 0.72 · PRIC-B.ST|10-22 rev↓+ttmEBIT↓ 0.70 ·
RVSB|10-31 classifieds>$22M+eff>78%+no-deal 0.75.

## Side job completed (user-directed): resolution packs
**24 packs armed, guard at ZERO flags** (was 16 flagged, then 8 more surfaced from freshly-frozen calls).
Six were KEY MISMATCHES (packs existed under old print dates; ledger calls re-dated) — re-keyed with
`rekeyed_from`. Grade-NOW candidates flagged inside the packs: **FOUR** (printed ~07-30 per its own
date_note) and **BBD ops** (printed 07-29). **IVN's DRC deadline (07-31) has passed** — grade or re-date by 08-07.

## OWED — for the main session to pick up
1. **Thesis docs (v1.4) before any envelope stages**: SFPI.PA (3-leg structure ready) and MBGL
   (conditional, only if the 08-07 gate clears). Nothing else stages — all other verdicts are PASS/AVOID/band-watch.
2. **08-05 to 08-07 catalyst cluster**: CRVL print Wed → grade both calls off the ~08-07 10-Q; CARG+CARS
   Wed → MBGL gate inputs; MBGL print Thu 8:00ET → gate + graded call; Hosiden 6804.T ~Thu (pack warns:
   pull instr 110 BEFORE fill on an amusement guide cut).
3. **7235.T / 7955.T courts** after their Q1 prints this week (EDINET lane).
4. **Generator defect wiring** — `verticals/generators/data/COURT_DEFECTS_20260803.json` (11 items, P1s:
   pension guard + executability gate + FCF fix on euronext_shelf; 8-K freshness gate on bank scanner;
   no-quiet-period rule on spinoff_orphans; 3 detector guards on ai_adopter). Per codify-doctrine these are
   owed as CODE, not notes.
5. **KG mechanisms to add to the dispatch index**: `bank_holdco_ratio_denominator`,
   `onetime_base_effect_inflation`, `disclosure_recency_gate`, `fx_cost_base_margin_mask`.
6. Consistency-check residuals (pre-existing): catalyst_overlays census gap on 14 held names (Brazil-gap class).

## Files touched (all backed up with .bak_20260803_*)
research_ledger.json (6 upserts) · edge_classifications/{SFPI.PA,CRVL,CASS,MBGL,PRIC-B.ST,RVSB}.json ·
entry_plan.json (8 intents incl. 2 adjudication-supersedes) · resolution_packs.json (+27 packs) ·
calibration_ledger.jsonl (+7 frozen) · DEPLOYMENT_INTAKE_20260803.json (court_results block) ·
COURT_DEFECTS_20260803.json (new). Dashboard verified fresh=1: all six names visible.
