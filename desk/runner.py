"""runner — the Desk orchestrator. Runs DUE watches (per the consolidated registry), normalizes their
output to Signals, dedupes + suppresses unchanged regimes, appends to the unified feed, and splits the
fresh signals into PUSH (high-severity, surface now) vs ACTIONABLE (high+med, for the daily digest /
agent triage). Deterministic + cheap (no agent tokens) — the OS cron calls this; the Desk AGENT then
reads desk_actionable.json to triage + auto-verify the decisive ones.
"""
from __future__ import annotations
import json, subprocess, time
from pathlib import Path
from . import registry as R, extractors as EX, signals as SG

HERE = Path(__file__).resolve().parent
ROOT = R.ROOT
FEED = HERE / "data" / "desk_feed.jsonl"
ACTIONABLE = HERE / "data" / "desk_actionable.json"


def _recent_feed(days=7) -> list[dict]:
    if not FEED.exists():
        return []
    cutoff = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - days * 86400))
    out = []
    for line in FEED.read_text().splitlines()[-4000:]:
        try:
            s = json.loads(line)
            if s.get("ts", "") >= cutoff:
                out.append(s)
        except Exception:
            pass
    return out


def _last_regime(feed, source):
    for s in reversed(feed):
        if s["source"] == source and s["signal_type"] == "REGIME_CHANGE":
            return s["evidence"]
    return None


def run(force=False, run_watches=True) -> dict:
    due = R.due(force=force)
    feed = _recent_feed()
    seen = {SG.dedupe_key(s) for s in feed}
    fresh = []
    ran = []
    for w in due:
      # PER-WATCH FAULT ISOLATION (2026-08-07): a malformed entry (25/113 lacked 'log')
      # was killing the WHOLE loop with KeyError — every later watch silently skipped.
      # One bad watch must never take down the belt; defaults + try/except, fail loud in-log.
      try:
        out = ""
        if run_watches:
            try:
                p = subprocess.run(w["cmd"], cwd=str(ROOT), capture_output=True, text=True, timeout=600)
                out = (p.stdout or "") + "\n" + (p.stderr or "")
            except Exception as e:
                out = f"[runner] {w['name']} failed: {e}"
            log = ROOT / w.get("log", f"desk/data/{w.get('name','unnamed')}.out")
            log.parent.mkdir(parents=True, exist_ok=True)
            with open(log, "a") as f:
                f.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M')} (desk) =====\n" + out)
            R.mark_ran(w["name"])
            ran.append(w["name"])
        for sig in EX.extract(w.get("extractor"), out):
            # suppress unchanged regimes (only fire on a flip)
            if sig["signal_type"] == "REGIME_CHANGE" and sig["evidence"] == _last_regime(feed, sig["source"]):
                continue
            k = SG.dedupe_key(sig)
            if k in seen:
                continue
            seen.add(k)
            fresh.append(sig)

      except Exception as e:
        print(f"[runner] watch {w.get('name','?')} skipped on error: {type(e).__name__}: {e}")
    if fresh:
        with open(FEED, "a") as f:
            for s in fresh:
                f.write(json.dumps(s) + "\n")

    push = [s for s in fresh if SG.is_push(s)]
    actionable = [s for s in fresh if SG.is_actionable(s)]
    # TOKEN CAP (the playbook's "cap before you ship"): bound how many auto-verify escalations the Desk
    # spawns per day, so a noisy day can't burn an unbounded SignalOS/skeptic budget. NO SILENT CAP —
    # excess is deferred to the digest with a logged note, not dropped.
    MAX_VERIFY_PER_DAY = 8
    today = time.strftime("%Y-%m-%d")
    spent = sum(1 for s in feed if s.get("ts", "").startswith(today) and s.get("_verified"))
    cand = [s for s in actionable if s.get("needs_verification")]
    needs_verify = cand[: max(0, MAX_VERIFY_PER_DAY - spent)]
    deferred = cand[len(needs_verify):]
    for s in needs_verify:
        s["_verified"] = True
    if deferred:
        for s in deferred:
            s["_deferred"] = f"verify-cap {MAX_VERIFY_PER_DAY}/day reached"
    payload = {"asof": time.strftime("%Y-%m-%dT%H:%M:%S"), "ran": ran,
               "n_fresh": len(fresh), "push": push, "actionable": actionable,
               "to_verify": needs_verify, "verify_deferred": len(deferred)}
    # pre-flight coverage check (cache-only, cheap): never let an under-covered name sit silently
    try:
        from . import coverage as COV
        cov = COV.audit(use_network=False)
        payload["coverage"] = {"thin": cov["thin"], "gaps": cov["gaps"]}
    except Exception as e:
        payload["coverage"] = {"error": str(e)}
    ACTIONABLE.write_text(json.dumps(payload, indent=1))
    return payload


def board(days=3) -> list[dict]:
    """The current actionable board: actionable signals from the last `days`."""
    return [s for s in _recent_feed(days) if SG.is_actionable(s)]


if __name__ == "__main__":
    import sys
    p = run(force=("--force" in sys.argv))
    print(f"ran: {p['ran']}  fresh: {p['n_fresh']}  push: {len(p['push'])}  verify: {len(p['to_verify'])}")
    for s in p["actionable"]:
        print(f"  [{s['severity']}] {s['source']}:{s['asset']} {s['signal_type']} — {s['evidence'][:90]}")
