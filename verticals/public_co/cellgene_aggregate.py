"""Aggregate the cell/gene therapy cohort subagent outputs."""
from __future__ import annotations

from pathlib import Path

from ._cohort_report import build_matrix, write_report
from .cellgene_cohort import COHORT, CUTOFF

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_cellgene_cohort"


METHODOLOGY = (
    "Seven names spanning cell/gene-therapy and CRISPR pure-plays "
    "(SAVA Cassava Sciences, CRSP CRISPR Therapeutics Swiss 20-F, "
    "BEAM Beam Therapeutics base-editing, EDIT Editas Medicine, "
    "NTLA Intellia in-vivo CRISPR) and mature commercial-biotech "
    "controls (REGN Regeneron, VRTX Vertex). Each ticker analyzed "
    "by an isolated, **blinded** Claude Code subagent with no outcome "
    "labels, no WebSearch / WebFetch, no shared context. Subagent "
    "workflow includes checkpointing.\n\n"
    "Biotech-specific calibration emphasis: **trial-phase ladder** "
    "discipline (Heuristic 9). preclinical -> IND -> Phase 1 -> "
    "Phase 2 -> Phase 3 -> filed -> approved are six distinct "
    "claims with distinct ClinicalTrials.gov registrations. "
    "Conflating interim Phase 2a with pivotal Phase 3 status is "
    "the central evasion pattern.\n\n"
    "**Killer M-source for this cohort:** clinical_trials.gov is "
    "directly plumbed; pipeline-asset claims are verifiable at the "
    "NCT-number level. openFDA cross-checks approval claims.\n\n"
    "Forward-bet emission uses the shared v2 emitter."
)


NOT_THIS = (
    "- **Not a fraud accusation.** Biotech pipelines fail for many "
    "legitimate reasons unrelated to disclosure quality.\n"
    "- **ClinicalTrials.gov coverage is non-exhaustive** for "
    "preclinical or foreign-only trials.\n"
    "- **Not pre-registered.** Commit this report's hash to git.\n"
)


DEBT = (
    "- **Foreign-trial coverage gap.** China-only and EMA-only trials "
    "may not appear in clinical_trials.gov.\n"
    "- **Manufacturing-capacity verification** for cell/gene therapy "
    "is partial: viral-vector and LNP CDMO capacity isn't in a single "
    "registry.\n"
)


def main():
    matrix = build_matrix(COHORT, LOCAL)
    write_report(
        matrix=matrix, cutoff=CUTOFF, out_dir=OUT,
        title="Cell/Gene Therapy Cohort — Blinded Forward-Test Predictions (v1)",
        methodology=METHODOLOGY, not_this=NOT_THIS, debt=DEBT,
    )


if __name__ == "__main__":
    main()
