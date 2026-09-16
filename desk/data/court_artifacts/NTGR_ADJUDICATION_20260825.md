# ADJUDICATION — NTGR (NETGEAR) — 2026-08-25

**Bench record:** RED 2026-08-25 05:50 (ACCEPT-WITH-CUTS, kill conviction 6/10, court-worthiness cut 7→4) · BLUE 2026-08-25 06:32 (PARTIALLY OVERTURNED, net 6/10, court-worthiness 5). Both benches pulled the same primaries independently (10-Q R4/R2, 8-K Ex-99.1, FCC DA-26-286A1) and **agree on every number** — the dispute is entirely interpretive.

## PRIMARY RE-VERIFICATION (§TIER-STRUCTURE)

| Load-bearing number | Bench value | Adjudicator check | Result |
|---|---|---|---|
| Conditional-approval sunset + peer set | NTGR 2027-10-01; Adtran same date; Amazon Leo/eero 2027-10-31; renewal condition = "time-sensitive plan to establish or expand US-based manufacturing" | Re-fetched DLA Piper May-2026 summary | **CONFIRMED — blue's peer-set overturn stands: standard regime term, not an NTGR-specific cliff; the renewal mechanism is written into the grant** |
| Cap / EV | 27,179,021 sh × $20.60 = $560M; EV $292M ex-leases (0.44× EV/S); BVPS $16.79 | Recomputed | VERIFIED |
| H1 operating decomposition | GP +$11.784M vs opex +$11.478M → op loss improved $0.306M; net-loss deterioration $7.831M is 113% explained by other income −$8.865M | Recomputed from the two benches' independent R4 pulls (cross-consistent) | VERIFIED — **blue's "treasury base effect graded as an operating verdict" correction is arithmetically right** |
| Q3 guide | $165–175M vs Q3'25 $184.6M → −7.9% mid; GAAP op margin (12)–(9)% | Cross-consistent 8-K pulls | ACCEPTED |
| Cash decline | $323.0→$267.9M; buybacks $33.0M + OCF −$8.5M = 75% of decline; zero borrowings | Recomputed | VERIFIED |

## RULINGS

1. **Red #1 (mix defense refuted / "completed experiment") — BLUE'S REDUCTION SUSTAINED, with a caveat.** The operating line is *flat*, not deteriorating; the net-loss headline is a below-the-line base effect. But blue's "discretionary reinvestment" framing is charitable — R&D +12.4% and S&M +10.0% against declining revenue with zero operating leverage is a *choice with no demonstrated return yet*. Ruling: the mix defense is neither refuted nor proven; it is **untested at the operating line**, and the refuting metric becomes blue's (opex ex-restructuring QoQ + other-income run-rate), not red's inert one.
2. **Red #2 (Oct-2027 "cliff") — BLUE'S OVERTURN SUSTAINED** (peer set re-verified above). Correct read: a real but diluted share window (TP-Link and Google Nest outside the approval; eero inside it), plus a dated renewal condition. Red's kg_candidate `conditional_approval_expiry_cliff` is **NOT endorsed as written** — it encodes the inverted read; re-draft against the peer set before harvest.
3. **Red #3 (10-Q silent on the Covered List) — SUSTAINED by both, and it is the record's best NOVEL finding.** A dated federal permission governing US saleability of ~47% of revenue appears nowhere in the vetted venue, in either direction. DATA severity; feeds the watch, not a kill.
4. **Red #6 (ARR is Consumer, not Enterprise) — SUSTAINED as a brief correction, declassified as a market kill** (blue is right: it corrects the desk, not the street; and rounding ≠ venue divergence).
5. **Blue's new findings — ALL SUSTAINED:** buyback retiring 6.5%/yr of diluted count with $75M (13.4% of cap) authorized; **segment merge masks the Mobile/service-provider runoff** (kg_candidate `segment_merge_masks_runoff` ENDORSED for harvest — both benches had used the merged line as homogeneous); other income is a stepping-down forward headwind.
6. **§CLEAN-COURT check:** is there a named kill barring entry? No FATAL exists — no leverage, no covenant, bounded downside, 48% of cap in net cash. What bars entry *now* is TIMING: a confirmed −8% revenue guide into an unconfirmed ~10/28 print, with the merged segment line making the decisive question (is Consumer-ex-Mobile declining faster or slower?) **unanswerable until the print**. This is a WAIT with a dated resolver, not a FLAT-without-a-kill.

## VERDICT: **WAIT — RP_FAIR-pending; minimum starter gated to the Q3 print.**

- **Size:** 0 now. Post-print: **0.4% minimum starter** (~$4.2K, ~200 sh).
- **Gate (all four legs required):** (a) Q3 print read first — no resting pre-print order (§resting-order-into-print); (b) price **≤$22** at entry (≈0.5× EV/S — a post-print pop above that is a chase, §value-ladder); (c) live tape/ADV/short-interest poll immediately before staging (both benches were permission-denied — liquidity is UNMEASURED and this gate is unwaivable); (d) the print must not show Consumer decline accelerating past ~−12% YoY or a Q4 guide worse than −8%.
- **Kills recorded:** NOVEL 2 (undisclosed Covered-List sunset; segment-merge masking) / CONSENSUS 3 (deceleration, GAAP guide wedge, cash decline). None rejection-grade.
- **Kill-variable watches:** 2027-10-01 approval renewal — a US-manufacturing-plan 8-K is the renewal mechanism firing (and makes `sentinel2_buildout` checkable: demand a named site); Q4 guide; the FY26 10-K segment disclosure (first chance to see inside the merged Consumer line); any acquisition announced from the cash pile.
- **Court-worthiness: 5/10** (blue's number; red's 4 undercounts the two NOVEL findings).

## WHAT COULD GO WRONG (v1.7 pre-mortem, for the post-print starter)

1. **Melting ice cube outruns the buyback.** Consumer hardware (ex-ARR) is decaying faster than the merged line shows; the buyback shrinks the count 6.5%/yr but the business shrinks 8%+. The segment merge means we cannot see which — truth arrives only at the FY26 10-K. *(This is also the named tripwire-less unknown — no feed separates Home Networking from Mobile inside "Consumer." Unknown-unknown class: disclosure-regime change.)*
2. **The 2027-10-01 renewal is discretionary.** DoW/DHS renewal politics have no docket feed; a non-renewal headline would hit ~47% of revenue with zero warning. Mitigant: every peer carries the same term, and a mass non-renewal of US-brand routers is politically implausible — but "implausible" is not a tripwire.
3. **Reflexive/structural leg:** 48% of cap in cash invites a value-destroying acquisition (Exium precedent) — the floor we are buying can be spent by management without shareholder consent.

**"If this position loses money, the most likely reason will be ___":** *"the Consumer hardware runoff proves structural rather than Mobile-mechanical, the buyback slows as cash approaches working-capital minimums, and the stock sits at 0.4× EV/S for years because nothing forces value realization — a value trap, not a blow-up."*

**Queue action for parent session:** mark ADJUDICATE → DONE. Pack to arm (parent): NTGR-Q3PRINT | ~2026-10-28 (UNCONFIRMED — verify scheduling release first) | gates (b)–(d) above.
