"""The two-pass court: a GENERAL evaluation of the security (shareable by
construction) and a private SUITABILITY ruling on top of it."""
import copy
import json
from datetime import timedelta

import pytest

from officekit import strategy_proposals as jobs
from officekit_ai import strategy_proposal as pipeline
from officekit_ai.court import run_court
from officekit_ai.general_court import GENERAL_SCHEMA, run_general_court
from officekit_research import cases, general
from test_officekit_strategy_proposals import Provider, clients, seed
from test_contextual_research import proposal, execute, sources, shared, context, donor  # noqa: F401 (fixture)

SENTINELS = ["PRIVATE OWNER SENTINEL", "SECRET-MANDATE-NOTE", "HOUSEHOLD-DOCTRINE-SENTINEL", "987654"]


def _prompt_text(call):
    return call.get("system", "") + json.dumps(call["messages"])


def _general_calls(provider):
    """Bench + general adjudication calls are the ones made without a tenant binding."""
    return [c for c in provider.calls if "Tenant personal context" not in c.get("system", "")
            and ("case" in c["output_config"]["format"]["schema"]["properties"]
                 or "factor_profile" in c["output_config"]["format"]["schema"]["properties"])]


# ---- privacy by construction ---------------------------------------------------

def test_no_office_data_ever_reaches_the_general_court(tmp_path, monkeypatch):
    sources(monkeypatch)
    folder = tmp_path / "office"
    _, p = proposal(folder)
    # Plant private markers everywhere an office could leak from.
    p["snapshot"]["personal_context"]["doctrine"] = [{"id": "d1", "rule": "HOUSEHOLD-DOCTRINE-SENTINEL", "date": "2026-09-01"}]
    p["brief"]["thesis"] = "SECRET-MANDATE-NOTE " + p["brief"]["thesis"]
    p["snapshot"]["answers"]["goals"] = [{"id": "g", "kind": "spending", "label": "House", "amount": 987654}]
    jobs.save(folder, p)
    p, provider = execute(folder, p)

    general_calls = _general_calls(provider)
    assert len(general_calls) == 3                               # RED, BLUE, general adjudication
    for call in general_calls:
        text = _prompt_text(call)
        for marker in SENTINELS:
            assert marker not in text, marker + " reached the general court"
    # ...and the suitability ruling DID see the office (that is its job).
    suitability = [c for c in provider.calls if "fit_for" in c["output_config"]["format"]["schema"]["properties"]]
    assert len(suitability) == 1 and "Tenant personal context" in suitability[0]["system"]

    record = p["general"]["VDC"]["record"]
    blob = json.dumps(record)
    assert all(marker not in blob for marker in SENTINELS)
    assert "office_id" not in blob and general.validate(record)


def test_general_court_strips_the_office_book_from_its_evidence(tmp_path, monkeypatch):
    # Test the built-in public tape policy. The optional desk gateway can
    # legitimately replace it with a private connector during app imports.
    from officekit_research import SOURCE_CLASSES
    monkeypatch.setitem(SOURCE_CLASSES, "tape", "public_market")
    pack = {"symbol": "VDC", "built": "2026-09-19", "errors": ["book: KeyError: 'PRIVATE'", "tape: timeout"], "reuse": {},
            "sections": {"fund_profile": {"url": "https://example.org/f", "fetched_at": "2026-09-19", "text": "Public fund text", "truncated": False},
                         "book": {"held": True, "value": 987654, "owner": "PRIVATE OWNER SENTINEL"}}}
    public = general.public_pack(pack)
    assert set(public["sections"]) == {"fund_profile"} and public["errors"] == ["tape: source unavailable"]
    provider = Provider()
    record, private = run_general_court("VDC", "etf", pack, tmp_path, clients=clients(provider))
    assert all("987654" not in _prompt_text(c) and "SENTINEL" not in _prompt_text(c) for c in provider.calls)
    assert [e["section"] for e in record["evidence"]] == ["fund_profile"]
    assert set(private) == {"refs", "runs"} and "usage" in private["runs"]["red"]      # accounting stays home
    assert all("usage" not in run for run in record["runs"].values())                   # never in the shareable record


def test_general_court_refuses_structures_and_programs(tmp_path):
    for kind in ("options", "program"):
        with pytest.raises(ValueError, match="contextual"):
            run_general_court("SPY", kind, {}, tmp_path, clients=clients(Provider()))


# ---- the general record --------------------------------------------------------

