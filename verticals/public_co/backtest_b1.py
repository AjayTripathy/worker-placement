"""
B1 backtest orchestrator: run the framework end-to-end at a historical
cutoff date with explicit hindsight-blinding.

For each ticker in a cohort:
  1. Ensure pre-cutoff 10-K is fetched (via backtest_fetch_filings).
  2. Render a planner prompt that:
       - References the historical filing path (filings_<cutoff>/)
       - Sets cutoff explicitly to the historical date
       - Adds hindsight-blinding language (no post-cutoff knowledge)
       - Writes plan.json into data/_backtest/<cutoff>/<TK>.plan.json
  3. (Manual step / parallel subagent) — generate plans.
  4. Run plan_executor with data_dir=data/_backtest/<cutoff>/
     so M-source calls honor the historical cutoff.
  5. Run deterministic_scorer with same data_dir.

Then build_aggregates() recomputes cohort matrices and pair emits
in the backtest namespace, parallel to the live one.

Usage:
    # Step 1 — emit prompts and launch subagents externally
    python3 -m verticals.public_co.backtest_b1 prep \
        --cutoff 2024-05-17 --cohorts fintech_cohort

    # Step 2 — once plans land, run downstream pipeline
    python3 -m verticals.public_co.backtest_b1 run \
        --cutoff 2024-05-17 --cohorts fintech_cohort
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from .m_source_catalog import CATALOG
from . import plan_executor, deterministic_scorer
from . import backtest_fetch_filings as fetch

HERE = Path(__file__).parent
DATA = HERE / "data"

HINDSIGHT_BLOCK = """
== STRICT HINDSIGHT-BLINDING DISCIPLINE ==
This is a HISTORICAL backtest run. The cutoff date is in the PAST.
- Treat your analysis as if you are reading the filing on that exact date
- Do NOT use any knowledge of events AFTER the cutoff date — no news,
  no subsequent filings, no later restatements, no later management
  changes, no later customer wins or losses
- Do NOT speculate about what eventually happened to the company
- Confine M-source queries to data filed BEFORE the cutoff date
  (the plan_executor will enforce this; pass cutoff_date={cutoff}
  to every connector call)
- If you find yourself drawing on post-cutoff knowledge to score
  a claim, STOP — that claim is inadmissible for this run
