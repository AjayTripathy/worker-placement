# Forward-test deployment picks — 2026-05-25

**Cutoff date**: 2026-05-25 (today). All scoring done with strict pre-cutoff blinding.
**Measurement dates**: 2027-05-25 (12m primary), 2028-05-25 (24m secondary).
**Universe**: 60-name random sample from 193 SP600 distressed names (drawdown ≤ -25% at cutoff). 59 scored (ASGN excluded — no CIK).

## Deployment rules applied

Based on Tier 1+3 backtest validation (n=122):

| group | filter | historical performance | action |
|---|---|---|---|
| **HIGH-CONV SHORT** | composite ≥ 1.30 AND form4 SEVERE | 75% catastrophe-precision (small N=8) | Buy 12m OTM puts at -25% strike |
| **MED-CONV SHORT** | composite 0.50-1.29 AND form4 SEVERE | Mixed; weaker signal | Light hedge / smaller put |
| **DISTRESSED LONG** | composite ≥ 0.50 AND insider-buy AND no external-M SEVERE | +56.6% mean, 28% big-winner rate at 12-24m | Long position, 2-3% sized |
| **CONSERVATIVE LONG** | composite < 0.50 AND insider-buy | Not historically tested but lower risk | Long position |
| **PASS** | rest | n/a | No deployment |

**Important caveat**: The forward-test agents elevated form4 SEVERE more aggressively than historical (~60% hit rate vs ~7% historical). Treat MED-CONV SHORTs as much less reliable than the count suggests. The HIGH-CONV bucket (composite ≥ 1.30 floor) is closer to historical specification.

## Group A: HIGH-CONVICTION SHORT (n=18)

Form 4 SEVERE finding + composite ≥ 1.30. Buy 12m OTM puts at -25% strike. Sized ~1-2% portfolio each (defined-risk).

| ticker | comp | drawdown | price | sector | key form4 finding |
|---|---:|---:|---:|---|---|
| MGPI | 2.00 | -43.9% | $18.05 | Consumer Defensive | Class actions name CFO; ex-Chair Seaberg $65M+ lifetime selling; CEO Francis 0 P-buys |
| CCOI | 1.89 | -64.6% | $18.16 | Comm Services | CEO margin-call forced liquidation $82.5M Aug 2025; 98% dividend cut |
| MOH | 1.78 | -40.2% | $184.14 | Healthcare | CEO Zubretsky $28M sale 7 days after "Reaffirms Guidance", before Jul 2025 cut; new class action surgically brackets sale window |
| AEO | 1.75 | -40.7% | $16.53 | Consumer Cyclical | CEO Schottenstein $26.8M 8-10 days after bullish Jan 2026 8-K; 0 P-buys in 275 Form 4s |
| SDGR | 1.60 | -50.2% | $13.30 | Healthcare | 0 P-buys / 28 sells; CEO sold $1M at $12 5 weeks pre-cutoff; CCO dep'd 1 wk pre-cutoff |
| ADMA | 1.56 | -62.3% | $8.24 | Healthcare | CEO 10b5-1 starts on 10-K filing day; channel-stuffing self-refutation; CFO retired |
| HRMY | 1.56 | -25.6% | $30.15 | Healthcare | 0 P-buys / 47 Form 4s; ANDA settlement reverse-payments expensed as IPR&D |
| SLVM | 1.56 | -29.6% | $38.10 | Basic Materials | 0 P-buys / 158 Form 4s; 3 officers sell in 13-day window post-10-K |
| AMPH | 1.50 | -40.2% | $18.41 | Healthcare | 0 P-buys during drawdown; FDA OAI at IMS facility not disclosed in 10-K |
| CBRL | 1.44 | -53.9% | $32.39 | Consumer Cyclical | 0 P-buys / 448 Form 4s; smart-money exited; 80% div cut, $150M convert maturity |
| VYX | 1.44 | -55.0% | $6.59 | Technology | CEO gifted ENTIRE common position 6 days post Q1 10-Q, 13 days pre-cutoff |
| CCS | 1.40 | -30.3% | $51.95 | Real Estate | Exec Chairman $7.25M sold 15 days post Q4 print, 69 days before 2026 guide cut |
| SKYW | 1.40 | -31.4% | $84.82 | Industrials | 0 P-buys / 33 Form 4s; $16M C-suite sales, clustered post-earnings |
| BFAM | 1.33 | -48.5% | $67.75 | Consumer Cyclical | 0 P-buys / 91 Form 4s; CEO/CFO/Chair sold $11M within 7-day cluster pre-decline |
| GPI | 1.33 | -33.0% | $326.18 | Consumer Cyclical | 0 P-buys / 72 Form 4s; CFO+director sold $9.4M pre-JLR cyber disclosure |
| PBH | 1.33 | -44.6% | $48.00 | Healthcare | 0 P-buys / 96 Form 4s; FDA Class I recalls not disclosed in 10-K |
| BL | 1.30 | -50.9% | $28.90 | Technology | 0.08 P:S ratio across 109 Form 4s; activist proxy contest; CEO/founder never bought |
| MHK | 1.30 | -26.7% | $102.40 | Consumer Cyclical | 0 P-buys / 99 Form 4s; Lorberbaum family $16.5M sold; $257M trapped Russia cash |

