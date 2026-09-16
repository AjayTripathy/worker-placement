# HSBK.L — Halyk Bank (Kazakhstan), London Reg S GDR — RE-COURT
**Date** 2026-08-05 (evening; grades for the 08-06 session) · **Court** court_queue_20260804
**Position** 334 GDR @ $29.965 · spot $33.10 · +$1,047 (+10.5%) · 1.08% of NLV ($1,021,585)
**Prior state** HELD / ADJUDICATED, conviction 6/10, no FV, no target, no trim prose anywhere on record.

> **Three of this court's own first-pass numbers were REFUTED by primary sources mid-run and are
> corrected below with the retraction stated. Book value, dividend yield, and ROE were all wrong on
> the first pass — two of them in the bullish direction, one in the bearish.**

---

## 1. THE EXECUTABILITY TEST (run FIRST — it was the premise of the re-court)

The 08-05 exit sweep flagged this line "CLOSE-ONLY on LSEIOB1 with an EMPTY BOOK — the EXIT itself may
not be executable," and inferred alerts-only was forced. **REFUTED.**

| # | Claim under test | Method / source | Result | Finding |
|---|---|---|---|---|
| E1 | The account can trade this line at all | IBKR blotter, `get_account_trades` DAYS_90 | order_id 5373062263: **BUY 305+17+9+3 = 334 GDR, order_type LIMIT @ 29.95, exchange LSEIOB1**, 2026-07-01 07:00:28Z→07:27:12Z, 4 executions | **CONFIRMED — we hold trade permission and a LIMIT order rested and was worked for 27 minutes on this exact line. How we bought it is how we sell it.** |
| E2 | "Empty book" = a venue restriction | `get_price_snapshot` conid 80626741 at 2026-08-05 **23:55 UTC = 00:55 London** | LSE IOB trades ~08:00–16:30 London; venue shut ~8.5h. `bid-ask:{}` + `is_close:true` are the expected artifacts of a **closed** market | **REFUTED — observation-time artifact, not a gate** |
| E3 | We are blind to the quote | `get_price_history` conid 80626741 | `{"error":"No market data permissions"}` | **CONFIRMED — but this is the MARKET-DATA subscription, a different IBKR permission from order routing.** Dictates order *type*, not order *possibility* |
| E4 | GTC works on foreign venues here | `get_account_orders`, ~120 live orders | GTC limits resting now on LSE (TW., FUTR, CAML, FDM, OMG, SPR, TFW), Tokyo, Korea, Warsaw, Helsinki, Tel Aviv | **CONFIRMED — LSEIOB1 is an LSE segment** |
| E5 | Our size is a liquidity problem | yfinance HSBK.L (12 sessions to 08-04) + IBKR `avg_90d_usd_volume` | median **81,668 GDR/day**, **zero** zero-volume sessions; **$2,060,520/day** USD turnover. Our 334 GDR = **0.41% of median daily volume** | **REFUTED — no size constraint** |
| E6 | An HSBK order currently rests | `get_account_orders` | none | CONFIRMED — the §6 violation was real |
| E7 | **The issuer is a standing buyer in this very line** | Company buyback page (embedded JSON) via primary pull | **USD 50mn GDR buyback, 1-Oct-2025 → 1-Oct-2026, $11.1mn executed; last purchases 14–16 Jul 2026 at $30.70/GDR**; prior $50mn programme 2024-25 used $22.3mn | **CONFIRMED — the company bids the London line. A price-sensitive floor near $30–31, and direct evidence of commitment to the venue.** |
| E8 | Delisting / migration to KASE or AIX | Full RNS review (152 announcements, latest 03-Aug-2026) + company news | **NOTHING FOUND.** Contrary evidence: Almex ran a **fully marketed GDR secondary of 7.6% (~$475mn) in Nov-2025**, and GDR holders rose **34.5% → 35.1%** of the register Dec-25→Mar-26 | **The line is being DEEPENED, not retired** |

**Ruling.** The exit is **EXECUTABLE by resting GTC SELL LIMIT on LSEIOB1**. Alerts-only is **NOT**
forced. The correct label is not "un-sellable"; it is **"sellable, but un-watchable"** — we have order
permission and lack market-data permission. Binding consequences:

