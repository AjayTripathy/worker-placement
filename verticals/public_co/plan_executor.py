"""
Non-LLM execution of MAPPED queries from a TickerPlan.

Phase-2 (Scorer) subagents were stalling because they ran one Bash
process per M-source query. The query execution itself is fully
deterministic — there's no LLM judgment needed to dispatch a query
that's already been mapped. Splitting execution from scoring lets
the LLM focus on the *judgmental* part (severity classification)
against pre-computed M-side results.

Usage:
    python3 -m verticals.public_co.plan_executor TICKER

Reads:
    data/_local/<TK>.plan.json

Writes:
    data/_local/<TK>.queries.json     -- {claim_id: [result_dicts]}

The scorer subagent then reads plan.json + queries.json and emits
scores.json without running any M-source queries itself.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from .m_source_catalog import CATALOG, call

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"


def execute_plan(ticker: str, *, throttle_sec: float = 1.0, data_dir: Path | None = None) -> dict:
    """Run all MAPPED queries from <TK>.plan.json. Skip PROPOSED / NONE.

    data_dir lets backtest runs read/write into a separate directory
    (default: data/_local/). Used by backtest_b1.py to keep historical
    runs from clobbering the live plans/queries/scores.
    """
    base = Path(data_dir) if data_dir else LOCAL
    plan_path = base / f"{ticker}.plan.json"
    if not plan_path.exists():
        return {"error": f"plan not found: {plan_path}"}
    plan = json.loads(plan_path.read_text())

    results: dict[str, list[dict]] = {}
    summary: dict[str, dict] = {}
    creative_extensions_log: list[dict] = []
    n_mapped = n_proposed = n_none = n_skipped_unknown = 0
    n_creative = 0

    for claim in plan.get("claims", []):
        cid = claim["claim_id"]
        status = claim.get("m_source_status", "NONE")

        # Always collect creative_extensions regardless of MAPPED/PROPOSED/NONE.
        # These are non-auto-executed proposals from the planner that get
        # logged for promotion review. Domain + claim_type_taxonomy fields
        # (from r_f_m_taxonomy) ride along for context.
        for ext in (claim.get("creative_extensions") or []):
            creative_extensions_log.append({
                "claim_id":   cid,
                "claim_text": claim.get("claim_text", "")[:200],
                "domain":     claim.get("domain"),
                "claim_type_taxonomy": claim.get("claim_type_taxonomy"),
                **ext,
            })
            n_creative += 1

        if status == "MAPPED":
            n_mapped += 1
            sid    = claim.get("source_id")
            params = dict(claim.get("source_params") or {})
            if sid not in CATALOG:
                results[cid] = [{
                    "label":   "catalog_miss",
                    "error":   f"source_id not in catalog: {sid}",
                    "params":  params,
                }]
                n_skipped_unknown += 1
                continue
            # Auto-inject plan-level cutoff_date for connectors that accept
            # it. Prevents hindsight leaks from snapshot connectors (OSHA,
            # DOL H-1B LCA, etc.) when the planner didn't explicitly pass it.
            plan_cutoff = plan.get("cutoff")
            if plan_cutoff and "cutoff_date" not in params:
                import inspect
                fn = CATALOG[sid].get("fn")
                if fn is not None:
                    try:
                        sig = inspect.signature(fn)
                        if "cutoff_date" in sig.parameters:
                            params["cutoff_date"] = plan_cutoff
                    except (TypeError, ValueError):
                        pass
            r = call(sid, params)
            results[cid] = [{
                "label":  sid,
                "params": params,
                "result": r,
            }]
            summary[cid] = {"status": "MAPPED", "source_id": sid, "ok": "error" not in (r or {})}
            time.sleep(throttle_sec)

        elif status == "PROPOSED":
            n_proposed += 1
            prop = claim.get("proposed_connector") or {}
            prop_name = prop.get("name", "")
            # If the proposed connector got promoted to the catalog by the
            # compile phase, run it. Otherwise mark for UNVERIFIABLE scoring.
            if prop_name in CATALOG:
                # Run with sample params guessed from the proposal
                r = call(prop_name, {})
                results[cid] = [{
                    "label":  prop_name,
                    "params": {},
                    "result": r,
                    "note":   "proposed_connector_promoted_post_phase1",
                }]
                summary[cid] = {"status": "PROPOSED_PROMOTED", "source_id": prop_name}
                time.sleep(throttle_sec)
            else:
                results[cid] = [{
                    "label":     "proposed_not_promoted",
                    "proposed":  prop_name,
                    "rationale": prop.get("rationale", ""),
                    "endpoint":  prop.get("endpoint", ""),
                    "note":      "score UNVERIFIABLE; connector not yet built",
                }]
                summary[cid] = {"status": "PROPOSED_PENDING", "name": prop_name}

        else:  # NONE
            n_none += 1
            results[cid] = [{
                "label": "structural_none",
                "note":  "claim is not externally adjudicatable; score UNVERIFIABLE",
            }]
            summary[cid] = {"status": "NONE"}

    out = {
        "ticker":   ticker,
        "cutoff":   plan.get("cutoff"),
        "filing":   plan.get("filing"),
        "summary":  summary,
        "results":  results,
        "creative_extensions": creative_extensions_log,
        "stats": {
            "mapped":            n_mapped,
            "proposed":          n_proposed,
            "none":              n_none,
            "catalog_miss":      n_skipped_unknown,
            "creative_extensions": n_creative,
        },
    }

    out_path = base / f"{ticker}.queries.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))

    # Aggregated proposals log for cross-ticker promotion review.
    if creative_extensions_log:
        proposals_dir = base / "_proposed_sources"
        proposals_dir.mkdir(parents=True, exist_ok=True)
        prop_path = proposals_dir / f"{ticker}.creative_extensions.json"
        prop_path.write_text(json.dumps({
            "ticker":   ticker,
            "cutoff":   plan.get("cutoff"),
            "filing":   plan.get("filing"),
            "extensions": creative_extensions_log,
        }, indent=2, default=str))
    return out


def main():
    if len(sys.argv) < 2:
        print("usage: python3 -m verticals.public_co.plan_executor TICKER", file=sys.stderr)
        sys.exit(2)
    ticker = sys.argv[1].upper()
    out = execute_plan(ticker)
    if "error" in out:
        print(out["error"], file=sys.stderr)
        sys.exit(1)
    print(f"{ticker}: wrote {LOCAL / f'{ticker}.queries.json'}")
    print(f"  stats: {out['stats']}")


if __name__ == "__main__":
    main()
