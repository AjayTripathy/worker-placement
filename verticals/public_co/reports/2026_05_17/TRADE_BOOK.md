# Signal OS — Tradeable Book Report

_Cutoff date: 2026-05-16 · Generated: 2026-05-17_

Companion to `data/_pair_trades/POSITION_SIZING.md` (the full 12-pair sized
sheet) and `data/_pair_trades/PAIR_TRADES.md` (the 15-pair emit list across
12 cohorts). This report focuses on **practical executability**: which
pairs you can actually open today, at what borrow cost, at what size.

## TL;DR — 5 cleanly executable pairs

| Tier | Pair | Comp | IBKR borrow (annl.) | Cap $ (long-leg) | Hedge ratio |
|---|---|---:|---:|---:|---:|
| 1 | **FCEL / LIN** | 1.00 | **0.68%** ⬇ | $4.72M | 3.22× |
| 2 | **IREN / EQIX** | 1.17 | **0.44%** | $31.85M | 4.24× |
| 2 | **AFRM / COF** | 0.67 | **0.25%** | $18.63M | 3.55× |
| 2 | **RDW / IRDM** | 0.71 | **0.42%** | $4.72M | 3.07× |
| 1 | AIRO / KTOS (caveat) | 0.75 | 1.10% ⬆ | $0.18M | 1.00×* |

The four "clean" pairs (FCEL, IREN, AFRM, RDW) are retail-tradeable, have
SHORTABLE classification, real beta data, and notional caps > $1M. AIRO is
technically shortable but only at tiny size ($0.18M cap) with expensive
borrow (1.10%) and a default hedge ratio (beta missing).

\* = default 1:1 hedge because IBKR beta data unavailable for AIRO.

---

## Borrow-rate snapshot (IBKR, 2026-05-15)

Source: iborrowdesk.com (public scrape of IBKR daily securities-lending
data). Fees are annualized %. "Available" is shares; multiply by short
price for $-availability.

| Ticker | Price | Fee % | 30d avg | 30d max | Trend | Avail (sh) | Status |
|---|---:|---:|---:|---:|---|---:|---|
| AFRM | $65.82 | 0.25% | 0.26% | 0.30% | stable | 2.3M | clean |
| CIFR | $20.33 | 0.25% | 0.32% | 0.42% | stable | 8.4M | clean |
| OUST | $34.86 | 0.27% | 0.28% | 0.38% | stable | 1.3M | clean |
| RDW  | $14.06 | 0.42% | 0.45% | 0.56% | stable | 6.6M | clean |
| AEVA | $20.48 | 0.43% | 0.54% | 0.66% | stable | 0.8M | clean |
| IREN | $52.94 | 0.44% | 0.40% | 0.88% | stable | 8.6M | clean |
| MVST | $1.42 | 0.48% | 0.45% | 0.55% | stable | 4.8M | sub-$5 |
| BLDP | $4.45 | 0.52% | 0.69% | 0.97% | stable | 6.0M | sub-$5 |
| FCEL | $21.36 | 0.68% ⬇ | 1.08% | 1.39% | stable | 5.0M | clean |
| SES  | $1.13 | 0.79% ⬆ | 0.63% | 2.00% | **rising** | 6.2M | sub-$5, fee rising |
| AIRO | $6.37 | 1.10% ⬆ | 1.29% | 1.58% | stable | 0.2M | tight inventory |
| KSCP | $2.95 | — | — | — | — | — | **not in IBKR universe (HTB)** |

**Key reads:**
- All 11 names ex-KSCP have current borrow under 1.5% annualized — well below the cost of running these as concentrated single-name shorts.
- **SES borrow is rising** (current 0.79% vs 30d avg 0.63%; 30d max touched 2.00%). If the framework's thesis is correct, this will likely keep tightening — front-running by other shorts.
- **FCEL borrow has eased** (current 0.68% vs 30d avg 1.08%) — possibly other shorts covered after the November 2024 reverse-split-then-redilute cycle played out.
- **AIRO inventory is tight** (only 200k shares available) — fee elevated and any meaningful institutional position could push it higher.
- **KSCP is genuinely HTB** — outside IBKR's lending universe entirely; would need specialty short-borrow desk access.

