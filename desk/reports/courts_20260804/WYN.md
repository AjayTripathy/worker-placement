# WYN — WYNNSTAY GROUP PLC — COURT (LSE shelf, 2026-08-04)

**Verdict: REJECT 3/10** — on business quality and execution, **not** on accounting. Shelf rank
12/249. AIM. ISIN GB0034212331. **IBKR: conid 790402910, exchange LSE — RESOLVED.**

> **SELF-CORRECTION, RECORDED.** This court's first draft argued the 9.8x multiple was an artifact
> of a *recurring* add-back that had "grown five-fold over four years and would keep recurring."
> Primary sources **REFUTE that.** See §3. The verdict survives; the reasoning that produced it did
> not. Recorded rather than silently overwritten.

---

## 0. IDENTITY RESOLUTION

`WYN` = **Wynnstay Group plc**, AIM, UK agricultural supplies (animal feed, grain trading,
fertiliser/seed, and a retail depot estate). ISIN GB0034212331, Companies House **02704051**,
fiscal year ends **31 October**.

**Near-miss trap avoided:** IBKR `search_contracts("Wynnstay")` also returns **WYNNSTAY PROPERTIES
PLC (WSP, conid 90366428)** — an unrelated Surrey property investor. The shelf's ISIN-keyed
identity is correct; a name-keyed join takes the wrong company.

---

## 1. TAPE VERIFICATION

| item | value | source |
|---|---|---|
| Shelf price | 367.5p (GBX), 2026-08-04 | LSE price-explorer |
| yfinance last close | 367.5p, 2026-08-04 | daily bars |
| IBKR last | 367.5, **`is_close=true` — close-only, no bid/ask returned** | conid 790402910 @LSE |
| 52w range | 322.5 – 420.0 (IBKR) / 322.4 – 404.9 (yfinance) | |
| Today's volume | 15,441 shares ≈ £56.7k | IBKR |
| Exchange touch | bid 360 / offer 375 = **408bp**, **NMS 300 shares** | shelf row |
| 1-year price change | **−0.6%** | yfinance |

Units CONFIRMED pence across three sources.

---

## 2. CAUSE CHECK — THERE IS NO DRAWDOWN TO COURT

13.9% off a 52-week low that is **251 days old**; 1-year change −0.6%. The stock has been flat for a
year. This is not "quality at an own-history discount" — there is no de-rate event. That alone
makes it a poor fit for this court's frame before any fundamental work.

---

## 3. THE ACCOUNTING CLAIM — TESTED AND REFUTED (my own, against me)

**Draft claim:** the £5.2m of "unusual items" the screen adds back has recurred every year, grown
five-fold, and is therefore an operating cost — so 9.8x EV/EBIT is really ~21x.

**Authority:** FY2025 statutory Group accounts (y/e 31-Oct-2025, filed 25-Apr-2026, Companies House
02704051, Note 5); FY25 Final Results RNS 09-Feb-2026; FY24 Final Results RNS 11-Feb-2025; H1 FY26
Interim Results RNS 29-Jun-2026; Trading Update 01-Dec-2025.

| test | finding |
|---|---|
| What the £5.2m actually is | Note 5 subtotal **£5,195k** = non-recurring £5,881k **less** a £686k derivative mark-to-market gain. The £5,881k is **closure of manufacturing operations £4,137k** (Glasson Dock and Standon Mill) + **business reorganisation £1,744k** |
| Has it recurred every year? | **REFUTED.** FY2023 non-recurring was **£82k** — trivial. FY2024 £2,312k. FY2025 £5,881k. The gap opened only when Project Genesis landed |
| Is it cash? | **Largely NOT.** The 01-Dec-2025 TU guided the £5.4–5.9m charge to a **net cash cost of £2.0–2.5m after asset realisations** |
| Does it continue? | **REFUTED.** **H1 FY26 (to 30-Apr-2026) had ZERO non-recurring items** — the only adjustments were amortisation, share-based payments and derivative marks. FY25 guidance of "no further material restructuring charges expected in FY26" has held |

**Conclusion: this is a genuine, bounded, mostly non-cash three-year transformation charge cycle
(Project Genesis, launched 11-Feb-2025, completes 2027), not chronic "adjusted" inflation.** The
add-back is defensible. My draft was wrong.

