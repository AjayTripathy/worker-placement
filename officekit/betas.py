"""betas — the beta-assignment engine: category priors for sleeves without data.

Phase-1 productization: external users don't hand-author factor loadings, so intake
assigns each sleeve a DEFAULT beta vector from its category (+ an optional style
modifier), inheriting the same first-pass-estimate caveat the dashboard prints.
The priors are the house view — the same loadings the reference account uses —
and are meant to be REFINED from realized returns later (Phase 3), never trusted
as regression output.

default_beta(category, style=None) -> {factor: loading}
assign_betas(sleeve)               -> fills sleeve["beta"] in place if missing
"""
from __future__ import annotations

DEFAULT_FACTORS = ["S&P 500", "Venture Capital", "Mortgage Debt", "Inflation", "Rates", "USD"]

# category -> base loading vector (house priors; first-pass estimates)
_BASE = {
    "public_equity":        {"S&P 500": 1.00, "Venture Capital": 0.45, "Mortgage Debt": 0.0, "Inflation": -0.20, "Rates": -0.30, "USD": 0.10},
    "direct_index":         {"S&P 500": 1.15, "Venture Capital": 0.60, "Mortgage Debt": 0.0, "Inflation": -0.25, "Rates": -0.35, "USD": 0.10},
    "single_name_equity":   {"S&P 500": 1.10, "Venture Capital": 0.50, "Mortgage Debt": 0.0, "Inflation": -0.20, "Rates": -0.30, "USD": 0.10},
    "venture_private":      {"S&P 500": 0.80, "Venture Capital": 1.00, "Mortgage Debt": 0.0, "Inflation": -0.20, "Rates": -0.50, "USD": 0.10},
    "real_estate":          {"S&P 500": 0.40, "Venture Capital": 0.20, "Mortgage Debt": 0.3, "Inflation": 0.50, "Rates": -0.60, "USD": -0.10},
    "municipal_credit":     {"S&P 500": 0.15, "Venture Capital": 0.00, "Mortgage Debt": -0.6, "Inflation": -0.50, "Rates": -1.20, "USD": 0.00},
    "fixed_income":         {"S&P 500": 0.10, "Venture Capital": 0.00, "Mortgage Debt": -0.3, "Inflation": -0.60, "Rates": -0.90, "USD": 0.00},
    "alpha_market_neutral": {"S&P 500": 0.00, "Venture Capital": 0.10, "Mortgage Debt": 0.0, "Inflation": 0.05, "Rates": 0.00, "USD": 0.00},
    "cash":                 {"S&P 500": 0.00, "Venture Capital": 0.00, "Mortgage Debt": 0.0, "Inflation": -1.00, "Rates": 0.10, "USD": 0.00},
    "cash_pending":         {"S&P 500": 0.00, "Venture Capital": 0.00, "Mortgage Debt": 0.0, "Inflation": -1.00, "Rates": 0.10, "USD": 0.00},
    # a FIXED-rate mortgage is a short fixed bond: rising rates make the locked
    # cheap debt WORTH LESS to the lender, i.e. a WIN for the borrower's net
    # worth. With the liability's negative weight, a negative Rates beta yields a
    # positive NW sensitivity — the mortgage HEDGES the home's rate exposure
    # rather than compounding it (sign fix 2026-09-07). ARM overrides this below.
    "real_estate_debt":     {"S&P 500": 0.00, "Venture Capital": 0.00, "Mortgage Debt": 1.0, "Inflation": -0.80, "Rates": -1.00, "USD": 0.00},
    "tax_reserve":          {"S&P 500": 0.00, "Venture Capital": 0.00, "Mortgage Debt": 0.0, "Inflation": 0.00, "Rates": 0.00, "USD": 0.00},
    # capitalized future earnings — an asset with a beta like everything else
    # (principal-ratified 2026-09-02). Wages inflate (+Inflation); the PV of a
    # long earnings stream has duration (-Rates); market exposure depends on style.
    "human_capital":        {"S&P 500": 0.30, "Venture Capital": 0.10, "Mortgage Debt": 0.0, "Inflation": 0.30, "Rates": -0.20, "USD": 0.00},
    # options overlay imported at net mark — modeled with a modest long-equity
    # beta rather than market-neutral (all-zero would understate risk on a
    # delta-bearing book; 2026-09-06). A crude prior — the honest fix needs
    # per-contract deltas, which the overlay row doesn't carry.
    "options_overlay":      {"S&P 500": 0.50, "Venture Capital": 0.10, "Mortgage Debt": 0.0, "Inflation": -0.10, "Rates": -0.10, "USD": 0.05},
    # deferred tax asset (loss carryforward) — a tax attribute, factor-neutral
    "tax_asset":            {"S&P 500": 0.00, "Venture Capital": 0.00, "Mortgage Debt": 0.0, "Inflation": 0.00, "Rates": 0.00, "USD": 0.00},
}

# (category, style) -> field overrides on the base vector
_STYLE = {
    ("public_equity", "intl"):        {"S&P 500": 0.85, "Venture Capital": 0.40, "Inflation": -0.10, "Rates": -0.20, "USD": -0.60},
    ("public_equity", "target_date"): {"S&P 500": 0.90, "Venture Capital": 0.40, "Inflation": -0.15, "USD": -0.10},
    ("public_equity", "tech"):        {"S&P 500": 1.15, "Venture Capital": 0.60, "Inflation": -0.25, "Rates": -0.35},
    ("single_name_equity", "megacap_tech"): {"S&P 500": 1.15, "Venture Capital": 0.60, "Rates": -0.35},
    ("fixed_income", "short_duration"): {"Mortgage Debt": -0.1, "Inflation": -0.80, "Rates": -0.20},
    # tech/startup comp moves with equity markets; tenured/gov income is bond-like
    ("human_capital", "equity_linked"): {"S&P 500": 0.70, "Venture Capital": 0.50, "Inflation": 0.10, "Rates": -0.30},
    ("human_capital", "stable"):        {"S&P 500": 0.05, "Venture Capital": 0.00, "Inflation": 0.20, "Rates": -0.50},
    # an ADJUSTABLE-rate mortgage floats: rising rates raise the payment/burden,
    # so it HURTS net worth — the opposite of the fixed default. (2026-09-07)
    ("real_estate_debt", "arm"):        {"Rates": 1.00, "Inflation": -0.30},
    ("real_estate_debt", "fixed"):      {"Rates": -1.00, "Inflation": -0.80},
}


def default_beta(category, style=None):
    """The prior loading vector for a sleeve category (+ optional style). Unknown
    categories get a zero vector — visible as ~independent, never a silent guess."""
    base = dict(_BASE.get(category) or {f: 0.0 for f in DEFAULT_FACTORS})
    if style and (category, style) in _STYLE:
        base.update(_STYLE[(category, style)])
    return base


def assign_betas(sleeve, style=None):
    """Fill sleeve['beta'] from the priors when the importer/wizard didn't supply one."""
    if not sleeve.get("beta"):
        sleeve["beta"] = default_beta(sleeve["category"], style)
    return sleeve
