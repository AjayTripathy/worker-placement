"""ibkr_flex — Flex Query lot-level basis: parsing, FX, LT/ST split, harvest."""
import json

import officekit_adapters as A
from officekit_adapters import ibkr_flex as F

SAMPLE = """<FlexQueryResponse>
 <FlexStatements>
  <FlexStatement accountId="U123">
   <OpenPositions>
     <OpenPosition accountId="U123" currency="USD" symbol="ONON" assetCategory="STK"
        position="100" costBasisMoney="6000" positionValue="4000" fifoPnlUnrealized="-2000"
        openDateTime="20240115;120000" fxRateToBase="1" levelOfDetail="LOT"/>
     <OpenPosition accountId="U123" currency="USD" symbol="ONON" assetCategory="STK"
        position="50" costBasisMoney="3000" positionValue="2500" fifoPnlUnrealized="-500"
        openDateTime="20260601;120000" fxRateToBase="1" levelOfDetail="LOT"/>
     <OpenPosition accountId="U123" currency="HKD" symbol="3388" assetCategory="STK"
        position="1000" costBasisMoney="10000" positionValue="8000" fifoPnlUnrealized="-2000"
        openDateTime="20230101" fxRateToBase="0.128" levelOfDetail="LOT"/>
     <OpenPosition accountId="U123" currency="USD" symbol="WIN" assetCategory="STK"
        position="10" costBasisMoney="1000" positionValue="1500" fifoPnlUnrealized="500"
        openDateTime="20240101" fxRateToBase="1" levelOfDetail="LOT"/>
   </OpenPositions>
  </FlexStatement>
 </FlexStatements>
</FlexQueryResponse>"""


def test_parse_splits_lt_st_and_aggregates_lots():
    rows = {r["symbol"]: r for r in F.parse_flex_positions(SAMPLE, as_of="2026-09-09")}
    onon = rows["ONON"]
    assert len(onon["lots"]) == 2
    assert onon["cost_basis"] == 9000 and onon["value"] == 6500
    assert onon["loss_lt"] == 2000 and onon["loss_st"] == 500      # real term split
    assert onon["ccy"] == "USD"


def test_parse_converts_foreign_via_fxratetobase():
    rows = {r["symbol"]: r for r in F.parse_flex_positions(SAMPLE, as_of="2026-09-09")}
    hk = rows["3388"]
    assert abs(hk["value"] - 1024) < 1e-6 and abs(hk["cost_basis"] - 1280) < 1e-6   # *0.128
    assert abs(hk["loss_lt"] - 256) < 1e-6 and hk["loss_st"] == 0                    # LT (2023)
    assert hk["ccy"] == "USD"


def test_parse_winner_has_no_harvestable_loss():
    rows = {r["symbol"]: r for r in F.parse_flex_positions(SAMPLE, as_of="2026-09-09")}
    assert rows["WIN"]["loss_lt"] == 0 and rows["WIN"]["loss_st"] == 0


def test_warn_envelope_raises_not_ready():
    warn = ('<FlexStatementResponse><Status>Warn</Status><ErrorCode>1019</ErrorCode>'
            '<ErrorMessage>Statement generation in progress</ErrorMessage></FlexStatementResponse>')
    try:
        F.parse_flex_positions(warn)
        assert False, "should have raised"
    except RuntimeError as e:
        assert "1019" in str(e)


def test_norm_row_and_convert_preserve_lot_fields():
    row = A._norm_row({"symbol": "onon", "qty": 150, "value": 6500, "cost_basis": 9000,
                       "lots": [{"loss": 2000}], "loss_lt": 2000, "loss_st": 500})
    assert row["loss_lt"] == 2000 and row["loss_st"] == 500 and row["lots"]
    out = A.convert_to_base([{**row, "ccy": "USD"}], {}, base="USD")[0]
    assert out["loss_lt"] == 2000 and out["loss_st"] == 500      # base already -> unchanged


def test_flex_adapter_registered_and_detects_missing_creds(monkeypatch):
    monkeypatch.delenv("IBKR_FLEX_TOKEN", raising=False)
    monkeypatch.delenv("IBKR_FLEX_QUERY_ID", raising=False)
    d = {r["name"]: r for r in A.discover(names=["ibkr_flex"])}["ibkr_flex"]
    assert d["status"] == "needs_key" and "IBKR_FLEX_TOKEN" in d["detail"]


def test_harvest_uses_lot_level_split(tmp_path):
    from officekit.serve import build_office
    from officekit import build_model, load_balance_sheet
    from officekit import harvest as H
    build_office({"as_of": "2026-09-09", "profile": {},
                  "positions": {"account": "b", "rows": [
                      {"symbol": "ONON", "value": 6500, "cost_basis": 9000,
                       "lots": [{"loss": 2000}, {"loss": 500}], "loss_lt": 2000, "loss_st": 500}]}},
                 tmp_path)
    m = build_model(load_balance_sheet(tmp_path / "balance_sheet.json", strict=False))
    col = H.collect(m, tmp_path)
    onon = next(p for p in col["positions"] if p["label"] == "ONON")
    assert onon["term"] == "lot-level" and onon["source"] == "Flex lot basis"
    assert onon["lt"] == 2000 and onon["st"] == 500 and onon["loss"] == 2500
    assert onon["n_lots"] == 2
