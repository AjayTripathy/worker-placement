"""aggregator — the single read-only data layer behind the Desk/SignalOS dashboard. Pulls every
surface (watches, detectors, catalysts, the book, signals, harvest, research archive) from its
authoritative source in the repo and normalizes it to plain dicts the API serves. Each section is
isolated in try/except so one broken source degrades that card, never the whole page. READ-ONLY.
"""
from __future__ import annotations
import json, time, datetime, sys, re, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _safe(fn):
    try:
        return fn()
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


_LIVE = {}   # symbol -> (price, epoch) — short-TTL cache so page navigation doesn't re-hit yfinance


def _price_age_s(sym) -> float | None:
    """Age in seconds of the cached live price for a symbol (None = never fetched)."""
    e = _LIVE.get(sym)
    return None if not e else (time.time() - e[1])


def _live_prices(symbols, ttl=120) -> dict:
    """Live prices for display — DELEGATES to desk.prices (the single pricing source: registry +
    sanity rails + freshness). Returns {yf_symbol: px} for backward compatibility; suspect quotes
    return None (never show a bad tick), and _LIVE mirrors (px, asof) so _price_age_s keeps working."""
    from desk import prices as P
    out = {}
    for s_ in {x for x in symbols if x}:
        q = P.quote_yf(s_)
        px = None if q["suspect"] else q["px"]
        if px is not None:
            _LIVE[s_] = (round(float(px), 2), q["asof"] or time.time())
            out[s_] = _LIVE[s_][0]
    return out


def _last_log_rows(path: Path):
    """Last JSONL line's ({tkr: row}, asof) for a basket watch log (live px + zone, no network call)."""
    if not path.exists():
        return {}, None
    lines = [l for l in path.read_text().splitlines() if l.strip()]
    if not lines:
        return {}, None
    try:
        rec = json.loads(lines[-1])
        return {r["tkr"]: r for r in rec.get("rows", [])}, rec.get("asof")
    except Exception:
        return {}, None


# ---------------- WATCHES ----------------
RUNS_DIR = Path(__file__).resolve().parent / "data" / "watch_runs"


def _line_score(l: str) -> int:
    """Rank a watch-output line by how actionable it is as the inline head. Higher = better.
    Prefers a concrete signal line (a price + a band/state) over the generic closing ACTION/summary line."""
    u = l.upper()
    s = 0
    if l[:1].isspace():
        s -= 4                       # indented = a continuation/detail line (FV/catalyst), not the header
    has_price = ("$" in l) or bool(re.search(r"\b\d+\.\d{2}\b", l))
    state = any(k in u for k in ("ABOVE", "BELOW", "ZONE", "ACCUMULATE", "ENTRY", "TOUCH", "DEEP-VALUE", "IN-BAND"))
    signal = any(k in u for k in ("VETO_", "SELL_VOL", "DIRECTIONAL", "DETFIRE", "_CANDIDATE", "PROMOTE-READY"))
    if has_price and state:
        s += 6                       # the money line: a name at a price in a named band
    if signal:
        s += 5                       # an explicit engine verdict
    if has_price:
        s += 2
    if state:
        s += 2
    if "->" in l:
        s += 1
    # the closing summary / bookkeeping lines are the weakest heads
    if l.lstrip()[:1] == "[" or any(k in u for k in ("ACTION:", "===", "LOGGED", "STAGING", "NO ORDERS", "DILIGENCE QUEUE")):
        s -= 3
    return s


def _watch_latest(name: str):
    """Latest captured output of a watch (written by the Run endpoint / a Desk run) → inline reading."""
    f = RUNS_DIR / f"{name}.txt"
    if not f.exists():
        return None
    lines = [l for l in f.read_text(errors="ignore").splitlines() if l.strip()]
    if not lines:
        return None
    # the inline head = the highest-scoring (most actionable) line; ties → the EARLIEST (a watch leads
    # its output with its primary subject, e.g. stvn_book's "STVN $.. -> ABOVE" header line)
    best, best_score = lines[-1], -10
    for l in lines:
        sc = _line_score(l)
        if sc > best_score:
            best, best_score = l, sc
    return {"head": best.strip()[:150], "lines": lines[-14:],
            "ran": datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="minutes")}


def watches() -> dict:
    from desk.registry import WATCHES, _load_state, _cadence_minutes
    st = _load_state()
    now = time.time()
    out = []
    for w in WATCHES:
        last = st.get(w["name"], 0)
        mins = _cadence_minutes(w["cadence"])
        due_in = None if not last else round((last + mins * 60 - now) / 60)
        out.append({
            "name": w["name"], "cadence": str(w["cadence"]), "asset_class": w.get("asset_class"),
            "extractor": w.get("extractor"), "enabled": w.get("enabled", False),
            "note": w.get("note", ""), "log": w.get("log"), "latest": _watch_latest(w["name"]),
            "last_run": (datetime.datetime.fromtimestamp(last).isoformat(timespec="minutes") if last else None),
            "due_in_min": due_in,
        })
    return {"count": len(out), "enabled": sum(1 for w in out if w["enabled"]), "watches": out}


# ---------------- DETECTORS ----------------
def detectors() -> dict:
    kg = json.loads((ROOT / "knowledge_graph" / "knowledge_graph.json").read_text())
    disp = {d["name"]: d.get("applies_to", {}) for d in kg.get("dispatch_index", [])}
    inv = []
    for d in kg.get("detector_inventory", []):
        inv.append({
            "name": d["name"], "vertical": d.get("vertical"), "kind": d.get("kind", "detector"),
            "category": d.get("category"), "asset_class": d.get("asset_class"),
            "summary": d.get("summary", ""), "primary_source": d.get("primary_source"),
            "channels": d.get("likely_signal_channels", []),
            "dispatch": disp.get(d["name"]),   # APPLIES_TO if dispatch-indexed
        })
    inv.sort(key=lambda x: (x["vertical"] or "", x["kind"], x["name"]))
    from collections import Counter
    by_kind = dict(Counter(d["kind"] for d in inv))
    return {"counts": kg.get("_counts", {}), "dispatch_indexed": len(disp), "by_kind": by_kind,
            "verticals": sorted({d["vertical"] for d in inv if d["vertical"]}),
            "kinds": sorted(by_kind), "detectors": inv}


# ---------------- CATALYSTS / TRIGGERS ----------------
def _catalyst_predictions() -> dict:
    p = ROOT / "desk" / "data" / "catalyst_predictions.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text()).get("predictions", {})
    except Exception:
        return {}


def catalysts() -> dict:
    from desk.catalyst_watch import snapshot
    rows, today = snapshot()
    preds = _catalyst_predictions()
    out = []
    for r in rows:
        d = r["days"]
        sev = "HIGH" if -3 <= d <= 21 else ("MED" if -10 <= d <= 60 else "low")
        out.append({"ticker": r["ticker"], "date": r["date"], "days": d, "severity": sev,
                    "catalyst": r["catalyst"], "watch": r.get("watch", r.get("thesis", "")),
                    "antibook": r.get("antibook", False), "imminent": -10 <= d <= 60,
                    "prediction": preds.get(r["ticker"])})
    return {"today": str(today), "count": len(out), "predicted": sum(1 for r in out if r["prediction"]),
            "imminent": sum(1 for r in out if r["imminent"]), "catalysts": out}


# ---------------- BOOK ----------------
def _basket(mod_path, log_name, currency):
    import importlib
    mod = importlib.import_module(mod_path)
    basket = getattr(mod, "BASKET")
    rows_by_tkr, asof = _last_log_rows(ROOT / "verticals" / "deep_value" / "data" / log_name)
    # live prices: smallcap symbol == ticker; krx names carry their yfinance symbol in cfg["yf"]
    sym_of = {t: (cfg.get("yf") or t) for t, cfg in basket.items()}
    live = _live_prices(list(sym_of.values()))
    # IBKR override: yfinance's Korean (.KQ/.KS) feed lags by days — prefer a cached live IBKR snapshot.
    override = {}
    ovf = Path(__file__).resolve().parent / "data" / "krx_px_override.json"
    if ovf.exists():
        try:
            o = json.loads(ovf.read_text())
            override = {k: v for k, v in o.get("prices", {}).items()}
        except Exception:
            pass
    zone_fn = getattr(mod, "_zone", None)
    any_live = False
    out = []
    for tkr, cfg in basket.items():
        lr = rows_by_tkr.get(tkr, {})
        bear, base, bull = cfg["fv"]
        ov = override.get(tkr)
        is_live = (ov is not None) or (sym_of[tkr] in live)
        any_live = any_live or is_live
        px = (ov.get("px") if ov else (live.get(sym_of[tkr]) if sym_of[tkr] in live else lr.get("px")))
        zone = lr.get("zone")
        if px is not None and zone_fn:           # recompute the entry zone from the live price
            try:
                zone = zone_fn(px, cfg)[0]
            except Exception:
                pass
        out.append({
            "ticker": tkr, "currency": currency, "conviction": cfg.get("conv") or cfg.get("verdict"),
            "sector": cfg.get("sector"), "entry": cfg.get("entry"), "fv_bear": bear, "fv_base": base,
            "fv_bull": bull, "px": px, "zone": zone, "live": is_live,
            "upside_base": (round((base / px - 1) * 100) if px else None),
            "thesis": cfg.get("thesis", ""), "kill": cfg.get("kill", ""),
        })
    return out, (datetime.datetime.now().isoformat(timespec="minutes") + " (live)" if any_live else asof)


