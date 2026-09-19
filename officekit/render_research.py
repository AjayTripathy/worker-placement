"""Shared office UI for explicit, reviewable contextual research exchange."""
import json
from html import escape


def esc(value):
    return escape(str(value), quote=True)


def label(value):
    if isinstance(value, list):
        return ', '.join(label(v) for v in value)
    return {'under_2y': 'Under 2 years', '2_to_7y': '2–7 years', 'over_7y': 'Over 7 years',
            'deploy_powder': 'Deploy available capital', 'cash_mgmt': 'Cash management',
            'non_US': 'Outside the US'}.get(str(value), str(value).replace('_', ' '))


def case_details(bundle):
    c = bundle["case"]
    ctx = c["context"]
    rows = ''.join('<dt>' + esc(k.replace('_', ' ')) + '</dt><dd>' + esc(label(v)) + '</dd>' for k, v in ctx.items())
    return (f'<details id="case-{esc(bundle["id"])}"><summary>{esc(c["subject"]["symbol"])} · {esc(label(ctx["goal_types"]))} · {esc(label(ctx["life_stage"]))}</summary>'
            '<p class="muted">Historical case. Contributor review does not independently verify its claims.</p><dl>' + rows + '</dl>'
            '<p>Historical court: ' + esc(c['court']['verdict']) + ' · ' + esc(c['as_of'][:10]) + '</p>'
            '<h3>Question investigated</h3><p>' + esc(c['investigation']['question']) + '</p>'
            '<h3>Reasoning in that context</h3><p>' + esc(c['investigation']['thesis']) + '</p><p>' + esc(c['court']['rationale']) + '</p>'
            '<p>Factors investigated: ' + esc(label(c['investigation']['factors'])) + '. These are research topics, not measured exposures.</p>'
            '<h3>Alternatives considered</h3><ul>' + ''.join('<li>' + esc(s) + '</li>' for s in c['investigation']['alternatives']) + '</ul>'
            '<h3>Open questions</h3><ul>' + ''.join('<li>' + esc(s) + '</li>' for s in c['court']['unverified_items']) + '</ul>'
            '<p>Recorded decision: ' + esc(c['decision']['status']) + '. Execution unconfirmed; user decision reason not recorded.</p>'
            '<p class="muted">Case <code>' + esc(bundle['id']) + '</code></p></details>')


def reuse_section(p):
    from officekit_research.cases import proposal_retrievals
    retrievals = proposal_retrievals(p)
    if not any(r for r in retrievals):
        return ''
    matches = {m['id']: m for r in retrievals for m in r.get('matches', [])}
    rejects = {r['id']: r for found in retrievals for r in found.get('rejected', [])}
    errors = {e['file']: e for found in retrievals for e in found.get('errors', [])}
    reused = sum(len(pack.get('reuse', {})) for pack in p.get('evidence', {}).values())
    body = '<section class="slide"><div class="eyebrow">Shared investigation</div><h2>Research reused for this office</h2>'
    body += f'<p>{len(matches)} prior cases considered · {reused} public source sections reused. This office receives a fresh court and Risk Officer review.</p>'
    if (p.get('research_reuse') or {}).get('mode') == 'evidence_only':
        body += '<p class="note">Evidence-only evaluation: prior case arguments were withheld from model stages. Source lineage remains available below.</p>'
    if not matches:
        body += '<p class="muted">No applicable shared case was found. Research proceeds from this office and the available sources.</p>'
    for m in matches.values():
        body += case_details(m['bundle'])
        if m['differences']:
            body += '<p><b>Differences to account for</b></p><ul>' + ''.join('<li>' + esc(d['field'].replace('_', ' ')) + ': ' + esc(label(d['prior'])) + ' → ' + esc(label(d['current'])) + '</li>' for d in m['differences']) + '</ul>'
    if rejects:
        body += '<details><summary>Cases excluded from this review</summary><ul>' + ''.join('<li>' + esc(r['symbol']) + ': ' + esc('; '.join(r['reasons'])) + '</li>' for r in rejects.values()) + '</ul></details>'
    if errors:
        body += '<p class="warning">' + str(len(errors)) + ' invalid research files were excluded. Review the library before importing them again.</p>'
    return body + '<p><a href="/research">Manage shared research</a></p></section>'


def page(body, revision):
    from officekit.serve import STYLE
    from officekit.mandates import stamp_forms
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Contextual research · Worker Placement</title><style>' + STYLE +
            'a{color:var(--emerald)}textarea{width:100%;font:13px/1.5 monospace}details{margin:20px 0;padding:16px;border:1px solid #33404c;border-radius:8px}summary{cursor:pointer}dl{display:grid;grid-template-columns:140px minmax(0,1fr);gap:8px 16px}dt{color:var(--dim);font-size:12px;text-transform:capitalize}dd{margin:0}code{overflow-wrap:anywhere}button{margin-top:8px}@media(max-width:500px){dl{grid-template-columns:110px minmax(0,1fr)}} </style></head>'
            '<body><main class="wrap"><p><a href="/pages/strategies.html">← Strategies</a></p><h1>Shared research</h1>' + body + '</main></body></html>')
    return stamp_forms(html, revision)


