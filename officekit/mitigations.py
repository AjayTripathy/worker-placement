"""mitigations — the FULL menu of scenario responses, costed & profile-scored.

The full menu is always presented (this is a product, not one book's doctrine).
Each option's $ cost is computed from the client's REAL exposures; the fit BADGE is
scored against the loaded risk profile — so index insurance shows as "Core hedge" for
a levered/decumulating client and "Situational" for a net-buyer accumulator, but is
shown to both either way. Tax inputs (LTCG rate, embedded gain) come from the data,
never hardcoded.
"""
from __future__ import annotations

from officekit.fmt import fmt_usd as _fmt


def exposures(m):
    a = m["assets"]
    tm = m.get("tm") or {}
    val = lambda cats: sum(s["value"] for s in a if s["category"] in cats)
    one = lambda cat: next((s["value"] for s in a if s["category"] == cat), 0.0)
    conc = next((s for s in a if s["category"] == "direct_index"), None)
    return {"eq": val({"public_equity", "direct_index", "single_name_equity"}),
            # tech-tilt heuristic: direct-index + single-name full weight, cap-weight funds ~0.7
            "tech": one("direct_index") + one("single_name_equity") + 0.7 * val({"public_equity"}),
            "conc": one("direct_index"), "googl": one("single_name_equity"),
            "ratebond": val({"municipal_credit", "fixed_income"}), "re": one("real_estate"),
            "venture": one("venture_private"), "NW": m["NW"],
            "ltcg_rate": tm.get("rate_ltcg", 0.371),
            "conc_gain_pct": (conc or {}).get("meta", {}).get("embedded_gain_pct")}


def _trim_cost(X):
    rate = X["ltcg_rate"]
    g = X["conc_gain_pct"]
    if g is None:
        return ("realizes LTCG", "cost = LTCG rate × the embedded gain on whatever is trimmed")
    return (f"~{_fmt(rate*g*2e6)} / $2M",
            f"{rate*100:.1f}% LTCG on ~{g*100:.1f}% embedded gain per $2M trimmed")


