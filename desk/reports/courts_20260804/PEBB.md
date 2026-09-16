# PEBB — THE PEBBLE GROUP PLC | LSE shelf rank 18 | court 2026-08-04

**Identity.** The Pebble Group plc, AIM (segment ASQ1), ISIN GB00BK71XP16, UK-incorporated. Quoted in
**pence (GBp)**. Live IBKR quote conid 394326260 / LSE: **55.6p, is_close=false, 2026-08-04**, today's
volume 161,026 sh; yfinance PEBB.L close 55.6p same date — units tie, no magnifier issue.
Two segments: **Facilisgroup** (subscription tech + group-purchasing network for ~253 North American
promotional-product distributors) and **Brand Addition** (outsourced branded-merchandise programmes for
large global brands). Analyst coverage: 1 (orphan).

**CORRECTED MARKET CAP — SCREEN ERROR.** Shares in issue **136,477,872** per RNS 30-Jul-2026
(Buyback Completion, total voting rights). The shelf used the FY25 filing count 147,368,501 →
shelf mcap £81.94M. **Corrected mcap = £75.88M (~$101.7M)**, shelf overstated by 8.0%. The shelf's
own `share_count_divergence 0.072 / share_count_unverified true` fired correctly; the cause is not
dual-class, it is buyback-and-cancel vintage drift. Every shelf ratio using mcap is off by ~8%.

## LEAD ITEM — the IBKR `PEBB.TEN` line

`PEBB.TEN` (conid 804483118, CORPACT) is a **HISTORICAL** corporate action, not live.

- **Launch of Tender Offer, RNS 21-Jul-2025.** Return of capital of up to **£6.5M** by purchase of up
  to **10,655,737 shares at a FIXED price of 61p** — **NOT a Dutch auction**, single strike price.
  Premium of 25.8% to the 48.5p pre-announcement close. Basic entitlement 6.69% of each holder's
  shares, plus an excess facility. Executed by Panmure Liberum as principal, repurchased and cancelled.
- **Result of Tender Offer, RNS 08-Aug-2025.** Closed 7-Aug-2025. Fully taken up: 9,208,353 tendered
  on basic entitlement + 1,447,384 on excess = the full 10,655,737 (6.69%). Shares in issue fell to
  148,714,709. **Offer period expired; no live tender.**
