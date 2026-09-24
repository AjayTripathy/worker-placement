"""End-to-end onboarding integration test — drives the real HTTP surface the
browser hits: adapter import -> /draft autosave -> reload restores from disk ->
/onboard build -> office persists across a refresh, with the numbers correct
(Parametric shorts net, mortgage a liability, a capital gain tax-reserved).

Runs the actual ThreadingHTTPServer in-process; the only thing faked is the
broker adapter fetch (no live gateway in CI).
"""
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

import pytest


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def _post(url, data, json_body=False):
    if json_body:
        body, ctype = json.dumps(data).encode(), "application/json"
    else:
        body, ctype = urllib.parse.urlencode(data).encode(), "application/x-www-form-urlencoded"
    from local_http import headers
    req = urllib.request.Request(url, data=body, headers={"Content-Type": ctype, **headers(url)})
    try:
        r = urllib.request.build_opener(_NoRedirect).open(req, timeout=30)
        return r.status, r.headers.get("Location"), r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location"), e.read().decode()


def _get(url):
    return urllib.request.urlopen(url, timeout=30).read().decode()


@pytest.fixture
def server(tmp_path, monkeypatch):
    # fake the broker adapter: a levered long/short book like Parametric, so the
    # test exercises shorts-net-into-assets without a live gateway
    import officekit_adapters as A
    monkeypatch.setattr(A, "fetch_positions", lambda name, ctx=None: [
        {"symbol": "AAPL", "value": 300000, "sec_type": "STK", "account": "U1"},
        {"symbol": "MSFT", "value": 200000, "sec_type": "STK", "account": "U1"},
        {"symbol": "SHORTX", "value": -100000, "sec_type": "STK", "account": "U1"},  # a short
        {"symbol": "CASH", "value": 50000, "sec_type": "CASH", "account": "U1"},
    ])
    monkeypatch.setitem(__import__("officekit.serve", fromlist=["_DISCOVERY_CACHE"])._DISCOVERY_CACHE,
                        "results", [{"name": "ibkr_socket", "label": "IBKR", "kind": "broker",
                                     "found": True, "status": "ready", "detail": "up",
                                     "guidance": None, "can_fetch": True}])
    monkeypatch.setitem(__import__("officekit.serve", fromlist=["_DISCOVERY_CACHE"])._DISCOVERY_CACHE,
                        "ts", time.time())
    from officekit.serve import make_handler
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(tmp_path))
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.2)
    yield f"http://127.0.0.1:{port}", tmp_path
    srv.shutdown()


