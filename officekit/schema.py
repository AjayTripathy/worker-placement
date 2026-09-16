"""schema — the BalanceSheet v1 data contract for officekit.

The data dict IS the product boundary: every importer (manual wizard, statement
parser, aggregator) writes this shape, and everything downstream (build_model,
both renderers) reads only it. stdlib-only validation: validate() returns a list
of problem strings (empty = valid) so callers can fail loud or render-with-warnings.

Identity (multitenant):
  office_id    UUID string — the office's stable identity, minted once by intake
               and stamped on every document and ledger record this office emits.
               Optional in v1 (pre-GUID sheets stay valid); required at the
               hosted tier. Goals carry per-goal `id` UUIDs for the same reason.

Required:
  as_of        "YYYY-MM-DD"
  factors      [str, ...]                      — factor names (order = display order)
  sleeves      [{name, kind: asset|liability, category, value, beta{factor: float},
                 target_pct?, _confidence: known|assumption|tbd, risks?[], short?,
                 eta? (cash_pending only), meta?{}, holdings?[]}]
  profile      {uses_leverage, net_buyer, premium_selling_allowed, decumulating,
                concentrated_low_basis}        — bools; scores the mitigation menu

Optional life-planning + strategy structure (Phase 2):
  goals              [{kind: retirement|spending|liquidity_floor, label,
                       date? "YYYY-MM-DD", amount? | annual_spending?}]
                     — the Office shows baseline status; the Scenario Planner
                     re-scores every goal per scenario ("goals through the tail")
  sleeves[].strategies     optional list of strategy keys — membership is
                           MANY-TO-MANY: one asset can serve several strategies
                           (T&D is Japan value AND the steepener). Edges are
                           whole-asset, never fractional. Also valid on
                           holdings[] for membership finer than the sleeve.
  sleeves[].strategy       legacy singular form of the above —
                           strategies are SLEEVES, not a blended alpha line
  sleeves[].holdings[].adjudication  optional {verdict, date, ref} — every ticker
                           a strategy picks carries its deliberation/adjudication

Optional personalization (all have generic engine defaults):
  owner              {first_name}
  category_labels    {category: display label}
  opportunities      [{icon,title,tone,chip,body,value}] — bodies/values may use
                     {net_txt} {net_deployable} {para_pct} format placeholders
  office             {liquidity_note_tail}
  scenario_text      {playbook_lead, liquidity_read, liquidity_note, claims_label, foot}
                     (legacy key "disaster" still honored)
                     — templates over {sept_net}{p0}{p1} / {dd_pct}{worst_access}{claims}{thedge}
  scenarios          {replace:{key:patch}, add:[scenario], drop:[key]}
  mitigation_labels  {opt_id: display name}
  strategy_decisions {strategy_id: {status: implemented|considering|planned|declined,
                       target_pct?, note?}} — the STRATEGIES page renders these;
                       no decision recorded = honestly NOT DECIDED, never inferred
  tax_model          accrued-tax reserve on incoming cash (see model.tax_reserve)
  income_streams     informational only
"""
from __future__ import annotations

import json
import re
from pathlib import Path

KINDS = {"asset", "liability"}
CONFIDENCE = {"known", "assumption", "tbd", None}
CATEGORIES = {"direct_index", "public_equity", "single_name_equity", "venture_private",
              "alpha_market_neutral", "municipal_credit", "fixed_income", "cash",
              "cash_pending", "real_estate", "real_estate_debt", "tax_reserve", "human_capital",
              "options_overlay", "tax_asset"}
PROFILE_FLAGS = ("uses_leverage", "net_buyer", "premium_selling_allowed",
                 "decumulating", "concentrated_low_basis")
TONES = {"violet", "emerald", "amber", "slate"}
GOAL_KINDS = {"retirement", "spending", "liquidity_floor", "tax_efficiency", "expense"}


