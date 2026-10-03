"""Private research backfill, lazy content, immutable lineage and calibration."""
import base64
from copy import deepcopy
from datetime import date
import io
import json
from pathlib import Path
import time
import zipfile

import pytest
from fastapi.testclient import TestClient

from test_hosted_migration import Backend, ORIGIN, client, office, upload, send
from hosting.app.main import create_app, SESSION
from hosting.app.offices import Offices
from hosting.app.private_research import PrivateResearch, import_batch
from hosting.app.workspace import materialize
from officekit.migration import canonical, digest, snapshot
from officekit.runtime import hosted_office
from officekit_research import pack_directory as directory
from officekit_research.pack_transfer import SCHEMA, validate
from officekit_research.discovery import catalog, inventory

PDF = b'%PDF-1.4\noriginal fixture PDF\n%%EOF'


def bundle(n=0, prior=None, forecasts=None, outcomes=None):
    deck = '# Court research ' + str(n) + '\n' + 'Original dated evidence. ' * 500
    m = {'id': f'court_x{n}', 'name': f'X{n} court deck', 'bucket': 'idiosyncratic', 'thesis': f'Research X{n}',
         'author': 'source-office', 'agent': 'source-agent', 'model': 'unknown', 'intelligence_level': 'unrated',
         'as_of': '2026-09-21', 'positions': [f'X{n}'], 'deck': 'DECK.md', 'deck_sha256': digest(deck.encode()),
         'sources': [], 'gaps': ['Structured source references not recorded'],
         'attachment': {'sha256': digest(PDF), 'size': len(PDF), 'name': 'DECK.pdf'},
         'private_court': {'revision': 1, 'supersedes': None, 'source_digest': digest(str(n).encode()),
                           'source_deck': f'X{n}_PITCH_DECK_20260921.md', 'ruling': 'ADJUDICATED — WATCH',
                           'reopen_gates': ['Next filing'], 'conviction': 6, 'court': 'historical court',
                           'ledger_state': 'WATCH', 'sleeve': 'test', 'provenance': {'status': 'unrecorded'}}}
    if prior:
        m['private_court'].update(revision=prior['manifest']['private_court']['revision'] + 1,
                                  supersedes=prior['id'], ruling='ADJUDICATED — DECLINE')
    if forecasts: m['forecasts'] = forecasts
    if outcomes: m['outcomes'] = outcomes
    body = {'schema': SCHEMA, 'manifest': m, 'deck': deck}
    return validate({'id': digest(canonical(body)), **body})


def activate(client, office):
    _, sid = upload(client, office)
    return send(client, '/api/migrations/' + sid + '/activate', {}).json()


def ingest(service, receipt, bundles):
    return import_batch(service, 'alice', receipt['office_id'], bundles,
                        {digest(PDF): base64.b64encode(PDF).decode()}, receipt.get('revision', receipt.get('digest')))


