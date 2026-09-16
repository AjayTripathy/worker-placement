"""Office sync — refresh holdings from live staging, safely (no data loss)."""
import json


def test_sync_refreshes_adds_never_deletes(tmp_path):
    from officekit.serve import build_office, sync_office_from_staging
    from officekit import staging
    answers = {"as_of": "2026-09-08", "profile": {},
               "positions": {"account": "b", "rows": [
                   {"symbol": "AAPL", "value": 100000},
                   {"symbol": "MSFT", "value": 50000}]}}
    build_office(answers, tmp_path)

    # a fresh live pull: AAPL up (+ basis), NVDA new, MSFT absent from THIS source
    staging.record_pull(tmp_path, "adapter:ibkr_socket", "adapter", "IBKR",
                        rows=[{"symbol": "AAPL", "value": 130000, "sec_type": "STK", "cost_basis": 90000},
                              {"symbol": "NVDA", "value": 40000, "sec_type": "STK"}],
                        refresh="auto", as_of="2026-09-09")
    res = sync_office_from_staging(tmp_path)

    by = {r["symbol"]: r for r in json.load(open(tmp_path / "answers.json"))["positions"]["rows"]}
    assert by["AAPL"]["value"] == 130000 and by["AAPL"]["cost_basis"] == 90000   # refreshed + basis
    assert "NVDA" in by and by["NVDA"]["value"] == 40000                         # added
    assert "MSFT" in by and by["MSFT"]["value"] == 50000                         # kept — NEVER deleted
    assert res["changed"] >= 1 and res["added"] == 1


def test_sync_ignores_cash_and_nonequity(tmp_path):
    from officekit.serve import build_office, sync_office_from_staging
    from officekit import staging
    build_office({"as_of": "2026-09-08", "profile": {},
                  "positions": {"account": "b", "rows": [{"symbol": "AAPL", "value": 100000}]}}, tmp_path)
    staging.record_pull(tmp_path, "adapter:ibkr_socket", "adapter", "IBKR",
                        rows=[{"symbol": "USD", "value": 999, "sec_type": "CASH"},
                              {"symbol": "CASH", "value": 999, "sec_type": "CASH"}],
                        refresh="auto", as_of="2026-09-09")
    res = sync_office_from_staging(tmp_path)
    by = {r["symbol"] for r in json.load(open(tmp_path / "answers.json"))["positions"]["rows"]}
    assert "USD" not in by and "CASH" not in by      # cash isn't added as an equity position
    assert res["added"] == 0


def test_sync_value_is_cost_attaches_basis_without_degrading_market(tmp_path):
    """A cost-only pull (Gateway w/o market data) must attach cost basis but
    NOT overwrite a good market value with cost."""
    from officekit.serve import build_office, sync_office_from_staging
    from officekit import staging
    build_office({"as_of": "2026-09-08", "profile": {},
                  "positions": {"account": "b", "rows": [{"symbol": "AAPL", "value": 130000}]}}, tmp_path)
    # broker gives cost basis only (value == cost, flagged)
    staging.record_pull(tmp_path, "adapter:ibkr_socket", "adapter", "IBKR",
                        rows=[{"symbol": "AAPL", "value": 100000, "cost_basis": 100000,
                               "value_is_cost": True, "sec_type": "STK"}],
                        refresh="auto", as_of="2026-09-09")
    sync_office_from_staging(tmp_path)
    row = next(r for r in json.load(open(tmp_path / "answers.json"))["positions"]["rows"]
               if r["symbol"] == "AAPL")
    assert row["value"] == 130000        # market value preserved (NOT degraded to 100k cost)
    assert row["cost_basis"] == 100000   # basis attached -> harvest can now see it's underwater


def test_sync_attaches_lots_and_prefers_flex_over_blended(tmp_path):
    """A Flex pull (lots + LT/ST split) must attach to the office row and WIN over
    a same-symbol blended socket row, so harvest gets the real term split."""
    from officekit.serve import build_office, sync_office_from_staging
    from officekit import staging
    build_office({"as_of": "2026-09-09", "profile": {},
                  "positions": {"account": "b", "rows": [{"symbol": "ONON", "value": 6500}]}}, tmp_path)
    # blended socket row (no lots) + Flex row (lots) for the same symbol
    staging.record_pull(tmp_path, "adapter:ibkr_socket", "adapter", "IBKR",
                        rows=[{"symbol": "ONON", "value": 6500, "cost_basis": 9000, "sec_type": "STK"}],
                        refresh="auto", as_of="2026-09-09")
    staging.record_pull(tmp_path, "adapter:ibkr_flex", "adapter", "IBKR",
                        rows=[{"symbol": "ONON", "value": 6500, "cost_basis": 9000, "sec_type": "STK",
                               "lots": [{"loss": 2000}, {"loss": 500}], "loss_lt": 2000, "loss_st": 500}],
                        refresh="auto", as_of="2026-09-09")
    sync_office_from_staging(tmp_path)
    row = next(r for r in json.load(open(tmp_path / "answers.json"))["positions"]["rows"]
               if r["symbol"] == "ONON")
    assert row["loss_lt"] == 2000 and row["loss_st"] == 500 and len(row["lots"]) == 2


