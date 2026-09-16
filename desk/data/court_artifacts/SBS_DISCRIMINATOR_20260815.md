# SBS — ELECTION-GATE DISCRIMINATOR PACK
**2026-08-15 · verification pack for any advance on SBS (SABESP ADR / SBSP3)**
Reads: `edge_classifications/SBS.json`, `SBS_COURT_RED_202608150738.md`, `SBS_COURT_BLUE_202608150746.md`, `SBS_TRAP_VERIFY_202608150731.md`

---

## VERDICT: **NO-DISCOUNT** — the election was never priced into SBSP3. Close the October gate as *irrelevant*, not as *resolved*.

> **But the court's fundamental kill does NOT stand as written.** Its load-bearing "FATAL" finding — *IPCA-only in-cycle, capex remunerated only at the 2029 RTO* — is **REFUTED against the operative primary sources**. Both benches read a **consultation draft**. See Discriminator 3(a). The entry still fails today, but it fails for narrower reasons than the court gave, and one accepted knowledge-graph candidate is built on a refuted mechanism.

The principal's framing — "either the signal impeaches or the entry decides NOW" — is a **false dichotomy**. There is a third branch and four independent tests say it is the true one: **SBSP3 has no measurable election beta.** The gate was never load-bearing in either direction. Removing an incoherent gate does not manufacture an entry. Polymarket's 93.5% is *correct* — and it does not matter.

**Headline arithmetic (broker-verified tape):** at a 93.5% priced probability the election branch offers **+0.5% to collect against a −7.4% tail** — **14.4 : 1 against**. That ratio is `p/(1−p)`, **invariant to what the branch spread is worth**.

---

## TAPE CORRECTIONS (both courts' open data gap — CLOSED)

IBKR permission was granted this session.

| item | court used | verified | source |
|---|---|---|---|
| ADR SBS | $4.60 | **$4.55** | IBKR snapshot, last 2026-08-14 22:58 UTC, `is_close:false`, ctr 14996978 |
| SBSP3 | R$24.28 | **R$23.79** | 8/14 close (R$24.28 was 8/13) |
| SBSP3 13w / 52w low | — | R$23.39 / R$21.11 | IBKR, ctr 51283341 |

ADR parity clean: R$23.79 ÷ 5.1998 = $4.575 vs $4.55 (−0.6%). No ADR dislocation.
**EV at the corrected price:** mcap R$81.3bn + net debt R$34.2bn = **EV R$115.5bn → 8.25x** adj-EBITDA (7.41x reported). Red's EV arithmetic survives the price correction — marginally worse, not better.

---

## DISCRIMINATOR 1 — SIGNAL INTEGRITY: **SIGNAL STANDS** (precision is overstated; direction and level are right)

Polymarket event 421102, market 2088352, condition `0x7fad7ba1…bcee`.

**The "$220k liquidity" is not depth.** That is the whole-book `liquidity` field. Actual CLOB book at the touch:

| side | price | size | notional |
|---|---|---|---|
| ask | 0.95 | 2,145 | $2,038 |
| **ask** | **0.94** | **1,074** | **$1,009** |
| **bid** | **0.93** | **4,147** | **$3,857** |
| bid | 0.92 | 1,829 | $1,683 |

Within 2c of mid: **~$5.5k bids / ~$3.0k asks**. The headline is padded by $22.4k parked at 0.99 and lottery bids at 0.44/0.60/0.70 (41 bid levels vs 6 ask levels).

**Flow is near-dead.** `volume24hr` **$346** · `volume1wk` **$892** · `volume1mo` $7,479. The last 500 trades (06-02→08-14) total **$74,168 across 213 wallets**, and are top-heavy: one wallet **31.4% of notional in 9 trades**, top 3 **56.7%**. August tickets run $1–$120.

**The tight quote is subsidised.** `clobRewards`: $5/day, `rewardsMaxSpread` 5.5c, `rewardsMinSize` 20 — **started 2026-08-12, three days ago**. The 1c book is liquidity-mining, not conviction.

