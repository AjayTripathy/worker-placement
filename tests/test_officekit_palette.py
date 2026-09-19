"""Palette drift guard.

The office restyle (2026-09-13) moved every renderer to a single dark palette:
muted gray #9aa4b0 (AAA contrast on #0b0e12) and accent #b1a5ff. A previous
pass left some pages on the retired tokens (#7d858e / #8b7cf6) and one broke a
button by referencing an undefined var(--violet). Full-HTML golden tests
(test_officekit.py) pin three pages exactly; this cheaper source scan covers the
rest so a partial restyle can't reintroduce the old hues silently, and asserts
that every var(--violet)/var(--dim) a renderer emits is actually defined for the
document it ships in.
"""
import re
from pathlib import Path

import pytest

OFFICEKIT = Path(__file__).resolve().parent.parent / "officekit"
RENDERERS = sorted(OFFICEKIT.glob("render_*.py")) + [OFFICEKIT / "serve.py"]

# retired tokens — old muted gray, old accent, and the old accent as an rgb tint
RETIRED = ("#7d858e", "#8b7cf6", "139,124,246", "139, 124, 246")


@pytest.mark.parametrize("path", RENDERERS, ids=lambda p: p.name)
def test_no_retired_palette_literals(path):
    src = path.read_text()
    hits = [tok for tok in RETIRED if tok in src]
    assert not hits, f"{path.name} still carries retired palette token(s): {hits}"


def test_shared_signals_css_defines_accent_tokens():
    """render_imports borrows render_signals.CSS and emits var(--violet) in a
    button; that only renders if the shared stylesheet defines the token."""
    from officekit.render_signals import CSS
    assert "--violet:#b1a5ff" in CSS
    assert "--dim:#9aa4b0" in CSS


def test_css_variables_used_are_defined():
    """Any --var a renderer references in a style attribute must be defined in a
    stylesheet that page ships (its own :root, or the shared signals CSS it wraps
    with). Catches the undefined-var(--violet) class of bug at the source."""
    from officekit.render_signals import CSS as SIGNALS_CSS
    from officekit.serve import STYLE as OFFICE_CSS

    def defined_vars(text):
        return set(re.findall(r"--[a-z0-9-]+(?=\s*:)", text))

    signals_vars = defined_vars(SIGNALS_CSS)
    # renderers that wrap their body in render_signals._page inherit its tokens
    borrow_signals = {"render_signals.py", "render_imports.py"}

    for path in RENDERERS:
        src = path.read_text()
        used = set(re.findall(r"var\((--[a-z0-9-]+)\)", src))
        if not used:
            continue
        own = defined_vars(src)
        available = own | (signals_vars if path.name in borrow_signals else set())
        if path.name == 'render_research.py':
            available |= defined_vars(OFFICE_CSS)
        missing = used - available
        assert not missing, f"{path.name} uses undefined CSS var(s): {sorted(missing)}"
