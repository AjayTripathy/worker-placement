"""desk — the Desk CLI: the consolidated entrypoint that owns all watch scheduling.

  python3 -m desk.desk run [--force]     run DUE watches -> update feed + desk_actionable.json
  python3 -m desk.desk board             print the current actionable board (last 3 days)
  python3 -m desk.desk digest            print the daily digest (for the daily push)
  python3 -m desk.desk install-cron      consolidate: back up crontab, strip old signalos-* lines,
                                         install ONE heartbeat (hourly run) + ONE daily digest
  python3 -m desk.desk show-cron         preview the consolidated crontab without installing

READ-ONLY desk: never places orders. Decisive signals are routed to the SignalOS agent for
read-only verification by the Desk AGENT (see .claude/agents/desk.md), not by this script.
"""
from __future__ import annotations
import sys, json, subprocess, time
from pathlib import Path
from . import runner as RUN, registry as R

HERE = Path(__file__).resolve().parent
PY = sys.executable or "/usr/bin/python3"
TAG = "signalos-desk"


def _fmt(sigs):
    if not sigs:
        return "  (nothing actionable)"
    by = {}
    for s in sigs:
        by.setdefault(s.get("asset_class") or "other", []).append(s)
    lines = []
    for ac, group in sorted(by.items()):
        lines.append(f"  — {ac} —")
        for s in sorted(group, key=lambda x: x["severity"]):
            v = " [VERIFY]" if s.get("needs_verification") else ""
            lines.append(f"    [{s['severity']}] {s['source']}:{s['asset']} {s['signal_type']}{v}")
            lines.append(f"        {s['evidence'][:120]}")
    return "\n".join(lines)


def cmd_run(force=False):
    p = RUN.run(force=force)
    print(f"=== DESK RUN {p['asof']} ===  ran={p['ran']} fresh={p['n_fresh']} push={len(p['push'])} verify={len(p['to_verify'])}")
    if p["push"]:
        print(">>> PUSH (surface now):")
        print(_fmt(p["push"]))
    if p["to_verify"]:
        print(">>> AUTO-VERIFY QUEUE (Desk agent -> SignalOS read-only):")
        for s in p["to_verify"]:
            print(f"    {s['source']}:{s['asset']} — {s['evidence'][:90]}")
    _print_coverage(p.get("coverage"))


def _print_coverage(cov):
    if not cov or cov.get("error"):
        return
    thin, gaps = cov.get("thin", []), cov.get("gaps", [])
    if thin or gaps:
        print(">>> COVERAGE (desk maintenance — under-covered book names):")
        if thin:
            print(f"    THIN (no detector): {', '.join(thin)}")
        for g in gaps:
            print(f"    GAP {g['ticker']}: SIC implies {', '.join(g['missing'])} — confirm & tag")


def cmd_board():
    b = RUN.board(days=3)
    print(f"=== DESK BOARD (actionable, last 3d) — {len(b)} signals ===")
    print(_fmt(b))


def cmd_digest():
    b = RUN.board(days=1)
    print(f"=== DESK DAILY DIGEST {time.strftime('%Y-%m-%d')} — {len(b)} actionable ===")
    print(_fmt(b))
    try:
        from . import coverage as COV
        _print_coverage({k: v for k, v in COV.audit(use_network=False).items() if k in ("thin", "gaps")})
    except Exception:
        pass
    print("\n(verify-flagged signals are auto-checked by the Desk agent before you act; READ-ONLY)")


def _consolidated_crontab() -> str:
    try:
        cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    except Exception:
        cur = ""
    kept = [l for l in cur.splitlines() if l.strip() and "signalos-" not in l]   # strip ALL old signalos crons
    root = str(R.ROOT)
    kept.append(f"# {TAG}: consolidated watch heartbeat (registry gates cadence)")
    kept.append(f"30 * * * 1-5 cd {root} && {PY} -m desk.desk run >> {root}/desk/data/desk_cron.out 2>&1 # {TAG}")
    kept.append(f"45 13 * * 1-5 cd {root} && {PY} -m desk.desk digest >> {root}/desk/data/desk_digest.out 2>&1 # {TAG}")
    return "\n".join(kept) + "\n"


def cmd_show_cron():
    print(_consolidated_crontab())


def cmd_install_cron():
    new = _consolidated_crontab()
    bak = HERE / "data" / f"crontab_backup_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        old = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    except Exception:
        old = ""
    bak.write_text(old)
    subprocess.run(["crontab", "-"], input=new, text=True, check=True)
    print(f"installed consolidated crontab (backup -> {bak.name}). Old signalos-* entries removed; now:")
    print(new)


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "run"
    if a == "run":
        cmd_run(force=("--force" in sys.argv))
    elif a == "board":
        cmd_board()
    elif a == "digest":
        cmd_digest()
    elif a == "show-cron":
        cmd_show_cron()
    elif a == "install-cron":
        cmd_install_cron()
    else:
        print(__doc__)
