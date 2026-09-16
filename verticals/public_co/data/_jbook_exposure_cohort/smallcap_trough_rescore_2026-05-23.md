# Smallcap-Trough Rescore — 2026-05-23

_Corpus: 750 programs (181 OP-5 across 8 services: SOCOM + Army Active/NG/Reserve + Navy/Reserve + USMC/Reserve)._
_Universe: 11 cohort members with mkt cap ≤ $10B AND drawdown ≥ 30% from 52w high._
_Cutoff: 2026-05-23 close._

## DISCLAIMER

Algorithmic research output, not investment, fiduciary, or tax advice. The author is **not** a fiduciary or licensed advisor. Framework composite scores measure *claim verifiability* against M-sources at a point in time; they are not buy/sell recommendations. Trough proximity is a price-action observation, not a guarantee of mean reversion. Position decisions are the reader's responsibility.

## Method

For each smallcap-trough name:
1. Pull existing framework composite from the most recent `.jbook.scores.json` LLM-subagent run
2. Apply build_forward_test tier rule: LONG if composite ≤ 0.20, SHORT if ≥ 0.50, else NEUTRAL
3. Compute drawdown from 52w high and proximity to 52w low
4. Cross-reference against the expanded 181-SAG OP-5 corpus for any newly-resolvable claims
5. Look for **asymmetric setups** — LONG-tier composite AND deep trough AND fresh trough proximity

## The 11 smallcap troughs at a glance

| Ticker | Class | Mkt$B | Price | 52wLo | Drawdown | Above lo | Tier | Composite | n claims (Sev/Mod/Red/Unv) |
|---|---|---:|---:|---:|---:|---:|---|---:|---|
| AIRO | MICRO | 0.2 | $6.56 | $5.85 | −78.8% | +12% | SHORT | 0.667 | 0/2/0/5 of 8 |
| ARQQ | SMALL | 0.3 | $17.49 | $11.78 | −70.0% | +48% | SHORT | 1.167 | 2/0/1/2 of 8 |
| AVAV | MID | 8.8 | $174.23 | $158.00 | −57.5% | +10% | SHORT | 0.571 | 1/2/0/3 of 10 |
| RGTI | MID | 8.8 | $26.42 | $10.79 | −53.1% | +145% | **LONG** | 0.200 | 0/1/0/4 of 9 |
| BBAI | MID | 2.0 | $4.18 | $3.04 | −53.1% | +37% | SHORT | 0.857 | 1/4/0/3 of 10 |
| QUBT | MID | 2.8 | $12.31 | $6.31 | −50.0% | +95% | SHORT | 1.286 | 1/1/2/2 of 9 |
| RCAT | SMALL | 1.4 | $9.41 | $5.95 | −45.8% | +58% | SHORT | 0.600 | 1/1/0/3 of 8 |
| PSN | MID | 5.7 | $53.71 | $48.74 | −39.8% | +10% | NEUTRAL | 0.333 | 0/2/0/4 of 10 |
| BAH | MID | 9.4 | $78.68 | $71.59 | −39.1% | +10% | NEUTRAL | 0.286 | 0/2/0/5 of 12 |
| KBR | MID | 4.2 | $33.46 | $30.06 | −37.7% | +11% | SHORT | 0.667 | 0/1/1/5 of 11 |
| CDRE | SMALL | 1.3 | $30.31 | $27.38 | −34.2% | +11% | **LONG** | 0.000 | 0/0/0/3 of 10 |

## The two asymmetric long candidates

### 🎯 CDRE — Cadre Holdings ($1.3B, SMALL, −34.2% from high, +11% above 52w low)

**Cleanest setup in the cohort.** Composite 0.000 (no MODERATE / SEVERE / RED flags across 10 scored claims; 7 PASS + 3 UNVERIFIABLE). At a fresh trough — only 11% above 52w low.

