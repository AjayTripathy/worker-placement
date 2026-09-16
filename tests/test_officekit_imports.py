"""Drop-anything imports: staging provenance, dedupe, the reconciliation gate,
the deterministic-first router, and the audit page."""
import json

from officekit import staging


def _pull(folder, sid, rows, as_of=None, refresh="manual", **kw):
    return staging.record_pull(folder, sid, kw.pop("kind", "upload"), sid, rows,
                               refresh=refresh, as_of=as_of, **kw)


def test_staging_dedupe_freshest_wins_and_overlaps_surface(tmp_path):
    _pull(tmp_path, "upload:old.pdf", [{"symbol": "MNDY", "value": 7000, "sec_type": "STK", "account": "U1"}],
          as_of="2026-08-01")
    _pull(tmp_path, "adapter:ibkr_socket", [{"symbol": "MNDY", "value": 8000, "sec_type": "STK", "account": "U1"},
                                            {"symbol": "VTI", "value": 100, "sec_type": "STK", "account": "U1"}],
          as_of="2026-09-05", kind="adapter", refresh="auto")
    rows, overlaps = staging.merged_rows(tmp_path)
    mndy = next(r for r in rows if r["symbol"] == "MNDY")
    assert mndy["value"] == 8000 and mndy["source_id"] == "adapter:ibkr_socket"
    assert mndy["refresh"] == "auto"
    assert overlaps == [{"symbol": "MNDY", "kept": "adapter:ibkr_socket",
                         "displaced": ["upload:old.pdf"]}]
    src = staging.source_of(tmp_path, "mndy")
    assert src["source_id"] == "adapter:ibkr_socket" and src["as_of"] == "2026-09-05"
    assert staging.source_of(tmp_path, "TYPED") is None      # manual = no source, by design


def test_staging_repull_replaces_not_stacks(tmp_path):
    _pull(tmp_path, "upload:s.pdf", [{"symbol": "A", "value": 1}], as_of="2026-09-01")
    _pull(tmp_path, "upload:s.pdf", [{"symbol": "B", "value": 2}], as_of="2026-09-05")
    rows, _ = staging.merged_rows(tmp_path)
    assert [r["symbol"] for r in rows] == ["B"]
    assert staging.ledger(tmp_path)[0]["n_rows"] == 1


def test_cash_rows_never_dedupe_across_sources(tmp_path):
    _pull(tmp_path, "adapter:a", [{"symbol": "CASH", "value": 100, "sec_type": "CASH"}],
          as_of="2026-09-05", kind="adapter", refresh="auto")
    _pull(tmp_path, "upload:b.pdf", [{"symbol": "CASH", "value": 200, "sec_type": "CASH"}],
          as_of="2026-09-04")
    rows, overlaps = staging.merged_rows(tmp_path)
    assert len([r for r in rows if r["symbol"] == "CASH"]) == 2 and not overlaps


def test_generic_account_label_does_not_erase_independent_holdings(tmp_path):
    # Scenario C: two DIFFERENT brokers that both default their account label to
    # the generic 'brokerage' — independent $100 and $200 AAPL positions must NOT
    # collapse to $200 (an erased holding). They stay distinct and sum to $300.
    _pull(tmp_path, "adapter:broker1", [{"symbol": "AAPL", "value": 100, "sec_type": "STK",
          "account": "brokerage"}], as_of="2026-09-01", kind="adapter", refresh="auto")
    _pull(tmp_path, "adapter:broker2", [{"symbol": "AAPL", "value": 200, "sec_type": "STK",
          "account": "brokerage"}], as_of="2026-09-02", kind="adapter", refresh="auto")
    rows, overlaps = staging.merged_rows(tmp_path)
    aapl = [r for r in rows if r["symbol"] == "AAPL"]
    assert len(aapl) == 2 and not overlaps                 # both kept, nothing displaced
    assert sum(r["value"] for r in aapl) == 300

    from officekit.reconciliation import reconcile
    res, _ = reconcile({}, rows, staging.load(tmp_path)["sources"])
    row = next(r for r in res["positions"]["rows"] if r["symbol"] == "AAPL")
    assert row["value"] == 300 and len(row["accounts"]) == 2


def test_real_account_number_still_dedupes_across_feeds(tmp_path):
    # The fix must NOT break the intended supersede: a live feed replacing a stale
    # statement of the SAME real custodial account (a unique id) still dedupes.
    _pull(tmp_path, "upload:stmt.pdf", [{"symbol": "AAPL", "value": 100, "sec_type": "STK",
          "account": "ACCOUNT_ALPHA"}], as_of="2026-09-01")
    _pull(tmp_path, "adapter:ibkr", [{"symbol": "AAPL", "value": 200, "sec_type": "STK",
          "account": "ACCOUNT_ALPHA"}], as_of="2026-09-02", kind="adapter", refresh="auto")
    rows, overlaps = staging.merged_rows(tmp_path)
    aapl = [r for r in rows if r["symbol"] == "AAPL"]
    assert len(aapl) == 1 and aapl[0]["value"] == 200      # freshest wins
    assert overlaps and overlaps[0]["displaced"] == ["upload:stmt.pdf"]


def test_specific_account_classifier():
    assert not staging.specific_account("brokerage") and not staging.specific_account("")
    assert not staging.specific_account("Portfolio") and not staging.specific_account("  manual ")
    assert staging.specific_account("ACCOUNT_ALPHA") and staging.specific_account("A")


