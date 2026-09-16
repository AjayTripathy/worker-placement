from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterator

from .exceptions import SourceError
from .models import Entity, Signal, SignalRule
from .protocols import GapFunction, RuleInterpreter, Scorer, SignalStore, Source


@dataclass
class RunSummary:
    run_id: str
    vertical: str
    jurisdiction: str
    started_at: datetime
    completed_at: datetime
    processed: int
    signaled: int
    high: int
    medium: int
    low: int
    exempt: int
    total_annual_impact: Decimal


class SignalEngine:
    def __init__(
        self,
        vertical: str,
        jurisdiction: str,
        sources: list[Source],
        gap_function: GapFunction,
        rules: list[SignalRule],
        interpreter: RuleInterpreter,
        scorer: Scorer,
        store: SignalStore,
    ):
        self.vertical = vertical
        self.jurisdiction = jurisdiction
        self.sources = sources
        self.gap_function = gap_function
        self.rules = sorted(rules, key=lambda r: r.priority)
        self.interpreter = interpreter
        self.scorer = scorer
        self.store = store

    def run(self, entities: Iterator[Entity]) -> RunSummary:
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        counts = {"processed": 0, "signaled": 0, "high": 0, "medium": 0, "low": 0, "exempt": 0}
        total_impact = Decimal(0)

        for entity in entities:
            counts["processed"] += 1
            signal = self.run_one(entity, run_id=run_id)
            if signal is not None:
                counts["signaled"] += 1
                counts[signal.fraud_tier] += 1
                if signal.estimated_annual_impact:
                    total_impact += signal.estimated_annual_impact

        return RunSummary(
            run_id=run_id,
            vertical=self.vertical,
            jurisdiction=self.jurisdiction,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            processed=counts["processed"],
            signaled=counts["signaled"],
            high=counts["high"],
            medium=counts["medium"],
            low=counts["low"],
            exempt=counts["exempt"],
            total_annual_impact=total_impact,
        )

    def run_one(
        self,
        entity: Entity,
        run_id: str | None = None,
        seed_records: list | None = None,
    ) -> Signal | None:
        run_id = run_id or str(uuid.uuid4())

        records = list(seed_records) if seed_records else []
        seeded_types = {r.record_type for r in records}

        for source in self.sources:
            if source.record_type in seeded_types:
                continue  # caller already provided this record type; skip re-fetch

            # Check record cache before hitting the network
            cache_ttl = getattr(source, "cache_ttl_days", 30)
            if self.store is not None:
                cached = self.store.read_records(entity.id, source.source_id, max_age_days=cache_ttl)
                if cached is not None:  # None = miss; [] = cached empty result
                    records.extend(cached)
                    continue

            try:
                fresh = source.fetch(entity)
                records.extend(fresh)
                if self.store is not None:
                    self.store.write_records(entity.id, source.source_id, fresh)
            except SourceError:
                pass  # non-fatal: partial data; gap function will flag data_quality

        gap = self.gap_function.compute(entity, records)
        if gap is None:
            return None

        rule_matches = [
            self.interpreter.apply(rule, gap, records)
            for rule in self.rules
        ]

        modifier_adjustments = sum(
            m.gap_adjustment
            for m in rule_matches
            if m.matched and m.rule.rule_type == "gap_modifier"
        )
        net_gap = gap.raw_gap + modifier_adjustments

        fraud_score, fraud_tier = self.scorer.score(gap, rule_matches)
        annual_impact = self.scorer.annual_impact(gap, rule_matches)

        signal = Signal(
            signal_id=str(uuid.uuid4()),
            run_id=run_id,
            entity_id=entity.id,
            vertical=self.vertical,
            jurisdiction=self.jurisdiction,
            gap=gap,
            rule_matches=rule_matches,
            fraud_score=fraud_score,
            fraud_tier=fraud_tier,
            net_gap=net_gap,
            estimated_annual_impact=Decimal(str(annual_impact)) if annual_impact else None,
        )

        if self.store is not None:
            self.store.write_signal(signal)
        return signal
