## Context

SLBT is not a dislocation — it is a de‑SPAC reference price deflating. SL Science Holding listed 2026‑06‑12/15 via merger with Horizon Space Acquisition II at an implied **$5.568B** equity value on **$2.2M of declining Taiwanese skincare revenue**, with an entirely **pre‑clinical** pipeline (no IND filed on anything). The −81.2% dd52 is measured off a high that was never an economic price.

**Fetch note:** sec.gov 403'd direct WebFetch; filing figures below come from a proxy render of the actual SEC Archives URLs cross‑checked against StockTitan's independent filing summary — the two agree on every load‑bearing number. IBKR `search_contracts` permission was declined, so tape facts are the evidence pack's `ibkr_gw` block.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| SLBT | **STRUCTURAL** | Contractual license/milestone obligations vs. cash — the metric that would refute "pre‑clinical shell" is a funded path to IND | **$41.1M remaining obligations ($37.0M JY BioMed + $4.1M CytoArm) against $9.0M pro‑forma cash** (12/31/25) and a $3.8M annual loss. Revenue **$2.2M in 2025, down from $3.4M in 2024 (−35%)**, and it is *skincare/haircare the company intends to phase out*. All programs pre‑clinical; **no IND filed**; GBM orphan‑designation request **declined May 2026**. [20‑F](https://www.sec.gov/Archives/edgar/data/0002070534/000121390026070158/ea0293184-20f_slscience.htm) · [F‑1](https://www.sec.gov/Archives/edgar/data/0002070534/000110465926089195/tmb-20260331xf1.htm) | **~2027‑04‑30** (FY2026 20‑F, FPI 4‑month deadline; no mandated quarterly) | Discount is not merely correct — it is **incomplete**. See below. |

### Why STRUCTURAL, and why the drawdown understates it

**The −81% has not made this cheap.** 560,759,757 shares outstanding as of 2026‑06‑18 × $2.73 = **$1.531B** — which reconciles to the evidence pack's mcap to the dollar ($1,530,874,137), confirming the share count. That is **~697× 2025 sales** and **~170× total pro‑forma capitalization**, for a company with no human trial ever conducted.

⚠️ **stockanalysis.com reports 161.63M shares / $431.5M mcap / $3.27M TTM revenue — that is wrong.** Anyone anchoring there sees "200× sales" instead of 697×. The 20‑F figure is authoritative and arithmetically confirmed.

**Both endpoints of the drawdown are non‑economic.** William Wang beneficially owns 333,832,129 shares — 59.53% of voting power. 3,502,404 HSPT public shares were tendered for redemption at the 2026‑02‑12 business‑combination meeting ([8‑K ex‑99.1](https://www.sec.gov/Archives/edgar/data/2032950/000121390026011274/ea027522701ex99-1_horizon2.htm)), before extension‑meeting redemptions. Real tradeable float is plausibly low‑single‑digit millions against 560.76M shares — **well under 1%**. The $14.50 high, the $2.73 print, and the $1.53B "market cap" are all artifacts of a sliver of float; the notional cap is unmonetizable.

**The one dated supply event is negative.** The 2026‑07‑31 F‑1 registers 1,040,000 shares for resale (780,000 PIPE shares + 260,000 on preferred conversion); PIPE lockup runs six months from the 2026‑06‑12 close, i.e. **~2026‑12‑12**. Trivial against 560.76M shares — but potentially a **30–100% increase in effective float**, which is precisely why it matters to this tape. Price is 7.6% off its all‑time low and still falling.

**COURT-WORTHY (damage-absent, ranked):**
*(none — no member classifies DAMAGE‑ABSENT)*

**COURT-WORTHINESS SLBT: 1/10** — the sizing decision is zero at any court outcome; the name fails float and valuation threshold gates before thesis work has any option value.

**PRINT PROXIMITY: NONE** — verified structurally, not from a vendor field. SLBT is a foreign private issuer with a Dec‑31 fiscal year end; the 2026‑06‑18 20‑F was the post‑merger shell‑company report covering FY2025. FPIs carry no quarterly obligation, so the next *mandated* report is the FY2026 20‑F, due ~2027‑04‑30. Interim 6‑Ks are unscheduled. The evidence pack's null next‑print is correct, not a gap. No print‑decisive reconstruction is required and no pre‑print position question arises: **FLAT**, and not on a timing basis — on a threshold basis.

---

### One screen-hygiene finding worth wiring

This is a **false positive of the dd52 blob sweep**, and it will recur. Recent de‑SPACs mechanically produce extreme `dd52` and extreme `excess_dd` because the 52‑week high is a thin‑float post‑merger artifact rather than a price the market ever cleared size at. The sweep read −0.561 excess vs. Health Care median and routed a name whose drawdown carries no information about mispricing.

Suggested gate, in priority order: exclude candidates whose **CERT/listing date is <12 months old AND that arrived via business combination**; or, where you want to keep them, compute `dd52` against the **$10.00 trust reference** rather than the post‑close high. A float filter (public float < 5% of shares outstanding → suppress) would catch the same class from a different angle.

Want me to wire that gate into the blob sweep and add a regression case pinned to SLBT? I'd want to check how many of the current untriaged cohort are de‑SPACs before choosing which of the two forms to implement — that count decides whether this is an edge case or a systematic leak.