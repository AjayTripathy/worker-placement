"""signals_desk — the desk's real machinery registered into the app's
capability registry (F3b first sweep, principal-directed 2026-09-05:
"migrate the real desk generators and detectors into the registry").

This is the TENANT-PLUGIN layer of the unified architecture: officekit_signals
ships the registry and the generic flagships; this module registers the desk's
own fleet — the 40+ Stage-0 generators, the connector-backed detectors, and
the desk evidence overrides. Importing this module is the registration
(desk/household.py imports it at build, so desk pages carry the full fleet;
external users never see it — plane separation by import boundary).

Mechanics:
  - Generators bulk-register from verticals/generators/*.py: metadata (label,
    one-line desc) parsed from each module's own docstring WITHOUT importing
    it; the module loads lazily at RUN time and we call, in preference order,
    scan() (all-defaults) -> scan(days=30) -> main(). A scanner without a
    callable entry registers anyway (page + code + health NEVER_RUN) — visible
    is better than forgotten.
  - applies_to comes from a hand-curated strategy map for the load-bearing
    generators; unmapped ones register index-only (no strategy binding) until
    someone maps them — honest, not hidden.
  - Detectors wrap the buyside connectors' callable entries (litigation
    screen, app-review velocity, USASpending gov-contracts) with datasources
    enumerated.
"""
from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path

from officekit_signals import capability

ROOT = Path(__file__).resolve().parents[1]
GEN_DIR = ROOT / "verticals" / "generators"

# files in verticals/generators that are not standing generators
_SKIP = {"insider_drift_backtest", "quality_wishlist", "data"}

# the load-bearing generators, hand-mapped to the strategies they feed
_STRATEGY_MAP = {
    "quality_drawdown": ["quality_drawdown", "quality_value", "core_equity", "concentrated"],
    "dislocation_sweep": ["value_band_entry"],
    "us_broad_dislocation_sweep": ["value_band_entry"],
    "intl_dislocation_sweep": ["value_band_entry"],
    "cohort_dislocation": ["value_band_entry"],
    "lockup_expiry_scanner": ["value_band_entry"],
    "insider_cluster_scanner": ["quality_value", "value_band_entry"],
    "spinoff_orphans": ["quality_value"],
    "japan_tob_lane": ["custom_japan", "japan_value"],
    "spac_trust_arb_scanner": ["cash_mgmt"],
    "preferred_oddlot_scanner": ["bonds"],
    "cef_term_liquidation_scanner": ["bonds"],
    "ai_adopter_gates": ["quality_value", "core_equity"],
    "attention_divergence_scanner": ["value_band_entry"],
    "auditor_late_filing_scanner": ["quality_value"],
    "award_flow_scanner": ["quality_value"],
    "bank_consolidation_scanner": ["quality_value"],
    "biotech_clearing_scanner": ["value_band_entry"],
    "borrow_fee_scanner": ["value_band_entry"],
    "country_risk_arb_scanner": ["value_band_entry"],
    "crossborder_twin_scanner": ["value_band_entry"],
    "december_dislocation_scanner": ["value_band_entry"],
    "distress_8k_scanner": ["value_band_entry"],
    "euronext_shelf": ["quality_value"],
    "fda_velocity_scanner": ["quality_value"],
    "hiring_wave_scanner": ["quality_value"],
    "insider_10b51_scanner": ["quality_value"],
    "january_reversal_scanner": ["value_band_entry"],
    "litigation_flow_scanner": ["quality_value"],
    "lse_shelf": ["quality_value"],
    "nih_grant_scanner": ["quality_value"],
    "plume_cluster_scanner": ["quality_value"],
    "ptab_itc_docket_scanner": ["quality_value"],
    "russell_recon_scanner": ["value_band_entry"],
    "subthreshold_arb_scanner": ["value_band_entry"],
    "tariff_refund_cohort": ["quality_value"],
    "thematic_etf_rebalance_scanner": ["value_band_entry"],
    "warn_layoff_scanner": ["value_band_entry"],
}

# generators that deliberately map to NO strategy — the reason ships in the desc
_INDEX_ONLY_REASON = {
    "kalshi_divergence_scanner": "prediction-market divergences feed frozen CALLS, not a holdings strategy",
    "polymarket_whale_scanner": "prediction-market flow intel feeds calibration, not a holdings strategy",
    "venue_class_scanner": "market-structure census — infrastructure intel, not a candidate source",
}


def _module_meta(path):
    """Label + one-line description from the module's own docstring, read
    from source (never imported at registration time)."""
    head = path.read_text()[:2000]
    m = re.search(r'"""\s*([^\n]+)', head)
    line = (m.group(1) if m else path.stem).strip()
    if "—" in line:
        name, desc = line.split("—", 1)
    elif " - " in line:
        name, desc = line.split(" - ", 1)
    else:
        name, desc = path.stem, line
    return name.strip().strip('"'), desc.strip()


