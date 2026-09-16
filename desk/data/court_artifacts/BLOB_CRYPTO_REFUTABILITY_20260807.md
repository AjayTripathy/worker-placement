# Refutability Triage — Crypto-Financial Complex (discovery blob)
**Date:** 2026-08-07 · **Tier:** Opus volume · **Universe:** 19 members of a 95-name Finance:Consumer Services pocket, median −59% excess vs sector
**Analyst note:** all prices live from IBKR 2026-08-07; all coin marks from Coinbase spot 2026-08-07.

## Reference marks used throughout
| Asset | Spot 2026-08-07 |
|---|---|
| BTC | $64,313.53 |
| ETH | $1,901.46 |
| SOL | $72.895 |
| TRX | $0.326627 |
| XRP | $1.02655 |
| WLD | $0.2972 |
| WYFI (equity) | $25.50 |

**Regime context.** BTC ≈ −49% from its Oct-2025 peak, ETH ≈ −62%, SOL ≈ −75%. A −80% to −95% equity drawdown on a treasury vehicle is therefore *arithmetically expected* before any company-specific fact is considered. Desk case law applies: **beta-bleed is not a dislocation.** The triage below exists to find the handful of names where something other than coin beta is doing the work.

**Pocket contamination (finding in its own right).** The screen's "Finance: Consumer Services" pocket is not a clean crypto cohort. Six of nineteen are not crypto businesses at all: BRBI is a Brazilian investment bank, FRMI an AI/nuclear datacenter REIT, SUPX an AI-server vendor, DVLT a data/audio-AI company, BTQ a post-quantum *cryptography* company (pure name collision), AIIO a former Chinese auto parallel-importer. Any basket built off this pocket inherits those misclassifications.

---

# LEAD FINDINGS (Mode B first — derived without promoter framing)

## 1. BTBT — the marked-to-market holdco discount. **8/10**

The strongest item in the batch, and it is not a coin story.

Bit Digital is not a treasury shell; it is a **holding company whose largest asset is a controlling stake in a separately listed, non-crypto AI datacenter company.** From the 10-Q's own opening line: *"a Strategic Asset Company (SAC) focused on active participation in Ethereum (ETH) infrastructure while winding down its digital asset mining business. Through our controlling majority equity stake in WhiteFiber Inc. (Nasdaq: WYFI), the Company also engages in high performance computing ('HPC') business."*

**The arithmetic** (every input primary-sourced):

| Component | Value | Source |
|---|---|---|
| BTBT shares outstanding | 349,190,420 (as of 2026-05-11) | 10-Q cover, acc 0001213900-26-057116 |
| BTBT price | $1.36 | IBKR live 2026-08-07 |
| **BTBT market cap** | **$474.9M** | |
| WhiteFiber shares outstanding | 38,614,216 (as of 2026-05-12) | WYFI 10-Q, acc 0001213900-26-056212 |
| WYFI price | $25.50 | IBKR live 2026-08-07 |
| WhiteFiber market cap | $984.7M | |
| **BTBT's 70.1% stake** | **$690.2M** | ownership % stated in BTBT 10-Q, Note 20 |
| ETH held: 140,195.9 × $1,901.46 | $266.6M | BTBT 10-Q digital-assets table, 2026-03-31 |
| Cash | $79.5M | BTBT 10-Q balance sheet, 2026-03-31 |
| **Gross sum-of-parts** | **$1,036.4M** | |

**BTBT's WYFI stake alone ($690.2M) exceeds BTBT's entire market capitalization ($474.9M) by 45%** — and the buyer receives 140,196 ETH and $79.5M of cash on top, for free. Implied ratio **0.46x**; even charging a punitive $200M of unallocated holdco liabilities it is **0.57x**.

**Why holdco debt does not rescue the bear case.** The natural objection is that consolidated liabilities of $572.0M (2026-03-31) offset the stake. They do not, for two reasons. First, WhiteFiber's own leverage is already inside WYFI's $25.50 equity price — subtracting it again double-counts. Second, and decisively, the 8-K of 2026-05-27 (acc 0001213900-26-061574) shows Bit Digital's subsidiary Bit Digital Capital acting as **LENDER**, not borrower, under a Delayed Draw Term Loan to Enovum NC-1 Venture, a WhiteFiber subsidiary, to build out the Madison, NC datacenter. The holdco is deploying surplus capital *into* its sub. Holdco-standalone debt is minimal.

**Mechanism (masking × signal × latency).**
- *Masking channel:* BTBT's ticker, its SEC SIC code ("Finance Services"), its index/thematic membership and its entire headline narrative say "ETH treasury." Screens and thematic flows classify it as crypto beta and sell it with the complex. Its most valuable asset is a **non-crypto AI datacenter company**, and consolidation hides it — WhiteFiber's economics surface inside BTBT's P&L as an undifferentiated "cloud services" revenue line ($16.8M in Q1-26), never as a marked security.
- *Signal channel:* unusually clean. WYFI's own listed price is a daily, liquid, third-party mark. The divergence is directly observable on the tape: **WYFI trades at $25.50 versus its $17.00 August-2025 IPO price (+50%), while BTBT is −70% over the same window.**
- *Latency:* **indefinite, and this is the trade's principal weakness.** There is no forced catalyst. The discount closes only on a distribution/spin of WYFI shares, sell-side sum-of-parts initiation, or slow recognition. Holdco discounts are structurally persistent.

