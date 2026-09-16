# CHH — Churchill China plc (AIM: CHH) — LSE shelf court, 2026-08-04

**Verdict: 3/10 REJECT — WATCH with a price gate.** Honest company, impaired business, bounce already
run, and a disclosed-but-under-modelled cash claim restarts in seven weeks.

This court adjudicates the primary evidence gathered by the deep-read child agent
(`CHH_DEEPREAD_EVIDENCE.md`, AR2025 verified) plus the RNS/tape work below. Research was not redone.

---

## 1. Identity, tape, friction (verify before anything else)

| Item | Source | Result |
|---|---|---|
| Line | LSE_SHELF row TIDM `CHH`, ISIN GB0001961035, AIM, `lse_segment` ASX1 | Churchill China plc |
| IBKR line | `conid 748086669`, exchange LSE, `ibkr_verified_utc 2026-08-04T17:20Z` | **EXECUTABLE — verified**, not data-gated |
| Price unit | IBKR snapshot `last 380.0 (is_close)`; yfinance `currency=GBp`, 08-04 close 385.0 | **GBp (pence)**. £3.85/share |
| Unit cross-check | IBKR `dividend-yield 5.53%` at 380p vs AR2025 total DPS 21.0p → 21.0/380 = **5.53%** | Unit CONFIRMED by an independent ratio, not asserted |
| Market cap | 10,997,835 sh × 385p | **£42.34m** (~$56.9m) |
| 52w range | yfinance intraday: low 270.9p 2026-03-23, high 459.82p 2026-02-03. IBKR: low_52w 275.0, high_52w 445.0 | Two vendors agree within 2% |
| Path | intraday basis **+42.1% off a 134-day low**; close basis (shelf) **+35.1% off a 119-day low** | Bounce is well advanced; not a fresh low |
| Touch | shelf bid 380 / offer 390 → 10p on 385 = **260bp round-trip**; half-touch ~130bp | AIM ⇒ **stamp duty 0%**, but the touch alone is 2.6x the stamp it saves |
| Liquidity | shelf `adv_usd` 88,501 (**median** of 63 sessions); IBKR `avg-90d-usd-volume` 232,400 (mean) | `adv_block_inflated:true` fires correctly — use the median. `max_order_usd` $17,700 |
| Offer period | LSE_OFFER_PERIODS.json — no CHH entry; no .TEN line | **Not** a special situation |
| Prior art | grep of research_ledger.json + resolution_packs.json | **None** — no frozen call to respect |

Sizing arithmetic for later: 0.5% of $3.3M = $16,500, which fits inside one median session
($17,700). 0.75% ($24,750) does not — it is ~1.4 median days in, 3-8 sessions out.

---

## 2. Cause-check — what actually happened to the price

| Date | Move | Event |
|---|---|---|
| 2025-07-17 | **−16.5%** | H1-2025 pre-close/trading news; the de-rate leg begins (664p Jun-25 → 420p Jul-25) |
| 2025-09-03 | — | Interim results H1-25: revenue £38.5m (−5.2%), **operating profit £2.8m (−37.8%)**, interim DPS 7.0p (−39.1%) |
| 2026-02-02 | +12.7% | Full-year trading update 2025 |
| 2026-03-23 | trough 270.9p | FY2025 final results period; margin 7.4%, EPS 39.7p, total DPS 21.0p (−44.7%) |
| 2026-05-29 | — | AGM statement: "hospitality sales remain broadly in line"; welcomes **£120m UK government support for the ceramics industry** |
| 2026-07-31 | — | **Trading update**: H1-26 sales £37.4m vs £38.5m; cash £8.8m vs £5.6m; "trading performance stabilised" |

Cause is READ, not assumed: a two-year UK/European hospitality demand contraction running through a
fixed-cost Stoke-on-Trent ceramics plant.

---

## 3. Mode B first — the questions the release framing hid

