from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from .models import Entity, GapResult, Record, RuleMatch, Signal, SignalRule


@runtime_checkable
class Source(Protocol):
    source_id: str
    record_type: str                    # "assessment", "sale", "deed"
    cache_ttl_days: int                 # how long the store should cache records from this source

    def fetch(self, entity: Entity) -> list[Record]: ...


@runtime_checkable
class GapFunction(Protocol):
    def compute(self, entity: Entity, records: list[Record]) -> GapResult | None: ...


@runtime_checkable
class RuleInterpreter(Protocol):
    def apply(self, rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch: ...


@runtime_checkable
class Scorer(Protocol):
    def score(
        self,
        gap: GapResult,
        rule_matches: list[RuleMatch],
    ) -> tuple[int, Literal["low", "medium", "high", "exempt"]]: ...

    def annual_impact(
        self,
        gap: GapResult,
        rule_matches: list[RuleMatch],
    ) -> float | None: ...


@runtime_checkable
class SignalStore(Protocol):
    def write_signal(self, signal: Signal) -> None: ...
    def read_signals(self, **filters) -> list[Signal]: ...
    def write_rules(self, rules: list[SignalRule]) -> None: ...
    def read_rules(self, vertical: str, jurisdiction: str) -> list[SignalRule]: ...
    def read_records(self, entity_id: str, source_id: str, max_age_days: int = 30) -> list[Record] | None: ...
    def write_records(self, entity_id: str, source_id: str, records: list[Record]) -> None: ...
