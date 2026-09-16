"""memory_lint — the rot detector for the doctrine/memory layer.

Three stale-memory incidents in two days (cocoa 'crashed' after it doubled
back; the CCRN/Aya merger dead 7 months; 'Tier-1 controls STILL NOT RUN' when
they'd run in May) proved the memory layer has no expiry mechanism. This
linter supplies mechanical review pressure:

  - scans every memory file for PERISHABLE claims (prices, percentages,
    deal/status words, 'still/not yet/pending/current', as-of dates)
  - scores staleness = file age x perishability density
  - emits the ranked review queue -> desk/data/memory_lint.json + stdout

THE RITUAL (handoff): weekly, the morning pass re-verifies the top-5 —
either the fact still holds (touch the file with a re-verified stamp) or it
doesn't (fix it on the spot). A memory that can't be cheaply re-verified gets
its perishable claim REWRITTEN as a dated observation ('as of 2026-07-06,
cocoa ~$5,700') so it can never masquerade as current again.

Registered weekly on the heartbeat. READ-ONLY (reports; never edits memories).
    python3 -m desk.memory_lint
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

MEMDIR = Path.home() / ".claude" / "projects" / "-Users-ajay-exalted-signalos" / "memory"
OUT = Path(__file__).resolve().parents[1] / "desk" / "data" / "memory_lint.json"

# perishable-claim markers, weighted by how fast that claim class rots
MARKERS = [
    (r"STILL NOT RUN|not yet run|hasn.t (?:yet )?(?:run|happened|closed)", 5, "status-negation (the 'controls not run' class)"),
    (r"\bpending\b|\bawaiting\b|\bunresolved\b|\bin progress\b|\bupcoming\b", 4, "pending-status"),
    (r"\bcurrently\b|\bright now\b|\btoday\b|\bas of now\b|\bstill\b", 3, "present-tense claim"),
    (r"crashed|spiked|doubled|halved|collapsed|rallied|at (?:all-time |cycle |era )?highs?|at lows?", 4, "price-action claim (the cocoa class)"),
    (r"\$[\d,]+(?:\.\d+)?[MBk]?\b", 2, "dollar figure"),
    (r"\b\d{1,3}(?:\.\d+)?%|\b\d+(?:\.\d+)?pp\b", 2, "percentage"),
    (r"\b(?:merger|deal|acquisition|tender|buyout)\b", 3, "deal-status (the Aya class)"),
    (r"\b20\d{2}-\d{2}(?:-\d{2})?\b", 1, "hard date (good if labeled as-of; rot if implied current)"),
    (r"close-only|feed is|endpoint|API|permission", 3, "infrastructure claim (feeds/permissions change)"),
]
# files whose whole purpose is a durable LESSON decay slowly; weight down
LESSON_HINT = re.compile(r"^feedback_", re.I)


def lint() -> dict:
    rows = []
    for f in sorted(MEMDIR.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        txt = f.read_text(errors="ignore")
        age_d = (time.time() - f.stat().st_mtime) / 86400
        hits = []
        score = 0
        for pat, w, label in MARKERS:
            found = re.findall(pat, txt, re.I)
            if found:
                hits.append({"class": label, "n": len(found), "sample": str(found[0])[:60]})
                score += w * min(len(found), 3)
        lesson = bool(LESSON_HINT.match(f.name))
        # staleness = perishability x age, lessons discounted (their facts still count, halved)
        staleness = score * (0.5 if lesson else 1.0) * min(age_d / 14, 4.0)
        # a re-verified stamp inside the file resets the effective clock
        m = re.search(r"re-?verified[: ]+(\d{4}-\d{2}-\d{2})", txt, re.I)
        if m:
            hits.append({"class": "re-verified stamp", "n": 1, "sample": m.group(1)})
        rows.append({"file": f.name, "age_days": round(age_d, 1), "perishability": score,
                     "staleness": round(staleness, 1), "lesson_file": lesson,
                     "top_hits": hits[:4]})
    rows.sort(key=lambda r: -r["staleness"])
    out = {"asof": time.strftime("%Y-%m-%d %H:%M"), "n_files": len(rows),
           "review_queue_top10": rows[:10], "all": rows}
    OUT.write_text(json.dumps(out, indent=1))
    return out


def main():
    out = lint()
    print(f"[memory_lint] {out['n_files']} memories scanned — the review queue (re-verify or re-date the top 5):")
    for r in out["review_queue_top10"][:8]:
        classes = ", ".join(h["class"] for h in r["top_hits"][:3])
        print(f"  {r['staleness']:6.1f}  {r['file']:55s} age {r['age_days']:5.1f}d  [{classes}]")


if __name__ == "__main__":
    main()
