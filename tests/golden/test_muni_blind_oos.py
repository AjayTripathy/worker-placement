"""Golden-master characterization test for the muni_credit blind-OOS analyzer.

Freezes the deterministic output of blind_oos_analyzer.py (the dispositive
overfit test, 2016-19 blind universe) so extracting core/firewall.py and
redirecting muni's parallel confusion-matrix reimplementation can prove it
changed no number. The output JSON carries no absolute paths or timestamps, so
we regenerate and assert byte-identical against the golden copy.

Usage:
    python3 tests/golden/test_muni_blind_oos.py            # check (exit 1 on drift)
    python3 tests/golden/test_muni_blind_oos.py --update   # recapture golden
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "verticals/muni_credit/blind_oos_analyzer.py"
OUTPUT = ROOT / "verticals/muni_credit/outputs/blind_oos_results.json"
GOLDEN = Path(__file__).resolve().parent / "muni_credit" / "blind_oos_results.json"


def regenerate() -> None:
    r = subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.stderr.write(f"\nblind_oos_analyzer.py FAILED (exit {r.returncode}):\n{r.stderr}\n")
        sys.exit(2)


def update() -> None:
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    regenerate()
    GOLDEN.write_bytes(OUTPUT.read_bytes())
    print(f"  captured {GOLDEN.relative_to(ROOT)}")


def check() -> int:
    if not GOLDEN.exists():
        sys.stderr.write("No golden master. Run with --update first.\n")
        return 2
    regenerate()
    if OUTPUT.read_bytes() == GOLDEN.read_bytes():
        print("  [ok] blind_oos_results.json")
        print("\nGolden master intact — muni blind-OOS output byte-identical.")
        return 0
    sys.stderr.write(
        "\n  [DRIFT] blind_oos_results.json\n"
        "The refactor changed a number the blind-OOS test depends on. Investigate\n"
        "before committing; if intended, re-run with --update.\n"
    )
    return 1


def main() -> None:
    if "--update" in sys.argv:
        update()
    else:
        sys.exit(check())


if __name__ == "__main__":
    main()
