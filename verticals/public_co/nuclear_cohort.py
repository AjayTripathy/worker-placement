"""
Advanced nuclear / SMR cohort — Signal OS blinded forward test.

Cohort selection criteria (per `feedback_truth_vs_alpha.md`):
  - HIGH Truth_signal potential: pre-revenue or recently-revenue companies
    with bold commercial-deployment timelines; M-sources available
    (USAspending DOE contracts, USPTO patents, EDGAR FTS counterparty);
  - HIGH Discovery_advantage potential: small-cap names with thin sell-side
    coverage, modest short interest (no Hindenburg-style report yet),
    complex / buried disclosure that requires careful reading.

5 names: 3 speculative (OKLO/NNE/ASPI) + 2 controls (LEU/BWXT).

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
        ticker="OKLO",
        name="Oklo Inc.",
        notes="Pre-revenue microreactor pure-play (Aurora design, 75 MWe). "
              "Backed by Sam Altman. Lots of customer LOI / power-purchase "
              "claims to data center / DoD. NRC combined license submission "
              "rejected once already (Jan 2022)."),
    CohortMember(
        ticker="NNE",
        name="NANO Nuclear Energy Inc.",
        notes="Pre-revenue microreactor R&D-stage; multiple subsidiary "
              "acquisitions (Altavista Strategic Partners, LANL spin-out IP). "
              "IPO 2024. Aggressive capital raises."),
    CohortMember(
        ticker="ASPI",
        name="ASP Isotopes Inc.",
        notes="Enriched isotope production. Some real fluorinated-medical-isotope "
              "business; pivoted heavily to HALEU narrative for SMR fuel."),
    CohortMember(
        ticker="LEU",
        name="Centrus Energy Corp",
        notes="**CONTROL** — established uranium enrichment company. Has actual "
              "DOE HALEU production contract at Piketon OH. Real revenue."),
    CohortMember(
        ticker="BWXT",
        name="BWX Technologies, Inc.",
        notes="**CONTROL** — established naval nuclear / SMR enabler. Builds USN "
              "reactors. Real revenue."),
]


COHORT_CONTEXT = (
    "Advanced nuclear / SMR pure-play or enabler. Counterparties: NRC (for "
    "licensing milestones — Combined Operating License COL vs Construction "
    "Permit CP vs Early Site Permit ESP), DOE (R&D contracts via Office of "
    "Nuclear Energy, Idaho National Laboratory INL, ARPA-E, ARDP, NRIC), "
    "utility / strategic / data-center partners (NextEra Energy NEE, "
    "American Electric Power AEP, Duke Energy DUK, Constellation CEG, "
    "Vistra VST, Talen TLN, Curtiss-Wright CW, GE Vernova GEV, Westinghouse, "
    "Microsoft MSFT, Equinix EQIX, Oracle ORCL, AMAZON AMZN). Claims "
    "typically reference: NRC application stage, DOE contract awards (HALEU, "
    "ARDP, NRIC), customer announcements ('we will provide X MW to data "
    "center Y by 20Z'), pilot reactor timelines.\n\n"
    "Apply Layer 3 Rule 7 (counterparty-disclosure threshold): for a small "
    "nuclear pure-play, a real PPA with a Tier-1 utility or data center "
    "would be material to the counterparty AND would appear in their 10-K. "
    "Apply Calibration Heuristic 3 (planned vs operational) WITH EXTRA "
    "WEIGHT — nuclear timelines slip routinely; 'planned' vs 'submitted to "
    "NRC' vs 'NRC docketed' vs 'NRC accepted' vs 'license granted' are very "
    "different stages."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Utilities / power
    "NextEra Energy (NEE)":       "0000753308",
    "AEP (American Electric Power)": "0000004904",
    "Duke Energy (DUK)":          "0001326160",
    "Constellation Energy (CEG)": "0001868275",
    "Vistra Corp (VST)":          "0001692819",
    "Talen Energy (TLN)":         "0001381668",
    "Exelon (EXC)":               "0001109357",
    "Southern Co (SO)":           "0000092122",
    "Dominion Energy (D)":        "0000715957",
    # Nuclear ecosystem
    "Curtiss-Wright (CW)":        "0000026324",
    "GE Vernova (GEV)":           "0002012970",
    "BWX Technologies (BWXT)":    "0001486957",
    # Hyperscaler customers (named as nuclear offtake partners)
    "Microsoft (MSFT)":           "0000789019",
    "Amazon (AMZN)":              "0001018724",
    "Oracle (ORCL)":              "0001341439",
    "Equinix (EQIX)":             "0001101239",
    "Digital Realty (DLR)":       "0001297996",
    "Alphabet (GOOG)":            "0001652044",
    "Meta Platforms (META)":      "0001326801",
}


CUTOFF = "2026-05-16"
