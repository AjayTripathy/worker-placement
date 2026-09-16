"""goal_projection — can the office actually reach / sustain a goal?

Three honest models, picked by goal kind:

  * lump-sum growth (plain dated target / retirement corpus): serving capital
    grown at a blended expected return until it crosses the target.
  * FINANCED PURCHASE (a home / property): you don't liquidate the whole price —
    you put ~25% down (and pay capital-gains tax to RAISE that down from
    low-basis equity), finance the rest, and CARRY it forever. Affordability is
    then: can you raise the down, and does the post-purchase portfolio sustain
    the annual carrying cost (mortgage P&I + property tax + maintenance +
    insurance) — net of the drag your EXISTING debt already imposes. This is
    what kills the "139% funded" illusion.
  * EXPENSE (an ongoing annual outlay, adjustable): a permanent drag the
    portfolio must sustain at the safe-withdrawal rate.

Every number is a first-pass estimate (like the betas), stated on the page.

    project(goal, serving, as_of, m=None) -> dict
"""
from __future__ import annotations

import math
import re

from officekit.goals import SWR

# blended expected NOMINAL return per strategy sid — house priors, refine later.
EXPECTED_RETURN = {
    "core_equity": 0.070, "direct_index": 0.070, "concentrated": 0.080,
    "muni": 0.035, "bonds": 0.040, "cash_mgmt": 0.040, "duration_mgmt": 0.040,
    "real_estate": 0.055, "real_assets": 0.045, "venture": 0.120,
    "human_capital": 0.030, "trend": 0.050, "deploy_powder": 0.050,
    "index_hedge": 0.0, "tail_vol": -0.02, "harvest_engine": 0.0,
}
DEFAULT_RETURN = 0.05

FINANCE_DEFAULTS = {"down_pct": 25.0, "rate_pct": 6.5, "term_years": 30}
CARRY_DEFAULTS = {"tax_pct": 1.1, "maint_pct": 1.0, "insurance_pct": 0.3, "closing_pct": 1.5}
_MARKETABLE = ("cash", "public_equity", "direct_index", "single_name_equity",
               "municipal_credit", "fixed_income", "alpha_market_neutral")
_PURCHASE_RE = re.compile(r"\b(home|house|property|properties|condo|apartment|mansion|"
                          r"real[- ]?estate|purchase|buy|down\s*payment|pied|villa|estate)\b", re.I)


# ------------------------------------------------------------------ helpers

def _years_to(date, as_of):
    if not date or not as_of:
        return None
    try:
        y0, m0 = int(str(as_of)[:4]), int(str(as_of)[5:7] or 1)
        y1, m1 = int(str(date)[:4]), int(str(date)[5:7] or 1)
        return max(0.0, (y1 - y0) + (m1 - m0) / 12.0)
    except (ValueError, TypeError):
        return None


def blended_return(serving):
    v = sum(max(e.get("cur_val") or 0, 0) for e in serving)
    if v <= 0:
        return DEFAULT_RETURN
    return sum(max(e.get("cur_val") or 0, 0) * EXPECTED_RETURN.get(e.get("sid"), DEFAULT_RETURN)
               for e in serving) / v


def _marketable(m):
    return sum(s["value"] for s in m["assets"] if s["category"] in _MARKETABLE) if m else 0.0


def _existing_debt_service(m, exclude_id=None):
    """Total fixed ongoing drag the portfolio must carry before any discretionary
    goal — the first call on the budget in every view (single-goal and contention).

    Two sources: (1) intuited fixed commitments that draw on the portfolio —
    mortgage P&I, and lifestyle spending once decumulating — taken at their full
    modeled amount; (2) interest-only on any debt NOT promoted to an implicit
    goal (legacy offices / offices without the intuition layer). A debt covered by
    an implicit mortgage goal is counted once, via (1)."""
    if not m:
        return 0.0
    data = m.get("d", {}) or {}
    goals = data.get("commitments", data.get("goals")) or []
    covered = {g.get("sleeve") for g in goals
               if g.get("source") == "mortgage"}
    covered_ids = {g.get("sleeve_id") for g in goals if g.get("source") == "mortgage" and g.get("sleeve_id")}
    svc = sum(float(g.get("annual_amount") or 0) for g in goals
              if (g.get("implicit") or "commitments" in data) and g.get("portfolio_funded")
              and g.get("active", True) and g.get("id") != exclude_id)
    for s in m["sleeves"]:
        if s.get("category") == "real_estate_debt" and not (
                s.get("id") in covered_ids if s.get("id") else s.get("name") in covered):
            rate = (s.get("rate_pct") or s.get("meta", {}).get("rate_pct") or 6.0) / 100.0
            svc += abs(s.get("value") or 0) * rate
    return svc


