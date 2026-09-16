"""Auto-adapters — discovery contract, normalization, and the onboarding
prefill mapping. No live network: probes are exercised through fakes; the
live-gateway path was proven by hand (2026-09-05: 111 positions, options
labeled, AirPlay-on-5000 false positive rejected)."""
import officekit_adapters as A


def test_registry_carries_the_landscape():
    # the surveyed surfaces stay registered — detect-only stubs are trailheads
    for name in ("ibkr_socket", "ibkr_clientportal", "alpaca", "downloads_csv",
                 "tradier", "coinbase", "kraken", "snaptrade", "plaid", "schwab",
                 "ghostfolio"):
        assert name in A.ADAPTERS, name


def test_discover_degrades_loud_and_sorts_found_first(monkeypatch):
    saved = dict(A.ADAPTERS)
    monkeypatch.setattr(A, "ADAPTERS", {})
    try:
        @A.adapter("good", label="Good", kind="broker")
        def _good():
            return {"detect": lambda ctx: {"found": True, "status": "ready", "detail": "up"},
                    "fetch": lambda ctx: []}

        @A.adapter("bad", label="Bad", kind="broker")
        def _bad():
            def detect(ctx):
                raise ValueError("boom")
            return {"detect": detect, "fetch": None}

        rs = A.discover()
        assert [r["name"] for r in rs] == ["good", "bad"]      # found first
        assert rs[0]["can_fetch"] and rs[0]["status"] == "ready"
        assert rs[1]["status"] == "error" and "boom" in rs[1]["detail"]
    finally:
        A.ADAPTERS.clear()
        A.ADAPTERS.update(saved)


def test_fetch_normalizes_and_detect_only_refuses(monkeypatch):
    saved = dict(A.ADAPTERS)
    monkeypatch.setattr(A, "ADAPTERS", {})
    try:
        @A.adapter("f", label="F", kind="broker")
        def _f():
            return {"detect": lambda ctx: {"found": True, "status": "ready", "detail": ""},
                    "fetch": lambda ctx: [{"symbol": "mndy", "qty": "105", "value": 8001.934},
                                          {"symbol": "HSBK", "qty": 334, "value": None,
                                           "ccy": "GBP", "sec_type": "STK"}]}

        @A.adapter("stub", label="S", kind="broker")
        def _s():
            return {"detect": lambda ctx: {"found": True, "status": "needs_key", "detail": ""},
                    "fetch": None}

        rows = A.fetch_positions("f")
        assert rows[0] == {"symbol": "MNDY", "qty": 105.0, "value": 8001.93,
                           "description": "", "account": "brokerage", "ccy": "USD",
                           "sec_type": "STK"}
        assert rows[1]["ccy"] == "GBP" and rows[1]["value"] == 0
        import pytest
        with pytest.raises(RuntimeError, match="detect-only"):
            A.fetch_positions("stub")
        with pytest.raises(KeyError):
            A.fetch_positions("nope")
    finally:
        A.ADAPTERS.clear()
        A.ADAPTERS.update(saved)


def test_env_stub_flips_on_key(monkeypatch):
    monkeypatch.delenv("TRADIER_ACCESS_TOKEN", raising=False)
    impl = A.ADAPTERS["tradier"]["factory"]()
    assert impl["detect"]({})["found"] is False
    monkeypatch.setenv("TRADIER_ACCESS_TOKEN", "x")
    assert impl["detect"]({})["found"] is True
    assert impl["fetch"] is None                     # trailhead, not a fetcher


def test_downloads_csv_adapter_sniffs_real_export(tmp_path, monkeypatch):
    d = tmp_path / "Downloads"
    d.mkdir()
    (d / "Portfolio_Positions_Sep-05-2026.csv").write_text(
        "Symbol,Description,Quantity,Current Value\n"
        "VTI,VANGUARD TOTAL STOCK MARKET ETF,100,26000.00\n"
        "VWLUX,VANGUARD LT TAX-EXEMPT,5000,55000.00\n")
    (d / "random_data.csv").write_text("a,b,c\n1,2,3\n")
    monkeypatch.setattr(A, "CSV_SCAN_DIRS", (d,))
    impl = A.ADAPTERS["downloads_csv"]["factory"]()
    det = impl["detect"]({})
    assert det["found"] and "Portfolio_Positions" in det["detail"]
    rows = A.fetch_positions("downloads_csv")
    assert {r["symbol"] for r in rows} == {"VTI", "VWLUX"}
    assert sum(r["value"] for r in rows) == 81000.0


