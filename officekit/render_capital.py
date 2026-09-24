"""Capital & Commitments: shared commitment cards and a twelve-month cash view."""
from __future__ import annotations

from officekit.commitments import cash_calendar, edit_values, revision
from officekit.fmt import esc


def money(value):
    """Keep reviewable dollar amounts on the payment surface, including cents."""
    value = round(float(value or 0), 2)
    prefix = '-$' if value < 0 else '$'
    return f'{prefix}{abs(value):,.0f}' if value == int(value) else f'{prefix}{abs(value):,.2f}'

CSS = """
*{box-sizing:border-box}body{margin:0;background:#0b0e12;color:#e8ebee;font:14px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
.wrap{max-width:1140px;margin:auto;padding:32px 26px 90px}h1{font-size:32px;letter-spacing:-.04em;margin:6px 0}h2{font-size:19px;margin:30px 0 12px}h3{margin:0;font-size:15px}p{margin:7px 0 14px}.muted,.sub{color:#9aa4b0}.eyebrow{text-transform:uppercase;letter-spacing:.14em;color:#8ee5c1;font-size:11px}a{color:#b1a5ff}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}.stat,.commit-card{background:#14191f;border:1px solid #28313c;border-radius:14px;padding:18px}.stat b{display:block;font-size:26px;letter-spacing:-.03em}.stat span{font-size:12px;color:#9aa4b0}.positive{color:#8ee5c1}.negative{color:#f0b3ad}.notice{border-left:3px solid #d9a441;background:#211d16;padding:14px 18px;border-radius:8px}.commit-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.commit-head{display:flex;align-items:start;justify-content:space-between;gap:12px}.commit-status{white-space:nowrap;font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:#edcc8a}.commit-status.confirmed{color:#8ee5c1}.commit-amount{font-size:23px;font-weight:600;margin:8px 0 2px}.commit-card details{border-top:1px solid #28313c;margin-top:12px;padding-top:10px}.commit-card summary{cursor:pointer;color:#b1a5ff;font-size:12px}.commit-fields{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}.commit-fields label{font-size:11px;color:#adb7c3;display:block}input,select,textarea{font:inherit;background:#0b0e12;border:1px solid #354050;border-radius:7px;color:#e8ebee;padding:9px;width:100%;margin-top:4px;min-width:0}button{background:#8ee5c1;color:#0b1511;border:0;padding:10px 15px;border-radius:8px;font-weight:600;cursor:pointer}.secondary{background:#29313c;color:#dce4ed}textarea{min-height:74px;resize:vertical}.calendar{overflow-x:auto;border:1px solid #28313c;border-radius:14px}table{border-collapse:collapse;width:100%;text-align:left}th{color:#9aa4b0;font-size:10px;text-transform:uppercase;letter-spacing:.08em}th,td{padding:15px 18px;border-bottom:1px solid #28313c;vertical-align:top}td small{display:block;color:#9aa4b0}td.amount,th.amount{text-align:right;white-space:nowrap}tr:last-child td{border-bottom:0}.payment{margin-bottom:5px}.payment span{color:#9aa4b0;font-size:11px}.empty{color:#8a939e}.review{max-width:750px}.review table{margin:24px 0}.commit-card .sub{font-size:12px}.jump{display:flex;gap:18px;margin:18px 0;font-size:12px}
@media(max-width:740px){.wrap{padding:22px 16px 60px}.stats{grid-template-columns:1fr 1fr}.stat b{font-size:23px}.commit-grid{grid-template-columns:1fr}.commit-fields{grid-template-columns:1fr}h1{font-size:28px}th,td{padding:12px}.calendar table{min-width:580px}}
"""

CSS += """
.jump{flex-wrap:wrap}.inflow-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:18px 0}
.inflow-stats span{display:block;font-size:12px;color:#9aa4b0}.inflow-stats b{display:block;font-size:23px}
.wide{grid-column:1/-1}.receipt-confirm{display:flex;align-items:start;gap:10px;margin:16px 0;font-size:13px}
.receipt-confirm input{width:auto;flex:none;margin:5px 0 0}.receipt-history{margin-top:22px}
.receipt-row{padding:14px 0;border-top:1px solid #28313c;overflow-wrap:anywhere}.receipt-row>.commit-status{margin-left:12px}
.inflow-card button{margin-top:12px}input:focus-visible,select:focus-visible,button:focus-visible,summary:focus-visible{outline:2px solid #b1a5ff;outline-offset:3px}
@media(max-width:740px){.inflow-stats{grid-template-columns:1fr}.receipt-row>.commit-status{display:block;margin-left:0}}
"""

