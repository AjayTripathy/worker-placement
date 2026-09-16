"""Materiality derivation and re-derivation.

Materiality is a Pydantic model on Claim with three statuses: known, estimated,
unclear. It drives whether to spend money on paid sources for a claim.

Three passes:
  1. INFER deal_context from the full set of extracted claims (asset_count,
     deal_size_usd, mode). This is what makes the system productizable —
     the operator shouldn't have to hand-enter portfolio metadata.
  2. INITIAL materiality from the claim alone, using predicate-specific rules
     and the inferred deal_context.
  3. RE-DERIVATION after free sources return — observation evidence can upgrade
     Unclear → Known/Estimated (sponsor failure → 100% of deal, etc.)
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from .connectors.base import ConnectorResult
from .schemas import Claim, Materiality


# Default cap rate inverse used for income-based materiality (8% cap → 12.5x multiplier)
INCOME_TO_VALUE_MULTIPLE = 12.5


# Predicates that explicitly express the size of the offering/fund/raise
DEAL_SIZE_PREDICATES = {
    "raise_amount", "fund_size", "offering_size", "commitment_size",
    "total_capital_raise", "investment_amount", "loan_amount",
}


# Corporate-suffix tokens used both to RECOGNISE an entity-shaped subject and to
# strip down to its distinctive core so "American Housing Corp" and "The American
# Housing Corporation" collapse to the same issuer key.
_ENTITY_SUFFIXES = frozenset({
    "inc", "inc.", "incorporated", "corp", "corp.", "corporation", "co", "co.",
    "company", "llc", "l.l.c.", "lp", "l.p.", "ltd", "limited", "holdings",
    "labs", "technologies", "technology", "partners", "capital", "ventures",
    "group", "trust", "fund",
})
_LEADING_ARTICLES = frozenset({"the", "a", "an"})


def _entity_core(name: str) -> str:
    """Distinctive name core with leading articles and trailing corporate
    suffixes stripped: 'The American Housing Corporation' -> 'american housing'."""
    toks = re.sub(r"[^a-z0-9 ]+", " ", (name or "").lower()).split()
    while toks and toks[0] in _LEADING_ARTICLES:
        toks.pop(0)
    while toks and toks[-1] in _ENTITY_SUFFIXES:
        toks.pop()
    return " ".join(toks)


def _looks_like_entity(name: str) -> bool:
    """Heuristic: a subject is entity-shaped if it carries a corporate suffix or
    is a Title-Cased multi-word proper noun (excludes generic row labels like
    'Factory 1', sentence fragments, and bare numbers)."""
    s = (name or "").strip()
    if not s or any(ch.isdigit() for ch in s):
        return False
    toks = s.split()
    if not (1 <= len(toks) <= 6):
        return False
    low = [re.sub(r"[^a-z0-9.]+", "", t.lower()) for t in toks]
    if any(t in _ENTITY_SUFFIXES for t in low):
        return True
    # Title-cased multi-word proper noun (e.g. "American Housing")
    cap = [t for t in toks if t[:1].isupper()]
    return len(toks) >= 2 and len(cap) >= 2


def infer_deal_context(typed_claims: list[dict]) -> dict:
    """Auto-derive deal_context from extracted claims so the operator doesn't
    have to hand-enter portfolio metadata.

    Currently infers:
      - asset_count: count of distinct PARCEL referent subjects
      - deal_size_usd: explicit deal-size predicate, if extracted
      - issuer_name: most-frequent entity-shaped subject (normalized core), so the
        Stage-1.5 resolver has a real-world anchor for relative claims like
        'Factory 1'. This is the field that was empty and starved the AHC factory
        resolution.
      - mode: 'usd' if deal_size_usd inferred, else 'pct' if asset_count inferred,
              else 'unknown'

    Deliberately does NOT infer a single deal-level city/state: a multi-project
    deal (AHC spans Austin/Bozeman/Miami/LA/Aspen) has no one city, and a
    most-frequent pick would mis-anchor a relative subject to the wrong place.
    Per-claim scope already carries the right city for claims that have one.
    """
    parcel_subjects: set[str] = set()
    deal_size_usd: Optional[float] = None
    parcel_addresses: set[str] = set()
    # issuer inference: count entity-shaped subjects by distinctive core, but keep
    # a representative surface form (the longest seen) to hand back as issuer_name.
    issuer_core_counts: Counter = Counter()
    issuer_surface: dict[str, str] = {}

    for c in typed_claims:
        rt = (c.get("referent_type") or "").lower()
        subj = (c.get("subject") or "").strip()
        if rt == "parcel" and subj:
            parcel_subjects.add(subj.lower())
        # Also catch parcel-flavored claims via scope.address
        scope = c.get("scope") or {}
        addr = scope.get("address") or scope.get("property_address")
        if addr and isinstance(addr, str):
            parcel_addresses.add(addr.strip().lower())
        # Issuer inference (referent_type is often absent on raw Stage-1.5 claims,
        # so key off subject shape, not the type tag).
        if subj and (rt in ("", "sponsor", "company", "entity", "issuer")) and _looks_like_entity(subj):
            core = _entity_core(subj)
            if core and len(core) >= 3:
                issuer_core_counts[core] += 1
                prev = issuer_surface.get(core)
                if prev is None or len(subj) > len(prev):
                    issuer_surface[core] = subj
        # Deal-size signals
        pred = (c.get("predicate") or "").lower()
        if pred in DEAL_SIZE_PREDICATES:
            try:
                v = float(c.get("object_value"))
                if deal_size_usd is None or v > deal_size_usd:
                    deal_size_usd = v
            except (ValueError, TypeError):
                pass

    asset_count = max(len(parcel_subjects), len(parcel_addresses))

    ctx: dict = {}
    if asset_count > 0:
        ctx["asset_count"] = asset_count
    if deal_size_usd is not None:
        ctx["deal_size_usd"] = deal_size_usd
        ctx["mode"] = "usd"
    elif asset_count > 0:
        ctx["mode"] = "pct"
    else:
        ctx["mode"] = "unknown"
    if issuer_core_counts:
        top_core, _ = issuer_core_counts.most_common(1)[0]
        ctx["issuer_name"] = issuer_surface[top_core]
    ctx["_inferred"] = True  # marker so downstream knows this wasn't operator-set
    return ctx


def derive_initial(claim: Claim, deal_context: Optional[dict] = None) -> Materiality:
    """First-pass materiality from claim alone, before any source has been queried.

    deal_context (optional):
      - 'deal_size_usd': float       — enables USD-denominated materiality
      - 'asset_count': int           — enables pct-denominated materiality (1/N share)
      - 'mode': 'usd' | 'pct'        — explicit mode override; default = whichever
                                       context fields are populated, USD wins on tie

    Sponsor / structural claims default to 100% of deal in pct mode; deal_size_usd
    in USD mode. Property-level claims default to 1/asset_count in pct mode;
    claim_value in USD mode.
    """
    pred = claim.predicate
    val = claim.object_value
    ctx = deal_context or {}
    deal_size_usd = ctx.get("deal_size_usd")
    asset_count = ctx.get("asset_count")
    mode = ctx.get("mode") or ("usd" if deal_size_usd else ("pct" if asset_count else "unknown"))

    try:
        nval = float(val) if val is not None else None
    except (ValueError, TypeError):
        nval = None

    # ── RAISE AMOUNT (venture fund-raise verification) ───────────────────
    if pred == "raise_amount" and nval is not None:
        return Materiality(status="known", estimated_usd=nval,
                           derivation="raise_amount = claim value")

    # ── ACQUISITION PRICE ────────────────────────────────────────────────
    if pred == "acquired_at_price":
        if mode == "usd" and nval is not None:
            return Materiality(status="known", estimated_usd=nval,
                               derivation="acquisition price = claim value")
        if mode == "pct" and asset_count:
            return Materiality(status="known", estimated_pct=1.0/asset_count,
                               derivation=f"1 of {asset_count} properties = {100/asset_count:.2f}%")
        if nval is not None:
            return Materiality(status="known", estimated_usd=nval,
                               derivation="acquisition price = claim value (no portfolio context)")
        return Materiality(status="unclear", derivation="acquisition price not numeric")

    # ── RENT ─────────────────────────────────────────────────────────────
    if pred in ("charges_rent", "listed_rent") and nval is not None:
        annual = nval * 12 if (claim.object_unit or "").endswith("/mo") else nval
        if mode == "pct" and asset_count:
            return Materiality(status="estimated", estimated_pct=1.0/asset_count,
                               derivation=f"per-property rent → 1/{asset_count} share")
        return Materiality(status="estimated", estimated_usd=annual * INCOME_TO_VALUE_MULTIPLE,
                           derivation=f"annual rent × {INCOME_TO_VALUE_MULTIPLE} cap inverse")

    # ── NOI ──────────────────────────────────────────────────────────────
    if pred in ("projects_noi", "projects_cash_flow") and nval is not None:
        if mode == "pct" and asset_count:
            return Materiality(status="estimated", estimated_pct=1.0/asset_count,
                               derivation=f"per-property NOI → 1/{asset_count} share")
        return Materiality(status="estimated", estimated_usd=nval * 10,
                           derivation="NOI × 10 cap inverse")

    # ── REHAB ────────────────────────────────────────────────────────────
    if pred == "rehab_spend_planned":
        return Materiality(status="unclear",
                           derivation="single-property rehab; pattern-level only")

    # ── SPONSOR / STRUCTURAL ─────────────────────────────────────────────
    if pred in ("acquired_at_arms_length", "lien_status_is_clean", "legal_status_is_clean",
                "previously_acquired", "prior_fund_returned_irr"):
        if mode == "usd" and deal_size_usd:
            return Materiality(status="known", estimated_usd=float(deal_size_usd),
                               derivation=f"sponsor/structural claim → deal_size_usd={deal_size_usd}")
        if mode == "pct":
            return Materiality(status="known", estimated_pct=1.0,
                               derivation="sponsor/structural claim → 100% of deal")
        # No context: default to pct=1.0 since these claims are deal-level by nature
        return Materiality(status="estimated", estimated_pct=1.0,
                           derivation="sponsor/structural claim with no deal context → assume 100%")

    # ── VENTURE / GROWTH-STAGE PREDICATES ────────────────────────────────
    # Core thesis claims: factory existence, capacity, software, key product
    if pred in ("operates_industrial_facility", "factory_planned_capacity", "factory_current_capacity",
                "software_in_production", "registered_as_entity",
                "current_round_pre_money", "current_round_size",
                "manufacturing_cycle_time", "install_cycle_time",
                "current_build_cost_per_sqft", "target_build_cost_per_sqft",
                "current_gross_margin", "target_gross_margin"):
        if deal_size_usd:
            return Materiality(status="known", estimated_usd=float(deal_size_usd),
                               derivation=f"venture core-thesis claim → deal_size_usd={deal_size_usd}")
        return Materiality(status="known", estimated_pct=1.0,
                           derivation="venture core-thesis claim → 100% of deal")

    # Corroborating claims: prior rounds, team backgrounds, pipeline projects
    if pred in ("prior_round_post_money_valuation", "prior_round_raise_amount",
                "prior_round_lead_investor", "team_member_prior_employer",
                "founder_prior_role", "pipeline_project_count_units"):
        if deal_size_usd:
            return Materiality(status="estimated", estimated_usd=float(deal_size_usd) * 0.5,
                               derivation=f"venture corroborating claim → 50% × deal_size")
        return Materiality(status="estimated", estimated_pct=0.5,
                           derivation="venture corroborating claim → 50% of deal")

    # Comparable / market benchmark claims (lower individual weight)
    if pred in ("comparable_local_hard_cost", "shipping_cost_advantage",
                "target_ebitda_margin_of_gross_profit", "projected_fy31_revenue",
                "projected_fy31_gross_margin", "projected_moic"):
        if deal_size_usd:
            return Materiality(status="estimated", estimated_usd=float(deal_size_usd) * 0.25,
                               derivation=f"venture benchmark claim → 25% × deal_size")
        return Materiality(status="estimated", estimated_pct=0.25,
                           derivation="venture benchmark claim → 25% of deal")

    return Materiality(status="unclear", derivation=f"no derivation rule for predicate '{pred}'")


def rederive_after_free_pass(
    claim: Claim,
    initial: Materiality,
    free_results: list[ConnectorResult],
    deal_context: Optional[dict] = None,
) -> Materiality:
    """Use free-source observations to upgrade Unclear materiality to Known.

    Triggers:
      - Any FAIL/NOT_FOUND on a sponsor-related claim → upgrade to deal_size
      - 'no record found' on an acquisition claim with a numeric value → upgrade to claim value
      - Conflict between sources → upgrade so paid sources can break the tie

    If no upgrade trigger fires, return the initial materiality unchanged.
    """
    if initial.status != "unclear":
        return initial  # only re-derive Unclear claims

    # Did any source fail with NOT_FOUND? (e.g., 'no SoS registration found' is a smoking gun)
    not_found = [r for r in free_results if not r.success and r.error_kind and r.error_kind.value == "not_found"]
    failed = [r for r in free_results if not r.success]

    ctx = deal_context or {}
    deal_size_usd = ctx.get("deal_size_usd")
    asset_count = ctx.get("asset_count")

    # Sponsor-related predicates: any failure to verify becomes deal-level material
    sponsor_predicates = {
        "previously_acquired", "legal_status_is_clean", "prior_fund_returned_irr",
        "registered_as_entity", "acquired_at_arms_length",
    }
    if claim.predicate in sponsor_predicates and (not_found or failed):
        if deal_size_usd:
            return Materiality(status="known", estimated_usd=float(deal_size_usd),
                               derivation=f"sponsor verification failed against {len(failed)} sources → deal_size")
        # Pct mode: sponsor failure = 100% of deal
        return Materiality(status="known", estimated_pct=1.0,
                           derivation=f"sponsor verification failed against {len(failed)} sources → 100% of deal")

    # Acquisition-price claim where deed lookup found no record → claim value at risk
    if claim.predicate == "acquired_at_price" and not_found:
        try:
            cv = float(claim.object_value)
            return Materiality(status="known", estimated_usd=cv,
                               derivation="deed lookup returned no record → full claim value at risk")
        except (ValueError, TypeError):
            pass
        if asset_count:
            return Materiality(status="known", estimated_pct=1.0/asset_count,
                               derivation=f"deed not found → 1/{asset_count} property at risk")

    return initial
