"""ibkr_flex — IBKR Flex Web Service importer with LOT-LEVEL cost basis.

The socket / Client-Portal adapters give position-level BLENDED average cost, so
a harvest can only say "this symbol is underwater" — it can't split the loss into
long-term vs short-term, and it can't harvest one losing lot while leaving a
winning lot untouched. A Flex Query with the Open Positions section at
`levelOfDetail=LOT` reports every open lot: its open date, its own cost basis and
market value, and IBKR's own base-currency FX rate. That is the only IBKR path to
REAL lot-level harvesting (LT/ST split, per-lot selection).

Setup (once, by the principal — read-only, no trading scope):
  IBKR Account Management -> Reports -> Flex Queries -> Activity Flex Query
    * Sections: Open Positions, with "Lots" / level of detail = Lot
    * fields incl. symbol, position, costBasisMoney, positionValue,
      fifoPnlUnrealized, openDateTime, holdingPeriodDateTime, assetCategory,
      putCall, strike, expiry, multiplier, fxRateToBase, currency
  Reports -> Settings -> Flex Web Service: enable, copy the token.
Then export:  IBKR_FLEX_TOKEN=...  IBKR_FLEX_QUERY_ID=...   (env, never committed)

Two-step web service: SendRequest -> ReferenceCode -> GetStatement (poll until
the statement is generated). Parsing is split out and pure so it is unit-tested
offline against a sample statement — no network, no creds.
"""
from __future__ import annotations

import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime

FLEX_BASE = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"


# --------------------------------------------------------------------- parsing
def _num(x, default=0.0):
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return default


def _parse_dt(s):
    """Flex dates arrive as 'YYYYMMDD', 'YYYYMMDD;HHMMSS', or 'YYYY-MM-DD'."""
    if not s:
        return None
    s = str(s).split(";")[0].split(" ")[0].replace("-", "")
    if len(s) < 8 or not s[:8].isdigit():
        return None
    try:
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except ValueError:
        return None


def _term(open_dt, as_of):
    """Long-term if held > 1 year at the reference date (the harvest-relevant
    federal split). Unknown open date -> ST (the conservative, higher-tax bucket)."""
    if not open_dt:
        return "ST"
    ref = as_of or date.today()
    days = (ref - open_dt).days
    return "LT" if days > 365 else "ST"


_SEC = {"STK": "STK", "OPT": "OPT", "FOP": "FOP", "FUT": "FUT", "CASH": "CASH",
        "BOND": "BOND", "FUND": "FUND", "ETF": "ETF", "CFD": "CFD"}


def _lot_elements(root):
    """Every lot row, whether the query emits flat OpenPosition rows at
    levelOfDetail=LOT or nests <Lot> children under a SUMMARY OpenPosition."""
    lots, nested = [], []
    for op in root.iter("OpenPosition"):
        lvl = (op.get("levelOfDetail") or "").upper()
        kids = op.findall("Lot")
        if kids:
            nested.extend(kids)
        elif lvl == "LOT" or lvl == "":
            lots.append(op)
        # a SUMMARY row with no Lot children is skipped only if LOT rows exist;
        # handled below by falling back when we found nothing lot-level.
    lots.extend(nested)
    if lots:
        return lots
    # no lot detail at all -> treat each SUMMARY OpenPosition as one blended lot
    return [op for op in root.iter("OpenPosition")]


