"""remark_buylist — daily re-mark of the staged muni buy list against the live EMMA tape.

WHY. Munis trade by appointment; list marks go stale in days. The pre-trade DD (2026-06-10) found
5 of 24 limits already wrong: Covina-Valley had cheapened 2.3pt (our limit would have OVERPAID),
Chico/Albany had richened >1pt (our limits sat unfillable below market). This script does that
re-mark every run: fresh last-trade px/date per CUSIP, drift vs the working mark, refreshed limit,
and a digest of names needing attention.

Limits: fast names mark+0.25 (lift the offer), thin names mark+0.50 ceiling (work the bid).
DRIFT FLAGS: |move| > 0.40pt -> RE-MARK (limit updated automatically, flagged for review);
stale > 45d with no print -> STALE (bid passively, do not chase).

Run:  PYTHONPATH=. python3 remark_buylist.py            (from verticals/muni_credit)
In/out: outputs/BUY_LIST_20260610.json (working limits updated in place, audit trail appended)
        + printed digest. NEVER places orders — staging only; placement is a human action in TWS
        (the claude.ai IBKR connector is stocks-only; TWS API placement would need read-only off
        and explicit per-batch approval).
"""
import json, time, datetime, statistics as st
import liquidity_gate as LG
import emma_scraper as E

BL = "outputs/BUY_LIST_20260610.json"
DRIFT_PT = 0.40
STALE_D = 45


def latest_prints(cusip, s, today):
    rows = [r for r in LG._fetch_trades(cusip, s) if r.get("PX") and r.get("YX") is not None]
    rows.sort(key=lambda r: r["TDT"] or r["TD"], reverse=True)
    if not rows:
        return None
    last = rows[0]
    # freshest customer-buy (S) print = what a buyer actually pays; fall back to any print
    s_rows = [r for r in rows if r.get("TT") == "S"]
    buy = s_rows[0] if s_rows else last
    d = datetime.date(int(last["TD"][:4]), int(last["TD"][5:7]), int(last["TD"][8:10]))
    return {"last_px": last["PX"], "last_ytw": last["YX"] / 100.0, "last_date": last["TD"][:10],
            "days_ago": (today - d).days, "buy_side_px": buy["PX"],
            "n_recent": sum(1 for r in rows if (today - datetime.date(int(r["TD"][:4]), int(r["TD"][5:7]), int(r["TD"][8:10]))).days <= 30)}


def main():
    today = datetime.date.today()
    bl = json.load(open(BL))
    s = E._session()
    digest, errors = [], []
    for o in bl["orders"]:
        if o.get("filled"):
            continue
        try:
            p = latest_prints(o["cusip"], s, today)
        except Exception as ex:
            errors.append((o["cusip"], str(ex)[:50])); time.sleep(1); continue
        if not p:
            digest.append((o["cusip"], "NO-TAPE", o["last_print_px"], None, o["limit_px"], "no prints on record"))
            time.sleep(0.6); continue
        old_mark = o["last_print_px"]
        move = round(p["last_px"] - old_mark, 2)
        room = 0.25 if o["phase"] == 1 else 0.50
        status, note = "OK", ""
        if p["days_ago"] > STALE_D and p["n_recent"] == 0:
            status, note = "STALE", f"no print in {p['days_ago']}d — bid passively, don't chase"
        elif abs(move) > DRIFT_PT:
            status = "RE-MARKED"
            note = f"tape moved {move:+.2f}pt -> mark {p['last_px']:.2f}, limit {p['last_px'] + room:.2f}"
            o["last_print_px"] = p["last_px"]
            o["last_trade"] = p["last_date"]
            o["limit_px"] = round(p["last_px"] + room, 2)
        else:
            o["last_trade"] = p["last_date"]
        o.setdefault("remark_log", []).append(
            {"date": str(today), "tape_px": p["last_px"], "tape_date": p["last_date"],
             "move_vs_mark": move, "status": status})
        digest.append((o["cusip"], status, old_mark, p["last_px"], o["limit_px"], note))
        time.sleep(0.6)
    bl["last_remark"] = str(today)
    json.dump(bl, open(BL, "w"), indent=1)

    print(f"RE-MARK {today} — {len(digest)} open names"
          + (f", {len(errors)} fetch errors: {errors}" if errors else ""))
    attn = [d for d in digest if d[1] != "OK"]
    print(f"{'cusip':11} {'status':9} {'oldMk':>7} {'tape':>7} {'limit':>7}  note")
    for cu, stt, om, tp, lim, note in (attn if attn else digest[:5]):
        print(f"{cu:11} {stt:9} {om:7.2f} {(tp if tp is not None else -1):7.2f} {lim:7.2f}  {note}")
    if not attn:
        print("  (all marks within tolerance; first 5 shown)")
    return digest


if __name__ == "__main__":
    main()
