"""gauntlet_book — the one-place review UX for the gauntlet + the Brier book.

Joins, per frozen call: the NUMBER (our_p / market_p), the DATE (cat_date),
the GRADER (the resolution pack's adjudication spec + pre-committed branches),
the STAKE (held position + resting orders in the name), the plain-language
meaning (freeze_call's what/how/conclusion), and — once graded — the outcome
+ Brier. Renders desk/ui/static/gauntlet.html (the GAUNTLET tab).

Sections: PAST-DUE UNGRADED (the shame list) · THIS WEEK · REST OF MONTH ·
LATER · THE BRIER BOOK (scoreboard; honest empty-state until grades exist).

    python3 -m desk.gauntlet_book       # registered hourly; also sentinel-run
READ-ONLY.
"""
from __future__ import annotations

import datetime
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desk" / "ui" / "static" / "gauntlet.html"


def _load():
    led = {n["ticker"]: n for n in json.loads((ROOT / "desk/data/research_ledger.json").read_text())["names"]}
    packs = json.loads((ROOT / "desk/data/resolution_packs.json").read_text())["packs"]
    calls = []
    for ln in (ROOT / "desk/data/calibration_ledger.jsonl").read_text().splitlines():
        if ln.strip():
            try:
                calls.append(json.loads(ln))
            except Exception:
                pass
    pos, orders = {}, {}
    try:
        pc = json.loads((ROOT / "desk/ui/data/positions_cache.json").read_text())
        for p in pc.get("positions", []):
            pos[p["symbol"].split(" ")[0]] = pos.get(p["symbol"].split(" ")[0], 0) + (p.get("qty", 0) or 0)
    except Exception:
        pass
    try:
        oc = json.loads((ROOT / "desk/ui/data/orders_cache.json").read_text())
        for o in oc.get("orders", []):
            if str(o.get("status", "")).upper() in ("SUBMITTED", "PRESUBMITTED", "NEW"):
                orders[o["symbol"]] = orders.get(o["symbol"], 0) + abs((o.get("qty") or 0) * (o.get("limit") or 0))
    except Exception:
        pass
    scoreboard = {}
    try:
        scoreboard = json.loads((ROOT / "desk/data/CALIBRATION.json").read_text())
    except Exception:
        pass
    return led, packs, calls, pos, orders, scoreboard


_FAV = {True, "HIT", "FAVORABLE", "FAVOURABLE"}
_UNFAV = {False, "MISS", "UNFAVORABLE", "UNFAVOURABLE"}


def _grade_one(c):
    """Normalize a graded call -> (outcome_str, favorable 1/0/None, brier or None, correct bool/None).
    Writers vary: resolution is a dict {'outcome','brier'} OR a bare string; outcome may be a top-level key."""
    res = c.get("resolution")
    if isinstance(res, dict):
        o, br = res.get("outcome"), res.get("brier")
    else:
        o, br = (res if res is not None else c.get("outcome")), None
    o_str = str(o or "").upper()
    fav = 1 if (o in _FAV or o_str.startswith("FAV") or o_str == "HIT") else \
          0 if (o in _UNFAV or o_str.startswith("UNFAV") or o_str == "MISS") else None
    p = c.get("our_p")
    if br is None and fav is not None and p is not None:
        br = round((p - fav) ** 2, 4)
    correct = None if (fav is None or p is None) else ((p >= 0.5) == (fav == 1))
    return o_str or "—", fav, br, correct


