"""BETA completion-basket generator (runbook amendment 2026-08-21c).

BETA (ACCOUNT_BETA) direct-indexes MECHANICALLY: S&P 1500 membership (SPTM daily
holdings, cap weights) MINUS every name the household already touches with
judgment or with Parametric's optimizer. No courts because no thesis claim —
and this file is the rule. Any manual edit to the output basket is a doctrine
violation, not a tweak.

Exclusion stack (union):
  1. Parametric latest bundle        (msprime.db, latest reporting_date)
  2. research_ledger tickers         (every courted/screened name, any state)
  3. edge_classifications filenames  (every ruled record)
  4. ALPHA live positions cache      (desk/data/alpha_positions_cache.json)
  5. ALPHA resting-order symbols     (same cache — standing intents wash too)
  6. GOOGL                           (household wash name — asserted, never assumed)
  7. IBM                             (principal is an IBM employee — employment conflict;
                                      asserted in code, never trades in any desk book)

Usage:
  python3 -m desk.beta_basket_generator --notional 1600000 [--top 150]
      [--cap 0.025] [--holdings PATH.xlsx] [--out-dir desk/data/beta_basket]
Downloads today's SPTM holdings from SSGA when --holdings is absent.
Output: BasketTrader CSV (LMT at snapshot price, DAY) + manifest JSON.
The CSV is STAGED WORK — the principal reviews and clicks in TWS BasketTrader.
"""
import argparse
import csv
import datetime as dt
import json
import os
import sqlite3
import sys
from pathlib import Path

DESK = Path(__file__).parent
DATA = DESK / "data"
MSPRIME = Path("/Users/ajay/msprime/app/data/msprime.db")
SPTM_URL = ("https://www.ssga.com/us/en/intermediary/library-content/products/"
            "fund-data/etfs/us/holdings-daily-us-en-sptm.xlsx")
BETA_ACCOUNT_ROLE = "BETA"


def _beta_account():
    reg = json.loads((DATA / "accounts.json").read_text())
    return reg["accounts"]["BETA"]["account_id"]


def parametric_symbols():
    c = sqlite3.connect(MSPRIME)
    maxd = c.execute("select max(reporting_date) from positions").fetchone()[0]
    syms = {r[0] for r in c.execute(
        "select distinct symbol from positions where reporting_date=?", (maxd,))}
    c.close()
    return syms, maxd


def ledger_symbols():
    led = json.loads((DATA / "research_ledger.json").read_text())
    out = set()
    for n in led.get("names", []):
        if isinstance(n, dict) and n.get("ticker"):
            out.add(n["ticker"].split(".")[0].upper())
    for f in (DATA / "edge_classifications").glob("*.json"):
        out.add(f.stem.split(".")[0].upper())
    return out


def alpha_cache_symbols():
    cache = json.loads((DATA / "alpha_positions_cache.json").read_text())
    asof = dt.date.fromisoformat(cache["asof"])
    age = (dt.date.today() - asof).days
    if age > 7:
        print(f"WARNING: alpha_positions_cache.json is {age}d old — re-pull "
              "positions/orders before executing this basket.", file=sys.stderr)
    return {s.upper() for s in cache["positions"] + cache["resting_order_symbols"]}


