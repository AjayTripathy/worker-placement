"""Proposal contracts: real court/SignalOS orchestration with deterministic providers."""
import copy
import json
from types import SimpleNamespace

import pytest

from officekit import build_from_answers, build_model
from officekit.personal_context import empty
from officekit.commitments import revision

def current_revision(folder):
    return revision(json.loads((folder / "answers.json").read_text()))

from officekit import strategy_proposals as jobs
from officekit_ai import strategy_proposal as pipe
from officekit.render_proposal import render_proposal
from officekit.strategy_playbooks import PLAYBOOKS
from test_officekit_onboarding_e2e import server, _post, _get


def seed(folder, option="diversify", cash=100000):
    a = {"as_of": "2026-09-14", "owner": "Proposal test", "profile": {"decumulating": False},
         "sleeves": [{"category": "cash", "name": "Cash", "value": cash}],
         "incoming": {"amount": 5000000, "rate": .30, "character": "ltcg"}}
    m = build_model(build_from_answers(a))
    (folder / "personal_context.json").write_text(json.dumps(empty("test-office")))
    p = jobs.create(folder, a, m, "deploy_powder", "scenario", "tech/" + option, option=option, target_pct=10)
    return a, p


class Provider:
    def __init__(self, program=False, verdict="OWN", options=False, fail_pitch=False):
        self.program, self.verdict, self.options, self.fail_pitch = program, verdict, options, fail_pitch
        self.calls = []
        self.messages = self

    def create(self, **kw):
        props = kw['output_config']['format']['schema']['properties']
        self.calls.append(kw)
        if 'program_steps' in props:
            out = dict(thesis="Reduce tech exposure with a bounded staples allocation.", alternatives=["Keep cash until review"],
                       candidates=[] if self.program else [dict(symbol="SPY" if self.options else "VDC", instrument="options" if self.options else "etf", rationale="Fits the mandate", structure="Defined-loss put" if self.options else "Consumer staples ETF")],
                       program_steps=["Broker: obtain replacement-cost coverage quotes and review exclusions before renewal."] if self.program else [], assumptions=["Allocation target is a research assumption"])
        elif 'case' in props:
            out = dict(case="Independent argument grounded in the supplied evidence.", key_points=["Sector concentration remains"], unverified=[], lean="own")
        elif 'conviction' in props:
            out = dict(verdict=self.verdict, conviction=7, rationale="Appropriate bounded implementation", decisive_points=["Compare alternatives"], unverified_items=[])
        elif 'budget_pct' in props:
            out = dict(verdict="support", rationale="Fits the funding ceiling", budget_pct=50,
                       allocations=[] if self.program else [dict(symbol="SPY" if self.options else "VDC", weight_pct=100, rationale="One implementation avoids duplicate exposure", conditions=[])], findings=["Keep obligations reserved"], conditions=[], monitoring=["Review on receipt or allocation drift"])
        else:
            if self.fail_pitch:
                raise RuntimeError("pitch provider unavailable")
            out = dict(headline="A bounded defensive allocation", thesis="Defensive sector diversification", why_now="Review current concentration", alternatives=["Cash has less equity downside"], downside=["Staples can fall"], implementation=["Review conditions before recording intent"], monitoring=["Revisit quarterly"])
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(out))])


def clients(fake):
    return {s: (fake, 'test-opus') for s in ['intake', 'bench', 'adjudicate']}


def fake_sources(monkeypatch):
    import officekit_research as r
    monkeypatch.setitem(r.SOURCES, 'fund_profile', lambda symbol, ctx: dict(url='https://example.com/fund', fetched_at='2026-09-14', text='Primary fund mandate ' + symbol, truncated=False))
    monkeypatch.setitem(r.SOURCES, 'tape', lambda symbol, ctx: dict(last=100, as_of='09/14/2026', wk52_hi=110, wk52_lo=90, off_high_pct=-9, off_low_pct=11))


def execute(folder, p, provider):
    jobs.run(folder, p['id'], lambda record, directory, checkpoint: pipe.build_proposal(record, directory, checkpoint, clients(provider)))
    return jobs.load(folder, p['id'])


