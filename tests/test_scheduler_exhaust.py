"""Framework tests for the scheduler-exhaust channel (desk/scheduler_exhaust.py).

Covers: PanelSpec validation, aggregation semantics (blocked = MISSING, never
zero), newline-safe history append, manual CSV ingest, the book-wide census
artifact, and the knowledge-graph / source-atlas wiring (APPLIES_TO contract).
No network, no browser — the Playwright path is exercised only up to its lazy
import boundary.
"""
import importlib
import json
import pathlib

import pytest

from desk import scheduler_exhaust as se

ROOT = pathlib.Path(__file__).resolve().parents[1]


def make_spec(**overrides):
    kw = dict(
        ticker="TST",
        company="Test Co",
        scheduler_url="https://example.com/book",
        flow_notes="landing -> location -> service -> calendar",
        locations=[{"location_id": "loc1", "label": "One"},
                   {"location_id": "loc2", "label": "Two"}],
        cadence="weekly",
        read_target="unit volume",
        extract=lambda page, loc: {"status": "ok", "days_to_next_slot": 1.0},
    )
    kw.update(overrides)
    return se.PanelSpec(**kw)


# ─────────────────────────────────────────────────────────────────────────────
# PanelSpec validation
# ─────────────────────────────────────────────────────────────────────────────
class TestPanelSpec:
    def test_valid_spec_passes(self):
        assert make_spec().validate().ticker == "TST"

    def test_rejects_non_http_url(self):
        with pytest.raises(ValueError, match="http"):
            make_spec(scheduler_url="ftp://x").validate()

    def test_rejects_empty_locations(self):
        with pytest.raises(ValueError, match="location"):
            make_spec(locations=[]).validate()

    def test_rejects_location_without_id(self):
        with pytest.raises(ValueError, match="location_id"):
            make_spec(locations=[{"label": "no id"}]).validate()

    def test_rejects_duplicate_location_ids(self):
        locs = [{"location_id": "a"}, {"location_id": "a"}]
        with pytest.raises(ValueError, match="duplicate"):
            make_spec(locations=locs).validate()

    def test_rejects_bad_cadence(self):
        with pytest.raises(ValueError, match="cadence"):
            make_spec(cadence="hourly").validate()

    def test_rejects_impolite_pacing(self):
        with pytest.raises(ValueError, match="politeness"):
            make_spec(request_pacing_s=0.1).validate()

    def test_extract_may_be_none_but_browser_sampling_refuses(self):
        spec = make_spec(extract=None)
        spec.validate()  # manual-only instances are legal
        with pytest.raises(ValueError, match="manual"):
            se.sample_panel(spec)


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation — blocked = MISSING, never zero
# ─────────────────────────────────────────────────────────────────────────────
class TestAggregator:
    def test_blocked_is_missing_not_zero(self):
        obs = [
            {"location_id": "a", "status": "ok", "days_to_next_slot": 3.0},
            {"location_id": "b", "status": "blocked"},
            {"location_id": "c", "status": "blocked"},
        ]
        agg = se.aggregate(obs, ticker="T", asof="2026-07-23")
        # if blocked were imputed as 0, the median would be 0.0 — it must stay 3.0
        assert agg["median_days_to_next_slot"] == 3.0
        assert agg["n_blocked"] == 2
        assert agg["n_ok"] == 1

    def test_all_blocked_yields_none_and_missing_quality(self):
        obs = [{"location_id": str(i), "status": "blocked"} for i in range(4)]
        agg = se.aggregate(obs, ticker="T", asof="2026-07-23")
        assert agg["median_days_to_next_slot"] is None
        assert agg["pct_same_day"] is None
        assert agg["pct_within_48h"] is None
        assert agg["pct_booked_out"] is None
        assert agg["sample_quality"] == "MISSING"

    def test_majority_blocked_marks_degraded(self):
        obs = [
            {"location_id": "a", "status": "ok", "days_to_next_slot": 2.0},
            {"location_id": "b", "status": "blocked"},
            {"location_id": "c", "status": "blocked"},
        ]
        agg = se.aggregate(obs, ticker="T", asof="2026-07-23")
        assert agg["sample_quality"] == "DEGRADED"

    def test_no_slots_is_censored_not_averaged(self):
        obs = [
            {"location_id": "a", "status": "ok", "days_to_next_slot": 1.0},
            {"location_id": "b", "status": "no_slots"},
        ]
        agg = se.aggregate(obs, ticker="T", asof="2026-07-23")
        assert agg["median_days_to_next_slot"] == 1.0   # no_slots never enters the median
        assert agg["pct_booked_out"] == 0.5
        assert agg["n_no_slots"] == 1

    def test_ok_without_reading_is_demoted_to_blocked(self):
        # an 'ok' with no number must not become a silent zero
        norm = se.normalize_observation({"location_id": "a", "status": "ok"})
        assert norm["status"] == "blocked"
        assert norm["days_to_next_slot"] is None

    def test_same_day_and_48h_derivation(self):
        obs = [
            {"location_id": "a", "status": "ok", "days_to_next_slot": 0.0},
            {"location_id": "b", "status": "ok", "days_to_next_slot": 1.5},
            {"location_id": "c", "status": "ok", "days_to_next_slot": 5.0},
        ]
        agg = se.aggregate(obs, ticker="T", asof="2026-07-23")
        assert agg["pct_same_day"] == pytest.approx(1 / 3, abs=1e-3)
        assert agg["pct_within_48h"] == pytest.approx(2 / 3, abs=1e-3)

    def test_unknown_status_treated_as_blocked(self):
        norm = se.normalize_observation({"location_id": "a", "status": "weird",
                                         "days_to_next_slot": 4.0})
        assert norm["status"] == "blocked"
        assert norm["days_to_next_slot"] is None

    def test_negative_days_clamped_to_zero_not_dropped(self):
        norm = se.normalize_observation({"location_id": "a", "status": "ok",
                                         "days_to_next_slot": -0.2})
        assert norm["status"] == "ok"
        assert norm["days_to_next_slot"] == 0.0

    def test_confounder_note_travels_with_every_snapshot(self):
        agg = se.aggregate([], ticker="T", asof="2026-07-23")
        assert "hiring_velocity" in agg["confounder"]