### B-1. The 5.5% dividend yield is 81% pre-spent from September 2026. **DECISIVE**

The pension note (AR2025 Note 19) carries a **£7,651k surplus** (assets 44,583 / obligations 36,932),
IFRIC-14 assessed as recoverable-on-cessation and therefore *not* restricted. The narrative reads that
assets exceeding liabilities helps "avoid additional cash contributions." Sitting against that, in the
same note, is the schedule agreed at the **August-2024 triennial**: **£nil to 31-Aug-2026, then
£1.75m/yr from September 2026 to June 2029** — approximately £4.96m of contractual cash.

The note itself ties pension payments to dividend policy explicitly. Run the arithmetic the note
invites:

| | £'000 |
|---|---|
| FY2025 free cash flow | 4,992 |
| Less pension schedule from Sept-2026 | (1,750) |
| Less dividend at the *already cut* 21.0p × 10.998m sh | (2,310) |
| **Residual** | **932** |

**81% of free cash flow is committed** the moment the schedule restarts — seven weeks from this court.
FCF yield falls from 11.8% to **7.7%** on the same market cap. A second dividend cut is not a tail; it
is the arithmetic centre of the distribution unless margin inflects.

Grade: this is **disclosed in full**. Nothing is hidden. But the *takeaway* a reader carries away from
the surplus paragraph ("pension is a non-issue, it's in surplus") diverges from the schedule two
sentences later. Under the honesty boundary that is a **review flag, not an elevate** — divergence of
emphasis, zero divergence of fact.

Book-value treatment per the LSE addendum (strip a surplus before any P/B claim):

| Basis | Equity £'000 | BVPS | P/B at 385p |
|---|---|---|---|
| As reported | 61,539 | 559.6p | 0.688 |
| **Strip gross surplus (addendum rule)** | **53,888** | **490.0p** | **0.786** |
| Strip surplus net of 25% deferred tax | 55,801 | 507.4p | 0.759 |

The shelf's 0.688 P/B is optically 13pp too cheap. Immaterial to the verdict — this is a tier-1/2
quality-at-own-history frame where book is not the thesis — but it is the addendum's point, verified.

### B-2. "Cash generation remained strong" is 43% a smaller dividend cheque

The 07-31 update leads with cash £8.8m at 30-Jun-26 vs £5.6m at 30-Jun-25, +£3.2m, attributed to
"operational efficiency and disciplined working capital management." Independent derivation:

- FY2024 final dividend 26.5p × 10.998m = £2.914m, paid ~May-2025 (inside the H1-25 cash figure)
- FY2025 final dividend 14.0p × 10.998m = £1.540m, paid ~May-2026 (inside the H1-26 cash figure)
- Difference: **£1.374m = 43% of the £3.2m YoY cash improvement**

The operating improvement is real but roughly £1.8m, not £3.2m. Second review flag: same pattern —
true statement, flattered takeaway.

### B-3. The auditor left a profitability warning inside the audit report

PwC changed its materiality benchmark to **1% of revenue** because "profit as a percentage of total
revenue has declined… considered to be low." An auditor abandoning a profit-based benchmark is a
statement about the durability of profit, published in a document nobody reads for that reason. It is
corroborative of the trajectory, not incremental to it — but it is a genuine primary tell and it was
left visible. PwC exits by competitive tender to Forvis Mazars, **pre-announced and benign** — this is
not an auditor resignation and should not be scored as one.

### B-4. Anti-masking credit — large, and it does not make the stock a buy

Four things this company did that a promotional management does not do:

1. **Headcount 836 → 687 (−17.8%) with ZERO exceptional charges.** Attrition and automation, expensed
   through the P&L. The industry-standard move is a restructuring provision that flatters adjusted
   profit; they declined it. The 7.4% margin is a *clean* 7.4%.
2. **Dividend cut 44.7%, both legs.** No defence of an uncoverable payout.
3. **Zero buyback in FY24 and FY25** despite a standing authority and the usual boilerplate. They did
   not manufacture support.
