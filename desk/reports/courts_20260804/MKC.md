# MKC — McCormick & Company | COURT 3/10 REJECT-AS-FRAMED
**Court date** 2026-08-03 (grades 08-04) · **Queue** TIER_2_flagged, score 41.2, flags [GUIDE-DECEL]
· **Screen why**: "-37% from own 3y high, gm 39%, rev3y 2.5%"

**Live basis (IBKR, 2026-08-03 close):** MKC (non-voting) **$51.52** · MKC V (voting) **$52.85**
(zero volume today, no two-sided quote). 90d ADV: MKC $220.6M/day, MKC V effectively nil.
Div yield 3.67%. IV 34.5% annual.

---

## RULING IN ONE LINE
Not a de-rate and not a derailment — **the wrong instrument**. MKC agreed on 2026-03-31 to combine
with Unilever's Foods business in a ~$42.7–45bn transaction creating a ~$65bn food company in which
**Unilever's shareholders end up with the majority stake**. Every per-share input the screen ranked
on is a pre-deal stub that does not survive close. Separately, the screen's headline cheapness is a
**non-cash accounting artifact I was able to isolate to the dollar.**

---

## FINDING 1 (DECISIVE) — the trailing P/E is 57% fake, confirmed from audited XBRL

| step | value | source |
|---|---|---|
| Screen/vendor trailing EPS | $6.01 → "trailing P/E 8.6x" | yfinance |
| Q1 FY26 (Dec-25→Feb-26) operating income | $228M | SEC XBRL `OperatingIncomeLoss` |
| Q1 FY26 net income | **$1,016M** | SEC XBRL `NetIncomeLoss` |
| Q1 FY26 GAAP diluted EPS | **$3.77** | SEC XBRL `EarningsPerShareDiluted` |
| H1 FY26 equity-method income | **$889.5M** | SEC XBRL `IncomeLossFromEquityMethodInvestments` |
| Q2 FY26 equity-method income (alone) | $3.5M | same |
| FY25 FULL-YEAR equity-method income | $72.2M | same |

Net income printed **4.5× operating income** in a single quarter. Backing Q2 out of H1 puts
**~$886M of equity-method income into Q1 FY26 alone, against a ~$18M/quarter run-rate** — a one-off
non-cash gain (remeasurement/step-acquisition on a previously held JV stake; the specific instrument
is the one item I could not name from XBRL alone — see gaps).

Reconciliation: FY25 GAAP EPS $2.93; H1 FY26 GAAP EPS $4.33; Q2 FY26 alone $0.56. TTM $6.01 ties
exactly, and **~$3.40 of it (57%) is that single gain.**

**Corrected multiples at $51.52:** clean trailing GAAP EPS ≈ $2.61 → **~19.7x trailing** (not 8.6x).
FY26 consensus $3.09 → **16.7x**. FY27 $3.30 → 15.6x. A staple at 16.7x with 3.67% yield is
ordinary, not distressed-cheap. **The screen ranked MKC on a number a JV remeasurement created.**

## FINDING 2 (DECISIVE) — the pending Unilever Foods combination voids the frame

