"""intuition — implicit goals derived from the balance sheet.

The commitments analogue of the implicit-strategy doctrine: the office should
INTUIT the commitments a balance sheet implies, not wait for them to be typed.
Two to start:

  * Service the mortgage — any ``real_estate_debt`` liability implies a full
    principal+interest payment and a payoff date. When the rate/term are unknown
    we work up from a documented default and flag it, so the commitment is
    honest today and sharpens the moment the user supplies the real terms.
  * Lifestyle spending — a statistical estimate scaled by net-worth band, used as
    a GATEWAY: a provisional number that starts a conversation about how the
    household actually lives, refined by adding data or chatting with the AI.

Every intuited goal carries ``implicit: True`` plus ``assumptions`` (what was
defaulted and why) and ``missing`` (the fields to fill). Renderers surface those
with add-data and refine-with-AI affordances; nothing here is ever written back
to the user's answers — it is re-derived on every build.

    implicit_goals(data) -> [goal dict, ...]
"""
from __future__ import annotations

from datetime import date, datetime
import hashlib

from officekit.fmt import fmt_usd as _fmt

# Documented defaults for a mortgage whose terms the office doesn't yet know.
# Deliberately conservative-ish and clearly flagged; the user overrides them.
DEFAULT_MORTGAGE_RATE_PCT = 6.5     # planning assumption, not a market quote
DEFAULT_MORTGAGE_TERM_YEARS = 30    # assume a fresh 30-yr term from today

# Property tax is a PERMANENT carry the home implies — it never terminates the
# way the mortgage does. When the home isn't on the balance sheet we intuit its
# value from the mortgage balance at an assumed loan-to-value, all flagged.
DEFAULT_PROPERTY_TAX_RATE_PCT = 1.1   # ~ US effective average (assumption)
DEFAULT_LTV = 0.80                    # to back into a home value from the loan

# Statistical lifestyle-spend anchors by net-worth band (annual, USD). Rough
# figures scaled up from consumer-expenditure norms — a starting point to refine,
# never a measurement. One knob, easy to replace with a real model later.
_SPEND_BANDS = [
    (1_000_000, 75_000),
    (5_000_000, 120_000),
    (20_000_000, 200_000),
    (float("inf"), 350_000),
]


def _annual_pi(principal, rate_pct, term_years):
    """Annualized principal+interest for a fully-amortizing loan."""
    r = (rate_pct / 100.0) / 12.0
    n = int(round(term_years * 12))
    if principal <= 0 or n <= 0:
        return 0.0
    if r == 0:
        return principal / term_years
    pmt = principal * r / (1 - (1 + r) ** -n)
    return pmt * 12.0


def statistical_lifestyle_spend(net_worth):
    """A provisional annual lifestyle-spend estimate for a household at this net
    worth. A gateway number, explicitly an estimate — refine with real data."""
    nw = max(float(net_worth or 0), 0)
    for ceiling, spend in _SPEND_BANDS:
        if nw < ceiling:
            return spend
    return _SPEND_BANDS[-1][1]


def _as_of_year(data):
    try:
        return int(str(data.get("as_of") or "")[:4])
    except ValueError:
        return datetime.now().year


def _identity(s):
    # Older raw balance-sheet fixtures lack IDs; live intake always mints them.
    return s.get("id") or hashlib.sha256(str(s.get("name", s.get("category"))).encode()).hexdigest()[:16]