**Disconfirming evidence — actively hunted, and material.**
1. **Dilution is the real bear case.** Shares went 324,192,228 (2025-12-31) → 331,434,734 (2026-03-31) → 349,190,420 (2026-05-11): **+7.7% in about four and a half months** via an H.C. Wainwright ATM. Issuing equity at ~0.5x NAV is directly value-destructive and can offset the discount indefinitely. A discount that management arbitrages *against* shareholders is not an opportunity.
2. **The NAV is only as good as WYFI's own mark.** WYFI trades at roughly 2.1x its book equity. If AI-datacenter valuations are rich, the "discount" is measured against an inflated numerator. This is not a discount to hard assets; it is a discount to another equity's multiple.
3. Ownership of 70.1% is stated as of the May-2026 10-Q and is **not re-verified as of August**. No SC 13D/A or ownership-change filing by Bit Digital appears on WhiteFiber's docket, which is consistent with the stake being intact but does not prove it.
4. Q1-2026 net loss −$146.7M, driven by −$121.1M of digital-asset losses; the ETH leg keeps falling.
5. Cayman holdco — tax friction on any monetization.

**Metric to track:** (0.701 × WYFI market cap + ETH × spot + cash − holdco debt) ÷ BTBT market cap. **Next print:** Q2-2026 10-Q, due ~2026-08-14 — will restate both the stake percentage and the share count, i.e. it tests dilution and stake integrity simultaneously.

**Per desk doctrine this is a decisive, load-bearing finding and should be re-verified with full context and a stronger model before any action** — specifically items 1 and 3 above.

---

## 2. FWDI — below-NAV Solana treasury with a live, executing buyback. **7/10**

The only *classic* below-NAV treasury case in the group that survives scrutiny.

**Holdings are hard, not estimated.** From the 10-Q DIGITAL ASSETS note (acc 0001683168-26-003917), at 2026-03-31: **SOL 5,278,000 units**, cost $995,792,000, fair value $438,734,000 (an implied $83.12/SOL); plus fwdSOL (their own liquid staking token) $56,854,000; plus other tokens ~$11,704,000. Total digital assets $507,292,000.

| Component | Value |
|---|---|
| SOL 5,278,000 × $72.895 | $384.7M |
| fwdSOL, scaled by SOL move (×0.877) | $49.9M |
| Other tokens (scaled) | $10.3M |
| Cash (2026-03-31) | $16.6M |
| Less total liabilities (2026-03-31) | ($57.1M) |
| **NAV** | **$404.4M** |
| Shares (2026-04-30 cover) | 74,679,699 |
| **NAV per share** | **$5.42** |
| Price | $4.22 |
| **Ratio** | **0.78x — a 22% discount** |

**The discount-closing mechanism is real and already executing.** A **$1 billion** repurchase authorization (November 2025, running through 2027-09-30) has retired **12,390,000 shares for $65.4M through 2026-04-30** — roughly **14% of shares out in seven months**. Share count fell 86,145,514 (2025-09-30) → 74,679,699 (2026-04-30). Included was a privately negotiated block from **Multicoin at $4.44/share**, i.e. a PIPE insider exiting into the buyback. Leverage is modest and disclosed: **$40M from Galaxy Digital at a 3.4% weighted-average rate**, secured by fwdSOL — ~9% LTV. Staking generated $9.3M in the quarter on ~$495.6M staked, roughly a **7.5% annualized yield**.

**Disconfirming evidence.**
1. **Capital allocation is internally contradictory.** On 2026-06-01 Forward made an unsolicited **all-stock** bid for Brera Holdings/Solmate (SLMT) at 1.54 FWDI shares per SLMT share (acc 0001683168-26-004672). Issuing stock at 0.78x NAV to buy another vehicle, while simultaneously repurchasing that same stock as undervalued, cannot both be right. SLMT's board rejected it on 2026-06-06; SLMT's counsel then alleged an undisclosed Section 13(d) group involving Forward and RockawayX (acc 0001683168-26-004852). The Irish Takeover Rule 2.6 deadline was 2026-07-21 and **no firm-offer 8-K was filed**, so the bid appears to have lapsed — but the revealed preference for stock issuance is the concern, not the deal.
2. **Management instability** — an *Interim* CEO (Michael Pruitt), plus a further Item 5.02 officer change on 2026-07-20.
3. **The holdings are four months stale** (2026-03-31). They sold SOL over the prior two quarters (6,854,000 → 5,278,000, −23%) to fund buybacks. Selling assets at NAV to buy stock at 0.78x is accretive to NAV/share, so the direction is favorable, but the count must be refreshed.
4. **This is not an arbitrage.** A 22% discount is a second-order cushion on a first-order SOL position. Unhedged, you are ~90% long Solana; the discount is a rounding error against SOL's volatility.
5. DAT-sector discounts have been persistent — the closed-end-fund problem.

**Metric:** mNAV = market cap ÷ (SOL × spot + fwdSOL + cash − debt). **Next print:** fiscal Q3-FY26 10-Q (quarter ended 2026-06-30), due ~mid-August 2026 — **within about a week** — giving a refreshed SOL count and share count, a direct test of NAV/share accretion.

