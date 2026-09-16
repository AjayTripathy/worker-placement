"""thesis_board — assemble per-thesis strategy sleeves from the office's OWN data
(the court engine's `adjudications.jsonl` + the office's positions), replacing the
office's live read of the desk positions board.

Migration (2026-09-11, desk-deprecation): the court/docket ENGINE already lives in
officekit (`officekit_ai.court` writes adjudications.jsonl; `officekit_ai.docket`
drains the queue). What was missing was the assembler that joins adjudications +
positions into the thesis-sleeve shape the strategy page renders. This is it —
office-native (reads only the office folder). `import_desk_board()` is the
one-time/transition importer that snapshots the desk's positions board into the
office-owned `answers["desk_theses"]` so the principal's existing theses become
owned data; after that the office never reads desk/data for theses.

The output contract (consumed by render_strategies) is one dict per sleeve:
    {sid, label, value, n, thesis, verdict, court_date, edge, next_date, positions[]}
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

_SKIP_SLEEVES = {"held", "(untagged)", "", None}     # non-thesis buckets on the desk board


def _positions_value(folder):
    """symbol -> market value, from the office's OWN positions (answers.json)."""
    out = {}
    try:
        ans = json.loads((Path(folder) / "answers.json").read_text())
        for r in (ans.get("positions") or {}).get("rows", []):
            s = (r.get("symbol") or "").upper()
            if s:
                out[s] = out.get(s, 0.0) + float(r.get("value") or 0)
    except Exception:
        pass
    return out


def _label(sid):
    return str(sid).replace("_", " ").title()


def _finalize(sid, positions, meta):
    bysym = {}
    for p in positions:                              # dedupe by symbol, keep the latest
        bysym[p["symbol"]] = p
    poss = sorted(bysym.values(), key=lambda x: -(x["mv"] or 0))
    return {"sid": sid, "label": _label(sid), "value": round(sum(p["mv"] for p in poss)),
            "n": len(poss), "thesis": meta.get("thesis", ""), "verdict": meta.get("verdict", ""),
            "court_date": meta.get("court_date", ""), "edge": meta.get("edge", ""),
            "next_date": meta.get("next_date", ""), "positions": poss}


def from_adjudications(folder):
    """Thesis sleeves assembled from the office's OWN court adjudications
    (adjudications.jsonl) joined to the office's positions. Empty until courts run
    in the office. Groups by the adjudication's `strategy` (== the sleeve)."""
    try:
        from officekit_ai.court import load_adjudications
        adjs = load_adjudications(folder)
    except Exception:
        adjs = []
    if not adjs:
        return []
    pv = _positions_value(folder)
    groups = defaultdict(lambda: {"positions": [], "meta": {}})
    latest = {}
    for a in sorted(adjs, key=lambda a: a.get("date", "")):
        if a.get("subject_kind", "security") != "security":
            continue
        latest[(a.get("strategy") or a.get("sleeve"), str(a.get("symbol") or "").upper())] = a
    for a in sorted(latest.values(), key=lambda a: a.get("date", ""), reverse=True):
        sid = a.get("strategy") or a.get("sleeve")
        if sid in _SKIP_SLEEVES:
            continue
        sym = (a.get("symbol") or "").upper()
        g = groups[sid]
        g["positions"].append({"symbol": sym, "mv": round(pv.get(sym, 0.0)),
                               "verdict": a.get("verdict"), "date": a.get("date")})
        for src, dst in (("thesis", "thesis"), ("rationale", "thesis"), ("verdict", "verdict"),
                         ("date", "court_date"), ("edge", "edge"), ("next_date", "next_date")):
            if a.get(src) and not g["meta"].get(dst):
                g["meta"][dst] = a.get(src)
    return sorted((_finalize(sid, g["positions"], g["meta"]) for sid, g in groups.items()),
                  key=lambda x: -x["value"])


