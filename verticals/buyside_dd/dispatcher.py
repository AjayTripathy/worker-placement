"""Policy-driven dispatcher.

For each claim:
  1. Derive initial materiality (claim alone)
  2. Sort applicable sources by (authority_tier asc, cost asc)
  3. FREE PASS: dispatch every free source (subject to per-claim call cap and time budget)
     — runs regardless of materiality, because free signal is asymmetric
  4. Re-derive materiality from free observations (Unclear → Known when warranted)
  5. PAID PASS: only if materiality.status != 'unclear' AND value ≥ paid_source_floor
     AND policy allows paid sources AND budget allows
  6. Set StopReason on the result tuple so the comparator can build a defensible Finding

Termination per claim:
  CONVERGED  — count of successful observations meets policy.convergence_by_tier
  EXHAUSTED  — all applicable sources tried, no convergence
  IMMATERIAL — known materiality < floor; paid sources skipped
  DEFERRED   — unclear materiality after free pass; paid skipped, human triage queued
  BUDGET_HIT — run-level cost or time cap hit before claim resolved
  UNREACHABLE— all sources failed (network/auth)
  NOT_DISPATCHED — no f-rule + no source found, never queried
"""
from __future__ import annotations

import importlib
import inspect
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from .budget import BudgetState
from .connectors.base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ErrorKind,
)
from .materiality import derive_initial, rederive_after_free_pass
from .policy import RunPolicy, STANDARD
from .schemas import (
    ClaimWithSources,
    MSource,
    Materiality,
    StopReason,
    TypedClaim,
    ReferentType,
)


# ─────────────────────────────────────────────────────────────────────────────
# Connector loading (cached)
# ─────────────────────────────────────────────────────────────────────────────
_CONNECTOR_CACHE: dict[str, Optional[BaseConnector]] = {}

_US_STATES = frozenset(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO "
    "MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split()
)


def load_connector(module_path: Optional[str]) -> Optional[BaseConnector]:
    if not module_path:
        return None
    if module_path in _CONNECTOR_CACHE:
        return _CONNECTOR_CACHE[module_path]
    candidates = [
        f"verticals.buyside_dd.{module_path}",
        module_path,
        f"verticals.buyside_dd.connectors.{module_path.rsplit('.', 1)[-1]}",
    ]
    for path in candidates:
        try:
            mod = importlib.import_module(path)
        except (ImportError, ModuleNotFoundError):
            continue
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if obj is BaseConnector:
                continue
            if issubclass(obj, BaseConnector) and obj.__module__ == mod.__name__:
                inst = obj()
                _CONNECTOR_CACHE[module_path] = inst
                return inst
    _CONNECTOR_CACHE[module_path] = None
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Request building
# ─────────────────────────────────────────────────────────────────────────────
def build_request(typed_claim: TypedClaim, source: MSource) -> ConnectorRequest:
    claim = typed_claim.claim
    scope = claim.scope or {}
    extra: dict = {}

    address = scope.get("address") or scope.get("property_address")
    # If the claim's PREDICATE itself names an address (e.g. "located_at_address",
    # "owns_property_at", "filed_permit_for"), the object_value IS the address —
    # promote it so downstream connectors get an address-mode query instead of
    # falling back to entity-name search. Fixes the false-negative pattern where
    # tenants don't appear in permit databases (permits are filed by GCs and
    # property owners, not tenants) so an address-keyed query is needed.
    if not address and isinstance(claim.object_value, str):
        addr_predicates = (
            "located_at_address", "address_is", "owns_property_at",
            "filed_permit_for", "operates_at_address", "headquartered_at",
            "factory_address", "facility_address",
        )
        if any(p in claim.predicate for p in addr_predicates):
            address = claim.object_value
    parcel_id = scope.get("parcel_id") or typed_claim.referent_id
    state = scope.get("state")
    city = scope.get("city")
    zip_code = scope.get("zip") or scope.get("zip_code")

    # State propagation: an entity-resolution child keyed on a street address
    # (e.g. "4422 Supply Ct, Austin TX 78744") carries the state in the address
    # string but NOT in scope.state — so OSHA/permit connectors that filter by
    # State silently fall back to "All". Parse it from the address when absent so
    # the resolved-facility query is correctly scoped.
    if not state:
        addr_like = address if isinstance(address, str) else None
        if not addr_like and isinstance(claim.object_value, str):
            addr_like = claim.object_value
        if addr_like:
            m = re.search(r",?\s*([A-Z]{2})\s+\d{5}(?:-\d{4})?\b", addr_like)
            if not m:
                m = re.search(r",\s*([A-Z]{2})\b", addr_like)
            if m and m.group(1) in _US_STATES:
                state = m.group(1)

    # Pass subject as both entity_name and person_name fallback so connectors
    # that need either can pick — the per-connector logic decides what to use.
    # Without this, BUILDING/PARCEL claims with a company subject can't query
    # entity-keyed sources (austin_permits, OSHA, etc.) and fail with UNSUPPORTED.
    entity_name = None
    person_name = None
    geographic_area = None
    if typed_claim.referent_type == ReferentType.PERSON:
        person_name = claim.subject
    elif typed_claim.referent_type == ReferentType.GEOGRAPHIC_AREA:
        geographic_area = claim.subject
    else:
        # Default: pass subject as entity_name for ENTITY/BUILDING/PARCEL/EVENT/etc.
        # Connectors that require an address will still be able to fall back to
        # entity_name for permit-applicant style queries.
        entity_name = claim.subject

    year = None
    tp = scope.get("time_period") or scope.get("year")
    if isinstance(tp, int):
        year = tp
    elif isinstance(tp, str) and tp.isdigit() and len(tp) == 4:
        year = int(tp)

    if source.source_id == "wprdc_allegheny_assessment":
        extra["table"] = "assessment"
    elif source.source_id == "wprdc_allegheny_sales":
        extra["table"] = "sales"
    elif source.source_id == "sec_edgar_company":
        extra["edgar_mode"] = "company"
    elif source.source_id == "sec_edgar_form_d":
        extra["edgar_mode"] = "form_d_detail"
        # CIK is required for form_d_detail; pull from claim.scope if present.
        if scope.get("cik"):
            extra["cik"] = str(scope["cik"])
        if scope.get("accession"):
            extra["accession"] = str(scope["accession"])

    return ConnectorRequest(
        address=address,
        parcel_id=parcel_id,
        entity_name=entity_name,
        person_name=person_name,
        geographic_area=geographic_area or zip_code,
        state=state,
        city=city,
        year=year,
        extra=extra,
    )


