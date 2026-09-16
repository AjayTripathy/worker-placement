"""Inline the full IPO-DD knowledge-graph dispatch index into diligencer prompts,
and validate detector coverage against an issuer's features AFTER the run.

WHY THIS EXISTS
---------------
The keyword feature-scanner (`infer_features_from_text`) used to PRE-FILTER the
M-source menu *before* the LLM ran: a dumb gate upstream of a high-intelligence
selector. It silently subtracted applicable detectors — e.g. `pentagon_jbook`
never reached the RIPO subagents because the hand-curated menu omitted it, so the
agent could not pick what it never saw.

This module inverts that:
  - SELECTION (intelligent): show the agent the WHOLE applicable graph. It declares
    the issuer's features and picks / declines each applicable detector itself.
  - DETERMINISM (relocated): moved downstream into `coverage_gaps()`, which
    re-derives the applicable set from union(agent-declared features, keyword-net
    features) and flags any applicable detector neither dispatched nor explicitly
    declined. The keyword scanner survives only as a validation safety-net, never
    as the primary selector.
"""
from __future__ import annotations

import re
from functools import lru_cache

from knowledge_graph import dispatch as kgd

# Asset-class scope for a newly-public-company IPO diligence run.
IPO_ASSET_CLASSES = {
    "corporate_ipo_dd", "public_co_defense", "public_co_space",
    "public_co_quantum", "diagnostics_biotech_dd",
}

# Per-source dispatch guidance, rendered inline in the index AND enforced by the
# validator's query-quality check. The lesson from KRMN: an agent can SELECT the
# right source but query it on the wrong key (contractor_name on a subcomponent
# supplier that is never a prime → structurally guaranteed NOT_FOUND), then rule
# out a fire by reasoning instead of measurement. Coverage != query quality.
DISPATCH_NOTES = {
    "pentagon_jbook": (
        "Query BY NAMED PROGRAM / PE NUMBER — pulled from the prospectus AND from the "
        "program/award titles usaspending returns (e.g. 'Small Diameter Bomb', PE "
        "'1206410SF'). Run one query per material named program. NEVER contractor_name-"
        "only: subcomponent suppliers are never primes, so contractor-absence is "
        "uninformative and a contractor-only NOT_FOUND is a WEAK dispatch, not a clean "
        "check. The fire unit is the PROGRAM's forward funding, not whether the corpus "
        "lists the issuer."
    ),
    "doe_budget": (
        "Same discipline as pentagon_jbook: query by the named DOE/NQI program or PE, "
        "not by the company. Company-absence is not program-defunding."
    ),
}

# Query-quality rules: a dispatched source must use at least one of these kwarg
# keys, else the validator marks it WEAK_DISPATCH (invoked, but not meaningfully).
WEAK_DISPATCH_RULES = {
    "pentagon_jbook": {"requires_any": ["program_name", "pe_number"]},
    "doe_budget": {"requires_any": ["program_name", "pe_number"]},
}


def _in_ipo_scope(applies_to: dict) -> bool:
    decl = set(applies_to.get("asset_classes") or [])
    # No declared classes => unscoped, include it; else require IPO overlap.
    return (not decl) or bool(decl & IPO_ASSET_CLASSES)


@lru_cache(maxsize=1)
def _ipo_menu() -> tuple[dict, ...]:
    """Every detector / M-source / helper whose APPLIES_TO is in IPO scope.

    This is the FULL menu shown to the agent — not pre-filtered by issuer features.
    """
    out = []
    for mod_name in kgd._module_paths_to_scan():
        mod = kgd._safe_import(mod_name)
        if mod is None:
            continue
        a = kgd._module_applies_to(mod)
        if not a or not _in_ipo_scope(a):
            continue
        parts = mod_name.split(".")
        out.append({
            "name": parts[-1],
            "vertical": parts[1] if len(parts) > 1 else "?",
            "kind": a.get("kind", "detector"),
            "features": list(a.get("issuer_features") or []),
            "universal": bool(a.get("applies_universally")),
            "must_have": list(a.get("must_have_any_feature") or [])
                         + ([a["must_have_feature"]] if a.get("must_have_feature") else []),
            "summary": (a.get("summary") or "").strip(),
            "vq": (a.get("verification_question") or "").strip(),
        })
    order = {"m_source": 0, "detector": 1, "helper": 2}
    out.sort(key=lambda e: (order.get(e["kind"], 9), e["name"]))
    return tuple(out)