def test_adapter_prefill_maps_stocks_and_reports_rest():
    from officekit.serve import adapter_prefill
    rows = [{"symbol": "MNDY", "qty": 105, "value": 8001.93, "sec_type": "STK",
             "description": "", "account": "U1", "ccy": "USD"},
            {"symbol": "EQT", "qty": -1, "value": -227.95, "sec_type": "STK",
             "description": "", "account": "U1", "ccy": "USD"},
            {"symbol": "SLS", "qty": 1, "value": 129.0, "sec_type": "OPT",
             "description": "SLS 20270115 10C", "account": "U1", "ccy": "USD"},
            {"symbol": "CASH", "qty": 20160.0, "value": 20160.0, "sec_type": "CASH",
             "description": "IBKR cash balance (U1)", "account": "U1", "ccy": "USD"}]
    prefill, note = adapter_prefill(rows)
    assert prefill == [("ticker", "MNDY", 8001.93, "", ""), ("ticker", "EQT", -227.95, "", ""),
                       ("cash", "IBKR cash balance (U1)", 20160.0, "", ""),
                       ("options_overlay", "Options overlay (1 positions)", 129.0, "", "")]
    assert "2 stock/fund positions" in note
    assert "Cash balance $20,160" in note
    assert "1 option positions imported as one overlay row" in note
    assert "Skipped" not in note                     # options are understood, not skipped


def test_urows_prefill_renders_selected_ticker_rows():
    from officekit.serve import _urows_html
    h = _urows_html(n=2, prefill=[("ticker", "MNDY", 8001.93, "", "src-auto")])
    assert 'value="ticker" selected' in h
    assert 'value="MNDY"' in h
    assert 'class="row src-auto"' in h               # auto-imported rows styled
    assert h.count('name="u_kind"') == 3             # 1 prefilled + 2 blank


def test_convert_to_base_the_20m_lesson():
    # JPY/KRW market values summed as dollars inflated a $937k account 22x
    rows = [{"symbol": "8035", "qty": 100, "value": 1_316_000, "ccy": "JPY", "sec_type": "STK"},
            {"symbol": "MNDY", "qty": 105, "value": 8001.93, "ccy": "USD", "sec_type": "STK"},
            {"symbol": "HSBK", "qty": 334, "value": 10008.30, "ccy": "GBP", "sec_type": "STK"},
            {"symbol": "MYST", "qty": 1, "value": 500, "ccy": "XXX", "sec_type": "STK"}]
    fx = {"JPY": 0.0063993, "GBP": 1.3520912, "USD": 1.0}
    out = A.convert_to_base(rows, fx, base="USD")
    assert round(out[0]["value"], 2) == round(1_316_000 * 0.0063993, 2)
    assert out[0]["local_value"] == 1_316_000 and out[0]["fx"] == 0.0063993
    assert out[1]["value"] == 8001.93                # base currency: rate 1, provenance kept
    assert round(out[2]["value"], 0) == 13532
    # unknown currency: ZEROED (never left local to poison a total) + flagged,
    # local kept for the user to set manually
    assert out[3]["value"] == 0.0
    assert out[3]["local_value"] == 500 and out[3]["needs_fx"] == "XXX"
    assert "UNCONVERTED" in out[3]["description"]