def test_extract_reconciliation_gate():
    from officekit_ai.extract import reconcile
    clean = {"rows": [{"symbol": "VTI", "value": 26000, "confidence": 0.95},
                      {"symbol": "VWLUX", "value": 55000, "confidence": 0.9}],
             "stated_total": 81000, "notes": []}
    assert reconcile(clean) == []
    off = dict(clean, stated_total=95000)
    w = reconcile(off)
    assert any("81,000.00 but the document states 95,000.00" in x for x in w)
    assert any("UNRECONCILED" in x for x in reconcile(dict(clean, stated_total=None)))
    lowc = dict(clean, rows=clean["rows"] + [{"symbol": "GUESS", "value": 1, "confidence": 0.3}],
                stated_total=81001)
    assert any("low-confidence" in x for x in reconcile(lowc))


def test_extract_refuses_unknown_types_and_truncation(tmp_path):
    import pytest
    from types import SimpleNamespace
    from officekit_ai.extract import extract_file
    with pytest.raises(ValueError, match="unsupported"):
        extract_file("notes.docx", b"x", client=object(), model="m")
    trunc = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: SimpleNamespace(
        stop_reason="max_tokens", content=[])))
    with pytest.raises(RuntimeError, match="truncated"):
        extract_file("s.pdf", b"%PDF", client=trunc, model="m")


def test_extract_file_reconciles_via_fake_client():
    from types import SimpleNamespace
    from officekit_ai.extract import extract_file
    payload = {"account_label": "Fidelity ...1234", "as_of": "2026-08-31",
               "stated_total": 81000.0, "currency": "USD", "notes": ["page 2 cropped"],
               "rows": [{"symbol": "VTI", "description": "VANGUARD TOTAL", "qty": 100,
                         "value": 26000.0, "confidence": 0.97}]}
    calls = []

    def create(**kw):
        calls.append(kw)
        return SimpleNamespace(stop_reason="end_turn",
                               content=[SimpleNamespace(type="text", text=json.dumps(payload))])

    cl = SimpleNamespace(messages=SimpleNamespace(create=create))
    out = extract_file("statement.pdf", b"%PDF-1.4", client=cl, model="m")
    assert calls[0]["messages"][0]["content"][0]["type"] == "document"   # pdf -> document block
    assert any("55,000" in w or "document states" in w for w in out["warnings"])  # rows don't foot
    assert any("extractor note: page 2 cropped" in w for w in out["warnings"])


def test_router_csv_is_deterministic_no_model(tmp_path):
    from officekit.serve import import_files

    class Part:
        filename = "Portfolio_Positions.csv"
        import io
        file = io.BytesIO(b"Symbol,Description,Quantity,Current Value\n"
                          b"VTI,VANGUARD TOTAL,100,26000.00\n")
    res = import_files(tmp_path, [Part()])
    assert "exact CSV parse" in res[0]
    led = staging.ledger(tmp_path)
    assert led[0]["refresh"] == "manual" and led[0]["n_rows"] == 1
    assert "no model" in led[0]["detail"]


def test_imports_page_renders_ledger_and_asset_map(tmp_path):
    from officekit.render_imports import render_imports
    _pull(tmp_path, "upload:fid.pdf", [{"symbol": "VTI", "value": 26000, "sec_type": "STK", "account": "U1"}],
          as_of="2026-08-31", stated_total=95000.0,
          warnings=["rows sum to 26,000.00 but the document states 95,000.00"])
    _pull(tmp_path, "adapter:ibkr_socket", [{"symbol": "VTI", "value": 26500, "sec_type": "STK", "account": "U1"}],
          as_of="2026-09-05", kind="adapter", refresh="auto")
    rows, overlaps = staging.merged_rows(tmp_path)
    disc = [{"name": "ibkr_socket", "label": "Interactive Brokers — TWS / IB Gateway",
             "kind": "broker", "found": True, "status": "ready",
             "detail": "IB Gateway (live) on 127.0.0.1:4001", "guidance": None, "can_fetch": True}]
    h = render_imports(disc, staging.ledger(tmp_path), rows, overlaps)
    assert "Your connections" in h and "Interactive Brokers" in h
    assert "fid.pdf" in h and "manual" in h and "auto" in h
    assert "document states 95,000.00" in h                  # warning shown, not buried
    assert "also in upload:fid.pdf" in h                     # the asset's full supply trail
    assert "$95,000" in h                                    # stated total column


def test_derivatives_dedupe_by_contract_not_symbol(tmp_path):
    # the live $14k lesson: QCOM 135P and 140P are DIFFERENT obligations
    _pull(tmp_path, "adapter:ib", [
        {"symbol": "QCOM", "value": -10, "sec_type": "OPT", "description": "QCOM 20260918 140.0P", "account": "U1"},
        {"symbol": "QCOM", "value": -5, "sec_type": "OPT", "description": "QCOM 20260918 135.0P", "account": "U1"},
        {"symbol": "QCOM", "value": 5000, "sec_type": "STK", "account": "U1"},
    ], as_of="2026-09-05", kind="adapter", refresh="auto")
    rows, overlaps = staging.merged_rows(tmp_path)
    assert len(rows) == 3 and not overlaps
    # the SAME contract from two sources still dedupes
    _pull(tmp_path, "upload:s.pdf", [
        {"symbol": "QCOM", "value": -11, "sec_type": "OPT", "description": "QCOM 20260918 140.0P", "account": "U1"}],
        as_of="2026-08-31")
    rows, overlaps = staging.merged_rows(tmp_path)
    assert len(rows) == 3
    assert overlaps and overlaps[0]["kept"] == "adapter:ib"


