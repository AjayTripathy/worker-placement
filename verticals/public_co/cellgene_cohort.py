"""
Cell/gene therapy biotech cohort — Signal OS blinded forward test.

5 speculative names (SAVA / CRSP / BEAM / EDIT / NTLA) + 2 mature
commercial-stage controls (REGN / VRTX). Strong fit for the framework:
clinical_trials.gov and openFDA are already plumbed; biotech disclosure
is heavy on pipeline-milestone claims that registries can adjudicate.

Heuristic emphasis: clinical-trial-stage discipline — preclinical vs
IND-cleared vs Phase 1 vs Phase 2 vs Phase 3 vs filed-with-FDA vs
approved are six distinct claims, each with a different registry
cross-check. Conflating them in marketing tier while the financial-
statement notes disclose a different stage is the central evasion
pattern.

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
        ticker="SAVA", cik_override="0001069530",
        name="Cassava Sciences, Inc.",
        notes="Simufilam (PTI-125) for Alzheimer's. Long history of "
              "research-paper-integrity allegations, citizens' petitions "
              "to the FDA, and stock-promotion controversies. Phase 3 "
              "data readout history."),
    CohortMember(
        ticker="CRSP",
        name="CRISPR Therapeutics AG",
        notes="ex-vivo CRISPR-Cas9 gene editing. Casgevy (exa-cel) for "
              "sickle cell + beta-thalassemia is the first FDA-approved "
              "CRISPR therapy (Dec 2023). Partnership with Vertex. "
              "Swiss-domiciled, files 20-F."),
    CohortMember(
        ticker="BEAM",
        name="Beam Therapeutics Inc.",
        notes="Base-editing platform — single-nucleotide DNA edits. "
              "Pre-revenue. Pipeline focused on hemoglobinopathies, "
              "T-cell therapy. Pfizer collaboration history."),
    CohortMember(
        ticker="EDIT",
        name="Editas Medicine, Inc.",
        notes="CRISPR gene-editing therapeutics. EDIT-301 (renamed "
              "reni-cel) for sickle cell. Pre-revenue. Multiple "
              "pipeline pivots."),
    CohortMember(
        ticker="NTLA",
        name="Intellia Therapeutics, Inc.",
        notes="In-vivo CRISPR via LNP delivery. NTLA-2001 for ATTR; "
              "NTLA-2002 for HAE. Regeneron partnership. Pre-revenue "
              "but pipeline is more clinically validated than peers."),
    CohortMember(
        ticker="REGN",
        name="Regeneron Pharmaceuticals, Inc.",
        notes="**CONTROL** — established commercial biotech. Eylea, "
              "Dupixent, Praluent, Libtayo. Real revenue, mature "
              "pipeline disclosure. Expected to score clean."),
    CohortMember(
        ticker="VRTX",
        name="Vertex Pharmaceuticals Incorporated",
        notes="**CONTROL** — established commercial biotech. Trikafta "
              "(CF franchise), Casgevy (with CRSP). Real revenue, "
              "approved-product portfolio. Expected to score clean."),
]


COHORT_CONTEXT = (
    "Cell / gene therapy or CRISPR-based therapeutic biotech, or "
    "mature commercial-stage biotech control. Counterparties span "
    "partnership pharmacos (Pfizer PFE, Regeneron REGN, Vertex VRTX, "
    "Bayer, Sanofi SNY, AstraZeneca AZN — many foreign filers), CROs "
    "(Quintiles/IQVIA IQV, Charles River CRL, Syneos SYNH), CDMOs "
    "(Lonza, Catalent), and US regulators (FDA via openFDA; "
    "ClinicalTrials.gov for trial registration).\n\n"
    "Claims typically reference: trial-phase status, pivotal-trial "
    "endpoints, dosing milestones, BLA / IND / Fast Track / "
    "Breakthrough Designation status, named patient counts, "
    "partnership milestone payments, manufacturing-capacity claims "
    "(viral vector, LNP, cell-therapy bioreactors).\n\n"
    "Apply Calibration Heuristic 3 (planned vs operational) WITH EXTRA "
    "WEIGHT. Trial-phase ladder is: preclinical -> IND-cleared -> "
    "Phase 1 -> Phase 2 -> Phase 3 -> filed-with-FDA -> approved. "
    "Each stage has a distinct ClinicalTrials.gov registration and a "
    "distinct disclosure threshold. Conflating Phase 2a interim data "
    "with Phase 3 pivotal status is the central evasion pattern.\n\n"
    "Apply Layer 3 Rule 7 (counterparty-disclosure threshold): if a "
    "company claims a milestone-bearing partnership with REGN/PFE/"
    "VRTX/BAYRY at material $-amount, that should appear in the "
    "counterparty's 10-K/20-F R&D commentary. Absence is a HARD "
    "CONTRADICTION."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Big pharma partners
    "Pfizer (PFE)":               "0000078003",
    "Regeneron (REGN)":           "0000872589",
    "Vertex (VRTX)":              "0000875320",
    "Eli Lilly (LLY)":            "0000059478",
    "Merck (MRK)":                "0000310158",
    "Bristol-Myers Squibb (BMY)": "0000014272",
    # CROs / CDMOs (real revenue partners)
    "IQVIA (IQV)":                "0001478242",
    "Charles River (CRL)":        "0001100682",
    "Catalent (CTLT)":            "0001596783",
}


CUTOFF = "2026-05-16"