def test_chat_first_line_leads_with_detection(monkeypatch):
    from officekit import serve
    monkeypatch.setitem(serve._DISCOVERY_CACHE, "results", [
        {"name": "ibkr_socket", "label": "Interactive Brokers — TWS / IB Gateway",
         "kind": "broker", "found": True, "status": "ready",
         "detail": "IB Gateway (live) listening on 127.0.0.1:4001",
         "guidance": None, "can_fetch": True}])
    import time
    monkeypatch.setitem(serve._DISCOVERY_CACHE, "ts", time.time())
    line = serve.chat_first_line()
    assert "auto-detected" in line
    assert "IB Gateway (live) listening on 127.0.0.1:4001" in line   # the HOW
    assert "Import positions" in line
    # post-import: the line reports what was pulled and from where
    line2 = serve.chat_first_line(notice="Imported 97 stock/fund positions ($956,037).",
                                  via="Interactive Brokers — TWS / IB Gateway")
    assert line2.startswith("Imported 97")
    assert "Pulled read-only from your Interactive Brokers" in line2
    # nothing found: says what was scanned for
    monkeypatch.setitem(serve._DISCOVERY_CACHE, "results", [])
    assert "found none" in serve.chat_first_line()


def test_turn_injects_detection_context(monkeypatch):
    import json
    from types import SimpleNamespace
    from officekit_ai.intake_chat import turn
    calls = []

    def create(**kw):
        calls.append(kw)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(
            type="text", text=json.dumps({"reply": "ok", "complete": False, "answers_json": ""}))])

    cl = SimpleNamespace(messages=SimpleNamespace(create=create))
    turn([{"role": "user", "content": "hi"}], client=cl, model="m", scope="assets",
         context="Interactive Brokers — IB Gateway on 127.0.0.1:4001")
    assert "AUTO-DETECTED ON THIS MACHINE" in calls[0]["system"]
    assert "127.0.0.1:4001" in calls[0]["system"]
    assert "Import button" in calls[0]["system"]
    turn([{"role": "user", "content": "hi"}], client=cl, model="m", scope="assets")
    assert "AUTO-DETECTED" not in calls[1]["system"]  # no context, no injection


def test_models_key_falls_back_to_home_file(tmp_path, monkeypatch):
    from officekit_ai.models import resolve_key
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: tmp_path))
    assert resolve_key() is None                     # nothing anywhere
    (tmp_path / ".anthropic_key").write_text("sk-ant-test\n")
    assert resolve_key() == "sk-ant-test"            # file fallback
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env")
    assert resolve_key() == "sk-ant-env"             # env wins
    assert resolve_key("CUSTOM_KEY") is None         # custom env: no file fallback


def test_keyless_onboarding_asks_for_key(monkeypatch, tmp_path):
    # deterministic path intact + the agent ASKS instead of vanishing
    from officekit import serve
    import time
    monkeypatch.setitem(serve._DISCOVERY_CACHE, "results", [
        {"name": "ibkr_socket", "label": "Interactive Brokers — TWS / IB Gateway",
         "kind": "broker", "found": True, "status": "ready",
         "detail": "IB Gateway (live) listening on 127.0.0.1:4001",
         "guidance": None, "can_fetch": True}])
    monkeypatch.setitem(serve._DISCOVERY_CACHE, "ts", time.time())
    h = serve._key_ask_html()
    assert "auto-detected" in h and "127.0.0.1:4001" in h   # detection line is key-free
    assert 'action="/key"' in h and 'type="password"' in h
    assert "never in your Worker Placement folder" in h
    assert "works without any key" in h


def _opt(sym, right, strike, qty, mult=100, ccy="USD", fx=None, value=0, account="U1"):
    r = {"symbol": sym, "qty": qty, "value": value, "sec_type": "OPT",
         "right": right, "strike": strike, "multiplier": mult, "ccy": ccy,
         "account": account, "description": f"{sym} 20270115 {strike}{right}"}
    if fx:
        r["fx"] = fx
    return r


def test_short_put_obligations():
    rows = [_opt("QCOM", "P", 140, -1), _opt("QCOM", "P", 135, -1),
            _opt("FAF", "P", 70, -2), _opt("APP", "C", 340, -1),   # call: not an obligation here
            _opt("XX", "P", 50, 1),                                # LONG put: no obligation
            _opt("JP", "P", 1000, -1, ccy="JPY", fx=0.0064)]       # converts through fx
    sp = A.short_put_obligations(rows)
    assert sp["count"] == 4 and sp["contracts"] == 5
    assert sp["total"] == 14000 + 13500 + 14000 + 640
    assert sp["items"][0]["obligation"] in (14000.0,)              # largest first
    assert all(i["symbol"] != "APP" for i in sp["items"])


