"""One readable program workspace for funding, constituents and harvesting."""
from datetime import date
from html import escape

from officekit import beta_programs as B
from officekit.mandates import stamp_forms


def esc(value):
    return escape(str(value if value is not None else ''), quote=True)


def money(value):
    return 'Not modeled' if value is None else f'${value:,.2f}'


def field(label, name, value='', kind='text'):
    step = ' step="any"' if kind == 'number' else ''
    return f'<label>{esc(label)}<input type="{kind}"{step} name="{name}" value="{esc(value)}"></label>'


def form(action, pid='', body='', button='Save'):
    return (f'<form method="POST" action="/beta/program"><input type="hidden" name="action" value="{action}">'
            f'<input type="hidden" name="pid" value="{esc(pid)}">{body}<button>{esc(button)}</button></form>')


def source_select(model):
    from officekit.deployment import sources
    return '<label>Incoming-money source<select name="inflow_id"><option value="">Choose a source</option>' + ''.join(
        f'<option value="{esc(s["id"])}">{esc(s["label"])}</option>' for s in sources(model)) + '</select></label>'


def section(answers, model, source_id=None, revision=None):
    linked = B.summaries(answers, model, source_id)
    out = ['<section id="beta-programs"><h2>Beta &amp; tax-loss harvesting</h2>']
    if linked:
        for v in linked:
            out.append(f'<article><h3><a href="{esc(v["href"])}">{esc(v["label"])} →</a></h3>'
                       f'<p><b>{esc(v["state"].title())}</b> · {len(v["basket"]["rows"])} constituents · '
                       f'{money(v["budget"]["current"])} received allocation · {money(v["budget"]["pending"])} conditional allocation</p>'
                       + ('<p>Needs attention: ' + esc(v['gaps'][0]) + '</p>' if v['gaps'] else '') + '</article>')
    else:
        c = B.candidate(model)
        out.append('<p><b>' + esc(c['status'].replace('_', ' ').title()) + '</b> · ' + esc(c['reason']) + '</p>')
    out.append('<p><a href="/pages/beta_programs.html">Review programs, create a basket or import an existing mandate →</a></p>')
    if source_id:
        for p in B.programs(answers).values():
            if source_id not in p['bindings']:
                out.append(form('bind', p['id'], f'<input type="hidden" name="inflow_id" value="{esc(source_id)}">'
                                + field('Share of this source’s available proceeds (%)', 'allocation_pct', 100, 'number'),
                                'Link to ' + p['label']))
    out.append('<p class="note">Tax and goal reserves stay protected. Program allocations describe intent; purchases and transfers are not performed here.</p></section>')
    return stamp_forms(''.join(out), revision) if revision else ''.join(out)


def editor(model, p=None):
    p = p or {}
    q = p.get('policy') or {}
    tax = p.get('taxable')
    body = field('Program name', 'label', p.get('label', 'Beta & tax-loss harvesting'))
    body += field('Custodian account name (match your imported holdings)', 'account', p.get('account', ''))
    body += '<label>Taxable account<select name="taxable">' + ''.join(
        f'<option value="{v}"{" selected" if tax is flag else ""}>{label}</option>'
        for v, flag, label in [('', None, 'Not confirmed'), ('yes', True, 'Yes'), ('no', False, 'No')]) + '</select></label>'
    for label, name, default in [('Investment horizon (years)', 'horizon_years', 5),
        ('Annual all-in costs (basis points; 100 = 1%)', 'fee_bps', None),
        ('Maximum constituents', 'max_names', 150), ('Minimum harvest loss ($)', 'min_loss', 1000),
        ('Reviewed capital-gain offset capacity ($)', 'gain_capacity', None), ('Tax year', 'tax_year', date.today().year),
        ('Additional approved tax-reserve floor ($)', 'reserve_floor', 0), ('Maximum program capital ($; blank = funding ceiling)', 'capital_cap', None)]:
        body += field(label, name, q.get(name, default), 'number')
    body += field('Maximum constituent weight (%)', 'max_weight', q.get('max_weight', .025) * 100, 'number')
    body += field('Reviewed tax rate on offset gains (%)', 'tax_rate', q['tax_rate'] * 100 if q.get('tax_rate') is not None else '', 'number')
    body += field('Excluded symbols (comma-separated; restrictions and coordinated account exclusions)', 'exclusions', ', '.join(q.get('exclusions', [])))
    if not p:
        body += source_select(model) + field('Share of available proceeds (%)', 'allocation_pct', 100, 'number')
    return form('edit' if p else 'create', p.get('id', ''), body, 'Save policy' if p else 'Create program')


