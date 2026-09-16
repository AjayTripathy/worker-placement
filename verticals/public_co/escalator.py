"""
LLM escalation pass for deterministic-scored claims.

The deterministic_scorer makes mechanical severity calls and flags
`escalation_needed=true` on cases where the data exists but a stronger
severity *might* apply (elevated bank-partner credit metrics; PASS-by-existence
on a quantitative claim that needs fact-checking). This module:

1. Gathers all escalation candidates across a cohort into one batched JSON
   payload + one focused prompt.
2. Hands that payload to a single LLM agent — much smaller workload than
   the per-ticker scorer subagents that kept stalling at the framework's
   600s watchdog.
3. Parses the agent's verdicts and patches the corresponding scores.json
   files in place.

The escalator can only *upgrade* severity, never downgrade. The deterministic
pass's PASS/MODERATE remains the floor.

Usage:
    # Print the prompt that would be sent (dry run)
    python3 -m verticals.public_co.escalator fintech_cohort --dry-run

    # Apply decisions from a JSON file the LLM agent wrote
    python3 -m verticals.public_co.escalator fintech_cohort --apply DECISIONS_PATH
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"

ESCALATION_RUBRIC = """\
You are reviewing a small set of claims that the deterministic Phase-2 scorer
flagged as `escalation_needed=true`. Each was given a first-pass severity (PASS
or MODERATE) but the underlying data may warrant a stronger downgrade.

Rules:
1. You may UPGRADE severity (PASS → MODERATE/SEVERE/RED_FLAG), never DOWNGRADE.
2. UPGRADE thresholds (apply conservatively):
   - PASS → MODERATE_UNDERDELIVERY: claim's narrative tone diverges materially
     from the M-side numbers (e.g. filing says "high-quality book" but the
     bank partner is at >5% charge-off / >10% nonaccrual). Or quantitative
     claim ($, %, count) doesn't match what filings actually show.
   - PASS → SEVERE_UNDERDELIVERY: claim is materially overstated; filing
     emphasizes a metric the M-side flatly contradicts.
   - PASS → RED_FLAG_NEGATIVE: hard contradiction. Counterparty disclosure
     or registry directly contradicts the claim.
3. If the existing severity already captures the worst case, return the same
   severity with rationale="confirmed".
4. Output a single JSON object: {"reviews": [{"claim_id": ..., "final_severity": ..., "rationale": ...}, ...]}.
   No prose outside the JSON.