def _graded_table(items):
    """The track record — one scannable table of every resolved call, newest first, with a summary footer.
    sizing_gate_excluded rows show but don't count toward the record (HCA-OPS retrospective split)."""
    rows = sorted(items, key=lambda x: str(x[0].get("cat_date")), reverse=True)
    hits = misses = mixed = 0
    briers = []
    body = []
    for c, cd in rows:
        t = c.get("ticker", "?")
        p = c.get("our_p")
        mp = c.get("market_p")
        o_str, fav, br, correct = _grade_one(c)
        excl = bool(c.get("sizing_gate_excluded"))
        if not excl:
            if correct is True: hits += 1
            elif correct is False: misses += 1
            elif fav is None: mixed += 1
            if br is not None and fav is not None:
                briers.append(br)
        # cells
        mark = "—" if excl else ("✓" if correct else ("✗" if correct is False else "~"))
        mcol = "#3D453F" if excl else ("#14532D" if correct else ("#A32B18" if correct is False else "#7A5410"))
        oco = "#14532D" if fav == 1 else ("#A32B18" if fav == 0 else "#7A5410")
        note = " <span style='color:#7A5410;font-size:10px'>(sizing-excl)</span>" if excl else ""
        body.append(
            f"<tr><td style='font-family:ui-monospace,Menlo,monospace'>{html.escape(str(c.get('cat_date')))}</td>"
            f"<td style='font-weight:700'>{html.escape(str(t))}{note}</td>"
            f"<td style='font-size:10px;color:#3D453F'>{html.escape(str(c.get('event_type','')))}</td>"
            f"<td style='font-family:ui-monospace,Menlo,monospace;text-align:right'>{p if p is not None else '—'}</td>"
            f"<td style='font-family:ui-monospace,Menlo,monospace;text-align:right;color:#3D453F'>{mp if mp is not None else '—'}</td>"
            f"<td style='color:{oco};font-weight:600'>{html.escape(o_str)}</td>"
            f"<td style='text-align:center;color:{mcol};font-weight:800'>{mark}</td>"
            f"<td style='font-family:ui-monospace,Menlo,monospace;text-align:right'>{br if br is not None else '—'}</td></tr>")
    n = len(briers)
    mean_b = round(sum(briers) / n, 4) if n else None
    beat = (mean_b is not None and mean_b < 0.25)
    summ = (f"<div style='margin:10px 0;font-size:13px'>"
            f"<b>{hits} right &middot; {misses} wrong</b>"
            + (f" &middot; {mixed} mixed" if mixed else "")
            + f" &nbsp;|&nbsp; mean Brier <b style='color:{'#14532D' if beat else '#A32B18'}'>"
            + (f"{mean_b}" if mean_b is not None else "—")
            + f"</b> vs 0.25 coin <span style='color:#3D453F'>(n={n}; lower is better; "
            + ("beating" if beat else "not beating") + " the coin)</span></div>")
    head = ("<tr><th>resolves</th><th>ticker</th><th>type</th><th style='text-align:right'>our p</th>"
            "<th style='text-align:right'>mkt p</th><th>outcome</th><th style='text-align:center'>call</th>"
            "<th style='text-align:right'>Brier</th></tr>")
    return summ + "<div style='overflow-x:auto'><table>" + head + "".join(body) + "</table></div>"


def _stake(t, pos, orders, led):
    base = t.split(".")[0].split("|")[0]
    bits = []
    if pos.get(base):
        bits.append(f"HELD {pos[base]:g} sh")
    if orders.get(base):
        bits.append(f"${orders[base]:,.0f} resting")
    st = (led.get(t) or led.get(base) or {}).get("state") or (led.get(t) or led.get(base) or {}).get("verdict")
    if st:
        bits.append(st)
    return " · ".join(bits) or "no live exposure (a graded belief)"


