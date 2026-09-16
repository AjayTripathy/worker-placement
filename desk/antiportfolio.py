"""antiportfolio — the portfolio of everything we REFUSED to own.

Grades every DECLINE/AVOID verdict as if it were a position: baseline = the
name's price on the day the verdict entered the ledger (recovered from git
history — the ledger is committed on every upsert), measured against SPY over
the same window (the beta-placeholder grading doctrine).

  saved_pp = SPY return − name return   (positive: the decline beat holding
             beta instead — a SAVE; negative: the name outran beta — a MISS)

Honesty notes baked in: the antibook precedent says our conviction has
INVERTED before (36% hit rate on directional calls) — this page exists to
find out whether the DECLINE class deserves the trust the landmine-detector
validation implies. Regret is listed first.

Outputs: desk/data/antiportfolio.json + desk/ui/static/antibook.html (the
ANTI tab). Baselines cached; new AVOIDs picked up on each run.
    python3 -m desk.antiportfolio          # registered weekly
READ-ONLY on the world.
"""
from __future__ import annotations

import datetime
import html
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = "desk/data/research_ledger.json"
BASE = ROOT / "desk" / "data" / "antiportfolio_baselines.json"
OUT_JSON = ROOT / "desk" / "data" / "antiportfolio.json"
OUT_HTML = ROOT / "desk" / "ui" / "static" / "antibook.html"

SKIP_PREFIX = ("TAIL-", "SEPT-", "HONESTY-", "BOOK-", "SPX-", "UKR", "SPACEX", "PSLV", "UKRCEASE")


def _git_baselines() -> dict:
    """First date each ticker's verdict became AVOID, from ledger git history."""
    cached = json.loads(BASE.read_text()) if BASE.exists() else {}
    log = subprocess.run(["git", "log", "--reverse", "--format=%H|%cI", "--", LEDGER_PATH],
                         capture_output=True, text=True, cwd=ROOT).stdout.splitlines()
    known = set(cached)
    for line in log:
        sha, ciso = line.split("|")
        # skip commits older than everything we still need only if nothing new could appear;
        # cheap enough to parse all — the ledger is small
        try:
            blob = subprocess.run(["git", "show", f"{sha}:{LEDGER_PATH}"],
                                  capture_output=True, text=True, cwd=ROOT).stdout
            names = json.loads(blob)["names"]
        except Exception:
            continue
        for n in names:
            t = n.get("ticker", "")
            v = (n.get("verdict") or n.get("state") or "").upper()
            if v == "AVOID" and t not in known:
                cached[t] = {"date": ciso[:10], "yf": n.get("yf"), "thesis": (n.get("thesis") or "")[:160]}
                known.add(t)
    BASE.write_text(json.dumps(cached, indent=1))
    return cached


def _yf_series(sym: str, start: str):
    import yfinance as yf
    try:
        h = yf.Ticker(sym).history(start=start, auto_adjust=True)
        if len(h) < 2:
            return None
        return float(h["Close"].iloc[0]), float(h["Close"].iloc[-1])
    except Exception:
        return None


