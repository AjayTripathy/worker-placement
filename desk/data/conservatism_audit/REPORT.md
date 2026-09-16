# Conservatism Audit — Run 1 (2026-08-05, spec v1.0 frozen pre-run)

## HEADLINE: NET −$204,310 over the 35-day window — conservatism did NOT pay, but not where intuition says.

**Cover caveats (printed per spec):** one regime only (SPY +3.5%, a melt-up — any below-market-ladder system grades badly in a straight-up tape); run-1 proxies in effect (14d maturity floor, close-basis penetration, current-deployment-as-average); coverage 368 records classified / 229 to review (no extractable date) / 4 price-failed / 118 immature.

| Cohort | N | $ | Reading |
|---|---|---|---|
| C1 rejects (avoided-loss) | 55 | **+$2,797** | precision 0.491 (0.455 at 30d, n=22) — rejects performed like COIN FLIPS vs SPY. The bar neither destroyed nor added net value this window. Dodged: UI −51%, CRTO −30%, WOLF −27%. Missed: OPHC +49%, TRAX +42%, CRCT +35% (each individually defensible; the grade counts them anyway). |
| C2 gated, never met (foregone) | 41 of 112 | **−$115,144** | 61% of never-met names beat SPY (activation threshold 0.65). 63% of gated names DID come to us — the cost concentrates in the 37% that ran. Top: IT −$37k (a 6/10 COURT-APPROVED name that simply never deployed), CURV, ASTS, FUTU, THC. |
| C3 under-sizing | 7 | −$1,322 | tiny — the 6s are young/unfilled; pre-v1.4 winners excluded per spec |
| C4 missed entries | 2 | −$1,658 | BKE + ADIG |
| C5 deployment drag | — | **−$88,983** | $2.915M idle × (SPY 3.46% − SGOV 0.41%). Doctrine caveat: principal rejected physical index in this book; the doctrine's own alternative was court-name deployment — C2+C5 jointly measure that gap. |

## The decomposition that matters
Selection graded NEUTRAL (C1 ≈ $0 net). **~$204k of cost sits in bands-never-met + idle capital** — the price of insisting the market come to us, in a tape that didn't. This matches the pre-audit diagnosis: the bar is calibrated; the bands and the deployment cadence are the expensive parts.

## Levers fired (pre-wired thresholds)
1. **C2 at 0.61 vs 0.65:** meet-the-price on RP_FAIR = CONDITIONAL activation — case-by-case behind confirmation courts (the TMUS pattern), full activation if the mature sample crosses 0.65.
2. **C5 largest cohort:** deployment cadence is the binding fix — RP_FAIR carry sleeve + TLH-core flow.
3. **C1:** no bar change; re-grade at N≥100 mature. Precision <0.55 trigger NOT fired as a widen-the-bar order because net $ ≈ 0 and the window is one regime — recorded as a deferral, not an override.

## Run-2 improvements owed
Wrong-side fill-cause subgrade (needs trade-fill news alignment); daily-NAV deployment series for C5; the 229 no-date records recovered; verdict+60d horizon as records season.


---

## CORRECTION + DECOMPOSITION — added 2026-08-05 PM (run-1 numbers above left as printed; corrections on the record)

**C1 date-extraction bug found and fixed.** Run-1's extractor grabbed dates mentioned in thesis text for batch-court records; TRAX/MFP/OTEX "misses" were moves that happened BEFORE their (Aug-4) courts. **Corrected C1: n=43, precision 0.488, net avoided −$9.2k** — still ≈ zero. Genuine misses: OPHC (+48.7pp) and CRCT (+35.2pp); the tail is thin (QUAD/ELF/HMR ~+14pp).

**The two genuine misses, caused:**
- **OPHC** — the court correctly killed a fake pitch (0.56× book was an artifact of ignoring an imminent deep-ITM preferred conversion; AVOID 8/10, reconciliation 9/10). The stock then won on something the court never underwrote: record Q2 (net income +85%, +$121M deposits). *Lesson: PITCH-KILL ≠ NAME-KILL — a name whose pitch dies on arithmetic goes back to the pond, not to AVOID.*
- **CRCT** — retired on tariff-driven margin collapse (33%→23%) + fwd-P/E>trailing. Aug-4: EPS beat by $0.14 on a revenue miss — profitability recovered exactly as the tariff regime turned (§122 lapse), which **our own tariff-refund lane predicted as a macro event**. *Lesson: kill-reasons that are dated/reversible macro states need reversal tripwires wired to the owning lane; the connection existed in-house and never fired.*

**C2 came-to-us decomposition (the assumption test):** of 71 gated names whose price came to us (−5%+ dip), **we fired on 3** (OLLI, PRCT, ACEL). 68 dips produced no fill — mostly because NO ORDER WAS RESTING (WATCH verdicts carried bands that never became rungs), not because bands were unreachable. 25 of the never-fired then beat SPY: **additional foregone ~$134k** ($85k excluding the JTAI +287pp outlier). Counter-signal worth keeping: came-to-us names beat SPY at only **37%** vs never-met at 61% — dips select for deteriorating names, which VALIDATES below-market entry as selection; the failure is that watches carried no resting expression when the dip arrived.

**Combined corrected picture:** selection ≈ zero either way (C1); the cost of conservatism = never-met foregone ($115k) + came-and-never-fired ($85–134k) + idle drag ($89k). The binding fixes, in order: (1) WATCH-with-band verdicts must REST their band or state why not; (2) pitch-kill vs name-kill verdict vocabulary; (3) macro-keyed kills get reversal tripwires; (4) deployment cadence. None of these lowers the bar.


## THE RESTING COUNTERFACTUAL — added 2026-08-05 PM (the falsification test for 'bands rest by default')
If orders had rested on every gated name from its court date: **-5% bands: 71 fills, 66% hit vs SPY, +$173.8k excess (+$122k ex-JTAI)** · -10%: 42 fills, 76% hit, +$148.4k (+$92k ex). The 37% came-to-us beat rate (from court date) INVERTS to 66% from the fill price — the discount out-earns the adverse selection the dip signals. Rejects sensitivity +$11k/58% (selection neutral, again). Caveat: one melt-up regime; bear-tape bleed is what the catalyst-date rule + monthly re-runs guard. DOCTRINE ADOPTED 08-05: bands rest by default + every order catalyst-dated with forced re-derive (court contract amended).


**Corrected-dates revision (same day):** cohort 112→106 after date fixes; fills 71→62. **−5% bands: +12.1% on $1.39M deployed vs SPY +3.4% = beat +8.7pp (+$121.6k; ex-JTAI +5.1pp/+$69.4k), hit 68%. −10%: beat +15.1pp (+$123.6k; ex +8.4pp), hit 80%.** Beats SPY in all eight cells (both depths × with/without outlier × both date sets). Whole-book vs 100%-SPY: ~+$60k net after idle-remainder drag. Earlier $173.8k figure included mis-dated rows — revised down on the record.


**C5 CORRECTION (principal, same day):** drag was charged on the $3.4M plan base as if it sat at IBKR. True idle = settled cash ($296k) + SGOV ($249k) − put collateral (~$60k) = **~$485k → C5 = ~$14,795**, not $89k. **Corrected NET ≈ $-130,122.** Cohort ranking changes: C2 (bands never rested) is decisively the dominant cost — the cohort already fixed. Un-arrived inbound capital is not drag; put collateral is working capital.
