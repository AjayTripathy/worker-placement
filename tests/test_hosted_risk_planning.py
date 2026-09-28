"""Hosted policy writes and queued research use the same private office model."""
import base64
import json

from test_hosted_workspace import workspace, post  # noqa: F401
from test_hosted_migration import office  # noqa: F401
from test_hosted_parity import Queue
from test_deployment_plan import Form
from test_risk_planning import definition, evidence, Forecaster
from hosting.app.offices import Offices
from hosting.app.jobs import Jobs
from hosting.app.main import SESSION
from officekit_ai import scenario_forecast


def test_hosted_policy_durable_and_private(workspace):
    client, receipt, _ = workspace
    form = Form(client.get(receipt['path']+'/pages/risk.html').text, suffix='/risk/policy')
    form.fields.update(annual_spending='300000', annual_income='0', horizon_years='20', reserve_months='24')
    response = post(client, receipt, '/risk/policy', form.fields)
    assert response.status_code == 303, response.text
    current, saved = Offices(client.store).read('alice', receipt['office_id'])
    answers = json.loads(base64.b64decode(saved['documents']['answers.json']))
    assert answers['risk_policy']['annual_spending'] == 300000
    assert 'value="300000.0"' in client.get(receipt['path']+'/pages/risk.html').text
    assert post(client, receipt, '/risk/policy', form.fields).status_code == 409
    client.cookies.set(SESSION, 'bob')
    assert client.get(receipt['path']+'/pages/scenario_research.html').status_code in {403,404}


def test_hosted_forecast_queue_persists_and_reviews_without_repeating_calls(workspace, monkeypatch):
    client, receipt, _ = workspace
    queue=Queue(); client.app.state.jobs.queue=queue
    f=Forecaster(); original=scenario_forecast.run
    monkeypatch.setattr(scenario_forecast, 'run', lambda folder,d: original(folder,d,
        clients={r:(f,'fixture') for r in ['scenario-base-rate','scenario-mechanism','scenario-adjudicator']},
        fetcher=lambda s:(evidence(),[])))
    form=Form(client.get(receipt['path']+'/pages/scenario_research.html').text, suffix='/risk/forecast')
    fields=definition(); fields.pop('scenario_key'); fields.pop('submitter'); fields['symbols']=''
    form.fields.update(fields)
    result=post(client, receipt, '/risk/forecast', form.fields)
    assert result.status_code == 303 and '/jobs/' in result.headers['location'], result.text
    uid,oid,jid=queue.items[0]
    jobs=Jobs(Offices(client.store),queue)
    jobs.run(uid,oid,jid);jobs.run(uid,oid,jid)
    state,_=jobs.read(uid,oid,jid)
    assert state['status'] == 'complete', state
    assert len(f.calls) == 3
    current,saved=Offices(client.store).read('alice',oid)
    rows=[json.loads(line) for line in base64.b64decode(saved['documents']['research/predictions.jsonl']).splitlines()]
    assert len(rows) == 3
    page=client.get(receipt['path']+'/pages/scenario_research.html')
    assert '40.0%' in page.text and 'Needs event and evidence review' in page.text
    form=Form(page.text,suffix='/risk/forecast-review');form.fields['reviewed']='yes'
    response=post(client,current,'/risk/forecast-review',form.fields)
    assert response.status_code == 303, response.text
    assert 'Reviewed for aggregation' in client.get(receipt['path']+'/pages/scenario_research.html').text


def test_provider_failure_is_failed_job_without_a_forecast(workspace, monkeypatch):
    client,receipt,_=workspace
    queue=Queue();client.app.state.jobs.queue=queue
    def fail(*args,**kw): raise RuntimeError('Provider unavailable; no forecasts recorded')
    monkeypatch.setattr(scenario_forecast,'run',fail)
    form=Form(client.get(receipt['path']+'/pages/scenario_research.html').text,suffix='/risk/forecast')
    fields=definition(); fields.pop('scenario_key');fields.pop('submitter');fields['symbols']=''
    form.fields.update(fields)
    result=post(client,receipt,'/risk/forecast',form.fields)
    assert result.status_code == 303
    uid,oid,jid=queue.items[0]
    jobs=Jobs(Offices(client.store),queue);jobs.run(uid,oid,jid)
    state,_=jobs.read(uid,oid,jid)
    assert state['status'] == 'error', state
    _,saved=Offices(client.store).read('alice',oid)
    assert 'research/predictions.jsonl' not in saved['documents']
