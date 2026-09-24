"""Browse the same dated research catalog used by candidate discovery."""
import json
from html import escape
from pathlib import Path
from urllib.parse import urlencode

from officekit_research.discovery import catalog, manifest_digest


def section(found, limit=None):
    from officekit.runtime import research_library
    from officekit_research.taxonomy import label
    entries = sorted(found['entries'], key=lambda e: (e.get('as_of') or '', e['id']), reverse=True)
    visible = entries if limit is None else entries[:limit]
    out = ['<section id="saved-research"><h2>Existing research and tickers</h2>',
           '<p>Available now, without a new AI run. Original dates and prior verdicts are preserved; '
           'research alone does not approve or size an investment. Linked program pages show their own approvals and funding.</p>']
    if not entries:
        out.append('<p>No ticker research is available in this office yet.</p>')
    else:
        out.append('<p>' + str(len(entries)) + ' research entries available.</p><div style="overflow:auto"><table>'
                   '<tr><th>Tickers</th><th>Research and prior conclusion</th><th>Source date</th></tr>')
    shared = research_library()
    can_search = callable(getattr(shared, 'search', None))
    for e in visible:
        url = e['href']
        out.append('<tr><td><b>' + escape(', '.join(e['symbols'])) + '</b></td><td><a href="' + escape(url, quote=True) + '">'
                   + escape(e.get('title') or e['id'].replace('_', ' ')) + ' →</a><p>' + escape(e['summary']) + '</p><small>'
                   + escape(e.get('verdict') or e.get('standing') or 'Research thesis') + ' · '
                   + escape(label(e['kind'])) + '</small>')
        if can_search:
            # Search on demand. Counting every ticker's matches here downloads
            # all area indexes and scans the whole library before navigation.
            links = ['<a target="_top" href="/app/research?' + escape(urlencode({'q': s, 'match': 'symbol'}), quote=True)
                     + '">Search ' + escape(s) + ' source files</a>' for s in e['symbols'][:8]]
            if links:
                out.append('<p>' + ' · '.join(links) + '</p>')
        out.append('</td><td>' + escape(str(e.get('as_of') or 'Unrecorded')) + '</td></tr>')
    if entries:
        out.append('</table></div>')
    if len(visible) < len(entries):
        out.append('<p>Showing ' + str(len(visible)) + ' entries. <a href="/pages/research_catalog.html">Browse all saved research →</a></p>')
    for warning in found.get('warnings', []):
        out.append('<p class="warning">' + escape(warning) + '</p>')
    return ''.join(out) + '</section>'


def page(folder, answers, key=None):
    from officekit.render_research import page as research_page
    from officekit.commitments import revision
    def wrap(body, revision):
        return research_page('<p><a href="/research/scorecard">Research calibration by submitter and agent →</a></p>' + body, revision, title='Saved research' if key else 'Research catalog')
    found = catalog(folder, answers)
    if key is None:
        from officekit_research.taxonomy import render
        return wrap(render() + section(found), revision(answers))
    e = next((e for e in found['entries'] if e['href'] == '/pages/research_' + key + '.html'), None)
    if e is None:
        raise ValueError('Saved research not found in this office.')
    body = '<p><a href="/research/scorecard">Research calibration by submitter and agent</a></p><p><a href="/pages/research_catalog.html">← All saved research</a></p>' + section({'entries': [e]})
    source = e.get('source_href') or ''
    if source.startswith('/app/research/document?'):
        body += '<p><a target="_top" href="' + escape(source, quote=True) + '">Open original published research →</a></p>'
        return wrap(body, revision(answers))
    if e['kind'] == 'general':
        from officekit_research.general import load
        record = load(folder, e['id'])
    elif e['kind'] == 'office_court':
        from officekit_ai.court import load_adjudications
        from officekit.render_deck import render_deck
        record = next(r for r in load_adjudications(folder) if r['id'] == e['id'])
        return render_deck(record)
    elif e['kind'] == 'contextual_case':
        from officekit_research.cases import load_library
        from officekit.render_research import case_details
        record = next(b for b in load_library(folder)[0] if b['id'] == e['id'])
        return wrap(body + case_details(record), revision(answers))
    elif e['kind'] == 'strategy_pack':
        from officekit.strategy_packs import load_packs
        from officekit.render_deck import render_markdown_deck
        pack = next((p for p in load_packs([Path(folder) / 'strategies'])[0]
                     if p['id'] == e['id'] and manifest_digest(p) == e['manifest_sha256']), None)
        if pack and pack.get('deck_path'):
            return render_markdown_deck(pack['name'], Path(pack['deck_path']).read_text(encoding="utf-8"), author=pack['author'])
        record = e
    else:
        record = next(r for r in answers.get('desk_theses', []) if r['sid'] == e['id'])
    body += '<details open><summary>Retained research record</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere">' + escape(json.dumps(record, indent=2, ensure_ascii=False)) + '</pre></details>'
    return wrap(body, revision(answers))
