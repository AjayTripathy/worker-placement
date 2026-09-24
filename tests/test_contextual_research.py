"""Two-office contract tests. Provider fixtures test mechanics, not investment skill."""
import copy
from datetime import date, timedelta
import json

import pytest

from officekit import strategy_proposals as jobs
from officekit_ai import strategy_proposal as pipeline
from officekit_research import cases
from test_officekit_strategy_proposals import Provider, clients, seed
from test_officekit_onboarding_e2e import server, _get, _post


def context(**overrides):
    return {"strategy": "deploy_powder", "goal_types": ["risk_reduction"], "goal_basis": "declared",
            "life_stage": "accumulating", "horizon": "over_7y", "liquidity": "unspecified", "country": "US", **overrides}


def sources(monkeypatch):
    import officekit_research as research
    counts = {"fund_profile": 0, "tape": 0, "book": 0}
    def profile(symbol, ctx):
        counts["fund_profile"] += 1
        return {"url": "https://example.org/issuer/" + symbol, "fetched_at": cases.utcnow(),
                "text": "Evaluation fixture: " + symbol + " is a consumer-staples equity fund; sector concentration and equity loss remain possible.", "truncated": False}
    def tape(symbol, ctx):
        counts["tape"] += 1
        return dict(last=100, as_of=cases.day(cases.utcnow()).isoformat(), wk52_hi=110, wk52_lo=90, off_high_pct=-9, off_low_pct=11)
    original_book = research.SOURCES["book"]
    def book(symbol, ctx):
        counts["book"] += 1
        return original_book(symbol, ctx)
    for name, fn in (("fund_profile", profile), ("tape", tape), ("book", book)):
        monkeypatch.setitem(research.SOURCES, name, fn)
    return counts


def proposal(folder, ctx=None):
    folder.mkdir(exist_ok=True)
    answers, p = seed(folder)
    p["research_context"] = ctx or context()
    if p["research_context"]["life_stage"] != "unknown":
        p["snapshot"]["answers"]["profile"]["decumulating"] = p["research_context"]["life_stage"] == "decumulating"
        p["snapshot"]["data"]["profile"]["decumulating"] = p["research_context"]["life_stage"] == "decumulating"
    p["snapshot"]["personal_context"]["jurisdictions"] = {"country": "US" if p["research_context"]["country"] == "US" else "Canada"}
    p["snapshot"]["answers"]["owner"] = "PRIVATE OWNER SENTINEL"
    jobs.save(folder, p)
    return answers, p


def execute(folder, p, provider=None, reuse=True, contextual_reuse=True):
    provider = provider or Provider()
    jobs.run(folder, p["id"], lambda r, d, save: pipeline.build_proposal(r, d, save, clients(provider), reuse=reuse, contextual_reuse=contextual_reuse))
    p = jobs.load(folder, p["id"])
    assert p["status"] in {"ready", "needs_review"}, p["errors"]
    return p, provider


def shared(p, **kwargs):
    draft = cases.prepare_case(p, "VDC")
    return cases.approve(draft, cases.digest(draft["case"]),
                         [{"section": "fund_profile", "basis": "original_summary",
                           "valid_until": (cases.day(cases.utcnow()) + timedelta(days=7)).isoformat()}], **kwargs)


@pytest.fixture
def donor(tmp_path, monkeypatch):
    counts = sources(monkeypatch)
    folder = tmp_path / "donor"
    _, p = proposal(folder)
    p, _ = execute(folder, p)
    return folder, p, shared(p), counts


def test_two_offices_reuse_evidence_but_run_independent_courts(tmp_path, donor):
    donor_folder, original, bundle, counts = donor
    folder = tmp_path / "recipient"
    _, p = proposal(folder, context(life_stage="decumulating", liquidity="ongoing_spending"))
    before = copy.deepcopy(p["snapshot"])
    cases.import_bundle(folder, bundle)
    p, provider = execute(folder, p)
    assert counts == {"fund_profile": 1, "book": 2, "tape": 2}
    assert len(provider.calls) == 7
    assert p["snapshot"] == before
    assert p["courts"][0]["id"] != original["courts"][0]["id"]
    assert p["courts"][0]["refs"] != original["courts"][0]["refs"]
    match = p["research_reuse"]["matches"][0]
    assert match["context_fit"] == "needs_comparison"
    assert {d["field"] for d in match["differences"]} >= {"life_stage", "liquidity"}
    assert p["evidence"]["VDC"]["acquisition"]["reused"] == ["fund_profile"]
    assert "Reused public evidence" in p["courts"][0]["evidence"]["md"]
    assert bundle["id"] in p["courts"][0]["evidence"]["md"]
    captured = json.loads((folder / "research/private_cases" / (p["id"] + ".json")).read_text())
    assert captured["decision"]["execution"] == "unconfirmed"
    assert captured["decision"]["reason"] is None
    assert captured["reused_case_ids"] == [bundle["id"]]
    assert (donor_folder / "research/private_cases" / (original["id"] + ".json")).exists()