def library(folder, revision):
    from officekit_research.cases import load_library
    from officekit.strategy_proposals import list_proposals
    bundles, errors = load_library(folder)
    body = '<p>Reuse an investigation while preserving its original goals, investor context, arguments and source dates. Your office makes its own decision.</p>'
    body += '<p class="note">Pilot exchange uses reviewed JSON files. These controls do not publish anything online.</p>'
    body += '<h2>Available cases</h2>' + (''.join(case_details(b) for b in bundles) or '<p>No shared cases imported yet.</p>')
    if errors:
        body += '<p role="alert">' + str(len(errors)) + ' invalid case files were excluded.</p>'
    body += '<details><summary>Import a reviewed case</summary><form method="POST" action="/research/import" enctype="multipart/form-data"><label for="bundle_file">Choose a research case file</label><input id="bundle_file" name="bundle_file" type="file" accept=".json,application/json"><details><summary>Or paste case JSON</summary><textarea aria-label="Reviewed case JSON" name="bundle" rows="8" maxlength="524288"></textarea></details><p>Imported claims remain attributed to their contributor. Importing does not adopt a strategy or place an order.</p><button>Import case</button></form></details>'
    body += '<h2>Contribute an investigation</h2><p>Prepare a private draft, check the anonymized context and arguments, and review permission to share any source material.</p>'
    count = 0
    for p in list_proposals(folder):
        if p['status'] in {'queued', 'running'}:
            continue
        completed = {c['symbol'] for c in p.get('courts', [])}
        for candidate in p.get('candidates', []):
            if candidate['symbol'] not in completed or candidate['instrument'] not in {'stock', 'etf', 'options'}:
                continue
            count += 1
            body += (f'<form method="POST" action="/research/prepare"><input type="hidden" name="pid" value="{esc(p["id"])}"><input type="hidden" name="symbol" value="{esc(candidate["symbol"])}">'
                     f'<p>{esc(p["brief"]["title"])} · {esc(candidate["symbol"])} <button>Prepare review draft</button></p></form>')
    if not count:
        body += '<p>A completed candidate court is needed before preparing a contribution.</p>'
    return page(body, revision)


def draft_page(draft, revision):
    c = draft['case']
    preview = case_details({'id': 'draft', 'case': c})
    preview += '<h3>Full court arguments</h3>' + ''.join('<details><summary>' + esc(role.upper()) + ' bench</summary><p style="white-space:pre-wrap">' + esc(brief['case']) + '</p></details>' for role, brief in c['court']['briefs'].items())
    preview += '<h3>Source material included</h3>' + ''.join('<details><summary>' + esc(e['section']) + ' · ' + esc(e['source_url']) + '</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere">' + esc(json.dumps(e['data'], indent=2)) + '</pre></details>' for e in c['evidence'])
    body = ('<p><a href="/research">← Research library</a></p><h2>Review the public case</h2>'
            '<p>This is a private draft. Check every argument for identifying details and preserve the circumstances that drove the conclusion. Automatic scrubbing cannot establish anonymity.</p>'
            + preview + '<form method="POST" action="/research/approve"><details><summary>Edit the case or inspect every field</summary><label for="projection">Case projection (editable JSON)</label>'
            '<textarea id="projection" name="projection" rows="24" maxlength="524288" required>' + esc(json.dumps(draft['case'], indent=2, ensure_ascii=False)) + '</textarea>'
            '</details><details><summary>Permit reuse of source evidence</summary>'
            '<label for="grants">Optional source reuse permissions (JSON list)</label><textarea id="grants" name="grants" rows="5">[]</textarea>'
            '<p>Leave this empty for context-only sharing. To permit source reuse, review the source content and specify its section, permission basis and expiry. For example: '
            '<code>[{"section":"fund_profile","basis":"original_summary","valid_until":"YYYY-MM-DD"}]</code>. A source expires within 30 days of collection. Use original_summary only after replacing source text with your own accurate summary; source dates must remain unchanged.</p></details>'
            '<label><input type="checkbox" name="reviewed" value="yes" required> I reviewed this exact projection for identifying details and permission to share its contents.</label>'
            '<p><button>Download reviewed case</button></p></form><p>Import the downloaded file into another office to exchange this research. Nothing is automatically published.</p>')
    return page(body, revision)
