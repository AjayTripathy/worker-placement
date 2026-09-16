"""
Brick-and-mortar retail distress cohort — Signal OS blinded forward test.

5 distressed-narrative names (KSS / M / JWN / GPS / BIG) + 2 retail-
resilient controls (TJX off-price / COST membership-warehouse). Tests
the framework's ability to discriminate honest-but-distressed retail
(comp-store-sales declines, going-concern caveats) from cleanly
operating retail.

Heuristic emphasis: comp-store-sales narratives, store-count
trajectories, lease-portfolio commitments, going-concern qualifiers,
form-15-12G / 25-NSE distress fingerprints. BIG specifically emerged
from Ch.11 in 2024 — its post-emergence claims should be cross-checked
against its plan of reorganization.

Uniform cutoff: 2026-05-16.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CohortMember:
    """Cohort member with CIK derived from ticker via SEC's authoritative map.

    Do NOT pass cik= directly. Use cik_override= only for tickers SEC's
    company_tickers.json doesn't list (rare: certain foreign filers, recently
    delisted, or special ADRs). Default code path resolves CIK on demand from
    `edgar.cik_for(ticker)` — single source of truth, no hand-typed CIKs.
    """
    ticker: str
    name:   str
    notes:  str
    cik_override: str | None = None  # rarely used; default is SEC lookup

    @property
    def cik(self) -> str:
        from .edgar import cik_for
        return cik_for(self.ticker, override=self.cik_override)
COHORT: list[CohortMember] = [
    CohortMember(
        ticker="KSS",
        name="Kohl's Corporation",
        notes="Mid-tier department store. Multi-year comp-sales decline. "
              "Recent management turnover. Real-estate-heavy."),
    CohortMember(
        ticker="M",
        name="Macy's, Inc.",
        notes="Mid-tier department store. Multi-format (Macy's, "
              "Bloomingdale's, Bluemercury). Real-estate portfolio. "
              "Recent take-private overtures (prior cycles)."),
    CohortMember(
        ticker="JWN", cik_override="0000072333",
        name="Nordstrom, Inc.",
        notes="Premium department store. Nordstrom Rack off-price + "
              "full-line + Hautelook. Recent take-private filings."),
    CohortMember(
        ticker="GPS", cik_override="0000039911",
        name="The Gap, Inc.",
        notes="Apparel (Gap, Old Navy, Banana Republic, Athleta). "
              "Multi-year comp-sales pressure. Banana Republic + "
              "Athleta as growth narratives."),
    CohortMember(
        ticker="BIG", cik_override="0000768835",
        name="Big Lots, Inc.",
        notes="Closeout / off-price discount retailer. Emerged from "
              "Chapter 11 in 2024 via Nexus Capital acquisition. "
              "Post-emergence claims need cross-check against plan "
              "of reorganization."),
    CohortMember(
        ticker="TJX",
        name="The TJX Companies, Inc.",
        notes="**CONTROL** — off-price retail (T.J. Maxx, Marshalls, "
              "HomeGoods, Winners). Consistently positive comps for "
              "decades. Real revenue growth, mature disclosure."),
    CohortMember(
        ticker="COST",
        name="Costco Wholesale Corporation",
        notes="**CONTROL** — membership warehouse club. Real revenue, "
              "predictable membership-fee growth. Best-in-class "
              "retail disclosure."),
]


COHORT_CONTEXT = (
    "Brick-and-mortar retail (department store / off-price / apparel "
    "/ discount). Counterparties span: suppliers (apparel and consumer "
    "brands), commercial real-estate landlords (mall REITs like SPG / "
    "Simon Property Group, MAC / Macerich), and credit-card / payment "
    "partners. Most retail-distress claims pivot on:\n"
    "  - Comp-store-sales trajectory (real M-side check: customers' "
    "credit-card data; not directly registry-queryable, but suppliers' "
    "10-Ks discuss volume to top retailers)\n"
    "  - Store-count + lease-commitments disclosure\n"
    "  - Going-concern qualifier or covenant compliance\n"
    "  - Inventory turns vs. industry benchmarks\n\n"
    "Apply Calibration Heuristic 3 (planned vs operational): announced "
    "store closures vs executed store closures; announced cost-savings "
    "vs realized cost-savings. Retail-distress names typically have "
    "multi-year transformation plans; trace each named milestone to "
    "the corresponding M-side evidence.\n\n"
    "Apply Layer 3 Rule 10 hard for this cohort: form-15-12G, 25-NSE, "
    "going-concern qualifiers, large-write-down charges in 8-K, "
    "covenant-waiver disclosures are direct distress markers.\n\n"
    "**Calibration note:** this cohort has slow-bleed dynamics — even "
    "real distress names can grind sideways for years before resolution. "
    "Emissions should be paired with a tighter exit rule than the "
    "default 12-month falsification window."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Mall REIT landlords
    "Simon Property Group (SPG)":  "0001063761",
    "Macerich (MAC)":              "0000912242",
    # Apparel / consumer brand suppliers
    "Hanesbrands (HBI)":           "0001359841",
    "Levi Strauss (LEVI)":         "0000094845",
    "VF Corp (VFC)":               "0000103379",
    "Tapestry (TPR)":              "0001116132",
    # Payment / credit card
    "American Express (AXP)":      "0000004962",
    "Capital One (COF)":           "0000927628",
    "Visa (V)":                    "0001403161",
    # Off-price / warehouse compare-set
    "TJX (TJX)":                   "0000109198",
    "Ross Stores (ROST)":          "0000745732",
    "Burlington (BURL)":           "0001579298",
}


CUTOFF = "2026-05-16"