def test_projection_preserves_context_and_arguments_with_known_private_details_removed(donor):
    _, p, _, _ = donor
    p["courts"][0]["rationale"] = "PRIVATE OWNER SENTINEL should preserve $250,000 for spending; 100,000 is recorded as cash. Concentration remains a concern."
    draft = cases.prepare_case(p, "VDC")
    value = json.dumps(draft)
    assert "PRIVATE OWNER SENTINEL" not in value and "$250,000" not in value
    assert '100,000' not in value
    assert "Concentration remains a concern" in draft["case"]["court"]["rationale"]
    assert draft["case"]["context"]["goal_types"] == ["risk_reduction"]
    assert draft["case"]["investigation"]["alternatives"]
    assert 'cash' in ' '.join(draft["case"]["investigation"]["alternatives"]).lower()
    assert '"office_id"' not in value and '"positions"' not in value
    assert not any(e["section"] in {"book", "tape"} for e in draft["case"]["evidence"])
    assert draft["review_required"] is True


@pytest.mark.parametrize("change, expected", [
    ({"horizon": "under_2y"}, "Near-term"),
    ({"country": "non_US"}, "jurisdictions"),
])
def test_incompatible_cases_do_not_enter_model_context_or_skip_sources(tmp_path, donor, change, expected):
    _, _, b, counts = donor
    folder = tmp_path / "recipient"
    _, p = proposal(folder, context(**change))
    cases.import_bundle(folder, b)
    p, _ = execute(folder, p)
    assert not p["research_reuse"]["matches"]
    assert any(expected in reason for r in p["research_reuse"]["rejected"] for reason in r["reasons"])
    assert counts["fund_profile"] == 2


def test_excluded_ticker_never_reuses_approval(tmp_path, donor):
    _, _, b, _ = donor
    folder = tmp_path / "recipient"
    _, p = proposal(folder)
    p["snapshot"]["personal_context"]["exclusions"] = [{"scope": "ticker", "value": "VDC"}]
    jobs.save(folder, p)
    cases.import_bundle(folder, b)
    p, _ = execute(folder, p)
    assert p["research_reuse"]["rejected"][0]["reasons"] == ["Investment is excluded by this office"]
    assert not p["basket"][0]["eligible"] and p["basket"][0]["amount"] == 0


def test_expired_evidence_may_inform_context_but_must_be_refetched(tmp_path, donor):
    _, _, b, _ = donor
    folder = tmp_path / "recipient"
    _, p = proposal(folder)
    cases.import_bundle(folder, b)
    future = cases.day(cases.utcnow()) + timedelta(days=8)
    found = cases.retrieve(folder, p, today=future)
    assert found["matches"]
    reused, conflicts = cases.reusable_sections(found, "VDC", today=future)
    assert reused == {} and conflicts == []


def test_case_age_and_future_availability_are_enforced(tmp_path, donor):
    _, _, b, _ = donor
    folder = tmp_path / "recipient"
    _, p = proposal(folder)
    cases.import_bundle(folder, b)
    assert not cases.retrieve(folder, p, today=cases.day(cases.utcnow()) - timedelta(days=1))["matches"]
    assert not cases.retrieve(folder, p, today=cases.day(cases.utcnow()) + timedelta(days=91))["matches"]


def test_contradictory_source_snapshots_force_refresh(tmp_path, donor):
    _, p, b, counts = donor
    folder = tmp_path / "recipient"
    _, q = proposal(folder)
    cases.import_bundle(folder, b)
    p = copy.deepcopy(p)
    p["evidence"]["VDC"]["sections"]["fund_profile"]["text"] = "A contradictory claim about the fund mandate."
    cases.import_bundle(folder, shared(p))
    q, _ = execute(folder, q)
    assert len(q["research_reuse"]["matches"]) == 2
    assert q["evidence"]["VDC"]["acquisition"]["conflicts"] == ["fund_profile"]
    assert counts["fund_profile"] == 2