**But thin ≠ wrong, and the polling corroborates it decisively.** Five houses, tightly clustered on margin:

| poll | field | Tarcísio | Haddad | margin |
|---|---|---|---|---|
| American Analytics/Times/CNBC | Aug 4–8 | 46% | 29% | **+17** |
| Ideia/ACSP | Aug 5–8 | 50.6% | 33.6% | **+17.0** |
| Vox | Jul 29–31 | 52.9% | 34.3% | +18.6 |
| Quaest | Jul 23–27 | 41% | 26% | +15 |
| Datafolha | Jul 1–3 | 46% | 30% | +16 |

**Consensus Tarcísio +15 to +19, flat for five months**, incumbent, opponent at full name recognition, two of the last four polls at/above 50% (first-round win). Brazilian state-race margin error is ~4–5pp sd, so +17 is ≈3.5σ ⇒ >99% naive. Reaching 93.5% requires ~6.5pp of haircut for poll error, seven weeks of drift and scandal tail — a **reasonable, even conservative, discount**.

**Finding: SIGNAL STANDS — NOT impeached.** The 93.5% *level* is fair-to-slightly-cheap. What is impeached is only its **apparent precision**: it is a 1c mid on ~$900/week with a 3-day-old subsidy, so read it as "heavily favoured, ~90–96%", not "93.5% ± nothing." **The date gate is not restored** — because Discriminator 2 shows the entry fails at *any* p.

---

## DISCRIMINATOR 2 — THE DECISIVE ONE: **DID SBSP3 EVER PRICE THE ELECTION DOWN? NO.**

Four independent tests. All negative. A placebo refuted my own first hypothesis, and the falsification test I designed to break the finding instead confirmed it.

### Test A — regression: abnormal return ~ Δ(Tarcísio probability)

Market model estimated on a **clean pre-event window** (2025-06-01 → 2026-04-26, before the market existed): SBSP3 β=1.118 vs IBOV. Event window 04-28 → 08-14.

| spec | implied FULL Tarcísio-minus-Haddad spread | t | 95% CI |
|---|---|---|---|
| SBSP3 same-day | **+7.9%** | +1.09 | [−6.3, +22.2] |
| SBSP3 3-day cumulative | +18.4% | +1.55 | [−4.9, +41.6] |
| SBSP3 leads PM 1d / lags 1d / weekly | −1.1 / +4.4 / +4.9% | −0.14 / +0.57 / +0.32 | — |
| SBS ADR vs EWZ, same-day | +8.8% | +1.10 | [−6.9, +24.5] |
| SBS ADR 3-day / leads / lags / weekly | +0.4 / −3.4 / +3.3 / +1.5% | +0.04 / −0.44 / +0.40 / +0.09 | — |

**Ten specifications; none reaches t=2.** R²=0.018 on the base spec.

*Leverage check:* the highest-leverage observation (04-29, dp=+16pts) is contaminated twice — it is the Polymarket **inception** week (price discovery, not news) **and** the SBSP3 1:5 split ex-date. Dropping it: +6.5% (t=0.51). Dropping the whole inception fortnight: +9.2% (t=0.64). Winsorised: +4.9% (t=0.33). **Conclusion unchanged.**

### Test B — the level test (immune to the attenuation critique)

The strongest objection to Test A is that a thin Polymarket makes Δp noisy, attenuating β toward zero. **Test B uses no regressor at all**, so that critique cannot apply.

Over 2026-04-28 → 08-14 Tarcísio went **0.585 → 0.935** — i.e. **35 points of Haddad risk were retired**. If SBSP3 carried an election discount, this is exactly when it gets collected.

| | indexed 04-28 = 100 | total |
|---|---|---|
| **SBSP3** | **70.0** | **−30.0%** |
| SAPR11 (Sanepar, Paraná) | 78.5 | −21.5% |
| CSMG3 (Copasa, Minas Gerais) | 100.3 | +0.3% |
| IBOV | 88.1 | −11.9% |

**SBSP3 underperformed the water-peer average by 19.4 points** (13.5 ex-print; 12.4 measured from 05-05 post-inception/post-split to 08-12 pre-print) **while its election tail was being retired**. The sign is wrong. This is affirmative evidence, not merely absence of evidence.

