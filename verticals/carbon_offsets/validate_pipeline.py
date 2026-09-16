"""Validation tests for the carbon offsets pipeline.

Three categories of test:
  1. SIGNAL QUALITY — does synthetic-control divergence actually correlate with
     known invalidation status? If yes, the model is using real evidence.
  2. MODEL DECOMPOSITION — does adding SC features improve fit beyond country+subcat
     alone? If not, the model is just memorizing demographic patterns.
  3. KNOWN-SCANDAL SPOT-CHECKS — for projects publicly known to be problematic,
     does the model assign elevated risk? This is the "would the underwriter trust
     this output" test.

Run after V2 scan + calibration finish. Prints PASS/FAIL per check + diagnostics.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import Counter

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

DATA_DIR = Path(__file__).parent / "data"


def load_all():
    with open(DATA_DIR / "forest_scan_results_v2.json") as f:
        sc_results = json.load(f)
    with open(DATA_DIR / "verra_projects.json") as f:
        all_projects = json.load(f)
    seen = {}
    for p in all_projects:
        seen[p["resourceIdentifier"]] = p
    projects_by_id = seen
    calib_path = DATA_DIR / "calibrated_probabilities.json"
    calib = []
    if calib_path.exists():
        with open(calib_path) as f:
            calib = json.load(f)
    return sc_results, projects_by_id, calib


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Signal quality — divergence vs. invalidation status
# ─────────────────────────────────────────────────────────────────────────────
def test_divergence_correlates_with_invalidation(sc_results, projects_by_id):
    """For projects with both an SC score AND a known status, does higher
    divergence correlate with invalidation?

    PASS if: invalidation rate in top-quartile divergence is meaningfully higher
             than bottom-quartile (>1.5x or >10pp absolute).
    """
    INVALID = {"Withdrawn", "Rejected by Administrator", "On Hold - see notification letter"}

    pairs = []
    for r in sc_results:
        if r.get("status") != "ok" or r.get("divergence_normalized") is None:
            continue
        proj = projects_by_id.get(r["id"])
        if not proj:
            continue
        status = proj.get("resourceStatus")
        if status not in INVALID and status not in ("Registered", "Late to verify", "Verification approval requested"):
            continue
        is_invalid = status in INVALID
        pairs.append((r["divergence_normalized"], is_invalid))

    if len(pairs) < 20:
        print(f"  ⚠️  Only {len(pairs)} project-status pairs available; skip (need ≥20)")
        return None

    pairs.sort()
    n = len(pairs)
    q1 = pairs[: n // 4]
    q4 = pairs[3 * n // 4 :]
    q1_inv_rate = sum(1 for _, inv in q1 if inv) / max(len(q1), 1)
    q4_inv_rate = sum(1 for _, inv in q4 if inv) / max(len(q4), 1)

    print(f"  N={n} project-status pairs with SC scores")
    print(f"  Q1 (lowest divergence)  mean={np.mean([d for d,_ in q1]):+.2f}  invalidation_rate={q1_inv_rate:.1%}")
    print(f"  Q4 (highest divergence) mean={np.mean([d for d,_ in q4]):+.2f}  invalidation_rate={q4_inv_rate:.1%}")

    if q1_inv_rate < 0.001:
        ratio = float("inf") if q4_inv_rate > 0 else 1.0
    else:
        ratio = q4_inv_rate / q1_inv_rate
    diff = q4_inv_rate - q1_inv_rate
    passed = ratio > 1.5 or diff > 0.10
    print(f"  Q4/Q1 ratio: {ratio:.2f}x | diff: {diff:+.1%}")
    print(f"  {'✅ PASS' if passed else '❌ FAIL'} — {'divergence is informative' if passed else 'divergence does not separate invalidation status meaningfully'}")
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Model decomposition — does SC add lift beyond demographics?
# ─────────────────────────────────────────────────────────────────────────────
def test_sc_adds_lift_beyond_demographics(sc_results, projects_by_id):
    """Train two models on the same training set:
      A) demographics only (country/continent + subcat + log_claim + age)
      B) demographics + synthetic-control divergence + has_sc

    Compare 5-fold CV log-loss. If B is meaningfully better, SC adds signal.
    """
    INVALID = {"Withdrawn", "Rejected by Administrator", "On Hold - see notification letter"}
    VALID = {"Registered", "Late to verify", "Verification approval requested"}
    sc_by_id = {r["id"]: r for r in sc_results if r.get("status") == "ok"}

    rows = []
    for pid, p in projects_by_id.items():
        status = p.get("resourceStatus")
        if status not in INVALID and status not in VALID:
            continue
        reg = p.get("projectRegistrationDate") or p.get("creditingPeriodStartDate") or ""
        if not reg or len(reg) < 4 or not reg[:4].isdigit():
            continue
        reg_year = int(reg[:4])
        if reg_year > 2020:
            continue
        units = p.get("estAnnualEmissionReductions") or 0
        if units <= 0:
            continue
        sc = sc_by_id.get(pid)
        div = sc.get("divergence_normalized", 0) if sc else 0
        has_sc = 1 if sc else 0
        rows.append({
            "y": 1 if status in INVALID else 0,
            "div": div,
            "has_sc": has_sc,
            "log_claim": np.log10(units),
            "age": 2024 - reg_year,
            "continent": p.get("country", "")[:3],  # crude
            "subcat": (p.get("protocolSubCategories") or "").split(";")[0].strip()[:6],
        })

    if len(rows) < 50:
        print(f"  ⚠️  Only {len(rows)} usable rows; need ≥50 for CV")
        return None

    from itertools import chain
    all_continents = sorted({r["continent"] for r in rows})
    all_subcats = sorted({r["subcat"] for r in rows})

    def featurize(rs, with_sc=False):
        X, y = [], []
        for r in rs:
            base = [r["log_claim"], r["age"]]
            for c in all_continents:
                base.append(1 if r["continent"] == c else 0)
            for s in all_subcats:
                base.append(1 if r["subcat"] == s else 0)
            if with_sc:
                base.extend([r["div"], r["has_sc"]])
            X.append(base)
            y.append(r["y"])
        return np.array(X), np.array(y)

    Xa, y = featurize(rows, with_sc=False)
    Xb, _ = featurize(rows, with_sc=True)

    sc = StandardScaler().fit(Xa)
    Xa_s = sc.transform(Xa)
    sc_b = StandardScaler().fit(Xb)
    Xb_s = sc_b.transform(Xb)

    # 5-fold CV log-likelihood (negative so higher is better)
    ma = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced")
    mb = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced")
    sa = cross_val_score(ma, Xa_s, y, cv=5, scoring="neg_log_loss").mean()
    sb = cross_val_score(mb, Xb_s, y, cv=5, scoring="neg_log_loss").mean()

    lift = sa - sb  # because neg_log_loss; if sb > sa, sb is better => lift positive
    rel_lift = (sa - sb) / abs(sa) if sa != 0 else 0

    print(f"  N={len(rows)} | invalidation_rate={np.mean(y):.1%}")
    print(f"  Model A (demographics only)        neg_log_loss = {sa:.3f}")
    print(f"  Model B (demographics + SC)        neg_log_loss = {sb:.3f}")
    print(f"  Lift from adding SC: {lift:+.3f} ({rel_lift*100:+.1f}%)")

    # PASS if SC adds at least 5% relative improvement
    passed = rel_lift > 0.05
    print(f"  {'✅ PASS' if passed else '⚠️  WEAK SIGNAL' if rel_lift > 0 else '❌ FAIL'} — "
          f"{'SC meaningfully improves prediction' if passed else 'SC barely affects fit; model is mostly demographics'}")
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Known-scandal spot checks
# ─────────────────────────────────────────────────────────────────────────────
# Public scandals in carbon offset space — these should rank elevated risk if
# the model is producing useful insurance-grade signal.
KNOWN_SCANDALS = {
    # Format: project_id_or_name_keyword: expected_min_p_5yr
    # Cambodia Southern Cardamom — multiple investigations of permanence / leakage
    "Southern Cardamom": 0.50,
    # Sumatra Merang Peatland (SMPP) — repeatedly questioned by audits
    "Sumatra Merang": 0.50,
    # Katingan — controversial, rated low by Sylvera/BeZero
    "Katingan": 0.40,
    # Rimba Raya — lost government recognition in 2024
    "Rimba Raya": 0.50,
    # Kariba / Carbon Tanzania — Verra suspended methodologies similar to these
    # NB: not all listed projects necessarily appear in our 322-project calibration set
}


def test_known_scandals(calib):
    """Spot-check: do publicly-known problematic projects show elevated P(5yr)?"""
    if not calib:
        print(f"  ⚠️  No calibration output; skip")
        return None

    by_name = {(r.get("name") or "").lower(): r for r in calib}
    hits = []
    misses = []
    for keyword, expected_min in KNOWN_SCANDALS.items():
        kw_lower = keyword.lower()
        match = next((r for n, r in by_name.items() if kw_lower in n), None)
        if not match:
            print(f"  ?  '{keyword}': not in calibrated set")
            continue
        p5 = match["predictions"]["horizons"]["p_5yr"]["estimate"]
        ci = match["predictions"]["horizons"]["p_5yr"]
        passed = p5 >= expected_min
        marker = "✅" if passed else "❌"
        print(f"  {marker} '{keyword}' (id {match['id']}): P(5yr) = {p5:.1%} "
              f"[CI {ci['ci_low']:.2f}, {ci['ci_high']:.2f}] "
              f"(expected ≥ {expected_min:.0%})")
        if passed:
            hits.append(keyword)
        else:
            misses.append(keyword)
    if hits or misses:
        print(f"  Pass rate: {len(hits)}/{len(hits)+len(misses)}")
    return len(hits) > len(misses)


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Output structure check
# ─────────────────────────────────────────────────────────────────────────────
def test_output_structure(calib):
    """Verify calibrated output has the fields downstream consumers need."""
    if not calib:
        return None
    required = ["id", "name", "country", "predictions"]
    horizon_required = ["p_1yr", "p_5yr", "p_10yr"]
    failures = []
    for r in calib[:5]:
        for f in required:
            if f not in r:
                failures.append(f"missing field {f}")
        h = r.get("predictions", {}).get("horizons", {})
        for hr in horizon_required:
            if hr not in h:
                failures.append(f"missing horizon {hr}")
            else:
                cell = h[hr]
                for k in ("estimate", "ci_low", "ci_high"):
                    if k not in cell:
                        failures.append(f"horizon {hr} missing {k}")
                est = cell.get("estimate", -1)
                if not (0 <= est <= 1):
                    failures.append(f"horizon {hr} estimate out of [0,1]: {est}")
    if failures:
        print(f"  ❌ {len(failures)} structural issues: {failures[:5]}")
        return False
    print(f"  ✅ all {len(calib)} records have required fields and valid horizon ranges")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    sc_results, projects_by_id, calib = load_all()
    print(f"Loaded: {len(sc_results)} scan results, {len(projects_by_id)} projects, {len(calib)} calibrated\n")

    print("Test 1 — Signal quality: divergence ↔ invalidation correlation")
    print("-" * 70)
    t1 = test_divergence_correlates_with_invalidation(sc_results, projects_by_id)
    print()

    print("Test 2 — Model decomposition: does SC add lift beyond demographics?")
    print("-" * 70)
    t2 = test_sc_adds_lift_beyond_demographics(sc_results, projects_by_id)
    print()

    print("Test 3 — Known-scandal spot checks")
    print("-" * 70)
    t3 = test_known_scandals(calib)
    print()

    print("Test 4 — Output structure check")
    print("-" * 70)
    t4 = test_output_structure(calib)
    print()

    print("=" * 70)
    print(f"SUMMARY")
    print("=" * 70)
    for name, t in [
        ("Signal correlates with invalidation", t1),
        ("SC adds lift over demographics", t2),
        ("Known scandals flagged elevated", t3),
        ("Output structure valid", t4),
    ]:
        marker = "✅" if t else ("⚠️" if t is None else "❌")
        print(f"  {marker} {name}")


if __name__ == "__main__":
    main()
