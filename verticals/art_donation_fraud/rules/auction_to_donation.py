"""
Auction-to-donation match rule (compiled).

Fires when a museum gift is plausibly preceded by a recent auction acquisition
by the same donor, in a high-value classification, within a 36-month window.
Per IRC §170(e)(1)(A) and Treas. Reg. §1.170A-13(c), the auction purchase price
is the most directly comparable market evidence for the claimed FMV deduction.

Without a paid auction-comp connector (Artnet/Artprice/MutualArt), this rule
fires on STRUCTURAL features of the donation portfolio rather than per-work
auction match. It surfaces high-risk donor archetypes:
  - high-volume living-collector clusters in Modern/Contemporary departments
  - donations concentrated in a single tax year (bunching pattern)
  - donations of works by artists currently appreciating in market
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["art_donation_claimed"],
    "asset_classes": ["art_donation_tax"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Auction-to-donation match rule (compiled).",
}

from decimal import Decimal

from core.models import GapResult, Record, RuleMatch, SignalRule


# Departments / classifications where auction-comparable values exist and
# claimed FMV is most subject to inflation. Excludes "the artist" donations
# (no purchase-and-donate fraud pattern when artist donates own work).
HIGH_MARKET_VOLATILITY = {
    "Modern and Contemporary Art", "Modern Art",
    "European Paintings",
    "American Paintings and Sculpture",
    "Painting & Sculpture",
}


def apply(rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
    meta = gap.metadata

    # Pull cohort features prepared by the gap function
    portfolio_works = meta.get("portfolio_works", 0)
    portfolio_years = meta.get("portfolio_years", 0)
    high_vol_share  = meta.get("portfolio_high_vol_share", 0.0)
    cluster_year_share = meta.get("portfolio_cluster_year_share", 0.0)
    donor = meta.get("donor_name_normalized", "")
    is_artist_self = donor in {"THE ARTIST", "THE DONOR"}

    if is_artist_self:
        return RuleMatch(
            rule=rule, matched=False, confidence=0.0,
            gap_adjustment=Decimal(0),
            explanation="Artist-self-donation — IRC §170(e)(1)(A) reduces deduction to basis for ordinary-income property held by creator; no FMV-inflation fraud shape.",
            interpreter="compiled",
        )

    # Heuristic: fires on high-volume, market-volatile, time-concentrated patterns
    score = 0
    rationale = []
    if portfolio_works >= 25:
        score += 1; rationale.append(f"high-volume donor ({portfolio_works} works)")
    if high_vol_share >= 0.5:
        score += 1; rationale.append(f"≥50% in market-volatile depts ({high_vol_share:.0%})")
    if cluster_year_share >= 0.6 and portfolio_works >= 10:
        score += 1; rationale.append(f"clustering: {cluster_year_share:.0%} of gifts in one tax year")
    if portfolio_works >= 100:
        score += 1; rationale.append("portfolio-scale donor (≥100 works)")

    matched = score >= 2

    return RuleMatch(
        rule=rule,
        matched=matched,
        confidence=min(0.5 + 0.15 * score, 0.95) if matched else 0.0,
        gap_adjustment=Decimal(0),
        explanation=(
            f"Pattern flags: {'; '.join(rationale) if rationale else 'none'}. "
            f"Per IRC §170(e)(1)(A) and Treas. Reg. §1.170A-13(c), the appraised "
            f"FMV underlying these gifts must reconcile to arm's-length auction "
            f"comparables. Per-work confirmation requires an auction-comp lookup "
            f"(Artnet, Artprice, or Christie's/Sotheby's lot archives — see "
            f"`audit_v1/connectors_to_add.md`)."
            if matched
            else f"Pattern features below threshold (score={score}/4: {'; '.join(rationale) or 'no flags'})"
        ),
        interpreter="compiled",
    )
