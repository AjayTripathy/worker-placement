# Fresh-Universe Taxonomy Re-Run — Cross-Cohort Results

_Re-ran the planner on all 8 fresh-universe tickers (LRHC, KULR, HDSN,
PESI, CWCO, CDNA, ALMU, KLIC) with the new taxonomy-aware prompt and
creative_extensions field. The original v1 plans used a flat catalog;
v2 plans use the (domain, claim_type) taxonomy as a strong default
plus explicit invitation for creative extensions._

## Per-ticker output

| Ticker | Claims | MAPPED | PROPOSED | NONE | Creative Ext. | Notes |
|--------|-------:|-------:|---------:|-----:|--------------:|-------|
| ALMU   | 8 | 7 | 1 | 0 | **30** | 4 framework calibration issues caught |
| KULR   | 9 | 8 | 0 | 1 | **27** | On-chain BTC verification, NASA TechPort |
| KLIC   | 7 | 6 | 1 | 0 | **25** | Singapore/Suzhou registries, BIS Entity List |
| LRHC   | 10 | 8 | 2 | 0 | **25** | State real-estate license-board (PROPOSED) |
| CDNA   | 8 | 5 | 3 | 0 | **23** | CMS LCD lookup, FDA 510(k), PACER (PROPOSED) |
| PESI   | 8 | 7 | 1 | 0 | **21** | EU TED (PROPOSED), excellent calibration discipline |
| CWCO   | 8 | 6 | 1 | 1 | **19** | Cayman OfReg, BVI, Bahamas WSC |
| HDSN   | 8 | 7 | 1 | 0 | **19** | EPA Section 608 reclaimer list |
| **Total** | **66** | **54** | **10** | **2** | **189** | |

Overall: **82% of claims got CANONICAL/PROVISIONAL taxonomy mapping**;
the remaining 18% surfaced as PROPOSED connectors (real connector
gaps the planner identified). **189 creative_extensions across 8
tickers — ~23 per ticker on average, far more than the flat-catalog
prompt produced.**

## Multi-ticker creative-extension proposals (the next-connector backlog)

Semantic grouping (state-by-state/county-by-county variants folded
together) reveals which novel sources the planners *independently
converged on* across different industries:

```
rank  src_label                                       #tickers  example tickers
=================================================================================
 1.   New York / state UCC lien filings (DOS-1500)        8/8   ALMU,CDNA,CWCO,HDSN,KLIC,KULR,LRHC,PESI
 2.   BLS QCEW NAICS-N county employment                  5/8   ALMU,CWCO,KLIC,KULR,LRHC
 3.   USPTO Patent Assignment Database (PAS)              4/8   ALMU,CDNA,KLIC,KULR
 4.   NASA NTRS (Technical Reports Server)                4/8   ALMU,CWCO,KLIC,KULR
 5.   DoD program-office press releases (MDA/SF/AFRL)     3/8   ALMU,KULR,PESI
 6.   LinkedIn headcount snapshot                         3/8   ALMU,KLIC,LRHC
 7.   Foreign business registry (Singapore ACRA etc.)     3/8   CWCO,KLIC,PESI
 8.   NASA SBIR/STTR Award Database                       2/8   ALMU,KULR
 9.   PCAOB audit-firm registry                           2/8   ALMU,LRHC
 10.  Compound-semi industry trade assoc / SEMI          2/8   ALMU,HDSN
```

**The #1 finding is the convergence on UCC lien filings (8/8).**
Every planner independently identified state UCC-1 filing databases
as the missing lien/encumbrance source. This catches:
- Senior debt encumbrances
- Receivables financing
- Equipment leases reclassified as financing
- Insider / affiliate loans secured against company assets
- Distress signals (sudden new UCC filings post-cutoff)

That's a universally-applicable connector across ALL domains in the
taxonomy. **Building `ucc_filings.query_secretary_of_state` is the
clearest next-connector priority.**

## Per-ticker discipline highlights

Selected calibration findings the agents articulated that the
framework should learn from:

**ALMU — caught 4 calibration issues:**
1. The `$5M flat SUB_MATERIAL threshold` is wrong for a $918K-revenue
   R&D firm: $1.32M IS material at that scale; only INFLATION_SUSPECT
   (0 UEIs) is a hard contradiction. Threshold should be revenue-scaled.
