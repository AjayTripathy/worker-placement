"""Adversarial admission and failure contracts; no live APIs or office data."""
import copy
import json

import pytest

from officekit_ai.general_court import run_general_court
from officekit_research import general, admission, contributor, index
from research_admission_fixtures import fixture_reviewer, fixture_admission
from test_officekit_strategy_proposals import Provider, clients

PACK = {"symbol": "VDC", "built": "2026-09-20", "sections": {"fund_profile": {
    "url": "https://example.org/fund", "fetched_at": "2026-09-20T10:12:35Z",
    "text": "The fund invests in consumer staples equities.", "truncated": False}}, "errors": []}


@pytest.fixture
def record(tmp_path):
    return run_general_court("VDC", "etf", PACK, tmp_path, clients=clients(Provider()))[0]


def test_unknown_sections_and_extra_fields_never_reach_public_prompts(record):
    pack = copy.deepcopy(PACK)
    pack["sections"]["new_connector"] = {"visibility": "public", "text": "PRIVATE DETAIL"}
    pack["sections"]["fund_profile"]["internal_request"] = "PRIVATE DETAIL"
    pack["errors"] = ["new_connector: PRIVATE DETAIL", "tape: PRIVATE DETAIL"]
    public = general.public_pack(pack)
    assert public["sections"] == {}
    assert "PRIVATE DETAIL" not in json.dumps(public)
    assert public["errors"]


def test_public_declaration_alone_does_not_grant_an_untyped_section(monkeypatch):
    from officekit_research import SOURCE_CLASSES
    monkeypatch.setitem(SOURCE_CLASSES, "future", "public_document")
    pack = {**PACK, "sections": {"future": PACK["sections"]["fund_profile"]}}
    assert general.public_pack(pack)["sections"] == {}


def test_registration_defaults_private(monkeypatch):
    import officekit_research as research
    monkeypatch.setattr(research, "SOURCES", {})
    monkeypatch.setattr(research, "SOURCE_CLASSES", {})
    research.evidence_source("future")(lambda *_: {})
    assert research.SOURCE_CLASSES["future"] == "private"


@pytest.mark.parametrize("defect", ["omit", "unsupported", "quote", "digest", "self_review", "no_claims"])
def test_claim_admission_fails_closed(record, defect):
    def reviewer(r, fields, passages):
        report = fixture_reviewer(r, fields, passages)
        finding = report["findings"][0]
        if defect == "omit": report["findings"].pop()
        elif defect == "unsupported": finding["supported"] = False
        elif defect == "quote": finding["claims"][0]["quote"] = "A fabricated source quote."
        elif defect == "digest": finding["claims"][0]["content_sha256"] = "0" * 64
        elif defect == "self_review": report["reviewer"] = r["models"]["adjudicate"]
        elif defect == "no_claims": finding["claims"] = []
        return report
    with pytest.raises(ValueError): admission.verify(record, PACK, reviewer)


def test_failed_review_and_changed_publisher_source_cannot_admit(record):
    def outage(*args): raise RuntimeError("provider credit exhausted")
    with pytest.raises(ValueError, match="review failed"):
        admission.verify(record, PACK, outage)
    moved = copy.deepcopy(PACK)
    moved["sections"]["fund_profile"]["text"] += " Different mandate."
    with pytest.raises(ValueError, match="differs"):
        admission.verify(record, moved, fixture_reviewer)
    with pytest.raises(ValueError, match="not configured"):
        admission.verify(record, PACK, None)


def test_no_review_or_self_asserted_review_enters_hosted_store(record):
    from hosting.app.exchange import Exchange
    from hosting.app.auth import AuthFailure
    from test_hosted_migration import MemoryStore
    store = MemoryStore()
    with pytest.raises(AuthFailure) as error:
        Exchange(store).submit("alice", record)
    assert error.value.status == 503 and store.rows == {}
    forged = copy.deepcopy(record)
    forged["assessment"]["summary"] = "A private unsupported assertion."
    forged = general.seal({k:v for k,v in forged.items() if k not in {"id", "schema"}})
    def reject(r, f, p):
        report = fixture_reviewer(r, f, p)
        report["findings"][0]["supported"] = False
        return report
    with pytest.raises(AuthFailure):
        Exchange(store, evidence_loader=lambda _: PACK, reviewer=reject).submit("alice", forged)
    assert store.rows == {}


def test_existing_unreviewed_hosted_rows_are_not_listed_or_exported(record):
    from hosting.app.exchange import Exchange
    from test_hosted_migration import MemoryStore
    store = MemoryStore()
    store.put("exchange/general/VDC/" + record["id"], record)
    service = Exchange(store)
    assert service.listing("VDC") == [] and list(service.export()) == []


