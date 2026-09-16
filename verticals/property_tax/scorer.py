from __future__ import annotations

from decimal import Decimal
from typing import Literal

from core.models import GapResult, RuleMatch


class PropertyTaxScorer:
    """
    Heuristic fraud scorer for property tax uncap signals.

    Rates and rule IDs are injected so the same scorer works across jurisdictions:
      - Michigan:   millage_standard=67, homestead_rule_id="PRE", reduced_rule_id="NEZ"
      - California: millage_standard=12, homestead_rule_id=None,  reduced_rule_id=None

    Score components (0-100):
        method_agreement:  both=40  sev_only=30  sale_only=15
        data_quality:      zero_consideration=+25  sale_suppressed=+15  sale_inflated=-10
        overdue:           +15 if past uncap year
        deed_flags:        quit_claim=+5
        owner_is_entity:   +5 (entities less likely to file exemptions)
    """

    def __init__(
        self,
        millage_standard: float = 67.0,
        millage_homestead: float | None = 40.0,
        millage_reduced: float | None = 6.0,
        homestead_rule_id: str | None = "PRE",
        reduced_rule_id: str | None = "NEZ",
        exempt_rule_ids: frozenset[str] = frozenset({"PILOT", "LIHTC"}),
    ):
        self.millage_standard = millage_standard
        self.millage_homestead = millage_homestead
        self.millage_reduced = millage_reduced
        self.homestead_rule_id = homestead_rule_id
        self.reduced_rule_id = reduced_rule_id
        self.exempt_rule_ids = frozenset(exempt_rule_ids)

    def score(
        self,
        gap: GapResult,
        rule_matches: list[RuleMatch],
    ) -> tuple[int, Literal["low", "medium", "high", "exempt"]]:
        if self._is_exempt(rule_matches):
            return 0, "exempt"

        s = 0
        meta = gap.metadata

        method = meta.get("method_agreement", "neither")
        s += {"both": 40, "sev_only": 30, "sale_only": 15, "neither": 0}.get(method, 0)

        dq = meta.get("data_quality", "")
        if dq == "zero_consideration":
            s += 25
        elif dq == "sale_suppressed":
            s += 15
        elif dq == "sale_inflated":
            s -= 10

        if meta.get("overdue"):
            s += 15

        if "quit_claim_deed" in gap.data_quality_flags:
            s += 5

        if meta.get("owner_is_entity"):
            s += 5

        # PRE-on-entity violation is a hard statutory contradiction —
        # MCL 211.7cc explicitly requires natural-person occupancy. An
        # LLC / Inc / Corp / Ltd / LP cannot legitimately claim PRE.
        # When the rule fires, force the parcel into the high-tier band
        # regardless of other scoring components.
        pre_entity_matched = any(
            m.matched and m.rule.rule_id == "PRE_ENTITY_VIOLATION"
            for m in rule_matches
        )

        s = max(0, min(100, s))
        if pre_entity_matched:
            s = max(s, 75)
        tier: Literal["low", "medium", "high", "exempt"] = (
            "high" if s >= 70 else "medium" if s >= 45 else "low"
        )
        return s, tier

    def annual_impact(
        self,
        gap: GapResult,
        rule_matches: list[RuleMatch],
    ) -> float | None:
        if self._is_exempt(rule_matches):
            return None

        # PRE_ENTITY_VIOLATION returns gap_adjustment as ANNUAL DOLLARS
        # (not TV-dollars), since it represents the millage-differential
        # fraud on the current capped TV. Pull it out separately so the
        # uncap-net_gap calculation isn't polluted by units-mismatched
        # adjustments.
        pre_entity_annual = Decimal(0)
        for m in rule_matches:
            if (m.matched and m.rule.rule_id == "PRE_ENTITY_VIOLATION"
                    and m.rule.rule_type == "gap_modifier"):
                pre_entity_annual += m.gap_adjustment

        # Uncap-gap adjustments (TV-dollar units), excluding the PRE-entity
        # rule which already used annual-dollar units above.
        net_gap = gap.raw_gap + sum(
            m.gap_adjustment for m in rule_matches
            if (m.matched and m.rule.rule_type == "gap_modifier"
                and m.rule.rule_id != "PRE_ENTITY_VIOLATION")
        )

        uncap_impact = Decimal(0)
        if net_gap > 0:
            # If PRE_ENTITY_VIOLATION fired, deny the PRE millage reduction
            # for the uncap gap — the LLC cannot legitimately get the 40-mill
            # rate on the uncap delta either.
            pre_entity_matched = any(
                m.matched and m.rule.rule_id == "PRE_ENTITY_VIOLATION"
                for m in rule_matches
            )
            if pre_entity_matched:
                millage = self.millage_standard
            else:
                millage = self._effective_millage(gap.metadata, rule_matches)
            uncap_impact = net_gap / 1000 * Decimal(str(millage))

        total = uncap_impact + pre_entity_annual
        return float(total) if total > 0 else None

    def _is_exempt(self, rule_matches: list[RuleMatch]) -> bool:
        return any(m.matched and m.rule.rule_id in self.exempt_rule_ids for m in rule_matches)

    def _effective_millage(self, meta: dict, rule_matches: list[RuleMatch]) -> float:
        if self.reduced_rule_id and self.millage_reduced is not None:
            if any(m.matched and m.rule.rule_id == self.reduced_rule_id for m in rule_matches):
                return self.millage_reduced

        if self.homestead_rule_id and self.millage_homestead is not None:
            pre_match = next(
                (m for m in rule_matches if m.matched and m.rule.rule_id == self.homestead_rule_id),
                None,
            )
            if pre_match:
                pct = meta.get("homestead_pct", 0) or 0
                blended = (
                    self.millage_homestead * (pct / 100)
                    + self.millage_standard * (1 - pct / 100)
                )
                return blended

        return self.millage_standard
