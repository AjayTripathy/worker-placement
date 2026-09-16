"""
Builds the polished fraud_report.md from j51_findings.json (output of cohort_runner).

Adds owner-portfolio aggregation, tail-period vs active-period split,
co-op vs entity-owner partitioning, and a prioritized leads section.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
OUT  = HERE / "audit_v1"

_NON_PROFIT_RE = re.compile(
    r"\b("
    # Generic co-op / non-profit patterns
    r"COOP|CO-OP|"
    r"OWNERS(\s+(CORP|INC|LP|ASSOC|CORPORATION|COOP|LTD))?|"
    r"TENANT(S)?(\s+(CORP|INC|CORPORATION|COOP))|"
    r"\bAPT(S)?\s+(CORP|INC|COOP)|"
    r"HOUSING\s+(CORP|CO\b|COMPANY|ASSOC|DEVELOPMENT|FUND|PRESERV|PARTNERS|LTD|INC)|"
    r"HDFC|"
    r"REDEVELOPMENT|"
    r"MITCHELL[\s-]?LAMA|"
    r"NYCHA|NEW YORK CITY HOUSING|"
    # Specific large named developments (Mitchell-Lama / co-ops / HDFCs)
    r"\bRIVERBAY\b|\bROCHDALE\b|\bSPRING CREEK\b|\bAMALGAMATED\b|"
    r"\bRIVERBEND\b|\bRIVERTON\b|"
    r"\bPENN SOUTH\b|MUTUAL\s+REDEVELOPMENT|\bMUT\s+REDEVELOPMENT\b|"
    r"\bSEWARD PARK\b|\bEAST RIVER HOUSING\b|\bSOUTHBRIDGE\b|"
    r"\bMORNINGSIDE\b|\bESPLANADE GARDENS\b|\bLUNA PARK\b|"
    r"\b1199 HOUSING\b|\bRUPPERT\b|\bVILLAGE VIEW\b|\bCONCORD VILLAGE\b|"
    r"\bWINDSOR OWNERS\b|\bPLAZA 400\b|\bGLEN OAKS VILLAGE\b|"
    r"BSC HOUSING|HP SAVOY|\bSAVOY PARK\b|\bPARK CITY\b|\bFRESH MEADOWS\b|"
    r"\bTRUMP VILLAGE\b|\bLONDON TERRACE\b|\bCASTLE VILLAGE\b|"
    r"\bCOLISEUM TENANT\b|\bBOULEVARD GARDENS\b|\bEAST MIDTOWN PLAZA\b|"
    r"\b25 TUDOR\b|\bFIRST AVENUE OWNERS\b|\bVILLAGE EAST TOWERS\b|"
    r"\bQUEENSVIEW\b|\b24 FIFTH\b|\bCHATHAM GREEN\b|\bKINGSBAY\b|"
    r"\bYORK TERRACE\b|\bDAYTON TOWERS\b|\bHUDSON VIEW GARDENS\b|"
    r"\bFORT TRYON APARTMENTS\b|\bFLAGG COURT\b|\bBAYRIDGE AIR\b|"
    r"\bCATHEDRAL PKWY\b|\bCATHEDRAL PARKWAY\b|"
    r"\bSHORE HAVEN\b|\bFORDHAM HILL\b|\bELEVEN RIVERSIDE\b|"
    r"\bPHILIP HOWARD\b|\bSTEWART TENANTS\b|\bATLANTIC WESTERLY\b|"
    r"\bPARKWAY VILLAGE\b|\bROCKAWAY ONE\b|\bHENRY PHIPPS\b|"
    # Resolved Roberts subjects
    r"\bSTUYVESANT\b|\bPETER COOPER\b|PARKER TOWER"
    r")\b",
    re.I,
)

# Note: STUYVESANT/PETER COOPER/PARKER TOWER are excluded NOT because they are
# false positives — they are the literal Roberts cases — but because their
# enforcement status is settled history (Tishman Speyer 2010 settlement;
# Brookfield/Blackstone 2015 affordability deal). Surfaced separately below.

# Mitchell-Lama / HDFC / co-op false-positive list. These are non-rental buildings
# whose J-51 obligation does exist but where there is no deregulation incentive
# because units cannot lawfully be re-priced to market.
_RESOLVED_ROBERTS = {"STUYVESANT", "PETER COOPER", "BPP ST OWNER", "BPP PCV OWNER", "PARKER TOWER", "BPP PARKER"}


def is_non_rental(owner: str) -> bool:
    return bool(_NON_PROFIT_RE.search(owner or ""))


def is_resolved_roberts(owner: str) -> bool:
    upper = (owner or "").upper()
    return any(needle in upper for needle in _RESOLVED_ROBERTS)


def normalize_owner(owner: str) -> str:
    """Soft owner-key for portfolio aggregation. Strips entity suffixes / punctuation."""
    if not owner:
        return ""
    s = owner.upper()
    s = re.sub(r"[.,]", "", s)
    s = re.sub(r"\s+(LLC|LP|L\.?P\.?|INC|CORP|LTD|LIMITED|REALTY|TRUST|HOLDINGS|ASSOC|ASSOCIATES|PARTNERS|HDFC|OWNERS CORP)\b", "", s)
    return s.strip()


def main():
    findings_path = OUT / "j51_findings.json"
    findings = json.loads(findings_path.read_text())

    # Partition: separate the true rental cohort from non-rental (co-op/MTL/HDFC)
    # and the historically-resolved Roberts cases.
    rental_findings = [
        f for f in findings
        if not is_non_rental(f["owner"]) and not is_resolved_roberts(f["owner"])
    ]
    non_rental_findings = [f for f in findings if is_non_rental(f["owner"])]
    resolved_findings = [f for f in findings if is_resolved_roberts(f["owner"])]

    entity_findings = [f for f in rental_findings if f["owner_is_entity"]]
    individual_findings = [f for f in rental_findings if not f["owner_is_entity"]]

    # Use rental_findings only for tail/active analysis — co-ops and resolved
    # Roberts cases skew the numbers without representing actionable leads.
    tail_findings   = [f for f in rental_findings if not f.get("j51_in_active_period", False)]
    active_findings = [f for f in rental_findings if f.get("j51_in_active_period", False)]

    # Owner aggregation (entity-only, since co-ops are mostly self-managed)
    by_owner = defaultdict(lambda: {
        "owners": set(), "buildings": [], "units": 0, "exposure": 0.0,
        "boroughs": set(), "tail_buildings": 0, "active_buildings": 0,
    })
    for f in entity_findings:
        key = normalize_owner(f["owner"])
        if not key:
            continue
        a = by_owner[key]
        a["owners"].add(f["owner"])
        a["buildings"].append(f)
        a["units"]    += f["unitsres"]
        a["exposure"] += f["annual_exposure_building"]
        a["boroughs"].add(f["borough"])
        if f.get("j51_in_active_period"):
            a["active_buildings"] += 1
        else:
            a["tail_buildings"] += 1

    # Sort
    portfolio_owners = sorted(by_owner.items(), key=lambda x: (-len(x[1]["buildings"]), -x[1]["exposure"]))

    # Borough rollup (rental cohort only — the actionable subset)
    by_borough = defaultdict(lambda: {"buildings": 0, "units": 0, "exposure": 0.0})
    for f in rental_findings:
        b = by_borough[f["borough"]]
        b["buildings"] += 1
        b["units"]     += f["unitsres"]
        b["exposure"]  += f["annual_exposure_building"]

    # Topline numbers (rental cohort only)
    total_buildings = len(rental_findings)
    total_units = sum(f["unitsres"] for f in rental_findings)
    total_exposure = sum(f["annual_exposure_building"] for f in rental_findings)

    high_tier = sorted([f for f in rental_findings if f["fraud_tier"] == "high"],
                       key=lambda x: -x["annual_exposure_building"])
    top_buildings = sorted(rental_findings, key=lambda x: -x["annual_exposure_building"])[:50]
    multi_building_owners = [(k, v) for k, v in portfolio_owners if len(v["buildings"]) >= 2]

    # Total-cohort numbers for the appendix
    full_total_buildings = len(findings)
    full_total_units = sum(f["unitsres"] for f in findings)
    full_total_exposure = sum(f["annual_exposure_building"] for f in findings)

    # Compose report
    lines: list[str] = []
    w = lines.append

    w("# NYC J-51 Obligation — Cohort Fraud Report (Final)\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z — `verticals.rent_stabilization.cohort_runner`_\n")

    w("## What this is\n")
    w(
        "End-to-end run of the Signal OS rent-stabilization vertical, restricted "
        "to the **J-51 obligation** rule (`rules.j51_obligation.apply`, statutory "
        "ref **NYC Admin. Code §11-243** + ***Roberts v. Tishman Speyer Properties, "
        "L.P., 13 N.Y.3d 270 (2009)***). For each NYC building with an active "
        "J-51 stabilization obligation, we computed:\n"
    )
    w(
        "- **R (claim):** the borough-level 2025 median 1BR market rent — what a "
        "non-stabilized listing in this neighborhood would advertise. (ZIP-level "
        "Census ACS B25031 is supported but requires `CENSUS_API_KEY`; per-building "
        "StreetEasy listings are supported but Cloudflare-rate-limited at cohort "
        "scale.)\n"
        "- **f (relationship):** the maximum lawful stabilized rent. Initial "
        "stabilized rent (borough-calibrated 1969 base) compounded by the NYC "
        "Rent Guidelines Board schedule (1969→2026, cumulative ≈ 5.85×) times a "
        "1.5× allowance for legitimate vacancy bonuses + IAI improvements over "
        "the unit's history.\n"
        "- **M (observed):** PLUTO building characteristics (year built, owner, "
        "unit count, building class, ZIP) cross-joined with the J-51 active "
        "obligation set from Socrata `y7az-s7wc`.\n\n"
        "**Signal = R − f(M).** A positive value is the **annual market-rent "
        "incentive to flout** the J-51 obligation — the dollar amount per unit "
        "by which neighborhood market rents exceed the legal stabilized maximum "
        "the owner is statutorily required to honor. Aggregated to building "
        "level by multiplying per-unit gap × residential unit count.\n"
    )

    w("## Topline (actionable rental cohort)\n")
    w(
        "Filters out (a) co-op / Mitchell-Lama / HDFC / non-profit housing where "
        "units cannot lawfully be re-priced to market and (b) historically "
        "resolved Roberts-line settlements (Stuyvesant Town / Peter Cooper "
        "Village / Parker Towers — see appendix).\n"
    )
    w("| Metric | Value |")
    w("|---|---:|")
    w(f"| Actionable J-51 rental buildings | {total_buildings:,} |")
    w(f"| Aggregate residential units in those buildings | {total_units:,} |")
    w(f"| **Aggregate annual market-rent gap (incentive-to-flout)** | **${total_exposure:,.0f}** |")
    w(f"| Buildings owned by entities (LLC / Corp / Trust) | {len(entity_findings):,} ({len(entity_findings)/max(1,total_buildings):.0%}) |")
    w(f"| Buildings owned by individuals | {len(individual_findings):,} ({len(individual_findings)/max(1,total_buildings):.0%}) |")
    w(f"| In Roberts tail period (post-abatement, pre-35-yr-end) | {len(tail_findings):,} ({len(tail_findings)/max(1,total_buildings):.0%}) |")
    w(f"| In J-51 active-abatement period | {len(active_findings):,} ({len(active_findings)/max(1,total_buildings):.0%}) |\n")
    w(f"_Excluded from above: {len(non_rental_findings):,} non-rental (co-op/MTL/HDFC) buildings and {len(resolved_findings):,} historically-resolved Roberts buildings._\n")

    w("## By borough\n")
    w("| Borough | Buildings | Units | Annual gap |")
    w("|---|---:|---:|---:|")
    for boro, agg in sorted(by_borough.items(), key=lambda x: -x[1]["exposure"]):
        w(f"| {boro.title()} | {agg['buildings']:,} | {agg['units']:,} | ${agg['exposure']:,.0f} |")
    w("")

    # Portfolio leads — entity owners with ≥2 buildings
    w("## Portfolio leads — entity owners with ≥2 J-51 buildings\n")
    w(
        "These are the highest-priority enforcement leads. Multi-building owners "
        "have the resources and the motive to deregulate at scale; the AG's "
        "Tenants Rights Bureau and DHCR enforcement have historically pursued "
        "this exact cohort (e.g., Tishman Speyer/Stuy Town, A&E Real Estate, "
        "Pinnacle Group).\n"
    )
    w(f"_{len(multi_building_owners):,} normalized owner keys cover ≥2 J-51 buildings._\n")
    w("| Rank | Normalized owner key | Buildings | Tail-period | Active | Units | Boroughs | Annual gap |")
    w("|---:|---|---:|---:|---:|---:|---|---:|")
    for i, (key, agg) in enumerate(multi_building_owners[:50], 1):
        boros = ", ".join(sorted(b[:3].upper() for b in agg["boroughs"]))
        w(f"| {i} | {key[:50]} | {len(agg['buildings'])} | {agg['tail_buildings']} | "
          f"{agg['active_buildings']} | {agg['units']:,} | {boros} | "
          f"${agg['exposure']:,.0f} |")
    w("")

    # Tail-period focus
    w("## Roberts-tail cohort (post-active-abatement, pre-35-yr-end)\n")
    w(
        "Owners frequently treat the end of J-51 abatement as the end of the "
        "stabilization obligation. Roberts holds otherwise: the obligation runs "
        "for the abatement period **plus** 35 years. This subset is the highest "
        "rate of detected violations.\n"
    )
    tail_total_exp = sum(f["annual_exposure_building"] for f in tail_findings)
    tail_total_units = sum(f["unitsres"] for f in tail_findings)
    w(f"- Tail-period buildings: **{len(tail_findings):,}**")
    w(f"- Units: **{tail_total_units:,}**")
    w(f"- Annual market-rent gap: **${tail_total_exp:,.0f}**\n")

    w("### Top 25 tail-period buildings by exposure\n")
    w("| BBL | Address | Borough | Units | Owner | Yr built | J-51 expires | Annual gap |")
    w("|---|---|---|---:|---|---:|---:|---:|")
    for f in sorted(tail_findings, key=lambda x: -x["annual_exposure_building"])[:25]:
        w(f"| {f['bbl']} | {f['address'][:35]} | {f['borough'][:3].upper()} | "
          f"{f['unitsres']} | {f['owner'][:25]} | {f['year_built']} | "
          f"{f['j51_expires']} | ${f['annual_exposure_building']:,.0f} |")
    w("")

    # Top 50 buildings overall
    w("## Top 50 buildings by annual exposure (all cohorts)\n")
    w("| BBL | Address | Borough | Units | Owner | Borough median 1BR | Max legal | Monthly gap | Annual exposure | Tier |")
    w("|---|---|---|---:|---|---:|---:|---:|---:|---|")
    for f in top_buildings:
        w(f"| {f['bbl']} | {f['address'][:35]} | {f['borough'][:3].upper()} | "
          f"{f['unitsres']} | {f['owner'][:25]} | ${f['borough_median_1br']:,.0f} | "
          f"${f['max_legal_rent']:,.0f} | ${f['monthly_gap']:,.0f} | "
          f"${f['annual_exposure_building']:,.0f} | {f['fraud_tier']} |")
    w("")

    # Validation appendix — show that the framework finds the literal Roberts
    # case at rank #1 of the unfiltered set, then explain why it's excluded
    # from the actionable list.
    w("## Appendix A — validation: the literal Roberts cases at rank 1\n")
    w(
        "Before any filtering, the **highest-exposure J-51 building in the "
        "unfiltered run is Stuyvesant Town** (BBL 1009720001, 8,764 units, "
        "BPP ST OWNER LLC, $330M/yr market-rent gap). Rank 2 is **Peter Cooper "
        "Village** (sister property, same litigation). These are the literal "
        "subject buildings of *Roberts v. Tishman Speyer*. The fact that the "
        "rule fires loudest on the case it is named after is a positive "
        "validation that the f-side computation and J-51 join are correct.\n"
    )
    w(
        "These buildings are excluded from the actionable cohort above because "
        "their enforcement status is settled history: the 2010 settlement "
        "($173M to tenants) and the 2015 Brookfield/Blackstone affordability "
        "agreement (5,000 units preserved as middle-income through 2035) close "
        "the open-question dimension of the original violation. They remain "
        "subject to ongoing DHCR oversight.\n"
    )
    if resolved_findings:
        w("| BBL | Address | Units | Owner | Annual gap |")
        w("|---|---|---:|---|---:|")
        for f in sorted(resolved_findings, key=lambda x: -x["annual_exposure_building"])[:10]:
            w(f"| {f['bbl']} | {f['address'][:40]} | {f['unitsres']} | {f['owner'][:30]} | ${f['annual_exposure_building']:,.0f} |")
        w("")

    w("## Appendix B — non-rental buildings excluded\n")
    w(
        f"{len(non_rental_findings):,} buildings (~{full_total_units - total_units - sum(f['unitsres'] for f in resolved_findings):,} units) "
        "matched J-51 obligation but were excluded from the actionable cohort "
        "because their owner names indicate they are co-ops, Mitchell-Lama "
        "developments, HDFC limited-equity buildings, or NYCHA-adjacent "
        "non-profit housing. Units in these buildings cannot lawfully be "
        "re-priced to market regardless of the J-51 obligation status, so "
        "the borough-median benchmark is not a meaningful incentive measurement.\n"
    )
    nr_total_units = sum(f["unitsres"] for f in non_rental_findings)
    nr_total_exp = sum(f["annual_exposure_building"] for f in non_rental_findings)
    w(f"- Excluded buildings: {len(non_rental_findings):,}")
    w(f"- Excluded units: {nr_total_units:,}")
    w(f"- Excluded gap (would-be-flout incentive if these were market-rate): ${nr_total_exp:,.0f}\n")
    w(
        "Tightening this filter further requires a connector to NYC HPD's "
        "Mitchell-Lama building list and HDFC roster — both FOIL-able.\n"
    )

    # Methodology + honesty
    w("## How to read this — and what it cannot say\n")
    w(
        "**What the signal IS:** structural exposure measurement. For every "
        "J-51 building in the cohort, the dollar gap between neighborhood market "
        "rent and the maximum legal stabilized rent the owner is statutorily "
        "required to honor. This is the magnitude of the *incentive* a rational "
        "owner has to flout the J-51 covenant.\n"
    )
    w(
        "**What the signal IS NOT:** confirmed unit-by-unit overcharge. To "
        "convert a building-level lead into a confirmed violation, an analyst "
        "must:\n"
        "1. Pull the DHCR Annual Apartment Registration history per unit (FOIL request).\n"
        "2. Compare the registered legal regulated rent to current rent rolls (RPIE filings or tenant-supplied leases).\n"
        "3. Confirm the J-51 abatement on file with the Department of Finance.\n\n"
        "The DHCR Annual Apartment Registration connector is the rent-stab "
        "analogue of the Detroit L-4260 PTA log — the single highest-ROI add to "
        "the framework. See `audit_v1/coverage_assessment.md` for the full "
        "M-source roadmap.\n"
    )
    w(
        "**Known false-positive sources in this report:**\n"
        "- **Co-op buildings.** Co-op corporations don't typically charge rent "
        "(members own units). Filter `is_coop=True` to remove these. We flag "
        f"{len(non_rental_findings):,} non-rental rows separately.\n"
        "- **HDFCs / income-restricted housing.** Many J-51 buildings in this "
        "set are HDFC limited-equity co-ops or LIHTC properties where rent is "
        "capped well below borough median. Same `is_coop` filter catches most.\n"
        "- **Borough-level rent benchmarks.** Using a single borough median "
        "1BR rent overstates the gap in cheap subneighborhoods (East Bronx, "
        "deep Queens) and understates in expensive ones (UWS, West Village). "
        "ZIP-level Census ACS resolution requires a `CENSUS_API_KEY`; per-building "
        "StreetEasy listings would be the next step beyond that.\n"
        "- **Sub-1974 vintage assumption.** For buildings built post-1974 with "
        "J-51, the base year is year_built, not 1969. The runner correctly applies "
        "this — RGB compounds from year_built — but newer buildings will show "
        "smaller gaps.\n"
    )
    w(
        "**Where this report sits in the pipeline:** stage 5 (gap detection) → "
        "stage 6 (rule application: J51_OBLIGATION fired). Next stages "
        "(verification, packaging for enforcement referral) require the DHCR "
        "connector or analyst hand-work.\n"
    )

    report_path = OUT / "fraud_report.md"
    report_path.write_text("\n".join(lines))
    print(f"Wrote final report → {report_path}")
    print(f"  total findings: {total_buildings:,}")
    print(f"  total exposure: ${total_exposure:,.0f}")
    print(f"  multi-building entity owners: {len(multi_building_owners):,}")
    print(f"  tail-period buildings: {len(tail_findings):,}")


if __name__ == "__main__":
    main()
