"""Expected proceeds, explicit balance attribution, and receipt review."""
from officekit.fmt import esc
from officekit.inflows import active_receipts, cash_accounts, progress
from datetime import date


def inflow_card(m, answers, rev, proposals=()):
    from officekit.render_capital import money
    inc = answers.get("incoming") or {}
    if not inc.get("id") or not inc.get("amount"):
        return ""
    state = progress(answers)
    tax = round((m.get("tax") or {}).get("net_tax", 0))
    accounts = cash_accounts(answers)
    p = ['<h2 id="inflows">Incoming money</h2><article class="commit-card inflow-card">'
         '<div class="commit-head"><h3>Expected proceeds</h3>'
         f'<span class="commit-status">{esc(state["status"])}</span></div>'
         f'<p class="sub">Expected: {esc(inc.get("eta") or "Date not set")} · '
         f'{money(state["gross"] - tax)} net proceeds after {money(tax)} estimated tax.</p>'
         '<div class="inflow-stats">'
         f'<div><span>Total expected</span><b>{money(state["gross"])}</b></div>'
         f'<div><span>Received, before withholding</span><b>{money(state["received"])}</b></div>'
         f'<div><span>Still pending</span><b>{money(state["pending"])}</b></div></div>']
    from officekit.deployment import source_for, href
    from officekit.render_deployment import link
    p.append(link(source_for(m, inc['id']), proposals, rev))
    if state["withheld"]:
        p.append(f'<p class="sub">{money(state["cash_received"])} deposited · {money(state["withheld"])} '
                 'tax withheld. Withholding reduces the outstanding tax reserve once.</p>')
    if state["pending"]:
        p.append('<details><summary>Record a receipt</summary><p class="sub">Refresh or update the receiving '
                 'account first. Link a deposit already included in its cash balance. This records your '
                 'confirmation and reference; the app has account snapshots, not a bank transaction match.</p>')
        if accounts and rev:
            opts = ''.join(f'<option value="{esc(a["id"])}">{esc(a["account"])} · {esc(a["source"])} · '
                           f'{money(a["balance"])} as of {esc(a["as_of"])}</option>' for a in accounts)
            p.append(f'<form method="POST" action="/inflows/preview"><input type="hidden" name="revision" value="{rev}">'
                     f'<input type="hidden" name="inflow_id" value="{esc(inc["id"])}">'
                     '<input type="hidden" name="action" value="receive"><div class="commit-fields">'
                     '<label>Gross proceeds received ($)<input name="gross" inputmode="decimal" required></label>'
                     f'<label>Receipt date<input name="date" type="date" max="{date.today().isoformat()}" required></label>'
                     '<label>Tax withheld ($, if any)<input name="withheld" inputmode="decimal" placeholder="0"></label>'
                     f'<label>Receiving cash account<select name="account_id" required><option value="">Choose an account…</option>{opts}</select></label>'
                     '<label class="wide">Statement or transaction reference<input name="reference" maxlength="240" '
                     'placeholder="For example: September statement, deposit on the 7th, reference 1234" required></label></div>'
                     '<label class="receipt-confirm"><input type="checkbox" name="included" value="yes" required>'
                     'I confirm the net deposit (gross proceeds minus withholding) is already included in this account’s cash balance.</label>'
                     '<button>Review receipt</button></form>')
        else:
            p.append('<p>No cash account is available to link. Import or enter the receiving account balance first.</p>')
        p.append('<p class="sub"><a href="/pages/imports.html">Review and refresh account sources</a></p></details>')
    events = [e for e in answers.get("inflow_events", []) if e["inflow_id"] == inc["id"]]
    active = {e["id"] for e in active_receipts(answers)}
    if events:
        p.append('<h3 class="receipt-history">Receipt history</h3>')
    for e in reversed(events):
        if e["kind"] == "reversal":
            p.append(f'<p class="sub">Correction recorded {esc(e["recorded_at"][:10])}: {esc(e["reason"])}</p>')
            continue
        evidence = e["evidence"]
        status = "Recorded · balance linked" if e["id"] in active else "Reversed"
        p.append(f'<div class="receipt-row" id="receipt-{esc(e["id"])}"><b>{money(e["gross"] - e["withheld"])} deposited · '
                 f'{esc(e["date"])}</b><span class="commit-status">{status}</span>'
                 f'<p class="sub">{money(e["gross"])} gross · {money(e["withheld"])} withheld · '
                 f'{esc(evidence["account"])} · {esc(evidence["source"])}<br>Reference: {esc(e["reference"])}<br>'
                 f'Balance at confirmation: {money(evidence["balance"])} as of {esc(evidence["as_of"])}.</p>')
        if e["id"] in active and rev:
            p.append('<p><a href="' + href(inc['id']) + '">Open deployment strategy for these proceeds →</a></p>')
            p.append('<details><summary>Correct this receipt</summary><p class="sub">Reverse an incorrect attribution, '
                     'then record its replacement. This restores the pending proceeds and tax allocation; account cash stays unchanged.</p>'
                     f'<form method="POST" action="/inflows/preview"><input type="hidden" name="revision" value="{rev}">'
                     f'<input type="hidden" name="inflow_id" value="{esc(inc["id"])}">'
                     f'<input type="hidden" name="receipt_id" value="{esc(e["id"])}">'
                     '<input type="hidden" name="action" value="reverse">'
                     '<label>Correction reason<input name="reason" maxlength="1000" required></label>'
                     '<button class="secondary">Review reversal</button></form></details>')
        p.append('</div>')
    p.append('</article>')
    return ''.join(p)