def page(answers, model):
    from officekit.render_capital import CSS
    from officekit.commitments import revision
    from officekit.beta_harvest import overlay
    from officekit.deployment import sources
    source_labels = {s['id']: s['label'] for s in sources(model)}
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>Beta &amp; tax-loss harvesting</title><style>' + CSS +
           'label{display:block;margin:10px 0}input,select,textarea{display:block;max-width:100%;padding:8px;background:#151d27;color:inherit;border:1px solid #445}'
           'textarea{width:100%;min-height:90px}table{width:100%;border-collapse:collapse}td,th{padding:8px;text-align:left;border-bottom:1px solid #345}'
           'section,article,details{margin:18px 0;padding:14px;border:1px solid #345;border-radius:8px}.note{color:#9aa4b0}button{margin:8px 0;padding:10px;cursor:pointer}'
           '</style></head><body><main class="wrap"><nav><a href="/pages/office.html">Home</a> · '
           '<a href="/pages/capital.html">Incoming money</a> · <a href="/pages/strategies.html">Strategies</a> · '
           '<a href="/pages/harvest.html">Portfolio loss review</a></nav><h1>Beta &amp; tax-loss harvesting</h1>'
           '<p>Maintain market exposure, allocate incoming cash, and review losses across your taxable lots.</p>'
           '<p><b>Eligible → Proposed → Approved → Funded → Operating</b>. Approval records intent; funding needs a cash reconciliation; operating needs current monitoring evidence. Readiness is checked separately.</p>']
    c = B.candidate(model)
    out.append('<p>' + esc(c['reason']) + '</p><p>Compare: ' + esc(' · '.join(c['alternatives'])) + '.</p>')
    for p in B.programs(answers).values():
        v, h = B.view(p, model), overlay(p, model)
        out.append(f'<section id="program-{esc(p["id"])}"><h2>{esc(p["label"])}</h2><p><b>{esc(v["state"].title())}</b>'
                   f' · Account: {esc(p["account"] or "Not confirmed")} · {esc(v["benchmark"])} · {esc(v["benchmark_as_of"] or "No snapshot")}</p>')
        out.append('<p>Received allocation: <b>' + money(v['budget']['current']) + '</b> · Conditional allocation: <b>' + money(v['budget']['pending']) +
                   '</b> · Recorded funding: ' + money(v['funded_amount']) + '</p><p>Additional reserve retained: ' + money(v['budget']['additional_reserve']) +
                   ' · Annual fee scenario: ' + money(v['annual_fee_estimate']) + '</p>')
        if p.get('approval'):
            out.append('<p>Recorded approval: ' + esc(p['approval']['as_of']) + ' · ' + esc(p['approval']['reference']) + '</p>')
        if p.get('provenance'):
            out.append('<p>Source: ' + esc(p['provenance']) + '</p>')
        if v['gaps']:
            out.append('<h3>Readiness</h3><ul>' + ''.join('<li>' + esc(g) + '</li>' for g in v['gaps']) + '</ul>')
        out.append('<details><summary>Policy and incoming-money links</summary>' + editor(model, p))
        out.append('<ul>' + ''.join('<li>' + esc(source_labels.get(sid, 'Unavailable source')) + ': ' + str(pct) + '%</li>' for sid, pct in p['bindings'].items()) + '</ul>')
        out.append(form('bind', p['id'], source_select(model) + field('Allocation (%; zero unlinks)', 'allocation_pct', 100, 'number'), 'Update funding link') + '</details>')
        out.append(form('refresh', p['id'], '', 'Refresh public benchmark and rebuild basket'))
        out.append('<details><summary>Import a dated benchmark snapshot</summary>' + form('snapshot', p['id'],
            '<label>Portable benchmark JSON<textarea name="snapshot_json" required></textarea></label>', 'Import benchmark') + '</details>')
        active = v['basket']['active_share']
        out.append('<details><summary>Constituents and dollar allocations (' + str(len(v['basket']['rows'])) + ')</summary><p>' + esc(v['method']) + '</p>')
        if active is not None:
            out.append(f'<p>Active share versus the source benchmark: {active:.1%}. This is not annual tracking error.</p>')
            sectors = v['basket']['sector_deviations']
            out.append('<p>Sector deviations: ' + (esc(' · '.join(f'{s}: {w:+.1%}' for s, w in sorted(sectors.items()))) if 'Unclassified' not in sectors else 'Unavailable: source holdings lack complete sector classifications.') + '</p>')
        out.append('<table><tr><th>Ticker</th><th>Weight</th><th>Received</th><th>Conditional</th></tr>' + ''.join(
            f'<tr><td>{esc(r["symbol"])}</td><td>{r["weight"]:.2%}</td><td>{money(r["current"])}</td><td>{money(r["pending"])}</td></tr>' for r in v['basket']['rows']) + '</table></details>')
        out.append('<details><summary>Lifecycle and operating record</summary>')
        actions = [('approve', 'Approve reviewed policy'), ('fund', 'Record reconciled funding'), ('operate', 'Confirm operating'), ('pause', 'Pause monitoring'), ('error', 'Record an operating problem')]
        for action, label in actions:
            out.append(form(action, p['id'], field('Decision / statement / monitoring reference', 'reference') +
                       (field('Reconciled received dollars', 'amount', '', 'number') if action == 'fund' else ''), label))
        if p.get('execution_note'):
            out.append(form('clear_note', p['id'], field('Evidence the imported operating issue is resolved', 'reference'), 'Resolve imported issue'))
        out.append('<ul>' + ''.join('<li>' + esc(e['at'] + ' · ' + e['action'] + ' · ' + e['reference']) + '</li>' for e in p.get('history', [])[-30:]) + '</ul></details>')
        out.append('<h3>Harvesting overlay</h3><p><b>' + esc(h['state'].replace('_', ' ').title()) + '</b></p><p>Reviewable loss scenario: ' + money(h['reviewable_losses']) + ' · Potential tax value: ' + money(h['potential_tax_value']) + '</p>')
        out.append('<ul>' + ''.join('<li>' + esc(g) + '</li>' for g in h['monitoring_gaps']) + '</ul>')
        out.append('<details><summary>Household wash-sale review</summary><p>Cover all household accounts, spouse/IRA activity, substantially identical securities, reinvestments and scheduled buys. Empty transactions means you checked and found none.</p>' +
                   form('wash', p['id'], field('Review reference', 'reference') +
                        '<label>Transactions: date, symbol, buy/sell, account (one per line)<textarea name="transactions"></textarea></label>' +
                        field('Open buys / reinvestment symbols (comma-separated)', 'open_buys') +
                        '<label><input type="checkbox" name="complete" value="yes" required> I reviewed the complete household wash-sale window and buy instructions.</label>', 'Save household review') + '</details>')
        out.append('<details><summary>Replacement review</summary>' + form('replacement', p['id'],
                   field('Harvest symbol', 'symbol') + field('Replacement symbol', 'replacement') +
                   field('Exposure and substantially-identical review', 'rationale') + field('Review reference', 'reference'), 'Save replacement') + '</details>')
        out.append('<table><tr><th>Security / lot</th><th>Loss</th><th>Replacement</th><th>Review</th></tr>')
        for r in h['candidates']:
            body = esc('; '.join(r['reasons'])) if r['reasons'] else 'Ready for lot review. Repurchase after ' + r['repurchase_after']
            if r['ready_for_review']:
                body += form('harvest', p['id'], f'<input type="hidden" name="security_id" value="{esc(r["id"])}"><input type="hidden" name="fingerprint" value="{esc(r["fingerprint"])}">' +
                             field('Broker confirmation for a sale completed today', 'reference'), 'Record completed sale')
            out.append(f'<tr><td>{esc(r["symbol"])} · {esc(r["lot"] or "Position estimate")}</td><td>{money(r["loss"])}</td><td>{esc(r["replacement"] or "Needs review")}</td><td>{body}</td></tr>')
        out.append('</table>')
        if h['needs_review']:
            out.append('<details><summary>Missing basis and account facts (' + str(len(h['needs_review'])) + ')</summary>')
            for r in h['needs_review'][:20]:
                out.append('<h4>' + esc(r['symbol'] + ' · ' + r['account']) + '</h4><p>' + esc(', '.join(r['missing']) + '; ' + '; '.join(r['blocked'])) + '</p>')
                body = f'<input type="hidden" name="security_id" value="{esc(r["id"])}"><input type="hidden" name="fingerprint" value="{esc(r["fingerprint"])}">'
                body += field('Total cost basis (blank = unknown)', 'cost_basis', r['cost_basis'], 'number')
                for key, label in [('long_term', 'Held more than one year'), ('taxable', 'Taxable account')]:
                    body += '<label>' + label + '<select name="' + key + '">' + ''.join(
                        f'<option value="{x}"{" selected" if r[key] is flag else ""}>{lab}</option>'
                        for x, flag, lab in [('', None, 'Not confirmed'), ('yes', True, 'Yes'), ('no', False, 'No')]) + '</select></label>'
                out.append(form('security-review', p['id'], body + field('Statement / review reference', 'reference'), 'Save missing facts'))
            out.append('</details>')
        out.append('<h4>Repurchase calendar</h4><ul>' + ''.join('<li>' + esc(l['symbol'] + ' · repurchase after ' + l['repurchase_after']) + '</li>' for l in h['locks']) + '</ul>')
        if p.get('harvests'):
            out.append('<details><summary>Recorded harvests and corrections</summary>')
            for i, r in enumerate(p['harvests']):
                out.append('<p>' + esc(r['date'] + ' · ' + r['symbol'] + ' · ' + r['reference']) + (' · Voided' if r.get('voided') else '') + '</p>')
                if not r.get('voided'):
                    out.append(form('void_harvest', p['id'], f'<input type="hidden" name="index" value="{i}">' + field('Correction reference', 'reference'), 'Void incorrect record'))
            out.append('</details>')
        out.append('<ul class="note">' + ''.join('<li>' + esc(n) + '</li>' for n in h['notes']) + '</ul></section>')
    out.append('<details id="new"><summary>Create a beta/TLH program</summary>' + editor(model) + '</details>')
    out.append('<details><summary>Import an existing private mandate</summary><p>Import its policy, dated basket and approval reference; choose the incoming-money source explicitly. Historical approval does not establish current readiness.</p>' +
               form('import', body='<label>Portable program JSON<textarea name="program_json" required></textarea></label>' + source_select(model) +
                    field('Share of available proceeds (%)', 'allocation_pct', 100, 'number'), button='Import private program') + '</details>')
    out.append('<p class="note">The baseline is long-only. Leveraged long/short extensions need a separate mandate. This workspace records plans and completed activity; it does not place orders.</p></main></body></html>')
    return stamp_forms(''.join(out), revision(answers))
