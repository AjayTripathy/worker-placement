# Narrative-Only R-Claims

**Generated**: 2026-05-26 (follows MANIFEST.md / GAPS.md)
**Purpose**: R-claims surfaced in the IJR manifest that have **no clean deterministic verification source** and therefore require LLM narrative reasoning over filings. These are the residual that the agentic R/f/M scorer must own; deterministic m-sources cannot substitute.

## Implication for IJR test design

If the deterministic battery (existing + Tier 1 gaps from GAPS.md) covers ~70-80% of catastrophe R-claims at meaningful precision, the narrative-only residual is the gap the agentic scorer would need to close — but the asymmetric-payoff math from HANDOFF.md says deterministic at lower precision still wins. So **narrative-only verification should be reserved for borderline names** (composite score in the middle tercile), not run on the full universe.

---

## Universal narrative-only claims (apply to all 608)

| # | R-claim | Why no deterministic source | Best LLM substitute |
|---|---|---|---|
| N1 | "Our brand has strengthened YoY" | Brand strength is a survey/qualitative construct; no public NPS feed | LLM compares marketing-spend YoY vs. claimed brand momentum |
| N2 | "Customer satisfaction is at all-time high" | NPS, CSAT, ACSI partial. Public ACSI covers ~50 large companies only | LLM cross-refs glassdoor/yelp/app-store sentiment delta |
| N3 | "We are not losing key talent" | Glassdoor reviews scraped, but selection bias huge | LLM compares Form 4 named-executive 10b5-1 plan adoption + 8-K 5.02 cluster |
| N4 | "Strategic review continuing" (pre-announcement) | No deterministic source — by definition pre-disclosure | LLM tracks language drift across 8-Ks / earnings transcripts |
| N5 | "We expect to launch [product] in [future quarter]" | No source until launched | LLM cross-refs prior-period launch promises vs. actuals (claim_evolution helps partially) |
| N6 | "TAM is $X billion and growing" | TAM is a claim, often self-cited from analyst reports | LLM checks whether TAM definition has been re-stretched YoY |
| N7 | "Pricing power is intact" | Pricing realization is private | LLM cross-refs gross-margin trajectory vs. claim |
| N8 | "Channel partners are healthy" | Channel-partner financials not public | LLM scans for distributor 10-K filings (sparse) |
| N9 | "Our culture / values are a competitive moat" | Pure qualitative | LLM checks for Glassdoor rating cliff + key-exec departures |
| N10 | "Founder/CEO long-term commitment" | Self-claim | LLM checks Form 4 net sell-downs + 10b5-1 inception |

## Cluster-specific narrative-only claims

### REAL_ESTATE
- N11 (REITs): "Sub-market fundamentals improving" — RCA / CoStar data paywalled
- N12: "Cap rate is supported by recent comps" — same paywall
- N13: "Tenant negotiations on renewals progressing" — pre-renewal narrative

### TECH_HARDWARE / SOFTWARE
- N14: "Customer pipeline is the strongest we've seen" — pre-bookings narrative
- N15: "Design-win activity accelerating" — `design_win_proxy.py` deprioritized → narrative-only
- N16: "AI / GenAI tailwind is real for our product" — sentiment claim, no clean unit

### HEALTHCARE_PHARMA / DEVICES
- N17: "Pre-clinical data supports advancement" — Pre-NCT-listing data not public
- N18: "We have strong KOL support" — qualitative
- N19: "Reimbursement landscape favorable" — partial CMS coverage signal, but commercial payer dynamics opaque

### HEALTHCARE_SERVICES
- N20: "Star ratings improving" — CMS data exists for some segments, partial deterministic substitute via `cms_qcor.py`
- N21: "Physician partnerships expanding" — qualitative narrative

### CONSUMER (RETAIL / RESTAURANTS / DISCRETIONARY)
- N22: "We are over the inventory hangover" — partial via `working_capital_drift.py` but qualitative residual
- N23: "Loyalty program engagement up" — internal-only KPI
- N24: "International expansion on track" — pre-launch narrative
- N25: "Off-price channel disciplined" — apparel-specific narrative

### ENERGY
- N26: "Hedging strategy positions us well" — partial via `hedge_book_check.py`; strategy commentary residual
- N27: "Reserve revisions are technical, not structural" — narrative interpretation of `reserves_revision.py`

### COMMUNICATIONS
- N28: "Fiber footprint build-out on schedule" — partial via `fcc_form_477.py`, but pre-completion claim
- N29: "Wholesale agreement on track" — pre-contract narrative

### CONSUMER_SERVICES
- N30: "Enrollment quality improving" (for-profit edu) — partial via IPEDS but qualitative claim
- N31: "Sponsorship pipeline robust" — MSGS-style, no public source

### INDUSTRIALS_CONSTRUCTION
- N32: "Land position is well-positioned for spring selling season" — qualitative
- N33: "Cycle inventory is appropriate" — partial via working_capital, residual narrative

### INDUSTRIALS_TRANSPORT
- N34: "Pricing discipline holding in trucking spot market" — directional from BTS/Cass index but commentary residual
- N35: "Fleet age managed appropriately" — internal KPI

### UTILITIES
- N36: "Regulatory environment is constructive" — qualitative
- N37: "Wildfire mitigation plan on track" — pre-incident narrative

### FINANCIALS
- N38: "Reserve build is appropriate" — qualitative on top of FDIC data
- N39: "Insurance pricing cycle hardening" — qualitative

---

## How to deploy the agentic scorer (when narrative-only matters)

Recommend deploying the agentic R/f/M scorer only on names where:
1. **Composite from deterministic battery is borderline** (e.g., 0.35-0.55 in the 0-1 normalized space), AND
2. **Narrative-heavy cluster** (TECH_SOFTWARE_SERVICES, CONSUMER_SERVICES, certain HEALTHCARE_PHARMA dev-stage)

This bounds the agentic call volume to ~50-80 of the 608 names, ~5-10x cheaper than full-universe agentic scoring while still catching the residual narrative liars.