LABELS = {"rate_pct": "Mortgage rate (%)", "term_years": "Years remaining", "home_value": "Home value ($)",
          "annual_amount": "Annual amount ($)", "amount": "Amount per payment ($)", "label": "Name",
          "cadence": "Payment frequency", "next_due": "Next payment", "ends_on": "Final payment (optional)",
          "funding_source": "Paid from", "settled": "Settled or released"}


def field(name, value="", adding=False, source=None):
    options = {"cadence": [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("annual", "Annually"), ("once", "One time")],
               "funding_source": [("portfolio", "Portfolio / cash"), ("income", "Outside income")],
               "settled": [("false", "Still outstanding"), ("true", "Settled / release reservation")]}
    if name in options:
        choices = options[name]
        if name == "cadence" and not adding:
            if source == "mortgage":
                choices = [("monthly", "Monthly")]
            elif source in {"lifestyle", "property_tax"}:
                choices = [(v, label) for v, label in choices if v != "once"]
            elif source in {"tax", "capital_call", "goal_reservation"}:
                choices = [("once", "One time")]
        current = next((label for v, label in choices if str(value).lower() == v), "Choose…")
        body = f'<select name="{name}"' + (' required' if adding else '') + '>'
        body += f'<option value="">{esc(current)}' + ('' if adding else ' · unchanged') + '</option>'
        body += ''.join(f'<option value="{v}">{label}</option>' for v, label in choices) + '</select>'
    else:
        typ = "date" if name in {"next_due", "ends_on"} else "text"
        body = f'<input name="{name}" type="{typ}" placeholder="{esc(str(value))}"'
        if name not in {"label", "next_due", "ends_on"}:
            body += ' inputmode="decimal"'
        if adding and name != "ends_on":
            body += ' required'
        body += '>'
        if value and typ == "date":
            body += f'<span class="muted">On file: {esc(str(value))}</span>'
    return f'<label>{LABELS[name]}{body}</label>'


def commitment_card(c, rev=None, chat=False, back="capital"):
    status = c.get("status") or ("estimated" if c.get("missing") else "confirmed")
    amount = c.get("annual_amount")
    if amount is not None:
        amount_text = money(amount) + "/year"
    else:
        amount_text = money(c.get("amount", 0)) + " · one time"
    funding = "Portfolio / cash" if c.get("portfolio_funded") else "Outside income"
    if c.get("funding_estimated"):
        funding += " (assumed)"
    assumptions = "; ".join(a["why"] for a in c.get("assumptions", []))
    end = f' · through {esc(c["ends_on"])}' if c.get("ends_on") else ""
    schedule = (f'{esc(c.get("cadence", "monthly").title())} · next {esc(c.get("next_due", "not set"))}{end}')
    if c.get("schedule_estimated"):
        schedule += " · timing estimated"
    if c.get("settled"):
        status = "settled"
    p = [f'<article class="commit-card" id="{esc(c["id"])}"><div class="commit-head"><h3>{esc(c["label"])}</h3>'
         f'<span class="commit-status {status}">{status}</span></div><div class="commit-amount">{amount_text}</div>'
         f'<p class="sub">{funding} · {schedule}</p>']
    if assumptions:
        p.append(f'<p class="sub">{esc(assumptions)}</p>')
    if c["source"] == "mortgage":
        facts = c.get("facts", {})
        p.append(f'<p class="sub">{money(facts.get("balance", 0))} balance · {facts.get("rate_pct", 0):g}% · '
                 f'{facts.get("term_years", 0):g} years remaining at this balance date. Principal + interest.</p>')
    elif c["source"] == "property_tax":
        p.append(f'<p class="sub">Home value: {money(c.get("facts", {}).get("home_value", 0))}'
                 + (' (inferred)' if c.get("facts", {}).get("inferred_value") else '') + '.</p>')
    if c.get('goal_id') and c['id'].startswith('charitable:'):
        p.append('<p><a href="/pages/goal_' + esc(c['goal_id']) + '.html">Edit charitable goal and reservation →</a></p>')
    elif rev:
        hidden = (f'<input type="hidden" name="cid" value="{esc(c["id"])}">'
                  f'<input type="hidden" name="revision" value="{rev}">'
                  f'<input type="hidden" name="back" value="{back}">')
        values = edit_values(c)
        # Show amount/terms first, then funding and timing. Blank = unchanged,
        # so saving a date never confirms an assumed amount by accident.
        order = [k for k in ("label", "home_value", "rate_pct", "term_years", "annual_amount", "amount",
                            "funding_source", "cadence", "next_due", "ends_on", "settled") if k in values]
        p.append('<details><summary>Edit details</summary><p class="sub">Enter only what you want to change. '
                 'Amounts and payment timing are confirmed separately.</p>'
                 f'<form method="POST" action="/commitments/update">{hidden}<div class="commit-fields">'
                 + ''.join(field(k, values[k], source=c["source"]) for k in order)
                 + '</div><button>Save changes</button></form></details>')
        if chat:
            p.append('<details><summary>Refine with AI</summary><p class="sub">Describe a change to this commitment. '
                     'Review the proposed values before saving.</p>'
                     f'<form method="POST" action="/commitments/preview">{hidden}'
                     f'<label>Change to {esc(c["label"])}<textarea name="instruction" required '
                     'placeholder="For example: the rate is 5% and ten years remain."></textarea></label>'
                     '<button class="secondary">Preview changes</button></form></details>')
    p.append('</article>')
    return ''.join(p)


