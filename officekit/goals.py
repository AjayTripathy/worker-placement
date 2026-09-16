"""goals — life-planning goals and their status, today and through the tail.

Phase-2 (principal-ratified 2026-09-02): goals are a first-class Office object —
retirement dates, spending targets, liquidity floors — and the Scenario Planner
answers "what happens to my GOALS in the tail", not just "can I cover my claims".

v1 math is a deliberately CONSERVATIVE no-growth heuristic, and says so on the
page: no return compounding to the goal date, retirement sustainability via a
flat safe-withdrawal rate on post-shock investable net worth. The Quant Desk's
Simulation slot (path/Monte-Carlo) replaces this math later; the statuses here
are a floor, not a forecast.

Goal kinds (v1 — labels carry the semantics, so education/home/philanthropy are
`spending` goals with their own labels):
  retirement       {label, date, annual_spending}
  spending         {label, date?, amount}          # one-time dated target
  liquidity_floor  {label, amount}                 # never dip below this liquid
"""
from __future__ import annotations

from datetime import datetime

from officekit.fmt import fmt_usd as _fmt

# Sample goals — quick-adds for the goals editor. Every sample maps to an
# existing kind (labels carry the meaning, per the ratified ruling: education,
# philanthropy, a sabbatical are all `spending` with a label). Amounts and
# horizons are STARTING POINTS the user edits, never data — a goal only exists
# once the user commits it in their own words.
GOAL_LIB = [
    {"kind": "retirement",      "label": "Retirement",            "hint": "annual spending it must support", "amount": 100000, "years_out": 25},
    {"kind": "liquidity_floor", "label": "Emergency floor",       "hint": "cash you can reach inside a week", "amount": 50000},
    {"kind": "spending",        "label": "College fund",          "hint": "per child; 4-year all-in",         "amount": 300000, "years_out": 12},
    {"kind": "spending",        "label": "Home purchase — down payment", "hint": "20% of the target price",   "amount": 250000, "years_out": 4},
    {"kind": "spending",        "label": "Home renovation",       "hint": "one project, all-in",              "amount": 150000, "years_out": 2},
    {"kind": "spending",        "label": "Wedding",               "hint": "yours or a child's",               "amount": 60000,  "years_out": 3},
    {"kind": "spending",        "label": "Sabbatical year",       "hint": "a year of spending, unpaid",       "amount": 120000, "years_out": 5},
    {"kind": "spending",        "label": "Parents' care reserve", "hint": "eldercare / long-term-care bridge", "amount": 200000, "years_out": 8},
    {"kind": "spending",        "label": "New car",               "hint": "bought in cash",                   "amount": 55000,  "years_out": 3},
    {"kind": "spending",        "label": "Philanthropy — giving fund", "hint": "a DAF seed or pledged gift",  "amount": 100000, "years_out": 5},
    {"kind": "spending",        "label": "Start a business",      "hint": "runway you could lose entirely",   "amount": 150000, "years_out": 4},
    {"kind": "spending",        "label": "Second home",           "hint": "down payment + first-year carry",  "amount": 350000, "years_out": 7},
    {"kind": "spending",        "label": "Health reserve",        "hint": "deductibles / uncovered care",     "amount": 40000},
    {"kind": "spending",        "label": "Big trip",              "hint": "the one you keep postponing",      "amount": 30000,  "years_out": 2},
]

SWR = 0.04            # flat safe-withdrawal heuristic until Simulation lands
OK, TIGHT, SHORT = "OK", "TIGHT", "SHORT"
STATUS_TONE = {OK: "emerald", TIGHT: "amber", SHORT: "coral"}

GOAL_KINDS = {"retirement", "spending", "liquidity_floor"}


def _status(ratio, tight_at=1.0, short_at=0.8):
    if ratio >= tight_at:
        return OK
    return TIGHT if ratio >= short_at else SHORT


def _years_until(date_str, as_of):
    try:
        d1 = datetime.strptime(date_str[:10], "%Y-%m-%d")
        d0 = datetime.strptime(as_of[:10], "%Y-%m-%d")
        return max((d1 - d0).days / 365.25, 0.0)
    except Exception:
        return None