- **Successor event, now also finished.** £5.0M buyback launched 17-Mar-2026, **raised to £7.0M on
  9-Jul-2026, COMPLETED 30-Jul-2026**: 12,236,837 shares bought for £6,999,999 at an average 57.20p.
  Final print 29-Jul: a single 3,351,337-share block at 55.00p at 16:28 (~15 sessions of median ADV
  in one cross — an institution exiting into the company's bid).
- **Shares out: 159.4M (pre-tender) → 148.7M (Aug-25) → 136.5M (Jul-26) = −14.4% in 12 months.**
  £14.3M returned in the 12m to 30-Jun-2026 vs £6.0M the prior 12m (~19% of today's mcap).

**Guard-gap finding (must be logged).** `in_offer_period: false` is **CORRECT** — PEBB is genuinely
not in a Takeover Code offer period, and LSE_OFFER_PERIODS.json (39 Panel entries) does not and should
not carry it. **An issuer self-tender is not a Code offer**, so the Panel disclosure table can never
surface one. The shelf therefore has a structural blind spot for issuer self-tenders, buyback
programmes and returns of capital — all of which materially change an underwriting. Fix: scan IBKR
`.TEN`/CORPACT lines and RNS headlines for "Tender Offer" / "Return of Capital" / "Share Buyback
Programme" as a **separate** guard from the Code table.

**US-holder exclusion — real and adverse.** The 2025 tender was expressly "not being made to
Shareholders who are located or resident in the United States". A US taxable account is **locked out
of PEBB's premium return-of-capital channel**: UK holders were offered a 25.8%-premium exit that we
could not take. We participate in open-market buybacks pro rata, but not in tenders. If the board
repeats the tender (its stated preference in 2025), we are the diluted party.

**And the board's own price marks are underwater.** Tender at 61p (Aug-25); buyback VWAP 57.20p
(Mar–Jul-26). The stock is **55.6p** today. "The board thinks it's cheap" has not been validated by
the tape at either mark.

## Segment decomposition (FY25 audited, RNS 17-Mar-2026, note 3 — the mix-erosion test)

| £'000 | Brand Addition | Facilisgroup | Central | Group |
|---|---|---|---|---|
| Revenue | 107,502 | 17,157 | – | 124,659 |
| Gross profit | 39,777 (37.0%) | 17,157 (100%) | – | 56,934 (45.6%) |
| Adjusted EBITDA | 11,380 (10.6%) | 7,261 (42.3%) | (2,822) | 15,819 |
| Amortisation | (1,891) | (4,120) | – | (6,011) |
| **Operating profit** | **7,914 (7.4%)** | **2,431 (14.2%)** | **(2,990)** | **7,355** |

**The trend runs the opposite way to the bull narrative.** Facilisgroup operating profit: $5.4M (FY23)
→ $4.5M (FY24) → £2.431M (~$3.1M, FY25). Its EBITDA margin per the AR KPI page: **60% → 54% → 50% →
50% → 42%** (FY21→FY25). Revenue £17.9M → £17.6M → £17.157M, three straight years of GBP decline
(+1%/+2% cc). GMV grew ($1,150M → $1,580M) but Preferred-Supplier spend went **flat at $509M** in FY25
on US-tariff purchasing behaviour, so the take rate is compressing. Meanwhile the "low-quality"
merchandise leg **improved**: BA operating profit £6.2M → £7.9M → £7.914M, gross margin 35.2% → 37.0%.
**The high-margin SaaS leg is the deteriorating one; the distributor is carrying the group.**

Facilis's 42% EBITDA margin is also a capitalisation artifact: **£4.5M of development spend was
capitalised in FY25** (£3.474M of it staff costs) against £4.120M of Facilis amortisation. On a
cash basis Facilis earns ~£2.4–2.8M, i.e. the operating-profit line, not the EBITDA line.

## "You get Facilisgroup for free" — REFUTED

EV = corrected mcap £75.88M + net debt £1.2M (30-Jun-2026, company definition) = **£77.1M**
(£81.8M including £5.2M IFRS-16 leases). Central costs £2.9M/yr capitalised at 8x = −£23.2M.

| Brand Addition at | BA value | Implied Facilisgroup | = x sales | x EBITDA | x EBIT |
|---|---|---|---|---|---|
| 6x EBIT | £47.5M | £52.8M | 3.08x | 7.3x | 21.7x |
| 7x EBIT | £55.4M | £44.9M | 2.62x | 6.2x | 18.5x |
| 8x EBIT | £63.3M | £37.0M | 2.15x | 5.1x | 15.2x |
| 10x EBIT | £79.1M | £21.1M | 1.23x | 2.9x | 8.7x |

Brand Addition has 7.4% operating margins, **top-10 clients = 61% of segment revenue / 53% of Group
revenue** (AR principal-risks page), one client at £13.0M (12.1% of BA, 10.4% of Group), positive
working capital of £15.4M tied up, and a stated organic-growth ambition of only ~5%. **6–8x EBIT is
the honest band** — 10x is not defensible. At 6–8x, the market is paying **2.2–3.1x sales / 15–22x
EBIT for Facilisgroup**, a business with 0–2% revenue growth for three years and a margin falling
600–800bp a year. That is roughly **fair, not free**. The bull case is refuted.

## Screen-corruption battery

1. **Securities-as-cash** — NOT APPLICABLE. `st_investments` null, `securities_as_cash false`,
   no vendor net-debt sign conflict. No CAPD-style inversion.
7. **Trust-safe / client float — PARTIAL FIRE, and the bigger problem is seasonality.** FY25 year-end
   cash £9.637M carries **£4.790M of contract liabilities** (Facilis subscriptions invoiced in
   advance, AR note 18 area) — roughly half the balance is customer money for services not yet
   delivered. Worse, **31-Dec is the seasonal cash PEAK** (Q4-weighted merchandise collections): the
   company reported **net DEBT of £1.2M at 30-Jun-2026** vs net cash £6.0M at 30-Jun-2025.
   `ncash_r +5.4%` is therefore both stale and measured at the high-water mark. Cash is now
   ~£0 and guided to ~£5.0M at 31-Dec-2026 (vs £16.5M at Dec-24) — **the balance sheet has been
   liquidated into buybacks.**
2. **Pension by hand — RESOLVED, NO DB SCHEME.** AR2025 note on employee benefits: "The Group operates
   a number of country-specific **defined contribution** plans." Zero references to defined benefit,
   scheme assets, or a surplus/deficit anywhere in the 7,116-line annual report. Pension cost £853k
   (2024: £848k). **No adjustment to book equity or EV.** The shelf's `pension_unverified: true` /
   "assume a DB scheme" default is a correct-but-non-firing caution here.
3. **Dual-class / share count — FIRES, corrected above.** 136,477,872 (not 147,368,501). No dual class;
   cause is buyback cancellation. EBT holds a further 1,346,208 shares.
4. **Trough anchor** — `ebit_vs_peak 0.74` on ebit_hist [7.627, 8.646, 7.852, 10.288] (FY25→FY22).
   Above the 0.7 melting line but a **26% decline from the FY22 peak**, and the decomposition shows
   100% of that decline is Facilisgroup. Not melting; not growing either.
5. **Commodity frame** — NOT APPLICABLE (no commodity exposure; the nearest analogue is US tariff
   pass-through in merchandise sourcing, which shows up as flat Preferred-Supplier spend).
6. **Committed capex — CLEARED EXPLICITLY.** AR2025 note 26: "The Group had no known commitments or
   contingencies at 31 December 2025 (2024: none)." Company note 16: £10.0M RCF (SONIA+2.0%,
   refinanced Feb-2025 to Feb-2029) **undrawn**, plus an undrawn RMB10M facility at Brand Addition
   Shanghai. Nothing earmarked.
8. **Path — FRAME-REJECT.** 55.6p vs 52w high 61.0p (02-Jun-2026): **only −8.9% off the high**. Low
   40.58p on 06-Jan-2026, **209 days ago**, +37% off it. +3% over 3 months. This is not a drawdown
   and not a fresh-low entry; it is a name near its high that a screen made look cheap.
9. **Staleness** — balance sheet and flows are **31-Dec-2025 (7 months old)**, and the intervening
   period materially changed the balance sheet (£7.0M buyback, £3.0M dividend). Half Year Results
   **8-Sep-2026** (35 days out — outside the 2-week print blackout, but the next real datapoint).
10. **Friction** — stamp **0%** (AIM, SDRT-exempt since Apr-2014). Median touch 357bp (bid 55 / offer 57).
    **All-in entry = 0 + 179bp = ~179bp; round trip ~357bp.** The 0% dividend WHT (UK-incorporated,
    treaty-clean, unlike SOM) is a holding-period edge only and does not pay for this.

**Liquidity — worse than the row says.** Median ADV $171k (63-session median, independently reproduced
at £126,948/day). But **the buyback bought ~12.24M shares over ~93 sessions ≈ 132k shares/day ≈ 60%
of the median daily volume**, and it stopped on 30-Jul-2026. `adv_block_inflated: true` is right.
Natural post-buyback turnover is plausibly £55–75k/day (~$75–100k). The tape agrees: the stock ran
59–60p through mid-July and fell to 55.5p in the ten sessions around completion. **The marginal buyer
has left.** A 0.75% position ($24.8k) is ~1.5 days of natural volume; exit 3–8 sessions.
**Register risk:** Liontrust 18.60% (26.01M, trimming), Harwood/Oryx 18.54% (25.30M, **bought ~5.3M on
29-Jul-2026**), BGF 5.02%, directors ~6%. Two funds hold 37%. Harwood (Christopher Mills) at 18.5% is
a plausible break-up/take-private agitator — an unpriced upside optionality, and an unpriced overhang.

## Findings table

| claim | source | result | verdict |
|---|---|---|---|
| Live tender offer in progress | investegate RNS 21-Jul-25 / 08-Aug-25 | tender launched 21-Jul-25, closed 07-Aug-25, £6.5M @ 61p fixed, 6.69%, cancelled | **REFUTED (historical)** |
| Tender was a Dutch auction | RNS 21-Jul-2025 | single fixed price 61p + basic/excess entitlement | **REFUTED** |
| US holders can participate in PEBB tenders | RNS 21-Jul-2025 restricted-jurisdiction legend | expressly excluded | **CONFIRMED (adverse)** |
| Shelf share count 147,368,501 | RNS 30-Jul-2026 total voting rights | 136,477,872; mcap £75.88M not £81.94M | **REFUTED — screen error** |
| Net cash £4.45M / ncash_r +5.4% | HY trading update 09-Jul-2026 | net DEBT £1.2M at 30-Jun-26; ~£5.0M net cash guided Dec-26 | **REFUTED (stale)** |
| Year-end cash is shareholder cash | AR2025 contract liabilities £4.790M + seasonality | ~half is deferred subscription income; Dec is the peak | **REFUTED** |
| DB pension scheme exists | AR2025 employee-benefit note | defined contribution only, £853k cost | **REFUTED — no adjustment** |
| Capital commitments encumber cash | AR2025 note 26 | "no known commitments or contingencies" (2024: none) | **REFUTED — cleared** |
| Facilisgroup is a growing SaaS asset | RNS FY23/FY24/FY25 + AR KPI page | rev £17.9→17.6→17.2M; EBITDA margin 60→42%; op profit −43% in 2yr | **REFUTED** |
| Brand Addition is client-concentrated | AR2025 principal risks + note 3 | top 10 = 61% of BA rev / 53% of Group; largest £13.0M (12.1% of BA) | **CONFIRMED** |
| "You get Facilisgroup for free" | SOTP on segment note | implied 2.2–3.1x sales / 15–22x EBIT at BA 6–8x | **REFUTED** |
| Facilisgroup inflecting in FY26 | HY trading update 09-Jul-2026 | +7% USD in H1-26; pricing reset lifts H2-26; multi-year contracts | **PLAUSIBLE (unaudited)** |
| Sustainable capital-return yield ~19% | HY update + FY25 cash flow | £14.3M/12m was balance-sheet liquidation; run-rate post-tax FCF ~£6.3M = ~8.3% | **REFUTED** |
| PEBB is in an offer period | LSE_OFFER_PERIODS.json (39 Panel entries) | absent — and correctly so; self-tenders are not Code offers | **CONFIRMED (guard gap)** |
| Median ADV $171k is tradeable size | yfinance 63-session + buyback arithmetic | ~60% of volume was the buyback, which ended 30-Jul-26 | **REFUTED** |
| PFIC risk | screen + FY25 revenue £124.7M | passive assets 8%, active operating business | **CONFIRMED clean** |
| 0% UK dividend WHT | GB00BK71XP16, UK-incorporated AIM | correct (contrast SOM) | **CONFIRMED** |

**UNVERIFIABLE / gaps:** (a) HY26 segment split — the 8-Sep-2026 interims are the first look at whether
Facilis's +7% carries margin with it; (b) the magnitude of the Facilis "pricing structure evolution"
(no £ quantification given); (c) whether Harwood's 29-Jul purchase is passive value-adding or the start
of an activist campaign — no RNS states intent; (d) FY26 consensus (1 analyst, house broker Panmure
Liberum — "market expectations" is effectively its own broker's number).

## Valuation and scenarios (pence, on 136,477,872 shares)

Group at 55.6p: EV/EBIT **10.5x**, EV/Adj EBITDA **4.9x**, statutory P/E **14.1x**, adj P/E 14.4x,
operating cash flow (after capex AND lease capital) £7.5M = **9.9% pre-tax / 8.3% post-tax on mcap**,
dividend 3.57%. NTAV is ~£23.5M after stripping £35.8M goodwill, £6.6M customer relationships and
£16.3M capitalised software from £82.2M net assets — **P/B 1.0 is meaningless here** (3.2x tangible).

- **Bear (p 0.25, FV 36p):** a top-3 Brand Addition client is lost or merchandise budgets crack;
  Facilis take-rate keeps compressing and the pricing reset triggers churn. Group EBIT → £5.5M at 8x.
  (The Jan-2026 low of 40.58p shows the market will pay this.)
- **Base (p 0.55, FV 60p):** FY26 in line — Facilis +5–7%, BA +4%, group EBIT ~£8.0M at an unchanged
  10.5x, plus ~£5M net cash and the dividend. +8% price, ~+12% total return.
- **Bull (p 0.20, FV 90p):** the Facilis pricing reset restores margin toward 48% and revenue growth
  to ~10%; group Adj EBITDA £18M re-rated to 13x EV/EBIT — **or** Harwood forces a break-up/take-private
  at ~8x group EBITDA (£126M EV).

**E[FV] = 60.0p. Edge = +7.9% gross, +6.1% after 179bp entry friction.** With a 357bp round trip and
an exit that takes 3–8 sessions in a name whose largest buyer just retired, that is not an edge.

## Kills / tripwires

- HY26 results 08-Sep-2026: Facilisgroup H1 revenue **below +5% in USD**, or Facilis Adj EBITDA margin
  **below 42%** → the inflection is not real, kill.
- HY26 net debt **worse than £1.5M**, or FY26E net cash guided below £4.0M → cash generation is not
  covering the returns; kill.
- Any RNS disclosing loss or material reduction of a top-5 Brand Addition client → kill.
- New tender offer announced at any price → confirms we are the excluded party; **do not chase**.
- Harwood/Oryx crossing 25% or an RNS of a formal approach → re-court as special-situation, not value.

## Ruling

**NOT A DRAWDOWN (3/10), with a SCREEN-ERROR overlay.** Nothing is wrong with the business and nothing
dishonest was found — reporting is clean, the pension is DC-only, commitments are nil, the buyback was
disclosed to the share. But the frame does not fit: the stock is **8.9% off its 52-week high**, 209 days
past its low, and up 3% in three months. The screen's cheapness is partly a stale share count (mcap
overstated 8%) and a stale, seasonally-peaked, half-deferred-income net cash line that is now net debt.
The one thing that would justify owning it — a free SaaS asset — is refuted by the segment note: the
SaaS leg's operating profit has fallen 43% in two years while the merchandise distributor carries the
group, and the SOTP shows you are paying 2.2–3.1x sales for Facilisgroup, not zero. £7.9M of expected
gross edge on a 179bp entry into a $100k-a-day AIM line whose only reliable bid just completed and
retired is not a trade for this book. **REJECT. No entry band.**

*Sources: investegate RNS (21-Jul-25, 08-Aug-25, 17-Mar-26, 29-Apr-26, 09-Jul-26, 30-Jul-26, 30/31-Jul-26
TR-1s, FY24 results 8783523); The Pebble Group Annual Report 2025 (272947_Pebble_Group_AR_Interactive.pdf,
notes 3/16/18/26 and KPI pages); IBKR get_price_snapshot conid 394326260 LSE; yfinance PEBB.L.*
