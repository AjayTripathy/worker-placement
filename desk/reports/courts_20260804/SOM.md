# SOM — Somero Enterprises, Inc. | 3/10 AVOID
**Court** lse_shelf_20260804 · 2026-08-04 · shelf rank 23 · default-REJECT skeptic

## Identity / unit basis
Laser-guided concrete screeding machines (Boomed screeds, ride-on screeds, 3-D profilers). HQ Fort
Myers FL. **AIM-only listing**; IBKR line `SOMERO ENTERPRISES INC- REGS`, conid 299619675, LSE,
**quoted in GBp**. Reports **USD under US GAAP** (not IFRS). RNS name "Somero Enterprises Inc **DI**"
— the AIM line is a CREST Depositary Interest over US common stock.
Live IBKR 2026-08-04: **230.0p**, −2.13%, 68,141 shares, 52w 175–243, yield 3.38%; ties to shelf `px`
and the yfinance tape. 54,065,489 shares out (AR2025 BS: 54,257,375 issued less 191,886 treasury) →
cap **US$167.2m** at GBPUSD ≈1.345. Cap ÷ count reconciles to price.

---
## STRUCTURAL Q1 — is the Reg S line buyable in a US taxable account? **UNVERIFIABLE. It governs.**
Established: Somero is a **Delaware corporation** (auditor's opinion: *"Somero Enterprises, Inc. … a
Delaware corporation"*). Common stock **never registered** under the Securities Act. Entire SEC
history = **one Form D, 2009-07-02, Rule 506**. ISIN **USU834501038** — US-country ISIN with a
U-prefix CUSIP body, the convention reserved for **Reg S tranches**. IBKR's description says "REGS".
Three sources agree: unregistered Reg S stock of a US *domestic* issuer.

Why that is worse than for a foreign issuer: Reg S **Rule 905** deems equity of a *domestic* issuer
sold under Reg S to be **restricted securities under Rule 144**, and the restriction travels with the
shares — it does not season out through offshore trading the way a foreign issuer's Category-1 stock
does. This is permanently restricted US stock with a London order book.

Does US law forbid a US person buying it? **Not on its face.** The AIM seller relies on Rule 904
(offshore transaction on a designated offshore securities market — the LSE is named in Rule 902(b));
the US buyer takes restricted stock, resellable offshore under 904 or into the US under Rule 144
after the holding period. **The binding gate is broker policy, not statute**, and IBKR's "REGS" tag is
exactly the mechanism brokers use to block US-resident purchases. IBKR's Reg S documentation was
unreachable (404/403 every route); I did not place a test order. The live snapshot proves *data*
permission, not trading permission — and note `bid-ask` returned **empty** while the exchange touch
(225/235) populates on the shelf row.

**Ambiguous = refutation for sizing.** No capital is committable until an IBKR order is accepted or a
written eligibility answer exists. Kill #1.

## STRUCTURAL Q2 — the withholding tag is wrong and the "0% WHT edge" is a phantom
Shelf row carries `country_incorp: "JE"`, `wht: 0%`, `wht_edge_bps: 1500`.

**`country_incorp: JE` is REFUTED by two primaries.** Auditor's report says Delaware. Company IR page:
*"As the Company is incorporated in the **USA, not the UK**…"*; AIM Rule 26 gives country of
incorporation as **"United States of America"**. No Jersey entity exists in the group. EDGAR
`jurisdictionOfInc: DELAWARE`.

For a US taxable holder:
- Dividends are **US-source, from a US domestic C-corporation**. There is **no foreign withholding to
  avoid**, so the 1500bp "withholding edge" is worth **exactly zero here**. The argument that AIM's 0%
  dividend withholding is a structural holding-period edge **does not apply to SOM at all**. The shelf
  should carry `wht_edge_bps: 0`.
- Dividends should be **qualified** (domestic corporation, holding period met) → 15/20% + 3.8% NIIT.
  Identical to any US stock — no edge, no penalty.
- **UNVERIFIED operational risk:** Somero withholds under the *US NRA* regime, administered by a UK
  registrar (Computershare UK) into CREST Depositary Interests. Whether a W-9 survives IBKR's UK
  nominee chain, or the chain defaults to 30% withholding on a US holder, is unresolved — the
  company's withholding-statement PDF is not reachable. At a 3.38% yield that is ~100bp/yr, painful
  to reclaim through a foreign nominee.

**Third structural finding — neither regime's protections apply.** Somero files nothing with the SEC:
no 10-K, 10-Q, XBRL, Section 16, 13D/G or SOX 404 (CREST nominees keep the §12(g) record-holder count
low). And by its own AIM Rule 26 statement it is **not subject to the UK City Code on Takeovers and
Mergers** — no mandatory offer at 30%, no minority equality. AIM semi-annual disclosure on a US
operating company, with no takeover-code floor under it.

---
## Cause-check and the cyclicality frame
Somero sells the capital good that pours non-residential slabs — warehouses and distribution centres
above all. Operating income (the filer's own line, ties exactly to the screen):

| FY | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| EBIT US$m | 43.1 | 33.6 | 24.3 | **13.9** |
| Revenue US$m | — | — | 109.2 | 88.9 |
| EBIT margin | — | — | 22.2% | 15.7% |

US private **commercial** construction put-in-place (FRED TLCOMCONS, SAAR annual avg, $bn) — the
category containing warehouse/distribution: 2019 84.3 · 2021 97.4 · 2022 131.2 · **2023 151.5 (peak)**
· 2024 136.6 · 2025 129.3 · 2026 YTD 123.3.

The decomposition is decisive. Commercial put-in-place is **−15%** off its Sep-2023 peak and still
**+44% above 2019**. Somero's EBIT is **−68%** off its 2022 peak. **4.6x amplification** — and
Somero's peak *leads* the spending peak by a year, because it sells the machine before the pour and
equipment demand tracks the *change* in construction activity, not its level. Add ~2x operating
leverage (revenue −19% in 2025 → EBIT −43%) and that is the entire earnings history. **The 2021-22
earnings were the e-commerce warehouse build-out. This is non-residential construction-equipment
beta wearing a value multiple.**

The honest mirror of the commodity frame test: nothing here is *flattered* by a spot peak — the
opposite. **9.8x EV/EBIT is being paid on trough earnings at half the peak margin.** So the frame does
not reject for spot-artifact cheapness; it rejects because 9.8x trough EBIT is **not a discount to its
own history — it is what a cyclical trough multiple looks like**, and the shelf's composite scored the
name on a FCF yield and a net-cash ratio that are themselves trough artifacts. Management's claim that
"our variable cost structure enables us to remain profitable through economic cycles" is true as to
*profitable*, false as to *margin*: 32% → 15.7%.

**Peak test (#4):** `ebit_vs_peak` 0.32. **MELTING, confirmed** (trend and peak anchors agree, so no
trough-anchor illusion). Only a cycle turn rescues it.

**The cycle has turned — and the entry is late.** RNS 16-Jul-2026: "better-than-expected trading in
H1 2026"; FY26 revenue now to **exceed the $86.0m consensus** (consensus adj EBITDA $15.9m, adj PBT
$13.5m); Boomed-screed demand **improved after a three-year decline**; backlog "elevated throughout
the first half." Corroborated from the balance sheet: **customer deposits $0.505m → $3.561m, 7x**, for
contracts shipping post-year-end. But the bar is low — $86m was *below* FY2025's $88.9m, so "exceeds
$86m" means roughly flat, not a boom.

**Path (#8):** 230.0p, **+31.5%** off a 174.94p low of 2026-03-30 (**127 days**), **−5.3%** off the
242.92p high of 2025-10-22, **+27.8% in three months**, +5.8% over a year. **A late entry** — the
upgrade printed 16-Jul and the tape already has it.

## Capital allocation — the supplemental is gone
**Cut, explicitly.** FY25 final results (10-Mar-2026): *"No supplemental dividend declared for 2026
**in support of M&A Framework**."* "Supplemental" appears nowhere in the AR2025 framework, which now
reads: ordinary at **50% of adjusted net income**, offset award dilution, opportunistic repurchases,
"pursue value-accretive M&A." The ordinary was cut too — FY25 **10.24c** vs FY24 **16.93c** (−40%,
the KPI page prints "-40%"); cash dividends paid $15.8m → $9.3m.

Wrong direction twice: the cash return was cut *and* the released cash earmarked for acquisitions, by
a company at the bottom of its own cycle with no disclosed M&A record. **Shareholders revolted.** A
governance review was announced 5-Jun-2026 over "governance arrangements and legal constitution",
**board composition and capital allocation**, on post-AGM feedback (adviser Cavendish; NED search open
to replace Larry Horsch); changes need a **general meeting later this year**. Management partly
retreated: 2026 buyback $6.0m (12-Mar) → expanded (9-Apr) → **$12.0m (22-Jul)**, ~7.2% of cap, shares
cancelled — but purchases only **begin after the 8-Sep-2026 interims**. Total shareholder yield if it
all executes ≈10.5%.

## UK battery / mandatory checks
| Check | Result |
|---|---|
| **Pension by hand** | **NO DB scheme.** AR2025 **Note 7** is a **401(k) defined-contribution** plan, $990k contribution (2024: $1,022k); US GAAP, not IAS 19. `pension_unverified` correctly resolves to **clean** — nothing to strip from equity, nothing to add to EV. |
| **Capital commitments** | **CLEAN.** **Note 12** = renewable one-year employment agreements + routine litigation. **No contracted capital commitments** — the 10.2% FCF yield is not pre-spent. *But trough-flattered:* capex **$0.8m = 0.9% of sales** vs $2.4m in 2024, and **+$2.0m of guided 2026 opex**. |
| **Securities-as-cash / sign** | **CONFIRMED, screen conservative.** `st_investments` null, no sign conflict. Filer: *"Net cash at 31 December 2025 was US$33.2m (2024: US$29.5m)… debt-free with access to an unutilized US$25.0m secured revolving line of credit."* BS shows **zero borrowings**; the screen's $30.28m deducts $2.881m of lease liabilities and reconciles exactly. Restricted cash ~$333k. Filer net cash = **19.9% of cap**. |
| **Trust-safe / customer cash** | **FIRES, immaterial.** **$3,561,000** customer deposit liabilities (2024: $505,000). Adjusted net cash $29.6m = **17.7% of cap** vs screen 18.1%. The 7x *jump* is a positive order tell. |
| **Dual-class / share count** | **CLEAN.** Single common class; filing count reconciles cap ÷ count to 230.0p. Divergence is buyback vintage drift; true count today is lower, so the multiple is slightly overstated in our favour. |
| **Offer period / tender** | **CLEAN** — and structurally cannot be in a Code offer: **not subject to the UK City Code**. No `.TEN` line. |
| **PFIC** | **Clean** — 34% passive assets, active operating business. |
| **Staleness** | BS and flows both **31-Dec-2025 — seven months stale**. Only post-year-end hard data is the 16-Jul update; interims **8-Sep-2026**. |
| **Friction** | Stamp **0%** (AIM, SDRT-exempt since Apr-2014) + half of a **435bp** touch (225/235) = **~218bp entry, ~435bp round trip** — among the widest in the band. The 3.38% dividend needs ~13 months just to repay it, and Q2 puts even that at risk. |
| **Size** | **Median ADV US$156k** (IBKR's 90d mean $436k is block-inflated). 20% cap = **$31k/day**. 0.75% of $3.3M = $24.8k fills in ~1 session; stressed exit 3-8 sessions. **1 analyst, orphan.** |

Also: **foreign operations lose money** — AR2025 tax note, US income before tax **$17,776k**, **foreign
loss $(2,575)k**. The Europe/Australia growth story is a $2.6m annual drag; European revenue fell
**39%** to $8.9m.

## Findings
| Claim | Source | Result | Verdict |
|---|---|---|---|
| Line is Reg S stock of a US domestic issuer | ISIN USU834501038 + IBKR "REGS" + zero SEC registration | Rule 905 restricted securities | **CONFIRMED** |
| A US-resident IBKR account may buy/hold it | IBKR policy unreachable; no test order; law permits, broker gates | cannot establish | **UNVERIFIABLE** (governs) |
| `country_incorp: JE` | auditor's opinion; AIM Rule 26; EDGAR CIK 1467570 | Delaware, USA | **REFUTED** |
| `wht 0% = 1500bp edge` | US-source dividends from a US C-corp | edge = 0bp | **REFUTED** |
| Files with SEC EDGAR | full submission history, CIK 0001467570 | **one Form D, 2009. Nothing else, ever** | **CONFIRMED non-filer** |
| Not subject to UK Takeover Code | company's own AIM Rule 26 | confirmed by the issuer | **CONFIRMED** |
| Debt-free with real net cash | AR2025 BS + CEO statement | **$33.2m**, zero borrowings, $25m revolver undrawn | **CONFIRMED** |
| Net cash is shareholder cash | AR2025 customer-deposit note | $3.56m is customer advances; adj $29.6m | **CONFIRMED w/ haircut** |
| No committed capex | AR2025 Note 12 | employment + routine litigation only | **CONFIRMED** |
| No DB pension | AR2025 Note 7 | 401(k) only | **CONFIRMED** |
| Screen EBIT $13.942m | AR2025 "Operating income 13,942" | exact match | **CONFIRMED** |
| Earnings are the warehouse/non-res cycle | FRED TLCOMCONS vs EBIT history | PIP −15% vs EBIT −68%; 4.6x amplification | **CONFIRMED** |
| Supplemental dividend cut | FY25 results 10-Mar-2026 | *"No supplemental… in support of M&A Framework"*; ordinary −40% | **CONFIRMED** |
| Estimates now inflecting up | RNS 16-Jul-2026 | FY26 revenue to exceed $86m; Boom screeds up after 3 yrs | **CONFIRMED** |
| $12m buyback = 7.2% of cap | RNS 22/23-Jul-2026 | from $6m; starts after 8-Sep | **CONFIRMED** |
| Governance/capital allocation under review | RNS 5-Jun & 21-Jul-2026 | GM later this year | **CONFIRMED, unresolved** |
| US holder receives qualified, un-withheld dividends | withholding PDF unreachable; CREST DI chain | cannot establish | **UNVERIFIABLE** |

## Scenarios (12-18m, pence; 230.0p basis, GBPUSD 1.345)
- **Bear 30% → 169p** — July inflection was a restock; commercial PIP keeps sliding (−5%/yr) and the
  +$2m opex bites; FY27 EBIT ~$11m at 8x EV/EBIT.
- **Base 50% → 264p** — FY26 revenue ~$92m, EBIT ~$15m; FY27 EBIT ~$18m on Boomed-screed recovery;
  8.5x EV/EBIT + $30m net cash, count ~51.5m after the buyback.
- **Bull 20% → 388p** — full non-res upcycle, revenue toward $115m, EBIT $24m at 9.5x.

**E[FV] ≈ 260p → +13.1% raw; ~+9pp after the 435bp round trip.** A risk-premium payoff on a levered
read of the US non-residential capex cycle — not an edge, and gated on an ability to buy that I could
not verify.

## Ruling
**DERAILMENT — inflecting, entered late.** Not a de-rate: estimates did not hold while the multiple
compressed; EBIT fell 68% over three years and the multiple followed. The first upgrade in three
years landed 16-Jul-2026 and the tape has already paid for it. Secondary: **SCREEN ERROR** on
`country_incorp` (JE → DE) and the `wht`/`wht_edge_bps` fields flowing from it — a classification
defect worth fixing shelf-wide, though it is not what makes the name look cheap.

**Score 3/10 AVOID.** Three independent grounds, any one sufficient under a default-REJECT skeptic:
(1) executability is unverifiable on a Reg S line of a US domestic issuer, and the brief makes that
governing; (2) the frame is wrong — 9.8x on trough EBIT is a normal cyclical inversion, not quality
at a discount to its own history; (3) late entry into an already-fired catalyst with a 435bp round
trip and $31k/day of size. The financials, unusually, **verify clean** — this is not a bad company
and not a corrupted row on the money items. It is the wrong shape of security bought at the wrong
point of a cycle it cannot escape. **Below 4/10: no entry band, no tranche.**

## Kills
1. **IBKR rejects a US-resident order on conid 299619675 as Reg S / ineligible** → dead at any price;
   must be tested before any capital is contemplated.
2. Dividend arrives net of 30% US NRA withholding through the CREST/DI nominee chain → yield leg is
   ~2.4%, not 3.4%; re-run the carry.
3. **8-Sep-2026 interims**: H1-26 revenue below H1-25, or FY26 guidance walked back below $86m.
4. Any acquisition out of the $33.2m cash pile without a disclosed multiple and immediate accretion.
5. FRED TLCOMCONS 3-month average below $115bn SAAR → the cycle is still rolling over.
6. Governance-review GM dilutes the 50%-of-adjusted-NI payout policy in favour of M&A discretion.
7. Price above 260p before any entry → the whole base case is in the tape.

## Freezable call
**SOM | 2026-09-08 (interims)** — bar: FY2026 revenue guidance stated **at or above $92m** (above
FY2025's $88.9m). **our_p = 0.45.** The 16-Jul update only cleared an $86m consensus that was itself
below FY2025; the tape's +27.8% three-month move implies a stronger recovery than management has
actually guided to.

## Top unverifiable
Whether a US-resident IBKR taxable account can lawfully and operationally buy this Reg S line at all.
Everything downstream — including the 13pp of modelled edge — is conditional on it.