def test_full_onboarding_flow(server):
    base, folder = server

    # 1) import the broker connection (staged, survives everything)
    status, loc, _ = _post(f"{base}/adapter/import", {"adapter": "ibkr_socket"})
    assert status == 303 and loc == "/"
    from officekit import staging
    assert staging.load(folder)["sources"], "import did not stage"

    # 2) autosave manual entries to DISK as typed (no Build yet)
    draft = {"rows": [["real_estate_debt", "Mortgage", 720000, ""],
                      ["ticker", "GOOG", 250000, ""]],
             "scalars": {"wind_amount": "5000000", "wind_eta": "Sep",
                         "wind_character": "ltcg", "wind_state": "CA"},
             "goals": [], "profile": {}, "taxharvest": 1}
    status, _, _ = _post(f"{base}/draft", draft, json_body=True)
    assert status == 204
    assert (folder / "draft.json").exists(), "draft not persisted server-side"

    # 3) a RELOAD (GET /) restores the manual entries from disk — the footgun fix
    page = _get(f"{base}/")
    assert "window.__OFFICEKIT_DRAFT__" in page and "Mortgage" in page and "GOOG" in page

    # 4) Build: imports (prefilled) + manual rows + windfall + tax goal
    from officekit.serve import staged_prefill
    prefill, _ = staged_prefill(folder)
    fields = [("owner", "T"), ("as_of", "2026-09-07"), ("account", "b")]
    for kind, name, value, rate, *_ in prefill:
        fields += [("u_kind", kind), ("u_name", str(name)), ("u_value", str(value)), ("u_rate", "")]
    fields += [("u_kind", "real_estate_debt"), ("u_name", "Mortgage"), ("u_value", "720000"), ("u_rate", ""),
               ("u_kind", "ticker"), ("u_name", "GOOG"), ("u_value", "250000"), ("u_rate", ""),
               ("wind_amount", "5000000"), ("wind_eta", "Sep"), ("wind_character", "ltcg"),
               ("wind_state", "CA"), ("wind_rate", ""), ("goal_taxharvest", "1")]
    status, loc, _ = _post(f"{base}/onboard", fields)
    assert status == 303 and loc == "/", "build did not succeed"
    assert (folder / "balance_sheet.json").exists()
    assert not (folder / "draft.json").exists(), "build should clear the draft"

    # 5) a refresh now shows the OFFICE, not onboarding (persistence)
    page = _get(f"{base}/")
    assert "SCENARIO PLANNER" in page and 'action="/onboard"' not in page   # office shell, not the build form

    # 6) the numbers are right
    from officekit import load_balance_sheet, build_model
    d = load_balance_sheet(folder / "balance_sheet.json", strict=False)
    m = build_model(d)
    cats = {}
    for s in d["sleeves"]:
        cats.setdefault(s["category"], 0)
        cats[s["category"]] += float(s.get("value") or 0)
    # mortgage is a liability, tax reserve exists (CA on the $5M gain), gain in assets
    assert any(s["category"] == "real_estate_debt" and s["kind"] == "liability" for s in d["sleeves"])
    assert d.get("tax_model") and d["tax_model"]["rate_ltcg"] == pytest.approx(0.371, abs=1e-6)
    res = next((s["value"] for s in m["sleeves"] if s["category"] == "tax_reserve"), 0)
    assert res == -1_855_000                                  # 37.1% of $5M
    # value conservation: the short nets in (not dropped, not counted gross).
    # equity may be concentration-split across public_equity + single_name_equity;
    # net across both = 300k+200k-100k imported + 250k GOOG = 650k
    equity_net = cats.get("public_equity", 0) + cats.get("single_name_equity", 0)
    assert equity_net == pytest.approx(650000, abs=1)
    assert cats.get("cash_pending", 0) == 5_000_000        # the gain, gross, as an asset
    # net worth = equity 650k + cash 50k + gain 5.0M - mortgage 720k - tax 1.855M
    assert m["NW"] == pytest.approx(650000 + 50000 + 5_000_000 - 720000 - 1_855_000, abs=2)


def test_stale_shell_pages_self_heal_after_reset(server):
    """A tab left open from before a /reset asks for a now-deleted core page —
    it must bust back to onboarding, not show a bare 'not found'."""
    base, folder = server
    # build an office the normal way (import stages, /onboard builds), then reset
    _post(f"{base}/adapter/import", {"adapter": "ibkr_socket"})
    from officekit.serve import staged_prefill
    prefill, _ = staged_prefill(folder)
    fields = [("account", "b")]
    for kind, name, value, rate, *_ in prefill:
        fields += [("u_kind", kind), ("u_name", str(name)), ("u_value", str(value)), ("u_rate", "")]
    _post(f"{base}/onboard", fields)
    assert (folder / "balance_sheet.json").exists()
    _post(f"{base}/reset", {})
    assert not (folder / "balance_sheet.json").exists()
    page = _get(f"{base}/pages/scenarios.html")
    assert "top.location='/'" in page, "reset office should self-heal a stale-shell page request"


def test_office_assets_editor_adds_sleeve_and_ticker(server):
    """The office-page 'Add assets' form appends to a LIVE office and rebuilds."""
    base, folder = server
    _post(f"{base}/adapter/import", {"adapter": "ibkr_socket"})
    from officekit.serve import staged_prefill
    prefill, _ = staged_prefill(folder)
    fields = [("account", "b")]
    for kind, name, value, rate, *_ in prefill:
        fields += [("u_kind", kind), ("u_name", str(name)), ("u_value", str(value)), ("u_rate", "")]
    _post(f"{base}/onboard", fields)
    from officekit import load_balance_sheet
    n0 = len(load_balance_sheet(folder / "balance_sheet.json", strict=False)["sleeves"])
    # add a mortgage sleeve + a manual ticker via the office-page editor
    status, loc, _ = _post(f"{base}/assets", [
        ("u_kind", "real_estate_debt"), ("u_name", "Mortgage (fixed)"), ("u_value", "500000"), ("u_rate", "6"),
        ("u_kind", "ticker"), ("u_name", "PRIVCO"), ("u_value", "40000"), ("u_rate", "")])
    assert status == 303 and loc == "/pages/office.html"
    d = load_balance_sheet(folder / "balance_sheet.json", strict=False)
    assert any(s["category"] == "real_estate_debt" and s["kind"] == "liability" for s in d["sleeves"])
    assert len(d["sleeves"]) > n0
    ans = json.loads((folder / "answers.json").read_text())
    assert any(r["symbol"] == "PRIVCO" for r in (ans.get("positions") or {}).get("rows", []))


