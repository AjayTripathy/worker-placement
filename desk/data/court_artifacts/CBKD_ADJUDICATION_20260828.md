# CBKD — ADJUDICATION (Fable tier, 2026-08-28)
**Benches:** RED 202608280738 (ACCEPT-WITH-CUTS, 6/10) / BLUE 202608280824 (partially overturned red, 7/10). The 8/27 rubber-stamp ("KILLED — ticker/instrument mismatch on Kuwait/Egypt banking entity") was reverted; this adjudication replaces it.

## ENTITY — RESOLVED AT THE BROKER'S CONTRACT MASTER (the directive's first question)
IBKR conid **36774813, symbol CBKD, exchange LSEIOB1, description "COMMERCIAL INTL BANK-GDR REG", country GB** — the London-listed Reg S GDR of **Commercial International Bank (Egypt) S.A.E.**, exactly as the desk watchlist recorded. The RNS stream for the line is titled "Commercial International Bank Egypt SAE GDR Reg S — CBKD." **The rubber-stamp's "Kuwait mismatch" kill is REFUTED — there was never an entity problem.** (Plausible source of the confusion: Commercial Bank of Kuwait shares the "Commercial Bank" prefix; nobody checked the contract master.)

## Tape (adjudication-tier, the grant the benches lack)
GDR last close **$2.655** (8/28, CBKD.IL bar-verified); IBKR 52w stats: high $2.829 / low $1.607 / open-52w $1.683; ADV-90d **$1.75M/day** (thin but workable at desk starter size ≈ 0.15% of a day). **USD returns bar-computed at the GDR line: 1y +61.9%, 3y +158.7% price-only (~+168–175% with dividends) — the screen's "+168% 3y USD" claim VERIFIES**, resolving both benches' vendor-rail worry. GDR vs EGX local: $2.655 vs EGP 139.28/50.20 = $2.774 → **4.3% discount, normal band** (fungibility dislocation ABSENT — anti-masking positive finding sustained).

## Decisive findings ratified
1. **The edge claim is dead; the diligence is not.** Both benches agree the trapped-capital refutation is already priced (Egypt USD sovereign 8.24% YTM / 301bp T-spread, +22.7% 1y sovereign index). Under §MISPRICING-ARTIFACT-TAXONOMY there is no divergence vs the external anchor — this file's product is diligence-replication value (§VALUE-IS-DILIGENCE), and the name is a fairly-paid frontier CARRY, not an EDGE. Blue's §POLICY-CHANNEL-VS-ANCHOR caveat noted (sovereign spread ≠ bank-remittance anchor; Nigeria 2016–23 counterexample) — it softens the anchor logic without changing the conclusion.
2. **Blue's Finding (A) is the operative kill and it is NOVEL: the floored liability book.** CIB has sold 3-year floating CDs at 19.50% with a **17.50% hard floor** (blue live-fetched cibeg.com, eff. 26/07/2026; the page is JS-walled to this tier today — flagged, not papered over). Against CBE's disinflation path (July CPI 14.9% → 7%±2 target), funding cost stops falling at the floor while the 52.2%-LDR sovereign asset book reprices down freely: **NIM compresses convexly, not linearly**, and the street models forward EPS UP (fwd P/E 6.20 < trailing 7.16) — a named, mechanism-level divergence on OUR side of the bear case. Magnitude ungated by disclosure (floored-CD share of deposits unpublished) — which is exactly why the gate is a print, not a price.
3. **Red's Finding 7 is its best work and is SUSTAINED: the $2.20 alert is an adverse-selection tripwire.** The GDR reaches $2.20 (−17% from tape) essentially only in an Egypt sovereign/FX shock — the state in which the 8.24% sovereign blows out and the carry engine breaks. The entry trigger fires only in the world where the thesis is dead. **PARENT ACTION: DISARM the ledger alert_below 2.20** and replace with the print-gated fundamental tripwire below.
4. **Valuation resolved: P/B 1.99×, not 2.27×** — blue's employee-profit-share/NCI reconciliation of the share count (3.41bn) is adopted; red's "12.8% share mystery" was Egyptian statutory profit-share mechanics, not a defect. Trailing P/E ~6.8×, EPS EGP 10.23 (H1), ROAE 33.5% (RNS-verified by both benches).
5. **Hard-currency ERP band: 6–12pp over the 8.24% sovereign floor.** Red's 4–8.5pp used CIP-implied 10–15% EGP depreciation; blue's 9–14pp used realized −4.5% (my 12m bar: −3.3%). The truth is regime-dependent; the adjudicated band 6–12pp **clears the bond-dominance floor in every scenario except the devaluation state — which is the same state as the CD floor biting.** All roads lead to the NIM print.