def mortgage_goals(data):
    """One implicit 'service the mortgage' goal per real_estate_debt liability."""
    out = []
    debts = [s for s in data.get("sleeves", [])
             if s.get("category") == "real_estate_debt" and (s.get("value") or 0)]
    for s in debts:
        balance = abs(float(s.get("value") or 0))
        meta = s.get("meta") or {}
        rate = s.get("rate_pct", meta.get("rate_pct"))
        term = s.get("term_years", meta.get("term_years"))
        assumptions, missing = [], []
        if rate is None:
            rate = DEFAULT_MORTGAGE_RATE_PCT
            assumptions.append({"field": "rate_pct", "value": rate, "assumed": True,
                                "why": "planning rate assumption — actual rate not on file"})
            missing.append("rate_pct")
        else:
            rate = float(rate)
        if term is None:
            term = DEFAULT_MORTGAGE_TERM_YEARS
            assumptions.append({"field": "term_years", "value": term, "assumed": True,
                                "why": "assumed a 30-yr term from today — actual remaining term not on file"})
            missing.append("term_years")
        else:
            term = float(term)
        from officekit.commitments import add_months
        anchor = date.fromisoformat(str(s.get("terms_as_of") or meta.get("terms_as_of") or data.get("as_of") or date.today()))
        payoff = add_months(anchor, round(term * 12))
        as_of = date.fromisoformat(str(data.get("as_of") or date.today()))
        remaining = max(0, (payoff.year - as_of.year) * 12 + payoff.month - as_of.month) / 12
        annual = round(_annual_pi(balance, rate, remaining))
        payoff_year = payoff.year
        name = s.get("name") or "Mortgage"
        out.append({
            "id": f"implicit:mortgage:{_identity(s)}", "sleeve_id": s.get("id"),
            "kind": "expense", "annual_amount": annual,
            "label": f"Service the {name.lower()}" if "mortgage" not in name.lower() else f"Service the {name}",
            "implicit": True, "source": "mortgage", "fixed": True, "portfolio_funded": True,
            "terminating": True, "ends_year": payoff_year, "ends_on": payoff.isoformat(), "sleeve": name,
            "assumptions": assumptions, "missing": missing,
            "facts": {"balance": round(balance), "rate_pct": rate, "term_years": remaining,
                      "terms_as_of": anchor.isoformat(),
                      "annual_pi": annual, "payoff_year": payoff_year},
        })
    return out


def property_tax_goals(data):
    """A permanent 'property tax' carry per residence the balance sheet implies.

    Uses a real_estate asset's value when present; otherwise intuits the home
    value from the mortgage balance at an assumed loan-to-value (flagged), so the
    commitment exists even before the home itself is on the books. Property tax
    does NOT terminate — it is a perpetual carry, unlike the mortgage."""
    out = []
    homes = [s for s in data.get("sleeves", [])
             if s.get("category") == "real_estate" and (s.get("value") or 0) > 0]
    debts = [s for s in data.get("sleeves", [])
             if s.get("category") == "real_estate_debt" and (s.get("value") or 0)]
    entries = []
    if homes:
        for s in homes:
            entries.append((s.get("name") or "Primary residence", abs(float(s["value"])), False, s))
    elif debts:                                   # no home on the books — infer it from the loan
        bal = abs(float(debts[0].get("value") or 0))
        entries.append(("Primary residence", round(bal / DEFAULT_LTV), True, debts[0]))
    for name, home_value, inferred, sleeve in entries:
        rate = DEFAULT_PROPERTY_TAX_RATE_PCT
        annual = round(home_value * rate / 100.0)
        assumptions = [{"field": "rate_pct", "value": rate, "assumed": True,
                        "why": "assumed ~1.1% effective property-tax rate — actual rate not on file"}]
        missing = ["rate_pct"]
        if inferred:
            assumptions.insert(0, {"field": "home_value", "value": round(home_value), "assumed": True,
                                   "why": f"home value inferred from the mortgage at {DEFAULT_LTV*100:.0f}% "
                                          "LTV — the residence isn't on the balance sheet yet"})
            missing.insert(0, "home_value")
        out.append({
            "id": sleeve.get("property_tax_id") or (sleeve.get("meta") or {}).get("property_tax_id") or f"implicit:property_tax:{_identity(sleeve)}",
            "sleeve_id": None if inferred else sleeve.get("id"),
            "kind": "expense", "annual_amount": annual,
            "label": "Property tax" + (f" · {name}" if len(entries) > 1 else ""),
            "implicit": True, "source": "property_tax", "fixed": True, "portfolio_funded": True,
            "terminating": False, "estimated": bool(inferred),
            "assumptions": assumptions, "missing": missing,
            "facts": {"home_value": round(home_value), "rate_pct": rate,
                      "annual_tax": annual, "inferred_value": inferred},
        })
    return out


