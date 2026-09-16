"""
Defense-tech / military-drone cohort definition + runner.

Forward test of the Signal OS framework on 5 names:
  - RCAT (Red Cat Holdings) — military drones
  - UMAC (Unusual Machines) — drone components
  - ONDS (Ondas Inc.) — drone / rail comms
  - AIRO (AIRO Group Holdings) — recent SPAC, UAS / military
  - KTOS (Kratos Defense & Security Solutions) — established mid-cap tactical drones

Uniform cutoff: 2026-05-16.

Subagent firewall: each ticker is scored in isolation by a blinded subagent
that receives only ticker + CIK + cutoff + cohort context + recipe library.
Subagent forbids WebSearch / WebFetch / training-data hindsight.
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
        ticker="RCAT",
        name="Red Cat Holdings, Inc.",
        notes="Military drone OEM; Teal Drones subsidiary. Heavy DoD/SOCOM narrative; "
              "Short Range Reconnaissance program key claim."),
    CohortMember(
        ticker="UMAC",
        name="Unusual Machines, Inc.",
        notes="Drone components (motors, FCs); pivoted from consumer drone hobby; "
              "Blue UAS NDAA-compliance narrative; recent IPO."),
    CohortMember(
        ticker="ONDS",
        name="Ondas Inc.",
        notes="Drone-grade industrial wireless + Airobotics subsidiary; rail and "
              "defense exposure; pre-revenue at scale."),
    CohortMember(
        ticker="AIRO",
        name="AIRO Group Holdings, Inc.",
        notes="Recent SPAC; consolidated 4 acquisitions (Aspen Avionics, Coastal "
              "Defense, Sky Defense, Agile Defense Systems); UAS / defense / training."),
    CohortMember(
        ticker="KTOS",
        name="Kratos Defense & Security Solutions, Inc.",
        notes="**CONTROL** — established mid-cap defense. XQ-58 Valkyrie, Mako, "
              "BQM-167; satellite, training, microwave. Real DoD revenue."),
]


COHORT_CONTEXT = (
    "Defense-tech / military-drone OEM or component supplier. Counterparties "
    "are US DoD (Air Force, Army, Navy, Marines, SOCOM), defense primes "
    "(Lockheed Martin LMT, Northrop Grumman NOC, Raytheon RTX, General "
    "Dynamics GD, L3Harris LHX), DARPA, foreign militaries (UK MOD, "
    "Ukraine AFU). Claims typically reference: named DoD programs (Short "
    "Range Reconnaissance, Replicator, Project Maven), specific contract "
    "vehicles (OTAs, IDIQs), Blue UAS / NDAA-compliance status, anchor "
    "platforms (XQ-58 Valkyrie, MQ-58, Black Hornet). Patents: USPTO ODP. "
    "DoD contracts: USAspending.gov (recipient name search; filter to "
    "Department of Defense). Apply Layer 3 Rule 7 (counterparty-disclosure "
    "threshold) — DoD is the counterparty for all of these; absence of a "
    "claimed contract in USAspending IS a hard contradiction."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Defense primes
    "Lockheed Martin (LMT)":      "0000936468",
    "Northrop Grumman (NOC)":     "0001133421",
    "Raytheon Technologies (RTX)":"0000101829",
    "General Dynamics (GD)":      "0000040533",
    "L3Harris (LHX)":             "0000202058",
    "Boeing (BA)":                "0000012927",
    "Huntington Ingalls (HII)":   "0001501585",
    "Textron (TXT)":              "0000217346",
    # Strategic / industrial
    "Honeywell (HON)":            "0000773840",
    "GE Aerospace (GE)":          "0000040545",
    "Booz Allen (BAH)":           "0001443669",
    "Leidos (LDOS)":              "0001336920",
    "CACI (CACI)":                "0000017843",
    # Test/communications counterparties
    "Iridium (IRDM)":             "0001418819",
    "Viasat (VSAT)":              "0000797721",
}


CUTOFF = "2026-05-16"
