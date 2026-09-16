"""harvest — whole-portfolio loss harvesting + factor tilt."""
from officekit import build_model
from officekit.intake import build_from_answers
from officekit import harvest as H


def _m(sleeves, tax=None, goals=None):
    a = {"as_of": "2026-09-08", "profile": {}, "sleeves": sleeves, "goals": goals or []}
    if tax:
        a["incoming"] = tax
    return build_model(build_from_answers(a))


def test_collect_measures_basis_and_flags_unknown():
    m = _m([
        {"category": "public_equity", "value": 800000, "name": "Losers",
         "holdings": [{"company": "X", "amount": 300000, "cost_basis": 500000}]},   # 200k loss
        {"category": "public_equity", "value": 400000, "name": "No basis"},
    ])
    col = H.collect(m)
    by = {p["label"]: p for p in col["positions"]}
    assert by["Losers"]["known"] and abs(by["Losers"]["loss"] - 200000) < 1
    assert by["No basis"]["known"] is False and by["No basis"]["loss"] == 0


def test_simulate_offsets_gain_and_shrinks_reserve():
    m = _m([{"category": "public_equity", "value": 800000, "name": "L",
             "holdings": [{"company": "X", "amount": 300000, "cost_basis": 500000}]}],
           tax={"amount": 1_000_000, "character": "ltcg", "state": "CA"})
    col = H.collect(m)
    sel = {p["id"] for p in col["positions"] if p["known"]}
    sim = H.simulate(col, sel, m, 0.30, "2026-09-08")
    assert abs(sim["harvested_loss"] - 200000) < 1
    assert abs(sim["tax_benefit"] - 60000) < 1                 # 200k * 30%
    assert sim["reserve_after"] < sim["reserve_before"]
    assert sim["lockout"] and sim["lockout"][0]["earliest_repurchase"] > "2026-09-08"


def test_carryforward_beyond_gain_carries_forward():
    m = _m([{"category": "public_equity", "value": 100000, "name": "L",
             "holdings": [{"company": "X", "amount": 100000, "cost_basis": 700000}]}],   # 600k loss
           tax={"amount": 200000, "character": "ltcg", "state": "CA"})
    col = H.collect(m)
    sim = H.simulate(col, {p["id"] for p in col["positions"] if p["known"]}, m, 0.30, "2026-09-08")
    assert sim["residual_carryforward"] > 0                     # loss exceeds the gain
    assert sim["reserve_after"] == 0


def test_factor_tilt_and_drift():
    m = _m([{"category": "public_equity", "value": 1_000_000, "name": "Eq",
             "holdings": [{"company": "X", "amount": 100000, "cost_basis": 400000}]},
            {"category": "fixed_income", "value": 500000, "name": "Bonds"}])
    tilt = H.factor_tilt(m)
    assert "S&P 500" in tilt
    # dropping the equity sleeve lowers the S&P tilt
    after = H.factor_tilt(m, exclude_names={"Eq"})
    assert after["S&P 500"] < tilt["S&P 500"]


def test_convert_to_base_scales_cost_basis():
    import officekit_adapters as A
    rows = [{"symbol": "TOYO", "value": 1000, "cost_basis": 1500, "unrealized_pnl": -500, "ccy": "JPY"}]
    out = A.convert_to_base(rows, {"JPY": 0.007}, base="USD")[0]
    assert abs(out["value"] - 7.0) < 1e-6            # 1000 * 0.007
    assert abs(out["cost_basis"] - 10.5) < 1e-6      # 1500 * 0.007 — basis converted too
    assert out["unrealized_pnl"] < 0


def test_harvest_reads_office_position_basis(tmp_path):
    # the office's own positions carry market value + cost basis (synced from the
    # broker's avg cost) -> a position below its basis is a measurable loser
    from officekit.serve import build_office
    from officekit import build_model, load_balance_sheet
    build_office({"as_of": "2026-09-08", "profile": {},
                  "positions": {"account": "b", "rows": [
                      {"symbol": "LOSE", "value": 60000, "cost_basis": 100000},
                      {"symbol": "WIN", "value": 120000, "cost_basis": 80000}]}}, tmp_path)
    m = build_model(load_balance_sheet(tmp_path / "balance_sheet.json", strict=False))
    col = H.collect(m, tmp_path)
    losers = {p["label"]: p for p in col["positions"] if p["known"]}
    assert "LOSE" in losers and abs(losers["LOSE"]["loss"] - 40000) < 1   # 100k basis - 60k value
    assert "WIN" not in losers                                            # a winner isn't harvestable


