"""
Probability calibration model.

Trains a logistic regression to predict P(invalidation_within_5yr) given:
  - Synthetic-control divergence score (primary feature)
  - Project age at observation
  - Project type (REDD/ARR/IFM)
  - Geography (continent grouping)
  - Project size (log hectares)
  - Crediting period start year

Training labels:
  Verra projects with status "Withdrawn" or "Rejected by Administrator" = invalidated (1)
  Verra projects with status "Registered" = not invalidated (0)

Output per project (whether in training set or not):
  - p_1yr, p_5yr, p_10yr (probability invalidated within horizon)
  - confidence interval via bootstrap
  - feature contributions for explainability
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample

DATA_DIR = Path(__file__).parent / "data"

# Continent mapping for project geography feature
CONTINENT_MAP = {
    # South America
    "Brazil": "south_america", "Peru": "south_america", "Colombia": "south_america",
    "Argentina": "south_america", "Chile": "south_america", "Uruguay": "south_america",
    "Venezuela": "south_america", "Bolivia": "south_america", "Ecuador": "south_america",
    "Paraguay": "south_america", "Guyana": "south_america", "Suriname": "south_america",
    # Central America / Caribbean
    "Mexico": "central_america", "Guatemala": "central_america", "Honduras": "central_america",
    "Nicaragua": "central_america", "Costa Rica": "central_america", "Panama": "central_america",
    "El Salvador": "central_america", "Belize": "central_america",
    "Dominican Republic": "central_america", "Haiti": "central_america", "Cuba": "central_america",
    # North America
    "United States": "north_america", "Canada": "north_america",
    # Africa
    "Kenya": "africa", "Tanzania": "africa", "Uganda": "africa", "Ethiopia": "africa",
    "Madagascar": "africa", "Ghana": "africa", "Nigeria": "africa", "Senegal": "africa",
    "Rwanda": "africa", "Cameroon": "africa", "South Africa": "africa", "Mozambique": "africa",
    "Niger": "africa", "Burkina Faso": "africa", "Mali": "africa", "Zambia": "africa",
    "Zimbabwe": "africa", "Malawi": "africa", "Namibia": "africa", "Botswana": "africa",
    "Sierra Leone": "africa", "Liberia": "africa", "Cote d'Ivoire": "africa",
    "Congo, The Democratic Republic of The": "africa", "Congo": "africa",
    # Asia
    "Indonesia": "asia", "India": "asia", "China": "asia", "Cambodia": "asia",
    "Vietnam": "asia", "Thailand": "asia", "Philippines": "asia", "Malaysia": "asia",
    "Bangladesh": "asia", "Pakistan": "asia", "Nepal": "asia", "Myanmar": "asia",
    "Lao People's Democratic Republic": "asia", "Sri Lanka": "asia",
    # Oceania
    "Papua New Guinea": "oceania", "Australia": "oceania", "New Zealand": "oceania",
    # Europe
    "Spain": "europe", "Portugal": "europe", "Italy": "europe", "Romania": "europe",
    "France": "europe", "Germany": "europe", "United Kingdom": "europe",
}


def get_continent(country):
    return CONTINENT_MAP.get(country, "other")


def get_subcat_simple(subcat):
    if not subcat:
        return "unknown"
    s = subcat.split(";")[0].strip()
    if s in ("REDD", "ARR", "IFM", "ALM", "WRC"):
        return s
    return "other"


def build_training_set(projects, scan_results=None):
    """
    Build training set:
      - X: features per project
      - y: 1 if invalidated (Withdrawn/Rejected), 0 if Registered/active

    Only include projects with crediting period that had time to be evaluated
    (registered before 2020 to give 5yr observation window).
    """
    # Index synthetic-control results by project ID for divergence feature
    sc_by_id = {}
    if scan_results:
        for r in scan_results:
            if r.get("status") == "ok" and r.get("divergence_normalized") is not None:
                sc_by_id[r["id"]] = r

    INVALID_STATUSES = {"Withdrawn", "Rejected by Administrator", "On Hold - see notification letter"}
    VALID_STATUSES = {"Registered", "Late to verify", "Verification approval requested"}

    X = []
    y = []
    project_meta = []

    for p in projects:
        status = p.get("resourceStatus")
        if status not in INVALID_STATUSES and status not in VALID_STATUSES:
            continue

        # Need registration date for project age
        reg_date = p.get("projectRegistrationDate") or p.get("creditingPeriodStartDate")
        if not reg_date or len(reg_date) < 4:
            continue
        try:
            reg_year = int(reg_date[:4])
        except ValueError:
            continue
        if reg_year > 2020:
            continue  # too recent to have observation window

        pid = p["resourceIdentifier"]

        # Features
        units_claimed = p.get("estAnnualEmissionReductions") or 0
        if units_claimed <= 0:
            continue

        # Synthetic control divergence (if available)
        sc = sc_by_id.get(pid)
        if sc:
            divergence = sc.get("divergence_normalized") or 0
            has_sc = 1
        else:
            divergence = 0
            has_sc = 0

        feature_dict = {
            "divergence_normalized": divergence,
            "has_synthetic_control": has_sc,
            "project_age_years": 2024 - reg_year,
            "log_claim_tco2": np.log10(units_claimed) if units_claimed > 0 else 0,
            "subcat": get_subcat_simple(p.get("protocolSubCategories")),
            "continent": get_continent(p.get("country", "")),
        }

        X.append(feature_dict)
        y.append(1 if status in INVALID_STATUSES else 0)
        project_meta.append({
            "id": pid,
            "name": p.get("resourceName"),
            "status": status,
            "country": p.get("country"),
            "subcat": p.get("protocolSubCategories"),
            "claim": units_claimed,
            "registration_year": reg_year,
        })

    return X, np.array(y), project_meta


def featurize(X_dicts, all_subcats=None, all_continents=None):
    """Convert list-of-dicts to numeric matrix with one-hot for categoricals."""
    if all_subcats is None:
        all_subcats = sorted(set(d["subcat"] for d in X_dicts))
    if all_continents is None:
        all_continents = sorted(set(d["continent"] for d in X_dicts))

    rows = []
    for d in X_dicts:
        row = [
            d["divergence_normalized"],
            d["has_synthetic_control"],
            d["project_age_years"],
            d["log_claim_tco2"],
        ]
        for s in all_subcats:
            row.append(1 if d["subcat"] == s else 0)
        for c in all_continents:
            row.append(1 if d["continent"] == c else 0)
        rows.append(row)
    return np.array(rows), all_subcats, all_continents


def feature_names(all_subcats, all_continents):
    base = ["divergence_normalized", "has_synthetic_control", "project_age_years", "log_claim_tco2"]
    sub = [f"subcat_{s}" for s in all_subcats]
    con = [f"continent_{c}" for c in all_continents]
    return base + sub + con


def train_model(X_dicts, y, n_bootstrap=200):
    """Train logistic regression with bootstrap CI."""
    X, all_subcats, all_continents = featurize(X_dicts)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    base_model = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced")
    base_model.fit(X_scaled, y)

    base_pred = base_model.predict_proba(X_scaled)[:, 1]
    base_acc = base_model.score(X_scaled, y)
    print(f"Training set: {len(y)} projects ({y.sum()} invalidated, {len(y)-y.sum()} valid)", file=sys.stderr)
    print(f"Base model accuracy: {base_acc:.3f}", file=sys.stderr)
    print(f"Predicted invalidation rate: {base_pred.mean():.3f}", file=sys.stderr)
    print(f"Actual invalidation rate: {y.mean():.3f}", file=sys.stderr)

    # Print coefficients for interpretability
    print(f"\nFeature coefficients (in scaled space):", file=sys.stderr)
    fnames = feature_names(all_subcats, all_continents)
    coefs = base_model.coef_[0]
    for name, c in sorted(zip(fnames, coefs), key=lambda x: -abs(x[1]))[:15]:
        print(f"  {name:<30}  {c:+.3f}", file=sys.stderr)

    # Bootstrap for CI
    boot_models = []
    for i in range(n_bootstrap):
        X_boot, y_boot = resample(X_scaled, y, n_samples=len(y))
        try:
            m = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced")
            m.fit(X_boot, y_boot)
            boot_models.append(m)
        except Exception:
            continue

    return {
        "model": base_model,
        "scaler": scaler,
        "all_subcats": all_subcats,
        "all_continents": all_continents,
        "boot_models": boot_models,
    }


def predict_with_ci(model_bundle, X_dicts, horizons_yrs=(1, 5, 10)):
    """Predict P(invalidation) for each project with bootstrap CI.

    The base model trained on (registered before 2020 → invalidated by 2024)
    estimates a roughly 5-year invalidation probability. We extrapolate to other
    horizons assuming exponential decay with constant hazard.
    """
    X, _, _ = featurize(X_dicts, model_bundle["all_subcats"], model_bundle["all_continents"])
    X_scaled = model_bundle["scaler"].transform(X)

    base_p5yr = model_bundle["model"].predict_proba(X_scaled)[:, 1]

    # Bootstrap for CI
    boot_preds = []
    for m in model_bundle["boot_models"]:
        p = m.predict_proba(X_scaled)[:, 1]
        boot_preds.append(p)
    if boot_preds:
        boot_arr = np.array(boot_preds)  # (n_boot, n_projects)
        ci_low = np.percentile(boot_arr, 2.5, axis=0)
        ci_high = np.percentile(boot_arr, 97.5, axis=0)
    else:
        ci_low = base_p5yr
        ci_high = base_p5yr

    # Convert P(5yr) to constant-hazard rate, then re-derive other horizons
    # P(t) = 1 - exp(-lambda * t), so lambda = -ln(1 - P(5)) / 5
    eps = 1e-6
    lambdas = -np.log(np.clip(1 - base_p5yr, eps, 1 - eps)) / 5
    lambdas_low = -np.log(np.clip(1 - ci_low, eps, 1 - eps)) / 5
    lambdas_high = -np.log(np.clip(1 - ci_high, eps, 1 - eps)) / 5

    out = []
    for i in range(len(X_dicts)):
        rec = {"horizons": {}}
        for h in horizons_yrs:
            p = 1 - np.exp(-lambdas[i] * h)
            p_low = 1 - np.exp(-lambdas_low[i] * h)
            p_high = 1 - np.exp(-lambdas_high[i] * h)
            rec["horizons"][f"p_{h}yr"] = {
                "estimate": float(p),
                "ci_low": float(p_low),
                "ci_high": float(p_high),
            }
        out.append(rec)
    return out


def main():
    # Load Verra projects (full registry for training set)
    with open(DATA_DIR / "verra_projects.json") as f:
        all_projects = json.load(f)

    # Dedupe by ID
    seen = {}
    for p in all_projects:
        seen[p["resourceIdentifier"]] = p
    projects = list(seen.values())

    # Filter to forest projects (where we have synthetic control)
    FOREST_SUBCATS = {"REDD", "ARR", "IFM", "WRC"}
    def is_forest(p):
        sub = (p.get("protocolSubCategories") or "").strip()
        if not sub: return False
        return any(s.strip() in FOREST_SUBCATS for s in sub.split(";"))

    projects = [p for p in projects if is_forest(p)]
    print(f"Forest projects total: {len(projects)}", file=sys.stderr)

    # Load synthetic control results if available
    sc_path = DATA_DIR / "forest_scan_results_v2.json"
    if sc_path.exists():
        with open(sc_path) as f:
            sc_results = json.load(f)
    else:
        # Fall back to old scan results (use ratio_observed_to_claimed inverted as divergence proxy)
        with open(DATA_DIR / "forest_scan_results.json") as f:
            old_results = json.load(f)
        sc_results = []
        for r in old_results:
            if r.get("status") == "ok" and r.get("ratio_observed_to_claimed") is not None:
                # Approximate divergence: 1 - ratio (high = lots of underdelivery)
                divergence = max(min(1.0 - r["ratio_observed_to_claimed"], 2.0), -2.0)
                sc_results.append({
                    "id": r["id"],
                    "status": "ok",
                    "divergence_normalized": divergence,
                })
        print(f"Using v1 results as proxy: {len(sc_results)} divergence scores", file=sys.stderr)

    # Build training set
    X_train, y_train, train_meta = build_training_set(projects, sc_results)
    print(f"\nTraining set size: {len(X_train)}", file=sys.stderr)
    inv_rate = y_train.mean()
    print(f"Invalidation rate in training: {inv_rate:.1%}", file=sys.stderr)

    # Sanity: verify divergence is correlated with invalidation
    div_vals = [d["divergence_normalized"] for d in X_train]
    has_sc = [d["has_synthetic_control"] for d in X_train]
    n_sc = sum(has_sc)
    print(f"Projects with synthetic-control divergence: {n_sc}/{len(X_train)}", file=sys.stderr)
    if n_sc > 10:
        with_sc_inv = [y for y, hs in zip(y_train, has_sc) if hs]
        without_sc_inv = [y for y, hs in zip(y_train, has_sc) if not hs]
        print(f"  Invalidation rate with SC: {np.mean(with_sc_inv):.1%}", file=sys.stderr)
        print(f"  Invalidation rate without SC: {np.mean(without_sc_inv):.1%}", file=sys.stderr)

        # Bin by divergence and show invalidation rate
        sc_only = [(d["divergence_normalized"], y) for d, y in zip(X_train, y_train) if d["has_synthetic_control"]]
        sc_only.sort()
        n = len(sc_only)
        if n >= 20:
            print("\nInvalidation rate by divergence quintile:", file=sys.stderr)
            quintile_size = n // 5
            for q in range(5):
                start = q * quintile_size
                end = (q+1) * quintile_size if q < 4 else n
                bucket = sc_only[start:end]
                avg_div = np.mean([d for d, _ in bucket])
                inv = np.mean([y for _, y in bucket])
                print(f"  Q{q+1} (div ≈ {avg_div:+.2f}): {inv:.1%} invalidation rate ({len(bucket)} projects)", file=sys.stderr)

    # Train
    bundle = train_model(X_train, y_train)

    # Predict for ALL projects (including those outside training set, for forward-looking scoring)
    X_all, y_all, all_meta = build_training_set(projects, sc_results)  # could include even more recent ones
    predictions = predict_with_ci(bundle, X_all)

    # Combine into output records
    output = []
    for meta, pred in zip(all_meta, predictions):
        output.append({
            **meta,
            "actual_status": meta["status"],
            "predictions": pred,
        })

    # Sort by p_5yr descending (highest-risk first)
    output.sort(key=lambda r: -r["predictions"]["horizons"]["p_5yr"]["estimate"])

    out_path = DATA_DIR / "calibrated_probabilities.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved {len(output)} calibrated predictions to {out_path}", file=sys.stderr)

    # Print top 20 highest-risk projects
    print(f"\n=== TOP 20 HIGHEST P(INVALIDATION_5YR) ===", file=sys.stderr)
    print(f"{'ID':<6} {'Country':<20} {'Status':<22} {'P(5y)':>7} {'CI':>20}  Name", file=sys.stderr)
    print("-" * 130, file=sys.stderr)
    for r in output[:20]:
        h = r["predictions"]["horizons"]["p_5yr"]
        ci = f"[{h['ci_low']:.2f}, {h['ci_high']:.2f}]"
        print(f"{r['id']:<6} {r['country'][:20]:<20} {r['status'][:22]:<22} {h['estimate']:>6.1%} {ci:>20}  {r['name'][:50]}", file=sys.stderr)


if __name__ == "__main__":
    main()