Sanepar and Copasa are the right controls: state water concessionaires carrying Brazilian sector/rate/political risk but **not** the São Paulo governor's race.

### Test C — the option surface (supporting, caveated)

| expiry | strikes listed 4.0–5.5 | ATM open interest |
|---|---|---|
| Aug 21 / Sep 18 / Jan 15 '27 | 5.0 only | — |
| **Oct 16 '26** (spans 1st round) | **4.0 / 4.5 / 5.0** | **call 0 / put 0** |

**Honest caveat:** the *entire* SBS surface is near-dead, so zero October OI is largely a general-illiquidity fact and cannot carry the verdict. Two things it does establish: October is the only expiry with sub-$5 strikes listed and **still nobody holds any**; and **the election tail is not hedgeable in practice** — an ENTER-NOW advance takes the 6.5% tail **naked**.

### Test D — **THE DECISIVE TEST**: event study on ten *dated, primary-sourced* election events

This is the test I flagged as the one most likely to break my own conclusion: the real repricing may have happened **before 2026-04-28**, outside the Polymarket series. Dated events were sourced independently from G1/CNN Brasil/Poder360/DOU. Measure = SBSP3 **idiosyncratic** return (abnormal net of water peers), idio sd = 1.65%.

| date | expected | SBSP3 abn | peers | **IDIO** | z | event |
|---|---|---|---|---|---|---|
| 2026-01-22 | BULLISH | +0.82% | +1.14% | −0.32% | −0.19 | **Tarcísio declares re-election** (continuity secured) |
| 2026-01-29 | BULLISH | −0.74% | −0.76% | +0.02% | +0.01 | Tarcísio confirms after Bolsonaro visit |
| **2026-03-19** | **BEARISH** | **+3.23%** | +1.52% | **+1.72%** | +1.04 | **Haddad quits Finance Ministry to run for SP** |
| 2026-03-20 | BEARISH | +0.10% | +0.15% | −0.05% | −0.03 | DOU decree published |
| **2026-05-21** | **BEARISH** | −2.12% | −2.44% | **+0.32%** | +0.19 | **Haddad: "vou rever as cláusulas" / "the Enel of water"** |
| 2026-06-15 | BEARISH | +1.52% | −0.53% | +2.05% | +1.24 | Haddad: SABESP sold "em mesa de amigos" |
| 2026-06-25 | BEARISH | +0.48% | +1.26% | −0.77% | −0.47 | Haddad names Márcio França VP |
| 2026-07-27 | BEARISH | +0.83% | +1.07% | −0.24% | −0.15 | PT convention nominates Haddad |
| 2026-08-04 | BULLISH | +1.53% | −0.83% | +2.37% | +1.43 | Republicanos launches Tarcísio |
| 2026-08-12 | BULLISH | +0.62% | +0.31% | +0.32% | +0.19 | Monday after the 1st debate |

**Not one event reaches |z| = 2.** Sign test (bullish +, bearish −): cumulative **−0.63%**, mean **−0.06%/event**, **t = −0.12** — indistinguishable from zero and, if anything, the *wrong sign*.

The two individually decisive readings:
- **03-19 — Haddad enters the race**, the single most bearish possible event for a privatised concession, and SBSP3 traded **+3.23% abnormal / +1.72% idio. It went UP.**
- **05-21 — Haddad states explicitly he will review the concession's clauses** and invokes the Enel comparison, the sharpest policy threat of the campaign: idio **+0.32%, z=+0.19**. The −2.12% abnormal that day was *fully shared by peers* (−2.44%) — a sector day.

3-day cumulative windows: 01-22 −1.92% (z=−0.67), 03-19 −1.08% (z=−0.38), 05-21 −0.07% (z=−0.02). Nothing.

### Supporting: the placebo caught my own error, and the print had zero election content

My first read scored 2026-06-22 (+2.24% abnormal, on the biggest Tarcísio re-rate) as real election beta. **The placebo refuted it: SAPR11 +2.46%, CSMG3 +3.38% — the out-of-state peers moved more.** A water-sector day, not an election day.