def render_receipt_preview(before, after, event, token):
    from officekit.commitments import cash_calendar, tax_funding
    from officekit.render_capital import CSS, money
    def figures(m):
        cal = cash_calendar(m)
        return [cal["cash"], (m["d"].get("inflow") or {}).get("pending", 0),
                tax_funding(m)["current"], cal["pending_tax_reserve"], cal["outflow"], cal["available"]]
    labels = ["Current cash (unchanged)", "Pending proceeds", "Tax reserved against current cash",
              "Tax reserved against pending proceeds", "Scheduled from portfolio", "Cash available to commit"]
    rows = ''.join(f'<tr><th scope="row">{label}</th><td>{money(b)}</td><td>{money(a)}</td></tr>'
                   for label, b, a in zip(labels, figures(before), figures(after)))
    rows += f'<tr><th scope="row">Planning balance date</th><td>{esc(before["d"]["as_of"])}</td><td>{esc(after["d"]["as_of"])}</td></tr>'
    date_note = ('<p class="sub">The planning date advances to the receipt date. Recurring payments before that date '
                 'are assumed paid; outstanding one-time payments remain reserved.</p>'
                 if before["d"]["as_of"] != after["d"]["as_of"] else '')
    if event["kind"] == "receipt":
        e = event["evidence"]
        detail = (f'{money(event["gross"])} gross proceeds, {money(event["withheld"])} tax withheld, '
                  f'{money(event["gross"] - event["withheld"])} net deposit on {event["date"]}. '
                  f'Linked to {e["account"]} ({e["source"]}). Reference: {event["reference"]}.')
        title, button = "Review receipt", "Record this receipt"
    else:
        detail = 'Correction reason: ' + event["reason"]
        title, button = "Review receipt reversal", "Reverse this attribution"
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>'
            f'<style>{CSS}</style></head><body><main class="wrap review"><div class="eyebrow">Review before saving</div>'
            f'<h1>{title}</h1><p>{esc(detail)}</p><p class="sub">Account balances stay unchanged. '
            'Only the pending proceeds, tax allocation and receipt history change.</p>'
            f'<div class="calendar"><table><thead><tr><th>Effect</th><th>Before</th><th>After</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'{date_note}<form method="POST" action="/inflows/apply"><input type="hidden" name="token" value="{token}">'
            f'<button>{button}</button> <a href="/pages/capital.html#inflows">Cancel</a></form></main></body></html>')
