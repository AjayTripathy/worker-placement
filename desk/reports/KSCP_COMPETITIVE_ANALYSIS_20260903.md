# Knightscope (KSCP) — Competitive Analysis for Houmanoids

**2026-09-03 · Prepared from public SEC filings only (10-Ks FY2021–2025, 10-Qs and 8-Ks through
Aug 2026), every figure traced to an accession number. Shared as diligence output: this is the
public record of the pure-play comp your memo argues against, independently recomputed. It
contains no investment recommendation about either company.**

## 1. Your chart's Knightscope number is exactly right

We recomputed the service-cost series from the audited segment tables (income-statement R4
exhibits, five consecutive 10-Ks):

| FY | Service revenue | Service cost | Cost per $1 of service revenue |
|---|---|---|---|
| 2021 | $3.41M | $5.46M | **$1.60** |
| 2022 | $5.16M | $8.80M | **$1.71** |
| 2023 | $7.17M | $9.87M | **$1.38** |
| 2024 | $7.47M | $11.63M | **$1.56** |
| 2025 | $7.97M | $12.32M | **$1.55** |

Your memo's 138%–171% range is confirmed to the dollar — the min and max land on the right years,
with no definitional games. (One footnote: FY2021 had no service/product split as filed; the
ratio derives from the FY2022 comparative column, and is 160% either way.)

## 2. One correction you'll want before showing this chart to anyone else

The United Rentals comparator of ~7.9% is not reproducible from URI's audited statements. URI's
FY2025 10-K (acc. 0001067701-26-000007) discloses total cost of revenues of $9,955M on revenues
of $16,099M — **~62 cents per revenue dollar** (URI itself reports 38.2% gross margin), and the
service-line and rental-line ratios land in the same place. We could not construct 7.9% from any
line item. The honest chart is **$1.55 vs $0.62 — a ~2.5x gap, not ~20x**. The argument survives
the correction (URI has 60 years of route density and still spends 62 cents; Knightscope spends
$1.55 and loses money on every deployed dollar), and a sophisticated investor who recomputes the
benchmark — as we did — will trust the whole exhibit more with the corrected number on it.

## 3. Why Knightscope's ratio never improved — decomposed from their own filings

Four years of scaling moved the ratio 160% → 171% → 138% → 156% → 155%. The composition (FY2025
10-K accounting policy + MD&A cost bridge) explains why:

- **Machine capital is not the problem.** Finished-robot depreciation is under $2.0M of the
  $12.3M service cost; connectivity is smaller and declining. The two costs people assume dominate
  robots-as-a-service are ~20% of the total.
- **Outsourced field service dominates.** Knightscope has always used third-party field-service
  firms (originally Konica Minolta) — every service event is a vendor truck roll at the vendor's
  margin, a per-incident cost with no density curve. Their FY2025 cost bridge: +$0.4M outsourced
  field service, +$0.4M headcount, against only −$0.2M connectivity savings.
- **Reliability failures land in service cost.** A $1.1M write-off discontinuing the K5v3 after
  field quality issues — with the entire affected fleet swapped "at no cost to our clients" —
  plus $0.9M of obsolescence in FY2025: ~7% of service cost is paying for hardware that didn't
  hold up. In RaaS the vendor eats every reliability failure.
- **Density never arrived.** Service revenue grew +6.6% in FY2024 and +6.6% in FY2025; robot
  backlog stands at $0.7M. The book stopped compounding before route density could form.

Read across: roughly two-thirds of the 155% is Knightscope-specific execution (outsourced service
at a markup, hardware that required a free fleet swap, sub-scale dispersion), one-third is
category physics. That is genuinely good news for a new entrant with in-house regional service
and better MTBF — but the honest mature-state floor for physical fleet-as-a-service looks like
URI's 50–70 cents, not single digits. A model below ~40 cents is an extraordinary claim that
should come with per-unit maintenance actuals attached.

## 4. The 2026 "turnaround" is worth understanding precisely

Knightscope's Q2-2026 print was headlined as revenue tripling with the first positive gross
margin in company history. The 10-Q's own footnotes (acc. 0001104659-26-094859, business-
combination and disaggregation notes) decompose it:

- In February 2026 Knightscope acquired **Event Risk LLC — a manned guarding business** (~90 →
  400+ employees). It contributed $9.2M of revenue and $2.0M of gross margin (21.7%) in four months.
- **Autonomous Security Robots revenue fell 19.3%** year-over-year in H1 ($2.33M → $1.88M), and
  the legacy business ex-acquisition still ran a **negative gross margin (−15%)**.
- On a like-for-like pro-forma perimeter, combined growth was +12.3% and the combined net loss
  *widened* 68%.

The decade-scale lesson for your category: the public pure-play never got the autonomous unit to
gross-margin positive, and its eventual answer was to buy humans at 21.7% margin. The robot
economics were not fixed; they were reweighted.

## 5. The compliance lane is genuinely unoccupied

Knightscope's FY2022 10-K used "Made in the USA" three times. The FY2025 10-K uses it zero times,
stating instead that products are assembled in Sunnyvale "using components sourced from a network
of domestic and international suppliers," with new tariff and single-source-supplier risk factors.
No Knightscope SEC filing has ever asserted §889 compliance. A competitor that documents
affidavit-grade §889 component sourcing would hold a differentiator the incumbent has never had
on the record — which is also why we've pressed on the BOM questions in our diligence list: the
lane is real, but only the documented version of it is worth anything.

## 6. A disclosure note, offered as advice

Across five annual reports Knightscope never disclosed deployed-unit counts, ARR, net revenue
retention, or contract counts ("nearly 10,000 machines-in-network" is dominated by static
call-boxes). The absence did them no favors — it reads as a choice, and it forced every serious
reader to reconstruct the business from cost ratios, which is exactly how the picture above
emerged. Publishing honest per-unit service actuals early, even when they're ugly, is how a
RaaS company keeps the benefit of the doubt.

---

*Sources: KSCP 10-Ks acc. 0001410578-22-000800 / 0001410578-23-000578 / 0001410578-24-000417 /
0001558370-25-004171 / 0001104659-26-036240; Q1/Q2-2026 10-Qs acc. 0001104659-26-062505 /
0001104659-26-094859; Event Risk 8-K/A acc. 0001104659-26-062519; URI FY2025 10-K acc.
0001067701-26-000007. All series recomputed independently from XBRL and exhibit tables; the two
decisive exhibits (acquiree-contribution and revenue-disaggregation notes) were verified twice.*
