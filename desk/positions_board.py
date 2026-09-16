"""positions_board — one row per open position with EVERYTHING joined:
prices for every line (live daemon feed for US names, yfinance closes for the rest),
FX->USD so the whole book totals in one currency, court verdict + note, edge
classification (type/action/exit-band), sleeve, resting exit/entry rungs, next dated
event, day change, and rule-6/stacking flags. Short options ride in their own section.

Sources: positions_cache + research_ledger + edge_classifications/ + orders_cache +
resolution_packs + orders_calendar.json. Output: desk/ui/static/positions_board.json
(hourly cron). Live US prices reach the page separately through the mirrored
/static/live_quotes.json (60s client refresh); this board carries the close basis,
prev-close (day %) and FX that the client math needs.
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desk" / "ui" / "static" / "positions_board.json"
EC_DIR = ROOT / "desk" / "data" / "edge_classifications"

# yahoo symbol overrides where the ledger has no (or a non-yahoo) mapping, keyed by fam
YF_OVERRIDES = {"8750": "8750.T", "KALMAR": "KALMAR.HE", "VRLA": "VRLA.PA", "AST": "AST.WA"}
# stale-but-sane fallbacks if the FX fetch fails outright (USD per 1 local unit; GBP = per POUND —
# IBKR reports LSE avg costs in pounds, yahoo .L closes in pence, so GBP rows divide px by 100)
FX_FALLBACK = {"USD": 1.0, "EUR": 1.15, "GBP": 1.35, "JPY": 0.0063, "DKK": 0.154, "PLN": 0.27,
               "KRW": 0.00073, "ILS": 0.30}


def norm(sym: str) -> str:
    return re.split(r"[.\s]", str(sym or "").strip())[0].upper()


def _yf_symbol(fam: str, ccy: str, ledger_yf: str | None) -> str:
    s = YF_OVERRIDES.get(fam) or ledger_yf or fam
    if ccy == "JPY" and not s.endswith(".T"):
        s += ".T"
    return s


def _fetch_closes(yf_syms: list[str], ccys: list[str]) -> tuple[dict, dict]:
    """One batched yahoo call: 7d daily closes for every position symbol + the FX pairs.
    Returns ({yf: {px, prev, asof}}, {ccy: usd_per_unit}). Raises on total failure —
    the caller falls back to the previous board."""
    import yfinance as yf
    fx_pairs = {c: f"{c}USD=X" for c in set(ccys) if c and c != "USD"}
    all_syms = sorted(set(yf_syms) | set(fx_pairs.values()))
    d = yf.download(" ".join(all_syms), period="7d", interval="1d", progress=False, threads=True)["Close"]
    if hasattr(d, "to_frame") and not hasattr(d, "columns"):  # single-symbol Series edge case
        d = d.to_frame(all_syms[0])
    closes = {}
    for s in all_syms:
        try:
            col = d[s].dropna()
        except Exception:
            continue
        if not len(col):
            continue
        closes[s] = {"px": round(float(col.iloc[-1]), 4),
                     "prev": round(float(col.iloc[-2]), 4) if len(col) > 1 else None,
                     "asof": str(col.index[-1].date())}
    fx = dict(FX_FALLBACK)
    for c, pair in fx_pairs.items():
        if pair in closes:
            fx[c] = closes[pair]["px"]
    return closes, fx


def _prev_board() -> dict:
    """Last successful board, keyed by fam — the price/FX fallback when the network is down."""
    try:
        old = json.loads(OUT.read_text())
        return {"rows": {r["fam"]: r for r in old.get("positions", [])}, "fx": old.get("fx") or {}}
    except Exception:
        return {"rows": {}, "fx": {}}


_DEAD_STATUS = re.compile(r"SUSPENDED|WITHDRAWN|PAPER_ONLY|CALENDARED|FILLED")


def _staged_label(o: dict) -> str | None:
    """Lifecycle label for an entry-plan order, or None for rows the board must not show
    (dead states and plain mirrors of orders already resting at the broker)."""
    src = str(o.get("source", "")).lower()
    st = str(o.get("status", "")).upper()
    if _DEAD_STATUS.search(st):
        return None
    if "APPROVED_CANCEL" in st:
        return "CXL-PENDING"          # resting at IBKR but the user approved a cancel in TWS
    if src == "ibkr_working_order":
        return None                   # resting mirror — already on the board as a rung
    if st.startswith("USER_APPROVED"):
        return "APPROVED-UNSUBMITTED"
    if "pending_user_approval" in src:
        return "NEEDS-APPROVAL"
    if "conditional" in src or "CONDITIONAL" in st:
        return "CONDITIONAL"
    return "STAGED"


def _staged_orders(plan: dict, ledger: dict) -> list[dict]:
    out = []
    for o in plan.get("orders", []):
        lab = _staged_label(o)
        if not lab or not (o.get("qty") and o.get("limit")):
            continue
        t = str(o["ticker"])
        f = norm(t)
        ccy = o.get("ccy") or "USD"
        out.append({"ticker": t, "fam": f, "side": o.get("side", "BUY"), "qty": o["qty"],
                    "limit": o["limit"], "ccy": ccy, "tranche": o.get("tranche"),
                    "label": lab, "source": str(o.get("source", ""))[:120],
                    "note": str(o.get("note", ""))[:300],
                    "yf": _yf_symbol(f, ccy, (ledger.get(f) or {}).get("yf"))})
    return out


def _resting_orders(oc: dict, ledger: dict) -> list[dict]:
    """Every order WORKING at the broker (the whole GTC ladder book, held or not).
    NOTE: IBKR LSE order limits are in PENCE — order rows keep the pence convention
    (yahoo .L closes are pence too), unlike position rows where IBKR costs are pounds."""
    out = []
    for o in oc.get("orders", []):
        if not (o.get("qty") and o.get("limit")):
            continue
        t = str(o["symbol"])
        f = norm(t)
        ccy = o.get("ccy") or "USD"
        pre = str(o.get("status", "")).lower() == "presubmitted"
        out.append({"ticker": t, "fam": f, "side": o.get("action", "BUY"), "qty": o["qty"],
                    "limit": o["limit"], "ccy": ccy, "tranche": None,
                    "label": "RESTING", "source": "IBKR GTC" + (" (presubmitted)" if pre else ""),
                    "note": "", "conid": o.get("conid"),
                    "yf": _yf_symbol(f, ccy, (ledger.get(f) or {}).get("yf"))})
    return out


def _reconcile(resting: list[dict], staged: list[dict]) -> tuple[list[dict], list[dict]]:
    """Reconcile the entry plan against the broker book so the same order never lists twice:
    - a CXL-PENDING plan row mirrors an order still resting at IBKR → mark the resting row
      (unmatched CXL rows are already cancelled and drop);
    - a staged plan row whose exact (side, qty, limit) is already resting was PLACED since the
      plan was written → keep the resting row, annotate it with the plan's tranche/source.
    Size/limit mismatches deliberately keep BOTH rows — plan-vs-broker drift should be visible."""
    def _matches(s):
        """All resting rungs at the same price level — an upsized plan rung may have been
        executed as several broker orders (WAL 350@79 = resting 225@79 + 125@79)."""
        return [r for r in resting if r["label"] == "RESTING" and r["fam"] == s["fam"]
                and r["side"] == s["side"] and abs(r["limit"] - s["limit"]) < 1e-6]
    keep_staged = []
    for s in staged:
        ms = _matches(s)
        placed = ms and abs(sum(r["qty"] for r in ms) - s["qty"]) < 0.5
        exact = next((r for r in ms if abs(r["qty"] - s["qty"]) < 0.5), None)
        if s["label"] == "CXL-PENDING":
            if exact:
                exact["label"] = "CXL-PENDING"
                exact["note"] = s["note"]
            continue                       # unmatched CXL = already cancelled — drop
        if placed or exact:
            for r in ([exact] if exact else ms):
                r["tranche"] = s.get("tranche")
                r["note"] = ("placed from plan: " + s["source"]).strip()
        else:
            keep_staged.append(s)
    return resting, keep_staged


def _edge_file(symbol: str, fam: str, yf_sym: str) -> Path | None:
    for cand in (f"{symbol}.json", f"{yf_sym}.json", f"{yf_sym.replace('.', '_')}.json", f"{fam}.json"):
        p = EC_DIR / cand
        if p.exists():
            return p
    return None


def _edge_context(symbol: str, fam: str, yf_sym: str) -> dict:
    """Distilled edge-classification context for the row: type/action/conviction + the freshest
    exit-band call. Files are heterogeneous — every read is defensive."""
    p = _edge_file(symbol, fam, yf_sym)
    if not p:
        return {}
    try:
        d = json.loads(p.read_text())
    except Exception:
        return {}
    out = {}
    exp = d.get("edge_explainer") or {}
    et = exp.get("edge_type") if isinstance(exp, dict) else None
    out["edge_type"] = et or (d.get("classification") if isinstance(d.get("classification"), str) else None)
    if isinstance(d.get("action"), str):
        out["action"] = d["action"][:400]
    if d.get("conviction") is not None:
        out["conviction"] = d.get("conviction")
    out["ec_date"] = d.get("date")
    bands = sorted(k for k in d if k.startswith("exit_band"))
    if bands:
        b = d[bands[-1]]
        if isinstance(b, dict):
            out["exit_band"] = str(b.get("classification") or "")[:120]
            out["exit_band_asof"] = b.get("as_of") or bands[-1].replace("exit_band_", "")
    return {k: v for k, v in out.items() if v}


def main() -> None:
    now = datetime.datetime.utcnow()
    pc = json.loads((ROOT / "desk/ui/data/positions_cache.json").read_text())
    oc = json.loads((ROOT / "desk/ui/data/orders_cache.json").read_text())
    rl = json.loads((ROOT / "desk/data/research_ledger.json").read_text())
    packs = json.loads((ROOT / "desk/data/resolution_packs.json").read_text())["packs"]
    try:
        cal = json.loads((ROOT / "desk/ui/static/orders_calendar.json").read_text())
    except Exception:
        cal = {}

    ledger = {}
    for n in rl.get("names", []):
        if isinstance(n, dict) and n.get("ticker"):
            ledger[norm(n["ticker"])] = n

    orders_by_fam: dict[str, dict] = {}
    for o in oc.get("orders", []):
        f = norm(o.get("symbol"))
        d = orders_by_fam.setdefault(f, {"sells": [], "buys": []})
        row = f"{o.get('qty'):g}@{o.get('limit')}"
        (d["sells"] if o.get("action") == "SELL" else d["buys"]).append(row)

    next_date: dict[str, tuple] = {}
    today = now.date().isoformat()
    for key in packs:
        if "|" not in key:
            continue
        name, d = key.rsplit("|", 1)
        if not re.match(r"\d{4}-\d{2}-\d{2}$", d) or d < today:
            continue
        f = norm(re.sub(r"-(REVIEW|CXL|EXIT|TRIM|OPS|RXN|PM|STK|OPS)$", "", name))
        if f not in next_date or d < next_date[f][0]:
            next_date[f] = (d, key)

    exit_undated = set(cal.get("exit_undated_positions", []))
    stacked = set(cal.get("stacked_tickers", []))

    stocks = [p for p in pc.get("positions", [])
              if p.get("sec_type") == "STK" and float(p.get("qty") or 0) > 0]
    shorts = [p for p in pc.get("positions", [])
              if p.get("sec_type") == "OPT" and float(p.get("qty") or 0) < 0]
    stock_fams = {norm(p["symbol"]) for p in stocks}

    try:
        staged = _staged_orders(json.loads((ROOT / "desk/data/entry_plan.json").read_text()), ledger)
    except Exception:
        staged = []
    resting = _resting_orders(oc, ledger)
    resting, staged = _reconcile(resting, staged)
    orders = resting + staged

    # ---- prices: batched closes + FX for every line (positions AND every order symbol),
    # previous board as the outage fallback ----
    prev = _prev_board()
    yf_of = {}
    for p in stocks:
        f = norm(p["symbol"])
        yf_of[f] = _yf_symbol(f, p.get("ccy") or "USD", (ledger.get(f) or {}).get("yf"))
    price_note = None
    all_yf = list(yf_of.values()) + [s["yf"] for s in orders]
    all_ccy = [p.get("ccy") or "USD" for p in stocks] + [s["ccy"] for s in orders]
    try:
        closes, fx = _fetch_closes(all_yf, all_ccy)
    except Exception as e:
        closes, fx = {}, dict(FX_FALLBACK, **prev["fx"])
        price_note = f"close fetch failed ({type(e).__name__}) — prices reused from the previous board"

    rows = []
    for p in stocks:
        sym = p["symbol"]
        f = norm(sym)
        ccy = p.get("ccy") or "USD"
        led = ledger.get(f, {})
        yf_sym = yf_of[f]
        c = closes.get(yf_sym) or {}
        px, px_prev, px_asof = c.get("px"), c.get("prev"), c.get("asof")
        if px is not None and ccy == "GBP":  # yahoo .L closes are pence; IBKR GBP costs are pounds
            px, px_prev = px / 100, (px_prev / 100 if px_prev else None)
        if px is None:  # network miss on this symbol — reuse the last board's price
            old = prev["rows"].get(f) or {}
            px, px_prev, px_asof = old.get("px_close"), old.get("px_prev"), old.get("px_asof")
        avg = p.get("avg_cost_per_unit") or p.get("avg_cost")
        rate = fx.get(ccy, FX_FALLBACK.get(ccy, 1.0))
        nd = next_date.get(f)
        suspect = bool(px and avg and (px / avg > 8 or px / avg < 0.125))  # unit-convention guard
        rows.append({
            "symbol": sym, "fam": f, "qty": p["qty"], "avg": avg,
            "ccy": ccy, "conid": p.get("conid"), "yf": yf_sym,
            "px_close": px, "px_prev": px_prev, "px_asof": px_asof, "px_suspect": suspect,
            "close_px": px,  # legacy alias
            "fx_usd": rate,
            "mv_usd": round(px * p["qty"] * rate, 2) if px else None,
            "upnl_usd": round((px - avg) * p["qty"] * rate, 2) if (px and avg) else None,
            "day_pct": round((px / px_prev - 1) * 100, 2) if (px and px_prev) else None,
            "sleeve": led.get("sleeve") or None,
            "thesis": (led.get("thesis") or "")[:300] or None,
            "verdict": led.get("verdict", "—"), "court": led.get("court", ""),
            "court_date": led.get("date", ""), "note": (led.get("note") or led.get("conviction") or "")[:600],
            "edge": _edge_context(sym, f, yf_sym),
            "exit_rungs": orders_by_fam.get(f, {}).get("sells", []),
            "entry_rungs": orders_by_fam.get(f, {}).get("buys", []),
            "next_date": nd[0] if nd else None, "next_pack": nd[1] if nd else None,
            "flags": [x for x in [
                "EXIT-UNDATED" if f in exit_undated else None,
                "STACKED" if f in stacked else None,
                "PENDING-DECISION" if "PENDING" in str(led.get("verdict", "")).upper() else None,
                "PX-SUSPECT" if suspect else None,
            ] if x],
        })

    book_mv = sum(r["mv_usd"] for r in rows if r["mv_usd"])
    for r in rows:
        r["weight_pct"] = round(r["mv_usd"] / book_mv * 100, 2) if (r["mv_usd"] and book_mv) else None

    # ---- orders (resting + staged): price, cost in USD, distance from the limit, held-vs-new.
    # Order rows stay in the broker's native units (pence for LSE), so away% compares like-for-like.
    held_fams = {r["fam"] for r in rows}
    for s in orders:
        c = closes.get(s["yf"]) or {}
        px = c.get("px")
        rate = fx.get(s["ccy"], FX_FALLBACK.get(s["ccy"], 1.0))
        # LSE quotes/limits are pence, TASE are agorot (the POLI.TA lesson) — 1/100 of the FX unit
        unit = rate / 100 if s["ccy"] in ("GBP", "ILS") else rate
        s["px_close"] = px
        s["px_asof"] = c.get("asof")
        s["est_usd"] = round(s["qty"] * s["limit"] * unit, 2)
        s["away_pct"] = round((s["limit"] / px - 1) * 100, 1) if px else None
        s["held"] = s["fam"] in held_fams
        del s["yf"]
    staged_by_fam: dict[str, list] = {}
    for s in staged:
        staged_by_fam.setdefault(s["fam"], []).append(s)
    for r in rows:
        sl = staged_by_fam.get(r["fam"], [])
        r["staged_rungs"] = [f"{s['qty']:g}@{s['limit']:g}" for s in sl]
        r["staged_count"] = len(sl)

    opt_rows = [{
        "underlying": norm(o["symbol"]), "symbol": o["symbol"], "qty": o["qty"],
        "premium_usd": round(abs(o["qty"]) * (o.get("avg_cost") or 0), 2),
        "covered": norm(o["symbol"]) in stock_fams, "conid": o.get("conid"),
    } for o in shorts]
    short_prem = round(sum(o["premium_usd"] for o in opt_rows), 2)

    payload = {
        "generated_utc": now.isoformat(timespec="seconds") + "Z",
        "price_note": price_note,
        "fx": fx,
        "positions": sorted(rows, key=lambda r: -(r["mv_usd"] or 0)),
        "short_options": sorted(opt_rows, key=lambda r: r["underlying"]),
        "orders": sorted(orders, key=lambda s: -(s["est_usd"] or 0)),
        "totals": {
            "mv_usd": round(book_mv, 2),
            "cost_usd": round(sum(r["avg"] * r["qty"] * r["fx_usd"] for r in rows if r["avg"]), 2),
            "upnl_usd": round(sum(r["upnl_usd"] for r in rows if r["upnl_usd"] is not None), 2),
            "short_premium_usd": short_prem,
            "staged_usd": round(sum(s["est_usd"] for s in staged if s["label"] != "CXL-PENDING"), 2),
            "resting_buy_usd": round(sum(s["est_usd"] for s in resting if s["side"] == "BUY"), 2),
            "resting_sell_usd": round(sum(s["est_usd"] for s in resting if s["side"] == "SELL"), 2),
            "priced": sum(1 for r in rows if r["px_close"] is not None),
        },
        "counts": {"positions": len(rows),
                   "exit_undated": sum(1 for r in rows if "EXIT-UNDATED" in r["flags"]),
                   "pending": sum(1 for r in rows if "PENDING-DECISION" in r["flags"]),
                   "staged": len(staged), "resting": len(resting)},
    }
    OUT.write_text(json.dumps(payload, indent=1))
    # mirror the daemon's live quotes into static (symlinks are refused by the static server)
    try:
        (ROOT / "desk/ui/static/live_quotes.json").write_text(
            (ROOT / "desk/data/ib_live_quotes.json").read_text())
    except Exception:
        pass
    t = payload["totals"]
    print(f"[positions_board] {payload['generated_utc']}: {len(rows)} positions, "
          f"{t['priced']} priced, MV ${t['mv_usd']:,.0f}, uP&L ${t['upnl_usd']:,.0f} "
          f"({payload['counts']['exit_undated']} exit-undated, {payload['counts']['pending']} pending)"
          + (f" [{price_note}]" if price_note else ""))


if __name__ == "__main__":
    main()