def test_review_and_import_detect_tampering_and_private_fields(tmp_path, donor):
    _, p, b, _ = donor
    draft = cases.prepare_case(p, "VDC")
    before = cases.digest(draft["case"])
    draft["case"]["investigation"]["thesis"] = "Changed after review"
    with pytest.raises(ValueError, match="changed since review"):
        cases.approve(draft, before)
    b["case"]["court"]["verdict"] = "OWN 10/10"
    with pytest.raises(ValueError, match="digest mismatch"):
        cases.import_bundle(tmp_path, b)
    draft["case"]["office_id"] = "private"
    with pytest.raises(ValueError):
        cases.approve(draft, cases.digest(draft["case"]))


def test_evidence_permission_is_separate_from_context_review(tmp_path, donor):
    _, p, _, _ = donor
    draft = cases.prepare_case(p, "VDC")
    b = cases.approve(draft, cases.digest(draft["case"]))
    folder = tmp_path / "recipient"
    _, q = proposal(folder)
    cases.import_bundle(folder, b)
    found = cases.retrieve(folder, q)
    assert found["matches"]
    assert cases.reusable_sections(found, "VDC") == ({}, [])


def test_evaluation_fixtures_do_not_enter_normal_proposals(tmp_path, donor):
    _, p, _, _ = donor
    draft = cases.prepare_case(p, "VDC")
    draft["case"]["provenance"]["kind"] = "evaluation_scenario"
    b = cases.approve(draft, cases.digest(draft["case"]))
    folder = tmp_path / "recipient"
    _, q = proposal(folder)
    cases.import_bundle(folder, b)
    assert not cases.retrieve(folder, q)["matches"]
    assert cases.retrieve(folder, q, include_evaluation=True)["matches"]


def test_reexport_does_not_reset_evidence_age(tmp_path, donor):
    _, _, b, _ = donor
    folder = tmp_path / "recipient"
    _, p = proposal(folder)
    cases.import_bundle(folder, b)
    p, _ = execute(folder, p)
    p["evidence"]["VDC"]["built"] = (cases.day(cases.utcnow()) + timedelta(days=10)).isoformat()
    draft = cases.prepare_case(p, "VDC")
    assert draft["case"]["evidence"][0]["retrieved_at"] == b["case"]["evidence"][0]["retrieved_at"]
    assert draft["case"]["provenance"]["derived_from"] == [b["id"]]


def test_retry_does_not_rerun_courts_or_reacquire_reused_sources(tmp_path, donor):
    _, _, b, counts = donor
    folder = tmp_path / "recipient"
    _, p = proposal(folder)
    cases.import_bundle(folder, b)
    fake = Provider(fail_pitch=True)
    jobs.run(folder, p["id"], lambda r, d, save: pipeline.build_proposal(r, d, save, clients(fake)))
    p = jobs.load(folder, p["id"])
    assert p["status"] == "error"
    calls = len(fake.calls)
    jobs.retry(folder, p["id"])
    fake.fail_pitch = False
    p, _ = execute(folder, p, fake)
    assert len(fake.calls) == calls + 1
    assert counts == {"fund_profile": 1, "book": 2, "tape": 2}


def test_import_is_idempotent_and_malformed_files_are_visible(tmp_path, donor):
    _, _, b, _ = donor
    folder = tmp_path / "recipient"
    _, p = proposal(folder)
    cases.import_bundle(folder, b)
    cases.import_bundle(folder, b)
    (folder / "research/shared_cases/bad.json").write_text('{"id":"broken"}')
    found = cases.retrieve(folder, p)
    assert len(found["matches"]) == 1 and len(found["errors"]) == 1


def test_private_capture_never_enters_the_public_library(donor):
    folder, p, _, _ = donor
    assert cases.load_library(folder) == ([], [])
    p["status"] = "adopted"
    jobs.save(folder, p)
    record = json.loads((folder / "research/private_cases" / (p["id"] + ".json")).read_text())
    assert record["decision"]["status"] == "adopted"
    assert record["decision"]["execution"] == "unconfirmed"


