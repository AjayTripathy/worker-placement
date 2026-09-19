"""Escaped hosted views; uploaded HTML and user scripts are never served."""
import base64
from html import escape as esc
import json
from urllib.parse import urlencode
from officekit.render_landing import page

def account(email,offices):
    rows=''.join('<article><h2>'+esc(o['name'])+'</h2><p>Balances as of '+esc(o['as_of'])+'</p><a class="text-link" href="'+esc(o['path'],quote=True)+'">Open hosted office ↗</a></article>' for o in offices)
    rows='<article class="bring-office-card"><h2>Bring your office.</h2><p>Choose your saved office folder and bring your accounts, goals and retained research online. Your local copy stays available.</p><a class="button primary" href="/app/import">Bring an office ↗</a></article>'+rows
    content='<main id="main" class="subpage"><p class="eyebrow">YOUR WORKSPACE</p><h1>Welcome home.</h1><p>'+esc(email)+'</p><div id="auth-error" role="alert" class="notice error" hidden></div><div class="account-grid">'+rows+'<article><h2>Start with the research.</h2><p>The SignalOS library is included with every account. Explore its datasets, evidence and findings.</p><a class="text-link" href="/app/research">Open research library ↗</a></article></div></main>'
    return page('Your workspace',content,auth_script=True,signed_in=True)


def bring_office(email):
    content = '''<main id="main" class="subpage office-import"><p class="eyebrow">YOUR OFFICE, HOSTED</p>
<h1>Bring your office.</h1><p>Same accounts, goals and research. Choose your saved office folder, review the files, and open it online.</p>
<p class="import-account">Uploading to <strong>''' + esc(email) + '''</strong> · <a href="/app">Back to your workspace</a></p>
<div id="auth-error" class="notice error" role="alert" hidden></div>
<div id="import-status" class="notice" role="status" aria-live="polite" hidden></div>
<section class="import-panel" aria-labelledby="choose-title"><p class="eyebrow">01 · CHOOSE</p><h2 id="choose-title">Your saved office folder</h2>
<p>Choose the folder containing <code>answers.json</code> and <code>balance_sheet.json</code>. This is the data folder used by your local app, usually named <code>office</code>.</p>
<label for="office-folder">Select a folder on this computer</label><input id="office-folder" type="file" webkitdirectory directory multiple aria-describedby="folder-note">
<p id="folder-note" class="fine-print">Selecting a folder only prepares a review in your browser. Nothing uploads until you choose Upload and open office. Up to 64 MiB and 1,024 saved documents.</p>
<p id="folder-unsupported" class="notice" hidden>This browser cannot select folders. Open this page in a desktop browser, or use <a href="http://127.0.0.1:8787/hosting" target="_blank" rel="noopener">Hosting &amp; sync in your local app</a>.</p></section>
<section class="import-panel" id="import-review" aria-labelledby="review-title" hidden><p class="eyebrow">02 · REVIEW</p><h2 id="review-title">What will come with you</h2>
<p id="import-summary"></p><p>Includes saved financial records and retained research. Credentials, generated pages and the Git checkout are excluded. Every hosted account also includes the shared SignalOS research library.</p>
<details><summary>Review selected documents</summary><ul class="document-list" id="import-files"></ul></details>
<div id="import-replace" class="notice" hidden><p id="replace-summary"></p><a id="replace-current" href="/app" target="_blank" rel="noopener">Review the current hosted office ↗</a><label class="import-check"><input id="replace-confirm" type="checkbox">Replace this hosted office with the selected saved copy.</label><p>Changes made online since this copy was saved will be replaced. Your hosted connection keys are kept.</p></div>
<div class="import-actions"><button class="button primary" id="upload-office" type="button">Upload and open office ↗</button><button class="button outline" id="cancel-import" type="button" hidden>Stop upload</button></div>
<progress id="import-progress" max="100" value="0" aria-label="Office upload progress" hidden></progress>
<p class="fine-print">Your local files stay in place. You can turn on automatic sync later from the local app’s Hosting &amp; sync page.</p></section>
<noscript><p class="notice">Enable JavaScript to review and upload your office folder.</p></noscript>
</main><script src="/public/office-import.js" defer></script>'''
    return page('Bring your office', content, auth_script=True, signed_in=True)

def device(device,code,email=None):
    if email:
        panel='<p>Connect this local device to <strong>'+esc(email)+'</strong>.</p><p>Only approve if this matches the code shown in your local app or by your own <code>./wp login</code> command.</p><p class="device-code">'+esc(code)+'</p><form id="device-form"><input type="hidden" name="device" value="'+esc(device,quote=True)+'"><input type="hidden" name="code" value="'+esc(code,quote=True)+'"><button class="button primary">Connect this device</button></form><p>Connecting signs this machine in. Return to your local app to review your saved files and choose <strong>Upload my office</strong>, or run <code>./wp migrate</code>.</p>'
    else:panel='<p>Sign in to connect your local app. After Google sign-in, return here to approve this device.</p><p class="device-code">'+esc(code)+'</p><a class="button primary" href="/signup">Sign in with Google ↗</a>'
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
    content='<main id="main" class="subpage wide"><p class="eyebrow">HOSTED OFFICE · '+esc(str(data['as_of']))+'</p><h1>'+esc(receipt['name'])+'</h1><p><a href="'+receipt['path']+'">← Open office workspace</a></p><p class="notice">Your saved office documents and retained research. Edits made in the hosted workspace are included in your export. Your local copy is separate.</p><div class="account-grid"><article><h2>Assets</h2><strong>'+money(assets)+'</strong></article><article><h2>Liabilities</h2><strong>'+money(debts)+'</strong></article></div><h2>Accounts and assets</h2><div class="table-scroll"><table><thead><tr><th>Name</th><th>Category</th><th>Saved value</th></tr></thead><tbody>'+rows+'</tbody></table></div><h2>Your goals</h2><ul>'+goals+'</ul><h2>Saved documents & retained research</h2><p>Original documents, financial facts and source dates are preserved. Downloads are private to your account.</p><ul class="document-list">'+artifacts+'</ul><p><a class="text-link" href="'+receipt['path']+'/export">Export the complete office ↗</a></p><p><a class="text-link" href="/app/research">Explore the included SignalOS research ↗</a></p><details><summary>Migration receipt</summary><pre>'+esc(json.dumps(receipt,indent=2))+'</pre></details></main>'
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