def _make_generator_runner(stem):
    def run(ctx):
        mod = importlib.import_module(f"verticals.generators.{stem}")
        scan = getattr(mod, "scan", None)
        if callable(scan):
            params = inspect.signature(scan).parameters
            required = [p for p in params.values()
                        if p.default is inspect.Parameter.empty
                        and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)]
            if not required:
                return scan()
            if [p.name for p in required] == ["days"]:
                return scan(days=int(ctx.get("days", 30)))
        main = getattr(mod, "main", None)
        if callable(main):
            main()
            return {"note": "ran main() — output in the desk's own stores/logs"}
        raise RuntimeError(f"{stem}: no scan()/main() entry")
    return run


def register_generators():
    n = 0
    for path in sorted(GEN_DIR.glob("*.py")):
        stem = path.stem
        if stem in _SKIP or stem.startswith("_"):
            continue
        name, desc = _module_meta(path)
        strategies = _STRATEGY_MAP.get(stem, [])
        if not strategies:
            reason = _INDEX_ONLY_REASON.get(stem, "not yet mapped to a strategy")
            desc = desc + f"  [index-only: {reason}]"
        capability(stem, "generator", name,
                   desc=desc,
                   datasources=[f"reference implementation: verticals/generators/{stem}.py "
                                f"(see the code section for the feeds it touches)"],
                   applies_to={"strategies": strategies},
                   source_ref=str(path))(_make_generator_runner(stem))
        n += 1
    return n


# ---------------------------------------------------------------- detectors --

@capability("litigation_screen", "detector", "Litigation screen (CourtListener/RECAP)",
            desc="Federal-docket background screen for any named principal/operator/"
                 "sponsor/GP: MATERIAL nature-of-suit codes (securities fraud, RICO, "
                 "stockholder suits, subject-as-debtor bankruptcy) fire; routine "
                 "employment/ADA baseline does not. FEDERAL ONLY — clean here is never "
                 "clean everywhere; state courts and UCC liens are the paid escalation.",
            datasources=["CourtListener / RECAP v4 search API (free PACER proxy)"],
            applies_to={"universal": True})
def det_litigation(ctx):
    from verticals.buyside_dd.connectors.litigation_screen import screen_entity
    name = ctx.get("name") or ctx.get("symbol")
    if not name:
        raise RuntimeError("litigation_screen needs ctx['name'] (entity or person)")
    return screen_entity(name, bool(ctx.get("is_person")))


@capability("app_review_velocity", "detector", "App-review velocity",
            desc="Consumer-app traction/deterioration read: dated review velocity, "
                 "exact cohort deltas from snapshots, lifetime-vs-visible calibration "
                 "(written cohorts are structurally angrier — never read the gap as "
                 "deterioration; a velocity COLLAPSE is the clean signal).",
            datasources=["iTunes Search/Lookup/RSS (keyless, US storefront)",
                         "Play Store ld+json aggregate"],
            applies_to={"strategies": ["quality_value", "core_equity"],
                        "issuer_features": ["consumer_app"]})
def det_app_review_velocity(ctx):
    from verticals.buyside_dd.connectors.app_review_velocity import read_app
    sym = ctx.get("symbol")
    if not sym:
        raise RuntimeError("app_review_velocity needs ctx['symbol']")
    return read_app(sym, query=ctx.get("query", ""))


@capability("gov_contracts", "detector", "Federal-contracts verification (USASpending)",
            desc="Verifies any government-revenue claim against the primary federal "
                 "procurement record — corporate-FAMILY search (contracts hide in "
                 "subsidiaries: '<Co> Federal Inc'), prime-only caveat stated: a low "
                 "total never proves small gov revenue (subcontracts/classified "
                 "invisible; the gap is thesis texture).",
            datasources=["USASpending API (api.usaspending.gov, public)"],
            applies_to={"issuer_features": ["government_revenue"], "universal": False})
def det_gov_contracts(ctx):
    from verticals.buyside_dd.connectors.base import ConnectorRequest
    from verticals.buyside_dd.connectors.usaspending import UsaSpendingConnector
    name = ctx.get("name") or ctx.get("symbol")
    if not name:
        raise RuntimeError("gov_contracts needs ctx['name'] (recipient entity name)")
    res = UsaSpendingConnector().query(ConnectorRequest(entity_name=name))
    return res.model_dump() if hasattr(res, "model_dump") else res.dict()


@capability("hiring_velocity", "watcher", "Hiring velocity (plant ramp)",
            desc="Capacity-ramp nowcast: job-posting count/mix/velocity at a site — "
                 "accelerating operator postings = mid-ramp; postings drying up = "
                 "nearing full utilization, ahead of the margin print. Small-N: read "
                 "the trend across snapshots, never one pull.",
            datasources=["LinkedIn guest jobs endpoint (keyless)",
                         "Adzuna (free key, production-role coverage)"],
            applies_to={"issuer_features": ["capacity_ramp"]}, cadence_days=7)