- 2026-03-31: Unilever and McCormick agreed to combine Unilever Foods (Hellmann's, Knorr et al.)
  with McCormick — reported ~$42.7–45bn, creating a ~$65bn food group.
  *(Unilever Global press release; Reuters; NYT; WSJ; Barron's — 2026-03-31/04-08, via news channel.)*
- Reported structure has **Unilever shareholders holding the majority** of the combined company
  (Reuters/The Journal Record, 2026-03-27/31) — i.e. a Reverse-Morris-Trust-shaped deal with very
  large share issuance.
- Market reaction was hostile on both sides ("Why Investors on Both Sides Hate the Deal", Barron's
  2026-03-31); MKC is -27.9% over 12m and -41.9% off its Aug-2023 high.
- Deal is "taking shape" as of 2026-07-23 (Food Business News) — **not yet closed.**

Consequence: the 12–13 analyst FY26/FY27 EPS estimates the screen leaned on are **standalone
McCormick**, not pro-forma. Market cap $13.85bn, EV $19.0bn, P/B 1.98, forward P/E — all pre-deal.
Underwriting this name requires a pro-forma model of a $65bn combined entity (synergy schedule,
issued share count, pro-forma leverage, Unilever-Foods organic trajectory, and the Hellmann's/Knorr
margin structure vs McCormick's 39% gross margin). **That work does not exist and this court is not
the venue for it.**

## FINDING 3 — the GUIDE-DECEL gate misfired (gate test)

Screen flagged GUIDE-DECEL = "forward revenue growth <60% of trailing." Actual consensus:
FY26 revenue **+15.4%** ($6.84bn → $7.89bn), FY27 **+3.6%**. Trailing rev3y was 2.5%.
So forward growth is *above* trailing; the flag fired on the **FY27-vs-FY26 step-down, which is the
acquisition anniversary rolling off**, not a demand signal. Any M&A-inflated revenue year will
trip this gate. **Recommend the gate exclude names with a revenue-year discontinuity >10pp
attributable to a disclosed acquisition.**

## PATH CHECK
- 52w low $44.83 (13w/26w/52w low all the same print), **79 days ago**; spot $51.52 = **+14.9% off
  the low** — by far the *least*-bounced name in this cohort (cohort range +15% to +140%).
- -41.9% off the 3y closing high ($87.62, 2023-08-07). 52w high $71.77.
- r1m -3.8%, r3m +0.1%, r6m -17.0%, r12m -27.9%. Still grinding, no bounce to fade.

Path is the *one* attribute here that argues for the name. It is not enough against Findings 1–2.

## ESTIMATE TRAJECTORY
Near-quarter (Q3 FY26, reports **2026-10-06** — verified from the company calendar) cut from $0.839
→ $0.757 in the last 7 days, **10 down / 0 up revisions**. FY26 held at $3.09 (analysts shifted
earnings between quarters rather than cutting the year); FY27 $3.347 → $3.299 over 90d (-1.4%).
Read: **flat-to-slightly-down, not collapsing.** The business is intact; the equity story isn't the
business.

## SHARE CLASS — the answer the principal asked for
**Take MKC (non-voting, NYSE, conid 271556). Do not take MKC V.**
- MKC V closed **$52.85 vs MKC $51.52** — the voting class carries a **+2.58% premium**, i.e. it is
  the *more expensive* one, not the cheaper one.
- MKC V traded **0 shares today** and returned **no bid/ask** from IBKR; MKC does ~$220M/day.
  (yfinance last-printed MKC V at $50.95 vs IBKR $52.85 — a 3.7% stale-print gap that is itself
  evidence of the illiquidity.)
- Economic rights are identical; the voting stock is largely family/insider-held. You would pay a
  premium for votes you will never use and accept an exit you cannot execute — including through a
  merger vote where an odd-lot voting stub is the worst thing to hold.

## SCENARIOS (standalone, pre-deal — explicitly incomplete)
| | p | FV | logic |
|---|---|---|---|
| bear | 0.35 | $40 | deal closes dilutively / integration of a $42.7bn low-growth foods book drags ROIC; 13x $3.10 |
| base | 0.45 | $54 | deal closes, synergies roughly offset dilution; 17x $3.20 |
| bull | 0.20 | $70 | Hellmann's/Knorr margin lift is real, 21x $3.35 |

e_FV ≈ **$52.3** vs $51.52 → **edge ≈ +1.5pp.** Zero. And the scenario set is built on standalone
estimates that the deal invalidates, so even that +1.5pp is not trustworthy.

## FOUR-IDEA FRAME
1. **The trade that exists**: a pro-forma merger-arb / post-close re-rate on the combined entity.
   Requires modelling work we have not done. Route to a special-situations pass, not here.
2. **The trade the screen thought existed**: cheap de-rated staple at 8.6x. Does not exist — the
   8.6x is a JV remeasurement.
3. **The trade that would exist later**: post-close, if the combined company guides to a credible
   synergy number and the pro-forma share count is fixed, MKC becomes a genuinely courtable
   quality-at-a-discount name. Re-open then.
4. **The anti-trade**: buying the voting stub for a "control premium." Actively negative.

## KILLS / GATES
- REJECT at spot. No position.
- Re-open only on: (a) deal close with pro-forma share count and FY27 pro-forma guide published, or
  (b) deal termination + price below $46 (below the May-13 low).

## VERIFICATION NOTES
| claim | source | result |
|---|---|---|
| trailing EPS $6.01 is 57% one-time | SEC XBRL companyconcept, CIK 0000063754 | **CONFIRMED** |
| Q1 FY26 equity-method income ~$886M vs $18M/q run-rate | SEC XBRL `IncomeLossFromEquityMethodInvestments` | **CONFIRMED** |
| Unilever Foods combination pending, Unilever holders majority | Unilever Global PR + Reuters + NYT, 2026-03-31 | **CONFIRMED** (headline); majority-stake structure PLAUSIBLE (secondary reporting, not read in the S-4) |
| MKC V trades at a premium and is illiquid | IBKR snapshot conid 48789220 | **CONFIRMED** |
| next print 2026-10-06 | company calendar | **CONFIRMED** |
| GUIDE-DECEL is an M&A-anniversary artifact | consensus revenue series | **CONFIRMED** |

### GAPS (UNVERIFIABLE ≠ clean)
1. **The exact identity of the ~$886M Q1 FY26 gain.** XBRL places it in equity-method income; I did
   not open the 10-Q footnote to name the JV or confirm it is a step-acquisition remeasurement. The
   *magnitude and non-recurrence* are confirmed; the *label* is not. **Top unverifiable.**
2. Deal structure (exchange ratio, pro-forma share count, majority-stake mechanics) not read from
   the S-4/proxy — taken from press reporting only.
3. No organic-growth decomposition (acquisition vs base) from the segment footnote.
