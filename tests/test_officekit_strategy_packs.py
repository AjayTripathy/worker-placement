"""strategy_packs — the OSS contribution unit: load/validate, taxonomy projection,
and the SAFE markdown deck renderer (untrusted contributor content)."""
import json

from officekit import strategy_packs as SP
from officekit.render_deck import render_markdown_deck


def _pack(tmp_path, pid, **over):
    d = tmp_path / "strategies" / pid
    d.mkdir(parents=True)
    m = {"id": pid, "name": "Test", "bucket": "defensive", "thesis": "x", "author": "me"}
    m.update(over)
    (d / "pack.json").write_text(json.dumps(m))
    (d / (m.get("deck", "DECK.md"))).write_text("# Deck\n\nbody")
    return d


def test_validate_catches_missing_and_bad_bucket(tmp_path):
    assert "missing required field: thesis" in SP.validate({"id": "a", "name": "n", "bucket": "defensive", "author": "me"})
    assert any("bucket" in p for p in SP.validate({"id": "a", "name": "n", "thesis": "t", "author": "me", "bucket": "nope"}))
    assert SP.validate({"id": "a", "name": "n", "thesis": "t", "author": "me", "bucket": "growth"}) == []


def test_load_packs_discovers_valid_skips_template_and_flags_bad(tmp_path):
    _pack(tmp_path, "good_one", bucket="cyclical_value")
    (tmp_path / "strategies" / "_template").mkdir(parents=True)
    (tmp_path / "strategies" / "_template" / "pack.json").write_text(json.dumps({"id": "_template", "name": "T", "bucket": "growth", "thesis": "t", "author": "x"}))
    bad = tmp_path / "strategies" / "bad_one"
    bad.mkdir(parents=True)
    (bad / "pack.json").write_text(json.dumps({"id": "bad_one", "name": "B"}))   # missing fields
    packs, probs = SP.load_packs([tmp_path / "strategies"], include_defaults=False)
    ids = {p["id"] for p in packs}
    assert "good_one" in ids and "_template" not in ids                 # template skipped
    assert any(x["pack"] == "bad_one" for x in probs)                   # bad flagged, not dropped silently


def test_id_must_match_folder(tmp_path):
    d = tmp_path / "strategies" / "folder_name"
    d.mkdir(parents=True)
    (d / "pack.json").write_text(json.dumps({"id": "different_id", "name": "N", "bucket": "growth", "thesis": "t", "author": "x"}))
    (d / "DECK.md").write_text("# d")
    _packs, probs = SP.load_packs([tmp_path / "strategies"], include_defaults=False)
    assert any("must match folder name" in p for x in probs for p in x["problems"])


def test_as_theses_projects_to_taxonomy_shape(tmp_path):
    _pack(tmp_path, "muni_x", bucket="defensive", positions=["ABC", "DEF"], edge="RP_FAIR")
    packs, _ = SP.load_packs([tmp_path / "strategies"], include_defaults=False)
    th = next(t for t in SP.as_theses(packs) if t["sid"] == "muni_x")
    assert th["sid"] == "muni_x" and th["bucket"] == "defensive" and th["n"] == 2
    assert th["pack"] is True and th["deck"] == "DECK.md"


def test_markdown_deck_is_safe_and_structured():
    md = "# Title\n\n## Sec\n\n- a\n- b\n\n**bold** and <script>x</script>\n\n| H |\n|---|\n| v |"
    h = render_markdown_deck("T", md, author="me")
    assert "<h1>Title</h1>" in h and "<h2>Sec</h2>" in h and "<li>a</li>" in h
    assert "<b>bold</b>" in h and "<table>" in h and "<th>H</th>" in h
    assert "<script>" not in h and "&lt;script&gt;" in h                # injection escaped
