"""Plain-language risk inputs, funding timelines, research and position lineage."""
from datetime import date, timedelta
from html import escape as esc
import json
from urllib.parse import quote

from officekit.risk_planning import capacity, inputs, stress, FIELDS
from officekit.mandates import stamp_forms

CSS = '''
:root{color-scheme:dark;--bg:#0b0e12;--panel:#141a22;--line:#293441;--muted:#9ca9b8;--ink:#ecf0f5;--accent:#8fe4c4}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 system-ui,sans-serif}.wrap{max-width:1180px;margin:auto;padding:30px 24px 90px}
nav{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:30px}a{color:var(--accent)}h1{font-size:32px;line-height:1.2;margin:12px 0}h2{font-size:21px;margin:0 0 12px}h3{font-size:17px;margin:14px 0 8px}.muted,small{color:var(--muted)}.eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:.13em;color:var(--accent)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.card,section{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:22px;margin:18px 0}.grid .card{margin:0}.big{font-size:29px;font-weight:650;font-variant-numeric:tabular-nums}.warn{border-left:3px solid #efb86f;padding:10px 16px;background:#282117}.bad{color:#ffa399}.good{color:var(--accent)}
label{display:block;margin:10px 0;font-size:13px}input,select,textarea,button{font:inherit;color:inherit;border:1px solid #425061;border-radius:6px;background:#0d131b;padding:9px 10px}input:not([type=checkbox]),select,textarea{width:100%;margin-top:6px}input[type=checkbox]{margin-right:8px}textarea{min-height:95px}button{background:#295b4c;cursor:pointer;margin:10px 0}button:hover{background:#36735f}details{border-top:1px solid var(--line);padding:14px 0}summary{cursor:pointer;font-weight:600}.table{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:11px 9px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted)}.chips{display:flex;flex-wrap:wrap;gap:9px}.chip{font-size:12px;padding:4px 9px;border:1px solid var(--line);border-radius:20px}.metric{display:block;color:var(--muted);font-size:12px}.timeline{width:100%;height:180px}.field-help{display:block;font-size:12px;color:var(--muted)}.actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap}@media(max-width:620px){.wrap{padding:20px 14px}h1{font-size:26px}.big{font-size:24px}section,.card{padding:16px}}
'''


def money(n):
    return 'Unknown' if n is None else f'${n:,.0f}'


