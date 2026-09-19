"""Bounded live-model pilot with fictional offices and frozen primary evidence.

No real-office mutation, publication, trades or performance claims. Source
acquisitions are counted replay calls, not a live-network latency benchmark.
Run donor first, review/export its case, then compare three recipient arms.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import random
import time
import uuid

from officekit import build_from_answers, build_model
from officekit.personal_context import empty
from officekit import strategy_proposals as jobs
from officekit_ai.court import _create
from officekit_ai.models import client_for
from officekit_ai.models import resolve
from officekit_ai.provenance import protocol_hash
from officekit_ai.strategy_proposal import build_proposal
from officekit.office_lock import locked
from officekit_research import SOURCES
from officekit_research.cases import (canonical, day, digest, import_bundle, read_bundle, reusable_sections, utcnow)

PROTOCOL = 'contextual_reuse_pilot_v2'
ARMS = {'baseline': (False, False), 'evidence_only': (True, False), 'contextual': (True, True)}


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_bytes(canonical(value) + b'\n')
    temporary.replace(path)


class BudgetClient:
    def __init__(self, client, log, max_calls, output_budget):
        self.client, self.log = client, Path(log)
        self.provider_client = type(client).__module__ + '.' + type(client).__name__
        self.max_calls, self.output_budget = max_calls, output_budget
        self.calls = json.loads(self.log.read_text()) if self.log.exists() else []
        if any(c['status'] not in {'complete', 'rejected'} for c in self.calls):
            raise ValueError('An earlier call has uncertain completion. Inspect the ledger before starting another pilot.')
        self.messages = self

    def save(self):
        write_json(self.log, self.calls)

    def create(self, **kw):
        # Missing usage is unknown; reserve the requested ceiling conservatively.
        used = sum((c.get('output_tokens') if type(c.get('output_tokens')) is int else c['max_tokens'])
                   for c in self.calls if c['status'] != 'rejected')
        remaining = self.output_budget - used
        if len(self.calls) >= self.max_calls or remaining < 2000:
            raise ValueError('Evaluation call/token budget reached; completed checkpoints are retained')
        kw['max_tokens'] = min(kw['max_tokens'], 6000, remaining)
        # Keep free-form court briefs bounded while leaving all schema fields.
        kw['system'] += '\nEvaluation run: be concise. Keep each bench brief under 800 words, retain every material gap, and cite supplied evidence.'
        record = {'id': str(uuid.uuid4()), 'status': 'started', 'at': utcnow(),
                  'model': kw['model'], 'request_sha256': digest(kw), 'max_tokens': kw['max_tokens']}
        self.calls.append(record)
        self.save()
        print('Model call ' + str(len(self.calls)) + ' started', flush=True)
        start = time.monotonic()
        try:
            response = _create(self.client, **kw)
        except Exception as exc:
            status = getattr(exc, 'status_code', None)
            record.update(status='rejected' if status in {400, 401, 402, 403, 404, 413, 422, 429} else 'uncertain',
                          http_status=status, error_type=type(exc).__name__, latency_s=round(time.monotonic()-start, 3))
            self.save()
            raise
        usage = getattr(response, 'usage', None)
        record.update(status='complete', latency_s=round(time.monotonic()-start, 3), stop_reason=response.stop_reason,
                      resolved_model=getattr(response, 'model', None) or 'unknown',
                      input_tokens=getattr(usage, 'input_tokens', None), output_tokens=getattr(usage, 'output_tokens', None))
        self.save()
        print('Model call ' + str(len(self.calls)) + ' complete', flush=True)
        return response


def scenario(folder, recipient=False, *, as_of=None, office_id=None):
    folder.mkdir(parents=True, exist_ok=True)
    if list((folder / 'strategy_proposals').glob('*.json')):
        return jobs.list_proposals(folder)[0]
    today = day(as_of) if as_of else datetime.now(timezone.utc).date()
    oid = office_id or str(uuid.uuid4())
    a = {'office_id': oid, 'as_of': today.isoformat(), 'owner': 'Fictional evaluation office',
         'profile': {'decumulating': recipient, 'net_buyer': not recipient},
         'sleeves': [{'id': str(uuid.uuid5(uuid.UUID(oid), 'pilot-cash')), 'category': 'cash',
                      'name': 'Evaluation cash', 'value': 150000 if recipient else 100000}],
         'goals': [{'id': 'pilot-goal', 'kind': 'spending' if recipient else 'liquidity_floor',
                    'label': 'Fictional near-term obligation' if recipient else 'Fictional liquidity reserve',
                    'amount': 90000 if recipient else 10000, 'date': (today + timedelta(days=10 if recipient else 365)).isoformat()}]}
    # A goal describes intent; an explicit reservation constrains cash. Isolate
    # this payment from statistical estimates of unspecified lifestyle spending.
    a['commitments'] = [
        {'id': 'implicit:spending:lifestyle', 'annual_amount': 0,
         'provenance': 'Controlled evaluation excludes other lifestyle spending'},
        {'id': str(uuid.uuid5(uuid.UUID(oid), 'pilot-reservation')), 'source': 'goal_reservation',
         'label': a['goals'][0]['label'], 'amount': a['goals'][0]['amount'], 'cadence': 'once',
         'next_due': a['goals'][0]['date'], 'funding_source': 'portfolio', 'provenance': 'Fictional evaluation reservation'}]
    pc = empty(oid)
    pc['jurisdictions'] = {'country': 'US'}
    pc['doctrine'] = [{'id': 'pilot-cash', 'rule': 'Do not recommend selling bank cash needed for an imminent payment. Investigate only surplus cash.', 'date': today.isoformat()}]
    (folder / 'personal_context.json').write_bytes(canonical(pc))
    data = build_from_answers(a)
    model = build_model(data)
    ctx = {'strategy': 'cash_mgmt', 'goal_types': ['spending' if recipient else 'liquidity_floor'], 'goal_basis': 'declared',
           'life_stage': 'decumulating' if recipient else 'accumulating', 'horizon': 'under_2y',
           'liquidity': 'dated_spending' if recipient else 'reserve', 'country': 'US'}
    p = jobs.create(folder, a, model, 'cash_mgmt', 'principal', 'evaluation-cash-reserve',
                    title='Evaluation: surplus liquidity', target_pct=20, research_context=ctx,
                    request='Investigate only SGOV as the single candidate; compare retaining bank cash as the alternative. '
                    'Do not introduce other traded symbols. Distinguish an ETF from payment-ready bank cash. '
                    'This is a fictional research evaluation, not an instruction to transact. '
                    'The scenario explicitly reserves the stated obligation and excludes other lifestyle spending. '
                    + ('The household is decumulating and owes 90,000 in ten days. That payment must remain in bank cash. '
                       'Evaluate only cash remaining after that obligation.' if recipient else
                       'The household is accumulating and maintains a 10,000 bank cash floor. Evaluate only the surplus.'))
    (folder / 'answers.json').write_bytes(canonical(a))
    (folder / 'balance_sheet.json').write_bytes(canonical(data))
    return p


def plan(args, model, evidence, bundle):
    """Freeze all experimental inputs before model construction or dispatch."""
    current = {'protocol': PROTOCOL, 'model': model, 'evidence_sha256': digest(evidence),
               'bundle_id': bundle['id'] if bundle else None,
               'implementation_sha256': digest({'agents': protocol_hash(),
                   'evaluate': Path(__file__).read_text(),
                   'cases': (Path(__file__).parent / 'cases.py').read_text()})}
    path = args.out / (args.phase + '-plan.json')
    if path.exists():
        saved = json.loads(path.read_text())
        if saved['inputs'] != current:
            raise ValueError('Evaluation inputs changed. Use a new output directory; existing results are retained.')
        return saved
    arm_names = ['donor'] if args.phase == 'donor' else list(ARMS)
    if any(list((args.out / arm / 'strategy_proposals').glob('*.json')) for arm in arm_names + ['reuse']):
        raise ValueError('Legacy evaluation has no frozen plan. Use a new output directory; existing checkpoints are retained.')
    run_id = str(uuid.uuid4())
    random.Random(run_id).shuffle(arm_names)
    saved = {'inputs': current, 'as_of': utcnow()[:10], 'office_id': str(uuid.uuid4()),
             'run_id': run_id, 'arm_order': arm_names}
    write_json(path, saved)
    return saved


def scenario_digest(p):
    # Proposal IDs are bookkeeping. Every other saved fact and instruction must
    # match across recipient arms and survive resume without silent edits.
    snapshot = deepcopy(p['snapshot'])
    for decision in snapshot['answers'].get('strategy_decisions', {}).values():
        decision.pop('proposal_ids', None)
    return digest({'snapshot': snapshot, 'brief': p['brief'], 'target_pct': p['target_pct'],
                   'research_context': p['research_context'], 'source': p['source'], 'source_ref': p['source_ref']})


def validate_inputs(args):
    """Reject a missing, expired or mismatched comparison before spending."""
    from officekit_research.cases import validate_evidence
    if args.max_calls < 1 or args.output_token_budget < 2000:
        raise ValueError('Use a positive call limit and at least 2,000 output tokens')
    evidence = json.loads(args.evidence.read_text())
    validate_evidence({'section': 'fund_profile', 'source_url': evidence['url'],
                       'retrieved_at': evidence['fetched_at'], 'data': evidence})
    today = datetime.now(timezone.utc).date()
    if not 0 <= (today - day(evidence['fetched_at'])).days <= 30:
        raise ValueError('The frozen source must have been collected within the last 30 days')
    bundle = None
    if args.phase == 'pair':
        if not args.bundle:
            raise ValueError('--bundle is required before starting the recipient comparison')
        bundle = read_bundle(args.bundle)
        case = bundle['case']
        if case['provenance']['kind'] != 'evaluation_scenario' or case['subject'] != {'symbol': 'SGOV', 'instrument': 'etf'}:
            raise ValueError('The pilot needs an explicitly labeled SGOV evaluation case')
        if not 0 <= (today - day(case['as_of'])).days <= 90 or day(bundle['review']['reviewed_at']) > today:
            raise ValueError('The evaluation case must be current and available today')
        context = case['context']
        if any(context[k] != v for k, v in {'strategy': 'cash_mgmt', 'life_stage': 'accumulating',
                'horizon': 'under_2y', 'country': 'US', 'liquidity': 'reserve'}.items()):
            raise ValueError('The comparison requires the accumulating cash-reserve donor case')
        allowed, conflicts = reusable_sections({'matches': [{'bundle': bundle}]}, 'SGOV')
        if conflicts or 'fund_profile' not in allowed or allowed['fund_profile']['sha256'] != digest(evidence):
            raise ValueError('The case must permit fresh reuse of the exact frozen source supplied to this evaluation')
    return evidence, bundle


AUDIT_CHECKS = {
    'payment_reserved': 'Does the proposal preserve the 90,000 payment in bank cash for ten days and size only surplus?',
    'recipient_context': 'Does it correctly use the recipient\'s decumulation, dated spending and liquidity needs?',
    'source_support': 'Are material factual claims supported by the evidence actually supplied, with gaps identified?',
    'alternatives': 'Does it compare retaining bank cash and distinguish an ETF from payment-ready cash?',
    'uncertainty': 'Does it retain missing market quotes and other conditions instead of claiming execution readiness?',
    'independent_judgment': 'Is suitability established for the current office without relying on a historical verdict?',
}


def review_packet(proposals, frozen):
    """Mask arm labels, never grade outputs with the generating model."""
    names = sorted(proposals)
    random.Random(frozen['run_id'] + '-review').shuffle(names)
    key, reviews = {}, {}
    for index, name in enumerate(names):
        label = chr(ord('A') + index)
        key[label] = name
        p = proposals[name]
        def output(value):
            return {k: v for k, v in (value or {}).items() if k not in {'run', 'call_ref', 'model'}}
        reviews[label] = {
            'research': output(p.get('research')), 'risk': output(p.get('risk')), 'pitch': output(p.get('pitch')),
            'funding': p.get('funding'), 'basket': [{k: v for k, v in row.items() if k != 'court_id'} for row in p.get('basket', [])],
            'courts': [{k: c.get(k) for k in ('symbol', 'verdict', 'rationale', 'briefs', 'unverified_items')} for c in p.get('courts', [])],
            'supplied_evidence': {symbol: {'sections': pack['sections'], 'errors': pack['errors']} for symbol, pack in p.get('evidence', {}).items()},
            'audit': {check: {'status': 'not_assessed', 'rationale': '', 'output_quote': '', 'evidence_locator': ''} for check in AUDIT_CHECKS}}
    return {'protocol': PROTOCOL, 'status': 'pending_independent_review', 'checks': AUDIT_CHECKS,
            'recipient_context': next(iter(proposals.values()))['research_context'],
            'recipient_inputs': {'brief': next(iter(proposals.values()))['brief'],
                                 'snapshot': next(iter(proposals.values()))['snapshot']},
            'instructions': ['Review before opening review-key.json or arm metrics.',
                             'Arm labels are masked; source gaps or narrative may reveal the treatment.',
                             'For each check record pass/fail/unknown/not_applicable, rationale, an output quote and an evidence locator.',
                             'This is one fictional case and cannot establish statistical or investment-performance superiority.'],
            'reviews': reviews}, key


def metrics(p):
    packs = list(p.get('evidence', {}).values())
    runs = [p[k]['run'] for k in ('research', 'risk', 'pitch') if p.get(k) and p[k].get('run')]
    runs += [run for court in p.get('courts', []) for run in court.get('runs', {}).values()]
    def tokens(kind):
        values = [r['usage'].get(kind) for r in runs]
        return sum(values) if values and all(type(v) is int for v in values) else None
    return {'proposal_id': p['id'], 'status': p['status'], 'context': p.get('research_context'),
            'reuse_mode': p.get('research_reuse', {}).get('mode'),
            'case_ids': sorted({m['id'] for found in [p.get('research_reuse', {})] + list(p.get('candidate_reuse', {}).values()) for m in found.get('matches', [])}),
            'source_acquisitions': sum(len(x.get('acquisition', {}).get('fetched', [])) + len(x.get('acquisition', {}).get('failed', [])) for x in packs),
            'source_sections_reused': sum(len(x.get('reuse', {})) for x in packs),
            'source_errors': [error for x in packs for error in x.get('errors', [])],
            'model_calls': len(runs), 'input_tokens': tokens('input_tokens'), 'output_tokens': tokens('output_tokens'),
            'model_latency_s': round(sum(r['latency_s'] for r in runs), 3), 'cost_usd': None,
            'basket': p.get('basket'), 'courts': [{'verdict': c['verdict'], 'rationale': c['rationale'], 'unverified': c['unverified_items']} for c in p.get('courts', [])],
            'human_audit': 'pending', 'performance_claim': None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['donor', 'pair'])
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path, help='Frozen, manually checked fund_profile JSON for SGOV')
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--max-calls', type=int, default=26)
    parser.add_argument('--output-token-budget', type=int, default=80000)
    parser.add_argument('--resume', action='store_true', help='Explicitly retry a saved proposal after resolving a definite provider rejection')
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    # Serialize the budget ledger and resume checks across evaluator processes.
    with locked(args.out):
        return run_phase(args)


def run_phase(args):
    evidence, bundle = validate_inputs(args)
    _, _, model = resolve('intake')
    frozen = plan(args, model, evidence, bundle)
    prepared = {arm: scenario(args.out / arm, recipient=args.phase == 'pair',
                as_of=frozen['as_of'], office_id=frozen['office_id']) for arm in frozen['arm_order']}
    fingerprints = {scenario_digest(p) for p in prepared.values()}
    if len(fingerprints) != 1 or (frozen.get('scenario_sha256') and frozen['scenario_sha256'] not in fingerprints):
        raise ValueError('Recipient facts or instructions changed across evaluation arms or since the plan was frozen')
    frozen['scenario_sha256'] = fingerprints.pop()
    write_json(args.out / (args.phase + '-plan.json'), frozen)
    if not args.resume and any(p['status'] == 'error' for p in prepared.values()):
        raise ValueError('A prior proposal failed. Inspect its saved error, resolve it and use --resume.')
    client, model = client_for('intake')
    if model != frozen['inputs']['model']:
        raise ValueError('The configured model changed while preparing the evaluation')
    bounded = BudgetClient(client, args.out / 'calls.json', args.max_calls, args.output_token_budget)
    slots = {slot: (bounded, model) for slot in ('intake', 'bench', 'adjudicate')}
    source_counts = {'fund_profile': 0, 'tape': 0}
    outage = args.phase == 'pair'
    def profile(symbol, ctx):
        source_counts['fund_profile'] += 1
        if outage:
            raise ValueError('Controlled evaluation: primary issuer source temporarily unavailable')
        if symbol != 'SGOV':
            raise ValueError('This frozen evaluation source covers SGOV only')
        return dict(evidence)
    def tape(symbol, ctx):
        source_counts['tape'] += 1
        raise ValueError('Current market quote was not captured in this evaluation; verify before implementation')
    originals = {name: SOURCES[name] for name in ('fund_profile', 'tape')}
    SOURCES.update(fund_profile=profile, tape=tape)
    try:
        results, proposals = {}, {}
        for arm in frozen['arm_order']:
            reuse, contextual = (False, False) if arm == 'donor' else ARMS[arm]
            folder = args.out / arm
            p = prepared[arm]
            if p['status'] == 'error':
                if not args.resume:
                    raise ValueError('A prior proposal failed. Inspect its saved error, resolve it and use --resume.')
                p = jobs.retry(folder, p['id'])
            if reuse:
                import_bundle(folder, bundle)
            print('Starting ' + arm, flush=True)
            jobs.run(folder, p['id'], lambda record, directory, checkpoint: build_proposal(record, directory, checkpoint, slots, reuse=reuse, contextual_reuse=contextual, include_evaluation=True))
            p = jobs.load(folder, p['id'])
            proposals[arm] = p
            results[arm] = metrics(p)
            (args.out / (arm + '-metrics.json')).write_text(json.dumps(results[arm], indent=2) + '\n')
            if p['status'] == 'error':
                print(json.dumps({'arm': arm, 'status': 'error', 'errors': p['errors']}), flush=True)
                return 1
            print('Completed ' + arm, flush=True)
        (args.out / (args.phase + '-report.json')).write_text(json.dumps({
            'protocol': PROTOCOL, 'population': 'fictional offices; configured provider responses',
            'plan': frozen,
            'model': model, 'evidence_sha256': digest(evidence), 'paired_source_condition': 'issuer unavailable' if outage else 'frozen primary-source summary',
            'source_replay_counts_this_invocation': source_counts, 'arms': results,
            'limitations': ['Small mechanism pilot, not a statistical effectiveness estimate',
                            'Source counts use controlled replay, not live-network benchmarking',
                            'Independent human source and constraint audit is required', 'No investment-performance claim']}, indent=2) + '\n')
        if args.phase == 'pair':
            packet, key = review_packet(proposals, frozen)
            # Preserve any human review on an idempotent rerun.
            if not (args.out / 'review-packet.json').exists():
                write_json(args.out / 'review-packet.json', packet)
            write_json(args.out / 'review-key.json', key)
        return 0
    finally:
        SOURCES.update(originals)


if __name__ == '__main__':
    raise SystemExit(main())