def investable(sleeve_pnls):
    """Post-shock investable net worth: every sleeve at shocked marks EXCEPT the
    primary residence and its debt (you live in it — it doesn't fund goals)."""
    return sum(s["value"] + pnl for s, pnl in sleeve_pnls
               if s["category"] not in ("real_estate", "real_estate_debt"))


def evaluate(goal, nw_inv, liquid, as_of, model=None):
    """One goal against one state of the world -> {status, ratio, detail, ...}.

    nw_inv  = investable net worth (post-shock when stressing)
    liquid  = cash + marketable at shocked marks
    """
    kind = goal["kind"]
    label = goal.get("label") or kind
    if model is not None:
        from officekit.goal_projection import is_financed_purchase, project
        if is_financed_purchase(goal) or kind == "expense":
            p = project(goal, [], as_of, model)
            result = {"label": label, "kind": kind, "ratio": p["ratio"],
                      "status": OK if p["affordable"] else SHORT,
                      "detail": p["verdict"], "assessment": p}
            if p["mode"] == "financed":
                result.update(target_txt=f"{_fmt(p['price'])} purchase",
                              closing_ratio=p["marketable"] / p["cash_needed"] if p["cash_needed"] else 0,
                              carry_ratio=p["ratio"],
                              closing_status=OK if p["marketable"] >= p["cash_needed"] else SHORT)
            else:
                result["target_txt"] = f"{_fmt(p['annual'])}/yr"
            return result
    if kind == "retirement":
        spend = float(goal["annual_spending"])
        sustainable = max(nw_inv, 0.0) * SWR
        fixed_other, covered = 0.0, 0.0
        if model is not None:
            from officekit.commitments import retirement_covered_spending
            from officekit.goal_projection import _existing_debt_service
            covered = retirement_covered_spending(goal, model)
            fixed_other = max(0, _existing_debt_service(model) - covered)
            sustainable -= fixed_other
        ratio = sustainable / spend if spend else 0.0
        yrs = _years_until(goal.get("date", ""), as_of)
        when = f" in {yrs:.0f}y" if yrs is not None else ""
        return {"label": label, "kind": kind, "ratio": ratio, "status": _status(ratio),
                "target_txt": f"{_fmt(spend)}/yr{when}",
                "detail": f"{_fmt(sustainable)}/yr sustainable at {SWR*100:.0f}% of {_fmt(nw_inv)} investable"
                          + (f" after {_fmt(fixed_other)}/yr of other fixed commitments" if fixed_other else "")
                          + (f"; includes {_fmt(covered)}/yr of lifestyle already reserved, counted once" if covered else "")}
    if kind == "liquidity_floor":
        amt = float(goal["amount"])
        ratio = liquid / amt if amt else 0.0
        return {"label": label, "kind": kind, "ratio": ratio,
                "status": _status(ratio, tight_at=1.25, short_at=1.0),
                "target_txt": f"{_fmt(amt)} liquid",
                "detail": f"{_fmt(liquid)} raisable vs the {_fmt(amt)} floor"}
    if kind == "spending":
        amt = float(goal["amount"])
        ratio = liquid / amt if amt else 0.0
        yrs = _years_until(goal.get("date", ""), as_of)
        when = f" in {yrs:.0f}y" if yrs is not None else ""
        return {"label": label, "kind": kind, "ratio": ratio,
                "status": _status(ratio, tight_at=1.5, short_at=1.0),
                "target_txt": f"{_fmt(amt)}{when}",
                "detail": f"{_fmt(liquid)} liquid vs the {_fmt(amt)} target (no-growth check)"}
    if kind == "expense":
        # an ONGOING annual outlay — a permanent drag the portfolio must sustain
        annual = float(goal.get("annual_amount", goal.get("amount", 0)) or 0)
        sustainable = max(nw_inv, 0.0) * SWR
        ratio = sustainable / annual if annual else 0.0
        return {"label": label, "kind": kind, "ratio": ratio,
                "status": _status(ratio, tight_at=1.25, short_at=1.0),
                "target_txt": f"{_fmt(annual)}/yr",
                "detail": f"{_fmt(sustainable)}/yr sustainable at {SWR*100:.0f}% of {_fmt(nw_inv)} — a permanent drag"}
    if kind == "tax_efficiency":
        # an ONGOING objective, not a funding target — no dollar ratio; it's
        # "met" by adopting a lot-level-harvesting strategy, not by a balance
        return {"label": label, "kind": kind, "ratio": 1.0, "status": OK,
                "target_txt": "ongoing", "detail": "harvest losses via a lot-level strategy (direct index)"}
    return {"label": label, "kind": kind, "ratio": 0.0, "status": SHORT,
            "target_txt": "?", "detail": f"unknown goal kind {kind!r}"}