---

## Cleanly executable pairs (4)

### 1. FCEL / LIN — Hydrogen / fuel-cell (Tier 1, comp 1.00)

**Thesis:** product backlog collapse hidden by mechanical LTSA-module revenue + post-reverse-split redilution pattern.

**Evidence:**
- Product backlog $111M → $66M (-41% YoY) while reported revenue grew +41% YoY. Revenue growth is mechanical GGE LTSA module replacement (22 modules FY25 vs 6 FY24), not new commercial bookings.
- 1-for-30 reverse split Nov 2024 (611M → 20.4M shares), then 25.6M new ATM shares sold FY25 at avg $7.44 ($190.4M gross) + 1.6M more post-Oct-31. **Net share count is back above pre-split levels.**
- 10-K dedicates significant "Market Opportunity" to AI data-center power demand but discloses **zero** named hyperscaler contract, LOI, MOU, or pilot deployment.

**Execution:**
- **Shortability:** SHORTABLE (retail OK at $21.36)
- **IBKR borrow:** **0.68% annualized**, 5.0M shares available, trend stable, **easing** from 1.08% 30d avg
- **Hedge ratio:** **3.22×** (short β 2.38, long LIN β 0.74)
- **Notional cap (5% daily $vol):** $4.72M long-leg
- **Sizing recipe:** for every $1M long LIN, short ~$3.22M of FCEL. Conservative entry: 30% of cap = $1.4M long LIN / $4.5M short FCEL.
- **Annual borrow cost on $4.5M FCEL short:** ~$30,600.

### 2. IREN / EQIX — AI-DC / crypto pivot (Tier 2, comp 1.17)

**Thesis:** AI-DC pivot funded by $7.3B convertible cadence; Microsoft contract claimed but zero tranches delivered six months after signing.

**Evidence:**
- $9.7B Microsoft GPU services contract claimed (Nov 2 2025, dedicated at Childress); **zero tranches delivered/accepted** as of Mar 31 2026; no Microsoft consideration in IREN's RPO.
- **$7.3B in convertible debt over 17 months** ($440M Dec-2024 + $550M Jun-2025 + $1.0B Oct-2025 + $2.3B Dec-2025 + $3.0B May-2026) + $635M ATM + $3.6B GS/JPM facility. Funding cadence consistent with racing to fund capex commitment that exceeds operating cash flow capacity.
- **Note:** the MSFT 10-K silence portion of this thesis was downgraded in the recent rescoring (Microsoft would not necessarily disclose a $9.7B/5y contract at 0.8% of revenue). The remaining self-disclosed evidence (zero tranches + funding cadence) is what supports MODERATE status. Was originally Tier 1.

**Execution:**
- **Shortability:** SHORTABLE
- **IBKR borrow:** **0.44% annualized**, 8.6M shares available, stable
- **Hedge ratio:** **4.24×** (short β 4.20, long EQIX β 0.99) — note IREN β is jumpy and may not hold post-crypto-cycle
- **Notional cap:** $31.85M long-leg (binding leg: long EQIX, not short IREN)
- **Sizing recipe:** for every $1M long EQIX, short ~$4.24M of IREN. Conservative entry: 30% of cap = $9.5M long EQIX / $40M short IREN.
- **Annual borrow cost on $40M IREN short:** ~$176,000.

### 3. AFRM / COF — Fintech lending / BNPL (Tier 2, comp 0.67)

**Thesis:** disclosure-quality issues at AFRM around bank-partner credit performance + counterparty silence at Amazon/Shopify on the framework's flagship customer-relationships claim.