# id -> (name, category, protects, cost_fn(X) -> (cost_str, note))
OPT = {
    "put_index":  ("Protective puts (SPX/SPY, ~5% OTM, rolled)", "HEDGE_INDEX", "Hard floor under the equity book below strike",
                   lambda X: (f"~{_fmt(0.020*X['eq'])}/yr", f"≈2.0%/yr of {_fmt(X['eq'])} equity — full premium, no upside cap")),
    "put_spread": ("Put spread (buy 5% / sell 15% OTM)", "HEDGE_INDEX", "Partial floor over a defined band, cheaper",
                   lambda X: (f"~{_fmt(0.008*X['eq'])}/yr", f"≈0.8%/yr of {_fmt(X['eq'])} equity — capped protection")),
    "collar_eq":  ("Zero-cost equity collar (buy put / sell call)", "COLLAR", "Floors downside, caps upside ~10%",
                   lambda X: ("~$0 premium", "self-funding, but sells upside + generates option premium (taxable)")),
    "tailfund":   ("Tail-risk / long-vol fund (5% sleeve)", "TAILFUND", "Convex crash payoff; bleeds in calm markets",
                   lambda X: (f"~{_fmt(0.015*0.05*X['NW'])}/yr", f"≈1.5%/yr drag on a {_fmt(0.05*X['NW'])} sleeve; multi-x in a crash")),
    "trend":      ("Managed-futures / trend (10% sleeve)", "TREND", "Crisis-alpha; positive in sustained selloffs",
                   lambda X: (f"~{_fmt(0.010*0.10*X['NW'])}/yr", f"≈1.0%/yr fee on a {_fmt(0.10*X['NW'])} sleeve")),
    "cash_deploy":("Keep dry powder to buy the drawdown", "CASH_BUFFER", "Turns a crash into accumulation",
                   lambda X: ("~$0 (carry +)", "MMF ~4.5% carry while waiting; cost = missed upside if no crash")),
    "put_tech":   ("Nasdaq/QQQ puts on the tech book", "HEDGE_SINGLE", "Floors the tech-concentrated block",
                   lambda X: (f"~{_fmt(0.030*X['tech'])}/yr", f"≈3.0%/yr of {_fmt(X['tech'])} tech-tilted exposure")),
    "collar_conc":("Zero-cost collar on the concentrated book", "COLLAR", "Floors the big position, caps its upside",
                   lambda X: ("~$0 premium", "self-funding; caps upside on your largest holding + sells premium")),
    "exch_fund":  ("Exchange fund (swap concentrated → diversified)", "EXCHANGE_FUND", "Diversifies AND defers the gain",
                   lambda X: (f"~{_fmt(0.015*X['conc'])}/yr", f"≈1.5%/yr on {_fmt(X['conc'])} + 7-yr lock; tax deferred not erased")),
    "trim":       ("Trim toward target (realize + rotate)", "TRIM", "Permanently cuts the concentration",
                   _trim_cost),
    "diversify":  ("Deploy incoming powder into non-tech", "TRIM", "Dilutes concentration with new capital",
                   lambda X: ("~$0 tax", "new money → no realization; the cheapest concentration lever")),
    "dur_short":  ("Shorten muni/bond duration", "DURATION", "Cuts rate sensitivity of the bond sleeve",
                   lambda X: (f"~{_fmt(0.006*X['ratebond'])}/yr", f"≈60bp yield give-up on {_fmt(X['ratebond'])} muni+bond")),
    "rate_hedge": ("Payer swaption / short-TLT overlay", "HEDGE_INDEX", "Gains as long rates rise",
                   lambda X: (f"~{_fmt(0.010*X['ratebond']*3)}/yr", "premium/carry on a duration-hedge overlay")),
    "realasset":  ("Real-asset ballast (gold / commodities / TIPS)", "REALASSET", "Hedges inflation & stagflation",
                   lambda X: (f"~{_fmt(0.04*0.05*X['NW'])}/yr", f"expected ~4%/yr opportunity drag on a {_fmt(0.05*X['NW'])} sleeve vs equities")),
    "commod_trend":("Commodity / CTA trend sleeve", "TREND", "Positive in inflation shocks",
                   lambda X: (f"~{_fmt(0.010*0.05*X['NW'])}/yr", f"≈1.0%/yr fee on a {_fmt(0.05*X['NW'])} sleeve")),
    "pace":       ("Pace new venture commitments", "ACCEPT", "Limits further illiquid buildout",
                   lambda X: ("~$0", "opportunity cost of slower deployment only")),
    "secondary":  ("Sell venture stakes on the secondary", "SECONDARY", "Raises liquidity ahead of a reset",
                   lambda X: ("20–40% haircut", "the only pre-reset exit for illiquid stakes — steep discount")),
    "reserve":    ("Hold reserve for follow-on rounds", "CASH_BUFFER", "Defends ownership in down rounds",
                   lambda X: ("cash drag", "reserve capital idles until follow-ons")),
    "insurance":  ("Hazard (fire/quake) + umbrella coverage", "INSURANCE", "Caps property + liability loss",
                   lambda X: ("~$3–8k/yr", "hazard premium on a hard asset; no market action")),
    "mort_cap":   ("Rate cap on the mortgage (if ARM)", "HEDGE_INDEX", "Caps the reset on floating debt",
                   lambda X: ("~$2–6k/yr", "cap premium; moot if the mortgage is fixed")),
    "put_single": ("Protective put on the single name", "HEDGE_SINGLE", "Floors it without selling (keeps the basis)",
                   lambda X: (f"~{_fmt(0.020*X['googl'])}/yr", f"≈2.0%/yr of {_fmt(X['googl'])} — no upside cap")),
    "collar_single":("Zero-cost collar on the single name", "COLLAR", "Floors + caps, self-funding",
                   lambda X: ("~$0 premium", "self-funding but caps upside + sells premium (taxable)")),
    "pvf":        ("Prepaid variable forward on the single name", "EXCHANGE_FUND", "Monetize now + downside floor + defer tax",
                   lambda X: (f"~{_fmt(0.015*X['googl'])}/yr", "≈1–2%/yr embedded; raises cash without a taxable sale")),
    "accept":     ("Accept the sized risk / hold", "ACCEPT", "None — a deliberate hold",
                   lambda X: ("$0", "no hedge; the position is intentional")),
    "cash_buffer":("Maintain MMF buffer + zero leverage", "CASH_BUFFER", "You are never a forced seller",
                   lambda X: ("~$0 (carry +)", "MMF carries ~4.5%; the buffer IS the hedge")),
    "credit_line":("Standby PAL / HELOC credit line", "CREDIT_LINE", "Liquidity without selling into weakness",
                   lambda X: ("~0.35%/yr", "commitment fee on an undrawn line; SOFR+~1.5% when drawn")),
    "harvest_engine":("Systematic tax-loss harvesting", "TAX", "Manufactures losses to offset the gain",
                   lambda X: ("~0.1–0.3%/yr tracking", "lot-level harvesting on the liquid sleeves; losses offset a same-tax-year gain")),
    "di_convert": ("Convert index funds → direct indexing", "TAX", "Turns a static sleeve into a harvest engine",
                   lambda X: (f"~{_fmt(0.003*X['eq'])}/yr", f"≈0.2–0.4%/yr fee on {_fmt(X['eq'])} equity + tracking error, for lot-level harvest capacity")),
    "daf_gift":   ("Gift appreciated shares (DAF / charity)", "GIFT", "FMV deduction + the embedded gain never realized",
                   lambda X: ("$0 tax on gifted gain", "deduct fair value, skip the capital gain — but the gift itself is the cost")),
    "disability_ins": ("Long-term disability insurance", "INSURANCE", "Replaces earnings if you can't work",
                   lambda X: ("~1–3% of income/yr", "own-occupation LTD sized to ~60% of earnings; the highest-probability tail for an earner")),
    "term_life":  ("Term life insurance", "INSURANCE", "Replaces the earner's capitalized income for dependents",
                   lambda X: ("~$0.5–1.5k/yr per $1M", "level term sized to the human-capital sleeve; lapses when the sleeve amortizes to zero")),
}

