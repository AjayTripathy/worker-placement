from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel


class SignalRule(BaseModel):
    rule_id: str
    vertical: str
    jurisdiction: str                   # "*" = applies to all jurisdictions in vertical
    rule_type: Literal["gap_modifier", "gap_explainer"]
    detectable: bool
    statutory_ref: str | None = None
    description: str = ""
    implementation: str | None = None   # fully-qualified path; None = LLM fallback
    confidence_if_llm: float = 0.5
    priority: int = 100                 # lower = applied first
    source_text: str = ""              # statute excerpt used by LLM


@dataclass
class Entity:
    id: str
    entity_type: str                    # "parcel", "vessel", "company"
    vertical: str                       # "property_tax"
    jurisdiction: str                   # "detroit"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Record:
    entity_id: str
    record_type: str                    # "assessment", "sale", "deed"
    source: str                         # "detroit_open_data", "zillow"
    data: dict[str, Any]
    fetched_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GapResult:
    entity_id: str
    regulated_value: Decimal            # R — the self-reported value
    market_value: Decimal               # M — the independent market value
    expected_regulated: Decimal         # f(M) — what R should be
    raw_gap: Decimal                    # R - f(M)
    gap_pct: float                      # raw_gap / expected_regulated
    gap_direction: Literal["under_reported", "over_reported", "compliant", "unknown"]
    data_quality_flags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleMatch:
    rule: SignalRule
    matched: bool
    confidence: float                   # 1.0 if compiled, lower if LLM
    gap_adjustment: Decimal             # how much this rule shifts the gap (negative = reduces)
    explanation: str
    interpreter: Literal["compiled", "llm"]


@dataclass
class Signal:
    signal_id: str
    run_id: str
    entity_id: str
    vertical: str
    jurisdiction: str
    gap: GapResult
    rule_matches: list[RuleMatch]
    fraud_score: int                    # 0-100
    fraud_tier: Literal["low", "medium", "high", "exempt"]
    net_gap: Decimal                    # raw_gap after gap_modifier adjustments
    estimated_annual_impact: Decimal | None
    metadata: dict[str, Any] = field(default_factory=dict)
    computed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VerticalManifest:
    vertical: str
    required_source_types: list[str]          # must have ≥1 source; startup fails without them
    optional_source_types: list[str] = field(default_factory=list)