def test_full_pipeline_native_courts_signals_and_budget(tmp_path, monkeypatch):
    fake_sources(monkeypatch)
    a, p = seed(tmp_path)
    original = copy.deepcopy(a)
    provider = Provider()
    p = execute(tmp_path, p, provider)
    assert p['status'] == 'needs_review'  # pending allocation remains contingent
    assert len(provider.calls) == 6  # analyst, RED, BLUE, adjudicator, risk, pitch
    assert p['basket'][0]['symbol'] == 'VDC'
    assert p['basket'][0]['amount'] == 50000
    assert p['basket'][0]['contingent_amount'] > 0
    assert p['funding']['current_cash'] == 100000
    assert p['funding']['pending_net'] == 3500000
    assert a == original  # never purchases or deducts cash
    runs = [json.loads(s)['name'] for s in (tmp_path/'signals_runs.jsonl').read_text().splitlines()]
    assert {'strategy_proposal_research','evidence_fund_profile','evidence_tape','evidence_book'} <= set(runs)
    courts = [json.loads(s) for s in (tmp_path/'adjudications.jsonl').read_text().splitlines()]
    assert courts[0]['proposal_id'] == p['id']
    assert len(courts[0]['refs']) == 3
    assert 'Primary fund mandate VDC' in courts[0]['evidence']['md']
    assert p['risk']['call_ref'] and p['pitch']['call_ref']
    html = (tmp_path/'pages'/f'proposal_{p["id"]}.html').read_text()
    assert 'RED bench' in html and 'BLUE bench' in html and '$50,000.00' in html
    assert 'Conditional allocation' in html and 'Print / save pitch deck' in html
    execute(tmp_path, p, provider)
    assert len(provider.calls) == 6  # completed jobs are idempotent


@pytest.mark.parametrize('verdict', ['KILL','AVOID','WATCH'])
def test_rejected_court_cannot_be_overridden_by_sizing(tmp_path, monkeypatch, verdict):
    fake_sources(monkeypatch)
    _, p = seed(tmp_path)
    p = execute(tmp_path, p, Provider(verdict=verdict))
    assert p['basket'][0]['amount'] == p['basket'][0]['contingent_amount'] == 0
    assert not p['basket'][0]['eligible']
    assert p['status'] == 'needs_review'


def test_exclusions_are_mechanical(tmp_path, monkeypatch):
    fake_sources(monkeypatch)
    _, p = seed(tmp_path)
    p['snapshot']['personal_context']['exclusions'] = [dict(scope='ticker', value='VDC')]
    jobs.save(tmp_path,p)
    p=execute(tmp_path,p,Provider())
    assert not p['basket'][0]['eligible'] and p['basket'][0]['amount']==0


def test_program_uses_court_but_never_becomes_fake_position(tmp_path):
    _, p = seed(tmp_path, option='insurance')
    p=execute(tmp_path,p,Provider(program=True))
    assert p['pitch'] and p['risk'] and not p['basket']
    assert p['courts'][0]['subject_kind']=='program'
    from officekit.thesis_board import from_adjudications
    assert not from_adjudications(tmp_path)
    assert 'replacement-cost coverage quotes' in render_proposal(p)


def test_options_underlying_is_not_a_stock_buy(tmp_path, monkeypatch):
    fake_sources(monkeypatch)
    _,p=seed(tmp_path,option='put_index')
    p=execute(tmp_path,p,Provider(options=True))
    assert p['basket'][0]['amount_label']=='Premium budget ceiling'
    assert 'option-chain quote' in ' '.join(p['basket'][0]['conditions'])
    assert p['courts'][0]['subject_kind']=='options'
    from officekit.thesis_board import from_adjudications
    assert not from_adjudications(tmp_path)


def test_retry_reuses_completed_research_and_courts(tmp_path,monkeypatch):
    fake_sources(monkeypatch)
    _,p=seed(tmp_path)
    fake=Provider(fail_pitch=True)
    p=execute(tmp_path,p,fake)
    assert p['status']=='error' and p['risk'] and len(p['courts'])==1
    jobs.retry(tmp_path,p['id'])
    fake.fail_pitch=False
    p=execute(tmp_path,p,fake)
    assert p['pitch'] and not p['errors']
    assert len(fake.calls)==7
    assert len((tmp_path/'adjudications.jsonl').read_text().splitlines())==1


def test_missing_primary_evidence_is_visible(tmp_path,monkeypatch):
    fake_sources(monkeypatch)
    import officekit_research as r
    def broken(*a): raise RuntimeError('issuer unavailable')
    monkeypatch.setitem(r.SOURCES,'fund_profile',broken)
    _,p=seed(tmp_path)
    p=execute(tmp_path,p,Provider())
    assert p['status']=='needs_review'
    assert 'issuer unavailable' in render_proposal(p)
    assert any('issuer unavailable' in c for c in p['basket'][0]['conditions'])


def test_all_planner_options_have_distinct_briefs():
    from officekit.mitigations import OPT
    from officekit.render_strategies import STRATEGY_LIB
    from officekit.strategy_playbooks import STRATEGY_DEFAULT
    assert set(OPT)==set(PLAYBOOKS)
    assert set(STRATEGY_LIB) <= set(STRATEGY_DEFAULT)
    assert len({p[0] for p in PLAYBOOKS.values()})==len(PLAYBOOKS)