def import_desk_board(board_path):
    """TRANSITION importer: snapshot the desk positions board into the thesis-sleeve
    shape (to be stored office-owned in answers['desk_theses']). This is the ONLY
    desk read, and it's an explicit import — not a per-build live dependency."""
    try:
        board = json.loads(Path(board_path).read_text())
    except Exception:
        return []
    groups = defaultdict(lambda: {"mv": 0.0, "positions": [], "meta": {}})
    for p in board.get("positions", []):
        sid = p.get("sleeve")
        if sid in _SKIP_SLEEVES:
            continue
        g = groups[sid]
        g["mv"] += p.get("mv_usd", 0) or 0
        g["positions"].append({"symbol": (p.get("symbol") or "").upper(),
                               "mv": round(p.get("mv_usd", 0) or 0),
                               "verdict": p.get("verdict"), "upnl": round(p.get("upnl_usd", 0) or 0),
                               "next_date": p.get("next_date")})
        for k in ("thesis", "verdict", "court", "court_date", "edge", "next_date"):
            if p.get(k) and not g["meta"].get(k):
                g["meta"][k] = p.get(k)
    out = []
    for sid, g in groups.items():
        f = _finalize(sid, g["positions"], g["meta"])
        out.append(f)
    return sorted(out, key=lambda x: -x["value"])


# ------------------------------------------------- taxonomy (goal + scenario lenses)
# A risk BUCKET per thesis sleeve — the axis that relates to BOTH the goal it funds
# (horizon/liquidity fit) and the factor-shock scenarios (how it behaves in a crash).
# Curated for the known sleeves; a keyword fallback catches new ones. Enumeration
# and these groupings are separate from how a sleeve gets implemented (its positions).
_BUCKET_OF = {
    # Defensive / ballast — carry, real assets, quality, financials
    "energy_realasset": "defensive", "real_asset_ballast": "defensive", "quality_carry": "defensive",
    "pc_specialty_quality": "defensive", "managed_care_pbm": "defensive", "financials_pool": "defensive",
    "frontier_banks": "defensive", "satellite_value": "defensive",
    # Cyclical value — deep/net-net value across regions
    "japan_netnet": "cyclical_value", "japan_value": "cyclical_value", "japan_deepvalue": "cyclical_value",
    "deep_value": "cyclical_value", "deep_value_thesis1": "cyclical_value", "deep_value_scan5": "cyclical_value",
    "europe_value_screen": "cyclical_value", "euronext_orphans": "cyclical_value",
    "korea_deepvalue": "cyclical_value", "korea_valueup": "cyclical_value",
    # High-beta growth — thematic
    "ai_application": "growth", "ai_sass_dislocation": "growth", "space_growth": "growth",
    "glp1_medtech": "growth", "diagnostics": "growth",
    # Idiosyncratic / event — catalysts, arb, tails
    "court_gates": "idiosyncratic", "catalyst_sleeve": "idiosyncratic", "slate4": "idiosyncratic",
    "country_risk_arb": "idiosyncratic", "ukraine_recovery": "idiosyncratic", "k_shaped_bottom": "idiosyncratic",
    "consumer": "idiosyncratic", "dogfood": "idiosyncratic", "alpha": "idiosyncratic",
}
BUCKETS = {   # ordered; scenario behavior across the 9 factor-shock scenarios
    "defensive": {"label": "Defensive / ballast",
                  "scenarios": "Intended ballast/carry role; crash and inflation resilience require position-level stress estimates.",
                  "goal_fit": "near"},
    "cyclical_value": {"label": "Cyclical value",
                       "scenarios": "Value/re-rating thesis; both broad-market and sector drawdowns remain possible.",
                       "goal_fit": "near"},
    "growth": {"label": "High-beta growth",
               "scenarios": "Growth thesis with a long payoff horizon; exposure depends on the actual holdings.",
               "goal_fit": "long"},
    "idiosyncratic": {"label": "Idiosyncratic / event",
                      "scenarios": "Event-driven thesis; market correlation, financing and break risk are unverified by this label.",
                      "goal_fit": "near"},
}
_KW = [("growth", ("ai", "space", "growth", "glp1", "medtech", "diagnostic", "sass")),
       ("defensive", ("carry", "realasset", "real_asset", "energy", "ballast", "bank", "quality", "satellite", "financial")),
       ("idiosyncratic", ("catalyst", "court", "slate", "arb", "ukraine", "k_shaped", "consumer", "dogfood", "alpha", "event")),
       ("cyclical_value", ("value", "netnet", "deep", "orphan", "screen", "valueup"))]


