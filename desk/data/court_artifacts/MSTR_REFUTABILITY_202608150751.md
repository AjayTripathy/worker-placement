## Context

Cohort file (`knowledge_graph/cohorts.json`) was not readable this session — path outside the granted working directory. Triaging the single member from the event blob. The narrative being priced on MSTR is the digital-asset-treasury (DAT) de-rating: *"the mNAV premium that made bitcoin accumulation accretive has collapsed, so the flywheel reverses."* For MSTR that narrative is not a sentiment overhang — it is now a mechanical, disclosed, dated fact set in the company's own filings, and the equity **still trades at a premium to net asset value after a −74.7% drawdown.**

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| MSTR | **STRUCTURAL** | **BTC-per-share** (the flywheel's only output metric), cross-checked against **mNAV net of senior claims** | BTC/share **−1.90% in the week of Aug 3–9, 2026**: holdings −1,690 BTC to **840,447** while **6,585,682** common shares were issued for **$653.1M** — and the BTC was sold *"to fund repurchases of STRC Stock"*, not to buy BTC ([8-K 2026-08-10](https://www.sec.gov/Archives/edgar/data/0001050446/000119312526341297/mstr-20260810.htm)). Net NAV/share ≈ **$85.75** vs $93.04 tape = **1.08× premium**, not a discount | 8-K weekly update **2026-08-17**; Q3 earnings **2026-10-29** (yfinance-derived, UNCONFIRMED) | Fixed cash obligations **~$1.74B/yr** against **$9.85M** of six-month operating cash flow ([10-Q 6/30/26](https://www.sec.gov/Archives/edgar/data/0001050446/000105044626000044/mstr-20260630.htm)) — coverage **0.011×**. Ratchet is one-way. MSCI removal proposed. |

### The NAV bridge (this is the whole case)

At BTC $62,829 and 840,447 coins:

| | $B |
|---|---:|
| Bitcoin | +52.80 |
| Cash / USD Reserve ($1.71B at 6/30 + ~$650M build) | +2.30 |
| Software business (~$490M rev, ~breakeven, 2.5–3× sales) | +1.30 |
| Preferred liquidation preference (STRF/STRC/STRE/STRK/STRD) | −15.35 |
| Convertible + secured debt principal | −6.75 |
| **Common NAV** | **34.30** |

Shares: Class A **364,585,501** (cover page, 7/24/26) + Class B ~19.64M + ~13–20M ATM since = **~400M**. → **NAV/share ≈ $85.75 vs $93.04 tape = mNAV 1.085×.** The premium is robust to the inputs: 1.077× at 397M shares, 1.096× at 404M, **1.13× if you value the software business at zero.** There is no plausible input set that produces a discount. **The dislocation screen fired on a name that is still expensive.**

**Why the drawdown exceeded bitcoin's:** $22.1B of fixed claims sit ahead of $52.8B of BTC, so the common carries **1.54× effective leverage on the downside** and only **1.29× on the upside** (fixed claims shrink as a share of a bigger pie). Negative convexity, before any drain. Common NAV reaches **zero at BTC ≈ $22,000** (−65% from spot).

### The three structural mechanisms — all disclosed, none reversible

1. **The STRC ratchet is a one-way $10.4B obligation.** The rate rises 0.5%/yr whenever STRC prints below $95 and *cannot be reversed if the price recovers*. It has gone **9% (Jul 2025) → 12% (Jul 2026) across seven consecutive increases**. Each click costs **~$52M/yr permanently**. STRC closed **$95.77 on 8/14** — 0.8% above the trigger, held there only by spending bitcoin. Remaining authorization is **$785.2M**, enough for ~7.9% of the stack.
2. **The dividend is not funded by the business, by construction.** Forward preferred run-rate: STRC ~$1,245M + STRD $140M + STRF $128M + STRK $112M + STRE ~$88M ≈ **$1.71B/yr** — already ~36% above the $629.2M paid in 1H26 because of the ratchet. Operating cash flow was **$9.85M for six months**. Every dollar comes from diluting common or selling bitcoin. That is **~4.7%/yr of NAV drain on the common market cap**, and the company has formalized it: the USD Reserve is defined in its own 8-K as liquidity *"intended to support the payment of dividends on Strategy's preferred stock and interest on its outstanding indebtedness."*
3. **MSCI has proposed removal** from its Global Investable Market Indexes under a rule targeting non-operating companies with large treasury holdings — decision by **October 2026**, implementation **November 2026**, ~$2.8B of estimated forced selling, landing in the same window as the 10/29 print.

The comparison that settles it: a buyer wanting this exposure pays **an 8.5% entry premium + ~4.7%/yr drain** for **1.54× down / 1.29× up**, versus IBIT at 0.25%/yr for 1.00× both ways with no premium, no ratchet, and no index event.

## COURT-WORTHY (damage-absent, ranked)

**NONE.** No member qualifies. The narrative's predicted damage is not merely present in MSTR's numbers — it is the disclosed operating model, and the market has not yet priced it fully (mNAV is still >1). A DAMAGE-ABSENT finding here would require mNAV < 1.0 *and* a covered dividend; neither holds.

## PRINT PROXIMITY: 2026-10-29 (Q3 earnings, yfinance-derived — UNCONFIRMED, no company PR names it) — NOT within 5 trading days. However, the weekly 8-K holdings/ATM update lands **Monday 2026-08-17, one trading day out**, and carries every decisive metric. Reconstruction run on that basis.

**Print-decisive reconstruction (8/17 8-K).** Loudest bull claim: *"the BTC sale was a one-off; accumulation resumes later in 2026"* (company-signaled 8/11). Loudest bear claim: *"net seller, diluting common to pay preferred."* Public pre-print data already resolves it:

- **STRC closed $95.77 on 8/14**, above the $95 trigger — the defense held, so expect a *smaller* STRC buyback than last week's $108.6M and therefore a smaller-or-zero BTC sale. Marginally bull-friendly.
- **MSTR traded ~$97.33 on 8/11 and −3.5% into ~$93 on 8/14** (MSCI news), so the 8/10–8/14 ATM printed at roughly $93–99 — below last week's $99.17 average but still above the ~$86 NAV/share, meaning the ATM stayed open. With $22.0B of remaining capacity and dividends that don't wait, another **~$400–700M of common (≈1.3–1.8% dilution)** is close to certain.
- **Highest-probability print:** holdings roughly flat (840,447 ± ~1,500), share count +4–7M, repurchase authorization drawn from $785.2M toward ~$650–785M. **BTC/share down again ~1.0–1.8%.**

**The branch that matters: it doesn't matter which way it breaks.** A "good" print — zero bitcoin sold — still shows ~1.5% common dilution funding the same $1.74B obligation. Both branches are per-share-NAV negative. No print outcome makes an 8.5% premium attractive.

**PRE-PRINT POSITION: FLAT.** Not short — MSTR borrow is expensive, the tape is a crypto beta with real squeeze risk, and the MSCI proposal can still be withdrawn after comment; shorting an 8% premium into that is a poor risk-per-unit-of-edge. Simply no position: the exposure this name offers is available at 1.00× with no premium and no drain elsewhere.

*Note: IBKR live-quote confirmation was declined (permission not granted this session) — tape facts are the evidence pack's $93.04 plus cited public closes.*

**COURT-WORTHINESS MSTR: 2/10** — a court cannot change a FLAT sizing decision that follows from cover-page arithmetic: the "dislocated" stock still trades ~8% *above* net NAV, and every mechanism driving the discount is disclosed, dated and irreversible.

Sources: [8-K 2026-08-10](https://www.sec.gov/Archives/edgar/data/0001050446/000119312526341297/mstr-20260810.htm) · [10-Q Q2 2026](https://www.sec.gov/Archives/edgar/data/0001050446/000105044626000044/mstr-20260630.htm) · [8-K 2026-05-26 (USD Reserve)](https://www.sec.gov/Archives/edgar/data/0001050446/000119312526237907/mstr-ex99_1.htm) · [Digital Credit Capital Framework](https://www.strategy.com/press/strategy-announces-digital-credit-capital-framework_06-29-2026) · [STRC ratchet / 12% hold](https://news.bitcoin.com/crypto-news/strategy-strc-dividend-12-percent-below-par/) · [MSCI removal proposal](https://cryptoslate.com/strategy-tells-msci-bitcoin-doesnt-need-you-as-2-8-billion-index-risk-hangs-over-mstr/) · [BTC price 8/14/26](https://fortune.com/article/price-of-bitcoin-08-14-2026/) · [The Block treasury tracker](https://www.theblock.co/treasuries/mstr)