def test_proposed_assets_carry_provenance_and_are_superseded_by_live(tmp_path):
    # a court-proposed purchase is a SOURCE like any pipeline pull
    _pull(tmp_path, "proposed:japan_value:8035", [{"symbol": "8035", "value": 5000,
                                                   "sec_type": "STK", "account": "U1"}],
          as_of="2026-09-05", kind="proposed",
          detail="adjudication ab12cd34 — STARTER 6/10 (EVIDENCED)")
    src = staging.source_of(tmp_path, "8035")
    assert src["source_kind"] == "proposed" and src["refresh"] == "manual"
    # the live connection later confirms the position — freshest wins, proposal superseded
    _pull(tmp_path, "adapter:ibkr_socket", [{"symbol": "8035", "value": 5100,
                                             "sec_type": "STK", "account": "U1"}],
          as_of="2026-09-06", kind="adapter", refresh="auto")
    src = staging.source_of(tmp_path, "8035")
    assert src["source_kind"] == "adapter" and src["refresh"] == "auto"
    rows, overlaps = staging.merged_rows(tmp_path)
    assert overlaps[0]["displaced"] == ["proposed:japan_value:8035"]


def test_imports_page_shows_proposed_section(tmp_path):
    from officekit.render_imports import render_imports
    _pull(tmp_path, "proposed:japan_value:8035", [{"symbol": "8035", "value": 5000,
                                                   "sec_type": "STK"}],
          as_of="2026-09-05", kind="proposed",
          detail="adjudication ab12cd34 — STARTER 6/10 (EVIDENCED)")
    rows, overlaps = staging.merged_rows(tmp_path)
    h = render_imports([], staging.ledger(tmp_path), rows, overlaps)
    assert "Proposed — born from a court verdict" in h
    assert "adjudication ab12cd34 — STARTER 6/10" in h
    assert "8035" in h


def test_key_status_and_source_classes(monkeypatch, tmp_path):
    from officekit import serve
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: tmp_path))
    ks = serve._key_status()
    assert not ks["attached"] and "Attach one" in ks["label"]
    (tmp_path / ".anthropic_key").write_text("sk-ant-x\n")
    ks = serve._key_status()
    assert ks["attached"] and "imported from ~/.anthropic_key" in ks["label"]
    # staged rows map refresh mode -> row class
    rows = [{"symbol": "A", "value": 1, "sec_type": "STK", "refresh": "auto",
             "source_id": "adapter:x", "description": "", "account": "u", "ccy": "USD"},
            {"symbol": "B", "value": 2, "sec_type": "STK", "refresh": "manual",
             "source_id": "upload:s.pdf", "description": "", "account": "u", "ccy": "USD"},
            {"symbol": "C", "value": 3, "sec_type": "STK",
             "description": "", "account": "u", "ccy": "USD"}]
    prefill, _ = serve.adapter_prefill(rows)
    assert [r[4] for r in prefill] == ["src-auto", "src-manual", ""]


def test_imports_page_key_row_and_pull_now(tmp_path):
    from officekit.render_imports import render_imports
    disc = [{"name": "ibkr_socket", "label": "Interactive Brokers — TWS / IB Gateway",
             "kind": "broker", "found": True, "status": "ready",
             "detail": "IB Gateway (live)", "guidance": None, "can_fetch": True}]
    h = render_imports(disc, [], [], [], key_status={"attached": False,
                       "label": "not attached — agents disabled. Attach one: ..."},
                       pull_endpoint="/adapter/import")
    assert "AI model key" in h and "needs attaching" in h
    assert "Pull now" in h and 'name="back" value="imports"' in h
    assert "Connected sources refresh daily" in h
    h2 = render_imports(disc, [], [], [], key_status={"attached": True,
                        "label": "imported from ~/.anthropic_key"})
    assert "attached" in h2 and "Pull now" not in h2   # no endpoint, no button


def test_dropzone_mentions_screenshots_and_prompts_for_key(monkeypatch, tmp_path):
    from officekit import serve
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: tmp_path))
    h = serve._dropzone_html()
    assert "screenshots" in h.lower()
    assert "need an agent key first" in h
    (tmp_path / ".anthropic_key").write_text("sk-ant-x\n")
    h2 = serve._dropzone_html()
    assert "screenshots" in h2.lower() and "need an agent key" not in h2
    assert "imported from ~/.anthropic_key" in h2


def test_dropzone_is_a_single_drag_and_drop_zone_supporting_folders():
    from officekit import serve
    h = serve._dropzone_html()
    assert 'class="dz"' in h and 'id="dzinput"' in h          # one drop zone, one input
    assert h.count('name="docs"') == 1                        # not two inputs anymore
    assert "Drag files or a folder here" in h                 # folder support stated
    assert "scanned recursively" in h
    assert "webkitGetAsEntry" in serve._DROPZONE_JS           # folders read via the entry API
    assert "readEntries" in serve._DROPZONE_JS                # recursion is paginated correctly
    assert "DataTransfer" in serve._DROPZONE_JS               # files pushed back to the form input


def test_adapter_import_empty_field_falls_back_to_single_ready(monkeypatch, tmp_path):
    # the KeyError-on-empty-adapter class: a dropped hidden field must not crash
    import io, time
    import officekit_adapters as A
    from officekit import serve
    monkeypatch.setitem(serve._DISCOVERY_CACHE, "ts", time.time())
    monkeypatch.setitem(serve._DISCOVERY_CACHE, "results", [
        {"name": "ibkr_socket", "label": "IBKR", "kind": "broker", "found": True,
         "status": "ready", "detail": "up", "guidance": None, "can_fetch": True}])
    monkeypatch.setattr(A, "fetch_positions",
                        lambda n, ctx=None: [{"symbol": "VTI", "value": 100, "sec_type": "STK"}]
                        if n == "ibkr_socket" else (_ for _ in ()).throw(KeyError(n)))
    # resolve the fallback exactly as the handler does
    ready = [r for r in serve._discover_cached()
             if r["found"] and r["can_fetch"] and r["status"] == "ready"]
    assert len(ready) == 1 and ready[0]["name"] == "ibkr_socket"
    rows = A.fetch_positions(ready[0]["name"])
    assert rows[0]["symbol"] == "VTI"