def render() -> str:
    led, packs, calls, pos, orders, sb = _load()
    today = datetime.date.today()
    buckets = {"PAST-DUE UNGRADED": [], "THIS WEEK": [], "REST OF THE MONTH": [], "LATER": [], "GRADED": []}
    for c in sorted(calls, key=lambda x: str(x.get("cat_date"))):
        try:
            cd = datetime.date.fromisoformat(str(c.get("cat_date"))[:10])
        except Exception:
            continue
        dd = (cd - today).days
        st = str(c.get("status", "")).upper()
        if st in ("VOIDED", "EXCLUDED_LOOKAHEAD") and not (c.get("resolution") or c.get("outcome")):
            continue                                   # neither open nor graded — don't clutter the ungraded buckets
        if c.get("resolution") or c.get("outcome"):
            buckets["GRADED"].append((c, cd))
        elif dd < -2:
            buckets["PAST-DUE UNGRADED"].append((c, cd))
        elif dd <= 7:
            buckets["THIS WEEK"].append((c, cd))
        elif cd.month == today.month and cd.year == today.year or dd <= 31:
            buckets["REST OF THE MONTH"].append((c, cd))
        else:
            buckets["LATER"].append((c, cd))

    C = {"h": "#14532D", "m": "#A32B18", "b": "#1E3A5F", "a": "#7A5410"}
    out = [f"""<title>The Gauntlet &amp; Brier Book</title><style>
body{{font-family:'Helvetica Neue',Arial,sans-serif;max-width:960px;margin:0 auto;padding:24px;background:#fff;color:#000;line-height:1.4}}
h1{{font-size:24px;margin:0}} .sub{{color:#3D453F;font-size:13px;margin:2px 0 16px}}
h2{{font-size:13px;text-transform:uppercase;letter-spacing:.08em;border-bottom:2px solid #000;padding-bottom:4px;margin:24px 0 8px}}
.card{{border:1px solid #D8DDD8;border-left:4px solid #1E3A5F;border-radius:5px;padding:12px 16px;margin:8px 0}}
.card.due{{border-left-color:#A32B18}} .card.graded-hit{{border-left-color:#14532D}} .card.graded-miss{{border-left-color:#A32B18}}
.top{{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}}
.tkr{{font-weight:800;font-size:16px}} .date{{font-family:ui-monospace,Menlo,monospace;font-size:12px}}
.p{{font-family:ui-monospace,Menlo,monospace;font-weight:700;color:#1E3A5F}}
.tag{{font-size:9.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#fff;background:#3D453F;padding:2px 6px;border-radius:3px}}
.what{{font-size:13.5px;margin:6px 0 2px;max-width:80ch}} .how{{font-size:12px;color:#3D453F;max-width:80ch}}
.grader{{font-size:11.5px;background:#F6F8F6;border:1px solid #D8DDD8;border-radius:4px;padding:6px 10px;margin-top:6px}}
.grader b{{font-size:10px;text-transform:uppercase;letter-spacing:.06em}}
.branch{{display:inline-block;font-size:10.5px;border:1px solid #C9CFC9;border-radius:3px;padding:1px 6px;margin:2px 3px 0 0;background:#fff}}
.stake{{font-size:11px;color:#1E3A5F;font-weight:600}}
table{{border-collapse:collapse;width:100%;font-size:12.5px}}th{{text-align:left;font-size:10px;text-transform:uppercase;border-bottom:2px solid #000;padding:5px 8px}}td{{padding:5px 8px;border-bottom:1px solid #D8DDD8}}
</style>
<h1>The Gauntlet &amp; Brier Book</h1>
<div class="sub">every frozen call &middot; its number, date, grader, stake, and grade &middot; regenerated hourly &middot; as of {today.isoformat()}</div>"""]

    # THE BRIER BOOK header block
    res = sb.get("summary") or {}
    n_open = sum(len(v) for k, v in buckets.items() if k != "GRADED")
    n_grad = len(buckets["GRADED"])
    out.append(f"<h2>The Brier Book</h2>")
    if n_grad == 0:
        nxt = buckets["THIS WEEK"][:3] or buckets["REST OF THE MONTH"][:3]
        nxts = " &middot; ".join(f"{c.get('ticker')} {c.get('cat_date')}" for c, _ in nxt)
        out.append(f"<div class='card'><div class='what'><b>{n_open} open calls, 0 graded — the curve starts with the next resolution.</b></div>"
                   f"<div class='how'>Scoring: Brier(ours) vs Brier(market-implied) vs coin(0.5). The autonomy ladder's rung 1 needs ours &lt; market at n&ge;20. First up: {nxts}</div></div>")
    else:
        out.append(f"<div class='card'><div class='what'><b>{n_grad} graded &middot; {n_open} open.</b> "
                   "The track record below is every resolved call; the open calls follow, grouped by when they resolve.</div></div>")
        # THE TRACK RECORD — a clean scannable table of every graded call (was: cards + a raw-JSON blob)
        out.append("<h2>Track record &mdash; graded calls</h2>")
        out.append(_graded_table(buckets["GRADED"]))

    for sec in ("PAST-DUE UNGRADED", "THIS WEEK", "REST OF THE MONTH", "LATER"):
        items = buckets[sec]
        if not items:
            continue
        out.append(f"<h2>{sec} ({len(items)})</h2>")
        for c, cd in items:
            t = c.get("ticker", "?")
            plain = c.get("plain") or {}
            key = f"{t}|{c.get('cat_date')}"
            pack = packs.get(key)
            cls = "card"
            grade_note = ""
            if sec == "PAST-DUE UNGRADED":
                cls += " due"
                grade_note = f"<div class='stake' style='color:#A32B18'>UNGRADED — resolve: python3 -m desk.calibration resolve {t} FAVORABLE|UNFAVORABLE|MIXED --date {c.get('cat_date')}</div>"
            if sec == "GRADED":
                res = c.get("resolution")            # writers vary: dict {'outcome','brier'} OR bare string
                if isinstance(res, dict):
                    r, br = str(res.get("outcome", "")).upper(), res.get("brier")
                else:
                    r, br = str(res or c.get("outcome", "")).upper(), None
                fav = 1 if (r.startswith("FAV") or r == "HIT") else 0 if (r.startswith("UNFAV") or r == "MISS") else None
                if br is None and fav is not None and c.get("our_p") is not None:
                    br = round((c["our_p"] - fav) ** 2, 4)   # compute Brier for string-style resolutions
                cls += " graded-hit" if fav == 1 else " graded-miss" if fav == 0 else ""
                grade_note = f"<div class='stake'>GRADED {html.escape(r)}{f' · Brier {br}' if br is not None else ''}</div>"
            mkt = f" <span class='p'>mkt {c['market_p']}</span>" if c.get("market_p") else ""
            out.append(f"""<div class='{cls}'><div class='top'>
<span class='tkr'>{html.escape(str(t))}</span><span class='date'>{c.get('cat_date')}</span>
<span class='p'>p={c.get('our_p')}</span>{mkt}<span class='tag'>{html.escape(str(c.get('event_type', '?')))}</span>
<span class='stake'>{html.escape(_stake(t, pos, orders, led))}</span></div>
<div class='what'>{html.escape(str(plain.get('what') or c.get('catalyst', ''))[:300])}</div>
<div class='how'>{html.escape(str(plain.get('conclusion') or '')[:300])}</div>""")
            if pack:
                branches = "".join(f"<span class='branch'>{html.escape(str(b))[:70]}</span>" for b in (pack.get("branches") or {}))
                irw = " · IR-page detector armed" if pack.get("ir_watch") else ""
                out.append(f"<div class='grader'><b>the grader</b>{irw}: {html.escape(str(pack.get('adjudication', ''))[:260])}<br>{branches}</div>")
            elif sec in ("THIS WEEK", "PAST-DUE UNGRADED"):
                out.append("<div class='grader' style='border-color:#A32B18'><b style='color:#A32B18'>no resolution pack</b> — the packs guard flags inside 30d</div>")
            out.append(grade_note + "</div>")
    return "".join(out)


def main():
    OUT.write_text(render())
    print(f"[gauntlet_book] rendered -> gauntlet.html")


if __name__ == "__main__":
    main()
