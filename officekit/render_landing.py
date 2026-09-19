"""Public presentation only: never reads an office or detects local accounts."""
from html import escape
import os
from pathlib import Path
from urllib.parse import urlparse

PUBLIC = Path(__file__).with_name('public')
REPO = 'https://github.com/AjayTripathy/worker-placement'
BRANCH = 'main'
REPO_URL = REPO + '/tree/' + BRANCH
# Filled with the verified deployment URL when the public service is deployed.
HOSTED_ORIGIN = 'https://worker-placement-web-653732113303.us-west1.run.app'
CLONE_COMMAND = 'git clone \\\n  --branch main \\\n  https://github.com/AjayTripathy/worker-placement.git'
ASSETS = {'site.css': 'text/css; charset=utf-8', 'site.js': 'text/javascript; charset=utf-8',
          'auth.js': 'text/javascript; charset=utf-8', 'office-import.js': 'text/javascript; charset=utf-8', 'mark.svg': 'image/svg+xml'}


def hosted_origin():
    value = os.environ.get('WORKER_PLACEMENT_HOSTED_URL', HOSTED_ORIGIN).rstrip('/')
    if value:
        parsed = urlparse(value)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise ValueError('WORKER_PLACEMENT_HOSTED_URL must be an HTTPS origin')
    return value


def asset(path):
    if not path.startswith('/public/'):
        return None
    name = path[len('/public/'):]
    if name not in ASSETS:
        return None
    return (PUBLIC / name).read_bytes(), ASSETS[name]


def render_landing(local=False):
    signup = (hosted_origin() + '/signup') if local and hosted_origin() else '/signup'
    values = {'HOME': '/welcome' if local else '/', 'SIGNUP': signup,
              'REPO_URL': REPO_URL, 'CLONE_COMMAND': CLONE_COMMAND,
              'BRING_OFFICE': (hosted_origin() if local else '') + '/app/import',
              'INSTALL_COMMAND': 'curl -fsSL ' + hosted_origin() + '/install.sh | sh',
              'LOCAL_ACTION': ''}
    html = (PUBLIC / 'landing.html').read_text()
    for key, value in values.items():
        html = html.replace('{{' + key + '}}', escape(value, quote=True))
    if local:
        html = html.replace('</div></section>\n<section class="closing',
            '<p class="local-action">Already running locally? <a href="/start">Open this local app →</a></p></div></section>\n<section class="closing')
    return html


def page(title, content, auth_script=False, signed_in=False, local=False):
    home = '/welcome' if local else '/'
    nav = '<button class="nav-signin" id="sign-out" type="button">Sign out ↗</button>' if signed_in else '<a class="nav-signin" href="' + escape((hosted_origin() if local else '') + '/signup', quote=True) + '">Sign in ↗</a>'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>' + escape(title) + ' — Worker Placement</title><link rel="icon" href="/public/mark.svg" type="image/svg+xml">'
            '<link rel="stylesheet" href="/public/site.css">' + ('<script src="/public/auth.js" defer></script>' if auth_script else '') +
            '</head><body><a class="skip" href="#main">Skip to content</a><header class="site-header"><a class="brand" href="' + home + '">'
            '<img src="/public/mark.svg" width="29" height="29" alt="">worker placement.</a><nav aria-label="Main navigation">'
               '<a href="/guides/local">Documentation</a>' + ('<a href="/app/import">Bring an office</a>' if signed_in else '') + nav + '</nav></header>' + content +
            '<footer class="site-footer wrap"><a class="brand" href="' + home + '">worker placement.</a><p>Built for decisions. Never places trades.</p>'
            '<div><a href="/guides/local">Docs</a><a href="/privacy">Privacy</a><a href="' + REPO_URL + '">GitHub ↗</a></div></footer></body></html>')


