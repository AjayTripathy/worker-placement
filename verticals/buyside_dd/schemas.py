"""
Pydantic schemas for the buyside DD pipeline.

These define the data flow between Stages 1-5 of the decomposer:
  Document → Claims → TypedClaims → ClaimsWithF → ClaimsWithSources → Findings
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Any, Literal

from pydantic import BaseModel, Field


class ReferentType(str, Enum):
    """The kind of real-world thing a claim refers to."""
    GEOGRAPHIC_AREA = "geographic_area"
    PARCEL = "parcel"
    BUILDING = "building"
    PERSON = "person"
    ENTITY = "entity"               # company, LLC, fund, government body
    EVENT = "event"                 # transaction, transfer, payment
    AMOUNT = "amount"               # $, count, volume
    TIME_PERIOD = "time_period"
    QUANTITY = "quantity"
    INTANGIBLE = "intangible"       # license, certification, exemption
    DRUG_PROGRAM = "drug_program"   # a therapeutic asset / development program
    TRIAL = "trial"                 # a registered clinical trial (NCT)
    PATIENT_COHORT = "patient_cohort"  # an enrolled population / arm
    UNKNOWN = "unknown"


class Verifiability(str, Enum):
    HIGH = "high"        # primary source verifiable (deed, assessor, registered filing)
    MEDIUM = "medium"    # secondary source verifiable (LinkedIn, scraped data)
    LOW = "low"          # only verifiable via interview / FOIA / costly
    UNVERIFIABLE = "unverifiable"


class Severity(str, Enum):
    CRITICAL = "critical"           # deal-breaker
    SEVERE = "severe"               # material misrepresentation
    MODERATE = "moderate"           # noteworthy gap
    MINOR = "minor"                 # within tolerance
    PASS = "pass"                   # claim verified
    UNVERIFIABLE = "unverifiable"   # no M source available


class StopReason(str, Enum):
    """Why dispatch terminated investigation of a particular claim.

    Always set on a Finding so the report can answer "why did/didn't you keep
    looking?" — critical for product defensibility.
    """
    CONVERGED = "converged"               # sources agree (PASS or FAIL — see severity)
    CONFLICT = "conflict"                 # sources disagree at same authority tier
    EXHAUSTED = "exhausted"               # no more applicable sources
    BUDGET_HIT = "budget_hit"             # run-level cost or time cap hit
    IMMATERIAL = "immaterial"             # known materiality < policy floor; paid sources skipped
    DEFERRED = "deferred"                 # unclear materiality + concerning result; needs human triage
    UNREACHABLE = "unreachable"           # all applicable sources failed (network, auth, etc.)
    NOT_DISPATCHED = "not_dispatched"     # claim never queried (no f-rule, no source, etc.)


class Materiality(BaseModel):
    """Exposure if a claim is wrong. Expressed as USD, pct-of-deal, or both.

    Drives whether to spend money on paid sources. Free sources always run.

    Two units are supported because deals are not always $-denominated yet:
      - estimated_usd: dollar value (use when deal_size_usd is known)
      - estimated_pct: 0-1 share of total deal economics (use when deal size
                       is flexible/negotiable; needs deal_context.asset_count
                       or per-claim weights)

    The status field still carries the most weight:
      - "known"     → derived from a deterministic rule (claim value, share of N)
      - "estimated" → derived from a heuristic (NOI × 10, etc.)
      - "unclear"   → no rule matched; free sources still run, but DO NOT spend
                      on paid until re-derivation upgrades it
    """
    status: Literal["known", "estimated", "unclear"] = "unclear"
    estimated_usd: Optional[float] = None
    estimated_pct: Optional[float] = Field(default=None, ge=0.0, le=1.0,
                                          description="0-1 share of total deal exposure")
    derivation: str = Field(default="no derivation rule matched")


class Claim(BaseModel):
    """A structured assertion extracted from a source document."""
    claim_id: str
    source_doc: str
    source_quote: str = Field(..., description="Exact text from doc; anti-hallucination check")

    subject: str = Field(..., description="What entity / thing the claim is about")
    predicate: str = Field(..., description="The assertion verb (owns, generates, paid, claims, etc.)")
    object_value: Any = Field(..., description="The asserted value (number, string, dict)")
    object_unit: Optional[str] = None

    scope: dict = Field(default_factory=dict, description="Time period, area, population context")
    confidence: float = Field(default=1.0, description="LLM confidence in extraction")
    extraction_notes: Optional[str] = None
    materiality: Materiality = Field(default_factory=Materiality)

    # ── Entity-resolution lineage ─────────────────────────────────────────
    # Set when this claim was produced by Stage 1.5 (entity_resolution.py)
    # from a Mode A/B parent claim. Allows the comparator + report to trace
    # a resolved-subject finding back to the original deck-level claim.
    parent_claim_id: Optional[str] = Field(
        default=None,
        description="claim_id of the parent claim this was resolved from",
    )
    resolution_question: Optional[str] = Field(
        default=None,
        description=(
            "Human-readable question the resolver was trying to answer when "
            "it produced this claim (e.g., 'What address corresponds to the "
            "claimed Austin TX factory?')."
        ),
    )
    resolution_provenance: list[dict] = Field(
        default_factory=list,
        description=(
            "Per-tool-call evidence trail. Each entry: {turn, tool, input, "
            "output_summary, source_url, extracted_fact}. Full audit trail of "
            "how the resolver arrived at this claim's subject/object_value. "
            "Empty list when the claim came from Mode A extraction or Mode B "
            "derivation rather than Stage 1.5 resolution."
        ),
    )


class TypedClaim(BaseModel):
    """Claim with referent type assigned."""
    claim: Claim
    referent_type: ReferentType
    referent_attributes: list[str] = Field(default_factory=list)
    referent_id: Optional[str] = Field(None, description="Resolved external ID (BBL, parcel#, LLC#, etc.)")
    jurisdiction: Optional[str] = None  # for f lookup
    verifiability: Verifiability = Verifiability.MEDIUM


class FRule(BaseModel):
    """An expected relationship between claim and observable reality."""
    rule_id: str
    predicate: str
    referent_type: ReferentType
    jurisdiction: Optional[str] = None  # None = applies anywhere

    description: str = Field(..., description="Human-readable description of the relationship")
    formula: str = Field(..., description="How to compute expected value from M")
    formula_inputs: list[str] = Field(..., description="What M attributes are needed")

    noise_tolerance: float = Field(default=0.10)
    severity_thresholds: dict[str, float] = Field(default_factory=dict)

    source_authority: Optional[str] = Field(None, description="Statute, contract, methodology citation")
    promoted_by: Optional[str] = "system"


class MSource(BaseModel):
    """An accessible source for verifying a referent attribute."""
    source_id: str
    referent_type: ReferentType
    attribute: str
    jurisdiction: Optional[str] = None
    granularity: Optional[str] = None

    access_pattern: str = Field(..., description="api / scrape / file_download / foia / manual")
    endpoint: Optional[str] = None
    auth_required: bool = False
    rate_limit_per_min: Optional[int] = None
    cost_per_query: float = 0.0

    authority_tier: int = Field(
        default=3,
        ge=1, le=5,
        description="1=gov primary record (deed/court/SEC), 2=gov derived (FMR/ACS), 3=industry aggregator, 4=public web aggregator, 5=search snippet",
    )
    completeness: float = Field(default=1.0, description="0-1 fraction of universe covered")
    latency_days: int = Field(default=0)
    accuracy_estimate: float = Field(default=1.0)

    connector_module: Optional[str] = Field(None, description="Path to Python module that fetches it")
    notes: Optional[str] = None

    @property
    def is_free(self) -> bool:
        return self.cost_per_query == 0.0 and self.access_pattern not in ("foia", "manual")


class ClaimWithF(BaseModel):
    typed_claim: TypedClaim
    f_rules: list[FRule] = Field(default_factory=list, description="Applicable f-rules")
    needs_human_review: bool = False
    reason: Optional[str] = None


class ClaimWithSources(BaseModel):
    typed_claim: TypedClaim
    f_rules: list[FRule]
    m_sources: list[MSource] = Field(default_factory=list)
    candidate_referent_ids: list[str] = Field(default_factory=list)


class Observation(BaseModel):
    """Result of querying an M source for a specific referent attribute."""
    source_id: str
    referent_id: str
    attribute: str
    value: Any
    fetched_at: datetime
    raw_response: Optional[str] = None  # for evidence trail
    error: Optional[str] = None


class Finding(BaseModel):
    """A divergence finding for a single claim."""
    claim: Claim
    referent_type: ReferentType
    referent_id: Optional[str] = None

    f_rule_id: Optional[str] = None
    expected_value: Any = None
    observed_values: list[Observation] = Field(default_factory=list)

    divergence_absolute: Optional[float] = None
    divergence_pct: Optional[float] = None
    severity: Severity = Severity.UNVERIFIABLE

    # Confidence aggregated across observations.
    # Driven by (a) authority tier of agreeing/disagreeing sources, (b) corroboration count.
    # Range 0-1; 1.0 = definitive (one Tier-1 source); 0.5 = single Tier-3 with no corroboration; 0.0 = unverifiable.
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Why dispatch stopped investigating this claim.
    stop_reason: StopReason = StopReason.NOT_DISPATCHED

    # Materiality at time of stop (may be re-derived from observations).
    materiality_at_stop: Optional[Materiality] = None

    evidence_trail: list[str] = Field(default_factory=list, description="Step-by-step provenance")
    notes: Optional[str] = None

    # Dollar exposure if claim is wrong
    exposure_estimate_usd: Optional[float] = None
