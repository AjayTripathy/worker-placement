"""Home -> saved research -> court -> funded ticker plan, across transports."""
import base64
from html.parser import HTMLParser
import json
import re

import pytest
from fastapi.testclient import TestClient

from officekit import build_from_answers, build_model, strategy_proposals as proposals
from officekit.commitments import revision
from officekit.deployment import funding
from officekit.personal_context import empty
from officekit.serve import build_office
from officekit_ai import strategy_proposal as pipeline
from test_officekit_onboarding_e2e import server, _get, _post
from test_officekit_strategy_proposals import Provider, clients, fake_sources
from test_hosted_migration import Backend, MemoryStore, ORIGIN, office, upload, send


class Form(HTMLParser):
    def __init__(self, html, suffix='/strategy/deploy'):
        super().__init__()
        self.action, self.fields, self.inside, self.suffix = None, {}, False, suffix
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            self.inside = a.get('action', '').endswith(self.suffix)
            if self.inside:
                self.action = a['action']
        if self.inside and tag == 'input' and a.get('name'):
            self.fields[a['name']] = a.get('value', '')

    def handle_endtag(self, tag):
        if tag == 'form':
            self.inside = False


def answers():
    return {'owner': 'Deployment test', 'as_of': '2026-09-21', 'profile': {'net_buyer': True},
            'sleeves': [{'category': 'cash', 'name': 'Bank cash', 'value': 100000}],
            'commitments': [{'id': 'implicit:spending:lifestyle', 'annual_amount': 0}],
            'incoming': {'amount': 5000000, 'rate': .30, 'character': 'ltcg'},
            'desk_theses': [{'sid': 'saved_staples', 'label': 'Saved staples', 'value': 0, 'n': 1, 'edge': '', 'next_date': '',
                            'thesis': 'Previously investigated staples; confirm concentration.',
                            'court_date': '2026-09-14', 'verdict': 'WATCH', 'positions': [{'symbol': 'VDC', 'mv': 0}]}]}


def deployment_link(html):
    return re.search(r'href="([^"]*/pages/deployment_[a-f0-9]+\.html)"', html)[1]


def test_deployment_reserves_tax_and_cash_shortfall():
    a = answers()
    a['commitments'].append({'id': 'dated-payment', 'source': 'goal_reservation', 'label': 'Payment',
                            'amount': 400000, 'cadence': 'once', 'next_due': '2026-09-30', 'funding_source': 'portfolio'})
    f = funding(build_model(build_from_answers(a)))
    assert f['pending_gross'] == 5000000 and f['pending_tax'] == 1500000
    assert f['current_budget'] == 0 and f['commitment_reserve'] == 300000
    assert f['contingent_budget'] == 3200000
    assert f['pending_gross'] == f['pending_tax'] + f['commitment_reserve'] + f['contingent_budget']
    a['commitments'][-1]['amount'] = 6000000
    assert funding(build_model(build_from_answers(a)))['contingent_budget'] == 0


def test_explicit_target_still_caps_incoming_capital():
    from officekit.strategy_playbooks import brief
    p = {'strategy_id': 'deploy_powder', 'brief': brief('deploy_powder'), 'target_pct': 1,
         'snapshot': {'data': build_from_answers(answers())}}
    result = pipeline.budget(p)
    assert result['current_budget'] == 0
    assert result['contingent_budget'] == round(build_model(p['snapshot']['data'])['NW'] * .01, 2)