def test_344_decks_use_directory_only_until_opened(client, office, monkeypatch, tmp_path):
    receipt = activate(client, office)
    service = Offices(client.store)
    _, original = service.read('alice', receipt['office_id'])
    values = [bundle(n) for n in range(344)]
    current = receipt
    for start in range(0, len(values), 25):
        current = ingest(service, current, values[start:start + 25])
    saved, record = service.read('alice', receipt['office_id'])
    for name, data in original['documents'].items():
        assert record['documents'][name] == data
    assert len(record['documents']) == len(original['documents']) + 1
    assert len(json.loads(base64.b64decode(record['documents']['research/pack_directory.json']))) == 344
    assert len(base64.b64decode(record['documents']['research/pack_directory.json'])) < 400000
    gets = []
    original_get = client.store.get
    def tracked(key):
        if '/research-content/' in key: gets.append(key)
        return original_get(key)
    monkeypatch.setattr(client.store, 'get', tracked)
    with TestClient(create_app(Backend(), ORIGIN, store=client.store), base_url=ORIGIN) as restarted:
        restarted.cookies.set(SESSION, 'alice')
        page = restarted.get(receipt['path'] + '/pages/research_catalog.html')
        assert page.status_code == 200 and 'X343 court deck' in page.text and 'X0 court deck' in page.text
        assert gets == []
        strategies = restarted.get(receipt['path'] + '/pages/strategies.html')
        assert strategies.status_code == 200 and 'X343 court deck' in strategies.text
        assert gets == []
        folder = tmp_path / 'materialized'; folder.mkdir()
        materialize(folder, record)
        from officekit.serve import _thesis_sleeves
        assert len([p for p in _thesis_sleeves({}, folder) if p['sid'].startswith('court_x')]) == 344
        assert gets == []
        href = next(e['href'] for e in catalog(folder, {})['entries'] if e['id'] == 'court_x343')
        full = restarted.get(receipt['path'] + href)
        assert full.status_code == 200 and values[-1]['deck'].splitlines()[0][2:] in full.text
        assert len(gets) == 1 and gets[0].endswith(values[-1]['id'])
        assert 'Download original PDF' in full.text and 'unrecorded' in full.text
        pdf = restarted.get(receipt['path'] + '/research/files/' + digest(PDF))
        assert pdf.content == PDF and 'attachment;' in pdf.headers['content-disposition']
        restarted.cookies.set(SESSION, 'bob')
        assert restarted.get(receipt['path'] + href).status_code == 404
        assert restarted.get(receipt['path'] + '/research/files/' + digest(PDF)).status_code == 404
    gets.clear()
    proposal = {'snapshot': {'answers': {}}, 'strategy_id': 'custom',
                'brief': {'candidates': ['X343'], 'title': 'X343', 'thesis': 'Research X343'}}
    with hosted_office(folder, private_research=PrivateResearch(service, 'alice', receipt['office_id'])):
        found = inventory(folder, proposal)
    assert found['entries'][0]['id'] == 'court_x343'
    assert found['entries'][0]['research_notes'] == values[-1]['deck'][:6000]
    assert 1 <= len(gets) <= 4
    assert len(gets) < found['available']


def test_metadata_revisions_old_links_resume_and_export(client, office, tmp_path):
    receipt = activate(client, office); service = Offices(client.store)
    first = bundle(); one = ingest(service, receipt, [first])
    second = bundle(prior=first); two = ingest(service, one, [second])
    # Reupload an old version: must not change latest or create another revision.
    repeated = ingest(service, two, [first, second])
    assert repeated['revision'] == two['revision']
    client.cookies.set(SESSION, 'alice')
    first_page = client.get(one['packs'][0]['href']).text
    second_page = client.get(two['packs'][0]['href']).text
    assert 'ADJUDICATED — WATCH' in first_page and 'ADJUDICATED — DECLINE' in second_page
    cat = client.get(receipt['path'] + '/pages/research_catalog.html').text
    assert one['packs'][0]['href'] not in cat and two['packs'][0]['href'] in cat
    exported = client.get(receipt['path'] + '/export')
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        assert archive.read('.research-content/' + digest(PDF) + '.pdf') == PDF
        archive.extractall(tmp_path / 'restored')
    assert directory.bundle(tmp_path / 'restored', first['id']) == first
    assert directory.bundle(tmp_path / 'restored', second['id']) == second
    assert not any('research-content' in f['path'] for f in snapshot(tmp_path / 'restored')[0]['files'])


def test_atomic_batch_owner_revision_lease_and_digest_guards(client, office):
    receipt = activate(client, office); service = Offices(client.store)
    path = '/api/offices/' + receipt['office_id'] + '/research/batch'
    b = bundle(); payload = {'revision': receipt['digest'], 'bundles': [b], 'files': {digest(PDF): base64.b64encode(PDF).decode()}}
    assert send(client, path, payload, 'bob').status_code == 404
    assert client.post(path, json=payload).status_code == 401
    invalid = deepcopy(payload); invalid['bundles'].append(bundle(1)); invalid['bundles'][1]['deck'] += 'tampered'
    assert send(client, path, invalid).status_code == 400
    assert service.read('alice', receipt['office_id'])[0]['digest'] == receipt['digest']
    invalid = deepcopy(payload); invalid['files'][digest(PDF)] = base64.b64encode(b'%PDF-wrong').decode()
    assert send(client, path, invalid).status_code == 400
    response = send(client, path, payload)
    assert response.status_code == 200, response.text
    assert send(client, path, payload).status_code == 409
    key = service.prefix('alice', receipt['office_id']) + 'active'
    active, generation = service.db().get(key)
    service.db().put(key, {**active, 'job': {'id': 'active', 'expires': time.time()+300}}, generation)
    assert send(client, path, {**payload, 'revision': response.json()['revision']}).status_code == 409


