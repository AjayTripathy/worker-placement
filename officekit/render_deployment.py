"""The Home entrypoint and saved result for incoming-capital research."""
from html import escape
from officekit.deployment import funding, sources, latest, href
from officekit.mandates import stamp_forms
from officekit.capital_planning import needs_refresh


def money(value):
    return f'${value:,.2f}'


def link(source, proposals=(), revision=None):
    p = latest(proposals, source)
    stale = p and ((revision and p['snapshot_revision'] != revision) or needs_refresh(p))
    tickers = ', '.join(a['symbol'] for a in (p or {}).get('basket', []))
    status = 'Refresh needed' if stale else ('Tickers: ' + tickers if tickers else (p or {}).get('stage', 'Choose investments and dollar allocations'))
    return '<a class="deployment-link" href="' + href(source['id']) + '">Open deployment strategy →</a><p class="note">' + escape(status) + '</p>'


def render(model, proposals=(), revision=None, exclude=()):
    """Linked inflows on Home/Capital; planning happens on a dedicated page."""
    selected = [s for s in sources(model) if s['id'] not in exclude]
    if not selected:
        return ''
    out = ['<section id="deploy-plan"><h2>Deployment strategies</h2>']
    for s in selected:
        out.append('<article class="commit-card"><h3>' + escape(s['label']) + '</h3><p>' + money(s['gross']) +
                   ' expected · ' + money(s['pending']) + ' pending · ' + escape(s['status']) + '</p>' + link(s, proposals, revision) + '</article>')
    out.append('</section>')
    return ''.join(out)


def page(model, source, proposals=(), revision=None, research=None):
    from officekit.render_capital import CSS
    from officekit.render_saved_research import section
    from officekit.render_beta import section as beta_section
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Deployment strategy · ' + escape(source['label']) + '</title><style>' + CSS +
            '.liqrow{display:flex;justify-content:space-between;gap:18px;padding:10px 0;border-bottom:1px solid #28313c}'
            '.warning{border-left:3px solid #d9a441;padding:12px}.note{color:#9aa4b0}</style></head><body><main class="wrap">'
            '<nav class="jump"><a href="/pages/office.html">← Home</a><a href="/pages/capital.html#inflows">Incoming money</a>'
            '<a href="/pages/strategies.html#deploy_powder">Strategies</a></nav>' +
            beta_section(model['d'], model, source['id'], revision) + _body(model, source, proposals, revision) +
            (section(research, limit=32) if research is not None else '') + '</main></body></html>')


def _body(model, source, proposals=(), revision=None, endpoint='/strategy/deploy'):
    from officekit.beta_programs import remaining_funding
    f = remaining_funding(model, funding(model, source['id']), source['id'])
    p = latest(proposals, source)
    stale = bool(p and ((revision and p['snapshot_revision'] != revision) or needs_refresh(p)))
    rows = [('Total expected proceeds', source['gross']), ('Recorded net deposits', source['cash_received']),
            ('Still pending', f['pending_gross']), ('Tax reserved against pending proceeds', f['pending_tax']),
            ('Cash reserved for unfunded commitments', f['commitment_reserve']),
            ('Available for additional proposals from received proceeds', f['current_budget']), ('Available for additional proposals after further receipts', f['contingent_budget'])]
    extra = [('Cash floor target', f.get('liquidity_floor', 0)),
             ('Pending proceeds retained for the cash floor', f.get('liquidity_reserve', 0)),
             ('Income-period bills retained from received proceeds', f.get('income_reserve_current', 0)),
             ('Income-period bills retained from pending proceeds', f.get('income_reserve_pending', 0))]
    rows[-2:-2] = [(label, value) for label, value in extra if value]
    if f['linked_programs']:
        rows[-2:-2] = [('Received proceeds assigned to beta programs', f['program_reserved_current']),
                       ('Pending proceeds assigned to beta programs (including retained cash)', f['program_reserved_pending'])]
    out = ['<section id="deploy-plan"><div class="eyebrow">Deployment strategy</div><h1>' + escape(source['label']) + '</h1>',
           '<p>The Capital Planner connects goals, existing strategies, disaster scenarios and saved ticker research '
           'to a plan with dollar amounts and conditions. Security courts and the Risk Officer review the proposed investments.</p>',
           '<div class="deploycmp">' + ''.join(f'<div class="liqrow"><span>{label}</span><b>{money(value)}</b></div>' for label, value in rows) + '</div>',
           '<p class="note">' + escape(f['sizing_basis']) + '</p>']
    for gap in f.get('blocking_gaps', []):
        out.append('<p class="warning">' + escape(gap) + '</p>')
    if f.get('income_expense_shortfall'):
        out.append('<p class="warning">Income-period bills exceed deployable proceeds by ' + money(f['income_expense_shortfall']) + '.</p>')
    if p:
        href = '/pages/proposal_' + p['id'] + '.html'
        out.append('<p><a href="' + escape(href, quote=True) + '">Open deployment proposal →</a> · ' + escape(p['stage']) + '</p>')
        if stale:
            out.append('<p class="warning">The office changed or the planning inputs were updated since this plan was prepared. Build a fresh plan to update its allocations.</p>')
        elif p.get('basket'):
            out.append('<div style="overflow:auto"><table><tr><th>Ticker</th><th>From received proceeds</th><th>After further receipts</th><th>Reason and conditions</th></tr>')
            for a in p['basket']:
                out.append('<tr><td><b>' + escape(a['symbol']) + '</b></td><td>' + money(a['amount']) + '</td><td>' + money(a['contingent_amount']) + '</td><td>' + escape(a['rationale']) + '<ul>' + ''.join('<li>' + escape(c) + '</li>' for c in a['conditions']) + '</ul></td></tr>')
            allocated = sum(a['contingent_amount'] for a in p['basket'])
            current_allocated = sum(a['amount'] for a in p['basket'])
            out.append('<tr><td>Cash retained</td><td>' + money(max(0, f['current_budget'] - current_allocated)) + '</td><td>' + money(max(0, f['contingent_budget'] - allocated)) + '</td><td>Unallocated proceeds after reserves</td></tr></table></div>')
        elif p['status'] in {'queued', 'running'}:
            out.append('<p>Research is running. Open the proposal to follow progress and see allocations as they complete.</p>')
        elif p['status'] == 'awaiting_key':
            out.append('<p>Connect an AI key in <a href="/settings">Office settings</a>, then resume the saved proposal.</p>')
        if p.get('errors'):
            out.append('<p class="warning">' + escape(' '.join(p['errors'])) + '</p>')
        inventory = p.get('research_inventory') or {}
        if inventory:
            out.append('<p>Candidate selection considered ' + str(len(inventory.get('entries', []))) + ' saved research entries. '
                       'Sources, original dates and prior verdicts are listed in the proposal.</p>')
    if (not p or stale) and f['proposal_ceiling'] > 0:
        out.append('<form method="POST" action="' + escape(endpoint, quote=True) + '"><input type="hidden" name="inflow_id" value="' + escape(source['id'], quote=True) + '"><button>' +
                   ('Build a fresh ticker plan' if p else 'Build ticker-level deployment plan') + '</button></form>'
                   '<p class="note">Runs research and court review using your configured AI provider.</p>')
    elif f['linked_programs'] and f['proposal_ceiling'] <= 0:
        out.append('<p>This source is assigned to the linked beta program above. Open its constituents and harvesting overlay, or edit its funding share to make room for another strategy.</p>')
    out.append('<p><a href="/pages/growth.html">Review allocation targets</a> · <a href="/research">Saved research cases</a></p></section>')
    return stamp_forms(''.join(out), revision)