# ─────────────────────────────────────────────────────────────────────────────
# History append — newline-safe JSONL
# ─────────────────────────────────────────────────────────────────────────────
class TestHistory:
    def test_append_and_read_roundtrip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(se, "DATA_DIR", tmp_path)
        se.append_history("TST", {"asof": "2026-07-16", "median_days_to_next_slot": 2.0})
        se.append_history("TST", {"asof": "2026-07-23", "median_days_to_next_slot": 2.5})
        hist = se.read_history("TST")
        assert [h["asof"] for h in hist] == ["2026-07-16", "2026-07-23"]

    def test_append_heals_missing_trailing_newline(self, tmp_path, monkeypatch):
        monkeypatch.setattr(se, "DATA_DIR", tmp_path)
        p = tmp_path / "TST_history.jsonl"
        p.write_text('{"asof": "2026-07-09"}')          # crashed writer: no trailing \n
        se.append_history("TST", {"asof": "2026-07-23"})
        lines = [ln for ln in p.read_text().splitlines() if ln.strip()]
        assert len(lines) == 2
        for ln in lines:
            json.loads(ln)                               # no concatenated/garbled line

    def test_record_containing_newline_stays_one_line(self, tmp_path, monkeypatch):
        monkeypatch.setattr(se, "DATA_DIR", tmp_path)
        se.append_history("TST", {"note": "line1\nline2"})
        raw = (tmp_path / "TST_history.jsonl").read_text()
        assert raw.count("\n") == 1                      # exactly the terminator


# ─────────────────────────────────────────────────────────────────────────────
# Manual CSV fallback
# ─────────────────────────────────────────────────────────────────────────────
class TestManualCSV:
    def test_ingest_statuses_and_missing_values(self, tmp_path):
        csv_path = tmp_path / "manual.csv"
        csv_path.write_text(
            "location_id,status,days_to_next_slot,same_day,within_48h,note\n"
            "a,ok,2.0,,,\n"
            "b,no_slots,,,,booked out\n"
            "c,blocked,,,,waf challenge\n")
        obs = se.ingest_manual_csv(csv_path)
        by = {o["location_id"]: o for o in obs}
        assert by["a"]["status"] == "ok" and by["a"]["days_to_next_slot"] == 2.0
        assert by["b"]["status"] == "no_slots" and by["b"]["days_to_next_slot"] is None
        assert by["c"]["status"] == "blocked" and by["c"]["days_to_next_slot"] is None

    def test_run_instance_manual_mode_writes_history(self, tmp_path, monkeypatch):
        monkeypatch.setattr(se, "DATA_DIR", tmp_path)
        csv_path = tmp_path / "manual.csv"
        csv_path.write_text("location_id,status,days_to_next_slot\n"
                            "loc1,ok,1.0\nloc2,blocked,\n")
        rec = se.run_instance(make_spec(), manual_csv=str(csv_path), asof="2026-07-23")
        assert rec["mode"] == "manual"
        assert rec["median_days_to_next_slot"] == 1.0    # blocked contributed nothing
        assert se.read_history("TST")[0]["asof"] == "2026-07-23"


# ─────────────────────────────────────────────────────────────────────────────
# Census artifact + coverage validator
# ─────────────────────────────────────────────────────────────────────────────
REQUIRED_CENSUS_FIELDS = {"ticker", "schedulable", "surface", "url_or_platform",
                          "feasibility", "read_target", "notes"}


