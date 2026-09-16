# TLH SLEEVE — HEDGE DECISION FROM FIRST PRINCIPLES
**SignalOS desk · 2026-08-28 v2 · principal directive: set aside the prior runbook ratification; derive the recommendation from scratch. The 8/21 collar spec is evaluated below as one candidate among several, with no incumbency.**

## Step 1 — What exactly is being hedged?
The household's dominant concentrated risk: **$5.18M of AI-complex exposure on a ~$19M household**
(Parametric $3.5M internal + ~$700k external GOOGL + index tech weights; the new sleeve adds
~$1.0M more). The desk's own 7-model ensemble freezes **P(credit event by end-2027) = 0.45** —
and, critically, predicts a **sequence**: neoclouds → Oracle → the credit channel → megacap
margins → equity multiples. The thing the household actually loses money on (the equity leg) is
the LAST step. A −30% complex repricing ≈ **−$1.55M**.

## Step 2 — What protection already exists before buying anything?
1. **Harvest convexity:** realized losses recover ~37.1¢/$ against this year's gain. On the
   $3.2M sleeve a −30% throws ~$220–370k of tax value. Real, but partially double-counted —
   crash-harvest and planned harvest draw on the same lots.
2. **Reserve anti-correlation:** $1.855M sits in bills; the liability it reserves shrinks in
   drawdown states.
3. **The alpha book is already light AI by court action** — the conveyor rejected the crowded
   AI-adjacent names all month (CORZ, AMPX, KTOS, XE, UMAC, RDW all FLAT/meme-excluded).
4. **The sequence is warning.** Credit-first means the desk's tripwires (CRWV credit event,
   Gate A on OpenAI terms, the Nash flip) are designed to fire BEFORE the equity leg — an
   informational asset most hedgers don't have.
Net residual: the household is exposed to (a) the equity leg arriving *faster than the sequence
model expects* (the no-warning branch), and (b) a deep, slow grind the tax code only partially
recovers.

## Step 3 — What does the upside branch cost?
The household is a **net buyer** (September tranche likely not the last; the escrow anniversary
structure suggests more). Any structure that sells the melt-up (a call leg) charges its "savings"
against the branch the household most wants to own. First principles: **caps are mispriced for a
net buyer** — the collar's cheapness is an illusion of accounting, not economics.

## Step 4 — The instrument menu, priced per unit of the RESIDUAL risk
| Structure | Cost/yr | Covers no-warning branch | Covers deep grind | Caps melt-up | Uses the sequence edge |
|---|---|---|---|---|---|
| Naked 10% OTM puts (full overlap) | ~$45–90k | yes | yes | no | no — pays for warning we already have |
| Collar (8/21 spec) | ~$25–50k | yes | yes | **YES** | no |
| Tail spread (10/30% OTM) | ~$15–25k | yes | no (hands off to tax code) | no | partially |
| Nothing (self-insured) | $0 | **no** | partial (37¢/$) | no | wastes it |
| **Gate-triggered ladder** (buy on tripwire fire) | ~$0 standing; pay-on-signal | no | yes | no | **fully** |

The pure structures each fail one test. The naked put and collar pay full price for the deep-tail
warning the ensemble already provides; doing nothing leaves the no-warning branch — the one
branch our models admit they'd miss — completely open; the pure gate-ladder is free until it
isn't (IV reprices violently ON the gate event; buying protection after CRWV defaults means
paying crisis vol).

## Step 5 — The first-principles recommendation: a two-layer hedge matched to the information structure
**Layer 1 — standing tail spread (the no-warning insurance):** Dec-2027 XND put spreads, long
~10% OTM / short ~30% OTM, **15–25 spreads (~$450–750k notional ≈ 10–17% of overlap)**,
~**$10–18k/yr**. Sized to the branch where our models give no warning — small, because that
branch is the residual after the sequence edge, not the whole 0.45. No call leg, ever (Step 3).
**Layer 2 — pre-registered gate-keyed escalation (the warned-branch insurance, bought only when
warned):** on ANY of — Gate A fires (OpenAI prices <$852B or slips past Q1-27) · a CRWV credit
event · the Nash flip · a quarterly re-freeze ≥0.55 — **escalate within 5 sessions to ~50% of
overlap** ($2.2M notional) in plain puts, accepting the then-higher IV as the known price of
certainty. Pre-registration is the point: the decision is made now, calmly; only the execution
waits for evidence. **Wind-down:** re-freeze <0.35 for two consecutive quarters → Layer 1
non-renews; Layer 2 never triggers.
**Layer 0 (already owned, no action):** harvest convexity + reserve anti-correlation carry the
deep grind; the doubling-up calendar (Nov 28) is part of the hedge and is already scheduled.

**Deployment floor retained from first principles** (not from the old runbook): no hedge
notional before the capital it protects has landed — protection follows capital AND evidence,
never calendar alone.

## What this changes vs the prior ratification
The 8/21 collar is **withdrawn as default**: its call leg fails the net-buyer test and its full
standing size pays for warning the ensemble already supplies. The conditioned-insurance doctrine
amends from *"phase with deployment %"* to **"phase with deployment AND information"** — the
phase-in variable becomes gate state and re-freeze level, not calendar fraction. This is a
doctrine amendment and requires principal ratification.

**Expected-cost comparison (rough):** old collar ~$33–66k over 16mo regardless of path. Two-layer:
~$13–24k if no gate ever fires (55% of paths at the frozen p); if a gate fires, ~$13–24k + the
escalation's crisis-IV premium (~$60–120k) — but paid only in the ~45% of paths where the
protection is about to be worth multiples of it. Lower cost in the modal path, larger protection
in the loss path, full upside always. That asymmetry is the recommendation.

*Numbers re-derive at landing and each re-freeze. Nothing stages until the $5M lands and this is
ratified or amended. Full context: TLH_SLEEVE_ARCHITECTURE_20260828_v2 (Parts I–II).*
