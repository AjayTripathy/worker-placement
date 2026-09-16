# SNFCA — RED BENCH (adversarial court, default-REJECT the LONG)

**Security National Financial Corp** · NASDAQ: SNFCA · CIK 0000318673 · Fable tier
Date 2026-08-07 · Live px **$9.63** (IBKR cid 274491, close; bid 9.59×200 / **ask 15.31**×100)
Prior: ORPHAN_US_TRAP_VERIFY_20260807.md passed it REAL, court-worthiness 6/10.

Posture: this is an ORPHAN FAIR-CARRY candidate under HSBK/III doctrine — the fair-value
computation is itself the edge. So the red bench's job is not to find fraud. The trap-verify is
right that there is none. The job is to test whether **the computation was done correctly**, because
if the fair value is wrong the entire premise of the name is wrong.

**It was not done correctly.** Three of the four load-bearing numbers are overstated, and the
cost-of-equity bar was never struck at all.

---

## MODE B FIRST — the decisive questions, derived with no memo framing

Strip the pitch. A buyer of SNFCA is asking exactly three things:

1. **Is 0.59x book the real multiple?** (What is book, after every claim on it?)
2. **What P/B does an 8% ROE deserve?** (Not "book is 1.0x" — that is an assumption, not a fact.)
3. **Can I get the money out?** (Cash to holders, and exit through a $322k/day tape.)

The memo answers (1) with a partial book, never asks (2) at all, and treats (3) as a sizing
footnote. All three break.

---

## KILL LIST

### K-1 — The book value is missing a 22.4% option overhang. Cap structure was never pulled.

| | |
|---|---|
| **Claim** | BVPS $16.36, P/B 0.59x on 26.02M shares |
| **Method** | DEF 14A Equity Compensation Plan Information table, 12/31/25; adjust for the 5% stock dividend issued 2026-07-17 |
| **Authority** | https://www.sec.gov/Archives/edgar/data/318673/000149315226019219/formdef14a.htm |
| **Finding** | **REFUTED as stated** |

The proxy discloses **3,144,697 options outstanding at a weighted-average strike of $6.85**, plus
**2,397,748 shares still available for future issuance** under the 2022/2013/2014 plans. Adjusted
for the July 5% stock dividend: **3,301,932 outstanding at $6.52**, plus 2,517,635 authorized.
Combined that is **22.4% of the share count**.

The strike is not near book — it is **$6.52 against a $16.36 book**. Every option exercised converts
$6.52 of cash into a $16.36 claim on book. This is not a rounding item; it is a standing transfer of
roughly $10/share × 3.3M shares ≈ **$32M of book value** from outside holders to insiders, already
granted and mostly vested.

The Form 4 record confirms these are real and concentrated: parsing 26 recent filings, Adam G. Quist
alone carries option tranches summing ~798k shares, S. Andrew Quist ~736k, CFO Sill ~525k,
Overbaugh ~299k — with strikes running down to **$2.84, $3.27, $3.76, $3.91, $4.32, $5.56, $7.02**.
(The 495 Form 4s on this CIK are largely the annual anti-dilution restatement of every option
tranche for each 5% stock dividend — which is itself the tell that the stock dividend's main
function is to keep the option book whole.)

**The trap-verify pulled the treasury-share subtlety correctly and then stopped before the option
table.** That is precisely the failure the cap-structure doctrine exists to prevent.

### K-2 — AOCI is +$36.8M and *inflates* book. And it inflates asymmetrically, by construction.

| | |
|---|---|
| **Claim** | "LDTI rate-volatile AOCI" framed as a risk to book |
| **Method** | XBRL companyfacts; decompose Q1'26 AOCI move into liability vs asset legs |
| **Authority** | data.sec.gov/api/xbrl/companyfacts/CIK0000318673.json; 10-Q Q1'26 |
| **Finding** | **VERIFIED but mis-signed — it is a book *inflator*, currently at a cycle high** |

AOCI at 3/31/26 = **+$36,836,062** on $425,515,510 of equity = **8.7% of book, positive**. So the
$16.36 BVPS is 8.7% *flattered*, not depressed. Rate-neutral BVPS is **$14.94**.

