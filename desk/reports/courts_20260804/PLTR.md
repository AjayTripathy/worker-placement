# PLTR — Palantir Technologies | COURT_QUEUE_20260804, tier-2 AI-COMPLEX conflict cohort #1

**Court date** 2026-08-03 (evening, US) for the 2026-08-04 session.
**Verdict: REJECT 3/10 — price gate, not a business objection.**
**Basis of every price below: IBKR live snapshot 2026-08-03, `last` $144.33, `is_close:false` (after-hours, +14.87% vs the 8/3 regular close of $125.65). Prior regular closes from yfinance daily bars: 7/31 $123.06.**

---

## 1. Cause-check — the drawdown, and the event that ended it

The screen picked PLTR up at $123.06 / −41% from its own three-year high of **$207.18 set 2025-11-03**. The cause of that fall is now fully readable and it is **not** an estimate problem.

| Event | Source | Result |
|---|---|---|
| Q2-2026 results released **today, 2026-08-03** | 8-K 0001321655-26-000039, EX-99.1 `a2026q2ex991pressrelease.htm` | CONFIRMED |
| Revenue $1,935.5M, **+93% y/y** (Q2-25 $1,004M per 10-Q XBRL) | press release + companyfacts | CONFIRMED |
| GAAP income from operations $912M (47% margin); GAAP net income $1,062M (55%) | press release | CONFIRMED |
| **GAAP EPS $0.41 = Adjusted EPS $0.41**; adjusted net income ($1,047M) is *below* GAAP net income | press release | CONFIRMED |
| Adjusted FCF $1,220M (63% margin); cash + ST Treasuries **$9.2B**, no debt | press release; 10-Q 3/31/26 showed $2,292M cash + $5,735M marketable securities, `LongTermDebt` absent since 2021 | CONFIRMED |
| FY-2026 revenue guidance **RAISED** to $8.150–8.158B (+82% y/y) | press release | CONFIRMED |
| Q3-2026 guide $2.160–2.164B (+83% y/y vs Q3-25 $1,181M) | press release | CONFIRMED |
| US commercial +149% y/y to $764M; US government +90% to $809M; US commercial RDV $6.238B +124% | press release | CONFIRMED |
| Market reaction | IBKR after-hours print $144.33, +14.87% | CONFIRMED |

The −41% drawdown from November-2025 to the June-25-2026 low of $107.27 happened **while revenue nearly doubled and guidance was raised at every print**. Trailing P/S went from ~132× (mid-2025) to ~56× today. That is the purest **DE-RATE** in this five-name cohort — the HUBS/CTSH/SAP signature in form and in fact.

## 2. Path check — the premise expired overnight

| Metric | At the screen ($123.06) | Live ($144.33) |
|---|---|---|
| Drawdown from 52w high ($207.52 intraday, IBKR) | −40.7% | **−30.4%** |
| Off the 52w low ($106.37, IBKR; 2026-06-25) | +15.7% | **+35.7%**, low 39 days old |
| Generator band 35–78% drawdown | qualifies | **FAILS — out of band** |
| Generator `entry_exhausted` (>35% off a <90-day low) | no | **YES** |

PLTR no longer satisfies the screen that surfaced it, on either the depth gate or the path gate. Anyone entering on 8/4 is buying a +15% earnings gap, 39 days off the low, at a price the generator would now reject outright.

## 3. Gate test — GUIDE-DECEL fired FALSE on PLTR

The queue flagged PLTR `GUIDE-DECEL` ("forward revenue growth <60% of trailing"). The company guides **+82% for FY-2026** against a trailing three-year revenue CAGR the screen itself recorded as 32.9%. The ratio is ~2.5×, not <0.60.

Root cause (read from `verticals/generators/quality_drawdown.py`): the flag divides yfinance's `revenue_estimate.loc["+1y","growth"]` — a **consensus** number — by `info["revenueGrowth"]`, a **realised** number. For a company whose consensus is chronically stale between raises, and where the trailing figure is itself measured on an accelerating base, the ratio is meaningless. This is not a small-print artifact: it demoted PLTR's score by ×0.65.

**Recommended gate change:** suppress `guide_decel_flag` when the subject filed an earnings 8-K/6-K within the last 10 trading days, or when the company's own published guidance is available (PLTR publishes an explicit FY revenue range — no consensus proxy is needed). Companion: the flag should compare *company guidance* to trailing where guidance exists, and only fall back to consensus where it does not.

Second gate finding: nothing in the screen re-checks a name after a print. PLTR moved from "qualifies" to "fails two gates" in one session.

## 4. Which leg of the AI cycle funds PLTR's earnings

Not capex. Not silicon. Not inference-hosting resale.

