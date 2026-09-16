"""Comparator: (TypedClaim, FRule, DispatchOutcome) → Finding.

Builds a Finding with:
  - severity (PASS/MINOR/MODERATE/SEVERE/CRITICAL/UNVERIFIABLE per f-rule thresholds)
  - confidence (0-1, derived from authority tier of agreeing sources)
  - stop_reason (CONVERGED/EXHAUSTED/IMMATERIAL/DEFERRED/BUDGET_HIT/UNREACHABLE)
  - materiality_at_stop (re-derived if observations upgraded it)
  - exposure_estimate_usd (clamped by materiality if it disagrees with raw divergence)
  - evidence_trail (step-by-step provenance for the report)
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from .connectors.base import ConnectorObservation, ConnectorResult
from .dispatcher import DispatchOutcome
from .spv_form_d import assess_raise_via_conduits
from .schemas import (
    Claim,
    FRule,
    Finding,
    MSource,
    Materiality,
    Observation,
    ReferentType,
    Severity,
    StopReason,
    TypedClaim,
)


# Map predicate → which observation attribute(s) the comparator should look at,
# ordered by preference. The dispatcher's connectors emit observations under
# stable attribute names; this table is the contract between them.
PREDICATE_TO_ATTR: dict[str, list[tuple[str, Optional[str]]]] = {
    "acquired_at_price": [
        ("sale[0].deed_consideration", "USD"),  # WPRDC
        ("mls_sale_price", "USD"),
    ],
    "charges_rent": [
        ("hud_fmr_3br", "USD/month"),
        ("acs_median_rent_3br", "USD/month"),
    ],
    "property_market_value": [
        ("assessor_market_value_total", "USD"),
    ],
    "previously_acquired": [
        ("form_d[0].totalAmountSold", "USD"),  # if form_d_detail dispatched
        ("edgar_company_match_count", None),
        ("edgar_filing_count", None),
        ("patent_count", None),
        ("pa_corp_match_count", None),
        ("tx_corp_match_count", None),
    ],
    "raise_amount": [
        ("form_d[0].totalAmountSold", "USD"),
        ("form_d[0].totalOfferingAmount", "USD"),
    ],
    "legal_status_is_clean": [
        ("edgar_filing_count", None),
    ],
    # ── VENTURE-FLAVOR PREDICATES ──────────────────────────────────────────
    "registered_as_entity": [
        ("tx_corp_match_count", None),
        ("edgar_company_match_count", None),
        ("pa_corp_match_count", None),
    ],
    "operates_industrial_facility": [
        ("austin_permit_count", None),
        ("bozeman_permit_count", None),
        ("abq_permit_count", None),
        ("osha_establishment_count", None),
    ],
    "factory_planned_capacity": [
        # No external M; only internal-consistency check applies.
    ],
    # ── ADDRESS-RESOLVED FACTORY VERIFICATION ──────────────────────────────
    # The relevant observation is permit_count for the address. If permit_count
    # > 0 at the claimed address, the address is corroborated. The comparator's
    # special-case logic (below) tiers this further: recent industrial permits
    # → strong corroboration; only old permits → moderate; zero → SEVERE.
    "located_at_address": [
        ("austin_permit_count", None),
        ("bozeman_permit_count", None),
        ("abq_permit_count", None),
    ],
    # ── PARENT-ENTITY FORM D EXISTENCE ─────────────────────────────────────
    # Boolean claim: "did parent file Form D?" Uses EDGAR company-name match
    # count. Zero → SEVERE (Reg D compliance question OR direct sales never closed).
    "filed_form_d_for_direct_safes": [
        ("edgar_company_match_count", None),
        ("edgar_filing_count", None),
    ],
    # ── LEAD INVESTOR VISIBILITY ───────────────────────────────────────────
    # Search EDGAR for the named lead investor. Zero EDGAR hits → SEVERE
    # (the lead is named in the deck but invisible in SEC filings).
    "led_investment_round": [
        ("edgar_company_match_count", None),
        ("edgar_filing_count", None),
        ("form_d[0].relatedPersons", None),  # future: when Form D parser exposes this
    ],
    # ── VALUATION CAP (SAFE-derived; needs safe_pdf_parser connector) ──────
    "valuation_cap": [
        ("safe.cap", "USD"),
    ],
    # ── TOTAL PAID BY INVESTOR (SAFE-derived; needs safe aggregator) ───────
    "total_paid_to_AHC": [
        ("safe.total_purchase_amount", "USD"),
    ],
    # ── OWNS PROPERTY AT (address-keyed property record check) ─────────────
    "owns_property_at": [
        ("austin_permit_count", None),
        ("tx_corp_match_count", None),
    ],
    # ── FILED PERMIT FOR (address-keyed contractor verification) ───────────
    "filed_permit_for": [
        ("austin_permit_count", None),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Predicate polarity
# ─────────────────────────────────────────────────────────────────────────────
# Negative-polarity ("absence") predicates assert that NOTHING adverse exists:
# "the entity is clean," "there is no undisclosed litigation," etc. For these,
# the existence test inverts. A boolean True claim against ZERO records is NOT a
# denial-of-existence CRITICAL — it is the honest hostile-validator outcome
# UNVERIFIABLE, because absence in a partial source (EDGAR full-text, which does
# not cover state courts or a private company's docket) is NOT proof of clean.
# A True claim against >0 adverse records IS a contradiction → SEVERE.
NEGATIVE_POLARITY_PREDICATES = frozenset({
    "legal_status_is_clean",
    "no_undisclosed_litigation",
    "no_material_litigation",
    "no_pending_litigation",
    "no_regulatory_action",
    "no_bankruptcy",
    "no_liens",
})


def _is_negative_polarity(predicate: Optional[str]) -> bool:
    """True if the predicate asserts the ABSENCE of something adverse."""
    if not predicate:
        return False
    p = predicate.strip().lower()
    if p in NEGATIVE_POLARITY_PREDICATES:
        return True
    return (
        p.startswith("no_")
        or p.startswith("free_of_")
        or p.startswith("absence_of_")
        or p.endswith("_is_clean")
        or p.endswith("_clean")
    )


# ─────────────────────────────────────────────────────────────────────────────
# Confidence
# ─────────────────────────────────────────────────────────────────────────────
TIER_CONFIDENCE_BASE = {1: 1.0, 2: 0.85, 3: 0.70, 4: 0.50, 5: 0.30}


def _compute_confidence(
    results: list[ConnectorResult],
    sources: list[MSource],
    stop_reason: StopReason,
) -> float:
    if stop_reason in (StopReason.NOT_DISPATCHED, StopReason.UNREACHABLE):
        return 0.0
    successes = [r for r in results if r.success and r.observations]
    if not successes:
        return 0.0
    tier_lookup = {s.source_id: s.authority_tier for s in sources}
    tiers = [tier_lookup.get(r.source_id, 5) for r in successes]
    best_tier = min(tiers) if tiers else 5
    base = TIER_CONFIDENCE_BASE.get(best_tier, 0.3)
    # Modest corroboration bonus
    bonus = min(0.10 * (len(successes) - 1), 0.20)
    # Discount if dispatch ended in DEFERRED or BUDGET_HIT
    if stop_reason in (StopReason.DEFERRED, StopReason.BUDGET_HIT):
        return round(min(1.0, base * 0.6 + bonus), 2)
    if stop_reason == StopReason.IMMATERIAL:
        return round(min(1.0, base * 0.85 + bonus), 2)
    return round(min(1.0, base + bonus), 2)


# ─────────────────────────────────────────────────────────────────────────────
# Severity classification
# ─────────────────────────────────────────────────────────────────────────────
def _classify(divergence_pct: Optional[float], thresholds: dict[str, float]) -> Severity:
    if divergence_pct is None:
        return Severity.UNVERIFIABLE
    ordered = sorted(thresholds.items(), key=lambda kv: kv[1])
    for label, bound in ordered:
        if divergence_pct <= bound:
            try:
                return Severity(label.lower())
            except ValueError:
                return Severity.MODERATE
    try:
        return Severity(ordered[-1][0].lower())
    except (IndexError, ValueError):
        return Severity.SEVERE


# ─────────────────────────────────────────────────────────────────────────────
# Observation selection
# ─────────────────────────────────────────────────────────────────────────────
def _select_best_observation(
    connector_results: list[ConnectorResult],
    attribute_candidates: list[tuple[str, Optional[str]]],
) -> Optional[ConnectorObservation]:
    for attr_pattern, _unit in attribute_candidates:
        for cr in connector_results:
            if not cr.success:
                continue
            for o in cr.observations:
                if o.attribute == attr_pattern or o.attribute.startswith(attr_pattern.split("[")[0] + "["):
                    if o.value is not None:
                        return o
    return None


def _to_obs(co: ConnectorObservation, source_id: str, referent_id: str) -> Observation:
    return Observation(
        source_id=source_id,
        referent_id=referent_id,
        attribute=co.attribute,
        value=co.value,
        fetched_at=co.observation_date or datetime.now(timezone.utc),
        raw_response=str(co.extra)[:500] if co.extra else None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main comparator
# ─────────────────────────────────────────────────────────────────────────────
def compare(
    typed_claim: TypedClaim,
    f_rule: FRule,
    outcome: DispatchOutcome,
    sources: list[MSource],
) -> Finding:
    claim = typed_claim.claim
    referent_id = typed_claim.referent_id or claim.subject
    results = outcome.results

    evidence_trail = [
        f"claim: {claim.subject} {claim.predicate} {claim.object_value} {claim.object_unit or ''}".strip(),
        f"f-rule applied: {f_rule.rule_id} ({f_rule.description})",
        f"materiality (initial→final): {claim.materiality.derivation} → "
        f"{outcome.materiality.status}/${outcome.materiality.estimated_usd or 0:,.0f} ({outcome.materiality.derivation})",
        f"stop reason: {outcome.stop_reason.value}",
    ]
    successful = [cr for cr in results if cr.success]
    failed = [cr for cr in results if not cr.success]
    for cr in successful:
        evidence_trail.append(f"queried {cr.source_id}: {len(cr.observations)} observations")
    for cr in failed:
        evidence_trail.append(f"failed {cr.source_id}: {cr.error_kind} {cr.error_detail}")

    confidence = _compute_confidence(results, sources, outcome.stop_reason)

    attr_candidates = PREDICATE_TO_ATTR.get(f_rule.predicate, [])
    obs = _select_best_observation(results, attr_candidates)

    # ── SPV-conduit-aware reconciliation for venture raises ──────────────────
    # A round funded through Sydecar/AngelList-style series vehicles files Form
    # Ds whose issuer entityName encodes the operating company ("<OpCo> <Month
    # Year> a Series of <X> LLC"). A single conduit's totalAmountSold is a SLICE
    # of the round, so the plain `raise == totalAmountSold` numeric rule mis-flags
    # it as UNVERIFIABLE/divergent. Reconcile conduits as a subset instead, and
    # filter out pooled funds that merely name-collide. Runs BEFORE the generic
    # branches so the conduit verdict wins when an SPV structure is present.
    if f_rule.predicate == "raise_amount":
        form_d_dicts = [o.value for cr in successful for o in cr.observations
                        if str(o.attribute).startswith("form_d[")
                        and "." not in str(o.attribute) and isinstance(o.value, dict)]
        if form_d_dicts:
            op_name = claim.subject
            if isinstance(op_name, str) and op_name.strip().isdigit():
                # Resolved child keyed on a bare CIK — recover the operating name
                # from the resolution provenance in the source_quote.
                m = re.search(r"\('([^']+)'\)", claim.source_quote or "")
                if m:
                    op_name = m.group(1)
            verdict = assess_raise_via_conduits(op_name, claim.object_value, form_d_dicts)
            if verdict is not None:
                summ = verdict["summary"]
                conduit_line = "; ".join(
                    f"{c['issuer']} (CIK {c['cik']}, ${(c['sold'] or 0):,.0f}, admin={c['admin']})"
                    for c in summ["attributable"]) or "none"
                trail = evidence_trail + [
                    f"SPV-conduit reconciliation: {verdict['note']}",
                    f"attributable conduits: {conduit_line}",
                ]
                if summ["unrelated_pooled"]:
                    trail.append("name-collision pooled funds excluded: " + "; ".join(
                        f"{u['issuer']}" for u in summ["unrelated_pooled"]))
                return Finding(
                    claim=claim,
                    referent_type=typed_claim.referent_type,
                    referent_id=referent_id,
                    f_rule_id=f_rule.rule_id,
                    severity=getattr(Severity, verdict["severity"]),
                    confidence=confidence,
                    divergence_pct=verdict["divergence_pct"],
                    stop_reason=outcome.stop_reason,
                    materiality_at_stop=outcome.materiality,
                    evidence_trail=trail,
                    notes="spv-conduit reconciliation",
                    observed_values=[
                        _to_obs(o, cr.source_id, referent_id)
                        for cr in successful for o in cr.observations
                    ],
                )

    if obs is None:
        # No usable observation. But — check if the stop_reason was CONVERGED with
        # all-zero counts: that's an "absence of record" signal that should NOT be
        # silently UNVERIFIABLE. If the claim asserts existence (factory, project,
        # entity) and every source returned a count==0 observation, that's evidence
        # of absence — surface it as SEVERE.
        zero_count_signal = False
        for cr in successful:
            for o in cr.observations:
                if o.attribute.endswith("_count") and o.value == 0:
                    zero_count_signal = True
                    break
        if zero_count_signal and f_rule.predicate in (
            "operates_industrial_facility", "registered_as_entity",
            "previously_acquired", "operates_facility_at",
            # Newly added: existence-of-record claims for SAFE-era venture deals
            "filed_form_d_for_direct_safes",  # absence → Reg D compliance question
            "led_investment_round",            # absence → named lead is invisible
            "located_at_address",              # absence → false address claim
            "owns_property_at",                # absence → false ownership claim
            "filed_permit_for",                # absence → false permit-filer claim
        ):
            return Finding(
                claim=claim,
                referent_type=typed_claim.referent_type,
                referent_id=referent_id,
                f_rule_id=f_rule.rule_id,
                severity=Severity.SEVERE,
                confidence=confidence,
                stop_reason=outcome.stop_reason,
                materiality_at_stop=outcome.materiality,
                evidence_trail=evidence_trail + [
                    f"ABSENCE OF RECORD: every queried source returned count=0 for an existence claim. "
                    f"Either (a) the entity/facility/project doesn't exist as claimed, "
                    f"(b) it operates under a different name we haven't identified, "
                    f"or (c) it's too new/small to have triggered a record."
                ],
                notes="absence-of-record signal on existence claim",
                observed_values=[
                    _to_obs(o, cr.source_id, referent_id)
                    for cr in successful for o in cr.observations
                ],
            )

        if outcome.stop_reason == StopReason.UNREACHABLE:
            severity = Severity.UNVERIFIABLE
            note = "all M sources failed to return data"
        elif outcome.stop_reason in (StopReason.DEFERRED, StopReason.IMMATERIAL):
            severity = Severity.UNVERIFIABLE
            note = f"stopped at {outcome.stop_reason.value} per policy"
        else:
            severity = Severity.UNVERIFIABLE
            note = f"M sources queried but none returned the expected attribute ({[a for a, _ in attr_candidates]})"
        return Finding(
            claim=claim,
            referent_type=typed_claim.referent_type,
            referent_id=referent_id,
            f_rule_id=f_rule.rule_id,
            severity=severity,
            confidence=confidence,
            stop_reason=outcome.stop_reason,
            materiality_at_stop=outcome.materiality,
            evidence_trail=evidence_trail + [note],
            notes=note,
            observed_values=[
                _to_obs(o, cr.source_id, referent_id)
                for cr in successful for o in cr.observations
            ],
        )

    # Numeric divergence — but special-case booleans: a claim of `True` (existence)
    # against an observed count > 0 should be PASS, not "1.0 vs 22 = 95% divergence".
    claim_val = claim.object_value
    # LLM extraction sometimes emits booleans as the strings "true"/"false".
    # Coerce to real bools so the is_boolean_existence branch below fires (an
    # existence claim of True against an observed count of 0 → CRITICAL) instead
    # of falling through to the numeric branch, where float("true") fails and the
    # finding silently degrades to UNVERIFIABLE.
    if isinstance(claim_val, str) and claim_val.strip().lower() in ("true", "false"):
        claim_val = claim_val.strip().lower() == "true"
    observed_val = obs.value
    divergence_abs = None
    divergence_pct = None

    # Special-case: address-shaped predicates with a STRING claim value (the
    # address) and a COUNT observation (permits at that address). Tier the
    # corroboration: any permits → PASS; recent industrial-scope permits →
    # strong PASS; only old permits → MODERATE; zero handled above.
    address_predicates = (
        "located_at_address", "owns_property_at",
        "filed_permit_for", "operates_at_address",
    )
    is_address_corroboration = (
        f_rule.predicate in address_predicates
        and isinstance(claim_val, str)
        and isinstance(observed_val, (int, float))
        and obs.attribute.endswith("_permit_count")
    )
    if is_address_corroboration:
        permit_count = int(observed_val) if observed_val else 0
        # Look at full permit list to score recency / scope
        all_permit_obs = []
        for cr in successful:
            for o in cr.observations:
                if o.attribute.startswith("austin_permit[") and isinstance(o.value, dict):
                    all_permit_obs.append(o.value)
        from datetime import datetime as _dt
        recent_industrial = False
        any_recent = False
        cutoff = _dt.now().year - 2
        for p in all_permit_obs:
            applied = (p.get("applied") or "")[:4]
            if applied.isdigit() and int(applied) >= cutoff:
                any_recent = True
                desc = (p.get("description") or "").lower()
                ptype = (p.get("type") or "").lower()
                if any(k in desc for k in ("amp", "service upgrade", "industrial", "manufacturing", "warehouse", "loading", "fire suppression", "spray booth")):
                    recent_industrial = True
                if any(k in ptype for k in ("electrical", "mechanical", "building")) and "remodel" in (p.get("work_class","") or "").lower():
                    recent_industrial = recent_industrial or any_recent
        if permit_count == 0:
            severity = Severity.SEVERE
            divergence_pct = 1.0
        elif recent_industrial:
            severity = Severity.PASS
            divergence_pct = 0.0
            evidence_trail.append(f"address corroborated: {permit_count} permits at address, including recent industrial-scope work")
        elif any_recent:
            severity = Severity.PASS
            divergence_pct = 0.05
            evidence_trail.append(f"address corroborated: {permit_count} permits at address, recent activity present (not flagged industrial-scope)")
        else:
            severity = Severity.MODERATE
            divergence_pct = 0.5
            evidence_trail.append(f"address exists ({permit_count} historical permits) but no recent build-out activity — claimed operations not corroborated by recent permits")

    # Negative-polarity ("clean" / "no litigation") predicates are handled FIRST
    # and independent of value type — the LLM emits the value inconsistently
    # across runs (boolean `true`, or a descriptive string like
    # "no_material_litigation"), and we must not let that representation decide
    # severity. An absence claim cannot be CONFIRMED from a partial source, and a
    # generic full-text match count is NOT adverse-specific (25 EDGAR hits ≠ 25
    # lawsuits), so the honest default is UNVERIFIABLE. Only an attribute whose
    # name marks it as adverse-specific (litigation/lien/enforcement/…) is
    # allowed to fire SEVERE on a positive count.
    is_negative_polarity = _is_negative_polarity(f_rule.predicate) and not is_address_corroboration
    is_boolean_existence = (
        isinstance(claim_val, bool)
        and not is_address_corroboration
        and not is_negative_polarity
    )
    if is_address_corroboration:
        pass  # handled above
    elif is_negative_polarity:
        adverse_specific_tokens = (
            "litigation", "lawsuit", "docket", "enforcement", "judgment",
            "lien", "bankruptcy", "default", "complaint", "violation", "penalty",
        )
        attr = (obs.attribute or "").lower()
        is_adverse_specific = any(t in attr for t in adverse_specific_tokens)
        observed_count = observed_val if isinstance(observed_val, (int, float)) else (1 if observed_val else 0)
        if is_adverse_specific and observed_count and observed_count > 0:
            severity = Severity.SEVERE
            divergence_pct = 1.0
            evidence_trail.append(
                f"negative-polarity predicate: {observed_count} adverse records "
                f"({obs.attribute}) contradict the 'clean' / 'no-litigation' claim"
            )
        else:
            severity = Severity.UNVERIFIABLE
            divergence_pct = None
            evidence_trail.append(
                "negative-polarity predicate: cannot confirm an absence/clean claim "
                "from a partial, non-adverse-specific source — UNVERIFIABLE (≠ clean)"
            )
    elif is_boolean_existence:
        observed_truthy = bool(observed_val) and (
            observed_val if not isinstance(observed_val, (int, float)) else observed_val > 0
        )
        # Positive-polarity existence:
        # True + (count > 0 OR truthy value) → PASS
        # True + (0 / None / empty) → CRITICAL (denial of existence)
        # False + (count > 0 OR truthy)  → SEVERE (claimed false but found something)
        if claim_val and observed_truthy:
            severity = Severity.PASS
            divergence_pct = 0.0
        elif claim_val and not observed_truthy:
            severity = Severity.CRITICAL
            divergence_pct = 1.0
        elif (not claim_val) and observed_truthy:
            severity = Severity.SEVERE
            divergence_pct = 1.0
        else:
            severity = Severity.PASS
            divergence_pct = 0.0
    else:
        try:
            cv = float(claim_val) if claim_val is not None else None
            ov = float(observed_val) if observed_val is not None else None
            if cv is not None and ov is not None and ov != 0:
                divergence_abs = cv - ov
                divergence_pct = abs(divergence_abs) / abs(ov)
        except (ValueError, TypeError):
            pass
        severity = _classify(divergence_pct, f_rule.severity_thresholds)

    evidence_trail.append(f"observed: {observed_val} from {obs.source_url or 'connector'}")
    if divergence_abs is not None and divergence_pct is not None:
        evidence_trail.append(f"divergence: ${divergence_abs:+,.0f} ({divergence_pct*100:.1f}%)")
    elif divergence_pct is not None:
        evidence_trail.append(f"divergence: {divergence_pct*100:.1f}% (boolean existence check)")

    # Exposure: divergence dollars, clamped by materiality if known
    exposure = abs(divergence_abs) if divergence_abs is not None else None
    if exposure and outcome.materiality.status != "unclear" and outcome.materiality.estimated_usd:
        exposure = min(exposure, outcome.materiality.estimated_usd)

    return Finding(
        claim=claim,
        referent_type=typed_claim.referent_type,
        referent_id=referent_id,
        f_rule_id=f_rule.rule_id,
        expected_value=observed_val,
        observed_values=[
            _to_obs(o, cr.source_id, referent_id)
            for cr in successful for o in cr.observations
        ],
        divergence_absolute=divergence_abs,
        divergence_pct=divergence_pct,
        severity=severity,
        confidence=confidence,
        stop_reason=outcome.stop_reason,
        materiality_at_stop=outcome.materiality,
        evidence_trail=evidence_trail,
        exposure_estimate_usd=exposure,
    )


def compare_all(
    typed_claim: TypedClaim,
    f_rules: list[FRule],
    outcome: DispatchOutcome,
    sources: list[MSource],
) -> list[Finding]:
    return [compare(typed_claim, rule, outcome, sources) for rule in f_rules]


if __name__ == "__main__":
    # End-to-end demo: claim → policy-driven dispatch → comparator → Finding
    from .schemas import Claim, TypedClaim, ClaimWithSources
    from .source_atlas import find_sources
    from .f_library import find_rules
    from .dispatcher import dispatch_with_policy
    from .policy import STANDARD
    from .budget import BudgetState

    claim = Claim(
        claim_id="demo-eureka",
        source_doc="Section 8 housing.pdf",
        source_quote="722 Eureka St — Purchase price $67,500",
        subject="722 Eureka St",
        predicate="acquired_at_price",
        object_value=67500,
        object_unit="USD",
        scope={"address": "722 Eureka St, Pittsburgh PA", "state": "PA", "city": "Pittsburgh"},
    )
    tc = TypedClaim(
        claim=claim, referent_type=ReferentType.PARCEL,
        referent_attributes=["deed_records"], jurisdiction="Allegheny_County_PA",
    )
    sources = find_sources(ReferentType.PARCEL, "deed_records", "Allegheny_County_PA")
    rules = find_rules("acquired_at_price", ReferentType.PARCEL)
    cws = ClaimWithSources(typed_claim=tc, f_rules=rules, m_sources=sources)

    budget = BudgetState(max_cost_usd=STANDARD.max_cost_usd, max_wall_time_min=STANDARD.max_wall_time_min)
    outcome = dispatch_with_policy(cws, policy=STANDARD, budget=budget,
                                   deal_context={"deal_size_usd": 30_000_000})
    findings = compare_all(tc, rules, outcome, sources)

    print(f"DispatchOutcome: {outcome}")
    print()
    for f in findings:
        if f.severity in (Severity.PASS, Severity.MINOR):
            continue
        print(f"=== {f.f_rule_id} ===")
        print(f"  severity:    {f.severity.value}")
        print(f"  confidence:  {f.confidence}")
        print(f"  stop_reason: {f.stop_reason.value}")
        print(f"  materiality: {f.materiality_at_stop.status} ${f.materiality_at_stop.estimated_usd or 0:,.0f}")
        print(f"  divergence:  ${f.divergence_absolute:+,.0f}" if f.divergence_absolute else "  divergence: n/a")
        print(f"  exposure:    ${f.exposure_estimate_usd:,.0f}" if f.exposure_estimate_usd else "  exposure: n/a")
        print(f"  trail:")
        for s in f.evidence_trail:
            print(f"    - {s}")
        print()
