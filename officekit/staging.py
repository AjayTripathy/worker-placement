"""staging — the import provenance layer (principal-directed 2026-09-05:
"a page with just the import integrations and their last pull dates; assets
need a source tracking what integration they came from or if their data has
to be manually pulled/refreshed").

One file per office — staging.json — holding every pull that ever fed the
book: which integration or document, when it was pulled, the rows it
contributed, its own stated total (for reconciliation), and whether it
refreshes automatically (a live adapter) or only by hand (a statement upload,
a typed row). merged_rows() is the single reviewable union: deduped per
(account, symbol, instrument) with the freshest source winning, and every
displaced source recorded — overlaps are surfaced, never silently double-counted.
The legacy account-label policy (see specific_account) remains in place for
non-generic labels. Generic/placeholder labels ('brokerage') retain source-scoped
observations through merging, updating, and closure. This does not establish that
two observations represent independent economic ownership.

This file is provenance, not the balance sheet: the office still builds only
from the reviewed form through the same validate gate.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# staging.json is one file behind a multi-threaded server: two concurrent
# imports (a folder POST + an IBKR POST) each read-modify-write it, and without
# a lock the last writer clobbers the other's source (the lost-update race,
# 2026-09-06 — adding a folder and IBKR together dropped the folder). Every
# mutation takes this lock and writes atomically (temp file + os.replace).
_LOCK = threading.RLock()


def _path(folder):
    return Path(folder) / "staging.json"


def _atomic_write(folder, st):
    p = _path(folder)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding='utf-8') as f:
            f.write(json.dumps(st, indent=1))
        for attempt in range(6):
            try:
                os.replace(tmp, p)                    # atomic swap; no torn reads
                break
            except PermissionError as error:
                if getattr(error, 'winerror', None) not in {5, 32, 33} or attempt == 5:
                    raise
                time.sleep(.01 * 2 ** attempt)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# Generic labels do not establish cross-source ownership. Keep their observations
# source-scoped. The existing matching policy for other labels is retained for
# now; a non-generic label is NOT proof that two sources describe one owner.
_GENERIC_ACCOUNTS = {"", "brokerage", "manual", "default", "account", "unknown",
                     "portfolio", "n/a", "na", "none", "?", "—", "-"}


def specific_account(acct):
    """Whether the legacy cross-source account-matching policy applies.

    Ownership inference for matching non-generic labels is deferred. Generic or
    missing labels retain separate observations; this is not proof of independence.
    """
    a = str(acct or "").strip()
    return bool(a) and a.lower() not in _GENERIC_ACCOUNTS


def row_source(row):
    """Source identity in staged rows or persisted account contributions."""
    source = row.get("source_id") or row.get("source") or ""
    return "" if source == "?" else str(source)


def ownership_key(row):
    """Match an existing contribution using the same policy as staged merging."""
    account = str(row.get("account") or "?").strip()
    if specific_account(account):
        return (account, "")
    return (account.lower(), row_source(row))


def load(folder):
    p = _path(folder)
    with _LOCK:
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except FileNotFoundError:
            return {"sources": {}}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def num(x):
    """Coerce any extracted/parsed value to a float — models return "1,234.56",
    "$1,234", "(500)" (accounting negative), None. A bad number must never blow
    up a render (the Vanguard-screenshot bug, 2026-09-06: one string value broke
    the whole office). Unparseable -> 0.0."""
    if isinstance(x, bool):                          # bool is an int subclass; a flag is not money
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    if x is None:
        return 0.0
    s = str(x).strip().replace(",", "").replace("−", "-")
    for sym in ("$", "£", "€", "¥", "₩", "₹", "kr", "CHF", "USD", "GBP", "EUR", "JPY", "KRW"):
        s = s.replace(sym, "")                        # a foreign-denominated value must not zero out
    s = s.strip()
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()%").strip()
    try:
        v = float(s)
    except ValueError:
        return 0.0
    return -v if neg else v


def _clean_row(r):
    """Normalize one row so staging never holds a type that breaks a reader:
    value -> float, symbol -> str, sec_type -> str (default STK), account ->
    str|None. Preserves other fields (description, qty, right, strike, …)."""
    if not isinstance(r, dict):
        return {"symbol": "", "value": 0.0, "sec_type": "STK", "account": None}
    out = dict(r)
    out["value"] = num(r.get("value"))
    out["symbol"] = "" if r.get("symbol") is None else str(r.get("symbol"))
    out["sec_type"] = str(r.get("sec_type") or "STK")
    acct = r.get("account")
    out["account"] = None if acct in (None, "") else str(acct)
    return out


from officekit.office_lock import transaction

@transaction()
def remove_source(folder, source_id):
    """Drop one staged source (a whole import). Locked + atomic like record_pull.
    Returns True if it existed."""
    with _LOCK:
        st = load(folder)
        existed = source_id in st.get("sources", {})
        if existed:
            del st["sources"][source_id]
            _atomic_write(folder, st)
        return existed


@transaction()
def record_pull(folder, source_id, kind, ref, rows, refresh, as_of=None,
                stated_total=None, warnings=None, detail="", snapshot=None):
    """Record one pull. source_id is stable per integration/document (an
    adapter name, an uploaded filename) so a re-pull REPLACES that source's
    rows — the ledger keeps last-pull semantics, history stays in git/backups.
    kind: adapter|upload|manual. refresh: auto|manual."""
    rows = list(rows or [])
    if snapshot is not None:
        validate_snapshot(rows, snapshot, as_of)
    entry = {
        "kind": kind, "ref": ref, "refresh": refresh,
        "pulled_utc": _now(), "as_of": as_of,
        "stated_total": stated_total, "warnings": warnings or [],
        "detail": detail, "rows": [_clean_row(r) for r in rows],
        "snapshot": snapshot or {"mode": "partial"},
    }
    with _LOCK:                                       # read-modify-write is atomic
        st = load(folder)
        previous = st["sources"].get(source_id)
        if previous and as_of and previous.get("as_of") and as_of < previous["as_of"]:
            raise ValueError("stale pull would replace a newer source snapshot")
        st["sources"][source_id] = entry
        _atomic_write(folder, st)
    from officekit.api_errors import clear
    clear(folder, context='import:' + source_id)
    return entry


def validate_snapshot(rows, snapshot, as_of):
    """A complete pull authorizes closure ONLY within its explicit coverage.

    Totals are broker/control totals in the office base currency, covering the
    declared security types. Partial/legacy imports never authorize deletion.
    Validate before replacing the last good pull, including empty snapshots.
    """
    if not isinstance(snapshot, dict) or snapshot.get("mode") not in ("partial", "complete"):
        raise ValueError("snapshot mode must be partial or complete")
    if snapshot["mode"] == "partial":
        return
    accounts = snapshot.get("accounts") or []
    types = snapshot.get("security_types") or []
    totals = snapshot.get("totals") or {}
    if (not isinstance(accounts, list) or not all(isinstance(a, str) and a.strip() for a in accounts)
            or not isinstance(types, list) or not all(isinstance(t, str) and t and t == t.upper() for t in types)
            or not isinstance(totals, dict)):
        raise ValueError("complete coverage requires account and uppercase security-type lists and a totals object")
    if not as_of or not accounts or not types or set(accounts) != set(totals):
        raise ValueError("complete snapshot requires as_of, accounts, security_types and per-account totals")
    datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    sums = dict.fromkeys(accounts, 0.0)
    for r in rows:
        if r.get("account") not in sums or str(r.get("sec_type") or "STK").upper() not in types:
            raise ValueError("row outside complete snapshot coverage")
        value = r.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("complete snapshot requires finite numeric market values")
        if r.get("value_is_cost"):
            raise ValueError("cost-only rows cannot certify a complete market-value snapshot")
        sums[r["account"]] += value
    for account, total in totals.items():
        if isinstance(total, bool) or not isinstance(total, (int, float)) or not math.isfinite(total):
            raise ValueError("account control totals must be finite numbers")
        if abs(sums[account] - total) > 0.011:
            raise ValueError(f"snapshot does not reconcile for account {account}")


@transaction()
def record_failure(folder, source_id, error):
    """Keep the last good rows and coverage; expose the failed refresh attempt."""
    with _LOCK:
        st = load(folder)
        source = st["sources"].setdefault(source_id, {
            "kind": "upload" if source_id.startswith('upload:') else "adapter",
            "ref": source_id.removeprefix('upload:'),
            "refresh": "manual" if source_id.startswith('upload:') else "auto",
            "pulled_utc": "", "as_of": None, "rows": [], "warnings": [],
        })
        from officekit.api_errors import message
        source["last_error"] = message(error)
        source["last_attempt_utc"] = _now()
        _atomic_write(folder, st)
    from officekit.api_errors import report
    report(folder, 'import:' + source_id, 'Account refresh failed', error,
           href='/pages/imports.html')


def freshness(source):
    return (source.get("as_of") or source.get("pulled_utc") or "",
            source.get("pulled_utc") or "")


def covers(source, row, source_id=None):
    """Coverage must respect the source boundary used when accepting a row.

    An unidentified owner cannot be closed by guessing from a generic label.
    Callers loading the source ledger supply its dictionary key as source_id.
    """
    snap = source.get("snapshot") or {}
    return (snap.get("mode") == "complete"
            and (specific_account(row.get("account"))
                 or bool(source_id and row_source(row) == source_id))
            and row.get("account") in (snap.get("accounts") or [])
            and str(row.get("sec_type") or "STK").upper() in (snap.get("security_types") or []))


def position_key(row):
    """Account + instrument identity, source-scoped for ambiguous accounts.

    Prefer structural option terms over broker-specific contract ids so two
    feeds can identify the same instrument. Cash legs aggregate within a source.
    """
    sec = str(row.get("sec_type") or "STK").upper()
    symbol = str(row.get("symbol") or "").upper()
    contract = ""
    if sec in ("OPT", "FOP"):
        expiry = row.get("expiry") or row.get("expiration") or row.get("lastTradeDateOrContractMonth")
        if expiry and row.get("strike") is not None and row.get("right"):
            contract = f"{expiry}|{num(row['strike']):g}|{row['right']}|{row.get('multiplier') or 100}"
        else:
            contract = str(row.get("description") or row.get("conid") or row.get("conId") or "")
    elif sec == "BOND":
        contract = str(row.get("isin") or row.get("cusip") or row.get("description") or symbol)
    key = (str(row.get("account") or ""), symbol, sec,
           str(row.get("ccy") or ""), contract)
    # Keep existing specific-account keys stable. Ambiguous accounts need the
    # source suffix so cash/options/bonds retain the same isolation as equities.
    return key if specific_account(row.get("account")) else key + (row_source(row),)


def merged_rows(folder):
    """The deduped union across every staged source, freshest-first per symbol.
    Returns (rows, overlaps): each row carries source_id/kind/refresh/pulled;
    overlaps lists {symbol, kept, displaced[]} wherever two sources claimed the
    same symbol — the review surface says so instead of double-counting."""
    st = load(folder)

    ordered = sorted(st["sources"].items(), key=lambda kv: freshness(kv[1]), reverse=True)
    # Dedupe collapses only the SAME holding in the SAME account seen from a
    # DIFFERENT source (a live feed superseding that account's stale statement).
    # It must NEVER collapse: (a) two lines within one source — a statement's
    # two USD cash legs are distinct, not duplicates (the Parametric $2.7M bug,
    # 2026-09-06); (b) a ticker held in two different accounts (IBKR + a
    # Parametric SMA both hold AAPL — that is 2x the exposure, not a dup).
    # No reliable account identity -> keep the row, never drop value silently.
    out, seen, overlaps, complete = [], {}, {}, []
    for sid, s in ordered:
        src_keys = set()                             # keys this source itself contributed
        for r in s["rows"]:
            row = {**r, "source_id": sid, "source_kind": s["kind"],
                   "refresh": s["refresh"], "pulled_utc": s["pulled_utc"],
                   "as_of": s.get("as_of")}
            # A newer complete snapshot supersedes an older statement even
            # when the old position has disappeared (sale/expiry/transfer).
            superseding = next((csid for csid, src in complete if covers(src, row, csid)), None)
            if superseding:
                overlaps.setdefault(str(r.get("symbol", "")), {
                    "symbol": str(r.get("symbol", "")), "kept": superseding,
                    "displaced": []})["displaced"].append(sid)
                continue
            sym = str(r.get("symbol", "")).upper()
            acct = str(r.get("account") or "").strip()
            # Generic account labels do not permit cross-source collapse.
            # This covers both a missing account and a generic placeholder ('brokerage',
            # the manual-entry default): two feeds that share such a label are two
            # observations to retain until ownership is established. Do not infer
            # independence from the label; do not silently erase a contribution.
            if not specific_account(acct):
                out.append(row)
                continue
            key = position_key(r)
            if key in seen and key not in src_keys:  # same account, a fresher source had it
                overlaps.setdefault(sym, {"symbol": sym, "kept": seen[key],
                                          "displaced": []})["displaced"].append(sid)
                continue
            seen[key] = sid
            src_keys.add(key)
            out.append(row)
        if (s.get("snapshot") or {}).get("mode") == "complete":
            complete.append((sid, s))
    return out, sorted(overlaps.values(), key=lambda o: o["symbol"])


def source_of(folder, symbol):
    """Trace one asset: which source supplies it (dedupe winner), or None —
    None means the datum was typed/managed by hand and refreshes only when a
    human refreshes it."""
    subs = sources_of(folder, symbol)
    return subs[0] if subs else None


def sources_of(folder, symbol):
    """Every source that supplies an asset, with each one's value — an asset can
    span accounts (IBKR + a Parametric SMA both hold AAPL). Returns a list (most
    valuable first) with a combined total on each entry; empty if untraced."""
    rows, _ = merged_rows(folder)
    sym = str(symbol).upper()
    hits = [r for r in rows if str(r.get("symbol", "")).upper() == sym]
    total = sum(num(r.get("value")) for r in hits)
    out = [{"source_id": r.get("source_id"), "source_kind": r.get("source_kind"),
            "refresh": r.get("refresh"), "pulled_utc": r.get("pulled_utc"),
            "as_of": r.get("as_of"), "account": r.get("account"),
            "value": num(r.get("value")), "asset_total": total}
           for r in hits]
    return sorted(out, key=lambda x: -abs(x["value"]))


def ledger(folder):
    """The audit view: one line per source — integration/document, kind,
    refresh mode, last pull, row count, as-of, reconciliation warnings."""
    st = load(folder)
    out = []
    for sid, s in sorted(st["sources"].items(),
                         key=lambda kv: kv[1].get("pulled_utc") or "", reverse=True):
        out.append({"source_id": sid, "kind": s["kind"], "ref": s["ref"],
                    "refresh": s["refresh"], "pulled_utc": s["pulled_utc"],
                    "as_of": s.get("as_of"), "n_rows": len(s.get("rows") or []),
                    "stated_total": s.get("stated_total"),
                    "warnings": (s.get("warnings") or []) +
                                (["Last refresh failed: " + s["last_error"]] if s.get("last_error") else []),
                    "snapshot": s.get("snapshot") or {"mode": "partial"},
                    "detail": s.get("detail", "")})
    return out
