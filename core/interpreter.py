from __future__ import annotations

import importlib
import json
from decimal import Decimal

from .exceptions import RuleError
from .llm import LLMClient, NullLLMClient
from .models import GapResult, Record, RuleMatch, SignalRule


class TieredRuleInterpreter:
    """
    Applies a SignalRule to a GapResult.

    Execution order:
      1. If rule.implementation is set, import and call it (compiled path, confidence=1.0).
      2. Otherwise, call the LLM with rule.source_text + gap context (fallback path).
    """

    def __init__(self, llm: LLMClient | None = None):
        self._llm = llm or NullLLMClient()

    def apply(self, rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
        if rule.implementation:
            return self._run_compiled(rule, gap, records)
        return self._run_llm(rule, gap, records)

    def _run_compiled(self, rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
        try:
            module_path, fn_name = rule.implementation.rsplit(".", 1)
            module = importlib.import_module(module_path)
            fn = getattr(module, fn_name)
            return fn(rule, gap, records)
        except Exception as e:
            raise RuleError(f"Compiled rule {rule.rule_id} failed: {e}") from e

    def _run_llm(self, rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
        prompt = _build_llm_prompt(rule, gap)
        try:
            response = self._llm.complete(prompt, system=_SYSTEM)
            parsed = json.loads(response)
            matched = bool(parsed.get("matched", False))
            adjustment = Decimal(str(parsed.get("adjustment", 0)))
            explanation = parsed.get("explanation", "")
        except Exception:
            matched = False
            adjustment = Decimal(0)
            explanation = "LLM interpretation failed — treating as not matched"

        return RuleMatch(
            rule=rule,
            matched=matched,
            confidence=rule.confidence_if_llm if matched else 0.0,
            gap_adjustment=adjustment,
            explanation=explanation,
            interpreter="llm",
        )


_SYSTEM = (
    "You are a property tax legal analyst. Given a rule and a gap result, "
    "determine whether the rule applies and by how much it adjusts the gap. "
    "Respond with valid JSON only: {\"matched\": bool, \"adjustment\": number, \"explanation\": string}. "
    "adjustment is the dollar amount by which this rule reduces the gap (negative = reduces gap). "
    "If the rule does not apply, adjustment must be 0."
)


def _build_llm_prompt(rule: SignalRule, gap: GapResult) -> str:
    return (
        f"Rule: {rule.rule_id} — {rule.description}\n"
        f"Statutory reference: {rule.statutory_ref}\n"
        f"Statute text: {rule.source_text[:2000]}\n\n"
        f"Gap context:\n"
        f"  Entity: {gap.entity_id}\n"
        f"  Regulated value (R): {gap.regulated_value}\n"
        f"  Market value (M): {gap.market_value}\n"
        f"  Expected regulated f(M): {gap.expected_regulated}\n"
        f"  Raw gap R - f(M): {gap.raw_gap}\n"
        f"  Data quality flags: {gap.data_quality_flags}\n"
        f"  Metadata: {json.dumps(gap.metadata, default=str)}\n\n"
        f"Does this rule apply? If so, by how much does it reduce the gap?"
    )