**One real data-integrity finding survives:** the screen's EBIT of £9,099k is **Yahoo's own
normalisation and reconciles to neither audited figure.** For FY2025 the three bases are:

| basis | FY2025 operating profit |
|---|---|
| Statutory (audited) | **£3,651k** |
| Company "adjusted" (Note 5) | **£9,199k** |
| Yahoo "Operating Income" (what the shelf uses) | **£8,685k** |

The number driving EV/EBIT, the composite rank and the `melting` flag ties to **no line in the
audited accounts**. It happens to sit near the company's adjusted figure here, but that is not a
property anyone verified.

---

## 4. WHAT THE BUSINESS ACTUALLY EARNS

| £000 | FY2023 | FY2024 | FY2025 | H1 FY26 |
|---|---|---|---|---|
| Revenue | 735,877 | 613,053 | 583,436 | 304,100 (−0.3%) |
| Adjusted operating profit | 10,160 | 7,926 | **9,199** | 5,755 (+9.7%) |
| Statutory operating profit | 8,788 | 4,598 | **3,651** | **6,083 (+10.2%)** |
| Statutory PBT | 8,703 | 4,097 | 3,492 | 6,218 (+12.1%) |

Segmental FY25: Feed & Grain revenue £314.7m, **statutory operating loss £(3,627)k** — it absorbed
£4,579k of the closure charge; Arable £125.6m / £2,252k; Stores £143.1m / £5,026k.

H1 is ~57% of the adjusted year. Annualising H1 FY26 gives **FY26 adjusted operating profit ≈£10m
with no exceptionals**, versus statutory £3.65m in FY25 — which is precisely what the market's
`forwardPE` of **10.5x** (against `trailingPE` **30.6x**) is discounting. The recovery is
consensus, not a discovery.

**The reason to decline is what the business is, not how it reports.** £583m of revenue producing
~£9-10m of operating profit is a **1.6% EBIT margin**; ROE on FY26E is ~5%. That is a
low-return distributor with no pricing power, and the frame of this court — quality at an
own-history discount — does not fit it.

---

## 5. BALANCE SHEET — THE SHELF STRUCK IT AT THE SEASONAL TROUGH

| date | cash | borrowings | net cash excl. leases | net cash incl. IFRS-16 |
|---|---|---|---|---|
| 31 Oct 2024 (**FY end**) | £38,289k | £(5,465)k | **+£32,824k** | +£17,166k |
| **30 Apr 2025** (interim) | £11,010k | £(726)k | +£10,284k | — |
| 31 Oct 2025 (**FY end**) | £26,464k | £(746)k | **+£25,718k** | **+£9,764k** |
| **30 Apr 2026** (interim) ← *what the shelf used* | £11,626k | £(748)k | **+£10,878k** | unverified |

**Strong intra-year seasonality — net cash troughs at the April half-year and peaks at the 31
October year end** (the spring fertiliser and seed working-capital build). The shelf's
`ncash_r` of **−0.049** is struck on the April interim. On the audited October year end the same
company carries **+£9.8m net cash including leases (+11.5% of cap)**. The sign flips.

*(Note: the 01-Dec-2025 TU said "net cash of £26.4m"; the audited figure is £25.718m. £26,464k is
gross cash — the TU quoted the wrong line. Use £25.718m.)*

**Defined-benefit pension: SETTLED — there is NONE.** The LSE addendum's §2 requirement is
discharged. Four read-verified confirmations: no retirement-benefit caption anywhere on the
balance sheet; **no IAS-19 actuarial remeasurements in OCI in any of FY23/24/25** (a DB scheme
produces these mechanically every year — their total absence across three years is conclusive);
Note 8 shows pension costs as an expense line only (£2,469k); Note 9 discloses **money purchase**
(i.e. defined contribution) schemes for 2 directors. **The `pension_unverified` flag was correct to
route, and the answer is a clean negative — no hidden CHH/COST-style surplus or deficit here.**

---

## 6. EXECUTION — THE BINDING CONSTRAINT

408bp touch · **NMS 300 shares (≈£1.1k)** · median $88k/day, max order **$17.6k** · IBKR returns
**close-only, no bid/ask** · 1 analyst · `orphan=true`.

A 408bp round trip on a name whose central case is a consensus recovery to a 5% ROE is not
investable at our size. The AIM stamp exemption is worth 50bp against a spread of 408bp — the
intake's own §1(b) arithmetic, and it is decisive here.