def test_general_record_is_content_addressed_and_tamper_evident(tmp_path):
    record, _ = run_general_court("VDC", "etf", {}, tmp_path, clients=clients(Provider()))
    assert record["label"] == "LITE" and record["id"] == cases.digest({k: v for k, v in record.items() if k != "id"})
    forged = copy.deepcopy(record)
    forged["assessment"]["standing"] = "uninvestable"
    with pytest.raises(ValueError, match="digest"):
        general.validate(forged)
    private = copy.deepcopy(record)
    private["assessment"]["office_id"] = "x"
    with pytest.raises(ValueError):
        general.validate(private)


def test_schema_demands_a_factor_profile_not_a_purchase_verdict():
    props = GENERAL_SCHEMA["properties"]
    assert "factor_profile" in props and "verdict" not in props and "conviction" not in props
    assert set(props["standing"]["enum"]) == general.STANDINGS


# ---- one security, many strategies: general research is generated once ---------

def test_second_strategy_on_same_security_reuses_the_general_evaluation(tmp_path, monkeypatch):
    sources(monkeypatch)
    folder = tmp_path / "office"
    _, first = proposal(folder)
    first, provider = execute(folder, first)
    assert len(provider.calls) == 7 and not first["general"]["VDC"]["reused"]

    _, second = seed(folder, option="hedge")                # a different mandate on the same security
    assert second["id"] != first["id"]
    second["research_context"] = context()
    second["snapshot"]["personal_context"]["jurisdictions"] = {"country": "US"}
    jobs.save(folder, second)
    second, provider2 = execute(folder, second)
    assert second["general"]["VDC"]["reused"] is True
    assert second["general"]["VDC"]["record"]["id"] == first["general"]["VDC"]["record"]["id"]
    assert len(provider2.calls) == 4                       # analyst, suitability, risk, pitch — no second general court
    # Each office ruling is still its own.
    assert second["courts"][0]["id"] != first["courts"][0]["id"]
    assert second["courts"][0]["general_id"] == first["courts"][0]["general_id"]
    assert set(second["courts"][0]["runs"]) == {"adjudicate"}      # reused research cost this proposal nothing


def test_stale_or_other_protocol_general_research_is_not_reused(tmp_path):
    record, _ = run_general_court("VDC", "etf", {"symbol": "VDC", "built": "2026-09-19", "errors": [], "reuse": {}, "sections": {
        "fund_profile": {"url": "https://example.org/f", "fetched_at": "2026-09-19", "text": "t", "truncated": False}}},
        tmp_path, clients=clients(Provider()))
    today = cases.day(record["as_of"])
    assert general.find(tmp_path, "VDC", "etf", record["protocol_hash"], today=today)["id"] == record["id"]
    assert general.find(tmp_path, "VDC", "etf", "0" * 64, today=today) is None                       # different doctrine
    assert general.find(tmp_path, "VDC", "etf", record["protocol_hash"], today=today + timedelta(days=31)) is None
    assert general.find(tmp_path, "VDC", "stock", record["protocol_hash"], today=today) is None


def test_intelligence_level_gates_reuse(tmp_path):
    pack = {"symbol": "VDC", "built": "2026-09-19", "errors": [], "reuse": {}, "sections": {
        "fund_profile": {"url": "https://example.org/f", "fetched_at": "2026-09-19", "text": "t", "truncated": False}}}
    weak = {s: (Provider(), "test-sonnet") for s in ("bench", "adjudicate")}
    record, _ = run_general_court("VDC", "etf", pack, tmp_path, clients=weak)
    from officekit_ai.court import _tier_of
    today = cases.day(record["as_of"])
    ok = general.find(tmp_path, "VDC", "etf", record["protocol_hash"], today=today, minimum_tier=_tier_of("sonnet"), tier_of=_tier_of)
    assert ok and ok["id"] == record["id"]
    # An office adjudicating at a stronger tier re-runs rather than trusting weaker research.
    assert general.find(tmp_path, "VDC", "etf", record["protocol_hash"], today=today, minimum_tier=_tier_of("opus"), tier_of=_tier_of) is None


