# LSE MAIN + AIM SMALL-VALUE SHELF — first intake

**Generated** 2026-08-04 · **Module** `verticals/generators/lse_shelf.py` · **Data**
`verticals/generators/data/LSE_SHELF.json` (249 scored rows) ·
`…/LSE_UNIVERSE.json` (1,599 lines) · `…/LSE_OFFER_PERIODS.json` (39 live offer periods) ·
`…/lse_conids.json` (4 verified) · registered `gen_lse_shelf`, weekly, enabled.

**Funnel.** 1,599 exchange-listed equity lines (LSE Main 989 + AIM 610) → 505 outside the
$50M–$2B band, 373 financials/vehicles, 138 fund-named, 113 non-ordinary share lines, 41
duplicate issuer lines → 418 in band → 310 clear a **median** $75k/day turnover floor → 301
scored → **249 on the shelf**, of which **210 are printable** (31 demoted for earnings
durability, 9 demoted because they are in a live takeover offer period).

**This is a ranking of cheapness, not a buy list, and section 3 is the reason.** Six names were
checked against their own annual reports and **three screen numbers were refuted** — including a
sign inversion on net cash at what was then the 4th-ranked name.

---

## 1. What is structurally different about this pond

**(a) Most of the LSE Main Market is not operating companies.** 310 of 989 Main-Market equity
lines — 31% — are closed-end investment companies under the exchange's own ICB classification;
415 of 1,599 across both venues are investment vehicles or property once REITs and real-estate
services are added. Any screen reaching the UK through a generic vendor "region = GB" query is
scoring a fund register. That is why the universe here is the **exchange's own price-explorer
API**: the LSE hands over ICB sector, market segment and ISIN, and it does not truncate.

