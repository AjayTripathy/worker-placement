"""Shared dataclass contract for the local-vs-API provider interface.

Both providers (LocalProvider, ApiProvider) read filings and produce these
exact shapes. The runner consumes them identically so providers are swappable.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Claim:
    claim_id: str
    claim_text: str
    subject: str = ""
    predicate: str = ""
    object_value: Any = None
    source_quote: str = ""
    category: str = "other"


@dataclass
class MQuery:
    source: str
    kwargs: dict
    rationale: str = ""


@dataclass
class Evidence:
    source: str
    kwargs: dict
    result: dict


@dataclass
class Finding:
    severity: str
    supports: bool | None
    M_check: str = ""
    M_value: str = ""
    interpretation: str = ""


@dataclass
class CompanyAnalysis:
    ticker: str
    cutoff_date: str
    cik: str = ""
    outcome: str | None = None
    outcome_detail: str = ""
    filing: str = ""
    provider: str = ""
    claims: list[Claim] = field(default_factory=list)
    queries_per_claim: dict[str, list[MQuery]] = field(default_factory=dict)
    evidence_per_claim: dict[str, list[Evidence]] = field(default_factory=dict)
    findings_by_claim: dict[str, Finding] = field(default_factory=dict)

    def severity_score(self) -> float:
        weights = {
            "RED_FLAG_NEGATIVE": 4.0,
            "SEVERE_UNDERDELIVERY": 3.0,
            "MODERATE_UNDERDELIVERY": 1.5,
            "UNVERIFIABLE": 0.0,
            "PASS": 0.0,
        }
        return sum(weights.get(f.severity, 0.0) for f in self.findings_by_claim.values())

    def n_contradicted(self) -> int:
        return sum(1 for f in self.findings_by_claim.values() if f.supports is False)

    def severity_counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for f in self.findings_by_claim.values():
            out[f.severity] = out.get(f.severity, 0) + 1
        return out

    def score_per_claim(self) -> float:
        n = len(self.findings_by_claim)
        return self.severity_score() / n if n else 0.0

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "cutoff_date": self.cutoff_date,
            "cik": self.cik,
            "outcome": self.outcome,
            "outcome_detail": self.outcome_detail,
            "filing": self.filing,
            "provider": self.provider,
            "n_claims": len(self.claims),
            "n_contradicted": self.n_contradicted(),
            "severity_score": round(self.severity_score(), 1),
            "score_per_claim": round(self.score_per_claim(), 2),
            "counts": self.severity_counts(),
            "claims": [asdict(c) for c in self.claims],
            "queries_per_claim": {
                cid: [asdict(q) for q in qs]
                for cid, qs in self.queries_per_claim.items()
            },
            "evidence_per_claim": {
                cid: [asdict(e) for e in es]
                for cid, es in self.evidence_per_claim.items()
            },
            "findings_by_claim": {
                cid: asdict(f) for cid, f in self.findings_by_claim.items()
            },
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str))
