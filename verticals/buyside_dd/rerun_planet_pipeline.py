"""Re-run Planet Labs (PL) through the buyside_dd dispatch pipeline — end-to-end.

    python3 -m verticals.buyside_dd.rerun_planet_pipeline

Demonstrates that the gap from the AD-HOC PL diligence (the '~82% government' claim left
unverified because no government source was ever dispatched) is now closed: the dispatch graph
selects USASpending (Tier-1) for the claim, the recall floor would FLAG its omission, the
connector runs live, and the claim gets a real confidence instead of 'secondary/unverified'.
"""
from __future__ import annotations

from verticals.buyside_dd.schemas import Claim, TypedClaim, FRule, ClaimWithSources, ReferentType
from verticals.buyside_dd.source_atlas import find_sources, recall_floor_gaps, canonical_attribute
from verticals.buyside_dd.dispatcher import dispatch_with_policy, coverage_report
from verticals.buyside_dd.comparator import compare
from verticals.buyside_dd.policy import STANDARD

# The two PL claims, including the one the ad-hoc run left unverified.
CLAIMS = [
    ("Planet Labs PBC", "derives_revenue_from_government", 0.82, "fraction", ["government_revenue"],
     "Defense & Intelligence ~59% + Civil Government ~23% = ~82% of revenue (Q4 FY26 call)"),
    ("Planet Labs PBC", "files_with_sec", True, None, ["public_filings"],
     "Planet Labs PBC is an SEC registrant (CIK 0001836833), FY26 10-K filed 2026-03-23"),
]


def syn_frule(predicate: str) -> FRule:
    return FRule(rule_id=f"gen::{predicate}", predicate=predicate, referent_type=ReferentType.ENTITY,
                 description="presence/scale check of the claim against the primary record",
                 formula="observed_presence", formula_inputs=[], severity_thresholds={})


def run_claim(subject, predicate, obj, unit, attrs, quote):
    claim = Claim(claim_id=predicate[:12], source_doc="PL FY26 10-K + Q4 FY26 earnings call",
                  source_quote=quote, subject=subject, predicate=predicate, object_value=obj,
                  object_unit=unit, scope={"entity_name": subject, "state": "US"})
    tc = TypedClaim(claim=claim, referent_type=ReferentType.ENTITY, referent_attributes=attrs, jurisdiction="US")
    attr = canonical_attribute(attrs[0])
    sources = find_sources(ReferentType.ENTITY, attrs[0], "US")
    selected = [s.source_id for s in sources]

    print(f"\n── CLAIM: {subject} {predicate} {obj}")
    print(f"   attribute '{attrs[0]}' -> canonical '{attr}'")
    print(f"   dispatch graph selected: {selected or '(none)'}")

    # recall-floor: now-satisfied vs the ad-hoc failure mode (usaspending omitted)
    gaps_now = recall_floor_gaps(tc, selected)
    gaps_adhoc = recall_floor_gaps(tc, [s for s in selected if s != "usaspending"])
    print(f"   recall-floor (as dispatched): {'CLEAR' if not gaps_now else gaps_now}")
    if gaps_adhoc:
        print(f"   recall-floor (ad-hoc, no gov source): WOULD FLAG -> {gaps_adhoc[0]['missing_source_ids']}  ✓ gap now caught")

    cws = ClaimWithSources(typed_claim=tc, f_rules=[syn_frule(predicate)], m_sources=sources)
    outcome = dispatch_with_policy(cws, policy=STANDARD)
    finding = compare(tc, cws.f_rules[0], outcome, sources)

    for cr in outcome.results:
        tag = "ok" if cr.success else f"FAIL {cr.error_kind}"
        print(f"   ↳ {cr.source_id}: {tag}, {len(cr.observations)} obs")
        for o in cr.observations:
            if o.attribute in ("government_contracts", "federal_awards_by_agency", "government_customer_confirmed"):
                print(f"        {o.attribute} = {o.value}")
    print(f"   FINDING: stop={outcome.stop_reason.value}  confidence={finding.confidence:.2f}  "
          f"severity={finding.severity.value}")
    return cws


def main():
    print("PLANET LABS — re-run through buyside_dd dispatch pipeline")
    print("(ad-hoc DD left '82% government' unverified; pipeline now dispatches the gov source + recall floor)")
    all_cws = [run_claim(*c) for c in CLAIMS]
    print("\n=== COVERAGE REPORT ===")
    print(coverage_report(all_cws))
    print("\ndone.")


if __name__ == "__main__":
    main()
