"""Starting briefs for every planner response, refined by research and court.

Tickers are candidates to investigate, not approvals or verified live quotes.
Different mitigations keep distinct briefs even when they share a strategy.
"""

PLAYBOOKS = {
    "put_index": ("Index downside protection", "options", ["SPY"],
        "Compare a three-to-six-month put about 5% below spot with a put spread; size the protected notional against equity exposure.",
        "Premium bleed, expiry, tax treatment and imperfect tracking; obtain current option quotes before recommending contracts."),
    "put_spread": ("Defined-band index protection", "options", ["SPY"],
        "Compare buying a roughly 5%-out-of-the-money put and selling a roughly 15%-out-of-the-money put with the same expiry.",
        "Protection stops below the short strike; verify net premium, assignment and permissions."),
    "collar_eq": ("Equity collar", "options", ["SPY"],
        "Pair a protective put with a covered call against an existing matching holding; compare upside sacrificed for premium saved.",
        "Covered holdings and option permissions are required; zero cost is a quote-dependent target, not a fact."),
    "tailfund": ("Tail-risk allocation", "security", ["TAIL"],
        "Investigate a small tail-risk ETF allocation and compare its convexity, holdings, carry cost and behavior across selloff speeds.",
        "Persistent drag and path dependence; a fund does not guarantee a household loss floor."),
    "trend": ("Managed-futures diversifier", "security", ["DBMF", "KMLM"],
        "Compare managed-futures ETFs as a diversifying allocation across equity, rates, currencies and commodity trends.",
        "Whipsaw, fees, leverage and lag in sudden reversals; historical crisis returns are not assured."),
    "cash_deploy": ("Drawdown deployment plan", "security", ["VTI", "SGOV"],
        "Keep a defined reserve in short Treasury exposure and propose staged broad-equity purchases with explicit triggers and an expiry for the plan.",
        "Waiting can miss a rebound; fund only from unreserved cash and keep near-term obligations liquid."),
    "put_tech": ("Technology exposure protection", "options", ["QQQ"],
        "Evaluate QQQ puts against measured technology exposure, with explicit hedge ratio, expiry and premium budget.",
        "QQQ is an imperfect hedge for an individual stock or custom SMA; verify sector holdings and option quotes."),
    "collar_conc": ("Concentrated holding collar", "options", [],
        "Identify the actual largest single-stock holding, then compare protective puts and covered calls on that same underlying.",
        "Do not infer a single stock from a diversified SMA. Review liquidity, assignment, employment restrictions and tax treatment."),
    "exch_fund": ("Exchange-fund diligence", "program", [],
        "Prepare a provider diligence brief for contributing eligible appreciated shares to a diversified exchange fund.",
        "Eligibility, illiquidity, fees, diversification limits and tax conditions require provider and adviser confirmation."),
    "trim": ("Tax-aware concentration rotation", "security", ["VTI", "VXUS"],
        "Identify the actual concentrated holding and candidate lots, estimate sale taxes from recorded basis, then compare diversified replacement ETFs.",
        "Missing basis prevents a sale budget; spread sales deliberately and coordinate wash-sale and employer restrictions."),
    "diversify": ("Defensive non-tech rotation", "security", ["VDC", "XLP"],
        "Compare consumer-staples ETFs for a defensive non-tech allocation funded by new proceeds. Select one implementation after verifying sector exposure, holdings, fees and liquidity.",
        "Staples remain equities and are sector-concentrated. Compare with broader value exposure, whose technology holdings must be disclosed."),
    "dur_short": ("Short-duration bond rotation", "security", ["VGSH", "SHY"],
        "Compare short Treasury ETFs with the existing bond sleeve and a maturity-matched ladder; show duration reduction and the income tradeoff.",
        "Realized gains, reinvestment risk and loss of tax-exempt income can outweigh reduced duration."),
    "rate_hedge": ("Rate-risk overlay", "options", ["TLT"],
        "Compare a defined-loss TLT put structure with a dealer payer-swaption quote for the measured duration exposure.",
        "Basis risk, premium and permissions matter; do not prescribe an uncovered short or invent a dealer quote."),
    "realasset": ("Inflation ballast", "security", ["IAU", "VTIP"],
        "Compare gold and short inflation-protected Treasury exposure, explain their different inflation mechanisms, and propose a bounded allocation.",
        "Gold has no cash yield; TIPS carry real-rate risk, and neither tracks household spending perfectly."),
    "commod_trend": ("Commodity-aware trend allocation", "security", ["KMLM", "DBMF"],
        "Compare managed-futures funds' commodity, currency and rates exposure for an inflation shock; distinguish trend following from permanently long commodities.",
        "Strategies may be short commodities and can lose in reversals; verify actual mandates and current exposures."),
    "pace": ("Venture commitment pacing", "program", [],
        "Inventory outstanding commitments and dated calls, set an annual new-commitment ceiling, and stress an exit drought before approving new funds.",
        "Unfunded commitments and overlapping funds can consume liquidity despite stable reported NAV."),
    "secondary": ("Private-asset secondary sale", "program", [],
        "Identify eligible stakes, prepare an information package, obtain competing bids, and compare proceeds net of discounts, fees and taxes.",
        "Transfer restrictions and stale NAV make headline discounts unreliable; a sale requires actual counterparties and consent."),
    "reserve": ("Follow-on reserve", "program", [],
        "Build a company-by-company follow-on schedule, rank participation priorities, and earmark a dated reserve without adding another asset.",
        "Avoid automatic pro-rata support for weak companies and avoid counting reserves twice as commitments and cash deductions."),
    "insurance": ("Property and liability coverage review", "program", [],
        "Inventory replacement-cost coverage, exclusions, deductibles and liability limits; produce a broker quote request and a coverage-gap schedule.",
        "Replacement cost differs from market value; exclusions and claims conditions control actual protection."),
    "mort_cap": ("Mortgage rate protection", "program", [],
        "Verify whether the mortgage floats, its reset index and caps; compare a lender cap quote with refinancing and retaining current terms.",
        "A fixed-rate mortgage may need no hedge. Fees, maturity mismatch and refinancing costs must be quoted."),
    "put_single": ("Single-stock downside protection", "options", [],
        "Select the actual single-stock exposure and compare puts across strikes and expiries using its current option chain.",
        "Option liquidity, premium drag and contract sizing may make the hedge impractical."),
    "collar_single": ("Single-stock collar", "options", [],
        "Compare a covered collar against the actual held shares, showing the loss floor, upside cap and net quoted premium.",
        "Review assignment, constructive-sale issues, share coverage and employer trading restrictions."),
    "pvf": ("Prepaid forward diligence", "program", [],
        "Prepare a competing-dealer quote request with the eligible holding, desired liquidity, term, downside floor and upside participation.",
        "Tax treatment, counterparty credit, collateral and documentation are essential; terms cannot be assumed."),
    "accept": ("Deliberate risk acceptance", "program", [],
        "Document the exposure being accepted, why mitigation costs exceed its benefit, a loss budget, and triggers that would reopen the decision.",
        "Acceptance needs a review date and explicit ownership; it is not evidence that the risk disappeared."),
    "cash_buffer": ("Liquidity buffer", "security", ["SGOV"],
        "Protect dated spending and liquidity floors first, then compare Treasury-bill exposure and bank/MMF cash for the remaining reserve.",
        "An ETF must be sold and settled; keep near-term payment cash outside market instruments."),
    "credit_line": ("Standby liquidity facility", "program", [],
        "Compare a pledged-asset facility and HELOC using written lender terms, stressed collateral capacity, rate resets and covenants.",
        "Undrawn capacity is not cash; collateral calls, cancellation and variable rates can coincide with a drawdown."),
    "harvest_engine": ("Tax-loss harvesting program", "program", [],
        "Use actual lots and gain character to identify harvest candidates, replacement exposure and a coordinated wash-sale calendar.",
        "Do not fabricate lots, tax savings or replacement equivalence; include spouse and outside-account restrictions."),
    "di_convert": ("Direct-index transition", "program", [],
        "Compare keeping index funds with a phased direct-index SMA transition, using tax-lot costs, tracking error, fees and exclusions.",
        "Transition taxes may outweigh harvesting benefits; do not recommend selling without recorded basis."),
    "daf_gift": ("Appreciated-share gifting", "program", [],
        "Identify eligible long-held appreciated lots and compare direct gifts with a donor-advised fund, subject to the household's charitable intent.",
        "Gifts are irrevocable; deduction limits, substantiation and recipient acceptance need confirmation."),
    "disability_ins": ("Income protection", "program", [],
        "Review existing disability coverage, occupation definition, elimination period, benefit taxation and remaining income gap; prepare a broker brief.",
        "Underwriting and exclusions determine coverage. Do not select a policy without actual terms."),
    "term_life": ("Dependent protection", "program", [],
        "Calculate the dependent funding gap after existing assets and coverage, then request level-term quotes matched to the obligation horizon.",
        "Avoid equating the entire modeled human-capital asset with insurance need; health and underwriting affect availability."),
}