def validate(data) -> list[str]:
    """Return a list of problems (empty list = valid BalanceSheet v1)."""
    p = []
    if not isinstance(data, dict):
        return ["data is not a dict"]
    for key in ("as_of", "factors", "sleeves", "profile"):
        if key not in data:
            p.append(f"missing required key: {key}")
    factors = data.get("factors") or []
    if not (isinstance(factors, list) and factors and all(isinstance(f, str) for f in factors)):
        p.append("factors must be a non-empty list of strings")
    for i, s in enumerate(data.get("sleeves") or []):
        tag = f"sleeves[{i}] ({s.get('name', '?')})"
        for key in ("name", "kind", "category", "value", "beta"):
            if key not in s:
                p.append(f"{tag}: missing {key}")
        if s.get("kind") not in KINDS:
            p.append(f"{tag}: kind must be asset|liability")
        if s.get("category") not in CATEGORIES:
            p.append(f"{tag}: unknown category {s.get('category')!r}")
        if not isinstance(s.get("value"), (int, float)):
            p.append(f"{tag}: value must be numeric")
        elif s.get("kind") == "liability" and s["value"] > 0:
            p.append(f"{tag}: liability value must be <= 0")
        if s.get("_confidence") not in CONFIDENCE:
            p.append(f"{tag}: _confidence must be known|assumption|tbd")
        beta = s.get("beta") or {}
        for f in beta:
            if f not in factors:
                p.append(f"{tag}: beta factor {f!r} not in factors")
        strats = s.get("strategies")
        if strats is not None and (not isinstance(strats, list)
                                   or not all(isinstance(t, str) and t for t in strats)):
            p.append(f"{tag}: strategies must be a list of strategy-key strings")
        for j, h in enumerate(s.get("holdings") or []):
            hs = h.get("strategies")
            if hs is not None and (not isinstance(hs, list)
                                   or not all(isinstance(t, str) and t for t in hs)):
                p.append(f"{tag}: holdings[{j}].strategies must be a list of strategy-key strings")
            adj = h.get("adjudication")
            if adj is not None and not (isinstance(adj, dict) and adj.get("verdict")):
                p.append(f"{tag}: holdings[{j}].adjudication needs at least a verdict")
    oid = data.get("office_id")
    if oid is not None and not re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", str(oid)):
        p.append("office_id must be a UUID string")
    for i, g in enumerate(data.get("goals") or []):
        tag = f"goals[{i}] ({g.get('label', '?')})"
        kind = g.get("kind")
        if kind not in GOAL_KINDS:
            p.append(f"{tag}: kind must be one of {sorted(GOAL_KINDS)}")
        if kind == "retirement" and not isinstance(g.get("annual_spending"), (int, float)):
            p.append(f"{tag}: retirement needs numeric annual_spending")
        if kind in ("spending", "liquidity_floor") and not isinstance(g.get("amount"), (int, float)):
            p.append(f"{tag}: {kind} needs a numeric amount")
        if kind == "expense" and not isinstance(g.get("annual_amount", g.get("amount")), (int, float)):
            p.append(f"{tag}: expense needs a numeric annual_amount")
        if g.get("date") and not re.match(r"^\d{4}-\d{2}-\d{2}", str(g["date"])):
            p.append(f"{tag}: date must be YYYY-MM-DD")
    prof = data.get("profile") or {}
    for f in PROFILE_FLAGS:
        if f in prof and not isinstance(prof[f], bool):
            p.append(f"profile.{f} must be a bool")
    tm = data.get("tax_model")
    if tm:
        if not isinstance(tm.get("incoming_gross"), (int, float)):
            p.append("tax_model.incoming_gross must be numeric")
        char = tm.get("character", "ltcg")
        if char == "ordinary" and "rate_ordinary" not in tm:
            p.append("tax_model: character=ordinary requires rate_ordinary")
        if char not in ("ordinary", "return_of_capital") and "rate_ltcg" not in tm:
            p.append("tax_model: requires rate_ltcg")
        if tm.get("harvest_mode") == "progression":
            for key in ("harvest_project_from", "harvest_project_to"):
                if key not in tm:
                    p.append(f"tax_model: progression mode requires {key}")
    for i, o in enumerate(data.get("opportunities") or []):
        tag = f"opportunities[{i}]"
        for key in ("icon", "title", "tone", "chip", "body", "value"):
            if key not in o:
                p.append(f"{tag}: missing {key}")
        if o.get("tone") not in TONES:
            p.append(f"{tag}: tone must be one of {sorted(TONES)}")
    for sid, dec in (data.get("strategy_decisions") or {}).items():
        if not isinstance(dec, dict) or dec.get("status") not in (
                "implemented", "considering", "planned", "declined"):
            p.append(f"strategy_decisions[{sid}]: status must be implemented|considering|planned|declined")
        elif dec.get("target_pct") is not None and not isinstance(dec["target_pct"], (int, float)):
            p.append(f"strategy_decisions[{sid}]: target_pct must be numeric")
        if isinstance(dec, dict):
            for o in dec.get("origins") or []:
                if o.get("source") not in ("principal", "scenario", "agent", "goal", "holding"):
                    p.append(f"strategy_decisions[{sid}]: origin source must be "
                             "principal|scenario|agent|goal|holding")
    scen = data.get("scenarios") or {}
    for key, patch in (scen.get("replace") or {}).items():
        if not isinstance(patch, dict):
            p.append(f"scenarios.replace[{key}] must be a dict")
    for i, sc in enumerate(scen.get("add") or []):
        for key in ("key", "ic", "name", "desc", "shocks", "opts", "fix"):
            if key not in sc:
                p.append(f"scenarios.add[{i}]: missing {key}")
    return p


def load_balance_sheet(path, strict=True):
    """Load + validate a BalanceSheet v1 JSON file. strict=True raises on problems."""
    data = json.loads(Path(path).read_text())
    problems = validate(data)
    if problems and strict:
        raise ValueError("invalid balance sheet: " + "; ".join(problems))
    return data