4. **Net cash, no bank debt, no covenants**, £2.5m facilities undrawn; capital commitments a trivial
   £244k (checked per the THX/commitments-note rule — the capex programme is run-rate, not committed).

Under house doctrine this is **CLEAN**: a genuinely impaired business that discloses its impairment is
not the catch. The honesty finding here is *anti-masking* — catalogue it, do not convert it into a
buy. Re-detecting honestly disclosed bad news is not alpha.

### B-5. The lease that appeared

Lease liabilities tripled to £3.384m on a £2.9m land-and-buildings addition. Small in absolute terms
and disclosed; noted so the net-cash figure (£7.424m = cash 10,808 − leases 3,384) is understood as
already lease-adjusted. Cap structure is plain vanilla: 10,997,835 ordinary shares, no warrants, no
preferred, no converts. Net-cash and EV claims below are safe to make.

### B-6. Register

Roper family >17.4% identified (J A Roper 9.3% audited + S Roper 8.06%, sub-3% holdings unquantified);
nine institutions >3% totalling 51.7%; Raymond James to 6.63% (04-14 RNS). Float 81.5%. A concentrated
but not controlled register; no takeover-defence structure, and the family stake is a plausible
consolidation vector on a £42m cap — noted, not underwritten.

---

## 4. Mode A — claim verification

| Claim | Method / authority | Finding |
|---|---|---|
| Price is 385p and the unit is pence | IBKR conid 748086669 close 380.0 + yfinance 08-04 close 385.0, cross-checked by 21.0p/380p = 5.53% = IBKR's own dividend yield | **CONFIRMED** |
| Margin fell 12.4% → 7.4% | AR2025: op profit 10,252 → 7,995 → 5,643 on revenue 82.3 → 78.3 → 76.3 | **CONFIRMED** |
| H1-2026 still declining | RNS 31-Jul-2026: external sales £37.4m vs H1-25 £38.5m (−2.9%) | **CONFIRMED** |
| H1-25 comparative base | RNS 03-Sep-2025 interims: revenue £38.5m, operating profit £2.8m (7.3% margin), EPS 21.0p, interim DPS 7.0p, net cash £5.6m | **CONFIRMED** |
| Dividend cut 44.7% | 21.0p vs 38.0p; interim leg 7.0p vs 11.5p, final leg 14.0p vs 26.5p | **CONFIRMED** |
| Pension surplus £7,651k in book equity | AR2025 Note 19; IFRIC-14 recoverable-on-cessation, **not** restricted | **CONFIRMED** |
| £1.75m/yr cash schedule restarts Sept-2026 | AR2025 Note 19, Aug-2024 triennial schedule, £nil to 31-Aug-26 then £1.75m/yr to Jun-2029 | **CONFIRMED** |
| Zero buyback despite authority | AR2025 capital section, FY24 and FY25 | **CONFIRMED** |
| Auditor change is benign | RNS "Change of Auditor" (id 9621960); competitive tender, pre-announced | **CONFIRMED** |
| Next print is early September 2026 | RNS 31-Jul-2026, verbatim: "will issue its results for the six months ended 30 June 2026 in early September 2026" | **CONFIRMED** — ~4-5 weeks out, outside the 2-week no-blind-entry window but inside the horizon |
| Not in an offer period | LSE_OFFER_PERIODS.json; no IBKR .TEN line | **CONFIRMED** |
| £120m UK government ceramics support | AGM statement 29-May-2026, verbatim; company itself says it "awaits the detail" | **PLAUSIBLE, unquantified** — do not underwrite |
| Pension admin costs £382k vs £94k (4x) | AR2025 Note 19 | **CONFIRMED as a fact, UNEXPLAINED as to cause** — see gaps |

### Gaps — UNVERIFIABLE is not clean

