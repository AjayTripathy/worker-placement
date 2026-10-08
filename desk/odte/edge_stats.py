"""Session-level descriptive inference; never selects an arm or routes orders."""
from __future__ import annotations

import math
import random
from statistics import mean


def paired_interval(values, *, family=1, draws=4000, block=5, minimum=20):
    """Circular moving-block bootstrap of ordered daily paired differences.

    Bonferroni adjusts percentile levels for a declared comparison family.
    This is approximate inference, not a guarantee under regime change or rare
    tails. One observation is a session, never a combination within a session.
    """
    if family < 1 or draws < 1 or block < 1:
        raise ValueError("Invalid bootstrap configuration")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise ValueError("Only finite, resolved daily differences are admissible")
    n = len(values)
    result = {"sessions": n, "mean_usd": mean(values) if n else None,
              "interval_usd": None, "family_size": family, "family_confidence": .95,
              "block_sessions": block, "bootstrap_draws": draws,
              "status": "insufficient_sessions" if n < minimum else "approximate_descriptive_interval"}
    if n < minimum:
        return result
    rng = random.Random(73421)
    samples = []
    for _ in range(draws):
        indexes = []
        while len(indexes) < n:
            start = rng.randrange(n)
            indexes.extend((start + offset) % n for offset in range(block))
        samples.append(mean(values[i] for i in indexes[:n]))
    samples.sort()
    alpha = .05 / family
    result["interval_usd"] = [samples[int((draws-1)*alpha/2)], samples[int((draws-1)*(1-alpha/2))]]
    return result


def participation_control(gross_less_trade_cost, take, research_cost):
    """Uniform k-of-n on the SAME resolved calendar; costs are not optimized."""
    if len(gross_less_trade_cost) != len(take):
        raise ValueError("Participation control calendars differ")
    n = len(take); k = sum(take)
    expected = k / n * sum(gross_less_trade_cost) if n else None
    selected = sum(p for p, included in zip(gross_less_trade_cost, take) if included) - n*research_cost
    return {"sessions": n, "trades": k, "strategy_net_usd": selected,
            "uniform_expected_net_usd": expected,
            "increment_after_research_usd": selected-expected if n else None,
            "note": "Uniform subset control pays trading costs but no research cost; descriptive, not a fitted strategy."}


def arm_audit(root):
    """Read sealed artifacts only. Never finalize or rewrite the running trial."""
    from pathlib import Path
    from desk.odte import arms as A, doctrine as D
    root = Path(root); m = A.protocol(root)
    if not m:
        raise ValueError("Arm experiment is not registered")
    ds = [A.checked(p) for p in sorted((root/"decisions").glob("*.json"))]
    outcomes = {r["date"]: r for p in (root/"outcomes").glob("*.json") if (r := A.checked(p))}
    for d in ds:
        r = outcomes.get(d["date"])
        if d["protocol"] != m["protocol"] or r and (r["decision_id"] != d["id"] or r["protocol"] != m["protocol"]):
            raise ValueError("Arm audit lineage mismatch")
    result = {}
    for name in m["arms"]:
        pairs, known, unresolved, unavailable = [], [], [], 0
        for d in ds:
            row = outcomes.get(d["date"], {}); arm = d["arms"][name]
            net = row.get("arms", {}).get(name, {}).get("net_pnl_usd")
            base = row.get("arms", {}).get("T3", {}).get("net_pnl_usd")
            if net is not None:
                known.append((net, arm["decision"] == "take"))
                if base is not None:
                    pairs.append(net-base)
            elif arm["decision"] == "take":
                unresolved.append((d["candidate"], arm["research_cost_usd"]))
            elif arm["decision"] == "unavailable":
                unavailable += 1
        subtotal = sum(n for n, _ in known)
        result[name] = {
            "vs_t3": paired_interval(pairs, family=len(m["arms"])-1) if name != "T3" else None,
            "resolved_sessions": len(known), "unresolved_takes": len(unresolved), "unavailable_sessions": unavailable,
            "resolved_net_subtotal_usd": subtotal,
            "cost_sensitivity_resolved_subtotal_usd": {
                str(cost): sum(net-(cost-m["trade_cost_usd"]) * take for net, take in known)
                for cost in (m["trade_cost_usd"], 12., 20.)},
            "unresolved_stress_totals_usd": {
                "lose_entry_max_risk": subtotal + sum(-c["max_loss_usd"]-m["trade_cost_usd"]-fee for c, fee in unresolved),
                "keep_entry_credit": subtotal + sum(c["credit"]*D.MULTIPLIER*D.CONTRACTS-m["trade_cost_usd"]-fee for c, fee in unresolved)},
        }
    return {"source_protocol": m["protocol"], "decision_sessions": len(ds), "arms": result,
            "limitations": ["Intervals are approximate and do not validate the best arm or a rare-tail distribution.",
                "Missing sessions can be informative; stress totals are scenarios, not guaranteed execution bounds.",
                "Cost scenarios hold decisions fixed and include only resolved paper trades.",
                "Source-arm charges omit failed news attempts; the matched trial reports all its own attempt costs.",
                "No comparison to institutional or retail account returns, depth, capacity or actual fills is present."]}