- **LIMIT ONLY. MARKET ORDERS PROHIBITED.** The sweep floated "LSE IOB market order days"; that sends
  an unpriced order into a book we are contractually blind to, on a $2M/day venue. Worst available choice.
- Resting GTC limits are **unaffected** by our market-data gap — the order sits at the exchange, which
  can see the book even though we cannot.
- Fills print in the London morning (03:00–11:30 ET); our own buy filled 03:00–03:27 ET.
- **SCANNER FIX REQUIRED:** for LSEIOB1, `is_close=true` + empty bid/ask *outside* 08:00–16:30 London
  is the NORMAL state, not a flag. This name will re-fire a false executability alarm daily until a
  venue-hours guard exists.
- No alternative path is needed. `search_contracts` returns exactly one Halyk instrument (conid
  80626741, LSEIOB1, "HALYK SAVINGS BANK-GDR REG S"); no KASE/AIX venue is offered to us. The one line
  we own is the one line we can trade — and we can trade it.

### 1b — the executability risk that IS real, displaced in time
This is a **Reg S GDR**, not an ordinary share. The near-term stranding branch is now largely closed
by E7/E8 (active buyback, a marketed secondary through the line, rising GDR register share, RNS
current). What remains is the **sanctions branch, where the line and the thesis fail simultaneously**:
in a designation event the depositary suspends and the venue halts *before* any holder exits — the
2022 Russian-GDR precedent (Sberbank/Gazprom LSE lines to ~$0.01, then forced cancellation, Western
holders stranded in local shares they could not custody). For a US holder at IBKR with no KASE access,
practical recovery there is near-total loss.

**Therefore downside ALERTS are close to worthless as risk control on this name.** An alert at $28
fires on ordinary volatility; the tail event offers no fill at any price. **The only working control
is size, set in advance.** The record already got this right ("UNLEVERED — binary sanctions tail"). At
1.08% of NLV the tail is bounded at ~0.9% of NLV. Keep it there.

---

## 2. MODE B — first principles, leading

### B1 — RETRACTION: the desk's own panel input is stale and flattered, and it flattered us bullish
`political_risk_xsec` carries **HSBK.L ROE = 30%**, producing residual −1.23x P/B, **z −2.14, the
cheapest EM bank in the book**. Primary sources say that input is out of date and moving fast:

| | source | value |
|---|---|---|
| FY2024 ROE | FY25 IFRS press release | 34.0% |
| FY2025 ROE | FY25 IFRS press release (19-Mar-2026) | **32.6%** |
| Q1-2025 ROE | Q1-26 IFRS press release | 34.6% |
| **Q1-2026 ROE** | **Q1-26 IFRS press release (18-May-2026)** | **25.9% — −870bps YoY** |

Q1-26 net income **KZT 234.8bn, −14.6% YoY**; NIM 7.5→7.0%; cost/income 16.5→18.2%; cost of risk
1.2→1.5%; and the **loan book contracted −2.2% QoQ**. Re-running the panel at a normalized ~22.3% ROE
(§B2) collapses the residual from −1.23 / z −2.14 to roughly **−0.75 / z −1.31**, and the module's own
de-bias note (peer-anchored ≈ −0.3x) takes it to about fair. **We were within one input of being
fooled by our own stale model.**

### B2 — THE HONESTY FINDING: reported ROE is coverage-release-flattered, and management's narrative
### diverges from management's own data
Asset quality, all from the company's own Q1-2026 release and presentation:

| metric | 5 quarters ago | 31-Mar-2026 |
|---|---|---|
| NPL 90+ | 3.1% | **4.7%** |
| Stage 3 | 6.8% | **8.2%** (KZT 1,101bn) |
| **Stage-3 coverage** | **75.2%** | **59.2%** |