def test_import_files_folder_filters_junk_and_dedupes(tmp_path, monkeypatch):
    import io
    from officekit import serve, staging

    class Part:
        def __init__(self, fn, data):
            self.filename = fn
            self.file = io.BytesIO(data)

    csv = b"Symbol,Description,Quantity,Current Value\nVTI,VANGUARD,100,26000.00\n"
    parts = [
        Part("statements/fidelity.csv", csv),         # webkitdirectory path -> basename
        Part("statements/notes.txt", b"junk"),        # unsupported -> ignored
        Part("statements/logo.svg", b"<svg/>"),       # unsupported -> ignored
        Part("fidelity.csv", csv),                     # dup basename from the files input -> deduped
        Part("statements/.DS_Store", b"\x00"),         # junk -> ignored
    ]
    res = serve.import_files(tmp_path, parts)
    joined = " | ".join(res)
    assert "fidelity.csv: 1 rows (exact CSV parse)" in joined
    assert "ignored 3 unsupported file(s)" in joined
    # only one source recorded (dedupe worked)
    assert [s for s in staging.load(tmp_path)["sources"]] == ["upload:fidelity.csv"]


def test_import_files_empty_selection_message(tmp_path):
    from officekit import serve
    assert serve.import_files(tmp_path, []) == ["no readable statements/screenshots/CSVs in the selection"]


def test_adapters_panel_and_key_always_show_even_with_no_connection(monkeypatch):
    # regression 2026-09-06: the AI-key display vanished whenever no broker was found
    from officekit import serve
    monkeypatch.setitem(serve._DISCOVERY_CACHE, "ts", 9e18)
    monkeypatch.setitem(serve._DISCOVERY_CACHE, "results", [])   # nothing detected
    h = serve._adapters_html()
    assert "Detected connections" in h and "AI model key" in h
    assert "Import positions" not in h
    # a near-miss (needs_key) surfaces its guidance without a fake import button
    monkeypatch.setitem(serve._DISCOVERY_CACHE, "results", [
        {"name": "alpaca", "label": "Alpaca", "kind": "broker", "found": False,
         "status": "needs_key", "detail": "no keys", "guidance": "export Alpaca keys",
         "can_fetch": True}])
    h2 = serve._adapters_html()
    assert "Alpaca" in h2 and "export Alpaca keys" in h2 and "AI model key" in h2
    assert "Import positions" not in h2


def test_extract_streams_with_timeout_and_fake_fallback():
    from types import SimpleNamespace
    from officekit_ai import extract
    import json as _json
    payload = {"account_label": "X", "as_of": None, "stated_total": None,
               "currency": "USD", "notes": [], "rows": []}

    # a streaming client: _create must use .stream and pass a timeout
    seen = {}
    class Stream:
        def __enter__(s): return s
        def __exit__(s, *a): return False
        def get_final_message(s):
            return SimpleNamespace(stop_reason="end_turn",
                                   content=[SimpleNamespace(type="text", text=_json.dumps(payload))])
    def stream(**kw): seen.update(kw); return Stream()
    cl = SimpleNamespace(messages=SimpleNamespace(stream=stream))
    extract.extract_file("s.pdf", b"%PDF", client=cl, model="m", timeout=42)
    assert seen["timeout"] == 42                       # hard per-document timeout applied
    assert seen["max_tokens"] == 16000

    # a minimal fake (create only, no stream, ignores timeout) still works
    def create(**kw):
        return SimpleNamespace(stop_reason="end_turn",
                               content=[SimpleNamespace(type="text", text=_json.dumps(payload))])
    cl2 = SimpleNamespace(messages=SimpleNamespace(create=create))
    out = extract.extract_file("s.png", b"x", client=cl2, model="m")
    assert out["rows"] == []


def test_import_files_processes_all_via_bounded_concurrency(tmp_path):
    # "12 at a time" = bounded concurrency draining the whole queue, no deferral
    import io, threading, time
    from officekit import serve, staging
    live = {"now": 0, "peak": 0}
    lock = threading.Lock()

    def fake_extract(name, data, folder=None, **kw):
        with lock:
            live["now"] += 1; live["peak"] = max(live["peak"], live["now"])
        time.sleep(0.05)                                # hold the slot so overlap is real
        with lock:
            live["now"] -= 1
        return {"rows": [{"symbol": name.split(".")[0], "value": 1}], "as_of": None,
                "stated_total": None, "currency": "USD", "warnings": []}
    import officekit_ai.extract as ex
    orig = ex.extract_file
    ex.extract_file = fake_extract
    try:
        class P:
            def __init__(s, fn): s.filename = fn; s.file = io.BytesIO(b"%PDF")
        parts = [P(f"stmt{i}.pdf") for i in range(30)]     # 30 model-bound docs
        res = serve.import_files(tmp_path, parts)
    finally:
        ex.extract_file = orig
    # ALL 30 processed (no deferral), concurrency held at/under 12
    assert len([r for r in res if "via extraction" in r]) == 30
    assert live["peak"] <= 12 and live["peak"] > 1
    assert len([s for s in staging.load(tmp_path)["sources"]]) == 30
    assert not any("deferred" in r for r in res)


