"""fmt — shared formatting helpers for the officekit renderers."""
from __future__ import annotations

import html


def esc(x):
    return html.escape(str(x if x is not None else ""))


def fmt_usd(v):
    a = abs(v)
    s = f"${a/1e6:.2f}M" if a >= 1e6 else f"${a/1e3:.0f}k"
    return ("-" if v < 0 else "") + s


# keep the desk-era alias so ported render code reads identically
_fmt = fmt_usd


def betacell(b):
    """Heatmap color for a beta value: coral neg, emerald pos, intensity by |b|."""
    if b is None:
        return "background:transparent", ""
    m = min(1.0, abs(b))
    if b > 0:
        return f"background:rgba(53,201,143,{0.10+m*0.42})", f"{b:+.2f}"
    if b < 0:
        return f"background:rgba(224,115,106,{0.10+m*0.42})", f"{b:+.2f}"
    return "background:rgba(138,145,153,.10)", "0.00"
