"""Synthetic reviewer for mechanics tests. Never a source-support quality grade."""
from officekit_research.admission import verify


def fixture_reviewer(record, fields, passages):
    section = next(iter(passages))
    source = next(e for e in record["evidence"] if e["section"] == section)
    return {"reviewer": "fixture-independent-reviewer", "findings": [
        {"field": field, "supported": True, "claims": [] if value == "[]" else [
            {"statement": value, "kind": "inference", "section": section,
             "content_sha256": source["content_sha256"], "quote": passages[section],
             "reasoning": "Synthetic support judgment, for transport and boundary tests only."}]}
        for field, value in fields.items()]}


def fixture_admission(record, pack):
    return verify(record, pack, fixture_reviewer)