1. **Pension admin cost 4x (£94k → £382k) is unexplained in the note.** On a £5.6m EBIT base this is
   5% of operating profit appearing with no narrative. Benign readings exist (triennial actuarial and
   IFRIC-14 assessment fees, GMP work, buy-in advisory). A non-benign reading — preparatory work for a
   buy-in/buy-out that would crystallise cost — is not excluded. Not resolvable from the AR.
2. **H2-2026 order visibility.** The company says outright that "sales visibility remains limited" and
   flags "the significance of the final quarter." The FY hinges on a quarter nobody can see.
3. **No sell-side estimate trajectory pulled.** Investec (Nomad/joint broker) and Panmure Liberum
   forecasts are not in the free corpus, so the formal "estimates falling vs multiple falling" test is
   run on *company-reported* actuals rather than consensus. Stated, not papered over.
4. Roper family sub-3% holdings unquantified; >17.4% is a floor, not the number.

---

## 5. The ruling — DERAILMENT that has plateaued, not a de-rate

The frame wants the HUBS/CTSH/SAP pattern: multiple compressed on **stable or rising** estimates. CHH
is the opposite and it is not close.

| | FY2023 | FY2024 | FY2025 | H1-2026 |
|---|---|---|---|---|
| Revenue £m | 82.3 | 78.3 | 76.3 | 37.4 (vs 38.5) |
| Operating profit £m | 10.25 | 8.00 | 5.64 | (Sept print) |
| Margin | 12.4% | 10.2% | 7.4% | — |
| EPS | 70.2p | 57.9p | 39.7p | — |
| DPS | 38.0p (FY24) | 38.0p | 21.0p | — |
| Price (period end) | — | ~614p Jan-25 | ~340p Dec-25 | 385p |

Profit fell **45%** on a **7%** revenue decline over two years — textbook operating deleverage on a
fixed-cost kiln base. The multiple followed the estimates down; it did not compress against them.
**This is a derailment.**

What has changed, and it is the only reason this is a WATCH rather than a discard: the derailment has
**plateaued**. Revenue decline decelerated (−4.9%, −2.6%, −2.9% H1-26); the company says trading
"stabilised"; factory yields are improving; energy is significantly hedged for the year; the
−17.8% headcount reduction is already in the run-rate. There is a credible self-help margin path that
does not require hospitality demand to recover. It is an option, not a fact, and the Sept print is
where it becomes one or the other.

**AI-complex test:** not applicable. CHH is not `ai_complex`, has no AI-capex linkage in either
direction, and the entry neither requires the AI cycle to hold nor benefits if it breaks. The frozen
house call AI-BREAK|2027-12-31 @ 0.45 is orthogonal here — stated explicitly so it is not averaged away
by silence.

---

## 6. Four-idea frame

1. **Long the self-help margin inflection.** Buy trough margin on stabilising revenue with automation
   capex landing. Requires the Sept interim to show it. *This is the only live idea.*
2. **Long the dividend.** 5.45% yield, net cash, no covenants. **Killed by B-1** — 81% of FCF is
   committed once the pension schedule restarts; the yield is the thing most at risk, not the support.
3. **Long the asset / consolidation.** 0.79x pension-adjusted book, £42m cap, 200-year franchise, a
   17%+ family stake. Real but unhandicappable; no offer period, no approach disclosed.
4. **Short / avoid.** Structurally shrinking end-market, fixed-cost base, AIM microcap with a 260bp
   touch. The short does not pay: net cash, no covenants, honest accounts, and the bounce already ran
   42%. **Correct expression is neither leg — it is a price gate.**

---

## 7. Valuation and scenarios

EV build (cap structure verified clean — 10,997,835 ordinary shares only):

