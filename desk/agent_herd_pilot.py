"""agent_herd_pilot — PRE-REGISTERED, ZERO-CAPITAL pilot (principal question 2026-09-12):
"can we front-run other retail agentic traders?"

MECHANISM UNDER TEST: retail trading agents are built on a handful of model families and fed the
same headlines, so their decisions should be far more CORRELATED than a human crowd's. If that
herd is real, measurable, and moves price, the tradable expression is either the FRONT-RUN
(if the herd's flow arrives after our read and pushes price) or the FADE (if it pushes price and
reverses). Base rate: five front-run pilots on this desk were killed because the feed FOLLOWED
price (see memory: killed-frontruns hub). This one differs only by the homogeneity mechanism and
dies the same way if the panel's picks do not LEAD price.

DESIGN (frozen 2026-09-12; changes require a dated amendment in this docstring):
  MORNING (pre-open, weekdays): collect the retail information set — headline RSS (CNBC,
  MarketWatch), Stocktwits trending, Yahoo most-actives. Run a PANEL of generic retail-agent
  prompts (no desk context, no tools) across three model sizes (haiku / sonnet / opus — proxies
  for the cost tiers retail products deploy). Each returns up to 5 BUY and 3 SELL tickers.
  Store everything with a timestamp BEFORE 09:30 ET. Homogeneity = pairwise Jaccard of BUY sets.
  EVENING (after close): grade every prior panel day whose horizons have matured:
    FLOW  — did the pick appear in NEXT morning's Stocktwits trending / most-actives (T+1) when it
            was not there at T? (hit rate vs the base rate of a random liquid ticker appearing)
    PRICE — open->close on T, close T-1 -> close T+1, T+5, T+20; excess vs SPY; and vs an
            ATTENTION CONTROL (equal-weight of that morning's most-actives NOT picked) so we
            separate "agents pick what is already moving" from "agents move it".
    REVERSAL — sign of T+5 -> T+20 excess vs T+1.
  KILLS (pre-registered):
    K1 by day 30: FLOW hit rate not above base rate at p<0.05 (one-sided)  -> no herd signal.
    K2 by day 30: |mean T+1 excess vs ATTENTION CONTROL| < 0.20% (bid-ask proxy) -> no price effect.
    K3 by day 60: T+5..T+20 excess indistinguishable from zero AND K2 holds -> dead.
    If FLOW predicts AND price reverses (T+1 up, T+20 excess < 0): the expression is the FADE.
    If FLOW predicts AND T+5 excess persists: the expression is the FRONT-RUN — court it.
  NOTHING TRADES. PAPER ONLY. Grades are Brier-style hit rates vs climatology, never "returns".

CLI:
  python3 -m desk.agent_herd_pilot --run [--force]     # morning panel (skips non-trading days unless --force; --force runs are tagged validation)
  python3 -m desk.agent_herd_pilot --grade             # evening grading of matured panel days
  python3 -m desk.agent_herd_pilot --summary           # kill-check readout
Data: desk/data/agent_herd/panel_YYYY-MM-DD.json, grades.jsonl, summary.json
"""
from __future__ import annotations

import datetime as dt
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "desk" / "data" / "agent_herd"
PANEL_MODELS = {
    "haiku": os.environ.get("HERD_MODEL_SMALL", "claude-haiku-4-5-20251001"),
    "sonnet": os.environ.get("HERD_MODEL_MID", "claude-sonnet-5"),
    "opus": os.environ.get("HERD_MODEL_LARGE", "claude-opus-5"),
}
FEEDS = {
    "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "marketwatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"
BIDASK_PROXY = 0.002          # K2 threshold
MAX_BUY, MAX_SELL = 5, 3
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,6}$")

RETAIL_AGENT_PROMPT = """You are an AI trading assistant inside a retail brokerage app. Your user has a $50,000 \
account, trades US-listed stocks and ETFs only, and asks you every morning before the open: \
"What should I buy and sell today?" Use ONLY the information below (you have no tools). \
Be decisive, the way a product like this is expected to be.

TODAY: {today}
HEADLINES (last ~18 hours):
{headlines}

TICKERS TRENDING WITH OTHER RETAIL TRADERS THIS MORNING:
Stocktwits trending: {stocktwits}
Most active on Yahoo Finance: {most_active}

Reply with ONLY a JSON object, no prose, exactly this shape:
{{"buy": [{{"ticker": "XXX", "reason": "one short sentence"}}, ...up to {max_buy}],
  "sell": [{{"ticker": "XXX", "reason": "one short sentence"}}, ...up to {max_sell}]}}
Tickers must be real US symbols (no crypto, no .X suffixes)."""


