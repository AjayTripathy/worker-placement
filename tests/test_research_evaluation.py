"""Exercise the live harness with explicit fixtures; never claim model quality."""
import copy
import json
from datetime import timedelta
from types import SimpleNamespace

import pytest

from officekit import strategy_proposals as jobs
from officekit_research import cases, evaluate
from test_officekit_strategy_proposals import Provider


class EvaluationProvider(Provider):
    """Deliberately ungraded canned output, with usage for budget mechanics."""
    def create(self, **kw):
        response = super().create(**kw)
        response.content[0].text = response.content[0].text.replace('VDC', 'SGOV')
        response.model = 'test-opus'
        response.usage = SimpleNamespace(input_tokens=100, output_tokens=100)
        return response


@pytest.fixture
def completed_pilot(tmp_path, monkeypatch):
    provider = EvaluationProvider()
    monkeypatch.setattr(evaluate, 'resolve', lambda slot: ('fixture', {}, 'test-opus'))
    monkeypatch.setattr(evaluate, 'client_for', lambda slot: (provider, 'test-opus'))
    evidence = {'url': 'https://example.org/issuer/SGOV', 'fetched_at': cases.utcnow(),
                'text': 'FICTIONAL TEST SOURCE: short-duration Treasury fund. Not a live research result.', 'truncated': False}
    source = tmp_path / 'source.json'
    source.write_text(json.dumps(evidence))
    root = tmp_path / 'pilot'
    common = ['--out', str(root), '--evidence', str(source)]
    assert evaluate.main(['donor', *common]) == 0
    p = jobs.list_proposals(root / 'donor')[0]
    draft = cases.prepare_case(p, 'SGOV')
    draft['case']['provenance']['kind'] = 'evaluation_scenario'
    bundle = cases.approve(draft, cases.digest(draft['case']), [{'section': 'fund_profile',
        'basis': 'original_summary', 'valid_until': (cases.day(cases.utcnow()) + timedelta(days=7)).isoformat()}])
    bundle_path = tmp_path / 'case.json'
    bundle_path.write_text(json.dumps(bundle))
    pair = ['pair', *common, '--bundle', str(bundle_path)]
    assert evaluate.main(pair) == 0
    return root, source, bundle_path, provider, pair


def test_three_arm_harness_freezes_facts_and_produces_ungraded_review_packet(completed_pilot):
    root, _, _, provider, pair = completed_pilot
    report = json.loads((root / 'pair-report.json').read_text())
    assert report['protocol'] == evaluate.PROTOCOL
    assert set(report['arms']) == {'baseline', 'evidence_only', 'contextual'}
    assert len(provider.calls) == 28  # donor + three fresh recipient reviews, seven calls each
    proposals = {name: jobs.list_proposals(root / name)[0] for name in report['arms']}
    assert len({evaluate.scenario_digest(p) for p in proposals.values()}) == 1
    assert len({json.dumps(p['snapshot']['data'], sort_keys=True) for p in proposals.values()}) == 1
    assert {p['funding']['current_cash'] for p in proposals.values()} == {60000}
    assert {p['funding']['current_budget'] for p in proposals.values()} == {30000}
    assert [report['arms'][k]['source_acquisitions'] for k in ('baseline', 'evidence_only', 'contextual')] == [3, 2, 2]
    assert {row['model_calls'] for row in report['arms'].values()} == {7}  # every arm pays for its own general + suitability passes
    assert all(row['human_audit'] == 'pending' for row in report['arms'].values())
    packet = json.loads((root / 'review-packet.json').read_text())
    key = json.loads((root / 'review-key.json').read_text())
    assert set(packet['reviews']) == set(key) == {'A', 'B', 'C'}
    assert set(key.values()) == set(report['arms'])
    assert all(c['status'] == 'not_assessed' for r in packet['reviews'].values() for c in r['audit'].values())
    assert 'reuse_mode' not in json.dumps(packet)
    # Completion is idempotent; a human's review survives re-running the command.
    packet['reviewer_note'] = 'Independent review has started'
    (root / 'review-packet.json').write_text(json.dumps(packet))
    assert evaluate.main(pair) == 0
    assert len(provider.calls) == 28
    assert json.loads((root / 'review-packet.json').read_text())['reviewer_note'] == packet['reviewer_note']


