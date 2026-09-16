"""scenario_planner — the Scenario Planner. Renders scenarios.html (the 'scenarios' tab).
Renamed from desk/disaster.py (principal-ratified 2026-09-02).

Born 2026-07-10 (user); 2026-09-02 Phase-0 productization: the ENGINE (scenarios,
mitigation menu, effects dispatch, renderer) moved to the officekit package —
byte-parity proven in tests/test_officekit.py. This module is the desk binding:
it runs on desk.household.load_model() — the SAME augmented balance sheet the
dashboard uses (incl. the auto-updating tax reserve), so the two never drift.

    python3 -m desk.scenario_planner   # -> desk/ui/static/scenarios.html
READ-ONLY. Scenario shocks are CALIBRATED estimates; betas are first-pass.
"""
from __future__ import annotations

from pathlib import Path

from officekit import render_scenarios
from desk.household import load_model

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desk" / "ui" / "static" / "scenarios.html"


def build():
    return render_scenarios(load_model(), effects_label="desk/effects.py")


def main():
    OUT.write_text(build())
    print(f"[scenario_planner] rendered -> {OUT}")


if __name__ == "__main__":
    main()