def render_signup(finish=False, available=True, google_finish=False):
    # The old finish page only completes links issued before the Google cutover.
    title = 'Make yourself at home.'
    subtitle = 'Use your Google account to start a hosted office or return to your workspace.'
    panel_title = 'Continue with Google'
    if finish:
        title, subtitle, panel_title = 'Finish your sign-in.', 'This page completes an email link you already received. New sign-ins use Google.', 'Confirm your email'
        form = ('<form id="auth-form" data-mode="complete"><label for="email">Email address</label>'
                '<input id="email" name="email" type="email" autocomplete="email" placeholder="you@example.com" maxlength="254" required>'
                '<button class="button primary" type="submit">Verify email &amp; continue ↗</button></form>'
                '<p><a href="/signup">Continue with Google instead ↗</a></p>')
    else:
        if google_finish:
            title, subtitle = 'Welcome back.', 'Completing your Google sign-in…'
        form = ('<button class="button google-signin" id="google-signin" type="button" data-finish="' + ('true' if google_finish else 'false') + '">Continue with Google</button>'
                '<p class="fine-print">Use the same Google email as your existing hosted account to return to your office.</p>'
                '<p class="fine-print">We request your basic profile and email only. No access to Gmail or Google Drive. <a href="/privacy">How we handle your data</a>.</p>')
    if not available:
        form = '<div class="notice">Google sign-in is being configured. Please return shortly, or <a href="/guides/local">start locally</a>.</div>'
    content = ('<main id="main" class="auth-layout"><div class="auth-copy"><p class="eyebrow">WORKER PLACEMENT · HOSTED EARLY ACCESS</p><h1>' + title + '</h1><p>' + subtitle + '</p><p>Explore the included SignalOS research, or bring your saved office folder directly from the website after signing in.</p></div>'
               '<section class="auth-panel"><h2>' + panel_title + '</h2><p>No new password. No payment details.</p><div id="auth-error" class="notice error" role="alert" hidden></div>'
               '<div id="auth-status" class="notice" role="status" aria-live="polite" hidden></div>' + form +
               '<noscript><p>Enable JavaScript to sign in with Google.</p></noscript>'
               '<div class="auth-note"><p>Prefer to keep your office on your machine?</p><a class="text-link" href="/guides/local">Run locally instead ↗</a></div></section></main>')
    return page(panel_title, content, auth_script=True)


def render_account(email):
    content = ('<main id="main" class="subpage"><p class="eyebrow">YOUR HOSTED ACCOUNT</p><h1>Welcome to<br>Worker Placement.</h1>'
               '<div id="auth-error" class="notice error" role="alert" hidden></div><div class="account-status"><span class="review-check">✓</span><div><strong>Email verified</strong><small class="account-email">' + escape(email) + '</small></div></div>'
               '<p>You’re signed in. This is your private account page; your local financial records have not been uploaded.</p><div class="account-grid">'
               '<article><h2>Start your local office.</h2><p>Bring your accounts, goals and commitments together today.</p><a class="text-link" href="/guides/local">Local setup guide ↗</a></article>'
               '<article><h2>Bring it to the cloud.</h2><p>Run ./wp login and ./wp migrate to open the same office workspace online with private saved edits and export.</p><a class="text-link" href="/guides/local">Migration guide ↗</a></article></div></main>')
    return page('Your account', content, auth_script=True, signed_in=True)