def _ltcg_rate(m):
    return (m.get("tax") or {}).get("rate") or 0.35


def _annual_mortgage_payment(principal, rate_pct, term_years):
    r = (rate_pct / 100.0) / 12.0
    n = int(term_years * 12)
    if principal <= 0 or n <= 0:
        return 0.0
    if r == 0:
        return principal / term_years
    pmt = principal * r / (1 - (1 + r) ** -n)
    return pmt * 12.0


def is_financed_purchase(goal):
    return bool(goal.get("finance") or (goal.get("kind") == "spending"
               and _PURCHASE_RE.search(goal.get("label") or "")))


def _params(goal, m):
    fin = {**FINANCE_DEFAULTS, **(goal.get("finance") or {})}
    car = {**CARRY_DEFAULTS, **(goal.get("carry") or {})}
    # low-basis books realize more tax to raise a given amount of cash
    concentrated = bool(((m or {}).get("d") or {}).get("profile", {}).get("concentrated_low_basis"))
    fin.setdefault("embedded_gain_pct", 70.0 if concentrated else 50.0)
    return fin, car


# --------------------------------------------------------------- the models

def _target(goal):
    kind = goal.get("kind")
    if kind == "spending":
        return float(goal.get("amount") or 0)
    if kind == "retirement":
        spend = float(goal.get("annual_spending") or 0)
        return spend / SWR if spend else 0.0
    if kind == "liquidity_floor":
        return float(goal.get("amount") or 0)
    return None


def _afford_for_price(price, m, fin, car, marketable=None):
    """The per-price affordability arithmetic — shared by the model and the
    recommendation search (max affordable price, income gap, all-cash check)."""
    ltcg = _ltcg_rate(m)
    if marketable is None:
        marketable = _marketable(m)
    down = price * fin["down_pct"] / 100.0
    closing = price * car["closing_pct"] / 100.0
    needed_net = down + closing
    haircut = min(0.95, fin["embedded_gain_pct"] / 100.0 * ltcg)
    gross_liquidation = needed_net / (1 - haircut) if haircut < 1 else needed_net
    mortgage = price - down
    pi = _annual_mortgage_payment(mortgage, fin["rate_pct"], fin["term_years"])
    annual_carry = pi + price * (car["tax_pct"] + car["maint_pct"] + car["insurance_pct"]) / 100.0
    existing_service = _existing_debt_service(m)
    post_marketable = marketable - gross_liquidation
    sustainable = max(post_marketable, 0) * SWR - existing_service
    ratio = (sustainable / annual_carry) if annual_carry > 0 else 0.0
    return {"down": down, "closing": closing, "gross_liquidation": gross_liquidation,
            "tax_to_raise": gross_liquidation - needed_net, "mortgage": mortgage, "annual_pi": pi,
            "prop_tax": price * car["tax_pct"] / 100.0, "maint": price * car["maint_pct"] / 100.0,
            "insurance": price * car["insurance_pct"] / 100.0, "annual_carry": annual_carry,
            "existing_service": existing_service, "post_marketable": post_marketable,
            "sustainable": sustainable, "ratio": ratio,
            "can_raise": gross_liquidation <= marketable}


