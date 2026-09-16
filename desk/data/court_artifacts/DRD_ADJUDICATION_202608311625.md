# ADJUDICATION — DRD (DRDGOLD ADR, NYSE) — 2026-08-31

**Ruling: BLUE SUSTAINED IN PART — STARTER 0.4% PROPOSED (miner-op-leverage sub-sleeve of the
ballast axis, explicitly labelled a levered rand-gold call, crash-beta, NOT royalty core).
Red's REJECT denied: its headline kill (prize-table "roof at the tape") used the wrong terminal
volume and its leverage-asymmetry kill used an FX input wrong in the direction of its own case.**

## Tier re-verification (adjudicator, live — benches were IBKR-denied all session)

1. **Live tape (IBKR 45210327, NYSE):** $28.00 (−2.7% today), prior close 28.77; 52w 18.51–39.01
   → −28.2% off high. ADV 90d **$9.46M/day** → 1% rail ~$95k/day: a $4–8k slice fills instantly.
   **Executability CONFIRMED at the gateway** (closes the benches' coverage gap).
2. **The decisive dispute — terminal volume.** Company disclosure via Daily Maverick 2026-07-15:
   Vision 2028 = 2.15 → **3.0 Mtpm throughput, ~6 tonnes (~193koz) gold/yr by 2028**, R10bn
   across five projects. Red's 5,150 kg row was the FY2027 guide midpoint — a tautology, exactly
   as blue charged. Blue's 6,220 kg slightly overstates (6.0t = 6,000 kg); recomputed at the
   honest 6,000 kg, red's own AISC/tax/multiple inputs, ZAR 16.13:
   **$4,000/oz → ~$28.1 ADR (tape); spot ~$4,470 → ~$35.5 (+27%); $5,000 → ~$44 (+57%);
   +50% clears ≈ $4,850/oz** — not red's ~$5,550. With AISC inflated 6%/yr to R1,382,000 by
   FY2029, spot still prices ~$31 (+10%). The fully-built value at spot is +10–27%, not zero.
3. **The one kill both benches proved and I sustain:** the FY2027 flat-margin tripwire.
   Flat vs FY2026 needs **~$4,570/oz at ZAR 16.13**; spot ~$4,470 is 2–3% below. FY2027 is a
   flat-to-down transition year at spot — this gates SIZE and TRANCHE, not existence.
4. **Category finding sustained with a correction of scope:** DRD was never proposed for the
   royalty CORE — the 7/08 backtest's own construction carries a separate 15% miner-op-leverage
   sub-sleeve, which is where DRD was enqueued. The benches' "category substitution" attack
   partially fought a strawman. What survives of it: op-lev names are crash-beta, so they fill
   the sub-sleeve that exists for torque, never the core that exists for crash resilience.

## Per-finding rulings (red numbered)

- R1 prize table — **OVERTURNED** (terminal-volume substitution; verified above). Reduced to
  SIZING: upside at spot is +10–27%, real but not a discount worth chasing after a +19% run.
- R2 leverage asymmetry — **OVERTURNED** (ZAR on 2026-01-29 ≈ 15.7, not 17.2; ratio ~1.5x vs
  ~1.95x predicted — residual explained by the disclosed volume ramp).
- R3 tripwire — **SUSTAINED** (both benches independently; I recomputed). The load-bearing leg.
- R4 street divergence — reduced per blue: 2-analyst orphan, H.C. Wainwright at Buy/$35 raised
  post-print; street misses this name to the UPSIDE.
- R5 "+27% run" — **OVERTURNED as computed** (VWAP-to-spot cross-currency artifact); +19%
  close-to-close stands; still a chase off the low → entry discipline, below.
- R6 venue divergence — **OVERTURNED** (spoken rounding + segment-vs-group category error).
  multi_venue detector needs a ±3% spoken-rounding tolerance — logged.
- R7 Withok permit — **REDUCED, mechanism corrected per blue** (slippage raises near-term FCF;
  the real risk is Ergo deposition capacity). Dated observable: approvals targeted Dec 2026.
- R8 Sibanye 50.1% — SIZING note (control real; R955m of dividends aligns on payout).
- R9 category — sustained as re-scoped in §4 above.
- Blue B (terminal-capex double-count risk) — moot after R1's overturn.
- Blue C (3.7% carry) — sustained; verified dividend yield 1.83% per IBKR field is the
  FORWARD indicated post-final-only figure; FY2026 declared total ≈ R2.20/sh → ~4.9% trailing
  on the ordinaries at R45.4. Carry is real; precise forward yield UNRESOLVED (final R1.20
  declared; interim policy variable) — recorded, does not change the ruling.

## Position and gates (PROPOSED — NOT STAGED)

- **STARTER 0.4% NAV (~$4.2k ≈ 150 ADR)** at ≤$28.50 limit, funded from the miner-op-leverage
  sub-sleeve (15% × $150k axis = $22.5k budget; ~$18k remains unallocated after this).
- Role label (binding for attribution): *levered rand-gold call; crash-BETA; contributes zero
  crash-convexity credit to the ballast axis; the royalty core must still be built separately.*
- **Add gates (any one):** (a) Q1 FY2027 operating update AISC tracking ≤R1,150,000/kg with
  volume at top of 160–170koz; (b) ZAR weaker than 17.0 at flat USD gold; (c) ADR ≤$25 WITH
  rand gold ≥R2.25m/kg (the mechanism guard that answers red's value-ladder flow-gate — a $25
  print caused by rand-gold breakdown does NOT fill).
- **Exit/void:** rand gold <R2.1m/kg sustained 5 sessions (FY27 margin −20%+ → thesis regime
  changed), or Withok DENIED with Ergo deposition constraint named.

## Packs and calibration

- Pack DRD|2026-12-31 (date field 2026-12-31): Withok TSF approval decision — targeted Dec 2026
  per company; APPROVED + FY28 capex guide reaffirmed = add-gate support; DENIED = exit review.
- Pack DRD|2026-11-15 (date field 2026-11-15, date-band ~Oct–Nov, UNCONFIRMED cadence-derived):
  Q1 FY2027 operating update — grade AISC/volume vs add-gate (a).
- Freeze: DRD-WITHOK|2026-12-31 P(approval granted by 12/31) = **0.45**.
- Freeze: DRD-Q1AISC|2026-11-15 P(AISC ≤R1,150,000/kg) = **0.30**.

## KG dispositions

- `terminal_state_volume_substitution` (blue) — **ACCEPT** (amended: DRD target is 6.0t/193koz,
  not 200koz; evidence text corrected). Verified here: it inverted red's verdict.
- `leverage_asymmetry_residual` (red) — **ACCEPT-GATED**: FX at both endpoints must come from a
  verified pair series; this instance failed on an assumed 17.2 vs actual ~15.7.
- `pre_print_zero_strike_award_vwap` (red) — **REJECT** per blue's finding A: FY2025 award was
  also struck mid-August (R27.42, VWAP to 13-Aug-2025) — fixed remuneration calendar, both
  years, not opportunistic timing. Do not harvest.

## Drains / desk tickets

- SA permits COVERAGE GAP: Ekurhuleni/Merafong municipal + DMRE/DWS water-use licence records
  for Withok — the highest-value new connector this case names (dated Dec-2026 tripwire).
- Facilities geocode BROKEN for RTSF (Gauteng centroid ~50km off) and Withok (no record) —
  fix before any satellite read; pull a plant_thermal baseline scene for Brakpan before the
  Q1 update.
- multi_venue_disclosure_consistency: add ±3% spoken-rounding tolerance before flagging
  call-vs-filing numerics.
- KG feature-tag errors: `asia_operating_jurisdiction` on a South African filer; three
  clinical-detector dispatches on a mining issuer.

Sources: FY2026 6-K acc 0001628280-26-057862 (fs_fy2026.htm, resultsrelease2026hy2.htm);
trading statement acc 0001628280-26-056522; awards 6-K acc 0001628280-26-059228 + SENS
22/08/2025 (FY25 calendar); Daily Maverick 2026-07-15 (Vision 2028 3Mtpm/6t, company
disclosure); Miningmx (Withok slip); IBKR live 45210327 2026-08-31.
