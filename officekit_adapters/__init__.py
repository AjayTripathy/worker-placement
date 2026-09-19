"""officekit_adapters — auto-discovery of live brokerage/portfolio connections
(the first auto-adapter, principal-directed 2026-09-05: "by default when we
install, search for an active IBKR or TWS connection to look up positions").

THE CONTRACT — an adapter is a registered probe + (optionally) a fetcher:

    @adapter("ibkr_socket", label="IBKR TWS / IB Gateway", kind="broker")
    def make():
        return {"detect": fn(ctx)->status, "fetch": fn(ctx)->rows | None}

  detect(ctx) -> {"found": bool, "status": "ready"|"needs_login"|"needs_key"|
                  "needs_dep"|"absent", "detail": str, "guidance": str|None}
      MUST be fast (sub-second budget; discover() runs every adapter with a
      hard per-probe timeout) and MUST NOT authenticate, write, or prompt.
  fetch(ctx)  -> [{"symbol", "qty", "value", "description", "account",
                   "ccy", "sec_type"}, ...]
      READ-ONLY, positions only. Absent fetch = detect-only: the adapter
      documents a connectable surface and its guidance tells the user (or a
      future session) what unlocks it. Fetchers NEVER handle credentials
      beyond passing env-var-named keys the user already exported — the
      models.json posture: secrets live in the environment, never in files.

Discovery is the onboarding simplifier: `officekit serve` scans on the
onboarding page and offers one-click position import; `officekit discover`
prints the same scan in the terminal. Everything degrades loud — an adapter
that errors reports the error as its detail, never blocks the scan.

THE LANDSCAPE (surveyed 2026-09-05; detect-only stubs mark the trailheads):
  live local processes .. IBKR TWS / IB Gateway (socket API, ports 7496/7497
                          live, 4001/4002 gateway); IBKR Client Portal gateway
                          (https://localhost:5000/v1/api); Ghostfolio
                          (self-hosted, :3333)
  env-keyed REST/lib .... Alpaca (APCA_API_KEY_ID; positions REST, fetch built);
                          Robinhood (ROBINHOOD_USERNAME/PASSWORD + ROBINHOOD_TOTP
                          via robin_stocks; equities + crypto, fetch built);
                          Tradier (TRADIER_ACCESS_TOKEN); Coinbase/Kraken/Binance/
                          Gemini (crypto keys); Webull/Public (unofficial) — stubs
  aggregators (OAuth) ... SnapTrade (SNAPTRADE_CLIENT_ID — reaches Robinhood,
                          Fidelity, Webull, Wealthfront, 20+ more), Plaid
                          Investments (PLAID_CLIENT_ID), Schwab (SCHWAB_APP_KEY),
                          E*TRADE (ETRADE_CONSUMER_KEY) — app-level OAuth; hosted-tier
  files ................. broker positions-CSV exports already sitting in
                          ~/Downloads (Fidelity/Vanguard/Schwab/Wealthfront-style;
                          sniffed with the same header detector as intake); and the
                          Morgan Stanley Prime bundle (morgan_stanley.py)
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import socket
import ssl
import time
import urllib.request
from pathlib import Path

ADAPTERS = {}
PROBE_TIMEOUT_S = 2.5          # hard per-adapter budget inside discover()

# Connector libraries the product ships with BY DEFAULT (import_name -> pip spec).
# These are declared as core dependencies in pyproject so one install of the
# product brings every connector — no per-broker `pip install`. `wp doctor`
# installs any that are missing (a bare checkout self-heals without pip commands).
CONNECTOR_PACKAGES = {
    "ib_insync":    "ib_insync>=0.9.86",   # Interactive Brokers — TWS / IB Gateway
    "robin_stocks": "robin_stocks>=3.0",   # Robinhood (equities + crypto)
    "pyotp":        "pyotp>=2.8",          # Robinhood 2FA (TOTP), headless login
}


def missing_connectors():
    """{import_name: pip_spec} for connector libs not importable in this env."""
    import importlib.util
    return {imp: spec for imp, spec in CONNECTOR_PACKAGES.items()
            if importlib.util.find_spec(imp) is None}


def adapter(name, label, kind, auto=True, runtimes=("local",)):
    """auto=False marks an adapter MANUAL-ONLY: the daily loop never auto-pulls it
    (e.g. downloads_csv, which scans ~/Downloads — a stray CSV there must not
    silently enter the book; the user pulls it deliberately). 2026-09-10."""
    def deco(factory):
        ADAPTERS[name] = {"name": name, "label": label, "kind": kind,
                          "auto": auto, "runtimes": tuple(runtimes), "factory": factory}
        return factory
    return deco


def supports_runtime(name, runtime):
    """Fail closed: new connectors are local unless explicitly reviewed for hosting."""
    spec = ADAPTERS.get(name)
    return bool(spec and runtime in spec.get('runtimes', ('local',)))


def discover(names=None, ctx=None):
    """Run every registered detect concurrently under a hard timeout.
    Returns [{name, label, kind, found, status, detail, guidance, can_fetch}]."""
    from officekit.runtime import hosted
    if hosted():
        names = [n for n in (ADAPTERS if names is None else names) if supports_runtime(n, 'hosted')]
    ctx = ctx or {}
    picked = [a for n, a in ADAPTERS.items() if names is None or n in names]

    def probe(a):
        out = {"name": a["name"], "label": a["label"], "kind": a["kind"],
               "auto": a.get("auto", True),
               "found": False, "status": "absent", "detail": "", "guidance": None,
               "can_fetch": False}
        try:
            impl = a["factory"]()
            out["can_fetch"] = impl.get("fetch") is not None
            r = impl["detect"](ctx)
            out.update({k: r[k] for k in ("found", "status", "detail") if k in r})
            if r.get("guidance"):
                out["guidance"] = r["guidance"]
        except Exception as e:                       # degrade loud, never block the scan
            out.update({"status": "error", "detail": f"{type(e).__name__}: {e}"})
        return out

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(len(picked), 1)) as ex:
        from contextvars import copy_context
        futs = {ex.submit(copy_context().run, probe, a): a for a in picked}
        results = []
        for f, a in futs.items():
            try:
                results.append(f.result(timeout=PROBE_TIMEOUT_S))
            except concurrent.futures.TimeoutError:
                results.append({"name": a["name"], "label": a["label"], "kind": a["kind"],
                                "auto": a.get("auto", True),
                                "found": False, "status": "timeout",
                                "detail": f"probe exceeded {PROBE_TIMEOUT_S}s", "guidance": None,
                                "can_fetch": False})
    order = {n: i for i, n in enumerate(ADAPTERS)}
    return sorted(results, key=lambda r: (not r["found"], order.get(r["name"], 99)))


def fetch_positions(name, ctx=None):
    """Run one adapter's fetcher. Raises on a detect-only adapter or any failure
    (callers surface the error; nothing silent)."""
    from officekit.runtime import hosted
    if hosted() and not supports_runtime(name, 'hosted'):
        raise ValueError("This broker runs on your local machine. Enable office sync to share its imported balances.")
    a = ADAPTERS.get(name)
    if not a:
        raise KeyError(f"unknown adapter {name!r}")
    impl = a["factory"]()
    if not impl.get("fetch"):
        raise RuntimeError(f"{name} is detect-only — {a['label']} needs manual setup")
    rows = impl["fetch"](ctx or {})
    return [_norm_row(r) for r in rows]


def fetch_snapshot(name, ctx=None):
    """Optional complete-snapshot seam; ordinary fetchers remain partial.

    An adapter may return {rows, as_of, snapshot} from factory()['snapshot'].
    Complete coverage and independent control totals are validated by staging;
    never infer completeness from a nonempty list or recompute a control total.
    """
    from datetime import date
    from officekit.runtime import hosted
    if hosted() and not supports_runtime(name, 'hosted'):
        raise ValueError("This broker runs on your local machine. Enable office sync to share its imported balances.")
    impl = ADAPTERS[name]["factory"]()
    if impl.get("snapshot"):
        result = dict(impl["snapshot"](ctx or {}))
        # Preserve strict numeric validation before _norm_row can coerce bad
        # data into plausible zeros.
        from officekit.staging import validate_snapshot
        validate_snapshot(result["rows"], result["snapshot"], result.get("as_of"))
        result["rows"] = [_norm_row(r) for r in result["rows"]]
        return result
    return {"rows": fetch_positions(name, ctx), "as_of": date.today().isoformat(),
            "snapshot": {"mode": "partial"}}


def _norm_row(r):
    out = {"symbol": str(r.get("symbol", "")).upper(),
           "qty": float(r.get("qty") or 0),
           "value": round(float(r.get("value") or 0), 2),
           "description": r.get("description") or "",
           "account": r.get("account") or "brokerage",
           "ccy": r.get("ccy") or "USD",
           "sec_type": r.get("sec_type") or "STK"}
    for k in ("local_value", "fx", "right", "strike", "multiplier", "expiry", "expiration",
              "lastTradeDateOrContractMonth", "conid", "conId", "isin", "cusip",
              "cost_basis", "unrealized_pnl", "value_is_cost",   # basis for harvest
              "lots", "loss_lt", "loss_st"):                     # lot-level (Flex) harvest
        if r.get(k) is not None:                     # conversion provenance + option terms + basis
            out[k] = r[k]
    return out


def short_put_obligations(rows, base="USD"):
    """Summarize short puts as what they really are: collateralized purchase
    obligations at the strike (|qty| x strike x multiplier), converted to base.
    A short-put book that MARKS to noise can still commit tens of thousands —
    the mark measures the premium, never the obligation (principal-directed
    2026-09-05). Returns {total, count, items} with items sorted largest-first;
    rows without option terms are simply not counted."""
    items = []
    for r in rows:
        if r.get("sec_type") not in ("OPT", "FOP"):
            continue
        if r.get("right") != "P" or float(r.get("qty") or 0) >= 0:
            continue
        strike, mult = float(r.get("strike") or 0), float(r.get("multiplier") or 100)
        if not strike:
            continue
        fx = float(r.get("fx") or (1.0 if (r.get("ccy") or base) == base else 0)) or 1.0
        ob = abs(float(r["qty"])) * strike * mult * fx
        items.append({"symbol": r["symbol"], "strike": strike,
                      "expiry": (r.get("description") or "").split()[1] if len((r.get("description") or "").split()) > 1 else "",
                      "qty": float(r["qty"]), "obligation": round(ob, 2)})
    items.sort(key=lambda x: -x["obligation"])
    return {"total": round(sum(x["obligation"] for x in items), 2),
            "count": len(items),
            "contracts": int(sum(abs(x["qty"]) for x in items)), "items": items}


def covered_call_summary(rows, base="USD"):
    """Classify SHORT CALLS against the rest of the imported book before
    labeling anything: a short call matched by a long call on the same
    underlying is a SPREAD LEG (defined risk, not a cap on stock); the
    remainder covered by held shares is a COVERED CALL (shares encumbered —
    callable away at the strike); anything left is NAKED (unbounded risk —
    flagged loudly, never averaged away). Aggregation is per underlying, not
    per strike pair — the point is exposure class, not spread reconstruction."""
    # key by (account, symbol): shares in one account must not "cover" a short
    # call written in another account (that would understate naked risk, 2026-09-06)
    stock_qty, stock_val = {}, {}
    long_calls = {}
    shorts = []
    for r in rows:
        k = (r.get("account"), r.get("symbol", ""))
        if r.get("sec_type") == "STK":
            q = float(r.get("qty") or 0)
            stock_qty[k] = stock_qty.get(k, 0) + q
            stock_val[k] = stock_val.get(k, 0.0) + float(r.get("value") or 0)   # weighted, not last-lot
        elif r.get("sec_type") in ("OPT", "FOP") and r.get("right") == "C":
            q = float(r.get("qty") or 0)
            if q > 0:
                long_calls[k] = long_calls.get(k, 0) + q
            elif q < 0:
                shorts.append(r)
    covered, naked, spread_matched = [], [], 0
    for r in sorted(shorts, key=lambda x: -abs(float(x.get("qty") or 0))):
        sym = r["symbol"]
        k = (r.get("account"), sym)
        n = abs(float(r["qty"]))
        mult = float(r.get("multiplier") or 100)
        strike = float(r.get("strike") or 0)
        fx = float(r.get("fx") or (1.0 if (r.get("ccy") or base) == base else 0)) or 1.0
        m = min(n, long_calls.get(k, 0))             # spread legs consume long calls (same account) first
        long_calls[k] = long_calls.get(k, 0) - m
        spread_matched += m
        n -= m
        if n <= 0:
            continue
        c = min(n, max(stock_qty.get(k, 0), 0) // mult)
        if c:
            shares = c * mult
            held = stock_qty.get(k, 0) or 1
            per_share = stock_val.get(k, 0.0) / held
            stock_qty[k] -= shares                    # shares cover one call once, in THIS account
            covered.append({"symbol": sym, "strike": strike, "contracts": c,
                            "shares": shares,
                            "callable_for": round(shares * strike * fx, 2),
                            "encumbered_value": round(shares * per_share, 2)})
        if n - c > 0:
            naked.append({"symbol": sym, "strike": strike, "contracts": n - c})
    return {"covered": covered, "spread_matched_contracts": int(spread_matched),
            "naked": naked}


def convert_to_base(rows, fx, base="USD"):
    """Convert local-currency market values to the account's base currency.
    THE $20.8M LESSON (2026-09-05, live): position marketValue arrives in LOCAL
    currency — summing JPY/KRW rows as dollars inflated a $937k account 22x.
    `value` after this call is base-currency; the local figure and rate ride
    along as provenance. A currency with NO rate is zeroed (value 0, local kept
    on local_value) and flagged — NEVER left at its local magnitude, because a
    downstream sum can't tell converted from local and a ¥1.3B row would enter
    the book as $1.3B (the no-rate half of the $20.8M lesson, 2026-09-06). A
    conservative $0 with a loud flag beats a catastrophic overstate."""
    from officekit.staging import num
    out = []
    for r in rows:
        r = dict(r)
        ccy = (r.get("ccy") or base).upper()
        rate = 1.0 if ccy == base else fx.get(ccy)
        val = num(r.get("value"))
        if rate is not None:
            r["local_value"] = round(val, 2)
            r["fx"] = rate
            r["value"] = val * rate
            for k in ("cost_basis", "unrealized_pnl", "loss_lt", "loss_st"):  # same ccy as value
                if r.get(k) is not None:
                    r[k] = round(num(r[k]) * rate, 2)
            r["ccy"] = base          # IDEMPOTENT: value is now base-currency, so a
            #                          second convert_to_base is a no-op (rate 1.0),
            #                          never a re-multiply or a zeroing. (2026-09-09)
        else:                                        # no FX rate: do not let local money reach a total
            r["local_value"] = round(val, 2)
            r["value"] = 0.0
            r["needs_fx"] = ccy
            r["description"] = (r.get("description") or r.get("symbol", "")) + \
                f" ({ccy} {val:,.0f} UNCONVERTED — no FX rate; shown as $0, set manually)"
        out.append(r)
    return out


# ------------------------------------------------------------------ probes

def _port_open(host, port, timeout=0.4):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _https_json(url, timeout=1.2, method="GET", headers=None):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False                      # local gateways use self-signed certs
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode(errors="replace"))


# ------------------------------------------------- IBKR: TWS / IB Gateway (socket API)

IBKR_SOCKET_PORTS = ((4001, "IB Gateway (live)"), (4002, "IB Gateway (paper)"),
                     (7496, "TWS (live)"), (7497, "TWS (paper)"))
# clientId far from any local convention (the desk pinned 23/41/43); collisions
# disconnect the OTHER client, so stay out of low ranges entirely
IBKR_CLIENT_ID = int(os.environ.get("OFFICEKIT_IBKR_CLIENT_ID", "87"))


@adapter("ibkr_socket", label="Interactive Brokers — TWS / IB Gateway", kind="broker")
def _ibkr_socket():
    def detect(ctx):
        import importlib.util
        for port, what in IBKR_SOCKET_PORTS:
            if _port_open("127.0.0.1", port):
                # find_spec, never import: ib_insync builds an asyncio loop at
                # import time and detect() runs in a worker thread
                if importlib.util.find_spec("ib_insync"):
                    return {"found": True, "status": "ready",
                            "detail": f"{what} listening on 127.0.0.1:{port}"}
                return {"found": True, "status": "needs_dep",
                        "detail": f"{what} listening on 127.0.0.1:{port}",
                        "guidance": "run `worker-placement doctor` to install the bundled connector libs"}
        return {"found": False, "status": "absent",
                "detail": "no TWS/Gateway socket on 4001/4002/7496/7497"}

    def fetch(ctx):
        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:                         # serve handler threads have no loop
            asyncio.set_event_loop(asyncio.new_event_loop())
        from ib_insync import IB
        port = next(p for p, _ in IBKR_SOCKET_PORTS if _port_open("127.0.0.1", p))
        ib = IB()
        ib.connect("127.0.0.1", port, clientId=IBKR_CLIENT_ID, timeout=12, readonly=True)
        try:
            # portfolio() carries live marketValue — but ib_insync only
            # auto-subscribes account updates when connect() gets an explicit
            # account, and with MULTIPLE managed accounts nothing subscribes at
            # all: portfolio() stays empty and a naive fetch silently degrades
            # to cost basis (the $917k-vs-$958k lesson, 2026-09-05). Subscribe
            # per account; reqAccountUpdatesAsync returns after the initial
            # download completes.
            for acct in ib.managedAccounts():
                try:
                    # hard per-account timeout: TWS honors ONE account-updates
                    # subscription at a time, and a second/empty account's
                    # download-end event may never fire (live hang, 2026-09-05)
                    ib._run(asyncio.wait_for(ib.reqAccountUpdatesAsync(acct), 8))
                except Exception:
                    continue                         # a dead sub-account never blocks the rest
            seen, items = set(), []
            for it in ib.portfolio():
                key = (it.account, it.contract.conId)
                if key not in seen:
                    seen.add(key)
                    items.append(it)
            rows = []
            if items:
                for it in items:
                    c = it.contract
                    row = {"symbol": c.symbol, "qty": it.position,
                           "value": it.marketValue, "ccy": c.currency,
                           "sec_type": c.secType, "account": it.account,
                           "description": _ib_desc(c), **_opt_terms(c)}
                    # capture cost basis + unrealized P&L so the harvest page can
                    # measure IBKR losers. NOTE: this is AVERAGE cost, not per-lot
                    # tax lots — lot-level LT/ST needs a Flex Query / statement.
                    upnl = getattr(it, "unrealizedPNL", None)
                    if upnl is not None and it.marketValue is not None:
                        row["unrealized_pnl"] = upnl
                        row["cost_basis"] = it.marketValue - upnl
                    rows.append(row)
            else:                                    # portfolio() empty (Gateway w/o
                # account-updates/market-data): positions() still carries qty +
                # avgCost, so we get real COST BASIS even with no market value.
                # value falls back to cost, FLAGGED so the sync won't overwrite a
                # good market value with cost (2026-09-09).
                for p in ib.positions():
                    c = p.contract
                    cost_basis = p.position * p.avgCost   # avgCost is per-unit (incl mult for options)
                    rows.append({"symbol": c.symbol, "qty": p.position,
                                 "value": cost_basis, "value_is_cost": True,
                                 "cost_basis": cost_basis,
                                 "ccy": c.currency, "sec_type": c.secType,
                                 "account": p.account,
                                 "description": _ib_desc(c) + " (cost basis; no live market value)",
                                 **_opt_terms(c)})
            # market values arrive in LOCAL currency — convert through the
            # account's own ledger FX ($LEDGER-ExchangeRate per currency)
            avs = ib.accountValues()
            fx = {av.currency: float(av.value) for av in avs
                  if av.tag == "$LEDGER-ExchangeRate" and av.currency not in ("", "BASE")}
            base = next((av.value for av in avs if av.tag == "Currency" and av.value
                         and av.value != "BASE"), "USD")
            rows = convert_to_base(rows, fx, base=base)
            # cash rides along so the import reconciles to NetLiquidation — EVERY
            # currency's cash leg, converted (a foreign cash balance dropped here
            # undershoots NetLiq; 2026-09-06)
            cash_rows = []
            for av in avs:
                if av.tag == "TotalCashValue" and av.currency not in ("", "BASE") and float(av.value):
                    cash_rows.append({"symbol": "CASH", "qty": float(av.value),
                                      "value": float(av.value), "ccy": av.currency, "sec_type": "CASH",
                                      "account": av.account,
                                      "description": f"IBKR cash balance {av.currency} ({av.account})"})
            rows += convert_to_base(cash_rows, fx, base=base)
            return rows
        finally:
            ib.disconnect()

    return {"detect": detect, "fetch": fetch}


def _ib_desc(c):
    if c.secType in ("OPT", "FOP"):
        return f"{c.symbol} {c.lastTradeDateOrContractMonth} {c.strike}{c.right}"
    return c.symbol


def _opt_terms(c):
    """Structured option terms — the right (P/C) is load-bearing for the
    obligation/covered-call summaries; never parse it back out of a label."""
    if c.secType not in ("OPT", "FOP"):
        return {}
    return {"right": c.right, "strike": float(c.strike or 0),
            "multiplier": float(c.multiplier or 100)}


# --------------------------------------------- IBKR: Client Portal gateway (REST)

@adapter("ibkr_clientportal", label="Interactive Brokers — Client Portal gateway", kind="broker")
def _ibkr_cp():
    def _base():
        for port in (5000, 5001):
            if _port_open("127.0.0.1", port):
                return f"https://127.0.0.1:{port}/v1/api"
        return None

    def detect(ctx):
        base = _base()
        if not base:
            return {"found": False, "status": "absent",
                    "detail": "no Client Portal gateway on 5000/5001"}
        try:
            st = _https_json(f"{base}/iserver/auth/status", method="POST")
        except urllib.error.HTTPError as e:          # an HTTP answer = a real CP gateway
            return {"found": True, "status": "needs_login",
                    "detail": f"gateway up, session not authenticated (HTTP {e.code})",
                    "guidance": f"log in at {base.rsplit('/v1', 1)[0]}"}
        except Exception:
            # an open port that can't speak the CP API is NOT a gateway —
            # macOS AirPlay Receiver squats on 5000 (live false positive, 2026-09-05)
            return {"found": False, "status": "absent",
                    "detail": "port 5000/5001 open but not a Client Portal gateway "
                              "(macOS AirPlay also uses 5000)"}
        if st.get("authenticated"):
            return {"found": True, "status": "ready", "detail": "gateway up, session authenticated"}
        return {"found": True, "status": "needs_login", "detail": "gateway up, session not authenticated",
                "guidance": f"log in at {base.rsplit('/v1', 1)[0]}"}

    def fetch(ctx):
        base = _base()
        if not base:
            raise RuntimeError("Client Portal gateway not reachable")
        accounts = _https_json(f"{base}/portfolio/accounts")
        rows = []
        for acct in accounts:
            aid = acct.get("accountId") or acct.get("id")
            page = 0
            while True:
                pos = _https_json(f"{base}/portfolio/{aid}/positions/{page}", timeout=8)
                if not pos:
                    break
                for p in pos:
                    rows.append({"symbol": p.get("ticker") or p.get("contractDesc", ""),
                                 "qty": p.get("position"), "value": p.get("mktValue"),
                                 "ccy": p.get("currency"), "sec_type": p.get("assetClass"),
                                 "account": aid, "description": p.get("contractDesc", "")})
                if len(pos) < 30:                    # CP pages are 30 rows
                    break
                page += 1
        # same local-currency trap as the socket API: convert via the CP
        # ledger's per-currency exchange rates
        fx = {}
        try:
            for aid in {r["account"] for r in rows}:
                ledger = _https_json(f"{base}/portfolio/{aid}/ledger", timeout=8)
                for ccy, leg in (ledger or {}).items():
                    if isinstance(leg, dict) and leg.get("exchangerate") is not None:
                        fx[ccy.upper()] = float(leg["exchangerate"])
        except Exception:
            pass                                     # convert_to_base labels what it can't convert
        return convert_to_base(rows, fx)

    return {"detect": detect, "fetch": fetch}


# ------------------------------------------------------------------- Alpaca (env keys)

@adapter("alpaca", label="Alpaca", kind="broker", runtimes=("local", "hosted"))
def _alpaca():
    def _keys():
        from officekit.runtime import credential
        kid = credential("APCA_API_KEY_ID") or credential("ALPACA_API_KEY_ID")
        sec = credential("APCA_API_SECRET_KEY") or credential("ALPACA_API_SECRET_KEY")
        return (kid, sec) if kid and sec else None

    def detect(ctx):
        if _keys():
            from officekit.runtime import hosted
            return {"found": True, "status": "ready", "detail": "Keys saved privately for this office" if hosted() else "API keys present in environment"}
        return {"found": False, "status": "needs_key",
                "detail": "no APCA_API_KEY_ID / APCA_API_SECRET_KEY in environment",
                "guidance": "export Alpaca keys to enable position import"}

    def fetch(ctx):
        kid, sec = _keys()
        from officekit.runtime import credential
        base = credential("APCA_API_BASE_URL") or "https://api.alpaca.markets"
        if base not in {"https://api.alpaca.markets", "https://paper-api.alpaca.markets"}:
            raise ValueError("Choose Alpaca live or paper accounts")
        req = urllib.request.Request(f"{base}/v2/positions",
                                     headers={"APCA-API-KEY-ID": kid, "APCA-API-SECRET-KEY": sec})
        from officekit.cloud import NoRedirect
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=8) as resp:
            pos = json.loads(resp.read(16 * 1024 * 1024).decode())
        return [{"symbol": p["symbol"], "qty": p.get("qty"), "value": p.get("market_value"),
                 "ccy": "USD", "sec_type": p.get("asset_class", "STK").upper(),
                 "description": p["symbol"]} for p in pos]

    return {"detect": detect, "fetch": fetch}


# ------------------------------------------------------------- Robinhood (env keys)

@adapter("robinhood", label="Robinhood", kind="broker")
def _robinhood():
    """Read-only positions via the maintained robin_stocks library (no hand-rolled
    auth). Credentials come from the environment the user already exported —
    ROBINHOOD_USERNAME / ROBINHOOD_PASSWORD, plus ROBINHOOD_TOTP (the TOTP secret,
    if 2FA is on) so login is headless. Never prompts, never stores a password."""
    def _creds():
        u = os.environ.get("ROBINHOOD_USERNAME") or os.environ.get("ROBINHOOD_USER")
        p = os.environ.get("ROBINHOOD_PASSWORD") or os.environ.get("ROBINHOOD_PASS")
        return (u, p) if u and p else None

    def detect(ctx):
        import importlib.util
        have_lib = importlib.util.find_spec("robin_stocks") is not None
        have_creds = _creds() is not None
        if have_lib and have_creds:
            return {"found": True, "status": "ready", "detail": "robin_stocks + credentials in environment"}
        if have_creds and not have_lib:
            return {"found": True, "status": "needs_dep",
                    "detail": "ROBINHOOD_* credentials present; robin_stocks not installed",
                    "guidance": "run `worker-placement doctor` to install the bundled connector libs"}
        if have_lib and not have_creds:
            return {"found": True, "status": "needs_key",
                    "detail": "robin_stocks installed; no ROBINHOOD_* credentials in environment",
                    "guidance": "export ROBINHOOD_USERNAME / ROBINHOOD_PASSWORD (+ ROBINHOOD_TOTP if 2FA) — read-only"}
        return {"found": False, "status": "absent",
                "detail": "no robin_stocks and no ROBINHOOD_* credentials",
                "guidance": "pip install robin_stocks and export ROBINHOOD_USERNAME/PASSWORD (+ ROBINHOOD_TOTP)"}

    def fetch(ctx):
        import robin_stocks.robinhood as rh
        u, p = _creds()
        kw = {"store_session": True, "expiresIn": 3600}
        totp = os.environ.get("ROBINHOOD_TOTP")
        code = os.environ.get("ROBINHOOD_MFA")            # a live 6-digit code, if supplied
        if totp:
            try:
                import pyotp
                kw["mfa_code"] = pyotp.TOTP(totp).now()
            except ImportError:
                raise RuntimeError("ROBINHOOD_TOTP set but pyotp not installed — pip install pyotp")
        elif code:
            kw["mfa_code"] = code
        rh.login(u, p, **kw)
        try:
            rows = []
            for sym, h in (rh.build_holdings() or {}).items():   # {sym: {quantity, equity, name, ...}}
                rows.append({"symbol": sym, "qty": float(h.get("quantity") or 0),
                             "value": float(h.get("equity") or 0), "ccy": "USD",
                             "sec_type": "STK", "description": h.get("name") or sym})
            try:                                              # crypto sleeve, if any
                for c in (rh.get_crypto_positions() or []):
                    q = float(c.get("quantity") or 0)
                    code_ = (c.get("currency") or {}).get("code", "")
                    if q <= 0 or not code_:
                        continue
                    quote = rh.get_crypto_quote(code_) or {}
                    px = float(quote.get("mark_price") or 0)
                    rows.append({"symbol": code_, "qty": q, "value": q * px, "ccy": "USD",
                                 "sec_type": "CRYPTO", "description": f"{code_} (crypto)"})
            except Exception:
                pass                                          # equities still import if crypto fails
            return rows
        finally:
            try:
                rh.logout()
            except Exception:
                pass

    return {"detect": detect, "fetch": fetch}


# -------------------------------------------------- positions CSVs already on disk

CSV_SCAN_DIRS = (Path.home() / "Downloads", Path.home() / "Desktop")
CSV_MAX_AGE_DAYS = 45


def _recent_position_csvs():
    hits = []
    cutoff = time.time() - CSV_MAX_AGE_DAYS * 86400
    from officekit.importers import read_positions_csv
    for d in CSV_SCAN_DIRS:
        if not d.is_dir():
            continue
        for f in d.glob("*.csv"):
            try:
                if f.stat().st_mtime < cutoff or f.stat().st_size > 5_000_000:
                    continue
                rows = read_positions_csv(f)         # header sniffer = the intake importer's
                if rows:
                    hits.append((f, len(rows)))
            except Exception:
                continue                             # not a positions export — fine
    hits.sort(key=lambda h: h[0].stat().st_mtime, reverse=True)
    return hits


@adapter("downloads_csv", label="Broker CSV exports on disk", kind="file", auto=False)
def _downloads_csv():
    def detect(ctx):
        hits = _recent_position_csvs()
        if hits:
            names = ", ".join(f.name for f, _ in hits[:3])
            return {"found": True, "status": "ready",
                    "detail": f"{len(hits)} positions export(s) in Downloads/Desktop: {names}"}
        return {"found": False, "status": "absent",
                "detail": f"no positions-shaped CSVs newer than {CSV_MAX_AGE_DAYS}d in Downloads/Desktop"}

    def fetch(ctx):
        hits = _recent_position_csvs()
        if not hits:
            raise RuntimeError("no positions CSV found")
        f, _ = hits[0]                               # newest export wins
        from officekit.importers import read_positions_csv
        return [{"symbol": r.get("symbol", ""), "qty": r.get("qty") or 0,
                 "value": r.get("value") or 0, "description": r.get("description", ""),
                 "account": f.stem[:40]} for r in read_positions_csv(f)]

    return {"detect": detect, "fetch": fetch}


# ------------------------------------------------- detect-only trailheads

def _env_stub(name, label, env_vars, guidance):
    @adapter(name, label=label, kind="broker")
    def _stub():
        def detect(ctx):
            present = [v for v in env_vars if os.environ.get(v)]
            if present:
                return {"found": True, "status": "needs_dep",
                        "detail": f"credentials present ({', '.join(present)}) — fetcher not built yet",
                        "guidance": guidance}
            return {"found": False, "status": "absent",
                    "detail": f"no {'/'.join(env_vars)} in environment", "guidance": guidance}
        return {"detect": detect, "fetch": None}
    return _stub


_env_stub("tradier", "Tradier", ["TRADIER_ACCESS_TOKEN"],
          "REST positions API exists; contribute a fetcher via the adapter contract")
_env_stub("coinbase", "Coinbase", ["COINBASE_API_KEY"],
          "REST accounts API exists; contribute a fetcher via the adapter contract")
_env_stub("kraken", "Kraken", ["KRAKEN_API_KEY"],
          "REST balances API exists; contribute a fetcher via the adapter contract")
_env_stub("snaptrade", "SnapTrade (aggregator)", ["SNAPTRADE_CLIENT_ID"],
          "OAuth aggregator across 20+ brokers — hosted-tier connector work")
_env_stub("plaid", "Plaid Investments (aggregator)", ["PLAID_CLIENT_ID"],
          "OAuth aggregator — hosted-tier connector work")
_env_stub("schwab", "Charles Schwab API", ["SCHWAB_APP_KEY"],
          "official OAuth API — needs an app registration + token flow")
_env_stub("etrade", "E*TRADE", ["ETRADE_CONSUMER_KEY"],
          "official OAuth 1.0a API (accounts/portfolio) — needs the consumer key/secret + token flow")
_env_stub("webull", "Webull", ["WEBULL_USERNAME", "WEBULL_TOKEN"],
          "unofficial API (the `webull` pip package) — contribute a fetcher via the adapter contract")
_env_stub("public", "Public.com", ["PUBLIC_API_KEY", "PUBLIC_TOKEN"],
          "unofficial API — contribute a fetcher via the adapter contract")
_env_stub("binance", "Binance", ["BINANCE_API_KEY"],
          "REST /api/v3/account (read-only key) — HMAC-signed; contribute a fetcher")
_env_stub("gemini", "Gemini", ["GEMINI_API_KEY"],
          "REST /v1/balances (read-only key) — HMAC-signed; contribute a fetcher")
# Consumer brokers without a direct API (Fidelity, Vanguard, Wealthfront, Betterment,
# Merrill) reach the office two supported ways today: a positions-CSV export (the
# downloads_csv adapter) or a SnapTrade/Plaid aggregator link (the stubs above).


@adapter("ghostfolio", label="Ghostfolio (self-hosted)", kind="portfolio_app")
def _ghostfolio():
    def detect(ctx):
        if _port_open("127.0.0.1", 3333):
            return {"found": True, "status": "needs_key",
                    "detail": "Ghostfolio answering on :3333 — fetcher not built yet",
                    "guidance": "its REST API can export holdings; contribute a fetcher"}
        return {"found": False, "status": "absent", "detail": "nothing on :3333"}
    return {"detect": detect, "fetch": None}


# ---------------------------------------- statement-family libraries (compounding)
# Each broker's statement family is a first-class module that self-registers its
# adapter here. Morgan Stanley Prime Brokerage (the Parametric bundles) is first.
from officekit_adapters import morgan_stanley as _morgan_stanley   # noqa: E402
_morgan_stanley.register()
from officekit_adapters import ibkr_flex as _ibkr_flex             # noqa: E402
_ibkr_flex.register()