def test_desk_thesis_sleeves_render_section(tmp_path):
    """The Desk's per-thesis sleeves render as a live strategy section, grouped by
    the positions' `sleeve` tag with verdict/edge/positions (2026-09-10)."""
    from officekit.render_strategies import render_strategies
    from officekit import build_model, load_balance_sheet
    from officekit.serve import build_office
    build_office({"as_of": "2026-09-10", "profile": {},
                  "positions": {"account": "b", "rows": [{"symbol": "X", "value": 100}]}}, tmp_path)
    m = build_model(load_balance_sheet(tmp_path / "balance_sheet.json", strict=False))
    theses = [{"sid": "japan_netnet", "label": "Japan Netnet", "value": 45332, "n": 8,
               "thesis": "sub-NCAV basket", "verdict": "BUY", "court_date": "2026-08-15",
               "edge": "lease rail", "next_date": "2026-10-01",
               "positions": [{"symbol": "6229", "mv": 12227, "verdict": "BUY", "upnl": -501}]}]
    html = render_strategies(m, desk_theses=theses)
    assert "1 thesis views" in html and 'data-state="held"' in html
    assert 'id="thesis-japan_netnet"' in html and "sub-NCAV basket" in html
    assert "lease rail" in html and "6229" in html


def test_desk_theses_absent_renders_no_section(tmp_path):
    from officekit.render_strategies import render_strategies
    from officekit import build_model, load_balance_sheet
    from officekit.serve import build_office
    build_office({"as_of": "2026-09-10", "profile": {},
                  "positions": {"account": "b", "rows": [{"symbol": "X", "value": 100}]}}, tmp_path)
    m = build_model(load_balance_sheet(tmp_path / "balance_sheet.json", strict=False))
    assert "Thesis sleeves (" not in render_strategies(m)        # None -> no section (backward compat)


def test_signals_fleet_migrated_to_officekit():
    """The desk's detector/generator fleet is registered from officekit_signals
    (not desk/) so the office SIGNALS page shows it without depending on the desk."""
    import officekit_signals as sig
    import officekit_signals.fleet as fleet          # registers the fleet
    assert fleet.N_GENERATORS >= 40
    kinds = {}
    for c in sig.CAPABILITIES.values():
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    assert kinds.get("generator", 0) >= 40 and kinds.get("detector", 0) >= 5
    # the desk re-export still works (backward compat during wind-down)
    import desk.signals_desk as ds
    assert ds.N_GENERATORS == fleet.N_GENERATORS


def test_sync_preserves_account_provenance(tmp_path):
    """Collapse to one row per symbol for the VIEW, but keep per-account provenance
    so the owner is recoverable (principal 2026-09-11)."""
    from officekit.serve import build_office, sync_office_from_staging
    from officekit import staging
    build_office({"as_of": "2026-09-11", "profile": {}, "positions": {"account": "b", "rows": [{"symbol": "SEED", "value": 1000}]}}, tmp_path)
    staging.record_pull(tmp_path, "adapter:ibkr_a", "adapter", "A",
                        rows=[{"symbol": "AAPL", "value": 6000, "cost_basis": 9000, "account": "U1", "sec_type": "STK"}],
                        refresh="auto")
    staging.record_pull(tmp_path, "adapter:schwab", "adapter", "S",
                        rows=[{"symbol": "AAPL", "value": 4000, "cost_basis": 3000, "account": "U2", "sec_type": "STK"}],
                        refresh="auto")
    sync_office_from_staging(tmp_path)
    row = next(r for r in json.load(open(tmp_path / "answers.json"))["positions"]["rows"] if r["symbol"] == "AAPL")
    assert row["value"] == 10000 and row["cost_basis"] == 12000        # collapsed sums (the VIEW)
    assert {a["account"] for a in row["accounts"]} == {"U1", "U2"}      # OWNER recoverable
    assert {a["source"] for a in row["accounts"]} == {"adapter:ibkr_a", "adapter:schwab"}


def test_wash_risk_recovers_owner_from_position_accounts(tmp_path):
    """wash_risk detects a multi-account holding from the office's OWN position
    provenance (no live staging needed)."""
    from officekit.serve import build_office
    from officekit import build_model, load_balance_sheet, harvest as H
    build_office({"as_of": "2026-09-11", "profile": {}, "positions": {"account": "b", "rows": [
        {"symbol": "AAPL", "value": 10000, "cost_basis": 15000,
         "accounts": [{"account": "U1", "source": "ibkr"}, {"account": "U2", "source": "schwab"}]}]}}, tmp_path)
    col = H.collect(build_model(load_balance_sheet(tmp_path / "balance_sheet.json", strict=False)), tmp_path)
    ma = {x["symbol"]: x for x in col["wash_risk"]["multi_account"]}
    assert "AAPL" in ma and set(ma["AAPL"]["accounts"]) == {"U1", "U2"}
