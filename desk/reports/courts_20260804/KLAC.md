# KLAC — KLA Corporation | COURT_QUEUE_20260804, tier-2 AI-COMPLEX conflict cohort #1

**Court date** 2026-08-03 (evening, US) for the 2026-08-04 session.
**Verdict: REJECT 3/10 — the de-rate mechanism is genuine and the level test still fails; plus an axis collision with the household's existing semi exposure.**
**Basis: IBKR live snapshot 2026-08-03, `last` $182.69, `is_close:false`, −0.03%. 52w range $82.86–$307.37 (IBKR, split-adjusted). Historic closes from yfinance daily bars, split-adjusted. All per-share figures reflect the 10-for-1 split effected 2026-06-11.**

---

## 1. Cause-check — a beat-and-raise that fell 17% in two sessions

| Event | Source | Result |
|---|---|---|
| Q4 FY-2026 (June-2026 quarter) reported **2026-07-28** | 8-K 0000319201-26-000024, EX-99.1 | CONFIRMED |
| Q4 revenue **$3,658M** (+15.2% y/y vs $3,175M), **above the guidance midpoint** | press release | CONFIRMED |
| GAAP diluted EPS **$1.04** (at the upper end of guidance); non-GAAP **$1.05** — a **1% GAAP-to-non-GAAP gap**, the cleanest in the cohort | press release | CONFIRMED |
| FY-2026: revenue **$13.58B**, GAAP net income **$4.83B**, GAAP diluted EPS **$3.66**, OCF $4.14B, **FCF $3.77B**, capital returns **$3.35B** | press release | CONFIRMED |
| **Q1 FY-2027 guide: revenue $4.0B ±$200M (+24.6% y/y vs $3,210M), non-GAAP EPS $1.16 ±$0.10 (+23%), non-GAAP GM 62.5%** | press release | CONFIRMED |
| CEO Rick Wallace: "the trends driving our growth are **strengthening**, and we see momentum **accelerating** in the second half of calendar 2026 and continuing through 2027" | press release | CONFIRMED |
| 10-for-1 stock split effected 2026-06-11 | press release | CONFIRMED |
| Tape: **−6.2% on 7/28 (print day), −10.8% on 7/29**, −31.3% on the month, low $170.19 on 7/29 | yfinance bars | CONFIRMED |

**Ruling: DE-RATE, unambiguously.** Guidance accelerated from +15% realised to +25% guided; the multiple fell 17% in two sessions. Estimates rose and the multiple followed them down. In *form* this is the HUBS/CTSH/SAP winner pattern.

## 2. Where the winner pattern breaks — the level test

The winner pattern is "quality at a discount **to its own valuation history**." KLAC is not at one.

**Trailing GAAP P/E at each fiscal-year end** (XBRL `EarningsPerShareDiluted` from 10-Ks, price from split- and dividend-adjusted bars; pre-split EPS divided by 10):

| FY end | EPS (split-adj) | P/E |
|---|---|---|
| 2017-06 | 0.59 | ~14× |
| 2018-06 | 0.51 | ~18× |
| 2019-06 | 0.75 | ~15× |
| 2020-06 | 0.77 | ~24× |
| 2021-06 | 1.34 | ~23× |
| 2022-06 | 2.19 | ~14× |
| 2023-06 | 2.42 | ~20× |
| 2024-06 | 2.03 | ~40× |
| 2025-06 | 3.04 | ~29× |
| **2026-06** | **3.66** | **49.9× at $182.69** |

Pre-AI (FY17–FY23) median ≈ **18–19×**. Even the AI-era years averaged ~35×.

On sales: TTM P/S is **17.7×** ($240.8B cap ÷ $13.58B) against a three-year range of **6.8× → 18.3×** — roughly the **95th percentile of its own history**.

**After a −40.6% drawdown, KLAC is still at ~2.6× its pre-AI median multiple and within a whisker of its own three-year maximum.** The de-rate returned the stock to roughly where it traded in May-2026, which was already an all-time-high valuation. The screen's premise — a quality business at a discount to its own history — is **false at the level**, notwithstanding that the mechanism is correct.

