"""Bond covenant trip-wire monitoring engine.

WHY THIS EXISTS

Hospital muni Master Trust Indentures specify financial covenants that, if
violated, trigger technical default — usually well before any actual missed
payment. Common covenants:

  - Days Cash on Hand minimum (typical: 50-75 days)
  - Debt Service Coverage Ratio (DSCR) minimum (typical: 1.10-1.25x)
  - Maximum Annual Debt Service (MADS) coverage minimum
  - Minimum unrestricted cash (dollar amount)
  - Additional debt test ratios

Once an obligor approaches a covenant, three things happen:
  1. Auditors must disclose covenant compliance status in audited financials
  2. Rating agencies typically begin downgrade reviews
  3. Bond covenant-trigger insurers may demand collateral or reserves

A systematic covenant tripwire monitor that compares CURRENT metrics to
SPECIFIC MTI covenants gives a binary, near-term, sharply-defined warning
that's structurally different from the slower agency outlook revisions our
composite predicts.

INPUT
  - data/covenant_terms.json — verified covenant minimums per obligor
  - data/cafr_overrides.json — current days cash / margin / etc per obligor
  - (future) Live HCRIS for current DSCR computation

OUTPUT
  - For each obligor: GREEN / YELLOW / ORANGE / RED / TRIPWIRED status per
    covenant + per-covenant headroom in percent
  - Aggregate basket scoring

TRIPWIRE TIERS

  GREEN     headroom > 30% — comfortably above covenant
  YELLOW    headroom 15-30% — monitor
  ORANGE    headroom 5-15% — significant risk, agency review possible
  RED       headroom 0-5% — covenant pressure, technical default risk
  TRIPWIRED current metric below covenant — technical default or waiver
            required; rating action highly likely
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent
COVENANT_FILE = HERE / "data" / "covenant_terms.json"
CAFR_FILE = HERE / "data" / "cafr_overrides.json"
OPERATING_FILE = HERE / "data" / "operating_metrics.json"


# -- Tripwire tiering --------------------------------------------------------

TIER_BANDS = [
    # (lower_pct, upper_pct, tier_label, severity)
    (None, 0.0,   "TRIPWIRED", 5),   # current < covenant min
    (0.0,  5.0,   "RED",       4),
    (5.0,  15.0,  "ORANGE",    3),
    (15.0, 30.0,  "YELLOW",    2),
    (30.0, None,  "GREEN",     1),
]


def tripwire_tier(headroom_pct: Optional[float]) -> tuple[str, int]:
    """Map headroom percentage to a tier label."""
    if headroom_pct is None:
        return ("NO_DATA", 0)
    for lo, hi, label, severity in TIER_BANDS:
        if (lo is None or headroom_pct >= lo) and (hi is None or headroom_pct < hi):
            return (label, severity)
    return ("NO_DATA", 0)


def compute_headroom_pct(current: Optional[float], minimum: Optional[float]) -> Optional[float]:
    """Headroom as % of covenant minimum. None if minimum or current is None/0."""
    if minimum is None or minimum == 0 or current is None:
        return None
    return ((current - minimum) / minimum) * 100.0


# -- Per-obligor evaluation ---------------------------------------------------

def compute_dscr(operating_metrics: dict) -> dict:
    """Compute operating-only DSCR and all-income DSCR for an obligor.

    operating_metrics keys:
      total_operating_revenue_usd: float
      operating_margin_pct: float (pre-investment-income, can be negative)
      investment_income_usd: float
      annual_debt_service_usd_estimated: float

    Returns:
      {
        "dscr_operating_only": float (NOI / debt service),
        "dscr_all_income": float ((NOI + invest income) / debt service),
        "noi_operating_only_usd": float,
        "noi_all_income_usd": float,
        "annual_debt_service_usd": float,
        "investment_income_dependency_pct": float (how much of debt service is covered
            by investment income — high % means high MTI-test fragility),
      }
    """
    rev = operating_metrics.get("total_operating_revenue_usd")
    op_margin = operating_metrics.get("operating_margin_pct")
    inv_income = operating_metrics.get("investment_income_usd") or 0  # treat None as 0
    debt_svc = operating_metrics.get("annual_debt_service_usd_estimated")

    if rev is None or op_margin is None or debt_svc is None or debt_svc == 0:
        return {
            "dscr_operating_only": None,
            "dscr_all_income": None,
            "noi_operating_only_usd": None,
            "noi_all_income_usd": None,
            "annual_debt_service_usd": debt_svc,
            "investment_income_dependency_pct": None,
        }

    noi_op = rev * (op_margin / 100.0)
    noi_all = noi_op + inv_income
    dscr_op = noi_op / debt_svc
    dscr_all = noi_all / debt_svc
    # How much of debt service is investment-income-dependent:
    #   If NOI alone covers debt service, dependency = 0
    #   If investment income is the only thing keeping you over 1.0x, dependency is high
    if dscr_all > 0 and dscr_op < 1.0:
        # Inv income contribution = max(0, 1.0 - dscr_op) / dscr_all
        inv_dep = min(1.0, max(0.0, 1.0 - dscr_op) / dscr_all) * 100
    elif dscr_op >= 1.0:
        inv_dep = 0.0
    else:
        inv_dep = 100.0  # both NOI and all-income negative

    return {
        "dscr_operating_only": dscr_op,
        "dscr_all_income": dscr_all,
        "noi_operating_only_usd": noi_op,
        "noi_all_income_usd": noi_all,
        "annual_debt_service_usd": debt_svc,
        "investment_income_dependency_pct": inv_dep,
    }


def evaluate_obligor(name: str, covenants: dict, current_metrics: dict) -> dict:
    """Compute covenant tripwire status for one obligor.

    covenants: subset from covenant_terms.json[obligor]
    current_metrics: e.g., {"days_cash_on_hand": 145, "debt_service_coverage_operating": 1.45,
                            "debt_service_coverage_all_income": 2.27}

    Returns dict with per-covenant headroom + overall worst-case tier.
    """
    results = {}
    worst_severity = 0
    worst_label = "GREEN"

    # Days cash on hand
    if "days_cash_on_hand_minimum" in covenants and "days_cash_on_hand" in current_metrics:
        cov = covenants["days_cash_on_hand_minimum"]
        cur = current_metrics["days_cash_on_hand"]
        hr = compute_headroom_pct(cur, cov["value"])
        tier, sev = tripwire_tier(hr)
        results["days_cash_on_hand"] = {
            "current": cur,
            "covenant_minimum": cov["value"],
            "covenant_source": cov.get("source_url"),
            "covenant_confidence": cov.get("confidence"),
            "headroom_pct": hr,
            "tier": tier,
            "severity": sev,
        }
        if sev > worst_severity:
            worst_severity = sev
            worst_label = tier

    # Debt service coverage — TWO variants: operating-only (strict) and all-income (MTI-like)
    if "debt_service_coverage_minimum" in covenants:
        cov = covenants["debt_service_coverage_minimum"]
        # All-income DSCR is closer to typical MTI definition — primary test
        if "debt_service_coverage_all_income" in current_metrics:
            cur = current_metrics["debt_service_coverage_all_income"]
            hr = compute_headroom_pct(cur, cov["value"])
            tier, sev = tripwire_tier(hr)
            results["debt_service_coverage_all_income"] = {
                "current": cur,
                "covenant_minimum": cov["value"],
                "covenant_source": cov.get("source_url"),
                "covenant_confidence": cov.get("confidence"),
                "headroom_pct": hr,
                "tier": tier,
                "severity": sev,
                "_note": "All-income DSCR (includes investment income) — closer to typical MTI definition",
            }
            if sev > worst_severity:
                worst_severity = sev
                worst_label = tier
        # Operating-only DSCR is the conservative / structural strength test
        if "debt_service_coverage_operating" in current_metrics:
            cur = current_metrics["debt_service_coverage_operating"]
            hr = compute_headroom_pct(cur, cov["value"])
            tier, sev = tripwire_tier(hr)
            results["debt_service_coverage_operating_only"] = {
                "current": cur,
                "covenant_minimum": cov["value"],
                "covenant_source": cov.get("source_url"),
                "covenant_confidence": cov.get("confidence"),
                "headroom_pct": hr,
                "tier": tier,
                "severity": sev,
                "_note": ("Operating-only DSCR (excludes investment income) — "
                          "structural strength test; if this is sub-1.0 while all-income "
                          "is above covenant, the obligor is leaning on investment "
                          "returns to cover debt"),
            }
            # NOTE: do NOT update worst_tier from operating-only — it's an info signal,
            # not a covenant violation. Real covenant violation uses all-income.

    # Investment-income dependency flag (not a covenant, but a fragility signal)
    if "investment_income_dependency_pct" in current_metrics:
        dep = current_metrics["investment_income_dependency_pct"]
        # >50% means investment income provides majority of debt service coverage
        if dep is not None and dep > 50:
            results["investment_income_dependency"] = {
                "dependency_pct": dep,
                "_note": (f"{dep:.0f}% of debt-service coverage is investment-income-derived. "
                          "Bond covenants typically allow this but it represents fragility — "
                          "a market downturn could trip the covenant even with stable operations."),
            }

    # MADS coverage
    if "mads_coverage_minimum" in covenants and "mads_coverage" in current_metrics:
        cov = covenants["mads_coverage_minimum"]
        cur = current_metrics["mads_coverage"]
        hr = compute_headroom_pct(cur, cov["value"])
        tier, sev = tripwire_tier(hr)
        results["mads_coverage"] = {
            "current": cur,
            "covenant_minimum": cov["value"],
            "covenant_source": cov.get("source_url"),
            "covenant_confidence": cov.get("confidence"),
            "headroom_pct": hr,
            "tier": tier,
            "severity": sev,
        }
        if sev > worst_severity:
            worst_severity = sev
            worst_label = tier

    # Distinguish "evaluated and clean" from "no data to evaluate"
    # A covenant counts as evaluable only if current metric is not None
    n_evaluable = sum(
        1 for v in results.values()
        if "tier" in v and v.get("current") is not None and v.get("tier") != "NO_DATA"
    )
    if n_evaluable == 0:
        worst_label = "NO_DATA"
        worst_severity = 0

    return {
        "obligor": name,
        "per_covenant": results,
        "worst_tier": worst_label,
        "worst_severity": worst_severity,
        "n_covenants_evaluated": n_evaluable,
    }


# -- Batch screen across all obligors -----------------------------------------

def run_screen(obligor_subset: Optional[list[str]] = None) -> dict:
    """Run covenant tripwire screen across all obligors in covenant_terms.json.

    obligor_subset: optional list of obligor names to filter. If None, all.

    Returns dict keyed by obligor with eval results, sorted by worst severity.
    """
    if not COVENANT_FILE.exists():
        raise FileNotFoundError(f"{COVENANT_FILE} missing")
    if not CAFR_FILE.exists():
        raise FileNotFoundError(f"{CAFR_FILE} missing")

    covenants_data = json.loads(COVENANT_FILE.read_text())
    cafr_data = json.loads(CAFR_FILE.read_text())
    cafr_overrides = cafr_data.get("overrides", {})
    operating_data = (json.loads(OPERATING_FILE.read_text()).get("obligors", {})
                      if OPERATING_FILE.exists() else {})

    results = []
    for obligor, covs in covenants_data.get("obligors", {}).items():
        if obligor_subset and obligor not in obligor_subset:
            continue
        # Map CAFR metrics → current_metrics
        cafr_record = cafr_overrides.get(obligor, {})
        current_metrics = {}
        if "consolidated_days_cash" in cafr_record:
            current_metrics["days_cash_on_hand"] = cafr_record["consolidated_days_cash"]

        # Compute DSCR if we have operating metrics
        op_record = operating_data.get(obligor)
        if op_record:
            dscr = compute_dscr(op_record)
            current_metrics["debt_service_coverage_operating"] = dscr["dscr_operating_only"]
            current_metrics["debt_service_coverage_all_income"] = dscr["dscr_all_income"]
            current_metrics["investment_income_dependency_pct"] = dscr["investment_income_dependency_pct"]

        eval_result = evaluate_obligor(obligor, covs, current_metrics)
        eval_result["cafr_data_source"] = "data/cafr_overrides.json (HAND-CURATED, see SCHEMA notes)"
        if op_record:
            eval_result["operating_data_source"] = op_record.get("source_url")
            eval_result["operating_data_confidence"] = op_record.get("confidence")
            eval_result["dscr_computation"] = dscr
        results.append(eval_result)

    # Sort by severity descending
    results.sort(key=lambda r: -r["worst_severity"])

    return {
        "evaluated_at": "2026-05-27",
        "n_obligors": len(results),
        "tier_distribution": {
            tier: sum(1 for r in results if r["worst_tier"] == tier)
            for tier in ["TRIPWIRED", "RED", "ORANGE", "YELLOW", "GREEN", "NO_DATA"]
        },
        "results": results,
    }


if __name__ == "__main__":
    import sys
    subset = sys.argv[1:] if len(sys.argv) > 1 else None
    out = run_screen(obligor_subset=subset)
    print(json.dumps(out, indent=2))