---

# QUICK KILLS AND MID-CASES

## BMNR — at NAV, not below it. **4/10**
The cleanest vehicle in the complex, and precisely therefore not a dislocation. Per the 8-K of 2026-08-03 (acc 0001493152-26-035752), as of 2026-08-02: **5,797,813 ETH** (4.8% of all ETH), 209 BTC, a $180M Beast Industries stake, a $61M Eightco/ORBS stake, and $173M cash and marketable securities. At live spot: ETH $11,024.3M + BTC $13.4M + $414M other = **$11,451.8M gross**, against total liabilities of just **$30.1M** (10-Q, 2026-05-31) — effectively debt-free. Shares 603,226,394 (2026-07-09 cover), less ~4.5M repurchased in the last week. Market cap ≈ **$10.95B**, so **≈0.96–1.00x NAV**.

A $4B repurchase authorization is live and 4,917,189 ETH (85%) is staked. Added to the Russell 1000 on 2026-06-26. **Open item:** a **9.50% Series A Perpetual Preferred (NYSE: BMNP)** was designated after 2026-05-31 (preferred carrying value was $0 at that date) — its size is not yet quantified and is a senior claim ahead of common; a $400–500M issue would move the ratio to ~1.00x. Also note the fiscal year-end change from Aug 31 to Dec 31 (8-K 2026-07-13), meaning an FY26 10-K for the year ended 2026-08-31 plus a Sep–Dec transition report. **Verdict: honest, liquid, well-structured ETH beta at fair value. Buy ETH instead if you want ETH.**

## BTGO — real franchise, but a dated supply overhang argues against acting now. **5/10**
Shares: 107,104,027 Class A + 8,855,382 Class B = **115,959,409** (2026-05-07 cover). Market cap **$568.2M**; corporate cash $186.6M; EV ≈ **$382M**; book equity $438.8M → **1.29x book**. The convertible preferred ($222.5M at 2025-12-31) fully converted at the IPO, leaving a clean cap structure. But **operating income turned negative: −$19.9M in Q1-2026 versus +$2.3M in Q1-2025.** Reported "revenue" of $3,773.6M is gross principal-basis trading turnover, not a fee line — do not use it for EV/revenue.

The decisive timing point: BitGo IPO'd in Q1-2026 (Class A went 33.8M → 106.8M shares in the quarter), so a standard **180-day lockup expiry lands right about now**. A dated, forecastable supply event on a name already −80% is a reason to wait, not to buy. Largest qualified crypto custodian is a genuine franchise; the entry is not yet.

## GEMI — a screen false-positive I disconfirmed. **3/10**
Worth recording as a methodology catch. Shares: 44,163,149 Class A + 75,126,784 Class B = **119,289,933** (2026-05-08). Market cap **$474.8M**. Balance sheet shows cash $215.6M and crypto assets held $271.9M = $487.6M, so a naive screen fires **"market cap below cash + own crypto."**

**That is wrong.** Reading the liabilities side: **related-party loans $252.6M**, third-party loans $75.3M, funding debt $140.5M — **$468.4M of actual borrowings** sitting beneath the cash. (Customer custodial funds $483.8M are properly matched by $483.7M due to customers; and 623 BTC / $42.5M of the crypto is pledged as collateral to insurers, so encumbered.) Net of borrowings the company trades at **≈1.04x book**, not below cash. Underlying: revenue flat ($50.6M in Q3-25 → $50.3M in Q1-26), **real operating cash burn $54.4M/quarter** against $215.6M cash — roughly four quarters of runway. Deterioration is genuine, fully disclosed, and correctly priced. **Honestly disclosed bad news is CLEAN, not alpha.** Q2 earnings due ~2026-08-14.

## XXI — a premium, not a discount; and the market may have misread the headline. **3/10**
43,515 BTC (10-K, 2025-12-31; corroborated by crypto fair value $2,951.6M at 2026-03-31) × $64,313.53 = $2,798.6M, plus cash $114.1M, **less $489.3M of liabilities** (convertible notes) = NAV **$2,423.4M**. Against a ~$2.84B market cap that is roughly **1.17x — a 17% premium.** Leverage cuts the wrong way: a further 50% BTC decline takes equity NAV down ~57%.

The idiosyncratic event is real but points the other way from the fear: the Item 3.01 8-K of 2026-05-20 sounds like a delisting notice and is **merely an audit-committee independence technicality** (two independent members fell to one on a director resignation; curable, and the company said it would appoint a replacement). The substantive news in the same filing is that **SoftBank exited entirely on 2026-05-19** — selling all 89,106,748 Class A shares to Tether International, with its 89,106,748 Class B shares cancelled. Control consolidated to Tether. Interesting, but a premium valuation removes the trade.

## ABTC — levered miner; coin and cash do not cover the debt. **3/10**
Shares: 24,004,726 Class A + 48,814,987 Class B = **72,819,713** (2026-07-30 cover) — market cap **$447.8M** (the headline "float" understates nothing here; blob matched). At 2026-06-30: **8,002 BTC** (fair value $478.9M) and cash $18.4M = $533.0M at live spot, against **total liabilities of $637.4M** — coin-plus-cash is **negative $104.4M** against the debt. Equity value therefore rests entirely on ~$812M of carrying-value mining hardware in a $64k-BTC world, and the fleet is burning: Q2 operating loss −$74.1M, net −$57.2M. Liabilities include a **$371.7M miner purchase liability** — a forward cash obligation into a bear market. A **1-for-15 reverse stock split effected 2026-07-02** is a listing-compliance tell (and explains the split-adjusted "52-week high of $217.80"). Trades at 0.67x an overstated book. Structural, honestly disclosed.

