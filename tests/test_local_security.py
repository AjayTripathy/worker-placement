import http.client
import json
from urllib.parse import urlsplit, urlencode

import pytest
from local_http import headers
from test_officekit_onboarding_e2e import server, _get, _post


def request(base, method, path, fields=None, **extra):
    u = urlsplit(base)
    c = http.client.HTTPConnection(u.hostname, u.port, timeout=10)
    body = urlencode(fields or {}) if method == 'POST' else None
    c.request(method, path, body=body, headers={'Content-Type': 'application/x-www-form-urlencoded', **extra})
    r = c.getresponse()
    out = r.status, dict(r.getheaders()), r.read().decode()
    c.close()
    return out


@pytest.mark.parametrize('route', ['/reset', '/draft', '/key', '/import/files', '/chat', '/beta/program'])
@pytest.mark.parametrize('bad', [{'Origin': 'https://unrelated.example'}, {'Origin': 'null'},
                                  {'Host': 'unrelated.example'}, {'X-Office-Local-CSRF': 'wrong'},
                                  {'Sec-Fetch-Site': 'cross-site'}])
def test_every_mutation_rejects_hostile_browser_requests_without_writes(server, route, bad):
    base, folder = server
    (folder/'answers.json').write_text('{}', encoding='utf-8')
    (folder/'balance_sheet.json').write_text('{}', encoding='utf-8')
    before = {p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()}
    status, response, _ = request(base, 'POST', route, **{**headers(base), **bad})
    assert status == 403 and 'X-Office-Local-CSRF' not in response
    assert {p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()} == before


def test_no_token_is_not_an_implicit_trust_of_localhost(server):
    base, _ = server
    assert request(base, 'POST', '/reset', Origin=base)[0] == 403
    assert request(base, 'GET', '/local-session', Host='evil.example')[0] == 403


def test_native_rendered_form_and_json_fetch_use_the_session(server):
    from html.parser import HTMLParser
    from test_deployment_plan import Form
    base, folder = server
    html = _get(base+'/reset')
    f = Form(html, suffix='/reset')
    assert f.fields['_local_csrf'] and 'X-Office-Local-CSRF' in html
    (folder/'answers.json').write_text('{}', encoding='utf-8')
    assert request(base, 'POST', '/reset', f.fields, Origin=base)[0] == 303
    assert not (folder/'answers.json').exists()
    assert _post(base+'/draft', {'rows': [], 'scalars': {}}, json_body=True)[0] == 204


def test_submitted_harvest_form_uses_schema_loader(server):
    from officekit.serve import build_office
    from test_deployment_plan import answers, Form
    base, folder = server
    build_office(answers(), folder)
    form = Form(_get(base+'/pages/harvest.html'), suffix='/harvest')
    assert form.action == '/harvest'
    form.fields['tax_rate'] = '.3'
    status, _, html = request(base, 'POST', form.action, form.fields, Origin=base)
    assert status == 200 and 'Harvest' in html