**Coverage falling 16pp while the problem stock rises is the classic provisioning-deferral tell** — it
flatters current earnings. Management's Q1 language is that the quarter *"supports the full-year 2026
guidance communicated earlier"*, said over a print in which earnings fell 14.6%, margin compressed,
cost/income rose, cost of risk rose, the loan book shrank, NPLs rose 160bps and coverage fell.
**That is a takeaway-vs-data divergence, not a disclosed-bad-news case** — every datum is disclosed
(which is to the company's credit), but the marketed conclusion is not what the data says.

Quantifying it: restoring 75.2% coverage on KZT 1,101bn of Stage 3 requires **KZT 176bn** of extra
provisions = **4.7% of equity**. Built over one year that is ~KZT 132bn post-tax against annualised
net income of ~KZT 939bn — a **14.1% earnings hit**, taking Q1's 25.9% ROE to a **normalized ~22.3%**.

Two things follow, and they cut in opposite directions:
- **It is an earnings event, not a solvency event.** k1-1 is **21.0%** against a 9.5% minimum — the
  capital to absorb it exists many times over. The dividend is not threatened by this.
- **But it is the reason the "30% ROE at ~1.1x book" framing is wrong.** §3 shows the market has
  already priced the normalized number, not the reported one.

Company attributes the Stage-3 build to a moratorium on selling problem retail loans to collection
agencies, stated to run **"till May 2026"**. **H1-2026 is therefore the first period that can reveal
whether the Stage-3 build unwinds or was masking genuine deterioration.** That is the print.

### B3 — The peer-relative cheapness is substantially a LISTING-STRUCTURE artifact
| | P/B | ROE | sovereign | listing |
|---|---|---|---|---|
| **HSBK.L** | ~1.15 | 32.6% rep. / ~22% norm. | 150bps | **Reg S GDR, LSE IOB** |
| BGEO.L | 1.93 | 27.4% | 152bps | LSE **premium ordinary**, FTSE 250 |
| TBCG.L | 1.34 | 24.0% | 152bps | LSE **premium ordinary**, FTSE 250 |

BGEO and TBC **earned** their multiples by converting *out* of the GDR structure into premium ordinary
listings with UK index membership — unlocking index demand and institutional mandates a Reg S GDR is
structurally excluded from. **Underwriting peer parity is underwriting a listing migration that has
not been announced** (and E8 found no sign of one in either direction). The re-rate leg is
structurally impaired; this court does not lean on it.

### B4 — Governance: the yield is a controlling-shareholder preference, not a minority right
The AGM circular states total **voting** shares of **7,904,221,264** against **10,894,886,733** in
circulation — roughly 3bn shares, almost exactly the GDR block, sit **outside the voting base**.
Almex's 6.757bn is therefore **~85% of votes actually counted**. Minority GDR holders have essentially
no governance lever. The 55–60% payout has been delivered three years running (FY23 55%, FY24 60%,
FY25 60%) — but by preference, not protection. Almex has also shown it is a **seller** (7.6% marketed
in Nov-2025); a further block is a live supply overhang against a ~$9bn cap. **This is worth ~100bps
on the cost of equity and is applied in §3.**

### B5 — Two-leg EM-bank method
**Leg 1, funding moat — PLAUSIBLE, still not CONFIRMED from the deposit note.** Successor to the
Soviet-era People's Savings Bank; dominant retail KZT deposit franchise; retail deposits +10.4% YoY vs
corporate +3.0%. Domestic tenge retail funding, no evident USD wholesale dependency. *Consequence:*
the sanctions tail does **not** work through insolvency — cut correspondent access and the bank keeps
its deposits and keeps earning in tenge. What breaks is the **GDR holder's claim** (USD dividend can't
clear the depositary; programme suspends). The bear case is therefore **bimodal**, and the record's
single line "correspondent-bank action → EXIT review" papered over the fact that in that branch there
is nothing to exit into. *Still needed:* loan/deposit ratio and any USD wholesale/eurobond maturities.

**Leg 2, geopolitical tail — sized, frozen call RESPECTED not contradicted.** Existing
`HSBK.L | 2026-12-31 | our_p 0.82` (no material secondary-sanctions action touching KZ bank USD
access) stands. Screening found **no 2026 OFAC designation or correspondent-banking action against
Halyk or any Kazakh bank** — but coverage was thin, so this is *not disproven*, not *clear*.
Kazakhstan sovereign **Fitch BBB, Stable** (Jun-2026, secondary source only); Halyk issuer **Fitch
BBB−** affirmed Sep-2025 (company/RNS confirmed). The IG kill trigger is two notches away.
Decomposing to stranding: 0.18 × ~0.35 (reaches Halyk) × ~0.6 (programme terminated) ≈ 3.8% by
year-end, **~5%/yr**, at ~85% severity ⇒ **~4%/yr expected loss**. E7/E8 reduce the *voluntary*
migration branch to near zero but do nothing for this one.

