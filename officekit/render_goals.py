"""Goals destination for both transports; shared evaluations, editors and intake."""
from officekit.render_goal import CSS
from officekit.render_office import _goals_panel


def render_goals(m, *, chat=False):
    goals = [g for g in m['d'].get('goals', []) if not g.get('implicit')]
    data = dict(m['d'], goals=goals)
    panel = _goals_panel(m, data, m['assets'], m['sleeves'], 0, '/goals', False,
                         back='goals', natural_language=False)
    empty = ('<p class="empty">No goals yet. Describe what you want your money to make possible, '
             'or add a goal with the fields below.</p>' if not goals else '')
    connection = ('' if chat else '<p class="key-note" id="goal-key-note">'
                  'Connect an AI agent in <a href="/settings" target="_blank" rel="noopener">Office settings</a> '
                  'to turn your words into goals. You can use the goal fields below now.</p>')
    disabled = '' if chat else ' disabled aria-describedby="goal-key-note"'
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Goals — Worker Placement</title>
<style>''' + CSS + '''
:root{--ink:#e8ebee;--dim:#9aa4b0;--line:#242a31;--emerald:#35c98f;--panel2:#1a1f25}
*{box-sizing:border-box}.wrap{max-width:1040px}h1{font-size:32px;letter-spacing:-.035em}
.eyebrow{color:#35c98f;font-size:11px;letter-spacing:.15em;text-transform:uppercase;margin:0 0 8px}
.intro{font-size:15px;max-width:700px}.composer{border-color:#365647;margin:24px 0}
.composer h2{font-size:18px;text-transform:none;letter-spacing:-.02em;color:var(--ink);margin:0 0 6px}
.composer label{display:block;font-size:12px;margin:18px 0 6px;color:var(--dim)}
.composer textarea{display:block;width:100%;min-height:112px;resize:vertical;background:#0b0e12;color:var(--ink);border:1px solid #3a454e;border-radius:10px;padding:12px;font:inherit}
.composer textarea::placeholder{color:#84919d}.composer button{background:#35c98f;color:#08110d;border:0;border-radius:8px;padding:11px 18px;font-weight:650;cursor:pointer}
.composer button:disabled{opacity:.45;cursor:not-allowed}.composer .actions{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-top:12px}
.hint,.key-note,.empty,.g{font-size:12px;color:var(--dim)}.key-note{margin-bottom:0}
.ph{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.ph h3{font-size:18px;margin:0}
.goalrow>div:first-child{flex:1;min-width:0}.goal-title{font-size:16px}.goal-target,.goal-detail{font-size:12px;color:var(--dim)}
.goal-status{font-size:11px;font-weight:600}.goal-measures{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;margin:10px 0}
.liqrow{display:flex;justify-content:space-between;gap:12px;margin:8px 0}
.entry-tools{border-top:1px solid var(--line);margin-top:18px;padding-top:16px}.entry-tools summary{color:var(--emerald);cursor:pointer}
.grow4 input,.grow4 select{min-width:0;width:100%}.grow4 button{grid-column:1/-1;justify-self:start}
:focus-visible{outline:2px solid #35c98f;outline-offset:3px}
@media(max-width:600px){.wrap{padding:22px 16px 60px}h1{font-size:28px}.grow4{grid-template-columns:1fr 1fr}.goalrow{flex-wrap:wrap}.goal-status{margin-left:auto}}
</style></head><body><main class="wrap">
<p class="eyebrow">Life planning</p><h1>Goals</h1>
<p class="sub intro">What do you want your capital to make possible? Plan the milestones, see what fits, and connect each goal to a strategy.</p>
<section class="panel composer" aria-labelledby="describe-goal"><h2 id="describe-goal">Describe a goal in your own words</h2>
<p class="sub">Include amounts and timing when you know them. You can describe several goals at once.</p>
<form method="POST" action="/goals/add"><input type="hidden" name="back" value="goals">
<label for="goalnl">What would you like to plan for?</label>
<textarea id="goalnl" name="nl" required maxlength="8000" placeholder="I want to retire in 2045 spending $120,000 a year, and set aside $300,000 for college by 2038."></textarea>
<div class="actions"><button type="submit"''' + disabled + '''>Add goals</button><a href="#add-goal" onclick="document.getElementById('add-goal').open=true">Use goal fields instead →</a></div>
''' + connection + '''</form></section>''' + empty + panel + '''
<p class="note">Mortgage payments, lifestyle spending and other recurring commitments live in <a href="/pages/capital.html">Capital &amp; Commitments →</a></p>
</main></body></html>'''