def test_no_current_cash_stays_zero(tmp_path,monkeypatch):
    fake_sources(monkeypatch)
    _,p=seed(tmp_path,cash=0)
    p=execute(tmp_path,p,Provider())
    assert p['basket'][0]['amount']==0 and p['basket'][0]['contingent_amount']>0


def test_adoption_requires_unchanged_snapshot(tmp_path,monkeypatch):
    fake_sources(monkeypatch)
    a,p=seed(tmp_path)
    p=execute(tmp_path,p,Provider())
    with pytest.raises(ValueError,match='office changed'):
        jobs.decide(tmp_path,{**a,'owner':'Changed'},p['id'],'adopt')
    adopted,_=jobs.decide(tmp_path,a,p['id'],'adopt')
    assert adopted['strategy_decisions']['deploy_powder']['status']=='planned'
    assert adopted['sleeves']==a['sleeves']
    (tmp_path/'personal_context.json').write_text(json.dumps({**empty(), 'notes':['New constraint']}))
    with pytest.raises(ValueError,match='constraints changed'):
        jobs.decide(tmp_path,a,p['id'],'adopt')


def test_untrusted_text_is_escaped(tmp_path):
    _,p=seed(tmp_path)
    p['brief']['title']='</h1><script>alert(1)</script>'
    html=render_proposal(p)
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html


def test_durable_replay_different_mitigations_and_validation(tmp_path):
    a,p=seed(tmp_path)
    m=build_model(p['snapshot']['data'])
    same=jobs.create(tmp_path,a,m,'deploy_powder','scenario','tech/diversify',option='diversify',target_pct=10)
    assert same['id']==p['id']
    other=jobs.create(tmp_path,a,m,'deploy_powder','scenario','tech/cash_deploy',option='cash_deploy',target_pct=10)
    assert other['id']!=p['id']
    with pytest.raises(ValueError): jobs.load(tmp_path,'../../answers')
    with pytest.raises(ValueError): jobs.create(tmp_path,a,m,'x','principal','x',target_pct=float('nan'))


def test_routes_all_creation_doors_open_proposal(server,monkeypatch):
    base,folder=server
    monkeypatch.setattr(jobs,'dispatch',lambda *a:None)
    a,_=seed(folder)
    from officekit.serve import build_office
    build_office(a,folder)
    code,loc,_=_post(base+'/strategy/new',{'revision':current_revision(folder),'title':'Custom rotation','status':'implemented','note':'Compare staples with short Treasuries'})
    assert code==303 and '/pages/proposal_' in loc
    assert 'Compare staples' in _get(base+loc)
    saved=json.loads((folder/'answers.json').read_text())
    assert saved['strategy_decisions']['custom_rotation']['status']=='considering'
    code,loc,_=_post(base+'/strategy/propose',{'revision':current_revision(folder),'sid':'core_equity'})
    assert code==303 and '/pages/proposal_' in loc
    from officekit.render_scenarios import applicable_scenarios
    from officekit.serve import _capital_model
    m=_capital_model(saved,folder)
    sc=next(sc for sc in applicable_scenarios(m) if sc.get('opts'))
    code,loc,body=_post(base+'/strategy/adopt',{'revision':current_revision(folder),'scenario':sc['key'],'opt':sc['opts'][0]})
    assert code==303 and '/pages/proposal_' in loc,body
    # Pending goal proposal has a meaningful destination and durable origin.
    _post(base+'/goals/add',{'gkind':'spending','glabel':'College','gamt':'300000','gdate':'2035-09-01'})
    saved=json.loads((folder/'answers.json').read_text())
    gid=next(g['id'] for g in saved['goals'] if g['label']=='College')
    code,loc,body=_post(base+'/strategy/goal-adopt',{'revision':current_revision(folder),'gid':gid,'sid':'bonds'})
    assert code==303 and '/pages/proposal_' in loc,body


@pytest.mark.parametrize('number', [float('nan'),float('inf'),-1,101])
def test_invalid_risk_sizing_rejected(tmp_path,number):
    _,p=seed(tmp_path)
    if __import__('math').isfinite(number):
        p['candidates']=[];p['courts']=[];p['evidence']={}
        with pytest.raises(ValueError): pipe.basket(p,pipe.budget(p),{'budget_pct':number,'allocations':[]})
    else:
        with pytest.raises(ValueError): pipe.validate(number,pipe.N)