**Evidence:**
- Celtic Bank (named partner, originates "substantially all loans"): FDIC Call Report shows **6.22% charge-off rate, 26.86% nonaccrual rate, +38.5% YoY consumer loan growth** as of Q4 2025. Elevated relative to peer fintech bank partners (SoFi Bank: 0.08% / 0.10% / +42.1%).
- Amazon (CIK 0001018724) and Shopify (CIK 0001594805) — both named as material partners with warrants outstanding — return **0 hits** for "Affirm" in their 10-K filings within the cutoff window.
- COF is the cleanest in-cohort long: composite 0.25, prime credit-card franchise, Capital One Securities CRD 44158 registration confirmed via FINRA BrokerCheck.

**Execution:**
- **Shortability:** SHORTABLE (retail OK at $65.82)
- **IBKR borrow:** **0.25% annualized**, 2.3M shares available, stable (cheapest in book)
- **Hedge ratio:** **3.55×** (short β 3.69, long COF β 1.04)
- **Notional cap:** $18.63M long-leg
- **Sizing recipe:** for every $1M long COF, short ~$3.55M of AFRM. Conservative entry: 30% of cap = $5.6M long COF / $20M short AFRM.
- **Annual borrow cost on $20M AFRM short:** ~$50,000.

### 4. RDW / IRDM — Space / satcom (Tier 2, comp 0.71)

**Thesis:** backlog conversion + cash burn divergence at Redwire vs IRDM's stable cash-generative satcom franchise.

**Evidence:**
- 1 SEVERE + 3 MODERATE flag pattern in scoring matrix. Specific findings include backlog-to-revenue conversion deterioration and burn-rate divergence from announced milestones.
- IRDM long is genuinely clean (composite 0.12) — mature commodity satcom not relying on aggressive growth claims.

**Execution:**
- **Shortability:** SHORTABLE
- **IBKR borrow:** **0.42% annualized**, 6.6M shares available, stable
- **Hedge ratio:** **3.07×**
- **Notional cap:** $4.72M long-leg
- **Sizing recipe:** for every $1M long IRDM, short ~$3.07M of RDW. Conservative entry: 30% of cap = $1.4M long IRDM / $4.3M short RDW.
- **Annual borrow cost on $4.3M RDW short:** ~$18,000.

---

## AIRO / KTOS — Defense-tech (Tier 1, comp 0.75) — **size carefully**

**Thesis:** stock-for-services-as-distress fingerprint across multiple AIRO subsidiaries.

**Evidence:**
- Stock-for-services pattern across Jaunt, Aspen, Coastal Defense, Agile Defense, AIRO Drone subsidiaries. Dangroup gets 20% of Sky-Watch EBITDA ($5.7M expensed 2025) → diluted to 5% fully-diluted at IPO.
- Material weakness in ICFR.

**Execution caveats:**
- **Shortability:** SHORTABLE in principle but daily $-volume is only $3.55M → 5% cap = $0.18M.
- **IBKR borrow:** **1.10% annualized**, only **200k shares available** (tightest in book), 1.58% 30d max.
- **Hedge ratio:** default 1.00× (no IBKR beta data) — likely too low; AIRO is much higher-beta than KTOS.
- Practical implication: this is a $50-100k single-name position at best, not a sizeable trade. Carry cost on $100k short ≈ $1,100/yr.

---

## Institutional-only (sub-$5 retail-restricted) — 3 pairs

These are Tier 1 by composite but the short legs trade under $5, so retail
brokers prohibit short. Institutional accounts with prime-broker borrow
have access; borrow costs themselves are cheap (<0.8%).

### MVST / ALB (Tier 1, 1.57)
- **Short:** MVST at $1.42, BORROW_AT_PREMIUM tier (sub-$5)
- **Borrow:** **0.48% / 4.8M sh available / stable**
- **Hedge:** 2.61× (β short 3.50, long ALB β 1.34)
- **Cap:** $0.31M long-leg
- **Top evidence:** EPA FRS has 0 Microvast facilities for TN despite 577k sq ft claimed; only $499,972 cumulative DOE assistance vs claimed major LPO; $62M cash trapped in China/Europe subs; Q2/Q3 2024 restatement + material weakness in ICFR. **Highest-conviction Tier 1 trade in the book.**
- **Long-side concentration warning:** ALB also longed against SES — don't stack.