def test_convert_to_base_is_idempotent():
    """Converting an already-converted row must be a no-op — not a re-multiply or
    a zeroing (the 2026-09-09 double-convert-zeroed-foreign-positions bug)."""
    import officekit_adapters as A
    once = A.convert_to_base([{"symbol": "3388", "value": 8055, "cost_basis": 8723,
                               "ccy": "HKD"}], {"HKD": 0.128}, base="USD")
    twice = A.convert_to_base(once, {}, base="USD")   # empty rates on 2nd pass
    assert abs(twice[0]["value"] - once[0]["value"]) < 1e-6      # unchanged, NOT 0
    assert abs(twice[0]["cost_basis"] - once[0]["cost_basis"]) < 1e-6


def test_wash_risk_flags_same_symbol_across_accounts(tmp_path):
    from officekit.serve import build_office
    from officekit import build_model, load_balance_sheet, staging
    build_office({"as_of": "2026-09-09", "profile": {},
                  "positions": {"account": "b", "rows": [
                      {"symbol": "ONON", "value": 6000, "cost_basis": 9000}]}}, tmp_path)
    staging.record_pull(tmp_path, "adapter:ibkr_a", "adapter", "IBKR",
                        rows=[{"symbol": "ONON", "value": 6000, "account": "U111", "sec_type": "STK"}],
                        refresh="auto")
    staging.record_pull(tmp_path, "adapter:ibkr_b", "adapter", "IBKR",
                        rows=[{"symbol": "ONON", "value": 3000, "account": "U222", "sec_type": "STK"}],
                        refresh="auto")
    col = H.collect(build_model(load_balance_sheet(tmp_path / "balance_sheet.json", strict=False)), tmp_path)
    w = col["wash_risk"]
    assert w["count"] == 1 and w["warnings"][0]["symbol"] == "ONON"
    assert set(w["warnings"][0]["accounts"]) == {"U111", "U222"}
    assert w["warnings"][0]["severity"] == "medium"


def test_wash_risk_sma_overlap_is_high_severity(tmp_path):
    from officekit.serve import build_office
    from officekit import build_model, load_balance_sheet, staging
    build_office({"as_of": "2026-09-09", "profile": {},
                  "positions": {"account": "b", "rows": [
                      {"symbol": "AAPL", "value": 6000, "cost_basis": 9000}]}}, tmp_path)
    staging.record_pull(tmp_path, "adapter:ibkr_a", "adapter", "IBKR",
                        rows=[{"symbol": "AAPL", "value": 6000, "account": "U111", "sec_type": "STK"}],
                        refresh="auto")
    staging.record_pull(tmp_path, "adapter:morgan_stanley_bundle", "file", "MS",
                        rows=[{"symbol": "AAPL", "value": 5000, "account": "SMA", "sec_type": "STK"}],
                        refresh="manual")
    col = H.collect(build_model(load_balance_sheet(tmp_path / "balance_sheet.json", strict=False)), tmp_path)
    assert col["wash_risk"]["warnings"][0]["severity"] == "high"


def test_wash_risk_standing_caution_when_sma_sleeve_but_no_constituents(tmp_path):
    from officekit.serve import build_office
    from officekit import build_model, load_balance_sheet
    build_office({"as_of": "2026-09-09", "profile": {},
                  "sleeves": [{"category": "direct_index", "value": 9_000_000,
                               "name": "Parametric direct-index SMA"}],
                  "positions": {"account": "b", "rows": [
                      {"symbol": "MSFT", "value": 6000, "cost_basis": 9000}]}}, tmp_path)
    col = H.collect(build_model(load_balance_sheet(tmp_path / "balance_sheet.json", strict=False)), tmp_path)
    assert col["wash_risk"]["has_standing"] is True
    assert "SMA" in col["wash_risk"]["standing"][0]["note"]


def test_wash_risk_quiet_when_single_account(tmp_path):
    from officekit.serve import build_office
    from officekit import build_model, load_balance_sheet, staging
    build_office({"as_of": "2026-09-09", "profile": {},
                  "positions": {"account": "b", "rows": [
                      {"symbol": "ONON", "value": 6000, "cost_basis": 9000}]}}, tmp_path)
    staging.record_pull(tmp_path, "adapter:ibkr_a", "adapter", "IBKR",
                        rows=[{"symbol": "ONON", "value": 6000, "account": "U111", "sec_type": "STK"}],
                        refresh="auto")
    col = H.collect(build_model(load_balance_sheet(tmp_path / "balance_sheet.json", strict=False)), tmp_path)
    assert col["wash_risk"]["count"] == 0 and col["wash_risk"]["has_standing"] is False


def test_realized_loss_is_banked_and_offsets_gain_without_harvesting():
    """Realized YTD losses are a banked tax asset — they cut the reserve even if you
    harvest nothing more (the 2026-09-10 'where's the realized loss' gap)."""
    m = _m([{"category": "public_equity", "value": 500000, "name": "X"}],
           tax={"amount": 1_000_000, "character": "ltcg", "state": "CA"})
    col = H.collect(m)
    col["realized"] = 300000                                  # banked this year
    sim = H.simulate(col, set(), m, 0.30, "2026-09-09")       # harvest NOTHING
    assert sim["realized"] == 300000 and sim["banked"] == 300000
    assert abs(sim["tax_benefit"] - 90000) < 1                # 300k * 30%, no harvest needed
    assert sim["reserve_banked"] < sim["reserve_before"]
    assert abs(sim["realized_benefit"] - 90000) < 1 and sim["harvest_benefit"] == 0


