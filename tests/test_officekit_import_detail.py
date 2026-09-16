"""Per-import detail pages: assets + totals, clickable from imports, right refresh UI."""
import json
from pathlib import Path

from officekit import staging
from officekit.render_imports import import_slug, render_import_detail
from officekit.serve import build_office, write_imports_page


def _office(tmp_path):
    build_office({"as_of": "2026-09-09", "profile": {},
                  "positions": {"account": "b", "rows": [{"symbol": "AAPL", "value": 100}]}}, tmp_path)


def test_import_slug_stable():
    assert import_slug("adapter:ibkr_socket") == "import_adapter-ibkr-socket"
    assert import_slug("upload:MyFile 2026.csv") == "import_upload-myfile-2026-csv"


def test_detail_page_written_with_assets_and_total(tmp_path):
    _office(tmp_path)
    staging.record_pull(tmp_path, "adapter:ibkr_socket", "adapter", "IBKR",
                        rows=[{"symbol": "NVDA", "value": 8000, "account": "U1", "sec_type": "STK"},
                              {"symbol": "TSLA", "value": 2000, "account": "U1", "sec_type": "STK"}],
                        refresh="auto", as_of="2026-09-09")
    write_imports_page(tmp_path)
    page = tmp_path / "pages" / "import_adapter-ibkr-socket.html"
    assert page.exists()
    html = page.read_text()
    assert "NVDA" in html and "TSLA" in html
    assert "10,000" in html                                  # total of the two rows
    assert "Re-pull now" in html and "/adapter/import" in html   # live-connection refresh


def test_upload_detail_has_file_picker_and_remove(tmp_path):
    _office(tmp_path)
    staging.record_pull(tmp_path, "upload:statement.csv", "upload", "statement.csv",
                        rows=[{"symbol": "MSFT", "value": 500, "sec_type": "STK"}],
                        refresh="manual", as_of="2026-09-01")
    write_imports_page(tmp_path)
    page = (tmp_path / "pages" / import_slug("upload:statement.csv")) .with_suffix(".html")
    html = page.read_text()
    assert 'action="/import/files"' in html and 'type="file"' in html   # full picker
    assert "Remove this import" in html and "MSFT" in html


def test_imports_index_links_to_detail(tmp_path):
    _office(tmp_path)
    staging.record_pull(tmp_path, "adapter:ibkr_socket", "adapter", "IBKR",
                        rows=[{"symbol": "NVDA", "value": 8000, "account": "U1", "sec_type": "STK"}],
                        refresh="auto", as_of="2026-09-09")
    write_imports_page(tmp_path)
    idx = (tmp_path / "pages" / "imports.html").read_text()
    assert "import_adapter-ibkr-socket.html" in idx           # the row is a link


def test_detail_reconciliation_diff_shown(tmp_path):
    entry = {"source_id": "upload:x.csv", "kind": "upload", "refresh": "manual",
             "as_of": "2026-09-01", "pulled_utc": "2026-09-01T00:00:00", "warnings": [],
             "stated_total": 10000}
    rows = [{"symbol": "A", "value": 9000, "sec_type": "STK"}]
    html = render_import_detail("x", "y", entry, rows, None)
    assert "10,000" in html and "9,000" in html and "1,000" in html   # stated/summed/Δ


def test_file_adapter_gets_full_picker_not_repull(tmp_path):
    # a file-based adapter (CSV scan / statement bundle) must offer the FULL file
    # picker to re-upload — never the live-pull metaphor
    _office(tmp_path)
    staging.record_pull(tmp_path, "adapter:morgan_stanley_bundle", "adapter",
                        "Morgan Stanley Prime Brokerage",
                        rows=[{"symbol": "AAPL", "value": 500, "account": "SMA", "sec_type": "STK"}],
                        refresh="auto", as_of="2026-09-09")
    write_imports_page(tmp_path)
    html = (tmp_path / "pages" / import_slug("adapter:morgan_stanley_bundle")).with_suffix(".html").read_text()
    assert 'action="/import/files"' in html and 'type="file"' in html    # full picker
    assert "Re-add file" in html and "Re-pull now" not in html
    assert "Re-scan disk" in html                                        # secondary re-read


def test_upload_framed_as_readd_file(tmp_path):
    _office(tmp_path)
    staging.record_pull(tmp_path, "upload:statement.csv", "upload", "statement.csv",
                        rows=[{"symbol": "MSFT", "value": 500, "sec_type": "STK"}],
                        refresh="manual", as_of="2026-09-01")
    write_imports_page(tmp_path)
    html = (tmp_path / "pages" / import_slug("upload:statement.csv")).with_suffix(".html").read_text()
    assert "Re-add file" in html and "Re-pull now" not in html


def test_imports_index_shows_manual_for_manual_only_adapter():
    from officekit.render_imports import render_imports
    disc = [{"name": "downloads_csv", "label": "Broker CSV exports on disk", "kind": "file",
             "auto": False, "found": True, "status": "ready", "detail": "8 rows",
             "can_fetch": True, "guidance": None}]
    html = render_imports(disc, [], [], [], pull_endpoint="/adapter/import")
    assert ">manual<" in html                                # refresh cell = manual, not auto