def test_legacy_export_only_emits_reviewed_bundles(donor):
    from officekit_ai.court import export_shareable_adjudications
    folder, p, bundle, _ = donor
    assert export_shareable_adjudications(folder) == []
    cases.import_bundle(folder, bundle)
    exported = export_shareable_adjudications(folder)
    assert exported == [bundle]
    assert '"office_id"' not in json.dumps(exported)


def test_symlink_inside_office_cannot_write_outside(tmp_path, donor):
    _, _, bundle, _ = donor
    outside = tmp_path / 'outside'
    outside.mkdir()
    office = tmp_path / 'office'
    office.mkdir()
    (office / 'research').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='symbolic'):
        cases.import_bundle(office, bundle)
    assert list(outside.iterdir()) == []


def test_hosted_runtime_uses_identical_retained_corpus(tmp_path, donor):
    from officekit.runtime import hosted_office
    from officekit.migration import safe_path
    _, _, b, _ = donor
    folder = tmp_path / "hosted"
    _, p = proposal(folder)
    with hosted_office(folder):
        cases.import_bundle(folder, b)
        p, _ = execute(folder, p)
    assert p["evidence"]["VDC"]["acquisition"]["reused"] == ["fund_profile"]
    assert safe_path("research/shared_cases/" + b["id"] + ".json")


def test_shared_http_review_import_and_revision_gates(server, donor):
    from officekit.serve import build_office
    from officekit.commitments import revision
    base, folder = server
    _, _, bundle, _ = donor
    a, p = proposal(folder)
    p, _ = execute(folder, p)
    build_office(a, folder)
    rev = revision(json.loads((folder / 'answers.json').read_text()))
    page = _get(base + '/research')
    assert 'Prepare review draft' in page and 'Import a reviewed case' in page
    import re
    for form in re.findall(r'<form\b.*?</form>', page, re.S):
        assert f'name="revision" value="{rev}"' in form
    status, _, page = _post(base + '/research/prepare', {'pid': p['id'], 'symbol': 'VDC', 'revision': rev})
    assert status == 200 and 'Review the public case' in page
    assert f'name="revision" value="{rev}"' in page
    draft = cases.prepare_case(p, 'VDC')
    status, _, result = _post(base + '/research/approve', {'projection': json.dumps(draft['case']), 'reviewed': 'yes', 'revision': rev})
    assert status == 200, result
    cases.validate_bundle(json.loads(result))
    assert cases.load_library(folder) == ([], [])  # approving only returns a file
    status, location, result = _post(base + '/research/import', {'bundle': json.dumps(bundle), 'revision': rev})
    assert status == 303 and location == '/research', result
    page = _get(base + '/research')
    assert bundle['id'] in page and 'Execution unconfirmed' in page
    status, _, _ = _post(base + '/research/import', {'bundle': json.dumps(bundle), 'revision': 'stale'})
    assert status == 400
    assert len(cases.load_library(folder)[0]) == 1


def test_imported_html_is_escaped_in_case_and_pitch(donor):
    from officekit.render_research import case_details, reuse_section
    _, p, b, _ = donor
    b['case']['investigation']['question'] = '</p><script>alert(1)</script>'
    b['id'] = cases.digest({k: v for k, v in b.items() if k != 'id'})
    # Presentation must escape even before validation, for defense in depth.
    assert '<script>alert(1)' not in case_details(b)
    p['research_reuse'] = {'matches': [{'id': b['id'], 'bundle': b, 'differences': []}]}
    html = reuse_section(p)
    assert '&lt;script&gt;' in html and '<script>alert(1)' not in html


def test_invalid_evidence_shape_cannot_bypass_source_fetch(donor):
    _, p, _, _ = donor
    draft = cases.prepare_case(p, 'VDC')
    e = draft['case']['evidence'][0]
    e['data']['url'] = 'https://example.org/different-source'
    e['sha256'] = cases.digest(e['data'])
    with pytest.raises(ValueError, match='disagree'):
        cases.approve(draft, cases.digest(draft['case']))


def test_malformed_edited_projection_is_a_validation_error(donor):
    _, p, _, _ = donor
    draft = cases.prepare_case(p, 'VDC')
    draft['case']['subject']['symbol'] = None
    with pytest.raises(ValueError, match='Malformed contextual research case'):
        cases.approve(draft, cases.digest(draft['case']))


