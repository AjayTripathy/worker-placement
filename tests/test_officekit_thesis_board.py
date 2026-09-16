"""thesis_board — office-native assembly of thesis sleeves (court adjudications +
positions), the desk-import transition, and the merge. Cuts the last desk/data read."""
import json
from pathlib import Path

from officekit import thesis_board as TB


def _office(tmp_path, rows):
    (tmp_path / "answers.json").write_text(json.dumps(
        {"as_of": "2026-09-11", "positions": {"account": "b", "rows": rows}}))


def test_from_adjudications_groups_by_strategy(tmp_path):
    _office(tmp_path, [{"symbol": "AAPL", "value": 5000}, {"symbol": "MSFT", "value": 3000}])
    (tmp_path / "adjudications.jsonl").write_text(
        json.dumps({"strategy": "ai_quality", "symbol": "AAPL", "verdict": "BUY 8/10",
                    "date": "2026-09-01", "rationale": "durable compounder"}) + "\n" +
        json.dumps({"strategy": "ai_quality", "symbol": "MSFT", "verdict": "BUY 7/10",
                    "date": "2026-09-02"}) + "\n")
    sl = {t["sid"]: t for t in TB.from_adjudications(tmp_path)}
    assert "ai_quality" in sl
    t = sl["ai_quality"]
    assert t["n"] == 2 and t["value"] == 8000 and t["thesis"] == "durable compounder"
    assert {p["symbol"] for p in t["positions"]} == {"AAPL", "MSFT"}


def test_from_adjudications_empty_when_no_ledger(tmp_path):
    _office(tmp_path, [{"symbol": "AAPL", "value": 5000}])
    assert TB.from_adjudications(tmp_path) == []          # no adjudications.jsonl -> nothing


def test_import_desk_board_snapshots_sleeves(tmp_path):
    board = tmp_path / "positions_board.json"
    board.write_text(json.dumps({"positions": [
        {"symbol": "6229", "sleeve": "japan_netnet", "mv_usd": 12227, "verdict": "BUY",
         "thesis": "sub-NCAV", "edge": "lease rail", "court_date": "2026-08-15"},
        {"symbol": "5408", "sleeve": "japan_netnet", "mv_usd": 8614, "verdict": "BUY"},
        {"symbol": "SGOV", "sleeve": "held", "mv_usd": 200000},          # non-thesis -> skipped
    ]}))
    out = {t["sid"]: t for t in TB.import_desk_board(board)}
    assert "japan_netnet" in out and "held" not in out
    jp = out["japan_netnet"]
    assert jp["n"] == 2 and jp["value"] == 20841 and jp["edge"] == "lease rail"


def test_merge_native_overrides_owned():
    owned = [{"sid": "japan_netnet", "label": "Japan", "value": 100, "n": 1,
              "thesis": "old", "verdict": "HELD", "court_date": "", "edge": "", "next_date": "", "positions": []}]
    native = [{"sid": "japan_netnet", "label": "Japan", "value": 200, "n": 2,
               "thesis": "courted", "verdict": "BUY", "court_date": "2026-09-01", "edge": "", "next_date": "", "positions": []},
              {"sid": "ai_quality", "label": "AI", "value": 50, "n": 1,
               "thesis": "", "verdict": "BUY", "court_date": "", "edge": "", "next_date": "", "positions": []}]
    m = {t["sid"]: t for t in TB.merge(owned, native)}
    assert m["japan_netnet"]["thesis"] == "courted"       # native wins
    assert "ai_quality" in m and len(m) == 2


def test_taxonomy_buckets_and_goal_grouping():
    from officekit import thesis_board as TB
    theses = [{"sid": "japan_netnet", "label": "Japan Netnet", "value": 45000, "n": 8,
               "positions": [], "thesis": "", "verdict": "", "court_date": "", "edge": "", "next_date": ""},
              {"sid": "ai_application", "label": "AI", "value": 28000, "n": 3,
               "positions": [], "thesis": "", "verdict": "", "court_date": "", "edge": "", "next_date": ""},
              {"sid": "energy_realasset", "label": "Energy", "value": 21000, "n": 2,
               "positions": [], "thesis": "", "verdict": "", "court_date": "", "edge": "", "next_date": ""}]
    assert TB.bucket_of("japan_netnet") == "cyclical_value"
    assert TB.bucket_of("ai_application") == "growth"
    assert TB.bucket_of("energy_realasset") == "defensive"
    assert TB.bucket_of("some_new_value_screen") == "cyclical_value"      # keyword fallback
    scn = {b["bucket"]: b for b in TB.by_scenario(theses)}
    assert set(scn) == {"cyclical_value", "growth", "defensive"}
    assert scn["growth"]["theses"][0]["sid"] == "ai_application"
    # goal grouping: growth is flagged long-horizon for a near-term spending goal
    goals = [{"id": "g1", "kind": "spending", "label": "SF purchase", "date": "2027-09-01", "amount": 5_000_000}]
    bg = TB.by_goal(theses, goals, "2026-09-11")
    assert len(bg) == 1 and bg[0]["goal"]["id"] == "g1"
    growth = next(b for b in bg[0]["buckets"] if b["bucket"] == "growth")
    assert growth["fit"].startswith("long")


def test_explain_fit_reasons_by_horizon():
    from officekit import thesis_board as TB
    near = {"id": "g1", "kind": "spending", "label": "SF purchase", "amount": 5_000_000, "date": "2027-09-01"}
    longg = {"id": "g2", "kind": "retirement", "label": "Retirement", "date": "2050-01-01"}
    # near-term goal: growth reads as a stretch, defensive as ballast
    assert "wrong risk" in TB.explain_fit("growth", near, "2026-09-11").lower()
    assert "ballast" in TB.explain_fit("defensive", near, "2026-09-11").lower()
    # long-dated goal: growth becomes where it earns its return
    assert "long-duration" in TB.explain_fit("growth", longg, "2026-09-11").lower()
    # by_goal attaches the explainer per bucket
    theses = [{"sid": "ai_application", "label": "AI", "value": 28000, "n": 1, "positions": [],
               "thesis": "", "verdict": "", "court_date": "", "edge": "", "next_date": ""}]
    bg = TB.by_goal(theses, [near], "2026-09-11")
    assert bg[0]["buckets"][0]["fit_why"]


def test_merge_pack_augments_live_sleeve_without_zeroing_value():
    """A pack (value 0) overlays a live desk sleeve's deck/thesis but KEEPS its
    real value + positions (adding a deck must not zero the dollars). 2026-09-12."""
    from officekit import thesis_board as TB
    owned = [{"sid": "japan_netnet", "label": "Japan", "value": 45000, "n": 8,
              "thesis": "old", "verdict": "BUY", "court_date": "", "edge": "",
              "next_date": "", "positions": [{"symbol": "6229", "mv": 12000}]}]
    pack = [{"sid": "japan_netnet", "label": "Japan", "value": 0, "n": 8, "thesis": "courted deck",
             "verdict": "", "court_date": "2026-09-12", "edge": "EDGE", "next_date": "",
             "positions": [], "deck": "DECK.md", "author": "pitch-bot", "pack": True}]
    m = {t["sid"]: t for t in TB.merge(owned, pack)}["japan_netnet"]
    assert m["value"] == 45000 and m["positions"]                 # live value/positions kept
    assert m["thesis"] == "courted deck" and m["deck"] == "DECK.md" and m["pack"] is True  # deck overlaid
