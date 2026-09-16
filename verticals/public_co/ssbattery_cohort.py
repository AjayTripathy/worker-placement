"""
Solid-state / next-gen battery cohort — Signal OS blinded forward test.

5 speculative pre-revenue or early-revenue battery pure-plays (QS / SES /
SLDP / MVST / ENVX) + 2 lithium-supply controls (ALB Albemarle, LAC
Lithium Americas). The speculative names all share the lidar-style
narrative: OEM design-wins, named-platform SOP dates, headline GWh
production capacity claims. The lithium controls are upstream raw-
material players — different stage of the value chain, real revenue,
real customer disclosure.

Direct sibling to the lidar cohort: same OEM-design-win stage-ladder
discipline, same counterparty-disclosure threshold against named auto
OEMs. Different vertical, same evasion patterns.

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
        ticker="QS",
        name="QuantumScape Corp.",
        notes="Solid-state lithium-metal battery; de-SPAC 2020 via Kensington "
              "Capital. VW / Cariad partnership (since 2018) is the "
              "centerpiece claim. Long history of pushed-out QSE-5 "
              "production timelines."),
    CohortMember(
        ticker="SES",
        name="SES AI Corp.",
        notes="Lithium-metal battery; de-SPAC 2022. Claims joint development "
              "agreements with GM, Hyundai, Honda. Pre-revenue. Recent "
              "AI-pivot rebrand in name."),
    CohortMember(
        ticker="SLDP",
        name="Solid Power, Inc.",
        notes="Sulfide-based solid-state battery; de-SPAC 2021. Ford / "
              "BMW joint development agreements. Pre-commercial."),
    CohortMember(
        ticker="MVST",
        name="Microvast Holdings, Inc.",
        notes="Commercial-vehicle Li-ion batteries (NOT solid-state — "
              "LTO / NMC chemistries). De-SPAC 2021. Recent DOE grant "
              "controversy / rescission. China manufacturing footprint."),
    CohortMember(
        ticker="ENVX",
        name="Enovix Corp.",
        notes="Silicon-anode lithium-ion (not solid-state per se but adjacent "
              "next-gen); de-SPAC 2021. Smartphone / wearable market claims; "
              "Malaysia Fab-2 ramp."),
    CohortMember(
        ticker="ALB",
        name="Albemarle Corp.",
        notes="**CONTROL** — world's largest lithium producer. Real revenue, "
              "established customer base across all major battery makers. "
              "Expected to score clean — different value-chain position."),
    CohortMember(
        ticker="LAC",
        name="Lithium Americas Corp.",
        notes="**CONTROL** — Thacker Pass lithium project (Nevada) operator. "
              "DOE loan + GM offtake disclosed; pre-production but milestones "
              "are real and counterparty-corroborated. Expected to score "
              "relatively clean as a controlled-development play."),
]


COHORT_CONTEXT = (
    "Solid-state / next-gen battery pure-play (lithium-metal / sulfide-based "
    "/ silicon-anode) or lithium raw-material producer. Counterparties span "
    "auto OEMs (Volkswagen / CARIAD foreign, Ford F, GM, Mercedes foreign, "
    "BMW foreign, Honda HMC 20-F, Hyundai foreign, Stellantis STLA), "
    "Tier-1 battery makers (CATL / Samsung SDI / LG Energy Solution / "
    "Panasonic — all foreign filers), DOE (loan programs, LPO, ARPA-E "
    "Battery500), and downstream consumer electronics (AAPL).\n\n"
    "Claims typically reference: named OEM JDA / SOP date, planned GWh "
    "production capacity, energy-density Wh/kg or Wh/L milestones, cycle-"
    "life numbers, validation tests / B-sample / C-sample / EV-grade "
    "cells, DOE grant / loan awards. Battery sub-vertical heuristic: "
    "energy-density and cycle-life claims should reference test conditions "
    "(rate, temperature, depth-of-discharge); claims without conditions "
    "are aspirational research-paper milestones, not production cells.\n\n"
    "Apply Calibration Heuristic 3 (planned vs operational) WITH EXTRA WEIGHT. "
    "Battery design-wins move through stages: JDA -> A-sample -> B-sample -> "
    "C-sample -> validation -> SOP -> series production. Each stage is a "
    "different claim with a different M-side cross-check. Conflating JDA "
    "with SOP is the central evasion pattern; lithium production capacity "
    "claims (e.g. 'X GWh by 2026') should be checked against actual installed "
    "capacity in the financial-statement notes.\n\n"
    "Apply Layer 3 Rule 7 (counterparty-disclosure threshold). Volkswagen "
    "is QS's flagship customer — if VW's 20-F doesn't mention QuantumScape "
    "in series production by the claimed SOP year, that's a HARD "
    "CONTRADICTION. Same for Ford / BMW for SLDP; same for GM / Hyundai / "
    "Honda for SES. Note: most major OEMs (VW, BMW, Mercedes, Hyundai, "
    "Toyota) file foreign forms (20-F) or don't file SEC forms at all; "
    "EDGAR coverage is partial. Acknowledge UNVERIFIABLE rather than "
    "false-clean."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Auto OEMs — US-listed
    "Ford Motor (F)":              "0000037996",
    "General Motors (GM)":         "0001467858",
    "Stellantis NV (STLA)":        "0001605484",
    "Tesla (TSLA)":                "0001318605",
    "Rivian (RIVN)":               "0001874178",
    "Lucid Group (LCID)":          "0001811210",
    "Polestar (PSNY)":             "0001884082",
    "Toyota Motor (TM, 20-F)":     "0001094517",
    "Honda Motor (HMC, 20-F)":     "0000715153",
    # Consumer electronics (silicon-anode customers)
    "Apple (AAPL)":                "0000320193",
    # Lithium-supply context
    "Albemarle (ALB)":             "0000915913",
    "Lithium Americas (LAC)":      "0001440972",
}


CUTOFF = "2026-05-16"
