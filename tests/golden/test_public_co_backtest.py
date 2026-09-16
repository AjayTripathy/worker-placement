"""Golden-master characterization test for the public_co survivorship backtest.

Freezes the deterministic outputs of the May-2025 survivorship backtest so a
later refactor (extracting core/control_suite.py, etc.) can prove it changed
*nothing* the numbers depend on. The three scripts emit JSON with no absolute
paths or timestamps, so we regenerate and assert byte-identical against the
golden copies under tests/golden/public_co/.

This is a characterization test, not a correctness test: it pins current
behavior, whatever it is. The numbers it guards (LOOSE_LONG +64.6%, placebo
%ile 99.91 / z=+3.36, det-screen ablation +15.4%) were verified green at
commit 9481bb3 before the core/ refactor began.

Usage:
    python3 tests/golden/test_public_co_backtest.py            # check (exit 1 on drift)
    python3 tests/golden/test_public_co_backtest.py --update   # recapture golden
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKTEST = ROOT / "verticals/public_co/data/_backtest/survivorship_2025_05"
GOLDEN = Path(__file__).resolve().parent / "public_co"

# (script, output file it writes). Order matters: synthesize.py writes
# synthesis.json, which both tier1 scripts read.
PIPELINE = [
    ("synthesize.py", "synthesis.json"),
    ("tier1_test_A_ablation.py", "tier1_test_A_results.json"),
    ("tier1_test_B_placebo.py", "tier1_test_B_results.json"),
]


def regenerate() -> None:
    for script, _ in PIPELINE:
        r = subprocess.run(
            [sys.executable, str(BACKTEST / script)],
            cwd=ROOT, capture_output=True, text=True,
        )
        if r.returncode != 0:
            sys.stderr.write(f"\n{script} FAILED (exit {r.returncode}):\n{r.stderr}\n")
            sys.exit(2)


def update() -> None:
    GOLDEN.mkdir(parents=True, exist_ok=True)
    regenerate()
    for _, out in PIPELINE:
        (GOLDEN / out).write_bytes((BACKTEST / out).read_bytes())
        print(f"  captured {out}")
    print(f"\nGolden master written to {GOLDEN.relative_to(ROOT)}")


def check() -> int:
    if not GOLDEN.exists():
        sys.stderr.write("No golden master. Run with --update first.\n")
        return 2
    regenerate()
    drift = []
    for _, out in PIPELINE:
        got = (BACKTEST / out).read_bytes()
        want = (GOLDEN / out).read_bytes()
        status = "ok" if got == want else "DRIFT"
        print(f"  [{status}] {out}")
        if got != want:
            drift.append(out)
    if drift:
        sys.stderr.write(
            f"\nGOLDEN-MASTER DRIFT in {len(drift)} file(s): {', '.join(drift)}\n"
            "The refactor changed a number the backtest depends on. Investigate\n"
            "before committing; if the change is intended, re-run with --update.\n"
        )
        return 1
    print("\nGolden master intact — backtest outputs byte-identical.")
    return 0


def main() -> None:
    if "--update" in sys.argv:
        update()
    else:
        sys.exit(check())


if __name__ == "__main__":
    main()