def _invoke(source: MSource, request: ConnectorRequest) -> ConnectorResult:
    connector = load_connector(source.connector_module)
    now = datetime.now(timezone.utc)
    if connector is None:
        return ConnectorResult(
            source_id=source.source_id,
            request=request,
            queried_at=now,
            success=False,
            error_kind=ErrorKind.UNSUPPORTED,
            error_detail=f"connector module {source.connector_module} not implemented",
        )
    try:
        result = connector.query(request)
    except Exception as e:
        result = ConnectorResult(
            source_id=source.source_id,
            request=request,
            queried_at=now,
            success=False,
            error_kind=ErrorKind.UNKNOWN,
            error_detail=f"connector raised: {type(e).__name__}: {e}",
        )
    # Canonicalize: a single connector can serve multiple MSource entries
    # (e.g. WPRDC connector serves _sales, _mortgages, _assessment).
    # Stamp the MSource source_id so authority_tier lookups in the comparator work.
    result.source_id = source.source_id
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Convergence
# ─────────────────────────────────────────────────────────────────────────────
def _has_converged(successes_by_tier: dict[int, int], threshold_by_tier: dict[int, int]) -> bool:
    """A claim has 'converged' (in the dispatcher's count-based sense) when, for
    any authority tier, we have enough informative successful observations to
    satisfy that tier's convergence threshold.

    The actual PASS/FAIL/CONFLICT classification is the comparator's job — this
    is just a stopping rule for source dispatch.
    """
    for tier, threshold in threshold_by_tier.items():
        if successes_by_tier.get(tier, 0) >= threshold:
            return True
    return False


def _is_informative(result: ConnectorResult) -> bool:
    """Heuristic: did this connector return data that's actually useful, vs. an
    empty 'we queried successfully but found nothing' response?

    The fix for the convergence bug: a full-text EDGAR search returning
    `filing_count = 0` is a successful query but uninformative. We should keep
    trying other sources at the same tier (e.g., the company-name endpoint)
    rather than declaring convergence on the empty result.

    Treat as informative if any observation has a non-zero numeric value, a
    non-empty list/dict/string, or a True boolean.
    """
    if not result.success or not result.observations:
        return False
    for obs in result.observations:
        v = obs.value
        if v is None:
            continue
        if isinstance(v, bool):
            if v:
                return True
        elif isinstance(v, (int, float)):
            if v > 0:
                return True
        elif isinstance(v, (list, dict, str)):
            if len(v) > 0:
                return True
        else:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Main dispatch entry point