def test_same_source_duplicate_symbols_never_dedupe(tmp_path):
    # the Parametric $2.7M bug (2026-09-06): a statement's two USD cash legs
    # (+2.70M and -2.71M) are distinct lines, not duplicates — both must survive
    _pull(tmp_path, "upload:parametric.csv", [
        {"symbol": "USD", "value": -2707818.34, "sec_type": "STK", "account": None},
        {"symbol": "USD", "value": 2700363.74, "sec_type": "STK", "account": None},
        {"symbol": "AAON", "value": -6501.38, "sec_type": "STK", "account": None},
        {"symbol": "AAON", "value": 100.0, "sec_type": "STK", "account": None},  # 2 AAON lines, 1 source
    ], as_of="2026-07-31")
    rows, overlaps = staging.merged_rows(tmp_path)
    assert len(rows) == 4 and not overlaps                 # nothing collapsed
    assert round(sum(float(r["value"]) for r in rows), 2) == round(-2707818.34+2700363.74-6501.38+100.0, 2)


def test_same_ticker_different_accounts_both_kept(tmp_path):
    # AAPL in a taxable IBKR account AND a Parametric SMA = 2x exposure, not a dup
    _pull(tmp_path, "adapter:ibkr", [{"symbol": "AAPL", "value": 10000, "sec_type": "STK",
                                      "account": "ACCOUNT_ALPHA"}],
          as_of="2026-09-05", kind="adapter", refresh="auto")
    _pull(tmp_path, "upload:parametric.csv", [{"symbol": "AAPL", "value": 4000, "sec_type": "STK",
                                               "account": "038CAG"}],
          as_of="2026-07-31")
    rows, overlaps = staging.merged_rows(tmp_path)
    assert len([r for r in rows if r["symbol"] == "AAPL"]) == 2      # both accounts
    assert sum(float(r["value"]) for r in rows) == 14000
    assert not overlaps                                    # different accounts ≠ overlap


def test_concurrent_record_pull_no_lost_update(tmp_path):
    # the folder+IBKR-at-once bug: concurrent read-modify-write must not drop a source
    import threading
    from officekit import staging

    def add(i):
        staging.record_pull(tmp_path, f"src{i}", "upload", f"f{i}.csv",
                            [{"symbol": f"S{i}", "value": i, "account": "U1"}], refresh="manual")

    threads = [threading.Thread(target=add, args=(i,)) for i in range(40)]
    for t in threads: t.start()
    for t in threads: t.join()
    sources = staging.load(tmp_path)["sources"]
    assert len(sources) == 40                               # every concurrent pull survived
    assert set(sources) == {f"src{i}" for i in range(40)}


def test_staging_json_never_torn_under_concurrency(tmp_path):
    # atomic write: a reader mid-storm always parses valid JSON
    import threading, json as _json
    from officekit import staging
    bad = []

    def writer(i):
        for _ in range(5):
            staging.record_pull(tmp_path, f"w{i}", "upload", "x",
                                [{"symbol": "A", "value": 1, "account": "U1"}], refresh="manual")

    def reader():
        for _ in range(50):
            try:
                _json.loads((tmp_path / "staging.json").read_text())
            except FileNotFoundError:
                pass
            except Exception as e:
                bad.append(str(e))

    ts = [threading.Thread(target=writer, args=(i,)) for i in range(8)] + \
         [threading.Thread(target=reader) for _ in range(4)]
    for t in ts: t.start()
    for t in ts: t.join()
    assert not bad, f"torn reads: {bad[:3]}"


def test_import_totals_block_by_source(tmp_path):
    from officekit import serve
    _pull(tmp_path, "adapter:ibkr_socket",
          [{"symbol": "MNDY", "value": 8000, "sec_type": "STK", "account": "U1"},
           {"symbol": "CASH", "value": -500, "sec_type": "CASH", "account": "U1"}],
          as_of="2026-09-06", kind="adapter", refresh="auto")
    _pull(tmp_path, "upload:parametric.csv",
          [{"symbol": "AAPL", "value": 4000, "sec_type": "STK", "account": "038"},
           {"symbol": "USD", "value": -100, "sec_type": "STK", "account": None}],
          as_of="2026-07-31")
    h = serve._import_totals_html(tmp_path)
    assert "check each against its statement" in h
    assert "ibkr_socket" in h and "$7,500" in h and "live connection" in h
    assert "parametric.csv" in h and "$3,900" in h and "uploaded document" in h
    assert "Everything" in h and "$11,400" in h              # grand total
    assert 'id="imptot-typed"' in h                          # live typed/agent line
    assert "src-auto" in h and "src-manual" in h            # refresh classes carried
    empty = serve._import_totals_html(tmp_path / "empty")   # nothing staged
    assert 'id="imptot-typed"' in empty and "$0" in empty   # scaffold present, JS hides when empty


def test_remove_source_and_totals_remove_button(tmp_path):
    from officekit import staging, serve
    _pull(tmp_path, "upload:a.csv", [{"symbol": "VTI", "value": 100, "account": "U1"}])
    _pull(tmp_path, "adapter:ibkr_socket", [{"symbol": "MNDY", "value": 50, "account": "U1"}],
          as_of="2026-09-06", kind="adapter", refresh="auto")
    h = serve._import_totals_html(tmp_path)
    assert h.count('action="/import/remove"') == 2               # a remove per source
    assert 'name="source_id" value="upload:a.csv"' in h
    assert staging.remove_source(tmp_path, "upload:a.csv") is True
    assert list(staging.load(tmp_path)["sources"]) == ["adapter:ibkr_socket"]
    assert staging.remove_source(tmp_path, "nope") is False      # idempotent-safe