def book() -> dict:
    from desk.book_universe import BOOK
    sc, sc_asof = _basket("verticals.deep_value.smallcap_value_watch", "smallcap_value_log.jsonl", "USD")
    krx, krx_asof = _basket("verticals.deep_value.krx_value_watch", "krx_value_log.jsonl", "KRW")
    # mark HELD names (cross-ref the IBKR positions cache) — a band 'zone' of WATCH on a name we OWN reads
    # backwards without this; the zone is "price vs the ADD band", not "don't own it"
    held = set()
    pc = Path(__file__).resolve().parent / "data" / "positions_cache.json"
    if pc.exists():
        try:
            held = {x["symbol"].split()[0] for x in json.loads(pc.read_text()).get("positions", [])}
        except Exception:
            pass
    for r in sc + krx:
        r["held"] = r["ticker"] in held
    # verified universe (generator+skeptic survivors)
    verified = _safe(lambda: json.loads((ROOT / "verticals/deep_value/data/verified_harvest_candidates.json").read_text()))
    vnames = [v.get("sym") for v in verified] if isinstance(verified, list) else []
    # feature universe (which detectors each name attracts)
    feats = {t: [k for k, val in meta.items() if val is True] for t, meta in BOOK.items()}
    return {"smallcap": sc, "smallcap_asof": sc_asof, "krx": krx, "krx_asof": krx_asof,
            "verified_count": len(vnames), "verified_names": vnames,
            "feature_universe": feats, "universe_count": len(BOOK)}


# ---------------- WATCHLIST (research ledger — every diligenced name + verdict) ----------------
def watchlist() -> dict:
    p = ROOT / "desk" / "data" / "research_ledger.json"
    if not p.exists():
        return {"asof": None, "names": [], "sleeves": {}}
    d = json.loads(p.read_text())
    names = d.get("names", [])
    live = _live_prices([n.get("yf") for n in names if n.get("yf")])
    held = set()
    pc = Path(__file__).resolve().parent / "data" / "positions_cache.json"
    if pc.exists():
        try:
            held = {x["symbol"] for x in json.loads(pc.read_text()).get("positions", [])}
        except Exception:
            pass
    for n in names:
        n["px"] = live.get(n.get("yf"))
        n["live"] = n.get("yf") in live
        n["held"] = n["ticker"] in held
    sleeves = {}
    for n in names:
        sleeves.setdefault(n.get("sleeve", "other"), []).append(n)
    return {"asof": d.get("asof"), "count": len(names), "sleeves": sleeves,
            "verdicts": sorted({n.get("verdict") for n in names})}


# ---------------- POSITIONS ----------------
def _position_targets() -> dict:
    """Per-ticker thesis context (base FV, add level, conviction) from the band-watch baskets + the
    research ledger — so the P&L page can show where a holding sits vs its diligenced target."""
    import importlib
    t = {}
    for mod_path in ("verticals.deep_value.smallcap_value_watch", "verticals.deep_value.krx_value_watch"):
        try:
            B = getattr(importlib.import_module(mod_path), "BASKET")
            for tk, cfg in B.items():
                fv = cfg.get("fv")
                t[tk] = {"target": (fv[1] if fv else None), "add": (cfg.get("entry") or [None, None])[1],
                         "conviction": cfg.get("conv") or cfg.get("verdict"), "src": "book"}
        except Exception:
            pass
    try:
        for n in json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", []):
            if n["ticker"] not in t:
                q = n.get("quant", {})
                t[n["ticker"]] = {"target": q.get("fv_base"), "add": n.get("alert_below"),
                                  "conviction": n.get("conviction"), "verdict": n.get("verdict"), "src": "ledger"}
    except Exception:
        pass
    return t


def positions() -> dict:
    p = Path(__file__).resolve().parent / "data" / "positions_cache.json"
    if not p.exists():
        return {"asof": None, "positions": [], "open_orders": [], "note": "no snapshot cached yet"}
    d = json.loads(p.read_text())
    pos = d.get("positions", [])
    # refresh equity (STK) market prices live; recompute mkt value + unrealized from the cached avg cost
    live = _live_prices([x["symbol"] for x in pos if x.get("asset_class") == "STK"])
    for x in pos:
        if x["symbol"] in live:
            x["market_price"] = live[x["symbol"]]
            x["market_value"] = round(live[x["symbol"]] * x["qty"], 2)
            x["unrealized_pnl"] = round((live[x["symbol"]] - x["avg_price"]) * x["qty"], 2)
            x["live"] = True
    if any(x.get("live") for x in pos):
        d["asof"] = datetime.datetime.now().isoformat(timespec="minutes") + " (equity live)"
    eq = sum(x["market_value"] for x in pos if x.get("asset_class") == "STK")
    # enrich each position: unrealized %, equity weight, and the thesis context (target FV / add level)
    tgt = _position_targets()
    cost_basis = 0.0
    for x in pos:
        if x.get("avg_price"):
            x["unrealized_pct"] = round((x["market_price"] / x["avg_price"] - 1) * 100, 1)
        if x.get("asset_class") == "STK":
            x["weight"] = round(x["market_value"] / eq * 100, 1) if eq else None
            cost_basis += x["avg_price"] * x["qty"]
        c = tgt.get(x["symbol"].split()[0])
        if c:
            x["ctx"] = c
            if isinstance(c.get("target"), (int, float)) and x.get("market_price"):
                x["upside_to_target_pct"] = round((c["target"] / x["market_price"] - 1) * 100)
    d["total_cost"] = round(cost_basis)
    d["total_unrealized_pct"] = round(sum(x["unrealized_pnl"] for x in pos if x.get("asset_class") == "STK") / cost_basis * 100, 1) if cost_basis else None
    # link covered calls: a SHORT option on the same underlying CAPS the stock — surface the NET economic P&L
    import re as _re
    shorts = [x for x in pos if x.get("asset_class") == "OPT" and (x.get("qty") or 0) < 0]
    for x in pos:
        if x.get("asset_class") != "STK":
            continue
        for o in shorts:
            if o["symbol"].split()[0] == x["symbol"]:
                mk = _re.search(r"(\d+(?:\.\d+)?)\s*(?:CALL|C)\b", o["symbol"])
                strike = float(mk.group(1)) if mk else None
                contracts = int(abs(o["qty"]))
                # capped exit value = strike*shares (called away) + premium collected, vs cost
                capped_val = (strike * contracts * 100 if strike else None)
                x["covered"] = {"call_pnl": round(o["unrealized_pnl"], 2),
                                "net_pnl": round(x["unrealized_pnl"] + o["unrealized_pnl"], 2),
                                "strike": strike, "contracts": contracts,
                                "max_value_if_assigned": capped_val}
                break
    upnl = sum(x["unrealized_pnl"] for x in pos)
    harvest = [x for x in pos if x.get("harvest_candidate")]
    return {**d, "equity_mv": round(eq), "total_unrealized": round(upnl, 2),
            "harvest_candidates": [x["symbol"] for x in harvest],
            "harvestable_loss": round(sum(x["unrealized_pnl"] for x in harvest), 2)}