## BLSH — an anti-masking finding: the market is pricing it correctly. **3/10**
The hypothesis "operating exchange mispriced as a coin proxy" **fails on the facts**, and that is itself worth cataloguing. Bullish's balance sheet largely *is* a coin book — own-account digital assets held as principal for market-making. Total assets $3,956.5M against liabilities $658.2M, equity attributable to owners $3,216.2M (20-F, 2025-12-31); cash and equivalents only $87.9M because the liquidity is held in crypto. At 150,833,916 shares × $23.25 = **$3,507M**, about **1.09x a stale year-end book that has since shrunk with coin prices.** So the equity moves with coins because it substantially *is* coins — the classification is accurate, not lazy. Independently, the franchise is shrinking: monthly volume per the 2026-08-06 6-K has fallen from a $43.2B peak to **$20.9B in July 2026**. FY2025 loss −$785.5M. Reported "revenue" of $244.8B is gross turnover; the real fee line is "other revenue" $158.9M.

## BKKT — small operating turnaround, not dislocated. **4/10**
Equity $170.9M, cash $80.0M, liabilities $42.5M (2026-03-31) against a ~$318M market cap ≈ **1.86x book**. Losses are narrowing meaningfully (Q1-2026 net −$11.7M versus FY2025 −$107.2M). Not below cash, not a coin-NAV story. Treat as an ordinary small-cap operating turnaround; nothing in the drawdown is mispriced enough to court.

## TRON — premium to NAV. **2/10**
274,382,064 shares × $1.44 = **$395.1M** market cap against equity of $249.9M and near-zero liabilities ($2.8M) at 2026-03-31 — roughly **1.58x NAV**. A clean, unlevered balance sheet carrying a Justin Sun brand premium. Expensive, not dislocated.

## ORBS — trades above liquidation value; one unresolved thread. **3/10**
388,011,544 shares × $0.70 = **$271.6M** market cap. The Worldcoin leg is impaired well beyond the last balance sheet: crypto fair value was $175.3M at 2026-03-31 (an implied ~$1.75/WLD), and **WLD is now $0.2972 — a further ~83% decline.** Cash was $7.5M and liabilities $18.3M. Dilution has been severe: **205,629,592 shares (2025-12-31) → 388,011,544 (2026-05-15), +89% in five months.** On the coin leg alone the equity trades far *above* liquidation value.

The one thread that keeps this off a 1: BitMine's 2026-08-03 release marks its Eightco stake at **$61M** and describes it as *"one of the only publicly listed equities in the world to provide investors indirect exposure to OpenAI,"* implying ORBS now holds an OpenAI SPV interest. That pivot is unverified here and is the only reason to look again. **UNVERIFIABLE ≠ clean.** ORBS files weekly Item 7.01 updates (latest 2026-08-06) — cheap to monitor.

## TDTH — thin disclosure, unresolved funding question. **2/10**
Trident Digital (Singapore, foreign private issuer, 20-F/6-K only, 20-F filed 2026-04-28). The XRP treasury requires confirming **funded-and-purchased versus merely announced** — the distinction is the entire question for this name and is not resolvable from the filings reviewed. Reverse-split-adjusted 52-week high $42.30 against $2.44 today. Disclosure cadence is too thin to underwrite.

