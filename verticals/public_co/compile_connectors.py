"""
Compile phase: aggregate proposed connectors across all tickers' plan.json
files, dedupe, prioritize by reference count, emit a queue for promotion.

This is the central, deterministic step between Phase 1 (Planner subagents)
and Phase 2 (Scorer subagents) in the Signal OS 3-phase pipeline.

Usage:
    python3 -m verticals.public_co.compile_connectors

Outputs:
    data/_connector_queue/queue.json   — structured queue for tooling
    data/_connector_queue/queue.md     — human-readable prioritized list
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_connector_queue"


def load_plans() -> list[dict]:
    """Walk data/_local/*.plan.json and return all plans."""
    plans = []
    for p in sorted(LOCAL.glob("*.plan.json")):
        try:
            plans.append(json.loads(p.read_text()))
        except json.JSONDecodeError:
            continue
    return plans


def aggregate_proposals(plans: list[dict]) -> dict[str, dict]:
    """Group proposed connectors by name; return dedup-aggregated dict."""
    agg: dict[str, dict] = {}
    for plan in plans:
        tk = plan.get("ticker", "?")
        for c in plan.get("claims", []):
            if c.get("m_source_status") != "PROPOSED":
                continue
            prop = c.get("proposed_connector") or {}
            name = prop.get("name")
            if not name:
                continue
            if name not in agg:
                agg[name] = {
                    "name":             name,
                    "description":      prop.get("description", ""),
                    "endpoint":         prop.get("endpoint", ""),
                    "access_pattern":   prop.get("access_pattern", ""),
                    "auth_required":    prop.get("auth_required", False),
                    "sample_invocation":prop.get("sample_invocation", ""),
                    "estimated_cost":   prop.get("estimated_cost", "?"),
                    "completeness":     prop.get("completeness", "?"),
                    "referent_type":    prop.get("referent_type", ""),
                    "attribute":        prop.get("attribute", ""),
                    "rationales":       [],
                    "tickers":          [],
                    "claim_count":      0,
                }
            entry = agg[name]
            entry["rationales"].append({
                "ticker": tk,
                "claim_id": c.get("claim_id", "?"),
                "category": c.get("category", ""),
                "rationale": prop.get("rationale", ""),
            })
            entry["claim_count"] += 1
            if tk not in entry["tickers"]:
                entry["tickers"].append(tk)
    return agg


def prioritize(agg: dict[str, dict]) -> list[dict]:
    """Sort proposals: free + low-auth + multi-ticker + many-claims first."""
    def score(p):
        s = p["claim_count"] * 2 + len(p["tickers"]) * 3
        if p.get("estimated_cost") == "free":
            s += 5
        if not p.get("auth_required"):
            s += 2
        if p.get("access_pattern") in {"csv_download", "api", "file_download"}:
            s += 3
        return -s
    return sorted(agg.values(), key=score)


def render_md(prioritized: list[dict], total_plans: int) -> str:
    lines: list[str] = []
    w = lines.append
    w("# Signal OS — Connector Queue (compile-phase output)\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z from {total_plans} plan.json files._\n")
    w(f"**Total unique proposed connectors:** {len(prioritized)}\n")
    w("")
    w("Connectors are ranked by **reference count × cohort breadth × buildability** (free + no-auth + structured-API connectors first). Top-of-queue connectors are the cheapest path to unlocking adjudication for the most claims.")
    w("")
    if not prioritized:
        w("_No proposed connectors. Either all claims mapped to the existing catalog, or no plan.json files have been produced yet._")
        return "\n".join(lines)

    w("## Priority queue\n")
    for i, p in enumerate(prioritized, 1):
        w(f"### {i}. `{p['name']}` — {p['description']}")
        w(f"- **Referenced by:** {p['claim_count']} claim(s) across {len(p['tickers'])} ticker(s): {', '.join(p['tickers'])}")
        w(f"- **Endpoint:** `{p['endpoint']}`")
        w(f"- **Access:** {p['access_pattern']}{'  (auth required)' if p['auth_required'] else '  (no auth)'}")
        w(f"- **Cost:** {p['estimated_cost']}  |  **Completeness:** {p['completeness']}")
        w(f"- **Referent / Attribute:** {p['referent_type']} / {p['attribute']}")
        w(f"- **Sample invocation:** `{p['sample_invocation'][:240]}`")
        w(f"- **Rationales (per claim):**")
        for r in p["rationales"][:5]:
            w(f"  - `{r['ticker']}` / `{r['claim_id']}` ({r['category']}): {r['rationale'][:200]}")
        if len(p["rationales"]) > 5:
            w(f"  - ... and {len(p['rationales']) - 5} more")
        w("")
    return "\n".join(lines)


def main():
    plans = load_plans()
    agg = aggregate_proposals(plans)
    prioritized = prioritize(agg)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "queue.json").write_text(json.dumps(prioritized, indent=2, default=str))
    (OUT / "queue.md").write_text(render_md(prioritized, total_plans=len(plans)))

    print(f"Compiled {len(plans)} plan.json files")
    print(f"Proposed connectors: {len(prioritized)}")
    print(f"Wrote {OUT / 'queue.md'}")
    print(f"Wrote {OUT / 'queue.json'}")
    print()
    for i, p in enumerate(prioritized[:10], 1):
        print(f"  {i}. {p['name']:<50}  {p['claim_count']} claim(s) / "
              f"{len(p['tickers'])} ticker(s)  ({p['access_pattern']}, {p['estimated_cost']})")


if __name__ == "__main__":
    main()
