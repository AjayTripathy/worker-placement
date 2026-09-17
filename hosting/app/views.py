"""Escaped hosted views; uploaded HTML and user scripts are never served."""
import base64
from html import escape as esc
import json
from urllib.parse import urlencode
from officekit.render_landing import page

def account(email,offices):
    rows=''.join('<article><h2>'+esc(o['name'])+'</h2><p>Balances as of '+esc(o['as_of'])+'</p><a class="text-link" href="'+esc(o['path'],quote=True)+'">Open hosted office ↗</a></article>' for o in offices)
    if not rows:rows='<article><h2>Bring your office.</h2><p>In your local app, choose <strong>Host office</strong>. Sign in, review the saved files, then upload your office.</p><p>Your local copy stays available. Prefer the terminal? Use <code>./wp login</code> and <code>./wp migrate --dir /path/to/office</code>.</p></article>'
    content='<main id="main" class="subpage"><p class="eyebrow">YOUR WORKSPACE</p><h1>Welcome home.</h1><p>'+esc(email)+'</p><div id="auth-error" role="alert" class="notice error" hidden></div><div class="account-grid">'+rows+'<article><h2>Start with the research.</h2><p>The SignalOS library is included with every account. Explore its datasets, evidence and findings.</p><a class="text-link" href="/app/research">Open research library ↗</a></article></div></main>'
    return page('Your workspace',content,auth_script=True,signed_in=True)

def device(device,code,email=None):
    if email:
        panel='<p>Connect this local device to <strong>'+esc(email)+'</strong>.</p><p>Only approve if this matches the code shown in your local app or by your own <code>./wp login</code> command.</p><p class="device-code">'+esc(code)+'</p><form id="device-form"><input type="hidden" name="device" value="'+esc(device,quote=True)+'"><input type="hidden" name="code" value="'+esc(code,quote=True)+'"><button class="button primary">Connect this device</button></form><p>Connecting signs this machine in. Return to your local app to review your saved files and choose <strong>Upload my office</strong>, or run <code>./wp migrate</code>.</p>'
    else:panel='<p>Sign in to connect your local app. Return here after verifying your email.</p><p class="device-code">'+esc(code)+'</p><a class="button primary" href="/signup">Sign in with email ↗</a>'
    return page('Connect your device','<main id="main" class="subpage"><p class="eyebrow">LOCAL LOGIN</p><h1>One account.<br>Your machine.</h1><div id="auth-error" class="notice error" role="alert" hidden></div><div id="auth-status" class="notice" role="status" hidden></div>'+panel+'</main>',auth_script=True,signed_in=bool(email))

def office(receipt,record):
    docs={k:base64.b64decode(v) for k,v in record['documents'].items()}
    data=json.loads(docs['balance_sheet.json']);answers=json.loads(docs['answers.json'])
    sleeves=data.get('sleeves',[])
    money=lambda x:'${:,.0f}'.format(float(x or 0))
    assets=sum(s.get('value',0) for s in sleeves if s.get('kind')=='asset')
    debts=sum(s.get('value',0) for s in sleeves if s.get('kind')=='liability')
    rows=''.join('<tr><td>'+esc(str(s.get('name','')) )+'</td><td>'+esc(str(s.get('category','')).replace('_',' '))+'</td><td>'+money(s.get('value'))+'</td></tr>' for s in sleeves)
    goals=''.join('<li>'+esc(str(g.get('label',g.get('kind','Goal'))))+((' · '+esc(str(g['date']))) if g.get('date') else '')+'</li>' for g in data.get('goals',[])) or '<li>No saved goals.</li>'
    artifacts=''.join('<li><a href="'+receipt['path']+'/document?'+urlencode({'path':n})+'">'+esc(n)+'</a></li>' for n in sorted(docs))
    content='<main id="main" class="subpage wide"><p class="eyebrow">HOSTED OFFICE · '+esc(str(data['as_of']))+'</p><h1>'+esc(receipt['name'])+'</h1><p class="notice">Your verified office snapshot is hosted. This first release supports viewing and export; editing, broker reconnects and cloud research runs are coming next. Continue making changes locally and migrate a new revision when ready.</p><div class="account-grid"><article><h2>Assets</h2><strong>'+money(assets)+'</strong></article><article><h2>Liabilities</h2><strong>'+money(debts)+'</strong></article></div><h2>Accounts and assets</h2><div class="table-scroll"><table><thead><tr><th>Name</th><th>Category</th><th>Saved value</th></tr></thead><tbody>'+rows+'</tbody></table></div><h2>Your goals</h2><ul>'+goals+'</ul><h2>Saved documents & retained research</h2><p>Original documents, financial facts and source dates are preserved. Downloads are private to your account.</p><ul class="document-list">'+artifacts+'</ul><p><a class="text-link" href="'+receipt['path']+'/export">Export the complete office ↗</a></p><p><a class="text-link" href="/app/research">Explore the included SignalOS research ↗</a></p><details><summary>Migration receipt</summary><pre>'+esc(json.dumps(receipt,indent=2))+'</pre></details></main>'
    return page(receipt['name'],content,signed_in=True,auth_script=True)

def research_index(catalog,area=None,entries=(),query='',offset=0):
    if area:
        title=next(a['title'] for a in catalog['areas'] if a['id']==area)
        matches=[e for e in entries if query.lower() in e['path'].lower()]
        rows=''.join('<li><a href="/app/research/document?'+urlencode({'area':area,'path':e['path']})+'">'+esc(e['path'])+'</a><small>'+str(e['size'])+' bytes</small></li>' for e in matches[offset:offset+100])
        next_link='<a class="text-link" href="/app/research?'+urlencode({'area':area,'q':query,'offset':offset+100})+'">Next 100 →</a>' if offset+100<len(matches) else ''
        body='<h1>'+esc(title.replace('verticals/','').replace('_',' '))+'</h1><form method="get"><input type="hidden" name="area" value="'+esc(area,quote=True)+'"><label for="query">Find a file or topic</label><input id="query" name="q" value="'+esc(query,quote=True)+'" maxlength="200"><button class="button outline">Search</button></form><p>'+str(len(matches))+' research files · showing '+str(offset+1 if matches else 0)+'–'+str(min(offset+100,len(matches)))+'</p><ul class="document-list">'+rows+'</ul>'+next_link
    else:
        body='<h1>Your research<br>starting point.</h1><p>SignalOS findings, datasets and source code, included with every account. These are research records with their original dates and limitations; inclusion is not an investment recommendation.</p><div class="account-grid">'+''.join('<article><h2>'+esc(a['title'].replace('verticals/','').replace('_',' '))+'</h2><p>'+str(a['files'])+' files · '+str(round(a['bytes']/1048576,1))+' MiB</p><a class="text-link" href="/app/research?area='+esc(a['id'],quote=True)+'">Explore ↗</a></article>' for a in catalog['areas'])+'</div>'
    return page('Research library','<main id="main" class="subpage wide"><p class="eyebrow">SHARED RESEARCH LIBRARY</p>'+body+'<p>Seed revision '+esc(catalog['revision'][:12])+'. Research stays read-only; your office records remain private.</p><a href="/app">Return to your workspace</a></main>',signed_in=True,auth_script=True)
