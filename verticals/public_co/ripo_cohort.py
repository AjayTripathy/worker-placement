"""RIPO-intersection cohort — public_co diligencer run on the 25 names that the
Renaissance IPO ETF (CIK 1026634) actually held AND appear in the survivorship-
free 2024-25 primary-IPO backtest (verticals/buyside_dd/.../_ipo_backtest_2024_2025).

Purpose: the buyside_dd backtest showed RIPO's own size/liquidity SELECTION rule
discriminates catastrophes better than the framework's structural screen, and
that exclusion-on-top-of-RIPO is value-destroying. The open question that test
could NOT answer: does the REAL product — the public_co R/f(M) claim-verifier,
run blinded on each prospectus — find independent honesty signal that separates
the 3 catastrophes from the 22 survivors WITHIN RIPO's already-vetted picks?

This module is the entry side. Outcomes are firewalled in `_ripo_outcomes.py`
and must NEVER be read by a scoring subagent.

Cutoff is PER-NAME = the IPO date. Each subagent reads only the prospectus
(S-1/F-1/424B*) filed on or before the offering — a true forward test at the
investment-decision point, matching the backtest's entry = first-day close.

Caveats (load-bearing, honesty-in-labeling):
  - N=25 with only 3 catastrophes is statistically underpowered; treat the
    confusion matrix as anecdote, not significance.
  - The cohort skews software/fintech (Chime, Reddit, Rubrik, ServiceTitan,
    SailPoint, Circle, OneStream) where registry M-sources have little to
    cross-check. Expect heavy UNVERIFIABLE on those. Registry hooks are
    strongest on LNG/land (EPA FRS), defense/aero (USAspending + USPTO),
    diagnostics/pharma (ClinicalTrials/openFDA), and hardware (USPTO).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CohortMember:
    """RIPO-cohort member. CIKs are passed explicitly (cik_override) because
    several names are foreign filers or already delisted (ZEEKR, OneStream) and
    SEC's ticker map is unreliable for them; the backtest cohort.json is the
    single source of truth for these CIKs. cutoff is the per-name IPO date."""
    ticker: str
    name: str
    cik_override: str
    ipo_date: str       # == cutoff for this name
    notes: str

    @property
    def cik(self) -> str:
        from .edgar import cik_for
        return cik_for(self.ticker, override=self.cik_override)

    @property
    def cutoff(self) -> str:
        return self.ipo_date


# Ordered by IPO date. 3 catastrophe labels live ONLY in _ripo_outcomes.py.
COHORT: list[CohortMember] = [
    CohortMember("BTSG", "BrightSpring Health Services, Inc.", "0001865782", "2024-01-26",
                 "Home & community health services + specialty/infusion pharmacy. "
                 "Counterparties: CMS/Medicare/Medicaid, pharma manufacturers. "
                 "Registry hooks: openFDA (drug/establishment), EDGAR FTS for payer "
                 "disclosure. KKR-backed; heavy leverage narrative."),
    CohortMember("AS", "Amer Sports, Inc.", "0001988894", "2024-02-02",
                 "Sporting-goods house of brands (Arc'teryx, Salomon, Wilson, Atomic). "
                 "FOREIGN PRIVATE ISSUER (Cayman inc / Finland ops) — filed F-1, "
                 "files 20-F. Registry hooks: USPTO ODP (brand/product patents). "
                 "Apply foreign-issuer caveat to US-registry absences."),
    CohortMember("RDDT", "Reddit, Inc.", "0001713445", "2024-03-21",
                 "Social-media platform; advertising + data-licensing (Google AI deal) "
                 "revenue. Few registry hooks; data-licensing counterparty disclosure "
                 "via EDGAR FTS (does Alphabet/Google disclose the deal?). Expect "
                 "mostly UNVERIFIABLE / counterparty-disclosure checks."),
    CohortMember("ALAB", "Astera Labs, Inc.", "0001736297", "2024-03-21",
                 "Connectivity semiconductors (PCIe/CXL retimers) for AI datacenters. "
                 "Counterparties: hyperscalers, NVIDIA, cloud OEMs. Registry hooks: "
                 "USPTO ODP (silicon IP), EDGAR FTS for hyperscaler customer disclosure."),
    CohortMember("PACS", "PACS Group, Inc.", "0002001184", "2024-04-12",
                 "Post-acute / skilled-nursing-facility operator. Counterparties: "
                 "CMS/Medicare. Registry hooks: openFDA limited; EDGAR FTS. Reimbursement "
                 "& occupancy claims are the high-value extractions."),
    CohortMember("ULS", "UL Solutions Inc.", "0001901440", "2024-04-15",
                 "Safety testing, inspection & certification (TIC). Counterparties: "
                 "manufacturers across many sectors. Registry hooks: thin (TIC labs "
                 "not in EPA/NHTSA scope); EDGAR FTS for named-customer disclosure."),
    CohortMember("LOAR", "Loar Holdings Inc.", "0002000178", "2024-04-26",
                 "Niche aerospace & defense components (proprietary, sole-source parts). "
                 "Counterparties: airframers, DoD. Registry hooks: USPTO ODP (component "
                 "IP), USAspending (any direct DoD obligations), EDGAR FTS for OEM "
                 "disclosure. Note most A&D content is subcontracted (indirect)."),
    CohortMember("RBRK", "Rubrik, Inc.", "0001943896", "2024-04-26",
                 "Cloud data-security / cyber-resilience SaaS. Counterparties: "
                 "enterprise customers, Microsoft partnership. Few hard registry "
                 "hooks; USPTO ODP for security IP, EDGAR FTS for partner disclosure. "
                 "Expect UNVERIFIABLE-heavy."),
    CohortMember("VIK", "Viking Holdings Ltd", "0001745201", "2024-05-02",
                 "River & ocean cruise operator. FOREIGN PRIVATE ISSUER (Bermuda) — "
                 "filed F-1. Registry hooks: thin in US federal registries; fleet/"
                 "newbuild orderbook and booking-curve claims are the extractions. "
                 "Apply foreign-issuer caveat."),
    CohortMember("ZEEKR", "ZEEKR Intelligent Technology Holding Ltd", "0001954042", "2024-05-10",
                 "Premium China EV brand (Geely). FOREIGN PRIVATE ISSUER (Cayman/China) — "
                 "filed F-1, ADS. LATER TAKEN PRIVATE by Geely (cash-out, NOT a failure). "
                 "Registry hooks: NHTSA only covers US-sold vehicles (likely empty for "
                 "China-market deliveries — do NOT red-flag absence); USPTO ODP possible. "
                 "Delivery-volume and production claims are the extractions."),
    CohortMember("WAY", "Waystar Holding Corp.", "0001990354", "2024-06-07",
                 "Healthcare-payments / revenue-cycle SaaS for providers. Counterparties: "
                 "hospitals, health systems, payers. Few registry hooks; EDGAR FTS for "
                 "named-client disclosure. Expect UNVERIFIABLE-heavy."),
    CohortMember("TEM", "Tempus AI, Inc.", "0001717115", "2024-06-17",
                 "Precision-medicine / genomic-diagnostics + AI. Counterparties: pharma, "
                 "health systems. Registry hooks: ClinicalTrials.gov (trial partnerships), "
                 "openFDA (assays/devices), USPTO ODP. Strong verifiability."),
    CohortMember("LB", "LandBridge Co LLC", "0001995807", "2024-06-28",
                 "Permian Basin surface-land owner; royalties, water, easements, data-"
                 "center/solar land deals. Counterparties: E&P operators, WaterBridge. "
                 "Registry hooks: EPA FRS (facilities on the land), EDGAR FTS for "
                 "operator disclosure. Acreage and royalty claims are the extractions."),
    CohortMember("ONESTREAM", "OneStream, Inc.", "0001889956", "2024-07-24",
                 "Corporate performance-management (CPM) finance SaaS. LATER TAKEN "
                 "PRIVATE (cash-out, NOT a failure). Few registry hooks; EDGAR FTS for "
                 "named-customer disclosure. Expect UNVERIFIABLE-heavy."),
    CohortMember("LINE", "Lineage, Inc.", "0001868159", "2024-07-26",
                 "Temperature-controlled (cold-storage) warehouse REIT — world's largest. "
                 "Counterparties: food producers, grocers. Registry hooks: EPA FRS "
                 "(ammonia-refrigeration facilities ARE EPA-regulated — strong), EDGAR "
                 "FTS. Facility-count and capacity claims are the extractions."),
    CohortMember("SARO", "StandardAero, Inc.", "0002025410", "2024-10-02",
                 "Aerospace engine MRO (maintenance, repair, overhaul). Counterparties: "
                 "airlines, OEMs (GE, P&W, RR), DoD. Registry hooks: USAspending (DoD "
                 "MRO contracts), USPTO ODP, EDGAR FTS for OEM-authorization disclosure."),
    CohortMember("PONY", "Pony AI Inc.", "0001969302", "2024-11-27",
                 "Autonomous-driving (robotaxi/robotruck), China + some US. FOREIGN "
                 "PRIVATE ISSUER (Cayman/China) — filed F-1, ADS. Registry hooks: NHTSA "
                 "(US AV testing limited; China fleet not covered — caveat absence), "
                 "USPTO ODP (AV IP). Permit/fleet-size and partnership claims extract well."),
    CohortMember("TTAN", "ServiceTitan, Inc.", "0001638826", "2024-12-12",
                 "Vertical SaaS for trades (HVAC/plumbing/electrical contractors). "
                 "Counterparties: SMB contractors. Few registry hooks; EDGAR FTS thin "
                 "(SMB customers don't file). Expect UNVERIFIABLE-heavy."),
    CohortMember("VG", "Venture Global, Inc.", "0002007855", "2025-01-24",
                 "LNG export-terminal developer (Calcasieu Pass, Plaquemines). "
                 "Counterparties: offtakers (Shell, BP, ENGIE), FERC, DOE. Registry "
                 "hooks: EPA FRS (the terminals ARE major EPA-permitted facilities — "
                 "strong), EDGAR FTS for offtaker SPA disclosure (note ongoing offtaker "
                 "arbitration). Capacity, FID, and offtake claims are high-value."),
    CohortMember("KRMN", "Karman Holdings Inc.", "0002040127", "2025-02-13",
                 "Defense & space systems (missile/hypersonics structures, propulsion). "
                 "Counterparties: DoD, primes, NASA. Registry hooks: USAspending (DoD "
                 "obligations — strong), USPTO ODP, EDGAR FTS for prime disclosure. "
                 "Named-program participation claims are the high-value extractions."),
    CohortMember("SAIL", "SailPoint, Inc.", "0002030781", "2025-02-14",
                 "Identity-security / governance SaaS (Thoma Bravo re-IPO). "
                 "Counterparties: enterprise customers. Few registry hooks; USPTO ODP "
                 "for identity IP, EDGAR FTS for partner disclosure. UNVERIFIABLE-heavy."),
    CohortMember("CRWV", "CoreWeave, Inc.", "0001769628", "2025-03-31",
                 "GPU-cloud / AI-infrastructure provider. Counterparties: NVIDIA "
                 "(investor+supplier), Microsoft (major customer), OpenAI. Registry "
                 "hooks: EPA FRS (data-center facilities — variable), EDGAR FTS for "
                 "Microsoft/NVIDIA customer-and-supplier disclosure (strong: are the "
                 "concentration claims corroborated?). Capex and contract-backlog claims."),
    CohortMember("CRCL", "Circle Internet Group, Inc.", "0001876042", "2025-06-05",
                 "USDC stablecoin issuer. Counterparties: Coinbase (revenue-share), "
                 "banks/custodians, BlackRock (reserve fund). Registry hooks: EDGAR FTS "
                 "for Coinbase/BlackRock disclosure of the arrangements; reserve-"
                 "attestation claims. Crypto-specific — thin federal registry coverage."),
    CohortMember("CHYM", "Chime Financial, Inc.", "0001795586", "2025-06-12",
                 "Consumer neobank (banking-as-a-service via The Bancorp / Stride Bank). "
                 "Counterparties: partner banks, Visa. Registry hooks: EDGAR FTS for "
                 "partner-bank disclosure; few hard registries (Chime is not itself a "
                 "chartered bank). Member-count and interchange claims; UNVERIFIABLE-heavy."),
    CohortMember("CAI", "Caris Life Sciences, Inc.", "0002019410", "2025-06-20",
                 "Molecular-diagnostics / cancer-profiling + AI. Counterparties: pharma, "
                 "oncology networks. Registry hooks: ClinicalTrials.gov (trial/biopharma "
                 "partnerships), openFDA (assay/device), USPTO ODP. Strong verifiability."),
]


COHORT_CONTEXT = (
    "Newly-public companies (primary IPOs Jan-2024 -> Jun-2025) that the "
    "Renaissance IPO ETF actually held — i.e. names that already passed a "
    "size/liquidity selection screen. Each is scored from its PROSPECTUS "
    "(S-1 / F-1 / 424B4) as of the IPO date. The cohort is sector-heterogeneous: "
    "LNG/land & real-assets (EPA FRS strong), defense/aerospace (USAspending + "
    "USPTO strong), diagnostics/pharma (ClinicalTrials.gov + openFDA strong), "
    "hardware/semis (USPTO strong), and a large software/fintech/crypto bloc "
    "(few hard registry hooks — rely on EDGAR full-text counterparty disclosure "
    "and expect heavy UNVERIFIABLE). Pick M-source queries from the per-name "
    "notes. The test is whether independent registry evidence at the IPO date "
    "separates honest disclosure from underdelivery — NOT whether the company "
    "later rose or fell (that label is firewalled)."
)


# Counterparties that recur across the cohort — use with edgar_fts.query_fulltext
# (cik=COUNTERPARTY) to test whether a claimed relationship is disclosed by the
# other side. Not exhaustive; subagents resolve others from the filing.
COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    "NVIDIA (NVDA)":            "0001045810",
    "Microsoft (MSFT)":         "0000789019",
    "Alphabet / Google (GOOGL)":"0001652044",
    "Coinbase (COIN)":          "0001679788",
    "BlackRock (BLK)":          "0001364742",
    "Visa (V)":                 "0001403161",
    "Shell plc (SHEL)":         "0001306965",
    "BP plc (BP)":              "0000313807",
    "GE Aerospace (GE)":        "0000040545",
    "RTX / Pratt & Whitney":    "0000101829",
}
