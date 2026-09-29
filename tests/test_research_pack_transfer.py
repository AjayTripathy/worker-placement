"""Local research survives upload, process replacement, discovery and retry."""
import base64
from copy import deepcopy
import json
import time

import pytest
from fastapi.testclient import TestClient

from officekit.migration import canonical, digest
from officekit_research.pack_transfer import export, install, validate, roots
from officekit_research.discovery import catalog, inventory, refresh_proposal_inventory
from officekit import strategy_proposals as proposals, build_model
from officekit.personal_context import empty
from test_hosted_migration import Backend, ORIGIN, client, office, upload, send


@pytest.fixture
def pack(tmp_path):
    p = tmp_path / 'local_hedge'; p.mkdir()
    m = {'id': p.name, 'name': 'Local downside research', 'bucket': 'defensive',
         'thesis': 'Compare puts and spreads; a spread caps the hedge payout.',
         'author': 'Local submitter', 'agent': 'researcher', 'model': 'unknown', 'intelligence_level': 'unrated',
         'as_of': '2026-09-21', 'positions': ['SPY', 'VDC'], 'gaps': ['Current option quotes'],
         'sources': [{'title': 'Primary source', 'url': 'https://www.cboe.com/options', 'retrieved_at': '2026-09-21'}]}
    (p / 'pack.json').write_text(json.dumps(m))
    (p / 'DECK.md').write_text('# Original research\nA spread caps protection. <script>alert(1)</script>')
    return p


def test_immutable_idempotent_deck_lineage_and_discovery(pack, tmp_path):
    from officekit.render_saved_research import page
    folder = tmp_path / 'recipient'; folder.mkdir()
    b = export(pack)
    first = install(folder, b)
    assert install(folder, b) == first and len(roots(folder)) == 1
    entry = next(e for e in catalog(folder, {})['entries'] if e['id'] == 'local_hedge')
    assert entry['author'] == 'Local submitter' and entry['agent'] == 'researcher'
    assert entry['href'] == first['href'] and entry['model'] == 'unknown'
    html = page(folder, {}, first['href'].removeprefix('/pages/research_').removesuffix('.html'))
    assert '&lt;script&gt;' in html and '<script>alert(1)</script>' not in html
    (pack / 'DECK.md').write_text('New version; preserve old citations.')
    second = install(folder, export(pack))
    assert second['href'] != first['href'] and len(roots(folder)) == 2
    assert 'Original research' in page(folder, {}, first['href'].split('research_')[1][:-5])
    assert not (folder / 'adjudications.jsonl').exists()
    original_deck = roots(folder)[0] / 'local_hedge' / 'DECK.md'
    original_deck.write_text('Changed outside the import path')
    found = catalog(folder, {})
    assert found['warnings'] and len([e for e in found['entries'] if e['id'] == 'local_hedge']) == 1


@pytest.mark.parametrize('mutation', ['digest', 'path', 'secret', 'source', 'future', 'oversize'])
def test_invalid_import_is_rejected_without_writes(pack, tmp_path, mutation):
    b = export(pack)
    if mutation == 'digest': b['deck'] += 'tampered'
    if mutation == 'path': b['manifest']['id'] = '../escape'
    if mutation == 'secret': b['deck'] += ' sk-' + 'a'*30
    if mutation == 'source': b['manifest']['sources'][0]['url'] = 'file:///private/data'
    if mutation == 'future': b['manifest']['as_of'] = '2999-01-01'
    if mutation == 'oversize': b['deck'] = 'x' * 524289
    if mutation != 'digest':
        b['manifest']['deck_sha256'] = digest(b['deck'].encode())
        b['id'] = digest(canonical({k: v for k, v in b.items() if k != 'id'}))
    folder = tmp_path / 'recipient'
    with pytest.raises(ValueError): install(folder, b)
    assert not folder.exists()


def test_symlink_import_rejected(pack, tmp_path):
    folder = tmp_path / 'recipient'; folder.mkdir()
    outside = tmp_path / 'outside'; outside.mkdir()
    (folder / 'research').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='symlinks'): install(folder, export(pack))
    assert list(outside.iterdir()) == []


def test_source_links_are_clickable_but_active_content_is_not():
    from officekit.render_deck import render_markdown_deck
    html = render_markdown_deck('Research', '[Source](https://www.cboe.com/options) [Bad](javascript:alert) <img src=x onerror=alert(1)>')
    assert 'href="https://www.cboe.com/options"' in html
    assert 'href="javascript:' not in html and '<img ' not in html


def test_export_command_produces_the_same_verified_bundle(pack, tmp_path):
    from officekit.cli import main
    output = tmp_path / 'research.json'
    assert main(['research-export', '--pack', str(pack), '--output', str(output)]) == 0
    assert json.loads(output.read_text()) == export(pack)


