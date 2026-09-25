"""Regression coverage for the strategy and HTTP failure-layer review."""
import copy
import json
import logging
import urllib.error
import urllib.request
from types import SimpleNamespace

import pytest

from officekit import api_errors, mandates, strategy_proposals as jobs
from officekit.commitments import revision
from officekit.personal_context import empty
from test_officekit_onboarding_e2e import server, _post, _get
from test_officekit_strategy_proposals import seed


@pytest.mark.parametrize('target', [float('nan'), float('inf'), float('-inf'), 0, -1, 100.01, 150, True, False, 'bad', '1e999'])
def test_invalid_target_rejected_before_any_writer_mutates(tmp_path, target):
    from officekit import build_model, build_from_answers
    from officekit_ai import propose_strategy
    answers = {'owner': 'Validation test', 'sleeves': [{'category': 'cash', 'value': 1000}]}
    model = build_model(build_from_answers(answers))
    before = copy.deepcopy(answers)
    writers = [
        lambda: mandates.queue_agent_proposal(answers, 'Defensive', 'call-1', target_pct=target),
        lambda: mandates.create_adhoc(answers, 'Defensive', target_pct=target),
        lambda: jobs.create(tmp_path, answers, model, 'defensive', 'principal', 'test', target_pct=target),
        lambda: propose_strategy(answers, tmp_path/'learning.jsonl', 'Defensive', 'Test', empty(), target_pct=target),
    ]
    for writer in writers:
        with pytest.raises(ValueError, match='above zero and at most 100%'):
            writer()
        assert answers == before
        assert not (tmp_path/'learning.jsonl').exists()
        assert not list((tmp_path/'strategy_proposals').glob('*.json'))
    json.dumps(answers, allow_nan=False)


@pytest.mark.parametrize('target, expected', [(None, None), ('0.01', .01), (100, 100.)])
def test_valid_target_normalized_for_each_mandate_writer(target, expected):
    for writer in (lambda a: mandates.queue_agent_proposal(a, 'Defensive', 'call', target_pct=target),
                   lambda a: mandates.create_adhoc(a, 'Defensive', target_pct=target)):
        answers = {}
        sid = writer(answers)
        assert answers['strategy_decisions'][sid].get('target_pct') == expected
        json.dumps(answers, allow_nan=False)


def _office(folder):
    from officekit.serve import build_office
    answers, proposal = seed(folder)
    build_office(answers, folder)
    return json.loads((folder/'answers.json').read_text()), proposal


def test_unexpected_error_generic_500_with_full_traceback(server, monkeypatch, caplog):
    base, folder = server
    monkeypatch.setattr('officekit.serve._ai', lambda *a, **kw: True)
    def fail(*args, **kwargs):
        raise FileNotFoundError('/Users/private/office/answers.json')
    monkeypatch.setattr('officekit_ai.intake_chat.turn', fail)
    with caplog.at_level(logging.ERROR):
        code, _, body = _post(base+'/chat', {'messages': []}, json_body=True)
    assert code == 500 and json.loads(body)['error'] == api_errors.UNEXPECTED
    assert '/Users/' not in body + json.dumps(api_errors.active(folder))
    assert any(r.exc_info and r.exc_info[2] for r in caplog.records)
    assert '/Users/private/office/answers.json' in caplog.text


def test_streamed_credit_failure_returns_actionable_http_notice(server, monkeypatch):
    import httpx
    import openai
    base, folder = server
    monkeypatch.setattr('officekit.serve._ai', lambda *a, **kw: True)
    def fail(*args, **kwargs):
        raise openai.APIError('Provider rejected the request',
                              request=httpx.Request('POST', 'https://api.openai.com/v1/responses'),
                              body={'code': 'credit_balance_exhausted'})
    monkeypatch.setattr('officekit_ai.intake_chat.turn', fail)
    code, _, body = _post(base+'/chat', {'messages': []}, json_body=True)
    assert code == 502 and json.loads(body)['error'] == api_errors.CREDIT_EXHAUSTED
    assert api_errors.active(folder)[0]['message'] == api_errors.CREDIT_EXHAUSTED