def render_local_guide(local=False):
    bootstrap = 'curl -fsSL ' + hosted_origin() + '/install.sh | sh'
    body = ('<main id="main" class="subpage"><p class="eyebrow">THE LOCAL SETUP GUIDE</p><h1>One script.<br>Your whole office.</h1>'
            '<p>Paste this into your terminal. The script downloads the full repository, installs the app and opens your local office:</p>'
            '<pre class="code-block"><code>' + escape(bootstrap) + '</code></pre>'
            '<p>Requires Git and Python 3.9 or later (3.11+ recommended). The public repository requires no GitHub login. The download includes the research datasets.</p>'
            '<p>The script creates its own Python environment, installs connector libraries and prepares your office folder. No separate clone, install or activation commands.</p>'
            '<p>You can <a href="' + escape(hosted_origin()) + '/install.sh">inspect the installer</a> first.</p>'
            '<h2>Next time</h2><p>From the downloaded <code>worker-placement</code> folder, run <code>./start.sh</code>. Your saved office is kept.</p>'
            '<details><summary>Prefer to clone it yourself?</summary>'
            '<pre class="code-block"><code>' + escape(CLONE_COMMAND + '\ncd worker-placement\n./start.sh') + '</code></pre></details>'
            '<p>On Windows, use <code>python wp start</code> from the checkout. No environment activation is needed.</p>'
            '<h2>Three commands to remember</h2><ol class="guide-list"><li><code>./start.sh</code> — start your local office at <strong>http://127.0.0.1:8787</strong>.</li>'
            '<li><code>./wp login</code> — sign in with Google in your browser, compare the device code and connect this machine. Login alone uploads nothing.</li>'
            '<li><code>./wp migrate</code> — upload your saved office and retained research to your verified account. It checks every document before activating the hosted snapshot and keeps your local copy.</li></ol>'
            '<p>Default office folder: <code>./office</code>. For an existing office, use <code>./start.sh --dir /path/to/office</code> and <code>./wp migrate --dir /path/to/office</code>. Choose another port with <code>--port 8790</code>; use <code>--no-browser</code> for terminal-only startup. Stop the server with Ctrl+C.</p>'
            '<h2>Build your first office</h2><p>Import a positions CSV or enter your assets and debts, review the sources, then add goals and commitments. Start with Home and Capital &amp; Commitments. Scenario Planner helps stress-test the plan; strategy proposals bring research and review together.</p>'
            '<h2>Bring your office from the website</h2><p>Sign in and choose <strong>Bring an office</strong> from your workspace. Select the saved folder containing <code>answers.json</code> and <code>balance_sheet.json</code>, review the files, then choose <strong>Upload and open office</strong>. Your local copy stays available. An existing hosted office requires a reviewed replacement.</p>'
            '<h2>What is hosted today?</h2><p>The same office workspace with private saved edits, retained documents and complete export, plus a shared SignalOS research library for every account. Connect your AI key and supported brokers in Office settings. Upload statements from Imports. Enable automatic sync in the local app to keep an offline copy; conflicting edits pause for review.</p>'
            '<p>Migration accepts up to 64 MiB across 1,024 saved office documents. It excludes credentials, generated pages and the Git checkout. The website asks you to review a different hosted revision before replacing it; the CLI uses <code>--replace-revision</code>. Interrupted uploads resume when you retry with the same saved files.</p>'
            '<h2>Models are optional</h2><p>Manual entry, CSV import and core planning work without a key. Chat, document extraction and courts use your configured model provider. Set provider keys in the environment; <code>models.json</code> stores variable names, never keys.</p>'
            '<h2>Keep your office</h2><p>Back up the office folder as private financial data. The local server binds only to localhost. Use the separate hosted service for internet access.</p>'
            '<p><a class="text-link" href="' + REPO_URL + '/officekit/README.md">Complete usage and troubleshooting guide ↗</a></p></main>')
    return page('Run locally', body, local=local)


def render_privacy(local=False):
    body = '''<main id="main" class="subpage"><p class="eyebrow">DATA & PRIVACY · EARLY ACCESS</p><h1>A clear boundary<br>around your data.</h1><h2>Hosted account signup</h2><p>Google sign-in uses Google Identity Platform. Google processes your basic profile, email address and authentication information to verify your account. We request only identity scopes, with no access to Gmail, Google Drive or your financial accounts. The service stores the account in Identity Platform and uses essential session and anti-forgery cookies. These cookies are not used for advertising.</p><p>We use your email for authentication. Signup does not enroll you in marketing emails and does not upload your local office. Choosing <strong>Upload and open office</strong> on the website or running <code>./wp migrate</code> explicitly uploads your saved office and retained documents to your verified account. Your local copy is kept.</p><h2>Hosted office storage</h2><p>Private documents are stored in Google Cloud Storage with application-level envelope encryption backed by Cloud KMS. Access is scoped to your verified account. Shared seeded research is stored separately and does not include customer office uploads. Download an office export from its hosted page.</p><h2>Connections and sync</h2><p>Hosted AI and broker credentials are encrypted separately from office records and excluded from exports and sync. AI requests send relevant inputs to your configured provider and may incur provider charges. Automatic sync is opt-in and transfers saved office data while the local app is running. If both copies change, sync waits for your review. Background-job records expire after 30 days; local sync keeps the last five download backups.</p><h2>Operational records</h2><p>Google Cloud hosts the service and retains operational logs. Application logs exclude OAuth codes, email-link codes, session credentials and request bodies. No advertising analytics or tracking pixels are included.</p><h2>Your local office</h2><p>Local records stay in the office folder you choose. Importing documents with an AI model or requesting research sends the relevant inputs to the providers you configure. Core planning and CSV imports do not require a model.</p><h2>Managing your account</h2><p>Sign out to remove the hosted session from this browser. To request deletion of your hosted account, contact the repository owner through the existing channel by which you received early access. Self-service account and office deletion are not yet available. Signing out does not delete your hosted records.</p></main>'''
    return page('Privacy', body, local=local)