# ---------------- TRIGGERS (kill-triggers across the book + dated catalysts) ----------------
def triggers() -> dict:
    import importlib
    out = []
    for mod_path, cur in [("verticals.deep_value.smallcap_value_watch", "USD"),
                          ("verticals.deep_value.krx_value_watch", "KRW")]:
        try:
            basket = getattr(importlib.import_module(mod_path), "BASKET")
            for tkr, cfg in basket.items():
                if cfg.get("kill"):
                    out.append({"ticker": tkr, "type": "kill_trigger",
                                "conviction": cfg.get("conv") or cfg.get("verdict"),
                                "detail": cfg["kill"]})
        except Exception:
            pass
    # dated event triggers from the catalyst watch
    try:
        from desk.catalyst_watch import snapshot
        rows, _ = snapshot()
        for r in rows:
            out.append({"ticker": r["ticker"], "type": "dated_catalyst", "days": r["days"],
                        "detail": r["catalyst"] + " — " + r.get("watch", "")})
    except Exception:
        pass
    kill = [t for t in out if t["type"] == "kill_trigger"]
    dated = sorted([t for t in out if t["type"] == "dated_catalyst"], key=lambda x: x.get("days", 999))
    # ENTRY-trigger watch: research-ledger WATCH names carrying a price level — alert when px <= alert_below
    entry = []
    try:
        led = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text())
        names = [n for n in led.get("names", []) if n.get("alert_below")]
        live = _live_prices([n.get("yf") for n in names if n.get("yf")])
        for n in names:
            # per-name tolerance: a single malformed ledger entry (e.g. missing "name") must not
            # truncate the whole trigger board — that bug silently hid 137/220 alert rows until 2026-07-30
            px = live.get(n.get("yf"))
            trig = px is not None and px <= n["alert_below"]
            entry.append({"ticker": n["ticker"], "name": n.get("name", n["ticker"]), "sleeve": n.get("sleeve"),
                          "verdict": n.get("verdict"), "alert_below": n["alert_below"], "px": px,
                          "pct_to_trigger": (round((px / n["alert_below"] - 1) * 100) if px else None),
                          "triggered": trig, "detail": n.get("entry", "")})
        entry.sort(key=lambda x: (not x["triggered"], x.get("pct_to_trigger") if x.get("pct_to_trigger") is not None else 999))
    except Exception:
        pass
    return {"kill_count": len(kill), "dated_count": len(dated), "entry_count": len(entry),
            "entry_triggered": sum(1 for e in entry if e["triggered"]),
            "kill_triggers": kill, "dated_triggers": dated, "entry_triggers": entry}


# ---------------- SIGNALS ----------------
def signals() -> dict:
    act = _safe(lambda: json.loads((ROOT / "desk/data/desk_actionable.json").read_text()))
    feed = []
    # also scan recent per-watch logs for the latest ALERT lines
    return {"latest_run": act if isinstance(act, dict) else {}, "feed": feed}


# ---------------- HARVEST ----------------
def harvest() -> dict:
    import desk.harvest_ledger as H
    para = _safe(H.parametric_realized)
    diy = _safe(H.diy_realized)
    para = para if isinstance(para, (int, float)) else 0.0
    diy = diy if isinstance(diy, (int, float)) else 0.0
    realized = para + diy + H.EXISTING_LOSSES
    today = datetime.date.today()
    days_left = (H.YEAR_END - today).days
    yday = today.timetuple().tm_yday
    run_rate = (para + diy) / max(yday, 1) * 365 if (para + diy) else 0
    projected = H.EXISTING_LOSSES + (H.PARAMETRIC_TARGET if para < H.PARAMETRIC_TARGET else para) + diy
    return {"goal": H.GOAL, "realized": round(realized), "parametric": round(para), "diy": round(diy),
            "existing_losses": H.EXISTING_LOSSES, "parametric_target": H.PARAMETRIC_TARGET,
            "projected_year_end": round(projected), "gap": round(H.GOAL - projected),
            "pct_to_goal": round(realized / H.GOAL * 100), "days_left": days_left,
            "on_pace": projected >= H.GOAL}


# ---------------- RESEARCH ARCHIVE ----------------
def _title_of(md: Path) -> str:
    try:
        for line in md.read_text(errors="ignore").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except Exception:
        pass
    return md.stem.replace("_", " ")


def research() -> dict:
    items = []
    scan_dirs = [ROOT / "verticals/deep_value/data", ROOT / "verticals/buyside_dd/outputs"]
    seen = set()
    for d in scan_dirs:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md")):
            if p.name.startswith("_") or p.stat().st_size < 200:
                continue
            key = p.stem.lower()
            pdf = p.with_suffix(".pdf")
            items.append({"title": _title_of(p), "file": str(p.relative_to(ROOT)),
                          "kind": "deck" if "PITCH" in p.name or "DECK" in p.name else
                                  ("trap" if "_trap" in p.name.lower() else
                                   ("dd" if "_DD" in p.name or "dd" in p.name.lower() else "report")),
                          "has_pdf": pdf.exists(), "kb": round(p.stat().st_size / 1024),
                          "mtime": datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="minutes")})
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return {"count": len(items), "items": items}


# ---------------- TICKER DOSSIER (click a ticker -> all research on it) ----------------
_DOC_CACHE = None


def _research_docs_text():
    global _DOC_CACHE
    if _DOC_CACHE is None:
        _DOC_CACHE = []
        for it in research().get("items", []):
            try:
                txt = (ROOT / it["file"]).read_text(errors="ignore")
            except Exception:
                txt = ""
            _DOC_CACHE.append((it, txt))
    return _DOC_CACHE


def ticker_dossier(sym: str) -> dict:
    import re
    s = sym.upper().strip()
    base = s.split(".")[0]
    pat = re.compile(r"\b" + re.escape(base) + r"\b")          # case-sensitive: matches TICKER, not lowercase words
    # ledger
    led = None
    try:
        for n in json.loads((ROOT / "desk/data/research_ledger.json").read_text()).get("names", []):
            if n["ticker"].upper() == s:
                led = n
                break
    except Exception:
        pass
    # band-watch book entry
    bk = None
    try:
        b = book()
        for r in (b.get("smallcap", []) + b.get("krx", [])):
            if r["ticker"].upper() == s:
                bk = r
                break
    except Exception:
        pass
    # position
    pos = None
    try:
        for x in positions().get("positions", []):
            if x["symbol"].upper().split()[0] == s:
                pos = x
                break
    except Exception:
        pass
    # catalyst
    cat = None
    try:
        for c in catalysts().get("catalysts", []):
            if c["ticker"].upper() == s:
                cat = c
                break
    except Exception:
        pass
    # detector features
    feats = []
    try:
        from desk.book_universe import BOOK
        meta = BOOK.get(s, {})
        feats = [k for k, v in meta.items() if v is True]
    except Exception:
        pass
    # research docs: filename, title, or a case-sensitive word-boundary text mention.
    # AMBIG = short symbols that collide with exchange abbreviations / common tokens (KRX=Korea Exchange,
    # DG, AST, J): for these, match only on filename/title — NOT loose body text — to avoid false attaches.
    AMBIG = {"KRX", "DG", "AST", "J", "AI"}
    docs = []
    for it, txt in _research_docs_text():
        hit = pat.search(it["file"]) or pat.search(it["title"])
        if not hit and base not in AMBIG and txt:
            hit = pat.search(txt)
        if hit:
            docs.append({k: it[k] for k in ("title", "file", "kind", "has_pdf", "mtime")})
    docs.sort(key=lambda d: d["mtime"], reverse=True)
    # edge-classification record (the DD verdict + the plain-language edge explainer)
    ec = None
    for cand in (s, base, s + ".L", base + ".L"):
        f = ROOT / "desk" / "data" / "edge_classifications" / (cand + ".json")
        if f.exists():
            try:
                ec = json.loads(f.read_text())
                break
            except Exception:
                pass
    # briefs (DD / case studies / pitches) that cover this ticker
    briefs = []
    try:
        for b in json.loads((ROOT / "desk/data/briefs_manifest.json").read_text()).get("briefs", []):
            toks = re.split(r"[^A-Za-z0-9.]+", (b.get("tickers") or "").upper())
            if base in toks or s in toks:
                briefs.append({k: b.get(k) for k in ("title", "file", "tag", "date")})
    except Exception:
        pass
    # closed trades on this name
    trades = []
    try:
        for t in json.loads((ROOT / "desk/data/closed_trades.json").read_text()).get("trades", []):
            if (t.get("ticker") or "").upper() == s:
                trades.append(t)
    except Exception:
        pass
    # convexity-bucket role — analysis for barbell names that may not have a ledger entry
    bucket = None
    try:
        cb = json.loads((ROOT / "desk/data/convexity_bucket.json").read_text())
        for grp in ("core", "satellite", "reserve"):
            g = cb.get(grp) or {}
            if s in g or base in g:
                bucket = {**(g.get(s) or g.get(base)), "sleeve": grp}
                break
    except Exception:
        pass
    name = (led or {}).get("name") or (pos or {}).get("symbol") or s
    return {"ticker": s, "name": name, "ledger": led, "book": bk, "position": pos,
            "catalyst": cat, "features": feats, "docs": docs, "doc_count": len(docs),
            "edge_record": ec, "edge_explainer": (ec or {}).get("edge_explainer"),
            "edge_source": (led or {}).get("edge_source") or ("CONVEXITY" if bucket else None),
            "frozen_calls": _frozen_calls(sym), "briefs": briefs, "trades": trades,
            "bucket": bucket,
            "found": bool(led or bk or pos or cat or docs or ec or bucket)}