def _affordability(goal, m, serving):
    """The financed-purchase / carry-vs-sustainable model."""
    price = float(goal.get("amount") or 0)
    fin, car = _params(goal, m)
    ltcg = _ltcg_rate(m)
    marketable = _marketable(m)
    a = _afford_for_price(price, m, fin, car, marketable)
    down, closing = a["down"], a["closing"]
    gross_liquidation, tax_to_raise = a["gross_liquidation"], a["tax_to_raise"]
    mortgage, pi = a["mortgage"], a["annual_pi"]
    prop_tax, maint, insurance = a["prop_tax"], a["maint"], a["insurance"]
    annual_carry = a["annual_carry"]
    existing_service = a["existing_service"]
    post_marketable, sustainable = a["post_marketable"], a["sustainable"]
    can_raise, ratio = a["can_raise"], a["ratio"]

    if not can_raise:
        verdict = (f"can't even raise the {_pct(fin['down_pct'])} down payment — it needs "
                   f"liquidating more than your entire marketable book")
    elif ratio >= 1.0:
        verdict = (f"affordable — the ~{_m(annual_carry)}/yr carry sits inside the ~{_m(sustainable)}/yr "
                   f"your post-purchase portfolio sustains")
    elif sustainable > 0:
        verdict = (f"NOT affordable on the current book — the ~{_m(annual_carry)}/yr carrying cost is "
                   f"~{annual_carry / sustainable:.2f}× the ~{_m(sustainable)}/yr your portfolio sustains "
                   f"after the down payment — a {_m(annual_carry - sustainable)}/yr gap")
    else:
        verdict = f"NOT affordable — no annual carrying capacity remains after the purchase and existing debt"
    return {
        "applicable": True, "mode": "financed", "kind": goal.get("kind"), "verdict": verdict,
        "affordable": can_raise and ratio >= 1.0, "ratio": ratio,
        "price": price, "down": down, "down_pct": fin["down_pct"], "closing": closing,
        "tax_to_raise": tax_to_raise, "gross_liquidation": gross_liquidation,
        "cash_needed": gross_liquidation, "mortgage": mortgage, "rate_pct": fin["rate_pct"],
        "term_years": fin["term_years"], "annual_pi": pi, "prop_tax": prop_tax, "maint": maint,
        "insurance": insurance, "annual_carry": annual_carry, "existing_service": existing_service,
        "marketable": marketable, "post_marketable": post_marketable, "sustainable": sustainable,
        "ltcg_rate": ltcg, "embedded_gain_pct": fin["embedded_gain_pct"],
        "params": {**fin, **{"tax_pct": car["tax_pct"], "maint_pct": car["maint_pct"],
                             "insurance_pct": car["insurance_pct"]}},
    }


def _expense(goal, m):
    """Ongoing annual expense — a permanent drag on the portfolio."""
    annual = float(goal.get("annual_amount") or goal.get("amount") or 0)
    marketable = _marketable(m)
    existing_service = _existing_debt_service(m, exclude_id=goal.get("id"))
    sustainable = max(marketable, 0) * SWR - existing_service
    ratio = (sustainable / annual) if annual > 0 else 0.0
    covers_pct = min(100.0, ratio * 100.0)
    if ratio >= 1.0:
        verdict = (f"sustainable — {_m(annual)}/yr sits inside the {_m(sustainable)}/yr your "
                   f"portfolio throws off at {SWR*100:.0f}%")
    else:
        max_forever = max(sustainable, 0)
        verdict = (f"NOT sustainable indefinitely — {_m(annual)}/yr exceeds the {_m(max_forever)}/yr "
                   f"the portfolio sustains; it draws down principal")
    return {"applicable": True, "mode": "expense", "kind": "expense", "verdict": verdict,
            "annual": annual, "sustainable": sustainable, "marketable": marketable,
            "existing_service": existing_service, "ratio": ratio, "covers_pct": covers_pct,
            "affordable": ratio >= 1.0}