## Group A2: MEDIUM-CONVICTION SHORT (n=16) — light hedge

| ticker | comp | drawdown | sector |
|---|---:|---:|---|
| PLMR | 1.25 | -35.2% | Financial Services |
| VRTS | 1.22 | -28.9% | Financial Services |
| CORT | 1.20 | -33.3% | Healthcare |
| DORM | 1.11 | -29.0% | Consumer Cyclical |
| AMWD | 1.10 | -44.1% | Consumer Cyclical |
| CALM | 1.10 | -32.1% | Consumer Defensive |
| CWK | 1.10 | -25.1% | Real Estate |
| EPC | 1.10 | -35.3% | Consumer Defensive |
| ASTE | 1.00 | -25.1% | Industrials |
| CNMD | 1.00 | -36.8% | Healthcare |
| STEP | 1.00 | -29.1% | Financial Services |
| WAY | 1.00 | -52.5% | Healthcare |
| CLSK | 0.89 | -31.2% | Financial Services |
| LNN | 0.70 | -25.5% | Industrials |
| EAT | 0.67 | -25.3% | Consumer Cyclical |
| CNR | 0.62 | -25.8% | Energy |

## Group B: DISTRESSED LONG (n=17) — asymmetric upside

Framework correctly flagged distress, but insiders are putting personal capital to work with no external-M corroboration of the worst-case interpretation. Sized 2-3% each.

| ticker | comp | drawdown | price | sector | key insider-buy finding |
|---|---:|---:|---:|---|---|
| KSS | 1.50 | -46.3% | $13.06 | Consumer Cyclical | (caution — composite high, watch for clarity) |
| SMPL | 1.50 | -66.0% | $11.86 | Consumer Defensive | Kilts $991K Apr 2026 post-impairment; Daley $118K |
| TTGT | 1.38 | -44.6% | $4.82 | Technology | CEO Nugent + Director Flaschen P-buys @ $5.85-5.97 Sep 2025 |
| TMDX | 1.25 | -54.2% | $68.93 | Healthcare | CEO Hassanein $3.0M (2 P-buys at $114-117.5) post-short report |
| TRIP | 1.20 | -47.3% | $10.08 | Consumer Cyclical | (mixed — has Insider-buy mention but limited) |
| XRX | 1.20 | -54.8% | $2.90 | Technology | CEO $99K, CFO $44K, COO $109K, Director $110K — all bought May 2025 at $4.48 |
| USPH | 1.10 | -32.2% | $61.96 | Healthcare | Director Gilmartin $276K Nov 2025 + $172K Sep 2024 |
| FMC | 1.00 | -69.7% | $13.11 | Basic Materials | 3 directors $482K post-10-K (Barry $250K, Raines, Davidson) |
| GO | 0.90 | -57.0% | $8.02 | Consumer Defensive | CEO Potter $2.41M + Lead Director $2.82M + Chairman $1.64M = $7.92M cluster |
| VRRM | 0.90 | -47.4% | $13.49 | Technology | (caution — only mention is absence-of-buying; may be misclassified) |
| KMPR | 0.89 | -52.8% | $29.71 | Financial Services | Director Parker $920K Nov 2025 + 5-insider Aug cluster = $1.5M |
| DEI | 0.75 | -28.8% | $11.46 | Real Estate | CEO Kaplan $998K Feb 2026 + EVP $492K + Director $592K = $2.08M |
| QDEL | 0.67 | -66.5% | $11.86 | Healthcare | CEO Blaser $750K + CFO $304K + 4 directors = $1.61M, 10 P-buys |
| MNRO | 0.60 | -28.8% | $16.75 | Consumer Cyclical | CEO Fitzsimmons $502K Feb 2026 + Icahn $84.7M 13D stake |
| SCVL | 0.60 | -34.0% | $16.66 | Consumer Cyclical | CFO Jackson $500K Apr 2026 post-10-K + founder family $19M Dec 2024 |
| ABG | 0.56 | -29.4% | $187.72 | Consumer Cyclical | CEO Hult $1.03M + Director $130K + Abrams Capital $10.6M = 11.6× P:S |
| OI | 0.56 | -46.9% | $8.83 | Consumer Cyclical | CEO Hardie + CFO + Chairman + 4 others = 11 P-buys, May 8-15 2026 cluster |

