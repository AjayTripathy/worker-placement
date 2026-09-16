"""render_deck — one adjudication as a full PITCH DECK page.

UX ruling (principal, 2026-09-04): every courted asset sits alongside its full
pitch deck — the whole adversarial record, click-through from the
goal -> strategy -> assets taxonomy. Verdict banner, mandate context, the
adjudicator's rationale and decisive points, BOTH bench briefs in full, the
unverified work queue, and the provenance line (models, tier, frozen-call
refs). Read-only; never places orders.
"""
from __future__ import annotations

from officekit.fmt import esc

TONE = {"KILL": "#e0736a", "AVOID": "#e0736a", "WATCH": "#d9a441",
        "STARTER": "#35c98f", "OWN": "#35c98f"}


def render_deck(adj, strategy_title=None):
    verdict_word = (adj.get("verdict") or "").split(" ")[0]
    color = TONE.get(verdict_word, "#8a939e")
    briefs = adj.get("briefs") or {}

    def brief_block(name, b, accent):
        if not b:
            return ""
        pts = "".join(f"<li>{esc(x)}</li>" for x in b.get("key_points", []))
        unv = "".join(f"<li>{esc(x)}</li>" for x in b.get("unverified", []))
        return (f'<h2 style="color:{accent}">{name} bench — lean: {esc(b.get("lean", "?").upper())}</h2>'
                f'<div class="case">{esc(b.get("case", ""))}</div>'
                + (f'<div class="lbl">Key points</div><ul>{pts}</ul>' if pts else "")
                + (f'<div class="lbl">Unverified (this bench)</div><ul class="unv">{unv}</ul>' if unv else ""))

    dp = "".join(f"<li>{esc(x)}</li>" for x in adj.get("decisive_points", []))
    uq = "".join(f"<li>{esc(x)}</li>" for x in adj.get("unverified_items", []))
    models = adj.get("models") or {}
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(adj.get('symbol', ''))} — pitch deck</title>
<style>
body{{margin:0;background:#0b0e12;color:#e8ebee;font:14px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}}
.wrap{{max-width:880px;margin:0 auto;padding:28px 24px 90px}}
a{{color:#b1a5ff}} h1{{font-size:24px;margin:0 0 2px;letter-spacing:-.02em}}
.sub{{color:#9aa4b0;margin:0 0 18px;font-size:13px}}
.verdict{{display:inline-block;font:700 15px ui-monospace,Menlo,monospace;color:#0b0e12;
background:{color};border-radius:9px;padding:8px 16px;margin:6px 0 16px}}
h2{{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:#9aa4b0;margin:26px 0 8px}}
.case{{background:#14181d;border:1px solid #242a31;border-radius:12px;padding:14px 18px;white-space:pre-wrap}}
.lbl{{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:#9aa4b0;margin:12px 0 4px;font-weight:600}}
ul{{margin:4px 0;padding-left:20px}} li{{margin-bottom:5px}}
.unv li{{color:#eccb8a}}
.prov{{font-size:11px;color:#9aa4b0;border-top:1px solid #242a31;margin-top:28px;padding-top:12px;line-height:1.7}}
.rat{{background:#14181d;border:1px solid #242a31;border-left:4px solid {color};border-radius:12px;padding:14px 18px}}
</style></head><body><div class="wrap">
<a href="strategies.html#strat-{esc(adj.get('strategy', ''))}">&larr; back to the strategy</a>
<h1>{esc(adj.get('symbol', ''))}</h1>
<p class="sub">courted under <b>{esc(strategy_title or adj.get('strategy', ''))}</b> · {esc(adj.get('date', ''))} · every pick carries its deliberation</p>
<div class="verdict">{esc(adj.get('verdict', ''))}</div>
<h2>Adjudication</h2><div class="rat">{esc(adj.get('rationale', ''))}</div>
{f'<h2>Decisive points</h2><ul>{dp}</ul>' if dp else ''}
{f'<h2>Unverified work queue — what a full court must verify at primary</h2><ul class="unv">{uq}</ul>' if uq else ''}
{('<h2>Evidence pack</h2><div class="case">' + esc((adj.get('evidence') or {}).get('md', '')) + '</div>') if (adj.get('evidence') or {}).get('md') else ''}
{brief_block('RED', briefs.get('red'), '#e0736a')}
{brief_block('BLUE', briefs.get('blue'), '#35c98f')}
<div class="prov">{'Evidence-backed court — source snapshots and unresolved claims are retained above.' if (adj.get('evidence') or {}).get('md') else 'LITE court — no live data connectors; deliberation from model knowledge under the shipped court doctrine, plane-2 gated.'}
Bench: {esc(models.get('bench', '?'))} · Adjudicate: {esc(models.get('adjudicate', '?'))} · tier: {esc(adj.get('tier', '?'))}<br>
Frozen calls: red {esc((adj.get('refs') or {}).get('red', '')[:8])}… · blue {esc((adj.get('refs') or {}).get('blue', '')[:8])}… · adjudicate {esc((adj.get('refs') or {}).get('adjudicate', '')[:8])}…<br>
Read-only — never places orders. Not investment advice.</div>
</div></body></html>"""


def deck_filename(adj):
    return f"deck_{adj['id'][:8]}.html"


# --- contributed strategy-pack decks: a SAFE minimal markdown renderer ---
# Pack decks are authored by third parties (their agents) — escape everything, then
# apply markdown on the escaped text so no contributor content can inject HTML.
import re as _re  # noqa: E402


def _md_inline(s):
    s = esc(s)
    s = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = _re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", s)   # *italic*
    s = _re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def _md_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [c for c in cells if not all(_re.fullmatch(r":?-{2,}:?", x or "") for x in c)]  # drop --- sep
    if not cells:
        return ""
    head = "".join(f"<th>{_md_inline(c)}</th>" for c in cells[0])
    body = "".join("<tr>" + "".join(f"<td>{_md_inline(c)}</td>" for c in r) + "</tr>" for r in cells[1:])
    return f'<table><tr>{head}</tr>{body}</table>'


def render_markdown_deck(title, md, author=None):
    """Render a contributed pack's DECK.md to a safe HTML deck page."""
    lines = md.splitlines()
    out, i = [], 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("### "):
            out.append(f"<h3>{_md_inline(ln[4:])}</h3>"); i += 1
        elif ln.startswith("## "):
            out.append(f"<h2>{_md_inline(ln[3:])}</h2>"); i += 1
        elif ln.startswith("# "):
            out.append(f"<h1>{_md_inline(ln[2:])}</h1>"); i += 1
        elif ln.lstrip().startswith(("- ", "* ")):
            items = []
            while i < len(lines) and lines[i].lstrip().startswith(("- ", "* ")):
                items.append(f"<li>{_md_inline(lines[i].lstrip()[2:])}</li>"); i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i]); i += 1
            out.append(_md_table(rows))
        elif ln.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip(">").strip()); i += 1
            out.append(f'<blockquote style="border-left:3px solid #2a3038;margin:8px 0;padding:2px 0 2px 12px;'
                       f'color:#a9b1ba">{_md_inline(" ".join(quote))}</blockquote>')
        else:
            para = [ln]; i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].lstrip()[:1] in ("#", "-", "*", "|", ">"):
                para.append(lines[i].rstrip()); i += 1
            out.append(f"<p>{_md_inline(' '.join(para))}</p>")
    sub = f"Contributed strategy pack · {esc(author)}" if author else "Contributed strategy pack"
    css = ("body{margin:0;background:#0b0e12;color:#e8ebee;font:15px/1.65 -apple-system,BlinkMacSystemFont,"
           "'Segoe UI',Roboto,sans-serif}.wrap{max-width:820px;margin:0 auto;padding:30px 24px 90px}"
           "a{color:#b1a5ff}h1{font-size:25px;margin:0 0 2px;letter-spacing:-.02em}"
           ".sub{color:#9aa4b0;margin:0 0 20px;font-size:13px}"
           "h2{font-size:12.5px;text-transform:uppercase;letter-spacing:.11em;color:#9aa4b0;margin:26px 0 8px}"
           "h3{font-size:15px;margin:18px 0 6px}code{background:#1a1f25;padding:1px 5px;border-radius:5px}"
           "table{width:100%;border-collapse:collapse;font-size:13.5px;margin:8px 0}"
           "td,th{padding:7px 10px;border-bottom:1px solid #242a31;text-align:left}"
           "th{color:#9aa4b0;text-transform:uppercase;font-size:10.5px;letter-spacing:.07em}"
           "ul{margin:6px 0;padding-left:20px}li{margin:3px 0}p{margin:8px 0}")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)} — deck</title><style>{css}</style></head><body><div class="wrap">'
            f'<p><a href="strategies.html">&larr; Strategies</a></p>'
            f'<p class="sub">{sub}</p>' + "\n".join(out) + '</div></body></html>')
