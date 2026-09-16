"""Aggregate the fintech lending / BNPL cohort subagent outputs."""
from __future__ import annotations

from pathlib import Path

from ._cohort_report import build_matrix, write_report
from .fintech_cohort import COHORT, CUTOFF

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_fintech_cohort"


METHODOLOGY = (
    "Five names spanning fintech lending (UPST AI-underwriting), BNPL "
    "(AFRM), iBuying (OPEN Opendoor), neobank (SOFI), and bank control "
    "(COF Capital One). Each ticker analyzed by an isolated, "
    "**blinded** Claude Code subagent with no outcome labels, no "
    "WebSearch / WebFetch, no shared context. Subagent workflow "
    "includes checkpointing.\n\n"
    "Fintech-specific calibration emphasis: **origination-volume vs "
    "balance-sheet volume vs net revenue** (Heuristic 9). Fintech "
    "names routinely emphasize headline volume metrics that aren't "
    "balance-sheet risk; this is a disclosure-quality issue more than "
    "a fraud signal.\n\n"
    "**Cohort caveat:** the framework is built for divergence detection "
    "where M-sources are authoritative registries. Consumer-credit-"
    "quality claims don't have a clean registry analog; this cohort "
    "is expected to produce more UNVERIFIABLE than other verticals. "
    "Emissions should be rare and high-conviction.\n\n"
    "Forward-bet emission uses the shared v2 emitter."
)


NOT_THIS = (
    "- **Not a fraud accusation.** Consumer-credit cycles drive "
    "fintech results in ways the framework can't always discriminate.\n"
    "- **Consumer-experience claims** (CFPB complaints, BBB scores) "
    "are not plumbed; partial coverage.\n"
    "- **Not pre-registered.** Commit this report's hash to git.\n"
)


DEBT = (
    "- **CFPB consumer-complaint registry / FDIC call reports** are "
    "the #1 coverage gap for consumer-credit-quality claims. Both "
    "are free + structured; worth plumbing.\n"
    "- **Securitization-trust disclosures** (loan-backed ABS trustee "
    "reports) sit off-EDGAR but are public; future-cohort opportunity.\n"
)


def main():
    matrix = build_matrix(COHORT, LOCAL)
    write_report(
        matrix=matrix, cutoff=CUTOFF, out_dir=OUT,
        title="Fintech Lending / BNPL Cohort — Blinded Forward-Test Predictions (v1)",
        methodology=METHODOLOGY, not_this=NOT_THIS, debt=DEBT,
    )


if __name__ == "__main__":
    main()
