## Cause-check (run first, per event context) — the trigger is an artifact

Before triaging, the drawdown has to be attributed. It does not survive attribution.

SVC issued **479,166,665 shares at $1.20** (416.7M base upsized via over-allotment), settled **2026-04-02**, then ran a **1-for-5 reverse split on 2026-07-06**. Split-adjusted, the share count went **33,614,025 → 129,527,433**, i.e. **2.85 new shares issued per existing share (+285%)**.

That reconciles exactly and reprices the "dislocation":

| | split-adj px | shares | market cap |
|---|---|---|---|
| pre-deal (hi26w, ~Feb 2026) | $11.85 | 33.6M | $398M |
| offering clearing price | $6.00 ($1.20 × 5) | — | +$542M net raised |
| theoretical post-money | **$7.26** | 129.5M | $940M |
| today | **$7.83** | 129.5M | **$1,014M** |

The stock trades **8% above its mechanical post-money value** and **+30% above the recap clearing price**; `lo52` $5.65 is the post-offering trough, and `pct_off_low +38.6%` says it has been rallying off it. **Market cap is up ~155% over the window in which `dd52` reads −0.48.** The −0.353 excess vs the Real Estate median is manufactured by the screen's own price-series arithmetic — Yahoo adjusts for the reverse split but nothing adjusts for issuing 2.85x the float at a 49% discount.

So: no cohort narrative sold this name, and the Q2 print landed **2026-08-05, nine trading days *before* the sweep fired on 8/14**. Per the beta-bleed/artifact doctrine, this is not a dislocation — it is a recapitalization.

Separately, the narrative *is* nonetheless true of the business, which is what the table records.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| SVC | **STRUCTURAL** | Net Debt / Adjusted EBITDAre (corroborant: Normalized FFO less recurring capex) | **9.0x**, interest coverage **1.3x**, net debt/gross assets 56.1% — *after* raising $542M and retiring $550M of 2027 notes; debt $5.289B → $4.509B. FY26 guide: NFFO $124–144M vs capex $120–140M ⇒ **AFFO ≈ $4M midpoint (~$0.03/sh), negative at the bad end**. Dividend $0.20/yr = $25.9M ≈ **6.5x midpoint AFFO**, funded by dispositions. Offering terms primary: [svcreit.com pricing release, 2026-03-31](https://www.svcreit.com/news/press-release-details/2026/Service-Properties-Trust-Announces-Pricing-of-500-Million-Underwritten-Public-Offering-of-Common-Shares/default.aspx); Q2 figures from 10-Q acc. 0000945394-26-000049 (2026-08-05) | **~2026-11-04 — UNCONFIRMED** | Dilution is the drawdown, but leverage is still the business. They diluted holders 285% and leverage barely moved. Ops are genuinely fine (RevPAR $134.53 +6.6%, 7th straight quarter of outperformance; net lease 96.6% occ, 2.09x coverage, 7.1yr WALT) — the equity is just 18% of EV, so ops don't reach the stub. |

**COURT-WORTHY (damage-absent, ranked):**
None. SVC is the only member and it classifies STRUCTURAL, not damage-absent. The dispersion the screen flagged is a corporate-action artifact, not ignored fundamental dispersion — there is no mispricing for a court to adjudicate against an external anchor.

**COURT-WORTHINESS SVC: 2/10** — trigger is a dilution artifact and the discount is correct; a court would spend Opus volume to re-derive the FLAT we already hold.

**PRINT PROXIMITY: ~2026-11-04 — UNCONFIRMED (yfinance-derived; no company PR names it). Not within 5 trading days (~55 out). The decisive print already landed 2026-08-05 (10-Q 0000945394-26-000049 + 8-K 0000945394-26-000048), nine trading days before the sweep fired — no catalyst is being raced, so no pre-print reconstruction is owed. Standing position: FLAT, consistent with book (held=NO POSITION, orders=NONE).**

---

**Sizing note (why 2/10, not higher):** the bull optic is real — 5.8–6.5x P/NFFO. It fails on three counts that a court would not overturn. AFFO is ~zero, so the FFO multiple is not a cash yield. SOTP flips sign inside a plausible cap-rate band (net lease $383M NOI at 7.5% + hotels at 12% ⇒ ~$1.5B equity; at 8.5%/14% ⇒ ~$760M, *below* today's $1.0B cap) — at 18% equity/EV the verdict is swamped by assumption noise. And RMR is externally paid on gross assets while having just issued 2.85x the share count, which is a permanent governance discount, not a closing gap. Tails are not bounded at 9.0x, so this cannot clear RP_FAIR regardless of court outcome.

**Screen fix — this is the actual deliverable.** `blob_sweep`'s `dd52` is not invariant to equity issuance. Recommend gating class-dislocation membership on **market-cap drawdown, not price drawdown**: pull `dei:EntityCommonStockSharesOutstanding` (already in the XBRL the pipeline fetches), and if shares outstanding grew >25% across the 52-week window, tag `DILUTION_ARTIFACT` and re-test `excess_dd` on mcap before admitting the member. SVC would have been rejected at admission — its mcap `dd52` is **+155%**. I could not inspect `blob_sweep`/`cohorts.json` to wire this (both are outside my granted read scope — `/Users/ajay/exalted/signalos/knowledge_graph/cohorts.json` denied), so the COHORT and NARRATIVE fields stayed unresolved and I reconstructed the cohort from the event record alone. Grant read on that path and I'll wire the guard and its invariant this session.

**Sourcing caveat:** every `sec.gov` and `data.sec.gov` fetch returned 403 (WebFetch can't set the Sec-Ch-Ua/Sec-Fetch fingerprint the browser-fingerprint doctrine calls for). The offering terms above were fetched directly from the company's own newsroom — primary. The 10-Q figures came via a filing-rendering service; I cross-checked them against the evidence pack's audited XBRL and they tie (10-Q's 33,614,025 split-adjusted Dec-2025 count × 5 = 168.1M vs pack `dil_sh` 165.7M at 2025-06-30, the gap being H2-2025 issuance). Treat the 10-Q line items as verified-by-reconciliation, not as a direct primary read.