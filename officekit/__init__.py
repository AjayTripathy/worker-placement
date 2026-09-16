"""officekit — the family-office engine, extracted from the desk as a product package.

Phase 0 of productization (2026-09-02): the OFFICE dashboard + DISASTER planner engine,
de-personalized. Everything account-specific lives in the balance-sheet JSON (see
officekit.schema); the package holds only the model, the scenario/mitigation libraries,
the effects registry, and the two renderers.

Pipeline:  data dict (schema.validate) -> build_model() -> render_office()/render_disaster()

The desk's own tabs run through thin wrappers in desk/household.py and desk/scenario_planner.py;
tests/test_officekit.py holds the golden byte-parity proof against the pre-extraction
renderers plus a generic-client smoke test (no personal strings leak from the package).
READ-ONLY: nothing in here places orders.
"""
from officekit.schema import load_balance_sheet, validate
from officekit.model import build_model, fmt_usd
from officekit.render_office import render_office
from officekit.render_scenarios import render_scenarios, render_disaster
from officekit.render_strategies import render_strategies
from officekit.intake import build_from_answers

__all__ = ["load_balance_sheet", "validate", "build_model", "fmt_usd",
           "render_office", "render_scenarios", "render_strategies", "render_disaster", "build_from_answers"]