The mechanism is a genuine measurement asymmetry, and it reconciles exactly:

| Q1'26 AOCI leg | Amount |
|---|---|
| LDTI discount-rate remeasurement of future policy benefits (after tax) | **+$11,483,503** |
| AFS bond mark: net unrealized went +$0.956M → −$3.360M | ≈ −$3.4M after tax |
| **Total AOCI move** | **+$8,073,939** ✓ (28,762,123 → 36,836,062) |

The liability being remeasured through AOCI is **$790,945,507**. The asset base that marks against
it in AOCI is the **$371,602,158** AFS book — **2.1x more liability than asset**. The rest of the
$705,213,000 fixed-income portfolio (mortgage loans held for investment) sits at amortized cost and
**never marks**, and $234,345,333 of real estate held for investment sits at depreciated cost and
never marks. So a rate rise books a large liability gain against a small asset loss: in Q1'26 the
liability leg was **3.4x** the asset leg, and book rose $8.1M on a rate move that made the company no
richer. FY2024 ran the same way at **+$35,523,326**.

**This is the trap the memo inverted.** Book value is not merely "rate-volatile" — it is
*ratcheted up by the rate cycle we just had*, and mean-reverts down when rates fall.

### K-3 — The mortgage-recovery catalyst and the book-value discount are NEGATIVELY CORRELATED.

This is the finding the memo's framing hid, and it is the mechanism that makes SNFCA structurally
un-ownable as a two-legged thesis.

The memo's bull case has two legs: (a) buy at 0.59x book, (b) the mortgage segment is a −$4.8M drag
today vs +$55.1M in FY2020, so earnings are cyclically depressed with upside.

**Leg (b) only fires if rates fall. Leg (a) only survives if rates don't.**

- Rates fall → origination volume recovers → mortgage segment swings positive (the $72.5M
  peak-to-trough range is real) → **and the LDTI liability remeasurement reverses, taking AOCI with
  it.** A move symmetric to FY2024's +$35.5M would remove ~8% of book. The 10-K's own asset-side
  table shows −100bps adds only **+$22,837k** to the $705.2M fixed-income portfolio — smaller than
  the liability leg, and mostly in buckets that never touch AOCI anyway.
- Rates stay high → book stays inflated → mortgage stays a drag → the 13% earnings yield stays the
  whole story, and that story is answered by K-5.

You cannot underwrite both legs at once. Any model that adds "cheap on book" to "mortgage cyclical
upside" is double-counting a single interest-rate variable in two directions.

### K-4 — The honest P/B is 0.70x, not 0.59x.

Compounding K-1 and K-2 on the 10-Q Q1'26 balance sheet ($425,515,510 equity; goodwill $5,253,783;
DAC $137,601,837), at $9.63:

| Basis | BVPS | P/B |
|---|---|---|
| As reported — **the memo's number** | $16.36 | **0.589x** |
| ex-AOCI (rate-neutral) | $14.94 | 0.645x |
| ex-AOCI, ex-goodwill | $14.74 | 0.653x |
| As reported, fully diluted for options | $15.25 | 0.632x |
| **ex-AOCI, ex-goodwill, fully diluted — the honest number** | **$13.81** | **0.697x** |
| + plan shares still authorized | $13.48 | 0.714x |
| + ex-DAC (acquisition basis, see caveat) | $9.12 | 1.056x |

**The headline understates the multiple by ~18%.** The claimed 41% discount to book is really a
**30% discount**, before we ask what discount is deserved.

*Caveat, stated honestly:* the ex-DAC line is a sensitivity, not my base case. DAC is a legitimate
going-concern GAAP asset and an acquirer replaces it with VOBA rather than zero. But it is
**$137.6M = 32.3% of equity**, it is capitalized commission with no liquidation value, and it is
excluded from statutory surplus. Anyone arguing "worth book in a sale" has to defend it, and the
memo never mentions it. The relevant tell: **statutory capital and surplus across all five insurance
subsidiaries is $139,068,212 against $425.5M of GAAP equity** (10-K Note 23).

### K-5 — THE STRONGEST KILL: an 8.1% ROE does not deserve 1.0x book. It deserves ~0.70x. That is where it trades.

