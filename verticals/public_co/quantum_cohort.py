"""
Quantum computing cohort — Signal OS HELD-OUT blinded forward test.

This is the cross-cohort calibration validation: the framework's scoring
heuristics (in defense/lidar/nuclear_subagent_prompt.py) were authored
after observing eVTOL, then defense-tech, then lidar, then nuclear
cohorts. Per TECH_DEBT.md "Calibration heuristics tuned on a single
cohort are contaminated," there's a real risk those heuristics carry
hindsight from previous cohorts even though the subagent firewall
preserves outcome blinding within each cohort.

Quantum is a deliberately held-out cohort for two reasons:
  1. The 7 calibration heuristics in the prompt templates were not
     informed by any quantum-cohort outcome (no prior quantum cohort
     has been run in this repo).
  2. Quantum-computing pure-plays share the Truth_signal characteristics
     that have driven the previous cohorts' interesting findings:
     hyped pre-revenue or early-revenue names, government /
     national-lab partnership claims, hyperscaler PPA-style
     partnership narratives, complex / buried disclosure that
     requires careful reading.

5 names:
  - RGTI (Rigetti Computing)        — superconducting qubits; QPU
                                      via cloud + AFRL contract
                                      narrative; de-SPAC 2022.
  - IONQ (IonQ Inc.)                — trapped-ion; largest market cap
                                      in the cohort; AWS/Azure/GCP
                                      cloud distribution claims;
                                      $1.1B DoD-RFP narrative.
  - QBTS (D-Wave Quantum)           — annealing (separate paradigm);
                                      claims commercial revenue
                                      (vs all others pre-revenue);
                                      de-SPAC 2022.
  - ARQQ (Arqit Quantum)            — quantum-encryption / QKD,
                                      not gate computing; UK
                                      foreign filer (20-F); has
                                      a long history of customer-
                                      claim restatements.
  - QUBT (Quantum Computing Inc.)   — photonic qubits + recent
                                      acquirer of Luminar's LSI
                                      semiconductor subsidiary
                                      (Feb 2026, see LAZR cohort).
                                      Major balance-sheet pivot in
                                      progress.

Uniform cutoff: 2026-05-16.

QUBT cross-cohort note: QUBT appears in the lidar cohort's LAZR-2
claim as the $110M LSI acquirer. The subagent for QUBT should
extract claims independently from QUBT's own filings — the LSI
acquisition is a recent material event that QUBT itself discloses,
so the framework's evaluation will naturally encounter it.
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
        ticker="RGTI",
        name="Rigetti Computing, Inc.",
        notes="Superconducting-qubit gate computing. De-SPAC 2022 via "
              "Supernova Partners II. QPU access via Rigetti Quantum Cloud "
              "Services. Major narrative claims: AFRL contract (Air Force "
              "Research Laboratory), DARPA programs, Fab-1 in Fremont CA, "
              "84-qubit Ankaa system + 336-qubit Lyra roadmap."),
    CohortMember(
        ticker="IONQ",
        name="IonQ, Inc.",
        notes="Trapped-ion quantum computing. Largest quantum pure-play by "
              "market cap. De-SPAC 2021 via dMY Technology Group III. "
              "Cloud distribution via AWS Braket, Azure Quantum, Google "
              "Cloud. Major narrative claims: $1.1B in cumulative bookings "
              "(per company), DoD contracts (AFRL, ARL), Forte / Tempo "
              "systems, recent IDQ + Qubitekk acquisitions in QKD."),
    CohortMember(
        ticker="QBTS",
        name="D-Wave Quantum Inc.",
        notes="Quantum annealing (different paradigm — solves QUBO problems, "
              "not gate-circuit). De-SPAC 2022 via DPCM Capital. Claims to "
              "have actual commercial revenue (vs other names pre-revenue). "
              "Major narrative claims: Advantage2 system, hybrid solver "
              "service, Mastercard / Davidson Technologies / NTT DOCOMO "
              "customer references."),
    CohortMember(
        ticker="ARQQ",
        name="Arqit Quantum Inc.",
        notes="Quantum-encryption / QKD (Quantum Key Distribution) — NOT "
              "gate-model quantum computing. UK-domiciled, foreign private "
              "issuer (20-F filer). De-SPAC 2021 via Centricus Acquisition. "
              "Long history of revenue-recognition issues; previously "
              "restated 2021/2022 financials. Major narrative claims: "
              "SKA (Symmetric Key Agreement) platform, BT / Sumitomo / "
              "Juniper / Verizon partnerships, defense / government "
              "customers."),
    CohortMember(
        ticker="QUBT",
        name="Quantum Computing Inc.",
        notes="Photonic-qubit + thin-film lithium niobate (TFLN) approach. "
              "Recently completed $110M acquisition of Luminar Semiconductor "
              "Inc. (LSI) from Luminar's bankruptcy estate (Feb 2026). "
              "Major narrative claims: Dirac-3 EQC system, NASA contract "
              "for imaging applications, photonic chip foundry build-out "
              "in Arizona. Significant balance-sheet pivot in progress "
              "from the LSI acquisition."),
]


COHORT_CONTEXT = (
    "Quantum computing pure-play (gate-model superconducting / trapped-ion "
    "/ photonic) or QKD encryption. Counterparties span hyperscaler cloud "
    "platforms (AWS / Azure / GCP) that distribute QPU access, US national "
    "labs (AFRL, ARL, ORNL, LANL, INL, Sandia, LBNL, Argonne, NIST), DoD "
    "research agencies (DARPA, IARPA), defense primes (LMT, NOC, RTX), "
    "and financial-services or telecom customers (JPM, Goldman, BT, "
    "Verizon, Sumitomo for QKD). Claims typically reference: qubit-count "
    "milestones (e.g. 84-qubit Ankaa, Advantage2, Forte), cloud-platform "
    "availability (AWS Braket / Azure Quantum / Google Cloud), named "
    "government contracts (AFRL Air Force, ARL Army, DARPA programs), "
    "named commercial-customer engagements (Mastercard, BT), and "
    "technology-roadmap milestones (e.g. logical qubit counts, error-"
    "correction thresholds).\n\n"
    "Apply Calibration Heuristic 3 (planned vs operational) WITH EXTRA "
    "WEIGHT. Quantum hardware claims move through stages: "
    "design → fabrication → bring-up → noise characterization → cloud "
    "availability → benchmarked operation at claimed qubit count. "
    "Headline qubit counts are often physical-qubit counts (not "
    "logical / error-corrected qubits) and may refer to fabricated-but-"
    "not-benchmarked devices. Each stage is a different claim with a "
    "different M-side cross-check.\n\n"
    "Apply Layer 3 Rule 7 (counterparty-disclosure threshold): if the "
    "quantum company claims a contract or commercial deployment with a "
    "hyperscaler (AWS / Microsoft / Google), Tier-1 financial (JPM / "
    "Goldman / Mastercard), defense prime, or national lab, that "
    "relationship is material to the counterparty (in $-amount or "
    "PR-value) and should appear in their 10-K / 20-F or USAspending. "
    "Absence while the quantum company claims headline customer "
    "revenue is a HARD CONTRADICTION → RED_FLAG_NEGATIVE.\n\n"
    "Specific Quantum-vertical risk: 'quantum supremacy' or 'quantum "
    "advantage' marketing language is research-paper jargon that does "
    "not correspond to any commercial deployment milestone. Same for "
    "'world's largest' (qubit count) — the metric changes monthly and "
    "absolute counts vary with how qubits are counted (physical vs "
    "logical, online vs total fabricated)."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Hyperscalers (cloud QPU distribution)
    "Amazon (AMZN, AWS Braket)":      "0001018724",
    "Microsoft (MSFT, Azure Quantum)":"0000789019",
    "Alphabet (GOOGL, Google Cloud)": "0001652044",
    "IBM (IBM Quantum)":              "0000051143",
    "HPE (HPE)":                      "0001645590",
    "Oracle (ORCL)":                  "0001341439",
    # Silicon / compute partners
    "Nvidia (NVDA)":                  "0001045810",
    "Intel (INTC)":                   "0000050863",
    # Defense primes (named DoD / DARPA quantum customers)
    "Lockheed Martin (LMT)":          "0000936468",
    "Northrop Grumman (NOC)":         "0001133421",
    "Raytheon Technologies (RTX)":    "0000101829",
    # Financial-services customers
    "JPMorgan Chase (JPM)":           "0000019617",
    "Goldman Sachs (GS)":             "0000886982",
    "Bank of America (BAC)":          "0000070858",
}


CUTOFF = "2026-05-16"