**This is the gate the screen is missing.** `quality_drawdown.py` measures the discount to a *price* high. It never measures the discount to a *multiple* history. Recommended addition: disqualify any name whose current trailing EV/Sales (or P/E) sits in the top quartile of its own three-year distribution, regardless of drawdown depth. That single gate rejects KLAC, ARM and MRVL in this cohort and passes PLTR and APP — which is the correct partition.

**Gate test as filed:** `EXHAUSTED` fired and is **RIGHT** (+120.5% off a $82.86 low, 331 days old — past `HARD_OFF_LOW`). But it is right for the wrong reason: the low is nearly a year old and the run since was a *genuine* fundamental re-rating (revenue accelerating to +25% guided), not a bounce. The decisive objection is the multiple percentile, not the path.

## 3. Which leg of the AI cycle funds the earnings — and the China axis

From the Q3 FY-26 10-Q (`klac-20260331.htm`, geographic and product tables):

| Region | Q3 FY26 | share | y/y |
|---|---|---|---|
| Taiwan | $869.1M | 25.5% | **−12%** |
| **China** | **$829.6M** | **24.3%** (9-mo: 31.2%) | +5% |
| **Korea** | $681.1M | 19.9% | **+80%** |
| North America | $410.2M | 12.0% | +40% |
| Europe & Israel | $247.3M | 7.2% | +45% |
| Rest of Asia | $197.4M | 5.8% | **+97%** |
| Japan | $180.4M | 5.3% | **−47%** |

Product: Wafer Inspection 51%, Services 23%, Patterning 18%.

Two findings the headline hides:

1. **China is flat, not falling — and not driving.** $3,091.6M over nine months vs $3,083.7M a year earlier (+0.3%) while the total grew 10%. So China's *share* fell from 34.3% to 31.2% by dilution. The export-control tail is real (~$4B/yr of revenue exposed to a BIS rule change) but the incremental growth is not coming from it, so a further curb is a **level** shock, not a **growth** shock. That is a materially less bad framing than the "China export controls" headline implies — an anti-masking finding worth cataloguing.
2. **The growth is Korea-led — i.e. memory/HBM-led (+80%), with leading-edge foundry/logic (Taiwan) DOWN 12%.** Memory capex is the **most volatile leg of WFE**, historically the first to be cut and the deepest to fall. A Korea-led acceleration is the highest-beta version of a WFE upcycle, not the safest. KLA's own recent history: revenue fell **−20.9% y/y** in the March-2024 quarter.

## 4. Conflict resolution vs AI-BREAK | 2027-12-31 @ 0.45 — the lag cuts both ways

WFE is the **lagging** leg. Process-control tools are ordered two to four quarters ahead of the fabs that make the chips that fill the data centres that consume the capex. So a credit event in late-2027 shows up in KLA's *revenue* in late-2027/2028 — after the equity has already discounted it.

That is exactly what makes this drawdown ambiguous rather than reassuring: **a −40% fall on rising guidance is precisely what the top of a semi-cap cycle looks like from the inside.** The equity de-rates before the revenue confirms. The July 28–29 reaction (beat + 25% guide → −17%) is the market pricing the 2028 order book, not the 2026 one. The house's 45% is *the* variable, and KLAC is a levered read on it with a two-year reporting delay.

- **Does the entry require the cycle holding?** Yes, through 2028 — a longer requirement than any other name in the cohort.
- **Does the −40.6% price the break?** No — 95th-percentile own-history multiple (§2).

## 5. Valuation and cap structure

At $182.69 × 1,318M split-adjusted diluted shares (131.8M pre-split from the Q3 FY-26 10-Q; cross-checked: FY26 net income $4,830M ÷ EPS $3.66 = 1,320M) = **$240.8B market cap**. Debt $5,950M carrying / $5,887M net of issuance (10-Q 3/31/26); cash $1,787M plus marketable securities → net debt ~$3.5B → **EV ≈ $244B**.

| metric | value |
|---|---|
| EV / FY26 revenue $13.58B | 18.0× |
| EV / FY26 FCF $3.77B | **64.7×** |
| P/E trailing FY26 | **49.9×** |
| P/E on FY27E non-GAAP ~$5.20 | ~35× |
| FCF yield | 1.5% |

## 6. Household axis note (sizing constraint, per contract)