def test_holdings_rows_have_remove_buttons():
    from officekit.serve import _urows_html
    h = _urows_html(n=2, prefill=[("ticker", "MNDY", 50, "", "src-auto")])
    assert h.count("removeURow(this)") == 3                       # 1 prefilled + 2 blank
    assert h.count('class="rmrow"') == 3


def test_asset_spanning_multiple_sources_totals_and_breaks_out(tmp_path):
    from officekit import staging
    from officekit.render_imports import render_imports
    staging.record_pull(tmp_path, "adapter:ibkr", "adapter", "IBKR",
        [{"symbol": "AAPL", "value": 10000, "sec_type": "STK", "account": "ACCOUNT_ALPHA"},
         {"symbol": "MNDY", "value": 8000, "sec_type": "STK", "account": "ACCOUNT_ALPHA"}],
        refresh="auto", as_of="2026-09-06")
    staging.record_pull(tmp_path, "upload:parametric.csv", "upload", "parametric.csv",
        [{"symbol": "AAPL", "value": 4000, "sec_type": "STK", "account": "038CAG"}],
        refresh="manual", as_of="2026-07-31")
    # sources_of gives every source + a combined asset_total
    ss = staging.sources_of(tmp_path, "AAPL")
    assert len(ss) == 2 and ss[0]["asset_total"] == 14000
    assert {s["source_id"] for s in ss} == {"adapter:ibkr", "upload:parametric.csv"}
    assert staging.source_of(tmp_path, "AAPL")["value"] == 10000   # primary = largest
    # the asset map totals AAPL once and breaks out each account beneath it
    rows, overlaps = staging.merged_rows(tmp_path)
    seg = render_imports([], staging.ledger(tmp_path), rows, overlaps)
    seg = seg[seg.index("Asset source map"):]
    assert "<b>AAPL</b>" in seg and "2 sources" in seg and "14,000" in seg  # combined
    assert "ACCOUNT_ALPHA" in seg and "038CAG" in seg              # per-account breakout
    assert "combined across accounts" in seg


def test_num_coercion():
    from officekit.staging import num
    assert num("1,234.56") == 1234.56
    assert num("$1,234") == 1234.0
    assert num("($9,000.00)") == -9000.0            # accounting negative
    assert num("−500") == -500.0                     # unicode minus
    assert num(None) == 0.0 and num("garbage") == 0.0
    assert num(42) == 42.0 and num(3.5) == 3.5


def test_dirty_screenshot_row_never_breaks_the_office(tmp_path):
    # the Vanguard-screenshot bug: a dirty extracted row poisoned every render
    from officekit import staging, serve
    staging.record_pull(tmp_path, "adapter:ibkr", "adapter", "IBKR",
        [{"symbol": "MNDY", "value": 8000, "sec_type": "STK", "account": "U1"}],
        refresh="auto", as_of="2026-09-06")
    dirty = [{"symbol": "VTSAX", "value": "1,234.56", "sec_type": "STK"},   # string value
             {"symbol": None, "value": 5000, "sec_type": "STK"},           # None symbol
             {"symbol": "VMFXX", "value": None, "sec_type": "STK"},        # None value
             {"symbol": "VFIAX", "value": "($9,000)", "account": {"x": 1}},# acct dict + acct-neg str
             "not a dict"]                                                  # malformed entirely
    staging.record_pull(tmp_path, "upload:vanguard.png", "upload", "vanguard.png",
                        dirty, refresh="manual", as_of="2026-09-06")
    # sanitized at the gate: no bad type survives in staging
    vals = [r["value"] for s in staging.load(tmp_path)["sources"].values() for r in s["rows"]]
    assert all(isinstance(v, float) for v in vals)
    # every render-path reader survives AND the other position is intact
    merged, _ = staging.merged_rows(tmp_path)
    assert any(r["symbol"] == "MNDY" for r in merged)
    pf, _ = serve.staged_prefill(tmp_path)
    assert ("ticker", "VTSAX", 1234.56, "", "src-manual") in pf
    assert ("ticker", "VFIAX", -9000.0, "", "src-manual") in pf
    serve._import_totals_html(tmp_path)              # must not raise
    staging.sources_of(tmp_path, "VTSAX")           # must not raise


def test_build_conserves_value_no_row_dropped(tmp_path):
    # build#1/#2: a BOND and a blank-symbol line counted in totals must ALSO be
    # placed in the form so the built office matches (the $11,735 class)
    from officekit import serve
    rows = [{"symbol": "VTI", "value": 26000, "sec_type": "STK", "account": "U1", "refresh": "auto", "source_id": "adapter:x"},
            {"symbol": "", "value": 11735, "sec_type": "STK", "description": "USD cash balance", "account": "U1", "refresh": "auto", "source_id": "adapter:x"},
            {"symbol": "T2050", "value": 50000, "sec_type": "BOND", "account": "U1", "refresh": "auto", "source_id": "adapter:x"}]
    prefill, note = serve.adapter_prefill(rows)
    placed_total = sum(p[2] for p in prefill)
    assert placed_total == 26000 + 11735 + 50000     # nothing dropped
    cats = {p[0] for p in prefill}
    assert "fixed_income" in cats and "cash" in cats  # bond->FI, blank cash line->cash
    assert "Placed" in note and "Skipped" not in note


def test_money_never_raises_on_junk():
    from officekit.serve import _money
    for junk in ("TBD", "~500k", "call broker", "10%", "abc", "inf", "nan", ""):
        assert _money(junk) in (None,) or isinstance(_money(junk), float)
    assert _money("$1,234") == 1234.0 and _money("500k") == 500000.0
    assert _money("nan") is None and _money("inf") is None   # never poison JSON