def test_home_form_runs_research_and_shows_saved_tickers(server, monkeypatch):
    base, folder = server
    fake_sources(monkeypatch)
    build_office(answers(), folder)
    provider = Provider()
    monkeypatch.setattr(proposals, 'dispatch', lambda directory, pid: proposals.run(directory, pid,
        lambda p, f, save: pipeline.build_proposal(p, f, save, clients(provider))))
    home = _get(base + '/pages/office.html')
    destination = deployment_link(home)
    assert 'href="#deploy-plan"' not in home
    form = Form(_get(base + destination))
    assert form.action and form.fields['revision']
    assert form.fields['inflow_id']
    status, location, body = _post(base + form.action, form.fields)
    assert status == 303, body
    p = proposals.list_proposals(folder)[0]
    assert p['status'] == 'needs_review', p['errors']
    assert p['brief']['option'] == 'new_capital' and p['target_pct'] is None
    assert p['funding']['current_budget'] == 0 and p['funding']['contingent_budget'] == 3500000
    assert p['basket'][0]['amount'] == 0 and p['basket'][0]['contingent_amount'] == 1750000
    payload = provider.calls[0]['messages'][0]['content']
    assert 'saved_staples' in payload and 'WATCH' in payload and '2026-09-14' in payload
    assert len(provider.calls) == 7
    home = _get(base + '/pages/office.html')
    assert 'VDC' in home and destination in home
    detail = _get(base + destination)
    assert '$1,750,000.00' in detail and 'Cash retained' in detail and location in detail
    assert destination in _get(base + '/pages/capital.html')
    deck = _get(base + location)
    assert 'Saved research used for candidate selection' in deck and 'saved_staples' in deck
    current = json.loads((folder / 'answers.json').read_text())
    # Repeated clicks use the completed proposal and do not repeat paid calls.
    status, again, _ = _post(base + form.action, {'revision': revision(current)})
    assert status == 303 and again == location and len(provider.calls) == 7
    # Changed capital hides outdated dollars and permits a genuinely fresh plan.
    current['incoming']['amount'] = 2000000
    build_office(current, folder)
    stale = _get(base + destination)
    assert 'office changed' in stale and '$1,750,000.00' not in stale
    fresh = Form(stale)
    monkeypatch.setattr(proposals, 'dispatch', lambda *args: None)
    status, new_location, _ = _post(base + fresh.action, fresh.fields)
    assert status == 303 and new_location != location
    assert proposals.load(folder, p['id'])['status'] == 'superseded'


def test_discovery_uses_hosted_manifest_context_and_keeps_negative_verdicts(tmp_path, monkeypatch):
    from officekit_research.discovery import inventory
    from officekit.runtime import hosted_office, research_library
    monkeypatch.setattr('officekit.strategy_packs.load_packs', lambda *a: ([], []))
    class Library:
        def strategy_packs(self):
            return [{'id': 'shared', 'positions': ['VGSH'], 'thesis': 'Short Treasury comparison',
                     'as_of': '2026-09-14', 'author': 'contributor', 'bucket': 'defensive'}]
    p = {'brief': {'candidates': []}, 'strategy_id': 'deploy_powder', 'snapshot': {'answers': answers()}}
    with hosted_office(tmp_path, research_library=Library()):
        found = inventory(tmp_path, p)
    assert research_library() is None
    assert {e['id'] for e in found['entries']} == {'shared', 'saved_staples'}
    assert next(e for e in found['entries'] if e['id'] == 'saved_staples')['verdict'] == 'WATCH'
    assert 'approval' in found['use']


def test_published_library_only_supplies_valid_strategy_manifests():
    from hosting.app.research import Research
    pack = {'id': 'treasury', 'name': 'Treasury ladder', 'positions': ['VGSH'], 'thesis': 'Check maturity matching',
            'author': 'contributor', 'bucket': 'defensive'}
    class Published:
        def catalog(self):
            return {'areas': [{'id': 'strategies--treasury'}, {'id': 'verticals--public_co'}]}
        def entries(self, area):
            assert area == 'strategies--treasury'
            return [{'path': 'strategies/treasury/pack.json', 'size': 400, 'sha256': 'a' * 64},
                    {'path': 'strategies/bad/pack.json', 'size': 4, 'sha256': 'b' * 64},
                    {'path': 'strategies/treasury/DECK.md', 'size': 200, 'sha256': 'c' * 64}]
        def read(self, area, path):
            return json.dumps(pack if '/treasury/' in path else {}).encode()
    result = Research.strategy_packs(Published())
    assert len(result) == 1 and result[0]['id'] == 'treasury'
    assert result[0]['source_sha256'] == 'a' * 64


