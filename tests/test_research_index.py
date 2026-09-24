"""The research index: keyed by contributor / agent + intelligence / strategy,
and made gradeable by append-only, sourced outcomes."""
import json
import sqlite3
from datetime import date

import pytest

from officekit.migration import safe_path
from officekit_ai.general_court import run_general_court
from officekit_research import cases, general, index
from test_officekit_strategy_proposals import Provider, clients
from test_contextual_research import proposal, execute, sources, donor  # noqa: F401 (fixture)

SOURCE = "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/filing.htm"


def test_every_kind_of_research_lands_in_one_keyed_view(donor, tmp_path):
    folder, p, bundle, _ = donor
    recipient = tmp_path / "recipient"
    _, rp = proposal(recipient)
    cases.import_bundle(recipient, bundle)
    rp, _ = execute(recipient, rp)
    rows = index.query(recipient, symbol="VDC")
    kinds = {r["kind"] for r in rows}
    assert kinds == {"general", "ruling", "case"}
    ruling = next(r for r in rows if r["kind"] == "ruling")
    assert ruling["strategy"] == "deploy_powder" and ruling["contributor"] == "self"
    assert ruling["general_id"] == next(r for r in rows if r["kind"] == "general")["id"]     # ruling -> the research it stands on
    assert ruling["adjudicate_model"] == "test-opus" and ruling["adjudicate_tier"] == 2
    assert ruling["protocol_hash"] and ruling["outcome_label"] == "OWN"
    imported = next(r for r in rows if r["kind"] == "case")
    assert imported["origin"] == "imported" and imported["contributor"] is None   # no identity in a shared case, by design
    assert imported["horizon"] == "over_7y" and imported["country"] == "US"
    # keyed access
    assert {r["kind"] for r in index.query(recipient, strategy="deploy_powder")} == {"ruling", "case"}
    assert index.query(recipient, symbol="VDC", minimum_tier=3) == []              # nothing was adjudicated at the top tier
    db = sqlite3.connect(index.index_path(recipient))
    assert {row[0] for row in db.execute("SELECT factor FROM factor_exposure")} == {"equity", "sector_concentration"}


def test_the_index_is_derived_and_only_outcomes_are_durable(tmp_path):
    record, _ = run_general_court("VDC", "etf", {}, tmp_path, clients=clients(Provider()))
    index.resolve(tmp_path, record["id"] + ":0", True, SOURCE)
    first = index.query(tmp_path)
    index.index_path(tmp_path).unlink()
    assert index.query(tmp_path) == first                                  # rebuilt from the office's files
    assert not safe_path("research/index.sqlite")                          # never migrated
    assert safe_path("research/outcomes.jsonl")                            # the durable record is
    assert safe_path("research/general/" + record["id"] + ".json")


def test_outcomes_are_sourced_append_only_and_cannot_predate_the_forecast(tmp_path):
    record, _ = run_general_court("VDC", "etf", {}, tmp_path, clients=clients(Provider()))
    fid = record["id"] + ":0"
    with pytest.raises(ValueError):
        index.resolve(tmp_path, fid, True, "http://insecure.example/x")          # needs a public HTTPS locator
    with pytest.raises(ValueError, match="Unknown forecast"):
        index.resolve(tmp_path, record["id"] + ":9", True, SOURCE)
    with pytest.raises(ValueError, match="before it was made"):
        index.resolve(tmp_path, fid, True, SOURCE, resolved_at="2020-01-01T00:00:00+00:00")
    index.resolve(tmp_path, fid, True, SOURCE)
    index.resolve(tmp_path, fid, False, SOURCE, note="Corrected after the restated filing")
    lines = index.outcomes_path(tmp_path).read_text().splitlines()
    assert len(lines) == 2                                                  # the mistake stays on the record
    assert index.load_outcomes(tmp_path)[fid]["outcome"] is False           # the correction governs


def _seed_forecasts(folder, n, probability, base_rate, outcomes):
    """n general records with one forecast each, resolved as given."""
    class Forecaster(Provider):
        def create(self, **kw):
            response = super().create(**kw)
            if "factor_profile" in kw["output_config"]["format"]["schema"]["properties"]:
                out = json.loads(response.content[0].text)
                out["forecasts"] = [dict(statement="Annual revenue rises.", probability=probability,
                                         base_rate=base_rate, resolve_by="2027-06-30")]
                response.content[0].text = json.dumps(out)
            return response
    for i in range(n):
        record, _ = run_general_court(f"T{i:03d}", "stock", {}, folder, clients=clients(Forecaster()))
        index.resolve(folder, record["id"] + ":0", outcomes[i], SOURCE)


def test_skill_is_suppressed_until_there_are_enough_resolutions(tmp_path):
    _seed_forecasts(tmp_path, 5, 0.9, 0.85, [True] * 5)
    row = index.scoreboard(tmp_path, "adjudicate_model")[0]
    assert row["resolved"] == 5 and row["brier"] is not None
    assert row["skill_vs_base_rate"] is None and "needs 20" in row["note"]   # five forecasts are noise, not knowledge


def test_always_yes_in_a_lopsided_category_earns_no_skill(tmp_path):
    # 90% of these events happen. A forecaster who just says 0.9 every time is
    # quoting climatology: a coin benchmark would flatter them; the base rate does not.
    outcomes = [True] * 18 + [False] * 2
    _seed_forecasts(tmp_path, 20, 0.9, 0.9, outcomes)
    row = index.scoreboard(tmp_path, "adjudicate_model")[0]
    assert row["resolved"] == 20 and row["brier"] == row["brier_base_rate"]
    assert row["skill_vs_base_rate"] == 0.0
    coin = sum((0.5 - o) ** 2 for o in outcomes) / 20
    assert row["brier"] < coin                                               # ...which is exactly why a coin is the wrong benchmark


def test_real_discrimination_shows_as_positive_skill(tmp_path):
    class Sharp(Provider):
        n = 0
        def create(self, **kw):
            response = super().create(**kw)
            if "factor_profile" in kw["output_config"]["format"]["schema"]["properties"]:
                out = json.loads(response.content[0].text)
                hit = Sharp.n % 2 == 0
                Sharp.n += 1
                out["forecasts"] = [dict(statement="Guidance is met.", probability=0.85 if hit else 0.15,
                                         base_rate=0.5, resolve_by="2027-06-30")]
                response.content[0].text = json.dumps(out)
            return response
    for i in range(20):
        record, _ = run_general_court(f"S{i:03d}", "stock", {}, tmp_path, clients=clients(Sharp()))
        index.resolve(tmp_path, record["id"] + ":0", i % 2 == 0, SOURCE)
    row = index.scoreboard(tmp_path, "adjudicate_tier")[0]
    assert row["adjudicate_tier"] == 2 and row["skill_vs_base_rate"] > 0.8


def test_overdue_forecasts_are_counted_not_hidden(tmp_path):
    record, _ = run_general_court("VDC", "etf", {}, tmp_path, clients=clients(Provider()))
    row = index.scoreboard(tmp_path, "symbol", today=date(2028, 1, 1))[0]
    assert row["forecasts"] == 1 and row["resolved"] == 0 and row["overdue_unresolved"] == 1


def test_grouping_is_an_allowlist(tmp_path):
    with pytest.raises(ValueError):
        index.scoreboard(tmp_path, "id; DROP TABLE research")
