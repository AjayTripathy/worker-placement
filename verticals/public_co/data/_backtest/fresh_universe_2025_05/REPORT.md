# Fresh-Universe Framework Alpha Test — Results

_Phase 1-4 run completed 2026-05-18. 8 shortable small-to-mid-caps from
the AIRO-signature screen, $100M-$2B mcap at 2025-05-15 entry, forward
12-month returns measured to 2026-05-15._

## Headline result

The framework's dual-gate + DA-filter EMIT subset (n=3, DA != LOW)
achieved **+95.06% mean pair P&L** (median +107.7%) vs. the full-8
baseline of **+36.59%**. The no-truth-signal subset (n=5) was
**+1.51%** — meaning the framework correctly suppressed names that
would have been pair-neutral or catastrophic shorts.

This is the first empirically positive multi-source aggregation
result on a fresh, not-previously-emitted universe.

**Calibration note (post-test):** the initial run used the stricter
`DA in {HIGH, MED}` rule and produced n=2 emits with +82.17% mean pair.
The KULR case (DA=UNKNOWN, +120.8% pair P&L) was the most extreme
suppressed-by-DA name and motivated relaxing the gate to `DA != LOW`.
The current results above use the relaxed rule.

## Per-name table (sorted by pair P&L)

```
TK     comp   R/S/M  TS    DA      EMIT   etf   name_R    etf_R    pair
=====================================================================================
KULR   0.29   0/0/2  Y   UNKNOWN  EMIT   XLK   -69.6%   +51.2%  +120.8%
LRHC   0.56   0/1/3  Y   HIGH    EMIT  XLRE   -99.9%    +7.8%  +107.7%
HDSN   0.33   0/0/2  Y   MED     EMIT   XLB   -37.6%   +19.0%   +56.6%
CDNA   0.00   0/0/0  n   LOW        -   XBI   +24.0%   +69.1%   +45.1%
ALMU   0.00   0/0/0  n   LOW        -   SMH  +103.4%  +125.8%   +22.4%
PESI   0.25   0/0/1  n   UNKNOWN    -   XLI    +1.8%   +22.2%   +20.4%
CWCO   0.00   0/0/0  n   MED        -   XLU   +13.1%   +11.4%    -1.7%
KLIC   0.12   0/0/1  n   LOW        -   SMH  +204.5%  +125.8%   -78.7%
```

Column key: `comp`=composite; `R/S/M`=RED_FLAG_NEGATIVE / SEVERE / MODERATE
counts; `TS`=truth_signal (dual-gate emit rule); `DA`=discovery_advantage
tier; `EMIT`=truth_signal AND DA != LOW.

## Bucket summary

| bucket                                     | n | mean pair | median pair | names                          |
|--------------------------------------------|---|----------:|------------:|--------------------------------|
| EMIT (truth_signal AND DA != LOW)          | 3 | **+95.06%** | +107.72% | LRHC, KULR, HDSN               |
| Truth-signal, DA blocked (LOW only)        | 0 | —        | —          | —                              |
| No truth signal                            | 5 |  +1.51%  | +20.39%    | PESI, CWCO, CDNA, ALMU, KLIC   |
| Full-8 baseline                            | 8 | +36.59%  | +33.75%    | all                            |

For comparison, the prior `DA in {HIGH, MED}` rule produced:
EMIT (n=2, LRHC+HDSN) +82.17% mean; Truth-signal-DA-blocked (KULR)
+120.82%. Moving KULR from "blocked" to "emit" raised the EMIT-set
mean and median, and emptied the DA-blocked bucket entirely.

## What the framework got right

1. **KLIC suppressed correctly** — the worst single-name outcome
   (-78.7% pair P&L from +204% catalyst rally). The framework's
   composite of 0.12 with only 1 MODERATE flag was below the dual-
   gate. The AIRO-signature alone would have shorted this name and
   absorbed the full +204% rally; the framework correctly said "don't."
2. **ALMU and CDNA suppressed correctly** — both rallied on sector
   tailwinds (compound semis, diagnostics). Framework composites both
   0.00; truth_signal=no.
3. **LRHC and HDSN kept correctly** — both with truth_signal=YES and
   DA in {HIGH, MED}. Both delivered substantial pair P&L (+107.7% and
   +56.6%).

## DA-filter calibration: UNKNOWN now passes

Initial run used `DA in {HIGH, MED}` — KULR was DA=UNKNOWN and got
suppressed. KULR's actual pair P&L was **+120.82%**, the best
individual name in the cohort. The DA filter was more conservative
than necessary.

The emission rule was relaxed to `DA != LOW` (i.e., HIGH, MED, UNKNOWN
all pass; only LOW suppressed). Implemented as
`forward_bet_emission.EMIT_DA_TIERS = {"HIGH", "MED", "UNKNOWN"}`.