| | |
|---|---|
| **Claim** | 0.59x book + 14% earnings yield = mispricing |
| **Method** | Justified P/B = (ROE − g)/(CoE − g), struck against the Damodaran US bar |
| **Authority** | pages.stern.nyu.edu/~adamodar/pc/datasets/wacc.xls, **updated 2026-01-05**: Rf **3.95%**, ERP **4.46%**, Insurance (Life) N=20 beta **0.6445**, CoE **6.82%** |
| **Finding** | **REFUTED — the discount is EARNED, not a mispricing** |

FY2025 ROE = $32,152,330 / avg LDTI-restated equity ($381,898,427→$410,368,728) = **8.12%**.
Book growth g ≈ 4–8%; use g = 4% (conservative, and buybacks are negligible).

| Cost of equity | Justified P/B |
|---|---|
| 6.82% — Damodaran Insurance (Life) **as published** | 1.460x |
| 9.82% — +300bp microcap illiquidity | **0.707x** |
| 10.82% — +300bp illiquidity, +100bp agency/control | 0.604x |
| 11.82% — +300bp illiquidity, +200bp agency/control | 0.526x |

**The honest P/B (0.697x) sits inside the justified band (0.53–0.71x).** SNFCA is not cheap. It is
**efficiently priced** for a $250M microcap earning 8% on book, with $322k/day of liquidity and a
permanent control block.

Damodaran's 6.82% is computed on 20 large, liquid US life insurers (MET/PRU/AFL/GL/PRI class). It
cannot be applied unadjusted to a name whose live quote is **bid 9.59 / ask 15.31**. The entire bull
case rests on using a large-cap discount rate on a microcap.

**The tape independently confirms the model.** Stock-dividend-adjusted, 2021-08 $6.746 → 2026-08
$9.63 = **+42.8% over five years = 7.38%/yr total return** (IBKR monthly bars, cid 274491). The
stock was "cheap on book" for that entire window. The discount did not close, and the carry did not
compensate — 7.38%/yr is below even the 8.41% unadjusted US market CoE.

### K-6 — Owner yield is ~0.4–0.6%, not 13%. And the constraint is the family, not the regulator.

| | |
|---|---|
| **Claim** | ~14% earnings yield; statutory capacity $11.4M is the binding constraint |
| **Method** | 10-K Item 5 dividend policy + Note 23 + buyback disclosure |
| **Authority** | https://www.sec.gov/Archives/edgar/data/318673/000149315226010228/form10-k.htm |
| **Finding** | **REFUTED — capacity is real but irrelevant; nothing is paid out** |

> "The Company **has never paid a cash dividend** on its Class A or Class C Common Stock. The Company
> currently anticipates that all its earnings will be retained… and **does not intend to pay any cash
> dividends** … in the foreseeable future." — 10-K FY2025, Item 5

> "The Company paid a 5% stock dividend on Class A and Class C Common Stock each year from **1990
> through 2019**, a 7.5% stock dividend for 2020, and a 5.0% stock dividend for **2021 through
> 2025**." — *ibid.*

**36 consecutive years of stock dividends and zero cash dividends.** A stock dividend is not a
return of capital — it is a split that transfers nothing and costs nothing, and whose principal
economic function here (K-1) is the anti-dilution restatement of the option book.

Actual cash to holders:

| Channel | FY2025 | Rate |
|---|---|---|
| Cash dividends | **$0** | 0.00% |
| Buybacks (XBRL PaymentsForRepurchaseOfCommonStock) | $1,610,049 | 0.64% |
| 2026 authorization: 10b5-1 executed 2026-02-16, **capped at $1,000,000**, purchases from 3/16/26 | $1.0M | **0.40%** |

**Realistic owner yield: 0.4–0.6%.** Roughly 95% of the 13.07% earnings yield never reaches the
shareholder in cash — it compounds inside a regulated box, into things like real estate held for
investment, which grew **$19.4M in Q1'26 alone** to $234.3M (14.8% of assets) and is carried at cost
less depreciation.