def parse_flex_positions(xml_text, as_of=None, base="USD"):
    """Parse a Flex statement into per-symbol position rows carrying real lots.

    Returns rows shaped for the adapter contract, each already in BASE currency
    (via IBKR's own fxRateToBase), so convert_to_base is a no-op:
        {symbol, qty, value, cost_basis, unrealized_pnl, ccy=base, sec_type,
         account, description, lots:[...], loss_lt, loss_st}
    loss_lt / loss_st are the harvestable (underwater) loss in each tax bucket.
    """
    if isinstance(as_of, str):
        as_of = _parse_dt(as_of)
    root = ET.fromstring(xml_text)

    # a Warn/Fail envelope (statement not ready / bad query) has no positions
    status = root.findtext(".//Status")
    if status and status.lower() in ("warn", "fail"):
        code = root.findtext(".//ErrorCode") or "?"
        msg = root.findtext(".//ErrorMessage") or "statement not available"
        raise RuntimeError(f"Flex {status} {code}: {msg}")

    agg = {}   # (account, symbol) -> row
    for el in _lot_elements(root):
        sym = (el.get("symbol") or el.get("underlyingSymbol") or "").strip().upper()
        if not sym:
            continue
        acct = el.get("accountId") or "brokerage"
        ccy = (el.get("currency") or base).upper()
        fx = _num(el.get("fxRateToBase"), 1.0) or 1.0
        qty = _num(el.get("position"))
        cost = _num(el.get("costBasisMoney")) * fx
        val = _num(el.get("positionValue")) * fx
        # prefer the explicit unrealized field; else derive it
        pnl_raw = el.get("fifoPnlUnrealized")
        pnl = (_num(pnl_raw) * fx) if pnl_raw not in (None, "") else round(val - cost, 2)
        open_dt = _parse_dt(el.get("openDateTime") or el.get("holdingPeriodDateTime"))
        term = _term(open_dt, as_of)
        sec = _SEC.get((el.get("assetCategory") or "STK").upper(), "STK")

        k = (acct, sym)
        row = agg.get(k)
        if row is None:
            row = {"symbol": sym, "qty": 0.0, "value": 0.0, "cost_basis": 0.0,
                   "unrealized_pnl": 0.0, "ccy": base, "sec_type": sec,
                   "account": acct, "description": el.get("description") or sym,
                   "lots": [], "loss_lt": 0.0, "loss_st": 0.0}
            # option terms (so short-put / covered-call summaries still work)
            if sec in ("OPT", "FOP"):
                pc = (el.get("putCall") or "").upper()[:1]
                if pc:
                    row["right"] = pc
                row["strike"] = _num(el.get("strike"))
                row["multiplier"] = _num(el.get("multiplier"), 100) or 100
            agg[k] = row
        row["qty"] += qty
        row["value"] = round(row["value"] + val, 2)
        row["cost_basis"] = round(row["cost_basis"] + cost, 2)
        row["unrealized_pnl"] = round(row["unrealized_pnl"] + pnl, 2)
        loss = cost - val
        lot = {"qty": qty, "cost": round(cost, 2), "value": round(val, 2),
               "open": open_dt.isoformat() if open_dt else None, "term": term,
               "loss": round(loss, 2) if loss > 0 else 0.0}
        row["lots"].append(lot)
        if loss > 0:                                   # only underwater lots are harvestable
            if term == "LT":
                row["loss_lt"] = round(row["loss_lt"] + loss, 2)
            else:
                row["loss_st"] = round(row["loss_st"] + loss, 2)

    return list(agg.values())


# --------------------------------------------------------------------- network
def _http_get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "worker-placement/flex"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def fetch_flex(token, query_id, as_of=None, tries=8, wait=3.0, timeout=20):
    """Run the two-step Flex Web Service and return parsed position rows.
    Step 1 SendRequest -> ReferenceCode + Url; step 2 poll GetStatement until the
    statement is generated (IBKR returns Warn 1019 'not yet ready' meanwhile)."""
    q = urllib.parse.urlencode({"t": token, "q": query_id, "v": "3"})
    sr = _http_get(f"{FLEX_BASE}/SendRequest?{q}", timeout=timeout)
    root = ET.fromstring(sr)
    if (root.findtext("Status") or "").lower() != "success":
        code = root.findtext("ErrorCode") or "?"
        raise RuntimeError(f"Flex SendRequest failed {code}: {root.findtext('ErrorMessage') or sr[:200]}")
    ref = root.findtext("ReferenceCode")
    url = root.findtext("Url") or f"{FLEX_BASE}/GetStatement"

    last = ""
    for _ in range(tries):
        gq = urllib.parse.urlencode({"t": token, "q": ref, "v": "3"})
        last = _http_get(f"{url}?{gq}", timeout=timeout)
        # a "not ready yet" envelope is a small FlexStatementResponse with Warn 1019
        if "<FlexStatementResponse" in last[:200] and "Warn" in last[:400]:
            time.sleep(wait)
            continue
        return parse_flex_positions(last, as_of=as_of)
    # ran out of polls — surface whatever IBKR last said
    raise RuntimeError(f"Flex statement not ready after {tries} polls: {last[:200]}")


# -------------------------------------------------------------------- register
def register():
    """Register the Flex importer as a first-class adapter (called at package
    import; a function so tests can register into a fresh registry)."""
    from officekit_adapters import adapter

    @adapter("ibkr_flex", label="Interactive Brokers — Flex Query (lot-level basis)",
             kind="broker")
    def _flex():
        def _creds():
            return (os.environ.get("IBKR_FLEX_TOKEN"),
                    os.environ.get("IBKR_FLEX_QUERY_ID"))

        def detect(ctx):
            tok, qid = _creds()
            if tok and qid:
                return {"found": True, "status": "ready",
                        "detail": "Flex token + query id present — lot-level basis available"}
            missing = ", ".join(n for n, v in
                                (("IBKR_FLEX_TOKEN", tok), ("IBKR_FLEX_QUERY_ID", qid)) if not v)
            return {"found": False, "status": "needs_key",
                    "detail": f"missing {missing}",
                    "guidance": "IBKR Account Mgmt -> Reports -> Flex Queries: build an "
                                "Activity query with Open Positions at level-of-detail LOT, "
                                "enable the Flex Web Service, then export IBKR_FLEX_TOKEN + "
                                "IBKR_FLEX_QUERY_ID (read-only; the true LT/ST harvest surface)"}

        def fetch(ctx):
            tok, qid = _creds()
            if not (tok and qid):
                raise RuntimeError("IBKR_FLEX_TOKEN / IBKR_FLEX_QUERY_ID not set")
            return fetch_flex(tok, qid, as_of=(ctx or {}).get("as_of"))

        return {"detect": detect, "fetch": fetch}

    return _flex
