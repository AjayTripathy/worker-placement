# VTY — Vistry Group plc (LSE Main, GB0001859296) — COURT, 2026-08-04

**Verdict: REJECT 2/10.** Derailment in progress, pre-mark. No entry band at any price until the
24 September 2026 half-year mark is on the tape.

**Basis:** IBKR conid 26652747 (LSE), live streaming quote 290.2p at 17:29 UTC 2026-08-04
(`is_close:false`), −7.87% on the day, 13.76m shares, day range 258.8–318.0, prior close 315.0.
52w high 746.0, 52w low 220.0, YTD −54.76%. All fundamentals from the FY2025 Annual Report &
Accounts (year ended 31-Dec-2025, PDF pulled from vistry.co.uk), reporting currency GBP, price in
GBX. Fundamentals are **7 months stale** and the company has issued four negative updates since.

**Prior art — respected, not contradicted.** `desk/data/research_ledger.json` already carries
`VTY.L | AVOID | CYCLE-TRAP (falling knife)` from the 2026-07-23 batch, and carries Taylor Wimpey
(`TW.` STARTER-HALF) explicitly framed as "the anti-Vistry." This court reaches the same verdict
independently and adds the mechanism. It does not reopen the frozen call.

---

## 1. Cause-check — what actually happened (the brief's framing was one year stale)

The task framed this as "the 2024-25 profit-warning cascade (three warnings, build-cost
misestimates in the South division)." That is the *old* cascade. The tape says the decisive damage
is **2026 and still running**. Daily bars, yfinance unadjusted, cross-checked to IBKR 52-week stats:

| Date | Close move | Volume | Event |
|---|---|---|---|
| 2026-01-14 | −9.0% | 4.7m | Trading update (per company financial calendar) |
| **2026-03-04** | **−25.6%** | **13.7m** | FY25 results: 2026 margin warning; CEO Greg Fitzgerald steps down; chair/CEO roles split |
| 2026-03-19 | −7.8% | 6.8m | (no RNS found — UNVERIFIED trigger) |
| 2026-05-13 | −12.3% | 9.0m | AGM day; guide-down + buyback pause (per house ledger) |
| 2026-06-15 | −7.1% | 6.3m | 52-week low 220p set |
| **2026-07-08** | −7.1% | 8.8m | Trading update: **H1-26 loss ~£30m**; separate RNS 07:01 **Resignation of CFO** |
| 2026-08-03 | +8.0% | 4.6m | no RNS; sector +2.2% |
| **2026-08-04** | **−9.8%** | **13.8m** | **no RNS; every peer UP** |

Peak-to-trough 736.8p (11-Feb-26) → 220p (15-Jun-26) = **−70% in four months**. YTD −54.8%.

**Today is name-specific, not sector.** On 2026-08-04 the UK housebuilder cohort *rose* —
TW. +1.6%, BKG +1.5%, BWY +2.2%, PSN +1.1%, MSLH +4.5%, GLE +3.7%, CRST −0.2%, FTSE-250 +1.0% —
while VTY fell 9.8% on 2.4x volume with a 23% intraday range and **no regulatory announcement**.
Google-News RSS returns exactly one price-explaining item, an Investing.com piece at 10:02 GMT
("Why is Vistry stock plunging today?") whose body I could not retrieve, plus a Telegraph feature
published 05:45 GMT — pre-open — headlined *"How Labour's favourite housebuilder became a
'corporate disaster'."* Proximate trigger: **UNVERIFIABLE**. Character: idiosyncratic, and the
+8.0%/−9.8% round trip across two sessions is the signature of a heavily-shorted book being run
both ways, not of new fundamental information.

---

## 2. The 0.27 P/B — tested first, per addendum rule 1. It is NOT a unit artifact.

| Step | Check | Result |
|---|---|---|
| Price unit | IBKR + yfinance + LSE row all quote GBX; 290.2p = £2.902 | consistent |
| Share count | AR25 weighted average 326.9m; screen filing count 320.04m; yfinance 317.59m; LSE-implied 352.5m (11% divergence, flagged) | material but not 100x |
| Book value | AR25 five-year summary, **Net assets £3,324.6m** (2024: £3,235.9m) — verbatim | CONFIRMED |
| Arithmetic | £3,324.6m ÷ 320.04m = **£10.39 book/share** vs £2.90 price | **P/B 0.279 — REAL** |