# ---------------- OVERVIEW ----------------
def overview() -> dict:
    w = _safe(watches); d = _safe(detectors); c = _safe(catalysts); b = _safe(book)
    h = _safe(harvest); r = _safe(research); p = _safe(positions); t = _safe(triggers); s = _safe(signals); wl = _safe(watchlist)
    sr = s.get("latest_run", {}) if isinstance(s, dict) else {}
    return {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "watches": {"total": w.get("count"), "enabled": w.get("enabled")} if isinstance(w, dict) else {},
        "detectors": {**(d.get("counts", {}) if isinstance(d, dict) else {}),
                      "by_kind": d.get("by_kind", {}) if isinstance(d, dict) else {}},
        "catalysts": {"total": c.get("count"), "imminent": c.get("imminent")} if isinstance(c, dict) else {},
        "book": {"smallcap": len(b.get("smallcap", [])), "krx": len(b.get("krx", [])),
                 "verified": b.get("verified_count"), "universe": b.get("universe_count")} if isinstance(b, dict) else {},
        "watchlist": {"count": wl.get("count"), "sleeves": len(wl.get("sleeves", {}))} if isinstance(wl, dict) else {},
        "harvest": {"pct_to_goal": h.get("pct_to_goal"), "on_pace": h.get("on_pace"),
                    "gap": h.get("gap")} if isinstance(h, dict) else {},
        "research": {"docs": r.get("count")} if isinstance(r, dict) else {},
        "positions": {"equity_mv": p.get("equity_mv"), "unrealized": p.get("total_unrealized"),
                      "harvestable": p.get("harvestable_loss"), "open_orders": len(p.get("open_orders", []))} if isinstance(p, dict) else {},
        "triggers": {"kill": t.get("kill_count"), "dated": t.get("dated_count")} if isinstance(t, dict) else {},
        "signals": {"fresh": sr.get("n_fresh"), "push": len(sr.get("push", [])), "actionable": len(sr.get("actionable", []))},
    }


# ---------------- ENTRY (highest-conviction orders to place today) ----------------
ENTRY_PLAN = ROOT / "desk" / "data" / "entry_plan.json"
APPROVED_ORDERS = Path(__file__).resolve().parent / "data" / "approved_orders.json"
# approximate FX → USD for sizing display only (limit orders execute in local ccy). GBP is quoted in PENCE on LSE.
_FX_USD = {"USD": 1.0, "EUR": 1.08, "GBP": 0.0127, "PLN": 0.27, "CHF": 1.25, "KRW": 0.00073}


def _approved_set() -> set:
    if APPROVED_ORDERS.exists():
        try:
            return set(json.loads(APPROVED_ORDERS.read_text()).get("approved", []))
        except Exception:
            return set()
    return set()


def set_order_approval(ticker: str, approved: bool) -> dict:
    """Stage/unstage an approved order. READ-ONLY w.r.t. IBKR — writes only to a local queue file; the
    assistant later places each queued order with explicit per-order confirmation. Never touches the broker."""
    cur = _approved_set()
    if approved:
        cur.add(ticker)
    else:
        cur.discard(ticker)
    APPROVED_ORDERS.parent.mkdir(parents=True, exist_ok=True)
    APPROVED_ORDERS.write_text(json.dumps({"approved": sorted(cur),
                                           "updated": datetime.datetime.now().isoformat(timespec="seconds")}, indent=1))
    return {"ticker": ticker, "approved": approved, "queue": sorted(cur)}


def entry_candidates() -> dict:
    if not ENTRY_PLAN.exists():
        return {"asof": None, "orders": [], "target_nlv": None, "approved_count": 0}
    plan = json.loads(ENTRY_PLAN.read_text())
    nlv = plan.get("target_nlv") or plan.get("book_nlv")
    cash = plan.get("deployable_cash")
    approved = _approved_set()
    # IBKR truth: a WORKING order at the Gateway = approved, regardless of the manual toggle
    ibkr_working = set()
    try:
        oc = json.loads((ROOT / "desk" / "ui" / "data" / "orders_cache.json").read_text())
        for o in oc.get("orders", []):
            if str(o.get("status", "")).upper() in ("SUBMITTED", "PRESUBMITTED", "NEW", "PENDINGSUBMIT", "PENDING_NEW"):
                ibkr_working.add(o["symbol"])
        approved = approved | ibkr_working
    except Exception:
        pass
    # join the edge classification (thesis_type / species / target) from the research ledger
    led = {}
    try:
        for n in json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", []):
            led[n["ticker"]] = n
    except Exception:
        pass
    out = []
    tot_cost = tot_appr = 0.0
    for o in sorted(plan.get("orders", []), key=lambda x: (x.get("tranche", 9), x.get("rank", 99))):
        fx = _FX_USD.get(o.get("ccy", "USD"), 1.0)
        # calendared sentinel rows (qty 0 / limit null, e.g. DGE.L 07-31) must not TypeError the panel
        est_usd = round((o.get("qty") or 0) * (o.get("limit") or 0) * fx)
        is_appr = o["ticker"] in approved
        adv = o.get("adv_usd")
        # liquidity: rough days-to-fill at ~25% of ADV participation (a non-disruptive accumulation pace)
        days = (round(est_usd / (adv * 0.25), 1) if adv else None)
        liq = "deep" if (days is not None and days <= 1) else ("work" if (days is not None and days <= 4) else
              ("THIN" if days is not None else None))
        tot_cost += est_usd
        if is_appr:
            tot_appr += est_usd
        ln = led.get(o["ticker"], {})
        edge = ln.get("thesis_type", "")
        if edge == "EDGE" and ln.get("edge_species"):
            edge = "EDGE:" + ln["edge_species"].split()[0]
        out.append({**o, "est_usd": est_usd, "approved": is_appr,
                    "weight_actual_pct": (round(est_usd / nlv * 100, 1) if nlv else None),
                    "fill_days": days, "liquidity": liq,
                    "edge": edge, "target_price": ln.get("target_price", "")})
    # ---- LIVE sync (2026-07-03): the staged file goes stale the moment an adjudication lands, so the
    # page now ALSO derives the actionable set from the SAME stores as the alerts page — ledger verdicts
    # (OWNABLE/STARTER) + per-record sizing/entry text — and flags drift in both directions.
    import re as _re
    def _sizing_from_record(t, ledger_conviction=""):
        f = EC_DIR / f"{t}.json"
        if not f.exists():
            return None, None, None, False
        try:
            rec = json.loads(f.read_text())
        except Exception:
            return None, None, None, False
        has_explainer = bool(rec.get("edge_explainer"))
        sizing = rec.get('sizing') or {}
        lo = sizing.get('pct_lo') if isinstance(sizing, dict) else None
        hi = sizing.get('pct_hi') if isinstance(sizing, dict) else None
        from desk.research_contracts import routing_issues
        issues = routing_issues({'verdict': rec.get('verdict_state'), 'state': rec.get('verdict_state')}, rec)
        if issues:
            lo = hi = None
        return lo, hi, str(rec.get("entry_band") or "")[:120], has_explainer
    plan_tickers = {o["ticker"] for o in plan.get("orders", [])}
    live_rows, drift, pending_review = [], [], []
    try:
        led_names = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", [])
    except Exception:
        led_names = []
    nlv_eff = nlv or 1_000_000
    for n in led_names:
        v = (n.get("verdict") or "").upper()
        if v not in ("OWNABLE", "STARTER"):
            continue
        t = n["ticker"]
        lo, hi, band, has_exp = _sizing_from_record(t, n.get("conviction") or "")
        if not has_exp:
            continue          # pipeline-complete only — same membership rule as the READY bucket
        row = {"ticker": t, "verdict": v, "approved": t in approved, "sizing_pct_lo": lo, "sizing_pct_hi": hi,
               "est_usd_lo": (round(lo / 100 * nlv_eff) if lo else None),
               "est_usd_hi": (round(hi / 100 * nlv_eff) if hi else None),
               "entry_band": band, "alert_below": n.get("alert_below"),
               "plan_snippet": (n.get("conviction") or "")[:150],
               "in_staged_plan": t in plan_tickers,
               "needs_sizing": lo is None}
        from desk.research_contracts import routing_issues
        record = json.loads((EC_DIR / f'{t}.json').read_text(encoding='utf-8'))
        issues = routing_issues(n, record)
        if issues:
            row['review_issues'] = issues
            pending_review.append(row)
            drift.append(f"{t}: excluded from ready deployment — " + '; '.join(issues))
            continue
        live_rows.append(row)
        if t not in plan_tickers:
            drift.append(f"{t}: approved ({v}) but NOT in the staged entry plan")
    led_v = {n["ticker"]: (n.get("verdict") or "").upper() for n in led_names}
    for o in plan.get("orders", []):
        pv = led_v.get(o["ticker"])
        if pv and pv not in ("OWNABLE", "STARTER", "HELD", "OWN"):
            drift.append(f"{o['ticker']}: staged in the plan but ledger verdict is now {pv} — stale order")
    live_rows.sort(key=lambda r: -(r["sizing_pct_hi"] or 0))
    return {"asof": plan.get("asof"), "note": plan.get("note"), "target_nlv": nlv,
            "deployable_cash": cash, "current_nlv": plan.get("current_nlv"),
            "orders": out, "count": len(out), "approved_count": len(approved),
            "total_est_usd": round(tot_cost), "approved_est_usd": round(tot_appr),
            "approved_over_cash": (bool(cash) and tot_appr > cash),
            "total_weight_pct": (round(tot_cost / nlv * 100, 1) if nlv else None),
            "live": live_rows, "pending_review": pending_review, "drift": drift}