- **US government $809M (42% of total, +90% y/y)** — funded by DoD and allied appropriations. Counter-cyclical to a private-capex break, and in a break scenario the sovereign-AI budget line is the one that most plausibly *grows*.
- **US commercial $764M (39%, +149%)** — funded by enterprise **operating** budgets for AI deployment, not capital budgets for compute. This is the leg that thins in a break, but it thins the way SaaS thins in a recession, not the way an ASIC order book vanishes.
- **Zero credit exposure to the complex.** No debt, $9.2B net cash, no neocloud counterparties, no take-or-pay, no vendor financing, no GPU-backed paper. PLTR cannot be the subject of the credit event the house call describes, and it is not a counterparty to one.

## 5. Conflict resolution vs AI-BREAK | 2027-12-31 @ 0.45

The frozen call is a **credit** claim (neocloud default/seizure, take-or-pay impairment, GPU-ABS downgrade cascade, RPO counterparty reprice), not an equity-drawdown claim.

- **Does the entry require the cycle holding?** On the revenue leg: no. On the price leg: **entirely yes.** At $144.33 the fully-diluted market cap is ~$374B (2,571M diluted shares, 10-Q 3/31/26) against FY-26 guided revenue of $8.154B — **~42× forward sales, ~79× guided adjusted FCF**. At that multiple essentially 100% of the price is the multiple. A 45%-probability regime event is not compatible with paying a top-decile software multiple, however good the business.
- **Does the −30% de-rate price the break?** No. PLTR sits at roughly the **45th percentile of its own three-year P/S range** (19× in mid-2023 → 132× in mid-2025 → 56× TTM now). That is the *only* name in this cohort in the lower half of its own range — which is why the business score is high — but the mid-point of a bubble range is not a discount to a break.
- **Never averaged away:** the break scenario here is not "PLTR's revenue collapses." It is "PLTR compounds revenue at 40%+ and the stock still halves," which is precisely what happened between 2025-11-03 and 2026-06-25 with estimates rising the whole way. That is the risk, and it is unhedged at 42× sales.

## 6. Scenarios (FY-2027 basis, revenue $12.2B mid)

| | p | assumption | FV/sh |
|---|---|---|---|
| Bear | 0.30 | break lands; FY27 revenue $10.2B (+25%), 15× sales | **$63** |
| Base | 0.50 | cycle holds; FY27 revenue $12.1B (+48%), 30× sales | **$145** |
| Bull | 0.20 | FY27 $13.0B (+60%), 40× sales | **$216** |

**E[FV] $134.6 vs $144.33 live → edge −6.7%.** Fairly-to-richly priced with a fat left tail. Note the base case is deliberately *not* stripped to peer multiples (30× forward sales is a premium to every software comparable) — the conservative-FV reflex is not the reason this rejects.

## 7. Four-idea frame

1. **Long here** — rejected. Negative expected edge, both gates failed, buying a +15% gap.
2. **Long on a price gate** — the honest expression. $85–95 is 20–23× FY27 sales; it requires a −35% move from here and would coincide with the break beginning to price. Arm it, do not chase it.
3. **Short / premium sale** — rejected. Taxable book, no premium-selling (doctrine: CSP/CC premium is non-deferrable ST ordinary income); and shorting a 93%-grower into raised guidance is the wrong side of the momentum.
4. **No position, encode the mechanism** — adopted. The finding worth keeping is the gate defect and the de-rate/level distinction.

## 8. Catalyst map

| Catalyst | date | p | magnitude | note |
|---|---|---|---|---|
| Q2 earnings | **2026-08-03 — DONE** | 1.0 | +14.9% AH | already in the price |
| Q3-2026 print | ~2026-11-02 (Q3-25 was 11/03) | 1.0 | ±12–18% | the next fireable event |
| FY-27 guide | with Q4, ~Feb-2027 | 1.0 | large | first guide that spans the break window |
| US federal budget/CR risk to gov segment | ongoing FY27 approps | 0.3 | −5–10% | the gov leg's own tail |

## 9. Kills / re-court triggers

- **KILL the price gate** if a quarter shows US commercial RDV growth <60% y/y (from +124%) — that is the leg that justifies the multiple.
- **KILL** if GAAP EPS and adjusted EPS re-diverge by >20% (today they are identical; convergence is the honesty marker).
- **RE-COURT** at ≤$95 with the FY-27 guide in hand.
- **RE-COURT** immediately if a Tier-1 AI credit event resolves the house call NO before 2027-12-31.

## 10. Verification notes / gaps

- Q2-2026 **10-Q not yet filed** — segment detail, SBC, share count and RPO are press-release-only tonight. Diluted-share and cash figures used above are 3/31/26 10-Q + the press release's $9.2B. **This is the top UNVERIFIABLE item.**
- Cap structure pulled before any net-cash claim, per doctrine: no debt tagged since 2021, no preferred, no warrants found in companyfacts. Dilution runs through SBC only (Q2 GAAP-vs-adjusted op income gap $282M = 14.6% of revenue).
- Honesty read: **CLEAN.** GAAP net income exceeds adjusted net income; GAAP EPS equals adjusted EPS; guidance was raised, not re-based; the headline growth rate is the audited one. There is no takeaway-vs-data divergence to find. The problem is entirely the price.