So the screen's 0.27 survives. The artifact is not pence-vs-pounds and not the goodwill mix — it is
**temporal**. That £10.39 is a 31-December-2025 measurement, signed off 27-Feb-2026, by a CEO and a
CFO who have both since left, and it has not been re-measured through four subsequent negative
updates. Stripping goodwill (£827.6m) and other intangibles (£329.2m) gives tangible book
£2,167.8m = **£6.77/share, P/TB 0.43x**. The company's own (non-standard, net-debt-added-back)
TNAV of £2,312.0m gives £7.22/share, 0.40x.

Goodwill alone is **£2.59/share — 89% of the entire share price.**

---

## 3. Mode B, lead finding: the goodwill test is refuted by the company's own sensitivity table

Note 11 (AR25) discloses the value-in-use base case and, unusually helpfully, the **single-assumption
break-points** — the change in each variable that alone would take the £674m headroom to zero:

| Assumption | FY25 base case | Break-point (headroom → nil) | What has happened since |
|---|---|---|---|
| Volume growth | 9.1% CAGR to 2030; 2026 "expected to exceed" the 5–8% target | falls to 4.6% | 8-Jul: weak Registered-Provider/affordable-partner demand; completions already 15,658 (−9% y/y) |
| Adj. operating margin | 8.5% (2025) rising to 12.0% by 2030 | **stays flat at 8.5%** | 8-Jul: **H1-26 loss ~£30m**; "heavy discounting on unsold homes" |
| Operating cash conversion | >100% near term, 100% terminal | terminal falls to 76% | H1-26 average daily net debt ~£799m vs a Board target of *net cash* £100m by Dec-26 |
| Real pre-tax discount rate | 13.1% | rises to 15.3% | n/a |

The Directors wrote that **none** of these was "reasonably possible," and their "severe and unlikely"
*combined* scenario — which still capped margin at 9.8% — produced only a **£138m** impairment.
Reality four months later is worse than their severe case on the margin leg alone: an H1 loss is not
a 9.8% margin, it is a negative one.

**Finding: the £674m headroom is not credible as at 30-Jun-2026.** A goodwill impairment at the
24-September half-year is close to mechanical unless the new CEO re-forecasts *upward* into a
deteriorating market — which no incoming management does. The impairment trigger (market cap below
NAV) was already identified in the FY25 accounts with no impairment taken; market cap is now **28%**
of NAV, not merely below it.

This is the honesty read, and it is nuanced: **Vistry disclosed all of it.** The sensitivity table,
the trigger, the average-net-debt gap, the covenant stress — every number in this section is the
company's own. That is disclosure integrity, and it is why this is a REJECT on *fundamentals*
rather than an EXCLUDE on honesty. What diverges is not the data; it is the FY25 *narrative*
("signs of stabilisation in Q1 2026," net cash £100m by year-end) which was falsified within a week
of publication.

---

## 4. Net-debt seasonality — quantified, and it breaks the screen's cheapness

The brief asked whether housebuilders window-dress year-end. Vistry states it outright (AR25, CFO
review, verbatim): **"The Group's average daily net debt in 2025 was £733.7m (2024: £698.1m)"** —
against a reported year-end net debt of **£144.2m**.

The year-end figure understates the true average financing requirement by **£589.5m, a factor of
5.1x**, and the same gap existed in 2024 (£698.1m vs £180.7m, 3.9x). The 8-Jul-2026 update puts
H1-26 average daily net debt at **~£799m** — higher again.

Re-striking enterprise value on the honest denominator (live 290.2p, 320.04m shares, mcap £928.8m):

| EV basis | EV | EV / FY25 statutory EBIT £222.6m |
|---|---|---|
| Screen / year-end net debt £144.2m | £1,073m | 4.8x |
| + IFRS-16 leases £98.1m + building-safety provision £303.6m | £1,475m | 6.6x — *this is roughly the shelf's 6.1x* |
| **FY25 average daily net debt £733.7m** | £1,662m | **7.5x** |
| **+ leases + building safety** | £2,064m | **9.3x** |
| **H1-26 average daily net debt ~£799m + leases + building safety** | £2,129m | **9.6x** |

**The shelf's "6.1x EV/EBIT" is a year-end-optics number. On the company's own average net debt it
is 9.3–9.6x** — and that is against a 2025 EBIT that 2026 will not repeat. Same mechanism voids the
19% FCF yield: FCF struck on a balance sheet observed one day a year.

Capital allocation compounds it: in 2025 the Group paid out £71.2m buying back 11.5m shares (part of
a £130m special distribution, £101m completed) **while running £733.7m of average net debt**. The
residual £29m buyback was paused in May 2026 (house ledger).