**I concede one attack here.** The MD&A says flatly that the subsidiaries "cannot pay dividends to
their parent company without the approval of state insurance regulatory authorities," which reads as
zero ordinary capacity. Note 23 governs and is more precise: Utah law permits Security National Life
approximately **$8,500,000** without extraordinary-dividend notice, and Louisiana permits Kilpatrick
and First Guaranty their amounts — the trap-verify's **$11.4M** aggregate is **VERIFIED and
disclosed**, not derived. The two passages are in mild tension (a disclosure-quality nit, not a
finding). But the point survives inverted and stronger: **capacity is not the binding constraint —
willingness is.** $11.4M could be upstreamed. $0 is paid. You cannot blame the Commissioner for a
policy the controlling family chose and has maintained since 1990.

### K-7 — The P/E is also overstated: 7.65x, not 7.2x. Stock-dividend units were mixed.

| | |
|---|---|
| **Claim** | TTM EPS $1.34, P/E 7.2x |
| **Method** | XBRL NetIncomeLoss; put EPS and BVPS on the same post-stock-dividend share count |
| **Authority** | companyfacts CIK0000318673; 8-K 2026-06-29 (5% stock dividend issued 2026-07-17) |
| **Finding** | **REFUTED (minor)** |

TTM net income = $32,152,330 (FY25) − $6,413,735 (Q1'25) + $7,001,426 (Q1'26) = **$32,740,021**.
The memo divides by **pre**-dividend shares for EPS but uses **post**-dividend shares for BVPS.
On a consistent post-dividend 26,016,709: **TTM EPS $1.258 → P/E 7.65x, earnings yield 13.07%**
(diluted: ~$1.22 → 7.90x). Small, but it is the same unit error as the treasury double-count the
trap-verify caught in the company's own cover page — this time in our own memo.

### K-8 — Governance: the discount is PERMANENT by 36 years of revealed preference, and the ratchet runs the wrong way.

**On the merits, the trap-verify is right that there is no abuse record**, and I affirm that:
board is majority independent (5 of 9), three of nine directors are elected by Class A voting
separately as a class, there are independent compensation and nominating committees, no
related-party leases/loans/asset transfers, and no Nasdaq controlled-company exemption claimed.
Related-party disclosure is limited to family employment. **No fraud, no looting, no self-dealing.**
That is a real anti-masking finding and I do not dispute it.

But "not abusive" is not "harvestable," and three facts say the discount never closes:

1. **The ratchet adds votes.** At the 2026-06-26 meeting shareholders approved reallocating
   **500,000 plan shares from Class A to Class C — adding 4,500,000 votes** at 10:1 (DEF 14A
   Proposal 2). Class C is already **14.1% of shares and 62.1% of votes**. Control is being
   *increased*, not sunset. There is no dual-class collapse provision.
2. **One of the three minority-designated board seats is held by a Quist.** The Class A separately-
   elected nominee slate is Fuller, Stephens, and **Adam G. Quist** — who is simultaneously a VP,
   General Counsel, and a $1.4M-comp executive. The minority's structural protection is one seat
   thinner than it appears.
3. **Insiders do not buy.** Across 26 parsed Form 4s (2025-12 → 2026-07) there is **not a single
   open-market purchase**. Every acquisition is an option grant, an option exercise, or a stock-
   dividend anti-dilution adjustment. The only cash transactions run the other way: **Fuller sold
   10,000 shares at $9.45 (2026-04-07, code S)**, plus disposals at $9.79/$9.46/$8.68 and gifts from
   Stephens (10,000), S. Andrew Quist (5,005) and Overbaugh (4,500/7,000 @ $9.54). The people with
   62% of the votes and the best information are monetizing at $9.63 against a claimed $16.36 book.

**Compensation, for scale** (DEF 14A Summary Compensation Table):