def test_missing_bundle_is_rejected_before_client_construction(tmp_path, monkeypatch):
    source = tmp_path / 'source.json'
    source.write_text(json.dumps({'url': 'https://example.org/issuer/SGOV', 'fetched_at': cases.utcnow(),
                                  'text': 'Fixture', 'truncated': False}))
    monkeypatch.setattr(evaluate, 'client_for', lambda slot: pytest.fail('No client should be constructed'))
    with pytest.raises(ValueError, match='--bundle is required'):
        evaluate.main(['pair', '--out', str(tmp_path / 'pilot'), '--evidence', str(source)])


def test_changed_frozen_evidence_is_rejected_before_calls(completed_pilot, monkeypatch):
    _, source, _, provider, pair = completed_pilot
    evidence = json.loads(source.read_text())
    evidence['text'] += ' Changed.'
    source.write_text(json.dumps(evidence))
    monkeypatch.setattr(evaluate, 'client_for', lambda slot: pytest.fail('No client should be constructed'))
    with pytest.raises(ValueError, match='exact frozen source'):
        evaluate.main(pair)
    assert len(provider.calls) == 28


def test_changed_recipient_facts_are_rejected_before_calls(completed_pilot, monkeypatch):
    root, _, _, _, pair = completed_pilot
    p = jobs.list_proposals(root / 'evidence_only')[0]
    p['snapshot']['data']['profile']['decumulating'] = False
    # Directly edit the synthetic checkpoint: normal save validates its context.
    path = root / 'evidence_only' / 'strategy_proposals' / (p['id'] + '.json')
    path.write_text(json.dumps(p))
    monkeypatch.setattr(evaluate, 'client_for', lambda slot: pytest.fail('No client should be constructed'))
    with pytest.raises(ValueError, match='facts or instructions changed'):
        evaluate.main(pair)


def test_expired_grant_is_rejected_before_calls(completed_pilot, monkeypatch):
    _, _, bundle_path, _, pair = completed_pilot
    b = json.loads(bundle_path.read_text())
    yesterday = (cases.day(cases.utcnow()) - timedelta(days=1)).isoformat()
    e = b['case']['evidence'][0]
    e['retrieved_at'] = e['data']['fetched_at'] = yesterday
    e['sha256'] = cases.digest(e['data'])
    b = cases.approve({'case': b['case']}, cases.digest(b['case']),
                      [{'section': 'fund_profile', 'basis': 'original_summary', 'valid_until': yesterday}])
    bundle_path.write_text(json.dumps(b))
    monkeypatch.setattr(evaluate, 'client_for', lambda slot: pytest.fail('No client should be constructed'))
    with pytest.raises(ValueError, match='fresh reuse'):
        evaluate.main(pair)


def test_budget_reserves_unknown_usage_and_keeps_unknown_model(tmp_path):
    provider = Provider()
    bounded = evaluate.BudgetClient(provider, tmp_path / 'calls.json', 10, 7000)
    from officekit_ai.strategy_proposal import ANALYST
    kw = {'model': 'fixture', 'max_tokens': 6000, 'system': 'Test', 'messages': [],
          'output_config': {'format': {'type': 'json_schema', 'schema': ANALYST}}}
    bounded.create(**copy.deepcopy(kw))
    with pytest.raises(ValueError, match='budget reached'):
        bounded.create(**copy.deepcopy(kw))
    assert len(provider.calls) == 1
    assert bounded.calls[0]['resolved_model'] == 'unknown'
    assert bounded.calls[0]['output_tokens'] is None