*Related:* a vendor `region=gb` query returns three venues — LSE, **IOB** (the International
Order Book, where foreign GDRs such as the account's own HSBK line trade) and **Cboe UK**
(`.XC`, duplicate lines of LSE stocks). Two thirds of the quote lines a naive UK screen sees are
depositary receipts or duplicates.

**(b) AIM's stamp-duty exemption is more than eaten by AIM's spread — and only the exemption
gets discussed.** Measured on this shelf from live exchange touch prices:

| | n | median touch | median ADV (median day) | median cap | stamp on buys | entry friction |
|---|---|---|---|---|---|---|
| **AIM** | 118 | **234 bp** | $244k | $208M | 0.0% | ~**117 bp** (half-spread) |
| **Main** | 131 | **20 bp** | $1.32M | $643M | 0.5% (UK-incorporated) | ~**60 bp** (50bp SDRT + 10bp) |

AIM is roughly **twice as expensive to enter** despite paying no stamp duty, and the same names
are the ones you cannot size. The 0% withholding edge — worth about 60bp a year on a 4%-yielding
name against a 15% treaty-reclaim baseline — does not repay a 234bp round trip inside two years.
**The UK edge is a HOLDING-PERIOD edge, not an entry edge**, and only a strategy that intends to
hold for years can collect it.

**(c) The 0% withholding is an incorporation fact, not a listing fact.** Of 249 shelf names, 233
are UK-incorporated, **9 Jersey, 5 Irish, 1 Isle of Man, 1 Guernsey**. Jersey/IoM/Guernsey also
withhold nothing; the **5 Irish issuers withhold 25%** with a reclaim. Incorporation is read per
name from the exchange's instrument record, never inferred from the `.L` suffix.

**(d) The acquirable slice is narrow.** Capping orders at 20% of a median day's prints, only
**3 of the top 15** support a $100k+ single-day order (VTY $1.4M, CAML $307k, AEP $251k, SRB
$197k). Most of the rest cap at **$18–60k/day**: a 0.5% position on a $5M book fills in a day, a
1% position takes most of a week. Size the tranche to the tape before liking the multiple.

---

## 2. Top 15, court-ready order

Shared deep-value composite (mean rank-percentile of EV/EBIT, FCF yield, P/B, net-cash/cap,
NCAV/cap). Durability-demoted and in-offer names already excluded. **`vs peak` is EBIT against
its own 4-year peak** — the anchor that matters, see 4(e).

| # | TIDM | Name | Mkt | Cap $M | EV/EBIT | FCFy | P/B | NetCash/cap | vs peak | Why it is here | Trap flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **THX** | Thor Explorations | AIM | 489 | 1.6x | 41% | 1.18 | +0.32 | 1.05 | Producing gold miner at ~1.6x EBIT with a third of the cap in net cash; EBIT is *above* its own peak, so the cheapness is not a trough artifact | **VERIFIED-WITH-OMISSION: US$254M of Douta capex is earmarked against a US$137.8M cash pile — the FCF yield is pre-committed** · reserve disclosure is the undepleted DFS figure and no remaining mine life is stated · 370bp touch · $58k/day |
| 2 | **CHH** | Churchill China | AIM | 57 | 6.2x | 12% | 0.69 | +0.18 | 0.55 | Below book with real net cash and a double-digit FCF yield; 200-year-old branded ceramics | **REFUTED FLAG: the screen said "no pension" — there is a DB scheme, in SURPLUS, £7.65M recognised as an asset = 12% of equity, so P/B 0.69 is really ~0.78** · EBIT 0.55x peak — melting · 260bp touch · $18k/day |
| 3 | **SRB** | Serabi Gold | AIM | 253 | 2.3x | 16% | 1.27 | +0.24 | 1.24 | Brazil gold producer at 2.3x EBIT with a quarter of the cap in net cash — and **verified clean: no contracted capital commitments at all** | **Textbook trough anchor: the legacy oldest-year trend reads 38.8x against 1.24x on the peak** — the "growth" is a base effect · 400bp touch · reports USD |
| 4 | **ACSO** | Accesso Technology | AIM | 152 | 8.5x | 17% | 0.78 | +0.19 | 1.00 | Ticketing/queueing software below book, net cash, EBIT at its own peak; tightest touch in the AIM top ten (81bp) | **IBKR carries an `ACSO.TEN` tender line plus two subscribed-rights lines — check for a live tender / return of capital before treating this as an entry** · share count unverified · customer-cash model (scored trust-safe) |
| 5 | **GENL** | Genel Energy | Main | 189 | n/a | 7% | 0.54 | +0.60 | −0.09 | 60% of the cap in net cash at half of book | **EBIT is NEGATIVE** — a cash shell with a Kurdistan receivable, not an earner · **PFIC-flagged on the FMV test** · WC-driven FCF · at a 6-day-old 52-week low · Jersey |
| 6 | **LBG** | LBG Media | AIM | 96 | 3.9x | 6% | 0.86 | +0.19 | 0.80 | 3.9x EBIT below book with net cash — social publisher | Late entry: +36% off a 56-day-old low · 299bp touch · $20k/day · mean ADV block-inflated |
| 7 | **AEP** | AEP Plantations | Main | 923 | 6.1x | 9% | 1.59 | +0.27 | 0.88 | Palm oil at 6.1x EBIT, 27% of cap in net cash, near-zero debt, **57bp touch and $251k/day** — the most executable name in the top ten | **+98% off its 52-week low: the entry is exhausted** · reports USD, quotes GBX · pays 0.5% stamp |
| 8 | **KMK** | Kromek | AIM | 74 | 4.6x | 23% | 0.97 | −0.06 | n/a | 23% FCF yield at book — radiation detection | **859bp touch, the widest on the shelf** · zero analyst coverage · durability-watch (rescued only because it generated cash on both sides of the EBIT cross) · slight net debt · +75% off the low |
| 9 | **CAML** | Central Asia Metals | AIM | 342 | 4.3x | 13% | 1.20 | +0.19 | 0.61 | 4.3x EBIT, 13% FCF yield, net cash, **14bp touch and $307k/day** — the best size-to-cheapness trade-off on the shelf | EBIT 0.61x peak — melting on the peak anchor, invisible on the legacy one · Kazakhstan / North Macedonia assets · reports USD |
| 10 | **OMG** | Oxford Metrics | AIM | 58 | n/a | 4% | 0.71 | **+0.24** | −0.06 | Below book with net cash | **CORRECTED IN-RUN: "+0.66 net cash" was 57% short-term INVESTMENTS, not cash — the honest figure is +0.24** · EBIT negative · PFIC-flagged · capitalised-intangible heavy · 6-day-old low |
| 11 | **VTY** | Vistry Group | Main | 1,222 | 6.1x | 19% | **0.27** | −0.49 | 0.74 | Cheapest P/B on the shelf, 19% FCF yield, **17 analysts** — the only *covered* name here, so the discount is not neglect, and $1.4M/day of size | **VERIFIED: the £269.8M provision is Building Safety Act cladding remediation (£213.2M of it), not pension — 230 buildings under remediation, spend phased evenly across 2026-28** · £827.6M goodwill = 25% of equity, impairment trigger identified · also has a £32.2M pension SURPLUS the screen cannot see |
| 12 | **WYN** | Wynnstay Group | AIM | 114 | 9.8x | 11% | 0.63 | −0.05 | 0.42 | Agricultural supplies at 0.63x book | **EBIT 0.42x peak — melting** · 1 analyst · 408bp touch · **NMS is 300 shares** · no pension tag on a legacy distributor · $18k/day |
| 13 | **SPR** | Springfield Properties | AIM | 159 | 6.8x | 27% | 0.69 | −0.40 | 0.97 | 27% FCF yield below book — Scottish housebuilder | Net debt 40% of cap · provisions proxy on a housebuilder means **read the building-safety note, not IAS-19** · 302bp touch |
| 14 | **CLBS** | Celebrus Technologies | AIM | 57 | n/a | 7% | 1.47 | +0.55 | −0.18 | Over half the cap in net cash | EBIT negative · PFIC-flagged · WC-driven FCF · +44% off a 36-day-old low |
| 15 | **TFW** | Thorpe (F.W.) | AIM | 386 | 7.3x | 8% | 1.54 | +0.18 | 1.05 | Professional lighting, EBIT at its peak, net cash, family-controlled compounder | Trough-anchored on the legacy trend · 1 analyst · 233bp touch · $26k/day |

**Dropped out of the top four by the in-run fix:** **CAPD (Capital Ltd)** ranked 4th on "+11% of
the cap in net cash". Its own accounts say **net debt US$31.8M**. See 3(a).

---

## 3. Primary verification — six names, three refutations

Checked against company annual reports and results statements, not aggregators.

**(a) CAPD — REFUTED, sign inverted.** Screen: net cash +11% of cap, EV/EBIT 5.6x, rank 4.
Authority: Capital Ltd Annual Report 2025, Going Concern §1.3 and CFO review — **loans and
borrowings $94.8M, cash $63.4M, net debt $31.8M**, 0.4x adjusted EBITDA. Cause: the vendor's
`Other Short Term Investments` held **$99.8M of listed junior-miner equities at fair value
through P&L**, which the screen netted against debt as though it were cash. Note 20 also shows a
**$66.0M realised and unrealised fair-value gain** running through FY25 — a mark-to-market on
mining equities, not services earnings, which will distort any EBIT- or FCF-derived multiple.
**Fixed in-module** (guard (o)): CAPD now prints −0.22 net cash and 7.6x, reconciling to the
filer's figure once IFRS-16 leases inside Total Debt are backed out, and it is out of the top 15.
The same guard cut **OMG** from +0.66 to +0.24 net cash.

**(b) CHH and COST — REFUTED flag, in the direction that flatters.** Both were tagged "no
pension tag found". Both have defined-benefit schemes, both in **surplus**, both **recognised as
balance-sheet assets**: Churchill China **£7.65M** (Note 19; the auditor lists the DB valuation
as a key audit matter) and Costain **£60.0M** (retirement benefit obligations: nil). Each
inflates book equity and flatters P/B — Churchill's true ex-surplus P/B is ~0.78, not 0.69. The
screen cannot see either, because the vendor carries no pension-asset tag on UK balance sheets
at all. `pension_unverified` fired on both, which is the guard working as a *routing* flag even
though the surplus detector is dead. Costain's surplus is now a **tailwind**: the Trustee
agreement of 26 Jan 2026 removed the dividend-parity constraint, enabling a £20M FY26 buyback.

**(c) THX — VERIFIED, with a material omission the screen structurally cannot catch.** FY25
profit from operations **US$199.7M** (screen carries ~112M — understated), cash **$137.75M**
against **nil** loans and borrowings, so the net cash is genuine at 28% (not 32%). But: Douta
(Senegal) PFS initial capex is **US$254M, "to be entirely funded from the Company's cash
reserves and project financing"**, FID targeted 2026 — roughly 1.8x the cash balance. And no
remaining mine life is stated anywhere; the only Segilola reserve disclosed is the *undepleted*
DFS figure of 518koz while ~375koz has already been produced, with 2026 guidance of 75–85koz
against 91.9koz actual in 2025. **Committed capex against a cash pile lives in the notes, not on
the face of anything — no balance-sheet screen will ever catch it.**

**(d) SRB — VERIFIED clean.** Q1-26 operating profit **US$27.1M** (vs $10.6M), net cash
~**$61.7M**, and AR2025 Note 23: *"the Group has not made any commitments for capital
purchases."* The Coringa ramp is planned but uncommitted; the cash is not pre-spent.

**(e) VTY — VERIFIED.** Note 22: non-current provisions £269.8M = **building safety £213.2M** +
completed sites £36.5M + customer care £10.9M; total building-safety provision £303.6M, **230
buildings under remediation**, spend phased evenly across 2026–28, +10% sensitivity = +£25.2M.
Equity £3,324.6M confirmed; **goodwill £827.6M** (£547.5M from Galliford Try Partnerships,
£280.1M from Countryside), 24.9% of equity, with an impairment trigger identified in-year (market
cap below NAV) and no impairment taken. Three DB schemes in **net surplus, £32.2M asset**.

**Also verified during the build:** AEP's 177p price and 387.8M share count against both the LSE
instrument record and the filed balance sheet (the figure looked wrong on first read; the
recollection was wrong, not the screen). **LSE executability** from the account blotter itself —
`BRBY @LSE` and `TW. @LSE` held in GBP. *Correction to the intake brief:* the `III` position is
the **US** ticker (Information Services Group, USD), **not** 3i Group of London.

Everything not listed above is **UNVERIFIED, which is not the same as clean.**

---

## 4. Guards added, and what each caught on the first run

| Guard | What it does | Effect |
|---|---|---|
| **(o) Cash quality + net-debt sign reconciliation** | Short-term investments are not cash equivalents; and the vendor's own `Net Debt` line agreeing in sign with our net cash is a contradiction. Either check demotes the name to a strict true-cash view that then governs EV, EV/EBIT and the composite | **The most consequential guard here.** 7 names corrected, 1 outright sign conflict (CAPD). Limitation: the vendor `Net Debt` tag exists on only 133 of 249, so check 2 is silent on the rest |
| **Pension / IAS-19, net of tax** | Adds the obligation to debt **after** a 25% tax shield — gross over-captures (the SFPI correction, 4.58x → 6.06x) | Supplies the obligation on 119 of 249 via a provisions proxy vs 60 explicit tags. **70 names return no tag at all, 37 in DB-normal sectors** — and CHH/COST prove the "no tag" case is the dangerous one |
| **Provision-kind labelling** | Distinguishes what the proxy actually contains | Caught the biggest proxy hit mislabelled: Vistry's £269.8M is cladding remediation, **verified**. Debt-like treatment stays (statutory, non-negotiable); the label was wrong and sent readers to the wrong note |
| **FCF on total capex + `capdev_r`** | Verified empirically that the vendor's UK `Capital Expenditure` already includes intangibles (TW 6.7 = 4.2+2.5; SGE 59 = 41+18; ITV 54 = 26+28) — so no double count — and sizes capitalised development against **sales** (the Tecnotree wedge) | 58 intangible-heavy, 10 above 8% of sales |
| **Durability + cash-generation condition** | The "HUBS fix": a turnaround that converted to cash on both sides of the EBIT cross is not a one-year artifact. Never rescues the accrual-gap shape | 31 demoted, **9 rescued to watch**. First implementation — the condition previously existed only by reference. **Not backtested** |
| **Peak-anchored EBIT trend** | `ebit_vs_peak` beside the legacy oldest-year anchor | **111 of 249 (45%) are trough-anchored** — the legacy anchor reports an uptrend on nearly half this pond by construction. Peak anchoring moves 54 into `melting`, only 9 of which the old anchor saw. Serabi: 38.8x legacy vs 1.24x peak |
| **Median ADV + live touch + order cap** | Median of 63 sessions, not the vendor mean; plus exchange bid/offer, NMS, and a 20%-of-prints order cap | **37 names (15%) were block-inflated** on the mean; 80 quote wider than 200bp |
| **Path fields** | `pct_off_52w_low`, `days_since_low`, `entry_exhausted` on `quality_drawdown.py`'s constants | 71 late entries, 13 at fresh lows |
| **Four-way share count** | The HOOD dual-class error — cap ÷ count must reconcile to price | 50 flagged. **UK dual-class barely exists** (1 multi-line issuer of 249); the fires are vendor-vs-filing vintage drift, the opposite of the US cause |
| **PFIC gate ON + FMV overlay** | Against the Euronext leg's skip; §1297's asset test on a public issuer runs on market value | 8 flagged. **The overlay ADDED exactly the two most de-rated names (GENL 0.54 P/B, OMG 0.71) and CLEARED six whose caps are large against book** — the PDD mechanism stated exactly: the de-rate causes the status |
| **Live offer period, ISIN-exact** | Takeover Panel Disclosure Table joined on ISIN | **9 shelf names in a Code offer period today** — Senior, Gooch & Housego, Advanced Medical Solutions, Gama Aviation (Epiris) among them. All would otherwise have printed as cheap industrials. Demoted: merger arb, not value |

---

## 5. Defects and gaps, stated plainly

1. **`pension_surplus_in_equity` has never fired — 0 of 249 — and we now know it should have
   fired at least twice.** The vendor carries no pension-*asset* tag on UK balance sheets, so
   the guard is dead code against this source. Churchill (£7.65M, 12% of equity), Costain
   (£60.0M) and Vistry (£32.2M) all carry recognised surpluses this screen cannot see, each
   inflating book equity and flattering P/B. Only `pension_unverified` catches them, and only
   by accident of the missing tag.
2. **Committed capex against a cash pile is invisible.** THX is the specimen. Treat `ncash_r` on
   any miner, developer or project business as a question, not an answer.
3. **The vendor net-debt cross-check covers only 133 of 249 names.** On the other 116 the
   securities-share test carries the load alone.
4. **`sector_takeout_heat` fires on 38% of the shelf** — too broad to discriminate. The
   ISIN-exact `in_offer_period` (9 names) is the column that carries information.
5. **No trailing take-private history.** The Panel table is *today's* state only; a name taken
   out last year is invisible. And the cohort warning travels: the bank-consolidation screen
   measured realised takeouts at 0.77–1.06x TBV against a cohort at 1.41x — **a takeout can be a
   down round. Acquisition is a free option, never a thesis.**
6. **The durability cash-condition is untested on this universe.** It rescued 9 names; whether
   any deserved it is unknown until they are read.
7. **IFRS-16 cuts both ways at once** — lease liabilities inflate EV (conservative) while lease
   principal sits in financing and flatters CFO (not conservative). 21 names flagged.
8. **ADV comes from consolidated daily bars** including off-book prints on some UK lines: an
   upper bound on lit liquidity, so the $18–60k order caps are optimistic.
9. **245 of 249 conids unresolved** — unverified, not unexecutable.
10. **The universe is a static snapshot** until `--refresh-universe` (monthly, ~9 minutes).

---

## 6. Suggested routing

- **Court first — cheapness looks real and the trap is nameable and testable:** **CAML** (best
  size-to-cheapness on the shelf, 14bp touch, $307k/day; question = why EBIT is 0.61x peak),
  **SRB** (verified clean balance sheet and no commitments; question = whether 2.3x survives a
  gold-price normalisation), **THX** (question = mine life and whether Douta is funded without
  equity), **TFW** (quality compounder at its own EBIT peak; question = why it is here at all).
- **Do not court until one specific question is answered:** **ACSO** — is there a live tender?
  **CHH** — is a 12%-of-equity pension surplus recoverable, and what caused EBIT to halve from
  peak? **VTY** — what is left of the remediation provision after 2028, and what is the
  Countryside/Galliford goodwill actually worth?
- **Cash-shell lane, not the value lane:** GENL, OMG, CLBS — negative EBIT, majority-cash balance
  sheets, PFIC-flagged. Different underwriting entirely.
- **Skip on execution alone regardless of multiple:** KMK (859bp touch), WYN (408bp, NMS 300
  shares).
- **Re-underwrite, do not delete:** CAPD. The business may still be interesting at 7.6x with a
  $99.8M securities book; it is simply not the net-cash bargain the screen advertised.