def prediction():
    body = dict(schema=1, recorded_at='2026-08-01T12:00:00+00:00', symbol='X0', statement='Event occurs',
                resolution_criteria='Official release says the event occurred by September 1', resolve_by='2026-09-01',
                probability=0.8, base_rate=0.5, submitter='original submitter', agent='forecast agent',
                model='recorded-model-version', protocol='protocol-v1', strategy='source-strategy', event_key='X0:event:2026')
    return {'id': digest(canonical(body)), **body}


def test_original_forecast_attribution_brier_and_known_time(client, office, tmp_path):
    from officekit_research import index
    receipt = activate(client, office); service = Offices(client.store)
    pred = prediction()
    outcome = dict(forecast_id=pred['id'] + ':0', outcome=True, source_url='https://example.com/release',
                   resolved_at='2026-09-01T12:00:00+00:00', note='Public result')
    b = bundle(forecasts=[pred], outcomes=[outcome])
    result = ingest(service, receipt, [b]); assert ingest(service, result, [b])['revision'] == result['revision']
    _, record = service.read('alice', receipt['office_id'])
    folder = tmp_path / 'restored'; folder.mkdir(); materialize(folder, record)
    rows = index.forecast_rows(folder)
    assert len(rows) == 1 and rows[0]['contributor'] == 'original submitter'
    assert rows[0]['agent'].startswith('forecast agent / recorded-model-version')
    assert rows[0]['attribution'] == 'claimed_import'
    score = index.scoreboard(folder, 'submitter')[0]
    assert score['brier'] == 0.04 and score['resolved'] == 1 and score['skill_vs_base_rate'] is None
    assert index.scoreboard(folder, 'agent')[0]['brier'] == 0.04
    # Outcome was imported now, not known to the receiving office in September.
    assert index.scoreboard(folder, 'submitter', today=date(2026, 9, 2))[0]['resolved'] == 0
    client.cookies.set(SESSION, 'alice')
    assert 'original submitter' in client.get(receipt['path'] + '/research/scorecard').text
    assert '0.04' in client.get(receipt['path'] + '/research/scorecard').text


def test_local_upload_resumes_after_partial_failure(client, office, tmp_path, monkeypatch):
    from officekit import cloud
    receipt = activate(client, office)
    local = tmp_path / 'sender'; local.mkdir()
    for n in range(30): directory.cache(local, bundle(n), PDF)
    monkeypatch.setattr(cloud, 'credentials', lambda: {'origin': ORIGIN, 'token': 'alice'})
    calls = []
    def request(origin, path, payload=None, token=None):
        if path.endswith('/batch'):
            calls.append(payload)
            if len(calls) == 2: raise ValueError('simulated disconnection')
        response = client.get(path, headers={'Authorization': 'Bearer alice'}) if payload is None else send(client, path, payload)
        if not response.is_success: raise ValueError(response.text)
        return response.json()
    monkeypatch.setattr(cloud, 'request', request)
    with pytest.raises(ValueError, match='disconnection'): directory.upload(local, receipt['office_id'])
    result = directory.upload(local, receipt['office_id'])
    assert result['uploaded'] == 5 and result['retained_versions'] == 30
    assert directory.upload(local, receipt['office_id'])['uploaded'] == 0


def test_duplicate_forecasts_and_conflicting_resolutions_are_rejected():
    p = prediction()
    with pytest.raises(ValueError, match='Duplicate forecasts'):
        bundle(forecasts=[p, p])
    r = dict(forecast_id=p['id'] + ':0', outcome=True, source_url='https://example.com/release',
             resolved_at='2026-09-01T12:00:00+00:00', note='Result')
    with pytest.raises(ValueError, match='only once'):
        bundle(forecasts=[p], outcomes=[r, {**r, 'outcome': False}])