# ---------------------------------------------------------------------------
# Goals add-on-enter / remove (2026-09-08): appending never overwrites, the
# tax_efficiency goal survives, and existing strategies auto-serve a new goal.
# ---------------------------------------------------------------------------

def _build_office_with_taxharvest(base, folder):
    _post(f"{base}/adapter/import", {"adapter": "ibkr_socket"})
    from officekit.serve import staged_prefill
    prefill, _ = staged_prefill(folder)
    fields = [("account", "b"), ("goal_taxharvest", "1")]
    for kind, name, value, rate, *_ in prefill:
        fields += [("u_kind", kind), ("u_name", str(name)), ("u_value", str(value)), ("u_rate", "")]
    _post(f"{base}/onboard", fields)


def _goals(folder):
    import json as _json
    return _json.loads((folder / "answers.json").read_text()).get("goals", [])


def test_goal_add_appends_and_never_overwrites(server):
    base, folder = server
    _build_office_with_taxharvest(base, folder)
    assert any(g["kind"] == "tax_efficiency" for g in _goals(folder)), "harvest goal missing"

    # add a dated goal — the tax_efficiency goal must SURVIVE (the overwrite bug)
    status, loc, _ = _post(f"{base}/goals/add",
                           [("gkind", "spending"), ("glabel", "House"), ("gamt", "800000"),
                            ("gdate", "2030-01-01")])
    assert status == 303 and loc == "/pages/office.html"
    kinds = [g["kind"] for g in _goals(folder)]
    assert "tax_efficiency" in kinds and "spending" in kinds, f"overwrote: {kinds}"

    # add a second — all three coexist (append, not replace)
    _post(f"{base}/goals/add", [("gkind", "liquidity_floor"), ("glabel", "Floor"), ("gamt", "50000")])
    assert len(_goals(folder)) == 3


def test_goal_remove_deletes_only_that_goal(server):
    base, folder = server
    _build_office_with_taxharvest(base, folder)
    _post(f"{base}/goals/add", [("gkind", "spending"), ("glabel", "Car"), ("gamt", "60000")])
    car = next(g for g in _goals(folder) if g["label"] == "Car")
    status, loc, _ = _post(f"{base}/goals/remove", [("gid", car["id"])])
    assert status == 303
    remaining = _goals(folder)
    assert all(g["id"] != car["id"] for g in remaining)
    assert any(g["kind"] == "tax_efficiency" for g in remaining)          # unrelated goal untouched


def test_existing_strategy_auto_serves_new_goal(tmp_path):
    from officekit.serve import _link_existing_strategies
    answers = {"as_of": "2026-09-07",
               "goals": [{"id": "g1", "kind": "liquidity_floor", "label": "Floor", "amount": 50000}],
               "strategy_decisions": {"cash_mgmt": {"status": "implemented", "origins": []},
                                      "venture_moonshot": {"status": "considering", "origins": []}}}
    _link_existing_strategies(answers, ["g1"], tmp_path)
    cash = answers["strategy_decisions"]["cash_mgmt"]["origins"]
    assert any(o["source"] == "goal" and o["ref"] == "g1" for o in cash)   # in the menu -> linked
    assert answers["strategy_decisions"]["venture_moonshot"]["origins"] == []  # not in menu -> untouched
    # idempotent
    _link_existing_strategies(answers, ["g1"], tmp_path)
    assert sum(1 for o in cash if o.get("ref") == "g1") == 1


def test_state_version_bumps_and_shell_polls(server):
    """Cross-tab reactivity: /state carries the build version, it changes on any
    mutation, and the app shell polls it to reload the open tab."""
    import json as _json
    base, folder = server
    _post(f"{base}/adapter/import", {"adapter": "ibkr_socket"})
    from officekit.serve import staged_prefill
    prefill, _ = staged_prefill(folder)
    fields = [("account", "b")]
    for kind, name, value, rate, *_ in prefill:
        fields += [("u_kind", kind), ("u_name", str(name)), ("u_value", str(value)), ("u_rate", "")]
    _post(f"{base}/onboard", fields)

    v1 = _json.loads(_get(f"{base}/state"))["v"]
    assert v1 > 0
    _post(f"{base}/goals/add", [("gkind", "spending"), ("glabel", "X"), ("gamt", "1000")])
    v2 = _json.loads(_get(f"{base}/state"))["v"]
    assert v2 != v1                                   # any mutation bumps the version

    shell = _get(f"{base}/")
    assert "/state" in shell and "setInterval" in shell   # the shell watches it

    # query strings are stripped so cache-busted reloads still resolve the file
    assert "Decisions &amp; attention" in _get(f"{base}/pages/office.html?v=" + str(v2))