Across the print, Polymarket read 8/13 **0.935** · 8/14 **0.935** · 8/15 **0.935** while SBSP3 posted **−7.09%** and **−1.97%** abnormal (worst and 10th-worst of 2026). The principal's premise is confirmed: **print-driven**. Of the largest idiosyncratic moves since Sep-2025, the only two with an identified cause are **both the print**.

### Why re-specifying p cannot rescue the entry

The data cannot rule out a full spread as large as ~22% of price. It does not need to — **the trade dies on the residual probability, not the spread estimate**:

> collectable if Tarcísio wins = (1 − p) × spread. At the **95% upper bound** spread of 22.2%: 0.065 × 22.2% = **1.44% of price**.

Nor does re-specifying p help: at p=0.85 the collectable rises but the tail widens, and the ratio stays `p/(1−p)` = 5.7:1 against. **There is no value of p at which a 93.5%-priced binary with a ≤22% spread is an entry.**

---

## DISCRIMINATOR 3 — BRANCH VALUES

### (a) The OWED contract read — **the court's "FATAL" finding is REFUTED**

This closes the flagged open item, and the answer overturns it. Escalation discipline applied: the finding flips a court FATAL, so I re-verified every load-bearing element myself against primary sources rather than accepting the research pass.

**Process finding first — both benches read the wrong document.** `Contrato-de-Concessao-1-1.pdf` (Feb 2024, 85pp), cited by red, blue and the trap-verify, is the **consultation draft**. The signed contract is a different document (Aug 2024, **92pp**, `Contrato-de-Concessao-Assinado_assinado_dp_assinado.pdf`) — both fetched and page-counted this session. More importantly there are **two structurally different Anexo V versions**, and the Feb draft contains no RAB-update chapter at all. The operative annex is `2024/05/Anexo-V.pdf`.

**What the operative sources actually say — three independent confirmations:**

1. **Anexo V item 3.7** (verified verbatim by me from the May-2024 PDF):
   > *"A TARIFA DE EQUILÍBRIO necessária para cobrir a RR do PERÍODO DE REFERÊNCIA **será calculada anualmente durante os dois primeiros CICLOS TARIFÁRIOS** após o início do CONTRATO (**2024-29 e 2030-34**) **em sede de REAJUSTE**…"*

   The equilibrium tariff is recalculated **annually**, at the annual adjustment, throughout cycle 1 — only from the 3rd cycle (2035+) does it move to five-yearly. The annex elsewhere refers to 2035 as *"período em que se encerra **o reconhecimento anual dos investimentos realizados**"* — the period in which annual recognition of investments made *ends*.

2. **20-F FY2025, SEC-filed 2026-04-29** (verified verbatim by me from EDGAR, CIK 1170858):
   > *"Changes of the tariff review equation for the first two cycles … with the inclusion of the Factor U and updates to the regulatory asset base ("RAB") … **In the first two cycles, the RAB will be updated annually.**"*
   > *"Adoption of a retroactive methodology for tariff recognition of investments (the tariff calculation will only incorporate the investments already made by us)."*

3. **The arithmetic proves it flowed through.** The court read the 6.11% Jan-2026 reajuste as "IPCA-only, zero real." **It was not.** IPCA 12m (BCB SGS 13522): Oct-25 **4.68%**, Nov-25 **4.46%**, Dec-25 **4.26%**. Against a 6.11% reajuste that is **≈ +1.4 to +1.8pp of REAL tariff growth** — consistent with an annual RAB roll-forward plus market update, net of Factors X/U/Q.

**Verdict on (a): red's item #3 — *"IPCA-only in-cycle reajustes (zero real); capex remunerated only at the 2029 RTO; at flat equity EV/EBITDA RISES every quarter"* — is REFUTED.** The remuneration lag is **~1 year, not ~3–5 years**, and cycle 1 is not a frozen box. The `rab_remuneration_lag_value_trap` KG candidate is built on this refuted mechanism and **SABESP is the wrong exemplar** — its contract has exactly the annual roll-forward the mechanism assumes away. Recommend the candidate be re-scoped or withdrawn before acceptance.

