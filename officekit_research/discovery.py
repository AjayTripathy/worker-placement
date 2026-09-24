"""Bounded candidate discovery from existing research; never an admission path.

Keep original dates, IDs, dissent and authors. Historical research suggests what
to investigate; it never substitutes for the general or office suitability court.
"""
from datetime import date
import re
from pathlib import Path

from officekit.strategy_proposals import digest, now


def reference_key(kind, identity, variant=None):
    return digest([kind, str(identity)] + ([variant] if variant else []))


def manifest_digest(pack):
    return digest({k: v for k, v in pack.items() if k not in
                   {'deck_path', 'pack_dir', 'source', 'source_sha256', 'source_href'}})


def catalog(folder, answers):
    """One derived catalog for browsing and AI discovery; no model calls or writes."""
    from officekit_research import general
    from officekit_ai.court import load_adjudications
    from officekit.strategy_packs import load_packs
    from officekit.runtime import research_library
    entries, warnings = [], []
    today = date.today().isoformat()

    def add(kind, identity, symbols, as_of, summary, **meta):
        symbols = [s.upper() for s in symbols if isinstance(s, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.^-]{0,14}', s)]
        if not identity or (not symbols and kind != 'office_program') or (as_of and str(as_of)[:10] > today):
            return
        key = reference_key(kind, identity, meta.get('manifest_sha256'))
        entries.append({'kind': kind, 'id': str(identity), 'symbols': symbols[:30],
                        'as_of': as_of or None, 'summary': str(summary)[:1400],
                        'href': '/pages/research_' + key + '.html', **meta})

    for r in general.load_all(folder):
        if r['subject']['instrument'] not in {'stock', 'etf'}:
            continue
        a = r['assessment']
        add('general', r['id'], [r['subject']['symbol']], r['as_of'], a['summary'],
            title=r['subject']['symbol'] + ' · security research',
            standing=a['standing'], risks=a['risks'][:4], gaps=a['unverified_items'][:4],
            factors=a['factor_profile'], attribution=general.provenance(folder, r['id']))
    for r in load_adjudications(folder):
        if r.get('subject_kind', 'security') != 'security':
            continue
        add('office_court', r.get('id'), [r.get('symbol')], r.get('date'), r.get('rationale', ''),
            title=str(r.get('symbol', '')) + ' · ' + str(r.get('strategy') or 'office review').replace('_', ' '),
            strategy=r.get('strategy'), verdict=r.get('verdict'), gaps=r.get('unverified_items', [])[:4])
    from officekit_research.cases import load_library
    bundles, problems = load_library(folder)
    if problems:
        warnings.append(f'{len(problems)} invalid research cases excluded.')
    for b in bundles:
        c = b['case']
        if c['provenance']['kind'] == 'evaluation_scenario' or b['review']['reviewed_at'][:10] > today:
            continue
        if c['subject']['instrument'] in {'stock', 'etf'}:
            add('contextual_case', b['id'], [c['subject']['symbol']], c['as_of'],
                c['investigation']['thesis'], verdict=c['court']['verdict'],
                title=c['investigation']['question'][:160],
                strategy=c['context']['strategy'], gaps=c['court']['unverified_items'][:4],
                author=b['review'].get('contributor') or 'Anonymous contributor')
    for r in answers.get('desk_theses') or []:
        add('imported_thesis', r.get('sid'), [p.get('symbol') for p in r.get('positions', [])],
            r.get('court_date'), r.get('thesis', ''), verdict=r.get('verdict'), strategy=r.get('sid'),
            title=r.get('label') or str(r.get('sid', '')).replace('_', ' '))
    packs, problems = load_packs([Path(folder) / 'strategies'])
    if problems:
        warnings.append(f'{len(problems)} invalid strategy packs excluded.')
    library = research_library()
    if library is not None:
        try:
            packs += library.strategy_packs()
        except Exception:
            warnings.append('The hosted research library could not be loaded; inspect it before relying on coverage.')
    for p in packs:
        add('strategy_pack', p['id'], p.get('positions', []), p.get('as_of'), p['thesis'],
            title=p.get('name') or p['id'].replace('_', ' '),
            author=p['author'], bucket=p['bucket'], source=p.get('source', 'Installed or office strategy pack'),
            source_href=p.get('source_href'),
            manifest_sha256=manifest_digest(p),
            source_sha256=p.get('source_sha256') or digest({k: v for k, v in p.items() if k not in {'deck_path', 'pack_dir'}}))

    # Private program mandates join the same discovery path. Their household
    # policy/approval data never enters a general-research publication record.
    from officekit.beta_programs import programs, basket
    for p in programs(answers).values():
        snap = p.get('benchmark_snapshot') or {}
        selected = basket(p, {'current': 0, 'pending': 0})['rows']
        add('office_program', p['id'], [r['symbol'] for r in selected[:30]],
            snap.get('as_of'), 'Long-only beta/TLH mandate. Review funding, approval and current readiness on the program page.',
            title=p['label'], strategy='direct_index', href='/pages/beta_programs.html#program-' + p['id'])
    # Deduplicate installed and published copies of the same manifest. Prefer
    # the published copy because it has an immutable, authenticated source URL.
    entries = list({e['href']: e for e in entries}.values())
    return {'entries': entries, 'warnings': warnings}


def inventory(folder, proposal):
    found = catalog(folder, proposal['snapshot']['answers'])
    entries, warnings = found['entries'], found['warnings']

    seeds = set(proposal['brief']['candidates'])
    words = lambda s: set(re.findall(r'[a-z][a-z0-9]{2,}', str(s).lower())) - {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'research', 'strategy', 'office'}
    terms = words(' '.join(str(proposal['brief'].get(k, '')) for k in ('title', 'thesis', 'request')))
    entries.sort(key=lambda e: (bool(seeds.intersection(e['symbols'])),
                               e.get('strategy') == proposal['strategy_id'],
                               len(terms.intersection(words(e['summary'] + ' ' + e['id']))),
                               e['as_of'] or '', e['id']), reverse=True)
    selected, seen, used = [], set(), 0
    for e in entries:
        key = e['href']
        size = len(str(e))
        if key in seen or len(selected) >= 32 or used + size > 30000:
            continue
        selected.append(e)
        seen.add(key)
        used += size
    return {'captured_at': now(), 'entries': selected, 'sha256': digest(selected),
            'available': len(entries), 'omitted': len(entries) - len(selected), 'warnings': warnings,
            'use': 'Historical candidate leads, not current evidence or an approval. Refresh sources and run suitability.'}
