"""Human review surface for a charitable goal and its tax-planning assumptions."""
from html import escape
from officekit.charitable import VEHICLES, FUNDING


def body(goal, plan, endpoint):
    c = goal.get('charitable') or {}
    esc = lambda value: escape(str(value if value is not None else ''), quote=True)
    money = lambda value: 'Not yet modeled' if value is None else f'${value:,.2f}'
    def field(name, label, value='', kind='text', hint=''):
        return ('<label>' + esc(label) + '<input name="' + name + '" type="' + kind + '" value="' + esc(value) + '">' +
                ('<small>' + esc(hint) + '</small>' if hint else '') + '</label>')
    def select(name, label, choices, value):
        return '<label>' + esc(label) + '<select name="' + name + '">' + ''.join(
            '<option value="' + esc(k) + '"' + (' selected' if k == value else '') + '>' + esc(v) + '</option>'
            for k, v in choices.items()) + '</select></label>'
    def confirmation(name, label):
        return select(name, label, {'': 'Not confirmed', 'yes': 'Yes', 'no': 'No'},
                      'yes' if c.get(name) is True else 'no' if c.get(name) is False else '')
    out = ['<style>.giving-fields{display:grid;grid-template-columns:1fr 1fr;gap:14px}.giving-fields label{display:grid;gap:6px;font-size:12px;color:#b8c2cc}'
           '.giving-fields input,.giving-fields select{min-width:0;box-sizing:border-box;width:100%;background:#0b0e12;color:#e8ebee;border:1px solid #39424d;border-radius:7px;padding:10px;font:inherit}'
           '.giving-fields small{color:#9aa4b0}.giving button{background:#35c98f;color:#08110d;border:0;border-radius:8px;padding:11px 16px;font-weight:650;cursor:pointer}'
           '.giving .stats{display:grid;grid-template-columns:1fr 1fr;gap:24px}.giving :focus-visible{outline:2px solid #b1a5ff;outline-offset:3px}@media(max-width:620px){.giving-fields,.giving .stats{grid-template-columns:1fr}}</style>',
           '<p class="sub">A giving goal connects your intended gift to funding, timing and a tax review. The gift amount leaves the household; any tax benefit is a separate scenario.</p>',
           '<div class="panel giving"><h2>Giving plan</h2><div class="stats">']
    for label, value in [('Proposed gift', goal['amount']), ('Available from selected source today', plan['available_today']),
                         ('Modeled deduction benefit', plan['deduction_tax_benefit']), ('Modeled tax avoided on donated shares', plan['avoided_gain_tax'])]:
        out.append('<div class="stat"><div class="l">' + label + '</div><div class="n">' + money(value) + '</div></div>')
    out.append('</div><p>' + ('Cash is reserved in Capital &amp; Commitments.' if plan['cash_reserved'] else 'This goal has no cash reservation.') +
               '</p><p><a href="/pages/strategies.html#goal-' + esc(goal['id']) + '">Compare strategies for this goal →</a></p>'
               '<form method="POST" action="/strategy/goal-adopt"><input type="hidden" name="gid" value="' + esc(goal['id']) +
               '"><input type="hidden" name="sid" value="gifting"><button>Research this giving strategy</button></form></div>')
    out.append(securities_section(goal['id'], plan.get('securities') or {}))
    out.append('<div class="panel giving"><h2>Gift and funding choices</h2><form method="POST" action="' + esc(endpoint) + '">'
               '<input type="hidden" name="gid" value="' + esc(goal['id']) + '"><input type="hidden" name="charitable_form" value="yes"><div class="giving-fields">')
    out.extend([field('label', 'Goal name', goal.get('label')), field('amount', 'Total gift amount ($)', goal['amount']),
                field('date', 'Intended gift date', goal.get('date', ''), 'date'),
                select('vehicle', 'Giving vehicle', VEHICLES, c.get('vehicle', 'undecided')),
                select('funding', 'Gift funding', FUNDING, c.get('funding', 'undecided')),
                field('recipient', 'Charity or DAF sponsor', c.get('recipient')),
                confirmation('recipient_qualified', 'Recipient eligibility checked'),
                select('reserve_cash', 'Reserve this cash gift in the cash calendar', {'no': 'No reservation', 'yes': 'Reserve the full gift'}, 'yes' if c.get('reserve_cash') else 'no'),
                field('symbol', 'Ticker of securities to donate', c.get('symbol'), hint='Identify actual owned shares; transfer instructions still require exact lots.'),
                field('cost_basis', 'Cost basis of the gift portion ($)', c.get('cost_basis')),
                confirmation('long_term', 'Gift securities held more than one year'),
                confirmation('before_sale', 'Transfer can occur before sale or a binding sale obligation')])
    out.append('</div><h2>Reviewed tax assumptions</h2><p class="sub">Enter the deduction usable in the gift year after reviewing AGI limits, other gifts, carryovers, the applicable floor and itemization. '
               'The effective rate must reflect the actual income mix and federal/state treatment. Blank means unknown. Saving these figures does not change the office tax reserve.</p><div class="giving-fields">')
    out.append(field('deductible_amount', 'Usable deduction this tax year ($)', c.get('deductible_amount')))
    for key, label in [('deduction_tax_rate', 'Effective tax benefit of the deduction (%)'), ('capital_gain_tax_rate', 'Tax rate on the donated share gain (%)')]:
        out.append(field(key, label, c[key] * 100 if c.get(key) is not None else ''))
    out.append(field('tax_review_reference', 'Tax review reference and date', c.get('tax_review_reference'), hint='For example, a preparer projection covering this gift and the other gifts in that tax year.'))
    out.append('</div><p><button>Save giving plan</button></p></form></div>')
    out.append('<h2>Choices to compare</h2><div class="panel"><table><tr><th>Choice</th><th>Planning consideration</th></tr>'
               '<tr><td>Cash directly to charity</td><td>Uses spendable cash. Review the usable deduction and recipient eligibility.</td></tr>'
               '<tr><td>Appreciated securities directly to charity</td><td>Review owned lots, basis, holding period, acceptance and transfer timing before selling.</td></tr>'
               '<tr><td>Donor-advised fund</td><td>Separate the contribution date from later grants. The sponsor controls contributed assets; later grants do not generate another contribution deduction.</td></tr></table></div>')
    if plan['gaps']:
        out.append('<h2>Items to resolve</h2><div class="panel"><ul>' + ''.join('<li>' + esc(g) + '</li>' for g in plan['gaps']) + '</ul></div>')
    out.append('<p class="note">' + ' '.join(esc(s) for s in plan['limitations']) + '</p>')
    out.append('<p class="note">Tax rules: ' + ' · '.join('<a href="' + esc(s['url']) + '">' + esc(s['title']) + '</a>' for s in plan['sources']) + '</p>')
    return ''.join(out)


