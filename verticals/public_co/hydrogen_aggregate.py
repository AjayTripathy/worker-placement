"""Aggregate the hydrogen-cohort subagent outputs."""
from __future__ import annotations

from pathlib import Path

from ._cohort_report import build_matrix, write_report
from .hydrogen_cohort import COHORT, CUTOFF

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_hydrogen_cohort"


METHODOLOGY = (
    "Seven US-listed hydrogen / fuel-cell pure-plays + industrial-gas "
    "controls: PLUG (PEM electrolyzer + fuel cell), BE (SOFC), BLDP "
    "(PEM transportation/stationary — Canadian 20-F filer), FCEL "
    "(carbonate / SOFC), HYZN (FCEV trucks), LIN (Linde — control), "
    "APD (Air Products — control). Each ticker analyzed by an "
    "isolated, **blinded** Claude Code subagent with no outcome labels, "
    "no WebSearch / WebFetch access, no shared context with other "
    "tickers. Subagent workflow includes checkpointing: input.json "
    "written immediately after extraction; scores.json rewritten "
    "per-claim.\n\n"
    "Hydrogen-specific calibration emphasis: **announced-vs-operating "
    "capacity stage ladder** (Heuristic 9). H2 names routinely conflate "
    "headline GW electrolyzer capacity numbers with what's actually "
    "operating; the financial-statement notes carry the truth.\n\n"
    "Forward-bet emission uses the shared v3 emitter "
    "(`forward_bet_emission.py`): composite >= 0.6 AND "
    "discovery_advantage_tier IN {HIGH, MED}. Crowded shorts are "
    "suppressed."
)


NOT_THIS = (
    "- **Not a fraud accusation.** RED_FLAG_NEGATIVE means the filing "
    "claim diverges from independent registry evidence at the cutoff.\n"
    "- **Not a trade recommendation.** Hydrogen pure-plays are mostly "
    "micro/small-cap; shortability is variable.\n"
    "- **Not pre-registered.** Commit this report's hash to git for "
    "honest forward-bet bookkeeping.\n"
)


DEBT = (
    "- **Foreign-issuer / Asian-OEM counterparty coverage is partial** "
    "(Korea Hydro for FCEL, SK Group for Plug, Hyundai/Toyota for BLDP). "
    "Counterparty-disclosure cross-check for these names is partial.\n"
    "- **EPA FRS connector usefulness varies** — H2 production facilities "
    "ARE EPA-regulated, but many hydrogen claims reference non-US "
    "facilities (NEOM, Geismar LA shared by APD, Sundance UT, etc.) "
    "where FRS scope partially applies.\n"
)


def main():
    matrix = build_matrix(COHORT, LOCAL)
    write_report(
        matrix=matrix,
        cutoff=CUTOFF,
        out_dir=OUT,
        title="Hydrogen / Fuel-Cell Cohort — Blinded Forward-Test Predictions (v1)",
        methodology=METHODOLOGY,
        not_this=NOT_THIS,
        debt=DEBT,
    )


if __name__ == "__main__":
    main()
