"""Research exchange through the actual hosted tenant/CAS/CSRF transport."""
import json

from test_hosted_migration import office
from test_hosted_workspace import workspace, post
from test_contextual_research import donor
from hosting.app.main import SESSION
from hosting.app.offices import Offices
from officekit.commitments import revision


def test_hosted_import_is_durable_revisioned_and_tenant_scoped(workspace, donor):
    client, receipt, folder = workspace
    _, _, bundle, _ = donor
    answers = json.loads((folder / 'answers.json').read_text())
    page = client.get(receipt['path'] + '/research')
    assert page.status_code == 200
    assert receipt['path'] + '/research/import' in page.text
    assert 'nonce-' in page.headers['content-security-policy']
    response = post(client, receipt, '/research/import', {'revision': revision(answers)},
                    files={'bundle_file': ('research-case.json', json.dumps(bundle).encode(), 'application/json')})
    assert response.status_code == 303, response.text
    current, saved = Offices(client.store).read('alice', receipt['office_id'])
    assert current['digest'] != receipt['digest']
    assert 'research/shared_cases/' + bundle['id'] + '.json' in saved['documents']
    page = client.get(receipt['path'] + '/research')
    assert bundle['id'] in page.text
    assert post(client, receipt, '/research/import', {'revision': revision(answers), 'bundle': json.dumps(bundle)}).status_code == 409
    client.cookies.set(SESSION, 'bob')
    assert client.get(receipt['path'] + '/research').status_code in {403, 404}


def test_hosted_review_approval_returns_json_without_publishing(workspace, donor):
    from officekit_research.cases import validate_bundle
    client, receipt, folder = workspace
    _, _, bundle, _ = donor
    answers = json.loads((folder / 'answers.json').read_text())
    before = Offices(client.store).read('alice', receipt['office_id'])
    response = post(client, receipt, '/research/approve', {'revision': revision(answers), 'projection': json.dumps(bundle['case']), 'reviewed': 'yes'})
    assert response.status_code == 200, response.text
    assert response.headers['content-disposition'] == 'attachment; filename="research-case.json"'
    validate_bundle(response.json())
    assert Offices(client.store).read('alice', receipt['office_id']) == before