---

## 3. THE FV SET — struck fresh, on primary data

### Corrections to this court's own first pass (stated, not buried)
| item | first pass | primary source | corrected |
|---|---|---|---|
| BVPS/GDR | $27.63 *(back-solved from the desk panel)* | Q1-26 interim FS: equity attributable **KZT 3,740,929mn**, shares **10,894,886,733**, **GDR ratio 40 CONFIRMED** (company "About us", cross-checked to the cent against the declared $2.56/GDR at KZT 469.85) | **$29.23 at 31-Mar**, roll-forward for Q2 retention less the KZT 328bn dividend paid 18-May ⇒ **$28.70 now** |
| spot P/B | 1.198x | — | **1.153x** *(I had it too rich)* |
| dividend yield | 12.28% *(IBKR feed)* | AGM 23-Apr-26 **KZT 30.10/sh = $2.56/GDR**; EGM 20-Aug-26 proposes **KZT 28.09/sh ≈ $2.39/GDR**; FY25 total **KZT 58.19 = $4.95/GDR, payout 59.9%** | **14.97% at spot.** IBKR **understates**. Neither tranche is a special — Halyk pays two ordinary tranches per year (unbroken FY23/24/25) |
| ROE input | 30% (desk panel) | FY25 **32.6%**, **Q1-26 25.9%** | reported 25.9% falling; **normalized ~22.3%** (§B2) |

**RETRACTION, explicit.** My first pass claimed a triangulation — "payout 49% × ROE 30% ÷ P/B 1.198 =
12.27% vs IBKR's 12.28%, three numbers closing to 1bp." **That was a coincidence produced by two wrong
inputs.** The correct version: payout **59.9%** × ROE **32.6%** ÷ P/B **1.153**, adjusted for the ~14%
book growth between the FY25 average-equity period and today, ⇒ **~15.0%**, matching the
company-declared **$4.95/GDR = 14.97%** at spot. *That* is the valid check, and it says the carry is
**15%, not 12.3%.**

### Method
Gordon in USD terms. The standard Kazakh-bank trap is quoting a ~30% **tenge** ROE against a **USD**
cost of equity. Corrected: ROE_usd = ROE_kzt − KZT depreciation (5%/yr assumed); g_usd = retained
growth − depreciation; **payout 60%** (confirmed, three-year record). KZT/USD **469.85** (National Bank
of Kazakhstan, effective 06-Aug-2026, primary).

**Fair P/B grid:**

| durable ROE (KZT) | COE 12.5% | COE 14.0% | **COE 15.0%** | COE 15.5% |
|---|---|---|---|---|
| 32.6% *(FY25 reported)* | 4.39 | 3.28 | 2.81 | 2.62 |
| 26.0% | 2.20 | 1.81 | 1.63 | 1.54 |
| **22.3% *(coverage-normalized)*** | 1.56 | 1.33 | **1.21** | 1.16 |
| 20.6% | 1.33 | 1.15 | 1.05 | 1.01 |
| 18.0% *(our kill trigger)* | 1.05 | 0.92 | 0.84 | 0.81 |

**COE selection: 15.0%.** KZ USD sovereign ≈ UST 4.2% + 150bps = 5.7%; frontier-bank equity premium
8–9% ⇒ 13.7–14.7%; **plus ~100bps for §B4** (GDR block outside the voting base, Almex ~85% of votes
and a proven block seller).

### The decisive read
Spot **1.153x** implies a **durable KZT ROE of 20.6% at COE 14.0%, ~21.7% at 15.0%, ~22.2% at 15.5%.**
The coverage-normalized number from §B2 is **22.3%**.

> **The market is already pricing Halyk's coverage-normalized ROE at a governance-appropriate cost of
> equity — not its reported 25.9–32.6%. The apparent cheapness on headline ROE is not cheapness; it is
> the market correctly discounting a provisioning shortfall that management's "supports guidance"
> language does not acknowledge. We are not early to this; we are level with it.**