def test_program_court_cannot_be_misrepresented_as_a_security_case(donor):
    _, p, _, _ = donor
    p['candidates'][0]['instrument'] = 'program'
    with pytest.raises(ValueError, match='currently supports security'):
        cases.prepare_case(p, 'VDC')


def test_declared_context_cannot_relabel_known_household_facts(tmp_path):
    _, p = proposal(tmp_path)
    p['research_context']['life_stage'] = 'decumulating'
    with pytest.raises(ValueError, match='saved office facts'):
        cases.proposal_context(p)


def test_paired_baseline_has_same_recipient_context_and_no_implicit_reuse(tmp_path, donor):
    from officekit_research.evaluate import metrics
    _, _, bundle, _ = donor
    results = {}
    for arm, reuse in [('baseline', False), ('reuse', True)]:
        folder = tmp_path / arm
        _, p = proposal(folder, context(life_stage='decumulating', liquidity='ongoing_spending'))
        cases.import_bundle(folder, bundle)
        p, _ = execute(folder, p, reuse=reuse)
        results[arm] = p
    assert results['baseline']['research_reuse']['context'] == results['reuse']['research_reuse']['context']
    assert metrics(results['baseline'])['source_acquisitions'] == 3
    assert metrics(results['reuse'])['source_acquisitions'] == 2
    assert metrics(results['baseline'])['model_calls'] == metrics(results['reuse'])['model_calls'] == 7
    assert metrics(results['baseline'])['cost_usd'] is None


def test_evidence_only_arm_withholds_prior_reasoning_from_every_model_stage(tmp_path, donor):
    _, original, _, _ = donor
    draft = cases.prepare_case(original, 'VDC')
    marker = 'PRIOR_CASE_REASONING_SENTINEL'
    draft['case']['investigation']['thesis'] = marker
    bundle = cases.approve(draft, cases.digest(draft['case']), [{'section': 'fund_profile',
        'basis': 'original_summary', 'valid_until': (cases.day(cases.utcnow()) + timedelta(days=7)).isoformat()}])
    results = {}
    for arm, enabled in [('evidence_only', False), ('contextual', True)]:
        folder = tmp_path / arm
        _, p = proposal(folder, context(life_stage='decumulating', liquidity='ongoing_spending'))
        cases.import_bundle(folder, bundle)
        p, provider = execute(folder, p, contextual_reuse=enabled)
        assert len(provider.calls) == 7
        assert p['evidence']['VDC']['acquisition']['reused'] == ['fund_profile']
        assert p['research_reuse']['mode'] == arm
        assert (marker in json.dumps(provider.calls)) == enabled
        results[arm] = p
    assert results['evidence_only']['evidence']['VDC']['sections']['fund_profile'] == results['contextual']['evidence']['VDC']['sections']['fund_profile']
    assert results['evidence_only']['research_reuse']['context'] == results['contextual']['research_reuse']['context']


def test_reuse_mode_cannot_change_after_a_checkpoint(tmp_path, donor):
    _, _, bundle, _ = donor
    _, p = proposal(tmp_path)
    cases.import_bundle(tmp_path, bundle)
    p, _ = execute(tmp_path, p, contextual_reuse=False)
    provider = Provider()
    with pytest.raises(ValueError, match='cannot change'):
        pipeline.build_proposal(p, tmp_path, lambda *a, **k: None, clients(provider))
    assert not provider.calls


def test_matching_source_outage_is_improved_only_by_fresh_permitted_evidence(tmp_path, donor, monkeypatch):
    import officekit_research
    _, _, bundle, _ = donor
    def unavailable(*args):
        raise ValueError('Issuer temporarily unavailable')
    monkeypatch.setitem(officekit_research.SOURCES, 'fund_profile', unavailable)
    for arm, reuse in [('baseline', False), ('reuse', True)]:
        folder = tmp_path / arm
        _, p = proposal(folder)
        cases.import_bundle(folder, bundle)
        p, _ = execute(folder, p, reuse=reuse)
        pack = p['evidence']['VDC']
        assert ('fund_profile' in pack['sections']) == reuse
        assert bool(pack['errors']) != reuse


