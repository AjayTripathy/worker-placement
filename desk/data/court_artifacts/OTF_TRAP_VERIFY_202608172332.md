### OTF (Blue Owl Technology Finance — software/tech-focused BDC, $14.68B portfolio, 205 cos) — screen $11.13 / NAV $16.48 / 32.5% disc / 12.2% yld / $5.1B mcap — **REAL CANDIDATE**

**SCREEN TIE-OUT (all five defect families checked, none fire):** NAV $16.48 ✓, shares 457.6M, net assets $7.54B (Q2'26 PR, 8-K 2026-08-05). Mcap join CLEAN: 457.6M × live $11.5718 = **$5.295B**. Discount corrected to **29.8%** (screen used a stale $11.13; stock +4.0% since). Yield: base $1.40 = **12.10%**, but *covered* yield is only **10.37%**. The 235M→465M share jump in the pack's XBRL is the OTF II merger (closed 2025-03-24), not a split artifact; count has since *fallen* 1.6% on $170M of buybacks.

**LIVE FACTS**
- **Harshest non-accrual recognition in the cohort I've built.** 0.6% at cost / 0.1% at FV ⇒ implied mark **16.3c** ($90M cost → $14.7M FV) — below TCPC's 19.4c, vs FSK 47.9c, MFIC 55.1c. And it discloses *both bases*, the test FSK and NMFC failed.
- PIK $25.0M = **18.0% of NII** (vs NMFC 41.8%, FSK 34.9%). Marks 97.9% of cost; +$0.03/sh gains this quarter.
- **Tails bounded:** debt $7.16B vs net assets $7.54B ⇒ asset coverage **205%**; needs a **27% portfolio markdown** to breach 150%. 78% first lien, 97% floating.
- **Flow overhang is behind, not ahead** — all pre-listing lock-ups expired 2026-06-12 (amended schedule, PR 2025). $195M buyback left, accretive ~$0.036/sh per $55M.
- Today's 424B2/FWP is a **6.50% 2029 notes reopening — debt, not dilutive equity.**

**KILL FACTS**
- **Base dividend uncovered:** NII $0.30 vs base $0.35; special $0.05 is explicitly terminal. Spillover $0.32/sh ≈ *one quarter*. Management concedes coverage only "by the middle of 2027."
- **Fee asymmetry:** post-listing income incentive fee is 17.5% over a 1.5% quarterly hurdle with **no cumulative total-return hurdle** (the TCPC feature that exonerated it). Residual expense line is $36M after mgmt $54M + interest $109M — the adviser is paid while the dividend under-earns. *Exact incentive-fee dollars UNVERIFIED — 10-Q expense table.*
- **Taxable-account drag:** ordinary-income distributions ⇒ ~7.0% net, not 12.1%.
- **Not an orphan.** Fully covered, NYSE, $5.3B. The 30% discount is cohort-wide; OTF is *not* the widest. The bet is quality-convergence, and my own prior finding is that the cohort persistently fails to discriminate on mark integrity.
- Girard Sharp investigation notice (2026-08-12) re OTF II holders — **solicitation, not a filed complaint**; low weight.
- ADV **UNVERIFIED** (not asserting an unchecked number — the TCPC lesson).

**RESOLVES ON:**
- **2026-11-04 (unconfirmed, yfinance-derived) Q3 print:** NII ≥$0.33 and non-income-producing equity <7% ⇒ coverage path live; NII ≤$0.30 or base cut ⇒ thesis dead.
- **Mid-2027:** management's stated coverage crossover — hard date, hard test.
- Rating-3+ bucket (7.6% today) rising, or non-accruals >1.5% at cost.
- Any *filed* OTF II complaint ⇒ RP_TAINTED.

**PROMPT CORRECTION (file this):** the trap catalog handed to me is an operating-company catalog — SBC-vs-dilution, prefunded warrants, FCF quality, statutory-EBIT one-offs, net-cash claims. **None apply to a BDC** (no FCF, no SBC, no EBIT; the pack's `ocf` line is portfolio flow, not operations). The BDC catalog is: non-accrual disclosure-basis asymmetry, PIK-as-%-of-NII, incentive-fee definition, unrealized-recognition lag, controlled positions without third-party price, asset-coverage cushion, post-listing lock-up flow. Defect class: **instrument-class mismatch in the screen template.**

**Disposition: advance-to-court.** Court question: does best-in-cohort mark integrity at a cohort-*median* discount pay for a base dividend that under-earns by 14% until mid-2027, in a taxable account that keeps 58% of the coupon?

Sources: [Q2'26 results PR](http://www.prnewswire.com/news-releases/blue-owl-technology-finance-corp-announces-june-30-2026-financial-results-302844208.html), [Q2'26 call transcript](https://www.investing.com/news/transcripts/earnings-call-transcript-blue-owl-technology-finance-rises-on-q2-2026-results-93CH-4843508), [Q2'26 slides](https://www.investing.com/news/company-news/blue-owl-technology-finance-q2-2026-slides-portfolio-grows-to-147b-93CH-4843761), [lock-up schedule PR](https://www.prnewswire.com/news-releases/blue-owl-technology-finance-corp-announces-amended-lock-up-release-schedule-302606218.html), [OTF II merger completion](https://www.prnewswire.com/news-releases/blue-owl-technology-finance-corp-completes-merger-with-blue-owl-technology-finance-corp-ii-302408687.html), [424B2 6.50% 2029 notes](https://www.stocktitan.net/sec-filings/OTF/424b2-blue-owl-technology-finance-corp-prospectus-supplement-f24b64eb22d2.html), [Girard Sharp notice](https://www.globenewswire.com/news-release/2026/08/12/3343453/0/en/investigation-notice-girard-sharp-law-firm-encourages-former-investors-of-blue-owl-technology-finance-corp-ii-who-received-shares-of-blue-owl-technology-finance-corp-nyse-otf-to-co.html)

Two caveats on method: SEC.gov returned 403 to my fetch tool throughout, so the 10-Q itself (equity note, expense table, SOI) is **unread** — every figure above is from the 8-K press release, slides, or transcript, and the incentive-fee dollars and share rollforward remain UNVERIFIED. That is the same truncation/403 failure mode that has now fired three times this week; the working direct path is `desk/sec_fetch.py`, which I could not invoke here without repo read permission.