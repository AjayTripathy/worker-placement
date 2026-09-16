"""run_diligence — Phase 2 hook: run the signalos-quant-analyst two-mode pass on each candidate
in outputs/needs_diligence.json, fill the OVERSTATED|REAL|INCONCLUSIVE verdict, and write it back
to the log so score_log can evaluate the SELL_VOL / DIRECTIONAL arms.

Automation: invokes `claude -p` headless with the signalos-quant-analyst agent per candidate (the
diligence IS the honesty engine — Mode A claim-verification + Mode B disconfirmation). If the
`claude` CLI isn't on PATH, it prints the queue + per-name prompt for an analyst (or the main-loop
orchestrator via the Agent tool) to process manually. NEVER places an order.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUEUE = HERE / "outputs" / "needs_diligence.json"
VERDICTS = HERE / "outputs" / "diligence_verdicts.jsonl"

_PROMPT = """You are diligencing a SOCIAL-DRIVEN equity move for a "be-the-casino" options thesis.
Ticker: {ticker} ({name}). Reddit mentions: {mentions}. Conditioning regime: {regime}. \
Options IV verdict: {iv_verdict} (IV/HV {iv_hv}).

Run your two-mode pass (Mode A claim-verification on the current bull/bear narrative against PRIMARY
sources; Mode B independent first-principles disconfirmation) focused on ONE question: is the current
move OVERDONE / built on overstatement, or is it backed by a REAL, verifiable catalyst?

Return STRICT JSON only: {{"ticker":"{ticker}","verdict":"OVERSTATED|REAL|INCONCLUSIVE",
"confidence":"HIGH|MED|LOW","one_line":"...","key_evidence":["..."]}}.
OVERSTATED = sell premium into the rich IV. REAL = do not fade; consider directional. \
INCONCLUSIVE = no trade."""


def _run_one_headless(c: dict) -> dict | None:
    claude = shutil.which("claude")
    if not claude:
        return None
    prompt = _PROMPT.format(**{k: c.get(k) for k in
                              ("ticker", "name", "mentions", "regime", "iv_verdict", "iv_hv")})
    try:
        r = subprocess.run([claude, "-p", "--agent", "signalos-quant-analyst", prompt],
                           capture_output=True, text=True, timeout=900)
        out = r.stdout.strip()
        s, e = out.find("{"), out.rfind("}")
        if s >= 0 and e > s:
            return json.loads(out[s:e + 1])
    except Exception as ex:
        return {"ticker": c["ticker"], "verdict": "ERROR", "error": str(ex)[:120]}
    return None


def run() -> dict:
    if not QUEUE.exists():
        print("no diligence queue."); return {"n": 0}
    queue = json.loads(QUEUE.read_text())
    if not queue:
        print("diligence queue empty — no SELL_VOL/DIRECTIONAL candidates this run.")
        return {"n": 0}
    have_cli = bool(shutil.which("claude"))
    print(f"{len(queue)} candidate(s) to diligence; headless claude {'available' if have_cli else 'NOT on PATH'}.")
    results = []
    for c in queue:
        v = _run_one_headless(c) if have_cli else None
        if v is None:
            # surface for manual / orchestrator processing
            print(f"\n--- DILIGENCE NEEDED: {c['ticker']} ({c.get('name')}) ---")
            print(_PROMPT.format(**{k: c.get(k) for k in
                                   ("ticker", "name", "mentions", "regime", "iv_verdict", "iv_hv")}))
        else:
            results.append(v)
            print(f"  {v.get('ticker')}: {v.get('verdict')} ({v.get('confidence')}) — {v.get('one_line','')[:80]}")
    if results:
        with open(VERDICTS, "a") as f:
            for v in results:
                f.write(json.dumps(v, default=str) + "\n")
    return {"n": len(queue), "scored": len(results)}


if __name__ == "__main__":
    run()
