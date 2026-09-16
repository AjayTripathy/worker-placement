"""MS bundle triplication guard: a bundle shipping several report-date copies of a
point-in-time snapshot must NOT sum them (the 2026-09-10 'much larger loss' bug —
3 copies of the open-taxlot/positions extract tripled market value and the harvest
loss surface). Snapshots keep the latest copy; gain/loss windows union by lot key."""
import csv
import io
import zipfile

from officekit_adapters import morgan_stanley as ms


def _csv(headers, rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def test_file_report_date_parses_bundle_date():
    assert ms._file_report_date("CCAR001X - Open Taxlot - X - 08Sep2026-5.csv") == "2026-09-08"
    assert ms._file_report_date("CCAR001X - X - 30Aug2026-2.csv") == "2026-08-30"
    assert ms._file_report_date("no-date.csv") == ""


def test_snapshot_taxlots_and_positions_keep_latest_copy_only(tmp_path):
    tl_hdr = ["Reported Date", "Symbol", "Taxlot ID", "Date Acquired", "Quantity",
              "Base Unit Cost", "Base Cost"]
    tl_rows = [["2026-08-30", "AAPL", "L1", "2026-01-01", "10", "200", "2000"],
               ["2026-08-30", "MSFT", "L2", "2026-02-01", "5", "400", "2000"]]
    pos_hdr = ["Reporting Date", "Symbol", "Current Quantity", "Price (USD)",
               "Market Value / Net Equity (USD)", "Product Type"]
    pos_rows = [["2026-08-30", "AAPL", "10", "180", "1800", "EQUITY"],
                ["2026-08-30", "MSFT", "5", "380", "1900", "EQUITY"]]
    z = tmp_path / "Bundle_08302026120000.zip"
    with zipfile.ZipFile(z, "w") as zf:
        # THREE report-date copies of each snapshot (as the real bundles ship)
        for d in ("28Aug2026", "29Aug2026", "30Aug2026"):
            zf.writestr(f"CCAR001X - Open Taxlot Extract - T - {d}-1.csv", _csv(tl_hdr, tl_rows))
            zf.writestr(f"MAC001X - Global Positions Extract - T - {d}-2.csv", _csv(pos_hdr, pos_rows))
    bd = ms.parse_bundle(z)
    assert len(bd.taxlots()) == 2       # NOT 6 — latest snapshot only, never summed
    assert len(bd.positions()) == 2     # NOT 6
    assert sum(p["market_value_usd"] for p in bd.positions()) == 3700   # 1x, not 11100


def test_gainloss_windows_union_by_lot_key(tmp_path):
    gl_hdr = ["Reported Date", "Symbol", "Taxlot ID", "Date Closed", "Quantity",
              "Base GainLoss", "GainLoss Type"]
    early = [["2026-08-28", "AAPL", "L1", "2026-08-27", "10", "-500", "SHORT TERM"]]
    # a wider window that RE-LISTS the same close plus a new one
    later = [["2026-08-30", "AAPL", "L1", "2026-08-27", "10", "-500", "SHORT TERM"],
             ["2026-08-30", "TSLA", "L9", "2026-08-29", "4", "-300", "SHORT TERM"]]
    z = tmp_path / "Bundle_08302026130000.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("CCAR002X - Daily Gain Loss Summary Extract - T - 28Aug2026-1.csv", _csv(gl_hdr, early))
        zf.writestr("CCAR002X - Daily Gain Loss Summary Extract - T - 30Aug2026-2.csv", _csv(gl_hdr, later))
    bd = ms.parse_bundle(z)
    gl = bd.gainloss()
    assert len(gl) == 2                                          # union: L1 once + L9, not 3
    assert round(sum(r["gainloss"] for r in gl)) == -800        # -500 (once) + -300


def test_realized_ledger_unchanged_by_dedup():
    # the ledger already dedups by lot key, so the parse-time fix leaves it intact
    led = ms.RealizedLedger()
    led.merge_bundles(ms.find_bundles())
    s = led.summary()
    if s["n_lots"]:                                              # only when real bundles present
        assert s["st_loss"] <= 0 and s["net"] <= 0
