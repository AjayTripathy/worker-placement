"""Aggregate the robotics / autonomous-systems cohort subagent outputs."""
from __future__ import annotations

from pathlib import Path

from ._cohort_report import build_matrix, write_report
from .robotics_cohort import COHORT, CUTOFF

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_robotics_cohort"


METHODOLOGY = (
    "Six names spanning speculative robotics / autonomous-systems "
    "pure-plays and mature robotics-adjacent controls: SYM "
    "(Symbotic warehouse automation), KSCP (Knightscope security "
    "robots), BBAI (BigBear.AI defense AI), SERV (Serve Robotics "
    "delivery) + IRBT (iRobot — control), TER (Teradyne, Universal "
    "Robots parent — control). Each ticker analyzed by an isolated, "
    "**blinded** Claude Code subagent with no outcome labels, no "
    "WebSearch / WebFetch access, no shared context. Subagent workflow "
    "includes checkpointing.\n\n"
    "Robotics-specific calibration emphasis: **pilot-vs-commercial-"
    "deployment conflation** (Heuristic 9). Robotics names routinely "
    "headline 'deployed at N customer sites' without separating "
    "pilots-as-PR from commercial-scale revenue-bearing deployments. "
    "ARR vs one-time-sale split is the cleanest cross-check.\n\n"
    "Forward-bet emission uses the shared v2 emitter."
)


NOT_THIS = (
    "- **Not a fraud accusation.** Pilot deployments are real customer "
    "engagements even when they don't convert to commercial scale.\n"
    "- **Not a trade recommendation.** Several names are micro-cap with "
    "limited borrow.\n"
    "- **Not pre-registered.** Commit this report's hash to git.\n"
)


DEBT = (
    "- **Defense-intel customer disclosure gap** for BBAI: many DoD "
    "intelligence-community customers don't disclose contractors by "
    "name in 10-Ks. USAspending covers some but classified-IC contracts "
    "are off-USAspending. Score classified-IC-customer claims as "
    "UNVERIFIABLE rather than false-clean.\n"
    "- **Walmart-related-party (SYM)** — SYM has a Greenbox Systems "
    "joint-venture structure with Walmart that creates structural "
    "related-party-revenue risk worth a dedicated cross-check.\n"
)


def main():
    matrix = build_matrix(COHORT, LOCAL)
    write_report(
        matrix=matrix,
        cutoff=CUTOFF,
        out_dir=OUT,
        title="Robotics / Autonomous-Systems Cohort — Blinded Forward-Test Predictions (v1)",
        methodology=METHODOLOGY,
        not_this=NOT_THIS,
        debt=DEBT,
    )


if __name__ == "__main__":
    main()
