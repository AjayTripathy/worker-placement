"""Read-only matched-trial summary, suitable for the local office pages folder."""
from html import escape
import json


def render(report):
    def text(value):
        return escape(str(value))
    def money(value):
        return "—" if value is None else f"${value:,.2f}"
    def details(title, value):
        return '<details><summary>'+text(title)+'</summary><pre>'+text(json.dumps(value, indent=2))+'</pre></details>'
    comparisons = []
    for phase, entries in report["comparisons"].items():
        for name, row in entries.items():
            interval = row["interval_usd"]
            comparisons.append('<tr>'+''.join('<td>'+text(v)+'</td>' for v in
                (phase, name.replace('_', ' '), row["sessions"], money(row["mean_usd"]),
                 ' to '.join(money(v) for v in interval) if interval else 'Insufficient sessions'))+'</tr>')
    coverage = []
    for variant, row in report["operational"].items():
        coverage.append('<tr>'+''.join('<td>'+text(v)+'</td>' for v in
            (variant, row["model_attempts"], row["candidate_days_missing_accepted_forecast"], row["unresolved_takes"],
             money(row["assumed_all_attempt_cost_usd"]), money(row["resolved_trading_subtotal_less_all_attempt_costs_usd"])))+'</tr>')
    limitations = ''.join('<li>'+text(v)+'</li>' for v in report["limitations"])
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>0DTE edge evaluation</title>
<style>body{font:16px system-ui;max-width:1120px;margin:40px auto;padding:0 22px;color:#182e36;background:#f6f8f8}
h1,h2{letter-spacing:-.02em}table{border-collapse:collapse;width:100%;background:white;margin:18px 0}
td,th{padding:10px;text-align:left;border-bottom:1px solid #dae2e3}section{overflow:auto}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:15px}details{margin:15px 0}li{margin:10px 0}
.notice{padding:16px;border-left:4px solid #926017;background:#fff4dd}a{color:#00675b}</style></head><body>
<p><a href="odte_arms.html">← Original factorial arms</a></p><h1>Does the research add an edge?</h1>
<p class="notice">Prospective paper research. No proven investment edge, capital allocation or automatic promotion.
The original frozen trial remains independent.</p>
<p>Two fresh calls to the same model receive the same frozen premarket prices and calendar. One also receives
the source excerpts. A numerical control trains only on prior resolved sessions. All forecast stop risk,
severe-loss risk and gross return per dollar of entry risk. A fixed rule tests whether expected return pays the assumed costs.</p>
<p>Primary comparison: text versus no text. First 60 source decision sessions are discovery; the next 60 are
prospective validation. Missing outcomes do not move those boundaries. Confidence intervals are approximate
block-bootstrap descriptions, not permission to stop early and declare a winner.</p>''' + (
        f'<p>Discovery decisions: {report["discovery_decision_sessions"]} · Validation decisions: '
        f'{report["validation_decision_sessions"]} · Incomplete runs: {report["incomplete_runs"]}</p>'
        '<h2>Matched comparisons</h2><section><table><tr><th>Phase</th><th>Comparison</th><th>Sessions</th>'
        '<th>Mean daily improvement</th><th>Approximate interval</th></tr>'+''.join(comparisons)+'</table></section>'
        '<h2>Coverage and costs</h2><p>These subtotals charge every recorded model attempt, including failures, '
        'but omit unknown trading outcomes. They are not a complete realized return.</p><section><table><tr>'
        '<th>Variant</th><th>Attempts</th><th>Missing forecasts at candidates</th><th>Unresolved takes</th>'
        '<th>Assumed research cost</th><th>Known trading subtotal less all attempts</th></tr>'+''.join(coverage)+'</table></section>'
        +details('Run status and failures', report["run_directory"])
        +details('Calibration by submitter, agent and model', report["calibration_by_submitter_agent"])
        +details('Equal-participation controls', report["equal_participation_controls"])
        +details('Cost sensitivity', report["operational"])
        +details('Original arms: comparison families and missing-path stress scenarios', report["existing_arm_audit"])
        +details('Session decisions and lineage', report["sessions"])
        +'<h2>What remains untested</h2><ul>'+limitations+'</ul><p>Protocol: '+text(report["protocol"])
        +'</p></body></html>')
