"""goal_contention — goals compete for ONE shared pool.

Every goal page projects against the whole marketable book, so on their own they
all look funded — but the same dollar can't buy the house AND the Ferrari AND
fund retirement. This models the contention across two shared budgets:

  * CAPITAL — the marketable book. Up-front claims draw it down: a financed
    purchase takes its down-payment-plus-tax, a cash purchase takes the whole
    (grossed-up) price, a liquidity floor reserves cash off the table.
  * ONGOING — what's LEFT of the book sustains at the safe-withdrawal rate
    (minus existing-debt drag). Ongoing claims draw it down: a mortgage/carry, an
    expense, retirement spending.

A set of goals is feasible together only if BOTH budgets hold. The cascade funds
them in list order (the office's priority for now) and marks who gets squeezed.

    contention(m, goals) -> {feasible, capital_*, ongoing_*, cascade, verdict}
"""
from __future__ import annotations

from officekit.goals import SWR
from officekit.goal_projection import (_afford_for_price, _existing_debt_service, _ltcg_rate,
                                       _marketable, _params, is_financed_purchase)


def claims(goal, m):
    """{capital, carry, reserve} — what this goal draws from the shared pools."""
    kind = goal.get("kind")
    if kind == "tax_efficiency":
        return {"capital": 0.0, "carry": 0.0, "reserve": False, "how": "ongoing objective — no claim"}
    if kind == "liquidity_floor":
        amt = float(goal.get("amount") or 0)
        return {"capital": amt, "carry": 0.0, "reserve": True, "how": f"reserves {amt:,.0f} in cash"}
    if kind == "expense":
        c = float(goal.get("annual_amount", goal.get("amount", 0)) or 0)
        return {"capital": 0.0, "carry": c, "reserve": False, "how": "ongoing annual drag"}
    if kind == "retirement":
        from officekit.commitments import retirement_covered_spending
        c = float(goal.get("annual_spending") or 0)
        covered = min(c, retirement_covered_spending(goal, m))
        return {"capital": 0.0, "carry": c - covered, "reserve": False,
                "how": f"annual spending above {covered:,.0f} already reserved for lifestyle"}
    if kind == "spending":
        price = float(goal.get("amount") or 0)
        if is_financed_purchase(goal):
            fin, car = _params(goal, m)
            a = _afford_for_price(price, m, fin, car)
            return {"capital": a["gross_liquidation"], "carry": a["annual_carry"], "reserve": False,
                    "how": "down payment (+tax) up front, mortgage carry ongoing"}
        # a cash purchase: grossed up for the tax to raise it from low-basis equity
        haircut = min(0.95, 0.5 * _ltcg_rate(m))
        return {"capital": price / (1 - haircut), "carry": 0.0, "reserve": False,
                "how": "paid in cash (grossed up for capital-gains tax)"}
    return {"capital": 0.0, "carry": 0.0, "reserve": False, "how": ""}


def contention(m, goals):
    """Fund the DISCRETIONARY goals against the shared capital + ongoing budgets,
    in list order.

    Fixed commitments the balance sheet implies (mortgage service, and lifestyle
    spending once decumulating) are the first call on the budget — they're folded
    into the sustainable figure via `_existing_debt_service`, not cascaded here."""
    goals = [g for g in (goals or [])
             if g.get("kind") != "tax_efficiency" and not g.get("implicit")]
    pool = _marketable(m)
    existing = _existing_debt_service(m)
    cl = [(g, claims(g, m)) for g in goals]
    from officekit.commitments import household_retirement
    household_claim = 0.0
    for g, claim in cl:
        if household_retirement(g):
            needed = claim["carry"]
            claim["carry"] = max(0, needed - household_claim)
            household_claim = max(household_claim, needed)
    total_capital = sum(c["capital"] for _, c in cl)
    remaining_capital = pool - total_capital
    sustainable = max(remaining_capital, 0) * SWR - existing
    total_carry = sum(c["carry"] for _, c in cl)

    # cascade: fund capital claims in order, then ongoing claims from what's left
    run_cap = pool
    cascade = []
    for g, c in cl:
        cap_ok = c["capital"] <= run_cap + 1e-6
        if cap_ok:
            run_cap -= c["capital"]
        cascade.append({"goal": g, "claim": c, "cap_ok": cap_ok, "cap_after": run_cap})
    run_carry = max(run_cap, 0) * SWR - existing
    carry_budget = run_carry
    for e in cascade:
        c = e["claim"]
        carry_ok = c["carry"] <= run_carry + 1e-6
        if carry_ok:
            run_carry -= c["carry"]
        e["carry_ok"] = carry_ok
        e["carry_after"] = run_carry
        e["feasible"] = e["cap_ok"] and carry_ok

    feasible = remaining_capital >= -1e-6 and sustainable >= total_carry - 1e-6
    squeezed = [e["goal"].get("label") or e["goal"].get("kind") for e in cascade if not e["feasible"]]
    if feasible:
        verdict = "these goals fit together on the current book"
    elif remaining_capital < 0:
        verdict = (f"the up-front cost of these goals (~{_m(total_capital)}) exceeds your "
                   f"~{_m(pool)} marketable book — they can't all be bought")
    else:
        verdict = (f"the ongoing cost (~{_m(total_carry)}/yr) exceeds the ~{_m(carry_budget)}/yr "
                   f"the book sustains after the purchases — squeezed out: {', '.join(squeezed)}")
    return {"feasible": feasible, "capital_pool": pool, "capital_claim": total_capital,
            "capital_remaining": remaining_capital, "sustainable": sustainable,
            "carry_claim": total_carry, "carry_budget": carry_budget, "existing_service": existing,
            "cascade": cascade, "squeezed": squeezed, "verdict": verdict, "n": len(cl)}


def _m(x):
    x = float(x or 0)
    sign = "-" if x < 0 else ""
    x = abs(x)
    return f"{sign}${x/1e6:.2f}M" if x >= 1e6 else f"{sign}${x/1e3:.0f}k"