def test_suitability_adjudicator_may_not_be_weaker_than_the_general_bench(tmp_path):
    strong = {s: (Provider(), "test-opus") for s in ("bench", "adjudicate")}
    record, _ = run_general_court("VDC", "etf", {}, tmp_path, clients=strong)
    from officekit.personal_context import empty
    weak = {"bench": (Provider(), "test-haiku"), "adjudicate": (Provider(), "test-haiku")}
    with pytest.raises(RuntimeError, match="weaker tier"):
        run_court("VDC", "core_equity", {"status": "considering"}, empty("o"), tmp_path, clients=weak,
                  evidence={}, general=record)


# ---- the shared case built on a two-pass court ---------------------------------

def test_general_briefs_survive_projection_while_the_ruling_is_redacted(tmp_path, monkeypatch):
    sources(monkeypatch)

    class Facts(Provider):
        def create(self, **kw):
            response = super().create(**kw)
            props = kw["output_config"]["format"]["schema"]["properties"]
            out = json.loads(response.content[0].text)
            if "case" in props:
                out["case"] = "Revenue grew from $4.2B to $5.1 billion; 2450000000 shares outstanding."
            elif "fit_for" in props:
                out["rationale"] = "Fits after the $90,000 House payment."
            response.content[0].text = json.dumps(out)
            return response

    folder = tmp_path / "office"
    _, p = proposal(folder)
    p["snapshot"]["answers"]["goals"] = [{"id": "g", "kind": "spending", "label": "House", "amount": 90000}]
    jobs.save(folder, p)
    p, _ = execute(folder, p, Facts())
    case = cases.prepare_case(p, "VDC")["case"]
    assert "$4.2B" in case["court"]["briefs"]["red"]["case"]                   # public facts intact
    assert "2450000000" in case["court"]["briefs"]["red"]["case"]
    assert "90,000" not in case["court"]["rationale"] and "omitted]" in case["court"]["rationale"]
    assert case["court"]["general_id"] == p["courts"][0]["general_id"]
    cases.validate_case(case)


def test_a_sleeve_named_after_the_ticker_does_not_scrub_the_subject(tmp_path, monkeypatch):
    sources(monkeypatch)
    folder = tmp_path / "office"
    _, p = proposal(folder)
    p["snapshot"]["answers"].setdefault("sleeves", []).append({"name": "VDC", "value": 250000})
    jobs.save(folder, p)
    p, _ = execute(folder, p)
    p["courts"][0]["rationale"] = "VDC is appropriate; VDC adds staples exposure."
    case = cases.prepare_case(p, "VDC")["case"]
    assert case["court"]["rationale"].count("VDC") == 2
    assert "250" not in json.dumps(case["court"]["rationale"])


# ---- independent contributors agree unless the CONTENT differs -----------------

def test_identical_content_read_at_different_times_is_corroboration_not_conflict(tmp_path, donor_pair):
    office, p, first, second = donor_pair
    cases.import_bundle(office, first)
    cases.import_bundle(office, second)
    found = cases.retrieve(office, p)
    assert not any(found["evidence_conflicts"].values())         # no section is in conflict
    reused, conflicts = cases.reusable_sections(found, "VDC")
    assert conflicts == [] and "fund_profile" in reused
    assert len(reused["fund_profile"]["case_ids"]) == 2                      # both contributors credited


@pytest.fixture
def donor_pair(tmp_path, monkeypatch):
    """Two contributors who read the SAME source text at different moments."""
    sources(monkeypatch)
    bundles = []
    for i, stamp in enumerate(("T09:00:00+00:00", "T15:30:00+00:00")):
        folder = tmp_path / f"donor{i}"
        _, p = proposal(folder)
        p, _ = execute(folder, p)
        draft = cases.prepare_case(p, "VDC")
        for e in draft["case"]["evidence"]:
            e["data"]["fetched_at"] = e["data"]["fetched_at"][:10] + stamp
            e["data"]["text"] = "Identical issuer text for VDC."
            e["retrieved_at"] = e["data"]["fetched_at"]
            e["sha256"] = cases.digest(e["data"])
        bundles.append(cases.approve(draft, cases.digest(draft["case"]), [{"section": "fund_profile", "basis": "original_summary",
                       "valid_until": (cases.day(cases.utcnow()) + timedelta(days=7)).isoformat()}]))
    assert bundles[0]["case"]["evidence"][0]["sha256"] != bundles[1]["case"]["evidence"][0]["sha256"]   # envelopes differ
    office = tmp_path / "recipient"
    _, p = proposal(office)
    return office, p, bundles[0], bundles[1]


# ---- shareable SEC facts, and expiry by KIND of evidence -----------------------

CIK = 1045810