def bucket_of(sid):
    b = _BUCKET_OF.get(sid)
    if b:
        return b
    s = str(sid).lower()
    for bucket, keys in _KW:
        if any(k in s for k in keys):
            return bucket
    return "cyclical_value"


def _bucket_for(t):
    """A thesis's bucket: a contributed pack's DECLARED bucket wins (the author
    chose it), else the curated/keyword classifier by sid."""
    b = t.get("bucket")
    return b if b in BUCKETS else bucket_of(t.get("sid", ""))


def by_scenario(theses):
    """Thesis sleeves grouped by risk BUCKET (the scenario-resilience lens)."""
    groups = defaultdict(list)
    for t in (theses or []):
        groups[_bucket_for(t)].append(t)
    order = list(BUCKETS) + [b for b in groups if b not in BUCKETS]
    out = []
    for b in order:
        ts = sorted(groups.get(b, []), key=lambda x: -x["value"])
        if not ts:
            continue
        meta = BUCKETS.get(b, {"label": b.replace("_", " ").title(), "scenarios": "", "goal_fit": "near"})
        out.append({"bucket": b, "label": meta["label"], "scenarios": meta["scenarios"],
                    "goal_fit": meta.get("goal_fit", "near"),
                    "value": round(sum(x["value"] for x in ts)), "theses": ts})
    return out


def _years_to(goal, as_of=""):
    d = goal.get("date")
    if not d:
        return None
    try:
        from datetime import date
        y0 = int(str(as_of)[:4]) if as_of else date.today().year
        return max(int(str(d)[:4]) - y0, 0)
    except Exception:
        return None


def explain_fit(bucket, goal, as_of=""):
    """A labeled horizon heuristic, never a claim of measured resilience."""
    yrs = _years_to(goal, as_of)
    label = goal.get("label") or "this goal"
    if yrs is None:
        return f"Horizon unknown for {label}; set a date before judging funding fit. Taxonomy does not reserve capital."
    horizon = "near-term" if yrs <= 3 else "long-dated"
    role = {
        "defensive": "Intended ballast and carry; verify liquidity and the estimated loss before reserving capital.",
        "cyclical_value": "Re-rating may take years; a drawdown or delayed catalyst can disrupt funding.",
        "growth": ("Long-duration compounding may suit the horizon; expected growth is uncertain."
                   if yrs > 3 else "Long-duration compounding can be the wrong risk for a near-term spend; test the funding shortfall."),
        "idiosyncratic": "Check dated exits, deal-break losses and financing; independence from market shocks is unknown.",
    }.get(bucket, "Position-level risk is unknown.")
    return f"Heuristic fit for {label} ({horizon}, ~{yrs}y): {role} No capital is reserved by this grouping."