def _lump_sum(goal, serving, as_of):
    """Plain dated target / retirement corpus grown by the serving strategies."""
    target = _target(goal)
    v0 = sum(max(e.get("cur_val") or 0, 0) for e in serving)
    yrs = _years_to(goal.get("date"), as_of)
    try:
        base = int(str(as_of)[:4])
    except (ValueError, TypeError):
        base = 2026
    r = blended_return(serving)

    if goal.get("kind") == "liquidity_floor":
        return {"applicable": True, "mode": "floor", "is_floor": True, "kind": "liquidity_floor",
                "v0": v0, "target": target, "blended": r,
                "funded_ratio": (v0 / target if target else 0.0),
                "verdict": ("above the floor" if v0 >= target else "below the floor — top up liquidity"),
                "series": [], "reach_years": 0.0 if v0 >= target else None, "reach_year": None,
                "yrs_to_date": yrs, "goal_year": None, "funded_at_date": None}

    if v0 >= target and target > 0:
        reach = 0.0
    elif v0 <= 0 or not target or r <= 0:
        reach = None
    else:
        reach = math.log(target / v0) / math.log(1 + r)
    horizon = int(min(45, max(6, (yrs or 0) + 4, (reach or 0) + 4)))
    series = [(base + t, v0 * (1 + r) ** t) for t in range(horizon + 1)]
    funded_at_date = (v0 * (1 + r) ** yrs / target if yrs is not None and target else None)

    if reach is None:
        verdict = "the current allocation doesn't reach this on growth alone — add contributions or shift the mix"
    elif reach == 0:
        verdict = "already funded today by the serving strategies"
    elif yrs is None:
        verdict = f"reaches the target in about {reach:.0f} year(s) on the current allocation"
    elif reach <= yrs + 0.25:
        verdict = f"on track — reaches it ~{yrs - reach:.0f} year(s) before your target date"
    else:
        verdict = f"short — reaches it ~{reach - yrs:.0f} year(s) AFTER your target date"

    return {"applicable": True, "mode": "lump_sum", "is_floor": False, "kind": goal.get("kind"),
            "v0": v0, "target": target, "blended": r, "reach_years": reach,
            "reach_year": (base + round(reach)) if reach is not None else None, "yrs_to_date": yrs,
            "goal_year": (base + round(yrs)) if yrs is not None else None,
            "funded_at_date": funded_at_date, "funded_ratio": (v0 / target if target else 0.0),
            "series": series, "verdict": verdict}


def project(goal, serving, as_of, m=None):
    kind = goal.get("kind")
    if kind == "tax_efficiency":
        return {"applicable": False, "reason": "ongoing objective — no funding target", "mode": "none"}
    if kind == "expense":
        return _expense(goal, m or {})
    if m and is_financed_purchase(goal) and (goal.get("amount") or 0) > 0:
        return _affordability(goal, m, serving)
    return _lump_sum(goal, serving, as_of)


def portfolio_return(m):
    """Value-weighted expected return of the office's MARKETABLE allocation —
    the rate the book compounds at while you wait to afford something."""
    from officekit.implicit_strategies import category_to_strategy
    cat2sid = category_to_strategy()
    acc = tot = 0.0
    for s in (m or {}).get("assets", []):
        if s["category"] not in _MARKETABLE:
            continue
        v = max(s["value"], 0)
        acc += v * EXPECTED_RETURN.get(cat2sid.get(s["category"]), DEFAULT_RETURN)
        tot += v
    return acc / tot if tot else DEFAULT_RETURN


def max_affordable_price(m, fin, car):
    """Largest price the office can carry today (ratio >= 1) — binary search."""
    marketable = _marketable(m)
    if marketable <= 0 or _afford_for_price(1000.0, m, fin, car)["ratio"] < 1:
        return 0.0
    lo, hi = 0.0, marketable * 5 or 1e7
    for _ in range(44):
        mid = (lo + hi) / 2
        if _afford_for_price(mid, m, fin, car)["ratio"] >= 1:
            lo = mid
        else:
            hi = mid
    return lo


def years_to_afford_price(price, m, fin, car, r):
    """Years of marketable growth at r until `price` becomes affordable."""
    if r <= 0:
        return None
    marketable = _marketable(m)
    for y in range(0, 61):
        if _afford_for_price(price, m, fin, car, marketable=marketable * (1 + r) ** y)["ratio"] >= 1:
            return y
    return None