- Market cap 385p × 10,997,835 = **£42.34m**
- Net cash FY25 = cash 10,808 − lease liabilities 3,384 = **£7.42m**
- **EV = £34.92m** → EV/EBIT(FY25 5,643) = **6.19x**, EV/EBITDA(9,312) = 3.75x
- Charging the pension schedule as an EV-like claim (PV ~£4.5m): adjusted EV £39.4m → **EV/EBIT 7.0x**
- P/E = 385/39.7p = **9.70x** on trough EPS

| Scenario | p | Thesis | FV |
|---|---|---|---|
| **Bear** | 0.35 | Hospitality stays soft, Q4 disappoints, margin sticks 7.0-7.5%. Pension + dividend force a second cut. EBIT £5.0-5.5m, EPS ~35p. An AIM microcap with a shrinking top line and a cut payout re-rates to ~7x. | **260p** |
| **Base** | 0.45 | Sales flat, self-help carries margin to ~9% through FY27, EBIT ~£6.9m, EPS ~48p, 9.5x, dividend held at 21p. | **430p** |
| **Bull** | 0.20 | Hospitality recovers, the £120m ceramics package delivers real energy relief, automation compounds. Margin ~11%, EBIT £8.4m, EPS ~60p, 11x. | **620p** |

**E[FV] = 409p** vs 385p spot → **+6.1% gross, ~+4.8% after the 130bp entry half-touch.**

Six percent of expected edge, on a name where exit takes 3-8 sessions and the round-trip touch is
260bp, four weeks before a print that decides the base case. That is not a position; it is a coin
flip with a toll booth on both sides.

---

## 8. Score: 3/10 — REJECT, WATCH with a price gate

**For (3 points earned):** honest accounts, verified anti-masking on four independent axes; net cash,
no covenants, clean cap structure; trajectory has plateaued with a real self-help option; IBKR line
verified executable; 6.2x EV/EBIT on trough margin is genuinely not expensive.

**Against (why it stops at 3):**
1. **Derailment, not de-rate** — fails the frame's central test outright.
2. **+42% off the low already** (intraday, 134 days). The easy re-rating is behind us.
3. **+6.1% expected edge does not survive 260bp of friction** plus 3-8 session exit.
4. **£1.75m/yr starts in seven weeks**, taking committed cash to 81% of FCF, with the pension note
   itself pointing at the dividend. Disclosed — and, on the evidence of the price, not modelled.
5. **Print risk in ~4-5 weeks** on the exact variable the base case rests on.

Per the response taxonomy: this is a **valuation finding → price gate** (the only case where a price
gate is the right instrument), with a **business-risk finding → size cut** layered on top.

- **Price gate: re-court at ≤300p.** At 300p, E[FV] 409p = **+36% gross, ~+34% net**. That level is
  +11% above the 270.9p low — it does not require a new low, only a give-back of the bounce.
- **Size if it ever clears: 0.50%** of $3.3M = ~$16,500 (not the 0.75% UK cap — cut one notch for the
  pension-cash and second-dividend-cut risk). $16,500 fits inside one median session ($17,700).
- **Instrument:** limit only, never market, never a marketable order into a 10p touch. GTC ladder at
  300 / 288 / 275p, thirds. No premium selling (taxable book doctrine); no options exist on this line
  in any case.

**Not escalated to red team** — the threshold is 6/10 and this is a 3. Nothing here is decisive enough
to warrant a stronger model; the finding that *would* have been decisive (the pension cash schedule)
was already primary-verified by the deep-read child from Note 19.

---

## 9. Freezable call

**`CHH.L | 2026-09-30`**

> **Bar:** Churchill China's H1-2026 interim results (company-stated: "early September 2026") report
> **operating profit ≥ £3.3m** for the six months to 30 June 2026 — that is ≥ 8.8% margin on the
> already-announced £37.4m of H1 sales, versus £2.8m / 7.3% in H1-2025.
>
> **our_p = 0.38**

Why this bar: revenue is pre-announced, so the interim is a **pure margin print** — the single cleanest
test of the self-help thesis available anywhere in the calendar. Below £3.3m and the automation and
attrition story has not reached the P&L, the base case is broken, and the WATCH should be discarded
rather than gated. At or above it, the base case is live and the gate should be re-cut upward.