def test_realized_plus_harvest_stack_and_excess_carries_forward():
    m = _m([{"category": "public_equity", "value": 800000, "name": "L",
             "holdings": [{"company": "Z", "amount": 100000, "cost_basis": 500000}]}],   # 400k harvestable
           tax={"amount": 500000, "character": "ltcg", "state": "CA"})
    col = H.collect(m)
    col["realized"] = 300000
    sim = H.simulate(col, {p["id"] for p in col["positions"] if p["known"]}, m, 0.30, "2026-09-09")
    assert sim["banked"] == 300000 and abs(sim["harvested_loss"] - 400000) < 1
    assert sim["residual_carryforward"] > 0                   # 300k+400k > 500k gain
    assert sim["tax_asset"] > 0 and sim["reserve_after"] == 0


def test_realized_st_lt_split_and_blended_application():
    """ST losses are shown split out, but with no ST gains they apply at the LTCG
    (blended) rate — the ordinary-rate premium is reported as foregone, not applied."""
    m = _m([{"category": "public_equity", "value": 500000, "name": "X"}],
           tax={"amount": 1_000_000, "character": "ltcg", "state": "CA"})
    m["d"]["tax_model"]["rate_ordinary"] = 0.50
    col = H.collect(m)
    col.update({"realized": 494000, "realized_st": 498000, "realized_lt": 0})
    sim = H.simulate(col, set(), m, 0.371, "2026-09-10")
    assert sim["realized_st"] == 498000 and sim["realized_lt"] == 0
    assert sim["st_at_ordinary"] == 0 and sim["st_at_blended"] == 498000   # no ST gains
    assert abs(sim["st_premium_foregone"] - 498000 * (0.50 - 0.371)) < 1
    # applied at blended: banked benefit == net realized * LTCG rate
    assert abs(sim["realized_benefit"] - 494000 * 0.371) < 1


def test_read_scorecard_prefers_office_folder(tmp_path):
    """harvest reads the OFFICE-generated scorecard first (no desk/data dependency
    once the office has generated its own) — the desk copy is only a fallback."""
    import json as _j
    (tmp_path / "parametric_scorecard.json").write_text(
        _j.dumps({"asof": "2026-09-10", "harvest": {"total_surface": -5},
                  "structure": {"net": 9}, "realized_ytd": {"net": -3}}))
    sc = H._read_scorecard(tmp_path)
    assert sc["asof"] == "2026-09-10" and sc["harvest"]["total_surface"] == -5


def test_build_scorecard_none_without_bundles(tmp_path):
    import officekit_adapters.morgan_stanley as ms
    assert ms.build_scorecard(directory=tmp_path) is None      # empty dir -> no card, not a crash


def test_wash_risk_flags_stocks_in_sma_and_brokerage(tmp_path):
    """A name held in BOTH a direct-index SMA sleeve and a brokerage account is a
    multi-account holding — flagged even though the office collapses positions by
    symbol (the SMA sleeve's holdings supply the second account). 2026-09-11."""
    from officekit.serve import build_office
    from officekit import build_model, load_balance_sheet, staging
    build_office({"as_of": "2026-09-11", "profile": {},
                  "sleeves": [{"category": "direct_index", "name": "Parametric SMA (130/30)",
                               "value": 500000,
                               "holdings": [{"company": "AAPL", "amount": 5000},
                                            {"company": "XOM", "amount": 4000}]}],
                  "positions": {"account": "b", "rows": [{"symbol": "AAPL", "value": 6000,
                                                          "cost_basis": 9000}]}}, tmp_path)
    staging.record_pull(tmp_path, "adapter:ibkr_socket", "adapter", "IBKR",
                        rows=[{"symbol": "AAPL", "value": 6000, "account": "U1", "sec_type": "STK"}],
                        refresh="auto", as_of="2026-09-11")
    col = H.collect(build_model(load_balance_sheet(tmp_path / "balance_sheet.json", strict=False)), tmp_path)
    w = col["wash_risk"]
    ma = {x["symbol"]: x for x in w["multi_account"]}
    assert "AAPL" in ma and ma["AAPL"]["sma"] is True                # SMA + IBKR
    assert any(a for a in ma["AAPL"]["accounts"] if "SMA" in a) and "U1" in ma["AAPL"]["accounts"]
    # AAPL is a harvestable loser held in two accounts -> a high-severity wash warning
    assert any(wn["symbol"] == "AAPL" and wn["severity"] == "high" for wn in w["warnings"])