---

## 7. SCENARIOS (2y, GBp)

| | p | fair value | reasoning |
|---|---|---|---|
| Bear | 0.25 | 300p | Project Genesis benefits leak to customers in a commoditised market; adjusted operating profit stalls at £8m; de-rate to 0.5x book |
| Base | 0.50 | 380p | FY26 adjusted operating profit ~£10m with no exceptionals, FY27 ~£11m; stock holds ~0.65x book — i.e. the consensus recovery arrives and is already paid for |
| Bull | 0.25 | 480p | Genesis completes in 2027 at a genuinely higher margin (2.2%+), ROE to 8%, re-rate to 0.8x book (the single analyst's 500p target) |

**E[FV] = 75 + 190 + 120 = 385p vs 367.5p spot → edge +4.8%**, before 408bp of entry friction.
**Net of the spread the edge is approximately zero. No position.**

---

## 8. KILL / REVISIT TRIGGERS

- **REVISIT** only if the touch narrows below 200bp **or** NMS rises above 1,000 shares — the
  execution gate is the binding one and nothing else matters until it clears.
- **REVISIT** if FY2027 (Genesis completion) delivers a group EBIT margin above 2.2%.
- **STAY OUT** if any further non-recurring charge above £1.5m appears in FY26 or FY27 — that would
  reinstate the original (now refuted) thesis.

## 9. FREEZABLE CALL

**WYN | 2027-02-28 | Wynnstay FY2026 (year to 31-Oct-2026) reports adjusted operating profit
between £9.5m and £11.0m AND non-recurring items below £1.0m | our_p = 0.65.**

Rationale: H1 delivered £5,755k adjusted with zero exceptionals against a ~57% H1 weighting, and
management has guided to no further material restructuring. Both legs should hold.

---

## 10. UNVERIFIABLE / GAPS (not clean — listed)

1. **Project Genesis has never quantified its expected annualised savings.** Checked across the
   Feb-2025 launch RNS, the FY25 results and the H1 FY26 results — **no number has ever been
   published.** A three-year transformation programme with no stated benefit target is a genuine
   disclosure gap, and it is the single thing that would make the bull case underwritable.
2. **Net debt including IFRS-16 leases at 30-Apr-2026 is UNVERIFIED** — the interim returned a
   figure internally inconsistent with the audited 31-Oct-2025 position. Only the ex-lease figure
   (+£10,878k) is read cleanly.
3. **Capital commitments note UNREAD** (LSE addendum §3, the THX lesson) — the 10.9% FCF yield
   carries an unquantified claim.
4. **wynnstay.co.uk returns HTTP 403 on every path even with a full Chrome fingerprint.** Primary
   access was via Investegate RNS full text and Companies House; the CH filing is an **image-only
   scan with no text layer**, so Note 5, Note 8 and Note 9 were read visually rather than
   text-searched. The figures are read, not grepped — a lower-redundancy basis than a text PDF.

---

## 11. GUARD GRADE

**`melting` (ebit_vs_peak 0.42): CORRECT VERDICT, FRAGILE MECHANISM — and it survives the
correction.** Checked against the company's own adjusted series (FY22 ~£21.7m → FY25 £9.2m), the
0.42 ratio holds, so the flag is not an artifact of Yahoo's normalisation. But the anchor is the
**FY2022 fertiliser-and-grain inflation spike sitting at the oldest edge of the window**, and 27 of
the 54 melting names on this shelf (50%) share that shape. When Wynnstay reports FY2026 in roughly
three months, FY22 rolls out of the window, the peak becomes ~£9.3m and `ebit_vs_peak` jumps
**0.42 → ~0.98 with zero change in the business.** A verdict that flips on the calendar is not
measuring the business. Fix: carry `peak_is_window_edge`, and prefer a "no recovery in N years"
test on anything commodity-exposed.

**`ncash_r` (−0.049): WRONG — struck on the seasonal trough.** Same interim-vs-annual defect as
SPR, opposite direction. Year-end net cash is **+£9.8m incl. leases (+11.5% of cap)**; the shelf
shows net debt. See gate grade §3b.

**`pension_unverified`: CORRECT ROUTING, clean negative answer.** Worked exactly as designed.

**Intake routing ("skip on execution alone"): CORRECT, and it is the right reason.** The stronger
grounds are execution and business quality; the accounting objection I reached for does not hold.