def build() -> dict:
    led = {n["ticker"]: n for n in json.loads((ROOT / LEDGER_PATH).read_text())["names"]}
    baselines = _git_baselines()
    avoids = {t: b for t, b in baselines.items()
              if t in led and (led[t].get("verdict") or led[t].get("state", "")).upper() == "AVOID"
              and not t.startswith(SKIP_PREFIX) and not t[0].isdigit() or
              (t in led and t[0].isdigit() and led[t].get("yf"))}
    # SPY once per unique start date
    import yfinance as yf
    rows, skipped = [], []
    spy_cache = {}
    for t, b in sorted(avoids.items()):
        v = (led.get(t, {}).get("verdict") or "").upper()
        if v != "AVOID":
            continue
        sym = b.get("yf") or led[t].get("yf") or t
        start = b["date"]
        pair = _yf_series(sym, start)
        if not pair:
            skipped.append(t)
            continue
        p0, p1 = pair
        if start not in spy_cache:
            sp = _yf_series("SPY", start)
            spy_cache[start] = (sp[1] / sp[0] - 1) * 100 if sp else None
        spy_ret = spy_cache[start]
        ret = (p1 / p0 - 1) * 100
        rows.append({"ticker": t, "since": start, "px0": round(p0, 2), "px": round(p1, 2),
                     "ret_pct": round(ret, 1), "spy_pct": round(spy_ret, 1) if spy_ret is not None else None,
                     "saved_pp": round((spy_ret - ret), 1) if spy_ret is not None else None,
                     "thesis": b.get("thesis") or (led[t].get("thesis") or "")[:160]})
    import math
    scored = [r for r in rows if r["saved_pp"] is not None and math.isfinite(r["saved_pp"])]
    saves = sorted([r for r in scored if r["saved_pp"] > 0], key=lambda r: -r["saved_pp"])
    misses = sorted([r for r in scored if r["saved_pp"] <= 0], key=lambda r: r["saved_pp"])
    n = len(scored)
    d = {"asof": datetime.date.today().isoformat(), "n_scored": n, "n_skipped": len(skipped),
         "skipped": skipped,
         "hit_rate": round(len(saves) / n * 100) if n else None,
         "mean_saved_pp": round(sum(r["saved_pp"] for r in scored) / n, 1) if n else None,
         "median_saved_pp": round(sorted(r["saved_pp"] for r in scored)[n // 2], 1) if n else None,
         "misses": misses, "saves": saves}
    OUT_JSON.write_text(json.dumps(d, indent=1))
    return d


def render(d: dict) -> str:
    rowfmt = lambda r, col: (f"<tr><td><b>{html.escape(r['ticker'])}</b></td><td class='n'>{r['since']}</td>"
                             f"<td class='n'>{r['ret_pct']:+.1f}%</td><td class='n'>{r['spy_pct']:+.1f}%</td>"
                             f"<td class='n' style='color:{col};font-weight:700'>{r['saved_pp']:+.1f}pp</td>"
                             f"<td>{html.escape(r['thesis'])[:110]}</td></tr>")
    head = f"""<title>The Anti-Portfolio</title><style>
body{{font-family:'Helvetica Neue',Arial,sans-serif;max-width:960px;margin:0 auto;padding:24px;background:#fff;color:#000;line-height:1.45}}
h1{{font-size:24px;margin:0}} .sub{{color:#3D453F;font-size:13px;margin:2px 0 14px}}
h2{{font-size:13px;text-transform:uppercase;letter-spacing:.08em;border-bottom:2px solid #000;padding-bottom:4px;margin:22px 0 8px}}
table{{border-collapse:collapse;width:100%;font-size:12.5px}}th{{text-align:left;font-size:10px;text-transform:uppercase;border-bottom:2px solid #000;padding:5px 8px}}
td{{padding:5px 8px;border-bottom:1px solid #D8DDD8;vertical-align:top}} td.n{{font-family:ui-monospace,Menlo,monospace;white-space:nowrap}}
.big{{font-size:30px;font-weight:800}} .kpi{{display:inline-block;margin-right:28px}} .kpi .l{{font-size:10px;text-transform:uppercase;color:#3D453F;letter-spacing:.06em}}
.note{{background:#F6F8F6;border:1px solid #D8DDD8;border-radius:5px;padding:10px 14px;font-size:12.5px;max-width:82ch}}
</style><h1>The Anti-Portfolio</h1>
<div class='sub'>every DECLINE graded as a position we refused &middot; baseline = the verdict-day price (from git history) &middot; scored vs SPY same-window &middot; as of {d['asof']}</div>
<div style='margin:10px 0 4px'>
<span class='kpi'><div class='big'>{d['n_scored']}</div><div class='l'>declines scored</div></span>
<span class='kpi'><div class='big'>{d['hit_rate']}%</div><div class='l'>saves (beat holding beta)</div></span>
<span class='kpi'><div class='big'>{d['mean_saved_pp']:+.1f}pp</div><div class='l'>mean saved vs SPY</div></span>
<span class='kpi'><div class='big'>{d['median_saved_pp']:+.1f}pp</div><div class='l'>median saved</div></span></div>
<div class='note'>Reading: <b>saved_pp = SPY − name</b> over the window since we declined. Positive = the money that would have gone here did better in beta — the decline SAVED money. Negative = the name outran beta — REGRET, listed first on purpose. Skipped (no price series): {', '.join(d['skipped']) or 'none'}. Caution carried from the antibook: our directional conviction has inverted before; this page is the DECLINE class's honest grade.</div>"""
    cols = "<tr><th>name</th><th>declined</th><th>its return</th><th>SPY</th><th>saved</th><th>why we declined</th></tr>"
    misses = "".join(rowfmt(r, "#A32B18") for r in d["misses"])
    saves = "".join(rowfmt(r, "#14532D") for r in d["saves"])
    return (head + f"<h2>Regret — declines that outran beta ({len(d['misses'])})</h2><table>{cols}{misses}</table>"
            + f"<h2>Saves — declines that beta beat ({len(d['saves'])})</h2><table>{cols}{saves}</table>")


def main():
    d = build()
    OUT_HTML.write_text(render(d))
    print(f"[antiportfolio] {d['n_scored']} declines scored | hit {d['hit_rate']}% | "
          f"mean saved {d['mean_saved_pp']:+.1f}pp | regret list: "
          f"{[r['ticker'] for r in d['misses'][:5]]}")


if __name__ == "__main__":
    main()