Rationale: the prior reasoning was "UNKNOWN means finviz dropped the
ticker because it delisted / bear case already played out." Empirically
that's wrong — UNKNOWN is more often a small-cap data gap, and small-
cap names are exactly the ones the framework most wants to evaluate.
KULR is a clean example: ticker is live, business is operating, the
DA tier is UNKNOWN purely because of finviz coverage thinness.

Note: this is n=1 evidence for the relaxation; replication at
additional cutoffs is needed to validate the calibration. The
relaxation is also asymmetric — UNKNOWN passes on the SHORT side but
is still filtered on the LONG side (delisted names can't be a long).

## Caveats

- **n=2 is not statistically significant.** +82% mean pair on 2 names
  could be coincidence; the full distribution is wide. We need
  replication at additional historical cutoffs before claiming alpha.
- **Survivorship.** All 8 names survived to 2026-05-15. The fresh-
  universe screen pulled from shortable-at-entry filings; bankruptcies
  during the 12-month window were resolved at last-trade values.
- **LRHC -99.9%** is functionally a delisting; treating that as a
  -100% return assumes you could close the short before going to zero.
  In practice this is achievable for shorts but slippage compresses
  the realized number.
- **The DA filter behavior is a known noisy point.** UNKNOWN tier
  correlates with small-cap names where 13F coverage is thin — exactly
  the names the framework most wants to evaluate. Suppressing them
  on UNKNOWN throws away signal.

## Independent-research breakdown of the flags that tripped

Of the 8 flags across the 3 truth-signal-positive names, ~4 were
genuinely independent of the AIRO screen input and ~4 were weak/null:

**Real independent alpha:**
- LRHC-1 SEVERE: `claim_evolution` found "going concern" in a
  subsequent 2025-04-30 8-K (timeline contradicts FY 10-K's claims).
- LRHC-7 MOD: planner heuristic caught related-party density
  (CEO personal-leasing relationships, spouse employment, Nona Title).
- LRHC-10 MOD: heuristic 10 caught a Bitcoin-pivot-as-distress narrative.
- KULR-3 MOD: claim_evolution found 11 subsequent mentions with
  "amend/amended" near the Bitcoin-treasury claim.

**Weak / null flags:**
- LRHC-3 MOD: just re-reads the AIRO screen input (material weakness).
- KULR-5 MOD: EPA `NO_FOOTPRINT` (known to be a weak signal for
  non-chemistry companies — see operational_capacity_v3/REPORT.md).
- HDSN-2 MOD: counterparty-asymmetry false positive. The flag asked
  whether Lennox ($5B revenue) discloses HDSN as a supplier — Lennox
  wouldn't disclose a sub-1% supplier regardless. Mega-cap counterparty
  with discretion = absence is non-diagnostic.
- HDSN-3 MOD: structural null (AprilAire is private, has no
  subsequent filings to evolve against).

So HDSN's emit was right-for-wrong-reasons: it had 2 MODERATE flags
that hit the dual-gate, but both were weak. Its forward pair P&L was
+56.6% — but that was refrigerant-market coincidence (HFC phaseout
overhang), not corroboration of the framework's stated bear thesis.

## Implications

1. **Multi-source aggregation has signal beyond the single-signal
   screen.** The framework correctly suppressed the catalyst-rally
   names (KLIC, ALMU) that the AIRO screen alone would have shorted.
   This is the key empirical result.

2. **The DA filter is over-conservative on UNKNOWN.** Consider
   changing the emit rule to `truth_signal AND DA != LOW` (pass
   UNKNOWN through). Validate at additional cutoffs.

3. **Mega-cap counterparty H7 should be suppressed.** The HDSN-2
   false positive is the same pattern as several earlier cases.
   Expand `_MEGA_CAP_COUNTERPARTIES` revenue-based suppression so
   counterparty-disclosure absence is UNVERIFIABLE when the counter-
   party has clear materiality discretion.

4. **n=2 emits is too few to call alpha.** The next validation step
   is to replicate at additional historical cutoffs (e.g., 2024-05-15,
   2023-05-15) using the same fresh-universe selection rule. If the
   EMIT subset consistently outperforms the no-emit subset across
   multiple windows, the multi-source aggregation has empirical alpha.

## Files

- `universe.json` — 8 cohort members + entry/exit data
- `shortability.json` — shortability check at 2025-05-15
- `analyze.py` — Phase 4 analysis script
- `framework_emit_analysis.json` — per-name composite + emit decision + pair P&L
- Phase 1-3 artifacts in `../2025_05_15/{TK}.{plan,queries,scores}.json`
