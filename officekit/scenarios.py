"""scenarios — the scenario library for the Scenario Planner: market, tax,
income, and life-event scenarios (worst-first "disaster" framing preserved).

Scenario shocks are on the factor-beta scale (S&P/VC ~ % return; Rates ~ +0.12 ≈ +200bp
given typical muni/bond loadings; Inflation/USD ~ standardized). Calibrated so headline
sleeve moves are realistic. cat_ov / name_ov add scenario-specific idiosyncratic hits;
each scenario carries its own mitigation-menu `opts` (ids into mitigations.OPT).

The DEFAULTS below are written for a generic client (no account names, no dollar
figures). A client's balance sheet personalizes them via data["scenarios"]:
  {"replace": {<key>: {<field>: <value>, ...}},   # field-level replace on a default
   "add":     [<full scenario dict>, ...],        # extra client-specific scenarios
   "drop":    [<key>, ...]}                       # remove a default

LIFE-EVENT scenarios (ratified with the Scenario Planner rename): a scenario may
carry `goal_ov` — it shocks the GOAL SET and spending rather than asset marks:
  "goal_ov": {"add":    [<goal dict>, ...],                 # e.g. a college target
              "modify": [{"kind": <goal kind>,              # first goal of kind
                          "annual_spending_delta"? / "amount_delta"? / <field>: <abs>}]}
The goals-through-the-tail grid re-scores each column under that scenario's
effective goal set ("Having a kid" = add college + raise retirement spending).
Life events aren't shipped as defaults — they're personal; clients add them via
the "add" overlay.
The desk's own household.json carries this account's prose (Sept powder, Parametric,
GOOGL) as exactly such an overlay — the library itself stays client-neutral.
"""
from __future__ import annotations

import copy