## Group B2: CONSERVATIVE LONG (n=6) — solid long

Framework doesn't see distress AND insiders are buying. Lower asymmetric upside than Group B but safer.

| ticker | comp | drawdown | price | sector | key buy |
|---|---:|---:|---:|---|---|
| ALG | 0.44 | -35.1% | $150.02 | Industrials | New CEO Hureau 5 P-buys $250K personal cash (~26% of base salary) |
| CVCO | 0.40 | -27.0% | $509.17 | Consumer Cyclical | CEO Boor's FIRST-EVER P-buy $495K + 2 directors |
| LYFT | 0.40 | -43.4% | $13.90 | Technology | CEO Risher 3 P-buys $299K scaling into drawdown |
| NSP | 0.40 | -47.5% | $32.09 | Industrials | CEO Sarvadi $7.56M open-market + CFO + GC + Director = 14.8:1 buy:sell |
| AMTM | 0.30 | -38.1% | $23.23 | Industrials | Exec Chair Demetriou $2.08M + Director $98K |
| PRAA | 0.11 | -34.1% | $14.64 | Financial Services | Director Olsen $711K (3 P-buys, latest 3 days post-impairment) |

## Group C: PASS (n=2)

| ticker | comp | drawdown | reason |
|---|---:|---:|---|
| AZTA | 1.44 | -50.8% | High composite but no clear form4-SEVERE pattern, and no insider buying |
| DFIN | 0.50 | -40.5% | Borderline composite, no insider buying signal |

## How to deploy

**Forecast cost**: 35 SHORTS × ~$1-2 of puts each = small premium outlay. 23 LONGS × $position-size.

**Tracking**:
- Lock in prices at market open 2026-05-26
- Forward measurement: 2027-05-25 (12m) for catastrophe-recall test
- Secondary measurement: 2028-05-25 (24m) for full asymmetric-upside test
- Re-run framework Q4 2026 / Q1 2027 to update positions if any have changed materially

**Critical reminders**:
- This is a SMALL forward sample. Even with our backtest validation, a single 12m window could see noisy results.
- The form4 SEVERE bucket here is much larger than historical (60% vs 7%) — agents were more aggressive in this run. Group A historical precision was on a much tighter subset.
- Composite scores are agent-self-reported and will be deterministically recomputed by synthesize-style scripts before formal measurement. Re-tier as needed.
- DO NOT add fundamentals overrides to these picks. The whole point of forward-testing is to measure what the framework alone produces.

## Files

- `forward_test_set.json` — 60-name universe
- `forward_agent_manifest.json` — blinded manifest with pre-cutoff fields
- `scores/pilot_*.json` — 59 individual pilot scores
- `forward_test_picks_v2.json` — structured pick list
- `AGENT_PROMPT.md` — prompt template used
- `apply_rules_v2.py` — rule application script
