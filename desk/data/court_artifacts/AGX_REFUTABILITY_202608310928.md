## CAUSE-CHECK (run first)

Not a print, not company news — cohort beta into a catalyst. AGX fell **-9.18% on 2026-08-28** ($459.96 → $417.74) on the day AI-datacenter pure plays unwound together behind IREN's FY26 impairment (IREN -13%, APLD -7%, WULF -7%). AGX's only company-specific event in the window is the [8-K of 2026-08-04](https://www.sec.gov/Archives/edgar/data/100591/000110465926090398/) — SMC's acquisition of ValCor Communications, ~$8.3M initial consideration, i.e. 0.14% of a $5.86B cap and immaterial. The -17% 5d excess is narrative repricing of the AI-power complex, landing 3 sessions before AGX's own print.

**Two pack artifacts, flagged before triage:**
- `sector: "Consumer Discretionary"` is **wrong** — AGX is Industrials/Capital Goods (SIC 1731, power-plant EPC via Gemma Power Systems). The "indiscriminate cohort" premise depends on the peer set being right; this one isn't.
- `COHORT: ?` and the narrative both point at `knowledge_graph/cohorts.json`, which I could not read (filesystem access outside the working dir was denied this session). I triaged against the narrative **reconstructed from tape and news** — "AI/data-center power capex is being reassessed → EPC order momentum stalls → backlog rolls over" — and say so explicitly rather than triaging against a blank.

**PRINT PROXIMITY: 2026-09-02 (after close, 5:00pm ET call) — CONFIRMED by company PR, [BusinessWire 2026-08-19](https://www.businesswire.com/news/home/20260819618104/en/Argan-Inc.-to-Announce-Second-Quarter-Fiscal-2027-Results-and-Host-Conference-Call-on-Wednesday-September-2-2026). Upgrades the pack's "yfinance-derived — UNCONFIRMED." 2 trading days out.**

## PRINT-DECISIVE RECONSTRUCTION (pre-print filings only)

Loudest bear claim: *the award cycle peaked; backlog is rolling over; 34.5x forward is unsupportable.* The decisive metric is the **Jul-31-2026 consolidated project backlog**, and it is mechanically bounded before the print.

**1. Backlog identity.** BL_Jul31 = BL_Apr30 + Q2 bookings − Q2 revenue.
- BL_Apr30-2026 = **~$2.8B**, down from ~$2.9B at Jan-31-2026 ([Argan Q1 FY27 release, 2026-06-04](https://arganinc.com/news/argan-inc-reports-first-quarter-fiscal-2027-results-record-revenue-of-291-million-backlog-of-2-8-billion/); 8-K EX-99.1 accession 0001104659-26-070517).
- Q1 revenue $291.0M ⇒ implied Q1 bookings ~$191M, **book-to-bill ~0.66**. Honest band: backlog is rounded to $0.1B, so bookings were $91M–$291M and b2b was 0.31–1.00. Either way, **not above 1.0**.
- Q2 consensus revenue $300.5M. **No new award/NTP press release exists between 2026-05-01 and 2026-07-31** — the last was [CPV Basin Ranch, 1,350MW, 2025-10-30](https://www.businesswire.com/news/home/20251030500209/en/Argan-Inc.s-Gemma-Power-Systems-Receives-Full-Notice-to-Proceed-on-EPC-Contract-for-1350-MW-Combined-Cycle-Power-Plant-in-Texas). Weak evidence, not decisive: AGX books industrial awards without standalone PRs (the $125M data-center tank contract surfaced only on a call).

**Zero-bookings floor ≈ $2.50B**, vs **$2.0B at Jul-31-2025** (Q2 FY26 release, 2025-09-04, SEC accession 0001558370-25-011873). So even the worst mechanical case is **+25% YoY**. Pre-registered thresholds:

| Jul-31-26 backlog | implied Q2 bookings | reading |
|---|---|---|
| **≥ $2.8B** | ≥ $300M (b2b ≥1.0) | rollover claim **refuted** |
| $2.6–2.8B | $100–300M (b2b 0.33–1.0) | second straight sub-1 quarter — unresolved |
| **< $2.5B** | negative (cancellation/descope) | rollover **confirmed**, narrative is true |

**2. The consensus bar embeds mean-reversion Q1 already refused.** Consensus $2.64 EPS on $300.5M — *lower* EPS on *higher* revenue than Q1's $3.24 — implies ~18.5% gross margin, i.e. back to the 18.6% of Q2 FY26. Q1 FY27 printed **21.0% consolidated / 23.6% Power**. Holding 21% adds ~$7.5M GP ≈ **+$0.40/sh** after tax → ~$3.04.

**3. A hard floor the narrative cannot touch.** $973.6M cash+investments, **no debt**, at ~4% ≈ $9.7M/qtr pretax ≈ **$0.52/sh** after tax on ~14.1M diluted shares — roughly **20% of consensus EPS is non-operating**.

**4. What the bears get right.** Net liquidity is $421.4M, not $973.6M (rest is customer advances) ⇒ EV ≈ $5.43B, ~34x TTM earnings ($11.38 TTM EPS). And insiders sold **31 times, bought 0, in six months**: Chairman Griffin 50,000sh ≈ $36.98M at $725.85/$760.43 (Jun 18/22), CEO Watson 31,183sh ≈ $19.46M, Director Ronald 5,716sh at $579.64 (Jul 31) — matching the 144/Form 4 cluster in the pack. Spot is 43% below Griffin's average. The valuation leg is real and the print does not resolve it.

## Triage

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| AGX | **DAMAGE-ARRIVING** | Consolidated project backlog / implied book-to-bill | $2.9B (Jan-31-26) → **$2.8B (Apr-30-26)** on $291.0M revenue ⇒ b2b ~0.66; but +40% vs $2.0B at Jul-31-25. Revenue +50% YoY, GM 21.0% vs 18.6% ([Q1 FY27 release](https://arganinc.com/news/argan-inc-reports-first-quarter-fiscal-2027-results-record-revenue-of-291-million-backlog-of-2-8-billion/)) | **2026-09-02** (confirmed) | P&L damage absent; **order-momentum damage is the narrative's actual claim and its one printed observation is negative.** CEO on the Q1 call: new projects arrive over "the next 10 to 18 months" — bookings are back-half events by management's own framing |

Not DAMAGE-ABSENT: that would require backlog *up*, and it is down. Not STRUCTURAL: revenue +50%, margins +240bp, $974M cash and no debt is not a business the narrative is simply true of.

**COURT-WORTHY (damage-absent, ranked):** *none.* AGX is the only member and it does not clear the damage-absent bar — the decisive metric printed once and printed against the bull. Per **[beta-bleed ≠ dislocation]**, I also cannot claim degraded discovery: 36.7x trailing, consensus PT $667.80, +84% 1yr TSR, and insiders distributing at the top is `discovery_state = CROWDED`. This is a momentum unwind in a well-discovered name, not an information dislocation. AGX routes on its own score below.

## PRE-PRINT POSITION: **FLAT**

The metric the selloff is about resolves in 48 hours, its last reading was negative, and waiting costs two days against learning the entire thesis variable. Buying a -17% 5d excess into that is accidental short-vol.

**NAMED KILL** (required — FLAT is never a default): *Q1 FY27 book-to-bill below 1.0 ($2.9B→$2.8B on $291M revenue), zero announced awards May 1–Jul 31, management guiding new projects to a 10–18 month horizon, at 34.5x forward, with 31-of-31 insider sales at $580–760.* Falsified or confirmed 2026-09-02.

**Pre-registered post-print rule** (this is what survives the print — write it now, not while the bench deliberates):
- Backlog **≥$2.8B AND GM ≥20%** → STARTER 0.5%, scale to 1.0% on any pullback. Kill is falsified.
- Backlog **$2.6–2.8B** → no position; re-triage at the Q3 print for a second consecutive b2b reading.
- Backlog **<$2.5B**, or any descope/cancellation language → reclassify **STRUCTURAL**, do not bid.

**COURT-WORTHINESS AGX: 7/10** — a court cannot beat the Sep-2 print, but it converts it into a trade by pre-registering the backlog thresholds and margin bar before the tape moves, which is exactly the failure mode that cost +30% on TEAM.

Sources: [Argan Q1 FY27 results](https://arganinc.com/news/argan-inc-reports-first-quarter-fiscal-2027-results-record-revenue-of-291-million-backlog-of-2-8-billion/) · [Q2 FY27 date PR](https://www.businesswire.com/news/home/20260819618104/en/Argan-Inc.-to-Announce-Second-Quarter-Fiscal-2027-Results-and-Host-Conference-Call-on-Wednesday-September-2-2026) · [CPV Basin Ranch NTP](https://www.businesswire.com/news/home/20251030500209/en/Argan-Inc.s-Gemma-Power-Systems-Receives-Full-Notice-to-Proceed-on-EPC-Contract-for-1350-MW-Combined-Cycle-Power-Plant-in-Texas) · [Q1 FY27 call transcript](https://www.fool.com/earnings/call-transcripts/2026/06/05/argan-agx-q1-2027-earnings-call-transcript/) · [Aug-28 datacenter unwind](https://247wallst.com/investing/2026/08/28/applied-digital-sinks-7-iren-tumbles-13-as-data-center-selloff-broadens-past-one-name/) · [insider selling](https://www.quiverquant.com/news/Argan+Falls+as+Investors+Weigh+Insider+Selling+and+a+Small+Backlog+Pullback) · [AGX quote/valuation](https://stockanalysis.com/stocks/agx/)

**Two access gaps worth fixing:** `knowledge_graph/cohorts.json` and the desk data dir were permission-denied, so the cohort definition and median are unverified from my side — the dispersion-vs-cohort-median ranking the template asks for could not be computed, only the single-member triage. IBKR `get_price_history` and `get_option_data` were also denied, so the implied move for Sep-2 is missing; that number would sharpen the FLAT call into a sized event trade.