### SES / ALB (Tier 1, 1.50)
- **Short:** SES at $1.13, BORROW_AT_PREMIUM tier (sub-$5)
- **Borrow:** **0.79% / 6.2M sh available / RISING** (was 0.63% 30d avg; touched 2.00% max). Worth watching — if borrow keeps climbing, other shorts are crowding in.
- **Hedge:** 0.62× (β short 0.83, long ALB β 1.34)
- **Cap:** $0.52M long-leg
- **Top evidence:** Hyundai B-sample JDA concluded Dec 2025 without C-sample advancement; pivoted from Li-Metal manufacturing to AI/Molecular Universe; $0 OEM-funded R&D vs $8.6M PY; EPA FRS facility still registered under legacy "SolidEnergy" name.
- **Long-side concentration warning:** ALB also longed against MVST — pick one or split allocation.

### BLDP / LIN (Tier 1, 1.22)
- **Short:** BLDP at $4.45, BORROW_AT_PREMIUM tier (sub-$5 by a few cents)
- **Borrow:** **0.52% / 6.0M sh available / stable** (eased from 0.69% 30d avg)
- **Hedge:** 2.68× (β short 1.98, long LIN β 0.74)
- **Cap:** $1.07M long-leg
- **Top evidence:** Weichai (largest strategic investor + customer) sold shares + nominees resigned May 2026; leadership cluster (CEO Jul 2025, COO Apr 2026); order book is fragmented small-MW (1.5, 5, 6.4, 8, 20, 50) with no hyperscaler-grade contract.
- **Long-side concentration warning:** LIN also longed against FCEL.

---

## Pairs not currently executable (4)

| Pair | Composite | Why excluded |
|---|---:|---|
| KSCP / TER | 1.44 | KSCP not in IBKR lending universe (HTB); only $0.08M cap even if found. |
| CIFR / EQIX | 0.83 | DA cache stale for CIFR (missing avg_volume/market_cap/beta); hedge ratio defaults to 1:1, can't size. Borrow itself is 0.25% — refresh DA data and revisit. |
| AEVA / INVZ | 0.75 | INVZ long-leg has no liquidity/beta data (sub-$1 stock, likely uninvestable as hedge). Borrow on AEVA is fine (0.43%); the issue is the hedge instrument. |
| OUST / INVZ | 0.67 | Same INVZ problem. |

**For CIFR/EQIX specifically:** the only blocker is data freshness — composite 0.83 is mid-Tier-2, borrow is cheap (0.25%), short price is fine ($20.33). Worth refreshing the Discovery-Advantage cache and re-running position_sizing.

---

## Book-level sizing — clean 4-pair basket

Sized at 30% of the smallest notional cap in each pair (conservative entry):

| Long $ | Long | Short $ | Short | Annual borrow $ | Net $ |
|---:|---|---:|---|---:|---:|
| $1.4M | LIN | $4.5M | FCEL | $30,600 | -$3.1M |
| $9.5M | EQIX | $40.3M | IREN | $177,000 | -$30.8M |
| $5.6M | COF | $19.9M | AFRM | $49,750 | -$14.3M |
| $1.4M | IRDM | $4.3M | RDW | $18,100 | -$2.9M |
| **$17.9M** | | **$69.0M** | | **$275,450** | **-$51.1M** |

**Annual book carry: ~$275k on $69M short notional = ~0.40% blended borrow.**