---

## 5. Cladding provision — the shelf pointed at the wrong note (anti-masking finding)

The task asked me to test adequacy. Note 22 (AR25), verbatim reconstruction:

| | Building safety | Customer care | Completed sites | Other | Total |
|---|---|---|---|---|---|
| At 31-Dec-2024 | 324.4 | – | – | 28.8 | 353.2 |
| Additional provisions | 14.3 | – | – | – | 14.3 |
| — change in discount rate | 3.1 | – | – | – | 3.1 |
| Transferred from accruals | – | 22.1 | 36.5 | – | 58.6 |
| Utilised | (46.2) | – | – | (11.5) | (57.7) |
| Unwind of discounting | 8.0 | – | – | – | 8.0 |
| **At 31-Dec-2025** | **303.6** | 22.1 | 36.5 | 17.3 | **379.5** |
| of which non-current | 213.2 | 10.9 | 36.5 | 9.2 | **269.8** |

Buildings under remediation: 240 at 1-Jan-25, +11 identified, 21 completed → **230 at 31-Dec-25**.
Spend "phased relatively evenly across 2026, 2027 and 2028"; 2026 net cash spend guided to c.£70m.
Disclosed sensitivities: buildings +5% → +£15.2m; remediation spend +10% → +£25.2m; discount rate
±50bp → ±£2.2m.

**Adequacy verdict: BOUNDED, and maturing — this is not the problem.** The top-up cadence has
collapsed, not accelerated: income-statement building-safety net expense was **£114.7m in FY24 and
£8.0m in FY25**. Vistry front-loaded in FY24. The comparator I can verify from house primary work is
Taylor Wimpey, which front-loaded £225.8m in FY25. Peer-by-peer top-up comparison across Barratt
Redrow / Persimmon / Bellway / Berkeley is **UNVERIFIED** — I did not read their notes, and the
addendum's rule is that unverified is not clean. But on Vistry's own trajectory and disclosed
sensitivities, the plausible surprise is roughly ±£40m — **13 pence a share.** That is noise against
a stock that has lost 456p this year.

The £269.8m the screen flagged as a pension proxy is confirmed as the *non-current slice* of a
£379.5m provisions block, of which building safety is £213.2m. The screen's provision-kind
relabelling was right; its implicit conclusion that this is the trap was wrong. **Correcting where
the risk lives is the finding: it is in inventory NRV, not in the cladding note.**

---

## 6. Where the covenant actually breaks — inventory, not goodwill

Covenant package (Note 20, verbatim): the RCF, Term Loan and USPP "all include a covenant package,
covering **interest cover, gearing and tangible net worth** requirements, which are **tested
semi-annually**." Facilities: £1.0bn committed (£900m syndicate extended to **April 2028**, plus a
£100m USPP maturing **February 2027** which the going-concern assessment explicitly does not rely on
beyond that date) + £130m uncommitted = £1,130m.

Two consequences the market may be conflating:

1. **A goodwill impairment does not touch the covenant.** Goodwill is already excluded from tangible
   net worth. An £828m write-off is optically violent and covenant-neutral.
2. **An inventory write-down does.** Accounting policy (Note 18): *"Where the remaining life-of-site
   margin becomes negative, the full forecast loss is recognised immediately as an impairment of
   inventories."* With press-reported discounting of up to 17% on Open Market stock, sites tip
   margin-negative and the **whole remaining site loss lands at once**. FY25 inventory impairment
   was £14.7m (FY24: £61.2m) against gross inventories of £3,228.3m. Land £1,932.4m + WIP £1,295.9m.

And the going-concern severe-but-plausible downside, approved 27-Feb-2026, assumed:
*a further 3% price reduction on Open Market and unsecured Partner Funded sales from 1 July 2026;
a seven-week delay to new Partner Funded completions; a 5% cancellation rate; a 5% build-cost
increase from 1 September 2026* — under which "**the Group would exceed its committed borrowing
facilities and breach certain financial covenants**" absent mitigations.

**The discounting leg of that scenario has been overshot, on the company's own 8-July language, four
months after the Board approved it.** The mitigations (defer land, cut discretionary site spend,
bulk-sell stock, cut overhead, suspend distributions) are real and mostly within management control —
which is precisely why the buyback stopped in May. The next covenant test date is **30 June 2026**,
reported at the **24 September 2026** half-year results.

---