# ------------------------------------------------------------------ collection
def _get(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def _rss_titles(xml: str, limit: int = 40) -> list[str]:
    items = re.findall(r"<item>(.*?)</item>", xml, re.S)
    out = []
    for it in items[:limit]:
        m = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
        if m:
            t = re.sub(r"\s+", " ", m.group(1)).strip()
            if t:
                out.append(t)
    return out


def collect_context() -> dict:
    ctx = {"asof_utc": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "headlines": [], "stocktwits": [], "most_active": [], "errors": []}
    for name, url in FEEDS.items():
        try:
            ctx["headlines"] += [f"[{name}] {t}" for t in _rss_titles(_get(url))]
        except Exception as e:
            ctx["errors"].append(f"{name}: {type(e).__name__}")
    try:
        d = json.loads(_get("https://api.stocktwits.com/api/2/trending/symbols.json"))
        ctx["stocktwits"] = [s["symbol"] for s in d.get("symbols", []) if not s["symbol"].endswith(".X")]
    except Exception as e:
        ctx["errors"].append(f"stocktwits: {type(e).__name__}")
    try:
        from yfinance.screener import screen
        r = screen("most_actives", count=25)
        ctx["most_active"] = [q["symbol"] for q in r.get("quotes", [])]
    except Exception as e:
        ctx["errors"].append(f"yf_most_active: {type(e).__name__}")
    return ctx


# ------------------------------------------------------------------ panel
def _dispatch(prompt: str, model: str, timeout_s: int = 240) -> dict:
    """Bare claude -p call, NO tools: the agent sees only the retail information set."""
    claude_bin = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
    cmd = [claude_bin, "-p", prompt, "--output-format", "json", "--model", model,
           "--disallowedTools", "Bash,Task,Agent,Write,Edit,WebFetch,WebSearch,Read,Grep,Glob"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s,
                           cwd=str(DATA if DATA.exists() else ROOT))
        payload = json.loads(r.stdout)
        return {"text": payload.get("result", "") or "", "cost": payload.get("total_cost_usd")}
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": f"{type(e).__name__}"}


def parse_picks(text: str) -> dict:
    """Extract {"buy":[...], "sell":[...]} from model output; tolerant of fences/prose."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {"buy": [], "sell": [], "parse_error": "no-json"}
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"buy": [], "sell": [], "parse_error": "bad-json"}
    out = {"buy": [], "sell": []}
    for side, cap in (("buy", MAX_BUY), ("sell", MAX_SELL)):
        seen = set()
        for row in (d.get(side) or [])[:cap]:
            t = str((row or {}).get("ticker", "")).upper().strip().replace("$", "")
            if TICKER_RE.match(t) and t not in seen and not t.endswith(".X"):
                seen.add(t)
                out[side].append({"ticker": t, "reason": str((row or {}).get("reason", ""))[:200]})
    return out


def homogeneity(panel: dict) -> dict:
    """Pairwise Jaccard of BUY sets across models + overlap with the trending lists."""
    sets = {k: {p["ticker"] for p in v.get("buy", [])} for k, v in panel.items() if "buy" in v}
    pairs = {}
    for a, b in itertools.combinations(sorted(sets), 2):
        u = sets[a] | sets[b]
        pairs[f"{a}|{b}"] = round(len(sets[a] & sets[b]) / len(u), 3) if u else None
    vals = [v for v in pairs.values() if v is not None]
    return {"pairwise_jaccard": pairs, "mean_jaccard": round(sum(vals) / len(vals), 3) if vals else None,
            "union_buy": sorted(set().union(*sets.values())) if sets else [],
            "consensus_buy": sorted(t for t in set().union(*sets.values()) if sum(t in s for s in sets.values()) >= 2) if sets else []}


def is_trading_day(d: dt.date) -> bool:
    if d.weekday() >= 5:
        return False
    try:
        import pandas_market_calendars as pmc      # optional
        return not pmc.get_calendar("NYSE").schedule(d, d).empty
    except Exception:
        return True


def run(force: bool = False) -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()
    if not force and not is_trading_day(today):
        return {"skipped": "non-trading day"}
    ctx = collect_context()
    prompt = RETAIL_AGENT_PROMPT.format(
        today=today.isoformat(), headlines="\n".join(f"- {h}" for h in ctx["headlines"][:45]) or "- (none)",
        stocktwits=", ".join(ctx["stocktwits"][:25]) or "(none)", most_active=", ".join(ctx["most_active"][:25]) or "(none)",
        max_buy=MAX_BUY, max_sell=MAX_SELL)
    panel, cost = {}, 0.0
    for name, model in PANEL_MODELS.items():
        res = _dispatch(prompt, model)
        if res.get("error"):
            panel[name] = {"error": res["error"], "model": model}
            continue
        picks = parse_picks(res["text"])
        picks["model"] = model
        picks["raw"] = res["text"][:2000]
        panel[name] = picks
        cost += float(res.get("cost") or 0)
    rec = {"date": today.isoformat(), "asof_utc": ctx["asof_utc"], "validation": bool(force and not is_trading_day(today)),
           "context": {k: ctx[k] for k in ("headlines", "stocktwits", "most_active", "errors")},
           "panel": panel, "homogeneity": homogeneity(panel), "cost_usd": round(cost, 4)}
    (DATA / f"panel_{today.isoformat()}.json").write_text(json.dumps(rec, indent=1))
    return rec


# ------------------------------------------------------------------ grading
def _closes(tickers: list[str], start: dt.date, end: dt.date):
    import yfinance as yf
    px = yf.download(tickers, start=start.isoformat(), end=(end + dt.timedelta(days=1)).isoformat(),
                     auto_adjust=True, progress=False, group_by="column", threads=True)
    return px


def grade_day(rec: dict, today: dt.date, next_panel: dict | None) -> list[dict]:
    """Grade one panel day against matured horizons. Returns per-pick rows (paper only)."""
    d0 = dt.date.fromisoformat(rec["date"])
    picks = []
    for model, p in rec["panel"].items():
        for side in ("buy", "sell"):
            for row in p.get(side, []):
                picks.append((model, side, row["ticker"]))
    if not picks:
        return []
    tickers = sorted({t for _, _, t in picks})
    ctrl = [t for t in rec["context"].get("most_active", []) if t not in tickers][:15]
    import pandas as pd
    px = _closes(tickers + ctrl + ["SPY"], d0 - dt.timedelta(days=5), today)
    if px is None or len(px) == 0:
        return []
    close = px["Close"] if "Close" in px else px
    opn = px["Open"] if "Open" in px else None
    idx = [d.date() for d in close.index]
    if d0 not in idx:
        return []
    i0 = idx.index(d0)
    def ret(t, a, b):
        try:
            return float(close[t].iloc[b] / close[t].iloc[a] - 1)
        except Exception:
            return None
    def horizon(k):
        j = i0 + k
        return j if j < len(idx) else None
    rows = []
    spy = {k: (ret("SPY", i0 - 1, horizon(k)) if horizon(k) is not None else None) for k in (1, 5, 20)}
    ctrl_ret = {}
    for k in (1, 5, 20):
        j = horizon(k)
        vals = [ret(t, i0 - 1, j) for t in ctrl] if j is not None else []
        vals = [v for v in vals if v is not None]
        ctrl_ret[k] = sum(vals) / len(vals) if vals else None
    trend_next = set((next_panel or {}).get("context", {}).get("stocktwits", []) + (next_panel or {}).get("context", {}).get("most_active", []))
    trend_today = set(rec["context"].get("stocktwits", []) + rec["context"].get("most_active", []))
    for model, side, t in picks:
        sign = 1 if side == "buy" else -1
        r = {"date": rec["date"], "graded": today.isoformat(), "model": model, "side": side, "ticker": t,
             "validation": rec.get("validation", False),
             "oc_T": (float(close[t].iloc[i0] / opn[t].iloc[i0] - 1) if opn is not None else None)}
        for k in (1, 5, 20):
            j = horizon(k)
            rr = ret(t, i0 - 1, j) if j is not None else None
            r[f"ret_{k}"] = rr
            r[f"xs_spy_{k}"] = (sign * (rr - spy[k])) if (rr is not None and spy[k] is not None) else None
            r[f"xs_ctrl_{k}"] = (sign * (rr - ctrl_ret[k])) if (rr is not None and ctrl_ret[k] is not None) else None
        r["was_trending_T"] = t in trend_today
        r["flow_hit_T1"] = (t in trend_next) if next_panel else None          # appears next morning
        r["flow_new_T1"] = (t in trend_next and t not in trend_today) if next_panel else None
        rows.append(r)
    return rows


def grade() -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()
    panels = sorted(DATA.glob("panel_*.json"))
    recs = {p.stem[6:]: json.loads(p.read_text()) for p in panels}
    graded_path = DATA / "grades.jsonl"
    done = set()
    if graded_path.exists():
        for ln in graded_path.read_text().splitlines():
            try:
                g = json.loads(ln); done.add((g["date"], g["graded"]))
            except Exception:
                pass
    dates = sorted(recs)
    n = 0
    with graded_path.open("a") as f:
        for i, d in enumerate(dates):
            d0 = dt.date.fromisoformat(d)
            if d0 >= today:
                continue
            # re-grade each day at most once per grading day (horizons mature over time)
            if (d, today.isoformat()) in done:
                continue
            nxt = recs.get(dates[i + 1]) if i + 1 < len(dates) else None
            for row in grade_day(recs[d], today, nxt):
                f.write(json.dumps(row) + "\n"); n += 1
    return {"graded_rows": n, "panels": len(recs)}


def summary() -> dict:
    """Kill-check readout: latest grade per (date, model, side, ticker); hit rates vs climatology."""
    rows = {}
    p = DATA / "grades.jsonl"
    if p.exists():
        for ln in p.read_text().splitlines():
            try:
                g = json.loads(ln)
            except Exception:
                continue
            if g.get("validation"):
                continue
            rows[(g["date"], g["model"], g["side"], g["ticker"])] = g      # latest grade wins
    rs = list(rows.values())
    days = sorted({r["date"] for r in rs})
    def stat(key):
        v = [r[key] for r in rs if r.get(key) is not None]
        if not v:
            return None
        m = sum(v) / len(v); sd = (sum((x - m) ** 2 for x in v) / max(1, len(v) - 1)) ** 0.5
        return {"n": len(v), "mean": round(m, 5), "t": round(m / (sd / len(v) ** 0.5), 2) if sd else None,
                "hit_rate": round(sum(1 for x in v if x > 0) / len(v), 3)}
    flow = [r for r in rs if r.get("flow_new_T1") is not None and not r.get("was_trending_T")]
    flow_hit = (sum(1 for r in flow if r["flow_new_T1"]) / len(flow)) if flow else None
    out = {"trading_days": len(days), "picks_graded": len(rs),
           "flow_new_T1_hit_rate": round(flow_hit, 3) if flow_hit is not None else None, "flow_n": len(flow),
           "xs_ctrl_1": stat("xs_ctrl_1"), "xs_ctrl_5": stat("xs_ctrl_5"), "xs_ctrl_20": stat("xs_ctrl_20"),
           "xs_spy_1": stat("xs_spy_1"), "xs_spy_5": stat("xs_spy_5"), "xs_spy_20": stat("xs_spy_20"),
           "kills": {}}
    if len(days) >= 30:
        k2 = out["xs_ctrl_1"] and abs(out["xs_ctrl_1"]["mean"]) < BIDASK_PROXY
        out["kills"]["K2_no_price_effect_T1"] = bool(k2)
        out["kills"]["K1_flow"] = "needs base-rate panel (flow_new_T1 vs random-liquid appearance rate)"
    if len(days) >= 60:
        k3 = (out["xs_ctrl_20"] and out["xs_ctrl_20"]["t"] is not None and abs(out["xs_ctrl_20"]["t"]) < 2) and out["kills"].get("K2_no_price_effect_T1")
        out["kills"]["K3_dead"] = bool(k3)
    if out["xs_ctrl_1"] and out["xs_ctrl_20"]:
        if out["xs_ctrl_1"]["mean"] > 0 and out["xs_ctrl_20"]["mean"] < 0:
            out["expression_hint"] = "FADE (T+1 up, T+20 excess negative)"
        elif out["xs_ctrl_5"] and out["xs_ctrl_5"]["mean"] > BIDASK_PROXY:
            out["expression_hint"] = "FRONT-RUN candidate (T+5 excess persists) — court it"
    (DATA / "summary.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--run" in a:
        print(json.dumps({k: v for k, v in run(force="--force" in a).items() if k != "context"}, indent=1)[:3000])
    elif "--grade" in a:
        print(json.dumps(grade()))
    else:
        print(json.dumps(summary(), indent=1))