| NEO | 2025 | 2024 | Δ |
|---|---|---|---|
| Scott M. Quist (Chairman/Pres/CEO) | **$2,224,959** | $1,345,577 | +65.4% |
| S. Andrew Quist (VP Mortgage Ops, GC) | $1,484,524 | $1,080,924 | +37.3% |
| Garrett S. Sill (CFO) | $1,474,164 | $834,207 | +76.7% |
| Adam G. Quist (VP Life & Memorial, GC) | $1,399,786 | $979,272 | +42.9% |
| Jason G. Overbaugh (VP Nat'l Mktg) | $737,670 | $685,927 | +7.5% |
| **Top-5 total** | **$7,321,103** | **$4,925,907** | **+48.6%** |

Top-5 NEO comp rose **+48.6%** while net income rose **+10.4%** ($29.12M → $32.15M), and equals
**22.8% of net income**. Three Quists took $5.11M (15.9% of net income). Scott Quist's "All Other
Compensation" jumped from $52,563 to **$457,009** (8.7x); the itemized (a)–(d) elements — auto
$7,200, group life $168, life insurance $12,390, medical $19,015 — account for only ~$39k of it.

The comparison that matters: in FY2025 **five executives received $7.32M in cash and equity; all
outside shareholders received $0 in dividends and $1.61M in buybacks.** Management extracted ~4.5x
what the owners did. Nothing here is illegal or undisclosed — and that is exactly the point. **A
permanent, legal, disclosed transfer is a value trap, not a catalyst.**

---

## WHAT I COULD NOT VERIFY (UNVERIFIABLE ≠ CLEAN)

- **No Article 7 Schedule I/II restricted-net-assets schedule is filed** — "restricted net assets"
  returns zero hits in the 10-K. The parent-only balance sheet and the true upstreamable figure are
  **UNVERIFIABLE** from the filing.
- **Real estate held for investment ($234,345,333, 14.8% of assets)** — the 10-K carries no
  composition schedule I could locate (property type, geography, occupancy, cap rate). For the
  single largest non-insurance asset, growing $19.4M in one quarter and carried at cost less
  $38.6M accumulated depreciation, this is **UNVERIFIABLE** and is where ~95% of retained earnings
  is going. It deserves its own workstream before any capital is committed.
- **Decades-long litigation/enforcement record** — I did not complete a CourtListener/AAER/comment-
  letter sweep (subagent capacity exhausted). Governance conclusions above rest on the FY2025 10-K
  and 2026 proxy only. **UNVERIFIABLE for pre-2024 history.**
- **Peer P/B triangulation** (UTGN, AAME as controlled-microcap-life-insurer analogues) not
  completed. This is the single best test of whether 0.70x is a structural cohort discount — it
  would corroborate K-5 but is **not yet run**.

## WHAT I AFFIRM FOR THE DEFENCE (findings that survive my attack)

Honest reporting requires these:

- **MSRs at amortized cost (LOCOM), carrying $2.46M vs $3.99M fair value, valuation allowance $0** —
  the mark-up-through-P&L channel is structurally unavailable. **CLEAN, and a small hidden asset.**
- **Reinsurance is conservative and boring**: retention capped at **$100,000 per life**, only
  **8.0%** of face ceded ($316,251,000 of $3.95bn in force), unaffiliated authorized reinsurers,
  annually renewed. No coinsurance, no reserve financing, no offshore captive. **CLEAN.**
- **Mortgage repurchase tail is genuinely small.** The put-back window is narrow by contract —
  default in any of the **first four** payments, or early payoff within six months — not life-of-loan
  reps. Indemnification liability **$384,000** (down from $697,000). Against $2.30bn of originations
  this is a real, bounded tail. **CLEAN — I withdraw this line of attack.**
- **Earnings quality is good.** FY2025 core pre-tax ex-gains $36.77M of $41.41M reported (88.8%),
  up from $35.43M. The mortgage segment is a **−$4.76M drag**, so this is not peak earnings.
- **The $11.4M statutory dividend capacity is disclosed and correct** (Note 23). I concede this.
- **Credit quality is fine**: only 1.6% ($5,825,000) of insurance-subsidiary bonds are NAIC 3–6;
  90+ day delinquencies $6,516,000 with $1,204,000 in foreclosure on a ~$330M held-for-investment
  book (~2%); leverage modest at 80.7% equity/total capitalization.

**The company is honest.** Under the honesty-alpha framework this is a CLEAN name — every negative I
found is disclosed in the filings. My verdict is not a fraud call. It is that **the fair-value
computation, which under orphan doctrine *is* the edge, produces fair value at the current price.**

---

## LIQUIDITY REALITY — what is actually exitable

Verified: **$322,248** avg 90-day USD volume (IBKR `avg_90d_usd_volume`, cid 274491, 2026-08-07).
Live book: **bid $9.59 for 200 shares / ask $15.31 for 100 shares — a 59% spread.** Session volume 0.
The August month-to-date bar shows 54,250 shares across three sessions.

| Participation | Horizon | Exitable |
|---|---|---|
| 20% of ADV | 5 days | $322k |
| 20% of ADV | 10 days | $644k |
| 20% of ADV | 20 days | $1,289k |
| 10% of ADV | 20 days | $644k |

**Realistic cap: $300–400k**, and only with patience and no forced exit. The $15.31 offer is the
honest signal — there is no natural two-sided market. In any stress this name goes bidless, and the
5% annual stock dividend adds a recurring corporate-action friction on every position.

Note the arithmetic that kills the sizing case on its own: at a $300–400k cap, even a 30% re-rating
that took two years to arrive contributes **~4–6bps to a $5M book, annualized**. The name cannot pay
for the diligence it demands.

---

## CATALYSTS — enumerated, and there are none that fire

| Catalyst | Probability | Assessment |
|---|---|---|
| Cash dividend initiated | **Very low** | Explicitly disclaimed in the 10-K; never paid in 36 yrs |
| Meaningful buyback | **Very low** | Authorization capped at $1.0M = 0.40% of cap |
| Sale / take-private | **Very low** | 62.1% voting block; two sons installed as VP/GC — succession is internal, not a sale |
| Dual-class collapse | **Very low** | Ratchet runs the other way: +4.5M votes approved 2026-06-26 |
| Activist / 13D | **Very low** | Structurally impossible against 62% of votes |
| Index inclusion / coverage | **Very low** | $322k/day; no sell-side follows it |
| Mortgage cycle recovery | **Moderate** | The only real one — **and K-3 shows it cancels the book discount** |

**No fireable catalyst = dead money** (per standing doctrine). The single genuine catalyst is
negatively correlated with the valuation premise.

## THE CARRY MATH vs THE FAIR-CARRY BAR

The fair-carry bar (RP_FAIR) requires: fairness **VERIFIED** + tails bounded/unlevered + sleeve-capped
+ carry-vs-edge labeled.

- Expected return at a static multiple = book growth ≈ **8%/yr**, of which **~0.5%** arrives as cash
  and ~7.5% accretes to an illiquid, unharvestable book.
- Required return for a $250M microcap at $322k/day with a permanent control block = **~10–11%**.
- **Fairness test: FAILS.** 8% expected against a 10–11% bar is not fairly paid — it is
  *underpaid* for the illiquidity and agency risk borne.
- Realized 5-year evidence: **7.38%/yr**, consistent with the model and below even the unadjusted
  8.41% market CoE.
- Tails: bounded and unlevered (80.7% equity/capitalization) — **PASSES**.
- Liquidity: **FAILS** the exitability screen at any size that would matter.

Two of four gates fail. RP_FAIR is a *default-ownable* class only when fairness is verified; here it
is verified **negative**.

---

## STRONGEST KILL

**The 0.59x book is a computation error, and the corrected computation lands exactly on fair value.**

Adjust book for the two things the memo omitted — a **22.4% option overhang struck at $6.52 against
$16.36 of book**, and **+$36.8M of AOCI that a rising-rate cycle manufactured** — and the honest
multiple is **0.697x**, not 0.589x. Then strike it against a bar that was never struck: an **8.12%
ROE** discounted at Damodaran's Insurance (Life) **6.82%** plus the ~300bp illiquidity premium any
$322k/day microcap requires, growing at 4%, justifies **0.60–0.71x**.

**Honest P/B 0.697x. Justified P/B 0.60–0.71x. There is no discount left.** The market has priced
this correctly, and the five-year realized return of **7.38%/yr** — earned while the stock looked
"cheap on book" the entire time — is the out-of-sample confirmation. Under orphan doctrine the
fair-value computation *is* the edge; done correctly, it says there is none.

The governance overlay is the reason it stays that way: **36 years, zero cash dividends, a $1.0M
buyback cap, a voting ratchet that just added 4.5M votes, top-5 comp +48.6% against +10.4%
earnings, and not one open-market insider purchase.** The discount is not waiting to be harvested.
It is the price of admission, permanently.

## WHAT WOULD CHANGE MY MIND

Ranked by how much each would move me:

1. **A capital-return regime change.** An initiated cash dividend, or a buyback authorization ≥5% of
   market cap (vs today's 0.40%). This single fact would convert 13% earnings yield into real owner
   yield and would break K-6 outright. Tripwire: any 8-K or Item 5 change to the dividend policy.
2. **Proof that ~9.8% is the wrong cost of equity.** The whole verdict hinges on the illiquidity
   premium. At Damodaran's unadjusted 6.82%, justified P/B is **1.46x** and SNFCA is deeply cheap. If
   UTGN, AAME and comparable controlled microcap life insurers trade at or above 1.0x book, my
   premium is wrong and K-5 collapses. **This test is not yet run and I flag it as the defence's
   best available ground.**
3. **ROE inflecting above ~11% durably.** At 11% ROE and g=4%, justified P/B at a 9.82% CoE is
   **1.21x** and the name is genuinely cheap. The mortgage segment swinging from −$4.8M to its
   +$14.1M (2022) or +$55.1M (2020) range would do it — but K-3 requires you show the AOCI reversal
   does not eat the book at the same time. Show me both legs modelled jointly and I will re-open.
4. **A real estate schedule** showing the $234.3M is materially undervalued at depreciated cost —
   e.g. appraised value or cap-rate disclosure well above carrying. That is unmarked book, and it
   would be a genuine hidden asset. Today it is UNVERIFIABLE.
5. **Any credible sale/succession signal** — a banker retention, a 13D, an outside CEO hire, or a
   Class C sunset proposal.

## CONVICTION

**8/10** on REJECT.

Held back from 9–10 by two honest gaps: the peer P/B triangulation (item 2 above) is not run, and
Damodaran's own published life-insurance CoE of 6.82% would, taken at face value, make this stock
deeply cheap. My 300bp illiquidity add is standard practice and the 59% live spread plus the 7.38%
realized five-year return both corroborate it — but it is a judgment, not a measured input, and it
is the one number the defence can legitimately contest.

## RECOMMENDATION

# REJECT

Not because SNFCA is a bad company or a dishonest one — it is neither. Reject because:

1. The valuation edge **does not survive correct computation** (0.589x → 0.697x vs a 0.60–0.71x
   justified band). For an orphan fair-carry name where the computation *is* the thesis, this is
   dispositive.
2. The carry **fails the fairness gate** — ~8% expected against a ~10–11% required return, with
   ~0.5% of it in cash.
3. There is **no fireable catalyst**, and the one real catalyst is **negatively correlated** with the
   valuation premise.
4. Exitable size (**$300–400k**) is too small to matter even if I were wrong — a 30% re-rating over
   two years is worth ~4–6bps annualized on a $5M book.

**Not ALLOW-TO-BLUE on the current record.** The blue bench should only be convened if it can carry
item 2 of "what would change my mind" — a peer-cohort P/B study establishing that controlled
microcap life insurers do *not* structurally trade at 0.6–0.7x book. Absent that, blue has no ground
to stand on that I have not already conceded.

**Not FAIR-CARRY-SIZE.** Fairness is verified *negative*, and liquidity fails independently. The
fair-carry class requires fairness VERIFIED; here it is refuted.

---

*Every claim above is bound to a primary source: SEC EDGAR CIK 0000318673 (10-K filed 2026-03-16
acc. 0001493152-26-010228; 10-Q filed 2026-05-11 acc. 0001493152-26-022202; DEF 14A filed 2026-04-28
acc. 0001493152-26-019219; 8-K filed 2026-06-29 acc. 0001493152-26-031035; Forms 4 as cited), the
audited XBRL companyfacts API, IBKR live market data (cid 274491, 2026-08-07), and
Damodaran/NYU Stern waccUS dataset updated 2026-01-05.*
