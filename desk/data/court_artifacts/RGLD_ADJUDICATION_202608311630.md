# ADJUDICATION — RGLD (Royal Gold, Nasdaq) — 2026-08-31

**Ruling: BLUE SUSTAINED — DONE, NO POSITION AT TAPE; three-rung entry ladder armed (T1 ≤$225,
T2 $200–210, T3 <$190), RGLD designated the sole royalty-core carrier of the ballast axis
(~$60k of the $150k target at full ladder). One household gate neither bench could see:
Parametric is SHORT 149 RGLD — staging at any rung requires the short to have rolled off, or
explicit principal acceptance of the offsetting-position (tax-straddle) treatment.**

## Tier re-verification (adjudicator, live — benches were IBKR-denied)

1. **Live tape (IBKR 4817403): $258.89, −1.5%** (bid/ask 258.63/259.16). Below both benches'
   $262.85 pack tape. 52w: 168.19–305.70; 26w low 186.33 (blue's July-low timing kill verified
   on the bar). 90-day ADV **$191.7M/day** — executability closed, trivially cleared.
2. **Blue's decisive overturn VERIFIED at the primary** (guidance 8-K, acc. 0000085535-26-000013):
   the 430–480k GEO five-year outlook is built from *named existing assets* — "expansions at
   Khoemacau and Platreef Phase 2… new production from assets including Corani, Great Bear,
   Hod Maden (NSR only), La India, Robertson and Warintza" — and **excludes** potential
   acquisitions and beyond-5-year starts (Fourmile, MARA, Oyu Tolgoi et al.). Volume grows
   ~25–35% over five years with zero incremental acquisition assumed. Red's finding 1 (122%
   acquisitions/OCF = mandatory replacement) is therefore a growth/maintenance conflation —
   red's own mind-change trigger (a) is met. Its finding 2's $164–196 FV dies with it
   (double-discount: capex charged out of OCF, then an EV/OCF multiple applied to the residual).
3. **Blue's corrections adopted**: honest multiple = **17.9x EV/OCF** (H1-annualized $1,257M;
   not red's flattering-basis 16.6x nor its stale-mix 21.4x TTM); buyback $203.80 was the
   contemporaneous market price (June range $197–223), not a revealed-FV ceiling — red's
   finding 3 OVERTURNED; realized drawdown beta ≈ **1.9x trough-to-trough** (306.25→186.33 vs
   gold −20.3%), red's 0.69x was a mismatched-window artifact — finding 7 OVERTURNED.
4. **Household exclusion surface (msprime.db, reporting_date 2026-08-14): Parametric holds RGLD
   SHORT −149 sh (−$34.4k)**, NEM long 148 sh. A long RGLD in ALPHA would internally cross the
   household's own short leg — offsetting positions (potential §1092 straddle: losses on either
   leg deferred while the offsetting leg is open). Not a court matter — a **staging gate**:
   at any band touch, re-poll Parametric positions first (sleeve rebalances monthly; the short
   may roll off), else surface to principal.

## Per-bench rulings

- Red 1 (replacement 122% of OCF) — OVERTURNED (verified conflation; Kansanshi $1.0B was a
  discrete, revolver-funded growth stream, and the 5-yr outlook needs no new deals).
- Red 2 (FV $164–196) — OVERTURNED (built on 1 + double-discount).
- Red 3 (buyback $203.80 = revealed FV) — OVERTURNED (same-window VWAP artifact).
- Red 4 (16.6x is the most flattering basis) — SUSTAINED AS METHOD; blue's 17.9x adopted.
- Red 5 (street-agreement, no screen-artifact edge) — SUSTAINED as CONSENSUS.
- Red 6 ($4,506 is LBMA average not realized) — SUSTAINED, immaterial.
- Red 7 (drawdown beta 0.69x, stress never happened) — OVERTURNED (1.9x trough-to-trough).
- Blue new findings (July-low timing kill; Hod Maden equity-call omission; deleveraging-phase
  read of the H1 capex lull; FV $211–252 below tape) — SUSTAINED.
- Refutability's T1 $255–265 — DENIED (both benches killed the entry at tape; the brief's own
  "margin of safety consumed" finding argues it).

## The ruling's shape

DAMAGE-ABSENT survives. The name is what the ballast axis wants — 1.9x drawdown beta *through*
a gold shock and a debt-free-ish annuity coming out of it — but at $258.89 it sits 3–23% above
the court's sustaining-adjusted FV band ($211–252) after a +27% one-month re-rate off $186.33.
Fairly-paid-risk is not available above the FV band. The axis argument ("refusing any position
leaves the hedge unbuilt") was heard and answered: the axis is not unbuilt — PHYS 320sh + the
resting 30.80/29.20 adds carry the metal leg today; the royalty leg earns its premium only at
a royalty-appropriate price.

**Ladder (armed in ledger; court-ratified, staging-gated on the Parametric check):**
- T1 **≤$225**: ~$20k (77 sh) — inside FV band, −13% from tape, a level traded 6 weeks ago.
- T2 **$200–210**: ~$20k — red's corrected entry zone; June's actual trading range.
- T3 **<$190**: ~$20k — July low zone; full royalty-core weight ~$60k.
- All rungs die 2027-02-28 (re-court on expiry or on pack triggers below, whichever first).

## Pack RGLD|2026-10-20 (Q3 prelim-sales 8-K, cadence-verified date)

- Total GEOs ≥110k with realized ≥$4,450 (inventory conversion: 27,400 oz Au + 371,200 oz Ag +
  0.7 Mlb Cu pre-loaded) → Q2 was a floor; loosen T1 to $240.
- GEOs <90k → delivery problem is real; tighten T1 to $210 (red's zone).
- Any Q3 repurchase disclosure showing avg >$250 → management re-anchoring; re-court.

## Calibration (frozen)

- RGLD-Q3GEO|2026-10-20: P(Q3 prelim total GEOs ≥110k) = **0.50**.
- RGLD-BB250|2026-11-04: P(Q3 buyback average price >$250) = **0.30**.

## KG dispositions

- `issuer_buyback_price_as_fv_anchor` (red) — ACCEPTED-GATED: mandatory same-window VWAP
  comparison; fires only when repurchase avg sits meaningfully BELOW the contemporaneous
  market VWAP (a price the issuer declined to pay), never on a rallying tape (RGLD's $203.80
  WAS the June market).
- `depletion_replacement_cash_ratio` (red) — ACCEPTED-AMENDED: acquisitions must first be
  classified discrete-growth vs sustaining (debt-funded single-asset purchases excluded);
  the unamended ratio misfired here (122% collapsed to ~8% sustaining once Kansanshi was
  identified).

## Drains owed (unverified_ledger)

- RGLD 144/Form 4 pairs (5/11, 6/16, 8/28) unread by any bench — 10b5-1 cadence check.
- Sustaining-capex assumption rests on one half-year ($50M = 8% of OCF); re-verify at the
  FY26 10-K capital plan.

Sources: 10-Q acc. 0000085535-26-000041; guidance 8-K acc. 0000085535-26-000013 (verbatim
asset-base extract re-pulled this session); Q3-2025 8-K acc. 0000085535-25-000158 (Kansanshi
$1.0B / $775M revolver); IBKR live tape + ADV 2026-08-31; msprime.db positions 2026-08-14.