def test_restart_is_explicit_and_preserves_checkpoints(tmp_path):
    _,p=seed(tmp_path)
    p.update(status='running',research={'thesis':'Frozen research'})
    jobs.save(tmp_path,p)
    jobs.recover_interrupted(tmp_path)
    p=jobs.load(tmp_path,p['id'])
    assert p['status']=='error' and p['research']['thesis']=='Frozen research'
    jobs.retry(tmp_path,p['id'])
    assert jobs.load(tmp_path,p['id'])['status']=='queued'


def test_revision_and_adoption_route_keep_evidence_lineage(server,monkeypatch):
    base,folder=server
    fake_sources(monkeypatch)
    monkeypatch.setattr(jobs,'dispatch',lambda *a:None)
    a,_=seed(folder)
    from officekit.serve import build_office
    build_office(a,folder)
    code,loc,_=_post(base+'/strategy/new',{'revision':current_revision(folder),'title':'Defensive program','note':'Compare VDC'})
    pid=loc.split('proposal_')[1].split('.')[0]
    p=execute(folder,jobs.load(folder,pid),Provider())
    code,_,body=_post(base+'/strategy/proposal/decide',{'revision':current_revision(folder),'pid':pid,'action':'adopt'})
    assert code==303,body
    assert jobs.load(folder,pid)['status']=='adopted'
    code,loc,body=_post(base+'/strategy/proposal/revise',{'revision':current_revision(folder),'pid':pid,'request':'Compare alternatives again'})
    assert code==303,body
    newid=loc.split('proposal_')[1].split('.')[0]
    assert newid!=pid
    assert jobs.load(folder,newid)['revision_of']==pid
    assert jobs.load(folder,pid)['superseded_by']==newid
    assert jobs.load(folder,pid)['courts']  # old evidence survives


def test_security_consumers_ignore_program_and_option_verdicts(tmp_path):
    _,p=seed(tmp_path,option='insurance')
    p=execute(tmp_path,p,Provider(program=True))
    from officekit_ai.court import export_shareable_adjudications
    from officekit_ai.docket import _adjudicated_pairs
    from officekit.render_strategies import render_strategies
    from officekit.serve import record_purchase
    assert export_shareable_adjudications(tmp_path)==[]
    assert _adjudicated_pairs(tmp_path)==set()
    html=render_strategies(build_model(p['snapshot']['data']),adjudications=p['courts'],holdings_endpoint='/holdings')
    assert p['courts'][0]['id'] not in html
    a={}
    record_purchase(a,p['strategy_id'],p['courts'][0]['symbol'],10,p['courts'])
    assert 'adjudication' not in a['sleeves'][0]['holdings'][0]


def test_fund_primary_evidence_needs_no_sec_contact(monkeypatch):
    fake_sources(monkeypatch)
    monkeypatch.delenv('OFFICEKIT_CONTACT',raising=False)
    from officekit_research import build_pack,render_pack
    p=build_pack('VDC')
    assert set(p['sections'])=={'fund_profile','book','tape'}
    assert not p['errors']
    assert 'Primary fund document' in render_pack(p)


def test_provider_credit_failure_has_actionable_message():
    message=jobs.error_message(RuntimeError('Error 400: Your credit balance is too low to access the Anthropic API; request_id=internal'))
    assert 'insufficient API credit' in message and 'resume' in message
    assert 'request_id' not in message


def test_courted_candidate_is_not_labeled_held(tmp_path,monkeypatch):
    fake_sources(monkeypatch)
    _,p=seed(tmp_path)
    p=execute(tmp_path,p,Provider())
    from officekit.thesis_board import from_adjudications
    from officekit.render_strategies import render_strategies
    html=render_strategies(build_model(p['snapshot']['data']),desk_theses=from_adjudications(tmp_path))
    assert 'data-state="watch"' in html and '1 candidate' in html
    assert 'data-state="held"' not in html


def test_declining_alternative_preserves_previously_adopted_plan(tmp_path,monkeypatch):
    fake_sources(monkeypatch)
    a,p=seed(tmp_path)
    p=execute(tmp_path,p,Provider())
    a,_=jobs.decide(tmp_path,a,p['id'],'adopt')
    assert a['strategy_decisions']['deploy_powder']['adopted_proposal_id']==p['id']
    other=jobs.create(tmp_path,a,build_model(p['snapshot']['data']),'deploy_powder','scenario','crash/cash_deploy',option='cash_deploy')
    other=execute(tmp_path,other,Provider())
    declined,_=jobs.decide(tmp_path,a,other['id'],'decline')
    assert declined['strategy_decisions']['deploy_powder']['status']=='planned'
    assert declined['strategy_decisions']['deploy_powder']['adopted_proposal_id']==p['id']
