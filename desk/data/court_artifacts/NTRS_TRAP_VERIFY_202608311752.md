### NTRS (Northern Trust — global custody/asset servicing + wealth management bank) — screen `omitted_metric`: "organic growth", "return on equity" dropped Q1→Q2 FY26 — **SCREEN-ARTIFACT**

**KILL FACTS (the flag is refuted at the exhibit layer)**
- Q2 FY26 EX-99.1 (8-K 2026-07-22, acc. 0000073124-26-000043) *does* carry ROE: "Financial Ratios — **Return on Average Common Equity 25.9% / 17.4% / 15.4% / 14.8% / 14.2%**" — [q22026earningsreleaseex991.htm](https://www.sec.gov/Archives/edgar/data/0000073124/000007312426000043/q22026earningsreleaseex991.htm). It also carries organic growth: CEO quote, "…helped drive an **eighth consecutive quarter of positive organic trust-fee growth**."
- **Defect class: phrase-literal adjacency matcher.** The detector required the exact bigrams `organic growth` and `return on equity`. Q2 used `organic **trust-fee** growth` and `Return on **Average Common** Equity`. Infixes broke the match; nothing was omitted and nothing under-parsed — the EX-99 read fine. Not an extraction artifact, a *matcher* artifact.
- **Direction gate missing (second, independent defect).** Masking requires deterioration. ROE went **17.4% → 25.9%** and organic fee growth extended to an eighth positive quarter ([Q1 EX-99.1](https://www.sec.gov/Archives/edgar/data/0000073124/000007312426000028/q12026earningsreleaseex991.htm): "Return on equity reached 17.4%"; "improved organic growth"). A flag on an *improving* metric should be auto-suppressed.

**LIVE FACTS (anti-masking finding — file it as positive)**
- Real narrative delta exists: the **Q1 CEO quote named ROE; the Q2 CEO quote did not**. But Q2's 25.9% is inflated by a **$525.4M pre-tax Visa Class B exchange gain**; the PR ring-fences it and quotes "+40% EPS **excluding notable items**." Declining to headline a one-off-inflated ROE is *conservative* disclosure — the inverse of masking. Sibling/multi-venue check passes: ROE still shown in the Q2 ratio table and the Q2 deck ([slides coverage](https://www.investing.com/news/company-news/northern-trust-q2-2026-slides-40-eps-growth-visa-gain-boosts-results-93CH-4806332)).
- SBC-vs-dilution honest: diluted shares 208.7M (Q1'23) → 193.4M (Q2'25), XBRL pack — ~7% real shrink.
- Cap structure: **Series D preferred redeemed 10/01/2026** (8-K 2026-08-03). NTRSO = Series E depositary share, not common — instrument-class guard.
- Tape $186.23, −4.9% off 52w high. Not an orphan: fully covered custody bank, so no FAIR-CARRY claim.

**RESOLVES ON:**
- 2026-10-21 (yfinance-derived, **UNCONFIRMED** — no company PR names it): does the Q3 PR restore ROE to the CEO quote once the Visa gain is out of the compare? Restoration = confirms conservative-omission read.
- Before next generator run: matcher fix (synonym lexicon + infix tolerance) and direction gate both shipped.

**Disposition:** AVOID/DECLINE the integrity court — dequeue NTRS from TRAP_VERIFY, no honesty case exists. **Prompt correction (first-class output): "the Q2 PR contains neither" is false.** Reopen-condition: a PR where a matched metric is absent from *both* the ratio table and the deck *while* the underlying value deteriorates QoQ.