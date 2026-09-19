"""Shared connection guidance; where a connector runs is a capability, not a UI fork."""
from html import escape


def desktop_connection_help():
    from officekit.render_landing import hosted_origin
    guide = hosted_origin() + '/guides/local#desktop-connections'
    return ('<section class="panel desktop-connections"><h2>IBKR TWS / IB Gateway &amp; desktop connections</h2>'
            '<p><b>Runs on your computer.</b> Install the open-source Worker Placement app on the same '
            'computer as your broker software. Import positions there, then use <b>Hosting &amp; sync</b> '
            'to keep this website updated.</p>'
            '<p><a class="btn btn2" href="' + escape(guide, quote=True) + '" target="_blank" rel="noopener">'
            'Install the local app →</a></p>'
            '<p class="note">Updates need the local app and broker connection running. '
            'Your broker login stays on your computer; office sync sends saved records.</p>'
            '<p class="note">Prefer to stay online? Upload a statement, or connect '
            '<a href="/settings" target="_top">IBKR Flex reports in Office settings</a>.</p></section>')
