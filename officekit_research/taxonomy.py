"""Human-facing names for existing research contracts, not a second store."""
KINDS = {
    'office_program': ('Office programs', 'A private portfolio mandate, funding sources, basket, approval and operating record.',
                       'Reuse the existing program after checking current readiness. Approval, funding and operation are distinct states; private terms are not published.'),
    'general': ('Security research', 'What is true about a stock or fund, independent of an investor.',
                'Eligible shared findings must pass publication checks. Reuse checks freshness, evidence, protocol and model quality.'),
    'strategy_pack': ('Strategy ideas', 'A contributed thesis, its factors, tickers and research deck.',
                      'A valid manifest makes an idea discoverable. It still needs evidence and court review before allocation.'),
    'contextual_case': ('Prior investigations', 'An investigation with its original strategy, circumstances and decision.',
                         'Compare the original context with this office. A prior recommendation does not transfer automatically.'),
    'office_court': ('Office decisions', 'A private ruling on whether an investment fits this office and strategy.',
                     'Retain the arguments, conditions and dissent. New strategies receive their own suitability review.'),
    'imported_thesis': ('Imported office theses', 'Research brought in with this office, including its previous verdict.',
                        'Use it as a dated lead. Importing a thesis does not establish fresh evidence or approval.'),
}


def label(kind):
    return KINDS.get(kind, (kind.replace('_', ' '),))[0]


def render():
    from html import escape
    rows = ''.join('<tr><td><b>' + escape(title) + '</b></td><td>' + escape(meaning) + '</td><td>' + escape(use) + '</td></tr>'
                   for title, meaning, use in KINDS.values())
    return ('<details id="research-taxonomy"><summary>How research becomes a strategy</summary>'
            '<p>Save or import → discover relevant research → check current evidence → evaluate the security → '
            'review fit for this office → size a proposal → record your decision.</p>'
            '<div style="overflow:auto"><table><tr><th>Research type</th><th>What it contains</th><th>How it is evaluated</th></tr>' + rows + '</table></div>'
            '<p><b>Source documents:</b> reports, filings and datasets stay linked to their originals. A search match is a source to inspect, not a finding.</p>'
            '<p><b>Factors and reusable mechanisms:</b> security findings carry factor profiles. Reusable detectors belong to the knowledge graph and its promotion and dispatch pipeline.</p>'
            '<p><b>Shared contributions:</b> another agent’s research becomes available through an admitted exchange record or a reviewed, published library version. '
            'Raw uploads are not automatically trusted. New general-research contributions require eligible evidence and claim checks; private-deal research also requires explicit release. '
            'This office’s holdings, suitability rulings and decisions stay private.</p>'
            '<p>Original research and imported research use the same catalog. Every new proposal keeps a dated snapshot of the research considered and links its selected tickers back to matching records.</p></details>')