def load_sptm(path):
    import openpyxl
    ws = openpyxl.load_workbook(path, read_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    asof = next((str(r[1]) for r in rows[:4] if r and r[0] == "Holdings:"), "?")
    hdr_i = next(i for i, r in enumerate(rows) if r and r[0] == "Name")
    hdr = {v: i for i, v in enumerate(rows[hdr_i]) if v}
    out = []
    for r in rows[hdr_i + 1:]:
        if not r or not r[hdr["Ticker"]]:
            continue
        t = str(r[hdr["Ticker"]]).strip().upper()
        w = r[hdr["Weight"]]
        if not t or t in ("-", "CASH_USD") or not isinstance(w, (int, float)) or w <= 0:
            continue
        out.append({"ticker": t, "name": str(r[hdr["Name"]]).strip(), "weight": float(w)})
    return out, asof


def fetch_sptm(dest):
    import requests
    r = requests.get(SPTM_URL, timeout=60, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127 Safari/537.36"})
    r.raise_for_status()
    if len(r.content) < 20000:
        raise RuntimeError("SPTM download suspiciously small — likely a block page")
    dest.write_bytes(r.content)
    return dest


def latest_prices():
    snaps = sorted((DATA / "px_snapshots").glob("2*.json"))
    if not snaps:
        raise RuntimeError("no px_snapshots available for share rounding")
    px = json.loads(snaps[-1].read_text())
    return px, snaps[-1].stem


def cap_and_renormalize(rows, cap):
    """Iteratively cap weights and redistribute to uncapped names."""
    w = {r["ticker"]: r["weight"] for r in rows}
    total = sum(w.values())
    w = {t: v / total for t, v in w.items()}
    for _ in range(50):
        over = {t: v for t, v in w.items() if v > cap}
        if not over:
            break
        excess = sum(v - cap for v in over.values())
        for t in over:
            w[t] = cap
        free = {t: v for t, v in w.items() if v < cap}
        free_sum = sum(free.values())
        if not free_sum:
            break
        for t in free:
            w[t] += excess * free[t] / free_sum
    return w


def build(notional, top, cap, holdings_path, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.date.today().strftime("%Y%m%d")
    if holdings_path is None:
        holdings_path = out_dir / f"sptm_holdings_{stamp}.xlsx"
        if not holdings_path.exists():
            fetch_sptm(holdings_path)
    universe, uni_asof = load_sptm(holdings_path)

    para, bundle_date = parametric_symbols()
    ledg = ledger_symbols()
    alpha = alpha_cache_symbols()

    def canon(sym):
        # class-share formats differ by vendor: BRK.B (SSGA) == BRK B (IBKR/Parametric)
        return sym.upper().replace(".", "").replace(" ", "").replace("-", "")

    # Asserted, never assumed: GOOGL (household wash), IBM (principal is an IBM employee —
    # employment conflict, 2026-08-31; never held in ANY desk book).
    excl = {canon(s) for s in para} | {canon(s) for s in ledg} \
         | {canon(s) for s in alpha} | {canon("GOOGL"), canon("IBM")}
    assert canon("GOOGL") in excl and canon("IBM") in excl

    kept = [r for r in universe if canon(r["ticker"]) not in excl]
    dropped = len(universe) - len(kept)
    kept.sort(key=lambda r: -r["weight"])
    basket = kept[:top]
    weights = cap_and_renormalize(basket, cap)

    px, px_date = latest_prices()

    def _lookup_px(t):
        # SSGA uses dot-class (BRK.B); snapshots/IBKR use space-class (BRK B)
        for k in (t, t.replace(".", " "), t.replace(".", "")):
            v = px.get(k)
            if isinstance(v, (int, float)) and v > 0:
                return v, k
        return None, t

    # yfinance fallback for names the snapshot lacks (class shares etc.)
    missing = [r["ticker"] for r in basket if _lookup_px(r["ticker"])[0] is None]
    yf_px = {}
    if missing:
        try:
            import yfinance as yf
            for t in missing:
                try:
                    p = yf.Ticker(t.replace(".", "-")).fast_info.last_price
                    if p and p > 0:
                        yf_px[t] = float(p)
                except Exception:
                    pass
        except ImportError:
            pass

    lines, skipped_px, alloc_total = [], [], 0.0
    for r in basket:
        t = r["ticker"]
        p, ib_sym = _lookup_px(t)
        if p is None and t in yf_px:
            p, ib_sym = yf_px[t], t.replace(".", " ")
        if p is None:
            skipped_px.append(t)
            continue
        alloc = notional * weights[t]
        qty = int(alloc // p)
        if qty < 1:
            skipped_px.append(t)
            continue
        alloc_total += qty * p
        lines.append({"ticker": ib_sym, "name": r["name"], "qty": qty, "px": round(p, 2),
                      "alloc": round(qty * p, 2), "weight": round(weights[t], 6)})

    # invariant: nothing excluded may appear (canonical comparison)
    leak = [l["ticker"] for l in lines if canon(l["ticker"]) in excl]
    assert not leak, f"exclusion leak: {leak}"

    acct = _beta_account()
    csv_path = out_dir / f"BETA_BASKET_{stamp}.csv"
    with open(csv_path, "w", newline="") as f:
        wtr = csv.writer(f)
        wtr.writerow(["Action", "Quantity", "Symbol", "SecType", "Exchange",
                      "Currency", "TimeInForce", "OrderType", "LmtPrice", "Account"])
        for l in lines:
            wtr.writerow(["BUY", l["qty"], l["ticker"], "STK", "SMART",
                          "USD", "DAY", "LMT", l["px"], acct])

    manifest = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "account": acct, "notional_requested": notional,
        "notional_allocated": round(alloc_total, 2),
        "universe": {"source": "SPTM (S&P 1500)", "asof": uni_asof, "n": len(universe)},
        "exclusions": {"parametric": len(para), "parametric_bundle": bundle_date,
                       "ledger_and_edge": len(ledg), "alpha_cache": len(alpha),
                       "union": len(excl), "universe_dropped": dropped},
        "basket": {"n": len(lines), "cap": cap, "top_requested": top,
                   "px_snapshot": px_date, "skipped_no_price": skipped_px},
        "doctrine": "mechanical completion replication — judgment-vs-rule boundary; "
                    "manual edits to the CSV violate the BETA doctrine",
        "lines": lines,
    }
    man_path = out_dir / f"BETA_BASKET_{stamp}_manifest.json"
    man_path.write_text(json.dumps(manifest, indent=1))
    return csv_path, man_path, manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notional", type=float, required=True)
    ap.add_argument("--top", type=int, default=150)
    ap.add_argument("--cap", type=float, default=0.025)
    ap.add_argument("--holdings", type=Path, default=None)
    ap.add_argument("--out-dir", type=Path, default=DATA / "beta_basket")
    a = ap.parse_args()
    csv_path, man_path, m = build(a.notional, a.top, a.cap, a.holdings, a.out_dir)
    b = m["basket"]; e = m["exclusions"]
    print(f"BETA basket: {b['n']} names, ${m['notional_allocated']:,.0f} of "
          f"${m['notional_requested']:,.0f} allocated (cap {b['cap']:.1%})")
    print(f"universe {m['universe']['n']} ({m['universe']['asof']}) minus {e['universe_dropped']} "
          f"excluded (parametric {e['parametric']} @ {e['parametric_bundle']}, "
          f"ledger/edge {e['ledger_and_edge']}, alpha cache {e['alpha_cache']})")
    if b["skipped_no_price"]:
        print(f"skipped (no price/sub-1-share): {len(b['skipped_no_price'])}: "
              f"{', '.join(b['skipped_no_price'][:12])}")
    print(f"CSV -> {csv_path}\nmanifest -> {man_path}")
    print("STAGED WORK ONLY: review + execute via TWS BasketTrader in the BETA account.")


if __name__ == "__main__":
    main()
