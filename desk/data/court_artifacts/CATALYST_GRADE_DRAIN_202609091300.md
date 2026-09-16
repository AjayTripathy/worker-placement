## CATALYST-GRADE BACKLOG DRAIN — 2026-09-09 (76 of 84 graded; brief dead 07-22..09-08 hid them)

**Aggregate:** all-in Brier 0.2430 (n=76) is FLATTERED by 9 MIXED calls at p~0.5 (avg 0.010). DECISIVE-ONLY
(n=67): **0.2743** — worse than a coin (0.25) and worse than this cohort's climatology (base rate 0.567 -> 0.2455);
we LOSE to climatology by 0.029. Decisive hit rate 57%: ops_data 48% (n=30), stock-reaction 58% (n=12), other 56%.
Book-wide: n_resolved 168, Brier 0.2225 vs coin 0.2318 vs MARKET 0.2098 — the market gate reads NOT EARNED
(16 genuine anchors of 20 required). edge_pp must not size positions. Adding the 4 determined-but-unwritable
grades (IVN x2 UNFAV, G x2 FAV) moves decisive to ~0.278.

**Stock-reaction legs (mechanical 5TD):** LDOS +18.7 FAV · BBD -9.5 UNFAV · GILT +4.2 FAV · HUBS -16.0 UNFAV ·
III +29.7 FAV · CRH -2.8 UNFAV · G -5.0 UNFAV · UPBD -10.1 UNFAV · 8750.T -4.4 UNFAV · ONON -20.0 UNFAV ·
COSMECCA +81.4 FAV · IT +40.0 FAV.

**Six headless-grader errors that changed a verdict (verification pass):** BBD-STK graded on BOMBARDIER (wrong
entity; actual -9.5%); four rows carry the bar only in `claim` which grade_brief never read -> graded against
nothing (SPCX-SUBS 12.0M vs frozen >=12.8M: 0.05 -> 0.608) [FIXED in grade_brief]; INTU guide compared to
consensus across a non-GAAP redefinition ($5.81/sh SBC moved inside); TM graded MIXED for want of DSR that was in
an SEC-filed exhibit (-0.8%); UBER failed on Waymo events predating the freeze and named in its own reasoning;
BOOK-SHARPE re-quoted the freeze-time parenthetical as the resolution (recomputed: window Sharpe 4.60, ROSE from
4.12 — a dozen binary gates absorbed without vol expansion; the '11.6' anchor is not reproducible).

**Honesty-alpha (takeaway-vs-data divergence, nothing concealed):** CLINUVEL "revenue -1%" masks H1 +3.6 / H2 -3.8
(gate written on H2 for this reason); Hyundai Investor Day discloses 1H26 OPM 5.6% below the 6.3-7.3% FY floor it
presents as intact, leading with a RAISED 2030 target; Ollie's beat = tariff refund (ex-refund GM 39.7 vs 39.9,
EPS ~1.07 < cons) — the paired comp gate failed = two-call doctrine working.

**Mechanism refuted (book P&L, strip the causal story):** ADIG — S&P ADDED it to SmallCap 600 (REZI never MidCap
400) -> index funds were forced BUYERS; the air-pocket was spin-off stub supply. KG: do not credit the
forced-seller story.

**Ledger-integrity defects (build tickets):**
1. Re-ingest race: catalyst_predictions.json = one mutable record per ticker; date-estimate moves write NEW keys,
   concurrent _write() re-appended the same key daily (GAP x8, LULU x6, INTU x4, BBD x3, GTM x2) and OVERWRITES
   `made` (FOUR/GTM look like lookahead; real freezes 06-29/07-02 per antibook). resolve() correctly refuses dupes.
2. Two-events-one-key: IVN 07-30 and G 08-06 each carry two gates; four determined grades unwritable
   (IVN p0.80 guide-held UNFAV 0.64; IVN p0.40 ramp UNFAV 0.16; G p0.65 FY-guide FAV 0.1225; G p0.62 CBS/ATS FAV
   0.1444). Key must be ticker|date|gate_id.
3. Action registry keys on TICKER: FAF's July BASE_OR_BETTER grade fired the OCTOBER personnel-ratio branch
   (COURT_CONFIRM_THEN_STARTER). NOT acted on. Key must be the call id.
4. Eleven cat_dates wrong (FAF -16d, ELV -23d, XOM -7d, FUTU -7d, MRVI -4d, GCT-earn -4d, PFSI -2d, IT -24d,
   BBW/OLLI/ONON -1d) — corrupts any event-window/latency study until corrected.

**Actions due (principal):** UBER FAVORABLE -> band $62-68 starter; spot 71.28 ABOVE band = no chase (nothing to
do). 6804.T MIXED -> strict-AND read is UNFAVORABLE (amusement -22.6% vs -5.9% path) = STAND_DOWN_OR_PULL branch
for the ¥2650 rung — NO resting 6804 order exists in the 9/8 order cache; confirm none was re-booked. FNF-ADOPTERNULL
UNFAV -> re-open the FNF adopter question at the FAF Oct court (10-21). XOM FAV -> REVIEW (no branches). FAF: DO NOT
act (arming defect above). Not yet gradeable: OLLI-STK window closes 09-10 (+6.3% now); COO x2, WLTH-Q2REV prints
not yet on EDGAR — re-check tonight.

Pre-drain backup: /tmp/calibration_ledger.BACKUP_20260909_121825.jsonl