"""Frozen, full-information paper arms and an exploratory allocation policy.

All arms take or skip the SAME first T3 candidate. No broker or order interface.
Decisions, weights and a sampled arm are sealed before any outcome is observed.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import math
from pathlib import Path
import random
import secrets
from statistics import mean

from desk.odte import doctrine as D, text_overlay as E, volatility as V
from desk.odte.storage import atomic_json

FACTORS = {
    "news": "Premarket news: stop <30%, severe-loss <10%",
    "volatility": "ATM IV / trailing 15-minute realized volatility ≥1.10",
    "trend": "15-minute path efficiency ≤0.60",
    "execution": "Selected-leg quoted spreads / entry credit ≤0.50",
}
# Stable numbering preserves T3 and the existing T4 text-only experiment.
COMBINATIONS = [(), ("news",), ("volatility",), ("trend",), ("execution",),
    ("volatility", "trend"), ("volatility", "execution"), ("trend", "execution"),
    ("volatility", "trend", "execution"), ("news", "volatility"), ("news", "trend"),
    ("news", "execution"), ("news", "volatility", "trend"),
    ("news", "volatility", "execution"), ("news", "trend", "execution"),
    ("news", "volatility", "trend", "execution")]
ARMS = {f"T{i+3}": {"factors": list(factors), "label": "Calendar baseline" if not factors else " + ".join(factors)}
        for i, factors in enumerate(COMBINATIONS)}
ARMS["CASH"] = {"factors": [], "label": "Always cash control"}


def code_hash():
    return E.digest({n: Path(__file__).with_name(n).read_text() for n in
        ("arms.py", "volatility.py", "text_overlay.py", "forecast_worker.py", "templates.py", "shadow.py", "doctrine.py")})


def code_files():
    return {n: E.digest(Path(__file__).with_name(n).read_text()) for n in
            ("arms.py", "volatility.py", "text_overlay.py", "forecast_worker.py", "templates.py", "shadow.py", "doctrine.py")}


def initialize(root, *, start_date, forecast_root, continuation_root=None, page_path=None, now=None):
    now = now or E.utcnow()
    dt.date.fromisoformat(start_date)
    if start_date <= now.astimezone(E.ET).date().isoformat():
        raise ValueError("Register arms for a future session; never retrofit observed results")
    source = E.protocol(forecast_root)
    if not source:
        raise ValueError("A registered forecast source is required")
    continuation = E.protocol(continuation_root) if continuation_root else None
    if continuation_root and (not continuation or continuation.get("session_date") or not source.get("session_date")
                              or source["session_date"] != start_date):
        raise ValueError("Continuation requires a one-day starting source and an ongoing registered source")
    m = {"version": 1, "mode": "shadow_only", "registered_at": now.isoformat(), "start_date": start_date,
         "code_hash": code_hash(), "code_files": code_files(), "arms": copy.deepcopy(ARMS), "factors": FACTORS,
         "gates": {"iv_rv_min": 1.10, "efficiency_max": .60, "spread_credit_max": .50,
                   "stop_max": .30, "severe_max": .10},
         "trade_cost_usd": 7.20, "news_cost_usd": 1., "risk_budget_usd": 200.,
         "reward": "clip(net P&L / $200, -1, 1) minus 0.5 * max(0, -clipped return)",
         "learning_rate": 2., "exploration": .20, "warmup_sessions": 20, "context_pool_strength": 20.,
         "max_training_sessions": 60, "seed": secrets.token_hex(16),
         "forecast_root": str(Path(forecast_root).resolve()), "forecast_protocol": source["protocol"],
         "forecast_deadline_et": source["forecast_deadline_et"],
         "continuation_root": str(Path(continuation_root).resolve()) if continuation_root else None,
         "continuation_protocol": continuation["protocol"] if continuation else None,
         "continuation_after": source.get("session_date") if continuation else None,
         "page_path": str(Path(page_path).resolve()) if page_path else None,
         "live_enabled": False, "promotion_allowed": False}
    m["protocol"] = E.digest(m)
    with E.locked(root):
        E.seal(Path(root)/"manifest.json", m)
    return m


def protocol(root):
    p = Path(root)/"manifest.json"
    if not p.exists():
        return None
    m = checked(p)
    if m["code_hash"] != code_hash() or m["arms"] != ARMS:
        raise ValueError("Arm code or definitions changed; register a new experiment")
    return m


def checked(path):
    row = E.read(path)
    key = "id" if "id" in row else "protocol"
    if row[key] != E.digest({k: v for k, v in row.items() if k != key}):
        raise ValueError(f"Research record integrity failure: {Path(path).name}")
    return row


def seal(path, row):
    row = copy.deepcopy(row); row["id"] = E.digest(row)
    E.seal(path, row)
    return row


def forecast_for(m, date, entry_at):
    continued = m.get("continuation_root") and date > m["continuation_after"]
    root = m["continuation_root"] if continued else m["forecast_root"]
    expected = m["continuation_protocol"] if continued else m["forecast_protocol"]
    source = E.protocol(root)
    if not source or source["protocol"] != expected:
        raise ValueError("Frozen forecast source changed")
    if source.get("session_date") and date != source["session_date"]:
        return None
    return E.admitted_forecast(root, date, source, entry_at)


def evaluate(features, candidate, forecast, m):
    ratio = features.get("iv_to_realized_15m")
    efficiency = features.get("path_efficiency_15m")
    spread = sum(leg["ask"]-leg["bid"] for leg in candidate["legs"].values())/candidate["credit"]
    f = forecast["forecast"] if forecast else None
    gates = {
        "news": {"value": {k: f[k] for k in ("stop_probability", "severe_probability")} if f else None,
                 "pass": f["stop_probability"] < m["gates"]["stop_max"] and f["severe_probability"] < m["gates"]["severe_max"] if f else None},
        "volatility": {"value": ratio, "pass": ratio >= m["gates"]["iv_rv_min"] if V.finite(ratio) else None},
        "trend": {"value": efficiency, "pass": efficiency <= m["gates"]["efficiency_max"] if V.finite(efficiency) else None},
        "execution": {"value": spread, "pass": spread <= m["gates"]["spread_credit_max"] if V.finite(spread) else None},
    }
    result = {}
    for name, arm in m["arms"].items():
        missing = [factor for factor in arm["factors"] if gates[factor]["pass"] is None]
        failed = [factor for factor in arm["factors"] if gates[factor]["pass"] is False]
        # Missing required inputs stay unavailable even if another filter fails.
        disposition = "unavailable" if missing else "skip" if failed or name == "CASH" else "take"
        result[name] = {"decision": disposition, "missing": missing, "failed": failed,
                       "research_cost_usd": m["news_cost_usd"] if "news" in arm["factors"] and forecast else 0.}
    return gates, result


def context(features):
    ratio = features.get("iv_to_realized_15m"); efficiency = features.get("path_efficiency_15m")
    return {"volatility": "unknown" if not V.finite(ratio) else "iv_above_rv" if ratio >= 1 else "iv_below_rv",
            "path": "unknown" if not V.finite(efficiency) else "directional" if efficiency > .60 else "two_way"}


def history(root, m, before):
    out = []
    for p in sorted((Path(root)/"outcomes").glob("*.json")):
        r = checked(p)
        if r["protocol"] == m["protocol"] and r["date"] < before.astimezone(E.ET).date().isoformat() and E.timestamp(r["resolved_at"]) < before:
            d = checked(Path(root)/"decisions"/p.name)
            if r["decision_id"] != d["id"] or d["protocol"] != m["protocol"]:
                raise ValueError("Outcome/decision lineage mismatch")
            out.append((d, r))
    return out


def allocation(m, decisions, ctx, past, date):
    eligible = [name for name, d in decisions.items() if d["decision"] != "unavailable"]
    # A shared historical panel prevents different missing-data calendars from
    # looking like alpha. Every observation below is one whole session.
    complete = [(d, r) for d, r in past if all(r["arms"].get(name, {}).get("net_pnl_usd") is not None for name in eligible)]
    panel = complete[-m["max_training_sessions"]:]
    def utility(value):
        normalized = max(-1., min(1., value/m["risk_budget_usd"]))
        return normalized - .5*max(0., -normalized)
    local = [(d, r) for d, r in panel if d["context"] == ctx]
    blend = len(local)/(len(local)+m["context_pool_strength"])
    estimates = {}
    for name in eligible:
        pooled = mean(utility(r["arms"][name]["net_pnl_usd"]) for _, r in panel) if panel else 0.
        conditional = mean(utility(r["arms"][name]["net_pnl_usd"]) for _, r in local) if local else pooled
        estimates[name] = (1-blend)*pooled + blend*conditional
    warmup = len(panel) < m["warmup_sessions"]
    logits = {k: 0. if warmup else m["learning_rate"]*math.sqrt(len(panel))*v for k, v in estimates.items()}
    maximum = max(logits.values()); weights = {k: math.exp(v-maximum) for k, v in logits.items()}
    total = sum(weights.values()); n = len(eligible)
    probs = {k: (1-m["exploration"])*weights[k]/total + m["exploration"]/n for k in eligible}
    draw = random.Random(m["seed"]+m["protocol"]+date).random()
    cumulative = 0.; chosen = eligible[-1]
    for name in eligible:
        cumulative += probs[name]
        if draw < cumulative:
            chosen = name; break
    return {"algorithm": "full-information experts: exponential weights, pooled context and uniform regularization",
            "status": "uniform_warmup" if warmup else "exploratory_learning", "probabilities": probs,
            "selected_arm": chosen, "selected_probability": probs[chosen], "random_draw": draw,
            "training_sessions": len(panel), "context_sessions": len(local), "context_blend": blend,
            "warmup_remaining": max(0, m["warmup_sessions"]-len(panel)),
            "prior_sessions": len(past), "incomplete_sessions": len(past)-len(complete),
            "windowed_out_sessions": max(0, len(complete)-len(panel)),
            "missing_by_arm": {n: sum(r["arms"].get(n, {}).get("net_pnl_usd") is None for _, r in past) for n in eligible},
            "utility_estimates": estimates, "training_outcome_ids": [r["id"] for _, r in panel],
            "live_enabled": False}


def resolve_arms(decision, counterfactual, resolved_at, m):
    arms = {}
    for name, d in decision["arms"].items():
        net = None
        if d["decision"] == "skip":
            net = -d["research_cost_usd"]
        elif d["decision"] == "take" and counterfactual:
            net = counterfactual["gross_pnl_usd"] - m["trade_cost_usd"] - d["research_cost_usd"]
        arms[name] = {"decision": d["decision"], "net_pnl_usd": round(net, 2) if net is not None else None,
                      "trade_cost_usd": m["trade_cost_usd"] if d["decision"] == "take" and counterfactual else None,
                      "research_cost_usd": d["research_cost_usd"]}
    return {"date": decision["date"], "protocol": m["protocol"], "decision_id": decision["id"],
            "resolved_at": resolved_at.isoformat(), "counterfactual": counterfactual, "arms": arms,
            "selected_arm": decision["allocation"]["selected_arm"]}


def observe(root, st, snap, calendar, *, now=None):
    m = protocol(root)
    if not m:
        return
    stamp = E.timestamp(snap["ts"]).astimezone(E.ET); date = stamp.date().isoformat()
    if date < m["start_date"]:
        return
    now = now or E.utcnow()
    if E.timestamp(m["registered_at"]) >= stamp or abs((now-stamp).total_seconds()) > 90:
        raise ValueError("Arm observations must be prospective and current")
    root = Path(root); dp = root/"decisions"/(date+".json"); op = root/"outcomes"/(date+".json")
    state_path = root/"sessions"/(date+".json")
    with E.locked(root):
        t3 = st["templates"]["T3_BLACKOUT"]
        candidate = {k: t3[k] for k in ("legs", "credit", "max_loss_usd")} if t3.get("legs") else None
        trace = V.record(root, snap, m["protocol"], now, candidate=candidate)
        state = E.read(state_path) if state_path.exists() else {"date": date, "protocol": m["protocol"], "status": "collecting"}
        if op.exists():
            # Recover a crash between the immutable outcome and state writes.
            prior = checked(op)
            status = "resolved" if prior["counterfactual"] else "unresolved"
            if state["status"] != status:
                state.update(status=status, error=None if prior["counterfactual"] else "incomplete counterfactual path")
                atomic_json(state_path, state)
            return
        if dp.exists():
            d = checked(dp)
            if "last_observed_at" not in state:
                # A crash after sealing the decision but before its mutable
                # checkpoint must resume at the sealed entry, not choose again.
                state.update(status="tracking", path_gap=False, last_observed_at=d["entry_at"])
            if stamp <= E.timestamp(state["last_observed_at"]):
                return  # an identical snapshot is already checked by V.record
            from desk.odte.templates import cost_to_close
            quote = cost_to_close(d["candidate"]["legs"], [r for r in snap["rows"] if r.get("live_eligible")])
            state["path_gap"] |= (stamp-E.timestamp(state["last_observed_at"])).total_seconds() > 90 or quote is None
            state["last_observed_at"] = stamp.isoformat()
            if t3["status"] == "CLOSED" or stamp.strftime("%H:%M") > "15:46":
                valid = (t3["status"] == "CLOSED" and not state["path_gap"] and quote is not None
                         and t3["exit_reason"] != "SETTLED" and stamp.strftime("%H:%M:%S") <= "15:46:30")
                cf = {"gross_pnl_usd": round((t3["credit"]-t3["exit_cost"])*D.MULTIPLIER*D.CONTRACTS, 2),
                      "exit_at": t3["exit_ts"], "exit_reason": t3["exit_reason"], "exit_cost": t3["exit_cost"]} if valid else None
                seal(op, resolve_arms(d, cf, now, m))
                state.update(status="resolved" if valid else "unresolved", error=None if valid else "incomplete counterfactual path")
        elif t3["status"] == "OPEN":
            fresh = {r.get("conId") for r in snap["rows"] if r.get("live_eligible")}
            if t3["entry_ts"] != snap["ts"] or not snap.get("indices_live") or not all(r["conId"] in fresh for r in candidate["legs"].values()):
                state.update(status="unavailable", error="first T3 entry was not captured with live quotes")
            else:
                forecast_error = None
                try:
                    forecast = forecast_for(m, date, stamp)
                except (ValueError, OSError, KeyError) as exc:
                    forecast = None; forecast_error = str(exc)
                gates, arms = evaluate(trace["features"], candidate, forecast, m)
                ctx = context(trace["features"])
                d = {"date": date, "protocol": m["protocol"], "decided_at": now.isoformat(), "entry_at": stamp.isoformat(),
                     "snapshot_digest": E.digest(snap), "observation_id": trace["id"], "candidate": candidate,
                     "features": trace["features"], "gates": gates, "arms": arms, "context": ctx,
                     "forecast": forecast, "forecast_error": forecast_error,
                     "allocation": allocation(m, arms, ctx, history(root, m, stamp), date)}
                seal(dp, d)
                state.update(status="tracking", path_gap=False, last_observed_at=stamp.isoformat())
        elif stamp.strftime("%H:%M") > "10:20" and state["status"] == "collecting":
            state.update(status="no_candidate", error=t3.get("skip_reason") or "no eligible T3 candidate")
        state["last_capture"] = stamp.isoformat()
        atomic_json(state_path, state)
    if stamp.minute % 15 == 0 or op.exists():
        write_report(root)


def stats(values):
    avg = mean(values) if values else None
    se = math.sqrt(sum((v-avg)**2 for v in values)/(len(values)-1)/len(values)) if len(values)>1 else None
    cumulative = peak = drawdown = 0.
    for v in values:
        cumulative += v; peak = max(peak, cumulative); drawdown = min(drawdown, cumulative-peak)
    return {"sessions": len(values), "mean_usd": avg, "total_usd": sum(values), "standard_error_usd": se,
            "worst_usd": min(values) if values else None, "max_drawdown_usd": drawdown}


def report(root):
    root = Path(root); m = protocol(root)
    if m is None:
        return {"status": "not_registered", "live_enabled": False}
    ds = [checked(p) for p in sorted((root/"decisions").glob("*.json"))]
    outcomes = {r["date"]: r for p in sorted((root/"outcomes").glob("*.json")) if (r := checked(p))["protocol"] == m["protocol"]}
    for d in ds:
        if d["protocol"] != m["protocol"] or d["date"] in outcomes and outcomes[d["date"]]["decision_id"] != d["id"]:
            raise ValueError("Arm history lineage mismatch")
    arms = {}
    for name, definition in m["arms"].items():
        daily = []
        for d in ds:
            r = outcomes.get(d["date"], {}); result = r.get("arms", {}).get(name, {})
            daily.append({"date": d["date"], **d["arms"][name], "net_pnl_usd": result.get("net_pnl_usd"),
                "counterfactual_gross_usd": (r.get("counterfactual") or {}).get("gross_pnl_usd"),
                "weight": d["allocation"]["probabilities"].get(name, 0.), "selected": d["allocation"]["selected_arm"] == name,
                "features": d["features"], "gates": d["gates"], "candidate": d["candidate"],
                "context": d["context"],
                "forecast_reasons": ((d.get("forecast") or {}).get("forecast") or {}).get("reasons", []),
                "forecast_error": d.get("forecast_error"),
                "entry_at": d["entry_at"], "forecast_id": (d.get("forecast") or {}).get("id"),
                "decision_id": d["id"], "outcome_id": r.get("id")})
        deltas = [r["arms"][name]["net_pnl_usd"]-r["arms"]["T3"]["net_pnl_usd"] for r in outcomes.values()
                  if r["arms"][name]["net_pnl_usd"] is not None and r["arms"]["T3"]["net_pnl_usd"] is not None]
        by_context = {}
        for day in daily:
            label = " / ".join(day["context"].values())
            by_context.setdefault(label, {"net": [], "delta": []})
            if day["net_pnl_usd"] is not None:
                by_context[label]["net"].append(day["net_pnl_usd"])
                base = outcomes[day["date"]]["arms"]["T3"]["net_pnl_usd"]
                if base is not None:
                    by_context[label]["delta"].append(day["net_pnl_usd"]-base)
        arms[name] = {**definition, "stats": stats([r["net_pnl_usd"] for r in daily if r["net_pnl_usd"] is not None]),
            "by_context": {k: {"stats": stats(v["net"]), "vs_t3": stats(v["delta"])} for k, v in by_context.items()},
            "vs_t3": stats(deltas), "takes": sum(r["decision"] == "take" for r in daily),
            "skips": sum(r["decision"] == "skip" for r in daily),
            "unavailable": sum(r["decision"] == "unavailable" for r in daily), "daily": daily}
    effects = {}
    for factor in FACTORS:
        pairs = [(a, b) for a, x in m["arms"].items() for b, y in m["arms"].items()
                 if a != "CASH" and b != "CASH" and factor not in x["factors"] and set(y["factors"]) == set(x["factors"]) | {factor}]
        daily_effects = []
        for date, r in sorted(outcomes.items()):
            differences = [r["arms"][b]["net_pnl_usd"]-r["arms"][a]["net_pnl_usd"] for a, b in pairs
                           if all(r["arms"][n]["net_pnl_usd"] is not None for n in (a,b))]
            if differences:
                daily_effects.append({"date":date,"mean_increment_usd":mean(differences),"paired_combinations":len(differences)})
        effects[factor] = {"description": FACTORS[factor], "stats": stats([r["mean_increment_usd"] for r in daily_effects]),
                           "daily": daily_effects, "interpretation": "Within-session paired ablation; descriptive, not causal"}
    chosen = [r["arms"][r["selected_arm"]]["net_pnl_usd"] for r in outcomes.values()
              if r["arms"][r["selected_arm"]]["net_pnl_usd"] is not None]
    paired_chosen = [r["arms"][r["selected_arm"]]["net_pnl_usd"]-r["arms"]["T3"]["net_pnl_usd"]
                     for r in outcomes.values() if all(r["arms"][name]["net_pnl_usd"] is not None
                                                      for name in (r["selected_arm"], "T3"))]
    return {"status": "paper_experiment", "built_at": E.utcnow().isoformat(), "protocol": m["protocol"],
            "start_date":m["start_date"], "live_enabled": False, "promotion_allowed": False,
            "arms": arms, "factor_effects": effects, "selector_stats": stats(chosen),
            "selector_vs_t3": stats(paired_chosen),
            "unresolved_sessions": sum(r.get("counterfactual") is None for r in outcomes.values()),
            "latest_allocation": ds[-1]["allocation"] if ds else None,
            "readiness": E.read(root.parent/"research_health.json") if (root.parent/"research_health.json").exists() else None,
            "sessions": [E.read(p) for p in sorted((root/"sessions").glob("*.json"))],
            "costs": {k: m[k] for k in ("trade_cost_usd", "news_cost_usd", "risk_budget_usd")},
            "limitations": ["Full-information paper outcomes are simulated touch fills, not executed fills.",
                "Arm results share the same sessions and are correlated; sixteen arms do not create sixteen observations.",
                "Thresholds are frozen hypotheses, not optimized or validated edges.",
                "Selector uses only resolved prior sessions on a common eligible-arm calendar, at most 60; missing observations can bias that subset.",
                "First 20 training sessions use uniform weights; context estimates shrink to pooled history.",
                "All arm outcomes are observable: this is an experts problem, not a bandit. Sampling does not gather additional information.",
                "The sampled paper selector is a prospective simulation, not evidence about live allocation or executed fills.",
                "News-only remains the existing premarket forecast; this experiment adds entry-time numeric combinations, not a new LLM call.",
                "Unresolved trade paths remain null; deliberate cash decisions may resolve independently.",
                "Multiple comparisons, changing regimes and estimated costs prevent a claim of live alpha."]}


def finalize_missing(root, *, now=None):
    """A stopped collector yields an unresolved path, never a reconstructed fill."""
    root = Path(root); m = protocol(root); now = now or E.utcnow()
    if not m:
        return
    with E.locked(root):
        for p in sorted((root/"decisions").glob("*.json")):
            d = checked(p); op = root/"outcomes"/p.name
            if d["protocol"] != m["protocol"]:
                raise ValueError("Cannot finalize a foreign protocol")
            cutoff = dt.datetime.combine(dt.date.fromisoformat(d["date"]), dt.time(15, 46, 30), E.ET)
            if now <= cutoff or op.exists():
                continue
            seal(op, resolve_arms(d, None, now, m))
            sp = root/"sessions"/p.name
            state = E.read(sp) if sp.exists() else {"date": d["date"], "protocol": m["protocol"]}
            state.update(status="unresolved", error="collector did not seal an exit before the resolution deadline")
            atomic_json(sp, state)


def write_report(root):
    from desk.odte.render_arms import render
    finalize_missing(root)
    result = report(root)
    atomic_json(Path(root)/"report.json", result)
    html = render(result)
    from desk.odte.storage import atomic_write
    atomic_write(Path(root)/"report.html", html)
    m = protocol(root)
    if m and m.get("page_path"):
        atomic_write(Path(m["page_path"]), html)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=D.DATA/"arm_experiment")
    p.add_argument("--forecast-root", type=Path, default=D.DATA/"text_overlay")
    p.add_argument("--continuation-root", type=Path)
    p.add_argument("--start-date"); p.add_argument("--page", type=Path)
    action=p.add_mutually_exclusive_group(required=True)
    action.add_argument("--init", action="store_true"); action.add_argument("--report", action="store_true")
    a=p.parse_args()
    if a.init:
        if not a.start_date:
            p.error("--init requires --start-date")
        initialize(a.root, start_date=a.start_date, forecast_root=a.forecast_root,
                   continuation_root=a.continuation_root, page_path=a.page)
    r=write_report(a.root)
    print(json.dumps({k:r.get(k) for k in ("status","start_date","protocol","live_enabled")},indent=2))


if __name__ == "__main__":
    main()