Note the convexity: ±4pp of durable ROE swings fair value ±35–40%. That alone justifies small and unlevered.

### Scenarios (12m, on BVPS $28.70)
| | p | FV | derivation |
|---|---|---|---|
| **BEAR** | 0.24 | **$19.25** | two branches: ROE→18% (the kill trigger) at COE 15.5% ⇒ 0.81x ⇒ **$23** (p 0.19), **plus the stranding branch** ⇒ ~$5 practical (p 0.05) |
| **BASE** | 0.56 | **$34.75** | normalized ROE 22.3%, COE 15.0% ⇒ 1.21x |
| **BULL** | 0.20 | **$44.00** | coverage build proves benign / moratorium unwind clean, ROE holds 26% ⇒ 1.54–1.63x ⇒ $44–47, partially realised |

**e_fv $32.88 vs spot $33.10 ⇒ price edge −0.7%. Zero, marginally negative.**

**Where the return is.** Base 12m = **+5.0% price + 15.0% dividend ≈ +20.0% gross**, less the ~4%/yr
tail cost ⇒ **~16% risk-adjusted against a 15.0% required return. ~1pp of excess. Fairly paid — this
is carry, not edge.**

---

## 4. VERDICT

# HOLD / RP_FAIR — 5/10. No add at spot. No trim at spot.

**Classification RISK_PREMIUM (fairly-paid), edge_source CARRY.** The fairly-paid doctrine makes this
an ownable default class with no edge required, provided fairness is *verified* (it is, and now on
primary data), tails are bounded and unlevered (1.08% NLV, no margin), and carry-vs-edge is labelled
(15% carry, ~0% price edge). The ledger's existing CARRY tag was right; the arithmetic behind it did
not exist until now — and the arithmetic is *better* on carry (15% vs 12.3%) and *worse* on earnings
quality than the record assumed.

**Why not higher:** the coverage-release flatter is real, ROE is down 870bps YoY, the loan book is
shrinking, and the H1 print is 13 days out. **Why not lower:** the market has already priced the
normalized ROE; capital is 21.0% against a 9.5% minimum; the 15% payout is three years unbroken and
delivered by a controlling shareholder whose own incentive sustains it; a $50mn issuer buyback is
bidding the line near $30–31; and the position is small.

**Taxonomy routing.** (a) executability — *data* finding, **RESOLVED, no kill**; (b) valuation —
fairly valued ⇒ **price gate on adds, not a sell**; (c) earnings quality + unhedgeable tail —
*business-risk* findings ⇒ **SIZE**, already correct. **Nothing routes to an exit.**

**Adds — AFFIRMED but GATED.** $28 (0.98x book) and $25 (0.87x book) are 19% and 27% below base FV and
correctly placed below, not at, market. **Do not add at $33, and do not add before the 18-Aug print**
(contract: no blind entry inside ~2 weeks of a print). Keep the rungs resting — they are 15%/24% below
spot and can only fill on an exogenous move — but re-derive them after 18-Aug.

**Not red-team required** (5/10, below the ≥6 threshold).

**Sizing conflict to surface (not resolved here):** the ledger's 2.0% target against the $3.3M
deployable base is ~$66k, exceeding the contract's ~1.2%/name cap (~$40k). At 1.08% of the current
$1.02M NLV the position is inside every limit. **The target needs restating against a single base.**

**Correlated-tail note:** the "5–6% frontier sleeve with TBC+BGEO" assumes diversification that does
not exist — Georgia and Kazakhstan are *the same* Russia-circumvention corridor and would be
designated in one news cycle. TBCG/BGEO are **not currently held** (verified), so this is not live;
flag it for the sleeve rule before that sleeve is ever built.

---

## 5. §6 EXIT EXPRESSION — RESTING, given the executability finding

§1 CONFIRMED the line is sellable by resting limit, so **the §6 default applies in full and the
alerts-only fallback is NOT invoked.**

Base FV is $34.75. Any rung below ~$35 sells *below fair value* into strength, surrendering a 15%
carry and paying ~50% short-term tax to do it — value-destructive. Rungs sit where the multiple starts
paying for the re-rate leg §B3 showed is impaired:

