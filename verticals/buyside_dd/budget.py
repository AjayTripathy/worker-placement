"""BudgetState: live tracking of cost, time, and call count during a dispatch run.

The dispatcher consults this before every paid-source call. Once any cap is hit,
`is_exhausted()` returns True and remaining claims get StopReason.BUDGET_HIT.
"""
from __future__ import annotations

import time
from typing import Optional

from pydantic import BaseModel, Field


class BudgetState(BaseModel):
    max_cost_usd: float
    max_wall_time_min: int

    spent_usd: float = 0.0
    calls_made: int = 0
    started_at_monotonic: float = Field(default_factory=time.monotonic)

    # For per-source debugging
    cost_by_source: dict[str, float] = Field(default_factory=dict)
    calls_by_source: dict[str, int] = Field(default_factory=dict)

    def can_afford(self, cost: float) -> bool:
        return (self.spent_usd + cost) <= self.max_cost_usd and not self.time_exhausted

    @property
    def elapsed_min(self) -> float:
        return (time.monotonic() - self.started_at_monotonic) / 60.0

    @property
    def time_exhausted(self) -> bool:
        return self.elapsed_min >= self.max_wall_time_min

    @property
    def cost_exhausted(self) -> bool:
        return self.spent_usd >= self.max_cost_usd

    def is_exhausted(self) -> bool:
        return self.time_exhausted or self.cost_exhausted

    def record(self, source_id: str, cost: float) -> None:
        self.spent_usd += cost
        self.calls_made += 1
        self.cost_by_source[source_id] = self.cost_by_source.get(source_id, 0.0) + cost
        self.calls_by_source[source_id] = self.calls_by_source.get(source_id, 0) + 1

    def summary(self) -> dict:
        return {
            "spent_usd": round(self.spent_usd, 2),
            "max_cost_usd": self.max_cost_usd,
            "elapsed_min": round(self.elapsed_min, 1),
            "max_wall_time_min": self.max_wall_time_min,
            "calls_made": self.calls_made,
            "cost_by_source": self.cost_by_source,
            "calls_by_source": self.calls_by_source,
            "exhausted": self.is_exhausted(),
            "exhausted_reason": (
                "cost" if self.cost_exhausted else
                "time" if self.time_exhausted else
                None
            ),
        }
