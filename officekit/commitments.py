"""Durable commitment edits and a conservative, nominal cash calendar.

Answers store user facts/overrides; resolved commitments are rebuilt projections.
Derived IDs follow assets, never list positions. Proposals are bounded patches
with an office revision, so accepting an old preview cannot overwrite new facts.
"""
from __future__ import annotations

import calendar
import copy
from datetime import date
import hashlib
import json
import math
import uuid

LIFESTYLE = "implicit:spending:lifestyle"
SOURCES = {"recurring_expense", "tax", "capital_call", "goal_reservation"}
CADENCES = {"monthly": 12, "quarterly": 4, "annual": 1, "once": 0}
COMMON = {"funding_source", "cadence", "next_due", "ends_on"}


def add_months(day, months, payment_day=None):
    n = day.year * 12 + day.month - 1 + months
    year, month = divmod(n, 12)
    month += 1
    return date(year, month, min(payment_day or day.day, calendar.monthrange(year, month)[1]))


def prepare_answers(answers, as_of):
    if answers.get("incoming"):
        answers["incoming"].setdefault("id", str(uuid.uuid4()))
    for g in answers.get("goals") or []:
        if g.get("kind") == "retirement":
            g.setdefault("spending_basis", "household_total")
            if g["spending_basis"] not in {"household_total", "additional"}:
                raise ValueError("Retirement spending must be a household total or additional spending")
    for s in answers.get("sleeves") or []:
        s.setdefault("id", str(uuid.uuid4()))
        if s.get("category") == "real_estate_debt":
            s.setdefault("terms_as_of", (s.get("meta") or {}).get("terms_as_of") or as_of)
    # Narrow compatibility migration: the old confirmation button emitted this
    # exact label. Other expense/retirement goals never replace lifestyle.
    for g in list(answers.get("goals") or []):
        if g.get("kind") == "expense" and g.get("label") == "Lifestyle spending":
            records = answers.setdefault("commitments", [])
            if not any(c.get("id") == LIFESTYLE for c in records):
                records.append({"id": LIFESTYLE, "annual_amount": g.get("annual_amount", 0),
                                "provenance": "legacy lifestyle confirmation", "legacy_goal_id": g.get("id")})
            answers["goals"].remove(g)


