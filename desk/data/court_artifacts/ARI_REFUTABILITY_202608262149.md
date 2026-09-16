## ARI — refutability triage

**The screen fired on an artifact.** ARI paid a **$3.75/share return-of-capital distribution on 2026-07-15**; the drawdown that triggered this event is that distribution, not a de-rate. Distribution-adjusted, ARI's 52w drawdown is **−7.8%**, versus a Real Estate sector median of −10.3% — so `excess_dd` is **+2.5pp, not −28.4pp.** The sign flips. ARI is also no longer a CRE lender: it sold its entire ~$9B loan book to Athene at **99.7% of total loan commitments** (closed 2026-04-24) and is now a **court-approved-pending liquidating vehicle** — DEFM14A filed 2026-08-24, dissolution vote **2026-09-29**.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| ARI | **DAMAGE-ABSENT** (cohort membership VOID) | Realized clearing price of the CRE loan book vs par — an arm's-length, same-event EXTERNAL anchor | Entire ~$9B portfolio sold to Athene at **99.7% of total loan commitments**, net of asset-specific CECL reserves; closed 2026-04-24. Loan book now **zero**. Q2'26 BVPS **$8.47** vs px $6.90 ([DEFM14A](https://www.sec.gov/Archives/edgar/data/0001467760/000119312526363807/d119099ddefm14a.htm), [PREM14A](https://www.sec.gov/Archives/edgar/data/0001467760/000119312526302255/d119099dprem14a.htm)) | 2026-10-29 (UNCONFIRMED, and non-decisive) — real catalyst is the **2026-09-29** dissolution vote | dd52 is a $3.75 ROC-distribution artifact; residual risk is 4 REO properties, not credit |

### Why the classification is DAMAGE-ABSENT but the cohort read is void
The narrative (CRE credit impairment) is refuted about as hard as it can be — not by a model, but by a third party paying cash at 99.7% of commitments. But that refutation is *already realized and distributed*. What's left is a liquidation, so ARI should be **removed from the cohort** rather than ranked within it.

### Balance-sheet bridge (6/30/26, verified by reconciliation)
Cash $1,239.5M + REO net $857.0M − REO debt $371.4M − preferred $169.3M (6,770,393 sh Series B-1) − dividend payable $480.8M = **$1,075M / 128,212,093 sh = $8.38** vs reported BVPS **$8.47** (~1% = other assets/liabilities). This confirms **$8.47 is already net of the $3.75 dividend** — the remaining-distribution estimate is not double-counting it.

### What you are actually buying at $6.90
- Management guides **$7.75–$8.50** of remaining liquidating distributions (plus the $3.75 already paid → $11.50–$12.25 total), completion by **1H 2028**.
- **$3.70–$4.00 arrives in cash within ~30 days of approval** (~late Oct 2026) — ~56% of the purchase price back in ~60–75 days.
- Residual basis after that: **~$3.05**, against **$3.75–$4.80** of further distributions → **~+40% on the stub** over 15–18 months. Blended IRR ≈ **18–22%**.
- The stub is backed by **four REO properties** (Brooklyn multifamily, a D.C. asset, two hotels): $912M net assets / **$541M net equity** ($4.22/sh), only $371M of debt against them.

**The single decisive question:** at $3.05 residual basis vs ~$4.28–$4.95 of residual book, the market is pricing a **~17–27% writedown of gross REO value**. That is a four-asset appraisal problem with a hard cash floor — unusually tractable for a court.

Scenarios: marks hold → **+12% to +23%**; 30% gross REO haircut → **−11%**; REO equity to zero (needs −59% gross) → −34% tail.

### Named risks a court must resolve before any sizing beyond a starter
1. **Liquidating-trust delisting / transferability** — on transfer to the Apollo-managed trust, shares typically delist and trust interests are commonly **non-transferable**. If so you are locked to 1H2028 with no exit and no TLH optionality on the lot. *I could not verify this term from primary text — it is the gating question.*
2. **Grantor-trust phantom income** — annual K-1 pass-through of income/gain without matching cash; real admin and tax drag on a taxable account.
3. **Estimate bias** — the $7.75–$8.50 range appears in a document soliciting a YES vote.
4. **Fee alignment** — Apollo affiliate earns 0.50%/yr on net assets in liquidation; mild incentive toward slowness.
5. Vote risk 2026-09-29 (low; initial distribution is conditioned on approval).