def securities_section(gid, view, editable=True):
    if not view:
        return ''
    esc = lambda value: escape(str(value if value is not None else ''), quote=True)
    money = lambda value: 'Unknown' if value is None else f'${value:,.2f}'
    out = ['<section class="panel giving" id="donation-securities"><h2>Which securities could fund this gift?</h2><p>' + esc(view['method']) + '</p>',
           '<p class="sub">Portfolio marks as of ' + esc(view.get('as_of')) + '. Missing basis is never treated as zero.</p>']
    mix = {r['id']: r for r in view['suggested_mix']}
    if view['candidates']:
        out.append('<div style="overflow-x:auto"><table><tr><th>Candidate / account</th><th>Market value / basis</th><th>Embedded gain</th><th>Illustrative gift / basis</th></tr>')
        for row in view['candidates']:
            gift = mix.get(row['id'])
            kind = ('Lot ' + str(row['lot'])) if row['level'] == 'lot' else 'Position total; exact lots not imported'
            out.append('<tr><td><b>' + esc(row['symbol']) + '</b><br>' + esc(row['account']) + '<br><small>' + esc(kind) + '</small></td>' +
                       '<td>' + money(row['market_value']) + '<br>Basis ' + money(row['cost_basis']) + '</td>' +
                       '<td>' + money(row['gain']) + '<br>' + f"{row['gain_fraction'] * 100:.1f}% of value" + '</td><td>' +
                       (money(gift['gift_amount']) + '<br>Basis ' + money(gift['gift_basis']) +
                        ('<br><small>Proportional estimate; verify lots</small>' if gift['estimate'] else '') if gift else 'Alternative') + '</td></tr>')
        out.append('</table></div><p>This illustrative mix covers ' + money(sum(r['gift_amount'] for r in mix.values())) +
                   ' of the gift. Unfilled: ' + money(view['unfilled']) + '. It does not select, reserve or transfer shares.</p>')
    else:
        out.append('<p>No holdings qualify for the shortlist yet. Complete the missing facts below or import an updated lot statement.</p>')
    if view['needs_review'] or view.get('reviewed'):
        out.append('<h3>Complete or review basis and eligibility</h3><p>' + str(view['review_count']) +
                   ' holding or lot records need review. These facts are shared across your office’s giving goals and research.</p>')
        for row in view['needs_review'] + view.get('reviewed', []):
            out.append('<details><summary>' + esc(row['symbol']) + ' · ' + esc(row['account']) +
                       (' · lot ' + esc(row['lot']) if row['lot'] else '') + ' · ' +
                       (', '.join({'cost_basis': 'basis missing', 'long_term': 'holding period missing', 'taxable': 'account tax status missing'}[k] for k in row['missing']) or ('saved review' if row['review_reference'] else 'source review needed')) + '</summary>')
            out.append('<p>Market value ' + money(row['market_value']) + '; total basis ' + money(row['cost_basis']) +
                       '. Source: ' + esc(row['source']) + ' · ' + esc(row['as_of']) + '.</p>')
            if row['review_stale']:
                out.append('<p>The source snapshot changed. Reconfirm missing facts against the current statement.</p>')
            out.extend('<p>' + esc(b) + '</p>' for b in row['blocked'])
            if editable and (row['missing'] or row['review_reference']):
                out.append('<form method="POST" action="/goal/security-review">' + ''.join(
                    '<input type="hidden" name="' + k + '" value="' + esc(v) + '">' for k, v in
                    [('gid', gid), ('security_id', row['id']), ('fingerprint', row['fingerprint'])]) + '<div class="giving-fields">')
                if row['imported_basis'] is None:
                    out.append('<label>Total adjusted cost basis for this ' + ('lot' if row['lot'] else 'account position') +
                               ' ($)<input name="cost_basis" inputmode="decimal" value="' + esc(row['cost_basis']) + '" placeholder="Unknown — enter from a statement"><small>Total dollars, not cost per share. Enter 0 only if verified.</small></label>')
                for key, label in [('long_term', 'All shares in this record held more than one year'), ('taxable', 'Held in a taxable account outside a retirement plan')]:
                    if row['imported_term' if key == 'long_term' else 'imported_taxable'] is None:
                        out.append('<label>' + label + '<select name="' + key + '"><option value="">Not confirmed</option><option value="yes"' + (' selected' if row[key] is True else '') + '>Yes</option><option value="no"' + (' selected' if row[key] is False else '') + '>No</option></select></label>')
                out.append('<label>Statement or review reference<input name="reference" required maxlength="1000" value="' + esc(row['review_reference']) + '" placeholder="Statement date and source"></label></div><p><button>Save facts and refresh suggestions</button></p></form>')
            out.append('</details>')
    if view['excluded_count']:
        out.append('<p class="note">' + str(view['excluded_count']) + ' records excluded because they are not confirmed long-term appreciated holdings in taxable accounts.</p>')
    if view['omitted']:
        out.append('<p class="note">' + str(view['omitted']) + ' further records are outside this view’s display limit.</p>')
    out.append('<p><a href="/pages/imports.html">Import or refresh a broker tax-lot statement →</a></p>')
    out.append('<ul class="note">' + ''.join('<li>' + esc(s) + '</li>' for s in view['limitations']) + '</ul></section>')
    return ''.join(out)