# ─────────────────────────────────────────────────────────────────────────────
class DispatchOutcome:
    """Bundle returned to the comparator: results + stop reason + final materiality."""
    def __init__(
        self,
        results: list[ConnectorResult],
        stop_reason: StopReason,
        materiality: Materiality,
    ):
        self.results = results
        self.stop_reason = stop_reason
        self.materiality = materiality

    def __repr__(self):
        return f"DispatchOutcome(stop={self.stop_reason.value}, mat={self.materiality.status}, n={len(self.results)})"


def dispatch_with_policy(
    claim_with_sources: ClaimWithSources,
    policy: RunPolicy = STANDARD,
    budget: Optional[BudgetState] = None,
    deal_context: Optional[dict] = None,
) -> DispatchOutcome:
    """Policy-driven dispatch: free always; paid gated by materiality + budget."""
    if budget is None:
        budget = BudgetState(max_cost_usd=policy.max_cost_usd, max_wall_time_min=policy.max_wall_time_min)

    sources = claim_with_sources.m_sources
    if not sources:
        return DispatchOutcome([], StopReason.NOT_DISPATCHED,
                               derive_initial(claim_with_sources.typed_claim.claim, deal_context))

    # Step 1: initial materiality
    claim = claim_with_sources.typed_claim.claim
    initial_mat = derive_initial(claim, deal_context)
    claim.materiality = initial_mat

    # Step 2: sort
    sorted_sources = sorted(sources, key=lambda s: (s.authority_tier, s.cost_per_query))
    free_sources = [s for s in sorted_sources if s.is_free]
    paid_sources = [s for s in sorted_sources if not s.is_free]

    successes_by_tier: dict[int, int] = defaultdict(int)
    free_results: list[ConnectorResult] = []
    calls_made = 0

    # Step 3: FREE PASS
    for source in free_sources:
        if budget.time_exhausted:
            return DispatchOutcome(free_results, StopReason.BUDGET_HIT, initial_mat)
        if calls_made >= policy.max_source_calls_per_claim:
            break
        request = build_request(claim_with_sources.typed_claim, source)
        result = _invoke(source, request)
        free_results.append(result)
        budget.record(source.source_id, 0.0)
        calls_made += 1
        if _is_informative(result):
            successes_by_tier[source.authority_tier] += 1
            if _has_converged(successes_by_tier, policy.convergence_by_tier):
                break

    # Step 4: re-derive materiality if free pass produced anything to learn from
    if policy.rederive_materiality_after_free_pass and free_results:
        rederived = rederive_after_free_pass(claim, initial_mat, free_results, deal_context)
        claim.materiality = rederived
    else:
        rederived = initial_mat

    # Step 5: decide on paid escalation
    converged = _has_converged(successes_by_tier, policy.convergence_by_tier)
    any_success = any(r.success for r in free_results)

    if converged:
        return DispatchOutcome(free_results, StopReason.CONVERGED, rederived)

    if not paid_sources or not policy.paid_sources_enabled:
        if not any_success:
            # Free sources existed but all failed
            return DispatchOutcome(free_results, StopReason.UNREACHABLE, rederived)
        return DispatchOutcome(free_results, StopReason.EXHAUSTED, rederived)

    if rederived.status == "unclear":
        # Can't justify paid spend; defer to human triage
        return DispatchOutcome(free_results, StopReason.DEFERRED, rederived)

    # Materiality gate: pass if EITHER the USD or pct floor is met (whichever
    # the materiality is denominated in). Both are checked when both fields populated.
    usd_passes = (rederived.estimated_usd or 0) >= policy.paid_source_floor_usd
    pct_passes = (rederived.estimated_pct or 0) >= policy.paid_source_floor_pct
    has_usd = rederived.estimated_usd is not None
    has_pct = rederived.estimated_pct is not None
    if has_usd and has_pct:
        passes = usd_passes or pct_passes
    elif has_usd:
        passes = usd_passes
    elif has_pct:
        passes = pct_passes
    else:
        passes = False
    if not passes:
        return DispatchOutcome(free_results, StopReason.IMMATERIAL, rederived)

    # Step 6: PAID PASS
    paid_results: list[ConnectorResult] = []
    for source in paid_sources:
        if budget.is_exhausted():
            return DispatchOutcome(free_results + paid_results, StopReason.BUDGET_HIT, rederived)
        if calls_made >= policy.max_source_calls_per_claim:
            break
        if source.access_pattern == "foia" and not policy.foia_enabled:
            continue
        if not budget.can_afford(source.cost_per_query):
            continue
        request = build_request(claim_with_sources.typed_claim, source)
        result = _invoke(source, request)
        paid_results.append(result)
        budget.record(source.source_id, source.cost_per_query)
        calls_made += 1
        if _is_informative(result):
            successes_by_tier[source.authority_tier] += 1
            if _has_converged(successes_by_tier, policy.convergence_by_tier):
                return DispatchOutcome(free_results + paid_results, StopReason.CONVERGED, rederived)

    all_results = free_results + paid_results
    if not any(r.success for r in all_results):
        return DispatchOutcome(all_results, StopReason.UNREACHABLE, rederived)
    return DispatchOutcome(all_results, StopReason.EXHAUSTED, rederived)


