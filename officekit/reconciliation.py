"""Reconcile scoped custody snapshots without deleting unconnected assets.

Complete coverage is an explicit adapter assertion, validated by staging against
independent account control totals. Legacy pulls are partial. Ownership metadata
is required for closures; an unowned manual sleeve is never silently adopted.
This module is pure: callers persist only after the resulting office renders.
"""
from __future__ import annotations

from copy import deepcopy
from collections import defaultdict

from officekit.staging import covers, freshness, num, ownership_key, position_key, row_source

EQUITIES = {"STK", "ETF", "FUND", "US_EQUITY", "ADR"}
OTHER = {"CASH": "cash", "OPT": "options_overlay", "FOP": "options_overlay",
         "BOND": "fixed_income", "BILL": "fixed_income", "NOTE": "fixed_income",
         "TBOND": "fixed_income", "TBILL": "fixed_income", "FIXED": "fixed_income"}


def superseded(row, sources, fallback_date=""):
    old = {"as_of": row.get("as_of") or fallback_date,
           "pulled_utc": row.get("pulled_utc") or ""}
    return any(covers(src, row, sid) and freshness(src) >= freshness(old)
               for sid, src in sources.items())


def reconcile(answers, rows, sources, attach_lots=None):
    result = deepcopy(answers)
    report = {"changed": 0, "added": 0, "removed": 0, "warnings": [], "closed": []}
    bysym = defaultdict(list)
    for row in rows:
        if str(row.get("sec_type") or "STK").upper() in EQUITIES and row.get("symbol"):
            bysym[str(row["symbol"]).upper()].append(row)
    pos = result.setdefault("positions", {"account": "brokerage", "rows": []})
    existing = {str(r.get("symbol") or "").upper(): r for r in pos.get("rows", [])}
    final = []
    for sym in dict.fromkeys([*existing, *bysym]):
        old = existing.get(sym)
        incoming = deepcopy(bysym.get(sym, []))
        if old and not old.get("accounts") and len(incoming) > 1 and any(r.get("value_is_cost") for r in incoming):
            final.append(old)
            report["warnings"].append(f"Ownership review required for {sym}: cannot allocate its market value across cost-only imports")
            continue
        # A stale file in another source must not overwrite a fresher account
        # contribution already owned by the office.
        for account in (old or {}).get("accounts", []):
            same = [r for r in incoming if ownership_key(r) == ownership_key(account)]
            if same and account.get("as_of") and all(freshness(r) < freshness(account) for r in same):
                incoming = [r for r in incoming if r not in same]
                report["warnings"].append(f"Retained newer mark for {sym} in {account.get('account')}")
        for r in list(incoming):
            if r.get("value_is_cost"):
                prior = next((a for a in (old or {}).get("accounts", [])
                              if ownership_key(a) == ownership_key(r)), None)
                if prior:
                    r["value"] = prior["value"]
                elif old and not old.get("accounts") and len(incoming) == 1:
                    r["value"] = old["value"]
                else:
                    incoming.remove(r)
                    report["warnings"].append(f"Market value unavailable for {sym} in {r.get('account')}; cost-only mark ignored")
        incoming_accounts = {ownership_key(r) for r in incoming}
        for account in (old or {}).get("accounts", []):
            if ownership_key(account) in incoming_accounts:
                continue
            prior = {**account, "symbol": sym, "sec_type": account.get("sec_type", "STK"),
                     "source_id": account.get("source")}
            if superseded(prior, sources, answers.get("as_of", "")):
                report["closed"].append({"symbol": sym, "account": prior["account"],
                                         "source": row_source(prior), "security_type": "equity"})
            else:
                incoming.append(prior)
        if not incoming:
            if old and old.get("accounts") and all(
                    superseded({**a, "symbol": sym, "sec_type": a.get("sec_type", "STK")}, sources,
                               answers.get("as_of", "")) for a in old["accounts"]):
                report["removed"] += 1
            elif old:
                final.append(old)
            continue
        current = dict(old or {"symbol": sym})
        accounts = []
        for r in incoming:
            a = {"account": r.get("account") or "?", "source": r.get("source_id") or "?",
                 "value": round(num(r.get("value")), 2)}
            for k in ("sec_type", "cost_basis", "value_is_cost", "as_of", "pulled_utc",
                      "lots", "loss_lt", "loss_st"):
                if r.get(k) is not None:
                    a[k] = r[k]
            accounts.append(a)
        all_cost = all(r.get("value_is_cost") for r in incoming)
        if not all_cost or old is None:
            current["value"] = round(sum(num(r.get("value")) for r in incoming), 2)
        else:
            # Retained market values must remain the values on the ownership
            # records too, otherwise a later partial pull can turn cost into NAV.
            for a in accounts:
                prior = next((p for p in (old or {}).get("accounts", [])
                              if ownership_key(p) == ownership_key(a)), None)
                if prior:
                    a["value"] = prior.get("value", a["value"])
        if all(r.get("cost_basis") is not None for r in incoming):
            current["cost_basis"] = round(sum(num(r.get("cost_basis")) for r in incoming), 2)
        elif len(incoming) > 1 and any(r.get("cost_basis") is not None for r in incoming):
            current.pop("cost_basis", None)
            report["warnings"].append(f"Incomplete cost basis for {sym}; account-level basis retained")
        current["accounts"] = accounts
        primary = dict(max(incoming, key=lambda r: bool(r.get("lots"))))
        if any(r.get("lots") for r in incoming):
            primary["lots"] = [{**lot, "account": r.get("account")} for r in incoming
                               for lot in (r.get("lots") or [])]
        for field in ("loss_lt", "loss_st"):
            if len({r.get("account") for r in incoming}) <= 1:
                continue  # retain legacy best-source lot detail for an unscoped import
            if all(r.get(field) is not None for r in incoming):
                primary[field] = round(sum(num(r[field]) for r in incoming), 2)
            elif len(incoming) > 1:
                primary.pop(field, None)
                current.pop(field, None)
        if attach_lots:
            attach_lots(current, primary)
        final.append(current)
        if old is None:
            report["added"] += 1
        elif current != old:
            report["changed"] += 1
    pos["rows"] = final

    # Cash, fixed income and option marks remain separate sleeves. Only known
    # complete coverage may create them on an existing office; partial refreshes
    # can update already-owned rows. Explicit metadata prevents double booking.
    sleeves = result.setdefault("sleeves", [])
    owned = {}
    for s in sleeves:
        meta = s.get("meta") or {}
        if not meta.get("custody_key"):
            continue
        # Older keys had no source suffix. Recover it from saved provenance;
        # do not guess ownership from an incoming refresh or a display label.
        key = position_key(meta["custody_row"]) if meta.get("custody_row") else tuple(meta["custody_key"])
        meta["custody_key"] = list(key)
        owned[key] = s
    manual = [s for s in sleeves if not (s.get("meta") or {}).get("custody_key")]
    manual_categories = {s["category"] for s in manual}
    other_rows = defaultdict(list)
    for r in rows:
        sec = str(r.get("sec_type") or "STK").upper()
        if sec in EQUITIES:
            continue
        key = position_key(r)
        if key not in owned and not any(covers(src, r, sid) for sid, src in sources.items()):
            continue
        category = OTHER.get(sec)
        if not category:
            report["warnings"].append(f"Unsupported custody instrument {sec}: {r.get('symbol')}; review required")
            continue
        if key not in owned and category in manual_categories:
            report["warnings"].append(
                f"Ownership review required for {r.get('account')} {sec}: existing manual {category} sleeve retained")
            continue
        other_rows[key].append(r)
    for key, rs in other_rows.items():
        first = rs[0]
        s = deepcopy(owned.get(key) or {})
        prior = (s.get("meta") or {}).get("custody_row")
        if prior and all(freshness(r) < freshness(prior) for r in rs):
            report["warnings"].append(f"Retained newer mark for {key[1]} in {key[0]}")
            continue
        if any(r.get("value_is_cost") for r in rs):
            report["warnings"].append(f"Market value unavailable for {key[1]} in {key[0]}; cost-only mark ignored")
            continue
        s.update({"category": OTHER[key[2]], "name": first.get("description") or f"{key[0]} {key[1]}",
                  "value": round(sum(num(r["value"]) for r in rs), 2)})
        s.setdefault("meta", {}).update({"custody_key": list(key), "custody_row": first})
        if key not in owned:
            report["added"] += 1
        elif s != owned[key]:
            report["changed"] += 1
        owned[key] = s
    for key in list(owned):
        if key not in other_rows and superseded(owned[key]["meta"]["custody_row"], sources):
            sleeve_row = owned[key]["meta"]["custody_row"]
            del owned[key]
            report["removed"] += 1
            report["closed"].append({"account": key[0], "symbol": key[1],
                                     "source": row_source(sleeve_row), "security_type": key[2]})
    result["sleeves"] = manual + list(owned.values())
    report["warnings"] = list(dict.fromkeys(report["warnings"]))
    result["reconciliation"] = report
    return result, report
