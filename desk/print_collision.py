"""print_collision — flag resting BUY orders that an EARNINGS GAP could fill.

WHY THIS EXISTS (INTU 2026-08-17). The bands-rest-by-default contract already dates every
resting order against a review pack, and orders_calendar surfaces undated orders as violations.
INTU passed both checks — it HAD a review pack (INTU-REVIEW|2026-08-18) that said "pull 08-18"
— and it still sat 20@312 into a 08-20 FY-end print until a human happened to look. A calendar
reminder is not a tripwire. This module is the tripwire.

THE MECHANISM (feedback_resting_order_into_print, the NATR case): a resting GTC buy with an
un-managed print inside its life is an ACCIDENTAL SHORT-VOL position. It does not fill at
random — it fills PRECISELY on the adverse branch, because only bad news gaps the tape down
through the limit. NATR filled 6h pre-print and went -17.6%. The band and the catalyst date
are ONE artifact: a band derived from a pre-print model is void the moment the guide changes,
so a gap-fill is not "our discount," it is a knife-catch against new information.

WHAT IT COMPUTES. For every resting BUY, the limit's distance below spot measured in units of
the PRINT'S OWN implied move, not in percent:
    event_sigma  = vol_annual * sqrt((sessions_to_print + 1) / 252)
    distance_sig = ln(limit / spot) / event_sigma        (negative = below spot)
A limit sitting within ~2 sigma below spot is inside the gap's reach and gets flagged; INTU
scored -1.0 sigma (312 vs 336.10 with a ~7.2% implied move) = a ~15% chance of filling, and
~100% of that 15% lands on the bad branch.

VOL SOURCE, STATED HONESTLY: 30-session REALIZED vol from yfinance, not implied. Realized
understates a name into its own print (that is exactly when IV is bid), so this check is
CONSERVATIVE BY CONSTRUCTION — it under-flags rather than over-flags, and the printed output
says so. When an IBKR gateway session is available, implied is preferred and labeled.

SEVERITY: print within 3 sessions = CRITICAL (act today); within 10 = WARN (decide at review).
Every flag names the pre-registered remedy: pull the rung, or state a reason to keep it and
re-derive the band POST-print (the "never silent death" branch of the review packs).
"""
from __future__ import annotations

import datetime
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ORDERS = ROOT / "desk" / "ui" / "data" / "orders_cache.json"
CACHE = ROOT / "desk" / "data" / "print_collision_cache.json"
OUT = ROOT / "desk" / "ui" / "static" / "print_collision.json"

NEAR_SESSIONS = 10        # look this far ahead for a print
CRITICAL_SESSIONS = 3     # inside this, a flag is act-today
SIGMA_REACH = 2.0         # limit within this many event-sigma below spot = in the gap's reach
CACHE_TTL_H = 18.0        # earnings dates move rarely; one refresh per session-day is plenty


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _sessions_between(a: datetime.date, b: datetime.date) -> int:
    """Trading sessions from a to b (weekdays; holidays ignored — off by at most one)."""
    if b < a:
        return -1
    n, d = 0, a
    while d < b:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return {}


def _fetch(symbol: str, cache: dict) -> dict | None:
    """{spot, vol_annual, vol_basis, next_print} — cached; None when unresolvable."""
    hit = cache.get(symbol)
    if hit:
        age = (_now() - datetime.datetime.fromisoformat(hit["asof"])).total_seconds() / 3600.0
        if age < CACHE_TTL_H:
            return hit
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        h = t.history(period="3mo", auto_adjust=True)
        if h is None or len(h) < 25:
            return None
        closes = list(h["Close"])
        spot = float(closes[-1])
        rets = [math.log(closes[i] / closes[i - 1]) for i in range(-30, 0) if closes[i - 1] > 0]
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / max(len(rets) - 1, 1)
        vol = math.sqrt(var) * math.sqrt(252)
        nxt = None
        try:                                   # yfinance surfaces this two different ways
            cal = t.calendar
            v = (cal or {}).get("Earnings Date") if isinstance(cal, dict) else None
            if isinstance(v, list) and v:
                nxt = str(v[0])[:10]
            elif v is not None:
                nxt = str(v)[:10]
        except Exception:
            pass
        if not nxt:
            try:
                ed = t.get_earnings_dates(limit=8)
                today = _now().date()
                fut = [d for d in ed.index if d.date() >= today]
                if fut:
                    nxt = str(min(fut).date())
            except Exception:
                pass
        row = {"spot": spot, "vol_annual": vol, "vol_basis": "realized_30d (CONSERVATIVE: "
               "understates a name into its own print)", "next_print": nxt,
               "asof": _now().isoformat(timespec="seconds")}
        cache[symbol] = row
        return row
    except Exception:
        return None