# ─────────────────────────────────────────────────────────────────────────────
# Backward-compatible thin wrapper
# ─────────────────────────────────────────────────────────────────────────────
def dispatch(claim_with_sources: ClaimWithSources) -> list[ConnectorResult]:
    """Old-API dispatch — used by demos. Prefer dispatch_with_policy()."""
    outcome = dispatch_with_policy(claim_with_sources, policy=STANDARD)
    return outcome.results


def coverage_report(claims_with_sources: list[ClaimWithSources]) -> dict:
    total = len(claims_with_sources)
    no_sources = 0
    only_unimplemented = 0
    has_implemented = 0
    for cws in claims_with_sources:
        if not cws.m_sources:
            no_sources += 1
            continue
        implemented = [s for s in cws.m_sources if load_connector(s.connector_module) is not None]
        if implemented:
            has_implemented += 1
        else:
            only_unimplemented += 1
    return {
        "total_claims": total,
        "claims_with_implemented_connector": has_implemented,
        "claims_with_only_unimplemented_sources": only_unimplemented,
        "claims_with_no_source": no_sources,
        "implementation_coverage_pct": round(100 * has_implemented / total, 1) if total else 0.0,
    }


if __name__ == "__main__":
    # Demo: TRIAGE policy on synthetic FCRE2-style claims
    from .schemas import Claim, TypedClaim, FRule, ClaimWithSources
    from .source_atlas import find_sources
    from .f_library import find_rules
    from .policy import TRIAGE, STANDARD, DEEP

    claims_input = [
        ("722 Eureka St", "acquired_at_price", 67500, "Allegheny_County_PA"),
        ("1932 Beech St", "acquired_at_price", 45000, "Allegheny_County_PA"),
    ]

    for policy in (TRIAGE, STANDARD):
        print(f"\n══ Policy: {policy.name} (max_cost=${policy.max_cost_usd}, paid={policy.paid_sources_enabled}) ══")
        budget = BudgetState(max_cost_usd=policy.max_cost_usd, max_wall_time_min=policy.max_wall_time_min)
        for subject, predicate, value, juris in claims_input:
            claim = Claim(
                claim_id=subject[:6],
                source_doc="demo",
                source_quote=f"{subject} - ${value}",
                subject=subject,
                predicate=predicate,
                object_value=value,
                object_unit="USD",
                scope={"address": f"{subject}, Pittsburgh PA", "state": "PA", "city": "Pittsburgh"},
            )
            tc = TypedClaim(claim=claim, referent_type=ReferentType.PARCEL,
                            referent_attributes=["deed_records"], jurisdiction=juris)
            cws = ClaimWithSources(
                typed_claim=tc,
                f_rules=find_rules(predicate, ReferentType.PARCEL),
                m_sources=find_sources(ReferentType.PARCEL, "deed_records", juris),
            )
            outcome = dispatch_with_policy(cws, policy=policy, budget=budget,
                                          deal_context={"deal_size_usd": 30_000_000})
            print(f"  {subject:20s} stop={outcome.stop_reason.value:12s} "
                  f"mat={outcome.materiality.status:9s} ${outcome.materiality.estimated_usd or 0:,.0f}  "
                  f"obs={sum(1 for r in outcome.results if r.success)}/{len(outcome.results)}")
        print(f"  budget: {budget.summary()['spent_usd']}/{budget.summary()['max_cost_usd']} USD; calls={budget.summary()['calls_made']}")