"""


def render_backtest_planner_prompt(cohort_module: str, ticker: str,
                                    cutoff: str, backtest_dir: Path) -> str:
    """Render a planner prompt with hindsight-blinding + historical
    filings path + custom output directory."""
    from .planner_prompt import build_planner_prompt_for_ticker

    base = build_planner_prompt_for_ticker(cohort_module, ticker)

    # Replace the live filings path with the historical one
    cutoff_slug = cutoff.replace("-", "_")
    base = base.replace(
        f"/data/{ticker.lower()}/filings/",
        f"/data/{ticker.lower()}/filings_{cutoff_slug}/",
    )
    base = base.replace(
        f"/data/{ticker.lower()}/filings_index.json",
        f"/data/{ticker.lower()}/filings_{cutoff_slug}/index.json",
    )
    # Redirect plan.json output (both forms — with leading slash in explicit
    # "Output (REQUIRED)" line and without in workflow step 5)
    base = base.replace(
        f"/data/_local/{ticker}.plan.json",
        f"/data/_backtest/{cutoff_slug}/{ticker}.plan.json",
    )
    base = base.replace(
        f"data/_local/{ticker}.plan.json",
        f"data/_backtest/{cutoff_slug}/{ticker}.plan.json",
    )
    # Replace the cutoff in any explicit references
    base = base.replace("Cutoff: 2026-05-16", f"Cutoff: {cutoff}")
    base = base.replace('"cutoff": "2026-05-16"', f'"cutoff": "{cutoff}"')
    # Inject hindsight-blinding header
    blinding = HINDSIGHT_BLOCK.format(cutoff=cutoff)
    base = base.replace("== STRICT BLINDING DISCIPLINE ==",
                        blinding + "\n== STRICT BLINDING DISCIPLINE ==")
    return base


def prep(cohort_module: str, cutoff: str) -> dict:
    """Step 1: fetch filings + emit planner prompts to /tmp/."""
    m = importlib.import_module(cohort_module)
    cohort_slug = cohort_module.rsplit(".", 1)[-1].replace("_cohort", "")
    cutoff_slug = cutoff.replace("-", "_")
    backtest_dir = DATA / "_backtest" / cutoff_slug
    backtest_dir.mkdir(parents=True, exist_ok=True)

    # Fetch filings
    cohort_full = (
        cohort_module if cohort_module.startswith("verticals.public_co.")
        else f"verticals.public_co.{cohort_module}"
    )
    work = fetch.collect_cohort_tickers([cohort_full])
    print(f"Cohort '{cohort_slug}' has {len(work)} tickers; fetching pre-{cutoff} filings...")
    fetched = []
    for tk, cik in work:
        if not cik:
            continue
        r = fetch.fetch_ticker(tk, cik, cutoff)
        if r["status"] in ("fetched", "cached"):
            fetched.append(tk)
            print(f"  {tk}: {r['status']}")
        else:
            print(f"  {tk}: SKIP ({r['status']})")

    # Emit planner prompts
    prompts: dict[str, str] = {}
    for tk in fetched:
        p = render_backtest_planner_prompt(cohort_full, tk, cutoff, backtest_dir)
        prompt_path = Path(f"/tmp/planner_b1_{cohort_slug}_{cutoff_slug}_{tk}.txt")
        prompt_path.write_text(p)
        prompts[tk] = str(prompt_path)
        print(f"  Prompt for {tk}: {prompt_path} ({len(p)} chars)")

    return {
        "cohort":       cohort_slug,
        "cutoff":       cutoff,
        "backtest_dir": str(backtest_dir),
        "tickers":      fetched,
        "prompts":      prompts,
    }


def run_downstream(cohort_module: str, cutoff: str) -> dict:
    """Step 2: assume plan.json files exist in data/_backtest/<cutoff>/.
    Run plan_executor + deterministic_scorer for each ticker."""
    m = importlib.import_module(cohort_module)
    cohort_slug = cohort_module.rsplit(".", 1)[-1].replace("_cohort", "")
    cutoff_slug = cutoff.replace("-", "_")
    backtest_dir = DATA / "_backtest" / cutoff_slug

    tickers_with_plans = []
    missing = []
    for member in m.COHORT:
        tk = member.ticker.upper()
        if (backtest_dir / f"{tk}.plan.json").exists():
            tickers_with_plans.append(tk)
        else:
            missing.append(tk)

    print(f"Found plans for {len(tickers_with_plans)} of {len(m.COHORT)} tickers")
    if missing:
        print(f"  missing: {missing}")

    # Execute + score
    for tk in tickers_with_plans:
        r = plan_executor.execute_plan(tk, data_dir=backtest_dir)
        if "error" in r:
            print(f"  {tk} executor: {r['error']}")
            continue
        s = deterministic_scorer.score_ticker(tk, data_dir=backtest_dir)
        if "error" in s:
            print(f"  {tk} scorer: {s['error']}")
            continue
        counts = s["counts"]
        ord_keys = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY",
                    "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]
        parts = [f"{k[:4]}={counts.get(k,0)}" for k in ord_keys]
        print(f"  {tk}: {s['n_claims']} claims, " + " ".join(parts))

    return {
        "cohort":           cohort_slug,
        "cutoff":           cutoff,
        "tickers_scored":   tickers_with_plans,
        "missing":          missing,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["prep", "run"])
    ap.add_argument("--cutoff", required=True)
    ap.add_argument("--cohorts", required=True, nargs="+",
                    help="cohort module names, e.g. fintech_cohort")
    args = ap.parse_args()

    for cm in args.cohorts:
        cohort_full = cm if cm.startswith("verticals.public_co.") else f"verticals.public_co.{cm}"
        print(f"\n=== {cm} @ {args.cutoff} ({args.step}) ===")
        if args.step == "prep":
            r = prep(cohort_full, args.cutoff)
        else:
            r = run_downstream(cohort_full, args.cutoff)
        print(json.dumps(r, indent=2, default=str)[:1500])


if __name__ == "__main__":
    main()
