"""csp_shadow — the paper put-writing sleeve (2026-07-30, user-directed: "think hard about CSPs —
what we're building could be a value-oriented hedge fund").

DOCTRINE SPLIT: premium-selling stays FORBIDDEN in the current taxable wrapper (the ~50% ordinary-
income drag makes a CSP a limit order that pays half its fee to the government). But the STRATEGY —
selling puts at court-adjudicated entry bands — is a legitimate fund-wrapper overlay with a genuinely
differentiated edge (strikes from underwritten fair value, not delta; event-aware IV timing from the
pack calendar). This module shadow-trades it so the fund decision is empirical, not vibes.

SELECTION GATES (all must pass to enter a shadow trade — same rigor as real):
  1. RP_FAIR/carry names ONLY (edge_source RISK_PREMIUM). Never EDGE-class — selling premium
     against a re-rate claim is selling our own alpha (the convexity rule).
  2. Strike at/below the court's band. The band IS the strike; no delta-picked strikes.
  3. Gate-6 meme/attention exclusion + no active squeeze-flow fingerprint (verbatim from the
     short-court doctrine).
  4. Kill-trigger linkage: the entry names the EC kill list; a kill-trigger fire during tenor =
     mandatory shadow buy-to-close at the then-market price (the forced-buyer-of-a-broken-thesis
     guard). Record the close honestly.
  5. Event-IV timing PREFERRED: entries just before a pack-covered print (where the pack already
     pre-commits us through the event) capture the crush; flag `event_entry: true`.

GRADING: every shadow trade resolves at expiry/assignment/kill-close and the ledger reports, vs the
counterfactual the book actually ran (the resting GTC at the same level): premium kept vs fills
missed vs assignments-into-drawdown. Quarterly report = the fund-decision evidence. Same honesty
rules as the calibration ledger: entries are prospective; anything retrospective is flagged and
excluded from grading.

CLI:
  python3 -m desk.csp_shadow add TICKER STRIKE EXPIRY(YYYY-MM-DD) PREMIUM IV --band-ref "EC cite" [--event]
  python3 -m desk.csp_shadow close TICKER EXPIRY --reason expiry|assigned|kill --px CLOSE_PX
  python3 -m desk.csp_shadow report
"""
from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "csp_shadow_ledger.json"


def _load():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"_doctrine": "shadow put-writing sleeve — see module docstring; taxable-wrapper premium-selling remains FORBIDDEN; this ledger exists so the FUND-wrapper decision is empirical",
            "trades": []}


def _save(d):
    LEDGER.write_text(json.dumps(d, indent=1))


def add(args):
    d = _load()
    t = {"ticker": args.ticker.upper(), "strike": args.strike, "expiry": args.expiry,
         "premium": args.premium, "iv_at_entry": args.iv, "band_ref": args.band_ref,
         "event_entry": bool(args.event), "entered": datetime.date.today().isoformat(),
         "status": "OPEN", "retrospective": bool(args.retro),
         "notional": args.strike * 100}
    if args.retro:
        t["grading"] = "EXCLUDED (retrospective entry — observation only)"
    d["trades"].append(t)
    _save(d)
    print(f"[csp_shadow] added {'(RETRO/EXCLUDED) ' if args.retro else ''}{t['ticker']} {t['strike']}p {t['expiry']} @ {t['premium']} (IV {t['iv']:.0%})" if False else
          f"[csp_shadow] added {'(RETRO/EXCLUDED) ' if args.retro else ''}{t['ticker']} {t['strike']}p {t['expiry']} @ ${t['premium']}")


def close(args):
    d = _load()
    for t in d["trades"]:
        if t["ticker"] == args.ticker.upper() and t["expiry"] == args.expiry and t["status"] == "OPEN":
            t["status"] = f"CLOSED_{args.reason.upper()}"
            t["close_px"] = args.px
            t["closed"] = datetime.date.today().isoformat()
            t["pnl_per_contract"] = round((t["premium"] - args.px) * 100, 2)
            _save(d)
            print(f"[csp_shadow] closed {t['ticker']} {t['strike']}p: {t['status']} pnl/contract ${t['pnl_per_contract']}")
            return
    print("[csp_shadow] no matching OPEN trade")


def report(args):
    d = _load()
    trades = d["trades"]
    open_t = [t for t in trades if t["status"] == "OPEN"]
    closed = [t for t in trades if t["status"].startswith("CLOSED") and not t.get("retrospective")]
    print(f"[csp_shadow] {len(trades)} total | {len(open_t)} open | {len(closed)} closed-gradeable")
    for t in trades:
        flag = " RETRO/EXCLUDED" if t.get("retrospective") else ""
        extra = f" pnl ${t.get('pnl_per_contract')}" if "pnl_per_contract" in t else ""
        print(f"  {t['entered']} {t['ticker']:9} {t['strike']}p {t['expiry']} @ ${t['premium']} "
              f"IV {t['iv_at_entry']:.0%} {'EVENT' if t.get('event_entry') else '     '} {t['status']}{extra}{flag}")
    if closed:
        pnl = sum(t.get("pnl_per_contract", 0) for t in closed)
        print(f"  gradeable P&L: ${pnl:.0f} across {len(closed)} — compare vs the GTC-ladder counterfactual at review")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("ticker"); a.add_argument("strike", type=float); a.add_argument("expiry")
    a.add_argument("premium", type=float); a.add_argument("iv", type=float)
    a.add_argument("--band-ref", required=True); a.add_argument("--event", action="store_true")
    a.add_argument("--retro", action="store_true")
    a.set_defaults(fn=add)
    c = sub.add_parser("close")
    c.add_argument("ticker"); c.add_argument("expiry")
    c.add_argument("--reason", required=True, choices=["expiry", "assigned", "kill"])
    c.add_argument("--px", type=float, required=True)
    c.set_defaults(fn=close)
    r = sub.add_parser("report")
    r.set_defaults(fn=report)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