| rung | limit | shares | P/B at limit | rationale |
|---|---|---|---|---|
| **T1** | **$40.00** GTC SELL | 84 (25%) | 1.39x | ~15% above base FV |
| **T2** | **$44.00** GTC SELL | 84 (25%) | 1.53x | at bull FV; richer than the name has sustained as a Reg S GDR |

Core retained **166 shares** to carry the 15% dividend. Wrong-side test: **PASS** — both fill only on
strength, by construction (not the BRKR trap).

- **Order type: LIMIT, GTC, exchange LSEIOB1. MARKET ORDERS PROHIBITED** (§1 — blind to the book).
- **cancel_below $26.00** — below the $25 add rung; if we're buying down there we're not trimming up here (HUBS-182).
- **Ladder class: RIDES ITS OWN EVENT.** Rungs are anchored to court-blessed fair/bull value, not to a
  discount off a good-state price, and a named observable kill branch governs (H1 ROE <18%; Stage-3
  coverage falling further). At +21%/+33% they cannot fill on a normal print, and if they do fill on a
  spectacular one, selling into it is correct. **Keep resting through 18-Aug.**
- **⚠ EX-DIVIDEND ADJUSTMENT — MANDATORY.** The second FY25 tranche (**≈$2.39/GDR, 7.2%**) goes
  **ex on 26-Aug-2026** (EGM vote 20-Aug; Almex's 62% makes passage near-certain; pays 7-Sep). Fixed
  dollar limits do not self-adjust. These are **cum-dividend levels**; they cannot realistically fill
  before 26-Aug (+21%/+33% in 15 sessions). **At the 08-28 review, if not otherwise re-derived, reset
  to $37.60 / $41.60.** Same caution applies to the $28 alert — post-ex it will fire ~7% early.
- **Tax: SHORT-TERM.** All 334 shares acquired 2026-07-01; LT date **2027-07-02**. A T1 fill at $40
  realises ~$843 gain, ~$421 tax at ~50% combined (vs ~$202 if LT) — ~$219 of deferral forgone.
  Accepted: 2026 is a TLH-max year so an ST gain is doubly expensive, but at 1.39x book the valuation
  call outranks $219, and a resting limit cannot be date-conditioned at the broker.
- **review_by 2026-08-14** (two sessions before the 18-Aug print) — forced re-derive, not silent
  expiry. **Hard re-derive 2026-08-28**, after the print, the EGM and the ex-date.

**Downside — ALERT class only, never stops**, with §1b's caveat that these will not save us in the
stranding branch and are logged for completeness only: $28.00 (also first add — **ex-adjust after
26-Aug**), $25.00 (second add), plus condition alerts on correspondent-bank sanctions action, sovereign
below IG, and ROE <18%.

---

## 6. FROZEN-CALL PROPOSAL — **PROPOSE only, not armed**

The existing `HSBK.L | 2026-12-31 | 0.82` sanctions-posture call is untouched. This sits on the
orthogonal and now-decisive axis: §3 showed the entire valuation reduces to durable ROE.

> **HSBK|2026-08-18** — *"Halyk's H1-2026 IFRS results report an annualised ROE of 25.0% or higher."*
> **our_p = 0.45** · FAVORABLE = ROE ≥ 25.0% · event_type earnings_print · px_at_pred **$33.10**
>
> **Date is CONFIRMED from primary**, not estimated: RNS "1H and 2Q 2026 Results Conference Call
> Invitation", 03-Aug-2026 — *"Halyk Bank's 1H and 2Q 2026 unaudited consolidated financial results
> will be available starting from 18 August 2026."* (The company's own `/investment-calendar` page
> returns an empty event list — do not use it.)
>
> **Bar:** annualised ROE for the six months, as reported in Halyk's own H1-2026 release (consolidated,
> attributable to shareholders) — the same metric on which it printed 25.9% for Q1-26 and 32.6% for FY25.
>
> **Why 0.45 (deliberately near a coin-flip — that is the point).** Q1-26 already printed **25.9%**, so
> the bar sits essentially *at* the current run-rate and H1 ≥25% requires Q2 ≈ ≥24%. Every Q1 line item
> moved the wrong way (NIM −50bp, C/I +170bp, CoR +30bp, loans −2.2% QoQ, earnings −14.6% YoY), the
> drivers are sector-wide and persistent (higher bank taxes, higher reserve requirements, a strong
> tenge), and **the collection-agency moratorium ended in May — inside Q2** — which should force
> Stage-3 recognition and provisioning into exactly this print. Tilted just below even.
>
> **Information value:** a ≥25% print pushes market-implied durable ROE toward 26% ⇒ fair 1.54–1.63x ⇒
> **$44–47, and the bull leg re-opens on fundamentals rather than on the listing migration §B3 killed.**
> A sub-22% print is the first hard evidence for the bear leg and puts the 18% kill trigger in play.
> **Read alongside — the honesty tripwire: Stage-3 coverage at 30-Jun-2026 vs 59.2%.** If coverage
> falls again while Stage 3 rises, the ROE print is flattered regardless of its level.
>
> *Alternate formulation if a pure-honesty call is preferred:* **HSBK|2026-08-18 — "Stage-3 coverage at
> 30-Jun-2026 is below 59.2%", our_p 0.55.*

