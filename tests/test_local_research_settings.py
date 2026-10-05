import stat

import pytest

from officekit import local_settings
from officekit.runtime import credential, hosted_office
from test_officekit_onboarding_e2e import server, _get, _post


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    monkeypatch.setenv('WORKER_PLACEMENT_CONFIG_DIR', str(tmp_path / 'machine-settings'))
    monkeypatch.delenv('OFFICEKIT_CONTACT', raising=False)


def test_local_contact_persists_outside_office_and_never_enters_hosted(tmp_path):
    local_settings.save_research_contact('research@example.com')
    assert credential('OFFICEKIT_CONTACT') == 'research@example.com'
    assert stat.S_IMODE(local_settings._path().stat().st_mode) == 0o600
    office = tmp_path / 'office'; office.mkdir()
    with hosted_office(office):
        assert credential('OFFICEKIT_CONTACT') is None
        assert local_settings.research_contact() is None
        with pytest.raises(ValueError, match='hosted office'):
            local_settings.save_research_contact('other@example.com')
    with hosted_office(office, {'OFFICEKIT_CONTACT': 'tenant@example.com'}):
        assert credential('OFFICEKIT_CONTACT') == 'tenant@example.com'
    assert not list(office.iterdir())
    assert local_settings.research_contact() == 'research@example.com'


def test_environment_contact_takes_precedence(monkeypatch):
    local_settings.save_research_contact('saved@example.com')
    monkeypatch.setenv('OFFICEKIT_CONTACT', 'environment@example.com')
    assert credential('OFFICEKIT_CONTACT') == 'environment@example.com'


def test_local_settings_form_saves_and_rejects_invalid_replacements(server):
    base, folder = server
    from officekit import api_errors
    api_errors.report(folder, 'signal:evidence_filings:TEST', 'Error', api_errors.RESEARCH_CONTACT_REQUIRED)
    page = _get(base + '/settings')
    assert 'action="/settings/research-contact"' in page and 'No research contact configured' in page
    code, location, body = _post(base + '/settings/research-contact', {'contact': 'research@example.com'})
    assert code == 303 and location == '/settings', body
    assert 'Contact configured on this computer' in _get(base + '/settings')
    assert credential('OFFICEKIT_CONTACT') == 'research@example.com'
    event = api_errors.active(folder)[0]
    assert event['title'] == 'Research retry needed'
    assert event['href'] == '/pages/capability_evidence_filings.html'
    assert 'TEST' in event['context']  # Preserve which request still needs data.
    code, _, _ = _post(base + '/settings/research-contact', {'contact': 'invalid'})
    assert code == 400
    assert credential('OFFICEKIT_CONTACT') == 'research@example.com'
    # This is not a route around the local Origin/session boundary.
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    with pytest.raises(HTTPError) as error:
        urlopen(Request(base + '/settings/research-contact', data=b'contact=untrusted%40example.com'))
    assert error.value.code == 403
    assert credential('OFFICEKIT_CONTACT') == 'research@example.com'


def test_contact_failure_links_to_settings_and_preserves_other_notices(tmp_path):
    from officekit import api_errors
    api_errors.report(tmp_path, 'unrelated', 'Failure', 'Other failure')
    error = RuntimeError('evidence: SEC fair-access needs a contact — set OFFICEKIT_CONTACT')
    event = api_errors.report(tmp_path, 'signal:evidence_filings:TEST', 'SignalOS request failed', error)
    assert event['title'] == 'Research contact needed' and event['href'] == '/settings'
    # HTTP transport reports the classified text again; keep the same action/id.
    replay = api_errors.report(tmp_path, event['context'], 'API request failed', api_errors.message(error))
    assert replay['id'] == event['id'] and replay['href'] == '/settings'
    assert len(api_errors.active(tmp_path)) == 2
    for link in ('https://untrusted.invalid/settings', '//untrusted.invalid/settings', '/settings?redirect=evil', '/settings/../x'):
        assert api_errors.report(tmp_path, 'bad-link', 'Error', 'Failure', href=link)['href'] is None
