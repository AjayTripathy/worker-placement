"""Aggregate the space / satcom cohort subagent outputs."""
from __future__ import annotations

from pathlib import Path

from ._cohort_report import build_matrix, write_report
from .space_cohort import COHORT, CUTOFF

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_space_cohort"


METHODOLOGY = (
    "Six names spanning space-launch (RKLB Rocket Lab), direct-to-mobile "
    "sat (ASTS AST SpaceMobile), space-infrastructure (RDW Redwire), "
    "earth-observation (PL Planet Labs), satcom (SATS EchoStar), and "
    "mature LEO-constellation control (IRDM Iridium). Each ticker "
    "analyzed by an isolated, **blinded** Claude Code subagent with no "
    "outcome labels, no WebSearch / WebFetch, no shared context. "
    "Subagent workflow includes checkpointing.\n\n"
    "Space-specific calibration emphasis: **constellation-announced "
    "vs constellation-operational** (Heuristic 9). Sat-network claims "
    "routinely conflate test-sats, on-orbit-but-pre-commercial, and "
    "commercial-service-active. Federal-contract claims (NASA, USSF, "
    "DARPA, NOAA) are USAspending-verifiable at the program level.\n\n"
    "Forward-bet emission uses the shared v2 emitter."
)


NOT_THIS = (
    "- **Not a fraud accusation.** Space milestones slip routinely for "
    "engineering reasons.\n"
    "- **FAA launch records** aren't plumbed as an M-source; "
    "launch-cadence claims rely on counterparty disclosure.\n"
    "- **Not pre-registered.** Commit this report's hash to git.\n"
)


DEBT = (
    "- **FAA launch registry / launch-license tracking is the #1 "
    "coverage gap.** A connector would directly verify launch-"
    "cadence claims.\n"
    "- **Foreign-launch / foreign-sat-operator contracts** "
    "(ESA, JAXA, ISRO, Telesat) are off-EDGAR.\n"
)


def main():
    matrix = build_matrix(COHORT, LOCAL)
    write_report(
        matrix=matrix, cutoff=CUTOFF, out_dir=OUT,
        title="Space / Satcom Cohort — Blinded Forward-Test Predictions (v1)",
        methodology=METHODOLOGY, not_this=NOT_THIS, debt=DEBT,
    )


if __name__ == "__main__":
    main()