def _our_tickers() -> set:
    """Every US ticker we own / intend to own / harvest in IBKR — for the Parametric wash-sale overlap."""
    ours = set()
    pc = Path(__file__).resolve().parent / "data" / "positions_cache.json"
    if pc.exists():
        try:
            for x in json.loads(pc.read_text()).get("positions", []):
                ours.add(x["symbol"].split()[0].upper())
        except Exception:
            pass
    try:
        from desk.book_universe import BOOK
        ours |= {t.upper() for t in BOOK}
    except Exception:
        pass
    # Parametric is a US-equity SMA — only US-listed tickers (no exchange suffix) can collide. Do NOT strip a
    # foreign suffix (DG.PA Vinci != DG Dollar General; CFR.SW Richemont != CFR Cullen/Frost; BC.MI != BC Brunswick).
    try:
        for n in json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", []):
            t = n["ticker"].upper()
            if "." not in t:
                ours.add(t)
    except Exception:
        pass
    try:
        for o in json.loads(ENTRY_PLAN.read_text()).get("orders", []):
            t = o["ticker"].upper()
            if "." not in t:
                ours.add(t)
    except Exception:
        pass
    return ours


def parametric() -> dict:
    """Read-only view of the Parametric direct-indexing SMA positions (from the local msprime extract DB),
    so the Desk KNOWS them — and flags any name that overlaps our IBKR book (cross-account §1091 wash-sale risk).
    'Regular' = reflects whatever the msprime app last ingested; we read the latest reporting_date each load."""
    import sqlite3
    db = os.environ.get("MSPRIME_DB", "/Users/ajay/msprime/app/data/msprime.db")
    if not Path(db).exists():
        return {"error": f"Parametric DB not found at {db} — the msprime app populates it from the daily Global Positions extract.",
                "positions": [], "count": 0}
    ours = _our_tickers()
    con = sqlite3.connect(db)
    try:
        d = con.execute("SELECT MAX(reporting_date) FROM positions").fetchone()[0]
        rows = con.execute(
            "SELECT symbol, security_description, current_quantity, long_short_code, price_usd, market_value_usd, asset_class "
            "FROM positions WHERE reporting_date=? AND symbol!='USD' AND product_type!='CASH' ORDER BY ABS(market_value_usd) DESC",
            (d,)).fetchall()
    finally:
        con.close()
    out, gross, net, nL, nS, overlaps = [], 0.0, 0.0, 0, 0, []
    for sym, desc, qty, side, px, mv, ac in rows:
        base = (sym or "").split(".")[0].upper()
        is_ov = base in ours
        mv = mv or 0.0
        gross += abs(mv); net += mv
        if (side or "") == "S" or qty < 0:
            nS += 1
        else:
            nL += 1
        rec = {"symbol": sym, "desc": desc, "qty": qty, "side": side, "px": px,
               "mv": round(mv), "asset_class": ac, "overlap": is_ov}
        if is_ov:
            overlaps.append(rec)
        out.append(rec)
    return {"reporting_date": d, "count": len(out), "n_long": nL, "n_short": nS,
            "gross_mv": round(gross), "net_mv": round(net), "overlap_count": len(overlaps),
            "overlaps": overlaps, "positions": out}


def factor_drift() -> dict:
    """Cached FF5 factor-drift-from-harvesting across IBKR / Parametric / Combined (written by
    desk.factor_drift --cache; recomputed on demand via the tab since loadings need network)."""
    f = Path(__file__).resolve().parent / "data" / "factor_drift.json"
    if not f.exists():
        return {"error": "no factor-drift run yet — hit Recompute on the tab.", "books": {}}
    try:
        return json.loads(f.read_text())
    except Exception as e:
        return {"error": f"factor_drift cache unreadable: {e}", "books": {}}


def catalyst_value() -> dict:
    """Prob-weighted FV vs MARKET-IMPLIED probability for catalyst names — the anti-optimism integration:
    a catalyst we like only earns 'UNDERPRICED' when OUR P(bull) diverges from what the price already pays for."""
    import importlib
    from desk.prob_weighted_fv import compute_one
    fvmap = {}
    for mp in ("verticals.deep_value.krx_value_watch", "verticals.deep_value.smallcap_value_watch"):
        try:
            B = getattr(importlib.import_module(mp), "BASKET")
            for t, c in B.items():
                fv = c.get("fv")
                if fv and len(fv) == 3:
                    fvmap[t] = {"bear": fv[0], "base": fv[1], "bull": fv[2], "yf": c.get("yf") or t}
        except Exception:
            pass
    splits = {}
    p = ROOT / "desk" / "data" / "catalyst_scenarios.json"
    if p.exists():
        try:
            splits = {k: v for k, v in json.loads(p.read_text()).items() if not k.startswith("_")}
        except Exception:
            pass
    # KRX override (authoritative live IBKR snapshot) takes precedence over stale yfinance
    krx_ov = {}
    ovf = Path(__file__).resolve().parent / "data" / "krx_px_override.json"
    if ovf.exists():
        try:
            krx_ov = {k: v.get("px") for k, v in json.loads(ovf.read_text()).get("prices", {}).items()}
        except Exception:
            pass
    names = sorted(set(fvmap) | set(splits))
    yfs = {t: (splits.get(t, {}).get("yf") or fvmap.get(t, {}).get("yf") or t) for t in names}
    live = _live_prices([v for v in yfs.values() if v])
    cat_p = _catalyst_predictions()
    out = []
    for t in names:
        fv, sp = fvmap.get(t, {}), splits.get(t, {})
        bear, base, bull = sp.get("bear", fv.get("bear")), sp.get("base", fv.get("base")), sp.get("bull", fv.get("bull"))
        if None in (bear, base, bull):
            continue
        px = krx_ov.get(t) or live.get(yfs[t])
        if px is None:
            continue
        r = compute_one(px, bear, base, bull, sp.get("p_bull"), sp.get("p_base"))
        cp = cat_p.get(t) or cat_p.get(t + ".L") or {}
        r.update({"ticker": t, "note": sp.get("note", ""), "p_favorable": cp.get("p_favorable"),
                  "catalyst_dir": cp.get("direction")})
        out.append(r)
    out.sort(key=lambda x: (x["edge_pp"] is None, -(x["edge_pp"] if x["edge_pp"] is not None else -999)))
    return {"count": len(out), "graded": sum(1 for x in out if x["edge_pp"] is not None), "names": out}


def antibook_perf() -> dict:
    """Cached anti-book CALL performance (written by desk.antibook_performance): does our non-owned
    watch/catalyst thesis-picking work — hit-rate + signed return + vs SPY from a baseline."""
    p = ROOT / "desk" / "data" / "antibook_perf.json"
    if not p.exists():
        return {"asof": None, "agg": {}, "rows": []}
    try:
        d = json.loads(p.read_text())
        return {"asof": d.get("asof"), "agg": d.get("last_agg", {}), "rows": d.get("last_rows", [])}
    except Exception as e:
        return {"error": str(e), "agg": {}, "rows": []}


CATMIS = ROOT / "desk" / "data" / "CATALYST_MISPRICING.json"


