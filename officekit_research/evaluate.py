"""Bounded live-model pilot with fictional offices and frozen primary evidence.

No real-office mutation, publication, trades or performance claims. Source
acquisitions are counted replay calls, not a live-network latency benchmark.
Run donor first, review/export its case, then run paired recipient arms.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
import uuid

from officekit import build_from_answers, build_model
from officekit.personal_context import empty
from officekit import strategy_proposals as jobs
from officekit_ai.court import _create
from officekit_ai.models import client_for
from officekit_ai.strategy_proposal import build_proposal
from officekit_research import SOURCES
from officekit_research.cases import (canonical, digest, import_bundle, read_bundle, utcnow)


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
        self.log.write_text(json.dumps(self.calls, indent=2) + '\n')

    def create(self, **kw):
        used = sum(c.get('output_tokens') or 0 for c in self.calls)
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
                      resolved_model=getattr(response, 'model', kw['model']),
                      input_tokens=getattr(usage, 'input_tokens', None), output_tokens=getattr(usage, 'output_tokens', None))
        self.save()
        print('Model call ' + str(len(self.calls)) + ' complete', flush=True)
        return response


def scenario(folder, recipient=False):
    folder.mkdir(parents=True, exist_ok=True)
    if list((folder / 'strategy_proposals').glob('*.json')):
        return jobs.list_proposals(folder)[0]
    today = datetime.now(timezone.utc).date()
    oid = str(uuid.uuid4())
    a = {'office_id': oid, 'as_of': today.isoformat(), 'owner': 'Fictional evaluation office',
         'profile': {'decumulating': recipient},
         'sleeves': [{'category': 'cash', 'name': 'Evaluation cash', 'value': 150000 if recipient else 100000}],
         'goals': [{'id': 'pilot-goal', 'kind': 'spending' if recipient else 'liquidity_floor',
                    'label': 'Fictional near-term obligation' if recipient else 'Fictional liquidity reserve',
                    'amount': 90000 if recipient else 10000, 'date': (today + timedelta(days=10 if recipient else 365)).isoformat()}]}
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
                    + ('The household is decumulating and owes 90,000 in ten days. That payment must remain in bank cash. '
                       'Evaluate only cash remaining after that obligation.' if recipient else
                       'The household is accumulating and maintains a 10,000 bank cash floor. Evaluate only the surplus.'))
    (folder / 'answers.json').write_bytes(canonical(a))
    (folder / 'balance_sheet.json').write_bytes(canonical(data))
    return p


def metrics(p):
    packs = list(p.get('evidence', {}).values())
    runs = [p[k]['run'] for k in ('research', 'risk', 'pitch') if p.get(k) and p[k].get('run')]
    runs += [run for court in p.get('courts', []) for run in court.get('runs', {}).values()]
    def tokens(kind):
        values = [r['usage'].get(kind) for r in runs]
        return sum(values) if values and all(type(v) is int for v in values) else None
    return {'proposal_id': p['id'], 'status': p['status'], 'context': p.get('research_context'),
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
    parser.add_argument('--max-calls', type=int, default=20)
    parser.add_argument('--output-token-budget', type=int, default=80000)
    parser.add_argument('--resume', action='store_true', help='Explicitly retry a saved proposal after resolving a definite provider rejection')
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    evidence = json.loads(args.evidence.read_text())
    # Validate before any paid calls. The source replay remains visibly labeled.
    from officekit_research.cases import validate_evidence
    validate_evidence({'section': 'fund_profile', 'source_url': evidence['url'], 'retrieved_at': evidence['fetched_at'], 'data': evidence})
    client, model = client_for('intake')
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
        arms = [('donor', False)] if args.phase == 'donor' else [('baseline', False), ('reuse', True)]
        results = {}
        for arm, reuse in arms:
            folder = args.out / arm
            p = scenario(folder, recipient=args.phase == 'pair')
            if p['status'] == 'error':
                if not args.resume:
                    raise ValueError('A prior proposal failed. Inspect its saved error, resolve it and use --resume.')
                p = jobs.retry(folder, p['id'])
            if reuse:
                if not args.bundle:
                    parser.error('--bundle is required for the paired evaluation')
                bundle = read_bundle(args.bundle)
                if bundle['case']['provenance']['kind'] != 'evaluation_scenario':
                    raise ValueError('The pilot accepts only explicitly labeled evaluation cases')
                import_bundle(folder, bundle)
            print('Starting ' + arm, flush=True)
            jobs.run(folder, p['id'], lambda record, directory, checkpoint: build_proposal(record, directory, checkpoint, slots, reuse=reuse, include_evaluation=True))
            p = jobs.load(folder, p['id'])
            results[arm] = metrics(p)
            (args.out / (arm + '-metrics.json')).write_text(json.dumps(results[arm], indent=2) + '\n')
            if p['status'] == 'error':
                print(json.dumps({'arm': arm, 'status': 'error', 'errors': p['errors']}), flush=True)
                return 1
            print('Completed ' + arm, flush=True)
        (args.out / (args.phase + '-report.json')).write_text(json.dumps({
            'protocol': 'contextual_reuse_pilot_v1', 'population': 'fictional offices; actual model responses',
            'model': model, 'evidence_sha256': digest(evidence), 'paired_source_condition': 'issuer unavailable' if outage else 'frozen primary-source summary',
            'source_replay_counts': source_counts, 'arms': results,
            'limitations': ['Small mechanism pilot, not a statistical effectiveness estimate',
                            'Source counts use controlled replay, not live-network benchmarking',
                            'Independent human source and constraint audit is required', 'No investment-performance claim']}, indent=2) + '\n')
        return 0
    finally:
        SOURCES.update(originals)


if __name__ == '__main__':
    raise SystemExit(main())