def test_validation_error_400_redacts_paths_and_does_not_log_traceback(server, monkeypatch, caplog):
    base, folder = server
    def fail(*args, **kwargs):
        raise ValueError('Review invalid row in /Users/private/office/answers.json')
    monkeypatch.setattr('officekit.serve.answers_from_form', fail)
    code, _, body = _post(base+'/onboard', {})
    assert code == 400 and 'Review invalid row' in body and '/Users/' not in body
    assert len(api_errors.active(folder)) == 1
    assert not any(r.exc_info for r in caplog.records)
    assert not (folder/'.flash.json').exists()


@pytest.mark.parametrize('route', ['/draft', '/chat', '/onboard/confirm'])
def test_malformed_client_json_is_validation_error(server, route):
    base, _ = server
    if route == '/onboard/confirm':
        code, _, _ = _post(base+route, {'answers_json': '{'})
    else:
        from local_http import headers
        request = urllib.request.Request(base+route, data=b'{', headers={'Content-Type': 'application/json', **headers(base)})
        with pytest.raises(urllib.error.HTTPError) as response:
            urllib.request.urlopen(request)
        code = response.value.code
    assert code == 400


def test_send_failure_has_guarded_generic_fallback(server, monkeypatch, caplog):
    base, _ = server
    def fail(body):
        raise RuntimeError('renderer failed at /Users/private/template.html')
    monkeypatch.setattr(api_errors, 'inject', fail)
    request = urllib.request.Request(base+'/start', headers={'Accept': 'text/html'})
    with pytest.raises(urllib.error.HTTPError) as response:
        urllib.request.urlopen(request)
    assert response.value.code == 500
    body = response.value.read().decode()
    assert 'Something went wrong' in body and '/Users/' not in body
    assert any(r.exc_info for r in caplog.records)


def test_signal_failure_before_record_is_not_success(server, monkeypatch, caplog):
    base, folder = server
    _office(folder)
    code, _, body = _post(base+'/signals/run', {'name': 'does_not_exist'})
    assert code == 500 and 'Something went wrong' in body
    assert api_errors.active(folder)[0]['context'] == 'signal:does_not_exist:'
    assert any(r.exc_info for r in caplog.records)


def test_adapter_failure_deduplicates_and_sanitizes_public_state(server, monkeypatch, caplog):
    from officekit import staging
    base, folder = server
    def fail(*a, **kw):
        raise OSError('/Users/private/broker.csv could not be read')
    monkeypatch.setattr('officekit_adapters.fetch_snapshot', fail)
    code, _, body = _post(base+'/adapter/import', {'adapter': 'ibkr_socket'})
    assert code == 500 and '/Users/' not in body
    events = api_errors.active(folder)
    assert len(events) == 1 and events[0]['context'] == 'import:adapter:ibkr_socket'
    assert staging.load(folder)['sources']['adapter:ibkr_socket']['last_error'] == api_errors.UNEXPECTED
    assert '/Users/private/' in caplog.text
    assert not (folder/'.flash.json').exists()


def test_partial_upload_keeps_good_rows_and_returns_error(server, monkeypatch):
    from officekit import staging
    from officekit.formdata import FilePart, Form
    base, folder = server
    def extract(name, data, **kw):
        if name == 'bad.pdf':
            raise RuntimeError('credit balance too low')
        return {'rows': [{'symbol': 'VTI', 'value': 1000}], 'account_label': 'Test'}
    monkeypatch.setattr('officekit_ai.extract.extract_file', extract)
    # Exercise the real per-file router through HTTP; multipart parsing is covered separately.
    monkeypatch.setattr('officekit.formdata.parse', lambda *a: Form({'docs': [
        FilePart('good.pdf', b'good'), FilePart('bad.pdf', b'bad')]}))
    code, _, body = _post(base+'/import/files', {})
    assert code == 502 and 'insufficient API credit' in body
    sources = staging.load(folder)['sources']
    assert sources['upload:good.pdf']['rows'][0]['value'] == 1000
    assert 'insufficient API credit' in sources['upload:bad.pdf']['last_error']
    assert sources['upload:bad.pdf']['kind'] == 'upload'
    assert sources['upload:bad.pdf']['refresh'] == 'manual'
    assert len(api_errors.active(folder)) == 1
    assert not (folder/'.flash.json').exists()