@lru_cache(maxsize=1)
def feature_vocabulary() -> tuple[str, ...]:
    """The declarable issuer-feature strings, gathered from the live menu's
    APPLIES_TO blocks (the true contract — not the keyword scanner's subset)."""
    feats: set[str] = set()
    for e in _ipo_menu():
        feats.update(e["features"])
        feats.update(e["must_have"])
    return tuple(sorted(feats))


def _catalog_call(name: str) -> str | None:
    """Map an m_source module name to its exact catalog call key, if present."""
    try:
        from .m_source_catalog import CATALOG
    except Exception:
        return None
    for key in CATALOG:
        if key.split(".")[0] == name:
            return key
    return None


def _feature_glossary() -> dict[str, str]:
    try:
        from verticals.buyside_dd.dispatch_prompt_template import _FEATURE_KEYWORDS
    except Exception:
        return {}
    return {k: (v[0] if v else "") for k, v in _FEATURE_KEYWORDS.items()}


def dispatch_block() -> str:
    """Prompt-injectable text: the full feature vocabulary + the full applicable
    detector/M-source index + the declare-and-account contract."""
    gloss = _feature_glossary()
    L: list[str] = []
    w = L.append
    w("== KNOWLEDGE-GRAPH DISPATCH INDEX (consult this; do NOT rely on a curated menu) ==")
    w("This is the COMPLETE set of detectors and M-sources that can apply to an IPO-DD")
    w("issuer. You — not a keyword scanner — decide which apply to THIS company. Two steps:")
    w("")
    w("STEP A — DECLARE FEATURES. From the prospectus, emit `issuer_features`: the subset")
    w("of the vocabulary below that is TRUE of this issuer. Be literal and complete — a")
    w("missed feature hides its detectors. Vocabulary (feature → hint):")
    for f in feature_vocabulary():
        h = gloss.get(f, "")
        w(f"  - {f}" + (f"  ({h})" if h else ""))
    w("")
    w("STEP B — ACCOUNT FOR EVERY APPLICABLE ITEM. An item APPLIES if it is universal")
    w("(fires on all IPOs) or if any of its trigger features is in your declared set.")
    w("For each applicable item, either (1) map ≥1 query to a claim, or (2) record an")
    w("explicit decline with a reason. Items below are grouped by kind.")
    w("")
    cur = None
    for e in _ipo_menu():
        if e["kind"] != cur:
            cur = e["kind"]
            w(f"--- {cur.upper()} ---")
        trig = "UNIVERSAL (all IPOs)" if e["universal"] else ("features: " + ", ".join(e["features"]) if e["features"] else "—")
        line = f"  • {e['name']}"
        call = _catalog_call(e["name"]) if e["kind"] == "m_source" else None
        if call:
            line += f"  [call: {call}]"
        w(line)
        w(f"      {trig}")
        desc = e["vq"] or e["summary"]
        if desc:
            w(f"      Q: {desc}")
        note = DISPATCH_NOTES.get(e["name"])
        if note:
            w(f"      ! QUERY DISCIPLINE: {note}")
    w("")
    w("STEP C — RECORD THE ACCOUNTING in input.json under `detector_dispatch` (see schema):")
    w('  "detector_dispatch": [{"detector": "<name>", "status": "dispatched|declined|not_applicable",')
    w('                          "reason": "<one line; why declined / which claim it maps to>"}]')
    w("List EVERY applicable item exactly once. A post-run coverage validator re-derives")
    w("the applicable set from your features (plus a keyword safety-net over the filing)")
    w("and flags anything applicable that you neither dispatched nor declined.")
    return "\n".join(L)


# ─────────────────────────────────────────────────────────────────────────────
# Output-side coverage validation
# ─────────────────────────────────────────────────────────────────────────────
def infer_features(filing_text: str) -> set[str]:
    """Keyword safety-net (the OLD pre-filter, demoted to a validation backstop)."""
    try:
        from verticals.buyside_dd.dispatch_prompt_template import infer_features_from_text
    except Exception:
        return set()
    return infer_features_from_text(filing_text or "")


def applicable_for(features, sic: str | None = None) -> list[dict]:
    issuer = {
        "sic": sic or "",
        "asset_classes": IPO_ASSET_CLASSES,
        "features": set(features or ()),
    }
    return kgd.relevant_for_issuer(issuer)


