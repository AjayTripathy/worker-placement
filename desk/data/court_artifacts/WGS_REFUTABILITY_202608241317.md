## Cause-check (run first, and it reframes the event)

The event fired on `dd52 -0.538 / excess_dd -0.312`, but the drawdown is **not** cohort-narrative selling. It is a **single-name guidance blowup, already re-priced upward**, measured against a stale high:

- **$170.87 52w high was set ~late Oct/Nov 2025**, after a Q3'25 beat (Guggenheim lifted its PT to $170 on 2025-10-29).
- **2026-05-05: −$33.42 (−49%) in one day** on the Q1'26 print — FY26 revenue guide cut ~12%, E+G growth guide cut from "33–35%" to "at least 20%", $31.287M Fabric Genomics impairment. Idiosyncratic, not sector.
- **The stock has fully round-tripped that damage.** Pre-crash 5/4 close ≈ $68.20; **today $87.07 = +28% above the pre-crash level and +170% off the $32.21 low.** `hi26w` $94.51 is only 8% overhead.
- Post-Q2 tape is a melt-up, not a dislocation: 7/28 $61.88 → 8/3 $67.86 → 8/10 $77.88 → 8/21 **$87.07 (+41% in 17 sessions)**.

So the cohort premise is an **arithmetic artifact of a 10-month-old high**, not indiscriminate selling. There is no same-event external anchor, so there is no dispersion trade to harvest here.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| WGS | **DAMAGE-ARRIVING** (damage real, peaking; magnitude unresolved) | Outpatient **genome collection rate**, and its upstream driver **% of outpatient genome volume under an active positive coverage policy**; summary metric = blended ARR $/test | Collection rate **32%**, flat Q1→Q2, **down from 43% YoY**; blended **ARR $3,258/test, flat QoQ**, guided ~$3,300 Q3; but coverage inverted — commercial genome coverage **87% vs 47% in Q1** (Carelon, 56M lives), volume-under-positive-policy **67% vs 46%**; Q2 rev $114.4M, E+G $100.3M on 30,785 tests (+32% vol), 70% adj GM, adj NI +$0.4M, GAAP −$17.7M, FY26 guide **reaffirmed** $475–490M — [ir.genedx.com Q2 2026 release, 2026-08-03](https://ir.genedx.com/news-releases/news-release-details/genedx-reports-second-quarter-2026-financial-results) | **2026-10-27 — yfinance-derived, UNCONFIRMED** (no company PR names it) | Not DAMAGE-ABSENT: compression is in the printed numbers. Not STRUCTURAL: coverage policy demonstrably reversed and volume compounds +32%. Mgmt pre-registers the test — collections "roughly flat" in Q3, "meaningful improvement" **starting Q4 2026**, main uplift 2027 |

**COURT-WORTHY (damage-absent, ranked):**
**NONE.** WGS does not qualify — the narrative's predicted damage *is* present in the current print (collection rate 43%→32% YoY, ARR down YoY). Promoting it here would be grading the name's attractiveness rather than its refutability.

**COURT-WORTHINESS WGS: 3/10** — a court confirms FLAT rather than changing sizing: the cohort premise is a stale-high artifact, and the standalone long is 43% above an informed anchor into a metric that has not yet inflected.

**PRINT PROXIMITY: 2026-10-27 — yfinance-derived, UNCONFIRMED; no company PR names it. NOT within 5 trading days (~44 sessions out); Q2 already printed 2026-08-03.** No pre-print reconstruction owed.

### The named kill (doctrine requires one for FLAT)

**Blackstone paid $61.00/share on 2026-08-03** for 81,967 Class A shares alongside expanding its own term loan to $150M aggregate. The 7/28 close was $61.88 — **struck at market by the most information-advantaged non-insider on the register**, a creditor with full diligence access, days before the print. We would be paying **$87.07, +43% over that mark**, for a collection rate management itself says stays flat through Q3. That is paying a full inflection price for an un-inflected metric.

Reinforcing, not load-bearing: `discovery_state` is **CROWDED**, not degraded (+41% in 17 sessions, heavy sell-side, Blackstone in) — the divergence gate fails. And the securities class action plus the $31.3M Fabric write-off put this under the integrity-overhang gate, so it can never be RP_FAIR and is capped at 0.85×E[fv] regardless of court outcome. All four vectors point the same way, which is why a court has low information value.

**What would re-open it:** a Q4 collection-rate print showing actual conversion (32% → 40%+) *together with* a pullback toward the $61–68 zone. That is a tripwire on the Q3/Q4 prints, not a court docket item.

### Two pipeline bugs worth fixing (they will misroute again)

1. **Cohort industry tag is wrong.** WGS is tagged `Medical/Nursing Services`; GeneDx is a clinical genomics laboratory. Whatever narrative `cohorts.json` encodes for that industry almost certainly does not apply, which is a second, independent reason this event should not have fired. I could not verify the narrative text directly — `cohorts.json` was not found and repo reads under `signalos/` were permission-denied, so `COHORT` and `NARRATIVE` stayed `?`.
2. **Evidence-pack XBRL block is ~a year stale.** It instructs "use THESE for SBC/share/OCF math," but `rev` ends 2025-06-30 and `sbc`/`ocf` end 2025-03-31 while the pack quotes the Q2 **2026** 10-Q. Any margin or per-share math off that block would be a year off. (Minor: pack tape `dd52 -0.49` vs event context `-0.538`.)

Also note: IBKR was not authorized in this non-interactive session, so the tape above is pack/Yahoo + stockanalysis.com rather than a live IBKR spot — contrary to the usual live-price rule. The claims here are drawdown-shape and anchor-relative, which tolerate a T-1 close, but re-pull before any sizing.

Sources:
- [GeneDx Q2 2026 results (primary IR release, 2026-08-03)](https://ir.genedx.com/news-releases/news-release-details/genedx-reports-second-quarter-2026-financial-results)
- [GeneDx Q2 2026 earnings call transcript](https://www.fool.com/earnings/call-transcripts/2026/08/10/genedx-wgs-q2-2026-earnings-call-transcript/)
- [WGS overview / 52w range](https://stockanalysis.com/stocks/wgs/) · [WGS daily price history](https://stockanalysis.com/stocks/wgs/history/)
- [Hagens Berman — 49% drop, Fabric Genomics write-off class action](https://www.prnewswire.com/news-releases/genedx-holdings-wgs-faces-securities-class-action-after-49-drop-94-write-off-related-to-fabric-genomics-acquisition--hbss-302810311.html)
- [Guggenheim $170 PT after Q3'25 beat](https://finance.yahoo.com/news/guggenheim-reaffirmed-buy-genedx-october-044221752.html)
- [Q2 2026 8-K / Blackstone facility and private placement](https://www.stocktitan.net/sec-filings/WGS/8-k-gene-dx-holdings-corp-reports-material-event-3e975983564d.html)