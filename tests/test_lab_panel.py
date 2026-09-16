"""lab_scheduler_panel invariants: panel shape, aggregator missing-data contract, history append,
registry wiring (the enabled-flag bug), manual-mode ingestion."""
import datetime as dt
import json

import pytest

from desk import lab_scheduler_panel as lp


# ------------------------------------------------------------------------------------ panel ----

def test_panel_parses_with_required_fields(root):
    cfg = json.loads((root / "desk" / "data" / "lab_panel" / "panel.json").read_text())
    assert set(cfg["companies"]) == {"quest", "labcorp"}
    assert len(cfg["metros"]) == 12
    for m in cfg["metros"]:
        for field in ("metro", "zip", "lat", "lon"):
            assert field in m, f"metro entry missing {field}: {m}"
        assert len(m["zip"]) == 5 and m["zip"].isdigit()
        assert 24 < m["lat"] < 50 and -125 < m["lon"] < -66   # continental US sanity
    assert len({m["metro"] for m in cfg["metros"]}) == 12     # no dupes


def test_load_panel_expands_to_24_locations():
    locs = lp.load_panel()
    assert len(locs) == 24
    assert sum(1 for x in locs if x["company"] == "quest") == 12
    assert sum(1 for x in locs if x["company"] == "labcorp") == 12
    for x in locs:
        assert x["zip"] and isinstance(x["lat"], float) and isinstance(x["lon"], float)


# -------------------------------------------------------------------------------- aggregator ----

ASOF = dt.datetime(2026, 7, 23, 9, 0, 0)


def _row(company, metro, status, days=None, **kw):
    r = {"company": company, "metro": metro, "zip": "00000", "status": status}
    if days is not None:
        r["days_to_next_slot"] = days
    r.update(kw)
    return r


def test_aggregate_median_over_ok_only_never_imputes_blocked_as_zero():
    rows = [
        _row("quest", "NYC", "ok", 1.0),
        _row("quest", "LA", "ok", 5.0),
        _row("quest", "CHI", "ok", 3.0),
        _row("quest", "HOU", "blocked"),
        _row("quest", "PHX", "blocked"),
    ]
    a = lp.aggregate(rows, ASOF)["quest"]
    # median of {1,3,5} = 3; if blocked were imputed as 0 the median would drop to 1
    assert a["median_days_to_next_slot"] == 3.0
    assert a["n_ok"] == 3 and a["n_blocked"] == 2 and a["n_no_slots"] == 0


def test_aggregate_no_slots_right_censored_not_zero_not_in_median():
    rows = [
        _row("labcorp", "NYC", "ok", 2.0),
        _row("labcorp", "LA", "no_slots"),
        _row("labcorp", "CHI", "ok", 4.0),
    ]
    a = lp.aggregate(rows, ASOF)["labcorp"]
    assert a["median_days_to_next_slot"] == 3.0    # mean(2,4) midpoint; no_slots excluded
    assert a["n_no_slots"] == 1
    assert a["pct_same_day"] == 0.0


def test_aggregate_all_blocked_yields_none_not_zero():
    rows = [_row("quest", m, "blocked") for m in ("NYC", "LA", "CHI")]
    a = lp.aggregate(rows, ASOF)["quest"]
    assert a["median_days_to_next_slot"] is None
    assert a["pct_same_day"] is None and a["pct_within_48h"] is None
    assert a["n_blocked"] == 3 and a["n_ok"] == 0


def test_aggregate_same_day_and_48h_percentages():
    rows = [
        _row("quest", "NYC", "ok", 0.0),   # same-day
        _row("quest", "LA", "ok", 2.0),    # within 48h
        _row("quest", "CHI", "ok", 7.0),   # neither
        _row("quest", "HOU", "error"),     # excluded from percentages entirely
    ]
    a = lp.aggregate(rows, ASOF)["quest"]
    assert a["pct_same_day"] == pytest.approx(33.3, abs=0.1)
    assert a["pct_within_48h"] == pytest.approx(66.7, abs=0.1)
    assert a["n_error"] == 1


def test_aggregate_walkin_wait_median_quest_only():
    rows = [
        _row("quest", "NYC", "ok", 1.0, walkin_wait_min=3),
        _row("quest", "LA", "ok", 2.0, walkin_wait_min=11),
        _row("quest", "CHI", "no_slots", walkin_wait_min=8),   # wait known even when booked out
        _row("quest", "PHX", "no_coverage", walkin_wait_min=1),  # JV site: excluded from median
        _row("labcorp", "NYC", "ok", 1.0),
    ]
    a = lp.aggregate(rows, ASOF)
    assert a["quest"]["median_walkin_wait_min"] == 8       # median(3,11,8); JV wait excluded
    assert a["quest"]["n_no_coverage"] == 1
    assert "median_walkin_wait_min" not in a["labcorp"]


def test_aggregate_no_coverage_is_not_error_not_zero():
    rows = [
        _row("quest", "PHX", "no_coverage"),
        _row("quest", "NYC", "ok", 4.0),
    ]
    a = lp.aggregate(rows, ASOF)["quest"]
    assert a["n_no_coverage"] == 1 and a["n_error"] == 0
    assert a["median_days_to_next_slot"] == 4.0            # not dragged toward zero


def test_days_to_slot_calendar_semantics():
    assert lp.days_to_slot("2026-07-23T15:40", ASOF) == 0.0     # later today = same-day
    assert lp.days_to_slot("2026-07-25T07:00:00", ASOF) == 2.0
    assert lp.days_to_slot("2026-08-06", ASOF) == 14.0          # bare date accepted


# ----------------------------------------------------------------------------------- history ----