**What genuinely does constrain cycle 1 (the honest bear case, re-derived):**
- **WACC frozen at 11.91% real pre-tax (7.86% post-tax) until Jan-2030.** Anexo VIII 10.7, and Anexo V **7.7.3** verified verbatim: *"O cálculo do WACC será revisto a cada REVISÃO TARIFÁRIA PERIÓDICA e seu valor será mantido nos REAJUSTES anuais … **bem como no âmbito das REVISÕES EXTRAORDINÁRIAS**."* **Even a successful extraordinary revision cannot re-open the WACC.** This is the real in-cycle exposure — a fixed return in a moving rate environment — and it is *narrower and more precise* than the court's framing.
- **Factor U** is an annual tariff **reducer of up to 10%** tied to universalization targets (20-F, verified). Factors X and Q also deduct. These are what compress the RAB uplift toward inflation — the court's *observation* was directionally near-right for the wrong reason.
- **Ex-post recognition with hard filing cliffs**: asset valuation due 31 May; filed after 31 August, that year's investments are not incorporated at all.
- **The extraordinary revision is effectively bolted shut** — Anexo V 4.5.1 gates it on *"inequívoco comprometimento da solvência e da liquidez"* (an insolvency/covenant-acceleration test), not on capex or WACC; plus a 180-day notice bar and a 12-month pre-RTP blackout.

### (b) Branch values re-derived, weighted 93.5 / 6.5

The honest branch values come from **the equity's own revealed sensitivity**, not a hand-built DCF — Discriminator 2 gives a direct market measurement of exactly this spread. At P = R$23.79, p = 0.935:

| | full spread | V(Tarcísio) | V(Haddad) | collect if T wins | tail if H wins |
|---|---|---|---|---|---|
| point estimate | +7.9% (R$1.88) | R$23.91 ($4.60) | R$22.03 ($4.24) | **+R$0.12 / +0.51%** | **−R$1.76 / −7.39%** |
| 95% upper bound | +22.1% (R$5.26) | R$24.13 ($4.64) | R$18.87 ($3.63) | +R$0.34 / +1.44% | −R$4.92 / −20.66% |
| 95% lower bound | −6.3% | R$23.69 | R$25.19 | −R$0.10 | +R$1.40 |

**Weighted value at 93.5/6.5 = R$23.79 = spot, by construction.** Not a dodge — it *is* the finding: the market has already weighted these branches, using a weighting indistinguishable from the one the pitch proposes. **Edge vs $4.55 ADR / R$23.79 local ≈ 0.**

**The consensus-gap decomposition — the number to take away:**

| | |
|---|---|
| consensus R$34.01 vs spot R$23.79 | gap **R$10.22 (43% claimed upside)** |
| election explains (point estimate) | **R$0.12 — 1.2% of the gap** |
| election explains (95% upper bound) | R$0.34 — 3.3% of the gap |
| **non-election residual** | **R$10.10 — 98.8% of the gap** |

The pitch attributes the consensus-to-spot gap to the election. **At least 96.7% of it is something else.** Post-Discriminator-3(a), that something is *not* the court's remuneration-lag story either — it is the verified leverage build (net debt R$23bn → R$34.2bn), the −590bps adjusted margin, the frozen 11.91% WACC, and Factor U/X drag.

---

## TAIL-LOSS ARITHMETIC (for the ENTER-NOW branch, which I do not recommend)

The ADR tail exceeds the local tail: a PT win in São Paulo would plausibly carry a BRL move, compounding against a USD holder — **a second risk axis neither bench costed.**

| scenario | gap-down | $100k | $250k | $500k |
|---|---|---|---|---|
| equity point estimate | −7.4% | −$7,387 | −$18,466 | −$36,933 |
| equity 95% upper bound | −20.7% | −$20,664 | −$51,659 | −$103,318 |
| upper bound + 5% BRL | −24.6% | −$24,630 | −$61,576 | −$123,152 |
| upper bound + 8% BRL | −27.0% | −$27,010 | −$67,526 | −$135,052 |
| **gain if Tarcísio wins (point est.)** | **+0.51%** | **+$513** | **+$1,284** | **+$2,567** |