## CNCK — Japanese exchange, no edge identified. **3/10**
Coincheck Group N.V. (SPAC'd December 2024, FYE March 31, 20-F filed 2026-06-29). ~$403M market cap at $2.10. An operating Japanese exchange whose revenue tracks domestic crypto volumes; drawdown is consistent with that beta. Nothing in the reviewed filings separates it from the complex.

---

# NON-CRYPTO CONTAMINANTS
These are in the pocket by classification error, and their drawdowns have nothing to do with coin prices. Full primary-source workup completed. **Two of these are stronger findings than most of the crypto names** — and the direction is short/exclude, not long.

**Correction to my own earlier read, recorded faithfully.** I initially identified AIIO as the former Cheetah Net Supply Chain. **That was wrong.** AIIO is **NWTN, Inc.**, the East Stone de-SPAC and a Dubai EV maker (per formerNames in the EDGAR submissions JSON); Cheetah Net is an unrelated CIK. The stale "Motor Vehicles" SIC code is genuine but traces to NWTN, not Cheetah Net. My conclusion (dilution-funded fade) survived; my entity resolution did not. Also corrected: DVLT had **one** auditor change reported across two Item 4.01 8-Ks, not two.

## FRMI — the screen has this exactly backwards. **6/10 — ESCALATES**
Fermi Inc. is a **pre-revenue development-stage REIT-elect**, not a crypto company: Project Matador, ~7,500 acres / 17 GW of private power and datacenter campus on Texas Tech System land in Amarillo, next to DOE Pantex. Dual-listed Nasdaq + LSE. IPO'd 32,500,000 shares at **$21.00** (424B4 dated 2025-09-30), peaked at $36.99, now **$6.19**.

**The dated cause is a single clean event.** Per the 8-K of 2025-12-12 (Item 8.01), LOI exclusivity with the investment-grade "First Tenant" **expired at midnight 2025-12-09**, and on **2025-12-11 that tenant terminated the $150M Advance in Aid of Construction Agreement**. The week of 2025-12-08 opened $15.19 and printed an $8.30 low on 55.6M shares. **Fermi has never signed a binding tenant lease** — the 10-Q says plainly *"we have not entered into agreements with any tenants."* **Revenue has been $0 for every period of the company's existence.**

**Why the drawdown is not the opportunity the screen implies.** 637,574,239 shares (2026-05-11) × $6.19 = **a ~$3.95B market capitalization for a company with zero revenue, no signed tenant, and audited going-concern doubt.** The 10-Q states *"these conditions raise substantial doubt about the Company's ability to continue as a going concern,"* alleviated only by (i) the Yorkville note, (ii) equipment facilities, and (iii) the option to **liquidate its own turbines and transformers**. The Yorkville facility ($156.3M committed) requires **≥$10.0M of each monthly amortization payment to be paid in shares**. Debt stack: MUFG $500M ($396.6M drawn), Keystone $220M ($39.5M drawn), Beal $165M ($3.0M drawn), plus **$431.25M of 5.00% convertible senior notes due 2031** closed 2026-07-14 (conversion ~$9.52; capped-call cap $14.64, struck at a 100% premium, implying a ~$7.32 stock at pricing). The same 8-K disclosed Fermi **deferred its REIT election** and was taxed as a C corp for the short 2025 year.

**This is the takeaway-versus-data divergence.** The screen's takeaway is "deeply oversold, −83%." The data says **still ~$3.95B for a pre-revenue project with going-concern doubt and two hard binary tripwires**, both **2026-12-31**: the Texas Tech ground lease bars vertical construction absent a notice-to-proceed conditioned on **executing a Phase-1 tenant lease of ≥200 MW by 12/31/2026**, and the Keystone facility triggers **mandatory prepayment if no approved customer agreement by 12/31/2026**. That is a dated, binary, falsifiable structure — which is precisely what makes it court-worthy, on the **short/avoid** side.

**Governance is the corroborating signal, though the proxy fight is now dormant.** Co-founder **Toby Neugebauer** (Vicksburg Investments + family trust, **146,516,035 shares = 22.7%**, largest holder) sought a special meeting to expand the board by seven and remove three directors for cause, to run a dual-track sale process (DEFC14A 2026-06-10). The board responded on 2026-05-13 by unilaterally amending the bylaws to require a **70% supermajority** to change board size. **Both solicitations were withdrawn** — the second on 2026-07-03 citing the recusal of the Texas Business Court judge — so **no special meeting is currently pending**, and the other co-founder (Griffin Perry / Caddis) publicly backs the board. Separately, director **Miles Everson** resigned 2026-07-10 stating the $431M convertible *"was not brought to the Board for discussion or debate. In fact, I wasn't made aware of the transaction until the public announcement was made"* (Ex-17.1), and filed a rebuttal on 2026-07-19 after the company disputed him. The company **has never held a shareholder meeting**. Management churn: CEO out 4/17, CFO 4/19, interim CFO 4/29.

Q1-2026: revenue $0, cash $207.5M (from $408.5M), net loss −$188.7M (operating cash burn only −$7.3M; the loss is non-cash). **Next print: Q2-2026 10-Q, due ~2026-08-14.**

## DVLT — related-party revenue and an auditor who walked. **5/10**
Datavault AI (f/k/a WiSA Technologies). The auditor sequence is the finding, and the answer is that there was **no disagreement — which is the point**. BPM LLP, auditor since 2016, issued a **clean unqualified FY2025 opinion on 2026-03-18 with no going-concern paragraph** and exactly one Critical Audit Matter: *"Revenue Recognition—Patent and intellectual property licensing arrangements… Certain of these contracts are with related parties."* **BPM then resigned effective immediately on 2026-06-15.** Its Ex-16.1 letter is the bare minimum — *"We agree with the statements concerning our Firm contained therein"* — taking no exception. The company was then **25 calendar days with no auditor of record** before engaging CBIZ on 2026-07-10, scoped only to 2026 periods; **CBIZ has never audited a DVLT annual period.**

Why that CAM matters: **$30.0M of FY2025's $39.1M of revenue** was one-time IP-license revenue booked to **Scilex — a 43% shareholder** that bought 278.9M DVLT shares for $150M **paid in Bitcoin** — and its affiliate Vivasor. At 2026-03-31 the related-party receivable was still **$29.5M with zero allowance**. So roughly 77% of revenue is uncollected paper owed by a large shareholder, and the auditor flagged exactly that and then left.

Q1-2026: revenue $3.416M at a **3.2% gross margin**, net loss −$53.1M, **cash $2.205M**, shares **855,561,995 (2026-05-11) — 8.8× in nine months**. Management guides **$200M of FY2026 revenue** off a $3.4M quarter. Also: a **Wolfpack Research short report 2025-10-31**; a securities class action filed 2026-08-05 (E.D. Pa.); and an Item 3.02 letting **EOS Technology Holdings** take earnout stock at a fixed $0.61 (~2× market) where **Nathaniel Bradley is CEO of DVLT and CEO and sole director of EOS**. **Nearest hard catalyst: the Nasdaq Rule 5550(a)(2) bid-price cure deadline of 2026-08-24 — 17 days out — arithmetically unreachable at $0.314 on 855M shares without a reverse split.** 10-Q due 2026-08-14 but the earnings call is announced for 2026-08-19, five days *after* the deadline, with a first-time auditor doing its first review — a live NT tripwire.

## SUPX — an AI narrative with no AI revenue. **5/10**
A rebrand, not an operator: Junee Ltd (Hong Kong interior-design contractor, 40 employees) → SuperX AI (2025-10-03). The legacy fit-out business was sold 2026-05-07 for **$480k**. The load-bearing sentence is the company's own, from the H1-FY2026 6-K: ***"No revenue was generated from the AI infrastructure segment during the reporting period for the six months ended December 31, 2025."*** **One hundred percent of all revenue the company has ever reported is Hong Kong interior fit-out work.**

That is a genuine takeaway-versus-data divergence, and the insider-selling pattern corroborates it: roughly **19.3M shares sold at ~$12.08–$13.00 into a $48–$76 tape**, each tranche struck *"irrespective of fluctuations in market prices."* The 1,800,000-share placement at $13.00 closed 2025-11-19 (the stock was $48.85 when signed on 11-11) and **was not disclosed until a 6-K filed 2025-12-16**; the crash began the very next session (four consecutive double-digit down days, 2025-11-20 to 11-25). A **$20M buyback was authorized 2025-11-26 — one week after selling stock at $13.** Share count went 12.98M → 43.22M in 18 months. Integrity flags: **four audit firms in about three years**, with KD & Co. dismissed **2026-07-21, three weeks after fiscal year end**; **six material weaknesses**; **eight senior departures in eight months, including both audit-committee members within seven days of each other, roughly two months before the auditor was fired.**

**Why this scores 5 and not higher: the price has largely caught up.** Market cap ~$282M against **$188.05M of cash and only $0.40M of debt** — about 1.5x net cash. The finding's value is **exclusion** (keep it out of any AI or drawdown basket) rather than a trade. Next print: FY2026 20-F, due 2026-10-31.

## AIIO — the issuer's own registration statement prices the downside. **4/10**
NWTN/Robo.ai is a de-operated shell: its sole operating asset, ICONIQ Holding, was **sold for US$1.00** and replaced by stock-funded purchases of BVI entities with no disclosed revenue (Neurovia AI, $100M paid in 149,097,957 shares; QC Capital, $60M in 20,491,805 shares). **No crypto treasury.** FY2025: revenue **$0.950M** against **share-based compensation of $117.0M** — revenue was 0.8% of one year's stock comp. **Shareholders' deficit of −$116.1M**; total assets $8.44M against total liabilities $124.56M; **going concern unalleviated**, the 20-F stating *"no credible pathway to achieving financial stability has been demonstrated."* Four separate Nasdaq deficiencies and **three audit firms in ~20 months**, with Marcum Asia stating its FY2022 report *"contained errors and should not be relied upon."*

The brief's price path was an artifact of a **1-for-20 reverse split effective 2026-04-06**; split-adjusted, 2026-02-03 $3.99 → 2026-08-06 $3.05 is **−24%**, not the stated path. The real event was a **17× melt-up in ten sessions** ($0.5401 on 2026-04-30 → $9.20 on 2026-05-14), ignited on 167.9M shares the session after the all-paper Neurovia announcement.

**The single most probative number is the company's own.** Across four registration statements it has registered **80,978,349 Class B shares for resale in eleven months — 4.55× the entire post-split Class B count and 50.5% of shares outstanding.** The F-3 filed 2026-07-31 registers **34,810,127 shares against $25M of notes**, sized to a **$0.79 conversion floor** — roughly **74% below the current $3.02**. The issuer is disclosing where it expects the stock to clear. Free float is only ~29.6M shares, so the 22.3M effective plus 36.4M pending equals **~2.0× the float**.

**Capped at 4/10 for a specific reason: this is squeeze-prone, not a clean short.** A 17× move in ten sessions on a sub-$600M shell with a ~$90M float is exactly the configuration that has overturned short theses on this desk before. Treat as **exclude**, not as a borrow.

## BTQ — name collision, but with real going-concern doubt. **4/10**
BTQ Technologies is a **post-quantum cryptography** company — it is in this pocket purely on the word "crypto," almost certainly caught by the 2026-01-12 "Bitcoin Quantum Testnet" release rather than any digital-asset operation. The classification is an artifact. But the company is not clean: **MNP LLP's audited opinion carries an explicit emphasis paragraph** — *"a material uncertainty exists that may cast significant doubt on the Company's ability to continue as a going concern"* — repeated in Q1-2026 and in the ATM prospectus. **The only revenue it has ever booked came from "a company controlled by the former COO"** (C$315,497 in FY2025; **Q1-2026 revenue was C$nil**). Cash fell to **C$12.13M** at 2026-03-31, −42% in one quarter, against a quarterly loss of C$19.93M — roughly 1.5 quarters of runway. The funding plan is a **C$150,000,000 ATM via Cantor** launched 2026-06-18, which is **~6.4× total shareholders' equity of C$23.3M**. Note all figures are **Canadian dollars**. The −75% drawdown from the October-2025 quantum-mania peak is sector beta, not a company event. Next print: Q2-2026 interim, due 2026-08-14.

## BRBI — confirmed artifact. Do not trade this line. **1/10**
BRBI BR Partners S.A. is a genuine, profitable **Brazilian investment bank** (São Paulo, IFRS, four segments, R$6.2bn wealth AUM, **17.5% ROE**). Zero crypto exposure. The US line is **not the company's stock**: it is an **ADS representing FOUR UNITS**, each unit being 1 common + 2 preferred, listed only ~12 months (Form 20FR12B 2025-07-21). **246,555 ADSs outstanding against 57,220,464 units — the entire US line is ~1.7% of the units, roughly $2.8M of value**, on recent weekly volumes of 101, 200 and 300 shares.

The arithmetic settles it. In the week of 2025-09-22 the US line printed a **$63.68 open and $67.01 high — about 4.7× fair value** — and **closed the same week at $13.52**, within 5% of the theoretical $14.21 (4 × R$19.01 ÷ 5.35). **That one bad first-week print is the entire "drawdown."** Measured from the first valid print, $13.52 → $11.43 is **−15.5%**, and today's ADS sits at a **+3.3% premium** to its own theoretical value (4 × R$14.12 ÷ 5.1017 = $11.07). Currency was a **tailwind** (USDBRL 5.4372 → 5.1017, the real appreciated ~6%), and **no ADR-ratio change occurred**. The home line's −35% is an ordinary bank cyclical on Selic at 14.25%, with the ADS at ~1.03× book on a 17.5%-ROE bank. **Kill on data quality — this name indicts the screen, not the issuer.**

---

# COURT-WORTHINESS

```
COURT-WORTHINESS BTBT: 8/10 — 70.1% stake in listed WhiteFiber worth $690.2M vs BTBT's entire $474.9M market cap, plus 140,196 ETH and $79.5M cash free; holdco is a net LENDER to its sub, so consolidated debt does not offset; discount marked to a liquid third-party price, with ATM dilution the live counter-risk.
COURT-WORTHINESS FWDI: 7/10 — 5,278,000 SOL + fwdSOL net of a $40M Galaxy loan gives $5.42 NAV/share against $4.22, a 22% discount being actively converted by a $1B buyback that has already retired 14% of shares; contradicted by an all-stock bid for SLMT that would issue stock at that same discount.
COURT-WORTHINESS FRMI: 6/10 — screen reads "oversold −83%" but the data reads ~$3.95B for a ZERO-revenue project with audited going-concern doubt and no binding tenant ever signed; anchor tenant terminated 2025-12-11 and two hard binary tripwires both hit 2026-12-31, making it court-worthy on the SHORT/AVOID side.
COURT-WORTHINESS BTGO: 5/10 — largest qualified crypto custodian at 1.29x book with $186.6M corporate cash and a clean post-IPO cap structure, but operating income flipped to −$19.9M and a ~180-day IPO lockup expiry lands now, so the supply event argues wait.
COURT-WORTHINESS BMNR: 4/10 — 5,797,813 ETH essentially debt-free at $30.1M liabilities with a $4B buyback live, but ~0.96–1.00x NAV is fair value not dislocation; unquantified 9.50% Series A perpetual preferred is the only open item.
COURT-WORTHINESS BKKT: 4/10 — operating turnaround with losses narrowing from −$107.2M FY25 to −$11.7M in Q1-26, but 1.86x book and not below cash leaves no dislocation to court.
COURT-WORTHINESS GEMI: 3/10 — screens as below cash+crypto but $468.4M of borrowings including $252.6M related-party loans refutes it; ~1.04x book with $54.4M quarterly cash burn and flat revenue is honestly disclosed decay, correctly priced.
COURT-WORTHINESS XXI: 3/10 — 43,515 BTC less $489.3M convertibles gives $2.42B NAV against a ~$2.84B cap, a 17% PREMIUM; the scary-sounding Item 3.01 was only a curable audit-committee technicality masking the real news, SoftBank's full exit to Tether.
COURT-WORTHINESS ABTC: 3/10 — 8,002 BTC plus cash of $533.0M does not cover $637.4M of liabilities, so equity rests on carrying-value miners burning $74.1M a quarter; 1-for-15 reverse split on 2026-07-02 is a compliance tell.
COURT-WORTHINESS BLSH: 3/10 — anti-masking finding, the coin-proxy pricing is CORRECT because the balance sheet substantially is a coin book; 1.09x a stale book with monthly volume halved from $43.2B to $20.9B.
COURT-WORTHINESS ORBS: 3/10 — trades far above liquidation value with WLD down a further 83% since the last balance sheet and shares up 89% in five months; held off a 1 only by an unverified OpenAI-SPV pivot implied by BitMine's $61M mark.
COURT-WORTHINESS CNCK: 3/10 — operating Japanese exchange whose drawdown tracks domestic volume beta; nothing in the 20-F separates it from the complex.
COURT-WORTHINESS SUPX: 5/10 — company's own 6-K admits "no revenue was generated from the AI infrastructure segment," so 100% of revenue ever booked is HK interior fit-out; ~19.3M shares sold at ~$12 into a $48-76 tape, buyback authorized a week later, 4 auditors in 3 years — an exclusion finding, but at 1.5x net cash the price has caught up.
COURT-WORTHINESS TRON: 2/10 — 1.58x NAV on a clean unlevered balance sheet is a Justin Sun brand premium, the opposite of the below-NAV case being hunted.
COURT-WORTHINESS TDTH: 2/10 — whether the XRP treasury was ever funded versus merely announced is unresolvable from 20-F/6-K disclosure alone, and that question is the entire name.
COURT-WORTHINESS AIIO: 4/10 — NWTN de-SPAC (NOT Cheetah Net, my error), sole asset sold for $1.00, shareholders' deficit −$116.1M, going concern unalleviated; registered 4.55x its entire Class B for resale and the F-3 is sized to a $0.79 floor vs $3.02, but a 17x melt-up in 10 sessions on a ~$90M float makes it squeeze-prone — exclude, do not borrow.
COURT-WORTHINESS DVLT: 5/10 — $30.0M of $39.1M FY25 revenue is uncollected paper owed by a 43% shareholder with zero allowance, which was the auditor's sole Critical Audit Matter before it resigned effective immediately, leaving 25 days with no auditor; Nasdaq bid-price cure 2026-08-24 is arithmetically unreachable.
COURT-WORTHINESS BTQ: 4/10 — name collision on "crypto" with zero cryptocurrency exposure, but carries an audited going-concern emphasis paragraph, C$nil Q1 revenue, and the only revenue it ever booked came from a company controlled by its former COO; C$12.1M cash against a C$150M ATM that is 6.4x equity.
COURT-WORTHINESS BRBI: 1/10 — CONFIRMED ARTIFACT: the "$67" was a bad first-week print at 4.7x fair value on an ADS representing 4 units, the same week closed at $13.52 within 5% of theoretical, and the line trades at a +3.3% premium today; whole US listing is ~246k ADSs worth ~$2.8M.
```

---

# METHOD NOTES AND CAVEATS

**Verified.** Coin counts, share counts (all classes), liabilities, cash and buyback authorizations for BTBT, FWDI, BMNR, XXI, ABTC, GEMI, BTGO, BLSH, ORBS, TRON, BKKT come from the cited 10-Q/10-K/20-F/8-K primary documents, cross-checked against XBRL company facts. Live equity prices from IBKR and coin spot from Coinbase, both 2026-08-07.

**Share-count check performed and cleared.** A systematic worry going in was that the blob's market caps used Class A float only, which would make dual-class names look artificially cheap. Checked against cover pages for GEMI (119,289,933), BTGO (115,959,409), ABTC (72,819,713) and BLSH (150,833,916): **the blob is using total shares in every case.** No float artifact.

**Unverified / stale — stated as such.**
- BMNR's Series A perpetual preferred size (designated after the 2026-05-31 balance sheet date).
- BTBT's 70.1% WhiteFiber ownership is as of the May-2026 10-Q, not re-confirmed for August; no contrary ownership filing found, which is supportive but not proof.
- FWDI's SOL count is as of 2026-03-31; the company has been selling SOL to fund buybacks.
- FWDI's fwdSOL and other-token values are **scaled by the SOL price move (×0.877), not independently marked** — an approximation, flagged.
- XXI's current share count is inferred from the blob's market cap divided by live price, not read off a cover page; the 89.1M Class B cancellation in May is confirmed but the resulting total is not.
- ORBS's implied OpenAI-SPV pivot is asserted by a third party (BitMine) and not verified against Eightco's own filings.
- TDTH's XRP funding status is UNVERIFIABLE from the documents reviewed.
- AIIO's 2026-05-13/14 leg to $9.20 has no SEC filing behind it — cause UNVERIFIABLE. DVLT's 2026-08-05 −24.0% move on ~15× ADV likewise has no 8-K — trigger UNVERIFIABLE.

**Errors made and corrected, recorded for calibration.** (1) I identified AIIO as the former Cheetah Net Supply Chain; it is **NWTN, Inc.**, an unrelated de-SPAC. Entity resolution failed even though the conclusion (dilution-funded fade) held — a reminder that a right answer reached through a wrong entity is luck, not method. (2) I read DVLT as having two auditor changes; it had one, reported across two Item 4.01 8-Ks. (3) My first pass on GEMI fired a "below cash + crypto" signal that the liabilities side refuted.

**Score revisions after the contaminant workup.** FRMI 5→6 (escalates), SUPX 3→5, DVLT 2→5, AIIO 2→4, BTQ 2→4. The revisions all run in the same direction: **the non-crypto contaminants were systematically under-scored on the first pass because I was triaging them as classification noise rather than as companies.** Being in the pocket by mistake is not the same as being uninteresting.

**Honesty-alpha framing.** Nothing in this batch is a detected liar. BMNR, FWDI, ABTC, GEMI and BLSH all disclose their impairment clearly and frequently — several weekly. Under desk doctrine, re-detecting honestly disclosed bad news is not alpha. The two names that scored are structural mispricings (a holdco discount and a NAV discount), not integrity findings, and both are graded on takeaway-versus-data divergence: in BTBT's case the *market's* takeaway ("ETH treasury") diverges from the company's own data (its largest asset is a listed AI datacenter company).
