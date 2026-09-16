"""Office-page editors — goals + assets addition, with natural-language boxes
(principal-directed 2026-09-07). The NL box calls /chat, which fills a
reviewable form; the human clicks Save/Add to commit (review-before-commit)."""
from officekit import build_model
from officekit.intake import build_from_answers
from officekit.render_office import render_office


def _office(chat):
    data = build_from_answers({
        "as_of": "2026-09-07", "profile": {},
        "sleeves": [{"category": "public_equity", "value": 500000, "name": "VTI"},
                    {"category": "cash", "value": 50000, "name": "MMF"}],
        "goals": []})
    m = build_model(data)
    return render_office(m, goals_endpoint="/goals", assets_endpoint="/assets", chat=chat)


def test_assets_editor_always_present():
    html = _office(chat=False)
    assert 'action="/assets"' in html and "Add to your office" in html
    assert 'name="u_kind"' in html and 'name="u_value"' in html
    # goals editor present too
    assert 'action="/goals/add"' in html                    # add-on-enter, no separate Save


def test_nl_input_boxes_present_only_with_chat():
    on, off = _office(chat=True), _office(chat=False)
    # the natural-language INPUT boxes appear only when an AI key is available
    for needle in ('id="assetnl"', "Add an asset in plain words", "a goal in plain words"):
        assert needle in on, needle
        assert needle not in off, f"{needle} should be gated behind chat"
    # assets still fill client-side via /chat; goals add-on-enter POSTs the words to the server
    assert "function assetNL" in on and 'name="nl"' in on


def test_assets_form_carries_debt_and_income_kinds():
    html = _office(chat=False)
    for k in ("real_estate_debt", "single_name_equity", "human_capital", "municipal_credit"):
        assert f'value="{k}"' in html, k
