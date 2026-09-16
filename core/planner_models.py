"""
Planner-phase data models for the 3-phase Signal OS pipeline.

Phase 1 (Planner subagent) reads filings, extracts claims, types referents,
maps each claim to an M-source from the catalog OR proposes a new connector
when the catalog doesn't cover it. The output is a TickerPlan, serialized
to data/_local/<TK>.plan.json.

The compile phase (compile_connectors.py) aggregates ProposedConnector
records across all tickers + all cohorts and emits a prioritized queue
for promotion into the live source catalog.

Phase 2 (Scorer subagent) consumes TickerPlan + the post-promotion source
catalog, runs the M-side queries, and emits per-claim severity scores
into data/_local/<TK>.scores.json.

The separation is the architectural promise of ARCHITECTURE.md
Stages 1-4 (planning) vs Stage 5 (execution).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


# M-source plan status per claim
MSourceStatus = Literal["MAPPED", "PROPOSED", "NONE"]


@dataclass
class ProposedConnector:
    """A new M-source the catalog doesn't currently expose.

    Emitted by Phase 1 subagents when they encounter a claim whose
    adjudicating registry isn't plumbed. The compile phase dedupes
    proposals across tickers (by `name`) and ranks by reference count.
    """

    name: str                       # e.g. "fdic_call_reports.bank_loan_performance"
    description: str                # one-line human description
    endpoint: str                   # URL / file path / API base
    access_pattern: str             # "csv_download" | "api" | "scrape" | "file_download" | "foia"
    auth_required: bool
    sample_invocation: str          # how Phase 2 should call it (pseudocode)
    rationale: str                  # why this claim type needs this source
    estimated_cost: str = "free"
    completeness: str = "?"         # qualitative coverage estimate
    referent_type: str = ""         # what kind of thing the source observes
    attribute: str = ""             # what about the referent it observes


@dataclass
class ClaimPlan:
    """One claim's plan: the extracted claim plus its M-source mapping."""

    claim_id: str
    claim_text: str
    source_quote: str               # literal text from the filing
    subject: str
    predicate: str
    object_value: str | None
    category: str                   # customer_pipeline | regulatory_milestone | ...
    referent_type: str              # geographic_area | entity | event | amount | ...

    # M-source plan
    m_source_status: MSourceStatus
    source_id: str | None = None              # if MAPPED — key in m_source_catalog.CATALOG
    source_params: dict[str, Any] = field(default_factory=dict)  # if MAPPED
    proposed_connector: ProposedConnector | None = None          # if PROPOSED

    # Provenance / debugging
    extraction_notes: str = ""


@dataclass
class TickerPlan:
    """Per-ticker Phase-1 output."""

    ticker: str
    cutoff: str                     # YYYY-MM-DD
    filing: str                     # filename of the analyzed filing
    claims: list[ClaimPlan]
    plan_version: int = 1


def to_jsonable(obj: Any) -> Any:
    """Convert dataclass / nested dataclasses to JSON-serializable dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    return obj
