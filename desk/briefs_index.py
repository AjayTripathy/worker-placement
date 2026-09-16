"""briefs_index — renders the in-app Briefs library (the 'briefs' dashboard tab).

Born 2026-07-09 (user: move the DD briefs off claude.ai artifacts and into our app).
Reads desk/data/briefs_manifest.json and renders a card index -> desk/ui/static/briefs.html.
Each card links to a full-doc HTML under desk/ui/static/ (served by the desk FastAPI app).

To add a brief: drop the full-doc HTML in desk/ui/static/briefs/, add an entry to the
manifest, and run this. Registered so the index stays in sync.

    python3 -m desk.briefs_index
READ-ONLY.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAN = ROOT / "desk" / "data" / "briefs_manifest.json"
OUT = ROOT / "desk" / "ui" / "static" / "briefs.html"

TAGC = {"DEEP DD": "#1f8a7a", "CASE STUDY": "#9a7b2e", "PITCH": "#5b6cc9", "MEMO": "#6b7280"}


def esc(s):
    return html.escape(str(s if s is not None else ""))


def build():
    m = json.loads(MAN.read_text())
    briefs = m.get("briefs", [])
    cards = []
    for b in briefs:
        tag = b.get("tag", "MEMO")
        c = TAGC.get(tag, "#6b7280")
        cards.append(f"""
    <a class="card" href="{esc(b.get('file'))}" target="_blank">
      <div class="crow"><span class="tag" style="--tc:{c}">{esc(tag)}</span>
        <span class="meta">{esc(b.get('tickers',''))} · {esc(b.get('date',''))}</span></div>
      <h2>{esc(b.get('title'))}</h2>
      <p>{esc(b.get('desc',''))}</p>
      <span class="open">Open →</span>
    </a>""")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Briefs</title>
<style>
:root{{--paper:#f6f5f1;--panel:#fff;--ink:#1c1a16;--dim:#6c716e;--line:#e4e0d6}}
*{{box-sizing:border-box}} body{{margin:0}}
.wrap{{max-width:920px;margin:0 auto;padding:34px 22px 80px;font:15px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:var(--ink);background:var(--paper)}}
h1{{font-size:24px;margin:0 0 3px;letter-spacing:-.01em}} .sub{{color:var(--dim);font-size:13px;margin:0 0 26px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}}
.card{{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px;text-decoration:none;color:inherit;transition:border-color .15s,transform .15s}}
.card:hover{{border-color:#c9c3b5;transform:translateY(-2px)}}
.crow{{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}}
.tag{{font:700 10px ui-monospace,Menlo,monospace;letter-spacing:.1em;color:var(--tc);border:1px solid var(--tc);border-radius:20px;padding:2px 9px}}
.meta{{font:11px ui-monospace,Menlo,monospace;color:var(--dim)}}
h2{{font-size:17px;margin:0 0 8px;letter-spacing:-.01em;line-height:1.25}}
p{{font-size:13px;color:var(--dim);margin:0 0 14px;line-height:1.5}}
.open{{font-size:12px;font-weight:600;color:var(--ink)}}
</style></head><body>
  <div class="wrap">
    <h1>Briefs</h1>
    <p class="sub">Diligence, case studies, and pitches — served from the desk, not claude.ai. {len(briefs)} on file.</p>
    <div class="grid">{''.join(cards)}
    </div>
  </div>
</body></html>"""


def main():
    OUT.write_text(build())
    print(f"[briefs_index] rendered {len(json.loads(MAN.read_text()).get('briefs', []))} briefs -> {OUT}")


if __name__ == "__main__":
    main()
