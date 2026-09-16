"""ibkr_bond_ingest.py — pull bonds straight from the running TWS via the TWS API (ib_insync).

Talks to the Trader Workstation you already have open — no separate gateway. Resolves each
bond's CUSIP / coupon / maturity / ratings and a live price, and writes a JSON the muni
pipeline scores (compute_bond_analytics -> channel_scoring_v2). Closes muni TD-2 (CUSIP-level
pricing the EMMA scale couldn't give).

NOTE: the TWS API cannot read a *named watchlist* (IBKR doesn't expose UI watchlists over the
socket). So source the bonds one of three ways:
  --cusips A,B,C           paste CUSIPs
  --file watchlist.csv     export your TWS watchlist to CSV (File ▸ export, or right-click ▸
                           Export) and point here — CUSIPs are auto-extracted from any column
  --positions              pull the bonds you actually hold

RUNS ON YOUR MACHINE (it connects to your local TWS socket).

────────────────────────────────────────────────────────────────────────────
SETUP
  1. In TWS:  File ▸ Global Configuration ▸ API ▸ Settings
        ✓ Enable ActiveX and Socket Clients
        ✓ (note the Socket port — live TWS = 7496, paper = 7497)
        ✓ add 127.0.0.1 to Trusted IPs   (and leave "Read-Only API" CHECKED — we only read)
  2. pip install ib_insync
  3. python ibkr_bond_ingest.py --cusips 13063DGA0,13063DLM8 --out bonds.json
     python ibkr_bond_ingest.py --file my_watchlist.csv --out bonds.json
     python ibkr_bond_ingest.py --positions --out bonds.json
     (add --port 7497 for paper TWS, --debug to see raw contract details)

Read-only: no order endpoints are touched.
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys

try:
    from ib_insync import IB, Bond
except ImportError:
    sys.exit("pip install ib_insync")

CUSIP_RE = re.compile(r"\b([0-9A-Z]{9})\b")
# tokens that look like a CUSIP but aren't (avoid grabbing tickers/dates from an export)
_NOT_CUSIP = re.compile(r"^\d{9}$|^[A-Z]{9}$")   # all-digit or all-alpha 9-chars are rarely muni CUSIPs
DEBUG = False


def cusips_from_file(path: str) -> list[str]:
    text = open(path, encoding="utf-8", errors="ignore").read().upper()
    out, seen = [], set()
    for m in CUSIP_RE.finditer(text):
        c = m.group(1)
        if c in seen or _NOT_CUSIP.match(c):
            continue
        seen.add(c); out.append(c)
    return out


def _price(tk) -> float | None:
    for v in (tk.last, tk.close, (tk.bid + tk.ask) / 2 if tk.bid and tk.ask else None,
              tk.ask, tk.bid):
        if v and v == v and v > 0:          # not None, not NaN, positive
            return float(v)
    return None


def detail_to_row(cd, tk) -> dict:
    c = cd.contract
    return {
        "conid": c.conId,
        "cusip": getattr(cd, "cusip", None) or c.symbol,
        "issuer": (cd.longName or c.symbol or "").strip(),
        "coupon": getattr(cd, "coupon", None),
        "maturity": getattr(cd, "maturity", None),
        "ratings": getattr(cd, "ratings", None),
        "bond_type": getattr(cd, "bondType", None),
        "callable": getattr(cd, "callable", None),
        "price": _price(tk) if tk else None,
        "bid": tk.bid if tk else None,
        "ask": tk.ask if tk else None,
    }


def pull_by_cusips(ib: "IB", cusips: list[str]) -> list[dict]:
    rows = []
    for cu in cusips:
        try:
            cds = ib.reqContractDetails(Bond(symbol=cu, exchange="SMART", currency="USD"))
        except Exception as e:
            print(f"  ! {cu}: contract lookup failed ({e})"); continue
        if not cds:
            print(f"  ! {cu}: no bond contract found"); continue
        cd = cds[0]
        if DEBUG:
            print(f"[debug] {cu}: {cd.cusip} {getattr(cd,'coupon',None)} {getattr(cd,'maturity',None)} {cd.longName}")
        tk = ib.reqMktData(cd.contract, "", False, False)
        ib.sleep(2)
        rows.append(detail_to_row(cd, tk))
        ib.cancelMktData(cd.contract)
    return rows


def pull_positions(ib: "IB") -> list[dict]:
    bonds = [p for p in ib.positions() if p.contract.secType == "BOND"]
    if not bonds:
        print("  (no bond positions held)"); return []
    rows = []
    for p in bonds:
        cds = ib.reqContractDetails(p.contract)
        cd = cds[0] if cds else None
        if not cd:
            continue
        tk = ib.reqMktData(cd.contract, "", False, False); ib.sleep(2)
        row = detail_to_row(cd, tk); row["position"] = p.position; row["avg_cost"] = p.avgCost
        rows.append(row); ib.cancelMktData(cd.contract)
    return rows


def main():
    global DEBUG
    ap = argparse.ArgumentParser()
    ap.add_argument("--cusips", help="comma-separated CUSIPs")
    ap.add_argument("--file", help="watchlist/CSV export to auto-extract CUSIPs from")
    ap.add_argument("--positions", action="store_true", help="pull bonds you currently hold")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=7496, help="TWS socket: live=7496, paper=7497")
    ap.add_argument("--client-id", type=int, default=17)
    ap.add_argument("--out", default="bonds.json")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    DEBUG = a.debug

    ib = IB()
    try:
        ib.connect(a.host, a.port, clientId=a.client_id, timeout=10, readonly=True)
    except Exception as e:
        sys.exit(f"Could not connect to TWS at {a.host}:{a.port} ({e}). "
                 f"Is TWS open with API enabled? (live port 7496 / paper 7497)")

    try:
        if a.positions:
            rows = pull_positions(ib)
        else:
            cusips = []
            if a.cusips:
                cusips += [x.strip().upper() for x in a.cusips.split(",") if x.strip()]
            if a.file:
                cusips += cusips_from_file(a.file)
            cusips = list(dict.fromkeys(cusips))   # dedupe, keep order
            if not cusips:
                sys.exit("Pass --cusips, --file <export>, or --positions")
            print(f"resolving {len(cusips)} CUSIP(s) via TWS…")
            rows = pull_by_cusips(ib, cusips)
    finally:
        ib.disconnect()

    if not rows:
        sys.exit("No bonds resolved.")
    with open(a.out, "w") as f:
        json.dump({"source": "tws_api", "n": len(rows), "bonds": rows}, f, indent=1, default=str)
    csv_path = a.out.rsplit(".", 1)[0] + ".csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cusip", "issuer", "coupon", "maturity", "ratings",
                                          "price", "bid", "ask", "conid"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in w.fieldnames})

    print(f"\nwrote {len(rows)} bonds -> {a.out} and {csv_path}")
    for r in rows:
        print(f"  {str(r.get('cusip')):>12}  {(r.get('issuer') or '')[:32]:32} "
              f"{r.get('coupon') or '?'}% {str(r.get('maturity') or '?'):>10}  px {r.get('price')}")
    print("\nnext: commit bonds.json (or paste it) and I'll run compute_bond_analytics + "
          "channel_scoring_v2 to score creditworthiness + AI-insulation and assemble the basket.")


if __name__ == "__main__":
    main()
