"""App-wide failure visibility without retries, lost edits or changed balances."""
import json
import pytest
import urllib.error
import urllib.request

from officekit import api_errors as errors
from test_officekit_onboarding_e2e import server, _post, _get


def test_notice_deduplication_dismissal_and_fresh_failure(tmp_path):
    one=errors.report(tmp_path,'proposal:a','Strategy review failed',RuntimeError('credit balance too low'),'/pages/proposal_a.html')
    same=errors.report(tmp_path,'proposal:a','Strategy review failed',RuntimeError('credit balance too low'),'/pages/proposal_a.html')
    assert same['id']==one['id'] and len(errors.active(tmp_path))==1
    errors.report(tmp_path,'import:b','Account refresh failed','Connection refused')
    errors.clear(tmp_path,event_id=one['id'])
    assert [e['context'] for e in errors.active(tmp_path)]==['import:b']
    new=errors.report(tmp_path,'proposal:a','Strategy review failed','credit balance too low')
    assert new['id']!=one['id']
    # A stale dismissal must not erase a later failure of the same request.
    errors.clear(tmp_path,event_id=one['id'])
    assert len(errors.active(tmp_path))==2
    errors.clear(tmp_path,context='proposal:a')
    assert len(errors.active(tmp_path))==1


def test_notices_are_bounded_and_links_cannot_escape_office(tmp_path):
    for i in range(30):
        errors.report(tmp_path,str(i),'Failure','Failed',href='javascript:alert(1)')
    rows=errors.active(tmp_path)
    assert len(rows)==errors.LIMIT and all(e['href'] is None for e in rows)
    assert not list(tmp_path.glob('.api-errors-*'))


def test_credentials_are_not_displayed():
    assert 'secret-value' not in errors.message('Authorization: Bearer secret-value failed')
    assert 'sk-sensitive-value' not in errors.message('Failed sk-sensitive-value')
    assert 'private' not in errors.message('api_key=private')
    assert 'insufficient API credit' in errors.message('Your credit balance is too low')


def test_chat_provider_failure_returns_502_and_creates_notice(server,monkeypatch):
    base,folder=server
    monkeypatch.setattr('officekit.serve._ai',lambda *a,**k:True)
    def fail(*a,**kw):raise RuntimeError('Your credit balance is too low to access the Anthropic API')
    monkeypatch.setattr('officekit_ai.intake_chat.turn',fail)
    code,_,body=_post(base+'/chat',{'messages':[],'scope':'goals'},json_body=True)
    assert code==502 and 'insufficient API credit' in json.loads(body)['error']
    events=json.loads(_get(base+'/api-errors'))
    assert len(events)==1 and events[0]['context']=='request:/chat'
    # The browser can dismiss immediately, before its next background poll.
    req=urllib.request.Request(base+'/chat',data=b'{"messages":[],"scope":"goals"}',headers={'Content-Type':'application/json'})
    with pytest.raises(urllib.error.HTTPError) as caught:
        urllib.request.urlopen(req)
    assert caught.value.headers['X-Office-API-Error-Id']==events[0]['id']
    assert 'data-office-api-errors' in _get(base+'/start')
    _post(base+'/api-errors/dismiss',{'id':events[0]['id']},json_body=True)
    assert json.loads(_get(base+'/api-errors'))==[]
    # Successful retry clears only the matching failed action.
    _post(base+'/chat',{'messages':[]},json_body=True)
    monkeypatch.setattr('officekit_ai.intake_chat.turn',lambda *a,**kw:{'message':'Ready'})
    _post(base+'/chat',{'messages':[]},json_body=True)
    assert errors.active(folder)==[]


def test_failed_html_form_response_keeps_navigation_and_banner(server):
    base,folder=server
    req=urllib.request.Request(base+'/strategy/new',data=b'title=Test',headers={'Accept':'text/html','Content-Type':'application/x-www-form-urlencoded'})
    try:
        urllib.request.urlopen(req)
        assert False,'Missing office should fail'
    except urllib.error.HTTPError as response:
        html=response.read().decode()
        assert response.code==400
        assert 'data-office-api-errors' in html and 'Back to the previous page' in html
        assert 'text/html' in response.headers['Content-Type']
    assert errors.active(folder)


def test_existing_rendered_pages_gain_banner_without_rebuild(server):
    base,folder=server
    pages=folder/'pages';pages.mkdir(exist_ok=True)
    original='<!doctype html><html><head><title>Saved page</title></head><body><input value="Keep my draft"></body></html>'
    (pages/'strategies.html').write_text(original)
    html=_get(base+'/pages/strategies.html')
    assert 'data-office-api-errors' in html and 'Keep my draft' in html
    assert (pages/'strategies.html').read_text()==original
    assert 'history.back()' not in errors.SCRIPT
    assert 'location.reload' not in errors.SCRIPT


def test_background_proposal_failure_links_back_and_retry_clears(tmp_path):
    from test_officekit_strategy_proposals import seed
    from officekit import strategy_proposals as jobs
    _,p=seed(tmp_path)
    def fail(*a):raise RuntimeError('credit balance too low')
    jobs.run(tmp_path,p['id'],fail)
    event=errors.active(tmp_path)[0]
    assert event['context']=='proposal:'+p['id']
    assert event['href']==f'/pages/proposal_{p["id"]}.html'
    jobs.retry(tmp_path,p['id'])
    jobs.run(tmp_path,p['id'],lambda p,f,checkpoint:checkpoint('Complete',status='ready'))
    assert errors.active(tmp_path)==[]


def test_background_signal_and_import_recover_independently(tmp_path,monkeypatch):
    import officekit_signals as signals
    from officekit import staging
    def fail(*a):raise RuntimeError('Source timed out')
    monkeypatch.setitem(signals.CAPABILITIES,'test_error_bar',{'fn':fail})
    try:signals.run_capability(tmp_path,'test_error_bar',{})
    except RuntimeError:pass
    staging.record_failure(tmp_path,'broker','API authentication failed')
    assert len(errors.active(tmp_path))==2
    monkeypatch.setitem(signals.CAPABILITIES,'test_error_bar',{'fn':lambda ctx:{'ok':True}})
    signals.run_capability(tmp_path,'test_error_bar',{})
    assert errors.active(tmp_path)[0]['context']=='import:broker'
    staging.record_pull(tmp_path,'broker','adapter','Broker',[],'auto')
    assert errors.active(tmp_path)==[]


def test_dismissal_requires_a_valid_event_id(server):
    base,folder=server
    event=errors.report(folder,'x','Error','Test')
    code,_,_=_post(base+'/api-errors/dismiss',{'id':'all'},json_body=True)
    assert code==400 and errors.active(folder)[0]['id']==event['id']
    assert len(errors.active(folder))==1  # no recursive error while dismissing
