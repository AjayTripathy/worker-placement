"""UX pass (2026-09-13): Home deploy plan, Strategies verdict translation,
Imports lead-with-active ordering. Covers the logic the golden snapshots don't
exercise (the household fixture has no recorded court verdicts)."""
from officekit.render_strategies import _verdict_label
from officekit.render_office import _deploy_plan
from officekit.render_imports import render_imports


# ---- item 2: machine verdict codes are translated for readers -----------------

def test_verdict_label_translates_machine_codes():
    assert _verdict_label("HELD_PENDING_DECISION") == "Held — decision pending"
    assert _verdict_label("PENDING_DECISION") == "Decision pending"
    assert _verdict_label("BUY") == "Cleared to buy"
    assert _verdict_label("WATCH") == "Watching"
    assert _verdict_label("") == ""


def test_verdict_label_unknown_code_is_humanized_not_raw():
    # an unmapped code must still read as words, never SCREAMING_SNAKE
    out = _verdict_label("SOME_NEW_STATE")
    assert "_" not in out and out == "Some new state"


# ---- item 1: the deploy plan is a concrete before/after allocation comparison --

def _model_with_pending(pending=5_000_000):
    assets = [{"category": "cash", "value": 250_000},
              {"category": "public_equity", "value": 13_000_000}]
    if pending:
        assets.insert(0, {"id": "incoming", "category": "cash_pending", "value": pending})
    A = sum(a["value"] for a in assets)
    return {"assets": assets, "A": A, "NW": A, "eta": "2026-09", "d": {},
            "sleeves": assets + [{"category": "tax_reserve", "value": -1_670_000,
                                   "meta": {"inflow_id": "incoming"}}],
            "tax": {"net_tax": 1_670_000, "deployable": 3_330_000,
                    "char": "ltcg", "rate": 0.238, "offset": 100_000}}


def test_deploy_plan_shows_net_after_tax_and_before_after():
    html = _deploy_plan(_model_with_pending())
    assert "Deploy plan" in html and 'id="deploy-plan"' in html
    assert "Dry cash, share of investable assets" in html
    assert "$3.33M" in html            # net deployable after the tax reserve
    assert "$5.00M" in html            # gross incoming
    assert "/pages/growth.html" in html  # steer-the-mix link


def test_deploy_plan_empty_without_pending_cash():
    assert _deploy_plan(_model_with_pending(pending=0)) == ""


# ---- item 5: connected sources lead; not-connected providers are demoted -------

def _adapter(name, status, found, can_fetch=True, auto=True):
    return {"name": name, "label": name.upper(), "status": status, "found": found,
            "can_fetch": can_fetch, "auto": auto, "detail": f"{name} needs {name.upper()}_KEY"}


def test_imports_demotes_not_connected_under_add_a_connection():
    discover = [_adapter("ibkr", "ready", True), _adapter("plaid", "absent", False)]
    html = render_imports(discover, ledger=[], merged=[], overlaps=[])
    conns, _, add_section = html.partition('Add a connection')
    # the connected source sits in the primary table; the absent one is demoted
    assert "IBKR" in conns
    assert "PLAID" not in conns and "PLAID" in add_section
    # the env-var name rides along in the demoted/detail area, not the lead
    assert "PLAID_KEY" not in conns


def test_imports_surfaces_refresh_problems_first():
    # a connection that has imported before but is now erroring must lead
    led = [{"source_id": "adapter:ibkr", "kind": "adapter", "pulled_utc": "2026-09-10T00:00:00Z",
            "n_rows": 5, "as_of": "2026-09-10"}]
    discover = [_adapter("ibkr", "error", True)]
    html = render_imports(discover, ledger=led, merged=[], overlaps=[])
    assert "need a refresh or reconnect" in html