def _xbrl(fetched="2026-09-19T10:00:00+00:00", val=35082000000):
    return {"rev": [{"end": "2026-07-27", "val": val, "form": "10-Q", "tag": "Revenues", "accn": "0001045810-26-000021"}],
            "_source": {"cik": CIK, "fetched_at": fetched,
                        "url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK:010d}.json"}}


def _entry(section, data):
    url, fetched = cases.source_of(data)
    return {"section": section, "symbol": "NVDA", "retrieved_at": fetched, "source_url": url,
            "data": data, "sha256": cases.digest(data)}


def test_as_filed_xbrl_facts_are_shareable_with_per_fact_locators():
    cases.validate_evidence(_entry("xbrl", _xbrl()))          # accepted: cik + companyfacts url + tag + accession


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d["rev"][0].pop("accn"), "XBRL fact"),                                    # unlocatable number
    (lambda d: d["rev"][0].update(accn="not-an-accession"), "accession"),
    (lambda d: d["rev"][0].update(val=float("inf")), "finite|JSON compliant"),   # refused before it can even be hashed
    (lambda d: d["_source"].update(url="https://evil.example/facts.json"), "companyfacts"),
    (lambda d: d.update(made_up_series=d["rev"]), "Unsupported XBRL"),
])
def test_unverifiable_or_malformed_xbrl_is_refused(mutate, message):
    data = _xbrl()
    mutate(data)
    with pytest.raises(ValueError, match=message):
        cases.validate_evidence(_entry("xbrl", data))       # building the entry hashes it; both steps must refuse


def test_xbrl_read_at_different_times_agrees_but_a_restated_number_conflicts():
    same = cases.content_sha256("xbrl", _xbrl("2026-09-01T00:00:00+00:00"))
    assert same == cases.content_sha256("xbrl", _xbrl("2026-09-19T23:59:00+00:00"))
    assert same != cases.content_sha256("xbrl", _xbrl(val=35082000001))


def test_filings_index_needs_the_registrants_submissions_locator():
    good = {"entity": "NVIDIA CORP", "cik": CIK, "fetched_at": "2026-09-19T10:00:00+00:00",
            "url": f"https://data.sec.gov/submissions/CIK{CIK:010d}.json",
            "recent": [{"form": "10-Q", "date": "2026-08-27", "acc": "0001045810-26-000021"}]}
    cases.validate_evidence(_entry("filings", good))
    with pytest.raises(ValueError, match="submissions"):
        cases.validate_evidence(_entry("filings", {**good, "url": "https://data.sec.gov/submissions/CIK0000000001.json"}))


def test_facts_may_be_granted_longer_than_snapshots(donor):
    """A live fund page drifts in weeks; a dated filing never changes."""
    assert cases.EVIDENCE_TTL_DAYS["filing_text"] > cases.EVIDENCE_TTL_DAYS["xbrl"] > cases.EVIDENCE_TTL_DAYS["fund_profile"]
    _, p, _, _ = donor
    draft = cases.prepare_case(p, "VDC")
    collected = cases.day(draft["case"]["evidence"][0]["retrieved_at"])
    def grant(days):
        return [{"section": "fund_profile", "basis": "original_summary", "valid_until": (collected + timedelta(days=days)).isoformat()}]
    cases.approve(draft, cases.digest(draft["case"]), grant(30))
    with pytest.raises(ValueError, match="within 30 days"):                  # a snapshot cannot borrow a fact's lifetime
        cases.approve(draft, cases.digest(draft["case"]), grant(120))


def test_live_xbrl_source_emits_the_shareable_shape(monkeypatch):
    import officekit_research as research
    payload = {"units": {"USD": [{"end": "2026-07-27", "val": 1, "form": "10-Q", "accn": "0001045810-26-000021"}]}}
    monkeypatch.setattr(research, "_get_json", lambda url, contact: payload)
    data = research.SOURCES["xbrl"]("NVDA", {"cik": CIK, "contact": "c@example.org"})
    assert "rev" in data and "dil_sh" in data                                # legacy readers still find flat keys
    cases.validate_evidence(_entry("xbrl", {k: v for k, v in data.items() if k in cases.XBRL_KEYS | {"_source"}}))
    from officekit_research import render_pack
    md = render_pack({"symbol": "NVDA", "built": "now", "sections": {"xbrl": data}, "errors": []})
    assert "_source" not in md and "NEWER periods may exist" in md