def test_every_strategy_mutation_rejects_stale_and_missing_revision(server, monkeypatch):
    from officekit.strategy_routes import PATHS
    base, folder = server
    answers, p = _office(folder)
    before = (folder/'answers.json').read_bytes()
    proposals_before = {f.name: f.read_bytes() for f in (folder/'strategy_proposals').glob('*.json')}
    calls = []
    monkeypatch.setattr(jobs, 'dispatch', lambda *a: calls.append(a))
    for route in sorted(PATHS | {'/strategy/goal-unadopt'}):
        for expected in ('', 'stale'):
            code, _, body = _post(base+route, {'title': 'Test', 'pid': p['id'], 'action': 'decline', 'revision': expected})
            assert code == 400 and 'Reload and review' in body, (route, body)
            assert (folder/'answers.json').read_bytes() == before
            assert {f.name: f.read_bytes() for f in (folder/'strategy_proposals').glob('*.json')} == proposals_before
    assert not calls


@pytest.mark.parametrize('status', ['considering', 'planned', 'implemented'])
def test_decline_http_revision_gate_and_replay(server, status):
    from officekit.serve import build_office
    base, folder = server
    answers, p = _office(folder)
    answers['strategy_decisions'][p['strategy_id']]['status'] = status
    build_office(answers, folder)
    expected = revision(json.loads((folder/'answers.json').read_text()))
    p.update(status='needs_review', stage='Awaiting decision')
    jobs.save(folder, p)
    payload = {'pid': p['id'], 'action': 'decline', 'revision': expected}
    code, _, body = _post(base+'/strategy/proposal/decide', payload)
    assert code == 303, body
    saved = json.loads((folder/'answers.json').read_text())
    assert saved['strategy_decisions'][p['strategy_id']]['status'] == ('declined' if status == 'considering' else status)
    assert jobs.load(folder, p['id'])['status'] == 'declined'
    before = (folder/'answers.json').read_bytes()
    assert _post(base+'/strategy/proposal/decide', payload)[0] == 303
    assert (folder/'answers.json').read_bytes() == before


def test_forms_use_rendered_revision_and_proposal_reload_uses_current_answers(server):
    from officekit.serve import build_office
    base, folder = server
    answers, p = _office(folder)
    expected = revision(answers)
    for name in ['strategies', 'scenarios']:
        html = _get(base+'/pages/'+name+'.html')
        import re
        forms = re.findall(r'<form\b[^>]*action="/strategy/[^>]+>.*?</form>', html, flags=re.S)
        assert forms and all('name="revision" value="'+expected+'"' in form for form in forms)
    answers['owner'] = 'Changed owner'
    build_office(answers, folder)
    current = revision(json.loads((folder/'answers.json').read_text()))
    html = _get(base+f'/pages/proposal_{p["id"]}.html')
    assert current != p['snapshot_revision']
    assert 'name="revision" value="'+current+'"' in html
    assert jobs.load(folder, p['id'])['snapshot_revision'] == p['snapshot_revision']


def test_full_queue_records_recoverable_failure_without_dispatch(tmp_path, monkeypatch):
    _, p = seed(tmp_path)
    monkeypatch.setattr(jobs, '_QUEUED', {('other', str(i)) for i in range(16)})
    submitted = []
    monkeypatch.setattr(jobs, '_EXECUTOR', SimpleNamespace(submit=lambda *a: submitted.append(a)))
    jobs.dispatch(tmp_path, p['id'])
    stored = jobs.load(tmp_path, p['id'])
    assert stored['status'] == 'error' and stored['stage'] == 'Queue full'
    assert not submitted
    assert api_errors.active(tmp_path)[0]['context'] == 'proposal:'+p['id']


def test_nonfinite_answers_never_replace_existing_financial_files(tmp_path):
    from officekit.serve import build_office
    answers, _ = _office(tmp_path)
    before = {n: (tmp_path/n).read_bytes() for n in ['answers.json', 'balance_sheet.json']}
    answers['strategy_decisions']['unused'] = {'target_pct': float('inf')}
    with pytest.raises(ValueError):
        build_office(answers, tmp_path)
    assert {n: (tmp_path/n).read_bytes() for n in before} == before