At $250k: risking **$18k–$68k to make $1.3k**, with no listed instrument available to hedge it.

---

## WHAT CHANGES THIS — AND WHAT DOES NOT

**Does not change it — retire these:**
- The election outcome. A Tarcísio win is worth **+0.5% (≤1.4%)** and is 93.5% priced, on a probability the polling says is fair. **Retire the `reopen_gates` entry "Tarcísio win WITH SBSP3 ≤ R$25"** — it would fire on a condition carrying no value, and SBSP3 is at R$23.79 *today*, already inside its price leg, for reasons unrelated to the election.
- Polymarket signal quality. It stands; it is simply not decision-relevant here.

**Would change it — the live axes now:**
- **Re-court the fundamental case on corrected facts.** The court's REJECT was 8/10 on a premise that is refuted. The disposition may well survive on the surviving facts (leverage build, margin, frozen WACC, Factor U drag) — but it has not been argued on them, and a verdict resting on a refuted mechanism should not stand unexamined.
- 3Q26 (~11/05): adj margin vs 58.3%, net debt vs R$38bn, and the R$403M reported-vs-adjusted EBITDA bridge.
- **New, quantifiable, and now the most interesting tripwire:** the Jan-2027 reajuste. The RAB roll-forward is annual and mechanical, so the real (ex-IPCA) component of that adjustment is a **direct, dated readout on how the RAB build is actually being remunerated** — and it is also the first tariff decision under the new governor, making it the regulatory-integrity signal *and* the RAB-compounder signal in one print. Watch the SABESP asset valuation filed by 31 May 2027 against the 31 Aug cliff.

---

## STANDING RECOMMENDATION

**No advance on the election gate; NO-DISCOUNT is the answer to the question asked.** Position FLAT into the ~11/05 print. The court's *disposition* (no entry today) is undisturbed; its *reasoning* requires correction, and the fundamental case should be re-courted on the verified record rather than treated as settled.

*No ledger, queue, or KG writes performed, per instruction.*

---
### METHOD LOG
- **Polymarket:** `gamma-api/events?id=421102`; `clob.polymarket.com/book`, `/prices-history` (110 daily pts); `data-api/trades` (500 trades, wallet-level aggregation).
- **Equity:** yfinance daily closes SBSP3.SA / SBS / SAPR11.SA / CSMG3.SA / EQTL3.SA / ^BVSP / EWZ / BRL=X; market model on a pre-event estimation window; placebo controls on out-of-state water concessionaires; leverage/winsorisation robustness; 10-event dated study with sign test.
- **Tape:** IBKR `get_price_snapshot` ctr 14996978 (ADR, live), 51283341 (SBSP3 statistics), and the Oct-16 option chain.
- **Primary documents (all fetched and read this session):** operative `2024/05/Anexo-V.pdf` (items 3.7, 4.5.1, 7.7.3 verified verbatim); `Anexo-VIII-Apostilado-1.pdf` (WACC 11.91%); signed contract Aug-2024 (92pp) vs Feb-2024 consultation draft (85pp); **20-F FY2025 from EDGAR** (CIK 1170858, acc. 0001292814-26-002681) — RAB-annual-update language verified verbatim.
- **Macro:** BCB SGS series 13522, IPCA 12m accumulated.
- **Election dating:** G1, CNN Brasil, Poder360, Diário Oficial da União, Paraná Pesquisas, pt.wikipedia poll tables. Three secondary headlines (02-19, 06-24, 07-03) are index-dated only and were **excluded** from the event study.
- Working files: `/private/tmp/claude-501/-Users-ajay-exalted-signalos/19c73007-514b-4a6d-93e3-bd50f8ad0892/scratchpad/` (`anexoV.txt`, `contrato.txt`, `f20f.txt`, `pm_join.csv`, `sbs_px_long.csv`).
