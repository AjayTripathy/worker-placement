"""Receipt attribution against existing cash; never a second cash ledger.

Immutable events live in answers alongside their financial state. Reversals keep
the evidence, and imported balances remain owned by their original source.
"""
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import uuid


def dollars(value):
    if isinstance(value, bool):
        raise ValueError("Enter a valid dollar amount")
    try:
        amount = Decimal(str(value).replace(",", "").replace("$", "").strip())
        if not amount.is_finite() or amount < 0 or amount > Decimal("1000000000000"):
            raise ValueError("Amounts must be finite and between zero and one trillion dollars")
        if amount != amount.quantize(Decimal("0.01")):
            raise ValueError("Use at most two decimal places")
        return amount
    except InvalidOperation:
        raise ValueError("Enter a valid dollar amount") from None


def active_receipts(answers):
    events = answers.get("inflow_events") or []
    reversed_ids = {e["reverses"] for e in events if e["kind"] == "reversal"}
    return [e for e in events if e["kind"] == "receipt" and e["id"] not in reversed_ids]


def progress(answers):
    incoming = answers.get("incoming") or {}
    receipts = [e for e in active_receipts(answers) if e["inflow_id"] == incoming.get("id")]
    gross = dollars(incoming.get("amount", 0))
    received = sum((dollars(e["gross"]) for e in receipts), Decimal(0))
    withheld = sum((dollars(e.get("withheld", 0)) for e in receipts), Decimal(0))
    if received > gross:
        raise ValueError("Expected proceeds cannot be less than recorded receipts. Reverse an incorrect receipt first.")
    return {"id": incoming.get("id"), "gross": float(gross), "received": float(received),
            "pending": float(gross - received), "withheld": float(withheld),
            "cash_received": float(received - withheld),
            "status": "received" if gross and received == gross else "partially received" if received else "expected"}


def cash_accounts(answers):
    """Only durable cash sleeves can be selected, using their ID, never a label."""
    result = []
    for s in answers.get("sleeves") or []:
        if s.get("category") != "cash" or not s.get("id"):
            continue
        meta = s.get("meta") or {}
        row = meta.get("custody_row") or {}
        result.append({"id": s["id"], "name": s.get("name") or "Cash",
                       "balance": float(s["value"]),
                       "account": row.get("account") or s.get("name") or "Cash",
                       "source": row.get("source_id") or row.get("source") or "Manual balance",
                       "as_of": (row.get("as_of") or (s.get("sync") or {}).get("as_of")
                                 or answers.get("as_of") or "")[:10],
                       "custody_key": deepcopy(meta.get("custody_key"))})
    return result


def propose(answers, fields, expected_revision, event_id=None):
    from officekit.commitments import revision
    if expected_revision != revision(answers):
        raise ValueError("The office changed. Reload Capital and review the latest balances.")
    updated = deepcopy(answers)
    inc = updated.get("incoming") or {}
    if not inc.get("id") or fields.get("inflow_id") != inc["id"]:
        raise ValueError("This expected inflow no longer exists")
    event = {"id": str(uuid.UUID(event_id)) if event_id else str(uuid.uuid4()),
             "inflow_id": inc["id"], "recorded_at": datetime.now(timezone.utc).isoformat()}
    if any(e["id"] == event["id"] for e in updated.get("inflow_events", [])):
        raise ValueError("This receipt action has already been recorded")
    if fields.get("action") == "reverse":
        original = next((e for e in active_receipts(updated)
                         if e["id"] == fields.get("receipt_id") and e["inflow_id"] == inc["id"]), None)
        if original is None:
            raise ValueError("This receipt is no longer active")
        reason = str(fields.get("reason") or "").strip()
        if not reason or len(reason) > 1000:
            raise ValueError("Enter a correction reason (up to 1,000 characters)")
        event.update(kind="reversal", reverses=original["id"], reason=reason)
    elif fields.get("action") == "receive":
        gross = dollars(fields.get("gross", ""))
        withheld = dollars(fields.get("withheld") or 0)
        if gross <= 0 or withheld > gross:
            raise ValueError("Gross proceeds must be positive and withholding cannot exceed them")
        if gross > dollars(progress(updated)["pending"]):
            raise ValueError("This receipt exceeds the remaining expected proceeds")
        try:
            received_on = date.fromisoformat(str(fields.get("date") or ""))
        except ValueError:
            raise ValueError("Enter a valid receipt date") from None
        if received_on > date.today():
            raise ValueError("A receipt cannot be dated in the future")
        account = next((a for a in cash_accounts(updated) if a["id"] == fields.get("account_id")), None)
        if account is None:
            raise ValueError("Choose an existing cash account; import or update its balance first")
        if not account["as_of"] or account["as_of"] < received_on.isoformat():
            raise ValueError("The selected account balance predates the receipt. Refresh that account first.")
        if fields.get("included") != "yes":
            raise ValueError("Confirm the net deposit is already included in the selected cash balance")
        reference = " ".join(str(fields.get("reference") or "").split())
        if not reference or len(reference) > 240:
            raise ValueError("Enter a statement or transaction reference (up to 240 characters)")
        if any(e["account_id"] == account["id"] and e["reference"].casefold() == reference.casefold()
               for e in active_receipts(updated)):
            raise ValueError("That reference is already linked to a receipt in this account")
        event.update(kind="receipt", gross=float(gross), withheld=float(withheld),
                     date=received_on.isoformat(), account_id=account["id"], reference=reference,
                     evidence=account)
        updated["as_of"] = max(updated["as_of"], received_on.isoformat())
    else:
        raise ValueError("Choose a receipt or correction action")
    updated.setdefault("inflow_events", []).append(event)
    progress(updated)
    return updated
