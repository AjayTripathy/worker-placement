"""Aggregate the retail-distress cohort subagent outputs."""
from __future__ import annotations

from pathlib import Path

from ._cohort_report import build_matrix, write_report
from .retail_cohort import COHORT, CUTOFF

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_retail_cohort"


METHODOLOGY = (
    "Seven names spanning distressed-narrative department stores (KSS "
    "Kohl's, M Macy's, JWN Nordstrom), apparel (GPS Gap), discount "
    "post-Ch.11 (BIG Big Lots), and retail-resilient controls (TJX off-"
    "price, COST membership warehouse). Each ticker analyzed by an "
    "isolated, **blinded** Claude Code subagent with no outcome labels, "
    "no WebSearch / WebFetch, no shared context. Subagent workflow "
    "includes checkpointing.\n\n"
    "Retail-specific calibration emphasis: **comp-store-sales claim "
    "test** (Heuristic 9) + **going-concern / form-15 fingerprints** "
    "(Heuristic 10, applied hard). Retail-distress names often have "
    "multi-year transformation plans where announced milestones diverge "
    "from realized progress.\n\n"
    "**Cohort caveat:** retail-distress is slow-bleed. Even validated "
    "Truth_signals can grind sideways for years. Emissions should be "
    "paired with tighter exit rules than the default 12-month "
    "falsification window.\n\n"
    "Forward-bet emission uses the shared v2 emitter."
)


NOT_THIS = (
    "- **Not a fraud accusation.** Retail distress is structural; "
    "framework-flagged claims are disclosure-quality concerns.\n"
    "- **Wholesale-supplier counterparty disclosure is partial.** "
    "Suppliers disclose top customers; not all material relationships "
    "are surfaced in 10-K narrative.\n"
    "- **Not pre-registered.** Commit this report's hash to git.\n"
)


DEBT = (
    "- **Mall-REIT tenant-exposure data** (SPG / MAC top-tenant "
    "concentration tables) is in their 10-Ks but unstructured; a "
    "small parser would surface retailer-by-retailer exposure for "
    "direct cross-check.\n"
    "- **Consumer / credit-card spend data** (Affinity Solutions, "
    "Earnest Analytics) are paid data sources; coverage gap.\n"
)


def main():
    matrix = build_matrix(COHORT, LOCAL)
    write_report(
        matrix=matrix, cutoff=CUTOFF, out_dir=OUT,
        title="Brick-and-Mortar Retail Distress Cohort — Blinded Forward-Test Predictions (v1)",
        methodology=METHODOLOGY, not_this=NOT_THIS, debt=DEBT,
    )


if __name__ == "__main__":
    main()