## VERDICT: WAIT — NO ENTRY BEFORE THE 3Q26 PRINT (~2026-11-10, UNCONFIRMED, cadence-derived). Print gate:
- **NIM ≥8.3% AND CASA flat-to-falling** → minimum starter **0.25%** (RP_FAIR, labeled CARRY not EDGE, ceiling 0.5% forever — jurisdiction tail), band-entry at ≤$2.60 post-print, same-session staging per §BANDS-OVER-RESTING-GTC, never resting into the print.
- **NIM <8.0% OR CASA still rising** → FLAT, file closes (the convexity kill confirmed).
- The $2.20 price alert is DISARMED per finding 3 — price is not the instrument here; the print is.

## Kills census: 2 NOVEL (floored-CD convexity; adverse-selection tripwire) / 2 CONSENSUS (no-divergence vs anchor; re-rated tape) / 1 DATA-RESOLVED (share count). §CLEAN-COURT-MINIMUM-STARTER does not force a starter — blue's named NOVEL kill on the compounding term stands until the print reads.

## Pre-mortem (v1.7)
Top-3: (1) the CD floor bites harder than modeled and NIM steps down 100bp+ in two prints; (2) EGP devalues into the easing cycle (the CIP is priced at 19.5% forward points for a reason) and the USD leg of the 6–12pp ERP evaporates; (3) tripwire-less unknown — CBE regulatory action on bank sovereign-carry concentration (class: regulatory-recomposition of the earning-asset mix; no feed watches CBE circulars). Reflexive leg: ADV $1.75M/day means even desk-size exits pay real spread in a stress tape.
**"If this position loses money, the most likely reason will be that we bought a sovereign-carry wrapper for its franchise story just as the policy rate rode down onto a 17.5% deposit floor the bank had already sold — NIM compressed convexly, the EGP devalued into the easing, and the fortress capital never protected us because the capital and the concentration were the same asset."**

## KG rulings
- red `adverse_selection_entry_tripwire` — **ACCEPT-PRIORITY** (mechanism generalizes to every carry-dependent EM band entry; fired here on our own armed alert).
- red `sovereign_zero_risk_weight_capital_artifact` — **ACCEPT-AMENDED**: the CBE 0%-risk-weight leg is UNVERIFIED; fires_on must include verifying the national-discretion treatment before asserting the artifact.
- blue `floored_floating_liability_vs_unfloored_asset_nim_convexity` — **ACCEPT-PRIORITY, desk-gold**: the detector is checkable from any bank's public deposit shelf, and the street's forward-EPS-up consensus proves it is not carried.

## Calibration (parent to freeze)
**CBKD-Q3NIM**: "3Q26 NIM ≥8.3% with CASA flat-to-falling" — p=0.45, cat 2026-11-10-UNCONFIRMED, px 2.655. (0.45 = the floor mechanism is real but one quarter may be too early for convexity to bind; the informative outcome is the MISS.)

## Unverified ledger (parent to file)
Floored-CD share of total deposits (the single datum that sizes the kill); sovereign securities as % of earning assets (undisclosed in RNS); CBE Basel risk-weight treatment of EGP sovereign paper; CIB CD page re-verification (JS-walled this session); Egypt local 10y 22.87% claim; GDR depositary fee vs the 4.19% gross yield.