def test_two_inflows_have_separate_links_plans_and_funding(server, monkeypatch):
    from officekit.deployment import sources, href
    base, folder = server
    a = answers()
    a['sleeves'].append({'category': 'cash_pending', 'name': 'Ordinary income payment', 'value': 200000})
    a['commitments'].append({'id': 'payment', 'source': 'goal_reservation', 'label': 'Payment',
                            'amount': 470000, 'cadence': 'once', 'next_due': '2026-09-30', 'funding_source': 'portfolio'})
    build_office(a, folder)
    m = build_model(build_from_answers(a))
    choices = sources(m)
    assert len(choices) == 2
    amounts = [funding(m, s['id']) for s in choices]
    assert sum(f['commitment_reserve'] for f in amounts) == 370000
    assert sum(f['contingent_budget'] for f in amounts) == 3330000
    monkeypatch.setattr(proposals, 'dispatch', lambda *args: None)
    # Ambiguous aggregate requests cannot silently fund the wrong source.
    code, _, _ = _post(base + '/strategy/deploy', {'revision': revision(a)})
    assert code == 400 and not proposals.list_proposals(folder)
    ids = []
    for source in choices:
        destination = href(source['id'])
        assert destination in _get(base + '/pages/office.html')
        assert destination in _get(base + '/pages/capital.html')
        form = Form(_get(base + destination))
        code, location, body = _post(base + form.action, form.fields)
        assert code == 303, body
        ids.append(location)
    assert len(set(ids)) == 2
    saved = proposals.list_proposals(folder)
    assert {p['deployment_source']['id'] for p in saved} == {s['id'] for s in choices}
    assert all(p['status'] == 'queued' for p in saved)
    # A same-sized replacement has a different identity and cannot inherit its plan.
    a = json.loads((folder / 'answers.json').read_text())
    old_id = a['sleeves'][-1]['id']
    a['sleeves'][-1]['id'] = 'replacement-income'
    build_office(a, folder)
    assert 'Open deployment proposal' not in _get(base + href('replacement-income'))
    import urllib.error
    with pytest.raises(urllib.error.HTTPError) as error:
        _get(base + href(old_id))
    assert error.value.code == 404


def test_received_windfall_keeps_link_and_revises_into_current_cash(server, monkeypatch):
    from officekit.deployment import href
    from officekit.inflows import propose
    base, folder = server
    fake_sources(monkeypatch)
    a = answers()
    build_office(a, folder)
    destination = href(a['incoming']['id'])
    provider = Provider()
    monkeypatch.setattr(proposals, 'dispatch', lambda directory, pid: proposals.run(directory, pid,
        lambda p, f, save: pipeline.build_proposal(p, f, save, clients(provider))))
    form = Form(_get(base + destination))
    assert _post(base + form.action, form.fields)[0] == 303
    original = proposals.list_proposals(folder)[0]
    a = json.loads((folder / 'answers.json').read_text())
    a['sleeves'][0]['value'] += 5000000  # refreshed bank balance already includes the deposit
    a = propose(a, {'action': 'receive', 'inflow_id': a['incoming']['id'], 'gross': '5000000',
                    'withheld': '0', 'date': '2026-09-21', 'account_id': a['sleeves'][0]['id'],
                    'reference': 'Synthetic full receipt', 'included': 'yes'}, revision(a))
    build_office(a, folder)
    assert destination in _get(base + '/pages/office.html')
    capital = _get(base + '/pages/capital.html')
    assert capital.count(destination) >= 2  # inflow and receipt retain the link
    page = _get(base + destination)
    assert 'office changed' in page and '$3,500,000.00' in page
    fresh = Form(page)
    assert fresh.fields['inflow_id'] == original['deployment_source']['id']
    code, _, body = _post(base + fresh.action, fresh.fields)
    assert code == 303, body
    p = proposals.list_proposals(folder)[0]
    assert p['id'] != original['id'] and p['status'] in {'ready', 'needs_review'}, p['errors']
    assert p['funding']['current_budget'] == 3500000 and p['funding']['contingent_budget'] == 0
    assert p['basket'][0]['amount'] == 1750000 and p['basket'][0]['contingent_amount'] == 0
    assert json.loads((folder / 'answers.json').read_text())['sleeves'][0]['value'] == 5100000


