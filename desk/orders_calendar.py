"""orders_calendar — build the resting-orders + expiry calendar JSON for the desk UI.

Merges, each run:
  1. LIVE resting orders (desk/ui/data/orders_cache.json — refreshed by the existing sync)
  2. Review/expiry dates from resolution_packs.json (keys TICKER-REVIEW|date / TICKER-CXL|date)
  3. Grading/catalyst packs (keys TICKER|date) for any ticker that has a resting order or
     staged instruction — so prints and pack-grades show on the same calendar
  4. Staged-but-unsubmitted instructions (edge_classifications/*.json staged_instructions* blocks)

Doctrine (2026-08-05 contract amendment): every resting order is catalyst-dated; an order with
no matching review date is a VIOLATION and is surfaced in its own 'undated' bucket, never hidden.

Output: desk/ui/static/orders_calendar.json  (fetchable at /static/orders_calendar.json)
Registry: hourly.
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desk" / "ui" / "static" / "orders_calendar.json"


def norm(sym: str) -> str:
    """Ticker family key: 'TW.' -> 'TW', 'STERV' matches 'STERV.HE', '6804' matches '6804.T'."""
    return re.split(r"[.\s]", sym.strip())[0].upper()




# ---------------- STACKING WATCH (2026-08-05, principal directive) ----------------
# Doctrine: put fills/assignments consume court allocation - when a short put lifts,
# assigns, or a stock rung fills on a ticker carrying BOTH exposures, the sibling
# orders must be re-checked against the court cap (and usually pulled). This watch
# diffs orders+positions each run and raises alerts the calendar page + mailer surface.

STATE_F = ROOT / "desk" / "data" / "orders_calendar_state.json"


def stacking_watch(orders: list, payload: dict) -> None:
    try:
        pc = json.loads((ROOT / "desk/ui/data/positions_cache.json").read_text())
        positions = pc.get("positions", [])
    except Exception:
        positions = []

    def fam(sym):
        return norm(str(sym or ""))

    # current snapshot: per family - stock buy orders, short-put orders, short-put pos, stock pos
    snap = {}
    for o in orders:
        f = fam(o.get("symbol"))
        s = snap.setdefault(f, {"stock_buy_orders": 0, "short_put_orders": 0,
                                "short_put_pos": 0, "stock_qty": 0.0})
        desc = str(o.get("symbol", ""))
        if o.get("action") == "BUY" and o.get("sec_type", "STK") == "STK":
            s["stock_buy_orders"] += 1
        elif o.get("action") == "SELL" and (o.get("right") == "P" or "PUT" in desc.upper()):
            # right (P/C) is authoritative when present; a short CALL order is NOT a put
            # (CAI covered-call misfire, 2026-09-03)
            s["short_put_orders"] += 1
    _blank = {"stock_buy_orders": 0, "short_put_orders": 0, "short_put_pos": 0,
              "short_call_pos": 0, "long_call_pos": 0, "short_opt_unknown": 0, "stock_qty": 0.0}
    for p in positions:
        f = fam(p.get("symbol"))
        s = snap.setdefault(f, dict(_blank))
        for k in _blank:
            s.setdefault(k, _blank[k])
        q = float(p.get("qty") or 0)
        if p.get("sec_type") == "OPT":
            r = p.get("right")
            if q < 0 and r == "P":
                s["short_put_pos"] += int(-q)
            elif q < 0 and r == "C":
                s["short_call_pos"] += int(-q)
            elif q < 0:
                # cache row predates the right field — never guess put; surface it
                s["short_opt_unknown"] += int(-q)
            elif q > 0 and r == "C":
                s["long_call_pos"] += int(q)
        elif p.get("sec_type") == "STK":
            s["stock_qty"] += q

    prev = {}
    if STATE_F.exists():
        try:
            prev = json.loads(STATE_F.read_text()).get("snap", {})
        except Exception:
            prev = {}

    alerts = []
    for f, s in snap.items():
        pv = prev.get(f)
        stacked = (s["short_put_pos"] + s["short_put_orders"]) > 0 and \
                  (s["stock_buy_orders"] > 0 or s["stock_qty"] > 0)
        if pv is None:
            continue
        if s["short_put_pos"] > pv.get("short_put_pos", 0) and stacked:
            alerts.append({"ticker": f, "event": "PUT LIFTED",
                           "action": f"short put position {pv.get('short_put_pos',0)} -> {s['short_put_pos']}: "
                                     f"re-check combined exposure vs the court cap; consider trimming the "
                                     f"{s['stock_buy_orders']} resting stock rung(s)"})
        if s["short_put_pos"] < pv.get("short_put_pos", 0) and s["stock_qty"] > pv.get("stock_qty", 0):
            alerts.append({"ticker": f, "event": "ASSIGNMENT",
                           "action": f"stock {pv.get('stock_qty',0):.0f} -> {s['stock_qty']:.0f} as puts closed: "
                                     f"assignment consumed allocation - PULL the {s['stock_buy_orders']} sibling "
                                     f"stock rung(s) unless the court cap still clears (doctrine default: pull)"})
        if s["stock_buy_orders"] < pv.get("stock_buy_orders", 0) and s["stock_qty"] > pv.get("stock_qty", 0) \
                and (s["short_put_pos"] + s["short_put_orders"]) > 0:
            alerts.append({"ticker": f, "event": "STOCK RUNG FILLED",
                           "action": "rung filled with short-put exposure still open - re-check the cap; "
                                     "consider buying back or letting the put stand per the name's pack"})
        # short CALLS get a coverage check, not a put alert: covered by stock (100/contract)
        # and/or long calls in the same family (spreads)
        if s.get("short_call_pos", 0) > (s["stock_qty"] / 100.0 + s.get("long_call_pos", 0)) + 1e-9:
            alerts.append({"ticker": f, "event": "UNCOVERED SHORT CALL",
                           "action": f"short calls {s['short_call_pos']} exceed stock/100 "
                                     f"({s['stock_qty']:.0f} sh) + long calls {s.get('long_call_pos',0)} — "
                                     f"naked upside exposure; court authority required, re-check now"})
        if s.get("short_opt_unknown", 0) > 0:
            alerts.append({"ticker": f, "event": "SHORT OPTION RIGHT UNKNOWN",
                           "action": "cache row lacks the P/C right — run desk.positions_sync to refresh; "
                                     "no put/call alert can be trusted for this family until it does"})

    payload["stacking_alerts"] = alerts
    payload["stacked_tickers"] = sorted(
        f for f, s in snap.items()
        if (s["short_put_pos"] + s["short_put_orders"]) > 0
        and (s["stock_buy_orders"] > 0 or s["stock_qty"] > 0))
    STATE_F.write_text(json.dumps({"snap": snap, "asof": payload["generated_utc"]}, indent=1))
    if alerts:
        body = "\n".join(f"{a['ticker']}: {a['event']} - {a['action']}" for a in alerts)
        print(f"[orders_calendar] STACKING ALERTS: {len(alerts)}\n{body}")
        try:
            from desk.mailer import send_raw
            send_raw(f"STACKING ALERT: {', '.join(a['ticker'] for a in alerts)} - pull sibling GTCs?", body)
        except Exception as ex:
            print(f"  (mail failed: {ex})")

def main() -> None:
    now = datetime.datetime.utcnow()
    today = now.date()

    oc = json.loads((ROOT / "desk/ui/data/orders_cache.json").read_text())
    orders = oc.get("orders", [])
    packs = json.loads((ROOT / "desk/data/resolution_packs.json").read_text())["packs"]

    # staged instructions from EC files
    staged = []
    ecd = ROOT / "desk/data/edge_classifications"
    for f in ecd.glob("*.json"):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        t = d.get("ticker", f.stem)
        for k, v in d.items():
            if k.startswith("staged_instructions") and isinstance(v, dict):
                ids = v.get("ids")
                if isinstance(ids, dict):
                    for iid, desc in ids.items():
                        staged.append({"ticker": t, "instr": iid, "desc": desc})
                elif isinstance(ids, list):
                    for desc in ids:
                        staged.append({"ticker": t, "instr": str(desc).split(":")[0], "desc": str(desc)})

    # date sources per ticker family
    review_by: dict[str, list] = {}
    events = []
    for key, v in packs.items():
        if "|" not in key:
            continue
        name, d = key.rsplit("|", 1)
        if not re.match(r"\d{4}-\d{2}-\d{2}$", d):
            continue
        dd = datetime.date.fromisoformat(d)
        if dd < today - datetime.timedelta(days=3) or dd > today + datetime.timedelta(days=180):
            continue
        adj = (v.get("adjudication") or "")[:240]
        if name.endswith("-REVIEW") or name.endswith("-CXL"):
            fam = norm(name.replace("-REVIEW", "").replace("-CXL", ""))
            review_by.setdefault(fam, []).append((d, key))
            events.append({"date": d, "type": "review", "ticker": fam, "label": key, "detail": adj})
        else:
            fam = norm(name)
            events.append({"date": d, "type": "grade", "ticker": fam, "label": key, "detail": adj})

    # attach review dates to live orders
    out_orders, undated = [], []
    for o in orders:
        fam = norm(o.get("symbol", ""))
        row = {"symbol": o.get("symbol"), "side": o.get("action"), "qty": o.get("qty"),
               "limit": o.get("limit"), "ccy": o.get("ccy"), "status": o.get("status")}
        dates = sorted(review_by.get(fam, []))
        if dates:
            row["review_by"], row["review_src"] = dates[0]
            out_orders.append(row)
        else:
            undated.append(row)

    for s in staged:
        fam = norm(s["ticker"])
        dates = sorted(review_by.get(fam, []))
        s["review_by"] = dates[0][0] if dates else None

    payload = {
        "generated_utc": now.isoformat(timespec="seconds") + "Z",
        "orders_cache_asof": oc.get("asof"),
        "doctrine": "bands rest by default + every resting order catalyst-dated (2026-08-05). Undated = violation, listed, never hidden.",
        "orders": sorted(out_orders, key=lambda r: r["review_by"]),
        "undated_orders": undated,
        "staged_instructions": staged,
        "events": sorted(events, key=lambda e: e["date"]),
        "counts": {"live_dated": len(out_orders), "live_undated": len(undated),
                   "staged": len(staged), "events_180d": len(events)},
    }

    # exit-band coverage (contract rule 6): held stock positions need a resting SELL or an -EXIT/-TRIM pack
    try:
        pc = json.loads((ROOT / "desk/ui/data/positions_cache.json").read_text())
        pos_rows = [r for r in pc.get("positions", []) if r.get("sec_type") == "STK" and float(r.get("qty") or 0) > 0]
    except Exception:
        pos_rows = []
    sell_fams = {norm(str(o.get("symbol",""))) for o in orders if o.get("action") == "SELL"}
    exit_pack_fams = {norm(k.rsplit("|",1)[0].replace("-EXIT","").replace("-TRIM",""))
                      for k in packs if ("-EXIT|" in k or "-TRIM|" in k)}
    exempt = {"SGOV", "PHYS"}  # cash-ballast class, explicit standing exemption
    # ratified rule-6 exemptions live in the EC exit_band blocks (ALERTS+EXEMPTION class)
    for fjson in (ROOT / "desk/data/edge_classifications").glob("*.json"):
        try:
            d = json.loads(fjson.read_text())
        except Exception:
            continue
        for k, v in d.items():
            if k.startswith("exit_band") and isinstance(v, dict):
                cls = str(v.get("class", "") or v.get("classification", "")).upper()
                if "EXEMPT" in cls or "ALERTS" in cls:
                    exempt.add(norm(d.get("ticker", fjson.stem)))
    payload["exit_undated_positions"] = sorted(
        {norm(str(r.get("symbol",""))) for r in pos_rows}
        - sell_fams - exit_pack_fams - exempt)
    payload["counts"]["exit_undated"] = len(payload["exit_undated_positions"])

    stacking_watch(orders, payload)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"[orders_calendar] {payload['generated_utc']}: {len(out_orders)} dated / "
          f"{len(undated)} UNDATED live orders · {len(staged)} staged instr · {len(events)} events")


if __name__ == "__main__":
    main()