*Neither should be armed until the principal serializes it — this court does not touch the calibration ledger.*

---

## 7. UNVERIFIABLE / GAPS (UNVERIFIABLE ≠ clean)

1. **Funding moat is PLAUSIBLE, not CONFIRMED.** Asserted from franchise structure and the retail-vs-
   corporate deposit growth split; **the audited deposit note has not been read.** Needed:
   loan/deposit ratio, retail/corporate deposit mix, USD wholesale and eurobond maturities.
   **Still the single most valuable remaining verification** — the whole transfer-risk-not-solvency-risk
   reframe rests on it.
2. **OFAC screen is a NEWS sweep, not a list check.** No 2026 designation or correspondent-banking
   action against Halyk or any Kazakh bank was found, but coverage was thin. **Not disproven ≠ clear.**
   A direct OFAC SDN-list query was not run and should be.
3. **Kazakhstan sovereign Fitch BBB/Stable (Jun-2026) is SECONDARY-SOURCED** (Astana Times); the Fitch
   primary release was not reached. Halyk's own BBB− is company/RNS-confirmed but dates to **Sep-2025**
   — no 2026 issuer action located. No Moody's or S&P 2026 action found.
4. **Q2-2026 equity is ESTIMATED.** BVPS $28.70 rolls Q1's audited KZT 3,740,929mn forward with an
   assumed ~KZT 230bn of Q2 earnings less the confirmed KZT 328bn dividend. FV scales linearly with it.
   The 31-Mar figure ($29.23/GDR) is the hard number.
5. **KZT depreciation at 5%/yr is an ASSUMPTION**, not taken from forwards. FV is about as sensitive to
   it as to ROE. Complication: the news channel reports a *strong* tenge is currently denting bank
   profits — near-term FX is working against earnings, not for them.
6. **The Nov-2025 Almex secondary size/price ($475mn, 7.6%) is secondary-sourced** — the RNS exists
   (19-Nov launch, 21-Nov pricing) but the pricing announcement was not opened. The supply-overhang
   argument in §B4 is directional.
7. **Capital ratios are unconsolidated (Bank-only) NBK regulatory**, not IFRS-consolidated. k1-1 21.0%
   should not be called "CET1".
8. **Peer P/B and ROE for BGEO/TBCG/KSPI are the panel's curated 2026-06-30 values**, not re-pulled live.
9. **Long-run price history unavailable** — yfinance carries 12 sessions, IBKR bars are permission-blocked,
   stooq does not carry the line. The 52w range **$21.29–$35.60** is single-sourced (IBKR
   `misc_statistics`). Path read — **+55% off the 52w low, −7% off the high; a name near its highs, not
   a drawdown candidate** — is directionally sound but not bar-verified.
10. **IBKR's 12.28% dividend yield could not be reconstructed** from any combination of declared amounts
    ($4.05/GDR implied). Treat the feed as stale/partial; use the company numbers.

---

## 8. KILLS (dated)