@pytest.mark.parametrize('kind', ['windfall', 'income'])
def test_hosted_home_form_queues_and_persists_ticker_plan(office, monkeypatch, kind):
    from hosting.app.main import create_app, SESSION
    from hosting.app.credentials import Credentials
    from hosting.app.offices import Offices
    from test_hosted_parity import Queue
    fake_sources(monkeypatch)
    from test_capital_planning import planning_answers
    a = planning_answers('income') if kind == 'income' else answers()
    a['office_id'] = json.loads((office / 'answers.json').read_text())['office_id']
    (office / 'personal_context.json').write_text(json.dumps(empty(a['office_id'])))
    build_office(a, office)
    provider = Provider()
    original_run = proposals.run
    def run(folder, pid, **kwargs):
        return original_run(folder, pid, lambda p, f, save: pipeline.build_proposal(p, f, save, clients(provider)))
    monkeypatch.setattr(proposals, 'run', run)
    store, queue = MemoryStore(), Queue()
    app = create_app(Backend(), ORIGIN, store=store, queue=queue)
    with TestClient(app, base_url=ORIGIN) as client:
        _, sid = upload(client, office)
        receipt = send(client, '/api/migrations/' + sid + '/activate', {}).json()
        Credentials(Offices(store)).update('alice', a['office_id'], {
            'provider': 'openai', 'credential_revision': '0', 'OPENAI_API_KEY': 'synthetic-key'})
        client.cookies.set(SESSION, 'alice')
        home = client.get(receipt['path'] + '/pages/office.html')
        destination = deployment_link(home.text)
        from copy import deepcopy
        before = deepcopy(store.rows)
        with monkeypatch.context() as fast_page:
            fast_page.setattr('officekit.serve.render_saved_office',
                             lambda *a: pytest.fail('Deployment must not render the entire office'))
            saved_page = client.get(destination)
            assert saved_page.status_code == 200
            missing = client.get(receipt['path'] + '/pages/deployment_' + '0' * 24 + '.html')
            assert missing.status_code == 404 and 'Incoming-money source not found' in missing.text
        assert 'Existing research and tickers' in saved_page.text and 'WATCH' in saved_page.text
        assert not provider.calls and store.rows == before
        from officekit_research.discovery import reference_key
        research_url = receipt['path'] + '/pages/research_' + reference_key('imported_thesis', 'saved_staples') + '.html'
        assert research_url in saved_page.text
        assert 'Previously investigated staples' in client.get(research_url).text
        assert store.rows == before
        form = Form(saved_page.text)
        response = client.post(form.action, data=form.fields, headers={'Origin': ORIGIN}, follow_redirects=False)
        assert response.status_code == 303, response.text
        assert '/jobs/' in response.headers['location'] and not provider.calls
        uid, oid, jid = queue.items[0]
        app.state.jobs.run(uid, oid, jid)
        app.state.jobs.run(uid, oid, jid)
        job, _ = app.state.jobs.read(uid, oid, jid)
        assert job['status'] == 'complete', job
        _, record = Offices(store).read('alice', a['office_id'])
        p = json.loads(base64.b64decode(next(v for k, v in record['documents'].items() if k.startswith('strategy_proposals/'))))
        assert p['status'] == 'needs_review', p['errors']
        assert p['research_inventory']['entries'] and len(provider.calls) == 7
        assert 'Capital Planner' in provider.calls[0]['system']
        assert p['capital_plan']['source']['id'] == a['incoming']['id']
        home = client.get(receipt['path'] + '/pages/office.html')
        assert 'VDC' in home.text and destination in home.text
        with monkeypatch.context() as fast_page:
            fast_page.setattr('officekit.serve.render_saved_office',
                             lambda *a: pytest.fail('Deployment must read the latest proposal directly'))
            detail = client.get(destination)
        assert detail.status_code == 200
        assert ('$4,500.00' if kind == 'income' else '$1,750,000.00') in detail.text
        assert receipt['path'] + '/pages/proposal_' in detail.text
        if kind == 'income':
            assert p['funding']['income_expenses'] == 6000
            assert p['funding']['contingent_budget'] == 9000
            assert 'Income-period bills retained from pending proceeds' in detail.text
        client.cookies.set(SESSION, 'bob')
        assert client.get(receipt['path'] + '/pages/office.html').status_code == 404
        assert client.get(destination).status_code == 404
        assert client.get(research_url).status_code == 404


def test_saved_research_links_work_before_any_model_call(server, monkeypatch):
    from officekit_research.discovery import catalog
    base, folder = server
    build_office(answers(), folder)
    monkeypatch.setattr(proposals, 'dispatch', lambda *a: pytest.fail('Browsing must not start paid work'))
    a = json.loads((folder / 'answers.json').read_text())
    entries = catalog(folder, a)['entries']
    page = _get(base + deployment_link(_get(base + '/pages/office.html')))
    assert 'Existing research and tickers' in page and 'VDC' in page
    for entry in entries:
        assert entry['href'] in page
        detail = _get(base + entry['href'])
        assert '<!doctype html>' in detail.lower()
        assert 'not found' not in detail.lower()
    assert not proposals.list_proposals(folder)


