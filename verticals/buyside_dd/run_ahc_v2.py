"""End-to-end DD run for AHC — v2.

Differences from run_ahc.py:
  - Tier 1 open-web discovery on the issuer name FIRST, surfaces address etc.
  - SAFE-derived claims from the executed Flux SAFEs (parsed from PDFs):
      • Flux Capital paid $1M on 2025-01-29 at $15M post-money cap
      • Flux Capital paid $2M on 2025-11-13 at $50M post-money cap
  - Proper issuer name "The American Housing Corporation" (Delaware) for
    EDGAR fulltext + state corporate registry searches
  - Antler/Contrary-as-leads claims tested against Form D related-persons +
    cross-checked SAFE register
  - 4422 Supply Ct flagged as a derived address claim (from web discovery
    AND/OR pre-loaded if Tier 1 is rate-limited)
  - Cost-basis reconciliation between user's $2.5M memory and SAFE total $3M
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
from .connectors.web_discovery import WebDiscoveryConnector
from .connectors.base import ConnectorRequest


HERE = Path(__file__).parent
RUN_DIR = HERE / "outputs" / f"ahc_v2_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"


# ─────────────────────────────────────────────────────────────────────────────
# Tier 1 discovery — runs first so derived facts (addresses) feed downstream
# ─────────────────────────────────────────────────────────────────────────────
def run_tier1_discovery(issuer_name: str) -> list[dict]:
    """Run web discovery on issuer; return derived claim dicts.

    If Brave is rate-limited (HTTP 429) or DDG is bot-blocked (HTTP 202),
    returns an empty list. Downstream stages handle this gracefully —
    the SAFE-derived hardcoded claims still test the same things via Tier 2/3.
    """
    print(f"\n=== Tier 1: web discovery on {issuer_name!r} ===", file=sys.stderr)
    connector = WebDiscoveryConnector()
    derived = []
    recipes = [
        {"keywords": ["factory", "address"], "category": "physical_facility"},
        {"keywords": ["headquarters", "office"], "category": "headquarters"},
        {"keywords": ["customers", "partners"], "category": "customer_pipeline"},
    ]
    for recipe in recipes:
        req = ConnectorRequest(
            entity_name=issuer_name,
            extra={"claim_keywords": recipe["keywords"]},
        )
        try:
            r = connector.query(req)
        except Exception as e:
            print(f"  [{recipe['category']}] connector exception: {e}", file=sys.stderr)
            continue
        if not r.success:
            print(f"  [{recipe['category']}] failed: {r.error_kind} ({(r.error_detail or '')[:60]})", file=sys.stderr)
            continue
        n_facts = 0
        for obs in r.observations:
            if obs.attribute == "discovery_meta":
                continue
            if obs.attribute == "discovery_address":
                derived.append({
                    "claim_id": f"d_addr_{len(derived)+1}",
                    "subject": issuer_name,
                    "predicate": "located_at_address",
                    "object_value": obs.value,
                    "object_unit": None,
                    "scope": {"category": recipe["category"]},
                    "source_quote": (obs.extra or {}).get("snippet", (obs.extra or {}).get("title", ""))[:200],
                    "source_doc": "tier1_web_discovery",
                    "discovery_url": obs.source_url,
                })
                n_facts += 1
            elif obs.attribute.startswith("discovery_url:"):
                cat = obs.attribute[len("discovery_url:"):]
                derived.append({
                    "claim_id": f"d_url_{len(derived)+1}",
                    "subject": issuer_name,
                    "predicate": f"surfaced_in_{cat}",
                    "object_value": obs.value,
                    "object_unit": None,
                    "scope": {"category": recipe["category"]},
                    "source_quote": (obs.extra or {}).get("title", "")[:200],
                    "source_doc": "tier1_web_discovery",
                    "discovery_url": obs.source_url,
                })
                n_facts += 1
        print(f"  [{recipe['category']}] {n_facts} derived claims surfaced", file=sys.stderr)
    return derived


# ─────────────────────────────────────────────────────────────────────────────
# Hardcoded claims — issuer-aware, SAFE-aware
# ─────────────────────────────────────────────────────────────────────────────
ISSUER = "The American Housing Corporation"  # Delaware corporation per SAFE

RAW_CLAIMS = [
    # ── ENTITY VERIFICATION (proper name + DE jurisdiction) ───────────────
    ("e1", ISSUER, "registered_as_entity", True, None,
     {"state": "DE"}, "entity", ["corporate_registration"], "DE",
     "The American Housing Corporation, a Delaware corporation (per executed SAFEs)."),

    ("e1b", ISSUER, "registered_as_entity", True, None,
     {"state": "TX"}, "entity", ["corporate_registration"], "TX",
     "TX franchise tax registration (mailing zip 75201 Dallas per prior DD)."),

    # ── SAFE-DERIVED FACTS (replace the imprecise prior-round claims) ─────
    # Round 1: $15M cap SAFE
    ("safe1_amt", ISSUER, "raise_amount", 1_000_000, "USD",
     {"round": "Jan 2025 SAFE", "cap_post_money": 15_000_000, "investor": "Flux Capital"},
     "entity", ["form_d_detail"], "US",
     "Executed Flux Capital SAFE: $1,000,000 purchase amount, $15M post-money cap, dated 1/29/2025."),

    ("safe1_cap", ISSUER, "valuation_cap", 15_000_000, "USD",
     {"round": "Jan 2025 SAFE", "type": "post_money_cap"}, "entity", ["form_d_detail"], "US",
     "Post-Money Valuation Cap = $15,000,000 (YC SAFE v1.2)."),

    # Round 2: $50M cap SAFE
    ("safe2_amt", ISSUER, "raise_amount", 2_000_000, "USD",
     {"round": "Nov 2025 SAFE", "cap_post_money": 50_000_000, "investor": "Flux Capital"},
     "entity", ["form_d_detail"], "US",
     "Executed Flux Capital SAFE: $2,000,000 purchase amount, $50M post-money cap, dated 11/13/2025."),

    ("safe2_cap", ISSUER, "valuation_cap", 50_000_000, "USD",
     {"round": "Nov 2025 SAFE", "type": "post_money_cap"}, "entity", ["form_d_detail"], "US",
     "Post-Money Valuation Cap = $50,000,000 (YC SAFE v1.2)."),

    # ── SPV-LEVEL FORM D (re-test against SAFE-derived dollar amounts) ────
    ("spv1_actual", "American Housing Corp Jan 2025 SPV", "raise_amount", 485_000, "USD",
     {"cik": "2059084", "year": 2025, "round": "Jan-Mar 2025"}, "entity", ["form_d_detail"], "US",
     "Sydecar SPV Form D: $485K raised, 2 accredited investors. Combined with Flux $1M direct = $1.485M total Round 1."),

    ("spv2_actual", "American Housing November 2025 SPV", "raise_amount", 2_000_000, "USD",
     {"cik": "2099529", "year": 2025, "round": "Nov-Dec 2025"}, "entity", ["form_d_detail"], "US",
     "Sydecar SPV Form D: $2M raised, 1 accredited investor. May or may not be the same $2M as Flux's direct check."),

    # ── DECK-CLAIMED ROUND TOTALS (still test against Form D + SAFE register) ──
    ("deck_r1", ISSUER, "round_total_raise", 2_000_000, "USD",
     {"round": "Mar 2025", "lead": "Antler", "post_money": 15_000_000}, "entity", ["public_filings", "entity_filings"], "US",
     "Deck claim: Mar 2025 round raised $2M total with Antler as lead at $15M post."),

    ("deck_r2", ISSUER, "round_total_raise", 7_000_000, "USD",
     {"round": "Dec 2025", "lead": "Contrary", "post_money": 50_000_000}, "entity", ["public_filings", "entity_filings"], "US",
     "Deck claim: Dec 2025 round raised $7M total with Contrary as lead at $50M post."),

    # ── LEAD INVESTOR VISIBILITY (Antler/Contrary should appear somewhere) ──
    ("lead1", "Antler", "led_investment_round", ISSUER, None,
     {"round": "Mar 2025", "expected_evidence": "Form D related person OR own SAFE doc OR cap table entry"},
     "entity", ["entity_filings", "form_d_detail"], "US",
     "Antler is named as lead investor in Mar 2025 round. Should be visible in: parent Form D as related person, OR have their own SAFE document, OR appear on AHC cap table."),

    ("lead2", "Contrary", "led_investment_round", ISSUER, None,
     {"round": "Dec 2025", "expected_evidence": "Form D related person OR own SAFE doc OR cap table entry"},
     "entity", ["entity_filings", "form_d_detail"], "US",
     "Contrary is named as lead investor in Dec 2025 round. Should be visible in: parent Form D as related person, OR have their own SAFE document, OR appear on AHC cap table."),

    # Also: AHC parent should have its OWN Form D for any direct-to-AHC SAFE checks
    # (Flux's checks went directly to AHC, not via SPV — so AHC-parent Form D is required by Reg D)
    ("parent_formD", ISSUER, "filed_form_d_for_direct_safes", True, None,
     {"required_by": "Reg D 506(b)/(c)", "direct_safe_amounts": "$1M Jan 2025 + $2M Nov 2025"},
     "entity", ["entity_filings"], "US",
     "AHC parent took direct SAFE checks from Flux totaling $3M. Reg D 506 requires Form D within 15 days of first sale. Should exist under AHC parent name on EDGAR."),

    # Surface any AHC-affiliated SEC filers (catches new SPV/Series LLC structures)
    ("e_surface", "American Housing", "registered_as_entity", True, None,
     {}, "entity", ["entity_filings"], "US",
     "Surface any SEC-filed entity name-matching 'American Housing' (catches SPV/Series LLC structures)."),

    # ── COST-BASIS RECONCILIATION (user memory vs. SAFE evidence) ─────────
    # User said $2.5M cost basis ($500K Mar + $2M Dec).
    # SAFEs say $1M Jan + $2M Nov = $3M.
    # Either user memory is wrong, or there's a $500K SAFE we don't have.
    ("flux_cost", "Flux Capital", "total_paid_to_AHC", 3_000_000, "USD",
     {"derivation": "SAFE 1 ($1M, 1/29/2025) + SAFE 2 ($2M, 11/13/2025)", "user_memory_was": 2_500_000},
     "entity", ["form_d_detail"], "US",
     "SAFE evidence shows Flux paid $3M total to AHC. Original DD memo said $2.5M cost basis ($500K Mar + $2M Dec). Reconcile: was the Jan SAFE actually $500K, or is there a separate $500K SAFE not in our docs?"),

    # ── FACTORY EXISTENCE (with the discovered address) ───────────────────
    # Pre-loaded so the run is meaningful even if Tier 1 fails
    ("f1", ISSUER, "operates_industrial_facility", "Austin TX factory", None,
     {"state": "TX", "city": "Austin"}, "entity", ["industrial_facility_presence"], "TX",
     "Pitch: factory in Austin TX. SAFE confirms DE incorporation; TX Comptroller mailing is Dallas, not Austin."),

    ("f1_addr", ISSUER, "located_at_address", "4422 Supply Ct, Austin, TX 78744", None,
     {"state": "TX", "city": "Austin", "zip": "78744"}, "building", ["building_permits"], "Austin_TX",
     "Specific factory address per user-supplied info (verified via permit records: 12 permits at this address since 2016, including Sept-Oct 2025 600A electrical service upgrade by CM Constructors as GC). Property owner: IGX Burleson Park, LLC."),

    # GC & landlord — both should be cross-verifiable
    ("f1_gc", "CM Constructors", "filed_permit_for", "4422 Supply Ct service upgrade", None,
     {"address": "4422 Supply Ct", "city": "Austin", "permit_year": 2025, "scope": "600A electrical service"},
     "entity", ["building_permits"], "Austin_TX",
     "CM Constructors filed Building + Electrical permits at 4422 Supply Ct in Sept-Oct 2025 for 600A service upgrade. Real Austin commercial GC (also doing Mueller hospital + Mopac office work)."),

    ("f1_landlord", "IGX Burleson Park, LLC", "owns_property_at", "4422 Supply Ct", None,
     {"address": "4422 Supply Ct", "city": "Austin"}, "entity", ["entity_filings"], "TX",
     "IGX Burleson Park, LLC filed the original 2017 building permit at 4422 Supply Ct. TX Comptroller: registered LLC at Bandera TX 78003."),

    # ── PIPELINE PROJECTS (each city-specific) — unchanged from v1 ────────
    ("p_aus", ISSUER, "operates_industrial_facility", "Austin 3-unit project", None,
     {"state": "TX", "city": "Austin"}, "building", ["building_permits"], "Austin_TX",
     "Austin TX: 3-unit rowhome project (per pipeline slide)"),

    ("p_boz", ISSUER, "operates_industrial_facility", "Bozeman 30-40 unit project", None,
     {"state": "MT", "city": "Bozeman"}, "building", ["building_permits"], "Bozeman_MT",
     "Bozeman MT: 30+ rowhomes (per pipeline slide); 40 units (per financial model)"),

    ("p_abq", ISSUER, "operates_industrial_facility", "Albuquerque 50+ rowhomes", None,
     {"state": "NM", "city": "Albuquerque"}, "building", ["building_permits"], "Albuquerque_NM",
     "New Mexico: 50+ rowhomes across projects in Albuquerque and Los Alamos"),

    # ── PRODUCTION CAPACITY (internal divergence flag) ────────────────────
    ("c1", ISSUER, "factory_planned_capacity", 1000, "homes/year",
     {"factory": "Factory 1"}, "entity", ["funding_round_history"], "US",
     "Factory 1 will have a production capacity of 1,000 homes/yr (pitch deck p.25)"),

    ("c2", ISSUER, "factory_planned_capacity", 1750, "homes/year",
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


def build_claims(extra_raw_claims=None):
    """Build ClaimWithSources for hardcoded RAW_CLAIMS plus any extras
    (e.g. Tier 1 discovery results)."""
    cws_list = []
    raw = list(RAW_CLAIMS)
    if extra_raw_claims:
        raw.extend(extra_raw_claims)

    for entry in raw:
        # Support both tuple and dict shapes (Tier 1 returns dicts)
        if isinstance(entry, dict):
            cid = entry["claim_id"]
            subj = entry["subject"]
            pred = entry["predicate"]
            val = entry.get("object_value")
            unit = entry.get("object_unit")
            scope = entry.get("scope", {})
            rt_str = entry.get("referent_type", "entity")
            attrs = entry.get("referent_attributes", ["entity_filings"])
            juris = entry.get("jurisdiction", "US")
            quote = entry.get("source_quote", "")
            source_doc = entry.get("source_doc", "tier1")
        else:
            cid, subj, pred, val, unit, scope, rt_str, attrs, juris, quote = entry
            source_doc = "ahc-pitch.pdf+spv+model+SAFEs"

        rt = ReferentType(rt_str)
        c = Claim(
            claim_id=cid, source_doc=source_doc,
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
    print(f"=== AHC v2 pipeline — DEEP policy ===", file=sys.stderr)
    print(f"Output: {RUN_DIR}", file=sys.stderr)

    # ── Phase 0: Tier 1 web discovery on issuer ─────────────────────────────
    discovery_claims = run_tier1_discovery(ISSUER)
    if discovery_claims:
        with open(RUN_DIR / "00_tier1_discovery.json", "w") as f:
            json.dump(discovery_claims, f, indent=2, default=str)
        print(f"  Saved {len(discovery_claims)} Tier 1 derived claims", file=sys.stderr)
    else:
        print(f"  Tier 1 returned no derived claims (likely rate-limited).", file=sys.stderr)
        print(f"  Falling back to hardcoded SAFE-derived + address-resolved claims.", file=sys.stderr)

    cws_list = build_claims(extra_raw_claims=discovery_claims)
    print(f"\nBuilt {len(cws_list)} typed claims ({len(RAW_CLAIMS)} hardcoded + {len(discovery_claims)} from Tier 1)", file=sys.stderr)

    typed_claim_dicts = [
        {**c.typed_claim.claim.model_dump(), "referent_type": c.typed_claim.referent_type.value,
         "scope": c.typed_claim.claim.scope}
        for c in cws_list
    ]
    deal_ctx = infer_deal_context(typed_claim_dicts)
    deal_ctx.setdefault("deal_size_usd", 50_000_000)  # $50M Series A
    deal_ctx["issuer_name"] = ISSUER
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

    print(f"\n=== Cross-claim consistency check ===", file=sys.stderr)
    internal_findings = find_internal_divergences([cws.typed_claim for cws in cws_list])
    for fd in internal_findings:
        print(f"  [{fd.severity.value.upper():8s}] {fd.f_rule_id} on '{fd.claim.subject[:30]}' / '{fd.claim.predicate}' "
              f"— divergence={(fd.divergence_pct or 0)*100:.1f}%", file=sys.stderr)
    all_findings.extend(internal_findings)

    with open(RUN_DIR / "outcomes.json", "w") as f:
        json.dump(outcomes_summary, f, indent=2, default=str)
    with open(RUN_DIR / "findings.json", "w") as f:
        json.dump([fd.model_dump() for fd in all_findings], f, indent=2, default=str)
    with open(RUN_DIR / "budget.json", "w") as f:
        json.dump(budget.summary(), f, indent=2, default=str)

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
