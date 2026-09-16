"""court_queue — the automatic verification→court conveyor for screen-surfaced names
(PRD P1 stages 3-5; user directive 2026-08-06: "things surfaced by the new screening
code should automatically be courted").

FLOW (the generator-never-grades-itself invariant is the queue's spine):
  screen emits candidates            -> stage TRAP_VERIFY   (enqueued by the screens themselves)
  trap verification survives         -> stage COURT_RED
  red bench done                     -> stage COURT_BLUE    (blue prosecutes the RED case)
  blue bench done                    -> stage ADJUDICATE
  adjudicated + pitch doc written    -> DONE (ledger/packs/edge writes by the adjudicator)

The queue is a Store-backed file (merge by ticker+enqueued date); desk/court_runner.py
drains it headlessly via `claude -p` (the headless_grader transport). Enqueueing is
idempotent; names already in the research ledger or previously adjudicated are refused
at enqueue time so screens can call blindly on every run.

  from desk.court_queue import enqueue_candidates
  enqueue_candidates([{"ticker": "AAA.L", ...}], source="screen_europe/2026-08-06")
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

from desk.store import Store

ROOT = Path(__file__).resolve().parents[1]
QUEUE = Store("desk/data/court_queue.json", list_path="items",
              key=lambda r: r["ticker"])

STAGES = ["TRAP_VERIFY", "REFUTABILITY", "SCIENCE", "COURT_RED", "COURT_BLUE", "ADJUDICATE", "DONE", "KILLED"]

DEEP_TECH_KEYWORDS = (
    "biolog", "biotech", "clinical", "trial", "phase 1", "phase 2", "phase 3", "fda", "drug",
    "molecule", "receptor", "oncolog", "therapeut", "genomic", "nct0",
    "semiconductor", "lithograph", "photonic", "quantum", "fusion", "nuclear", "reactor",
    "satellite", "launch vehicle", "hypersonic", "battery chemistry", "electrolyzer",
    "catalyst chemistry", "superconduct")


def is_deep_tech(context: str) -> bool:
    """Science-brief-first trigger (ratified 2026-09-04, GPCR precedent): names whose
    load-bearing claims are scientific/technical get a SCIENCE stage before the benches."""
    c = str(context or "").lower()
    return any(k in c for k in DEEP_TECH_KEYWORDS)


def _norm(sym: str) -> str:
    return re.split(r"[.\s]", str(sym or "").strip())[0].upper()


def _ledger_fams() -> set:
    try:
        rl = json.loads((ROOT / "desk/data/research_ledger.json").read_text())
        return {_norm(n["ticker"]) for n in rl.get("names", [])}
    except Exception:
        return set()


# THESIS-SOURCED rows do not have a screen row to verify (principal directive 2026-08-18, the
# LIND case). TRAP_VERIFY exists to catch SCREEN artifacts — mcap joins, windfall metrics, stale
# drawdown anchors, cash-is-customers' — and its verdict vocabulary is screen-shaped
# ("SCREEN-MISCLASSIFIED"). Point it at a name that arrived from a THESIS and it audits a row that
# does not exist and returns a true statement about nothing: LIND was killed for having "no
# valuation metric in the screen row" and a "stale, irrelevant" dd52 when it was enqueued on a
# permit-moat argument that never mentioned either. Those rows route STRAIGHT TO COURT_RED, where
# the brief IS the thesis and the benches argue the mechanism.
THESIS_SOURCES = ("principal_", "user_directive", "dogfood_", "band_touch_", "mark_integrity_",
                  "_thesis_", "_recourt", "recourt_", "ai_faircarry",
                  "thesis:", "thesis_")   # 2026-09-10: generator-sourced regime theses


def is_thesis_sourced(source: str) -> bool:
    src = str(source or "")
    return any(k in src for k in THESIS_SOURCES)


def enqueue_candidates(rows: list[dict], source: str, stage: str = "TRAP_VERIFY",
                       allow_ledger: bool = False) -> dict:
    """Idempotent enqueue. P1 screens: ledger names refused (fresh-name flow). P2 dislocation
    events pass allow_ledger=True — a class de-rate makes KNOWN names re-triageable (R2.4);
    already-queued names still dedupe."""
    if stage == "TRAP_VERIFY" and is_thesis_sourced(source):
        stage = "COURT_RED"       # no screen row exists — nothing for trap-verify to audit
    if stage == "COURT_RED":
        ctx = " ".join(str(r.get("context", "")) + " " + str(r.get("ticker", "")) for r in rows)
        if is_deep_tech(ctx):
            stage = "SCIENCE"     # deep-tech: science brief FIRST, benches argue from it
    led = _ledger_fams() if not allow_ledger else set()
    existing = {i["ticker"] for i in QUEUE.rows()}
    now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    fresh = []
    for r in rows:
        t = r.get("ticker") or r.get("sym")
        if not t or t in existing or _norm(t) in led:
            continue
        existing.add(t)                       # dedupe within the call — first row's context wins
        fresh.append({
            "ticker": t, "stage": stage, "source": source, "enqueued_utc": now,
            "screen_row": {k: v for k, v in r.items() if not str(k).startswith("_")},
            "history": [],
        })
    counts = QUEUE.upsert(fresh, generated_by=f"enqueue:{source}") if fresh else \
        {"added": 0, "updated": 0, "deleted": 0, "total": len(QUEUE.rows())}
    return counts


def advance(ticker: str, to_stage: str, artifact: str | None = None,
            note: str | None = None) -> dict:
    """Move an item to the next stage, recording the artifact path (verdict file, bench
    output) in its history. KILLED and DONE are terminal."""
    if to_stage not in STAGES:
        raise ValueError(f"unknown stage {to_stage}")
    items = QUEUE.rows()
    it = next((i for i in items if i["ticker"] == ticker), None)
    if it is None:
        raise KeyError(f"{ticker} not queued")
    it["history"].append({"from": it["stage"], "to": to_stage,
                          "utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                          "artifact": artifact, "note": note})
    it["stage"] = to_stage
    QUEUE.upsert([it], generated_by=f"advance:{ticker}->{to_stage}")
    return it


def pending(stage: str | None = None) -> list[dict]:
    items = [i for i in QUEUE.rows() if i["stage"] not in ("DONE", "KILLED")]
    return [i for i in items if i["stage"] == stage] if stage else items


def check_queue_health(flags: list) -> list:
    """Invariant hook (wired into pipeline_invariants.ALL_CHECKS): a queued name stuck in
    one stage >7d is a rotting candidate — the conveyor's version of the unwired tripwire."""
    try:
        now = datetime.datetime.utcnow()
        for it in pending():
            last = it["history"][-1]["utc"] if it.get("history") else it.get("enqueued_utc", "")
            try:
                age_d = (now - datetime.datetime.fromisoformat(last.rstrip("Z"))).days
            except ValueError:
                age_d = 999
            if age_d > 7:
                flags.append(f"CRITICAL COURT-QUEUE-STUCK: {it['ticker']} has sat in "
                             f"{it['stage']} for {age_d}d (source {it.get('source','?')}) — "
                             f"the conveyor is stalled; run desk.court_runner or kill the item")
    except Exception as e:
        flags.append(f"court-queue invariant errored: {type(e).__name__}: {e}")
    return flags


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        for it in QUEUE.rows():
            print(f"  {it['ticker']:12s} {it['stage']:12s} src={it.get('source','')[:40]} "
                  f"since={it.get('enqueued_utc','')[:10]}")
    else:
        p = pending()
        print(f"court_queue: {len(p)} pending / {len(QUEUE.rows())} total")
        for s in STAGES:
            n = len([i for i in p if i["stage"] == s])
            if n:
                print(f"  {s}: {n}")
