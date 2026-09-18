"""Shared office settings layout, with transport-specific connection controls."""
from html import escape as esc


def render_settings(*, hosted=False, connections=None, sync=None):
    from officekit.serve import STYLE
    connections = connections or {'revision': '0', 'connected': {}}
    connected = connections['connected']
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Office settings</title><style>' + STYLE + '</style></head><body><main class="wrap"><a class="reb" href="/" target="_top">← Back to your office</a><h1>Office settings</h1><p class="sub">Your workspace, connections and saved copies.</p>']
    if hosted:
        out.append('<section class="panel"><h2>Saved online</h2><p>Changes belong to your signed-in account. To keep a local copy in step, enable automatic sync in the local app’s <b>Hosting &amp; sync</b> page.</p><a class="btn btn2" href="/export">Export office</a> <a class="reb" href="/app" target="_top">Account</a></section>')
    else:
        out.append('<section class="panel"><h2>Saved on this computer</h2><p>Work offline or connect this office to your hosted account. Review conflicts before replacing either copy.</p><a class="btn" href="/hosting" target="_top">Hosting &amp; sync</a></section>')
    groups = [('anthropic', 'AI agent', 'Your key powers chat, document extraction, strategy research, courts and pitch decks. Calls use your provider account and may incur charges.', [('ANTHROPIC_API_KEY', 'Anthropic API key')]),
              ('alpaca', 'Alpaca', 'Import positions using your API credentials. Worker Placement only reads positions; it never sends orders.', [('APCA_API_KEY_ID', 'API key ID'), ('APCA_API_SECRET_KEY', 'API secret')]),
              ('ibkr_flex', 'Interactive Brokers Flex', 'Use a Flex Web Service token and an Activity query with Open Positions / Lots in XML format. Re-pull from Imports when a new report is ready.', [('IBKR_FLEX_TOKEN', 'Flex token'), ('IBKR_FLEX_QUERY_ID', 'Query ID')]),
              ('research', 'Public research contact', 'Some public sources, including SEC filings, require a contact email on data requests.', [('OFFICEKIT_CONTACT', 'Contact email')])]
    for group, title, explanation, fields in groups:
        out.append('<section class="panel"><h2>' + title + '</h2><p>' + explanation + '</p>')
        if hosted:
            hidden = '<input type="hidden" name="provider" value="' + group + '"><input type="hidden" name="credential_revision" value="' + esc(connections['revision']) + '">'
            out.append('<p><b>' + ('Connected' if connected.get(group) else 'Not connected') + '</b></p><form method="POST" action="/settings/credentials">' + hidden)
            for name, label in fields:
                out.append('<label>' + label + '<input type="' + ('email' if group == 'research' else 'password') + '" name="' + name + '" autocomplete="off" required maxlength="2048"></label>')
            if group == 'alpaca':
                out.append('<label>Account<select name="APCA_API_BASE_URL"><option value="https://api.alpaca.markets">Live</option><option value="https://paper-api.alpaca.markets">Paper</option></select></label>')
            out.append('<button type="submit">' + ('Replace connection' if connected.get(group) else 'Connect') + '</button></form>')
            if connected.get(group):
                out.append('<form method="POST" action="/settings/credentials">' + hidden + '<input type="hidden" name="remove" value="1"><button class="btn2" type="submit">Disconnect</button></form>')
        elif group == 'anthropic':
            from officekit_ai.models import key_source
            out.append('<p>' + ('Key available on this computer.' if key_source() else 'No key connected.') + '</p><form method="POST" action="/key"><label>Anthropic API key<input type="password" name="api_key" autocomplete="off" required></label><label class="chk"><input type="checkbox" name="remember" value="1">Remember securely on this computer</label><button type="submit">Connect</button></form>')
        else:
            out.append('<p>Available through your local connection settings. Set ' + ', '.join('<code>' + name + '</code>' for name, _ in fields) + ' before starting the server.</p>')
        out.append('</section>')
    out.append('<section class="panel"><h2>Desktop broker connections</h2><p>TWS, IB Gateway and other desktop connections run on your computer. Enable automatic office sync to bring their imported balances online while the local app is running.</p><a href="/pages/imports.html">Open Imports →</a></section>')
    if hosted:
        out.append('<section class="panel"><h2>Research &amp; documents</h2><a href="/documents">Your saved documents →</a><br><a href="/app/research" target="_top">Shared research library →</a></section><p class="note">Connection secrets are encrypted separately from your office. They are excluded from exports and sync. Disconnect removes the saved credential; revoke it with the provider to invalidate previously issued copies.</p>')
    out.append('</main></body></html>')
    return ''.join(out)