**Net exposure: $51M net-short by dollars,** but designed to be roughly
beta-neutral when β-weighted (assuming IREN's 4.20 beta is real — caveat:
that's a momentum-cycle artifact and may not hold).

**Tier mix in this basket:** 1 Tier 1 (FCEL) + 3 Tier 2 (IREN/AFRM/RDW).
The basket leans toward **disclosure-quality re-rating bets** rather than
hard-contradiction shorts. Expected catalysts:
- Quarterly disclosures showing claimed milestones haven't materialized
- Continued funding cadence (more dilution at IREN; more ATM at FCEL)
- Counterparty silence persists past expected disclosure windows

**Holding period guidance:** Tier 2 disclosure-quality trades typically
need 6-12 months for the multiple compression to play out. Tier 1 (FCEL
here) often re-rates on a specific catalyst (next earnings, next backlog
disclosure). Set an exit on **+20% adverse move** or **6 months without
confirming evidence** (whichever first), per the framework's
falsification window.

---

## Adding the institutional pairs — full 7-pair book

If you have prime-broker borrow access for sub-$5 names, add MVST, SES,
BLDP at small size (their notional caps are $0.31-1.07M long-leg). The
hard limit is daily volume on the short leg, not borrow inventory:

| Long $ | Long | Short $ | Short | Annual borrow $ |
|---:|---|---:|---|---:|
| _existing 4-pair basket above_ | | | | $275,450 |
| $0.15M | ALB | $0.39M | MVST | $1,870 |
| $0.30M | ALB | $0.19M | SES | $1,500 |
| $0.50M | LIN | $1.34M | BLDP | $6,970 |
| **$18.9M** | | **$70.9M** | | **$285,790** |

The institutional adds bring the highest-conviction Tier 1 names (MVST,
SES) into the book at small size. Even at tiny notional, they capture
the strongest framework signals (EPA FRS absence, USAspending DOE
absence, Hyundai stage-ladder, Weichai exit).

**Long-side concentration:** ALB now appears 2× (MVST + SES), LIN
appears 2× (FCEL + BLDP). Cap each pair's long allocation to 1/N of the
ALB / LIN total exposure.

---

## Caveats

1. **IBKR borrow ≠ all broker borrow.** Rates and availability differ across prime brokers and at retail intermediaries. The 0.25-1.10% range here is IBKR-indicative; institutional Prime Brokerage rates are often lower for size, retail rates at other brokers can be higher. Always cross-check at your actual execution venue.
2. **Borrow can spike on news.** AIRO and SES already show elevated/rising fees. A material adverse disclosure will spike borrow further — but typically the price moves first. If the trade is working, rising borrow is a feature, not a bug.
3. **Composite scores subject to refinement.** Recent rescoring softened IREN, FCEL, BLDP, SES, and several legacy SPACs after applying a materiality caveat to Heuristic 7. The position_sizing here reflects the current scores; if the framework's heuristics get further refined (especially around small-vs-large counterparty asymmetry), composites can shift.
4. **Hedge ratio for IREN is jumpy.** β=4.20 reflects the crypto-cycle equity component; if IREN's funding cadence is reduced or the cycle turns, the effective β may compress to ~2-3 and the hedge will over-cover. Watch correlation.
5. **Tier 2 trades are softer.** The MOD-pattern composite reflects disclosure-quality concerns rather than factual contradictions. Catalyst path is multiple-compression, not restatement. Holding period 6-12 months; basket sizing preferred over concentrated single-name conviction.
6. **Framework falsification window is 12 months.** Slow-bleeding shorts that move <50% in either direction stay non-falsified. Recommended exit rule: close on +20% adverse move OR 6 months without confirming evidence.

---

## Reproduction

```bash
# Pull fresh IBKR borrow rates
python3 -c "from verticals.public_co.m_sources.iborrow import get_borrow_rate; \
            import json; print(json.dumps(get_borrow_rate('IREN'), indent=2))"

# Refresh position sizing (after re-scoring)
python3 -m verticals.public_co.deterministic_scorer UPST AFRM OPEN SOFI COF
python3 -m verticals.public_co.fintech_aggregate
python3 -m verticals.public_co.pair_trades
python3 -m verticals.public_co.position_sizing

# All inputs are committed to git:
#   verticals/public_co/data/_pair_trades/{pairs.json,position_sizing.json,borrow_rates.json}
#   verticals/public_co/data/_local/<TK>.{plan,queries,scores}.json
```