"""


def gather_escalation_payload(cohort_module: str) -> dict[str, Any]:
    """Build the batched payload of escalation candidates for one cohort."""
    m = importlib.import_module(cohort_module)
    tickers = [c.ticker for c in m.COHORT]
    items: list[dict] = []
    for tk in tickers:
        sp = LOCAL / f"{tk}.scores.json"
        pp = LOCAL / f"{tk}.plan.json"
        qp = LOCAL / f"{tk}.queries.json"
        if not (sp.exists() and pp.exists() and qp.exists()):
            continue
        scores = json.loads(sp.read_text())
        plan   = json.loads(pp.read_text())
        qry    = json.loads(qp.read_text())
        plan_by_id = {c["claim_id"]: c for c in plan.get("claims", [])}
        for sc in scores.get("scores", []):
            if not sc.get("escalation_needed"):
                continue
            cid = sc["claim_id"]
            claim = plan_by_id.get(cid, {})
            qres = (qry.get("results", {}).get(cid) or [{}])[0]
            items.append({
                "ticker":            tk,
                "claim_id":          cid,
                "claim_text":        claim.get("claim_text", ""),
                "source_quote":      claim.get("source_quote", ""),
                "category":          claim.get("category", ""),
                "current_severity":  sc.get("severity"),
                "M_check":           sc.get("M_check"),
                "M_value":           sc.get("M_value"),
                "interpretation":    sc.get("interpretation"),
                "raw_M_result":      qres.get("result"),
            })
    return {
        "cohort":     cohort_module,
        "cutoff":     getattr(m, "CUTOFF", None),
        "n_items":    len(items),
        "candidates": items,
    }


def render_prompt(payload: dict[str, Any]) -> str:
    return (
        ESCALATION_RUBRIC
        + "\n== ESCALATION CANDIDATES ==\n"
        + json.dumps(payload, indent=2, default=str)
        + "\n\n== OUTPUT ==\nReturn ONLY the JSON object specified above.\n"
    )


def apply_decisions(decisions_path: Path) -> dict[str, int]:
    """Read a JSON file of LLM decisions and patch each ticker's scores.json."""
    data = json.loads(Path(decisions_path).read_text())
    reviews = data.get("reviews", [])
    by_cid: dict[str, dict] = {r["claim_id"]: r for r in reviews}
    counts = {"upgraded": 0, "confirmed": 0, "skipped": 0}

    # Group claim_ids by ticker (claim_id format is "<TK>-N")
    by_ticker: dict[str, list[str]] = {}
    for cid in by_cid:
        tk = cid.split("-")[0]
        by_ticker.setdefault(tk, []).append(cid)

    for tk, cids in by_ticker.items():
        sp = LOCAL / f"{tk}.scores.json"
        if not sp.exists():
            counts["skipped"] += len(cids)
            continue
        scores = json.loads(sp.read_text())
        dirty = False
        for sc in scores.get("scores", []):
            cid = sc.get("claim_id")
            r = by_cid.get(cid)
            if not r:
                continue
            new_sev = r.get("final_severity")
            rat     = r.get("rationale", "")
            if not new_sev:
                continue
            if new_sev == sc.get("severity"):
                sc["escalation_outcome"] = "confirmed"
                counts["confirmed"] += 1
            else:
                # Only allow upgrades.
                ORDER = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY",
                         "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]
                cur_i = ORDER.index(sc["severity"]) if sc["severity"] in ORDER else -1
                new_i = ORDER.index(new_sev) if new_sev in ORDER else -1
                # UNVERIFIABLE is its own thing (last in ORDER) — only upgrade
                # if going from PASS/MODERATE *down* to a worse severity in the
                # underdelivery direction (so cur != UNVERIFIABLE and new < UNVERIFIABLE).
                is_upgrade = (
                    sc["severity"] != "UNVERIFIABLE"
                    and new_sev != "UNVERIFIABLE"
                    and new_i > cur_i
                )
                if is_upgrade:
                    sc["original_severity"] = sc["severity"]
                    sc["severity"] = new_sev
                    sc["interpretation"] = (sc.get("interpretation") or "") + f"  [ESCALATED → {new_sev}: {rat}]"
                    sc["escalation_outcome"] = "upgraded"
                    counts["upgraded"] += 1
                else:
                    sc["escalation_outcome"] = "downgrade_rejected"
                    counts["skipped"] += 1
            sc["escalation_rationale"] = rat
            dirty = True
        if dirty:
            sp.write_text(json.dumps(scores, indent=2, default=str))

    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cohort_module", help="e.g. fintech_cohort (resolved as verticals.public_co.<cohort_module>)")
    ap.add_argument("--dry-run", action="store_true", help="Print the prompt that would be sent; exit.")
    ap.add_argument("--apply", help="Apply decisions from this JSON file.")
    ap.add_argument("--out-prompt", help="Write the rendered prompt to this path (for handing to an agent).")
    args = ap.parse_args()

    if args.apply:
        counts = apply_decisions(Path(args.apply))
        print(f"applied: {counts}")
        return

    cohort_mod = f"verticals.public_co.{args.cohort_module}" \
                 if not args.cohort_module.startswith("verticals.") else args.cohort_module
    payload = gather_escalation_payload(cohort_mod)
    prompt = render_prompt(payload)
    if args.out_prompt:
        Path(args.out_prompt).write_text(prompt)
        print(f"wrote prompt to {args.out_prompt} ({len(prompt)} chars, {payload['n_items']} candidates)")
        return
    if args.dry_run:
        print(prompt)
        return
    print(f"escalation candidates: {payload['n_items']}")
    for c in payload["candidates"]:
        print(f"  {c['ticker']}/{c['claim_id']:8} [{c['current_severity']:30}] {c['M_value'][:80]}")


if __name__ == "__main__":
    main()