The household already carries ~**$5.2M / 26% AI-complex exposure**, and the **Parametric direct-indexing sleeve holds a heavy semiconductor book of individual names**. Adding KLAC at IBKR would (a) concentrate a factor the household already owns through a vehicle it does not control name-by-name, and (b) extend the wash-sale surface, which per standing doctrine is confined to **Parametric singles + GOOGL only**. KLA is very likely already inside that Parametric book. Any KLAC sizing would therefore be *"X% standalone, competing for an axis the household is already long"* — and at a 3/10 verdict the question is moot, but it should be recorded so the next semi-cap court does not re-derive it.

## 7. Scenarios (FY-2028, ending Jun-2028)

| | p | assumption | FV/sh |
|---|---|---|---|
| Bear | 0.35 | break lands 2027–28; WFE down-cycle cuts EPS ~35% (cf. FY24's −20.9% revenue quarter); FY28 non-GAAP EPS $3.40, 20× | **$68** |
| Base | 0.45 | cycle holds; FY28 EPS $6.40, 26× (still a premium to the 18–19× pre-AI median) | **$166** |
| Bull | 0.20 | AI WFE supercycle extends; FY28 EPS $7.60, 32× | **$243** |

**E[FV] $147.1 vs $182.69 → edge −19.5%.** Note the **base case alone ($166) sits below the live price**. Only the bull case supports $182.69. That is the whole verdict in one line.

## 8. Four-idea frame

1. **Long here** — rejected, −19.5% expected edge, base case below spot.
2. **Long on a price gate** — a defensible band is **$105–125** (≈20–24× FY27 EPS, the upper half of its pre-AI multiple range). That is −35% from here. Arm it as a watch level, not as a staged order: at that price the WFE cycle would be visibly rolling and the earnings denominator would also be falling, so the band must be re-struck on the then-current EPS, not on today's.
3. **Premium sale into the elevated IV** (annual IV 78.4% vs HV 99.4%) — rejected on doctrine: no premium selling in the taxable book (short premium is non-deferrable short-term ordinary income at ~50%+). Note also that IV < HV here, so the premium is not even rich.
4. **No position; encode the multiple-percentile gate** — adopted, and it is the most portable output of this whole cohort.

## 9. Catalyst map

| Catalyst | date | p | magnitude | leading indicator |
|---|---|---|---|---|
| Q1 FY-27 print | ~2026-10-28 (Q1 FY26 was 2025-10-29) | 1.0 | ±8–12% | whether Korea/memory growth holds at +80% |
| BIS / China export-rule change | undated, standing | 0.3 by end-27 | −8–15% one-time level shock to ~$4B of revenue | Federal Register / BIS entity-list actions |
| Memory-capex guidance from Samsung/SK Hynix/Micron | quarterly | — | — | **the true KLAC leading indicator** — memory capex leads KLAC bookings ~2 quarters |
| TSMC capex guide (Taiwan is −12% y/y) | Jan-2027 | 1.0 | ±5% | the leading-edge logic leg |

## 10. Kills

- Kill any long while trailing P/E is above ~30× (≈$110 on FY26 EPS, ≈$156 on FY27E).
- Kill the watch if two consecutive quarters guide below +10% y/y — that is the cycle rolling and the base case dying.
- Re-court on either (a) price in the $105–125 band with FY28 EPS still guided above $5.50, or (b) resolution of AI-BREAK to NO.

## 11. Verification notes / gaps

- **Top UNVERIFIABLE item: KLA's order book / backlog.** KLA does not disclose bookings or backlog, so the single number that would resolve the lag question — how much of the FY27 guide is already contracted — is not obtainable from the filings. Everything in §4 about lag is structural inference, not verified fact.
- Q4 FY-26 10-K not yet filed; FY26 balance sheet figures above are from the Q3 FY-26 10-Q (3/31/26) plus the Q4 press release. Cap structure pulled before the EV claim: $5.95B senior notes, no preferred, no converts, 1,318M split-adjusted diluted shares.
- Geographic mix is Q3 FY-26 (March quarter); the June-quarter geographic split is in the unfiled 10-K.
- Honesty read: **CLEAN.** GAAP and non-GAAP EPS differ by one cent. Guidance is specific and quantified. Geographic and product mix are fully tabulated including the unflattering lines (Taiwan −12%, Japan −47%). There is no takeaway-vs-data divergence here at all — this is a straight valuation rejection of an honestly reported business, which under the honesty-alpha doctrine is explicitly *not* where the edge lives. Recorded as such.
