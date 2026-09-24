"""Research and prediction calibration, shared by local and hosted offices."""
from officekit.render_research import esc, page
from officekit_research import index
from officekit_research.cases import digest


def ledger_revision(folder):
    from officekit_research.predictions import load
    return digest({'predictions': load(folder), 'outcomes': index.load_outcomes(folder),
                   'research': [(r['id'], r['as_of']) for r in index.query(folder, kind='general')]})


def render(folder, revision):
    token = ledger_revision(folder)
    rows = index.forecast_rows(folder)
    body = ('<p><a href="/research">Research library</a> · <a href="/pages/research_catalog.html">Ticker catalog</a></p>'
            '<p>Brier score measures explicit binary predictions: (probability − outcome)². Lower is better; 0 is perfect and 1 is worst. '
            'Research verdicts and conviction ratings are not probabilities and are not scored.</p>'
            '<p>Attribution belongs to the original submitter and forecasting agent. Anonymous imports stay anonymous. '
            'A claimed identity has not been verified. Private predictions stay in this office.</p>')
    for group, title in [('submitter', 'By submitter'), ('agent', 'By forecasting agent'), ('submitter_agent', 'By submitter and agent')]:
        board = index.summarize(rows, group)
        body += '<h2>' + title + '</h2><div style="overflow:auto"><table><thead><tr><th>Identity</th><th>Resolved / total</th><th>Pending (overdue)</th><th>Brier</th><th>Base-rate Brier</th><th>Pooled Brier</th></tr></thead><tbody>'
        for r in board:
            number = lambda key: '—' if r[key] is None else str(r[key])
            body += (f'<tr><td>{esc(r[group] or "Anonymous / unknown")}<br><small>{esc(", ".join(r["attribution"]))}</small></td>'
                     f'<td>{r["resolved"]} / {r["forecasts"]}</td><td>{r["pending"]} ({r["overdue_unresolved"]})</td>'
                     f'<td>{number("brier")}</td><td>{number("brier_base_rate")}</td><td>{number("pooled_brier")}</td></tr>')
        body += '</tbody></table></div>' if board else '</tbody></table></div><p>No explicit forecasts recorded yet.</p>'
    body += ('<p class="muted">Pooled Brier smooths a group toward other resolved forecasts with up to 20 observations of weight. '
             'It is descriptive, not a confidence interval. Sparse or correlated samples cannot establish agent skill. '
             'Scores never gate research admission or dispatch. Skill versus the declared base rate requires at least 20 resolutions.</p>')
    body += '<h2>Forecasts and sourced outcomes</h2>'
    seen = set()
    for r in rows:
        if r['id'] in seen:
            continue
        seen.add(r['id'])
        state = 'Pending' if r['outcome'] is None else ('True' if r['outcome'] else 'False')
        body += (f'<details><summary>{esc(r["symbol"])} · {esc(state)} · due {esc(r["resolve_by"])}</summary>'
                 f'<p>{esc(r["statement"])}</p><p>Probability {r["probability"]:.1%}; base rate {r["base_rate"]:.1%}. '
                 f'Captured {esc(r["as_of"])}. Agent {esc(r["agent"])}.</p>')
        if r['source_url']:
            body += f'<p><a href="{esc(r["source_url"])}" rel="noreferrer">Outcome source</a> · {esc(r["resolved_at"])}</p>'
        body += (f'<form method="POST" action="/research/resolve"><input type="hidden" name="ledger_revision" value="{token}">'
                 f'<input type="hidden" name="forecast_id" value="{esc(r["id"])}">'
                 '<label>Outcome <select name="outcome"><option value="true">True</option><option value="false">False</option></select></label>'
                 '<label>Public source that settles the stated criteria <input name="source_url" type="url" required></label>'
                 '<label>Explanation (required for a correction) <input name="note" maxlength="600"></label>'
                 '<button>Record sourced outcome</button></form></details>')
    body += ('<details><summary>Register an explicit prediction</summary><p>Register before the outcome is known. '
             'Probability, criteria and identity are immutable. Repeated submissions for the same submitter, agent and event are refused.</p>'
             f'<form method="POST" action="/research/predict"><input type="hidden" name="ledger_revision" value="{token}">')
    fields = [('symbol', 'Ticker / subject'), ('event_key', 'Stable event key (subject + event + horizon)'),
              ('statement', 'Prediction'), ('resolution_criteria', 'Exact criteria for true or false'),
              ('submitter', 'Submitter identity'), ('agent', 'Agent identity / profile'), ('model', 'Model and version'),
              ('protocol', 'Research protocol version'), ('strategy', 'Strategy served (optional)')]
    for name, label in fields:
        body += f'<label>{label}<input name="{name}" maxlength="{1200 if name in {"statement", "resolution_criteria"} else 200}" {"required" if name != "strategy" else ""}></label>'
    body += ('<label>Probability (0–1)<input name="probability" type="number" min="0" max="1" step="any" required></label>'
             '<label>Declared base rate (0–1)<input name="base_rate" type="number" min="0" max="1" step="any" required></label>'
             '<label>Resolve by<input name="resolve_by" type="date" required></label><button>Register prediction</button></form></details>')
    return page(body, revision, 'Research calibration')
