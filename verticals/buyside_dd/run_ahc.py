"""End-to-end DEEP-policy dispatch for the AHC deal.

Pre-extracted typed claims (no LLM needed since the docs are in context).
Runs dispatch + compare + writes findings.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from .schemas import (
    Claim, TypedClaim, ClaimWithSources, FRule, MSource,
    ReferentType, Verifiability, Severity, StopReason, Materiality,
)
from .f_library import find_rules
from .source_atlas import find_sources
from .dispatcher import dispatch_with_policy, coverage_report
from .comparator import compare_all
from .policy import DEEP
from .budget import BudgetState
from .materiality import infer_deal_context
from .cross_claim_check import find_internal_divergences


HERE = Path(__file__).parent
RUN_DIR = HERE / "outputs" / f"ahc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"


# ─────────────────────────────────────────────────────────────────────────────
# Typed claims extracted from the AHC deal materials
# ─────────────────────────────────────────────────────────────────────────────
# Each entry: (claim_id, subject, predicate, object_value, object_unit, scope, ref_type, attributes, jurisdiction, source_quote)
RAW_CLAIMS = [
    # ── ENTITY VERIFICATION ───────────────────────────────────────────────
    ("e1", "American Housing Corporation", "registered_as_entity", True, None,
     {"state": "TX"}, "entity", ["corporate_registration"], "TX",
     "The American Housing Corporation is a vertically-integrated real estate development firm and housing manufacturer."),

    # Two attribute paths for the entity SEC verification — full-text + company-name
    ("e2a", "American Housing Corporation", "previously_acquired", "$2M @ $15M post (Mar 2025)", None,
     {"year": 2025, "lead": "Antler"}, "entity", ["public_filings", "entity_filings"], "US",
     "Mar 2025: $15M post-money / $2M raise / Lead: Antler, Flux Capital"),

    ("e3a", "American Housing Corporation", "previously_acquired", "$7M @ $50M post (Dec 2025)", None,
     {"year": 2025, "lead": "Contrary"}, "entity", ["public_filings", "entity_filings"], "US",
     "Dec 2025: $50M post-money / $7M raise / Lead: Contrary, Flux Capital"),

    # Lead investor verification (use entity_filings — full-text noise too high for common words)
    ("e4", "Contrary", "registered_as_entity", True, None,
     {}, "entity", ["entity_filings"], "US",
     "Lead investor in current Series A round and prior Dec 2025 round"),

    ("e5", "Antler", "registered_as_entity", True, None,
     {}, "entity", ["entity_filings"], "US",
     "Lead investor in Mar 2025 round"),

    # Surface AHC-affiliated SEC filers (this is what found the SPVs)
    ("e6", "American Housing", "registered_as_entity", True, None,
     {}, "entity", ["entity_filings"], "US",
     "Look for any SEC-filed entity name-matching 'American Housing' (catches SPV/Series LLC structures)"),

    # Verify SPV Form D financials against deck claims
    ("spv1", "American Housing Corp Jan 2025 SPV", "raise_amount", 2_000_000, "USD",
     {"cik": "2059084", "year": 2025, "round": "Mar 2025"}, "entity", ["form_d_detail"], "US",
     "Deck: Mar 2025 round raised $2M total (Antler led). Form D for the Sydecar Jan 2025 series should reconcile."),

    ("spv2", "American Housing November 2025 SPV", "raise_amount", 7_000_000, "USD",
     {"cik": "2099529", "year": 2025, "round": "Dec 2025"}, "entity", ["form_d_detail"], "US",
     "Deck: Dec 2025 round raised $7M total (Contrary led). Form D for the Sydecar Nov 2025 series should reconcile."),

    # ── FACTORY EXISTENCE ─────────────────────────────────────────────────
    ("f1", "American Housing Corporation", "operates_industrial_facility", "Austin TX factory", None,
     {"state": "TX", "city": "Austin"}, "entity", ["industrial_facility_presence"], "TX",
     "Each component of the Building System is manufactured in our Austin, TX factory."),

    # ── PIPELINE PROJECTS (each city-specific) ────────────────────────────
    ("p_aus", "American Housing Corporation", "operates_industrial_facility", "Austin 3-unit project", None,
     {"state": "TX", "city": "Austin"}, "building", ["building_permits"], "Austin_TX",
     "Austin, TX: 3-unit rowhome project (per pipeline slide)"),

    ("p_boz", "American Housing Corporation", "operates_industrial_facility", "Bozeman 30-40 unit project", None,
     {"state": "MT", "city": "Bozeman"}, "building", ["building_permits"], "Bozeman_MT",
     "Bozeman, MT: 30+ rowhomes in new-urbanist community (per pipeline slide); 40 units (per financial model)"),

    ("p_abq", "American Housing Corporation", "operates_industrial_facility", "Albuquerque 50+ rowhomes", None,
     {"state": "NM", "city": "Albuquerque"}, "building", ["building_permits"], "Albuquerque_NM",
     "New Mexico: 50+ rowhomes across projects in Albuquerque and Los Alamos"),

    # ── PRODUCTION CAPACITY (Internal divergence flag) ────────────────────
    ("c1", "American Housing Corporation", "factory_planned_capacity", 1000, "homes/year",
     {"factory": "Factory 1"}, "entity", ["funding_round_history"], "US",
     "Factory 1 will have a production capacity of 1,000 homes/yr (pitch deck p.25)"),

    ("c2", "American Housing Corporation", "factory_planned_capacity", 1750, "homes/year",
     {"factory": "Factory 1"}, "entity", ["funding_round_history"], "US",
     "Factory 1: 1,750 Townhomes (financial model Block 1)"),

    # ── TEAM CLAIMS ───────────────────────────────────────────────────────
    ("t1", "Will Davis", "previously_acquired", "CTO/Founder Tudu", None,
     {}, "person", ["patent_filings"], "US",
     "Will Davis: Former founder/CTO (Tudu) - a modern material procurement platform"),

    ("t2", "Harris Rothaermel", "previously_acquired", "NASA Glenn engineering", None,
     {}, "person", ["patent_filings"], "US",
     "Harris Rothaermel: Embedded systems experience from NASA Glenn"),
]


def build_claims():
    cws_list = []
    for (cid, subj, pred, val, unit, scope, rt_str, attrs, juris, quote) in RAW_CLAIMS:
        rt = ReferentType(rt_str)
        c = Claim(
            claim_id=cid, source_doc="ahc-pitch.pdf+spv+model",
            source_quote=quote,
            subject=subj, predicate=pred,
            object_value=val, object_unit=unit, scope=scope,
        )
        tc = TypedClaim(
            claim=c, referent_type=rt, referent_attributes=attrs,
            jurisdiction=juris,
        )
        rules = []
        for attr in attrs:
            rules.extend(find_rules(pred, rt, juris))
        # Dedupe rules
        seen = set()
        rules = [r for r in rules if not (r.rule_id in seen or seen.add(r.rule_id))]
        sources = []
        for attr in attrs:
            sources.extend(find_sources(rt, attr, juris))
        seen = set()
        sources = [s for s in sources if not (s.source_id in seen or seen.add(s.source_id))]
        cws_list.append(ClaimWithSources(typed_claim=tc, f_rules=rules, m_sources=sources))
    return cws_list


def main():
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== AHC pipeline — DEEP policy ===", file=sys.stderr)
    print(f"Output: {RUN_DIR}", file=sys.stderr)

    cws_list = build_claims()
    print(f"Built {len(cws_list)} typed claims", file=sys.stderr)

    # Auto-infer deal context
    typed_claim_dicts = [
        {**c.typed_claim.claim.model_dump(), "referent_type": c.typed_claim.referent_type.value,
         "scope": c.typed_claim.claim.scope}
        for c in cws_list
    ]
    deal_ctx = infer_deal_context(typed_claim_dicts)
    # AHC is a venture deal — round size is the natural denominator
    deal_ctx.setdefault("deal_size_usd", 50_000_000)  # $50M Series A round
    print(f"Deal context: {deal_ctx}", file=sys.stderr)

    cov = coverage_report(cws_list)
    print(f"Coverage: {cov}", file=sys.stderr)

    budget = BudgetState(max_cost_usd=DEEP.max_cost_usd, max_wall_time_min=DEEP.max_wall_time_min)
    all_findings = []
    outcomes_summary = []

    for cws in cws_list:
        cid = cws.typed_claim.claim.claim_id
        subj = cws.typed_claim.claim.subject
        pred = cws.typed_claim.claim.predicate
        if not cws.m_sources:
            print(f"  [{cid}] {subj[:40]:40s} {pred:35s}  NO_SOURCES", file=sys.stderr)
            outcomes_summary.append({"claim_id": cid, "subject": subj, "predicate": pred,
                                     "stop": "NOT_DISPATCHED", "n_sources": 0, "n_success": 0})
            continue
        outcome = dispatch_with_policy(cws, policy=DEEP, budget=budget, deal_context=deal_ctx)
        n_succ = sum(1 for r in outcome.results if r.success)
        print(f"  [{cid}] {subj[:40]:40s} {pred:35s}  {outcome.stop_reason.value:12s} "
              f"obs={n_succ}/{len(outcome.results)} mat={outcome.materiality.status}", file=sys.stderr)
        outcomes_summary.append({
            "claim_id": cid, "subject": subj, "predicate": pred,
            "stop": outcome.stop_reason.value,
            "n_sources": len(outcome.results), "n_success": n_succ,
            "materiality": outcome.materiality.model_dump(),
            "raw_results": [
                {"source_id": r.source_id, "success": r.success, "n_obs": len(r.observations),
                 "error_kind": r.error_kind.value if r.error_kind else None,
                 "error_detail": r.error_detail,
                 "observations": [o.model_dump() for o in r.observations[:5]]}
                for r in outcome.results
            ],
        })
        findings = compare_all(cws.typed_claim, cws.f_rules, outcome, cws.m_sources)
        all_findings.extend(findings)

    # ── Cross-claim internal consistency check ─────────────────────────────
    print(f"\n=== Cross-claim consistency check ===", file=sys.stderr)
    internal_findings = find_internal_divergences([cws.typed_claim for cws in cws_list])
    for fd in internal_findings:
        print(f"  [{fd.severity.value.upper():8s}] {fd.f_rule_id} on '{fd.claim.subject[:30]}' / '{fd.claim.predicate}' "
              f"— divergence={(fd.divergence_pct or 0)*100:.1f}%", file=sys.stderr)
    all_findings.extend(internal_findings)

    # Persist
    with open(RUN_DIR / "outcomes.json", "w") as f:
        json.dump(outcomes_summary, f, indent=2, default=str)
    with open(RUN_DIR / "findings.json", "w") as f:
        json.dump([fd.model_dump() for fd in all_findings], f, indent=2, default=str)
    with open(RUN_DIR / "budget.json", "w") as f:
        json.dump(budget.summary(), f, indent=2, default=str)

    # Severity rollup
    print(f"\n=== Findings rollup ===", file=sys.stderr)
    by_sev = {}
    for fd in all_findings:
        by_sev.setdefault(fd.severity.value, []).append(fd)
    for sev in ("critical", "severe", "moderate", "minor", "pass", "unverifiable"):
        if sev in by_sev:
            print(f"  {sev.upper()}: {len(by_sev[sev])}", file=sys.stderr)

    print(f"\nBudget: ${budget.spent_usd:.2f}/{budget.max_cost_usd} | calls: {budget.calls_made}", file=sys.stderr)
    print(f"\nFiles: {RUN_DIR}", file=sys.stderr)
    return all_findings, outcomes_summary, budget


if __name__ == "__main__":
    main()