def test_prompt_limit_cannot_hide_a_conflicting_source(tmp_path, donor):
    _, p, _, _ = donor
    folder = tmp_path / 'recipient'
    _, q = proposal(folder)
    for i in range(7):
        draft = cases.prepare_case(p, 'VDC')
        draft['case']['investigation']['alternatives'].append('Investigation ' + str(i))
        if i == 6:
            draft['case']['as_of'] = (cases.day(cases.utcnow()) - timedelta(days=1)).isoformat()
            evidence = draft['case']['evidence'][0]
            evidence['data']['text'] = 'Contradictory source snapshot'
            evidence['sha256'] = cases.digest(evidence['data'])
        b = cases.approve(draft, cases.digest(draft['case']), [{'section': 'fund_profile', 'basis': 'original_summary', 'valid_until': (cases.day(cases.utcnow()) + timedelta(days=7)).isoformat()}])
        cases.import_bundle(folder, b)
    found = cases.retrieve(folder, q)
    assert len(found['matches']) == 6 and found['omitted_matches'] == 1
    assert cases.reusable_sections(found, 'VDC') == ({}, ['fund_profile'])


def test_repeated_reviews_are_not_independent_cases(tmp_path, donor):
    _, p, b, _ = donor
    folder = tmp_path / 'recipient'
    _, q = proposal(folder)
    cases.import_bundle(folder, b)
    cases.import_bundle(folder, shared(p))
    found = cases.retrieve(folder, q)
    assert len(found['matches']) == 1 and found['duplicate_reviews'] == 1


@pytest.mark.parametrize('limit', ['count', 'bytes'])
def test_import_limits_preserve_the_readable_existing_library(tmp_path, donor, monkeypatch, limit):
    _, p, b, _ = donor
    cases.import_bundle(tmp_path, b)
    if limit == 'count':
        monkeypatch.setattr(cases, 'MAX_CASES', 1)
    else:
        monkeypatch.setattr(cases, 'MAX_LIBRARY_BYTES', len(cases.canonical(b)) + 1)
    cases.import_bundle(tmp_path, b)
    another = shared(p)
    with pytest.raises(ValueError, match='would exceed'):
        cases.import_bundle(tmp_path, another)
    assert cases.load_library(tmp_path) == ([b], [])


def test_large_case_arguments_are_explicitly_excerpted(donor):
    _, _, b, _ = donor
    b['case']['court']['briefs']['red']['case'] = 'Long argument. ' * 4000
    found = {'matches': [{'id': str(i) * 64, 'context_fit': 'needs_comparison', 'differences': [], 'bundle': b} for i in range(6)]}
    prompt = cases.model_cases(found)
    assert len(cases.canonical(prompt)) < 48000
    assert 'EXCERPT' in json.dumps(prompt)


def test_projection_uses_protocol_frozen_at_call_time(donor, monkeypatch):
    _, p, _, _ = donor
    original = p['research']['run']['protocol_hash']
    monkeypatch.setattr('officekit_ai.provenance.protocol_hash', lambda: 'f' * 64)
    draft = cases.prepare_case(p, 'VDC')
    assert draft['case']['provenance']['protocol_hash'] == original
    assert draft['case']['provenance']['runs']['analyst']['resolved_model'] == 'unknown'


def test_live_evaluator_records_definite_rejection_and_never_auto_retries(tmp_path):
    from officekit_research.evaluate import BudgetClient
    class Rejected(Exception):
        status_code = 400
    class Endpoint:
        def __init__(self):
            self.messages = self
            self.count = 0
        def create(self, **kwargs):
            self.count += 1
            raise Rejected('Provider rejected this request')
    endpoint = Endpoint()
    client = BudgetClient(endpoint, tmp_path / 'calls.json', 1, 6000)
    with pytest.raises(Rejected):
        client.create(model='fixture', system='Evaluation', messages=[], max_tokens=3000)
    assert endpoint.count == 1
    record = json.loads((tmp_path / 'calls.json').read_text())[0]
    assert record['status'] == 'rejected' and record['http_status'] == 400
    assert 'messages' not in record and 'system' not in record
    with pytest.raises(ValueError, match='budget reached'):
        client.create(model='fixture', system='Evaluation', messages=[], max_tokens=3000)
    assert endpoint.count == 1


def test_live_evaluator_will_not_replay_ambiguous_completion(tmp_path):
    from officekit_research.evaluate import BudgetClient
    path = tmp_path / 'calls.json'
    path.write_text('[{"status":"started"}]')
    with pytest.raises(ValueError, match='uncertain completion'):
        BudgetClient(None, path, 20, 6000)