Tax positive: ROC distributions reduce basis (no current tax); gain deferred and long-term if held >1yr.

**COURT-WORTHY (damage-absent, ranked):**
1. **ARI** — court-worthy for a reason unrelated to the cohort: an ~18% discount to a cash-heavy liquidating book where 56% of the price returns as cash in ~75 days, and the entire residual question reduces to marks on four named properties plus one verifiable proxy term (trust transferability). Any court must be **re-scoped from "CRE credit dislocation" to "REO appraisal + liquidating-trust liquidity trap."**

**COURT-WORTHINESS ARI: 7/10** — the sizing decision turns entirely on two tractable, testable items (four-property REO marks; liquidating-trust transferability), not on the narrative that fired the screen.

**PRINT PROXIMITY: NONE within 5 trading days.** The pack's 2026-10-29 is yfinance-derived and UNCONFIRMED — no company PR names it, and for a dissolving REIT the Q3 10-Q is not the decisive event. The binding dated catalyst is the **2026-09-29 special meeting** (record date 2026-08-21, per DEFM14A filed 2026-08-24), ~24 trading days out, followed by the initial distribution ~30 days after approval. Verified from the DEFM14A/PREM14A record, not from a vendor calendar.

**PRE-CATALYST POSITION (voluntary — no print in window, but the catalyst is dated and decisive): STARTER.** No named kill exists to justify FLAT, and the asymmetry is favorable with a fast cash return; but sizing beyond a starter must wait on a pack resolving trust transferability, because a locked, untradeable 18-month position is a materially different instrument than a listed stub.

### Two flags for the desk
- **Screen patch owed:** `blob_sweep` / `class_dislocation` compute `dd52` on an unadjusted price series. Any name with trailing-52w distributions >5% of price will manufacture false excess drawdown. This is a **fifth member of the vendor price-artifact family** (alongside PTS marks, intraday-vs-close, unadjusted reverse splits, vendor MA tables) — return-of-capital distributions corrupting screen drawdown. I could not write the memory update: **no Write/Edit tool is available in this session**, so this needs to be logged manually into `feedback_vendor_price_artifact_family.md`.
- **Sourcing honesty:** `sec.gov` returned **403 on every direct WebFetch** (no full-fingerprint fetcher or Bash available here). Primary-document content came from search-index reads of the DEFM14A/PREM14A plus filing summaries, cross-checked against each other and **reconciled arithmetically to the pack's own tape and share count** (the $8.38-vs-$8.47 bridge above is that verification). A full court should re-pull the DEFM14A with the desk's own fetcher before acting.

Sources: [DEFM14A 2026-08-24](https://www.sec.gov/Archives/edgar/data/0001467760/000119312526363807/d119099ddefm14a.htm) · [PREM14A 2026-07-14](https://www.sec.gov/Archives/edgar/data/0001467760/000119312526302255/d119099dprem14a.htm) · [8-K ex-99.1 2026-06-16](https://www.sec.gov/Archives/edgar/data/0001467760/000119312526271542/d116031dex991.htm) · [Athene portfolio sale PR](https://www.apollocref.com/insights-news/pressreleases/2026/01/apollo-commercial-real-estate-finance-inc-announces-entry-into-definitive-agreement-to-sell-commercial-real-estate-loan-portfolio--3227448) · [Dividend + strategic-alternatives PR 2026-06](https://www.apollocref.com/insights-news/pressreleases/2026/06/apollo-commercial-real-estate-finance-inc-declares-quarterly-common-stock-dividend-and-provides-update-on-review-of-strategic-alternatives-3312158) · [Bloomberg wind-down](https://www.bloomberg.com/news/articles/2026-06-15/apollo-property-lender-to-wind-down-after-hunt-for-other-options)