"""
Orchestrator for fraud-vs-control framework test.

Per-member-cutoff variant of backtest_b1. Renders one planner prompt
per cohort member, using that member's own pre-revelation cutoff date
(not a single cohort-wide cutoff). Writes prompts to /tmp/, plans into
data/_backtest/fraud_control/.

Steps:
  prep    — render and write prompts for each member
  run     — once plan.json files exist, run plan_executor + scorer
  emit    — apply forward_bet_emission + DA filter; compare classes
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .fraud_control_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS
from .planner_prompt import build_planner_prompt
from .m_source_catalog import CATALOG
from . import plan_executor, deterministic_scorer
from .backtest_b1 import HINDSIGHT_BLOCK

HERE = Path(__file__).parent
DATA = HERE / "data"
BACKTEST_DIR = DATA / "_backtest" / "fraud_control"


def render_member_prompt(m) -> str:
    """Render a planner prompt for one fraud_control_cohort member with
    its own pre-revelation cutoff + hindsight-blinding header + redirected
    output path."""
    base = build_planner_prompt(
        ticker=m.ticker,
        cik_padded=m.cik,
        company_name=m.name,
        notes=m.notes,
        cutoff=m.cutoff,
        cohort_context=COHORT_CONTEXT,
        counterparty_ciks=COMMON_COUNTERPARTY_CIKS,
        catalog=CATALOG,
    )

    cutoff_slug = m.cutoff.replace("-", "_")
    base = base.replace(
        f"/data/{m.ticker.lower()}/filings/",
        f"/data/{m.ticker.lower()}/filings_{cutoff_slug}/",
    )
    base = base.replace(
        f"/data/{m.ticker.lower()}/filings_index.json",
        f"/data/{m.ticker.lower()}/filings_{cutoff_slug}/index.json",
    )
    base = base.replace(
        f"/data/_local/{m.ticker}.plan.json",
        f"/data/_backtest/fraud_control/{m.ticker}.plan.json",
    )
    base = base.replace(
        f"data/_local/{m.ticker}.plan.json",
        f"data/_backtest/fraud_control/{m.ticker}.plan.json",
    )
    blinding = HINDSIGHT_BLOCK.format(cutoff=m.cutoff)
    base = base.replace("== STRICT BLINDING DISCIPLINE ==",
                        blinding + "\n== STRICT BLINDING DISCIPLINE ==")
    return base


def prep() -> dict:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    prompts = {}
    for m in COHORT:
        # Sanity check the filing exists
        cutoff_slug = m.cutoff.replace("-", "_")
        idx_path = DATA / m.ticker.lower() / f"filings_{cutoff_slug}" / "index.json"
        if not idx_path.exists():
            print(f"  {m.ticker}: MISSING filing index at {idx_path}; "
                  f"run fraud_control_fetch first")
            continue
        p = render_member_prompt(m)
        prompt_path = Path(f"/tmp/planner_fraud_control_{m.ticker}.txt")
        prompt_path.write_text(p)
        prompts[m.ticker] = str(prompt_path)
        print(f"  {m.ticker} [{m.klass}]  cutoff={m.cutoff}  "
              f"prompt={prompt_path} ({len(p):,} chars)")
    return {"backtest_dir": str(BACKTEST_DIR), "prompts": prompts}


def run() -> dict:
    """Phase 2 + Phase 3: plan_executor + deterministic_scorer per ticker.
    Assumes plan.json files exist in BACKTEST_DIR."""
    found = []
    missing = []
    for m in COHORT:
        if (BACKTEST_DIR / f"{m.ticker}.plan.json").exists():
            found.append(m.ticker)
        else:
            missing.append(m.ticker)

    print(f"Plans found: {len(found)} / {len(COHORT)}; missing: {missing}")
    for tk in found:
        r = plan_executor.execute_plan(tk, data_dir=BACKTEST_DIR)
        if "error" in r:
            print(f"  {tk} executor: {r['error']}")
            continue
        s = deterministic_scorer.score_ticker(tk, data_dir=BACKTEST_DIR)
        if "error" in s:
            print(f"  {tk} scorer: {s['error']}")
            continue
        counts = s["counts"]
        keys = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY",
                "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]
        parts = [f"{k[:4]}={counts.get(k,0)}" for k in keys]
        print(f"  {tk}: {s['n_claims']} claims  " + " ".join(parts))
    return {"backtest_dir": str(BACKTEST_DIR), "tickers_scored": found,
            "missing": missing}


def emit_compare() -> dict:
    """Phase 4: read scores.json for each member, apply forward_bet_emission
    + DA filter, tabulate by class."""
    from .forward_bet_emission import is_truth_signal, EMIT_DA_TIERS
    from ._cohort_report import severity_counts, composite_score
    from .discovery_advantage import compute_discovery_advantage

    rows = []
    for m in COHORT:
        scores_path = BACKTEST_DIR / f"{m.ticker}.scores.json"
        if not scores_path.exists():
            rows.append({"ticker": m.ticker, "klass": m.klass, "status": "no_scores"})
            continue
        s = json.loads(scores_path.read_text())
        scores = s.get("scores", [])
        sc = severity_counts(scores)
        comp = composite_score(scores)
        row_for_truth = {
            "severity_counts": sc,
            "composite_score": comp,
        }
        truth = is_truth_signal(row_for_truth)
        # DA tier: live lookup (finviz). May return UNKNOWN for delisted names.
        try:
            da = compute_discovery_advantage(m.ticker)
            da_tier = da.get("tier", "UNKNOWN")
        except Exception:
            da_tier = "UNKNOWN"
        emit = truth and (da_tier in EMIT_DA_TIERS)
        rows.append({
            "ticker":     m.ticker,
            "klass":      m.klass,
            "cutoff":     m.cutoff,
            "n_claims":   len(scores),
            "red":        sc.get("RED_FLAG_NEGATIVE", 0),
            "severe":     sc.get("SEVERE_UNDERDELIVERY", 0),
            "moderate":   sc.get("MODERATE_UNDERDELIVERY", 0),
            "unver":      sc.get("UNVERIFIABLE", 0),
            "pass":       sc.get("PASS", 0),
            "composite":  round(comp, 3),
            "truth_signal": truth,
            "da_tier":    da_tier,
            "emit":       emit,
        })

    by_class: dict[str, dict] = {}
    for r in rows:
        if r.get("status") == "no_scores":
            continue
        c = r["klass"]
        b = by_class.setdefault(c, {"n": 0, "emit": 0, "truth_signal": 0})
        b["n"] += 1
        b["emit"] += int(r["emit"])
        b["truth_signal"] += int(r["truth_signal"])

    out = {"rows": rows, "by_class": by_class}
    out_path = BACKTEST_DIR / "emit_decisions.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["prep", "run", "emit"])
    args = ap.parse_args()

    if args.step == "prep":
        r = prep()
    elif args.step == "run":
        r = run()
    else:
        r = emit_compare()
    print(json.dumps(r, indent=2, default=str)[:3000])


if __name__ == "__main__":
    main()