def spending_goal(data, net_worth):
    """One implicit lifestyle-spending goal (a statistical gateway estimate).

    Whether it draws on the PORTFOLIO depends on decumulation: while the
    household earns, income covers it (portfolio_funded False) — it is still
    surfaced to start the lifestyle conversation. In decumulation it becomes a
    real portfolio carry."""
    profile = data.get("profile") or {}
    decumulating = bool(profile.get("decumulating"))
    est = statistical_lifestyle_spend(net_worth)
    fund_note = ("drawn from the portfolio (you're decumulating)" if decumulating
                 else "covered by income today — it will draw on the portfolio in retirement")
    return {
        "id": "implicit:spending:lifestyle",
        "kind": "expense", "annual_amount": est,
        "label": "Lifestyle spending",
        "implicit": True, "source": "lifestyle", "fixed": True,
        "estimated": True, "portfolio_funded": decumulating,
        "assumptions": [{"field": "annual_amount", "value": est, "assumed": True,
                         "why": "statistical estimate for a household at this net worth — "
                                "refine by describing how you actually live"}],
        "missing": ["annual_amount"],
        "facts": {"annual_estimate": est, "decumulating": decumulating, "funding": fund_note},
    }


def implicit_strategies(m):
    """Holdings suggest strategies; they do not prove an operating TLH program."""
    sleeves = m.get("assets") or [s for s in m.get("sleeves", []) if s.get("kind") == "asset"]

    def _val(cats):
        return sum(s.get("value") or 0 for s in sleeves if s.get("category") in cats)

    def _lots(cats):
        return sum(len(s.get("holdings") or []) for s in sleeves if s.get("category") in cats)

    out = []
    di_val = _val(("direct_index", "single_name_equity"))
    if di_val > 0:
        lots = _lots(("direct_index", "single_name_equity"))
        lot_txt = f"{lots} individual equity lot(s) worth " if lots else ""
        out.append({
            "id": "implicit:strategy:direct_index", "implicit": True, "status": "review",
            "label": "Direct indexing / tax-loss harvesting review", "value": round(di_val),
            "why": (f"You hold {lot_txt}{_fmt(di_val)} in equity positions. Review direct indexing and "
                    "tax-loss harvesting against the benchmark, tax lots and account mandate. "
                    "Holdings alone do not establish an operating program."),
            "href": "beta_programs.html", "cta": "Review beta/TLH programs",
            "refine": "My direct-index SMA harvests on a __ cadence; watch washes across __ accounts."})
    if _val(("options_overlay",)) != 0:
        out.append({
            "id": "implicit:strategy:options_overlay", "implicit": True, "status": "active",
            "label": "Options overlay", "value": round(_val(("options_overlay",))),
            "why": ("You carry an options overlay — an income/hedging strategy already at work on the book. "
                    "Confirm its intent so its risk is scored, not just its mark."),
            "href": "risk.html", "cta": "See risk",
            "refine": "My options overlay is for __ (income / hedging / leverage); target size __."})
    if _val(("cash",)) > 0:
        out.append({
            "id": "implicit:strategy:cash_mgmt", "implicit": True, "status": "active",
            "label": "Cash management", "value": round(_val(("cash",))),
            "why": ("Your cash and money-market balances are a yield/liquidity sleeve — a strategy in "
                    "itself. Set a target floor so idle cash and negative carry get flagged."),
            "href": "harvest.html", "cta": "Review liquidity",
            "refine": "Keep about $__ liquid; sweep the rest into __."})
    return out


def implicit_goals(data, net_worth=None):
    """Derived baseline commitments. Only an explicit identity-linked override
    confirms/replaces lifestyle; unrelated expense and retirement goals do not."""
    if net_worth is None:
        net_worth = sum(s.get("value") or 0 for s in data.get("sleeves", [])
                        if s.get("category") != "human_capital")
    out = list(mortgage_goals(data)) + list(property_tax_goals(data))
    out.append(spending_goal(data, net_worth))
    return out
