# CRTO — Criteo S.A. | COURT 3/10 REJECT-AS-FRAMED → RE-ROUTE
**Court date** 2026-08-03 (grades 08-04) · **Queue** TIER_2_flagged, score 29.5, flags [EXHAUSTED]
· **Screen why**: "-56% from own 3y high, gm 54%, rev3y -1.2%"

**Live basis (IBKR, 2026-08-03 close): $21.37.** IV 49.0%. 90d ADV $20.6M. 52w range $15.575–$25.29
(both struck inside the last 13 weeks).

---

## RULING IN ONE LINE
**There is a live event here and the screen did not know about it.** The entire "+38% off the low"
that triggered the EXHAUSTED flag is a **takeover leak**: on 2026-07-06 Reuters/Bloomberg reported
that **Vista Equity Partners and Quinti Capital had made a >50%-premium buyout approach** for
Criteo. The stock gapped +21% that day and has bled steadily lower every week since. This is a
merger-arb / deep-value situation in a quality-drawdown queue — **wrong vertical, and it prints in
two days.** Reject here; re-route to deep_value/special-sits.

---

## FINDING 1 (DECISIVE) — the bounce is a deal leak, and the tape says the deal is decaying

Tape-verified from daily bars (basis: yfinance split/div-unadjusted daily closes; spot from IBKR):

| date | close | note |
|---|---|---|
| 2026-07-02 | $19.08 | last clean pre-leak close |
| **2026-07-06** | **$23.17** | **+21.4%, intraday high $25.29, volume 2.68M vs ~300k normal (9×)** |
| 2026-07-13 | $23.28 | peak of the post-leak plateau |
| 2026-07-24 | $20.44 | |
| 2026-07-31 | $21.82 | |
| **2026-08-03** | **$21.37** | **-7.8% below the announcement-day close; the $25.29 high never revisited** |

**Implied deal probability.** "More than 50% premium to its recent share price" (Reuters/PPC Land) on
a ~$18–19 pre-leak reference implies an offer around **$28**. Taking no-deal downside at the
pre-leak $19.08 (arguably lower now, given a -9.8% y/y revenue guide for the quarter):

- p(deal) ≈ (21.37 − 19.08) / (28 − 19.08) = **26%**
- using $18.50 downside: **30%**
- on the 07-06 close of $23.17 the same math gave **~46%**

**The market has repriced the deal from ~46% to ~28% over four weeks.** No board response, no
confirmation of terms, no exclusivity, no all-cash confirmation, no advisor appointments disclosed.
Criteo "has not yet made a decision on how it intends to respond." That monotonic bleed with no
confirming disclosure is the classic *approach-not-progressing* signature, not a deal maturing.

## FINDING 2 — the screen's path feature has no event overlay (gate defect)

The EXHAUSTED flag fires on "% off low." CRTO's +38% off its low is **100% attributable to a single
M&A headline**, not to a recovering business. The same defect would score any rumour pop, any
activist 13D, any FDA approval as "the bounce already ran."

This is the **second name in this seven-name cohort** whose ranking was corrupted by an unmodelled
corporate event (see MKC, where a pending $42.7bn Unilever Foods combination and an $886M JV
remeasurement gain drive the score). **Recommended gate: a pending-M&A / rumoured-M&A overlay that
either excludes the name or routes it to the special-sits vertical before the path features are
computed.** Two of seven is not noise.

## FINDING 3 — the underlying business, on its own, is declining

| | value |
|---|---|
| FY26 revenue consensus | $1.140bn, **-2.9% y/y** |
| FY27 revenue consensus | $1.196bn, +4.9% |
| Near-quarter revenue | $263.4M, **-9.8% y/y** |
| trailing rev3y | **-1.2%** |
| Gross margin | 54.0% |
| GAAP operating margin | 3.8% |
| Cap / EV | $1.074bn / **$0.929bn** (net cash ~$204M: $348M cash vs $144M debt) |
| FCF (ttm) | $180M → **16.8% FCF yield on cap, 19.4% on EV** |
| P/B | 0.945 |
| **Analyst coverage** | **2** |

The bear premise in the queue note ("negative rev3y — the derailment prior is strong") is
**CONFIRMED**: revenue is shrinking, and the retail-media pivot is not yet outrunning the decay of
the legacy retargeting book ("retail media weakness, soft outlook", 2026-05-06 Q1 print).

**SBC/non-GAAP honesty check:** forward P/E screens at 4.16× on a **$5.13 non-GAAP** FY27 EPS while
trailing **GAAP** EPS is $2.13 and GAAP net margin is 6.0%. The 4× headline is a non-GAAP artifact
amplified by an aggressive buyback shrinking the share count (50.2M shares). On GAAP the multiple is
~10×. Cheap, but for a declining asset — a deep-value question, not a quality-at-own-history-discount
question, and the tier-2 frame explicitly forbids the former.