Reasons our_p sits below a coin flip: the company itself says cost pressure has been "mitigated some
but not all… particularly within distribution costs"; H1 and H2 margins ran near-identical in FY2025
(7.3% / 7.5%), so there is no seasonal tailwind to borrow; and £3.3m requires +18% operating profit on
−2.9% revenue.

**Secondary bar (same print, same date, scored separately):** interim dividend held at **≥ 7.0p**.
**our_p = 0.72.** This is the direct test of B-1 — the declaration lands within days of the pension
schedule restarting. A cut here converts the review flag into a confirmed capital-allocation break and
should trigger an immediate discard, not a wider gate.

---

## 10. Dated kills / tripwires

| Trigger | Date | Action |
|---|---|---|
| H1-26 operating profit < £2.8m (below the H1-25 base) | early Sept 2026 | **DISCARD** — the plateau claim is refuted; delete from watch |
| Interim dividend cut below 7.0p | early Sept 2026 | **DISCARD** — B-1 confirmed, capital allocation broken |
| H1-26 operating profit ≥ £3.3m **and** price still ≤ 340p | early Sept 2026 | Re-court immediately with the gate raised to 340p |
| Any RNS disclosing an accelerated or increased pension contribution schedule | any | **DISCARD** |
| Q4-2026 trading update signals FY below Board expectations | ~Jan-Feb 2027 | **DISCARD** |
| Offer period opens / Rule 2.4 approach | any | Different court — special situation, not this one |
| Price ≤ 300p with the Sept print already clean | any | **Arm the gate**, tranche 1 of 3 |

---

## 11. Generator defect notes (CHH row — for the shelf maintainer)

1. **`pension_source: "NONE_FOUND"`, `pension_unverified: true`** — the guard **fired correctly as a
   warning** and its note ("treat net cash as UNVERIFIED, not clean") was right. It could not act.
   Ground truth from AR2025 Note 19: a **£7,651k SURPLUS** sitting in book equity = 12.4% of the
   £61,539k book, understating P/B by 13pp (0.688 → 0.786).
2. **Missing field: `pension_cash_schedule`.** No field in the row can express "surplus scheme that is
   nonetheless a contractual £1.75m/yr cash consumer for 34 months." This is the single most
   decision-relevant fact about the name and the schema cannot hold it. Source it from the
   triennial-valuation paragraph of the DB note and charge it against `fcf` — **a surplus scheme can
   still be a cash consumer**, and the sign of the balance-sheet number tells you nothing about that.
3. **`pct_off_52w_low` / `days_since_low` are close-basis** (0.3509 / 119) where the intraday basis is
   +42.1% / 134 days. Both are defensible; neither is labelled. Put the basis in the field name.
4. **`adv_block_inflated: true` was correct.** Median $88.5k vs IBKR's 90-day mean $232.4k — a 2.6x
   gap. The guard works; keep ranking on the median.
5. **Cross-cutting (also hit LBG): `yfinance fast_info.market_cap` returns pence × shares for GBp
   lines** — CHH reports **4,234,166,475** against the correct £42,341,664. A live 100x
   priceMagnifier trap. `.info['marketCap']` is correct and the shelf used it; anything downstream that
   reaches for `fast_info` will silently mis-scale by 100x.

---

*Court: `lse_shelf_20260804`. Prices tape-verified 2026-08-04 in GBp from IBKR conid 748086669 and
yfinance CHH.L. Fundamentals from AR2025 (deep-read child, primary) and RNS 31-Jul-2026 /
29-May-2026 / 03-Sep-2025 via investegate. UK reporting is semi-annual: the audited base is
31-Dec-2025 (seven months stale) and the only newer data is the unaudited 31-Jul-2026 sales-and-cash
line. No shared stores written.*
