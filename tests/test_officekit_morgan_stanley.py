"""morgan_stanley — the first-class MS Prime Brokerage statement library.

Synthetic bundles exercise the format parsing, the realized-lot ledger's
idempotent daily-window accumulation (the bug that undercounted realized losses
3.5x: reading only the newest bundle / only the first gain-loss file), and the
positions classifier (the "Cash Securities" = equity trap). A guarded block
runs against the real ~/Downloads bundles when present."""
import io
import zipfile
from pathlib import Path

import officekit_adapters as A
from officekit_adapters import morgan_stanley as ms


# ------------------------------------------------------------- synthetic bundles

def _positions_csv(rows):
    hdr = ("Reporting Date,Main Account Number,Sub Account Number,Symbol,"
           "Security Description,CUSIP,Current Quantity,Long/Short Code,Price (USD),"
           "Market Value / Net Equity (USD),Gross Market Value (USD),"
           "Accrued Interest (USD),Asset Class,Product Type,Issue Currency\n")
    return hdr + "".join(rows) + "Count=%d\n" % len(rows)


def _gainloss_csv(rows, empty=False):
    if empty:
        return "Count=0\n"
    hdr = ("Reported Date,Portfolio Id,CUSIP,Symbol,Security Description,Strategy,"
           "Taxlot ID,Date Acquired,Date Closed,Quantity,Base Cost,Base Proceeds,"
           "Base GainLoss,Issue GainLoss,GainLoss Type,Loss Disallowed,Issue Currency\n")
    return hdr + "".join(rows)


def _make_bundle(path, positions="", gainloss_files=None):
    with zipfile.ZipFile(path, "w") as z:
        if positions:
            z.writestr("MAC001X_Global_Positions_20260904.csv", positions)
        for i, gl in enumerate(gainloss_files or []):
            z.writestr(f"CCAR002X_Daily_Gain_Loss_Summary_Extract_0{i}Sep.csv", gl)


def test_detect_report_by_prefix():
    assert ms.detect_report("MAC001X_Global_Positions.csv") == "MAC001X"
    assert ms.detect_report("CCAR002X_Daily.csv") == "CCAR002X"
    assert ms.detect_report("something_else.csv") is None


def test_positions_classifier_cash_securities_is_equity(tmp_path):
    # the live bug: MS labels equities in a cash account "Cash Securities" and
    # product_type "EQTY" — a loose "CASH" substring match booked them as cash.
    pos = _positions_csv([
        "2026-09-04,ACCT,ACCT,AAPL,APPLE INC,x,100,L,200,20000,20000,0,Cash Securities,EQTY,USD\n",
        "2026-09-04,ACCT,ACCT,USD,DOLLARS,,5000,L,1,5000,5000,0,Cash,CASH,USD\n",
        "2026-09-04,ACCT,ACCT,USD,DOLLARS,,-3000,S,1,-3000,-3000,0,Cash,CASH,USD\n",
    ])
    b = tmp_path / "Bundle_09042026.zip"
    _make_bundle(b, positions=pos)
    rows = ms.positions_rows(ms.parse_bundle(b))
    kinds = {r["symbol"]: r["sec_type"] for r in rows}
    assert kinds["AAPL"] == "STK"                       # NOT cash
    assert all(r["sec_type"] == "CASH" for r in rows if r["symbol"] == "CASH")
    cash = sum(r["value"] for r in rows if r["sec_type"] == "CASH")
    assert cash == 2000                                 # 5000 long + (-3000) short financing leg


def test_gainloss_ledger_merges_all_files_and_is_idempotent(tmp_path):
    # a bundle carries SEVERAL daily gain/loss files, the first often the empty
    # Count=0 stub — reading only the first (old bug) drops real closures.
    day1 = _gainloss_csv([
        "2026-09-04,P,x,AAA,A INC,S1,LOT1,2025-01-01,2026-09-04,100,10000,9000,-1000,-1000,LONG TERM,,USD\n",
    ])
    day2 = _gainloss_csv([
        "2026-09-05,P,x,BBB,B INC,S1,LOT2,2026-06-01,2026-09-05,50,5000,4000,-1000,-1000,SHORT TERM,,USD\n",
    ])
    b1 = tmp_path / "Bundle_09052026.zip"
    _make_bundle(b1, gainloss_files=[_gainloss_csv([], empty=True), day1, day2])

    led = ms.RealizedLedger()
    added = led.merge_bundle(ms.parse_bundle(b1))
    assert added == 2                                   # both real days, empty stub ignored
    s = led.summary()
    assert s["n_lots"] == 2
    assert s["lt_net"] == -1000 and s["st_net"] == -1000
    assert s["net"] == -2000

    # re-merging the SAME bundle changes nothing (idempotent by lot key)
    assert led.merge_bundle(ms.parse_bundle(b1)) == 0
    assert led.summary()["n_lots"] == 2


