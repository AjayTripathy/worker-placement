"""grade_brief — turn a frozen call into a precise INTELLIGENT-READ task.

Doctrine (2026-07-09): prints are READ by intelligence against a pre-registered gate,
not PARSED by regex. Watchers detect that a release dropped; grading is an LLM read of
the PRIMARY source that evaluates the exact (often compound) frozen condition and returns
a proposed grade WITH evidence — which the assistant confirms before it's written. This
module assembles that read-task so grading is spec'd and dispatchable, never ad hoc.

    python3 -m desk.grade_brief BKE            # brief for BKE's OPEN call(s)
    python3 -m desk.grade_brief --due          # briefs for every call whose cat_date has passed
The output is a ready-to-dispatch prompt for a grader agent (or the assistant). It NEVER
writes a grade — resolution stays a confirmed step (desk.calibration.resolve).
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALIB = ROOT / "desk" / "data" / "calibration_ledger.jsonl"

# where a name's PRIMARY print lives (extend as sources are learned); else the agent finds it
SOURCE_HINTS = {
    "BKE": "Buckle IR monthly net-sales press release (corporate.buckle.com/investor-relations/press-releases)",
    "IVN": "Ivanhoe Mines quarterly production news release + MD&A (ivanhoemines.com / SEDAR+)",
    "OPBK": "OP Bancorp Q2 earnings release + call (SEC 8-K / IR)",
    "BAH": "Booz Allen Hamilton earnings release + 10-Q, Civil segment detail (SEC / IR)",
}


def _open_calls(ticker=None, due_only=False, today=None):
    today = today or datetime.date.today()
    seen = {}
    for line in CALIB.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if (r.get("status") or "OPEN").upper() != "OPEN" or not r.get("cat_date"):
            continue
        if ticker and r["ticker"] != ticker:
            continue
        if due_only:
            try:
                if datetime.date.fromisoformat(r["cat_date"]) > today:
                    continue
            except Exception:
                continue
        seen[(r["ticker"], r["cat_date"])] = r
    return list(seen.values())


def brief(r: dict) -> str:
    tk = r["ticker"]
    src = SOURCE_HINTS.get(tk, "find the company's PRIMARY release (8-K / earnings PR / production report / transcript) — not secondary coverage")
    # 2026-09-09: some rows carry the frozen bar ONLY in `claim` (SPCX-SUBS >=12.8M was graded
    # against "(gate not recorded)" and proposed FAVORABLE on 12.0M). Read every field the bar can live in.
    gate = (r.get("direction") or r.get("catalyst") or r.get("claim") or r.get("bar")
            or r.get("gate") or "(gate not recorded)")
    return f"""GRADE-A-PRINT · {tk} · catalyst {r.get('cat_date')} · our_p={r.get('our_p')}
PRIMARY SOURCE: {src}
THE FROZEN GATE (evaluate EXACTLY this — compound conditions must ALL hold for FAVORABLE):
  {gate}
CATALYST CONTEXT: {r.get('catalyst','')}
TASK:
  1. Read the PRIMARY source (not a headline, not an aggregator). Cite the number(s)/language.
  2. Evaluate the gate literally — every AND clause; read qualitative clauses ('no new X language',
     'stabilizes') as judgments, not keyword matches.
  3. Return: outcome = FAVORABLE | UNFAVORABLE | MIXED, the exact evidence, and any nuance that
     makes it close. If the print has NOT actually landed (estimated date), say so — do NOT grade.
  4. Flag for confirmation before it's written. Do NOT resolve; the assistant runs
     desk.calibration.resolve after confirming. Escalate close/decisive reads to a stronger model."""


def main():
    args = sys.argv[1:]
    due = "--due" in args
    tk = next((a for a in args if not a.startswith("--")), None)
    calls = _open_calls(ticker=tk, due_only=due)
    if not calls:
        print("no OPEN calls" + (f" for {tk}" if tk else "") + (" past their cat_date" if due else ""))
        return
    for r in sorted(calls, key=lambda x: x["cat_date"]):
        print(brief(r) + "\n" + "-" * 72)


if __name__ == "__main__":
    main()