def test_classify_positions_tolerates_strings_and_zero_net(tmp_path):
    from officekit.importers import classify_positions
    # string value must not crash; net-zero must not ZeroDivisionError
    sleeves = classify_positions([{"symbol": "AAPL", "value": "1,234"},
                                  {"symbol": "MSFT", "value": 5000},
                                  {"symbol": "SHORTX", "value": -5000}], account="b")
    assert sleeves  # built without raising


def test_extract_non_usd_flagged(tmp_path):
    import json as _json
    from types import SimpleNamespace
    from officekit_ai.extract import extract_file
    payload = {"account_label": "Nomura", "as_of": "2026-08-31", "stated_total": 100000000.0,
               "currency": "JPY", "notes": [],
               "rows": [{"symbol": "8035", "description": "", "qty": 100, "value": 100000000.0, "confidence": 0.9}]}
    cl = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: SimpleNamespace(
        stop_reason="end_turn", content=[SimpleNamespace(type="text", text=_json.dumps(payload))])))
    out = extract_file("nomura.png", b"x", client=cl, model="m")
    assert out["rows"][0]["ccy"] == "JPY"
    assert any("not USD" in w and "NOT converted" in w for w in out["warnings"])


def test_build_office_atomic_on_render_failure(tmp_path, monkeypatch):
    # a render failure must NOT leave a half-built office (no balance_sheet without pages)
    from officekit import serve
    answers = {"owner": "T", "as_of": "2026-09-06",
               "positions": {"account": "b", "rows": [{"symbol": "VTI", "value": 26000}]},
               "sleeves": [], "profile": {}, "goals": []}
    import officekit.serve as S
    monkeypatch.setattr(S, "render_strategies", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    import pytest
    with pytest.raises(RuntimeError):
        serve.build_office(answers, tmp_path)
    # nothing written — the office stays unbuilt, not half-built
    assert not (tmp_path / "balance_sheet.json").exists()
    assert not (tmp_path / "pages" / "office.html").exists()


def test_extract_rows_dedupe_by_account_across_filenames(tmp_path):
    # re-uploading the same account under a different filename must not double-count
    from officekit import staging
    for fn in ("vanguard.pdf", "vanguard_2026.pdf"):
        staging.record_pull(tmp_path, f"upload:{fn}", "upload", fn,
                            [{"symbol": "VTSAX", "value": 50000, "sec_type": "STK",
                              "account": "Vanguard ...9876"}],
                            refresh="manual", as_of="2026-08-31")
    rows, overlaps = staging.merged_rows(tmp_path)
    assert len([r for r in rows if r["symbol"] == "VTSAX"]) == 1   # deduped, not doubled
    assert overlaps and overlaps[0]["symbol"] == "VTSAX"


def test_options_overlay_has_nonzero_market_beta():
    from officekit.betas import default_beta
    b = default_beta("options_overlay")
    assert b["S&P 500"] != 0.0                        # not modeled market-neutral


def test_mortgage_rate_beta_fixed_hedges_arm_compounds():
    from officekit.intake import build_from_answers
    from officekit.model import build_model
    def rates_agg(style):
        d = build_from_answers({"owner": "T", "as_of": "2026-09-07", "profile": {}, "goals": [],
            "sleeves": [{"category": "real_estate", "name": "Home", "value": 1200000},
                        {"category": "real_estate_debt", "name": "M", "value": 720000, "style": style}]})
        return build_model(d)["agg"]["Rates"]
    # fixed mortgage HEDGES the home's rate exposure; ARM COMPOUNDS it
    assert rates_agg("fixed") > rates_agg("arm")
    from officekit.betas import default_beta
    assert default_beta("real_estate_debt")["Rates"] < 0        # fixed default = short-bond


def test_mortgage_style_inferred_from_name_and_rate_pct_parses():
    from officekit.serve import answers_from_form
    from officekit.formdata import Form
    import pathlib
    def mort(name, rate):
        f = {"owner": ["T"], "as_of": ["x"], "account": ["b"],
             "u_kind": ["real_estate", "real_estate_debt"], "u_name": ["Home", name],
             "u_value": ["1200000", "720000"], "u_rate": ["", rate]}
        a = answers_from_form(Form(f), pathlib.Path("/tmp"))
        return next(s for s in a["sleeves"] if s["category"] == "real_estate_debt")
    assert mort("Mortgage", "6.5%")["style"] == "fixed"
    assert mort("Mortgage (ARM)", "6.5%")["style"] == "arm"
    assert mort("Mortgage", "6.5%")["rate_pct"] == 6.5          # % no longer crashes


def test_windfall_and_tax_harvest_goal_from_form(tmp_path):
    from officekit.serve import answers_from_form
    from officekit.formdata import Form
    from officekit.intake import build_from_answers
    from officekit.schema import validate
    from officekit.goal_mandates import goal_strategy_menu
    from officekit.model import build_model
    f = {"owner": ["T"], "as_of": ["2026-09-07"], "account": ["b"],
         "u_kind": ["real_estate"], "u_name": ["Home"], "u_value": ["1200000"], "u_rate": [""],
         "wind_amount": ["500000"], "wind_eta": ["2026-09"], "wind_character": ["ltcg"],
         "goal_taxharvest": ["1"]}
    a = answers_from_form(Form(f), tmp_path)
    # windfall captured as an asset (incoming), harvest captured as a goal
    assert a["incoming"]["amount"] == 500000.0
    assert any(g["kind"] == "tax_efficiency" for g in a["goals"])
    data = build_from_answers(a)
    assert validate(data) == []                              # amountless tax goal is valid
    m = build_model(data)
    menu = goal_strategy_menu(m, None)
    entry = next(iter(menu.values()))
    assert entry["goal"]["kind"] == "tax_efficiency"
    assert entry["eval"]["status"] == "OK"                   # ongoing objective, not "short"
    opts = [o["sid"] for o in entry["options"]]
    assert "direct_index" in opts                            # offers lot-level harvesting
    assert entry["options"][0]["sid"] == "direct_index"      # primary = the harvesting strategy


def test_tax_efficiency_goal_evaluates_as_ongoing():
    from officekit.goals import evaluate
    ev = evaluate({"kind": "tax_efficiency", "label": "Harvest"}, 1_000_000, 500_000, "2026-09-07")
    assert ev["status"] == "OK" and ev["target_txt"] == "ongoing"   # never renders as underfunded


def test_capital_gain_never_books_tax_free():
    from officekit.intake import build_from_answers
    from officekit.model import build_model
    def nw_and_reserve(inc):
        d = build_from_answers({"owner": "T", "as_of": "2026-09-07", "profile": {}, "goals": [],
            "sleeves": [{"category": "cash", "name": "C", "value": 100000}], "incoming": inc})
        m = build_model(d)
        res = next((s["value"] for s in m["sleeves"] if s["category"] == "tax_reserve"), 0)
        return res, m["NW"], d["tax_model"]["rate_ltcg"], d["tax_model"]["rate_assumed"]
    # NO rate, no state -> conservative federal floor 23.8%, reserve applied
    res, nw, rate, assumed = nw_and_reserve({"amount": 5_000_000, "character": "ltcg", "eta": "Sep"})
    assert res == -1_190_000 and abs(rate - 0.238) < 1e-9 and assumed
    # state adds its top rate
    res, nw, rate, _ = nw_and_reserve({"amount": 5_000_000, "character": "ltcg", "state": "CA"})
    assert res == -1_855_000 and abs(rate - 0.371) < 1e-9        # 23.8 + 13.3
    # an exact rate overrides the floor and is NOT flagged assumed
    _, _, rate, assumed = nw_and_reserve({"amount": 5_000_000, "character": "ltcg", "rate": 0.30})
    assert abs(rate - 0.30) < 1e-9 and not assumed
    # return_of_capital is not taxed
    d = build_from_answers({"owner": "T", "as_of": "2026-09-07", "profile": {}, "goals": [],
        "sleeves": [{"category": "cash", "name": "C", "value": 100000}],
        "incoming": {"amount": 5_000_000, "character": "return_of_capital"}})
    assert d.get("tax_model") is None


def test_server_draft_autosave_survives_reload_and_clears_on_build(tmp_path):
    import io, json as _json
    from officekit import serve
    # POST /draft writes draft.json; onboarding GET re-injects it server-side
    draft = {"rows": [["real_estate_debt", "Mortgage", 720000, ""], ["ticker", "GOOG", 250000, ""]],
             "scalars": {"wind_amount": "5000000", "wind_state": "CA"}, "taxharvest": 1}
    (tmp_path / "draft.json").write_text(_json.dumps(draft))
    blob = serve._server_draft_blob(tmp_path)
    assert "window.__OFFICEKIT_DRAFT__" in blob and "Mortgage" in blob and "GOOG" in blob
    # a corrupt draft never breaks the page
    (tmp_path / "draft.json").write_text("{not json")
    assert serve._server_draft_blob(tmp_path) == ""
    # build clears the draft (it's folded into answers.json)
    (tmp_path / "draft.json").write_text(_json.dumps(draft))
    ans = {"owner": "T", "as_of": "2026-09-07", "profile": {}, "goals": [],
           "sleeves": [{"category": "cash", "name": "C", "value": 100000}]}
    serve.build_office(ans, tmp_path)
    assert not (tmp_path / "draft.json").exists()


def test_loss_carryforward_tracked_and_valued():
    from officekit.serve import answers_from_form
    from officekit.formdata import Form
    from officekit.intake import build_from_answers
    from officekit.schema import validate
    from officekit.model import build_model
    import pathlib

    def build(fields):
        a = answers_from_form(Form(fields), pathlib.Path("/tmp"))
        d = build_from_answers(a)
        assert validate(d) == [], validate(d)
        m = build_model(d)
        res = next((s["value"] for s in m["sleeves"] if s["category"] == "tax_reserve"), 0)
        dta = next((s for s in m["sleeves"] if s["category"] == "tax_asset"), None)
        return res, (dta["value"] if dta else 0), (dta or {}).get("meta", {}).get("face_carryforward")

    base = {"owner": ["T"], "as_of": ["2026-09-07"], "account": ["b"],
            "u_kind": ["cash"], "u_name": ["C"], "u_value": ["100000"], "u_rate": [""]}
    # $5M CA gain, no carryforward -> full reserve
    res, dta, face = build({**base, "wind_amount": ["5000000"], "wind_character": ["ltcg"],
                            "wind_state": ["CA"], "wind_rate": [""]})
    assert res == -1_855_000 and dta == 0
    # + $2M carryforward -> reserve on $3M only, all used (no residual DTA)
    res, dta, face = build({**base, "wind_amount": ["5000000"], "wind_character": ["ltcg"],
                            "wind_state": ["CA"], "wind_rate": [""], "loss_carryforward": ["2000000"]})
    assert res == -1_113_000 and dta == 0
    # $2M carryforward, no windfall -> deferred tax asset at the federal floor, face tracked
    res, dta, face = build({**base, "loss_carryforward": ["2000000"]})
    assert res == 0 and dta == 476_000 and face == 2_000_000    # 23.8% x $2M; face = $2M