def recommendations(goal, proj, m):
    """Concrete paths to the goal + timeline. Returns {headline, items:[{lever, detail}]}."""
    mode = proj.get("mode")
    if mode == "financed":
        fin, car = _params(goal, m)
        r = portfolio_return(m)
        price = proj["price"]
        maxp = max_affordable_price(m, fin, car)
        yrs = years_to_afford_price(price, m, fin, car, r)
        items = [{"lever": "Buy less now",
                  "detail": f"the current book carries about {_m(maxp)} today at these terms",
                  "action": {"kind": "apply", "fields": {"amount": int(maxp)},
                             "label": f"set the price to {_m(maxp)}"}}]
        if not proj["affordable"]:
            items.append({"lever": "Wait for the book to grow",
                          "detail": (f"at ~{r*100:.1f}%/yr the {_m(price)} target becomes affordable in "
                                     f"about {yrs} year(s) — if the portfolio isn't spent on other goals first"
                                     if yrs is not None else
                                     f"growth alone doesn't reach it at ~{r*100:.1f}%/yr"),
                          "action": {"kind": "growth"}})
            gap = proj["annual_carry"] - proj["sustainable"]
            items.append({"lever": "Cover the gap with income",
                          "detail": f"~{_m(max(gap, 0))}/yr of income (salary, not portfolio withdrawals) "
                                    f"closes the carry gap",
                          "action": {"kind": "link", "href": "/pages/office.html#add-asset",
                                     "label": "add an income sleeve"}})
            allc = _afford_for_price(price, m, {**fin, "down_pct": 100.0}, car)
            allc_ok = allc["ratio"] >= 1 and allc["can_raise"]
            items.append({"lever": "Pay all cash",
                          "detail": (f"even all-cash works — carry drops to {_m(allc['annual_carry'])}/yr"
                                     if allc_ok else
                                     f"all-cash still fails — you'd liquidate {_m(allc['gross_liquidation'])} "
                                     f"and the remaining book sustains only {_m(allc['sustainable'])}/yr"),
                          "action": ({"kind": "apply", "fields": {"down_pct": 100},
                                      "label": "set the down payment to 100%"} if allc_ok else None)})
        headline = ("Affordable today." if proj["affordable"] else
                    f"You can carry about {_m(maxp)} today; the {_m(price)} target is " +
                    (f"~{yrs} year(s) away at ~{r*100:.1f}%/yr growth." if yrs is not None
                     else "out of reach on growth alone — it needs income or a smaller purchase."))
        return {"headline": headline, "items": items}

    if mode == "expense":
        r = portfolio_return(m)
        items = [{"lever": "Trim to sustainable",
                  "detail": f"about {_m(max(proj['sustainable'], 0))}/yr is sustainable indefinitely "
                            f"at {SWR*100:.0f}%",
                  "action": {"kind": "apply", "fields": {"annual_amount": int(max(proj["sustainable"], 0))},
                             "label": f"set the expense to {_m(max(proj['sustainable'], 0))}/yr"}}]
        if not proj["affordable"]:
            yrs = None
            for y in range(0, 61):
                if max(proj["marketable"] * (1 + r) ** y, 0) * SWR - proj["existing_service"] >= proj["annual"]:
                    yrs = y
                    break
            items.append({"lever": "Grow into it",
                          "detail": (f"at ~{r*100:.1f}%/yr the portfolio sustains {_m(proj['annual'])}/yr in "
                                     f"about {yrs} year(s)" if yrs is not None else
                                     "growth alone won't sustain it"),
                          "action": {"kind": "growth"}})
            gap = proj["annual"] - proj["sustainable"]
            items.append({"lever": "Cover with income",
                          "detail": f"~{_m(max(gap, 0))}/yr of income covers the shortfall",
                          "action": {"kind": "link", "href": "/pages/office.html#add-asset",
                                     "label": "add an income sleeve"}})
        headline = ("Sustainable indefinitely." if proj["affordable"] else
                    f"Sustainable up to ~{_m(max(proj['sustainable'], 0))}/yr today at {SWR*100:.0f}%.")
        return {"headline": headline, "items": items}

    if mode == "lump_sum" and not proj.get("is_floor"):
        v0, target, r = proj["v0"], proj["target"], proj["blended"]
        yrs = proj.get("yrs_to_date")
        items = []
        if proj.get("reach_years") not in (None, 0) and yrs and proj["reach_years"] > yrs and r > 0:
            need = target - v0 * (1 + r) ** yrs
            pmt = need * r / ((1 + r) ** yrs - 1) if need > 0 else 0
            items.append({"lever": "Contribute",
                          "detail": f"about {_m(max(pmt, 0))}/yr of new savings hits {_m(target)} by "
                                    f"{proj.get('goal_year')}",
                          "action": {"kind": "growth"}})
        return {"headline": proj["verdict"], "items": items}
    return {"headline": "", "items": []}


# small formatters (kept local so the module has no render dep)
def _m(x):
    x = float(x or 0)
    return (f"-${abs(x)/1e6:.2f}M" if abs(x) >= 1e6 else f"-${abs(x)/1e3:.0f}k") if x < 0 else \
           (f"${x/1e6:.2f}M" if x >= 1e6 else f"${x/1e3:.0f}k")


def _pct(x):
    return f"{x:g}%"
