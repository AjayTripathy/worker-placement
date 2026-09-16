"""ai_break_ensemble — reads every member's JSON from desk/data/ai_ensemble/ and reports
the ensemble view of the AI-capex break question.

Members (each a different epistemology; disagreement is the output, not a bug):
  mechanism.json        refinance-wall constraint + gates + 2008-mapped clock (structural)
  lppl.json             Sornette critical-point fit + critical-slowing-down stats (price-only)
  credit_basis.json     credit-vs-equity divergence (market-implied; credit leads at turns)
  reference_class.json  historical capex-mania survival curve (actuarial outside view)
  minsky.json           financing-stage classifier (regime identification)
  contagion.json        counterparty-network clearing (WHERE it breaks, no timing)
  behavior_tells.json   informed-party behavior union (private-information aggregation)

Aggregation rules:
  - P(break) pools ONLY members that submit probabilities; median + range reported, never a
    false-precision single number.
  - States tally GREEN/AMBER/RED votes; structural members (contagion) and NO_SIGNAL members
    abstain from the vote but their findings print.
  - The DISAGREEMENT LINE is the headline: which members disagree and why is more
    informative than the pooled number.

    python3 -m desk.models.ai_break_ensemble
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

DIR = Path(__file__).resolve().parents[2] / "desk" / "data" / "ai_ensemble"


def main():
    members = {}
    for f in sorted(DIR.glob("*.json")):
        if f.stem.startswith("_"):
            continue
        try:
            members[f.stem] = json.loads(f.read_text())
        except Exception as e:
            members[f.stem] = {"member": f.stem, "state": f"UNREADABLE ({e})"}
    print(f"=== AI-BREAK ENSEMBLE — {datetime.date.today()} — {len(members)} members ===\n")

    votes = {"GREEN": [], "AMBER": [], "RED": []}
    p27, p28 = {}, {}
    for name, m in members.items():
        st = str(m.get("state", "?"))
        base = st.split()[0].split("|")[0]
        if base in votes:
            votes[base].append(name)
        if isinstance(m.get("P_break_by_2027"), (int, float)):
            p27[name] = m["P_break_by_2027"]
        if isinstance(m.get("P_break_by_2028"), (int, float)):
            p28[name] = m["P_break_by_2028"]
        print(f"  {name:16} {st}")
        for note in (m.get("notes") or [])[:2]:
            print(f"      - {note[:150]}")

    def pool(d):
        if not d:
            return "no submissions"
        vals = sorted(d.values())
        med = vals[len(vals) // 2] if len(vals) % 2 else (vals[len(vals)//2 - 1] + vals[len(vals)//2]) / 2
        return f"median {med:.2f}, range {min(vals):.2f}-{max(vals):.2f} across {len(vals)} ({', '.join(f'{k}={v:.2f}' for k, v in d.items())})"

    print(f"\n-- vote --  GREEN {len(votes['GREEN'])} ({', '.join(votes['GREEN'])}) | "
          f"AMBER {len(votes['AMBER'])} ({', '.join(votes['AMBER'])}) | "
          f"RED {len(votes['RED'])} ({', '.join(votes['RED'])})")
    print(f"-- P(break by end-2027) -- {pool(p27)}")
    print(f"-- P(break by end-2028) -- {pool(p28)}")

    summary = {"asof": datetime.date.today().isoformat(), "members": len(members),
               "votes": {k: v for k, v in votes.items()},
               "P_2027": p27, "P_2028": p28}
    (DIR / "_ensemble_summary.json").write_text(json.dumps(summary, indent=1))
    print(f"\nsummary -> {DIR / '_ensemble_summary.json'}")


if __name__ == "__main__":
    main()
