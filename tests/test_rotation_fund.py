"""Invariants for the rotation-fund engine — it's the risk source of truth for the IBKR book,
so exposures must reconcile and every rotation scenario must resolve to a number."""
import json

from desk import rotation_fund as rf


def test_book_loads_and_axes_reconcile_to_gross():
    book = rf.load_book()
    assert book["gross"] > 0
    assert book["names"], "book should not be empty"
    assert not book["missing_mark"], f"every held name needs a mark: {book['missing_mark']}"
    assert sum(n["mv"] for n in book["names"]) == book["gross"]
    for n in book["names"]:
        assert n["axis"], "every name must carry an axis (UNMAPPED is allowed but must be set)"


def test_axis_percentages_sum_to_one():
    book = rf.load_book()
    ax = rf.axis_exposure(book)
    assert abs(sum(a["pct"] for a in ax["by_axis"].values()) - 1.0) < 1e-6
    assert 1 <= ax["eff_axes"] <= len(ax["by_axis"])


def test_concentration_flags_the_software_stack_or_dfin():
    """The whole point of the engine: it must surface an over-concentration we already know about."""
    book = rf.load_book()
    ax = rf.axis_exposure(book)
    sw = ax["by_axis"].get("software_saas", {}).get("pct", 0)
    dfin = next((n["mv"] for n in book["names"] if n["sym"] == "DFIN"), 0) / book["gross"]
    assert sw > 0.15 or dfin > rf.NAME_LIMIT, "engine should catch the known software/DFIN concentration"


def test_every_rotation_resolves_and_software_is_worst_in_ai_derate():
    book = rf.load_book()
    # synthetic loadings (no DB dependency): all names fall back to mkt_beta=1.0, zero style
    st = rf.stress(book, ld={})
    assert set(st) == set(rf.ROTATIONS), "every rotation must produce a result"
    for r in st.values():
        assert isinstance(r["pnl"], (int, float)) and -1.0 < r["ret"] < 1.0
    # the AI-capex derate must hit software hardest (it carries the -0.12 axis override)
    assert st["ai_capex_derate"]["worst_axis"] == "software_saas"
    # and it must be a loss for a long book
    assert st["ai_capex_derate"]["pnl"] < 0


def test_report_is_json_serializable():
    out = rf.build(write=False)
    json.dumps(out["report"])          # must not raise
    assert "ROTATION FUND" in out["text"]


def test_hedge_overlay_shorts_the_tech_block_and_flags_dfin():
    book = rf.load_book()
    ax = rf.axis_exposure(book)
    h = rf.hedge_overlay(book, ax)
    axes_hedged = {t["axis"] for t in h["tickets"]}
    assert "software_saas" in axes_hedged, "the software stack must get a hedge ticket"
    assert all(t["action"] == "SHORT" for t in h["tickets"]), "hedges are ETF shorts, never written premium"
    assert any("DFIN" in n for n in h["notes"]), "DFIN single-name breach must surface as a SIZE note"


def test_hedge_reduces_the_ai_derate_tail():
    book = rf.load_book()
    ax = rf.axis_exposure(book)
    h = rf.hedge_overlay(book, ax)
    base = rf.stress(book, ld={})["ai_capex_derate"]["pnl"]
    hedged = rf.stress(book, ld={}, extra=h["legs"])["ai_capex_derate"]["pnl"]
    assert hedged > base, "hedging must shrink the AI-capex-derate loss"


def test_construction_freezes_hedged_axes_and_funds_intended():
    book = rf.load_book()
    ax = rf.axis_exposure(book)
    plan = rf.construction_plan(book, ax)
    dep = {r["axis"]: r["deploy"] for r in plan["rows"]}
    assert dep["software_saas"] == 0 and dep["it_services"] == 0, "hedged axes must be frozen (no new deploy)"
    assert dep["em_financials"] > 0, "intended under-weight axes must receive deployment budget"
    assert abs(sum(dep.values()) - plan["dry_powder"]) <= 5, "deployment must allocate the full dry powder"


def test_construction_check_blocks_growing_a_hedged_axis():
    book = rf.load_book()
    ax = rf.axis_exposure(book)
    v = rf.construction_check(book, ax, {"sym": "PANW", "axis": "software_saas", "mv": 30000})
    assert v["verdict"] == "HEDGED-AXIS"
    ok = rf.construction_check(book, ax, {"sym": "NEWBANK", "axis": "em_financials", "mv": 40000})
    assert ok["verdict"] == "ADD-OK"
