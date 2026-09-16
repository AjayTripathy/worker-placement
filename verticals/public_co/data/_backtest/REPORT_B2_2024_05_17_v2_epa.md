# Signal OS — B2 Rescore Report (EPA v2)

_Cutoff: 2024-05-17  ·  Forward window: 2024-05-17 → 2025-05-17_
_Rescore generated 2026-05-17 (today's FRS data, not point-in-time)._

## What this is

B2 is a **rescore** of B1 with one change: the EPA `epa_emissions` v2
connector (FRS + TRI + GHGRP + claimed-location audit) is run against
each industrial-cohort ticker's `physical_facility` (or
`production_volume`) claim, and the result is inserted at position 0
of the queries list so the deterministic scorer adjudicates that
claim via the EPA test.

Industrial cohort (n=14): PLUG, FCEL, HYZN, BE, BLDP, LIN, APD, ENVX,
MVST, QS, SES, SLDP, ALB, LAC.

## Headline

**Two new MODERATE_UNDERDELIVERY flags** appear that B1 didn't have:

| Ticker | Claim                | B1 sev          | B2 sev          | EPA signal                            |
|--------|----------------------|------------------|------------------|---------------------------------------|
| BLDP   | BLDP-6 (US mfg)      | UNVERIFIABLE     | MODERATE+esc    | NO_EPA_FOOTPRINT (0 FRS under "Ballard Power") |
| SES    | SES-5 (Shanghai+ROK) | UNVERIFIABLE     | MODERATE+esc    | FRS_PERMITTED_NO_INDUSTRIAL_REPORTING |

Both are legitimate R/M divergences. BLDP claims a U.S. manufacturing
presence in its FY2023 10-K, but EPA's master facility registry has no
record of any "Ballard Power" US facility. SES claims battery cell
manufacturing in Shanghai and Chungju (both non-US) — the EPA test is
asymmetric for the non-US ops, but the absence of *any* meaningful US
EPA footprint at SES's stated scale is also informative.

Composite impact:
- BLDP: 0.000 → **0.045** (single flag, 11 claims)
- SES:  0.000 → **0.062** (single flag, 8 claims)

Both well below the 0.6 emit gate. The framework would still decline
to trade these names. But it now *flags* them as worth a Phase-3
review where previously it was silent.

## Flips on the rest of the cohort

| Ticker | Target claim | Flip              | EPA signal                            |
|--------|--------------|---------------------|---------------------------------------|
| FCEL   | FCEL-4       | UNVE → PASS         | INDUSTRIAL_SCALE_CONFIRMED (Torrington CT) |
| BE     | BE-2         | UNVE → PASS         | INDUSTRIAL_SCALE_CONFIRMED (Fremont CA, Newark DE) |
| LIN    | LIN-3        | UNVE → PASS         | INDUSTRIAL_SCALE_CONFIRMED (110 TRI, 307 GHGRP — real) |
| APD    | APD-3        | UNVE → PASS         | INDUSTRIAL_SCALE_CONFIRMED (71 TRI, 363 GHGRP) |
| QS     | QS-4         | UNVE → PASS         | INDUSTRIAL_SCALE_CONFIRMED (San Jose CA) |
| ALB    | ALB-4        | UNVE → PASS         | INDUSTRIAL_SCALE_CONFIRMED (Magnolia AR, 11 TRI, 77 GHGRP) |
| PLUG   | PLUG-4       | UNVE → UNVE         | FRS_PERMITTED_NO_INDUSTRIAL_REPORTING (16 FRS, 0 TRI) — electrolytic, sub-threshold by chemistry |
| HYZN   | HYZN-1       | UNVE → UNVE         | FRS_PERMITTED_NO_INDUSTRIAL_REPORTING (1 FRS, Bolingbrook IL) |
| ENVX   | ENVX-1       | UNVE → UNVE         | FRS_PERMITTED_NO_INDUSTRIAL_REPORTING (3 FRS) — Penang MY is international |
| MVST   | MVST-2       | UNVE → UNVE         | FRS_PERMITTED_NO_INDUSTRIAL_REPORTING (2 FRS, Windsor CO missing) |
| SLDP   | SLDP-4       | UNVE → UNVE         | FRS_PERMITTED_NO_INDUSTRIAL_REPORTING (4 FRS, Thornton CO ✓) |

The UNVE → PASS flips are corroborative — the framework can now
confirm operational scale for the big names instead of leaving them
unverified. That's a positive: future false-positive shorts on
LIN/APD/BE are now harder for the framework to emit.

## Scorer aggregation fix

The first pass of this rescore exposed a systemic scorer bug: `score_claim`
only inspected `results[0]`, so multi-result claims silently dropped every
result past the first. The B2 EPA insertion at position 0 collided with
existing M-sources — LAC-7 in particular went PASS → UNVE because EPA
can't see Argentina but the original non-EPA adjudication PASSed.

Fixed in `deterministic_scorer.py` by aggregating over all results: each
result scores independently, the worst severity wins (with PASS beating
UNVERIFIABLE so any successful M-source confirmation surfaces), and
`escalation_needed` is the OR across results. Verified against B1: zero
drift on 19 tickers under the new aggregator, and LAC-7 returns to PASS
under B2. The fix is independent of EPA — it stabilizes any future
multi-source claim adjudication.

## Caveats

1. **Today's FRS, not 2024 FRS.** The rescore queries Envirofacts live
   at 2026-05-17 cutoff. Some PLUG facilities (Woodbine GA registered
   2024-Q1, in-scope) match the cutoff; others (Graham TX 2025+) are
   post-cutoff and shouldn't be credited to the May 2024 framework.
   This rescore reads as "what does today's framework say about these
   names" rather than "what would the framework have said in May 2024
   if it had this connector then."

2. **Substring noise on generic names.** "Ballard", "Linde", and a few
   others substring-match unrelated facilities. The patch run for BLDP
   used "Ballard Power" (yielded the right zero-hit answer);
   LIN/APD still report inflated FRS counts but their TRI/GHGRP
   counts are real (3-digit). A v2.1 connector should accept a
   `name_patterns: list[str]` argument so callers can specify how
   strictly to match.

3. **Single test at one cutoff.** B2 doesn't speak to forward-test
   outcomes — same 17 names, same 2024-05-17 cutoff, just enriched
   with the EPA v2 layer.

## Comparison to B1 final TL;DR

B1: framework emits ZERO signals across all three cohorts at May 2024.

B2: framework emits TWO new MODERATE flags (BLDP, SES) — both well
below the emit gate, both legitimate R/M divergences worth a Phase-3
review. The headline TL;DR is materially unchanged: at May 2024 the
framework still wouldn't trade any of these names. But the EPA v2
connector is producing the kind of operational-capacity diagnostic
the framework lacked — visible in the BLDP and SES flags, and in the
correctly-confirmed PASSes on the big industrial-gas / specialty-chem
names where blanket UNVERIFIABLE was the wrong answer.
