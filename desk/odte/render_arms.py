"""Read-only local experiment view; never an order entry surface."""
from html import escape
import json


def render(report):
    def text(value):
        return escape(str(value))

    def money(value):
        return "—" if value is None else f"{'−' if value < 0 else ''}${abs(value):,.2f}"

    def number(value):
        return "—" if value is None else f"{value:.4g}"

    def dump(value):
        return '<pre>' + text(json.dumps(value, indent=2, ensure_ascii=False)) + '</pre>'

    def stats_cells(stats):
        return f'<td>{stats["sessions"]}</td><td>{money(stats["mean_usd"])}</td><td>{money(stats["total_usd"])}</td>'

    allocation = report.get("latest_allocation")
    readiness = report.get("readiness")
    health = ''
    if readiness:
        blocked = readiness["status"] == "blocked"
        failures = [f'{item["name"]}: {item["error"]}' for item in readiness["checks"] if item["status"] == "blocked"]
        health = '<div class="card" style="border-color:' + ('#b3261e' if blocked else '#006956') + '"><strong>' \
            + ('Research blocked — action required' if blocked else 'Protocol preflight passed') + '</strong><p>' \
            + text('; '.join(failures) if failures else 'Source hashes and registration times checked. This check does not guarantee model or market-data availability.') \
            + '</p><small>' + text(readiness['checked_at']) + '</small></div>'
    start = report.get("start_date", "not registered")
    status = (f'{text(allocation["status"].replace("_", " "))} · '
              f'{allocation["training_sessions"]} common training sessions · '
              f'selected {text(allocation["selected_arm"])}'
              if allocation else f'Waiting for the first eligible entry on or after {text(start)}. No results yet.')
    coverage = (f'<p>{allocation.get("incomplete_sessions", 0)} prior sessions excluded for missing outcomes; '
                f'{allocation.get("warmup_remaining", 0)} more common sessions needed before adaptation. '
                'See selector inputs for missing counts by arm.</p>' if allocation else '')
    rows, details = [], []
    for name, arm in report.get("arms", {}).items():
        weight = (allocation or {}).get("probabilities", {}).get(name)
        weight_label = "—" if weight is None else f"{100*weight:.1f}%"
        vs = arm["vs_t3"]
        rows.append(f'<tr data-name="{text(name)}" data-label="{text(arm["label"])}" '
                    f'data-lift="{vs["mean_usd"] if vs["mean_usd"] is not None else -1e99}">'
                    f'<td><a href="#{text(name)}">{text(name)}</a></td><td>{text(arm["label"])}</td>'
                    f'<td>{arm["takes"]} / {arm["skips"]} / {arm["unavailable"]}</td>'
                    f'{stats_cells(arm["stats"])}<td>{money(vs["mean_usd"])} <small>(n={vs["sessions"]})</small></td>'
                    f'<td>{weight_label}</td></tr>')
        days = []
        for day in reversed(arm["daily"]):
            legs = ", ".join(f'{side.upper()} {leg["strike"]:g}{leg["right"]}' for side, leg in day["candidate"]["legs"].items())
            gates = "".join(f'<tr><td>{text(factor)}</td><td>{text(json.dumps(gate["value"]))}</td>'
                            f'<td>{"missing" if gate["pass"] is None else "pass" if gate["pass"] else "fail"}</td></tr>'
                            for factor, gate in day["gates"].items())
            features = "".join(f'<tr><td>{text(k)}</td><td>{number(v)}</td></tr>' for k, v in day["features"].items())
            days.append(f'<details><summary>{text(day["date"])} · {text(day["decision"])} · net {money(day["net_pnl_usd"])}'
                        f'{" · selected" if day["selected"] else ""}</summary>'
                        f'<p>{text(legs)} · entry credit {number(day["candidate"]["credit"])} points · '
                        f'{text(day["entry_at"])}. Counterfactual gross: {money(day["counterfactual_gross_usd"])}.</p>'
                        f'<p>Selection probability: {100*day["weight"]:.2f}%. '
                        f'Missing: {text(", ".join(day["missing"]) or "none")}. '
                        f'Failed filters: {text(", ".join(day["failed"]) or "none")}.</p>'
                        f'<div class="columns"><div><h4>Frozen gates</h4><table>{gates}</table></div>'
                        f'<div><h4>Entry features</h4><table>{features}</table></div></div>'
                        '<details><summary>News mechanisms and coverage</summary>' + dump({
                            "reasons": day["forecast_reasons"], "error": day["forecast_error"]}) + '</details>'
                        '<details><summary>Record lineage</summary>' + dump({k: day[k] for k in
                        ("forecast_id", "decision_id", "outcome_id")}) + '</details></details>')
        contexts = ''.join(f'<tr><td>{text(k)}</td><td>{v["stats"]["sessions"]}</td>'
                           f'<td>{money(v["stats"]["mean_usd"])}</td><td>{money(v["vs_t3"]["mean_usd"])} '
                           f'(n={v["vs_t3"]["sessions"]})</td></tr>' for k, v in arm["by_context"].items())
        details.append(f'<details id="{text(name)}" class="arm"><summary>{text(name)} · {text(arm["label"])}</summary>'
                       f'<p>Worst session: {money(arm["stats"]["worst_usd"])}. '
                       f'Drawdown across observed outcomes: {money(arm["stats"]["max_drawdown_usd"])}. '
                       f'Standard error of paired mean versus T3: {money(vs["standard_error_usd"])}.</p>'
                       + ('<h4>By volatility and trend context</h4><table><thead><tr><th>Context</th><th>Sessions</th>'
                          '<th>Mean net</th><th>Paired mean vs T3</th></tr></thead><tbody>'+contexts+'</tbody></table>' if contexts else '')
                       + ("".join(days) or '<p>No sealed entry decisions yet.</p>') + '</details>')
    effects = "".join(f'<tr><td>{text(name)}</td><td>{text(effect["description"])}</td>'
                      f'{stats_cells(effect["stats"])}</tr>' for name, effect in report.get("factor_effects", {}).items())
    selector = report.get("selector_stats", {})
    selector_vs = report.get("selector_vs_t3", {})
    sessions = "".join(f'<li>{text(s["date"])}: {text(s["status"])}'
                       f'{" — " + text(s["error"]) if s.get("error") else ""}</li>' for s in report.get("sessions", []))
    limitations = "".join(f'<li>{text(line)}</li>' for line in report.get("limitations", []))
    return ('''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>0DTE research arms</title>
<style>
:root{color-scheme:light;--ink:#182c31;--muted:#526b70;--line:#d6e1df;--accent:#006956}
*{box-sizing:border-box}body{margin:0;background:#f5f7f4;color:var(--ink);font:15px/1.6 system-ui,sans-serif}
main{max-width:1400px;margin:auto;padding:32px}h1{font-size:36px;margin:14px 0 4px;letter-spacing:-1px}
h2{font-size:22px;margin:28px 0 12px}h4{margin:12px 0}p{max-width:1050px}a{color:var(--accent)}
.tag{font-size:12px;letter-spacing:1px;font-weight:700;color:var(--accent)}.muted,small{color:var(--muted)}
.card,details.arm{background:white;border:1px solid var(--line);border-radius:12px;padding:20px;margin:16px 0}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th{text-align:left;color:var(--muted)}
td,th{padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:top}td:first-child{white-space:nowrap}
summary{cursor:pointer;font-weight:650;padding:10px 0}details:target{outline:2px solid var(--accent)}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}.columns{display:grid;grid-template-columns:1fr 1fr;gap:28px}
select,input{padding:9px;background:white;border:1px solid var(--line);border-radius:6px;margin:4px 16px 8px 0}
@media(max-width:750px){main{padding:18px}h1{font-size:28px}.columns{grid-template-columns:1fr}td,th{padding:8px}}
</style></head><body><main><a href="/#view=%2Fpages%2Foffice.html">← Office</a>
<div class="tag">SHADOW RESEARCH · FULL-INFORMATION EXPERTS</div><h1>Which filters earn their keep?</h1>
<p>Sixteen combinations share the same first eligible T3 condor. Each can take it or stay in cash.
The selector records one hypothetical choice before the outcome, while all arms retain their own paper results.</p>
''' + health + f'<div class="card"><strong>{status}</strong><p>Selected-policy net: {money(selector.get("total_usd"))} '
        f'over {selector.get("sessions", 0)} resolved sessions. Paired mean versus T3: '
        f'{money(selector_vs.get("mean_usd"))} (n={selector_vs.get("sessions", 0)}). '
        f'Unresolved trade paths: {report.get("unresolved_sessions", 0)}.</p>' + coverage + \
        '<p class="muted">Uniform weights for the first 20 common completed sessions; thereafter, '
        'pooled context estimates and a 20% uniform mixture. Every arm is observed, so sampling adds no information. '
        'The selector is a paper simulation and provides no evidence of live allocation performance.</p></div>' \
        '<h2>Arm directory</h2><label>Find an arm <input id="search" type="search" placeholder="e.g. news or T12"></label>' \
        '<label>Order <select id="sort"><option value="id">Arm ID</option><option value="lift">Paired mean versus T3</option></select></label>' \
        '<div class="scroll card"><table><thead><tr><th>Arm</th><th>Filters</th><th>Take / skip / unavailable</th>' \
        '<th>Resolved n</th><th>Mean net</th><th>Total net</th><th>Paired mean vs T3</th><th>Latest weight</th></tr></thead>' \
        '<tbody id="directory">' + ''.join(rows) + '</tbody></table></div>' \
        '<p class="muted">Arm totals can cover different dates. Use paired comparisons and their sample counts. '
        'Sorting finds candidates for investigation; it does not establish a winner. Costs assume $7.20 per trade '
        'and $1 for news research when available, including a deliberate news skip. Missing values are not zero returns.</p>' \
        '<h2>What did adding each filter change?</h2><p>For each day, compare every available pair of combinations '
        'that differs only by this filter, then average those differences. A day counts once, however many combinations were observed.</p>' \
        '<div class="scroll card"><table><thead><tr><th>Filter</th><th>Rule</th><th>Sessions</th><th>Mean increment</th>' \
        '<th>Total increments</th></tr></thead><tbody>' + effects + '</tbody></table></div>' \
        '<h2>Drill into decisions and features</h2>' + ''.join(details) \
        + '<details class="card"><summary>Latest selector inputs and probabilities</summary>' + dump(allocation) + '</details>' \
        + '<details class="card"><summary>Collection status</summary><ul>' + (sessions or '<li>No sessions recorded yet.</li>') + '</ul></details>' \
        + '<details class="card"><summary>Interpretation and limits</summary><ul>' + limitations + '</ul></details>' \
        + f'<p class="muted">Built {text(report.get("built_at", "—"))} · protocol <code>{text(report.get("protocol", "—"))}</code></p>' \
        + '''</main><script>
const body=document.getElementById('directory');
const rows=Array.from(body.children);
function update(){const q=document.getElementById('search').value.toLowerCase();
const byLift=document.getElementById('sort').value==='lift';
rows.sort((a,b)=>byLift?Number(b.dataset.lift)-Number(a.dataset.lift):rowsOrder.get(a)-rowsOrder.get(b));
for(const r of rows){r.hidden=!(r.dataset.name+' '+r.dataset.label).toLowerCase().includes(q);body.append(r)}}
const rowsOrder=new Map(rows.map((r,i)=>[r,i]));
document.getElementById('search').addEventListener('input',update);
document.getElementById('sort').addEventListener('change',update);
for(const a of document.querySelectorAll('#directory a'))a.addEventListener('click',()=>{
const el=document.getElementById(a.getAttribute('href').slice(1));if(el)el.open=true});
</script></body></html>''')
