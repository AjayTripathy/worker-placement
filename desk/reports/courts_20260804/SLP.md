# SLP — SYLVANIA PLATINUM LIMITED · LSE court 2026-08-04 · **3/10 NOT-A-DRAWDOWN (frame-reject)**

## Identity and unit basis
Sylvania Platinum Limited, AIM (TIDM SLP), ISIN **BMG864081044** — **Bermuda-incorporated**
(Clarendon House, 2 Church Street, Hamilton HM11; confirmed in the 31-Jul-2026 RNS). Reports in
**USD**; quotes in **GBp (pence)**. Six chrome-tailings retreatment plants (Sylvania Dump
Operations, "SDO") in the South African Bushveld, plus a 50% chrome JV (Thaba) and three Northern
Limb exploration projects.

- Price basis: yfinance `SLP.L` close 04-Aug-2026 = **79.0p**, ties to the shelf `px` field exactly.
  IBKR conid 89258385 @LSE quoting **live** (not close) at 77p intraday, prior close 75p — same
  session, up day. Both venues agree the unit is pence.
- Shares: **260,135,883 voting** (H1 FY26 note 12: 271,661,725 issued less 11,525,842 in treasury).
  Screen's `filing` count is right; `lse_implied` 245.7M is stale. 260.14M × 79p = £205.5M =
  **$276.3M** at 1.344 — ties the shelf `mktcap` to the dollar. Share-count check CLEARS.
- Fundamentals staleness: the screen's balance sheet is 31-Dec-2025 (7 months old). I have gone
  past it — the 31-Jul-2026 Q4 RNS carries 30-Jun-2026 cash and the full FY26 quarterly P&L.
  **Audited FY26 results land 15-Sep-2026** (six weeks out; not inside the 2-week print blackout).

## Cause-check — what actually happened
Peak 127.5p on **28-Jan-2026**, the exact day platinum spot peaked (~$2,606). Then:
March 2026 four sessions of −7.6% to −9.2% as the PGM complex broke (89.6p by 31-Mar); a chop to
110.6p on 07-May; grind to 83.2p by 30-Jun as platinum fell to $1,550; then **31-Jul-2026 −10.1%
on 6.38M shares (~7× median volume)** — the Q4 operations report. Now 79p, **−38% off the high**.
The shelf's `−28.6% 3m` anchors on the 07-May local peak; measured 04-May→04-Aug it is −20.2%.
The shelf's `days_since_low 365` is a window-boundary artifact (the 52-week low is the oldest bar);
the stock is in fact **8% above its 13-week low of 72p**, having round-tripped the entire rally.

What the 31-Jul RNS said: **record** annual production 95,885 4E oz (FY25: 81,002), guidance beaten
— and adjusted Group EBITDA **−65% q/q to $16.9M** because the 4E gross basket price fell **−25%
to $2,299/oz** (Q3: $3,047). Costs +8%. That is the whole story.

## CHECK 5 — COMMODITY FRAME TEST: **FIRES, decisively**
| FY | Avg 4E gross basket $/oz | 4E oz produced | EBIT $M | Source |
|---|---|---|---|---|
| 2022 | 2,890 | 67,053 | 79.4 | AR2023 Directors' report |
| 2023 | 2,086 | 75,469 | 61.9 | AR2023 Directors' report |
| 2024 | 1,339 | 72,704 | 7.5 | AR2025 Directors' report |
| 2025 | 1,507 | 81,002 | 23.9 | AR2025 Directors' report |
| 2026 | ~2,418 | 95,885 | ~105 (est) | four FY26 quarterly RNS |

Volume rose **43%** monotonically across the window. EBIT went 79 → 62 → 7.5 → 24 → ~105. Fit:
**EBIT on basket alone R² = 0.77; EBIT on volume alone R² = 0.19; the two together R² = 0.98.**

