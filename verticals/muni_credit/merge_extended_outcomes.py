"""Merge original (Dec 2022 - Mar 2025) outcomes with extension (Apr 2025 - May 2026)
into a NEW combined outcome class per obligor.

Output: data/verified_outcomes_extended/{slug}.json — same structure as original.
"""
from __future__ import annotations

import json
import glob
import re
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
EXTENDED_DIR = DATA / "verified_outcomes_extended" / "per_obligor"
EXTENDED_DIR.mkdir(parents=True, exist_ok=True)


# Outcome severity ranking — higher = more negative
SEVERITY = {
    "UPGRADE": 1,
    "AFFIRM_POSITIVE_OUTLOOK": 2,
    "AFFIRM_STABLE": 3,
    "AFFIRM_NEGATIVE_OUTLOOK": 4,
    "DOWNGRADE": 5,
    "MULTI_DOWNGRADE": 6,
    "DEFAULT": 7,
    "UNVERIFIABLE": 0,
    "NONE_FOUND": 0,
    None: 0,
}


def merge_outcome_classes(original: str, extension: str) -> str:
    """Merge logic:
      - Extension only OVERRIDES original if it shows new DETERIORATION (NEG_OUTLOOK or worse)
      - Stable/upgrade/positive extension does NOT override an earlier upgrade
      - The whole-window outcome should capture: did the credit deteriorate at any point?
    """
    if extension in (None, "NONE_FOUND", "UNVERIFIABLE", "AFFIRM_STABLE",
                     "AFFIRM_POSITIVE_OUTLOOK", "UPGRADE"):
        return original
    if original in (None, "UNVERIFIABLE"):
        return extension

    # Extension is a deterioration class; take it only if more severe than original
    orig_sev = SEVERITY.get(original, 0)
    ext_sev = SEVERITY.get(extension, 0)
    if ext_sev > orig_sev:
        return extension
    return original


def main():
    # Load original outcomes
    orig_dir = DATA / "verified_outcomes_2023_2025" / "per_obligor"
    extension_data = json.loads((DATA / "extension_outcomes_2025_2026.json").read_text())
    extension_obligors = extension_data.get("obligors", {})

    print(f"Original outcome files: {len(list(orig_dir.glob('*.json')))}")
    print(f"Extension outcomes: {len(extension_obligors)}")

    n_merged = 0
    n_changed = 0
    transitions = []

    for orig_f in sorted(orig_dir.glob("*.json")):
        d = json.loads(orig_f.read_text())
        name = d.get("obligor_name")
        if not name:
            continue
        original_class = d.get("computed_outcome_class")

        # Try to find matching extension entry (by name, alias, or state-stripped)
        ext_entry = extension_obligors.get(name)
        if not ext_entry:
            bare = re.sub(r"\s*\([^)]+\)\s*", "", name).strip()
            ext_entry = extension_obligors.get(bare)
        if not ext_entry:
            for alias in d.get("obligor_aliases", []) or []:
                ext_entry = extension_obligors.get(alias)
                if ext_entry:
                    break

        ext_class = (ext_entry or {}).get("extension_period_summary")
        new_class = merge_outcome_classes(original_class, ext_class)

        if new_class != original_class:
            transitions.append((name, original_class, ext_class, new_class))
            n_changed += 1

        # Write extended outcome file
        d_out = dict(d)
        d_out["computed_outcome_class"] = new_class
        d_out["_extension"] = {
            "original_outcome_class": original_class,
            "extension_period": "2025-04-01 to 2026-05-27",
            "extension_outcome_class": ext_class,
            "new_actions": (ext_entry or {}).get("new_actions", []),
        }
        d_out["window_end"] = "2026-05-27"
        out_path = EXTENDED_DIR / orig_f.name
        out_path.write_text(json.dumps(d_out, indent=2))
        n_merged += 1

    print(f"\nMerged {n_merged} obligors, {n_changed} had outcome class changes")
    print(f"\nTransitions (original → extended):")
    for name, orig, ext, new in transitions:
        print(f"  {name:<45} {orig:<25} + ext {ext:<25} → {new}")


if __name__ == "__main__":
    main()
