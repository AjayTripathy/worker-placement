"""DEPRECATED location. The desk's detector/generator fleet migrated to
`officekit_signals.fleet` (2026-09-10, desk-deprecation: the app is the product,
the machinery lives in the officekit registries). Kept as a thin re-export so
`desk.household` and any other desk-era importer keeps working during the
wind-down — importing this still registers the full fleet (idempotent). New work
registers in officekit_signals, never here.
"""
from officekit_signals.fleet import *          # noqa: F401,F403 — re-export + register
from officekit_signals.fleet import register_generators, N_GENERATORS  # noqa: F401
