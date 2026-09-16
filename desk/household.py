"""household — the family-office command center. Renders household.html (the 'office' tab).

Born 2026-07-10 (user); 2026-09-02 Phase-0 productization: the ENGINE moved to the
officekit package (model + renderers + effects + scenario/mitigation libraries,
de-personalized — byte-parity proven in tests/test_officekit.py). This module is now
the DESK BINDING only:
  - the account's data file (desk/data/household.json — schema: officekit.schema)
  - the live Parametric harvest feed (_load_harvest) injected into the tax reserve
  - output paths + the render chain (office -> disaster, so the tabs never drift)

    python3 -m desk.household        # -> desk/ui/static/household.html + scenarios.html
READ-ONLY.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from officekit import build_model, load_balance_sheet, render_office, render_strategies, validate
from officekit.fmt import esc, fmt_usd as _fmt  # re-exported for desk callers  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "desk" / "data" / "household.json"
OUT = ROOT / "desk" / "ui" / "static" / "household.html"


def _load_harvest():
    """Read the desk's realized Parametric loss data LIVE so the tax reserve
    auto-updates on every new sync. Returns magnitudes (positive = loss), the
    coverage window, and the derived daily harvest rate — or None on any miss."""
    sc = ROOT / "desk" / "data" / "parametric_scorecard.json"
    rz = ROOT / "desk" / "data" / "parametric_realized.json"
    try:
        ry = json.loads(sc.read_text()).get("realized_ytd") or {}
        net, asof = ry.get("net"), ry.get("asof")
        if net is None or not asof:
            return None
        start = None
        try:
            lots = json.loads(rz.read_text()).get("lots", {})
            dates = [v.get("closed") for v in lots.values() if v.get("closed")]
            start = min(dates) if dates else None
        except Exception:
            pass
        loss = max(0.0, -float(net))                      # magnitude of the net capital loss
        days = rate = None
        if start:
            d0 = datetime.strptime(start, "%Y-%m-%d")
            d1 = datetime.strptime(asof, "%Y-%m-%d")
            days = max((d1 - d0).days, 1)
            rate = loss / days
        return {"net": net, "loss": loss, "asof": asof, "coverage_start": start,
                "coverage_days": days, "daily_rate": rate}
    except Exception:
        return None


def load_model():
    """The account's augmented balance-sheet model (shared with desk.disaster).
    Runs the officekit sync layer first: registered desk connectors (IBKR board,
    Parametric scorecard) overlay live values + freshness stamps in memory —
    the JSON stays the manual base layer; staleness badges on the page, not
    silent rot."""
    data = load_balance_sheet(SRC, strict=False)
    problems = validate(data)
    if problems:
        print(f"[household] schema warnings ({len(problems)}): " + "; ".join(problems[:5]))
    from officekit import personal_context as pctx
    pc = pctx.load(SRC.parent)
    for v in pctx.check_exclusions(data, pc or {}):
        print(f"[household] EXCLUSION VIOLATION: {v['exclusion']['scope']} "
              f"{v['exclusion']['value']} found in {v['where']} — "
              f"{v['exclusion'].get('reason', 'no reason recorded')}")
    from desk import connectors_officekit  # noqa: F401 — importing registers the connectors
    from desk import signals_desk           # noqa: F401 — registers the desk fleet into the capability registry
    from officekit import sync as oksync
    for r in oksync.apply(data, oksync.run()):
        print(f"[household] sync {r['connector']}: {r['status']}"
              + (f" as_of {r['as_of']} ({r['age_days']}d)" if r.get("as_of") else "")
              + f" — {r['detail']}")
    return build_model(data, harvest=_load_harvest())


def build():
    return render_office(load_model())


def main():
    m = load_model()
    OUT.write_text(render_office(m))
    print(f"[household] rendered -> {OUT}")
    strat_out = OUT.parent / "strategies.html"
    strat_out.write_text(render_strategies(m, scenarios_href="scenarios.html"))
    print(f"[household] rendered -> {strat_out}")
    # F3b: the capability registry surfaces — index, per-primitive pages
    # (real code + datasources + health), per-asset pages (capability unions)
    try:
        import officekit_signals as sig
        from officekit.model import strategy_tags
        from officekit.render_signals import (asset_slug, render_asset,
                                              render_capability, render_signals_index)
        rt = sig.runtime(SRC.parent)                    # runs ledger lives in desk/data
        (OUT.parent / "registry.html").write_text(render_signals_index(sig.CAPABILITIES, rt))
        for name, cap in sig.CAPABILITIES.items():
            (OUT.parent / f"capability_{name}.html").write_text(
                render_capability(cap, rt.get(name), sig.source_code(name)))
        d = m["d"]
        assets = {}
        for s in d.get("sleeves", []):
            for h in s.get("holdings", []):
                if h.get("company"):
                    assets.setdefault(str(h["company"]).upper(), set()).update(
                        strategy_tags(h) or strategy_tags(s))
        for sym, strats in assets.items():
            strats = sorted(x for x in strats if x)
            union, seen = [], set()
            for st in strats or [None]:
                for c in sig.applicable(symbol=sym, strategy=st):
                    if c["name"] not in seen:
                        seen.add(c["name"])
                        union.append(c)
            (OUT.parent / f"asset_{asset_slug(sym)}.html").write_text(
                render_asset(sym, d, [], union, strats))
        print(f"[household] registry: {len(sig.CAPABILITIES)} capabilities, {len(assets)} asset pages")
    except Exception as e:
        print(f"[household] registry render skipped: {e}")
    # keep the Scenario Planner in lockstep (it runs on the same load_model())
    try:
        from desk import scenario_planner as _ds
        _ds.main()
    except Exception as e:
        print(f"[household] scenario-planner re-render skipped: {e}")
    # the learning edge: record today's snapshot / scenario predictions / goal
    # statuses to the local ledger (multi-tenant-ready records; one per kind/day)
    try:
        from officekit import learning
        from officekit.render_scenarios import compute_results
        _, _, results = compute_results(m)
        written = learning.observe(m, ROOT / "desk" / "data" / "officekit_learning.jsonl",
                                   results=results)
        if written:
            print(f"[household] learning ledger: recorded {', '.join(written)}")
    except Exception as e:
        print(f"[household] learning observe skipped: {e}")


if __name__ == "__main__":
    main()