def test_hosted_retry_reuses_intact_admission_and_hides_corrupt_report(record):
    from hosting.app.exchange import Exchange
    from hosting.app.auth import AuthFailure
    from test_hosted_migration import MemoryStore
    calls = []
    def reviewer(*args):
        calls.append(True)
        return fixture_reviewer(*args)
    store = MemoryStore()
    service = Exchange(store, evidence_loader=lambda _: PACK, reviewer=reviewer)
    assert service.submit("alice", record)["status"] == "contributed"
    assert service.submit("alice", record)["status"] == "already_present"
    assert len(calls) == 1
    review_key = "exchange/reviews/" + record["id"]
    review, generation = store.get(review_key)
    review["report"]["findings"].pop()
    store.put(review_key, review, generation)
    assert service.listing("VDC") == [] and list(service.export()) == []
    with pytest.raises(AuthFailure):
        Exchange(store).submit("alice", record)
    service.submit("alice", record)
    assert len(calls) == 2 and service.read("VDC", record["id"]) == record


def test_anonymous_default_and_source_times_coarsened(record):
    assert contributor.contributor_key({"office_id": "a" * 36}) is None
    assert record["evidence"][0]["retrieved_at"] == "2026-09-20"


def test_hosted_publication_transport_failure_is_safe_and_explicit(record):
    from officekit_research.hosted import Client
    class Offline:
        base_url = "https://example.org"
        def post(self, *args, **kwargs):
            raise TimeoutError("PRIVATE REQUEST DETAIL")
    with pytest.raises(ValueError, match="Hosted research post unavailable") as error:
        Client(Offline(), "secret").submit(record)
    assert "PRIVATE" not in str(error.value) and "secret" not in str(error.value)


def test_imported_producer_survives_reuse_and_index_rebuild(tmp_path, record):
    recipient = tmp_path / "recipient"
    people = [{"record_id": record["id"], "contributor": "a" * 32, "attribution": "verified"},
              {"record_id": record["id"], "contributor": "b" * 32, "attribution": "claimed"}]
    general.save(recipient, record, origin="imported", attributions=people)
    general.save(recipient, record)  # ordinary reuse does not acquire authorship
    row = index.query(recipient)[0]
    assert row["origin"] == "imported" and row["contributor"] is None
    assert {p["contributor"] for p in row["contributors"]} == {"a"*32, "b"*32}
    assert general.load(recipient, record["id"]) == record
    index.index_path(recipient).unlink()
    assert index.query(recipient)[0] == row
    index.resolve(recipient, record["id"] + ":0", True, "https://example.org/outcome")
    assert {r["contributor"] for r in index.scoreboard(recipient, "contributor")} == {"a"*32, "b"*32}


def test_missing_legacy_origin_is_unknown_not_self(tmp_path, record):
    folder = tmp_path / "old"
    general.save(folder, record)
    row = index.query(folder)[0]
    assert row["origin"] == "unknown" and row["contributor"] is None


def test_import_rejects_bad_attribution_before_writing_and_deduplicates_authors(tmp_path, record):
    tmp_path = tmp_path / "recipient"
    person = {"record_id": record["id"], "contributor": "a" * 32, "attribution": "verified"}
    with pytest.raises(ValueError):
        general.save(tmp_path, record, origin="imported", attributions=[{**person, "record_id": "bad"}])
    assert general.load(tmp_path, record["id"]) is None
    general.save(tmp_path, record, origin="imported", attributions=[person, person])
    row = index.query(tmp_path)[0]
    assert len(row["contributors"]) == 1
    meta = tmp_path / "research" / "origins" / (record["id"] + ".json")
    meta.write_text(json.dumps({"record_id": record["id"], "origin": "own", "contributors": "bad"}))
    assert general.provenance(tmp_path, record["id"])["origin"] == "unknown"


def test_failed_and_partial_acquisition_runs_have_nonzero_cli_status(monkeypatch, tmp_path, capsys):
    from verticals.public_co.m_sources import acq_coherence as acq
    from types import SimpleNamespace
    import verticals.cli
    path = tmp_path / "case.json"
    path.write_text(json.dumps({"parent_thesis": "Synthetic thesis", "acquisitions": [{"acquired_name": "A"}, {"acquired_name": "B"}]}))
    monkeypatch.setattr(verticals.cli, "selftest_or_input", lambda *a, **kw: SimpleNamespace(case=str(path)))
    import officekit_ai.models
    monkeypatch.setattr(officekit_ai.models, "client_for", lambda *a, **kw: (object(), "gpt-6-astra"))
    monkeypatch.setattr(acq, "_score_one_acquisition", lambda *a, **kw: {"error": "Credit exhausted"})
    assert acq.main() == 1
    failed = json.loads(capsys.readouterr().out)
    assert failed["status"] == "error" and failed["n_acquisitions_failed"] == 2
    monkeypatch.setattr(acq, "_score_one_acquisition", lambda _, a, **kw: {"error": "Credit exhausted"} if a["acquired_name"] == "B"
                        else {"coherence_score": .8, "is_revenue_synthetic": False})
    assert acq.main() == 1
    partial = json.loads(capsys.readouterr().out)
    assert partial["status"] == "partial" and partial["n_acquisitions_scored"] == 1
    path.write_text(json.dumps({"parent_thesis": "Synthetic thesis", "acquisitions": []}))
    def unavailable(*a, **kw): raise RuntimeError("No key")
    monkeypatch.setattr(officekit_ai.models, "client_for", unavailable)
    assert acq.main() == 0
    assert json.loads(capsys.readouterr().out)["signal"] == "NO_ACQUISITIONS"
