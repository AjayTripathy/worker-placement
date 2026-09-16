"""Aggregate the AI-DC crypto-pivot cohort subagent outputs."""
from __future__ import annotations

from pathlib import Path

from ._cohort_report import build_matrix, write_report
from .dcpivot_cohort import COHORT, CUTOFF

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_dcpivot_cohort"


METHODOLOGY = (
    "Seven names spanning AI-DC crypto-pivots and mature DC-REIT "
    "controls: CIFR / IREN / APLD / CORZ / BTDR (crypto-miner pivots) "
    "+ EQIX / DLR (controls). Each ticker analyzed by an isolated, "
    "**blinded** Claude Code subagent with no outcome labels, no "
    "WebSearch / WebFetch access, no shared context. Subagent workflow "
    "includes checkpointing.\n\n"
    "AI-DC-specific calibration emphasis: **TCV-vs-current-period-"
    "revenue conflation** (Heuristic 9). AI-DC pivot names routinely "
    "headline multi-billion-dollar contract values that span 10-15 years "
    "while only a small fraction is currently energized and "
    "revenue-bearing. The hyperscaler counterparty-disclosure threshold "
    "(Rule 7) is the killer cross-check — hyperscaler 10-Ks discuss "
    "data-center capex commitments and should name material partners "
    "at scale.\n\n"
    "**CoreWeave exception:** CoreWeave is private and won't appear in "
    "EDGAR; CoreWeave-named contracts are UNVERIFIABLE on the "
    "counterparty axis. APLD and CORZ have major CoreWeave deal claims "
    "that fall into this coverage gap.\n\n"
    "Forward-bet emission uses the shared v3 emitter "
    "(`forward_bet_emission.py`): composite >= 0.6 AND "
    "discovery_advantage_tier IN {HIGH, MED}."
)


NOT_THIS = (
    "- **Not a fraud accusation.** RED_FLAG_NEGATIVE means filings "
    "diverge from registries at the cutoff.\n"
    "- **CoreWeave gap.** CoreWeave is private; deals with it are "
    "structurally UNVERIFIABLE in EDGAR. Coverage limitation, not "
    "verdict.\n"
    "- **Not pre-registered.** Commit this report's hash to git.\n"
)


DEBT = (
    "- **CoreWeave UNVERIFIABLE gap** is the largest coverage gap for "
    "this cohort. A connector for CoreWeave's senior-secured-note "
    "indenture filings (CoreWeave issued $7.5B in senior secured notes "
    "in 2024-2025 across multiple deals) would partially close this — "
    "CoreWeave's hosting-customer obligations would appear in those "
    "indentures.\n"
    "- **Utility-side grid-interconnect filings** (utility-regulator "
    "filings at state PUCs for MW-scale interconnect) are off-EDGAR; "
    "verifying claimed grid interconnect requires per-state PUC scraping.\n"
)


def main():
    matrix = build_matrix(COHORT, LOCAL)
    write_report(
        matrix=matrix,
        cutoff=CUTOFF,
        out_dir=OUT,
        title="AI Data-Center / Crypto-Pivot Cohort — Blinded Forward-Test Predictions (v1)",
        methodology=METHODOLOGY,
        not_this=NOT_THIS,
        debt=DEBT,
    )


if __name__ == "__main__":
    main()
