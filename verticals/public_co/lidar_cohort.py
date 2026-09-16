"""
Lidar / ADAS cohort — Signal OS blinded forward test.

Five US-listed lidar pure-plays. Three speculative pre-series-production
names with heavy OEM-design-win narratives + two more revenue-stage names
that serve as partial controls (revenue exists, but customer-concentration
and design-win-vs-production-line claims are still testable).

Cohort selection criteria (per `feedback_truth_vs_alpha.md`):
  - HIGH Truth_signal potential: OEM-design-win / series-production claims
    are highly testable against named-OEM 10-K / 20-F counterparty
    disclosure; lidar pure-plays have to name OEM customers by brand to
    sustain valuation.
  - HIGH Discovery_advantage potential: MVIS is a well-known short-target
    (Hindenburg-adjacent attention); LAZR, AEVA, OUST, INVZ are
    less-covered or post-de-SPAC under-followed names.

Calibration emphasis for this cohort:
  - Heuristic 3 (planned vs operational) — design-win STAGE LADDER is
    decisive: "RFQ / evaluating" < "selected / nominated" < "design-win
    awarded" < "series-production line tooling complete" < "Start-of-
    Production / SOP" < "shipping at series-production volume". Each
    rung is a different M-side cross-check.
  - Heuristic 7 (counterparty-disclosure threshold) — for any claim
    naming an OEM (Volvo, Mercedes, BMW, GM, Ford, Polestar, Volvo
    Trucks, Daimler Truck, etc.), apply the counterparty-disclosure
    test hard. A material series-production lidar contract with a Tier-1
    OEM is material to the OEM and should be findable in their 10-K /
    20-F or 8-K.

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
        ticker="LAZR", cik_override="0001758057",
        name="Luminar Technologies, Inc.",
        notes="Lidar OEM with heavy Tier-1 OEM-design-win narrative "
              "(Volvo, Mercedes-Benz, Polestar, allegedly others). Founded "
              "by Austin Russell; de-SPAC 2020 via Gores Metropoulos. Long "
              "history of pushing SOP timelines right."),
    CohortMember(
        ticker="AEVA",
        name="Aeva Technologies, Inc.",
        notes="FMCW (frequency-modulated continuous-wave) lidar pure-play. "
              "Founded by ex-Apple lidar engineers. Porsche / Daimler / "
              "Plus.ai partnership narrative. De-SPAC 2021 via InterPrivate "
              "Acquisition."),
    CohortMember(
        ticker="OUST",
        name="Ouster, Inc.",
        notes="Digital flash lidar; merged with Velodyne 2023. Broadest "
              "claimed customer base in lidar (industrial, smart-infrastructure, "
              "robotics, automotive). Has actual revenue but mix is "
              "industrial/robotics, not automotive series production."),
    CohortMember(
        ticker="INVZ",
        name="Innoviz Technologies Ltd.",
        notes="Israeli lidar pure-play; foreign filer (20-F). Historic BMW "
              "iX design-win (2018) is the centerpiece claim. Recent "
              "Volkswagen / CARIAD selection claim (2022). De-SPAC 2021 "
              "via Collective Growth Corp."),
    CohortMember(
        ticker="MVIS",
        name="MicroVision, Inc.",
        notes="MEMS-scanning lidar; pivoted multiple times (HUD, AR display, "
              "now automotive lidar). Long history of imminent-deal "
              "announcements without conversion to series production. "
              "Persistent short-target. MOSAIK perception software pivot "
              "narrative since 2024."),
]


COHORT_CONTEXT = (
    "Automotive lidar pure-play / ADAS sensor supplier. Counterparties are "
    "Tier-1 ADAS suppliers (Aptiv, Magna, Mobileye, Visteon, Continental, "
    "ZF, Bosch, Denso), automotive OEMs (Volvo, Mercedes-Benz, BMW, "
    "Volkswagen / CARIAD, Ford, GM, Toyota, Honda, Stellantis, Polestar, "
    "Rivian, Lucid), autonomous-trucking / robotaxi platforms (Aurora "
    "Innovation, Waymo / Alphabet, Plus.ai, Kodiak Robotics, Gatik, "
    "Embark — defunct, TuSimple — China), and silicon partners (Nvidia, "
    "Qualcomm, Intel). Claims typically reference: named OEM design-wins, "
    "platform names (BMW iX, Mercedes EQS / EQE, Volvo EX90, Polestar 3, "
    "Volkswagen Trinity / CARIAD), Start-of-Production (SOP) dates, "
    "annualized unit-volume forecasts, FMCW vs ToF technology claims, "
    "and integration with named ADAS / autonomous platforms.\n\n"
    "Apply Calibration Heuristic 3 (planned vs operational) WITH EXTRA "
    "WEIGHT. Lidar design-wins move through stages: RFQ → selection / "
    "nomination → design-win awarded → A-sample / B-sample / C-sample → "
    "tooling complete → Start-of-Production (SOP) → series production at "
    "volume. Each stage is a different claim with a different M-side "
    "cross-check; conflating them is the central evasion pattern in "
    "this vertical.\n\n"
    "Apply Layer 3 Rule 7 (counterparty-disclosure threshold): if the "
    "lidar player claims a SERIES-PRODUCTION contract with a Tier-1 OEM "
    "(Volvo, Mercedes, BMW, Volkswagen, Ford, GM, Toyota, Polestar), "
    "that contract is material to the OEM and should appear in the OEM's "
    "10-K / 20-F or in 8-K disclosure if material. Absence of any "
    "counterparty mention while the lidar player claims headline "
    "OEM-design-win revenue is a HARD CONTRADICTION → RED_FLAG_NEGATIVE."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Automotive OEMs — US-listed
    "Ford Motor (F)":              "0000037996",
    "General Motors (GM)":         "0001467858",
    "Stellantis NV (STLA)":        "0001605484",
    "Tesla (TSLA)":                "0001318605",
    "Rivian (RIVN)":               "0001874178",
    "Lucid Group (LCID)":          "0001811210",
    "Polestar (PSNY)":             "0001884082",
    "Toyota Motor (TM, 20-F)":     "0001094517",
    "Honda Motor (HMC, 20-F)":     "0000715153",
    # Tier-1 ADAS suppliers
    "Aptiv (APTV)":                "0001521332",
    "Magna International (MGA)":   "0000749098",
    "Visteon (VC)":                "0001111335",
    "Mobileye Global (MBLY)":      "0001910139",
    # Silicon / compute partners
    "Nvidia (NVDA)":               "0001045810",
    "Qualcomm (QCOM)":             "0000804328",
    "Intel (INTC)":                "0000050863",
    # Autonomous / robotaxi platforms (counterparty for non-passenger-car claims)
    "Aurora Innovation (AUR)":     "0001828108",
    "Alphabet (Waymo parent)":     "0001652044",
    # Trucking customers (relevant for OUST industrial/trucking claims, AEVA Plus.ai)
    "Schneider National (SNDR)":   "0001692063",
    "Knight-Swift (KNX)":          "0001492691",
    "J.B. Hunt (JBHT)":            "0000728535",
}


CUTOFF = "2026-05-16"
