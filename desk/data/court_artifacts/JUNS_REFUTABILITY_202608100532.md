## Cause-check result: the event record is contaminated — I fixed it before classifying

**The `mcap` field in the event record is wrong by 75×, and I can prove it arithmetically.**

Per the Jul-28 8-K, shares outstanding were **56,520,143**. `56,520,143 × $5.10 = $288,252,729.30` — an exact match to the record's `mcap: 288252729.0`. The record multiplied the **pre-split share count** by the **post-split price**. JUNS executed a **1-for-75 reverse split effective 4:01pm ET Aug 6, 2026**, trading adjusted Aug 7. True share count is ~770,081 and true market cap is **~$2.95–3.93M**, not $288M.

Secondary contamination: `hi52: 138.0` / `lo52: 4.76` / `px: 5.10` are split-*adjusted*, but `hi26w: 0.62` is raw **pre**-split ($0.62 × 75 = $46.50). The pack mixes bases within one record. The `dd52: -0.963` is genuine — both endpoints are consistently adjusted — but it is a solvency spiral, not a cohort dislocation.

**PRINT PROXIMITY: 2026-08-13 — Q2 2026 10-Q, 4 trading days out.** Verified two ways: stockanalysis.com next-earnings date of Aug 13, 2026, and the statutory non-accelerated-filer deadline of Aug 14, 2026 (45 days after the Jun-30 quarter end; FYE Dec-31 confirmed by the Mar-31/Sep-30 quarter ends in the XBRL block). Not company-PR-confirmed, so treat Aug 13 as estimated within an Aug 13–14 window.

### Print-decisive reconstruction (run first, per R2.3)

The 10-Q cannot resolve anything, because **public pre-print filings already close the question**:

- **Dilution engine, disclosed and running.** Yorkville (YA II PN) SEPA dated Oct-24-2025, $20M capacity. Advances price at **97% of the *lowest* daily VWAP over a 3-day window, with no floor price**. ~12.5M shares issued for ~$4.1M net → realized average ~$0.33/share. This is reflexive: each advance prints shares below the recent low, which sets a lower low for the next advance.
- **Remaining overhang ≈ 5× the market cap.** ~$15.9M of the $20M facility is undrawn against a ~$3M cap. At $5.10 that is ~3.1M new shares versus **770k currently outstanding — roughly 4× the entire post-split share count still available to one counterparty.** The three 424B3s (Jul 21/27/29) plus the Jul-7 EFFECT are the resale plumbing keeping those shares free-trading, actively refreshed.
- **The reverse split makes the structure worse, not better.** It cures the minimum-bid deficiency and is *arithmetically incapable* of curing the other one. The Feb-26-2026 Nasdaq notice cited **both** the $1.00 bid **and** the **$35M market-value threshold**. MVLS = price × shares, which is invariant to a split. At ~$3M they are ~$32M short. Stockholders' equity is deeply negative and net income deeply negative, so **all three Nasdaq Capital Market continued-listing standards fail simultaneously**, and one of them cannot be split-engineered.
- **A cash commitment they do not have.** The Jul-21 PharmAla ALA-002 license carries **$1.5M cash upfront** (plus $1.8M stock) against total current assets of **$0.15M** at Mar-31-2026.
- **$1.5M convertible principal** at a fixed $1.50 pre-split conversion (= $112.50 post-split) is far out of the money, so it settles in market-discount SEPA shares, not at the fixed price.

**PRE-PRINT POSITION: FLAT.** No long — the equity is a residual claim behind $6.73M of liabilities on an asset the company cannot fund, and any option value in the MDMA license accrues to Yorkville and the noteholders first. No short either — a 770k-share, ~$3M post-reverse-split nano-cap has unavailable or punitive borrow and is exactly the float profile that squeezes violently on any news.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| JUNS | **STRUCTURAL** | Net working capital + going-concern paragraph vs. quarterly operating burn (would refute only if WC turns positive AND the going-concern doubt is removed) | Working capital **−$6.58M** at Mar-31-2026 (current assets $0.15M vs total liabilities $6.73M); cash $0.72M at Sep-30-2025 with management "substantial doubt"; OCF −$3.05M YTD through Q3-2025 (~−$1.0M/qtr); OCF −$1,063,041 at 2025-03-31 per pack XBRL. Trend: monotonically worse across 5 quarters. [8-K 2026-08-06](https://www.sec.gov/Archives/edgar/data/1679628/000149315226036279/form8-k.htm) · [424B3](https://www.sec.gov/Archives/edgar/data/0001679628/000149315226024764/form424b3.htm) | 2026-08-13 (est.; statutory 08-14) | Record `mcap` wrong 75×; true cap ~$3M. Fails all 3 Nasdaq continued-listing standards; split cures bid price only, cannot cure the $35M MVLS test. |

**COURT-WORTHY (damage-absent, ranked):** *None.* No member classifies DAMAGE-ABSENT. JUNS is not a cohort member that was sold indiscriminately on a shared narrative — it is an idiosyncratic insolvency whose 96% decline has a fully disclosed, still-running mechanical cause (a floorless SEPA with 5× the market cap in remaining capacity). The `excess_dd −0.719` versus the Health Care median is real but carries no dispersion information.

**COURT-WORTHINESS JUNS: 1/10** — the discount is correct and the delisting arithmetic is split-invariant, so no adversarial court could move a sizing decision that is already zero.

---

Two things you should know about how this ran:

**The real deliverable here is the data fix, not the verdict.** A pre-split share count × post-split price will silently misprice *every* name that reverse-splits between the share-count snapshot and the quote. JUNS entered a cohort screen as a $288M mid-cap when it is a $3M shell — a 75× error that survived all the way to a court dispatch. Worth a guard in the blob sweep: reject or flag any record where the price basis and share-count basis straddle a split date, and normalize `hi26w` to the same basis as `hi52`/`lo52`.

**Two limitations, stated plainly.** Bash is disabled this session and my read permission for `/Users/ajay/exalted/signalos` was declined, so I could not open `knowledge_graph/cohorts.json` — the COHORT and NARRATIVE fields are unresolved, and I triaged against the event record alone. That doesn't change the STRUCTURAL call, which rests on JUNS's own balance sheet, but it means I can't tell you how JUNS compares to its cohort median. I also could not perform the standing closing step (ledger upsert, edge_classification, entry_plan, scanner re-run, `/api/everything` verify). And sec.gov returned 403 to every WebFetch, so the SEC URLs above are cited from the pack's accession list and search-result confirmation — the underlying facts I actually read came from stocktitan, quiverquant, and stockanalysis summaries of those filings. The 8-K details (56,520,143 shares, SEPA terms, 1-for-75) are consistent across three independent secondaries and reconcile exactly to the pack's own arithmetic, but they are not primary-verified reads.

If you want, I can retry the SEC documents through the Playwright/full-Chrome-fingerprint path that's worked on gated portals before, and then write the ledger entries directly with the Write tool.