def revision(answers):
    return hashlib.sha256(json.dumps(answers, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def household_retirement(goal):
    return goal.get("kind") == "retirement" and goal.get("spending_basis", "household_total") == "household_total"


def reconcile_retirement_lifestyle(c, data):
    """A current retirement target supersedes the statistical lifestyle estimate.

    Actual confirmed lifestyle remains authoritative. Several household targets
    describe the same spending pool; use the largest, never their sum. Future
    targets only claim their incremental requirement in the goal planner.
    """
    if c.get("source") != "lifestyle" or "annual_amount" not in c.get("missing", []):
        return
    if not (data.get("profile") or {}).get("decumulating"):
        return
    targets = [g for g in data.get("goals", []) if household_retirement(g)
               and float(g.get("annual_spending") or 0) > 0
               and (not g.get("date") or g["date"][:10] <= data["as_of"])]
    if not targets:
        return
    c["annual_amount"] = max(float(g["annual_spending"]) for g in targets)
    c["retirement_goal_ids"] = [g.get("id") for g in targets]
    c["assumptions"] = [{"field": "annual_amount", "value": c["annual_amount"], "assumed": True,
                         "why": "using your current retirement spending target in place of the statistical lifestyle estimate; confirm actual spending when known"}]


def retirement_covered_spending(goal, m):
    """The part of a household retirement target already reserved as lifestyle."""
    if not household_retirement(goal):
        return 0.0
    data = m.get("d") or {}
    return sum(float(c.get("annual_amount") or 0) for c in data.get("commitments", data.get("goals", []))
               if c.get("source") == "lifestyle" and c.get("active", True) and c.get("portfolio_funded"))


def resolve(data, overrides):
    from officekit.intuition import implicit_goals
    today = date.fromisoformat(data["as_of"])
    indexed = {}
    for c in overrides:
        if str(c.get('id', '')).startswith('charitable:'):
            raise ValueError('Edit charitable cash reservations from their giving goal.')
        if not c.get("id") or c["id"] in indexed:
            raise ValueError("Commitments need unique, nonempty IDs")
        indexed[c["id"]] = c
    result = []
    for base in implicit_goals(data):
        c = copy.deepcopy(base)
        patch = indexed.get(c["id"], {})
        c["funding_source"] = "portfolio" if c.get("portfolio_funded") else "income"
        c["cadence"] = "monthly"
        next_month = add_months(today.replace(day=1), 1)
        c["next_due"] = (next_month if c["source"] == "mortgage" or today.day != 1 else today).isoformat()
        c["schedule_estimated"] = "next_due" not in patch
        c["funding_estimated"] = "funding_source" not in patch
        c.update({k: v for k, v in patch.items() if k in COMMON or k == "annual_amount"})
        if "annual_amount" in patch:
            c["missing"] = [x for x in c.get("missing", []) if x not in ("annual_amount", "rate_pct")]
            c["assumptions"] = [a for a in c.get("assumptions", []) if a["field"] not in ("annual_amount", "rate_pct")]
        reconcile_retirement_lifestyle(c, data)
        matured = c["source"] == "mortgage" and c.get("ends_on", "9999") <= today.isoformat()
        if matured:
            # A contractual payoff date does not forgive a still-recorded loan.
            # Keep that principal due until the balance or remaining term is updated.
            c["cadence"] = "once"
            c["next_due"] = today.isoformat()
            c["amount"] = c["facts"]["balance"]
            c["annual_amount"] = None
            c["ends_on"] = ""
            c["missing"] = ["term_years"]
            c["assumptions"] = [{"field": "term_years", "why": "Recorded payoff date has passed; outstanding principal remains due. Update the balance or remaining term."}]
        else:
            c["amount"] = round(c["annual_amount"] / CADENCES[c["cadence"]], 2)
        c["status"] = "estimated" if c.get("missing") else "confirmed"
        c["estimated"] = c["status"] == "estimated"
        c["portfolio_funded"] = c["funding_source"] == "portfolio"
        c["provenance"] = patch.get("provenance") or ("user terms" if not c["estimated"] else "balance-sheet estimate")
        c["active"] = not c.get("ends_on") or c["ends_on"] >= today.isoformat()
        if c["active"] and c.get("ends_on") and c["next_due"] > c["ends_on"]:
            raise ValueError("The next payment falls after the final payment date")
        result.append(c)
    for raw in overrides:
        if raw.get("source") not in SOURCES:
            continue
        c = copy.deepcopy(raw)
        c["status"] = "confirmed"
        c["estimated"] = False
        c["portfolio_funded"] = c["funding_source"] == "portfolio"
        c["active"] = not c.get("settled") and (not c.get("ends_on") or c["ends_on"] >= today.isoformat())
        if c["cadence"] != "once":
            c["annual_amount"] = c["amount"] * CADENCES[c["cadence"]]
        result.append(c)
    from officekit.charitable import reservation
    for goal in data.get('goals', []):
        if goal.get('kind') == 'charitable':
            held = reservation(goal)
            if held:
                result.append(held)
    return result


def editable_fields(record):
    src = record["source"]
    if src == "mortgage":
        return (COMMON - {"ends_on"}) | {"rate_pct", "term_years"}
    if src == "property_tax":
        return COMMON | {"home_value", "annual_amount"}
    if src == "lifestyle":
        return COMMON | {"annual_amount"}
    return COMMON | {"label", "amount", "settled"}


def edit_values(record):
    facts = record.get("facts") or {}
    return {k: record.get(k, facts.get(k, "")) for k in sorted(editable_fields(record))}


def validate_patch(record, patch):
    if record.get('goal_id') and record['id'].startswith('charitable:'):
        raise ValueError('Edit this cash reservation from its charitable goal.')
    if not isinstance(patch, dict) or not patch:
        raise ValueError("Enter at least one change")
    if set(patch) - editable_fields(record):
        raise ValueError("This edit contains fields that do not belong to the selected commitment")
    clean = {}
    for key, value in patch.items():
        if key in {"annual_amount", "amount", "home_value", "rate_pct", "term_years"}:
            if isinstance(value, bool):
                raise ValueError(f"Invalid {key}")
            try:
                value = float(str(value).replace(",", "").replace("$", "").strip())
            except (ValueError, TypeError):
                raise ValueError(f"Enter a number for {key}") from None
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{key} must be a finite, nonnegative number")
            if key == "rate_pct" and value > 100:
                raise ValueError("Rate must be between 0 and 100 percent")
            if key == "term_years" and not 1 / 12 <= value <= 50:
                raise ValueError("Remaining term must be between one month and 50 years")
            if key == "home_value" and value == 0:
                raise ValueError("Home value must be positive")
            if key in {"annual_amount", "amount", "home_value"}:
                if value > 1e15:
                    raise ValueError("Amount is outside the supported range")
                value = round(value, 2)
        elif key in {"next_due", "ends_on"}:
            if value or key == "next_due":
                value = date.fromisoformat(str(value)).isoformat()
            else:
                value = ""
        elif key == "funding_source" and value not in {"portfolio", "income"}:
            raise ValueError("Choose portfolio or income funding")
        elif key == "cadence":
            if value not in CADENCES or (value == "once" and record["source"] not in SOURCES):
                raise ValueError("Choose a valid payment frequency")
            if record["source"] == "mortgage" and value != "monthly":
                raise ValueError("This mortgage model uses monthly amortization")
            if record["source"] in {"tax", "capital_call", "goal_reservation"} and value != "once":
                raise ValueError("This obligation requires a one-time payment")
        elif key == "settled":
            if value not in (True, False, "true", "false"):
                raise ValueError("Choose whether this obligation is settled")
            value = value in (True, "true")
        elif key == "label":
            value = str(value).strip()
            if not value or len(value) > 160:
                raise ValueError("Enter a label of 1–160 characters")
        clean[key] = value
    merged = dict(record, **clean)
    if merged.get("ends_on") and merged["ends_on"] < merged.get("next_due", ""):
        raise ValueError("End date cannot be before the next payment")
    return clean


def apply_edit(answers, commitment_id, patch, expected_revision):
    if expected_revision != revision(answers):
        raise ValueError("The office changed since this page was loaded. Reload and review the latest values.")
    from officekit.intake import build_from_answers
    updated = copy.deepcopy(answers)
    data = build_from_answers(updated)
    record = next((c for c in data["commitments"] if c["id"] == commitment_id), None)
    if record is None:
        raise ValueError("This commitment no longer exists")
    clean = validate_patch(record, patch)
    records = updated.setdefault("commitments", [])
    override = next((c for c in records if c["id"] == commitment_id), None)
    if override is None:
        override = {"id": commitment_id}
        records.append(override)
    if record["source"] in {"mortgage", "property_tax"}:
        sleeve = next((s for s in updated["sleeves"] if s["id"] == record.get("sleeve_id")), None)
        if record["source"] == "mortgage":
            if sleeve is None:
                raise ValueError("The mortgage asset is no longer present")
            for field in ("rate_pct", "term_years"):
                if field in clean:
                    sleeve[field] = clean.pop(field)
            if "term_years" in patch:
                sleeve["terms_as_of"] = data["as_of"]
        elif "home_value" in clean:
            if sleeve is None:
                # The inferred-home card keeps its ID when it becomes a real
                # asset, making retries/edits idempotent rather than additive.
                sleeve = {"id": str(uuid.uuid4()), "name": "Primary residence", "category": "real_estate",
                          "property_tax_id": commitment_id}
                updated["sleeves"].append(sleeve)
            sleeve["value"] = clean.pop("home_value")
    override.update(clean)
    override["provenance"] = "user confirmed"
    build_from_answers(updated)  # cross-field validation after changed terms/value
    return updated


def add_commitment(answers, fields, expected_revision):
    if expected_revision != revision(answers):
        raise ValueError("The office changed. Reload before adding this commitment.")
    source = fields.get("source")
    if source not in SOURCES:
        raise ValueError("Choose an expense, tax, capital call, or goal reservation")
    record = {"id": str(uuid.uuid4()), "source": source, "provenance": "user confirmed"}
    required = {"label", "amount", "cadence", "next_due", "funding_source"}
    if not required <= set(fields):
        raise ValueError("Provide label, amount, frequency, next payment and funding source")
    record.update(validate_patch(record, {k: v for k, v in fields.items() if k != "source"}))
    if source in {"capital_call", "goal_reservation", "tax"} and record["cadence"] != "once":
        raise ValueError("Enter this dated obligation as a one-time payment")
    updated = copy.deepcopy(answers)
    updated.setdefault("commitments", []).append(record)
    return updated


def tax_funding(m):
    """Split explicitly linked pending-funded tax from tax requiring current cash.

    Matching amounts or labels are not proof of common origin. Intake gives its
    inflow and tax model the same ID; a received cash sleeve no longer qualifies.
    Keep any excess tax above the linked pending proceeds in current reserves.
    """
    pending = {}
    for s in m["assets"]:
        if s.get("category") == "cash_pending" and s.get("id"):
            pending[s["id"]] = pending.get(s["id"], 0) + max(0, float(s.get("value") or 0))
    current, contingent = 0.0, 0.0
    for s in m["sleeves"]:
        if s.get("category") != "tax_reserve":
            continue
        amount = abs(float(s.get("value") or 0))
        inflow_id = (s.get("meta") or {}).get("inflow_id")
        covered = min(amount, pending.get(inflow_id, 0),
                      max(0, float((s.get("meta") or {}).get("pending_tax", amount))))
        if covered:
            pending[inflow_id] -= covered
        contingent += covered
        current += amount - covered
    return {"current": current, "pending": contingent}


def pending_deployable(m):
    """Only the proceeds still pending, net of the tax still funded by them."""
    pending = sum(float(s["value"]) for s in m["assets"] if s.get("category") == "cash_pending")
    return max(0, pending - tax_funding(m)["pending"])


def cash_calendar(m):
    """Upcoming payments only; no presumed income, sales, returns or pending cash.

    Undated current tax and out-of-window obligations remain ring-fenced.
    Tax explicitly linked to an excluded pending inflow stays with that inflow.
    Goal reservations are earmarks, not additional payments or execution.
    """
    today = date.fromisoformat(m["d"]["as_of"])
    start = today.replace(day=1)
    stop = add_months(start, 12)
    rows = [{"month": add_months(start, i).isoformat()[:7], "payments": [], "outflow": 0.0} for i in range(12)]
    by_month = {r["month"]: r for r in rows}
    cash = sum(float(s.get("value") or 0) for s in m["assets"] if s.get("category") == "cash")
    funding = tax_funding(m)
    tax = funding["current"]
    # Tax payments entered manually schedule the existing reserve first. Excess
    # payments are additional cash needs; the reserve is never subtracted twice.
    scheduled_tax = sum(c["amount"] for c in m["d"].get("commitments", [])
                        if c["source"] == "tax" and c.get("active") and c["portfolio_funded"])
    undated_tax = max(0, tax - scheduled_tax)
    held = undated_tax
    outside = []
    for c in m["d"].get("commitments", []):
        if not c.get("active", True):
            continue
        due = date.fromisoformat(c["next_due"])
        cadence = c["cadence"]
        step = 12 // CADENCES[cadence] if CADENCES[cadence] else 0
        anchor_day = due.day
        while due < today and step:
            due = add_months(due, step, anchor_day)
        overdue = not step and due < today
        if overdue:
            due = today  # remain reserved until explicitly settled/released
        if not step and due >= stop:
            outside.append(c)
            if c["portfolio_funded"]:
                held += c["amount"]
        while today <= due < stop and (not c.get("ends_on") or due.isoformat() <= c["ends_on"]):
            amount = c["amount"]
            if step and c.get("annual_amount") is not None:
                # Allocate residual cents instead of adding a few cents each
                # year by independently rounding every annual/n installment.
                cents, extra = divmod(round(c["annual_amount"] * 100), CADENCES[cadence])
                amount = (cents + ((due.month - 1) // step < extra)) / 100
            payment = {"id": c["id"], "label": c["label"], "date": due.isoformat(), "amount": amount,
                       "funding_source": c["funding_source"], "status": c["status"], "source": c["source"],
                       "schedule_estimated": c.get("schedule_estimated", False)}
            payment["overdue"] = overdue
            row = by_month[due.isoformat()[:7]]
            row["payments"].append(payment)
            if c["portfolio_funded"]:
                row["outflow"] += amount
            if not step:
                break
            due = add_months(due, step, anchor_day)
    running = cash - held
    for row in rows:
        running -= row["outflow"]
        row["remaining"] = round(running, 2)
        row["payments"].sort(key=lambda p: (p["date"], p["label"]))
    total = sum(r["outflow"] for r in rows)
    return {"as_of": today.isoformat(), "cash": cash, "tax_reserve": undated_tax, "held": held,
            "pending_tax_reserve": funding["pending"],
            "outside": outside, "months": rows, "outflow": total, "remaining": round(running, 2),
            "available": max(0, round(running, 2)), "shortfall": max(0, round(-running, 2))}