def evaluate_all(goals, nw_inv, liquid, as_of):
    return [evaluate(g, nw_inv, liquid, as_of) for g in goals]


def evaluate_in_model(goal, model, sleeve_pnls=None, effective_goals=None):
    """One assessment for Home, goals, strategy planning and stressed worlds.

    Pending inflows are excluded from money available today. A financed purchase
    must pass both cash-to-close and annual carrying-capacity checks.
    """
    state = model
    if sleeve_pnls is not None:
        state = dict(model)
        state["sleeves"] = [{**s, "value": s["value"] + pnl} for s, pnl in sleeve_pnls]
        state["assets"] = [s for s in state["sleeves"] if s.get("kind") == "asset"]
    if effective_goals is not None:
        state = dict(state)
        state["d"] = dict(state["d"], goals=effective_goals)
        if "commitments" in state["d"]:
            overrides = {g.get("id"): g for g in effective_goals if g.get("implicit")}
            state["d"]["commitments"] = [dict(c, **{
                k: v for k, v in overrides.get(c["id"], {}).items()
                if k in {"annual_amount", "portfolio_funded", "active"}}) for c in state["d"]["commitments"]]
            from officekit.commitments import reconcile_retirement_lifestyle
            for c in state["d"]["commitments"]:
                # Explicit scenario changes to lifestyle win over the linked
                # retirement target, just like confirmed live spending does.
                base = next((b for b in model["d"]["commitments"] if b["id"] == c["id"]), {})
                if c.get("annual_amount") == base.get("annual_amount"):
                    reconcile_retirement_lifestyle(c, state["d"])
    marketable = ("public_equity", "direct_index", "single_name_equity",
                  "municipal_credit", "fixed_income", "alpha_market_neutral")
    liquid = sum(s["value"] * (0.98 if s["category"] in marketable else 1)
                 for s in state["assets"] if s["category"] in (*marketable, "cash"))
    inv = investable([(s, 0) for s in state["sleeves"] if s["category"] != "cash_pending"])
    if effective_goals is not None and goal.get("implicit"):
        resolved = next((c for c in state["d"].get("commitments", []) if c["id"] == goal.get("id")), None)
        if resolved and resolved.get("annual_amount") is not None:
            goal = dict(goal, annual_amount=resolved["annual_amount"])
    return evaluate(goal, inv, liquid, state["d"].get("as_of", ""), model=state)


def goal_key(g):
    """Stable goal ID across variants; (kind, label) for legacy records."""
    return g["id"] if g.get("id") else (g.get("kind"), g.get("label") or g.get("kind"))


def apply_goal_ov(goals, ov):
    """A scenario's effective goal set: base goals + the scenario's goal_ov.
    `modify` patches the first goal of the named kind (absolute fields override;
    *_delta fields add); `add` appends scenario-specific goals. Base list is
    never mutated."""
    if not ov:
        return list(goals)
    out = [dict(g) for g in goals]
    for patch in ov.get("modify", []):
        target = next((g for g in out if g.get("id") == patch["id"]), None) if patch.get("id") else next(
            (g for g in out if g.get("kind") == patch.get("kind") and not g.get("implicit")), None)
        if target is None:
            continue
        for k, v in patch.items():
            if k == "kind":
                continue
            if k.endswith("_delta"):
                base_field = k[:-6]
                target[base_field] = float(target.get(base_field, 0)) + float(v)
            else:
                target[k] = v
    out.extend(dict(g) for g in ov.get("add", []))
    return out
