"""principal_litigation_flag — fires when a deal's named principal/operator/sponsor/GP carries
MATERIAL federal litigation (the dangerous categories), as opposed to the routine operational
litigation every large operator accumulates.

THE SIGNAL. An operator-credential pitch ("we built the #4 franchisee," "proven sponsor") rests on
the principal's record. The material risk is hidden litigation: securities/fraud, RICO, investor /
breach-of-fiduciary, franchisor termination, or a bankruptcy where the principal/entity is the
DEBTOR. A 1,000-unit restaurant operator WILL have wage-hour / ADA / employment suits — that is
NOT a red flag and must not be treated as one (false positives erode the signal).

THE KILLER CONDITION (severity HIGH): the subject appears as a DEFENDANT/DEBTOR in a material-category
case. disambiguation_needed (common name, hits not clearable) -> REVIEW. Baseline-only or zero -> clean.

VALIDATED 2026-06-17 on PCM Hospitality: Barry Dubin / B Wild / 7 Star Eats / Sublime Huts / KBP /
US Laundry = NO material hits (only routine employment/ADA at the KBP franchisee) -> does NOT fire.

CONTRACT: evaluate(principals, screen) -> {fires, reason, severity, evidence}. Consumes the
litigation_screen connector's classified per-entity observations.
"""
from __future__ import annotations

COVERAGE = ("Federal/RECAP dockets only — STATE courts, full PACER, and UCC liens are not covered "
            "and remain a paid/manual escalation; clean here ≠ clean everywhere.")


def evaluate(principals: list[str], screen: dict) -> dict:
    """
    principals = the named operator/sponsor/GP entities & people the deal rests on (for context).
    screen = litigation_screen output: {name: {federal_dockets, material_hits:[...], n_material,
             disambiguation_needed, all_hits:[...]}}  (one entry per entity/person screened).
    """
    material, ambiguous, baseline_only, ev = [], [], [], {}
    for name, s in (screen or {}).items():
        mh = s.get("material_hits") or []
        if mh:
            material.append({"name": name, "cases": [h.get("case") for h in mh],
                             "labels": sorted({h.get("label") for h in mh})})
        elif s.get("disambiguation_needed"):
            ambiguous.append({"name": name, "federal_dockets": s.get("federal_dockets")})
        elif (s.get("federal_dockets") or 0) > 0:
            baseline_only.append(name)
    ev = {"material": material, "disambiguation_needed": ambiguous,
          "baseline_only": baseline_only, "coverage": COVERAGE, "screened": list((screen or {}).keys())}

    if material:
        return {"fires": True, "reason": "MATERIAL_PRINCIPAL_LITIGATION", "severity": "HIGH",
                "evidence": {**ev, "interpretation":
                    "A named principal/operator/sponsor appears as defendant/debtor in material-"
                    "category federal litigation (securities/fraud/RICO/investor-fiduciary/franchise/"
                    "debtor-bankruptcy). Pull the dockets and assess before relying on the credential."}}
    if ambiguous:
        return {"fires": True, "reason": "LITIGATION_DISAMBIGUATION_NEEDED", "severity": "REVIEW",
                "evidence": {**ev, "interpretation":
                    "Common-name federal hits could not be cleared as the subject vs. unrelated "
                    "parties — confirm by hand (or via paid PACER party search) before concluding clean."}}
    return {"fires": False, "reason": "NO_MATERIAL_PRINCIPAL_LITIGATION", "severity": "CLEAR",
            "evidence": {**ev, "interpretation":
                "No material-category federal litigation against the screened principals/entities; "
                f"any hits are routine operational suits (employment/ADA). {COVERAGE}"}}


# APPLIES_TO contract — dispatch index keys on this (feedback_kg_dispatch_index_pattern)
APPLIES_TO = {
    "asset_classes": ["private_equity", "private_re_credit", "real_estate_development", "venture",
                      "hedge_fund", "fund_manager", "co_investment", "any_with_named_principal"],
    "must_have_feature": "named_principal_or_operator",     # a sponsor/GP/operator the deal rests on
    "requires_sources": ["litigation_screen"],
    "fires_on": "material-category federal litigation against a named principal/operator (not routine "
                "employment/ADA); disambiguation_needed -> REVIEW",
}


if __name__ == "__main__":
    # PCM Hospitality demo — the validated clean case
    screen = {
        "Barry Dubin": {"federal_dockets": 8, "material_hits": [], "n_material": 0,
                        "disambiguation_needed": True},
        "B Wild Investments": {"federal_dockets": 0, "material_hits": []},
        "Sublime Huts": {"federal_dockets": 0, "material_hits": []},
        "KBP Brands": {"federal_dockets": 8, "material_hits": [],
                       "all_hits": [{"case": "Myers v. KBP Brands, LLC", "label": "flsa_wage_hour"}]},
    }
    r = evaluate(["Barry Dubin", "B Wild Investments", "Sublime Huts", "KBP Brands"], screen)
    print("fires:", r["fires"], "| severity:", r["severity"], "| reason:", r["reason"])
    print(" ", r["evidence"]["interpretation"])
    # material demo (synthetic)
    bad = {"Acme Sponsor LLC": {"federal_dockets": 2, "material_hits": [
        {"case": "SEC v. Acme Sponsor LLC", "label": "securities/commodities"}], "n_material": 1}}
    r2 = evaluate(["Acme Sponsor LLC"], bad)
    print("material-case fires:", r2["fires"], "| severity:", r2["severity"], "(should be HIGH)")