def watch_hiring_velocity(ctx):
    from verticals.buyside_dd.connectors.hiring_velocity import fetch_postings, ramp_metrics
    kw = ctx.get("keywords")
    loc = ctx.get("location")
    if not (kw and loc):
        raise RuntimeError("hiring_velocity needs ctx['keywords'] and ctx['location']")
    rows = fetch_postings(kw, loc)
    return ramp_metrics(rows)


# ------------------------------------------------- muni scanner + honesty + IBKR --

@capability("muni_bond_scanner", "generator", "Muni bond scanner (incremental)",
            desc="Grows the muni book: diffs the priced universe against held + "
                 "already-seen, funnels only NEW names through the validated screen "
                 "(EMMA issue-title gate, liquidity floor, de-minimis-aware after-tax "
                 "TEY, fit-to-need). Respects EMMA rate limits — incremental only.",
            datasources=["IBKR BOND.MUNI scanner universe (bonds_priced.json)",
                         "EMMA security details + trade tape (per-CUSIP)"],
            applies_to={"strategies": ["muni"]},
            source_ref=str(ROOT / "verticals/muni_credit/bond_scanner.py"))
def gen_muni_scanner(ctx):
    from verticals.muni_credit.bond_scanner import scan
    uni = ctx.get("universe_path") or str(ROOT / "verticals/muni_credit/bonds_priced.json")
    return scan(uni, max_new=int(ctx.get("max_new", 40)))


@capability("honesty_screen", "detector", "Honesty screen (claim-verification pipeline)",
            desc="The full lying-detector pipeline on one name: extract claims from "
                 "the latest periodic filing, mechanically verify each against "
                 "external authorities, score findings, aggregate. EXPENSIVE (LLM "
                 "stages + external queries, minutes per name). A negative-selection "
                 "filter: it excludes names whose disclosure diverges from verifiable "
                 "reality — it never re-detects honestly disclosed bad news.",
            datasources=["SEC EDGAR (filing text via officekit_research)",
                         "external verification authorities per claim (registries, "
                         "procurement, courts — dispatched by the pipeline)",
                         "Anthropic API (extraction + scoring stages)"],
            applies_to={"strategies": ["quality_value", "quality_drawdown", "value_band_entry"],
                        "universal": False},
            source_ref=str(ROOT / "verticals/public_co/unified_runner.py"))
def det_honesty_screen(ctx):
    import datetime as _dt
    from officekit_research import build_pack
    from verticals.public_co.providers import ApiProvider
    from verticals.public_co.unified_runner import analyze_company
    sym = ctx.get("symbol")
    if not sym:
        raise RuntimeError("honesty_screen needs ctx['symbol']")
    pack = build_pack(sym, contact=ctx.get("contact"), sources=["filing_text"])
    ft = pack["sections"].get("filing_text")
    if not ft:
        raise RuntimeError("no filing text: " + "; ".join(pack["errors"]))
    analysis = analyze_company(sym, _dt.date.today().isoformat(), ft["text"],
                               ApiProvider(), filing_name=f"{ft['form']} {ft['date']}")
    d = analysis.model_dump() if hasattr(analysis, "model_dump") else (
        analysis.dict() if hasattr(analysis, "dict") else vars(analysis))
    return json.loads(json.dumps(d, default=str))


# IBKR live tape — the desk's tenant EVIDENCE OVERRIDE: replaces the free
# close-only endpoint in the court pack with gateway quotes when available,
# falling back loudly to the free source when the gateway is down.
def _register_tape_override():
    import officekit_research as ev
    free_tape = ev.SOURCES["tape"]

    @ev.evidence_source("tape")
    def desk_tape(symbol, ctx):
        try:
            from desk.prices import get_price
            q = get_price(symbol)
            px = q.get("px") or q.get("last")
            if px:
                base = {}
                try:
                    base = free_tape(symbol, ctx)      # keep the 52wk anchors
                except Exception:
                    pass
                base.update({"last": px, "as_of": q.get("asof") or "live",
                             "source": "desk gateway (live)"})
                return base
        except Exception:
            pass
        out = free_tape(symbol, ctx)                   # loud fallback: source named
        out["source"] = "free endpoint (gateway unavailable)"
        return out


import json  # noqa: E402  (used by honesty_screen serialization)
if (ROOT / "desk/prices.py").is_file():
    _register_tape_override()
N_GENERATORS = register_generators()

# A portable wheel ships the registry, not every private monorepo dependency.
# Make that distinction visible before a user clicks Run.
from officekit_signals import CAPABILITIES
for _name, _path in {
    "litigation_screen": "verticals/buyside_dd/connectors/litigation_screen.py",
    "app_review_velocity": "verticals/buyside_dd/connectors/app_review_velocity.py",
    "gov_contracts": "verticals/buyside_dd/connectors/usaspending.py",
    "hiring_velocity": "verticals/buyside_dd/connectors/hiring_velocity.py",
    "muni_bond_scanner": "verticals/muni_credit/bond_scanner.py",
    "honesty_screen": "verticals/public_co/unified_runner.py",
}.items():
    CAPABILITIES[_name]["requires_paths"] = [str(ROOT / _path)]
