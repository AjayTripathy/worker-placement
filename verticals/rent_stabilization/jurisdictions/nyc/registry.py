"""
NYC registry — wires NYC sources into the rent stabilization engine.

No NYC-specific business logic beyond source selection. The RSL rules and
RGB schedule live in the vertical-level modules (not jurisdiction-specific)
because NYC is the only RSL jurisdiction we support.
"""
from __future__ import annotations

from core.engine import SignalEngine
from core.interpreter import TieredRuleInterpreter
from core.llm import AnthropicClient, NullLLMClient
from core.registry import SourceRegistry

from verticals.rent_stabilization.gap import RentStabilizationGapFunction
from verticals.rent_stabilization.manifest import RENT_STABILIZATION_MANIFEST
from verticals.rent_stabilization.rules import RULES
from verticals.rent_stabilization.scorer import RentStabilizationScorer
from verticals.rent_stabilization.sources.nyc_census_rents import NYCCensusRentsSource
from verticals.rent_stabilization.sources.nyc_pluto import NYCPLUTOSource
from verticals.rent_stabilization.sources.nyc_streeteasy import NYCStreetEasySource

from .config import LISTING_LOOKBACK_DAYS, MIN_RENT_DELTA, VACANCY_BONUS_FACTOR


def _build_registry(
    include_listings: bool = False,
    listing_source: str = "census",   # "census" | "streeteasy"
) -> SourceRegistry:
    registry = SourceRegistry()
    registry.register(NYCPLUTOSource(), "rent_stabilization", jurisdictions=["nyc"])
    if include_listings:
        if listing_source == "streeteasy":
            registry.register(NYCStreetEasySource(), "rent_stabilization")
        else:
            registry.register(NYCCensusRentsSource(), "rent_stabilization")
    return registry


def build_engine(
    include_listings: bool = False,
    use_llm: bool = False,
    listing_source: str = "census",
) -> SignalEngine:
    """
    Build a SignalEngine configured for NYC rent stabilization analysis.

    Args:
        include_listings: Fetch StreetEasy rent listings (required for gap
            detection; disable only for building enumeration / dry runs).
        use_llm: Enable LLM fallback for J-51 and HSTPA rules.
    """
    registry = _build_registry(include_listings, listing_source=listing_source)
    registry.validate("rent_stabilization", "nyc", RENT_STABILIZATION_MANIFEST)
    sources = registry.for_jurisdiction("rent_stabilization", "nyc")

    llm = AnthropicClient() if use_llm else NullLLMClient()

    return SignalEngine(
        vertical="rent_stabilization",
        jurisdiction="nyc",
        sources=sources,
        gap_function=RentStabilizationGapFunction(
            min_rent_delta=MIN_RENT_DELTA,
            lookback_days=LISTING_LOOKBACK_DAYS,
            vacancy_bonus_factor=VACANCY_BONUS_FACTOR,
        ),
        rules=RULES,
        interpreter=TieredRuleInterpreter(llm=llm),
        scorer=RentStabilizationScorer(),
        store=None,
    )