def test_covered_call_summary_spread_covered_naked():
    rows = [
        # APP vertical: short 340C matched by long 320C -> spread leg
        _opt("APP", "C", 340, -1), _opt("APP", "C", 320, 1),
        # CAI short call + 150 shares held -> 1 covered (100sh), 50sh spare
        _opt("CAI", "C", 30, -1),
        {"symbol": "CAI", "qty": 150, "value": 4500, "sec_type": "STK", "ccy": "USD", "account": "U1"},
        # ZZZ short 2 calls, no stock, no longs -> naked
        _opt("ZZZ", "C", 10, -2),
    ]
    cc = A.covered_call_summary(rows)
    assert cc["spread_matched_contracts"] == 1
    assert len(cc["covered"]) == 1
    c = cc["covered"][0]
    assert (c["symbol"], c["shares"], c["callable_for"]) == ("CAI", 100, 3000.0)
    assert c["encumbered_value"] == 3000.0           # 100sh at the $30 mark (4500/150)
    assert cc["naked"] == [{"symbol": "ZZZ", "strike": 10.0, "contracts": 2.0}]


def test_prefill_note_carries_obligation_and_cc_lines():
    from officekit.serve import adapter_prefill
    rows = [{"symbol": "CAI", "qty": 150, "value": 4500, "sec_type": "STK",
             "ccy": "USD", "description": "", "account": "U1"},
            _opt("CAI", "C", 30, -1), _opt("FAF", "P", 70, -2),
            _opt("ZZZ", "C", 10, -1)]
    _, note = adapter_prefill(rows)
    assert "imported as one overlay row" in note and "Skipped" not in note
    assert "Short puts: $14,000 of collateralized purchase obligations across 2 contracts" in note
    assert "Covered calls encumber 100 CAI @ $30 (callable for $3,000)" in note
    assert "NAKED short calls (unbounded risk — review): 1x ZZZ $10C" in note


def test_covered_call_does_not_cross_accounts():
    # shares in account A must NOT cover a short call written in account B
    rows = [{"symbol": "CAI", "qty": 100, "value": 3000, "sec_type": "STK", "account": "A"},
            _opt("CAI", "C", 30, -1, account="B")]     # short call in a DIFFERENT account
    cc = A.covered_call_summary(rows)
    assert not cc["covered"]                            # not covered across accounts
    assert cc["naked"] == [{"symbol": "CAI", "strike": 30.0, "contracts": 1.0}]


def test_num_strips_currency_symbols_and_rejects_bool():
    from officekit.staging import num
    assert num("£500") == 500.0 and num("¥100000") == 100000.0 and num("€1,234.56") == 1234.56
    assert num(True) == 0.0 and num(False) == 0.0      # a flag is not money


def test_norm_row_preserves_cost_basis_fields():
    """_norm_row must pass cost basis + market flag through to staging, or the
    harvest page can never see IBKR/broker losers (the 2026-09-09 bug)."""
    r = A._norm_row({"symbol": "x", "qty": 10, "value": 600,
                     "cost_basis": 1000, "unrealized_pnl": -400, "value_is_cost": True})
    assert r["cost_basis"] == 1000 and r["unrealized_pnl"] == -400 and r["value_is_cost"] is True


def test_convert_to_base_keeps_value_is_cost_flag():
    out = A.convert_to_base([{"symbol": "y", "value": 100, "cost_basis": 100,
                              "value_is_cost": True, "ccy": "USD"}], {}, base="USD")[0]
    assert out.get("value_is_cost") is True and out["cost_basis"] == 100


def test_downloads_csv_is_manual_only():
    """A stray CSV in ~/Downloads must not silently enter the book — downloads_csv
    is manual-only, so the daily auto-pull loop skips it (2026-09-10)."""
    assert A.ADAPTERS["downloads_csv"].get("auto") is False
    d = {r["name"]: r for r in A.discover(names=["downloads_csv"])}["downloads_csv"]
    assert d.get("auto") is False


def test_live_broker_adapters_default_auto():
    assert A.ADAPTERS["ibkr_socket"].get("auto") is True
    assert A.ADAPTERS["ibkr_flex"].get("auto") is True
