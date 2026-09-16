"""
LA County registry — wires LA County sources into the California property tax engine.

No LA County-specific business logic. All cap law comes from california/.
LA County contributes only: assessor data source + geographic config.
"""
from __future__ import annotations

from core.engine import SignalEngine
from core.interpreter import TieredRuleInterpreter
from core.llm import AnthropicClient, NullLLMClient
from core.registry import SourceRegistry

from verticals.property_tax.gap import PropertyTaxGapFunction
from verticals.property_tax.jurisdictions.california.cap_law import Prop13CapLaw
from verticals.property_tax.jurisdictions.california.config import (
    AV_RATIO, CAPPED_THRESHOLD, MIN_AV_DELTA, MILLAGE_STANDARD, SALE_LOOKBACK_YEARS,
)
from verticals.property_tax.jurisdictions.california.rules import RULES
from verticals.property_tax.manifest import PROPERTY_TAX_MANIFEST
from verticals.property_tax.scorer import PropertyTaxScorer
from verticals.property_tax.sources.redfin import RedfinSaleSource
from verticals.property_tax.sources.zillow import ZillowSaleSource

from .assessor import LACountyAssessorSource


def _build_registry(include_mls: bool = False) -> SourceRegistry:
    registry = SourceRegistry()
    registry.register(LACountyAssessorSource(), "property_tax", jurisdictions=["la_county"])
    if include_mls:
        registry.register(ZillowSaleSource(), "property_tax")
        registry.register(RedfinSaleSource(), "property_tax")
    return registry


def build_engine(
    include_mls: bool = False,
    use_llm: bool = False,
) -> SignalEngine:
    """
    Build a SignalEngine configured for LA County property tax analysis.

    Args:
        include_mls: Fetch Zillow/Redfin sale history (slow — use for targeted enrichment).
        use_llm: Enable LLM fallback for Prop 19 and welfare exemption rules.
    """
    registry = _build_registry(include_mls)
    registry.validate("property_tax", "la_county", PROPERTY_TAX_MANIFEST)
    sources = registry.for_jurisdiction("property_tax", "la_county")

    llm = AnthropicClient() if use_llm else NullLLMClient()

    return SignalEngine(
        vertical="property_tax",
        jurisdiction="la_county",
        sources=sources,
        gap_function=PropertyTaxGapFunction(
            cap_law=Prop13CapLaw(),
            lookback_years=SALE_LOOKBACK_YEARS,
            capped_threshold=float(CAPPED_THRESHOLD),
            min_tv_delta=MIN_AV_DELTA,
            av_ratio=AV_RATIO,
        ),
        rules=RULES,
        interpreter=TieredRuleInterpreter(llm=llm),
        scorer=PropertyTaxScorer(
            millage_standard=MILLAGE_STANDARD,
            millage_homestead=None,   # California HOE reduces AV, not millage rate
            millage_reduced=None,     # no reduced millage tier in California
            homestead_rule_id=None,
            reduced_rule_id=None,
            exempt_rule_ids=frozenset({"WELFARE_EXEMPTION"}),
        ),
        store=None,
    )
