"""scheduler_exhaust — booking-slot scarcity as a leading utilization read.

Primary data source: the subject business's own online appointment/reservation
scheduler (booking widget / check-in / reservation calendar), sampled over a
FIXED panel of locations at a fixed weekday/hour.

Mechanism: businesses that take public appointments leak utilization through slot
scarcity — days-to-next-available, %-same-day, booking-horizon depth — a LEADING
read on reported volume with 0-1 quarter latency. Operational physical quantity,
hard to fake, free to observe, too niche for alt-data vendors to productize.

CONFOUNDER: slot scarcity conflates demand with CAPACITY (staffing up shortens
waits while volume rises) — cross-check hiring_velocity before reading a scarcity
move as a volume move. Also spot-vs-average sampling: fixed sampling slot, trends
over snapshots only.

This is a THIN SHIM: the framework (PanelSpec, Playwright harness with the
realistic-Chrome fingerprint, blocked=MISSING aggregation, per-instance JSONL
history, --manual CSV fallback) lives in desk/scheduler_exhaust.py so panel
instances stay next to the desk's watch loop. The shim exists so the knowledge
graph's connector walk and the source atlas's connector_module resolution both
see the channel through their normal pattern.

STATUS: PAPER — calibration seed = DGX/LH Q2-2026 frozen calls; graduates only if
it beats consensus through the Q3-2026 prints (October). Instance #1 = the
Quest/Labcorp lab-appointment panel (desk/lab_scheduler_panel.py).
Applicability census (the APPLIES_TO surface over the book):
desk/data/scheduler_exhaust/candidates.json — UNSCREENED != CLEAR.
"""
from __future__ import annotations

from desk.scheduler_exhaust import (   # noqa: F401  (re-exported framework surface)
    APPLIES_TO,
    CONFOUNDER_NOTE,
    PanelSpec,
    aggregate,
    append_history,
    census_gaps,
    ingest_manual_csv,
    load_instances,
    normalize_observation,
    read_history,
    register_instance,
    run_instance,
    sample_panel,
)