## 7. Conditioning — this is a crowded short, not a neglected value name

The brief's "17 analysts = no coverage edge" is right about the conclusion and wrong about the
reason. FCA short-position register (daily disclosure file, downloaded 2026-08-04, latest position
dates 8–9 July 2026), positions ≥0.5% still live on 2026 dates:

Schonfeld (UK) 2.44 · GLG 2.24 · Two Sigma 1.28 · Citadel Advisors 1.19 · BlackRock (UK) 0.99 ·
Arrowstreet 0.91 · CFM 0.90 · AHL 0.81 · Schonfeld LLC 0.73 · Tages 0.72 · Soundstone 0.68 ·
Lombardi 0.66 · Wellington 0.59 · Premier Miton 0.54 · Point72 (DIFC) 0.54 · AQR 0.51 ·
Tudor Europe 0.51 · Citadel Securities Europe 0.50 → **≈16.7% of shares in issue disclosed net
short**, plus a tail of sub-threshold 0.4x positions. True short interest is higher; 0.5% is only
the disclosure floor.

That is one of the most heavily shorted lines on the UK main market, held by informed,
balance-sheet-literate capital. And the 17 analysts do not form a consensus: yfinance target range
**160p – 625p** around a 305p mean — a 3.9x spread — with a "Reduce" consensus recommendation
(MarketBeat, 2-Aug-26). Several of those models are visibly unrevised: forward EPS is still carried
at 45.3p, *above* trailing 42.2p, for a company guiding to an H1 loss. The screen's "6.3x forward
P/E" is that stale number.

`discovery_state` read: **CROWDED**, with squeeze fuel. Squeeze fuel is a reason not to be short.
It is not a reason to be long.

---

## 8. De-rate vs derailment

**DERAILMENT, unambiguously.** The winner pattern (HUBS/CTSH/SAP) is a multiple compressing against
stable or rising estimates. Here the estimates are falling *ahead* of the multiple:

- FY25 delivered: adjusted PBT £268.8m, statutory PBT £196.2m, statutory EPS 42.2p, ROCE 13.9%,
  completions 15,658 (2024: 17,225; 2023: 16,118).
- FY26 guided (8-Jul-26, per house ledger): **adjusted PBT ~£200m**, i.e. −26% — with **H1 a £30m
  loss**, which implies ~£230m of adjusted PBT in H2 alone, a 115%-of-year second-half skew.
- Adjusted operating margin already fell to 8.5% in 2025 from a five-year average of 11.4%.
- Adjusted revenue £4,155.3m vs statutory £3,613.7m: £541.6m runs through JVs, so the consolidated
  EBIT the screen multiplies is not the whole business, and JV losses are a further unmodelled leg.

Management is fully replaced mid-derailment: CEO Greg Fitzgerald out at the March results, CFO out
8 July, chair/CEO roles split. **The book value in the denominator of the 0.27 P/B is the property of
people who no longer work there.** New management inheriting a broken forecast has every incentive
to mark it down once, in full, at their first reporting event. That event is 24 September.

---

## 9. Path check

+31.9% off a **50-day-old** 52-week low (220.0p, 15-Jun-26). The contract's own rule — "a +35% bounce
off a <90d low = late; say so" — puts this at the boundary, and today's −9.8% is the bounce failing.
This is mid-air, not a base.

---

## 10. Four-idea frame

- **The bull idea:** 0.43x tangible book, 17% short base, £39bn government Social and Affordable
  Housing Programme 2026-36 as a demand floor, £900m of committed bank money to April 2028, and a
  new CEO who resets the bar. If the H1 mark is the low, the squeeze is violent.
- **The bear idea:** the book is unmarked. Inventory NRV on 17%-discounted stock, recognised as
  full-life-of-site losses, hits tangible net worth — the covenant metric — at the 30-June test.
- **The idea nobody is pricing:** the £100m USPP matures February 2027 and the going-concern
  assessment already refuses to rely on it. A refinancing conversation with a syndicate of eight
  banks, held by a company that has warned four times and lost both its CEO and CFO, is where the
  equity holder finds out what the balance sheet is really worth.
- **The idea that would change my mind:** a September print showing average H2 net debt *falling*
  toward the £100m net-cash target with the goodwill impairment already taken and covenants
  reaffirmed. That is a knowable, dated fact 51 days out. It is not a reason to pre-position.

---

## 11. Scenarios (fundamental, 12-month, from live 290.2p)

