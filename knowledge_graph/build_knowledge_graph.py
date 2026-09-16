"""Build the cross-vertical Signal OS knowledge graph.

Reads:
- knowledge_graph/masking_mechanisms.json (this dir)
- knowledge_graph/signal_channels.json (this dir)
- verticals/*/detectors/*.py (every vertical's detector library)

Produces:
- knowledge_graph/knowledge_graph.json — composed graph with nodes (mechanism, channel,
  detector, asset_class) and edges (reads, applies_to, masks, has)

This is the spine of Signal OS's microstructure-knowledge product. Every future
vertical scoping adds nodes/edges to the catalogs in this directory rather than
generating standalone prose findings.

Re-run after any vertical detector library change to refresh the graph.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

HERE = Path(__file__).parent  # signalos/knowledge_graph/
REPO_ROOT = HERE.parent
VERTICALS_DIR = REPO_ROOT / "verticals"


def load_masking_mechanisms():
    return json.loads((HERE / "masking_mechanisms.json").read_text())


def load_signal_channels():
    return json.loads((HERE / "signal_channels.json").read_text())


def extract_detector_inventory():
    """Walk every vertical's detectors/ dir and extract per-detector metadata.

    Each detector is tagged with its vertical (from path), name, summary,
    primary source, asset class, and category.
    """
    detectors = []
    # Each vertical may use different conventions. Known ones:
    #   detectors/  — muni_credit (canonical)
    #   rules/      — rent_stabilization, art_donation_fraud
    # Future: extend to handle f_library.py (buyside_dd), r_f_m_taxonomy.py (public_co), etc.
    # dir name -> kind. Originally only detectors/rules; EXTENDED to also index the
    # connectors (signal-source library), m_sources (e.g. pentagon_jbook — the jbook
    # detector), and property-tax jurisdictions that the graph previously dropped on the
    # floor (they live outside detectors/, so the dashboard never saw them).
    DIR_KIND = {"detectors": "detector", "rules": "detector", "connectors": "connector",
                "m_sources": "m_source", "jurisdictions": "jurisdiction"}
    SKIP = {"__init__.py", "union_runner.py", "honesty_decomposed.py", "base.py", "registry.py"}
    for vertical_dir in sorted(VERTICALS_DIR.iterdir()):
        if not vertical_dir.is_dir():
            continue
        vertical = vertical_dir.name
        all_files = []
        for dname, kind in DIR_KIND.items():
            dpath = vertical_dir / dname
            if dpath.exists():
                for f in sorted(dpath.glob("*.py")):
                    all_files.append((f, kind))
        if not all_files:
            continue
        for f, dirkind in all_files:
            if f.name in SKIP or f.name.startswith("_"):
                continue
            src = f.read_text()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            docstring = ast.get_docstring(tree) or ""
            first_line = docstring.split("\n")[0].strip() if docstring else ""

            primary_source_match = re.search(
                r"(?:Public data|Primary data source|Data source)s?[:\s\-]+(.+?)(?:\n\n|\n[A-Z]|$)",
                docstring, re.DOTALL)
            primary_source = primary_source_match.group(1).strip()[:200] if primary_source_match else "(not specified)"

            asset_class = f"{vertical}_general"
            name = f.stem.lower()
            if name.startswith("nh_") or "nursing home" in docstring.lower() or "snf" in docstring.lower():
                asset_class = "ca_nh_muni"
            elif name.startswith("ccrc_") or "ccrc" in docstring.lower() or "life plan community" in docstring.lower():
                asset_class = "ca_ccrc_muni"
            elif name in ("cms_readmissions", "hhs_oig_cia", "hcai_seismic", "doj_fca"):
                asset_class = "healthcare_muni"
            elif name in ("value_to_lien_collapse", "delinquency_spike", "reserve_fund_drawn",
                          "reserve_fund_burndown", "foreclosure_active", "issuer_administration_concern",
                          "buildout_stalled", "top_taxpayer_concentration", "coverage_ratio_thin",
                          "developer_bankruptcy", "nod_recorder_filing", "developer_corp_credit"):
                asset_class = "ca_cfd_muni"
            elif name in ("auditor_change", "pension_funded_ratio", "late_filing", "payor_concentration",
                          "exec_turnover", "going_concern") and vertical == "muni_credit":
                asset_class = "muni_general"
            elif name == "clinical_trial_referral_quality":
                asset_class = "diagnostics_biotech_dd"
            elif name == "clinicaltrials_lookup":
                asset_class = "diagnostics_biotech_dd"
            elif name == "competitor_trial_omission":
                asset_class = "diagnostics_biotech_dd"
            elif name in ("dual_class_voting_concentration",
                          "related_party_transaction_velocity",
                          "comparable_public_company_anchor",
                          "upc_tra_value_extraction",
                          "jobs_act_disclosure_exemption_audit",
                          "pe_dividend_recap_pre_ipo",
                          "common_control_merger_accounting",
                          "lockup_expiration_calendar",
                          "underwriter_archetype_risk",
                          "chinese_smallcap_ramp_dump_archetype"):
                asset_class = "corporate_ipo_dd"

            if name in ("nod_recorder_filing", "developer_corp_credit",
                        "clinical_trial_referral_quality", "clinicaltrials_lookup",
                        "competitor_trial_omission",
                        "dual_class_voting_concentration",
                        "related_party_transaction_velocity",
                        "comparable_public_company_anchor",
                        "upc_tra_value_extraction",
                        "jobs_act_disclosure_exemption_audit",
                        "pe_dividend_recap_pre_ipo",
                        "common_control_merger_accounting",
                        "lockup_expiration_calendar",
                        "underwriter_archetype_risk",
                        "chinese_smallcap_ramp_dump_archetype"):
                category = "diligence_replication"
            elif name in ("value_to_lien_collapse", "delinquency_spike", "reserve_fund_drawn",
                          "foreclosure_active", "nh_cms_star_rating", "nh_special_focus_facility",
                          "nh_civil_monetary_penalty", "developer_bankruptcy", "doj_fca",
                          "hhs_oig_cia", "cms_readmissions"):
                category = "classification_distress"
            elif name in ("reserve_fund_burndown", "auditor_change", "exec_turnover", "going_concern",
                          "late_filing", "issuer_administration_concern", "buildout_stalled",
                          "ccrc_occupancy", "ccrc_days_cash", "pension_funded_ratio",
                          "payor_concentration", "top_taxpayer_concentration", "coverage_ratio_thin",
                          "hcai_seismic"):
                category = "predictive_deterioration"
            else:
                category = "other"

            # connectors / m_sources / jurisdictions carry their dir-kind as the category
            if dirkind != "detector":
                category = dirkind
                if asset_class == f"{vertical}_general":
                    asset_class = f"{vertical}_{dirkind}"

            detectors.append({
                "vertical": vertical,
                "name": f.stem,
                "file": str(f.relative_to(REPO_ROOT)),
                "kind": dirkind,
                "summary": first_line,
                "primary_source": primary_source.replace("\n", " ").strip(),
                "asset_class": asset_class,
                "category": category,
            })
    return detectors


def map_detector_to_channels(detectors, channels):
    """Best-effort: for each detector, identify which signal channel it reads,
    using string matching between detector primary_source and channel name/publisher.
    """
    # Build channel lookup: lowercase tokens -> channel short_name
    channel_tokens = {}
    for ch in channels:
        short = ch.get("short_name")
        if not short:
            continue
        tokens = set()
        tokens.add(short.lower())
        for w in re.findall(r"[A-Za-z][A-Za-z0-9_]+", ch.get("name") or ""):
            if len(w) >= 4:
                tokens.add(w.lower())
        for w in re.findall(r"[A-Za-z][A-Za-z0-9_]+", ch.get("publisher") or ""):
            if len(w) >= 4:
                tokens.add(w.lower())
        channel_tokens[short] = tokens

    # For each detector, see which channels match
    for det in detectors:
        text = (det["primary_source"] + " " + det["summary"]).lower()
        matched = []
        for short, tokens in channel_tokens.items():
            for tok in tokens:
                if tok in text and len(tok) >= 5:
                    matched.append(short)
                    break
        det["likely_signal_channels"] = sorted(set(matched))
    return detectors


def asset_class_index(mechanisms, channels, detectors):
    """For each asset class touched anywhere, list mechanisms / channels / detectors."""
    ac = {}
    for mech in mechanisms:
        for cls in mech.get("asset_classes", []):
            ac.setdefault(cls, {"mechanisms": [], "channels": [], "detectors": []})
            ac[cls]["mechanisms"].append(mech.get("short_name"))
    for ch in channels:
        for cls in ch.get("asset_classes", []):
            ac.setdefault(cls, {"mechanisms": [], "channels": [], "detectors": []})
            ac[cls]["channels"].append(ch.get("short_name"))
    for det in detectors:
        cls = det.get("asset_class")
        if cls:
            ac.setdefault(cls, {"mechanisms": [], "channels": [], "detectors": []})
            ac[cls]["detectors"].append(det.get("name"))
    return ac


def main():
    mech_raw = load_masking_mechanisms()
    chan_raw = load_signal_channels()
    detectors = extract_detector_inventory()
    detectors = map_detector_to_channels(detectors,
                                          chan_raw.get("channels") if isinstance(chan_raw.get("channels"), list)
                                          else list(chan_raw.get("channels", {}).values()))

    mechanisms = mech_raw.get("mechanisms") if isinstance(mech_raw.get("mechanisms"), list) else list(mech_raw.get("mechanisms", {}).values())
    channels = chan_raw.get("channels") if isinstance(chan_raw.get("channels"), list) else list(chan_raw.get("channels", {}).values())

    ac_idx = asset_class_index(mechanisms, channels, detectors)

    # Count detectors per vertical
    from collections import Counter
    vertical_counts = Counter(d.get("vertical") for d in detectors)

    graph = {
        "_purpose": "Cross-vertical Signal OS knowledge graph: detectors × signal channels × masking mechanisms × asset classes",
        "_built_from": {
            "verticals_scanned": sorted(vertical_counts.keys()),
            "detector_count_per_vertical": dict(vertical_counts),
        },
        "_counts": {
            "detectors": len(detectors),
            "channels": len(channels),
            "mechanisms": len(mechanisms),
            "asset_classes": len(ac_idx),
        },
        "asset_class_index": ac_idx,
        "detector_inventory": detectors,
        "mechanism_inventory_count": len(mechanisms),
        "channel_inventory_count": len(channels),
        "cross_references": {
            "masking_mechanisms_json": "knowledge_graph/masking_mechanisms.json",
            "signal_channels_json": "knowledge_graph/signal_channels.json",
        },
    }

    # Export each module's APPLIES_TO declaration as a static dispatch_index.
    # Lets external tooling (orchestrators, validators) query the graph for
    # "what applies to issuer profile X?" without re-walking the file tree.
    import importlib, sys
    sys.path.insert(0, str(REPO_ROOT))
    dispatch_index, seen = [], set()
    for d in detectors:                       # detectors now includes connectors + m_sources
        mod_path = d["file"].replace("/", ".").rsplit(".py", 1)[0]
        try:
            mod = importlib.import_module(mod_path)
        except Exception:
            continue                          # missing dep etc. — just no dispatch badge, don't pollute
        a = getattr(mod, "APPLIES_TO", None)
        if a is not None and d["name"] not in seen:
            seen.add(d["name"])
            dispatch_index.append({"name": d["name"], "vertical": d["vertical"], "kind": d.get("kind"),
                                   "module": mod_path, "applies_to": a})
    graph["dispatch_index"] = dispatch_index
    graph["_counts"]["dispatch_indexed"] = len(dispatch_index)

    out_path = HERE / "knowledge_graph.json"
    out_path.write_text(json.dumps(graph, indent=2, default=str))
    print(f"Wrote {out_path}")
    print(f"  Detectors: {len(detectors)}")
    print(f"  Channels: {len(channels)}")
    print(f"  Mechanisms: {len(mechanisms)}")
    print(f"  Asset classes: {len(ac_idx)}")
    print(f"  Dispatch-indexed modules (with APPLIES_TO): {len(dispatch_index)}")
    return graph, mechanisms, channels, detectors, ac_idx


if __name__ == "__main__":
    main()