def render_capital(m, answers=None, chat=False, proposals=()):
    cal = cash_calendar(m)
    rev = revision(answers) if answers is not None else None
    inflow_jump = '<a href="#inflows">Incoming money</a>' if (answers or {}).get("incoming") else ''
    p = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Capital &amp; Commitments</title><style>{CSS}</style></head><body><main class="wrap">'
         '<div class="eyebrow">The next twelve months</div><h1>Capital &amp; Commitments</h1>'
         f'<p class="sub">What your cash can cover, and what is already spoken for. Balance date: {cal["as_of"]}.</p>'
         f'<nav class="jump"><a href="#calendar">Cash calendar</a>{inflow_jump}<a href="#commitments">Edit commitments</a>'
         '<a href="#add">Add an obligation</a></nav><div class="stats">'
         f'<div class="stat"><span>Cash today</span><b>{money(cal["cash"])}</b></div>'
         f'<div class="stat"><span>Scheduled from portfolio</span><b>{money(cal["outflow"])}</b></div>'
         f'<div class="stat"><span>Other amounts reserved</span><b>{money(cal["held"])}</b></div>'
         f'<div class="stat"><span>Cash available to commit</span><b class="positive">{money(cal["available"])}</b></div></div>']
    if cal["shortfall"]:
        p.append(f'<p class="notice">The entered obligations exceed current cash by <b>{money(cal["shortfall"])}</b>. '
                 'Review payment timing and decide how to raise the cash before making another commitment.</p>')
    p.append('<p class="sub">This is a cash planning view. Pending inflows, future income, investment sales and returns '
             'are excluded. Outside-income payments are shown but do not draw on this cash balance. '
             'Estimated amounts and dates remain visible until you confirm them. Recurring schedules assume earlier payments were made; '
             'overdue one-time obligations stay reserved until settled.</p>')
    if cal["pending_tax_reserve"]:
        p.append(f'<p class="sub">{money(cal["pending_tax_reserve"])} of modeled tax is reserved against its linked '
                 'pending inflow. Both are excluded from today’s available cash. When the receipt is recorded as cash, '
                 'its tax reserve must remain set aside.</p>')
    if cal["tax_reserve"]:
        p.append(f'<p class="notice">{money(cal["tax_reserve"])} of the modeled tax reserve has no payment date. '
                 'It is held aside now. Add tax payments below to schedule that reserve; scheduled amounts use it first.</p>')
    if cal["outside"]:
        p.append('<p class="sub">Beyond this calendar, still reserved: ' + '; '.join(
            f'{esc(c["label"])} · {money(c["amount"])} · {esc(c["next_due"])}' for c in cal["outside"]) + '.</p>')
    if answers is not None:
        from officekit.render_inflows import inflow_card
        p.append(inflow_card(m, answers, rev, proposals))
    from officekit.render_deployment import render as deployment_links
    p.append(deployment_links(m, proposals, rev, exclude=[((answers or {}).get('incoming') or {}).get('id')]))
    p.append('<h2 id="calendar">Cash calendar</h2><div class="calendar"><table><thead><tr><th>Month</th>'
             '<th>Payments and reservations</th><th class="amount">From portfolio</th>'
             '<th class="amount">Unreserved cash left</th></tr></thead><tbody>')
    for row in cal["months"]:
        payments = ''.join(f'<div class="payment">{esc(x["label"])} · {money(x["amount"])}'
                          f'<small>{x["date"]} · {x["funding_source"]}'
                          + (' · overdue' if x.get("overdue") else '')
                          + (' · amount estimated' if x["status"] == "estimated" else '')
                          + (' · timing estimated' if x["schedule_estimated"] else '')
                          + (' · earmark' if x["source"] == "goal_reservation" else '')
                          + '</small></div>' for x in row["payments"]) or '<span class="empty">No scheduled payments</span>'
        if row["payments"]:
            n = len(row["payments"])
            summary = f'{n} payment' + ('s' if n != 1 else '')
            if any(x["status"] == "estimated" or x["schedule_estimated"] for x in row["payments"]):
                summary += ' · includes estimates'
            payments = '<details' + (' open' if row is cal["months"][0] else '') + (
                f'><summary style="cursor:pointer;color:#b1a5ff;margin-bottom:6px">{summary}</summary>{payments}</details>')
        p.append(f'<tr><td>{row["month"]}</td><td>{payments}</td><td class="amount">{money(row["outflow"])}</td>'
                 f'<td class="amount {"negative" if row["remaining"] < 0 else ""}">{money(row["remaining"])}</td></tr>')
    p.append('</tbody></table></div><h2 id="commitments">Your commitments</h2><div class="commit-grid">')
    p.extend(commitment_card(c, rev, chat) for c in m["d"].get("commitments", []))
    p.append('</div>')
    if rev:
        p.append('<h2 id="add">Add an obligation</h2><div class="commit-card"><p class="sub">Reserve an actual expense, '
                 'tax payment, capital call or a goal amount you have chosen to set aside. A goal reservation is an earmark, '
                 'not an extra payment; release it when you record the payment elsewhere. Settling an obligation releases '
                 'its schedule; account balances and modeled tax liabilities must still be updated from their sources.</p>'
                 f'<form method="POST" action="/commitments/add"><input type="hidden" name="revision" value="{rev}">'
                 '<div class="commit-fields"><label>Type<select name="source"><option value="recurring_expense">Recurring expense</option>'
                 '<option value="tax">Tax payment</option><option value="capital_call">Capital call</option>'
                 '<option value="goal_reservation">Goal reservation</option></select></label>'
                 + ''.join(field(k, adding=True) for k in ("label", "amount", "cadence", "next_due", "funding_source", "ends_on"))
                 + '</div><button>Add commitment</button></form></div>')
    p.append('</main></body></html>')
    return ''.join(p)


def render_preview(record, patch, token, note=""):
    before = edit_values(record)
    rows = ''.join(f'<tr><td>{esc(LABELS[k])}</td><td>{esc(str(before.get(k, "")))}</td>'
                   f'<td>{esc(str(v))}</td></tr>' for k, v in patch.items())
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Review commitment change</title><style>{CSS}</style></head><body><main class="wrap review">'
            f'<div class="eyebrow">Review before saving</div><h1>{esc(record["label"])}</h1>'
            f'<p>{esc(note)}</p><p class="sub">Only these fields on this commitment will change.</p>'
            f'<table><tr><th>Field</th><th>On file</th><th>Proposed</th></tr>{rows}</table>'
            f'<form method="POST" action="/commitments/apply"><input type="hidden" name="token" value="{token}">'
            '<button>Apply these changes</button> <a href="/pages/capital.html">Cancel</a></form></main></body></html>')