def wrap(title, body, revision=''):
    nav = ('<nav><a href="/pages/risk.html">Loss budget &amp; protection</a><a href="/pages/scenarios.html">Scenarios</a>'
           '<a href="/pages/scenario_research.html">Forecast research</a><a href="/pages/risk.html#shorts">Short positions</a>'
           '<a href="/pages/office.html">Office</a></nav>')
    return stamp_forms('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                       '<title>' + esc(title) + ' · Worker Placement</title><style>' + CSS + '</style></head><body><main class="wrap">' + nav + body + '</main></body></html>', revision)


def field(name, label, value='', *, lo=0, hi=None, step='any', kind='number', help='', required=False):
    return ('<label>' + esc(label) + '<input name="' + esc(name) + '" type="' + kind + '" value="' + esc(str(value)) + '"'
            + (f' min="{lo}" step="{step}"' if kind == 'number' else '') + (f' max="{hi}"' if hi is not None else '')
            + (' required' if required else '') + '></label>' + ('<span class="field-help">' + esc(help) + '</span>' if help else ''))


def overview(m, answers, findings=(), folder=None):
    cap = capacity(m)
    cfg, v = cap['inputs'], cap['inputs']['values']
    body = '<div class="eyebrow">Goals-based risk planning</div><h1>Protect the life your portfolio funds</h1><p class="muted">A recommended loss budget based on expenses, reliable income, payment dates and the goals you protect.</p>'
    body += '<div class="grid">' + ''.join('<div class="card"><span class="metric">' + label + '</span><div class="big">' + value + '</div><small>' + note + '</small></div>' for label, value, note in [
        ('Recommended loss limit', money(cap['recommended_loss']), f"{cap['recommended_loss_pct']:.1f}% of accessible investment assets · {cap['status']}"),
        ('Capital needed for protected plans', money(cap['required_capital']), f"{v['horizon_years']:g}-year horizon · zero real growth"),
        ('Accessible investment assets', money(cap['resources']['total']), 'Excludes home, private, restricted and pending assets'),
        ('Protected cash reserve', money(cap['protected_reserve']), f"{v['reserve_months']:g} months of essential spending or your larger cash floor")]) + '</div>'
    if cap['funding_gap']:
        body += '<p class="warn">The protected plan already exceeds modeled resources by ' + money(cap['funding_gap']) + '. The recommended additional loss limit is zero. Review spending, income, goal priorities and the horizon.</p>'
    body += '<section><h2>Why this limit</h2><p>' + esc(cap['method']) + '</p><p>Largest cumulative funding need: ' + esc(cap['binding_month'] or 'No dated need') + '. '
    body += ('Goals due then: ' + esc(', '.join(cap['binding_goals'])) if cap['binding_goals'] else 'Essential spending and scheduled obligations set the capacity.') + '</p>'
    body += '<p>Financial loss capacity before the buffer: <b>' + money(cap['financial_capacity']) + '</b>. The recommendation retains a ' + str(v['buffer_pct']) + '% buffer; a lower comfort limit can reduce it further.</p>'
    for gap in cfg['gaps']:
        body += '<p class="warn">' + esc(gap) + '</p>'
    body += '</section><section id="inputs"><h2>Your life, in ordinary terms</h2><p>Prefilled recommendations stay assumptions until you confirm them. These answers are shared with scenario and deployment planning.</p><form method="POST" action="/risk/policy"><div class="grid">'
    labels = {
        'annual_spending': 'How much must your household spend each year, including housing and recurring bills?',
        'annual_income': 'How much reliable after-tax income arrives each year?',
        'horizon_years': 'For how many years should this plan protect your spending?',
        'reserve_months': 'How many months of spending should stay protected?',
        'income_interruption_months': 'How long should the plan withstand income stopping?',
        'buffer_pct': 'How much of the remaining loss capacity should we keep as a safety buffer (%)?',
        'uninsured_loss': 'After insurance, how large an unexpected bill should the plan withstand?',
        'comfort_loss_pct': 'Would you prefer a lower investment loss limit (%)? Optional',
    }
    source = {r['key']: r['source'] for r in cfg['rows']}
    for key in FIELDS:
        value = v.get(key, '')
        if key in {'annual_income', 'uninsured_loss'} and key not in (m['d'].get('risk_policy') or {}):
            value = ''
        body += '<div>' + field(key, labels[key], value, lo=FIELDS[key][0], hi=FIELDS[key][1], help=source.get(key, 'Personal preference; cannot increase financial capacity')) + '</div>'
    body += '<div>' + field('income_end_date', 'When does that reliable income end?', v.get('income_end_date', ''), kind='date', help='Required to credit future income. Gross earnings or lifetime income value are not spendable cash.') + '</div></div>'
    body += '<h3>Which goals must remain funded?</h3><p class="muted">Protected goals enter the loss budget together. Flexible goals remain in your office, but may be deferred in this risk plan.</p>'
    for g in cfg['goals']:
        if g['kind'] == 'tax_efficiency':
            continue
        gid = g.get('id') or g['label']
        priority = v.get('goal_priority', {}).get(gid, 'protect')
        body += '<label>' + esc(g['label']) + '<select name="goal_' + esc(gid) + '"><option value="protect"' + (' selected' if priority == 'protect' else '') + '>Protect this goal</option><option value="flexible"' + (' selected' if priority == 'flexible' else '') + '>Can defer or reduce</option></select></label>'
    body += '<button type="submit">Save risk inputs</button></form><p><a href="/pages/goals.html">Add a goal</a> · <a href="/pages/capital.html">Correct payment amounts and dates</a></p></section>'
    base = stress(m, {})
    body += '<section><h2>What happens before an investment loss?</h2>' + timeline(base) + '</section>'
    body += short_section(m, answers, folder)
    body += '<section><h2>Priorities and actions</h2>'
    for f in findings:
        body += '<details><summary>' + esc(f['title']) + ' · ' + esc(f['severity']) + '</summary><p>' + esc(f['detail']) + '</p><p>' + esc(f['advice']) + '</p>'
        if f.get('action'):
            a = f['action']
            body += '<a href="' + esc(a.get('href') or '/pages/growth.html') + '">' + esc(a.get('label', 'Review')) + '</a>'
        body += '</details>'
    body += '</section>'
    return wrap('Risk management', body, m.get('_commitment_revision', ''))


def short_section(m, answers, folder=None):
    from officekit.short_exposure import inventory
    book = inventory(m)
    from officekit_research.discovery import catalog
    saved = catalog(folder, answers)['entries'] if folder and book['positions'] else []
    body = '<section id="shorts"><h2>Which positions could squeeze?</h2><p>Identified gross short exposure: <b>' + money(book['known_gross']) + '</b>. ' + esc(book['note']) + '</p>'
    if not book['positions']:
        body += '<p>No ticker-level shorts are identified in the supplied holdings.</p>'
    else:
        body += '<div class="table"><table><tr><th>Ticker / account</th><th>Sleeve and strategy</th><th>Gross short</th><th>Price +50% / +100%</th><th>Borrow cost</th></tr>'
        for p in book['positions']:
            links = []
            for sid in p['strategies']:
                title = (answers.get('strategy_decisions', {}).get(sid) or {}).get('title') or sid.replace('_', ' ')
                anchor = 'thesis-' if any(t.get('sid') == sid for t in answers.get('desk_theses', [])) else 'strat-'
                links.append('<a href="/pages/strategies.html#' + anchor + quote(sid, safe='') + '">' + esc(title) + '</a>')
            body += '<tr><td><b>' + esc(p['symbol']) + '</b><br>' + esc(p['account']) + '<br><small>' + esc(p['as_of']) + '</small></td><td>' + esc(p['sleeve']) + '<br>' + (' · '.join(links) or 'Strategy not recorded') + '</td><td>' + money(p['gross']) + '</td><td>' + money(p['squeeze_50']) + ' / ' + money(p['squeeze_100']) + '</td><td>' + money(p['annual_borrow_cost']) + '/yr</td></tr>'
            body += '<tr><td colspan="5"><details><summary>Thesis, evidence and collateral · ' + esc(p['symbol']) + '</summary><p>' + esc(p['thesis'] or 'No position thesis supplied; review the linked strategy.') + '</p><p>Source: ' + esc(str(p['source'])) + '. Margin terms: ' + esc(str(p['margin'] or 'Not supplied; no collateral-call amount inferred')) + '.</p><a href="/pages/research_catalog.html">Open ticker research catalog</a></details></td></tr>'
            for entry in saved:
                if p['symbol'].upper() in entry['symbols']:
                    body += '<tr><td colspan="5"><a href="' + esc(entry['href']) + '">' + esc(p['symbol'] + ' · ' + entry['kind'].replace('_', ' ') + ' · ' + (entry.get('as_of') or 'Date unknown')) + '</a></td></tr>'
        body += '</table></div>'
    for g in book['gaps']:
        body += '<p class="warn"><b>' + esc(g['sleeve']) + '</b>: ' + esc(g['detail']) + (' Unmapped gross exposure: ' + money(g['unmapped']) if g['unmapped'] is not None else '') + '</p>'
    return body + '<p><a href="/pages/imports.html">Import current positions or manager holdings</a></p></section>'


def timeline(result):
    rows = result['months']
    out = '<div class="chips">' + ''.join('<span class="chip">' + k + ': <b>' + esc(v or 'None in modeled period') + '</b></span>' for k, v in [
        ('Cash requires sales', result['cash_sale_month']), ('Protected reserve breached', result['first_reserve_breach']),
        ('Funding shortfall', result['first_shortfall'])]) + '</div>'
    if result['housing_payment_at_risk']:
        out += '<p class="warn">A mortgage payment shares a funding-shortfall month in ' + esc(result['housing_payment_at_risk']) + '. This flags payment funding risk; it does not predict foreclosure.</p>'
    if rows:
        values = [r['liquid_remaining'] for r in rows] + [0, result['reserve']]
        lo, hi = min(values), max(values)
        span = max(hi - lo, 1)
        y = lambda v: 155 - (v - lo) / span * 130
        points = ' '.join(f'{25+i*900/max(1,len(rows)-1):.1f},{y(r["liquid_remaining"]):.1f}' for i, r in enumerate(rows))
        out += '<svg class="timeline" viewBox="0 0 960 180" role="img" aria-label="Accessible funding remaining each month; dotted line is the protected reserve"><line x1="25" y1="' + str(y(result['reserve'])) + '" x2="925" y2="' + str(y(result['reserve'])) + '" stroke="#efb86f" stroke-dasharray="5 5"/><polyline points="' + points + '" fill="none" stroke="#8fe4c4" stroke-width="3"/><text x="25" y="175" fill="#9ca9b8">' + rows[0]['month'] + '</text><text x="845" y="175" fill="#9ca9b8">' + rows[-1]['month'] + '</text></svg>'
    out += '<p class="muted">' + esc(result['basis']) + '</p><details><summary>Monthly cash flows and the goals at risk</summary><div class="table"><table><tr><th>Month</th><th>Income / conditional receipt</th><th>Outflow</th><th>Cash remaining</th><th>Accessible assets remaining</th><th>Payments and goals due</th></tr>'
    for r in rows:
        out += '<tr><td>' + r['month'] + '</td><td>' + money(r['income']) + ' / ' + money(r['pending']) + '</td><td>' + money(r['outflow']) + '</td><td>' + money(r['cash_remaining']) + '</td><td class="' + ('bad' if r['funding_gap'] else '') + '">' + money(r['liquid_remaining']) + '</td><td>' + esc(', '.join(g['label'] for g in r['goals_due'] + r['payments'])) + '</td></tr>'
    out += '</table></div></details>'
    return out + ''.join('<p class="warn">' + esc(n) + '</p>' for n in result['notes'])


def scenarios(m, answers, folder=None):
    from officekit.render_scenarios import compute_results
    from officekit_research.scenario_forecasts import records, aggregate
    _, _, results = compute_results(m)
    cap = capacity(m)
    forecasts = records(folder) if folder else []
    body = '<div class="eyebrow">Scenario planner</div><h1>See what a shock changes</h1><p>Edit market severity and cash-flow interruptions independently of the probability. Scenarios can overlap; their probabilities are not added or normalized.</p><p>Recommended loss limit: <b>' + money(cap['recommended_loss']) + '</b> · <a href="/pages/risk.html#inputs">Review goals and inputs</a>.</p>'
    for r in results:
        sc = r['sc']; key = sc['key']
        flow = stress(m, sc, include_pending=True)
        mode = sc.get('probability_mode', 'stress')
        enabled = sc.get('enabled', True)
        groups = aggregate([f for f in forecasts if f['scenario']['scenario_key'] == key])
        selected = next((g for g in groups if g['contract_id'] == sc.get('forecast_contract_id')), None)
        prob = f"{selected['probability']:.1%} by {selected['resolve_by']}" if mode == 'research' and selected else f"{sc.get('p',0):.1%} assumption" if mode == 'manual' else 'Stress test · no probability assigned'
        body += '<section id="scenario-' + esc(key) + '"><h2>' + esc(sc['name']) + '</h2><p>' + esc(sc.get('desc', '')) + '</p><div class="chips"><span class="chip">' + esc(prob) + '</span><span class="chip">Portfolio mark change: ' + money(flow['portfolio_mark_change']) + '</span><span class="chip">' + ('Included in comparisons' if enabled else 'Excluded from comparisons; stress remains visible') + '</span></div>'
        if mode == 'research' and not selected:
            body += '<p class="warn">No compatible, reviewed forecast selected. No research probability is implied.</p>'
        body += '<details><summary>Edit this scenario</summary><form method="POST" action="/risk/scenario"><input type="hidden" name="scenario_key" value="' + esc(key) + '"><label><input name="enabled" type="checkbox" value="yes"' + (' checked' if enabled else '') + '>Include in comparisons</label><div class="grid">'
        body += '<label>Probability source<select name="probability_mode">' + ''.join('<option value="' + k + '"' + (' selected' if k == mode else '') + '>' + label + '</option>' for k, label in [('stress', 'Stress test only'), ('manual', 'My probability assumption'), ('research', 'Reviewed research forecast')]) + '</select></label>'
        body += field('probability_pct', 'My assumed probability (%)', number(sc.get('p')) * 100, hi=100)
        body += '<label>Research event<select name="forecast_contract_id"><option value="">Choose a compatible event and deadline</option>' + ''.join('<option value="' + esc(g['contract_id']) + '"' + (' selected' if selected == g else '') + '>' + esc(g['statement'][:140] + ' · ' + g['resolve_by']) + '</option>' for g in groups) + '</select></label>'
        for factor in m['factors']:
            body += field('shock_' + factor, factor + ' factor shock (%)', number(sc.get('shocks', {}).get(factor)) * 100, lo=-95, hi=500, help='Factor-model input; rate/inflation factors are sensitivities, not literal CPI or interest-rate changes.')
        for name, label, default, hi in [('horizon_months', 'Months to follow cash and payments', 24, 120), ('income_interruption_months', 'Months without reliable income', 12 if key == 'income_shock' else 0, 120), ('pending_delay_months', 'Delay incoming cash by months', 0, 120), ('annual_inflation_pct', 'Annual household spending inflation (%)', 0, 30), ('sale_haircut_pct', 'Extra discount when selling investments (%)', 2, 100), ('uninsured_loss', 'Unexpected bill after insurance ($)', 0, 1e12)]:
            body += field(name, label, sc.get(name, default), hi=hi)
        body += field('pending_date', 'Expected receipt date for this stress (optional)', sc.get('pending_date', ''), kind='date', help='Scenario assumption only; does not record a deposit.')
        body += '</div><button type="submit">Save scenario</button></form></details>'
        if flow['loss_of_accessible_assets'] > cap['recommended_loss']:
            body += '<p class="warn">Modeled accessible-asset loss exceeds the recommended loss limit by ' + money(flow['loss_of_accessible_assets'] - cap['recommended_loss']) + '.</p>'
        body += timeline(flow)
        from officekit.mitigations import OPT, OPT_STRATEGY
        body += '<details><summary>Responses to investigate</summary><p>These open the shared strategy research and review workflow.</p>'
        for option in sc.get('opts', []):
            if option in OPT and option in OPT_STRATEGY:
                body += '<form method="POST" action="/strategy/adopt"><input type="hidden" name="opt" value="' + esc(option) + '"><input type="hidden" name="scenario" value="' + esc(key) + '"><button type="submit">Investigate ' + esc(OPT[option][0]) + '</button></form>'
        body += '</details>'
        body += '<div class="actions"><a href="/pages/scenario_research.html#' + esc(key) + '">Research or update its probability →</a><a href="/pages/strategies.html">Compare mitigation strategies</a></div></section>'
    return wrap('Scenario planning', body, m.get('_commitment_revision', ''))


def research(m, answers, folder):
    from officekit.render_scenarios import applicable_scenarios
    from officekit_research.scenario_forecasts import records, aggregate
    from officekit.render_scorecard import ledger_revision
    rows = records(folder)
    token = ledger_revision(folder)
    body = '<div class="eyebrow">Shared research taxonomy · scenario forecasts</div><h1>Forecast research library</h1><p>Event probability, portfolio severity and household suitability are separate. Research and imported forecasts join the existing catalog and calibration ledger. Your office inputs stay private.</p><p><a href="/research/scorecard">Brier scores by submitter and agent</a> · <a href="/pages/research_catalog.html">All research</a></p>'
    body += '<p class="muted">Original calls remain immutable. Updates do not create extra scored trials; the first registered call per submitter, agent and event is the primary Brier observation. Imported identities are claims. Publication requires the existing evidence and release checks; saving here does not publish.</p>'
    scenario_list = applicable_scenarios(m)
    known = {sc['key'] for sc in scenario_list}
    scenario_list += [dict(key=key, name='Imported scenario: ' + key, imported_only=True)
                      for key in sorted({r['scenario']['scenario_key'] for r in rows} - known)]
    for sc in scenario_list:
        key = sc['key']; definition = answers.get('scenario_research', {}).get(key, {})
        body += '<section id="' + esc(key) + '"><h2>' + esc(sc['name']) + '</h2>'
        for group in aggregate([r for r in rows if r['scenario']['scenario_key'] == key]):
            body += '<p><b>' + f"{group['probability']:.1%}" + '</b> by ' + group['resolve_by'] + ' · ' + esc(group['statement']) + '</p><p class="muted">' + esc(group['method']) + f" {group['submissions']} submissions, {group['source_families']} declared source families; range {group['range'][0]:.1%}–{group['range'][1]:.1%}." + '</p>'
        if sc.get('imported_only'):
            body += '<p class="muted">This research is in the catalog. It is not yet attached to an office stress scenario.</p>'
        else:
            body += '<details><summary>Define an event and run evidence-led research</summary><p>Three calls: reference class, independent mechanism analysis, and adjudication. Uses your configured intelligence provider and retrieved public evidence. An event such as “AI trouble” needs a measurable definition before it can be scored.</p><form method="POST" action="/risk/forecast"><input type="hidden" name="scenario_key" value="' + esc(key) + '"><input type="hidden" name="ledger_revision" value="' + token + '">'
            for name, label in [('event_key', 'Stable event name (keep it for future updates)'), ('statement', 'What exactly will happen?'), ('resolution_criteria', 'Which observable facts and source will settle yes or no?'), ('symbols', 'Relevant tickers, separated by commas (optional)')]:
                value = definition.get(name, '')
                if isinstance(value, list): value = ', '.join(value)
                body += field(name, label, value, kind='text', required=name != 'symbols')
            body += field('event_start', 'Event window starts', definition.get('event_start', date.today().isoformat()), kind='date', required=True)
            body += field('resolve_by', 'Resolution deadline', definition.get('resolve_by', (date.today()+timedelta(days=365)).isoformat()), kind='date', required=True)
            body += '<button type="submit">Research probability</button></form></details>'
        matching = [r for r in rows if r['scenario']['scenario_key'] == key]
        for r in reversed(matching):
            meta = r['scenario']
            body += '<details id="forecast-' + r['id'] + '"><summary>' + f"{r['probability']:.1%}" + ' · ' + esc(r['agent']) + ' · ' + esc(r['recorded_at'][:10]) + (' · update' if r.get('supersedes') else ' · original') + '</summary><p>' + esc(r['statement']) + '</p><p><b>Resolution:</b> ' + esc(r['resolution_criteria']) + ' by ' + esc(r['resolve_by']) + '</p><p>' + esc(meta['summary']).replace('\n', '<br>') + '</p><p>Submitter: ' + esc(r['submitter']) + ' · ' + esc(r['model']) + ' · intelligence ' + esc(meta['intelligence']) + '.</p>'
            from officekit_research import predictions
            raw = next(item for item in predictions.load(folder) if item['id'] == r['id'])
            body += '<details><summary>Native record for private import into another office</summary><p>Contains claimed identity and evidence. Check redistribution rights before sharing.</p><textarea readonly aria-label="Native forecast JSON">' + esc(json.dumps(raw, ensure_ascii=False, indent=2)) + '</textarea></details>'
            if meta['condition']:
                body += '<p class="warn">Conditional estimate: ' + esc(meta['condition']) + '. Excluded from unconditional aggregates.</p>'
            for gap in meta['gaps']:
                body += '<p class="warn">' + esc(gap) + '</p>'
            for i, e in enumerate(meta['evidence']):
                body += '<details><summary>Evidence ' + str(i+1) + ' · ' + esc(e['fetched_at'][:10]) + '</summary><a href="' + esc(e['url']) + '" rel="noreferrer">Source</a><p>Digest ' + e['sha256'] + ' · ' + esc(e['visibility']) + '</p><pre style="white-space:pre-wrap">' + esc(e['text']) + '</pre></details>'
            body += '<p>' + ('Reviewed for aggregation' if meta['reviewed'] else 'Needs event and evidence review before aggregation') + '</p>'
            if not meta['reviewed']:
                body += '<form method="POST" action="/risk/forecast-review"><input type="hidden" name="forecast_id" value="' + r['id'] + '"><input type="hidden" name="ledger_revision" value="' + token + '"><label><input type="checkbox" name="reviewed" value="yes" required>I checked the event, deadline, evidence and conditions. Include this estimate in compatible aggregates.</label><button type="submit">Record review</button></form>'
            body += '</details>'
        if not matching:
            body += '<p class="muted">No explicit forecast yet. The stress preset does not imply a research probability.</p>'
        body += '</section>'
    body += '<section><h2>Import another agent’s forecast</h2><p>Paste a native scenario-prediction JSON record. Source digests and schema are checked; identity and claims still need review. Capture time is the import time so new claims cannot be backdated for scoring.</p><form method="POST" action="/risk/forecast-import"><input type="hidden" name="ledger_revision" value="' + token + '"><label>Forecast JSON<textarea name="forecast_json" required></textarea></label><button type="submit">Import for review</button></form></section>'
    return wrap('Scenario forecast research', body, m.get('_commitment_revision', ''))


from officekit.risk_planning import number


def comparisons(items):
    if not items:
        return '<p>No funded ticker basket to compare yet.</p>'
    out = '<section><h2>Does deployment preserve the household plan?</h2><p>Same loss-capacity and monthly funding model as Risk management. Figures describe these saved assumptions, not a safe-return promise. <a href="/pages/risk.html">Review household inputs</a>.</p>'
    for item in items:
        out += '<details><summary>' + esc(item['label']) + '</summary>'
        if item.get('error'):
            out += '<p class="warn">Comparison incomplete: ' + esc(item['error']) + '</p></details>'
            continue
        out += '<p>' + esc(item['basis']) + '</p><p>Recommended loss limit: ' + money(item['after']['recommended_loss']) + '. Protected-plan funding gap: ' + money(item['after']['funding_gap']) + '.</p>'
        out += '<div class="table"><table><tr><th>Scenario</th><th>Hold cash: loss / first funding gap</th><th>Deploy: loss / first funding gap</th><th>Loss budget</th></tr>'
        for row in item['scenarios']:
            out += '<tr><td>' + esc(row['name']) + '</td>'
            for phase in ('before', 'after'):
                r = row[phase]
                out += '<td>' + money(r['loss_of_accessible_assets']) + ' / ' + esc(r['first_shortfall'] or 'None in period') + '</td>'
            out += '<td>' + ('Exceeded' if row['exceeds_loss_budget'] else 'Within modeled limit') + '</td></tr>'
        out += '</table></div><details><summary>Deployment cash-flow detail</summary>'
        for row in item['scenarios']:
            out += '<h3>' + esc(row['name']) + '</h3>' + timeline(row['after'])
        out += '</details>' + ''.join('<p class="muted">' + esc(g) + '</p>' for g in dict.fromkeys(item['gaps'] + item['after']['inputs']['gaps'])) + '</details>'
    return out + '</section>'