**Coverage collapse to 2 analysts** is itself informative: the sell side has abandoned the name, and
the vendor "estimate trend" series shows 0.00 for every prior period — meaning the estimate-trajectory
feature the de-rate/derailment test relies on **has no signal at all here.** The screen scored a
trajectory it could not observe.

## PATH / TIMING
- 52w low $15.575, **86 days ago**; spot = **+37.2% off the low**, but see Finding 1 for what that is.
- **Prints Q2 on 2026-08-05 — two days out.** The contract's no-blind-entry-inside-~2-weeks rule
  fires. Independently disqualifying.

## STRUCTURAL NOTES (checked because they change the instrument)
- IBKR lists the line as **"CRITEO SA-SPON"** (conid 906052343) with a separate legacy
  **"CRITEO SA-SPON ADR" (CRTO.OLD)** — the security appears to have converted from an ADR to a
  direct-listed ordinary. A French-domiciled issuer means **French FTT (0.3%) may apply on purchases**
  and any takeover runs through **AMF tender rules**, not a US merger vote. Both change the arb
  mechanics materially. Flagged, not resolved.

## SCENARIOS (event-weighted)
| | p | FV | logic |
|---|---|---|---|
| bear — approach lapses, revenue decline continues | 0.45 | $16 | standalone re-rates back toward the low; 8× GAAP on falling revenue |
| base — approach lapses, business stabilises, buyback works | 0.27 | $21 | ~16% FCF yield holds the price |
| bull — deal is signed at ~$28 | **0.28** | $28 | our p(deal), consistent with the tape's ~26–30% |

**e_FV ≈ $20.7** vs $21.37 → **edge ≈ -3pp.** Essentially fair. The market is pricing this event
correctly, which is the honest finding: **no edge, and the small remaining spread is compensation
for a real break risk we cannot handicap better than the tape can.**

## FOUR-IDEA FRAME
1. **Long as a quality drawdown**: the premise does not exist. Reject.
2. **Long as merger arb**: ~28% probability × $6.63 upside vs ~$3–5 downside. Roughly break-even at
   this price and requires deal-desk work (financing, AMF process, French antitrust, board posture)
   that this court has not done and is not scoped to do. **Route to special-sits.**
3. **Long as deep value**: 16.8% FCF yield, net cash, 0.94× book, buying back stock. Genuinely
   interesting *in the deep_value vertical with its own trap-filter* — and the trap-filter exists
   precisely for melting-ice adtech. **Route there, not here.**
4. **Do nothing until 08-05**: correct near-term answer regardless of which of the above wins.

## KILLS / GATES
- REJECT in this queue. No position.
- Re-route: **deep_value + special-sits**, after the 2026-08-05 print.
- Event tripwires: a confirmed binding offer with a stated price (re-underwrite as arb); an 8-K/AMF
  filing that the approach has been rejected or withdrawn (re-underwrite standalone at ~$16–18).

## VERIFICATION NOTES
| claim | source | result |
|---|---|---|
| Vista Equity + Quinti Capital made a >50%-premium approach, reported 2026-07-06 | Reuters, Bloomberg, PPC Land, Digiday | **CONFIRMED** (that an approach was *reported*) |
| terms undisclosed; not confirmed all-cash; board has not responded; no exclusivity disclosed | PPC Land 2026-07-07 (fetched) | **CONFIRMED** |
| +21.4% on 07-06 to $23.17 on 9× volume; steady bleed to $21.37 | own daily bars + IBKR spot | **CONFIRMED** |
| FY26 revenue -2.9%, near-quarter -9.8%, rev3y -1.2% | yfinance revenue_estimate + screen | **CONFIRMED** |
| net cash ~$204M, FCF $180M, P/B 0.945, 2 analysts | yfinance info | **PLAUSIBLE** — vendor data, **not** verified to the 20-F/6-K |
| prints 2026-08-05 | company calendar | **CONFIRMED** |

### GAPS
1. **The actual offer price is unknown.** "More than 50% premium to a recent share price" is a
   sourced-not-stated number; my $28 anchor is derived, and every probability above scales with it.
   **Top unverifiable — and it is the single input the whole event case rests on.**
2. **Balance sheet is vendor-sourced, not filing-verified.** The contract requires cap structure
   before any net-cash claim; I did not open the 20-F/6-K. The $204M net-cash and 16.8% FCF-yield
   figures are therefore **PLAUSIBLE, not CONFIRMED** — do not carry them into a deep_value court
   without re-deriving them.
3. ADR→ordinary conversion, French FTT applicability, and AMF tender mechanics are flagged from the
   IBKR contract listing only; unresolved.
