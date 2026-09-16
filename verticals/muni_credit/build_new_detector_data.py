"""Build detector data for the new detectors from existing artifacts.

- R/f/M decomposed: pull per-check scores from honesty_screen_results.json
- Going-concern: grep MD&A text files for "substantial doubt" / "going concern"
- DOJ FCA: skip — agent is collecting

Outputs: data/detector_data_honesty_going_concern.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

# Map slugs (used by honesty screen) to canonical obligor names (used by tripwire)
SLUG_TO_OBLIGOR = {
    "ascension": "Ascension Health",
    "upmc": "UPMC",
    "trinity_health": "Trinity Health",
    "cleveland_clinic": "Cleveland Clinic",
    "commonspirit": "CommonSpirit Health",
    "tower_health": "Tower Health",
    "mount_sinai": "Mount Sinai Health System (NYC)",
    "allegheny_health": "Allegheny Health Network",
    "rwjbarnabas": "RWJBarnabas Health",
    "nyu_langone": "NYU Langone Health",
    "mass_general_brigham": "Mass General Brigham",
    "mgb": "Mass General Brigham",
    "atrium_health": "Atrium Health",
    "advocate_health": "Atrium Health",
    "providence": "Providence St Joseph",
    "geisinger": "Geisinger Health System",
    "iu_health": "Indiana University Health",
    "henry_ford": "Henry Ford Health System",
    "christianacare": "ChristianaCare",
    "yale_new_haven": "Yale New Haven Health",
    "kaiser": "Kaiser Foundation",
    "bjc": "BJC HealthCare",
    "banner_health": "Banner Health",
    "duke_health": "Duke University Health",
    "stanford_health": "Stanford Health Care",
    "mayo_clinic": "Mayo Clinic",
    "cedars_sinai": "Cedars-Sinai",
    "nyp": "NewYork-Presbyterian",
    "northwell": "Northwell Health",
    "johns_hopkins": "Johns Hopkins Health System",
    "memorial_sloan_kettering": "Memorial Sloan Kettering",
    "msk": "Memorial Sloan Kettering",
    "adventhealth": "AdventHealth",
    "memorial_hermann": "Memorial Hermann",
    "houston_methodist": "Houston Methodist",
    "texas_childrens": "Texas Children's Hospital",
    "chop": "Childrens Hospital Philadelphia",
    "uchealth": "UCHealth",
    "wellstar": "Wellstar Health System",
    "sutter": "Sutter Health",
    "ssm_health": "SSM Health",
    "bon_secours": "Bon Secours Mercy Health",
    "intermountain_test": "Intermountain Healthcare",
    "corewell": "Spectrum Health (Corewell)",
    "ohiohealth": "OhioHealth",
    "inova": "Inova Health System",
    "childrens_atlanta": "Children's Healthcare of Atlanta",
    "unc_health_test": "UNC Health Care",
    "multicare": "MultiCare Health System",
    "hackensack_meridian": "Hackensack Meridian Health",
    "carilion": "Carilion Clinic",
    "norton_healthcare": "Norton Healthcare",
    "baptist_health_florida": "Baptist Health South Florida",
    "lifespan": "Lifespan",
    "lehigh_valley": "Lehigh Valley Health Network",
    "penn_medicine": "Penn Medicine",
    "boston_childrens": "Children's Hospital Boston",
    "bilh": "Beth Israel Lahey Health",
    "chla": "Children's Hospital Los Angeles",
    "centura": "Centura Health (now CommonSpirit)",
    "allina": "Allina Health",
    "avera": "Avera Health",
    "sanford": "Sanford Health",
    "adventist_health": "Adventist Health (Roseville)",
    "loma_linda": "Loma Linda University Medical Center",
}


def build_honesty_decomposed():
    honesty_path = HERE / "outputs" / "honesty_screen_results.json"
    if not honesty_path.exists():
        return {}
    honesty = json.loads(honesty_path.read_text())
    out = {}
    for slug, r in honesty.items():
        obligor = SLUG_TO_OBLIGOR.get(slug, slug)
        checks = r.get("checks", {})
        out[obligor] = {
            "rating_action_omission": {
                "rating_action_acknowledgment_score": checks.get("rating_action_acknowledgment", {}).get("score"),
            },
            "operating_margin_obscured": {
                "operating_margin_disclosure_score": checks.get("operating_margin_disclosure", {}).get("score"),
            },
            "same_facility_framing_heavy": {
                "same_facility_density_per_1000": checks.get("same_facility_framing", {}).get("mentions_per_1000_words"),
            },
        }
    return out


def grep_going_concern_in_mdas():
    """Search MD&A texts for going-concern language using the boilerplate-aware
    detector function (going_concern.has_going_concern_language)."""
    from detectors.going_concern import has_going_concern_language
    out = {}
    mda_dir = DATA / "mdas"
    if not mda_dir.exists():
        return out
    for txt_path in sorted(mda_dir.glob("*.txt")):
        slug = txt_path.stem.replace("_mda", "")
        obligor = SLUG_TO_OBLIGOR.get(slug, slug)
        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        found, excerpt = has_going_concern_language(text)
        out[obligor] = {
            "going_concern": {
                "audit_opinion_has_going_concern_language": False,
                "mda_has_going_concern_language": found,
                "going_concern_excerpt": excerpt,
                "source_url": str(txt_path),
                "confidence": "HIGH" if found else "MEDIUM",
            }
        }
    return out


def main():
    honesty_data = build_honesty_decomposed()
    going_concern_data = grep_going_concern_in_mdas()

    merged = {}
    for obligor in set(honesty_data) | set(going_concern_data):
        merged[obligor] = {
            **honesty_data.get(obligor, {}),
            **going_concern_data.get(obligor, {}),
        }

    out_path = DATA / "detector_data_honesty_going_concern.json"
    out_path.write_text(json.dumps({
        "_doc": "R/f/M decomposed + going-concern detector data, built from existing artifacts",
        "verified_at": "2026-05-27",
        "obligors": merged,
    }, indent=2, default=str))

    n_obligors = len(merged)
    n_honesty = sum(1 for v in merged.values() if v.get("rating_action_omission"))
    n_gc = sum(1 for v in merged.values() if v.get("going_concern", {}).get("mda_has_going_concern_language"))

    print(f"Built detector data for {n_obligors} obligors")
    print(f"  Honesty scores available: {n_honesty}")
    print(f"  Going-concern hits in MD&A: {n_gc}")
    if n_gc > 0:
        print(f"\n  Going-concern positives:")
        for obligor, v in merged.items():
            gc = v.get("going_concern", {})
            if gc.get("mda_has_going_concern_language"):
                excerpt = gc.get("going_concern_excerpt", "")[:120]
                print(f"    {obligor}: {excerpt}...")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