def test_append_history_newline_safe(tmp_path):
    p = tmp_path / "history.jsonl"
    lp.append_history({"a": 1}, path=p)
    lp.append_history({"b": 2}, path=p)
    # simulate a previous writer that left no trailing newline
    with open(p, "a") as f:
        f.write(json.dumps({"c": 3}))
    lp.append_history({"d": 4}, path=p)
    lines = p.read_text().splitlines()
    assert [json.loads(x) for x in lines] == [{"a": 1}, {"b": 2}, {"c": 3}, {"d": 4}]
    assert p.read_text().endswith("\n")


def test_append_history_creates_parent(tmp_path):
    p = tmp_path / "sub" / "dir" / "h.jsonl"
    lp.append_history({"x": 1}, path=p)
    assert json.loads(p.read_text()) == {"x": 1}


# ------------------------------------------------------------------------------ manual mode ----

def test_manual_csv_ingestion(tmp_path, monkeypatch):
    csvp = tmp_path / "hand.csv"
    csvp.write_text(
        "company,metro,zip,next_slot_iso,status,site\n"
        "quest,NYC,10016,2026-07-24T08:00:00,ok,268 3rd Ave\n"
        "quest,LA,90017,,blocked,\n"
        "labcorp,NYC,10016,2026-07-23,ok,115 E 57th St\n"
        "labcorp,LA,90017,,no_slots,\n"
        "quest,CHI,60614,,ok,\n"          # ok without a slot -> becomes error, not silent zero
    )
    hist = tmp_path / "hist.jsonl"
    monkeypatch.setattr(lp, "HISTORY", hist)
    rec = lp.run_manual(str(csvp))
    assert rec["source"] == "manual"
    q = rec["per_company"]["quest"]
    assert q["n_ok"] == 1 and q["n_blocked"] == 1 and q["n_error"] == 1
    lc = rec["per_company"]["labcorp"]
    assert lc["n_ok"] == 1 and lc["n_no_slots"] == 1
    assert lc["pct_same_day"] == 100.0
    # history got exactly one parseable line
    assert json.loads(hist.read_text().strip())["source"] == "manual"


# --------------------------------------------------------------------------------- registry ----

def test_registry_entry_enabled_weekly():
    """The 2026-07-22 bug class: a watch without enabled=True is silently never dispatched."""
    from desk import registry
    w = [x for x in registry.WATCHES if x["name"] == "lab_scheduler_panel"]
    assert len(w) == 1, "lab_scheduler_panel missing from desk registry"
    w = w[0]
    assert w.get("enabled") is True
    assert w["cadence"] == "weekly"
    assert w["log"] == "desk/data/lab_panel_cron.out"
    assert w["cmd"] == ["python3", "-m", "desk.lab_scheduler_panel"]


# -------------------------------------------------------------------------- parser fixtures ----

def _qsite(code, name, grid, sched=True, wait=None):
    s = {"siteCode": code, "name": name, "scheduleAppt": sched, "availability": grid}
    if wait is not None:
        s["waitTime"] = wait
    return s


GRID_JUL28 = [
    {"date": "2026-07-23", "slots": []},
    {"date": "2026-07-24", "slots": []},
    {"date": "2026-07-28", "slots": [{"time": "13:20", "available": True},
                                     {"time": "11:00", "available": False}]},
]
GRID_EMPTY = [{"date": "2026-07-23", "slots": []}, {"date": "2026-07-24", "slots": []}]
GRID_TODAY = [{"date": "2026-07-23", "slots": [{"time": "09:00", "available": True}]}]


def test_quest_site_reader_first_slot_and_censoring():
    site = _qsite("CQN", "Quest - Good Sam", GRID_JUL28, wait=1)
    assert lp._quest_first_slot(site) == "2026-07-28T13:20"
    out = lp._quest_read_sites({"data": [site]}, ASOF)
    assert out["status"] == "ok"
    assert out["days_to_next_slot"] == 5.0
    assert out["walkin_wait_min"] == 1
    # ALL nearest grids empty = right-censored no_slots (real scarcity), never zero
    out2 = lp._quest_read_sites({"data": [_qsite("X", "Booked Out", GRID_EMPTY)]}, ASOF)
    assert out2["status"] == "no_slots"
    assert "days_to_next_slot" not in out2


def test_quest_site_reader_dead_record_skipped_not_scarcity():
    """The CHI 'Blackhawk' case: a stale duplicate with an empty grid sits nearest; the live twin
    next to it has slots.  Primary must skip the dead record, not report 14d booked-out."""
    dead = _qsite("ANWE", "Quest Diagnostics - Blackhawk", GRID_EMPTY)
    live = _qsite("XYX", "Quest Diagnostics - Blackhawk ", GRID_TODAY, wait=0)
    out = lp._quest_read_sites({"data": [dead, live]}, ASOF)
    assert out["status"] == "ok"
    assert out["site_id"] == "XYX"
    assert out["days_to_next_slot"] == 0.0
    assert out["dead_sites_skipped"] == 1


def test_quest_site_reader_no_coverage_structural():
    """The PHX case: Sonora Quest JV sites carry scheduleAppt=False -> no_coverage, distinct from
    scarcity; availability=None on all bookable sites is also no_coverage."""
    jv = _qsite("BX5", "Sonora Quest Laboratories - Camelback", GRID_EMPTY, sched=False)
    out = lp._quest_read_sites({"data": [jv]}, ASOF)
    assert out["status"] == "no_coverage"
    assert "Sonora" in out["detail"]
    out2 = lp._quest_read_sites({"data": [_qsite("Y", "No Grid", None)]}, ASOF)
    assert out2["status"] == "no_coverage"
    assert lp._quest_read_sites({"data": []}, ASOF)["status"] == "no_coverage"
