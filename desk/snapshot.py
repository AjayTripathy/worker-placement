"""snapshot — daily dated copies of the irreplaceable stores (the calibration ledger IS the skill
record; append-only and unrecoverable if clobbered). Also trims server logs. Idempotent per day.

  python3 -m desk.snapshot
"""
from __future__ import annotations
import datetime, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "desk" / "data" / "snapshots"
KEEP_DAYS = 30
STORES = [
    ROOT / "desk" / "data" / "calibration_ledger.jsonl",
    ROOT / "desk" / "data" / "research_ledger.json",
    ROOT / "desk" / "data" / "entry_plan.json",
    ROOT / "desk" / "data" / "catalyst_predictions.json",
]
DIRS = [ROOT / "desk" / "data" / "edge_classifications"]
LOG_CAP = 5 * 1024 * 1024


def main():
    today = datetime.date.today().isoformat()
    dest = SNAP / today
    if not dest.exists():
        dest.mkdir(parents=True)
        for f in STORES:
            if f.exists():
                shutil.copy2(f, dest / f.name)
        for d in DIRS:
            if d.exists():
                shutil.copytree(d, dest / d.name)
        print(f"snapshot: {today} written ({sum(1 for _ in dest.rglob('*') if _.is_file())} files)")
    else:
        print(f"snapshot: {today} already exists — idempotent no-op")
    # retention
    for old in sorted(SNAP.iterdir()):
        if old.is_dir() and old.name < (datetime.date.today() - datetime.timedelta(days=KEEP_DAYS)).isoformat():
            shutil.rmtree(old)
    # log trim (keep the tail)
    for lg in (ROOT / "logs").glob("*.log"):
        if lg.stat().st_size > LOG_CAP:
            data = lg.read_bytes()[-LOG_CAP // 2:]
            lg.write_bytes(data)
            print(f"trimmed {lg.name}")


if __name__ == "__main__":
    main()
