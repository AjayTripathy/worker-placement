# OSB / Prediction-Market-Exposed Cohort — Refutability Triage
**Cohort:** `osb_prediction_market_exposed` · **Members triaged:** SRAD, DKNG (FLUT excluded — separate full court)
**Date:** 2026-08-07 · **Tier:** Opus volume triage · **Analyst:** SignalOS

---

## 0. Bottom line

| Ticker | Last | 52w high | Drawdown | Class | Court |
|---|---|---|---|---|---|
| SRAD | $12.70 (close 2026-08-06) | $32.22 | −60.6% | **DAMAGE-ABSENT** | **8/10** |
| DKNG | $21.84 (2026-08-07 pre-mkt) | $48.78 | −55.2% | **DAMAGE-ARRIVING** | **5/10** |

> **Score revision (2026-08-07):** DKNG was scored 6/10 on a first pass that treated CFTC preemption as
> effectively settled in Kalshi's favour. That premise is wrong — see §4.1. Preemption is live and
> majority-against at district level, the CFTC's own proposed rule would ban the high-margin prop/micro
> contracts, and both FanDuel and DraftKings abandoned Nevada licensing applications. The decisive
> variables are legal and unresolved on multiple undecided circuit appeals, so an adversarial court
> convened today cannot reach a defensible verdict. **DKNG drops to 5/10 and does NOT auto-escalate**;
> re-triage after the Q2 print and the NPRM final rule. Conceding this on the coordinator's correction.

Prices: IBKR live snapshot, conid 513610886 / 560105364, pulled 2026-08-07. SRAD last print `is_close=true`
(no trades yet on 08-07); DKNG last $21.84, −1.49% vs prior close $22.17.

**The damage is REAL but MIS-ATTRIBUTED.** US OSB handle has been negative for six straight months and
inflected in Dec-2025, *before* the Feb-2026 price breaks — so the market detected genuine deterioration
and was early, not late (§3.7). What it got wrong is the cause: the contraction is concentrated 3–5x in
states that raised taxes (PA −12.9%, NJ −9.8%) versus states that did not (MI/TN +3%), which is a
state-tax-and-margin-defence signature, not uniform prediction-market substitution. Cause determines
duration — extraction is partly reversible, disintermediation is not.

Neither name's largest single down-day was a substitution event: **SRAD's was a short-seller report on
compliance (2026-04-22, −22.6%); DKNG's was its own elective reinvestment guidance (2026-02-13, −13.5%).**
And SRAD, a feed vendor, is measurably decoupled from the channel doing the damage — **US revenue +9.9%
against handle −3.9%.**

---

## 1. Mode B first — the decisive questions, derived without the cohort's framing

Stripping the "prediction markets kill sportsbooks" premise, the questions that actually decide these two:

1. **Is betting VOLUME falling, and if so WHY?** Substitution destroys volume permanently; tax-driven
   margin defence suppresses volume while *raising* revenue. Opposite durations, opposite terminal values.
   **Volume IS falling — US handle is negative six straight months (−3.9%)** — but the decline is
   concentrated 3–5x in states that raised taxes (§3.7), which is a tax signature, not a substitution
   signature. Revenue must never be used as the volume proxy here: hold ran abnormally high (MI 16.4%), so
   GGR grew while handle shrank.
2. **Does the "victim" sell to the "predator"?** For a B2B data vendor this is dispositive and nobody
   in the cohort framing asked it. SRAD answered it on 2026-08-03: Kalshi and Polymarket are now
   **named customers under multi-year contracts.**
3. **What did the market pay UP for?** Both names rallied hard on days that *expanded* prediction
   markets federally. A market that believed in substitution cannot rally 45% off the low on a CFTC
   rule proposal that legalizes more event contracts. Revealed pricing contradicts the stated narrative.
4. **Which of the drawdown is idiosyncratic vs cohort?** SRAD's worst day (−22.6%) coincided with DKNG
   −2.3%. That is not a sector event. It was mis-filed into the cohort.

---

## 2. SRAD — dated driver decomposition

Sportradar Group AG is a **B2B sports data / odds-feed vendor** (revenue from books, leagues, media),
not a book operator. It takes no betting risk and holds no player funds.

### 2.1 The tape, decomposed (IBKR daily bars, 1Y, conid 513610886)