STALE_CACHE_H = 30.0      # one session + slack; beyond this the order book is not evidence


def scan(verbose: bool = True, email: bool = True) -> dict:
    try:
        oc = json.loads(ORDERS.read_text())
        orders = oc.get("orders", [])
    except (OSError, ValueError) as e:
        print(f"[print_collision] cannot read orders cache: {e}")
        return {"flags": [], "error": str(e)}

    # FRESHNESS ASSERTION (2026-08-17, found the day this module was built): orders_cache.json is
    # written by the gateway poller, and the gateway had been refusing connections since 08-12 —
    # so this scan was silently reading a 5-day-old book. A stale cache yielding zero flags reads
    # as "all clear" when it means "no data" (infra-failure-masquerading-as-a-negative-result).
    # Fail LOUD and refuse to report an all-clear we did not earn.
    stale_h = None
    try:
        asof = oc.get("asof")
        ts = (datetime.datetime.fromtimestamp(float(asof), datetime.timezone.utc)
              if isinstance(asof, (int, float))
              else datetime.datetime.fromisoformat(str(asof).replace("Z", "+00:00")))
        stale_h = (_now() - ts).total_seconds() / 3600.0
    except Exception:
        stale_h = None
    if stale_h is None or stale_h > STALE_CACHE_H:
        msg = (f"ORDER CACHE STALE ({stale_h:.0f}h old)" if stale_h is not None
               else "ORDER CACHE ASOF UNREADABLE")
        warn = (f"{msg} — the gateway poller has not refreshed desk/ui/data/orders_cache.json. "
                f"Any order placed or cancelled since then is INVISIBLE to this scan, so a clean "
                f"result here is NOT an all-clear. Restore the gateway feed, then re-run.")
        print(f"[print_collision] *** {warn}")
        if email:
            try:
                from desk.mailer import send_raw
                send_raw("PRINT-COLLISION BLIND: order cache stale, tripwire cannot see the book", warn)
            except Exception:
                pass

    buys, seen = [], set()
    for o in orders:
        if str(o.get("action")).upper() != "BUY":
            continue
        sym, lim = str(o.get("symbol") or ""), o.get("limit")
        if not sym or not isinstance(lim, (int, float)) or lim <= 0:
            continue
        if any(k in sym.upper() for k in (" PUT", " CALL")):    # option legs are a separate class
            continue
        buys.append({"symbol": sym, "limit": float(lim), "qty": o.get("qty"), "ccy": o.get("ccy")})
        seen.add(sym)

    # Our own packs outrank the vendor calendar: a TICKER|date grading pack is a date we
    # adjudicated, while yfinance dates are UNCONFIRMED by construction. Disagreement is
    # itself information (calendar_guard's lesson) and is carried into the flag, never hidden.
    pack_dates: dict[str, str] = {}
    try:
        import re as _re
        packs = json.loads((ROOT / "desk/data/resolution_packs.json").read_text())
        packs = packs.get("packs", packs)
        today0 = _now().date()
        for key in packs:
            if "|" not in key:
                continue
            nm, ds = key.rsplit("|", 1)
            if not _re.match(r"\d{4}-\d{2}-\d{2}$", ds) or nm.endswith(("-REVIEW", "-CXL")):
                continue
            fam = _re.split(r"[.\s]", nm.strip())[0].upper()
            if datetime.date.fromisoformat(ds) >= today0:
                if fam not in pack_dates or ds < pack_dates[fam]:
                    pack_dates[fam] = ds
    except Exception:
        pack_dates = {}

    cache = _load_cache()
    today = _now().date()
    flags, checked, unresolved = [], 0, []
    for b in buys:
        d = _fetch(b["symbol"], cache)
        if not d:
            unresolved.append(b["symbol"])
            continue
        fam = b["symbol"].split(".")[0].upper()
        vendor_date, pack_date = d.get("next_print"), pack_dates.get(fam)
        use = pack_date or vendor_date
        if not use:
            unresolved.append(b["symbol"])
            continue
        date_note = None
        if pack_date and vendor_date and pack_date != vendor_date:
            date_note = (f"pack says {pack_date}, vendor says {vendor_date} — using the PACK "
                         f"(vendor dates are UNCONFIRMED); resolve before acting on timing")
        elif not pack_date:
            date_note = "vendor-derived date, UNCONFIRMED by any pack"
        try:
            pdate = datetime.date.fromisoformat(use)
        except ValueError:
            unresolved.append(b["symbol"])
            continue
        sess = _sessions_between(today, pdate)
        if sess < 0 or sess > NEAR_SESSIONS:
            continue
        checked += 1
        spot, vol = d["spot"], d["vol_annual"]
        if spot <= 0 or vol <= 0:
            continue
        event_sigma = vol * math.sqrt((sess + 1) / 252.0)
        dist_sig = math.log(b["limit"] / spot) / event_sigma if event_sigma > 0 else -99
        if dist_sig > 0.0 or dist_sig < -SIGMA_REACH:
            continue                        # already above spot, or too far to be gap-reachable
        p_fill = 0.5 * (1 + math.erf(dist_sig / math.sqrt(2)))
        flags.append({
            "symbol": b["symbol"], "qty": b["qty"], "limit": b["limit"], "spot": round(spot, 2),
            "next_print": use, "date_note": date_note, "sessions_to_print": sess,
            "implied_event_move_pct": round(event_sigma * 100, 1),
            "distance_sigma": round(dist_sig, 2), "p_fill_on_gap": round(p_fill, 3),
            "severity": "CRITICAL" if sess <= CRITICAL_SESSIONS else "WARN",
            "vol_basis": d["vol_basis"],
            "remedy": ("PULL the rung before the print, or state a reason to keep it and re-derive "
                       "the band POST-print (review-pack 'never silent death' branch). A gap-fill "
                       "is not our discount — it is a knife-catch against new information."),
        })

    CACHE.write_text(json.dumps(cache, indent=1))
    flags.sort(key=lambda f: (f["sessions_to_print"], -f["distance_sigma"]))
    payload = {"generated_utc": _now().isoformat(timespec="seconds") + "Z",
               "order_cache_age_h": round(stale_h, 1) if stale_h is not None else None,
               "order_cache_stale": (stale_h is None or stale_h > STALE_CACHE_H),
               "doctrine": ("A resting GTC buy with an unmanaged print inside its life is an "
                            "accidental SHORT-VOL position: it fills only on the adverse branch "
                            "(NATR -17.6%). Band and catalyst date are ONE artifact."),
               "buy_orders_scanned": len(buys), "with_print_inside_window": checked,
               "unresolved_symbols": sorted(set(unresolved)), "flags": flags}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1))

    if verbose:
        print(f"[print_collision] {len(buys)} resting buys | {checked} with a print inside "
              f"{NEAR_SESSIONS} sessions | {len(flags)} FLAGGED | {len(set(unresolved))} unresolved")
        for f in flags:
            print(f"  {f['severity']:8s} {f['symbol']:8s} {f['qty']}@{f['limit']} vs spot {f['spot']} "
                  f"| print {f['next_print']} in {f['sessions_to_print']}d "
                  f"| {f['distance_sigma']:+.2f}s of a ±{f['implied_event_move_pct']}% move "
                  f"| P(fill on gap) {f['p_fill_on_gap']*100:.0f}%")
        if unresolved:
            print(f"  UNRESOLVED (no print date — never silence): {', '.join(sorted(set(unresolved))[:20])}")
    if email and flags:
        try:
            from desk.mailer import send_raw
            crit = [f for f in flags if f["severity"] == "CRITICAL"]
            subj = (f"PRINT COLLISION: {len(crit)} critical / {len(flags)} resting buys could fill "
                    f"on an earnings gap")
            body = "\n\n".join(
                f"{f['severity']} {f['symbol']} {f['qty']}@{f['limit']} (spot {f['spot']})\n"
                f"  print {f['next_print']} in {f['sessions_to_print']} sessions; limit is "
                f"{f['distance_sigma']:+.2f} sigma of a ±{f['implied_event_move_pct']}% implied move\n"
                f"  P(fill on the gap) ~{f['p_fill_on_gap']*100:.0f}% — and it fills only if the news is bad\n"
                f"  {f['remedy']}" for f in flags)
            send_raw(subj, body + f"\n\nvol basis: {flags[0]['vol_basis']}")
        except Exception as ex:
            print(f"  (mail failed: {ex})")
    return payload


if __name__ == "__main__":
    scan(email="--no-email" not in sys.argv)
