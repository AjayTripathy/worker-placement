"""Aggregate the solid-state battery cohort subagent outputs."""
from __future__ import annotations

from pathlib import Path

from ._cohort_report import build_matrix, write_report
from .ssbattery_cohort import COHORT, CUTOFF

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_ssbattery_cohort"


METHODOLOGY = (
    "Seven names spanning solid-state / next-gen battery pure-plays and "
    "lithium-supply controls: QS / SES / SLDP / MVST / ENVX (battery) "
    "+ ALB / LAC (lithium supply controls). Each ticker analyzed by an "
    "isolated, **blinded** Claude Code subagent with no outcome labels, "
    "no WebSearch / WebFetch access, no shared context. Subagent "
    "workflow includes checkpointing.\n\n"
    "Battery-specific calibration emphasis: **energy-density / "
    "cycle-life without test conditions** (Heuristic 9). Battery names "
    "routinely cite Wh/kg or cycle-count headlines without disclosing "
    "rate, temperature, or depth-of-discharge — the conditions that "
    "decide whether the number is lab-scale or production-realistic.\n\n"
    "**Foreign-OEM counterparty coverage:** most major battery customer "
    "OEMs (VW, BMW, Mercedes, Hyundai, Toyota) file foreign annual "
    "reports (20-F or none); EDGAR coverage is partial. UNVERIFIABLE "
    "rather than false-clean for these counterparty-disclosure tests.\n\n"
    "Forward-bet emission uses the shared v2 emitter."
)


NOT_THIS = (
    "- **Not a fraud accusation.** Battery JDAs are real research and "
    "development relationships even when they don't produce series "
    "production by the originally claimed SOP year.\n"
    "- **Foreign-OEM disclosure gap.** Counterparty-disclosure checks "
    "for VW/BMW/Mercedes/Hyundai/Toyota are partial because their "
    "primary annual reports are off-EDGAR.\n"
    "- **Not pre-registered.** Commit this report's hash to git.\n"
)


DEBT = (
    "- **Foreign-OEM counterparty disclosure gap** is the largest "
    "coverage limit. A connector for foreign-OEM annual reports "
    "(Volkswagen Group Annual Report Germany, BMW Annual Report, "
    "Mercedes-Benz Group Annual Report, Hyundai Motor Annual Report, "
    "Toyota Motor Annual Report) would close it.\n"
    "- **Battery-cell test-condition normalization** is currently "
    "manual; a structured registry of independent battery-cell test "
    "results (e.g. DOE/INL benchmarking publications) would let the "
    "framework cross-check energy-density claims directly.\n"
)


def main():
    matrix = build_matrix(COHORT, LOCAL)
    write_report(
        matrix=matrix,
        cutoff=CUTOFF,
        out_dir=OUT,
        title="Solid-State / Next-Gen Battery Cohort — Blinded Forward-Test Predictions (v1)",
        methodology=METHODOLOGY,
        not_this=NOT_THIS,
        debt=DEBT,
    )


if __name__ == "__main__":
    main()