| | p | FV | Reasoning |
|---|---|---|---|
| Bear | 0.40 | 120p | Full goodwill write-off + £150-250m inventory impairment; covenant waiver or an equity raise into a 17%-short book; management's own June "no plans for a rights issue" denial does not survive contact |
| Base | 0.45 | 260p | Kitchen-sink H1: goodwill impaired, inventory marked, FY26 adj PBT re-based to £120-160m; covenants held with mitigations; stock re-rates on the *cleared* book but off a lower base |
| Bull | 0.15 | 480p | Affordable-programme volume lands, Open Market stabilises, no impairment needed, average net debt inflects; short base capitulates |

E[FV] ≈ 0.40×120 + 0.45×260 + 0.15×480 = **237p**. Live 290.2p ⇒ **edge −18%**.

Market-implied p(bull) solving 290.2 = p·480 + (1−p)·(weighted bear/base) is above our 0.15 — i.e.
**the market is already paying for a better outcome than we underwrite.** Cheapness on a stale
denominator is not edge.

---

## 12. Catalyst map (probability × timing × magnitude)

| Catalyst | Date | p | Magnitude | Leading indicator |
|---|---|---|---|---|
| **H1-26 results** — first mark by new management | **2026-09-24** (verified: company financial calendar) | 1.00 | ±25-40% | Any pre-close RNS; further TR-1 short disclosures |
| Goodwill impairment ≥£300m at H1 | 2026-09-24 | 0.60 | non-cash, covenant-neutral, sentiment-negative | Auditor KAM language |
| Exceptional inventory impairment ≥£100m | 2026-09-24 | 0.55 | hits tangible net worth = covenant metric | Reported incentive/discount levels |
| Covenant waiver / amendment disclosed | 2026-09-24 | 0.25 | −20%+ | RCF amendment RNS |
| Equity raise announced by 2027-06-30 | H1-27 | 0.25 | −30%+ | Denied 23-Jun-26 by an executive; denials are not evidence |
| FY26 adj PBT guidance cut below £200m | 2026-09-24 or 2026-11-05 | 0.55 | −10-20% | H1 completions/reservation rate |
| Trading update | 2026-11-05 (verified) | 1.00 | ±10% | — |
| USPP refinancing outcome | by 2027-02 | — | tail | — |

**Print proximity:** 51 days to the 24-Sept H1 results — outside the contract's ~2-week no-blind-entry
window, so the block on entry here is fundamental, not timing.

---

## 13. Verification notes (claim → method → authority → finding)

| # | Claim | Method | Authority | Finding |
|---|---|---|---|---|
| 1 | P/B 0.27 | recompute from live px × share count vs reported equity | AR25 five-year summary "Net assets 3,324.6" | **CONFIRMED** — real, not a unit artifact |
| 2 | Price unit GBX | IBKR live 290.2 vs yfinance 284 close vs LSE row 284 | IBKR conid 26652747 | CONFIRMED, no 100x error |
| 3 | £269.8m is cladding, not pension | read Note 22 in full | AR25 Note 22 | **CONFIRMED** — non-current slice; total building safety £303.6m; 230 buildings |
| 4 | Cladding provision bounded | disclosed sensitivity table + top-up trajectory | AR25 Note 22; FY24 vs FY25 income-statement expense £114.7m → £8.0m | **CONFIRMED bounded** (±~£40m); peer top-up comparison **UNVERIFIED** |
| 5 | Goodwill £827.6m, 25% of equity, impairment trigger identified, none taken | read Note 11 | AR25 Note 11 | **CONFIRMED**; headroom £674m; break-points disclosed |
| 6 | Goodwill headroom still valid at H1-26 | compare disclosed break-points to 8-Jul-26 guidance | AR25 Note 11 vs 8-Jul-26 RNS | **REFUTED** — margin-flat break-point breached by an H1 loss |
| 7 | Net-debt window dressing | read CFO review | AR25: "average daily net debt in 2025 was £733.7m (2024: £698.1m)" vs year-end £144.2m | **CONFIRMED**, 5.1x gap, repeated |
| 8 | Screen EV/EBIT 6.1x | re-strike EV on average net debt + leases + provision | computed | **REFUTED** — 9.3-9.6x on the honest denominator |
| 9 | Covenant structure | read Note 20 | AR25 Note 20: interest cover, gearing, tangible net worth; semi-annual | CONFIRMED |
| 10 | FY25 severe-downside breaches covenants | read going-concern note | AR25 going concern | **CONFIRMED** — "would exceed its committed borrowing facilities and breach certain financial covenants" |
| 11 | H1-26 loss ~£30m, FY26 adj PBT ~£200m, avg net debt £799m | RNS 8-Jul-26 | company RNS via press + house research ledger | CONFIRMED (secondary + ledger; **primary RNS text not retrieved** — see gaps) |
| 12 | 17 analysts, "covered so not neglected" | pull target dispersion + short register | yfinance; FCA short register | **CONFIRMED but re-characterised** — 160-625p spread, stale forward EPS, ~16.7% disclosed short |
| 13 | Next print date | company financial calendar | vistry.co.uk/investors/financial-calendar | **CONFIRMED 24 September 2026**; trading update 5 November 2026 |
| 14 | 2026-08-04 −9.8% is name-specific | peer + index bars for the same session | yfinance TW./BKG/BWY/PSN/CRST/MSLH/GLE, ^FTMC | **CONFIRMED name-specific** (all peers up, FTSE-250 +1.0%) |
| 15 | Executability | IBKR contract resolve + live quote | conid 26652747, LSE, STK+CFD, 90d avg USD volume $7.64m | CONFIRMED — sizing is not the constraint |
| 16 | Offer period / tender | ISIN join vs Takeover Panel table | LSE_OFFER_PERIODS.json (39 live, ISIN-exact) | Not in an offer period |