| Date | Move | Volume | Driver | Primary source |
|---|---|---|---|---|
| 2025-08-25 | 52w high $32.22 | — | peak | IBKR bars |
| 2025-09-30 | −5.8% | 5.1M (~4x) | co-moved with DKNG −11.6%; **catalyst NOT independently sourced** | tape only |
| 2025-11-05 | −8.6% | 6.7M | Q3-2025 results | [6-K 2025-11-05](https://www.sec.gov/Archives/edgar/data/1836470/000110465925106662/) |
| 2026-03-03 | −9.8% | 4.4M | FY2025 results | [6-K 2026-03-03](https://www.sec.gov/Archives/edgar/data/1836470/000110465926022552/) |
| **2026-04-22** | **−22.6%** | **21.9M (~12x)** | **SHORT-SELLER REPORT** — no company filing that day | see 2.2 |
| 2026-04-28 | rebuttal | — | company response 6-K | [6-K 2026-04-28](https://www.sec.gov/Archives/edgar/data/1836470/000110465926049764/tm2612832d2_6k.htm) |
| 2026-08-03 | −15.1% | 8.6M | Q2-2026 results — **a beat** | [6-K 2026-08-03](https://www.sec.gov/Archives/edgar/data/1836470/000110465926089457/tm2621599d1_ex99-1.htm) |

**The single largest session (2026-04-22, −22.6%) accounts for roughly 19% of the entire peak-to-trough
point decline, and DKNG fell only 2.3% that day.** It is idiosyncratic and has nothing to do with
prediction markets.

### 2.2 What the 2026-04-22 crash actually was

No SEC filing on 2026-04-22. Six calendar days later Sportradar filed an unusual, unprompted 6-K whose
entire content is a rebuttal:

> "We are aware of recent efforts by certain **self-interested third-parties to publish sensationalized
> reports designed to drive down the Company's stock price** for their own financial benefit... these
> actors thrive on misinformation and repackaging historical allegations."
> — [6-K, 2026-04-28](https://www.sec.gov/Archives/edgar/data/1836470/000110465926049764/tm2612832d2_6k.htm)

The allegations the company chose to rebut, and therefore the short thesis, are:
- Serving **grey-market / offshore-licensed** operators (Anjouan, Curaçao licences named explicitly);
- **Downstream B2B redistribution** — SRAD's customer is itself a licensed aggregator that resells to
  operators SRAD has no contract with;
- **Pirated feeds** — third parties reverse-engineer client identifiers, producing a false "Sportradar
  footprint" on unlicensed sites;
- CEO Carsten Koerl's historical **passive minority stake** in a company that owned a Russian sportsbook,
  divested at the outbreak of war;
- **Trade-show sales conduct** toward prospects in jurisdictions that do not permit gaming.

Critically, the company concedes the underlying economics are already disclosed:
> "Sportradar's risk disclosures with the SEC have emphasized that it has **revenue indirectly derived
> from jurisdictions where we, or clients, are not required to hold a license or where limited
> regulatory framework exists**."

**Honesty read:** this is a *disclosed* risk being re-packaged, which under our framework is CLEAN on the
disclosure axis — the marketed takeaway does not diverge from the filed data. But it is **unquantified by
both sides**: SRAD has never sized grey-market revenue as a % of total, and I have not read the short
report itself. See §5 limitations.

### 2.3 The 2026-08-03 print — the divergence

Q2 2026, four days ago, on which the stock fell 15.1%:

| Metric | Q2-2026 | Q2-2025 | Change |
|---|---|---|---|
| Revenue | **€377.8M** | €317.8M | **+19%** |
| Betting & Gaming Content | €254.5M | €199.6M | **+27%** |
| Managed Betting Services | €59.2M | €59.2M | 0% |
| United States revenue | €101.8M | €88.0M | +16% |
| Adjusted EBITDA | **€76M** | €64M | **+19%** |
| Adj. EBITDA margin | **20.2%** | — | expanded |
| Free cash flow | €59M | — | +14% |
| Loss for the period | €(4)M | — | unrealized FX |

**FY2026 guidance (raised/strong, not cut):**
- Revenue +19–21% constant currency → **€1,518–1,533M**
- Adjusted EBITDA +24–27% constant currency → **€360–368M**
- Margin expansion **70–100bps** reported
- FCF conversion to exceed the FY2025 level of 56%

**Capital return:** $140M repurchased in Q2 alone; authorization raised to **$1 billion** (Feb 2026);
$422M repurchased since inception, $311M of it in 2026. A company with a live existential threat does not
buy back 12% of its market cap.

**And the widely-quoted headline from the same release — which I deliberately do NOT treat as thesis-proof:**
> "Announced a **multi-year global agreement with Kalshi**, positioning Sportradar as an official data and
> solutions provider for **the world's largest prediction market**... It also enables Sportradar to enter
> into agreements directly with **Kalshi's partners, including market makers and brokers**."
> "Entered into a **multi-year agreement with Polymarket**, in coordination with Tennis Data Innovations,
> to provide exclusive ATP Tour streaming rights, along with official data, live odds..."

Kalshi and Polymarket are now listed in SRAD's own client roster alongside Flutter, DraftKings, Google
and Microsoft. **Sportradar is the toll road. It gets paid on the event regardless of whether the wager
is booked at a sportsbook or matched on an exchange.**

> **Weight this correctly (see §4.1).** The Kalshi contract's *value* is contingent on Kalshi surviving
> preemption litigation that produced its first final merits loss on 2026-08-04, one day after this print.
> Do not treat the contract as thesis-proof. The durable finding is the weaker-sounding but stronger claim:
> SRAD's +19% revenue and +24–27% cc EBITDA guide are carried by **sportsbook customers and IMG ARENA**,
> with Kalshi/Polymarket as unpriced optionality on top. If exchanges are contained, the volume stays with
> sportsbooks — also SRAD customers. **SRAD is paid on either branch.** That channel-indifference, not the
> Kalshi headline, is what makes the 15% sell-off a divergence.

### 2.4 What survives as genuine bear case

Honest disconfirmation of my own read:
- **Growth quality.** Betting & Gaming Content +27% is materially inflated by the **IMG ARENA acquisition**
  (completed FY2025). Organic growth is lower than the 19% headline and the release does not decompose it.
- **The US is the slow leg.** US +16% vs Rest-of-World +20% — the OSB-substitution-exposed market grows
  slower. Not a refutation, but not nothing.
- **Managed Betting Services is flat** (0% YoY) and Sports Performance −13%.
- **Grey-market exposure is real, disclosed, and unsized.** A regulatory action against offshore licensing
  regimes would impair a revenue line neither the company nor the short seller has quantified.
- **Customer Net Retention Rate is an ANNUAL metric** — last disclosed **109% (FY2025)**, and its absence
  from the Q2 release is normal cadence, **not** a masking flag. I checked this specifically rather than
  scoring it as a disclosure gap. Next value ~March 2027 — too slow to serve as the refuting metric.

### 2.5 Valuation (live price, cap structure pulled first)

Share count from the Q2 balance sheet — **Class B carries 1/10 the economics** (confirmed: Q2 EPS Class A
€(0.01) vs Class B €(0.00); FY-prior €0.17 vs €0.02):
- Class A 215.0M + (Class B 783.7M ÷ 10 = 78.4M) = **293.4M economic shares**
- Market cap @ $12.70 = **$3.73B**
- Net cash: €251.1M cash − €61.0M loans (€10.9M current + €50.1M non-current) = **€190M net cash**
- Enterprise value ≈ **€2.9–3.2B** (range spans USD/EUR 1.10–1.22; FX not live-pulled — stated assumption)

**EV / FY2026E Adjusted EBITDA (guide midpoint €364M) ≈ 7.9x – 8.8x. EV / FY2026E revenue ≈ 2.0x.**

For a business guiding +19–21% cc revenue and +24–27% cc EBITDA with >56% FCF conversion and net cash,
~8x forward EBITDA is a distressed multiple attached to an undistressed P&L.

### 2.6 Classification — SRAD

**DAMAGE-ABSENT.**

- **Named refuting metric (upgraded on the handle amendment, §3.7):** the **US-revenue-to-US-handle wedge** —
  SRAD US revenue growth minus US OSB handle growth. This is the metric that discriminates a feed vendor
  from a book, and it is the one to kill the thesis with. It collapses if SRAD's economics turn out to be
  turnover-linked after all. Secondary: FY2026 Adjusted EBITDA guidance of **€360–368M**.
- **Current value:** **wedge ≈ +14 points** — SRAD US revenue **H1-2026 €191.2M vs €174.1M, +9.9%**, against
  US OSB handle **−3.9% (Jan–May 2026)**. Corroborated by turnover-sensitive Managed Betting Services **flat
  at €59.2M (0%)** while rights-driven Betting & Gaming Content grew **+27%**. Total revenue €377.8M +19%;
  Adj EBITDA €76M +19%; margin 20.2%; FY26 guide intact.
- **Next print:** **Q3 2026, ~early November 2026** (prior-year Q3 6-K filed 2025-11-05).
- **Citation:** https://www.sec.gov/Archives/edgar/data/1836470/000110465926089457/tm2621599d1_ex99-1.htm

**Mechanism (masking × signal × latency):**
- *Masking channel:* cohort mis-labelling, now **quantified**. A B2B vendor whose US revenue grew 9.9%
  while the handle it serves fell 3.9% is being priced with book-operator volume risk it does not carry —
  and separately carries an unquantified compliance overhang from a short report whose core allegation is
  already in the 20-F risk factors. The damage in this sector is real but travels through the *handle ×
  hold* channel that hits books; SRAD is paid on rights and product fees.
- *Signal channel:* signed customer contracts with the alleged predators (Kalshi, Polymarket), disclosed
  in the 2026-08-03 earnings release — a hard, contractual, non-narrative datum.
- *Signal-to-price latency:* **4 days and unpriced.** The stock closed 12.70 on 2026-08-06 versus a 52-week
  low of 11.55 set 2026-08-03. The market has not re-rated on the disclosure that refutes its own thesis.

---

## 3. DKNG — dated driver decomposition

### 3.1 The tape, decomposed (IBKR daily bars, conid 560105364)

| Date | Move | Volume | Driver | Primary source |
|---|---|---|---|---|
| 2025-09-05 | 52w high $48.78 | — | peak | IBKR bars |
| 2025-09-30 | **−11.6%** | 36.0M | no company filing; **catalyst NOT independently sourced** | tape only |
| 2025-10-21 | — | — | **acquires Railbird** (CFTC-licensed DCM) — countermove | [10-K](https://www.sec.gov/Archives/edgar/data/1883685/000188368526000013/dkng-20251231.htm) |
| 2025-12-19 | — | — | **DraftKings Predictions launches** (CFTC introducing broker) | 10-K |
| **2026-02-13** | **−13.5%** | **51.6M** | **Q4-2025 print — beat, but FY26 guide decelerates** | [8-K](https://www.sec.gov/Archives/edgar/data/1883685/000188368526000011/q425-prx8kexx991.htm) |
| 2026-03-25 | −8.1% | 16.5M | no filing; **catalyst NOT independently sourced** | tape only |
| 2026-03-27 | $20.72 | — | 52w low region ($20.46 intraday) | IBKR bars |
| 2026-04-06 | −1.1% | — | 3d Cir rules FOR Kalshi (No. 25-1922) — **near-zero reaction** | coordinator, confirmed |
| 2026-05-08 | **+1.2%** | — | **Q1-2026 print — guidance MAINTAINED** | [8-K](https://www.sec.gov/Archives/edgar/data/1883685/000188368526000019/q126-prx8kexx991.htm) |
| **2026-06-09** | **+11.3%** | 21.9M | **8-K: Predictions volume $3.1B annualized, +34% MoM** | [8-K](https://www.sec.gov/Archives/edgar/data/1883685/000110465926071581/tm2617134d1_8k.htm) |
| 2026-06-10/11 | to $30.02 | — | CFTC NPRM (moneylines/props permitted) — **+45% off the low** | coordinator, confirmed |
| 2026-06-17 | −7.7% | — | Illinois exchange-wager tax 3.5%/contract effective 06-16 | coordinator, confirmed |
| **2026-08-05** | **−7.8%** | 21.3M | **FLUTTER's Q2 read-across — NOT DKNG's own print** | see 3.3 |

### 3.2 The 2026-02-13 drop is the real one — and it is elective, not structural

Q4-2025 was, on its face, excellent: revenue **$1,989.2M, +42.8%**; FY2025 revenue **$6,054.5M, +27.0%**;
records in revenue and Adjusted EBITDA; first year of positive net income. The stock fell 13.5% anyway.

The cause is in the guidance paragraph, verbatim:
> "DraftKings is introducing a fiscal year 2026 revenue guidance range of **$6.5 billion to $6.9 billion**
> and a fiscal year 2026 Adjusted EBITDA guidance range of **$700 million to $900 million**. The Company's
> guidance ranges reflect **expected investment in DraftKings Predictions**, line-of-sight jurisdiction
> launches, and disciplined planning... The Company **assumes state tax rates will remain consistent with
> where they are today**."

That is **+7.4% to +14.0% revenue growth guided against +27% delivered** — a deceleration of ~15 points —
with EBITDA deliberately spent down on the Predictions build. This is self-inflicted, disclosed, and
strategic. It is *not* evidence of substitution; it is evidence of DKNG **buying its way into** the
substituting channel. Note also the explicit, unhedged state-tax assumption — the live structural risk.

### 3.3 The 2026-08-05 drop was somebody else's print

DKNG's most recent 8-K is **2026-06-26**. There is no company filing behind the 2026-08-05 −7.8% move.
It is a read-across from **Flutter's Q2 (2026-08-05)**, and Flutter's own bridge is anti-substitution:
- FanDuel US handle **+2.2% YoY — growing**
- Structural revenue margin **+40bps to 14.0% — improving**
- US sportsbook revenue −15%, attributed by the company to **adverse sports results (−70bps)** and
  **promotional spend (+140bps, to 5.4% of handle)**
- US market growth "mid-single digit" — **decelerating, not declining**
- Source: https://www.flutter.com/media/g23an0ae/flutter-q2-2026-earnings-release.pdf

> **CORRECTION (2026-08-07).** My first pass read Flutter's +2.2% as "handle grew — volume is not being
> substituted away." **That was wrong.** Aggregate US OSB handle has been *negative for six straight
> months* (§3.7). FanDuel's +2.2% is a **share gain inside a shrinking market**, not market growth. The
> corrected claim is narrower and survives: what compressed *Flutter's revenue* was margin (promo +140bps,
> sports results −70bps), and Flutter took share while doing it. But the market-level volume premise was
> mine and it was false. Corrected below.

### 3.4 The market's own revealed pricing contradicts the substitution narrative

DKNG rallied **+11.3% twice** on days that federally *legitimized and expanded* prediction markets (the
CFTC NPRM sequence), and ran **+45% off its March low to $30.02 by 2026-06-11**. It moved **−1.1%** on the
3d Circuit ruling FOR Kalshi (2026-04-06). A market pricing structural substitution does not behave this
way. It is pricing prediction markets as **incremental TAM for licensed incumbents**, which is also what
DKNG's own metrics say: Predictions annualized consumer volume $1.3B (+24% MoM), total volume traded
**$3.1B (+34% MoM)** as of May 2026.

The real dated structural risk is **tax parity**, not substitution: Illinois enacted a 3.5%-per-contract
exchange wager tax effective 2026-06-16, establishing the template. DKNG's FY26 guide explicitly assumes
no state tax change — so the guide is unprotected against that template spreading.

### 3.5 Valuation

Cap structure pulled before the multiple. **DKNG Class B has no economic rights** (10-K: "exclusive of
Class B common stock as these shares have no economic or participating rights"; Class B "will not
participate in any dividend"). Economic shares = Class A only.
- Class A outstanding **495.76M** @ $21.84 = **$10.83B** market cap
- Debt: convertible notes **$1,259.8M** + Term B Loan **$575.6M** = **$1,835.4M**
- Cash & equivalents **$999.4M** (cash reserved for users $378.7M is offset by liabilities to users $811.6M
  — a net working-capital drag, not a cash asset)
- **Enterprise value ≈ $11.67B**

**EV / FY2026E Adjusted EBITDA = 13.0x (at $900M) to 16.7x (at $700M); ~14.6x at the $800M midpoint.
EV / FY2026E revenue ≈ 1.74x.**

Q1-2026 supports the low end: revenue $1,646M **+17%**, net income **+$21.1M** (vs −$33.9M), adjusted
diluted EPS $0.20 vs $0.12, ARPMUP $131 **+21%** on higher Sportsbook net revenue margin, guidance
maintained, and CEO stating "profitability is inflecting."

### 3.6 Classification — DKNG

**DAMAGE-ARRIVING.**

Not because of substitution — that is refuted — but because a **promotional-intensity war is confirmed at
a direct competitor and DKNG has not yet printed against it.** Flutter escalated US promo to 5.4% of
handle (+140bps) in the quarter DKNG is about to report. DKNG's Q1 margin strength (ARPMUP +21% on higher
hold) predates that escalation.

- **Named refuting metric:** **Q2-2026 handle, Sportsbook net revenue margin and promotional intensity**,
  plus reaffirmation of the **FY2026 Adjusted EBITDA guide of $700–900M**. Report handle and hold
  *separately* — per §3.7(c), revenue growth on falling volume is the sector's characteristic disguise, and
  DKNG's Q1 ARPMUP +21% "on higher net revenue margin" is exactly that shape. Handle is the leading
  indicator; revenue is the harvested output.
- **Newly grounded exposure:** DKNG's FY26 guide states it "**assumes state tax rates will remain consistent
  with where they are today**." §3.7 shows state tax shocks are the *dominant identified driver* of the
  six-month handle contraction (PA −12.9%, NJ −9.8% vs MI/TN +3%). The guide's single explicit assumption
  is unhedged against the one variable empirically doing the damage.
- **Current value (last actual):** Q1-2026 revenue **$1,646M, +17%**; ARPMUP **$131, +21%**; MUPs 4.2M
  (−4% headline, **+2% ex-Lottery** after the Texas exit); FY26 guide **maintained** at $6.5–6.9B /
  $700–900M; net income **+$21.1M**.
- **Next print:** **Q2 2026 — IMMINENT and not yet scheduled by 8-K.** No earnings 8-K filed as of
  2026-08-06 (latest filings are Form 4s). Prior-year Q2 8-K was filed **2025-08-07**; Q1-2026 was released
  2026-05-07 with the call 05-08. **Expect 2026-08-07 to 2026-08-14.**
- **Citation:** https://www.sec.gov/Archives/edgar/data/1883685/000188368526000019/q126-prx8kexx991.htm

**Mechanism (masking × signal × latency):**
- *Masking channel:* two genuinely different impairments blended into one narrative — elective Predictions
  reinvestment (disclosed 2026-02-13, strategic, reversible) and a competitive promo cycle (confirmed at
  Flutter 2026-08-05) — both sold as structural disintermediation, which the handle data refutes.
- *Signal channel:* DKNG's own monthly Predictions volume 8-Ks, and Flutter's handle-vs-margin bridge.
- *Signal-to-price latency:* **split, and that is why this does not court.** The margin question self-resolves
  in DKNG's own Q2 print within roughly a week — no durable edge in front-running it. The *structural*
  question (preemption, NPRM final scope, tax parity) resolves over quarters-to-years across three
  undecided circuits and an open rulemaking, which is unadjudicable now. Neither latency band supports a
  court today.

**Second-order risk added on the coordinator's correction (§4.1):** DKNG's FY26 EBITDA was deliberately
spent building Predictions. A CFTC final rule banning prop/micro contracts caps that product's TAM; a
preemption loss strands it state-by-state (D. Utah final merits judgment against Kalshi, 2026-08-04;
districts majority-against); IL/KY per-contract taxes tax the remainder; and the abandoned Nevada licensing
applications hint at a licensure conflict between running an exchange and holding state sportsbook
licences. The offset is real and possibly larger — a prop ban on exchanges structurally protects DKNG's
core parlay franchise, which is ~$6B of revenue versus a start-up Predictions line. Net: genuinely
two-sided, which is an argument for waiting, not for conviction in either direction.

---

## 3.7 The handle data — the market DID detect real damage, and mis-labelled its cause

State regulator filings (8 states) show **aggregate US OSB handle negative for six consecutive months**:

| Period | US handle YoY |
|---|---|
| Dec-2025 | −4.0% |
| Jan–May 2026 | **−3.9%** |
| May-2026 | −4.0% |
| Jun-2026 | +24.6% — **World Cup noise, discard** |

Sources: njoag.gov, gaming.ny.gov, gamingcontrolboard.pa.gov and the equivalent MI/IL/IN/OH/TN regulators.

**Two consequences, and the first one costs me an argument.**

### (a) Facts LED price. My "narrative postdates the drivers" framing is partly wrong.

Handle inflected negative in **Dec-2025**, two months *before* the Feb-2026 stock breaks. The market was
not rationalizing after the fact on that leg — it was responding to real, observable deterioration, and it
was early. I over-claimed. The rationalization critique survives only in weaker form: **the market
correctly detected damage and mis-attributed its cause.** That distinction is the whole thesis, because
cause determines duration:
- *Substitution* → permanent, terminal-value impairment.
- *Tax-shock margin defence* → operators choosing to cut promo and widen pricing, which suppresses volume
  **while raising revenue** — extraction, not disintermediation, and partially reversible.

### (b) The dispersion points at tax, not substitution — but does not cleanly exclude it

| Tax-shock states | Handle | Unchanged-economics states | Handle |
|---|---|---|---|
| PA | **−12.9%** | MI | +3% |
| NJ | **−9.8%** | TN | +3% |
| IL | −5.1% | IN / NY / OH | −0.2% to −2.5% |

A 3–5x spread between states that raised taxes and states that did not is a **state-tax signature**. A
nationally-available federal product (Kalshi, Robinhood — live in ~all 50 states, including the ~20 with
no legal OSB) should erode legal-OSB states far more uniformly.

**Honest confound, which I will not paper over:** tax-shock states also have the *worst sportsbook pricing*
after operators defended margin — so they have both the weakest recreational demand **and** the strongest
incentive to switch to an exchange. Dispersion is therefore consistent with both stories. The clean
discriminator is whether Kalshi/Robinhood volume is disproportionately **sourced from PA/NJ/IL**, which I
do not have and which should be the first evidentiary request in any court.

### (c) Do not proxy volume with revenue — including for SRAD

Hold was abnormally high in Dec-2025 (MI **16.4%**), so **GGR grew while volume fell**. Revenue growth
anywhere in this cohort is therefore *not* evidence of a healthy underlying market. I apply that discipline
to my own SRAD verdict below: SRAD's growth does not prove the betting market is fine. It proves something
narrower and more useful — that **SRAD's revenue is decoupled from handle.**

### (d) The quantified SRAD decoupling — the metric this amendment produces

Period-aligned, using six-month figures rather than the flattering Q2 (Q2 contains the World-Cup June):

> **SRAD US revenue H1-2026 €191.2M vs H1-2025 €174.1M = +9.9%, against US OSB handle of −3.9% over
> Jan–May 2026. A ~14-point wedge.**

SRAD's US monetization grew ~10% while the volume of the activity it serves shrank ~4%. That is direct
evidence its economics are **rights-, content- and product-priced, not turnover-priced**. Corroborating it
from the same release: **Managed Betting Services — the most turnover-sensitive line — was flat at €59.2M
(0%)**, with higher Managed Trading Services turnover offset by lower platform revenue, while
rights-driven Betting & Gaming Content grew **+27%**.

**This reframes SRAD's exposure correctly.** A market where volume shrinks but GGR/hold rises hits a *book*
(revenue ≈ handle × hold, and it keeps the risk) very differently from a *feed vendor* (revenue ≈ contracted
rights and product fees). SRAD is substantially insulated from the handle channel that is actually damaging
the operators.

**New bear point this raises, which I had missed:** if handle keeps contracting, SRAD's customers come under
sustained margin pressure into **renewal cycles**, while SRAD's own largest cost — sport rights, rising with
IMG ARENA, the Wimbledon extension and ATP — is fixed and growing. Rising fixed rights cost against
financially squeezed customers is a genuine medium-term pricing-power risk. It is not biting yet (FY26 guide
is margin expansion of 70–100bps), but it is the right thing to underwrite, and it is a better bear case
than the substitution story the cohort is using.

---

## 4.1 The legal tail is TWO-SIDED and unsettled — correction to my first pass

My initial read leaned on "federal legitimization is good for incumbents," inferred from the June rallies.
That inference over-read a tape move as a settled legal fact. The primary record says preemption is very
much live, and the direction of travel at district level is **against** Kalshi:

| Date | Development | Direction |
|---|---|---|
| 2025-11-14 | **FanDuel and DraftKings voluntarily abandon Nevada licensing applications** (D. Nev. ECF 237 n.14) | negative |
| 2025-11-24 | Nevada **dissolves** Kalshi's preliminary injunction | against Kalshi |
| 2026-04-06 | 3d Cir. rules **for** Kalshi on preemption (No. 25-1922) | for Kalshi |
| 2026-06-10 | CFTC NPRM (91 FR 40102): keep moneylines/spreads, **BAN prop/micro contracts** | mixed |
| 2026-06-16 | Illinois exchange-wager tax, 3.5%/contract; Kentucky following | negative |
| **2026-08-04** | **D. Utah enters the FIRST FINAL MERITS JUDGMENT against Kalshi** — no CEA preemption of state anti-gambling law | against Kalshi |

- **District scoreboard is majority-against:** MD, OH, AZ, W.D. Mich., SDNY, UT, NV against; NJ, TN, MN for.
- **9th, 4th and 6th Circuit merits are all argued and undecided.**
- The CFTC is **suing nine states**.

### What this changes

**The prop/micro ban is the pivotal detail, and it cuts in DKNG's favour on the axis that actually matters.**
The substitution threat to sportsbook economics was never straight moneylines — those are low-margin. It
was always **parlay and prop replication**, and Kalshi's live API already carries 1,389 multi-leg parlay
collections including same-game and player props. If the CFTC's own proposed rule bans exactly those on
exchanges, the substitution vector into the core OSB franchise is **capped by federal rule**, while
sportsbooks keep offering props under state licences. That materially supports the DAMAGE-ABSENT reading
of the *substitution* claim for both names.

**But it damages the elective investment.** DKNG cut FY26 EBITDA to $700–900M specifically to build
Predictions. A prop/micro ban caps that product's addressable market; a preemption loss strands it
state-by-state; per-contract taxation (IL, KY) taxes what survives. The Nevada abandonment suggests state
gaming regulators may force a choice between sportsbook licensure and exchange operation — a structural
cost across DKNG's 27 sportsbook states that I did not price in the first pass. **I have confirmed the
abandonment as fact but have NOT verified its causal link to prediction-market affiliation; that inference
is mine and is unverified.**

**For SRAD this is close to a genuine hedge, and it forces me to demote my own best-sounding argument.**
The Kalshi contract announced 2026-08-03 is contingent on Kalshi surviving litigation that just produced
its first final merits loss one day later, on 2026-08-04. I should not have leaned on it as thesis-proof.
The stronger and correct form of the argument is that **SRAD does not need it**: the +19% revenue and
+24–27% cc EBITDA guide are driven by sportsbook customers and IMG ARENA, with Kalshi/Polymarket as
unpriced optionality on top. If prediction markets are contained, volume stays with sportsbooks — who are
SRAD's core customers. If they expand, SRAD has the contracts. **SRAD gets paid on either branch; that
channel-indifference, not the Kalshi headline, is the actual finding.**

---

## 4. Court-worthiness

**COURT-WORTHINESS SRAD: 8/10** — the sector's damage is real but travels through handle (−3.9% over six
months, tax-shock-concentrated), and SRAD is demonstrably decoupled from it: **US revenue +9.9% against
handle −3.9%, a ~14-point wedge**, with the turnover-sensitive line flat at 0% and the rights-driven line
+27%; it is a net-cash feed vendor priced with book-operator volume risk it does not carry, channel-
indifferent across the unsettled preemption outcome, buying back $1B against a $3.7B cap at ~8x forward
EBITDA, and it fell 15% four days ago on a print that showed all of this and has not re-rated; the
load-bearing bear cases are an unquantified grey-market compliance tail from a short report I have read
only the rebuttal to, and rising fixed sport-rights cost against financially squeezed customers into
renewal.

**COURT-WORTHINESS DKNG: 5/10 — does NOT escalate; re-triage, do not court** — the substitution thesis is
refuted on the axis that matters (Flutter US handle +2.2% growing, DKNG Predictions volume +34% MoM, and a
CFTC proposed rule that would ban the prop/parlay legs on exchanges while sportsbooks keep them), and
~14.6x forward EBITDA on maintained guidance with inflecting profitability is not demanding; but every
decisive variable is unresolved on a timetable we do not control — three undecided circuit appeals with
district courts majority-against Kalshi and a first final merits judgment on 2026-08-04, an open NPRM whose
final scope determines whether the FY26 EBITDA that was spent building Predictions is stranded, a spreading
per-contract tax template, and an unscheduled Q2 print landing within days against a confirmed competitor
promo war — so an adversarial court convened today would be adjudicating branches rather than facts.

**Only SRAD clears the ≥6 auto-escalation bar.** DKNG re-triages after (a) the Q2 print and (b) the CFTC
final rule.

---

## 5. Limitations — what I did NOT verify

Stated plainly, because UNVERIFIABLE is not clean:

1. **I have not read the April 2026 short report.** I have only Sportradar's rebuttal — the defendant's
   brief. Its author, exact publication date (inferred 2026-04-22 from the tape), and specific evidentiary
   claims are unverified. This one-sidedness is the single largest cap on the SRAD score, and a Fable court
   must obtain the report itself before sizing anything.
2. **Grey-market revenue is unquantified by both sides.** Sportradar has never disclosed offshore/grey
   revenue as a % of total; the 20-F language is qualitative. This is the genuine unresolved tail.
3. **Two tape gaps remain unsourced to a catalyst:** 2025-09-30 (DKNG −11.6% / SRAD −5.8%, 36.0M shares)
   and 2026-03-25 (DKNG −8.1%). The *moves* are verified from IBKR bars; the *causes* are not. The web
   search budget for this session was exhausted (200/200) before these could be sourced. The 2025-09-30
   date is the most likely true origin of the prediction-market repricing and should be sourced first in
   any court.
4. **DKNG's Q2 2026 earnings date is inferred**, not confirmed by 8-K or IR calendar — based on prior-year
   cadence (Q2-2025 8-K filed 2025-08-07).
5. **USD/EUR was not live-pulled.** SRAD enterprise value is therefore presented as a range across
   1.10–1.22 rather than a point estimate. The EV/EBITDA conclusion (~8x) is robust across that range.
6. **I initially treated CFTC preemption as settled for Kalshi**, inferring it from DKNG's June rallies.
   That was a tape-derived inference presented with more confidence than the legal record supports, and it
   was corrected on primary sources (§4.1). Logged as a calibration miss: a price move is evidence about
   what the market believes, never about what a court has held.
7. **The causal link between the Nevada licence abandonment and prediction-market affiliation is my
   inference, not a verified fact.** The abandonment itself (D. Nev. ECF 237 n.14) is confirmed.
8. **I asserted "handle grew — volume is not being substituted away" from a single company datapoint
   (Flutter +2.2%) and it was false at market level** (aggregate handle −3.9%). Flutter was gaining share
   in a shrinking market. Second calibration miss this session, same shape as #6: generalizing from one
   favourable observation to a market-level claim. Standing fix — for any market-level volume assertion,
   require the regulator/aggregate series, never a single issuer's disclosure.
9. **My "the narrative postdates the drivers" framing was partly wrong.** Handle inflected Dec-2025, before
   the Feb-2026 price breaks — facts led price on that leg. The surviving, weaker claim is mis-attribution
   of cause, not lateness of reaction.
10. **The state dispersion does not cleanly separate tax-shock from substitution**, because tax-shock states
    have both the weakest demand and the strongest switching incentive. The missing discriminator —
    Kalshi/Robinhood volume geography, specifically whether it over-indexes to PA/NJ/IL — is the first
    evidentiary request for any court and is NOT in hand.
8. Sportradar's constant-currency guidance vs reported growth was checked for consistency against FY2025
   actuals (revenue €1,290M, Adj EBITDA €297M, margin 23.0%) — guide implies FY26 margin 23.7–24.0%,
   consistent with the stated 70–100bps expansion. No conflation found.

---

## 6. Primary sources

- SRAD Q2-2026 results (6-K, 2026-08-03) — https://www.sec.gov/Archives/edgar/data/1836470/000110465926089457/tm2621599d1_ex99-1.htm
- SRAD short-report rebuttal (6-K, 2026-04-28) — https://www.sec.gov/Archives/edgar/data/1836470/000110465926049764/tm2612832d2_6k.htm
- SRAD FY2025 results (6-K, 2026-03-03) — https://www.sec.gov/Archives/edgar/data/1836470/000110465926022552/tm267539d1_ex99-1.htm
- SRAD FY2025 20-F (2026-03-27) — https://www.sec.gov/Archives/edgar/data/1836470/000110465926035485/srad-20251231x20f.htm
- DKNG Q1-2026 results (8-K, 2026-05-08) — https://www.sec.gov/Archives/edgar/data/1883685/000188368526000019/q126-prx8kexx991.htm
- DKNG Q4/FY2025 results (8-K, 2026-02-13) — https://www.sec.gov/Archives/edgar/data/1883685/000188368526000011/q425-prx8kexx991.htm
- DKNG FY2025 10-K (2026-02-13) — https://www.sec.gov/Archives/edgar/data/1883685/000188368526000013/dkng-20251231.htm
- DKNG Predictions volume (8-K, 2026-06-09) — https://www.sec.gov/Archives/edgar/data/1883685/000110465926071581/tm2617134d1_8k.htm
- Flutter Q2-2026 earnings release (2026-08-05) — https://www.flutter.com/media/g23an0ae/flutter-q2-2026-earnings-release.pdf
- Robinhood Q2-2026 10-Q (2026-07-30) — event-contracts revenue $156M vs $10M PY (12% of net revenue)
- CFTC NPRM **91 FR 40102** (2026-06-10) — moneylines/spreads permitted, prop/micro/injury/officiating banned
- **3d Cir. No. 25-1922 (2026-04-06)** — preemption FOR Kalshi
- **D. Utah, first final merits judgment AGAINST Kalshi (2026-08-04)** — no CEA preemption of state law
- **D. Nev. — Kalshi PI dissolved 2025-11-24; ECF 237 n.14 (2025-11-14)** — FanDuel and DraftKings
  voluntarily abandoned Nevada licensing applications
- 9th / 4th / 6th Circuit merits argued and undecided; CFTC suing nine states
- Illinois exchange-wager tax 3.5%/contract (eff. 2026-06-16); Kentucky following
- **US OSB handle (8-state aggregate):** njoag.gov, gaming.ny.gov, gamingcontrolboard.pa.gov, michigan.gov/mgcb, igb.illinois.gov, in.gov/igc, casinocontrol.ohio.gov, tn.gov/swc — monthly handle filings Dec-2025 through Jun-2026
- Prices: IBKR live snapshots + 1Y daily bars, conids 513610886 (SRAD) / 560105364 (DKNG), 2026-08-07