def _numf(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        m = re.search(r"-?\d[\d,]*\.?\d*", x.replace(",", ""))
        return float(m.group()) if m else None
    return None


def _catpred() -> dict:
    try:
        return json.loads((ROOT / "desk" / "data" / "catalyst_predictions.json").read_text()).get("predictions", {})
    except Exception:
        return {}


EC_DIR = ROOT / "desk" / "data" / "edge_classifications"

# public-data sources we log per name — keyword in the ticker's edge_classification -> human label
_SOURCE_LABELS = {
    "ias-24": "audited IAS-24 related-party note", "eurobond": "sovereign USD eurobond spread",
    "ofac": "OFAC sanctions screen", "bafin": "BaFin Directors' Dealings (insider)",
    "s&p global": "S&P Global Mobility production", "peer_readacross": "tier-1 peer earnings read-across",
    "deutsche": "Deutsche Börse index rules", "usaspending": "USASpending federal award-flow",
    "courtlistener": "federal court dockets", "openfda": "openFDA label / whale-ID", "census": "Census trade flow",
    "customs": "customs bill-of-lading", "emma": "EMMA muni disclosure", "edgar": "SEC EDGAR filings",
    "dart": "DART (Korea) filings", "audited": "audited financial statements",
    "nbk": "Nat'l Bank of Kazakhstan rate/FX", "satellite": "satellite alt-data",
    "hiring": "job-posting hiring velocity", "ibkr": "IBKR live market/positions",
    "leading_indicators": "catalyst leading-indicator set", "sec ": "SEC filings",
    "form 4": "SEC Form 4 (insider transactions)", "10-q": "10-Q quarterly filing", "10-k": "10-K annual filing",
    "8-k": "8-K current report", "transcript": "earnings-call transcript", "rns": "LSE RNS statement",
    "verified_primary": "primary-filing verification set", "street": "sell-side consensus/targets",
    "ev/arr": "ARR/EV comps", "covenant": "credit-agreement/covenant terms",
}
# how to GET MORE evidence, keyed on catalyst/thesis language. Prefer connectors we ALREADY own.
_THEORIES = [
    (("federal", "gov contract", "book-to-bill", "backlog", "defense", "civil", "contract award"),
     "Run the usaspending connector (we own it) — federal award-flow IS the gov book-to-bill tell (censor by Last-Modified-Date)."),
    (("launch", "collection", "gucci", "brand", "demna", "creative director", "consumer"),
     "Run social/beauty-virality + web-search attention on the launch reception; customs bill-of-lading for import volume; card/foot-traffic alt-data."),
    (("cpt", "panel", "fda", "approval", "code", "advisory", "committee", "hypoglossal"),
     "Pull the advisory-panel roster + a precedent base-rate of similar decisions; public comment letters; the options-implied move at the date."),
    (("earnings", "print", "quarter", "margin", "revenue", "guidance", "organic", "comparable"),
     "Peer read-across (competitors that report first) + options-implied move + insider transactions (Form 4 / BaFin)."),
    (("order", "production", "capacity", "plant", "ramp"),
     "hiring_velocity at the site (we own it) + satellite buildout + peer order-intake read-across."),
    (("customer", "concentration", "undisclosed"),
     "customs bill-of-lading shipper-alias to ID the undisclosed customer (we own the customer_id detector)."),
    (("refi", "balloon", "maturity", "covenant", "term loan"),
     "Pull the credit agreement / indenture from EDGAR for covenant + maturity terms; track any 8-K refi/amendment."),
]
_GENERIC_THEORY = "Baseline add-ons: insider transactions (Form 4 / BaFin), the options-implied move at the catalyst date, and a peer/precedent base-rate."


def _evidence(ticker, feats):
    """What we ACTUALLY scraped for this name: public-data sources (from its edge_classification) + detectors it
    attracts (feature_universe). Returns {sources, detectors, strength, n}. Never used to down-weight — only to
    surface the trail and, when THIN, flag for review with theories to get more."""
    sources, f = [], EC_DIR / (ticker + ".json")
    if f.exists():
        try:
            s, seen = f.read_text().lower(), set()
            for k, lab in _SOURCE_LABELS.items():
                if k in s and lab not in seen:
                    sources.append(lab); seen.add(lab)
        except Exception:
            pass
    dets = feats.get(ticker, []) if isinstance(feats, dict) else []
    n = len(sources) + len(dets)
    return {"sources": sources, "detectors": dets, "n": n,
            "strength": "rich" if n >= 4 else "moderate" if n >= 2 else "THIN"}


def _frozen_calls(ticker):
    """All calibration-ledger calls for a ticker (OPEN first, newest cat_date first) — the
    catalysts+predictions join the dossier/alert cards render alongside the edge explainer."""
    calls = []
    try:
        base = ticker.split(".")[0]
        for l in (ROOT / "desk" / "data" / "calibration_ledger.jsonl").read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("ticker") in (ticker, base):
                calls.append({"cat_date": r.get("cat_date"), "p": r.get("our_p"),
                              "market_p": r.get("market_p"), "direction": (r.get("direction") or "")[:70],
                              "catalyst": (r.get("catalyst") or "")[:140],
                              "reasoning": (r.get("reasoning") or "")[:400],
                              "plain": r.get("plain"),
                              "status": r.get("status"), "resolution": r.get("resolution"),
                              "made": r.get("made"), "px_at_pred": r.get("px_at_pred")})
    except Exception:
        pass
    calls.sort(key=lambda c: (c["status"] != "OPEN", c["cat_date"] or ""))
    return calls


def _explainer_for(ticker):
    """The plain-language edge explainer from the name's edge_classification record (why we think we have
    edge / why it might be priced in / what resolves it) — the user-facing thesis clarity block."""
    for cand in (ticker, ticker.split(".")[0], ticker + ".L"):
        f = EC_DIR / (cand + ".json")
        if f.exists():
            try:
                return json.loads(f.read_text()).get("edge_explainer")
            except Exception:
                pass
    return None


def _theories(text):
    t, out = (text or "").lower(), []
    for terms, sug in _THEORIES:
        if any(term in t for term in terms):
            out.append(sug)
    out.append(_GENERIC_THEORY)
    return out[:3]


def alerts() -> dict:
    """Go/No-Go on every name in our buy band. Band + edge are INPUTS to one decision, not parallel lists; a
    name where they disagree (in-band per a hand-set level but the live model is rich) is flagged as stale-band.
    Each decision carries the EVIDENCE trail (data scraped + detectors); THIN evidence flags for review with
    theories on how to get more — it never down-weights the call. Separate axes: CHANGED (edge moved) + imminent."""
    catpred = _catpred()
    b, w = _safe(book), _safe(watchlist)
    feats = b.get("feature_universe", {}) if isinstance(b, dict) else {}
    krx_t = {r["ticker"] for r in (b.get("krx") or [])}
    cm = {}
    if CATMIS.exists():
        try:
            cm = json.loads(CATMIS.read_text())
        except Exception:
            cm = {}
    scored = {r["ticker"]: r for r in cm.get("scored", [])}

    cand = {}   # ticker -> band-touch inputs
    for r in (b.get("smallcap") or []) + (b.get("krx") or []):
        if r.get("zone") in ("ENTRY", "DEEP-ADD"):
            cand.setdefault(r["ticker"], {}).update({"px": r.get("px"), "buy": None, "verdict": r.get("verdict"),
                "cur": "KRW" if r["ticker"] in krx_t else "USD", "src": "basket"})
    for sl, names in (w.get("sleeves") or {}).items():
        for n in names:
            ab, px = _numf(n.get("alert_below")), n.get("px")
            if ab and px and px <= ab * 1.01:
                try:
                    from desk.prices import REGISTRY as _PR
                    _cur = (_PR.get(n["ticker"]) or {}).get("ccy", "USD")
                except Exception:
                    _cur = "USD"
                cand.setdefault(n["ticker"], {}).update({"px": px, "buy": ab, "verdict": n.get("verdict"),
                    "cur": _cur, "src": "ledger:" + sl, "thesis": n.get("thesis")})
    for t, r in scored.items():
        if r.get("in_band") and str(r.get("fire", "")).startswith("ENTRY"):
            try:
                from desk.prices import REGISTRY as _PR2
                _cur2 = (_PR2.get(t) or {}).get("ccy", "USD")
            except Exception:
                _cur2 = "USD"
            cand.setdefault(t, {}).update({"px": r.get("px"), "buy": r.get("buy_below"), "cur": _cur2, "src": "catalyst"})
    for t, c in cand.items():
        r = scored.get(t)
        if r:
            c["edge_pp"], c["upside"] = r.get("edge_pp"), r.get("upside_pct")
            c["buy"] = c.get("buy") or r.get("buy_below")

    # the LEDGER verdict is authoritative for every candidate — scanner-sourced candidates carry no verdict,
    # which let HELD (HSBK) and WAIT-gated (MMS) names leak into "go" via the catalyst path
    try:
        led_v = {n["ticker"]: (n.get("verdict") or "") for n in
                 json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", [])}
    except Exception:
        led_v = {}
    go, no_go, in_book = [], [], []
    for t, c in sorted(cand.items(), key=lambda kv: (kv[1].get("cur") != "USD", kv[0])):
        v = (led_v.get(t) or c.get("verdict") or "").upper()
        p = catpred.get(t, {})
        pf, d = p.get("p_favorable"), (p.get("direction") or "").upper()
        edge = c.get("edge_pp")
        from desk.verdicts import HELDISH
        _tok = v.split()[0] if v else ""
        if _tok in HELDISH:    # structured routing group (desk.verdicts) — never substring-match verdict text
            # already in the book: an entry alert has served its purpose — route to monitoring, never "go"
            in_book.append({"ticker": t, "px": c.get("px"), "cur": c.get("cur"),
                            "catalyst": (scored.get(t, {}).get("catalyst") or p.get("prediction") or "")[:110],
                            "p_favorable": pf, "note": "held — monitoring tripwires/catalyst; adds only per DD ladder"})
            continue
        block = None
        if any(k in v for k in ("AVOID", "SHORT", "PASS", "SELL", "TRAP", "RICH")):
            block = f"verdict {c.get('verdict')}"
        elif "WAIT" in v:   # enter-AFTER-catalyst discipline (rebuttal gate: FOUR/S) — in-band != buy yet
            block = "gated — enter AFTER the catalyst confirms (see DD/rebuttal)"
        elif d in ("BEARISH", "SHORT"):
            block = f"catalyst {d.lower()}"
        elif pf is not None and pf < 0.4:
            block = f"SignalOS predicts MISS (p_favorable {pf:.0%})"
        elif edge is not None and edge < 0:
            block = f"model rich (edge {edge:+d}pp) — hand-set band looks stale"
        # FRESHNESS GATE (AMV0 lesson 2026-07-03: a GO fired on a stale price while the stock left the band):
        # a GO must be backed by a price we can date; basket/scanner rows carry their own asof, ledger rows
        # use the live-price cache age. Stale or undatable -> no_go with an explicit STALE reason.
        if not block:
            src = c.get("src") or ""
            if src.startswith("ledger"):
                _yfs = next((n.get("yf") for n in json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", []) if n["ticker"] == t), None)
                _age = _price_age_s(_yfs) if _yfs else None
                if _age is None or _age > 1200:
                    block = f"STALE PRICE ({'unknown age' if _age is None else str(int(_age//60))+'m old'}) — refresh before acting"
        cat_txt = (scored.get(t, {}).get("catalyst") or p.get("prediction") or c.get("thesis") or "")
        ev = _evidence(t, feats)
        rec = {"ticker": t, "px": c.get("px"), "buy": c.get("buy"), "edge_pp": edge, "upside": c.get("upside"),
               "cur": c.get("cur"), "src": c.get("src"), "disagree": (edge is not None and edge < 0),
               "catalyst": (cat_txt or "")[:110], "evidence": ev, "needs_review": ev["strength"] == "THIN",
               "edge_explainer": _explainer_for(t), "frozen_calls": _frozen_calls(t),
               "theories": _theories(cat_txt) if ev["strength"] == "THIN" else []}
        try:
            tf = json.loads((ROOT / "desk" / "data" / "tax_fit.json").read_text()).get("names", {}).get(t)
        except Exception:
            tf = None
        if tf:
            rec["tax_fit"] = tf
        (no_go if block else go).append({**rec, "reason": block} if block else rec)

    # READY: approved starters (OWNABLE/STARTER verdicts) not otherwise surfaced — a DD-approved
    # at-market plan is decision-relevant NOW, not only when a dip-alert trips (8750.T/IVN lesson 2026-07-02)
    surfaced = {r["ticker"] for r in go + no_go + in_book}
    ready = []
    try:
        led_names = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", [])
        yf_syms = {n["ticker"]: (n.get("yf") or "") for n in led_names}
        live = _live_prices([v for k, v in yf_syms.items()
                             if v and (led_v.get(k) or "").upper() in ("OWNABLE", "STARTER") and k not in surfaced])
        for n in led_names:
            t = n["ticker"]
            if t in surfaced or (n.get("verdict") or "").upper() not in ("OWNABLE", "STARTER"):
                continue
            from desk.research_contracts import routing_issues
            try:
                candidate = json.loads((EC_DIR / f'{t}.json').read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            if routing_issues(n, candidate):
                continue
            _ex = _explainer_for(t)
            if not _ex:
                continue          # READY = pipeline-complete only (explainer is the membership card);
                                  # legacy watchlist STARTERs stay on the watchlist tab
            try:
                tf = json.loads((ROOT / "desk" / "data" / "tax_fit.json").read_text()).get("names", {}).get(t)
            except Exception:
                tf = None
            if tf:
                import math as _m2
                if any(isinstance(v, float) and (_m2.isnan(v) or _m2.isinf(v)) for v in tf.values()):
                    tf = None
            _px = live.get(n.get("yf") or "")
            if _px is not None:
                import math as _m
                _px = None if (_m.isnan(_px) or _m.isinf(_px)) else _px
            ready.append({"ticker": t, "px": _px, "alert_below": n.get("alert_below"),
                          "plan": (n.get("conviction") or "")[:170], "tax_fit": tf,
                          "edge_explainer": _ex, "frozen_calls": _frozen_calls(t)})
    except Exception:
        pass
    ready.sort(key=lambda r: -(((r.get("tax_fit") or {}).get("tax_option_pct")) or 0))
    # rank GO by this-year fit (tax-option + dated catalyst), carry names visible but sorted down
    go.sort(key=lambda r: -( (r.get("tax_fit") or {}).get("tax_option_pct") or 0
                             + (2.0 if (r.get("tax_fit") or {}).get("dated_catalyst") else 0)))
    edge_moves, imminent = [], []
    for t, r in scored.items():
        dl, dc = r.get("edge_delta"), r.get("days_to_cat")
        if dl is not None and abs(dl) >= 8:
            edge_moves.append({"ticker": t, "edge_pp": r.get("edge_pp"), "edge_delta": dl,
                               "fire": r.get("fire"), "catalyst": r.get("catalyst")})
        if dc is not None and 0 <= dc <= 14:
            imminent.append({"ticker": t, "days": dc, "cat_date": r.get("cat_date"),
                             "catalyst": r.get("catalyst"), "edge_pp": r.get("edge_pp")})
    edge_moves.sort(key=lambda x: -abs(x["edge_delta"]))
    imminent.sort(key=lambda x: x["days"])
    review = [r["ticker"] for r in go + no_go if r["needs_review"]]
    return {"asof": cm.get("asof"), "cm_asof": cm.get("asof"), "go": go, "no_go": no_go, "in_book": in_book, "ready": ready,
            "edge_moves": edge_moves, "imminent": imminent, "review_needed": review,
            "counts": {"go": len(go), "no_go": len(no_go), "in_book": len(in_book), "edge": len(edge_moves),
                       "imminent": len(imminent), "review": len(review), "total": len(go)}}


def methodology() -> dict:
    f = ROOT / "desk" / "data" / "CATALYST_METHODOLOGY.md"
    return {"text": f.read_text() if f.exists() else ""}




def generators() -> dict:
    """Stage-0b inverted-generation harvests: each scanner's latest output file, summarized for the tab.
    The scanners PROPOSE (seeds); the pipeline disposes (trap-screen -> DD -> sizing)."""
    G = ROOT / "verticals" / "generators" / "data"
    DV = ROOT / "verticals" / "deep_value" / "data"
    def _j(p):
        try:
            return json.loads(p.read_text()) if p.exists() else None
        except Exception:
            return None
    imp, exp = _j(DV / "IMPORT_ANOMALIES.json"), _j(DV / "EXPORT_ANOMALIES.json")
    seeds = _j(DV / "IMPORT_THESIS_SEEDS.json")
    award, insider = _j(G / "AWARD_FLOW_ANOMALIES.json"), _j(G / "INSIDER_CLUSTERS.json")
    lit, dis = _j(G / "NEW_LITIGATION.json"), _j(G / "DISTRESS_8K.json")
    return {
        "doctrine": "Scanners propose; the pipeline disposes. No informational edge claimed on public data — these allocate diligence attention. Lesson from harvest #1: famous categories are consensus; the bite is in obscure corners.",
        "imports": imp and {"asof": imp.get("asof"), "window": imp.get("window"), "n": imp.get("n_categories"),
                            "accelerating": imp.get("accelerating", [])[:8], "decelerating": imp.get("decelerating", [])[:6]},
        "exports": exp and {"asof": exp.get("asof"), "window": exp.get("window"), "n": exp.get("n_categories"),
                            "accelerating": exp.get("accelerating", [])[:8], "decelerating": exp.get("decelerating", [])[:6]},
        "import_seeds": seeds and {"asof": seeds.get("asof"), "seeds": seeds.get("seeds", []),
                                   "outcomes": seeds.get("stage1_outcomes", {})},
        "award_flow": award and {"asof": award.get("asof"), "window": award.get("window"), "note": award.get("note"),
                                 "accelerating": award.get("accelerating", [])[:10], "decelerating": award.get("decelerating", [])[:6],
                                 "new_entrants": award.get("new_entrants_50m", [])[:5]},
        "insider_clusters": insider and {"asof": insider.get("asof"), "n_buys": insider.get("n_single_buys"),
                                         "clusters": insider.get("clusters", [])[:12]},
        "litigation": lit and {"asof": lit.get("asof"), "since": lit.get("since"), "n": lit.get("n_material_suits"),
                               "suits": lit.get("suits", [])[:12]},
        "distress": dis and {"asof": dis.get("asof"), "since": dis.get("since"), "n": dis.get("n_hits"),
                             "by_tell": {k: v[:8] for k, v in (dis.get("by_tell") or {}).items()}},
        "plumes": (_j(G / "PLUME_CLUSTERS.json") or None) and {**{k: v for k, v in _j(G / "PLUME_CLUSTERS.json").items() if k != "clusters"}, "clusters": _j(G / "PLUME_CLUSTERS.json").get("clusters", [])[:10]},
        "attention": _j(G / "ATTENTION_ANOMALIES.json"),
        "hiring_waves": _j(G / "HIRING_WAVES.json"),
        "warn": _j(G / "WARN_LAYOFFS.json"),
        "fda_velocity": _j(G / "FDA_VELOCITY.json"),
        "nih_grants": _j(G / "NIH_GRANT_FLOW.json"),
    }


def predictions_calendar():
    """Chronological view of every prediction on record — the primary way to read the book's
    upcoming resolution schedule (per-ticker cards remain as dossier context)."""
    import datetime as _dt
    today = _dt.date.today().isoformat()
    events = []
    try:
        for l in (ROOT / "desk" / "data" / "calibration_ledger.jsonl").read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            d = r.get("cat_date") or ""
            days = None
            try:
                days = (_dt.date.fromisoformat(d) - _dt.date.today()).days
            except Exception:
                pass
            res = r.get("resolution")
            if isinstance(res, dict):           # resolve-tool format: {'date':..., 'outcome': 'FAVORABLE'}
                res = res.get("outcome")
            events.append({"date": d, "days_away": days, "ticker": r.get("ticker"),
                           "p": r.get("our_p"), "market_p": r.get("market_p"),
                           "refined_p": r.get("refined_p"), "event_type": r.get("event_type"),
                           "market_p_current": r.get("market_p_current"),
                           "market_p_source": r.get("market_p_source"),
                           "market_p_mismatch": r.get("market_p_mismatch"),
                           "status": r.get("status"), "resolution": res,
                           "gate_excluded": bool(r.get("sizing_gate_excluded")),
                           "catalyst": (r.get("catalyst") or "")[:140], "plain": r.get("plain"),
                           "px_at_pred": r.get("px_at_pred"), "made": r.get("made")})
    except Exception:
        pass
    # merge dated CATALYSTS that carry no frozen prediction (curated store + catalyst_watch entries)
    have = {(e["ticker"], e["date"]) for e in events}
    try:
        cal = json.loads((ROOT / "desk" / "data" / "catalyst_calendar.json").read_text())
        for c in cal.get("dated", []):
            if c["date"] >= today and not any(t == c["ticker"] and abs((_dt.date.fromisoformat(d) - _dt.date.fromisoformat(c["date"])).days) <= 3 for t, d in have if d):
                events.append({"date": c["date"], "days_away": (_dt.date.fromisoformat(c["date"]) - _dt.date.today()).days,
                               "ticker": c["ticker"], "p": None, "market_p": None, "status": "OPEN", "resolution": None,
                               "kind": "catalyst_watch", "catalyst": c["event"],
                               "plain": {"what": c["event"], "how": c.get("why_no_number") or "", "conclusion": c.get("action") or ""}})
        undated = cal.get("undated_live", [])
    except Exception:
        undated = []
    try:
        from desk.catalyst_watch import CATALYSTS as _CW
        for c in _CW:
            d = c.get("date")
            if d and d >= today and (c["ticker"], d) not in have and not any(t == c["ticker"] and dd and abs((_dt.date.fromisoformat(dd) - _dt.date.fromisoformat(d)).days) <= 3 for t, dd in have):
                events.append({"date": d, "days_away": (_dt.date.fromisoformat(d) - _dt.date.today()).days,
                               "ticker": c["ticker"], "p": c.get("p_favorable"), "market_p": None, "status": "OPEN",
                               "resolution": None, "kind": "catalyst_watch", "catalyst": c.get("catalyst"),
                               "plain": {"what": f"{c.get('catalyst','')} — {c.get('thesis','')}"[:220], "how": "", "conclusion": (c.get("watch") or "")[:220]}})
    except Exception:
        pass
    # attach resolution-pack readiness (goal #107)
    try:
        packs = json.loads((ROOT / "desk" / "data" / "resolution_packs.json").read_text()).get("packs", {})
        pk = {}
        for key, v in packs.items():
            t, d = key.split("|")
            pk[(t, d)] = v
        for e in events:
            if e.get("market_p_current") is not None:
                e["crowd"] = {"p": e["market_p_current"],
                              "src": (e.get("market_p_source") or "")[:120],
                              "related": bool(e.get("market_p_mismatch"))}
            hit = pk.get((e["ticker"], e["date"])) or pk.get((e["ticker"].split(".")[0], e["date"]))
            if hit:
                e["pack"] = {"ready": True, "adjudication": hit.get("adjudication", "")[:200],
                             "branches": {k: v[:160] for k, v in (hit.get("branches") or {}).items()},
                             "urgency": hit.get("urgency")}
            elif e["status"] == "OPEN":
                e["pack"] = {"ready": False}
    except Exception:
        pass
    upcoming = sorted([e for e in events if e["status"] == "OPEN" and e["date"] >= today], key=lambda e: e["date"])
    stale_open = sorted([e for e in events if e["status"] == "OPEN" and e["date"] < today], key=lambda e: e["date"])
    resolved = sorted([e for e in events if e["status"] != "OPEN"], key=lambda e: -(ord((e["date"] or " ")[0])) if False else e["date"], reverse=True)
    # RIGHT/WRONG = directional correctness of OUR frozen p vs the outcome (a 0.45 call resolving
    # UNFAVORABLE is a HIT), counted over status==RESOLVED only (VOIDED/EXCLUDED never grade) and
    # skipping sizing_gate_excluded rows + MIXED outcomes. Resolution vocab normalized upstream —
    # the ledger carries True/'HIT'/'FAVORABLE' and False/'MISS'/'UNFAVORABLE' from different writers.
    hits = misses = mixed = 0
    for e in resolved:
        if e.get("status") != "RESOLVED" or e.get("gate_excluded") or e.get("p") is None:
            continue
        o = e.get("resolution")
        fav = 1 if o in (True, "HIT", "FAVORABLE") else 0 if o in (False, "MISS", "UNFAVORABLE") else None
        if fav is None:
            mixed += 1
            continue
        if (e["p"] >= 0.5) == (fav == 1):
            hits += 1
        else:
            misses += 1
    return {"asof": today, "n_open": len(upcoming) + len(stale_open),
            "record": {"hits": hits, "misses": misses, "mixed": mixed, "resolved": len(resolved)},
            "next_event": upcoming[0] if upcoming else None,
            "upcoming": upcoming, "awaiting_resolution": stale_open, "resolved": resolved[:40],
            "undated_live": undated}


def everything() -> dict:
    return {"alerts": _safe(alerts), "methodology": _safe(methodology), "overview": _safe(overview),
            "watches": _safe(watches), "detectors": _safe(detectors),
            "catalysts": _safe(catalysts), "book": _safe(book), "signals": _safe(signals),
            "harvest": _safe(harvest), "research": _safe(research), "positions": _safe(positions),
            "triggers": _safe(triggers), "watchlist": _safe(watchlist), "entry": _safe(entry_candidates),
            "parametric": _safe(parametric), "factor": _safe(factor_drift),
            "catalyst_value": _safe(catalyst_value), "antibook_perf": _safe(antibook_perf), "generators": _safe(generators),
            "predictions_calendar": _safe(predictions_calendar)}


if __name__ == "__main__":
    print(json.dumps(_safe(overview), indent=2))