**UNVERIFIED / gaps (not clean):**
- The precise trigger of the 2026-08-04 −9.8% and the 2026-08-03 +8.0%. No RNS on either date. The
  Investing.com body and the Telegraph feature were both unfetchable (paywall / host block).
- The **primary text** of the 8-Jul-2026 trading update. The £30m H1 loss, ~£200m FY26 adj PBT and
  £799m average net debt come from press descriptions plus our own research ledger, not from the RNS
  itself. They are internally consistent with the AR25 base case and I treat them as reliable, but
  they are **not** primary-verified in this court.
- The 2026-03-19 −7.8% has no identified cause.
- Peer cladding top-ups (Barratt Redrow, Persimmon, Bellway, Berkeley) for the adequacy benchmark.
- H1-26 balance sheet: no post-Dec-2025 equity, inventory or goodwill figure exists anywhere. Every
  ratio in this court rests on a 7-month-old book. That is the whole point of the verdict.
- **Data-integrity note:** vistry.co.uk's own investor-page share-price widget renders "37.10 GBp",
  which reconciles to nothing (IBKR 290.2, yfinance 284, LSE row 284, book £10.39/share). Treated as
  a broken widget, not a corporate action — but flagged so nobody joins on it.

---

## 14. Kill triggers / re-open conditions

This is a REJECT, so these are **re-open** conditions rather than exit kills. Re-court VTY only if
**all four** land:

1. H1-26 results (24-Sep-26) published **with** the goodwill impairment taken and inventory marked —
   the mark must be *in the past*, not pending.
2. Covenant compliance at the 30-Jun-26 test **explicitly reaffirmed**, with headroom quantified.
3. Average daily net debt for H2-26 disclosed and **falling** versus £799m.
4. No equity raise announced, and the balance sheet demonstrably capable of reaching Feb-2027 USPP
   maturity without one.

Automatic permanent kill: any rights issue, covenant waiver, or facility reduction.

---

## 15. Freezable call

**`VTY | 2026-09-24 | Vistry's H1-2026 results report a statutory pre-tax LOSS of £100m or worse
(i.e. materially worse than the ~£30m loss guided on 8-Jul-26), driven by exceptional goodwill
and/or inventory impairment | our_p = 0.60`**

Resolves on the H1 RNS. The market-implied read from a 290p price and a stale 45p forward EPS is
that this does not happen; we think it is the modal outcome.

---

## 16. Ruling

**REJECT 2/10.** Not a de-rate — a derailment with the balance-sheet leg still unmeasured. The 0.27
P/B is arithmetically real and analytically empty: it divides today's price by a book that the
company's own disclosed sensitivities say is about to be reduced, marked by a management team that
did not build it, 51 days from now. The screen's 6.1x EV/EBIT and 19% FCF yield are both artefacts of
a year-end balance sheet the company itself tells you it does not run — £733.7m average against
£144.2m reported. The one thing the shelf flagged as the trap, the cladding provision, is the
cleanest item in the accounts.

No band. No tranche. UK cap of 0.75% is irrelevant — size is zero.

**RED TEAM REQUIRED: No** (score < 6).
