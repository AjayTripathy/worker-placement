from __future__ import annotations

from decimal import Decimal
from typing import Literal

from core.models import GapResult, RuleMatch


class RentStabilizationScorer:
    """
    Heuristic fraud scorer for rent stabilization overcharge signals.

    Score components (0–100):
        stabilization_confidence: confirmed=40, high_inferred=25, medium=15, low=5
        gap_magnitude:  >100% over max=30, >50%=20, >25%=10, >10%=5
        owner_is_entity: +10 (entities exploit loopholes more frequently)
        data_quality:   confirmed_obligation=+10, low_confidence=-10
        inferred_stabilization flag: -5 (epistemic discount)
    """

    def score(
        self,
        gap: GapResult,
        rule_matches: list[RuleMatch],
    ) -> tuple[int, Literal["low", "medium", "high", "exempt"]]:
        if any(m.matched and m.rule.rule_type == "exempt" for m in rule_matches):
            return 0, "exempt"

        s = 0
        meta = gap.metadata

        status = meta.get("stabilization_status", "likely")
        conf   = meta.get("stabilization_confidence", 0.5)

        if status in ("j51_confirmed", "421a_confirmed"):
            s += 40
        elif conf >= 0.8:
            s += 25
        elif conf >= 0.6:
            s += 15
        else:
            s += 5

        gap_pct = gap.gap_pct  # listed / max_legal - 1
        if gap_pct > 1.0:
            s += 30
        elif gap_pct > 0.5:
            s += 20
        elif gap_pct > 0.25:
            s += 10
        else:
            s += 5

        if meta.get("owner_is_entity"):
            s += 10

        dq = meta.get("data_quality", "")
        if dq == "confirmed_obligation":
            s += 10
        elif dq == "low_confidence_inferred":
            s -= 10

        if "inferred_stabilization" in gap.data_quality_flags:
            s -= 5

        s = max(0, min(100, s))
        tier: Literal["low", "medium", "high", "exempt"] = (
            "high" if s >= 65 else "medium" if s >= 40 else "low"
        )
        return s, tier

    def annual_impact(
        self,
        gap: GapResult,
        rule_matches: list[RuleMatch],
    ) -> float | None:
        """Monthly overcharge × 12 = annual tenant harm."""
        if gap.raw_gap <= 0:
            return None
        net_gap = gap.raw_gap + sum(
            m.gap_adjustment for m in rule_matches
            if m.matched and m.rule.rule_type == "gap_modifier"
        )
        if net_gap <= 0:
            return None
        return float(net_gap * 12)