def test_goal_proposal_retains_origin_and_legacy_unlink(server, monkeypatch):
    """Goal creation opens review; the legacy unlink still removes its origin."""
    base, folder = server
    monkeypatch.setattr("officekit.strategy_proposals.dispatch", lambda *a: None)
    _post(f"{base}/adapter/import", {"adapter": "ibkr_socket"})
    from officekit.serve import staged_prefill
    prefill, _ = staged_prefill(folder)
    fields = [("account", "b")]
    for kind, name, value, rate, *_ in prefill:
        fields += [("u_kind", kind), ("u_name", str(name)), ("u_value", str(value)), ("u_rate", "")]
    _post(f"{base}/onboard", fields)
    # a dated target whose menu offers bonds (the office holds no fixed income -> not auto-linked)
    _post(f"{base}/goals/add", [("gkind", "spending"), ("glabel", "College"),
                                ("gamt", "300000"), ("gdate", "2035-09-01")])
    gid = next(g["id"] for g in _goals(folder) if g["label"] == "College")

    def _bonds_origins():
        decs = json.loads((folder / "answers.json").read_text()).get("strategy_decisions", {})
        return [o for o in decs.get("bonds", {}).get("origins", [])
                if o.get("source") == "goal" and o.get("ref") == gid]

    assert not _bonds_origins()                                        # not adopted yet
    from officekit.commitments import revision
    _post(f"{base}/strategy/goal-adopt", [("gid", gid), ("sid", "bonds"), ("revision", revision(json.loads((folder / "answers.json").read_text())))])
    assert _bonds_origins()                                            # proposal origin retained
    html = _get(f"{base}/pages/strategies.html")
    assert "Review proposal" in html and "/pages/proposal_" in html  # review before adoption

    _post(f"{base}/strategy/goal-unadopt", [("gid", gid), ("sid", "bonds"), ("revision", revision(json.loads((folder / "answers.json").read_text())))])
    assert not _bonds_origins()                                        # ☐ un-adopted


def test_classify_splits_sma_from_single_names():
    """With an SMA constituent list, individual equities split into a direct_index
    sleeve vs the deliberate single-name book — same lots, distinct risk read.
    (Many small lots, none >=20%, so the concentration split doesn't pre-empt.)"""
    from officekit.importers import classify_positions
    rows = [{"symbol": f"IDX{i}", "value": 10000} for i in range(8)]      # SMA constituents
    rows += [{"symbol": "MYPICK1", "value": 10000}, {"symbol": "MYPICK2", "value": 10000}]
    sleeves = classify_positions(rows, account="b",
                                 sma_symbols={f"IDX{i}" for i in range(8)}, sma_label="Parametric SMA")
    by_cat = {s["category"]: s for s in sleeves}
    assert by_cat["direct_index"]["value"] == 80000 and "Parametric SMA" in by_cat["direct_index"]["name"]
    assert by_cat["public_equity"]["value"] == 20000 and "Concentrated single names" in by_cat["public_equity"]["name"]


def test_classify_without_sma_list_is_unchanged():
    """No SMA list -> the classic single 'Individual stocks' pool (backward compat)."""
    from officekit.importers import classify_positions
    rows = [{"symbol": f"S{i}", "value": 10000} for i in range(6)]
    sleeves = classify_positions(rows, account="b")
    eq = [s for s in sleeves if s["category"] == "public_equity"]
    assert len(eq) == 1 and "Individual stocks" in eq[0]["name"]
    assert not any(s["category"] == "direct_index" for s in sleeves)


def test_ofx_named_fund_classified_as_fund_not_stock():
    """OFX/401k exports name the fund where a ticker goes ('Target Retire 2055 Tr')
    — must classify as a fund, not fall through to a single stock (2026-09-10)."""
    from officekit.importers import _classify
    assert _classify("Target Retire 2055 Tr", "GOOGLE LLC 401(K)") == ("public_equity", "target_date")
    assert _classify("VANGUARD INSTITUTIONAL INDEX FUND", "") == ("public_equity", None)
    # real stocks with 'Trust' in the name must NOT be miscaught as funds
    assert _classify("NTRS", "Northern Trust Corp") == ("__stock__", None)
    assert _classify("AAPL", "Apple Inc") == ("__stock__", None)
