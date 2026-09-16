# REGISTRY PATCH — scheduler_exhaust weekly cron

**Do not auto-apply.** `desk/registry.py` is another lane's file this session; the main
session applies this AFTER the lab-panel agent lands `desk/lab_scheduler_panel.py`
(the framework discovers instances from it — until then `--sample-all` is a no-op
that prints "no instances registered" and exits cleanly, so applying early is safe
but pointless).

## The exact WatchSpec dict to append to `WATCHES` in `desk/registry.py`

```python
    {"name": "scheduler_exhaust", "cmd": ["python3", "-m", "desk.scheduler_exhaust", "--sample-all"],
     "cadence": "weekly", "log": "desk/data/scheduler_exhaust/cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "booking-slot scarcity panels (days-to-next-available / %same-day / booking-horizon) "
             "over fixed location panels -> leading read on reported volume, 0-1q latency. "
             "Instance #1 = DGX/LH lab panel (desk/lab_scheduler_panel.py). PAPER status: "
             "Q2-2026 frozen calls grade at the October Q3 prints; no sizing use before "
             "graduation. blocked=MISSING never zero; >40% blocked marks snapshot DEGRADED. "
             "CONFOUNDER: capacity-vs-demand -> cross-check hiring_velocity. "
             "History: desk/data/scheduler_exhaust/<ticker>_history.jsonl. Built 2026-07-23."},
```

## Notes for the applier

- **`"enabled": True` is explicit and load-bearing.** On 2026-07-22 the desk found
  silently-dead crons whose entries were missing this flag — the runner skipped them
  without any error. Do not strip it; do not rely on a default.
- Cadence is **weekly** on purpose: the channel reads a slowly-moving quarterly
  quantity and spot-vs-average sampling is a named confounder — the framework wants
  a fixed weekly sampling slot, not a tighter loop. Keep the cron's day/hour stable
  for the same reason (spot-sample comparability across snapshots).
- The command samples every registered instance; per-instance failures print
  `SAMPLE FAILED ... snapshot MISSING, not zero` and do not abort the sweep.
- If a target starts hard-blocking the browser path, the fallback is
  `python3 -m desk.scheduler_exhaust --manual <TICKER> <CSV>` (columns:
  `location_id,status[,days_to_next_slot,same_day,within_48h,note]`).
- Coverage validator (run ad hoc or fold into consistency_check later):
  `python3 -m desk.scheduler_exhaust --census-gaps` — flags research-ledger names
  not graded in `candidates.json` (UNSCREENED != CLEAR).
