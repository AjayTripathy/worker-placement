"""
Detroit registry — wires Detroit sources into the Michigan property tax engine.

Sources are assembled via SourceRegistry:
  - national sources (Zillow, Redfin) auto-apply to every jurisdiction
  - city-scoped sources (Detroit assessor, Wayne County deeds) apply only here

Adding a new jurisdiction means only registering its city-scoped sources;
national sources propagate automatically.
"""
from __future__ import annotations

from core.engine import SignalEngine
from core.interpreter import TieredRuleInterpreter
from core.llm import AnthropicClient, NullLLMClient
from core.registry import SourceRegistry

from verticals.property_tax.gap import PropertyTaxGapFunction
from verticals.property_tax.jurisdictions.michigan.cap_law import MCL211a27CapLaw
from verticals.property_tax.jurisdictions.michigan.config import (
    CAPPED_THRESHOLD, MIN_TV_DELTA, SALE_LOOKBACK_YEARS,
)
from verticals.property_tax.jurisdictions.michigan.rules import RULES
from verticals.property_tax.manifest import PROPERTY_TAX_MANIFEST
from verticals.property_tax.scorer import PropertyTaxScorer
from verticals.property_tax.sources.redfin import RedfinSaleSource
from verticals.property_tax.sources.zillow import ZillowSaleSource

from .assessor import DetroitAssessorSource
from .deeds import WayneCountyDeedSource


def _build_registry(
    include_deeds: bool = False,
    include_mls: bool = False,
) -> SourceRegistry:
    registry = SourceRegistry()
    # City-scoped: only applies to detroit
    registry.register(DetroitAssessorSource(), "property_tax", jurisdictions=["detroit"])
    if include_deeds:
        registry.register(WayneCountyDeedSource(), "property_tax", jurisdictions=["detroit"])
    # National MLS sources — slow (per-parcel HTTP), use only for targeted enrichment
    if include_mls:
        registry.register(ZillowSaleSource(), "property_tax")
        registry.register(RedfinSaleSource(), "property_tax")
    return registry


def build_engine(
    include_deeds: bool = False,
    include_mls: bool = False,
    use_llm: bool = False,
) -> SignalEngine:
    """
    Build a SignalEngine configured for Detroit property tax analysis.

    Args:
        include_deeds: Include Wayne County deed scraper (slow — ~15s/parcel).
        use_llm: Enable LLM fallback for PA210/OPRA rules. Requires ANTHROPIC_API_KEY.
    """
    registry = _build_registry(include_deeds, include_mls)
    registry.validate("property_tax", "detroit", PROPERTY_TAX_MANIFEST)
    sources = registry.for_jurisdiction("property_tax", "detroit")

    llm = AnthropicClient() if use_llm else NullLLMClient()

    return SignalEngine(
        vertical="property_tax",
        jurisdiction="detroit",
        sources=sources,
        gap_function=PropertyTaxGapFunction(
            cap_law=MCL211a27CapLaw(),
            lookback_years=SALE_LOOKBACK_YEARS,
            capped_threshold=CAPPED_THRESHOLD,
            min_tv_delta=MIN_TV_DELTA,
        ),
        rules=RULES,
        interpreter=TieredRuleInterpreter(llm=llm),
        scorer=PropertyTaxScorer(),
        store=None,  # caller injects store
    )