def test_shared_search_matches_ticker_tokens_across_areas_without_loading_archives(tmp_path, monkeypatch):
    from hosting.app.research import Research
    class Library(Research):
        def __init__(self):
            pass
        def catalog(self):
            return {'revision': 'a' * 40, 'areas': [{'id': 'one'}, {'id': 'two'}]}
        def entries(self, area):
            paths = {'one': ['reports/ABC_COURT_20260901.md', 'reports/ABCD.json', 'reports/ABC.py'],
                     'two': ['reports/ABC.json', 'reports/BRK_B.json', 'reports/T_COURT.md', 'reports/TREASURY.md', 'reports/XYZ/court.json']}
            return [{'path': p, 'size': 10, 'sha256': 'b' * 64} for p in paths[area]]
        def read(self, *args):
            pytest.fail('Search should not download archives')
    library = Library()
    matches = library.search('ABC', symbol=True)
    assert len(matches) == 3 and {m['area'] for m in matches} == {'one', 'two'}
    assert len(library.search('BRK.B', symbol=True)) == 1
    assert len(library.search('T', symbol=True)) == 1
    assert len(library.search('XYZ', symbol=True)) == 1
    from officekit.runtime import hosted_office
    from officekit.render_saved_research import section
    with hosted_office(tmp_path, research_library=library), monkeypatch.context() as browsing:
        browsing.setattr(library, 'search', lambda *a, **k: pytest.fail('Render search links without scanning the library'))
        rendered = section({'entries': [{'id': 'example', 'kind': 'imported_thesis', 'symbols': ['ABC', 'KNSL'],
                                        'href': '/pages/research_example.html', 'summary': 'Saved case'}]})
    assert 'Search ABC source files' in rendered and 'q=ABC&amp;match=symbol' in rendered
    assert 'Search KNSL source files' in rendered and 'q=KNSL&amp;match=symbol' in rendered
    from hosting.app.main import create_app, SESSION
    with TestClient(create_app(Backend(), ORIGIN, store=MemoryStore(), research=library), base_url=ORIGIN) as client:
        assert client.get('/app/research?q=ABC&match=symbol', follow_redirects=False).status_code == 303
        client.cookies.set(SESSION, 'alice')
        response = client.get('/app/research?q=ABC&match=symbol')
        assert response.status_code == 200 and '3 matching files' in response.text
        assert 'area=one' in response.text and 'area=two' in response.text
        assert 'ABCD' not in response.text


def test_new_strategy_uses_same_catalog_and_links_selected_tickers(server, monkeypatch):
    from officekit_research.discovery import catalog
    base, folder = server
    fake_sources(monkeypatch)
    build_office(answers(), folder)
    provider = Provider()
    monkeypatch.setattr(proposals, 'dispatch', lambda directory, pid: proposals.run(directory, pid,
        lambda p, f, save: pipeline.build_proposal(p, f, save, clients(provider))))
    page = _get(base + '/pages/strategies.html')
    assert 'How research becomes a strategy' in page
    form = Form(page, suffix='/strategy/new')
    form.fields.update(title='Income diversification', note='Compare prior staples research and alternatives')
    status, location, body = _post(base + form.action, form.fields)
    assert status == 303, body
    saved = proposals.list_proposals(folder)[0]
    assert saved['brief']['option'] != 'new_capital'
    expected = catalog(folder, saved['snapshot']['answers'])
    assert 'saved_staples' in {r['id'] for r in saved['research_inventory']['entries']}
    thesis = next(r for r in expected['entries'] if r['id'] == 'saved_staples')
    assert saved['research_attachments'] == [{'symbol': 'VDC', 'references': [thesis['href']]}]
    assert 'saved_staples' in provider.calls[0]['messages'][0]['content']
    assert thesis['href'] in _get(base + location)


@pytest.mark.parametrize('reuse,contextual', [(False, False), (True, False)])
def test_evaluation_arms_do_not_receive_catalog_arguments(tmp_path, monkeypatch, reuse, contextual):
    from test_officekit_strategy_proposals import seed
    fake_sources(monkeypatch)
    _, p = seed(tmp_path)
    provider = Provider()
    proposals.run(tmp_path, p['id'], lambda p, f, save: pipeline.build_proposal(
        p, f, save, clients(provider), reuse=reuse, contextual_reuse=contextual))
    saved = proposals.load(tmp_path, p['id'])
    assert saved['status'] in {'ready', 'needs_review'}, saved['errors']
    assert 'research_inventory' not in saved and 'research_attachments' not in saved
