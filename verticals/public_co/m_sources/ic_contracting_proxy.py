"""
Intelligence Community contracting proxy.

WHY THIS EXISTS
IC contracts (NIP ~$77B, MIP ~$25B per FY26) are largely classified.
Pentagon J-Book and usaspending both have limited IC visibility:
- J-Book lists program elements for unclassified work only; the bulk of
  NSA/NRO/CIA work has no PE-level disclosure.
- USAspending shows obligations to recipients but classifies most IC
  agencies' detailed task orders.

Yet many services primes (BAH 16% IC, SAIC ~25% national-security,
CACI ~70% IC, LDOS ~30% intel) disclose IC revenue percentages in their
10-Ks. These claims land NOT_FOUND in pentagon_jbook (no PE to query)
and look "real" against usaspending only at agency-aggregate level.

This connector triangulates three signals:

1. CLEARED-FTE BENCHMARK (the f)
   IC services revenue is dominated by labor. Industry-standard
   utilization × revenue-per-cleared-FTE gives an envelope:
     expected_IC_revenue = cleared_FTE × utilization × rev_per_cleared_FTE
   Defaults: utilization=0.75, rev_per_cleared_FTE=$145k.

2. USASPENDING IC-AGENCY FLOOR
   Sum visible recipient obligations from IC agencies USASpending
   indexes (DIA, NGA, DCSA, partial DLA-intel). This is a LOWER BOUND
   on actual IC revenue; classified TOs aren't visible.

3. DISCLOSED CLAIM (R)
   The number the 10-K reports.

VERDICT (the f → comparison)
  CONSISTENT          — claim ∈ [0.7×, 1.3×] benchmark AND visible
                         floor ≥ 0.3× claim
  SUSPICIOUSLY_HIGH   — claim > 1.4× benchmark
  SUSPICIOUSLY_LOW    — claim < 0.6× benchmark (likely under-disclosed)
  COVERAGE_INSUFFICIENT — visible floor < 0.2× claim AND benchmark is
                         within range; we can't validate either direction
  UNVERIFIABLE        — missing inputs (cleared_FTE not disclosed)

LIMITATIONS
- The cleared-FTE × benchmark math is industry-standard but not
  company-specific. A heavily back-office company has lower
  revenue-per-cleared-FTE than a heavily delivery-side one.
- USAspending visibility into IC agencies is partial; some agencies
  (NSA, NRO, CIA) don't appear at all in unclassified spend data.
- This proxy doesn't pull peer benchmarks (SAIC/CACI/LDOS norms) — a v2
  enhancement would pull peer cleared-FTE disclosures from their 10-Ks
  and compute a peer-normalized residual.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["737", "873", "366"],
    "issuer_features": ["mentions_intelligence_community"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "Proxies classified IC contract exposure where J-Book and USAspending have no visibility.",
}

from typing import Any, Optional

from . import usaspending

# IC awarding-agency names as USAspending indexes them. Names must match
# the agency.toptier_name field in USAspending. NSA/NRO/CIA don't appear
# in unclassified spend data — visible-floor is a partial signal.
IC_AGENCIES = (
    "Defense Intelligence Agency",
    "National Geospatial-Intelligence Agency",
    "Defense Counterintelligence and Security Agency",
    # DISA carries cross-IC IT contracts; partial signal:
    "Defense Information Systems Agency",
)

# Industry-standard cleared-FTE economics.
DEFAULT_UTILIZATION_RATE = 0.75
DEFAULT_REVENUE_PER_CLEARED_FTE_K = 145.0  # $K per FTE per year


def query_ic_revenue_consistency(
    recipient_name: str,
    disclosed_ic_revenue_M: Optional[float] = None,
    cleared_employees: Optional[int] = None,
    fiscal_year: Optional[int] = None,
    utilization: float = DEFAULT_UTILIZATION_RATE,
    revenue_per_cleared_FTE_K: float = DEFAULT_REVENUE_PER_CLEARED_FTE_K,
) -> dict[str, Any]:
    """Verify an IC-revenue disclosure against cleared-FTE benchmark + USASpending floor.

    Args:
      recipient_name:             company name for usaspending lookup
      disclosed_ic_revenue_M:     IC revenue claimed in 10-K ($M)
      cleared_employees:          headcount with active security clearance
      fiscal_year:                fiscal year of the disclosure
      utilization:                billable utilization rate (default 0.75)
      revenue_per_cleared_FTE_K:  $K of annual revenue per cleared FTE (default 145)

    Returns:
      {
        "disclosed_M":           float (echo),
        "expected_M":            float (cleared × utilization × rev/FTE),
        "visible_floor_M":       float (sum of usaspending IC-agency obligations),
        "visible_by_agency":     dict (agency_name → total $M),
        "ratio_disclosed_to_expected": float,
        "ratio_visible_to_disclosed":  float,
        "signal":                CONSISTENT | SUSPICIOUSLY_HIGH | SUSPICIOUSLY_LOW |
                                  COVERAGE_INSUFFICIENT | UNVERIFIABLE,
        "fiscal_year":           int or None,
        "_inputs":               dict echo of inputs + benchmark params,
        "_note":                 human explainer,
      }
    """
    inputs = {
        "recipient_name":             recipient_name,
        "disclosed_ic_revenue_M":     disclosed_ic_revenue_M,
        "cleared_employees":          cleared_employees,
        "fiscal_year":                fiscal_year,
        "utilization":                utilization,
        "revenue_per_cleared_FTE_K":  revenue_per_cleared_FTE_K,
    }

    # Need at least disclosed + cleared to compute the consistency check
    if disclosed_ic_revenue_M is None or cleared_employees is None:
        return {
            "disclosed_M":      disclosed_ic_revenue_M,
            "expected_M":       None,
            "visible_floor_M":  None,
            "visible_by_agency": {},
            "ratio_disclosed_to_expected": None,
            "ratio_visible_to_disclosed":  None,
            "signal":           "UNVERIFIABLE",
            "fiscal_year":      fiscal_year,
            "_inputs":          inputs,
            "_note": (
                "Need both disclosed_ic_revenue_M and cleared_employees to "
                "run the benchmark consistency check. The 10-K typically "
                "discloses cleared headcount in the Human Capital section."
            ),
        }

    # 1. Compute the benchmark envelope
    expected_M = cleared_employees * utilization * revenue_per_cleared_FTE_K / 1000.0  # → $M

    # 2. Pull USAspending IC-agency floor
    # Window: 12 months ending at FY (Sep 30 typical for federal FY)
    if fiscal_year:
        end_date = f"{fiscal_year}-09-30"
        start_date = f"{fiscal_year - 1}-10-01"
    else:
        end_date = "2026-12-31"
        start_date = "2025-01-01"

    visible_floor_M = 0.0
    visible_by_agency: dict[str, float] = {}
    for agency in IC_AGENCIES:
        try:
            # IC agencies are subtier under DoD — use subtier filter.
            r = usaspending.query_recipient_contracts(
                recipient_name=recipient_name,
                start_date=start_date,
                end_date=end_date,
                awarding_agency=agency,
                awarding_agency_tier="subtier",
                page_size=5,
            )
            amt = float(r.get("total_amount", 0) or 0) / 1e6  # → $M
        except Exception:
            amt = 0.0
        visible_by_agency[agency] = amt
        visible_floor_M += amt

    # 3. Compute ratios and adjudicate
    ratio_disclosed_to_expected = disclosed_ic_revenue_M / expected_M if expected_M > 0 else None
    ratio_visible_to_disclosed = visible_floor_M / disclosed_ic_revenue_M if disclosed_ic_revenue_M > 0 else None

    # Signal logic:
    # - If disclosed claim is wildly above benchmark → SUSPICIOUSLY_HIGH (likely inflated)
    # - If disclosed claim is wildly below benchmark → SUSPICIOUSLY_LOW (under-disclosed, less concerning)
    # - Else: check the visible floor. If visible floor is so small it can't
    #   even ground-truth the disclosure → COVERAGE_INSUFFICIENT.
    if ratio_disclosed_to_expected is None:
        signal = "UNVERIFIABLE"
    elif ratio_disclosed_to_expected > 1.4:
        signal = "SUSPICIOUSLY_HIGH"
    elif ratio_disclosed_to_expected < 0.6:
        signal = "SUSPICIOUSLY_LOW"
    elif ratio_visible_to_disclosed is not None and ratio_visible_to_disclosed < 0.2:
        signal = "COVERAGE_INSUFFICIENT"
    else:
        signal = "CONSISTENT"

    note_parts = [
        f"Benchmark: {cleared_employees:,} cleared × {utilization:.2f} util × "
        f"${revenue_per_cleared_FTE_K:.0f}k/FTE = ${expected_M:,.0f}M expected.",
        f"Disclosed: ${disclosed_ic_revenue_M:,.0f}M ({ratio_disclosed_to_expected:.2f}× benchmark)." if ratio_disclosed_to_expected else "",
        f"USAspending IC-agency floor (DIA+NGA+DCSA+DISA): ${visible_floor_M:,.0f}M "
        f"({ratio_visible_to_disclosed:.2f}× disclosed)." if ratio_visible_to_disclosed is not None else "",
    ]

    return {
        "disclosed_M":                  disclosed_ic_revenue_M,
        "expected_M":                   expected_M,
        "visible_floor_M":              visible_floor_M,
        "visible_by_agency":            visible_by_agency,
        "ratio_disclosed_to_expected":  ratio_disclosed_to_expected,
        "ratio_visible_to_disclosed":   ratio_visible_to_disclosed,
        "signal":                       signal,
        "fiscal_year":                  fiscal_year,
        "_inputs":                      inputs,
        "_note":                        " ".join(p for p in note_parts if p),
    }