STRATEGY_DEFAULT = {"core_equity": ("security", ["VTI", "VXUS"]), "muni": ("security", ["VTEB", "MUB"]),
    "bonds": ("security", ["BND", "VGSH"]), "cash_mgmt": "cash_buffer", "real_estate": "insurance",
    "human_capital": "disability_ins", "venture": "pace", "deploy_powder": "diversify",
    "direct_index": "di_convert", "concentrated": "trim", "index_hedge": "put_index", "tail_vol": "tailfund",
    "trend": "trend", "real_assets": "realasset", "harvest_engine": "harvest_engine", "gifting": "daf_gift",
    "monetization": "exch_fund", "insurance_program": "insurance", "credit_line": "credit_line", "duration_mgmt": "dur_short"}


def brief(strategy_id, option=None, title=None, request=""):
    from officekit.render_strategies import STRATEGY_LIB
    spec = PLAYBOOKS.get(option)
    default = STRATEGY_DEFAULT.get(strategy_id)
    if spec is None and isinstance(default, str):
        spec = PLAYBOOKS[default]
    lib = STRATEGY_LIB.get(strategy_id) or {}
    if spec:
        name, kind, candidates, thesis, risks = spec
    else:
        kind, candidates = default if isinstance(default, tuple) else ("research", [])
        name = title or lib.get("title") or strategy_id
        thesis = lib.get("desc") or request or "Develop a thesis and investigate suitable implementations."
        risks = "Verify primary evidence, suitability, liquidity, costs and the household's exclusions before recommending investments."
    return {"title": title or name, "kind": kind, "candidates": candidates,
            "thesis": thesis, "risks": risks, "request": request, "option": option}