def test_retry_rediscovers_new_research_and_keeps_completed_synthesis(pack, tmp_path, monkeypatch):
    from test_officekit_strategy_proposals import seed, Provider, execute, fake_sources
    fake_sources(monkeypatch)
    _, p = seed(tmp_path)
    p['research_inventory'] = inventory(tmp_path, p)
    proposals.save(tmp_path, p)
    bundle = export(pack); install(tmp_path, bundle)
    provider = Provider(fail_pitch=True)
    saved = execute(tmp_path, p, provider)
    assert saved['status'] == 'error' and saved['research']
    entry = next(e for e in saved['research_inventory']['entries'] if e['id'] == 'local_hedge')
    assert 'A spread caps protection.' in entry['research_notes']
    assert entry['sources'] and entry['agent'] == 'researcher'
    assert 'A spread caps protection.' in provider.calls[0]['messages'][0]['content']
    assert entry['href'] in saved['research_attachments'][0]['references']
    previous = deepcopy(saved['research_inventory'])
    with pytest.raises(ValueError, match='completed research'): refresh_proposal_inventory(tmp_path, saved)
    provider.fail_pitch = False
    resumed = execute(tmp_path, saved, provider)
    assert len(provider.calls) == 8 and resumed['research_inventory'] == previous


def test_hosted_upload_preserves_other_documents_and_survives_restart(client, office, pack):
    from hosting.app.main import create_app, SESSION
    from hosting.app.offices import Offices
    a = json.loads((office / 'answers.json').read_text())
    (office / 'personal_context.json').write_text(json.dumps(empty(a['office_id'])))
    p = proposals.create(office, a, build_model(json.loads((office / 'balance_sheet.json').read_text())),
                         'index_hedge', 'scenario', 'crash/put_index', option='put_index')
    p['status'] = 'error'; proposals.save(office, p)
    _, sid = upload(client, office)
    receipt = send(client, '/api/migrations/' + sid + '/activate', {}).json()
    service = Offices(client.store)
    _, before = service.read('alice', receipt['office_id'])
    path = '/api/offices/' + receipt['office_id'] + '/research/packs'
    body = {'bundle': export(pack), 'revision': receipt['digest'], 'proposal_id': p['id']}
    assert send(client, path, body, 'bob').status_code == 404
    assert client.post(path, json=body).status_code == 401
    bad = {**body, 'proposal_id': 'bad'}
    assert send(client, path, bad).status_code == 400
    assert service.read('alice', receipt['office_id'])[1] == before
    response = send(client, path, body)
    assert response.status_code == 200, response.text
    result = response.json()
    current, after = service.read('alice', receipt['office_id'])
    for name, raw in before['documents'].items():
        if not name.startswith('strategy_proposals/'):
            assert after['documents'][name] == raw, name
    saved = json.loads(base64.b64decode(after['documents']['strategy_proposals/' + p['id'] + '.json']))
    assert not saved['research'] and saved['status'] == 'error'
    assert any(e['id'] == 'local_hedge' for e in saved['research_inventory']['entries'])
    assert send(client, path, body).status_code == 409
    repeated = send(client, path, {**body, 'revision': current['digest']})
    assert repeated.status_code == 200 and repeated.json()['revision'] == current['digest']
    with TestClient(create_app(Backend(), ORIGIN, store=client.store), base_url=ORIGIN) as restarted:
        restarted.cookies.set(SESSION, 'alice')
        assert 'Local downside research' in restarted.get(receipt['path'] + '/pages/research_catalog.html').text
        assert 'Original research' in restarted.get(result['href']).text
        proposal_page = restarted.get(result['proposal_href'])
        assert result['href'] in proposal_page.text and 'ready for candidate selection' in proposal_page.text
        restarted.cookies.set(SESSION, 'bob')
        assert restarted.get(result['href']).status_code == 404
    key = service.prefix('alice', receipt['office_id']) + 'active'
    active, generation = service.db().get(key)
    service.db().put(key, {**active, 'job': {'id': 'active', 'expires': time.time() + 300}}, generation)
    assert send(client, path, {**body, 'revision': current['digest']}).status_code == 409


def test_browser_import_uses_shared_revision_gated_handler(client, office, pack):
    from hosting.app.main import SESSION, CSRF
    from officekit.commitments import revision
    _, sid = upload(client, office)
    receipt = send(client, '/api/migrations/' + sid + '/activate', {}).json()
    client.cookies.set(SESSION, 'alice')
    page = client.get(receipt['path'] + '/research')
    assert 'Import local research' in page.text
    fields = {'_csrf': client.cookies.get(CSRF), '_office_revision': receipt['digest'],
              'revision': revision(json.loads((office / 'answers.json').read_text()))}
    response = client.post(receipt['path'] + '/research/import-pack', data=fields,
                           files={'bundle_file': ('research.json', canonical(export(pack)), 'application/json')},
                           headers={'Origin': ORIGIN}, follow_redirects=False)
    assert response.status_code == 303, response.text
    assert 'Local downside research' in client.get(response.headers['location']).text