# mitigation id -> strategy id (render_strategies.STRATEGY_LIB): clicking a
# mitigation on the Scenario Planner lands on that strategy's card, open.
# "accept" maps to nothing on purpose — accepting a sized risk needs no strategy page.
OPT_STRATEGY = {
    "put_index": "index_hedge", "put_spread": "index_hedge", "collar_eq": "index_hedge",
    "put_tech": "index_hedge",
    "tailfund": "tail_vol",
    "trend": "trend", "commod_trend": "trend",
    "cash_deploy": "deploy_powder", "diversify": "deploy_powder",
    "trim": "direct_index",
    "collar_conc": "concentrated", "collar_single": "concentrated", "put_single": "concentrated",
    "exch_fund": "monetization", "pvf": "monetization",
    "dur_short": "duration_mgmt", "rate_hedge": "duration_mgmt",
    "realasset": "real_assets",
    "pace": "venture", "reserve": "venture", "secondary": "venture",
    "insurance": "insurance_program", "mort_cap": "insurance_program",
    "term_life": "insurance_program", "disability_ins": "insurance_program",
    "harvest_engine": "harvest_engine", "di_convert": "harvest_engine",
    "daf_gift": "gifting",
    "cash_buffer": "cash_mgmt",
    "credit_line": "credit_line",
}

FIT_TONE = {"Core hedge": "emerald", "High fit": "emerald", "Good fit": "emerald", "Recommended": "emerald",
            "In place": "emerald", "Situational": "slate", "Optional": "slate", "Default": "slate",
            "Blocked here": "coral", "Costly": "amber"}


def fit(cat, p):
    """Score a mitigation category against the loaded risk profile. Full menu is
    always shown; this only sets the badge + reason."""
    accumulator = p.get("net_buyer") and not p.get("uses_leverage") and not p.get("decumulating")
    if cat in ("HEDGE_INDEX", "TAILFUND", "TREND"):
        return (("Situational", "insurance optimised for levered / decumulating books — a carry drag for a net-buyer accumulator")
                if accumulator else ("Core hedge", "standard drawdown insurance for a levered / decumulating book"))
    if cat == "HEDGE_SINGLE":
        return ("Good fit", "floors a concentrated single name without selling it (keeps the low basis)")
    if cat == "COLLAR":
        return (("Blocked here", "this profile disallows selling premium (short-term ordinary income)")
                if not p.get("premium_selling_allowed") else ("Good fit", "near-zero cost, but caps upside"))
    if cat in ("TRIM", "EXCHANGE_FUND"):
        return (("High fit", "directly cuts the concentration that drives the tail")
                if p.get("concentrated_low_basis") else ("Optional", "reallocation"))
    if cat == "CASH_BUFFER":
        return ("In place", "you already hold this — no action")
    if cat == "CREDIT_LINE":
        return ("Optional", "standby liquidity; you're already unlevered and cash-rich")
    if cat == "REALASSET":
        return ("Good fit", "reallocation, no derivative or premium")
    if cat == "DURATION":
        return ("Good fit", "reallocation, no derivative")
    if cat == "INSURANCE":
        return ("Recommended", "hazard coverage on a hard asset")
    if cat == "TAX":
        return ("Good fit", "a tax-code lever — offsets the bill without touching market exposure")
    if cat == "GIFT":
        return ("Situational", "only if charitable giving is already planned — a gift is not a hedge")
    if cat == "SECONDARY":
        return ("Costly", "the only exit for illiquid stakes — a steep discount")
    return ("Default", "size the risk and hold")


# Preset profiles for the in-page switcher. Same menu + costs; only the Fit
# column re-scores. The client's real profile lives in the data; these are the
# "what-if a different client" lenses.
PRESETS = {
    "acc":   ("Accumulator — net-buyer, unlevered (this account)",
              {"net_buyer": True, "uses_leverage": False, "premium_selling_allowed": False, "decumulating": False, "concentrated_low_basis": True}),
    "lev":   ("Levered growth — margin/leverage in use",
              {"net_buyer": True, "uses_leverage": True, "premium_selling_allowed": True, "decumulating": False, "concentrated_low_basis": True}),
    "dec":   ("Decumulating — drawing income / retiree",
              {"net_buyer": False, "uses_leverage": False, "premium_selling_allowed": True, "decumulating": True, "concentrated_low_basis": False}),
    "endow": ("Endowment — perpetual, diversified",
              {"net_buyer": True, "uses_leverage": False, "premium_selling_allowed": True, "decumulating": False, "concentrated_low_basis": False}),
}
_FLAGS = ("net_buyer", "uses_leverage", "premium_selling_allowed", "decumulating", "concentrated_low_basis")


def default_preset(profile):
    """Pick the preset whose flags match the client's profile; 'acc' fallback."""
    for pk, (_, flags) in PRESETS.items():
        if all(bool(profile.get(f)) == flags[f] for f in _FLAGS):
            return pk
    return "acc"
