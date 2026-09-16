"""Run policy: encodes a DD team's risk appetite + cost/time constraints.

Three product presets: TRIAGE, STANDARD, DEEP. Each is a different point on the
cost/time/coverage curve. Per-customer overrides plug in via `with_overrides()`.

The policy is consumed by the dispatcher to decide:
  - Which sources to dispatch for each claim (free always; paid gated)
  - When to stop investigating a claim (convergence rules)
  - When to stop the run as a whole (budget cap)

A run with a given policy must be reproducible: same input + same policy_version
= same output. This is what lets us bill per-claim and defend findings later.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RunPolicy(BaseModel):
    """The configurable dial for how aggressively to verify claims."""
    name: str
    version: str = "v0.1"

    # ── Budget caps ────────────────────────────────────────────────────────
    max_cost_usd: float = Field(..., description="Hard cap on paid-source spend per run")
    max_wall_time_min: int = Field(..., description="Hard cap on wall-clock time")
    max_source_calls_per_claim: int = Field(default=10, description="Soft cap on dispatch breadth")

    # ── Source gating ──────────────────────────────────────────────────────
    paid_sources_enabled: bool = Field(default=False, description="Allow cost_per_query > 0 sources")
    foia_enabled: bool = Field(default=False, description="Allow FOIA-pattern sources (slow async)")
    paid_source_floor_usd: float = Field(
        default=10000.0,
        description="Min USD materiality to dispatch a paid source. Below this, save the cost.",
    )
    paid_source_floor_pct: float = Field(
        default=0.01,
        description="Min pct-of-deal materiality (0-1) when materiality is in pct mode (no deal_size_usd in context). DEEP=0.005, STANDARD=0.05, TRIAGE=1.0 (off).",
    )

    # ── Convergence rules ──────────────────────────────────────────────────
    # How many sources of a given authority tier needed to call a claim "converged"
    convergence_by_tier: dict[int, int] = Field(
        default={1: 1, 2: 2, 3: 3, 4: 3, 5: 4},
        description="Tier 1 source = 1 call enough; Tier 5 needs 4 to corroborate",
    )

    # ── Reporting threshold ────────────────────────────────────────────────
    # Below this severity, omit from human-facing report (still in raw findings)
    report_severity_threshold: str = Field(
        default="moderate",
        description="critical | severe | moderate | minor — omit findings below this",
    )

    # ── Re-derivation ──────────────────────────────────────────────────────
    rederive_materiality_after_free_pass: bool = Field(
        default=True,
        description="Use free-source observations to upgrade Unclear materiality before paid dispatch",
    )

    def with_overrides(self, **kwargs) -> "RunPolicy":
        """Per-customer policy override (paid_source_floor, foia_enabled, etc.)."""
        d = self.model_dump()
        d.update(kwargs)
        return RunPolicy(**d)


# ─────────────────────────────────────────────────────────────────────────────
# Three product presets
# ─────────────────────────────────────────────────────────────────────────────
TRIAGE = RunPolicy(
    name="triage",
    max_cost_usd=50.0,
    max_wall_time_min=30,
    paid_sources_enabled=False,
    foia_enabled=False,
    paid_source_floor_usd=1_000_000.0,  # effectively off
    paid_source_floor_pct=1.0,           # effectively off
    report_severity_threshold="severe",
    max_source_calls_per_claim=5,
)

STANDARD = RunPolicy(
    name="standard",
    max_cost_usd=500.0,
    max_wall_time_min=240,
    paid_sources_enabled=True,
    foia_enabled=False,
    paid_source_floor_usd=25_000.0,
    paid_source_floor_pct=0.05,          # 5% of deal
    report_severity_threshold="moderate",
    max_source_calls_per_claim=10,
)

DEEP = RunPolicy(
    name="deep",
    max_cost_usd=5_000.0,
    max_wall_time_min=10_080,  # 1 week
    paid_sources_enabled=True,
    foia_enabled=True,
    paid_source_floor_usd=5_000.0,
    paid_source_floor_pct=0.005,         # 0.5% of deal
    report_severity_threshold="minor",
    max_source_calls_per_claim=20,
)


PRESETS = {"triage": TRIAGE, "standard": STANDARD, "deep": DEEP}


def get_policy(name: str = "standard", **overrides) -> RunPolicy:
    """Look up a preset by name and apply per-customer overrides."""
    base = PRESETS.get(name.lower())
    if base is None:
        raise ValueError(f"unknown policy preset {name}; choices: {list(PRESETS)}")
    if overrides:
        return base.with_overrides(**overrides)
    return base
