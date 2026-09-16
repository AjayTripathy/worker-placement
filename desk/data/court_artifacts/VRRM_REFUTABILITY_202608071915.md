## Cause-check result

**This did not fire as a cohort dislocation.** VRRM's −80% is a single-name customer event, not a Consumer-Discretionary/Transportation-Services narrative — so the "cohort sold indiscriminately, alpha = dispersion" premise does not apply here. There is no cohort to disperse against; the triage below is a single-name refutability call.

More importantly, **the narrative that caused the crash has already been superseded by fact.** The stock fell ~70% on 2026-05-27 on an Avis Budget termination notice (est. $135–145M revenue / $120–125M segment profit at risk). On 2026-08-05 Verra disclosed that Avis **re-signed for seven years** and Hertz **re-signed for five** — repriced, not lost.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| VRRM | **DAMAGE-ARRIVING** | Commercial Services segment revenue + segment profit (the RAC-concentration channel) | Q2-26 CS rev **$115.1M, +6% YoY**, segment profit **$77.2M / 67% margin** — but FY26 CS now guided to **decline high-single-digits**, implying H2-26 CS ≈ **$176M vs ~$222M H2-25 (−21%)**. FY26 guide cut twice: $1,020–1,030M → $945–965M rev, $405–415M → **$360–370M** EBITDA ([Q2-26 release](https://www.prnewswire.com/news-releases/verra-mobility-announces-second-quarter-2026-financial-results-302843961.html); [FY25 release w/ original guide](https://www.prnewswire.com/news-releases/verra-mobility-announces-fourth-quarter-and-full-year-2025-financial-results-302695918.html); [8-K ex-99.1](https://www.sec.gov/Archives/edgar/data/0001682745/000119312526335111/vrrm-ex99_1.htm)) | **Q3-26, ~early Nov 2026**; 10-Q imminent | Termination narrative **refuted** (7-yr Avis / 5-yr Hertz extensions), but both carry **fleet-volume-modulation rights** — counterparty now holds price *and* quantity. Mgmt **declined 2027 guidance**. Not damage-absent: damage is in the numbers. Not purely structural: the priced event didn't happen. |

**COURT-WORTHY (damage-absent, ranked):** *none.* VRRM does not qualify — the refuting metric (CS revenue) is visibly deteriorating, so it fails the damage-absent test on its own evidence. It routes to court on the **arriving-magnitude** question instead, below.

## Print-decisive reconstruction (run because the 10-Q lands inside the window)

The bridge closes on public data. FY25 CS was $427.5M rev / $272.8M profit. Guided FY26 CS decline of ~8% ⇒ H2-26 CS ≈ $176M vs H1-26 ≈ $217M — a **~$27M/quarter step-down, ~$105M annualized revenue**, at CS's near-pure-flow-through incremental margin ⇒ **~$85–95M annualized segment-profit loss**. Cross-check: 5 months of that (Aug–Dec) ≈ $40M, against an actual $45M EBITDA guide cut. **The reconstruction reconciles**, which means the 2026 guide embeds only ~5 months of repricing.

Rolling to a full year and adding GS growth: **2027 Adj EBITDA ≈ $300–330M**. At $4.91 ([stockanalysis.com, Aug 7](https://stockanalysis.com/stocks/vrrm/forecast/)) and $993.2M net debt, EV ≈ $1.75B ⇒ **~4.8x 2026E / ~5.6x 2027E EV/EBITDA**, 2027 leverage ~3.1x, 4.3x P/E on $1.14 adj EPS, 14.6% 2026 FCF yield. Versus a historical 11–13x. Offsetting: Government Solutions is now the **larger** segment (+20% YoY) and orthogonal to the RAC narrative, anchored by a **$998M / 5-year NYCDOT contract** — but its margin is guided down 450–500bps to "low 20s," so GS revenue growth ≠ earnings growth. Parking took $104.4M of impairments (confirmed M&A value destruction), and a securities class action is pending.

**PRE-PRINT POSITION: STARTER.** The balance sheet is not the risk (2.4x, revolver undrawn) and the crash-narrative is factually stale, but the single unresolved variable — whether repricing cascades to the rest of the RAC book — is only readable in the 10-Q's contract exhibits. Size small now; the add is conditional on those volume-modulation mechanics, not on the tape.

**PRINT PROXIMITY: 2026-08-05 (T-2, already landed) — verified via the company's own Q2 release dated Aug 5 and an Aug 7 quote; next scheduled print Q3-26 ~early Nov 2026, NOT within 5 trading days. The 10-Q (carrying the Avis/Hertz exhibits) is the live near-term disclosure and could not be confirmed as filed — EDGAR returned HTTP 403 on every fetch attempt this session.**

**COURT-WORTHINESS VRRM: 7/10** — the decisive number (2027 CS run-rate under counterparty-held volume rights) is undisclosed by management, reconstructable from public data, and swings the multiple between ~5x and ~8x, i.e. between STARTER and ZERO.

---

Three things I could not do, stated plainly:

- **Live price is not from IBKR.** The IBKR tools were permission-blocked, so the $4.91 is stockanalysis.com's Aug 7 quote, not a broker print — that violates the standing rule and should be re-pulled before any sizing.
- **Primary SEC documents were read indirectly.** Every `sec.gov` and `data.sec.gov` fetch returned 403 (no Bash available to set a browser fingerprint). The financials come from company-issued PRNewswire releases — primary and company-authored, but not the filed documents. The 8-K exhibit URL is cited from the search index, not a direct read.
- **The dashboard/ledger closing step was not performed.** Bash is disabled and the `signalos` directory read permission was not granted, so I could not check `cohorts.json`, upsert the ledger, or re-run the scanner.