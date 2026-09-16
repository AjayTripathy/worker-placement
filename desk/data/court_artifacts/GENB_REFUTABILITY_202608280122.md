## CAUSE-CHECK FIRST — the premise doesn't survive the tape

The `1d -21%` trigger is a **round trip of a two-day spike into a dated share unlock**, not damage.

| Date | Close | Chg | Vol | What happened |
|---|---|---|---|---|
| Aug 21 | 16.12 | +0.81% | 0.83M | baseline |
| Aug 24 | 17.72 | +9.93% | 2.50M | run-up into ERS |
| Aug 25 | 20.38 | **+15.01%** | 4.67M | ERS posters leak; ATH, intraday 22.67 |
| Aug 26 | 16.14 | **−20.80%** | 3.83M | **181-day IPO lock-up expires** + 8-K furnishes final posters |
| Aug 27 | 15.77 | −2.29% | 2.85M | — |

Four things fall out:

1. **The −20.8% bar is Aug 26, not Aug 27** (Aug 27 was −2.29%). The `d1` in the event record is the prior session's move.
2. **Net move Aug 21 → Aug 27: −2.2%.** The stock is flat. That is exactly what `excess_5d = +0.74%` was telling us, and it is the single fact that voids the dislocation reading.
3. **Aug 26 was the lock-up expiry.** IPO Feb 26, 2026 at $16, 25M shares / $400M; 181-day lock-up ended Aug 26. With 128,269,428 shares outstanding, roughly **103M shares — ~4× the float — became free that morning.** Dated, mechanical, disclosed in the S-1.
4. **Nothing negative was disclosed.** The leaked posters are Phase 1/1b PK-PD (positive: ~89–100 day half-life, sustained biomarker suppression ≥6 months, ~20× tezepelumab affinity) plus a *trial-design* poster for SOLAIRIA-1/2. Zero efficacy endpoints. The market's first read was +15%.

**Cohort integrity failure:** `knowledge_graph/cohorts.json` does not exist in the repo — COHORT and NARRATIVE resolve to literal `?`. With a single member there is also no cohort median, so the requested dispersion ranking is undefined by construction. I triaged against a reconstructed narrative ("the leak revealed impaired GB-0895 / the company is damaged") rather than invent a cohort.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| GENB | **DAMAGE-ABSENT** (event is an artifact) | Cash+marketable securities & stated runway; SOLAIRIA regulatory/enrollment breadth | $457.4M cash+MS at 6/30/26 (vs $516.6M at 3/31); runway "into the first half of 2028"; SOLAIRIA cleared in **33 of a planned 42 countries**, recruiting across all six global regions ([Q2'26 release, 8/6/26](https://generatebiomedicines.com/wp-content/uploads/2026/08/Generate-Biomedicines-Earnings-Release-Q22026.pdf)) | Q3 print **~2026-11-05, UNCONFIRMED** (yfinance-derived; no company PR names it) | No debt; total liabilities $105.6M are mostly leases. Q2 net loss $67.3M, 6-mo OCF −$138.3M (~$23M/mo). Efficacy metric (AAER) is **not printable until ~2029** — see below |

**The metric that would actually settle the thesis has no investable date.** SOLAIRIA-1 ([NCT07276724](https://clinicaltrials.gov/study/NCT07276724)) is Recruiting, n=786, started 12/3/2025, primary outcome = annualized asthma exacerbation rate through week 52, **primary completion December 2028**. Under R2.3 that makes the *bull/bear efficacy question* untriageable-by-date even though the *company* is triageable.

**COURT-WORTHY (damage-absent, ranked):**
- *(none)* — GENB is DAMAGE-ABSENT but **not court-worthy**, because there is no discount to adjudicate. The name is −2.2% over the window and $15.77 against a $16 IPO price six months ago. A court would be pricing a de-novo platform thesis, not a dislocation.

**PRINT PROXIMITY: NONE within 5 trading days.** Next earnings 2026-11-05 (yfinance-derived, UNCONFIRMED). The nearest company-confirmed dated event is the ERS Congress COPD Phase 1b poster on **Sept 8, 2026** (primary: Q2 release, 8/6/26) — 7th US session out, and **already defused**: the company furnished the final posters as Exhibit 99.1 to the 8-K filed 8/26 (accession 0001193125-26-365556), so the presentation carries near-zero incremental information. Reconstruction run anyway given borderline proximity.

**PRE-PRINT POSITION: FLAT.** The Sept 8 catalyst was pre-released by the issuer's own 8-K, so there is no information event to be paid for; meanwhile ~103M shares unlocked on Aug 26 and the market is only 1–2 sessions into discovering that supply. Buying the "−21%" is buying a spike give-back into a live overhang, at ~$1.6B EV ($2.02B mcap less ~$411M pro-forma cash) for an asset with **no clinical efficacy data until ~2029** and an approved competitor in Tezspire.

**COURT-WORTHINESS GENB: 3/10** — the −21% is a spike round-trip into a disclosed lock-up expiry, not a dislocation; a court cannot change sizing on an event that didn't happen.

Two notes worth carrying back to the pipeline: this fires the mispricing-artifact reflex in a form the catalog doesn't yet have — **lock-up-expiry reversion of a leak-driven spike**, which mimics a velocity dislocation on every `d1` screen; and the missing `cohorts.json` meant the template ran with an unresolved cohort and narrative rather than failing loudly, which is the infra-failure-as-negative-result pattern. Say the word and I'll write both up as memories and add a spike-round-trip guard (`d1` vs `excess_5d` sign disagreement + lock-up calendar) to the class-dislocation detector.

**Sources:** [Q2 2026 results, Generate Biomedicines (primary)](https://generatebiomedicines.com/wp-content/uploads/2026/08/Generate-Biomedicines-Earnings-Release-Q22026.pdf) · [NCT07276724 SOLAIRIA-1 (primary)](https://clinicaltrials.gov/study/NCT07276724) · [GENB price history](https://stockanalysis.com/stocks/genb/history/) · [BioSpace — data leaked ahead of conference](https://www.biospace.com/drug-development/generate-bio-drops-as-data-accidentally-leaked-ahead-of-european-conference) · [Endpoints — ERS26 poster leak](https://endpoints.news/ers26-generatebiomedicines-discloses-early-respiratory-drug-data-after-poster-leak/) · [Yahoo Finance — lock-up expiry](https://finance.yahoo.com/markets/stocks/articles/generate-biomedicines-stock-jumps-post-151000541.html) · [MarketBeat — lock-up ends Aug 26](https://www.marketbeat.com/instant-alerts/generate-biomedicines-incs-nasdaqgenb-lock-up-period-to-end-on-august-26th-2026-08-19/) · [S-1/A](https://www.sec.gov/Archives/edgar/data/2100782/000119312526062362/ck0002100782-20260223.htm)