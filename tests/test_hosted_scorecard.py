import base64
import json
from datetime import date, timedelta

from test_hosted_workspace import workspace, post  # noqa: F401
from test_hosted_migration import office  # noqa: F401
from test_deployment_plan import Form
from hosting.app.offices import Offices


def test_prediction_and_outcome_survive_hosted_materialization(workspace):
    client, receipt, _ = workspace
    response = client.get(receipt['path'] + '/research/scorecard')
    assert response.status_code == 200
    form = Form(response.text, suffix='/research/predict')
    form.fields.update(symbol='AAA', statement='Revenue > 100', resolution_criteria='Audited FY revenue > $100m',
                       probability='.8', base_rate='.5', submitter='office-researcher', agent='earnings-reviewer',
                       model='fixture', protocol='v1', event_key='AAA-FY-revenue',
                       resolve_by=(date.today() + timedelta(days=90)).isoformat())
    result = post(client, receipt, '/research/predict', form.fields)
    assert result.status_code == 200, result.text
    current, saved = Offices(client.store).read('alice', receipt['office_id'])
    predictions = base64.b64decode(saved['documents']['research/predictions.jsonl'])
    assert json.loads(predictions)['agent'] == 'earnings-reviewer'
    result = client.get(receipt['path'] + '/research/scorecard')
    form = Form(result.text, suffix='/research/resolve')
    form.fields.update(outcome='true', source_url='https://www.sec.gov/Archives/example.htm')
    result = post(client, current, '/research/resolve', form.fields)
    assert result.status_code == 200, result.text
    result = client.get(receipt['path'] + '/research/scorecard')
    assert '0.04' in result.text and '1 / 1' in result.text
    from hosting.app.main import SESSION
    client.cookies.set(SESSION, 'bob')
    assert client.get(receipt['path'] + '/research/scorecard').status_code in {403, 404}
