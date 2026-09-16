## Context

Cause-check first, per the mandate. **The dislocation is not a Vicor event.** No 8-K since the 7/21 Q2 print; the 5d window (8/18–8/24) contains only Form 4/144 insider paperwork. The cohort narrative is the mid-August AI-infrastructure de-rate — chip stocks fell >20% off June highs on hyperscaler-capex-digestion fear, with VRT −6.9% (8/18), CLS −13.7% (dilution), CRDO −30% YTD. VICR's −13.0% on 8/19 was pinned by the wires on "insider selling," and that attribution is false: the only documented sale is a director's **908 shares / $227,000**. A $227K sale did not move a $9.2B company 13%. The move is positioning, not news.

⚠️ Two disclosure limits up front: I could not read `knowledge_graph/cohorts.json` (outside the permitted directory), so the COHORT/NARRATIVE slots stayed `?` and I reconstructed the narrative from the tape and dated news — flag if the registry says otherwise. And SEC.gov 403s WebFetch with no header control (Bash disabled), so financials below are from the **issuer's own 7/21 release** and the Q2 call, not from the 10-Q text. The evidence pack's XBRL block is broken, not empty-of-news: `rev` blank, `sbc` newest 2013, `dil_sh` newest 2025-03-31. That is an extractor failure worth a ticket.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| VICR | **DAMAGE-ABSENT** | One-year backlog + book-to-bill (the metric capex-digestion must hit first) | $379.7M at 6/30/26, **+26% q/q, +145% y/y**; Q2 book-to-bill >1; lead times "stretched out… demand exceeding capacity" ([issuer release, 7/21/26](https://vicorcorporation.gcs-web.com/news-releases/news-release-details/vicor-corporation-reports-results-second-quarter-ended-june-15)) | 2026-10-20 (unconfirmed) | Constraint is **supply, not demand**: fab "approaching full capacity utilization," $2.5B target needs a second fab. Backlog ≈2.9x the Q2 product quarter — digestion must chew through that buffer before it reaches revenue. |

## The decisive reconstruction (royalty-stripped product bridge)

This is the number that separates a real read from the tape's read, and it's fully derivable from pre-print disclosure:

Q2's $143.4M includes **$15M of licensing royalty** recognized on a GAAP termination-clause quirk; Q3 carries only **$5M** under the same $60M/2-year deal. So the "+10% sequential" guide decomposes as:

- Total: $143.4M → ~$157.7M
- Royalty: $15M → $5M
- **Product: $128.4M → ~$152.7M = +19% sequential**

The guide understates the franchise. A cohort selling VICR for capex digestion is looking at a headline that is *masked downward* by a royalty step-down, while underlying product revenue accelerates. Conversely — and this cuts the other way — Q2's 34.7% net margin is *flattered* by that same ~100%-margin $15M; my estimate of ex-royalty product gross margin is ~53% vs the reported 58.0%. Both distortions are the same artifact, and both are checkable on 10/20.

## COURT-WORTHY (damage-absent, ranked):

**1. VICR** — Backlog +145% y/y against a −49% drawdown from the $382.65 high is the widest dispersion-vs-narrative in the event, and the two things that could actually kill it are *unresolved by any public metric*, which is precisely what makes a court worth running rather than a screen.

What a court has to adjudicate — and note that **neither vector is refuted by the backlog**:

- **Customer concentration.** An analyst put Cerebras at 25–30% of the business on the Q2 call; management explicitly declined to confirm or deny. Backlog quality is not backlog quantity — $379.7M concentrated in one private, single-purpose AI-chip customer is a categorically different asset than diversified backlog, and it is the one input that would flip this toward STRUCTURAL.
- **800VDC, and a dated information gap.** NVIDIA moved 800VDC to production on **8/11/26** with Google/Microsoft via OCP, Delta named as a supplier. The Q2 call was **7/21/26** — management has never been asked about it on the record. Bear read: rack power migrates to a spec Vicor didn't co-author. Bull read: 800V→48V→sub-1V still needs the last 1.5mm, which is exactly VPD (3 A/mm², vs competition "barely above 1"). Unresolvable until 10/20.

The honest tension, stated plainly: **damage-absent is not the same as cheap.** At $194.83 / ~$9.25B on FY26 revenue ">$600M," this is ~15x sales, ~14.6x EV/sales net of $453.6M cash. The de-rate from $382.65 may be nothing more than the removal of an unsupportable multiple, which the backlog does not and cannot refute. Under the response taxonomy that is a **price gate, not a kill** — it argues for a band well below spot, not for FLAT.

**PRINT PROXIMITY: 2026-10-20 — NOT within 5 trading days (~39 sessions out). yfinance-derived and UNCONFIRMED; no company PR names it. Cadence-consistent (Q2 filed 7/21, a Tuesday; 10/20 is a Tuesday), but treat as unverified.** The print-decisive reconstruction is therefore not mandatory here — I ran it above regardless, since it is the test that resolves the cohort's claim. No pre-print position section required; for the record, book is flat with no resting orders, and the price gate — not the thesis — is what a court needs to set.

**COURT-WORTHINESS VICR: 7/10 — damage-absent is well-evidenced, but concentration and 800VDC are live and unpriced, and with a flat book the court moves sizing from zero to a banded starter.**

One item back to the work queue: I could not size the 8/3–8/24 insider cluster (144s + four Form 4s) from primary — SEC blocks this session's fetch path. The $227K figure is one director from a secondary wire, not the cluster. Worth resolving before any court sets a band, since a large founder distribution at ~$250 is a supply overhang that would legitimately lower the entry rung.

Sources: [Vicor Q2 2026 issuer release](https://vicorcorporation.gcs-web.com/news-releases/news-release-details/vicor-corporation-reports-results-second-quarter-ended-june-15) · [Q2 2026 earnings call transcript](https://www.fool.com/earnings/call-transcripts/2026/07/21/vicor-vicr-q2-2026-earnings-call-transcript/) · [GlobeNewswire release](https://www.globenewswire.com/news-release/2026/07/21/3330291/0/en/Vicor-Corporation-Reports-Results-for-the-Second-Quarter-Ended-June-30-2026.html) · [NVIDIA 800VDC to production](https://www.storagereview.com/news/nvidia-moves-800-vdc-power-architecture-from-concept-to-production-just-dont-turn-off-ac-power-yet) · [MarketBeat insider-selling attribution](https://www.marketbeat.com/instant-alerts/vicor-nasdaqvicr-stock-price-down-81-after-insider-selling-2026-08-19/) · [Vertiv 8/18 move](https://www.tradingkey.com/news/market-movers/262116040-market-movers-vrt-20260818) · [Celestica dilution selloff](https://ca.investing.com/news/stock-market-news/why-is-celestica-stock-sliding-today-93CH-4782710)