2. Megacap-claim *disclaiming* matters: ALMU explicitly says "Apple
   does not currently use our technology" — INFLATION_SUSPECT should
   then be the expected baseline, not a contradiction.
3. The AIRO-signature stock-for-services trigger needs refinement —
   pre-IPO UCSB-advisor compensation is qualitatively different from
   microcap promoter dilution. Recipient-identity reverse search is
   the diagnostic test.
4. Proposed `sbir_gov.firm_awards` connector for sub-$5M federal R&D
   claims that USAspending under-represents.

**CDNA — captured the actual forward-mover mechanism:**
Plan explicitly identified that the +24% forward return was driven
by Natera invalidity ruling + $96.3M liability derecognition flipping
GAAP net income. The framework's NO-EMIT was right; this plan
explains *why* a short would have failed (litigation outcome
flipping a contingent liability).

**PESI — explicit discipline against over-firing:**
- BWXT-team membership flagged as "contingent" — absence not contradiction
- EU procurement flagged with H5 over-fit warning (USAspending doesn't cover EU)
- Distress-cluster H10 markers acknowledged BUT noted as "distress-
  funded-through-capital-markets" (no going-concern, $29M cash,
  equity raises at $14-16 not penny-stock, lender amendments are
  loosening not flight)
- Hanford LAW PLA flagged as forward-tense optionality

**CWCO — distress-signal suppression discipline:**
- Material weakness = "remediated ITGC change-management with no
  misstatements" — not real distress
- Continuous dividends since 1985 — non-distress signal
- "Stock for services" = routine 2008 Equity Incentive Plan grants
  (~0.65% dilution) — NOT services-for-shares fundraising

**HDSN — surfaced canonical regulatory list:**
- EPA Section 608 reclaimer list = the canonical "are you a real
  refrigerant reclaimer?" registry, exactly right for HDSN's business
- EPA AIM Act allocation connector proposed for HFC phase-down regs

**KULR — domain-specific blockchain insight:**
- Proposed on-chain BTC verification (public Bitcoin address visibility)
  as the canonical f(M) for KULR's Bitcoin treasury claim
- PHMSA hazmat / lithium-ion shipping regulations
- UL Product iQ certification database

**LRHC — domain-correct PROPOSED:**
- Real-estate brokerage's main GAP is state real-estate license
  boards; planner correctly emitted PROPOSED for agent count + office
  count rather than mapping to a noisy proxy.

## What the taxonomy added vs the flat catalog

1. **Domain classification was automatic.** All 8 tickers correctly
   mapped to their taxonomy domain. Subagents picked canonical
   sources for the right (domain, claim_type) cell.

2. **Creative_extensions is genuinely creative.** 189 proposals
   spanning foreign registries (Singapore, Cayman, BVI, Bahamas,
   China Suzhou, Israeli CBS), niche US sources (BIS Entity List,
   USTR Section 301, NASA TechPort, EPA Section 608, county
   assessors), domain-specific industry registries (SEMI, AHRI,
   compound-semi trade associations), visual/blockchain (satellite
   imagery, on-chain BTC verification), litigation/audit (PACER,
   PCAOB), and aggregates (BLS QCEW, Census).

3. **GAP cells correctly triggered PROPOSED status.** 10 PROPOSED
   claims across 4 tickers (CDNA 3, LRHC 2, KLIC 1, HDSN 1, PESI 1,
   CWCO 1, ALMU 1) — every PROPOSED targeted a real connector gap
   the taxonomy had marked.

4. **Calibration discipline was preserved.** Heuristic-fit warnings
   (mega-cap counterparty, EU coverage, distress-cluster nuance) all
   correctly applied. The planner refused to over-fire on real
   federal vendors (PESI), real utilities (CWCO), and the catalyst-
   rally name (ALMU).

5. **The promotion path is mechanical.** UCC filings at 8/8 is the
   clearest signal: build that connector first.

## Files

- `_proposed_sources/*.creative_extensions.json` — 8 per-ticker logs
- `proposals_backlog.json` — ranked aggregation across cohort
- `aggregate_proposals.py` — semantic grouping helper
- `<TK>.plan.v2.json` — new taxonomy-aware plans (8 tickers)
- `<TK>.queries.json` — executor output with creative_extensions logged
