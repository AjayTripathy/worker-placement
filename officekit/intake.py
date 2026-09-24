"""intake — build a valid BalanceSheet v1 from simple ANSWERS, no betas required.

This is the funnel every Phase-1 entry point writes through:
  - the CLI wizard (officekit.wizard) collects answers interactively,
  - the LLM statement agent emits the same answers JSON (officekit/INTAKE_AGENT.md),
  - CSV imports are resolved by officekit.importers.
The value-add over raw schema JSON: category-prior beta assignment, auto shorts,
kind derivation, the incoming-windfall -> cash_pending + tax-model wiring, and
validation at the end (fail loud, never render from a malformed sheet).

ANSWERS shape (all sleeves WITHOUT beta vectors — those come from the priors):
{
  "owner": "Sam", "as_of": "YYYY-MM-DD",
  "profile": {uses_leverage, net_buyer, premium_selling_allowed, decumulating,
              concentrated_low_basis},                      # bools
  "sleeves": [{"category": ..., "value": ..., "name"?, "target_pct"?, "style"?,
               "confidence"?: known|assumption|tbd, "risks"?: [...],
               "rate_pct"? (debt), "holdings"?: [...]}],
  "imports": [{"kind": "positions_csv", "path": ..., "account"?}],   # optional
  "positions": {"account"?, "rows": [{"symbol", "value"}, ...]},     # typed holdings —
               # same classifier as the CSV; the honest cold path
  "incoming": {"amount": ..., "eta": "Dec", "character": ltcg|ordinary|return_of_capital,
               "rate": 0.30, "harvest_losses"?: 0,
               "cadence"?: once|monthly|quarterly|annual,
               "planning_period"?: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}}
               # amount is total gross for the period, never multiplied by cadence
}
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from officekit.betas import assign_betas
from officekit.fmt import fmt_usd as _fmt
from officekit.importers import run_import
from officekit.schema import validate

LIABILITY_CATEGORIES = {"real_estate_debt", "tax_reserve"}

DEFAULT_NAMES = {
    "public_equity": "Public Equity",
    "direct_index": "Direct-Index Sleeve",
    "single_name_equity": "Concentrated Single Name",
    "venture_private": "Venture / Private",
    "real_estate": "Real Estate — Primary Residence",
    "municipal_credit": "Municipal Bonds",
    "fixed_income": "Bonds",
    "alpha_market_neutral": "Alpha / Market-Neutral",
    "cash": "Cash / Money Market",
    "cash_pending": "Incoming Cash (pending)",
    "real_estate_debt": "Mortgage",
    "human_capital": "Human Capital — capitalized earnings",
}

DEFAULT_RISKS = {
    "public_equity": ["Market drawdown"],
    "direct_index": ["Single-manager / single-strategy concentration"],
    "single_name_equity": ["Single-name idiosyncratic", "Concentration — sized position"],
    "venture_private": ["Illiquid / no exit control", "Power-law — most seed checks go to zero"],
    "real_estate": ["Illiquid — consumption asset", "Local market / rate-sensitive"],
    "municipal_credit": ["Duration / rate sensitivity", "Issuer credit concentration"],
    "fixed_income": ["Rate duration", "Inflation erosion of fixed coupon"],
    "alpha_market_neutral": ["Uncalibrated edge", "Execution"],
    "cash": ["Reinvestment / cash drag", "Inflation erosion"],
    "cash_pending": ["Deployment timing", "Not yet landed"],
    "real_estate_debt": ["Fixed obligation regardless of asset marks"],
    "human_capital": ["Capitalized future earnings — a MODEL, not a statement",
                      "Career / single-employer concentration",
                      "Uninsurable portions (job loss); insure the rest (disability/life)"],
}

HC_DISCOUNT = 0.04    # real discount rate for capitalizing earnings
HC_MAX_YEARS = 45


def _human_capital(inc, as_of):
    """Capitalize an income stream into a human-capital sleeve: PV of an annuity
    of `annual` for `years` (or until a date) at a real discount rate. An asset
    with a beta like everything else (principal-ratified 2026-09-02) — but tagged
    `assumption`, because it is a model of the future, not a statement."""
    annual = float(inc["annual"])
    years = inc.get("years")
    if years is None and inc.get("until"):
        d1 = datetime.strptime(str(inc["until"])[:10], "%Y-%m-%d")
        d0 = datetime.strptime(as_of, "%Y-%m-%d")
        years = max((d1 - d0).days / 365.25, 0.0)
    years = min(float(years or 0), HC_MAX_YEARS)
    if annual <= 0 or years <= 0:
        return None
    r = float(inc.get("discount", HC_DISCOUNT))
    pv = annual * (1 - (1 + r) ** -years) / r
    return {
        "category": "human_capital",
        "name": inc.get("label") or DEFAULT_NAMES["human_capital"],
        "value": pv, "confidence": "assumption", "style": inc.get("style"),
        "meta": {"annual": round(annual), "years": round(years, 1), "discount": r,
                 "note": f"PV of {_fmt(annual)}/yr for {years:.0f}y at {r*100:.0f}% real"},
    }


def auto_short(name):
    """A card/matrix label from a sleeve name: text before ' — '/'(' then <=14 chars
    trimmed at a word boundary."""
    base = name.split(" — ")[0].split(" (")[0].strip()
    if len(base) <= 14:
        return base
    out = ""
    for w in base.split(" "):
        cand = (out + " " + w).strip()
        if len(cand) > 14:
            break
        out = cand
    return out or base[:14]


def _normalize_sleeve(raw):
    cat = raw["category"]
    kind = "liability" if cat in LIABILITY_CATEGORIES else "asset"
    value = float(raw["value"])
    if kind == "liability" and value > 0:
        value = -value                     # accept "400000" for a mortgage
    s = {
        "name": raw.get("name") or DEFAULT_NAMES.get(cat, cat),
        "kind": kind, "category": cat,
        "value": round(value, 2) if cat in {"cash", "cash_pending", "tax_reserve"} and value != round(value) else round(value),
        "target_pct": raw.get("target_pct"),
        "_confidence": raw.get("confidence", "known"),
        "risks": raw.get("risks") or list(DEFAULT_RISKS.get(cat, [])),
    }
    if raw.get("id"):
        s["id"] = raw["id"]
    if raw.get("holdings"):
        s["holdings"] = raw["holdings"]
    if raw.get("strategy"):
        s["strategy"] = raw["strategy"]
    if raw.get("strategies"):
        s["strategies"] = raw["strategies"]
    if raw.get("eta"):
        s["eta"] = raw["eta"]
    meta = dict(raw.get("meta") or {})
    for field in ("rate_pct", "term_years", "terms_as_of", "property_tax_id"):
        if raw.get(field) is not None:
            meta[field] = raw[field]
    if meta:
        s["meta"] = meta
    assign_betas(s, style=raw.get("style"))
    s["short"] = raw.get("short") or auto_short(s["name"])
    return s


# A capital gain must NEVER book tax-free (2026-09-07): if no rate is given we
# apply a conservative FLOOR = top federal LTCG (20%) + NIIT (3.8%) + the state's
# top long-term rate, flagged as an assumption. A curated table of the states
# that actually tax gains meaningfully; anything absent adds 0 and says so.
FED_LTCG_FLOOR = 0.238
STATE_LTCG_TOP = {
    "CA": 0.133, "NY": 0.109, "NJ": 0.1075, "HI": 0.11, "OR": 0.099, "MN": 0.0985,
    "MA": 0.09, "CT": 0.0699, "VT": 0.0875, "DC": 0.1075, "WA": 0.07,  # WA gains tax
    # no state income tax on gains
    "TX": 0.0, "FL": 0.0, "NV": 0.0, "WY": 0.0, "SD": 0.0, "AK": 0.0, "TN": 0.0, "NH": 0.0,
}


def _tax_model(inc, as_of):
    """A flat-mode tax model from the windfall answers (no live harvest feed yet)."""
    char = inc.get("character", "ltcg")
    if char == "return_of_capital":
        return None
    state = (inc.get("state") or "").strip().upper()
    rate = inc.get("rate")
    assumed = False
    if rate in (None, "", 0):
        if char == "ordinary":
            return None                    # ordinary (escrow interest etc.) still needs a stated rate
        # a capital gain with no rate: assume the conservative floor + state top
        rate = FED_LTCG_FLOOR + STATE_LTCG_TOP.get(state, 0.0)
        assumed = True
    rate = float(rate)
    tm = {
        "as_of": as_of,
        "inflow_id": inc.get("id"),
        "incoming_gross": round(float(inc["amount"]), 2),
        "character": char,
        "state": state or None,
        "rate_assumed": assumed,
        "taxable_fraction": float(inc.get("taxable_fraction", 1.0)),
        "harvest_losses_2026": round(float(inc.get("harvest_losses", 0))),
        "_confidence": "assumption",
        "note": (("ASSUMED floor rate: 23.8% federal LTCG+NIIT"
                  + (f" + {state} top {STATE_LTCG_TOP[state]*100:.2f}%" if state in STATE_LTCG_TOP and STATE_LTCG_TOP[state] else
                     (f" + {state} state tax NOT modeled — confirm" if state else " + NO state given — federal only, confirm"))
                  + f" = {rate*100:.1f}%. Confirm with a tax preparer.") if assumed else
                 "Built by officekit intake from the user's answers — flat harvest offset, "
                 "no live harvest feed. Confirm rates with a tax preparer."),
    }
    # only the rate that applies to the stated character — never fabricate the other
    tm["rate_ordinary" if char == "ordinary" else "rate_ltcg"] = rate
    return tm


def build_from_answers(answers, sma_symbols=None, sma_label="Direct-index SMA"):
    """answers dict -> validated BalanceSheet v1 data dict (raises on invalid).

    Identity: mints a stable office_id (UUID) on first build and writes it back
    into the ANSWERS dict, so callers that persist answers.json keep the same
    identity across rebuilds — the multitenant key for every document this
    office ever emits. Goals get per-goal ids the same way (goal grading must
    survive reordering)."""
    as_of = answers.get("as_of") or date.today().isoformat()
    office_id = answers.setdefault("office_id", str(uuid.uuid4()))
    from officekit.commitments import prepare_answers
    prepare_answers(answers, as_of)
    # human-confirmed symbol mappings (AI-1 confirm step) — durable in answers,
    # so rebuilds re-classify identically with no model in the loop
    fund_map = {k.upper(): tuple(v) for k, v in (answers.get("fund_map") or {}).items()}
    for g in answers.get("goals") or []:
        g.setdefault("id", str(uuid.uuid4()))
    sleeves = [_normalize_sleeve(s) for s in answers.get("sleeves", [])]
    for spec in answers.get("imports", []):
        for s in run_import(spec, extra_map=fund_map or None):
            s["short"] = s.get("short") or auto_short(s["name"])
            sleeves.append(s)
    # manually-entered holdings: same classification pipeline as a statement upload
    pos = answers.get("positions")
    if pos and pos.get("rows"):
        from officekit.importers import classify_positions
        for s in classify_positions(pos["rows"], account=pos.get("account", "brokerage"),
                                    extra_map=fund_map or None, source="entered holdings",
                                    sma_symbols=sma_symbols, sma_label=sma_label):
            s["short"] = s.get("short") or auto_short(s["name"])
            s.setdefault('meta', {})['position_rows'] = True
            sleeves.append(s)
    tax_model = None
    from officekit.staging import num as _num
    lcf = _num(answers.get("loss_carryforward"))     # prior-year capital-loss carryforward (face $)
    inc = answers.get("incoming")
    from officekit.inflows import progress, active_receipts
    if any(e["inflow_id"] != (inc or {}).get("id") for e in active_receipts(answers)):
        raise ValueError("An inflow with recorded receipts cannot be removed or replaced; reverse incorrect receipts first")
    inflow = progress(answers)
    if inc and float(inc.get("amount", 0)) > 0:
        pending = {
            "id": inc.get("id"),
            "category": "cash_pending", "value": inflow["pending"],
            "name": f"Incoming Cash ({inc.get('eta', 'pending')})" if inc.get("eta") else DEFAULT_NAMES["cash_pending"],
            "eta": inc.get("eta"), "confidence": inc.get("confidence", "known"),
        }
        if inflow["pending"] > 0:
            sleeves.append(_normalize_sleeve(pending))
        tax_model = _tax_model(inc, as_of)
        if tax_model:
            tax_model.update(received_gross=inflow["received"], withheld=inflow["withheld"])
        elif inc.get("character") != "return_of_capital" and inflow["received"]:
            raise ValueError("Confirm the inflow's tax rate before recording a receipt")
        elif inflow["withheld"]:
            # Return of capital normally has no tax model, but a recorded
            # withholding still needs an explicit non-cash credit.
            tax_model = {"as_of": as_of, "inflow_id": inc["id"], "incoming_gross": float(inc["amount"]),
                         "character": "return_of_capital", "withheld": inflow["withheld"],
                         "received_gross": inflow["received"]}
    if lcf > 0:
        # a carryforward has value even with no windfall (offsets future gains).
        # Attach to the windfall's model, or stand one up to value the deferred
        # tax asset at the federal LTCG floor when there's no gain yet.
        if tax_model is None:
            tax_model = {"as_of": as_of, "incoming_gross": 0, "character": "ltcg",
                         "taxable_fraction": 1.0, "rate_ltcg": FED_LTCG_FLOOR,
                         "rate_assumed": True, "_confidence": "assumption",
                         "note": "No windfall — the loss carryforward is valued at the 23.8% "
                                 "federal LTCG floor against future gains. Confirm with a preparer."}
        tax_model["loss_carryforward"] = round(lcf)
    hc = answers.get("income")
    if hc:
        raw = _human_capital(hc, as_of)
        if raw:
            sleeves.append(_normalize_sleeve(raw))

    profile = {"uses_leverage": False, "net_buyer": True, "premium_selling_allowed": False,
               "decumulating": False, "concentrated_low_basis": False}
    profile.update({k: bool(v) for k, v in (answers.get("profile") or {}).items()})

    data = {
        "office_id": office_id,
        "as_of": as_of,
        "note": "Balance sheet built by officekit intake. Values tagged 'known' are "
                "statement/user-sourced; 'tbd' are placeholders to correct — never fabricated. "
                "Betas are category PRIORS (first-pass estimates), to refine from realized returns.",
        "owner": {"first_name": answers.get("owner")} if answers.get("owner") else {},
        "factors": ["S&P 500", "Venture Capital", "Mortgage Debt", "Inflation", "Rates", "USD"],
        "sleeves": sleeves,
        "profile": profile,
    }
    if tax_model:
        data["tax_model"] = tax_model
    if answers.get('security_basis_reviews'):
        from copy import deepcopy
        data['security_basis_reviews'] = deepcopy(answers['security_basis_reviews'])
    if answers.get('beta_programs'):
        from copy import deepcopy
        data['beta_programs'] = deepcopy(answers['beta_programs'])
    if inc:
        data["inflow"] = inflow
        data['inflow_terms'] = {'character': inc.get('character', 'ltcg'),
                                'cadence': inc.get('cadence', 'once'),
                                'planning_period': inc.get('planning_period')}
    # Intuit the commitments the balance sheet implies (mortgage service,
    # lifestyle spending) alongside the user's own goals. Implicit goals are
    # re-derived every build and never written back to answers.
    explicit = list(answers.get("goals") or [])
    probe = dict(data)
    probe["goals"] = explicit
    from officekit.commitments import resolve
    commitments = resolve(probe, answers.get("commitments") or [])
    data["commitments"] = commitments
    merged = explicit + [dict(c, kind="expense", implicit=True, fixed=True)
                         for c in commitments if c.get("annual_amount") is not None]
    if merged:
        data["goals"] = merged
    if answers.get("scenarios"):
        data["scenarios"] = answers["scenarios"]     # life-event / custom scenario overlay
    if answers.get("strategy_decisions"):
        data["strategy_decisions"] = answers["strategy_decisions"]   # mandate paper trail
    if not any(s["kind"] == "asset" for s in sleeves):
        raise ValueError("intake: at least one asset sleeve is required")
    problems = validate(data)
    if problems:
        raise ValueError("intake produced an invalid balance sheet: " + "; ".join(problems))
    return data