What the framework verified:
- Tactical / law-enforcement equipment franchise (body armor, holsters, ballistic helmets) — confirmed via usaspending DoD obligations
- Acquisition-led growth (Alpha Safety, Zircaloy, Cadre-NSA) — confirmed via SEC filings
- International growth narrative — corroborated

What the framework couldn't verify (UNVERIFIABLE):
- NNSA pit-production demand thesis (DOE budget out of J-Book scope)
- DoE EM remediation pipeline (DOE budget out of scope)
- Zircaloy UK-centric acquisition US-federal footprint (claim ambiguous)

The UNVERIFIABLE claims aren't negative signals — they're J-Book-scope limitations. The actual scored evidence is unblemished. Asymmetric setup: at the price low with a clean framework print.

### ⚠️ RGTI — Rigetti Computing ($8.8B, MID, −53.1% from high BUT +145% above 52w low)

Composite 0.200 puts it at the LONG threshold. But trough proximity is **misleading** — the price is already +145% above the 52w low, so the trough already mean-reverted. This is *not* a fresh trough setup; the run-from-trough has already happened.

**Verdict: not asymmetric at this price.** Wait for a renewed pullback toward ≤$15 (would put it +40% off low, asymmetric again). Or use as a smaller hold.

## The trough-but-SHORT names (caution against contrarian longs)

These look "cheap" on price but the framework says no. A −78% drawdown isn't an asymmetric long if fundamentals are correctly bearish:

- **QUBT** (composite 1.286, 1 SEV + 2 RED) — worst signal in cohort. Selling cheap.
- **ARQQ** (1.167, 2 SEV + 1 RED) — quantum-crypto narrative, framework finds it
- **BBAI** (0.857) — AI/autonomy narrative weak
- **KBR** (0.667) — services prime with named-PE NOT_FOUND on Sentinel/hypersonics — corpus gap, not necessarily bear, but framework can't validate the bull
- **AIRO** (0.667) — micro-cap drone, deep -78.8% but framework validates the bearishness
- **RCAT** (0.600) — drone SRR PoR claim challenged by framework
- **AVAV** (0.571) — claim quality issue

## NEUTRAL-at-trough — watch list

- **BAH** (composite 0.286 — close to LONG threshold of 0.20) — services prime at fresh trough (+10% above 52w low). Has 5 UNVERIFIABLE claims (Intel customer mix, JADC2, Cyber Mission Force) — if any resolved to PASS via deeper M-source ingest, BAH could cross into LONG. Worth watching.
- **PSN** (0.333) — Parsons. NEUTRAL; not at fresh trough behaviorally.

## What the expanded OP-5 corpus changed

Material delta on the smallcap-trough subset is **near-zero**. Only **BAH** picked up one new OP-5 hit (Cyber Mission Force → Army Cyberspace Operations SAG FUNDED_SHRINKING, but BAH's C5 claim was "cohort-attributed, NOT named in 10-K" so the underlying UNVERIFIABLE flag stands).

The OP-5 expansion benefits services primes whose claims reference SAG-named work (VVX LOGCAP) — but the smallcap troughs in this universe are quantum / drone / micro-cap names whose claims reference specific PE numbers and program names that aren't OP-5 SAGs. Their thesis depends on R-2 RDT&E and P-40 procurement signals, which the corpus already covered.

## Recommendation

**Single clean asymmetric long: CDRE.** Small, at trough (+11% above 52w low), composite 0.000, zero negative claims.

**BAH on watch** — composite at 0.286 is borderline-LONG and at +10% above 52w low. A 10K refresh or additional M-source ingest that converts 1-2 UNVERIFIABLE claims to PASS would push it across the 0.20 LONG threshold.

**Do not contrarian-long** the deep-drawdown SHORT-tier names. The framework is corroborating the price action.

## Files

- `cohort_prices_2026-05-23.json` — full cohort prices + market caps + drawdowns
- `cohort_rescore_181sag_2026-05-23.json` — machine-readable rescore against the 181-SAG corpus
- `smallcap_trough_analysis_2026-05-23.json` — this report's underlying data