def stress_estimate(thesis, model=None):
    """First-order stress using actual office holdings and the planner's priors.

    No inference from a pack's bucket. Missing symbols prevent a total estimate.
    Portfolio-wide nonlinear effects and financing are not allocated to a thesis.
    """
    symbols = {str(p.get("symbol") or "").upper() for p in thesis.get("positions", [])}
    symbols.discard("")
    matched = []
    found = set()
    for s in (model or {}).get("assets", []):
        holdings = s.get("holdings") or []
        for h in holdings:
            symbol = str(h.get("company") or "").upper()
            if symbol in symbols and h.get("amount") is not None:
                matched.append((s, float(h["amount"])))
                found.add(symbol)
        # Concentrated single-name sleeves carry the symbol in their name.
        name = str(s.get("name") or "").split(" — ")[0].upper()
        if not holdings and s.get("category") == "single_name_equity" and name in symbols:
            matched.append((s, s["value"]))
            found.add(name)
    if not symbols or found != symbols or not matched:
        return {"status": "unknown", "missing": sorted(symbols - found),
                "text": "Stress unknown: complete position-to-model coverage is unavailable. Bucket labels do not establish safety."}
    from officekit.render_scenarios import _move, applicable_scenarios
    gross = sum(abs(value) for _, value in matched)
    if not gross:
        return {"status": "unknown", "missing": [], "text": "Stress unknown: no marked exposure."}
    outcomes = [{"scenario": sc["key"], "name": sc["name"],
                 "pnl": sum(value * _move(s, sc) for s, value in matched)}
                for sc in applicable_scenarios(model)]
    if not outcomes:
        return {"status": "unknown", "missing": [], "text": "Stress unknown: no applicable scenarios."}
    worst = min(outcomes, key=lambda x: x["pnl"])
    return {"status": "estimated", "as_of": model["d"].get("as_of"), "outcomes": outcomes,
            "text": (f"Estimated first-order stress: {worst['name']} {worst['pnl']/gross:+.1%} of gross exposure "
                     f"(${worst['pnl']:,.0f}), using the office's category beta priors as of {model['d'].get('as_of')}. "
                     "Financing, nonlinear effects and exit liquidity need separate review; this is not a measured outcome.")}


def explain_sleeve(sleeve, goal=None, as_of="", model=None):
    """A SLEEVE-level 'why this fits' — specific to this thesis (its edge + bucket +
    the goal), one or two sentences. Deterministic; the full long-form reasoning
    lives in the sleeve's DECK. Complements the bucket-level explain_fit."""
    bucket = _bucket_for(sleeve)
    role = BUCKETS.get(bucket, {}).get("label", bucket.replace("_", " ").title())
    edge = sleeve.get("edge")
    et = (edge.get("edge_type") if isinstance(edge, dict) else edge) or ""
    bits = []
    thesis = (sleeve.get("thesis") or "").strip()
    if thesis:
        bits.append(thesis if len(thesis) <= 180 else thesis[:177] + "…")
    tag = f" (edge: {et})" if et else ""
    bits.append(f"Classed **{role}**{tag}.")
    if goal is not None:
        bits.append(explain_fit(bucket, goal, as_of))
    bits.append(stress_estimate(sleeve, model)["text"])
    return " ".join(bits)


def _goal_horizon(goal, as_of=""):
    """An approximate dated horizon; absent or invalid dates stay unknown."""
    years = _years_to(goal, as_of)
    return None if years is None else "near" if years <= 3 else "long"


def by_goal(theses, goals, as_of=""):
    """Thesis sleeves grouped GOAL-first, then by bucket within each goal, with a
    horizon-fit note (a near-term goal is funded from lower-beta buckets; high-beta
    growth is flagged as a long-horizon stretch). A sleeve appears under every goal
    it helps fund — multiple groupings are fine."""
    fundable = [g for g in (goals or []) if g.get("kind") in ("spending", "retirement", "liquidity_floor")]
    buckets = by_scenario(theses)
    out = []
    for g in fundable:
        hz = _goal_horizon(g, as_of)
        bl = []
        for bk in buckets:
            fit = ("horizon unknown" if hz is None else "core" if bk["goal_fit"] == hz else
                   "long-horizon — fund a near-term goal from the others first"
                   if bk["goal_fit"] == "long" else "supporting")
            bl.append({**bk, "fit": fit, "fit_why": explain_fit(bk["bucket"], g, as_of)})
        out.append({"goal": g, "value": round(sum(t["value"] for t in theses)), "buckets": bl})
    return out


def merge(owned, native):
    """Native courts supersede imported decisions, including at zero live value.
    Packs only overlay descriptive fields; they cannot rewrite court or custody.
    """
    by_sid = {t["sid"]: dict(t) for t in (owned or [])}
    for t in (native or []):
        sid = t["sid"]
        if sid in by_sid and t.get("pack"):
            base = by_sid[sid]
            fields = ("thesis", "deck", "author", "bucket", "pack", "review_status")
            for k in fields:
                if t.get(k):
                    base[k] = t[k]
        else:
            by_sid[sid] = dict(t)
    return sorted(by_sid.values(), key=lambda x: -(x.get("value") or 0))
