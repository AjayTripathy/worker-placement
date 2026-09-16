"""S1 store-contract tests — merge-only, atomicity, provenance, schema rejection, JSONL."""
import json
import os

import pytest

from desk import store as S


@pytest.fixture
def tmp_store(tmp_path):
    return S.Store(tmp_path / "t.json", list_path="rows", key=lambda r: r["k"])


def test_upsert_merges_never_clobbers(tmp_store):
    tmp_store.upsert([{"k": "A", "x": 1}, {"k": "B", "x": 2}], generated_by="t1")
    # a second writer touching only B must not drop A (the clobber bug)
    counts = tmp_store.upsert([{"k": "B", "x": 3, "y": 9}], generated_by="t2")
    rows = {r["k"]: r for r in tmp_store.rows()}
    assert counts == {"added": 0, "updated": 1, "deleted": 0, "total": 2}
    assert rows["A"]["x"] == 1
    assert rows["B"] == {"k": "B", "x": 3, "y": 9}


def test_upsert_partial_row_merges_fields(tmp_store):
    tmp_store.upsert([{"k": "A", "x": 1, "note": "keep me"}], generated_by="t")
    tmp_store.upsert([{"k": "A", "x": 2}], generated_by="t")
    (row,) = tmp_store.rows()
    assert row["x"] == 2 and row["note"] == "keep me"


def test_delete_requires_explicit_keys(tmp_store):
    tmp_store.upsert([{"k": "A"}, {"k": "B"}], generated_by="t")
    counts = tmp_store.upsert([], generated_by="t", delete_keys={"A"})
    assert counts["deleted"] == 1
    assert [r["k"] for r in tmp_store.rows()] == ["B"]


def test_provenance_stamp(tmp_store):
    tmp_store.upsert([{"k": "A"}], generated_by="prov-test")
    meta = tmp_store.read()["_meta"]
    assert meta["generated_by"] == "prov-test"
    assert meta["asof"].endswith("Z") and len(meta["run_id"]) == 12


def test_backup_written_on_overwrite(tmp_store):
    tmp_store.upsert([{"k": "A"}], generated_by="t")
    tmp_store.upsert([{"k": "B"}], generated_by="t")
    bak = tmp_store.path.with_suffix(".json.bak")
    assert bak.exists()
    assert {r["k"] for r in json.loads(bak.read_text())["rows"]} == {"A"}


def test_corrupt_read_is_loud(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("{not json")
    with pytest.raises(S.StoreError):
        S.Store(p).read()


def test_corrupt_file_preserved_not_backed_up(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("{not json")
    st = S.Store(p, list_path="rows", key=lambda r: r["k"])
    # upsert on a corrupt store raises on read — data is never silently rebuilt
    with pytest.raises(S.StoreError):
        st.upsert([{"k": "A"}], generated_by="t")


def test_schema_rejects_bad_write(tmp_path, monkeypatch):
    pytest.importorskip("jsonschema")
    monkeypatch.setattr(S, "SCHEMA_DIR", tmp_path)
    (tmp_path / "strict.json").write_text(json.dumps({
        "type": "object", "required": ["rows"],
        "properties": {"rows": {"type": "array", "items": {
            "type": "object", "required": ["k", "v"],
            "properties": {"v": {"type": "number"}}}}}}))
    st = S.Store(tmp_path / "s.json", schema="strict", list_path="rows", key=lambda r: r["k"])
    with pytest.raises(S.StoreError):
        st.upsert([{"k": "A"}], generated_by="t")   # missing required v
    assert not st.path.exists()                     # invalid write left NO partial file
    st.upsert([{"k": "A", "v": 1.5}], generated_by="t")
    assert st.rows() == [{"k": "A", "v": 1.5}]


def test_atomic_no_tmp_left_behind(tmp_store):
    tmp_store.upsert([{"k": "A"}], generated_by="t")
    leftovers = [f for f in os.listdir(tmp_store.path.parent) if ".tmp" in f]
    assert leftovers == []


def test_jsonl_append_and_read(tmp_path):
    p = tmp_path / "l.jsonl"
    S.append_jsonl(p, {"a": 1}, generated_by="t")
    S.append_jsonl(p, {"a": 2}, generated_by="t")
    rows = S.read_jsonl(p)
    assert [r["a"] for r in rows] == [1, 2]
    assert all(r["_prov"]["generated_by"] == "t" for r in rows)


def test_jsonl_corrupt_line_is_loud(tmp_path):
    p = tmp_path / "l.jsonl"
    p.write_text('{"a": 1}\n{broken\n')
    with pytest.raises(S.StoreError):
        S.read_jsonl(p)
