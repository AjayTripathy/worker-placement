"""Knowledge-graph-driven dispatch helper.

Inverts the previous convention where dispatch was directory-hardcoded
(`dispatch_prompt_template.IPO_DETECTORS = [list literal]`). Instead, walks
every detector + M-source module in the repo, reads each module's `APPLIES_TO`
constant, and returns the relevance subset for a given issuer profile.

This makes the knowledge graph PRESCRIPTIVE (what applies?) in addition to
DESCRIPTIVE (what exists?). Adding a new detector or M-source with a sensible
APPLIES_TO declaration means the orchestrator will auto-surface it on the next
dispatch — no bridge files, no cross-vertical imports written by hand.

## APPLIES_TO contract

Each detector / M-source module SHOULD declare a module-level constant:

```python
APPLIES_TO = {
    "sic_codes": [3812, 3721, ...],           # exact SIC matches
    "sic_prefixes": ["381", "372", ...],      # SIC-prefix matches
    "issuer_features": [                       # string predicates evaluated
        "mentions_dod_program",                 #   against the issuer profile's
        "government_customer_concentration_above_5pct",  # `features` set
    ],
    "asset_classes": ["corporate_ipo_dd"],     # asset-class tags
    "applies_universally": False,              # True = ignore predicates, always apply
    "kind": "detector" | "m_source" | "helper", # how to use it
    "summary": "Short description of what it tests.",
    "verification_question": "R/M gap framing (optional)",
}
```

If `APPLIES_TO` is absent, the module is treated as non-dispatchable (e.g.,
pure utility code that isn't a detector or verifier).

## Issuer profile contract

```python
issuer = {
    "name": "Quantinuum Inc.",
    "cik": "2110105",
    "sic": "7373",                              # str (EDGAR uses str) — both ok
    "asset_classes": {"corporate_ipo_dd"},      # set of class tags
    "features": {                               # set of issuer-feature strings
        "mentions_dod_program",
        "mentions_darpa",
        "mentions_doe_program",
        "government_customer_concentration_above_5pct",
        "upc_tra_structure",
        "egc_status",
    },
}
```

The orchestrator populates `features` from the S-1 / F-1 (keyword scan or LLM
extraction). It's the same set of strings the detector APPLIES_TO references —
that's the contract.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _module_paths_to_scan() -> list[str]:
    """All Python modules that may declare APPLIES_TO.
    Walks verticals/*/detectors/, verticals/*/rules/, verticals/*/m_sources/.
    """
    paths = []
    verticals_dir = REPO_ROOT / "verticals"
    for vd in verticals_dir.iterdir():
        if not vd.is_dir():
            continue
        for sub in ("detectors", "rules", "m_sources", "connectors"):
            d = vd / sub
            if not d.exists():
                continue
            for f in sorted(d.glob("*.py")):
                if f.name in ("__init__.py", "union_runner.py", "honesty_decomposed.py"):
                    continue
                # Convert path to module dotted-name relative to repo root
                rel = f.relative_to(REPO_ROOT).with_suffix("")
                mod_name = ".".join(rel.parts)
                paths.append(mod_name)
    return paths


def _safe_import(mod_name: str):
    try:
        return importlib.import_module(mod_name)
    except Exception:
        return None


def _module_applies_to(mod) -> dict | None:
    return getattr(mod, "APPLIES_TO", None)


def _matches(applies_to: dict, issuer: dict) -> bool:
    """Test whether APPLIES_TO predicate matches an issuer profile.

    Matching logic:
      - asset_class is treated as SCOPE not match: if both sides declare classes
        and there's no overlap, the module is out-of-scope, regardless of other
        signals.
      - `anti_features` is a HARD-NO gate: if the issuer has any feature listed
        in anti_features, the detector is excluded even if SIC/feature/universal
        would otherwise match. Use for detectors whose results are
        low-information or actively misleading on certain issuer types.
      - `must_have_feature` is a HARD-YES gate: when present, the issuer MUST
        have that feature in its features set OR the detector is excluded.
        Use for narrow-scope detectors that would over-match on SIC alone.
      - Within scope and gates, a module matches if:
          * applies_universally=True (universal-within-its-asset-classes), OR
          * any sic_code / sic_prefix match, OR
          * any issuer_features intersection.
        Asset-class match ALONE is not sufficient (would over-broaden).
    """
    if not applies_to:
        return False
    decl_classes = set(applies_to.get("asset_classes") or [])
    issuer_classes = set(issuer.get("asset_classes") or [])
    # Scope check: if both sides declare classes and they don't overlap, hard-NO
    if decl_classes and issuer_classes and not (decl_classes & issuer_classes):
        return False
    issuer_features = set(issuer.get("features") or [])
    # Anti-feature hard-NO gate (general-purpose; left in matcher for future use)
    anti = set(applies_to.get("anti_features") or [])
    if anti & issuer_features:
        return False
    # must_have hard-YES gate (any-of semantics; supports both singleton legacy
    # `must_have_feature: "X"` and list `must_have_any_feature: [...]`)
    must_any = list(applies_to.get("must_have_any_feature") or [])
    if applies_to.get("must_have_feature"):
        must_any.append(applies_to["must_have_feature"])
    if must_any and not (set(must_any) & issuer_features):
        return False
    # Universal within scope (after gates)
    if applies_to.get("applies_universally"):
        return True
    # Sic-code / sic-prefix / feature match (positive matches)
    sic = str(issuer.get("sic") or "")
    if sic:
        try:
            if int(sic) in (applies_to.get("sic_codes") or []):
                return True
        except ValueError:
            pass
        if any(sic.startswith(p) for p in (applies_to.get("sic_prefixes") or [])):
            return True
    if issuer_features & set(applies_to.get("issuer_features") or []):
        return True
    return False


def relevant_for_issuer(issuer: dict) -> list[dict]:
    """Return the full applicable-module inventory for an issuer profile.

    Returns a list of dicts:
      {"module": "verticals.buyside_dd.detectors.dual_class_voting_concentration",
       "kind": "detector" | "m_source" | "helper",
       "vertical": "buyside_dd",
       "name": "dual_class_voting_concentration",
       "summary": "...",
       "verification_question": "..." (optional),
       "applies_to": {...},
       "match_reasons": ["sic_prefix=383", "feature=mentions_darpa"]}
    """
    results = []
    for mod_name in _module_paths_to_scan():
        mod = _safe_import(mod_name)
        if mod is None:
            continue
        a = _module_applies_to(mod)
        if a is None:
            continue
        if not _matches(a, issuer):
            continue
        # Determine match reasons (for debuggability)
        reasons = []
        sic = str(issuer.get("sic") or "")
        if a.get("applies_universally"):
            reasons.append("universal")
        if sic and int(sic) in (a.get("sic_codes") or []):
            reasons.append(f"sic_code={sic}")
        for p in a.get("sic_prefixes") or []:
            if sic.startswith(p):
                reasons.append(f"sic_prefix={p}")
        for f in set(issuer.get("features") or []) & set(a.get("issuer_features") or []):
            reasons.append(f"feature={f}")
        for c in set(issuer.get("asset_classes") or []) & set(a.get("asset_classes") or []):
            reasons.append(f"asset_class={c}")

        parts = mod_name.split(".")
        vertical = parts[1] if len(parts) >= 2 else "?"
        name = parts[-1]
        results.append({
            "module": mod_name,
            "kind": a.get("kind", "detector"),
            "vertical": vertical,
            "name": name,
            "summary": a.get("summary", (mod.__doc__ or "").strip().split("\n")[0] if mod.__doc__ else ""),
            "verification_question": a.get("verification_question"),
            "applies_to": a,
            "match_reasons": reasons,
        })
    # De-dup by name (clinicaltrials_lookup helper + detector should both appear; module path differs)
    return results


def detector_names_for_issuer(issuer: dict) -> list[str]:
    """Convenience: just the detector + m_source names, deduped, dispatch-ready order.
    Detectors first, then M-sources, then helpers."""
    items = relevant_for_issuer(issuer)
    order = {"detector": 0, "m_source": 1, "helper": 2}
    items.sort(key=lambda x: (order.get(x["kind"], 9), x["name"]))
    return [i["name"] for i in items]


def coverage_report(prompt_text: str, issuer: dict) -> dict:
    """Return which graph-known applicable detectors are NOT mentioned in the prompt.

    Used by dispatch_prompt_pre_flight_validator.validate_coverage().
    """
    applicable = relevant_for_issuer(issuer)
    present, missing = [], []
    for it in applicable:
        if it["name"] in prompt_text:
            present.append(it["name"])
        else:
            missing.append({
                "name": it["name"],
                "kind": it["kind"],
                "vertical": it["vertical"],
                "summary": it["summary"],
                "verification_question": it.get("verification_question"),
                "match_reasons": it["match_reasons"],
            })
    return {
        "n_applicable": len(applicable),
        "n_present": len(present),
        "n_missing": len(missing),
        "present": present,
        "missing": missing,
    }


if __name__ == "__main__":
    # Quick demo
    import json
    issuer = {
        "name": "Quantinuum Inc.",
        "sic": "7373",
        "asset_classes": {"corporate_ipo_dd"},
        "features": {
            "mentions_dod_program",
            "mentions_darpa",
            "mentions_nqi",
            "mentions_q_next",
            "government_customer_concentration_above_5pct",
            "upc_tra_structure",
            "egc_status",
        },
    }
    print(f"Issuer: {issuer['name']}  SIC={issuer['sic']}")
    print(f"Features: {sorted(issuer['features'])}")
    print()
    print("=== Applicable detectors + M-sources ===")
    for it in relevant_for_issuer(issuer):
        print(f"  [{it['kind']:8}] {it['vertical']}/{it['name']:45} via {', '.join(it['match_reasons'])}")