class TestCensus:
    def test_candidates_json_parses_with_required_fields(self):
        doc = json.loads((ROOT / "desk/data/scheduler_exhaust/candidates.json").read_text())
        cands = doc["candidates"]
        assert len(cands) >= 300                          # the full book, not a sample
        for c in cands:
            assert REQUIRED_CENSUS_FIELDS <= set(c), c.get("ticker")
            assert c["schedulable"] in ("yes", "no", "indirect"), c["ticker"]
            assert c["feasibility"] in ("A", "B", "C", None), c["ticker"]
            if c["schedulable"] in ("yes", "indirect"):
                assert c["surface"], c["ticker"]
                assert c["feasibility"] in ("A", "B", "C"), c["ticker"]

    def test_live_lab_names_graded_yes_feasibility_a(self):
        doc = json.loads((ROOT / "desk/data/scheduler_exhaust/candidates.json").read_text())
        by = {c["ticker"]: c for c in doc["candidates"]}
        for t in ("DGX", "LH"):
            assert by[t]["schedulable"] == "yes"
            assert by[t]["feasibility"] == "A"
        assert by["CI"]["schedulable"] == "no"            # honest no stays no

    def test_census_meta_carries_the_confounder(self):
        doc = json.loads((ROOT / "desk/data/scheduler_exhaust/candidates.json").read_text())
        assert "hiring_velocity" in doc["_meta"]["confounder"]
        assert "CAPACITY" in doc["_meta"]["confounder"]

    def test_census_gaps_mechanics(self, tmp_path, monkeypatch):
        ledger = tmp_path / "ledger.json"
        cand = tmp_path / "cand.json"
        ledger.write_text(json.dumps(
            {"names": [{"ticker": "AAA"}, {"ticker": "BBB"}]}))
        cand.write_text(json.dumps(
            {"candidates": [{"ticker": "AAA", "schedulable": "no"}]}))
        monkeypatch.setattr(se, "LEDGER_PATH", ledger)
        monkeypatch.setattr(se, "CANDIDATES_PATH", cand)
        assert se.census_gaps() == ["BBB"]                # UNSCREENED flagged, not passed


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge-graph + source-atlas wiring
# ─────────────────────────────────────────────────────────────────────────────
class TestKnowledgeGraphWiring:
    def test_dispatch_index_carries_applies_to(self):
        g = json.loads((ROOT / "knowledge_graph/knowledge_graph.json").read_text())
        entries = [e for e in g["dispatch_index"] if e["name"] == "scheduler_exhaust"]
        assert entries, "scheduler_exhaust missing from dispatch_index"
        a = entries[0]["applies_to"]
        assert a["applies_universally"] is False
        assert a["asset_classes"]
        assert "booking" in a["summary"].lower()
        assert any("hiring_velocity" in c for c in a["confounders"])

    def test_channel_node_present_with_contract(self):
        d = json.loads((ROOT / "knowledge_graph/signal_channels.json").read_text())
        ch = [c for c in d["channels"] if c.get("short_name") == "scheduler_exhaust"]
        assert ch, "scheduler_exhaust channel missing from signal_channels.json"
        ch = ch[0]
        assert "applies_to" in ch and "online booking" in ch["applies_to"]
        assert ch["validation_status"].startswith("PAPER")
        assert ch["latency"] == "leads reported volume 0-1 quarter"
        assert any("hiring_velocity" in c for c in ch["confounders"])
        assert any("spot" in c.lower() for c in ch["confounders"])

    def test_module_applies_to_matches_dispatch_doctrine(self):
        assert se.APPLIES_TO["kind"] == "m_source"
        assert se.APPLIES_TO["applies_universally"] is False
        assert "issuer_features" in se.APPLIES_TO

    def test_source_atlas_registration(self):
        sa = importlib.import_module("verticals.buyside_dd.source_atlas")
        s = sa.source_by_id("scheduler_exhaust")
        assert s is not None
        assert s.attribute == "appointment_availability"
        assert s.is_free
        assert "PAPER" in s.notes
        # Ring-1 alias reconciliation
        assert sa.canonical_attribute("booking_horizon") == "appointment_availability"
        assert sa.canonical_attribute("wait_times") == "appointment_availability"
        # connector shim resolves
        importlib.import_module("verticals.buyside_dd.connectors.scheduler_exhaust")

    def test_recall_floor_rule_fires_narrowly(self):
        sa = importlib.import_module("verticals.buyside_dd.source_atlas")
        booking_claim = {"referent_type": "entity", "predicate": "is_booked_out",
                         "object_value": "clinics fully booked for weeks",
                         "referent_attributes": ["appointment_availability"]}
        assert any(g["feature"] == "booking_slot_utilization"
                   for g in sa.recall_floor_gaps(booking_claim, []))
        # narrow: a generic revenue claim must NOT fire it
        generic = {"referent_type": "entity", "predicate": "reported",
                   "object_value": "revenue grew 12% on pricing",
                   "referent_attributes": ["revenue"]}
        assert not any(g["feature"] == "booking_slot_utilization"
                       for g in sa.recall_floor_gaps(generic, []))
        # co-selection satisfies the floor
        assert not any(g["feature"] == "booking_slot_utilization"
                       for g in sa.recall_floor_gaps(booking_claim, ["scheduler_exhaust"]))