def test_daily_windows_accumulate_across_bundles(tmp_path):
    # each bundle is a DAILY WINDOW — YTD only reconstructs by merging every
    # bundle, not by reading the newest alone (the 3.5x-undercount bug).
    b_early = tmp_path / "Bundle_07032026.zip"
    b_late = tmp_path / "Bundle_09062026.zip"
    _make_bundle(b_early, gainloss_files=[_gainloss_csv([
        "2026-07-03,P,x,AAA,A,S,LOT1,2024-01-01,2026-07-03,100,10000,7000,-3000,-3000,LONG TERM,,USD\n"])])
    _make_bundle(b_late, gainloss_files=[_gainloss_csv([
        "2026-09-06,P,x,BBB,B,S,LOT2,2026-05-01,2026-09-06,10,1000,800,-200,-200,SHORT TERM,,USD\n"])])
    # touch mtimes so find_bundles orders them
    import os
    os.utime(b_early, (1, 1))
    os.utime(b_late, (2, 2))

    led = ms.RealizedLedger()
    led.merge_bundles(ms.find_bundles(tmp_path))
    s = led.summary()
    assert s["n_lots"] == 2
    assert s["net"] == -3200                            # BOTH days, not just the newest -200


def test_wash_flag_and_disallowed(tmp_path):
    gl = _gainloss_csv([
        "2026-09-04,P,x,AAA,A,S,LOT1,2026-08-01,2026-09-04,100,10000,9500,-500,-500,SHORT TERM,T,USD\n"])
    b = tmp_path / "Bundle_09042026.zip"
    _make_bundle(b, gainloss_files=[gl])
    led = ms.RealizedLedger()
    led.merge_bundle(ms.parse_bundle(b))
    lot = next(iter(led.lots.values()))
    assert lot["wash_flag"] is True
    assert led.summary()["wash_flagged_lots"] == 1


def test_save_load_roundtrip(tmp_path):
    gl = _gainloss_csv([
        "2026-09-04,P,x,AAA,A,S,LOT1,2025-01-01,2026-09-04,100,10000,9000,-1000,-1000,LONG TERM,,USD\n"])
    b = tmp_path / "Bundle_09042026.zip"
    _make_bundle(b, gainloss_files=[gl])
    led = ms.RealizedLedger()
    led.merge_bundle(ms.parse_bundle(b))
    out = tmp_path / "realized.json"
    led.save(out)
    led2 = ms.RealizedLedger.load(out)
    assert led2.lots == led.lots
    assert led2.merge_bundle(ms.parse_bundle(b)) == 0   # still idempotent after reload


def test_adapter_registered_and_detects_absence(tmp_path, monkeypatch):
    assert "morgan_stanley_bundle" in A.ADAPTERS
    monkeypatch.setattr(ms, "DOWNLOADS", tmp_path)      # empty dir
    res = [r for r in A.discover(names=["morgan_stanley_bundle"])][0]
    assert res["found"] is False and res["status"] == "absent"


# --------------------------------------------------------- guarded live-data check

def test_live_bundles_reconcile_if_present():
    bundles = ms.find_bundles()
    if not bundles:
        return                                          # no local bundles — skip silently
    led = ms.RealizedLedger()
    led.merge_bundles(bundles)
    s = led.summary()
    # the reconciled figure (2026-09-07): ~2,800 lots, gross realized loss ~ -580k,
    # tying to the principal's independent model (-570k). Loose bounds — the point
    # is the accumulator no longer undercounts by 3.5x (the old -162k).
    assert s["n_lots"] > 2000, s
    assert s["st_loss"] < -400000, s                    # was wrongly -162k before the fix
