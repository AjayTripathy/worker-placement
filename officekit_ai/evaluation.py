"""Offline comparison of frozen analyst/court calls against independent labels.

No model grades its own answer. Inputs name a common evidence hash, event,
resolution date and audit reference. A synthetic fixture proves arithmetic only;
it is not evidence that courts outperform. Run: python -m officekit_ai.evaluation FILE
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta


def _date(value):
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return datetime.strptime(value, "%m/%d/%Y").date()


def grade_direction(adjudication, closes, horizon_days=30, today=None):
    """Price follow-up at a fixed horizon, never a probability/alpha grade.

    Use first close on/after verdict and target dates (maximum seven-day lag).
    Never use pre-verdict data, a future quote or an arbitrary latest quote.
    """
    today = today or date.today()
    if horizon_days <= 0:
        raise ValueError("horizon must be positive")
    start = _date(adjudication["date"])
    target = start + timedelta(days=horizon_days)
    if target > today:
        return None
    word = str(adjudication.get("verdict") or "").split(" ")[0]
    if word not in {"STARTER", "OWN", "AVOID", "KILL"}:
        return None
    prices = sorted((_date(d), float(v)) for d, v in closes
                    if _date(d) <= today and math.isfinite(float(v)) and float(v) > 0)
    entry = next(((d, v) for d, v in prices if start <= d <= start + timedelta(days=7)), None)
    end = next(((d, v) for d, v in prices if target <= d <= target + timedelta(days=7)), None)
    if not entry or not end or end[0] <= entry[0]:
        raise ValueError("missing close near verdict or fixed-horizon date")
    move = (end[1] / entry[1] - 1) * 100
    return {"adjudication_id": adjudication["id"], "symbol": adjudication["symbol"],
            "strategy": adjudication.get("strategy"), "verdict": adjudication["verdict"],
            "verdict_date": start.isoformat(), "horizon_days": horizon_days,
            "entry_date": entry[0].isoformat(), "exit_date": end[0].isoformat(),
            "move_pct": round(move, 2), "favorable": move > 0 if word in {"STARTER", "OWN"} else move <= 0,
            "grade_kind": "price_direction_only", "protocol": "fixed_horizon_v1"}


def compare(cases):
    """Paired metrics; identical resolved cases and evidence for both methods.

    p is probability of the NAMED event, never conviction/10. Independent audit
    counts and recorded cost/latency are required so missing fields cannot appear
    as zero defects or free inference. Unresolved cases are excluded explicitly.
    """
    summaries = {name: {"brier": 0.0, "false_accepts": 0, "false_rejects": 0,
                        "abstentions": 0, "unsupported_claims": 0, "audited_claims": 0,
                        "cost_usd": 0.0, "latency_s": 0.0} for name in ("analyst", "court")}
    n, excluded, seen = 0, [], set()
    for case in cases:
        if case["id"] in seen:
            raise ValueError("duplicate case id")
        seen.add(case["id"])
        if case.get("outcome") is None:
            excluded.append(case["id"])
            continue
        if type(case["outcome"]) is not bool or not all(case.get(k) for k in
                ("event", "evidence_hash", "resolved_at", "audit_ref")):
            raise ValueError("resolved case requires a boolean outcome, event, evidence hash and independent audit")
        for name in summaries:
            call = case[name]
            if call.get("evidence_hash") != case["evidence_hash"]:
                raise ValueError("paired calls must use the same frozen evidence")
            if datetime.fromisoformat(call["frozen_at"].replace("Z", "+00:00")) >= datetime.fromisoformat(case["resolved_at"].replace("Z", "+00:00")):
                raise ValueError("call must be frozen before outcome resolution")
            p = call["p"]
            if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
                raise ValueError("p must be a finite event probability")
            if call["action"] not in {"accept", "reject", "abstain"}:
                raise ValueError("unknown action")
            for field in ("cost_usd", "latency_s", "audited_claims", "unsupported_claims"):
                value = call[field]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError(f"invalid {field}")
            if call["unsupported_claims"] > call["audited_claims"]:
                raise ValueError("unsupported claims exceed audited claims")
            s = summaries[name]
            s["brier"] += (p - case["outcome"]) ** 2
            s["false_accepts"] += call["action"] == "accept" and not case["outcome"]
            s["false_rejects"] += call["action"] == "reject" and case["outcome"]
            s["abstentions"] += call["action"] == "abstain"
            for field in ("cost_usd", "latency_s", "audited_claims", "unsupported_claims"):
                s[field] += call[field]
        n += 1
    for s in summaries.values():
        s["brier"] = round(s["brier"] / n, 6) if n else None
        s["unsupported_rate"] = (s["unsupported_claims"] / s["audited_claims"]
                                 if s["audited_claims"] else None)
    return {"protocol": "paired_frozen_calls_v1", "n_pairs": n, "excluded_unresolved": excluded,
            "methods": summaries, "brier_delta_court_minus_analyst":
            round(summaries["court"]["brier"] - summaries["analyst"]["brier"], 6) if n else None}


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(json.loads(args.cases.read_text())), indent=2))
