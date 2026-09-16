## Two blockers to disclose before the triage

- `knowledge_graph/cohorts.json` — **read denied** (permission, non-interactive session). I could not load the cohort's canonical narrative string, so I triaged against the narrative the event blob implies and state it explicitly below. If the stored narrative differs, re-run.
- **IBKR — permission denied**, so no live tape/position poll (violates my standing "live prices from IBKR" rule; disclosing rather than silently substituting). Tape and book below are the pack's yahoo/`BOOK` values, not broker-verified.

One line of context: GOGO's Q2 print **already landed 2026-08-06** (10-Q + 8-K in the pack) and *is* the −19% day that put the pack's $3.635 print on the tape — so this triage is post-print, not pre-print, and the narrative on trial ("Starlink/LEO obsoletes Gogo's air-to-ground franchise") is no longer a fear but a **named, realized displacement**: NetJets moved 600+ jets to Starlink.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| GOGO | **DAMAGE-ARRIVING** | Business-aviation **service** revenue (QoQ), cross-checked against total broadband AOL net adds (ATG+GEO+Galileo) | BA service rev **$151.3M, −8% YoY / −2% QoQ**; ATG AOL **5,731, −15% YoY / −6% QoQ**; GEO AOL 1,306 (flat); Galileo AOL 184 (+66% QoQ); Mil/Gov **$39.9M, +40% YoY**; total rev −1% YoY ([Q2 PR, 2026-08-06](https://www.globenewswire.com/news-release/2026/08/06/3340082/0/en/gogo-announces-second-quarter-results.html)) | **~2026-11-05** (Q3) — yfinance-derived, **UNCONFIRMED**; company has not PR'd a date | Damage is unambiguously present and *named* (NetJets→Starlink, ~1,200 FY26 net ATG deacts, Classic ATG shutoff 2026-05-01). Unresolved is **magnitude**: revenue fell 1/15th as fast as units, and half the EBITDA guide cut is legal fees, not operations. |

**PRINT PROXIMITY: NONE within 5 trading days — next print ~2026-11-05 (~62 trading days out), yfinance-derived and UNCONFIRMED by any company PR. The decisive print for this name ALREADY OCCURRED 2026-08-06 (10-Q 0001193125-26-337921 + 8-K …337916), verified against the pack's filing list and the company's own release.** No pre-print reconstruction is mandated; the guide-to-guide reconstruction below is post-print instead.

### Why this is not DAMAGE-ABSENT, and not (yet) STRUCTURAL

The narrative is **confirmed on units and refuted on cash — so far**. That split is the whole finding:

**Confirmed:** NetJets contracted 600+ jets to Starlink after a 2024 commitment to Gogo AVANCE L5, with delivery targeted through end-2026 ([AeroTime](https://www.aerotime.aero/articles/netjets-starlink-fleet-connectivity)). Classic ATG service terminates 2026-05-01, affecting ~2,000 aircraft — a self-inflicted forced migration that hands Starlink an open door. Guided FY26 net ATG deactivations ~1,200.

**Not yet confirmed:** guide-to-guide math from the reaffirmed May-7 guidance ([Q1 PR](https://www.globenewswire.com/news-release/2026/05/07/3289794/0/en/Gogo-Announces-First-Quarter-Results.html)) to Aug-6:

| line | prior (mid) | new (mid) | Δ | of which non-operating |
|---|---|---|---|---|
| Revenue | $925M | $882.5M | −$42.5M (−4.6%) | — |
| Adj EBITDA | $208M | $180M | −$28M (−13.5%) | litigation expense $8M→$22M = **−$14M, i.e. half the cut** |
| FCF | $100M | $75M | −$25M | strategic investments $3M→$30M = **−$27M** |

Back out the strategic-investment step-up and **guided FCF is flat-to-up** (~$103M → ~$105M) despite a $42.5M revenue cut and $14M more legal spend. The market marked the equity −19% on headline cuts whose non-operating share is ~100% of the FCF cut and ~50% of the EBITDA cut.

**The load-bearing ambiguity a court must kill:** the prior EBITDA guide explicitly bracketed *both* $3M strategic investments and $8M litigation; the new guide names only the $22M litigation. If the $30M of strategic investments also sits inside the new EBITDA range, then operational EBITDA guidance **rose** ~$13M; if it does not, operations fell ~$14M. That is a ~$27M swing on a $180M EBITDA base, and it is resolvable from primary documents I could not fetch here (sec.gov 403'd WebFetch on every attempt; no shell available). The 10-Q is at [`gogo-20260630.htm`](https://www.sec.gov/Archives/edgar/data/0001537054/000119312526337921/gogo-20260630.htm) — **I did not read it**; the HPS balance of $221.9M at 2026-06-30 and the April 30, 2028 maturity below are search-surfaced from that document, not directly verified by me.

**The structural tail the bulls under-weight:** the SmartSky verdict (2025-11-21, Delaware) was **willful** infringement on 7 claims across 4 patents, $22.7M past damages, with SmartSky seeking **enhanced damages and an ongoing royalty on patents expiring 2033 and 2035** ([PR Newswire](https://www.prnewswire.com/news-releases/smartsky-wins-patent-infringement-lawsuit-versus-gogo-on-all-claims-302625784.html)). The royalty attaches to **Gogo 5G** — the exact product now ramping (138 units sold in Q2 vs 52 in Q1). A perpetual royalty on the growth SKU is a different animal from a one-time $22.7M charge, and it is not in any published model I can see.

**Capital structure — why this is a stub, not a cheap stock:** $814.1M long-term debt vs $492M market cap; cash **$63.1M**, down from $103.5M after a $40M Satcom Direct earn-out and $21.1M excess-cash-flow paydown; net leverage **3.8x** vs a 2.5–3.5x target; both the 2021 and HPS term loans mature **2028-04-30**. EV ≈ $1.25B → ~6.9x guided EBITDA; equity FCF yield 15% on headline guidance, ~21% ex-strategic-investments. Cheap *if* the FCF is equityholders'; a 2028 refinancing of a shrinking-ATG credit says it may not be.

**Data-quality flag on the event itself:** the blob tags GOGO **Consumer Discretionary**, and the −0.528 excess drawdown is measured against a Consumer Discretionary sector median. GOGO is aviation connectivity/telecom services. The "excess" figure that triggered this triage is computed against the wrong comparison set and should not be treated as a dispersion signal on its own.

**COURT-WORTHY (damage-absent, ranked):**
None. GOGO does **not** qualify as damage-absent — the predicted damage is in the units, named to a specific defecting customer, and guided forward. It nonetheless clears the court bar on a *different* axis: the dispersion between a −15% unit decline and a −1% revenue decline, combined with a guidance cut that is majority non-operating, is exactly the kind of gap a court resolves and the tape has not priced separately from the extinction story.

**COURT-WORTHINESS GOGO: 7/10** — a court swings sizing from zero to a capped starter because two decisive, primary-document-resolvable questions (does the $30M strategic-investment line sit inside the new EBITDA guide, and does SmartSky's willfulness convert into a perpetual 5G royalty ahead of a 2028 maturity wall) separate a 21% ex-SI FCF-yield stub from a lender-captured melting asset.

Routing note: ≥6 → this auto-escalates to a full red/blue court. Three things the court must pull that I could not: the 10-Q cash-flow statement and litigation-contingency footnote (sec.gov 403s WebFetch, no shell in this session), the post-trial motion docket in D. Del. for enhanced damages/ongoing royalty, and the credit-agreement leverage covenant with headroom at 3.8x.

**Book:** pack reports NO POSITION / NO ORDERS — **not broker-verified** (IBKR permission denied). No sizing action taken and none recommended before the court reports.

Sources: [Gogo Q2 2026 press release](https://www.globenewswire.com/news-release/2026/08/06/3340082/0/en/gogo-announces-second-quarter-results.html) · [Q2 2026 earnings call transcript](https://www.investing.com/news/transcripts/earnings-call-transcript-gogo-q2-2026-miss-sparks-15-premarket-drop-93CH-4842510) · [Q2 2026 slides](https://www.investing.com/news/company-news/gogo-q2-2026-slides-military-growth-shines-amid-equipment-headwinds-93CH-4842814) · [Q1 2026 press release / prior guidance](https://www.globenewswire.com/news-release/2026/05/07/3289794/0/en/Gogo-Announces-First-Quarter-Results.html) · [SmartSky verdict](https://www.prnewswire.com/news-releases/smartsky-wins-patent-infringement-lawsuit-versus-gogo-on-all-claims-302625784.html) · [NetJets/Starlink](https://www.aerotime.aero/articles/netjets-starlink-fleet-connectivity) · [Classic ATG shutoff](https://www.weststaraviation.com/news/classic-gogo-atg-systems-service-terminates-may-1-2026-act-now/) · [10-Q (cited, not read)](https://www.sec.gov/Archives/edgar/data/0001537054/000119312526337921/gogo-20260630.htm)