Counterfactual: hold the basket at FY25's $1,507 and leave FY26's costs and record volumes as
reported — FY26 EBITDA falls from **$116.5M to $21–32M**, i.e. at or *below* FY25's $29.3M despite
18% more ounces (Thaba's cost drag more than eats the volume gain). **Price explains ~95–110% of
the entire earnings swing; volume explains none of it net.**

Within-year control, where volume is held nearly constant by nature: Q3→Q4 FY26, ounces **+4%**,
basket **−25%**, EBITDA **−65%**. Operating leverage on the basket ≈ **2.7×**.

Implied engine: annual EBITDA ≈ **0.096 × (basket − ~$1,200/oz)**, fitted on FY25 and FY26 and
consistent with the reported group cash cost of $1,034/4E oz. At today's EV of ~$214M, the market
is paying 4× EBITDA on a **mid-cycle basket of ~$1,750/oz** — a ~25% discount to spot. Owning SLP
*is* a bet that the mid-cycle PGM basket sits above $1,750. That is a commodity forecast, not a
quality-at-a-discount trade. **Frame-rejected: the 2.0× EV/EBIT is a spot-price artifact, and the
market's refusal to capitalise cycle-peak PGM earnings is a permanent, rational feature — not a
de-rate that reverses.**

Company-specific overlay (the part that is *not* the basket): the **Thaba JV chrome leg derailed**.
Guidance path FY26 — original ~90–100kt → cut to 60–90kt (Jan-26) → "revised ramp-up plan"
(Feb-26) → cut to 50–55kt (Apr-26) → delivered **50,317t, the bottom of the third cut**. Thaba
chrome cash cost **+77% q/q to $232/t**. Meanwhile the PGM leg was guided *up* twice (83–86k →
90–93k → 95.9k delivered). SDO executes; the growth leg does not.

## The UK/AIM battery
- **Pension by hand — NO SCHEME.** Verified, not assumed. The `pension_gross $6,098,244` is the
  non-current **Provisions** line, and AR2025 note 22 shows it is **environmental rehabilitation**
  in full ("closure, restoration and environmental rehabilitation… dismantling and demolition of
  infrastructure"). Bermuda holdco, South African subsidiaries — there is no DB scheme to find, no
  surplus inflating book equity, no deficit to add to EV. The screen's debt-like treatment
  ($4.57M net of 25% tax) is directionally correct and immaterial. **P/B 1.02 stands unadjusted.**
- **Capital commitments (the THX lesson).** AR2025 note: *"commitments signed for continued
  improvements of the plants amounted to **$8,721,594** (2024: $5,451,386)"* — 13% of the cash
  pile, not a THX-scale earmark. But two things the commitments note does **not** capture: FY26
  capex ran **$31.8M** with Q4 alone at $12.5M (+256% q/q, including a property purchase for a new
  Eastern-limb plant), and Sylvania has lent **$38.8M to its JV partner** (below). The cash is not
  pre-committed by contract; it is pre-committed by the ramp.
- **Friction:** AIM ⇒ **0% stamp**. Median touch 253bp ⇒ half-spread **~127bp all-in on entry**,
  ~253bp round trip. The 0% dividend WHT is a holding-period edge and does not repay that inside
  two years on a 5.3% yielder.
- **Executability / size:** conid 89258385 verified live @LSE, 566k shares traded 04-Aug, median
  ADV **$851k**, 20%-of-prints cap **$170k/day**, NMS 15,000 shares. A 0.75% position ($24.8k)
  fills inside one session. Access and size are not the constraint here.

## The other mandatory screen-corruption checks
1. **Securities-as-cash — fires MILDLY, corrected.** Screen `cash $56,535,895` = true cash
   $53,955,595 **plus $2,580,300 of "Other financial assets — current"**, which H1 note 10 shows is
   the current slice of **loans receivable from the JV partner**, not cash. `st_inv_share_of_cash
   0.046` is real. Honest figures at 31-Dec-25: net cash **$48.8M = 17.7% of cap**, not 18.6%.
   *No sign inversion* — the company's own Q3 RNS says *"the Group remains debt free."*
2. **Net cash re-verified on fresher data.** 30-Jun-2026 group cash **$67.198M** (excludes $1.1M
   restricted guarantees) against total leases + borrowings of ~$0.56M. Net cash ≈ **$66.6M = 24%
   of the $276M cap**. The claim survives and improves.
3. **…but it is not fully shareholder cash — a leak the screen cannot see.** ~$45M of it sits in
   ZAR in the South African subsidiaries. **South Africa levies 20% dividends withholding tax on
   upstreaming to the Bermuda parent, and there is no SA–Bermuda treaty.** AR2025's tax table
   proves this is live: FY2024 DWT paid **ZAR49.87M ($2.63M)** on internal dividends; FY2025 nil
   only because no internal dividend was declared. Haircut ≈ **$9M**, so the economically
   distributable net cash is nearer **$58M (21% of cap)** than $66.6M.
4. **Unusual items (`unusual_r −0.198`) — IDENTIFIED.** The **$12,263,788 impairment of the Hacra
   exploration and evaluation asset**, H1 FY26 (note 8), taken after management decided not to
   spend more on the project. Vendor EBIT $61.8M vs reported $50.1M reconciles to within $0.5M.
   Live tail: **$37.2M of exploration assets remain capitalised** (Volspruit, Far Northern Limb) —
   13% of market cap, at cost, with one write-off already taken.
5. **Trust-safe cash:** not applicable — no customer or client float.
6. **Trough anchor:** `ebit_vs_peak 0.77` is measured against a *stale* peak. On the FY26 figures
   just reported, EBIT is at an **all-time high, ~1.3× the FY22 peak**. Not melting — but see the
   frame test: that is the problem, not the reassurance.
7. **Path check:** full round-trip, not a late entry. 8% above the 13-week low, 38% below the
   January high. `days_since_low 365` is a boundary artifact and should not be read as "stale low".
8. **Incorporation field is WRONG.** Shelf carries `country_incorp: "GB"`. The ISIN prefix is
   **BM** and the registered office is Bermuda. Harmless for the WHT answer (both 0%), but the
   field is wrong and would misfire on any UK-specific rule keyed off it.

## South Africa specifics
- **Eskom / power:** real cost and reliability drag, not existential. AR2025 — Tweefontein shares
  electrical infrastructure with its host mine; host-mine demand at times crowded out Sylvania's
  grid access and **diesel consumption rose ~175% y/y**; a permanent new Eskom supply is being
  commissioned. Q4 FY26 — a buried power cable failed at Tweefontein (hurt flotation recovery) and
  there was a **"historic electricity cost adjustment" at the SDO**. Restricted cash includes
  guarantees lodged with **Eskom** and the DMPR.
- **Feedstock:** SDO owns no ore. It retreats chrome tailings — historical dumps plus higher-grade
  "current arisings" — from **host mines** under agreements. **The FY25 principal-risks register
  does not name host-mine feedstock supply or agreement renewal as a risk at all.** For a business
  whose entire input is somebody else's waste stream, that omission is the single most notable
  disclosure gap in the report.
- **ZAR:** revenue USD, costs ZAR — so a *stronger* rand is a margin headwind. R/$ went 17.64 →
  17.12 → 16.37 → 16.50 across FY26 (spot 16.41): the rand **strengthened ~7%**, which is why USD
  cash costs fell less than ZAR costs. AR2025's impairment model assumes a long-run **19.97**
  ZAR/$ — materially weaker than spot, i.e. the carrying values lean on rand depreciation.
- Other: a contract security officer was **killed in a criminal attack at Tweefontein in April
  2026**; 50% unionised workforce; mineral royalty tax; 27% SA corporate tax (H1 FY26 effective
  rate 36.8% including royalties).

## Bermuda: withholding, and the tax point the shelf gets backwards
- **`wht 0%` HOLDS**, but for the Bermuda reason, not the UK one. Bermuda imposes no dividend
  withholding tax. No treaty or reclaim is needed. CONFIRMED.
- **But for a US taxable holder the dividend is almost certainly NOT a "qualified dividend."**
  §1(h)(11) requires the payer to be incorporated in a US possession, *or* eligible for a
  comprehensive US income-tax treaty, *or* have stock readily tradable on a US exchange. Bermuda
  has no comprehensive US income-tax treaty (only the 1986 insurance/mutual-assistance treaty) and
  SLP has no US exchange listing. So the ~5.3% yield lands at **ordinary rates (~40.8% top with
  NIIT) rather than 23.8%** — roughly **90bp/yr of drag**, which cancels most of the 60bp the
  shelf credits for the missing withholding. **The shelf's `wht_edge_bps: 1500` overstates the
  benefit to this account.** Flagged for the tax adviser, not self-certified.
- **PFIC: clean, confirmed.** Income test — interest income $2.7M on revenue $99.8M = 2.7%,
  nowhere near 75%. Asset test on an FMV basis — passive assets (cash $54.0M + JV loans $38.8M +
  restricted $3.5M ≈ $96.3M) against an FMV asset base of ~$327M = **29%**. Trade receivables from
  metal sales are active. The de-rate-manufactures-status mechanism would need the cap to fall to
  ~41p with the cash intact; not a live risk, but it is the tripwire.

## Findings table
| Claim | Source | Result | Verdict |
|---|---|---|---|
| EBIT is a V that has tripled | 4 annual reports + 4 quarterly RNS | 95–110% of the swing is the basket price; volume adds nothing net | **REFUTED as a business improvement** |
| Net cash +18.6% of cap | H1 FY26 balance sheet; Q4 FY26 RNS | True cash 17.7% at Dec-25; **24% ($66.6M) at Jun-26**; company says "debt free" | **CONFIRMED (improved)** |
| …and it is shareholder cash | AR2025 tax table (DWT ZAR49.9M FY24) | ~$45M sits in SA subs; 20% SA DWT to upstream, no treaty; ~$9M haircut | **PARTIALLY REFUTED** |
| `st_inv_share_of_cash 0.046` | H1 note 10 | $2.58M is the current slice of JV loans receivable, not cash | **CONFIRMED as a defect** |
| Capital commitments | AR2025 note | $8,721,594 signed (2024: $5.45M) — 13% of cash | **CONFIRMED, modest** |
| No pension exposure | AR2025 note 22 | Provisions = environmental rehabilitation in full; no DB scheme exists | **CONFIRMED** |
| `unusual_r −0.198` | H1 FY26 note 8 | $12.26M Hacra exploration impairment | **CONFIRMED** |
| Share count / cap | H1 note 12 | 260,135,883 voting × 79p × 1.344 = $276.3M, ties exactly | **CONFIRMED** |
| 0% dividend WHT | Bermuda incorporation | Holds — but dividends are non-qualified for a US taxable holder | **CONFIRMED w/ material offset** |
| PFIC clean | H1 financials, market cap | 2.7% passive income, ~29% passive assets FMV | **CONFIRMED** |
| Thaba JV is a growth leg | Q2/Q3/Q4 FY26 RNS | Guidance cut three times, delivered the bottom of the last range | **REFUTED** |
| $38.8M lent to the JV partner | H1 note 10 | LMC capital loan $30.5M + working-capital loan $7.9M (nil a year ago), +$2.7M in Q4 | **CONFIRMED — unpriced credit risk** |
| Host-mine feedstock risk disclosed | AR2025 principal risks | Not named anywhere in the risk register | **REFUTED (disclosure gap)** |
| Not in a Takeover Code offer | LSE_OFFER_PERIODS + RNS | Confirmed; the only corporate action is an on-market buyback launched 23-Mar-2026 | **CONFIRMED** |

## Scenarios (12 months, pence; the only real variable is the 4E basket)
Engine: annual EBITDA ≈ 0.096 × (basket − $1,200). Spot basket ≈ $2,500–2,600 (Pt $1,761,
Pd $1,358 on 04-Aug — both +13% since the 30-Jun reference used for Q4 revenue).
- **Bear (p 0.30) → 55p.** Basket reverts to the FY25 $1,500 level. EBITDA ~$29M; Thaba stays
  loss-making and the LMC loan takes a provision; dividend cut. ~4.5× EV/EBITDA.
- **Base (p 0.45) → 100p.** Basket holds ~$2,300 (below spot). EBITDA ~$105M, but the market keeps
  paying only ~2.75× EV/EBITDA for cycle-peak PGM earnings. Net cash builds.
- **Bull (p 0.25) → 175p.** Basket $3,000+ on a persistent supply deficit and Thaba reaches its
  original 90kt chrome plan. EBITDA ~$188M at 3× — haircut because the multiple never expands.

**E[FV] ≈ 105p vs 79p = +33%.** *This number should not be trusted and is not the basis of the
ruling.* Every pence of it is a probability I assigned to a platinum price. We have no verified
edge on the PGM basket, so the "+33%" is a forecast dressed as an edge — precisely the artifact
the frame test exists to catch.

## Ruling and score — **3/10, NOT-A-DRAWDOWN (commodity frame-reject)**
Not a DE-RATE: estimates did not stay stable while the multiple compressed — the earnings power
itself moves 10× with an exogenous price, and it is currently at an all-time high, not a trough.
Not a DERAILMENT of the core: SDO beat guidance twice and set a production record at falling ZAR
unit costs. Not a SCREEN ERROR: the balance sheet, share count and multiple all survive primary
verification. It is a **PGM basket-price expression wearing a 2× EV/EBIT costume**, with a genuine
but secondary derailment in the chrome growth leg.

Points for: debt-free, 24%-of-cap cash, real free cash generation, a stated ≥40%-of-FCF dividend
policy actually paid, an on-market buyback, disciplined operations, honest and detailed quarterly
disclosure, and a full price round-trip rather than a late entry. Points against: the entire P&L
is one price; the multiple will not re-rate because it is not supposed to; $38.8M is lent to a JV
partner whose mine does not work; $37.2M of exploration assets sit at cost behind a fresh
write-off; the cash carries a 20% exit toll; and the dividend is taxed as ordinary income here.

**No entry band, no tranche, no size** (score < 4). Under the house frame this is a commodity beta
expression, not EDGE and not verifiably-fair RISK_PREMIUM.

## What would bring it back to court
1. Thaba reaching steady state — two consecutive quarters at ≥20kt chrome with cash cost back
   under $150/t, and the LMC capital loan beginning scheduled repayment.
2. A basket-independent earnings source large enough to break the R² — chrome at >25% of EBITDA.
3. A structural PGM supply argument we can verify from primary data rather than assert.
4. Price below ~55p (the bear FV) where the basket assumption stops being load-bearing.

## Kills / tripwires (if it were ever held)
- 4E gross basket below $1,600/oz for two consecutive quarterly reports → earnings back to ~zero.
- Any provision or extension against the $38.8M LMC loan.
- Chrome guidance cut a fourth time, or FY27 chrome guided below 60kt.
- A further exploration-asset impairment against the remaining $37.2M.
- ZAR below 15.00/$ sustained (margin compression on a USD revenue / ZAR cost book).
- FY26 final dividend (15-Sep-2026) below 2.0p — would signal the board sees the cycle turning.

## Freezable call
**SLP | 2026-10-31 | Q1 FY2027 adjusted Group EBITDA prints ABOVE Q4 FY2026's $16.9M | our_p 0.85.**
Direct test of the transmission model: spot basket is ~13% above the June reference used for Q4,
production is at a record run-rate and Thaba improved post-period. If this fails, the
0.096 × (basket − $1,200) engine above is wrong and every number in this court needs re-deriving.

## Top UNVERIFIABLE
The **host-mine chrome-tailings supply agreements** — their counterparties, tenure, renewal terms
and the split between depleting historical dumps and higher-grade current arisings are disclosed
nowhere in the annual report, and the risk register does not mention them. SDO's entire feedstock,
and therefore the whole business, rests on contracts we cannot read. Second: FY2027 production and
capex guidance, which will not exist until 15-Sep-2026.
