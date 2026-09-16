"""Cold start is public; opening an office remains explicit and local."""
import json
import urllib.request
from officekit import api_errors
from officekit.render_landing import render_landing, render_account, asset
from test_officekit_onboarding_e2e import server, _get


def test_fresh_root_lands_then_opens_onboarding(server):
    base, folder = server
    html = _get(base+'/')
    assert 'Give every<br>dollar' in html and 'href="/start"' in html
    assert 'data-office-api-errors' not in html
    assert 'data-office-api-errors' in _get(base+'/start')


def test_welcome_never_includes_office_errors_or_draft(server):
    base, folder = server
    api_errors.report(folder,'private','Private failure','Private account number')
    (folder/'answers.json').write_text(json.dumps({'name':'private-household'}))
    html = _get(base+'/welcome')
    assert 'Private failure' not in html and 'private-household' not in html
    assert 'data-office-api-errors' not in html
    assert 'Give every<br>dollar' in html
    assert 'text/css' in urllib.request.urlopen(base+'/public/site.css').headers['Content-Type']


def test_public_rendering_and_asset_boundary():
    assert asset('/public/../serve.py') is None
    assert asset('/public/landing.html') is None
    assert '{{' not in render_landing()
    assert '&lt;script&gt;' in render_account('<script>')
