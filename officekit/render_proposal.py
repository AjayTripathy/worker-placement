"""A readable, printable pitch deck with visible research and court lineage."""
from html import escape
from urllib.parse import urlparse


def esc(v):
    return escape(str(v if v is not None else ""), quote=True)


def money(v):
    return f"${v:,.2f}"


def bullets(items):
    return '<ul>' + ''.join('<li>' + esc(x) + '</li>' for x in items) + '</ul>' if items else ''


def render_proposal(p, revision=None):
    from officekit.capital_planning import needs_refresh
    outdated = needs_refresh(p)
    b, status = p["brief"], p["status"]
    busy = status in {"queued", "running"}
    refresh = '<meta http-equiv="refresh" content="8">' if busy else ''
    pitch, risk, funding = p.get("pitch") or {}, p.get("risk") or {}, p.get("funding") or {}
    P = [f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(b['title'])} · Strategy proposal</title>{refresh}<style>
:root{{--bg:#0b0e12;--panel:#141a20;--line:#2b3540;--ink:#e8eef3;--dim:#9aa9b7;--green:#49d6a3;--amber:#edbf76}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
main{{max-width:1120px;margin:auto;padding:30px 28px 90px}}a{{color:var(--green)}}nav,.actions{{display:flex;gap:16px;align-items:center;flex-wrap:wrap}}nav{{justify-content:space-between;margin-bottom:36px}}
button{{font-family:inherit;font-size:13px;font-weight:600;background:var(--green);color:#071b13;border:0;border-radius:8px;padding:11px 18px;cursor:pointer}}button.secondary{{background:var(--panel);color:var(--ink);border:1px solid var(--line)}}
.eyebrow{{font-size:11px;text-transform:uppercase;letter-spacing:.16em;color:var(--green)}}h1{{font-size:clamp(30px,5vw,48px);line-height:1.15;letter-spacing:-.035em;max-width:900px;margin:16px 0}}h2{{font-size:24px;line-height:1.25;margin:10px 0 18px}}h3{{font-size:17px}}p{{max-width:82ch}}.lead{{font-size:19px;color:#c8d4de}}.muted,small{{color:var(--dim)}}.badge{{display:inline-block;padding:5px 12px;border:1px solid var(--line);border-radius:20px;font-size:12px;text-transform:capitalize}}
.slide{{margin:28px 0;padding:30px;border:1px solid var(--line);border-radius:16px;background:var(--panel);break-inside:avoid}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}.metric{{padding:16px;border-left:2px solid var(--green)}}.metric b{{display:block;font-size:26px;font-variant-numeric:tabular-nums}}.metric small{{font-size:12px}}
.warning{{border-left:3px solid var(--amber);padding:10px 16px;background:#231f17;color:#f0d9b6}}.table{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:14px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{font-size:11px;color:var(--dim);text-transform:uppercase}}td b{{font-size:18px}}details{{margin:16px 0;border-top:1px solid var(--line);padding-top:14px}}summary{{cursor:pointer;font-weight:600}}li{{margin:8px 0}}.prose{{white-space:pre-wrap;overflow-wrap:anywhere}}.sources a{{overflow-wrap:anywhere}}form{{margin:0}}.steps{{display:flex;gap:8px;flex-wrap:wrap}}.steps span{{padding:5px 10px;background:var(--bg);border-radius:5px;font-size:12px}}textarea{{width:100%;padding:12px;background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:8px;font:inherit}}
@media(max-width:680px){{main{{padding:20px 16px 60px}}.slide{{padding:20px 16px}}.grid{{grid-template-columns:1fr}}nav{{margin-bottom:24px}}td,th{{padding:10px 8px}}}}
@media print{{:root{{--bg:white;--panel:white;--ink:#14222d;--dim:#465766;--line:#ccd3d8;--green:#176b4c}}nav,.actions,.progress,.decision{{display:none}}main{{padding:0;max-width:none}}.slide{{border:0;border-radius:0;break-before:page;padding:20px 0;margin:0}}a{{color:inherit}}details{{break-inside:auto}}h1{{font-size:38px}}}}
</style></head><body><main><nav><a href="/pages/strategies.html">← Strategies</a><button class="secondary" onclick="document.querySelectorAll('details').forEach(d=>d.open=true);window.print()">Print / save pitch deck</button></nav>
<header><div class="eyebrow">Strategy proposal · {esc(p['source'])}</div><h1>{esc(b['title'])}</h1>
<p class="lead">{esc(pitch.get('headline') or b['thesis'])}</p><span class="badge">{esc(status.replace('_',' '))}</span>
<p class="muted">Source: {esc(p['source_ref'])} · Office snapshot {esc(p['snapshot']['data'].get('as_of',''))} · Created {esc(p['created_at'][:10])}</p></header>''']
    P.append('<div class="steps"><span>1 · SignalOS research</span><span>2 · RED / BLUE court</span><span>3 · Risk Officer</span><span>4 · Pitch & implementation</span></div>')
    if outdated:
        P.append('<p class="warning">This saved proposal predates the current capital-planning inputs. Its allocations are historical; build a fresh revision before adopting.</p>')
    if p.get('deployment_source'):
        from officekit.deployment import href
        P.append('<p><a href="' + href(p['deployment_source']['id']) + '">← Deployment strategy for ' + esc(p['deployment_source']['label']) + '</a></p>')
    if status == 'awaiting_key':
        P.append('<section class="slide progress"><h2>Ready for an AI agent key</h2><p>Your strategy brief is saved. SignalOS research, the courts, and the AI Risk Officer can run once an agent key is connected. No research has been billed or investments selected.</p></section>')
    if busy or p.get('errors'):
        P.append(f'<section class="slide progress"><div class="eyebrow">Review progress</div><h2>{esc(p["stage"])}</h2>')
        if busy:
            P.append('<p>Research and independent reviews run in the background. This page refreshes as results arrive. Up to three candidates are reviewed per proposal.</p>')
        P.append(bullets(p.get('errors', [])))
        P.append(f'<form action="/strategy/proposal/retry" method="POST"><input type="hidden" name="pid" value="{esc(p["id"])}"><button class="secondary">Resume / retry review</button></form></section>')
    P.append(f'<section class="slide"><div class="eyebrow">01 / Investment case</div><h2>The investment case</h2><p>{esc(pitch.get("thesis") or (p.get("research") or {}).get("thesis") or b["thesis"])}</p>')
    if b.get('request'):
        P.append(f'<p><b>Your brief:</b> {esc(b["request"])}</p>')
    if pitch.get('why_now'):
        P.append(f'<h3>Why now</h3><p>{esc(pitch["why_now"])}</p>')
    if not p.get('research'):
        seeds = ', '.join(b['candidates']) or 'Provider terms and program design'
        P.append(f'<p class="muted">Starting research candidates: {esc(seeds)}. Selection and sizing follow court and risk review.</p>')
    P.append(bullets((p.get('research') or {}).get('assumptions', [])) + '</section>')
    plan = p.get('capital_plan') or {}
    if plan:
        P.append('<section class="slide"><h2>Capital Planner · inputs behind this plan</h2><p>Saved as of ' + esc(plan['as_of']) +
                 '. Goals, strategy decisions and disaster assumptions are reviewed with the same ticker research catalog used by new strategies.</p>')
        P.append('<h3>Goals</h3>' + bullets([g['goal'].get('label', g['goal']['kind']) + ' · ' + g['baseline']['status'] for g in plan['goals']]))
        from officekit.render_strategies import STRATEGY_LIB
        P.append('<h3>Existing strategies</h3>' + bullets([(d.get('title') or STRATEGY_LIB.get(sid, {}).get('title') or sid.replace('_', ' ').title()) +
                 ' · ' + d.get('status', 'unrecorded') for sid, d in plan['strategies'].items()]))
        P.append('<h3>Disaster planning</h3>')
        for sc in plan['disasters']:
            P.append('<details><summary>' + esc(sc['name']) + '</summary><p>' + esc(sc.get('description') or '') +
                     '</p><p>Existing portfolio net worth after this modeled scenario: ' + money(sc['estimated_net_worth_after']) +
                     '.</p>' + bullets(sc['tripwires']) + '</details>')
        P.append(bullets(plan['limitations']) + '</section>')
    if p.get('charitable_goals'):
        from officekit.charitable import VEHICLES, FUNDING
        P.append('<section class="slide"><h2>Charitable goals behind this strategy</h2><p>Giving commitments and reviewed tax scenarios from this proposal’s office snapshot.</p>')
        for giving in p['charitable_goals']:
            P.append('<h3><a href="/pages/goal_' + esc(giving['goal_id']) + '.html">' + esc(giving['label']) + '</a></h3><p>' +
                     money(giving['amount']) + ' · ' + esc(giving.get('date') or 'Date to decide') + ' · ' +
                     esc(VEHICLES[giving['vehicle']]) + ' · ' + esc(FUNDING[giving['funding']]) + '</p>')
            P.append('<p>Cash reservation: ' + ('included in commitments' if giving['cash_reserved'] else 'not requested') + '.</p>')
            for key, label in [('deduction_tax_benefit', 'Modeled deduction tax benefit'), ('avoided_gain_tax', 'Modeled tax avoided on donated-share gain')]:
                P.append('<p>' + label + ': ' + (money(giving[key]) if giving[key] is not None else 'needs reviewed inputs') + '.</p>')
            P.append(bullets(giving['gaps']))
            from officekit.render_charitable import securities_section
            P.append(securities_section(giving['goal_id'], giving.get('securities') or {}, editable=False))
        P.append('<p class="warning">These scenarios do not release tax reserves or add deployment cash. Review all gifts together for annual deduction limits.</p></section>')
    from officekit.render_research import reuse_section
    P.append(reuse_section(p))
    inventory = p.get('research_inventory') or {}
    if inventory:
        from officekit_research.taxonomy import label as research_label
        P.append('<section class="slide"><h2>Saved research used for candidate selection</h2><p>' + esc(inventory['use']) + '</p>')
        for attached in p.get('research_attachments', []):
            P.append('<p><b>' + esc(attached['symbol']) + '</b> · ' + str(len(attached['references'])) + ' matching saved research records; links below. This is research lineage, not proof that a prior verdict applies.</p>')
        for entry in inventory['entries']:
            if entry.get('href', '').startswith('/pages/research_'):
                P.append('<p><a href="' + esc(entry['href']) + '">Open saved research for ' + esc(', '.join(entry['symbols'])) + ' →</a></p>')
            P.append('<details><summary>' + esc(', '.join(entry['symbols'])) + ' · ' + esc(research_label(entry['kind'])) +
                     ' · ' + esc(entry.get('as_of') or 'Date unrecorded') + '</summary><p>' + esc(entry['summary']) + '</p>' +
                     '<p>Original ID: ' + esc(entry['id']) + ' · ' + esc(entry.get('verdict') or entry.get('standing') or 'Candidate thesis') + '</p>' +
                     ('<p>Contributor: ' + esc(entry['author']) + ' · ' + esc(entry.get('source', '')) + '</p>' if entry.get('author') else '') +
                     bullets(entry.get('risks', [])) + bullets(entry.get('gaps', [])) + '</details>')
        if inventory['omitted']:
            P.append('<p>' + str(inventory['omitted']) + ' further entries were outside this proposal’s discovery limit.</p>')
        P.append(bullets(inventory['warnings']) + '</section>')
    P.append('<section class="slide"><div class="eyebrow">02 / Funding</div><h2>What this office can allocate</h2>')
    if funding:
        P.append('<div class="grid">' + ''.join(f'<div class="metric"><small>{label}</small><b>{money(funding[key])}</b></div>' for label,key in [('Unreserved cash today','current_cash'),('Current proposal ceiling','current_budget'),('Pending proceeds, net of tax','pending_net')]) + '</div>')
        P.append(f'<p class="muted">{esc(funding["sizing_basis"])}</p>')
        P.append(bullets(funding.get('blocking_gaps', [])))
        if funding.get('liquidity_floor') or funding.get('income_expenses'):
            P.append('<p>Cash floor protected: ' + money(funding.get('liquidity_floor', 0)) +
                     '; income-period bills: ' + money(funding.get('income_expenses', 0)) + '.</p>')
        if funding.get('income_expense_shortfall'):
            P.append('<p>Income-period bills exceed deployable proceeds by ' + money(funding['income_expense_shortfall']) + '.</p>')
        if 'commitment_reserve' in funding:
            P.append('<p>Tax reserved: ' + money(funding['pending_tax']) + '; unfunded commitments reserved: ' +
                     money(funding['commitment_reserve']) + '; available after receipt: ' + money(funding['contingent_budget']) + '.</p>')
    else:
        P.append('<p>Funding is checked against the saved office snapshot before the courts and allocation review.</p>')
    P.append('</section><section class="slide"><div class="eyebrow">03 / Implementation</div><h2>Proposed investments and actions</h2>')
    if p.get('basket'):
        P.append('<div class="table"><table><tr><th>Investment</th><th>Current allocation</th><th>After proceeds arrive</th><th>Reason & conditions</th></tr>')
        for a in p['basket']:
            label = 'Options on ' if a['instrument'] == 'options' else ''
            P.append(f'<tr><td><b>{label}{esc(a["symbol"])}</b><div>{esc(a["structure"])}</div></td><td>{money(a["amount"])}<div class="muted">{esc(a["amount_label"])}</div></td><td>{money(a.get("contingent_amount", 0))}<div class="muted">Conditional allocation</div></td><td>{esc(a["rationale"])}{bullets(a["conditions"])}</td></tr>')
        P.append('</table></div>')
        if 'commitment_reserve' in funding:
            remaining = max(0, funding['contingent_budget'] - sum(a.get('contingent_amount', 0) for a in p['basket']))
            P.append('<p><b>Cash retained after reserves: ' + money(remaining) + '</b></p>')
    elif p.get('research'):
        P.append(bullets(p['research'].get('program_steps', [])))
        if p['candidates']:
            P.append('<p>Under review: ' + esc(', '.join(c['symbol'] for c in p['candidates'])) + '. Sizing follows adjudication.</p>')
    else:
        P.append('<p>The analyst will compare implementations and pass each candidate to independent courts.</p>')
    P.append(bullets(pitch.get('implementation', [])))
    P.append('<p class="muted">These are proposals. Adoption records intent; purchases, cash reservations and provider engagements are separate actions.</p></section>')
    P.append('<section class="slide"><div class="eyebrow">04 / Independent review</div><h2>What the courts concluded</h2>')
    if not p['courts']:
        P.append('<p class="muted">Court arguments and adjudications will appear here as each review completes.</p>')
    for a in p['courts']:
        P.append(f'<details open><summary>{esc(a["symbol"])} · {esc(a["verdict"])}</summary><p>{esc(a["rationale"])}</p>')
        for role in ['red','blue']:
            P.append(f'<details><summary>{role.upper()} bench</summary><div class="prose">{esc(a["briefs"][role]["case"])}</div>{bullets(a["briefs"][role]["key_points"])}</details>')
        P.append(bullets(a.get('unverified_items', [])))
        P.append(f'<small>Court {esc(a["id"])} · {esc(a["date"])} · {esc(a["tier"])} · {esc(a["models"])}</small></details>')
    P.append('</section><section class="slide"><div class="eyebrow">05 / Risk Officer</div><h2>Does it fit the whole portfolio?</h2>')
    if risk:
        P.append(f'<span class="badge">{esc(risk["verdict"])}</span><p>{esc(risk["rationale"])}</p>' + bullets(risk['findings']) + bullets(risk['conditions']))
    else:
        P.append('<p class="muted">Independent allocation reasoning follows the candidate courts.</p>')
    for f in p.get('deterministic_risk', []):
        P.append(f'<details><summary>{esc(f["severity"])} · {esc(f["title"])}</summary><p>{esc(f["detail"])}</p><p>{esc(f["advice"])}</p></details>')
    P.append('</section><section class="slide"><div class="eyebrow">06 / Alternatives & downside</div><h2>What could make this wrong</h2><p>' + esc(b['risks']) + '</p>')
    P.append(bullets(pitch.get('downside', [])) + bullets(pitch.get('alternatives') or (p.get('research') or {}).get('alternatives', [])))
    P.append('<h3>Monitoring and next decisions</h3>' + bullets(pitch.get('monitoring') or risk.get('monitoring', [])) + '</section>')
    P.append('<section class="slide sources"><div class="eyebrow">07 / Evidence & audit trail</div><h2>Sources behind the proposal</h2>')
    for symbol, entry in (p.get('general') or {}).items():
        P.append('<p>' + esc(symbol) + ' · general court: ' + esc(entry.get('source', 'unknown')) +
                 ' · <code>' + esc((entry.get('record') or {}).get('id', '')) + '</code></p>')
        sharing = entry.get('shared') or {}
        if sharing and sharing.get('shared') is False and sharing.get('reason') != 'Research sharing is off for this office':
            P.append('<p class="warning">Research publication needs attention: ' + esc(sharing.get('reason', 'Contribution failed')) + '</p>')
        elif sharing.get('shared'):
            P.append('<p class="muted">' + ('Private research held for explicit release.' if sharing.get('held') else
                     'General research contributed; this office’s suitability ruling remains private.') + '</p>')
    for symbol, pack in (p.get('evidence') or {}).items():
        P.append(f'<details><summary>{esc(symbol)} · collected {esc(pack["built"])}</summary>')
        for name, section in pack['sections'].items():
            url = section.get('url') if isinstance(section, dict) else None
            if url and urlparse(url).scheme == 'https' and urlparse(url).hostname:
                label = 'source cited by shared research' if name in pack.get('reuse', {}) else 'primary source'
                P.append(f'<p><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(name)} · {label}</a></p>')
                if name in pack.get('reuse', {}):
                    origin = pack['reuse'][name]
                    P.append(f'<p class="muted">Evidence originally collected {esc(origin["retrieved_at"])}; reuse expires {esc(origin["valid_until"])}. Basis: {esc(origin["basis"])}.</p>')
            else:
                P.append(f'<p>{esc(name)} · retained in the proposal evidence snapshot</p>')
        P.append(bullets(pack.get('errors', [])) + '</details>')
    P.append('<details><summary>Review history</summary>' + bullets([h['at'] + ' · ' + h['stage'] for h in p['history']]) + '</details></section>')
    P.append('<p><a href="/research">Review or contribute contextual research</a></p>')
    if status in {'ready', 'needs_review'}:
        P.append('<section class="slide decision"><h2>Your decision</h2><p>Record the plan after reviewing the court and Risk Officer conditions.</p><div class="actions">')
        for action,label in [('adopt','Adopt plan'),('decline','Decline proposal')]:
            if outdated and action == 'adopt':
                continue
            P.append(f'<form action="/strategy/proposal/decide" method="POST"><input type="hidden" name="pid" value="{esc(p["id"])}"><input type="hidden" name="action" value="{action}"><button class="{ "secondary" if action == "decline" else ""}">{label}</button></form>')
        P.append('</div></section>')
    if status not in {'queued','running','superseded'}:
        P.append(f'<section class="slide decision"><h2>Refine the proposal</h2><form action="/strategy/proposal/revise" method="POST"><input type="hidden" name="pid" value="{esc(p["id"])}"><label for="revision">Changes to investigate</label><textarea id="revision" name="request" rows="3" maxlength="8000" placeholder="Change the allocation, compare another investment, or rebuild with current balances"></textarea><button style="margin-top:12px">Build a fresh revision</button></form></section>')
    P.append('</main></body></html>')
    from officekit.mandates import stamp_forms
    return stamp_forms(''.join(P), revision or p['snapshot_revision'])