DEFAULT_SCENARIOS = [
    {"key": "crash", "ic": "📉", "name": "Equity crash (−30% SPX, 2008-style)",
     "desc": "Broad de-risking; flight-to-quality rallies bonds & munis.",
          "p": 0.08, "p_basis": "≈ the historical frequency of −30% SPX episodes (~1-in-12 years)",
     "tripwires": ['VIX term structure inverts', 'HY spreads +150bp in a month', 'SPX −10% from its high'],
"shocks": {"S&P 500": -0.30, "Venture Capital": -0.10, "Rates": -0.05, "USD": 0.06},
     "opts": ["cash_deploy", "put_index", "put_spread", "collar_eq", "tailfund", "trend"],
     "fix": {"tag": "DEPLOY", "action": "Buy the drawdown — deploy available cash toward target at lower prices. For an unlevered net buyer a crash is a discount, not a threat; an index hedge is usually the wrong instrument for an accumulator."}},
    {"key": "tech", "ic": "💻", "name": "Tech / AI wipeout (Nasdaq −45%)",
     "desc": "Mega-cap + AI unwind — hits any tech-tilted core (direct index, concentrated tech, cap-weight funds) hardest.",
          "p": 0.06, "p_basis": "sector-concentrated unwinds are rarer than broad crashes but deeper",
     "tripwires": ['hyperscaler capex guidance cuts', 'NDX underperforms SPX by 8%+', 'semiconductor orders roll over'],
"shocks": {"S&P 500": -0.25, "Venture Capital": -0.15, "Rates": -0.04},
     "cat_ov": {"direct_index": -0.10, "single_name_equity": -0.12, "public_equity": -0.04, "venture_private": -0.08},
     "opts": ["diversify", "trim", "exch_fund", "put_tech", "collar_conc", "tailfund"],
     "fix": {"tag": "DILUTE + TRIM", "action": "Attack the root cause — the tech-concentrated sleeve. Route new capital into NON-tech (intl/value/real assets/muni) to dilute the concentration at $0 tax; trim the concentrated sleeve only beyond that."}},
    {"key": "rates", "ic": "📈", "name": "Rate shock (+200bp)",
     "desc": "Duration repricing; munis/bonds/RE fall, equities de-rate.",
          "p": 0.15, "p_basis": "≈ the frequency of +150–200bp twelve-month moves since 1970",
     "tripwires": ['10y yield +50bp in a quarter', 'CPI re-accelerates two prints running', 'Fed dots shift up'],
"shocks": {"Rates": 0.12, "S&P 500": -0.10, "Inflation": 0.06, "USD": 0.06},
     "opts": ["dur_short", "rate_hedge", "realasset", "cash_deploy"],
     "fix": {"tag": "MINOR / HOLD", "action": "Little to do when the rate-sensitive sleeve is small and rising rates lift money-market income. Optionally shorten bond/muni duration if worried."}},
    {"key": "stagfl", "ic": "🔥", "name": "Stagflation (inflation + rates up, growth down)",
     "desc": "Real-terms hit to cash & bonds; equities de-rate; real assets partly hedge.",
          "p": 0.07, "p_basis": "rare regime, but the one factor models mis-hedge worst",
     "tripwires": ['CPI >4% while PMIs <50', 'breakevens rise as growth is revised down', 'wage growth sticky above 5%'],
"shocks": {"Inflation": 0.28, "Rates": 0.09, "S&P 500": -0.14, "Venture Capital": -0.10},
     "opts": ["realasset", "commod_trend", "put_index", "dur_short"],
     "fix": {"tag": "BALLAST", "action": "Add a real-asset ballast (TIPS / gold / commodities); owned housing with fixed-rate debt already hedges inflation."}},
    {"key": "vcwinter", "ic": "🥶", "name": "Venture winter / down-round wave",
     "desc": "Private marks reset ~−50%; recent-vintage direct checks lead down, with modest public-growth spillover.",
          "p": 0.12, "p_basis": "private-mark resets cluster; 2022-class winters ≈ 1-in-8 years",
     "tripwires": ['down-round share >30% of raises', 'VC fundraising −40% yoy', 'secondary discounts widen past 30%'],
"shocks": {"Venture Capital": -0.08, "S&P 500": -0.05}, "cat_ov": {"venture_private": -0.40},
     "opts": ["pace", "reserve", "secondary", "cash_deploy"],
     "fix": {"tag": "PACE", "action": "Slow new commitments and hold venture at/under its target weight; keep the fund/direct split balanced. Illiquid, so nothing to hedge after the fact."}},
    {"key": "housing", "ic": "🏚️", "name": "Housing / real-estate shock",
     "desc": "Local property + rate stress; the primary residence marks down.",
          "p": 0.07, "p_basis": "national shocks are rare; LOCAL ones are what hit a single residence",
     "tripwires": ['local inventory +50% yoy', 'days-on-market doubling', 'mortgage rates +100bp'],
"shocks": {"Rates": 0.07, "S&P 500": -0.08}, "cat_ov": {"real_estate": -0.22},
     "opts": ["insurance", "mort_cap", "accept"],
     "fix": {"tag": "INSURE / HOLD", "action": "A residence is a consumption asset and fixed-rate debt inflates away — a natural hedge. The action is adequate hazard coverage, not a market trade."}},
    {"key": "single_name", "ic": "⚖️", "name": "Concentrated single-name shock (−30%)",
     "desc": "An idiosyncratic hit to the largest concentrated single-name holding.",
          "p": 0.1, "p_basis": "idiosyncratic by definition — concentration makes it YOUR tail",
     "tripwires": ['gap-down >8% on company news', 'volume 3× average on weakness', 'analyst dispersion widening'],
"shocks": {"S&P 500": -0.04}, "cat_ov": {"single_name_equity": -0.30},
     "opts": ["put_single", "collar_single", "pvf", "exch_fund", "accept"],
     "fix": {"tag": "ACCEPT / SIZE", "action": "If the position is sized, a deliberate hold is defensible; a protective put floors it without selling (keeps a low basis intact)."}},
    {"key": "liqfreeze", "ic": "🧊", "name": "Liquidity freeze / credit crunch",
     "desc": "Spreads gap, risk sells off — the liquidity map below is the point here.",
          "p": 0.05, "p_basis": "genuine freezes are rare; their damage concentrates in levered books",
     "tripwires": ['bid-ask spreads widen across the board', 'HY issuance window closes', 'funding rates spike (FRA-OIS)'],
"shocks": {"S&P 500": -0.18, "Venture Capital": -0.20, "Rates": 0.05},
     "opts": ["cash_buffer", "credit_line", "put_index", "tailfund"],
     "fix": {"tag": "MAINTAIN", "action": "Keep a cash buffer and zero leverage — then a freeze cannot force selling. The only way to break this defense is to add margin, so don't."}},
    # a HUMAN disaster: earnings interrupted. Exists only when the balance sheet
    # capitalizes income as a human_capital sleeve (requires: human_capital) —
    # then the planner stresses it like any other asset, per the income-as-asset ruling.
    {"key": "income_shock", "ic": "💼", "name": "Income shock (job loss / disability)",
     "desc": "Earnings interrupted for an extended stretch — the capitalized-income sleeve takes the hit, savings pause, and goals feel it before markets do.",
          "p": 0.06, "p_basis": "≈ annual involuntary-separation odds for established professionals",
     "tripwires": ['industry layoff wave', 'employer earnings misses', 'own role scope shrinking'],
"shocks": {"S&P 500": -0.05}, "cat_ov": {"human_capital": -0.50}, "requires": "human_capital",
     "opts": ["disability_ins", "term_life", "cash_buffer", "credit_line"],
     "fix": {"tag": "INSURE / HOLD", "action": "Insure the earner, not the portfolio: disability + term life sized to the capitalized income, plus a cash buffer measured in months of spending. This is the disaster most households actually meet."}},
    # a TAX disaster, not a market one: the incoming gain lands with NO harvest
    # offset, so the reserve snaps from net to gross. Markets flat; only the tax
    # row moves. Shown only when the balance sheet actually has an offset at risk
    # (requires: tax_offset) — mitigation = build the offset BEFORE the gain lands.
    {"key": "taxbomb", "ic": "🧾", "name": "Unsheltered gain (harvest engine fails)",
     "desc": "The windfall lands but the loss harvest doesn't — the tax reserve snaps to the full gross bill. Markets flat; the bill isn't.",
          "p": 0.15, "p_basis": "an ENGINE risk, not a market one — depends on the harvest pace holding",
     "tripwires": ['realized harvest behind the plan line', 'market grinds up (no losses to make)', 'Q4 nears with the offset gap open'],
"shocks": {}, "tax_ov": {"no_offset": True}, "requires": "tax_offset",
     "opts": ["harvest_engine", "di_convert", "daf_gift", "exch_fund", "pvf"],
     "fix": {"tag": "HARVEST", "action": "Build the offset BEFORE the gain lands: turn the largest liquid sleeves into harvest engines and pre-commit any planned giving as appreciated shares. Once the gain is realized unsheltered, only deferral structures remain."}},
]

TAG_TONE = {"DEPLOY": "violet", "DILUTE + TRIM": "amber", "MINOR / HOLD": "slate", "BALLAST": "teal",
            "PACE": "slate", "INSURE / HOLD": "slate", "ACCEPT / SIZE": "slate", "MAINTAIN": "emerald",
            "HARVEST": "teal"}


def scenarios_for(data):
    """The scenario set for one client: library defaults + the client's overlay."""
    scen = copy.deepcopy(DEFAULT_SCENARIOS)
    ov = data.get("scenarios") or {}
    rep = ov.get("replace") or {}
    for sc in scen:
        patch = rep.get(sc["key"])
        if patch:
            for k, v in patch.items():
                sc[k] = copy.deepcopy(v)
    drop = set(ov.get("drop") or [])
    scen = [sc for sc in scen if sc["key"] not in drop]
    scen.extend(copy.deepcopy(ov.get("add") or []))
    return scen
