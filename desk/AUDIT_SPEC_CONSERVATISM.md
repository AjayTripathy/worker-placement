# AUDIT_SPEC_CONSERVATISM v1.0 — FROZEN 2026-08-05 (pre-run; rules may not change after prices are pulled)

## Question
Is the book's conservatism paying? One graded number:
**NET = Σ avoided-loss (rejects) − Σ foregone-gain (gates/ladders never met + under-sizing + missed entries + deployment drag)**, every leg vs SPY over the identical window.

## Universe
`desk/data/research_ledger.json` records carrying a court/verdict AND a date; plus `desk/data/missed_entries.jsonl`; plus current IBKR positions. Records without a parseable date or listed ticker go to a REVIEW list (counted in coverage stats, not silently dropped).

## Cohorts & counterfactual rules (frozen)
1. **REJECTS** (verdict ≤3/10 or REJECT/AVOID/PASS/KILL/FRAME-REJECT/NOT-A-*): counterfactual = bought verdict-day close at the record's stated size (parse "x%"), else 0.5% of $3.4M. Avoided-loss = −(excess return vs SPY) × size$. Precision = share with negative excess.
2. **GATED/LADDERED, NEVER MET** (WATCH/GATE/WAIT/STAGE/CONDITIONAL/LADDER/STARTER-unfilled): counterfactual = bought verdict-day close ("meet the price" policy). RUN-1 PROXY (stated): if the min low since verdict penetrated close×0.95, treat as "price came to us" → excluded from foregone (flagged PARTIAL); else foregone-gain = max(excess,0) × size$. Wrong-side fill-cause subgrade DEFERRED to run-2 (needs per-fill news alignment).
3. **UNDER-SIZING**: court-originated live positions — red-survived 6s at 2.0× actual, 5s at ruled cap. Delta = unrealized P&L × (multiplier−1). Pre-v1.4 entries without recorded court sizing (HUBS/DFIN/GCT/CTSH/SAP/MNDY cohort) EXCLUDED and listed — their inclusion would flatter the under-sizing claim; run-2 may add them with a documented rule.
4. **MISSED ENTRIES**: every `missed_entries.jsonl` record priced at its own stated actionable moment and size.
5. **DEPLOYMENT DRAG**: (deployable $3.4M − equities MV) × (SPY window return − SGOV actual) over the window, using current deployment as the period average (RUN-1 PROXY, stated; run-2 uses the daily NAV series).

## Honesty rules
- Maturity: run-1 headline includes records ≥14 days old (sample would be empty at 30d); a strict ≥30d sub-headline prints beside it; from run-2 the 30d rule is primary.
- Horizons: to-date now; verdict+60d added as records season.
- Fills require close-basis penetration (proxy above), not a touch.
- FX/pence: returns computed within each ticker's own quote series (ratio-safe); GBp/GBX handled by series consistency.
- Coverage stats print on the cover: N classified / N review / N price-failed. Price failures are NEVER defaulted — listed.
- Window-regime caveat prints on the cover. Re-runs monthly (registry cron).

## Decision thresholds (wired before results)
- Cohort-1 precision ≥60% → bar stays; <55% → widen the bar.
- Cohort-3 cost > 2× cohort-1 marginal contribution → raise size caps for red-survived names.
- Cohort-2: never-met names beating SPY at >65% rate → activate "meet the price on RP_FAIR" formally.
- Cohort-5 drag > any other cohort's magnitude → deployment cadence is the binding fix.

## Outputs
`desk/data/conservatism_audit/{universe.json, prices_cache.json, results.json, REPORT.md}` + deck artifact + monthly registry entry `conservatism_audit`.

## AMENDMENT 2026-08-05 PM (principal correction)
C5 idle = settled cash + SGOV − option-securing collateral, AT IBKR ONLY. Plan-base capital not yet arrived is NOT drag. Run-1's $88,983 corrected to the true-idle figure in results_final; NET corrected accordingly.