| trigger | source | action |
|---|---|---|
| **H1-26 annualised ROE <18%** | company IFRS release **18-Aug-2026** | EXIT review — bear FV ~$23, −30% |
| **Stage-3 coverage falls below 59.2% again while Stage 3 rises** | same release | **honesty tripwire** — the ROE print is flattered regardless of level; cut target 2.0%→1.0% |
| ROE prints 18–22% two halves running | H1-26 then FY-26 | cut target; cancel T2 |
| Correspondent-bank / OFAC action touching Halyk | OFAC SDN, EU packages, LSE RNS | EXIT review — **but assume no fill.** Size is the control |
| Kazakhstan sovereign below IG (from BBB) | Fitch / Moody's / S&P | EXIT review |
| GDR programme suspension / termination / forced conversion | depositary notice, LSE RNS | **immediate escalate** — no orderly exit past this point |
| EGM 20-Aug fails to pass the second dividend, or payout guided below ~40% | EGM result, company declaration | re-derive FV — the entire return is carry |
| Almex markets another block | LSE RNS | supply overhang; re-derive entry rungs |
| Price ≥ $40 | resting T1 | trims execute |

## 9. CATALYST MAP — three events in nine days

| catalyst | date | p | magnitude | leading indicator |
|---|---|---|---|---|
| **H1/Q2-2026 IFRS results** | **18-Aug-2026 (CONFIRMED, RNS 03-Aug)** | 1.0 | **±15–25%** on the durable-ROE and coverage read | none — no analyst tape on this line |
| **EGM votes second FY25 dividend** (KZT 28.09) | **20-Aug-2026** | ~0.99 (Almex 62% of shares, ~85% of votes) | confirms ~$2.39/GDR | EGM materials already published |
| **Ex-dividend, second tranche** | **26-Aug-2026** | 1.0 | mechanical **−7.2%** price drop; pays 07-Sep | — |
| Secondary-sanctions posture | rolling to 2026-12-31 | 0.18 adverse | bimodal: mark-down or stranding | OFAC advisories, EU package drafts |
| GDR→ordinary listing migration | unannounced | low | **the only credible re-rate mechanism** (§B3) | LSE RNS, depositary notices |
| Issuer buyback resumption | programme runs to 01-Oct-2026 | — | floor near $30–31; $38.9mn of $50mn unused | buyback page purchase log |

---

## 10. WHAT CHANGED vs THE INHERITED RECORD

1. **"Exit may not be executable / alerts-only forced" → REFUTED.** Sellable by resting GTC limit; the
   real constraint is market-data blindness, which bans market orders only. Plus: **the issuer itself
   is bidding this line** under a live $50mn buyback, and ran a marketed secondary through it in Nov-2025.
2. **"No FV exists" → struck on primary data:** base $34.75, e_fv $32.88, spot $33.10, price edge −0.7%.
3. **"25%+ ROE at ~1.1x book = cheap" → the market is pricing the coverage-NORMALIZED ~22% ROE at a
   governance-appropriate 15% COE.** Fairly priced. We are level with the market, not ahead of it.
4. **NEW, and the reason to re-court: earnings quality is deteriorating and management's narrative
   diverges from its own data.** ROE 32.6%→25.9%, NPL 3.1%→4.7%, Stage 3 6.8%→8.2%, **coverage
   75.2%→59.2%** — while the release says the quarter "supports guidance." It is an earnings event, not
   a solvency event (k1-1 21.0%), and **the desk's own panel ROE input of 30% is stale and was
   flattering us bullish** (z −2.14 → ~−1.31 normalized).
5. **Carry is BETTER than recorded:** ~15.0% from company-declared dividends ($4.95/GDR FY25, 59.9%
   payout, two ordinary tranches, three-year record), not the 8–10% underwritten or IBKR's 12.28%.
   **My own first-pass 12.28% triangulation is retracted as a coincidence on two wrong inputs.**
6. **Sanctions tail refined:** transfer/stranding risk, not solvency risk. In that branch there is no
   exit — alerts do not protect, size does. Keep ~1%.
7. **Governance priced:** ~3bn shares (the GDR block) sit outside the voting base; Almex holds ~85% of
   votes and has sold a 7.6% block. Worth ~100bps of COE, now applied.
8. **§6 violation cured:** GTC trims $40 / $44, cancel_below $26, review 08-14, hard re-derive 08-28,
   with a **mandatory ex-dividend reset to $37.60 / $41.60** after 26-Aug.