def coverage_gaps(input_obj: dict, filing_text: str | None = None,
                  sic: str | None = None) -> dict:
    """Re-derive applicable detectors from union(agent features, keyword-net) and
    classify each as DISPATCHED / DECLINED / GAP against the agent's accounting."""
    agent_feats = set(input_obj.get("issuer_features") or [])
    kw_feats = infer_features(filing_text) if filing_text else set()
    feats = agent_feats | kw_feats

    # source -> list of kwarg-key sets actually used (for query-quality checks)
    source_query_keys: dict[str, list[set]] = {}
    for c in input_obj.get("claims") or []:
        for q in c.get("queries") or []:
            src, keys = _query_source_and_keys(q)
            if src:
                source_query_keys.setdefault(src, []).append(keys)
    dispatched_sources = set(source_query_keys)

    accounting = {}
    for d in input_obj.get("detector_dispatch") or []:
        accounting[d.get("detector")] = (_norm_status(d.get("status")), d.get("reason", ""))

    applicable = applicable_for(feats, sic=sic)
    rows, gaps, weak = [], [], []
    for it in applicable:
        name = it["name"]
        acct_status, acct_reason = accounting.get(name, (None, ""))
        if name in dispatched_sources or acct_status == "dispatched":
            status = "DISPATCHED"
            rule = WEAK_DISPATCH_RULES.get(name)
            if rule:
                req = set(rule.get("requires_any") or [])
                keysets = source_query_keys.get(name, [])
                strong = any(req & ks for ks in keysets)
                if not strong:
                    status = "WEAK_DISPATCH"
        elif acct_status in ("declined", "not_applicable"):
            status = "DECLINED"
        else:
            status = "GAP"
        row = {
            "name": name, "kind": it["kind"], "status": status,
            "match_reasons": it["match_reasons"], "reason": acct_reason,
            "vq": it.get("verification_question") or it.get("summary"),
            "query_keys": sorted({k for ks in source_query_keys.get(name, []) for k in ks}),
        }
        rows.append(row)
        if status == "GAP":
            gaps.append(it)
        elif status == "WEAK_DISPATCH":
            weak.append(row)
    return {
        "agent_features": sorted(agent_feats),
        "keyword_only_features": sorted(kw_feats - agent_feats),
        "n_applicable": len(applicable),
        "n_dispatched": sum(1 for r in rows if r["status"] == "DISPATCHED"),
        "n_declined": sum(1 for r in rows if r["status"] == "DECLINED"),
        "n_weak": len(weak),
        "n_gap": len(gaps),
        "rows": rows,
        "weak_dispatches": [{"name": r["name"], "query_keys": r["query_keys"],
                             "required": WEAK_DISPATCH_RULES.get(r["name"], {}).get("requires_any"),
                             "vq": r["vq"]} for r in weak],
        "gaps": [{"name": g["name"], "kind": g["kind"],
                  "match_reasons": g["match_reasons"],
                  "vq": g.get("verification_question") or g.get("summary")} for g in gaps],
    }


# Agents phrase the dispatch status freely; normalize to the schema vocabulary so
# a near-synonym ("MAPPED", "DECLINE", "n/a") does not register as a phantom GAP.
_STATUS_SYNONYMS = {
    "dispatched": "dispatched", "mapped": "dispatched", "dispatch": "dispatched",
    "queried": "dispatched", "mapped_to_claim": "dispatched", "covered": "dispatched",
    "declined": "declined", "decline": "declined", "not_applicable": "declined",
    "n/a": "declined", "na": "declined", "not applicable": "declined", "skip": "declined",
    "skipped": "declined",
}


def _norm_status(s) -> str | None:
    if not s:
        return None
    return _STATUS_SYNONYMS.get(str(s).strip().lower(), str(s).strip().lower())


def _query_source_and_keys(q) -> tuple[str, set]:
    """Extract (source_module, set_of_kwarg_keys) from a query entry that may be
    a dict ({"source":..., "kwargs":{...}}) or a string ("src.fn(k1=.., k2=..)")."""
    if isinstance(q, str):
        src = q.split("(")[0].split(".")[0].strip()
        keys = set(re.findall(r"(\w+)\s*=", q))
        return src, keys
    if isinstance(q, dict):
        src = (q.get("source") or "").split(".")[0]
        keys = set((q.get("kwargs") or {}).keys())
        return src, keys
    return "", set()


if __name__ == "__main__":
    print(dispatch_block())
    print("\n\n# feature vocabulary:", len(feature_vocabulary()),
          "| menu items:", len(_ipo_menu()))
