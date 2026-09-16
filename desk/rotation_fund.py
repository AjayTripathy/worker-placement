"""rotation_fund — the risk/construction engine that turns the IBKR single-name book into a
deliberately sector-rotation-aware fund.

Stage 1 (this module): MEASURE. Decompose the book by rotation-axis and FF5 factor, flag where a
single rotation carries too much of the book, and stress it through named rotation scenarios (the
thing that hurt on 2026-07-22 when software/IT-services all fell together). READ-ONLY: no orders.

The model, deliberately legible (mirrors desk/disaster.py's shocks+overrides pattern):
    name move % = mkt_beta·mkt_shock + Σ_style FF5_beta·style_shock + axis_override[sector]
A rotation is fundamentally a SECTOR move, so the axis_override is the primary driver; the FF5
market/style terms add the broad + growth-vs-value overlay. Names with no FF5 fit (foreign) fall
back to mkt_beta=1.0 and are driven by the axis override — coverage is reported, never hidden.

Stage 2 (hedge overlay) and Stage 3 (construction ruleset) build on load_book()/axis_exposure().
"""
from __future__ import annotations
import json
from pathlib import Path

from desk import factor_drift as fd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "desk" / "data"
CACHE = ROOT / "desk" / "ui" / "data" / "positions_cache.json"
MARKS = DATA / "positions_marks.json"
SECTORS = DATA / "sector_map.json"
REPORT = DATA / "rotation_report.json"

# FX to USD (units of local ccy per USD, except GBP which is USD per unit). Refresh with marks.
FX = {"USD": 1.0, "JPY": 1 / 163.1, "PLN": 1 / 3.79, "DKK": 1 / 6.4, "GBP": 1.28}  # refreshed 2026-07-23 (live IBKR)

# limits that define "too concentrated on one rotation" (fraction of DEPLOYED book)
AXIS_LIMIT = 0.20        # no single rotation-axis > 20% net
NAME_LIMIT = 0.10        # no single name > 10% net

# ---- rotation scenarios: mkt + FF5 style shocks + per-axis overrides ----
ROTATIONS = {
    "ai_capex_derate": {
        "label": "AI-capex derate (software/IT multiple compression)",
        "desc": "The 2026-07-22 tape: enterprises shift budget to AI hardware, SaaS + IT-services re-rate down together.",
        "mkt": -0.03, "style": {},
        "axis": {"software_saas": -0.12, "it_services": -0.08, "gov_defense_services": -0.02},
    },
    "growth_to_value": {
        "label": "Growth → value rotation",
        "desc": "Value/quality bid, long-duration growth sold. Driven off the HML/RMW factor tilt.",
        "mkt": -0.02, "style": {"hml": 0.06, "rmw": 0.02, "cma": 0.02},
        "axis": {"software_saas": -0.04, "it_services": -0.02, "space_altdata": -0.05},
    },
    "risk_off": {
        "label": "Risk-off (cyclical → defensive)",
        "desc": "Broad de-risking: cyclicals + EM + retail down, quality/defensives relatively bid.",
        "mkt": -0.10, "style": {"rmw": 0.03},
        "axis": {"consumer_retail": -0.06, "em_financials": -0.08, "energy": -0.05,
                 "ecommerce_logistics": -0.07, "space_altdata": -0.08,
                 "insurance": 0.01, "healthcare": 0.01},
    },
    "us_to_intl": {
        "label": "US → international / dollar down",
        "desc": "Intl + EM outperform a softening US tape as the dollar falls.",
        "mkt": -0.01, "style": {},
        "axis": {"japan_value": 0.04, "em_financials": 0.05, "cee_other": 0.04,
                 "consumer_retail": 0.01, "software_saas": -0.01},
    },
    "software_to_energy": {
        "label": "Software → energy (growth → real assets)",
        "desc": "The classic factor rotation: tech multiples compress into a real-asset/commodity bid.",
        "mkt": 0.0, "style": {"hml": 0.03},
        "axis": {"software_saas": -0.10, "it_services": -0.05, "energy": 0.12},
    },
    "rate_spike": {
        "label": "Rate spike (+bp, long-duration down)",
        "desc": "Disorderly rates-up: long-duration growth + rate-sensitive financials down, insurers bid.",
        "mkt": -0.05, "style": {"hml": 0.03, "cma": 0.02},
        "axis": {"software_saas": -0.05, "space_altdata": -0.07, "financial_svcs": -0.03,
                 "em_financials": -0.03, "insurance": 0.02},
    },
}
STYLE_FACTORS = ("hml", "rmw", "smb", "cma")


def _base(sym: str) -> str:
    return sym.split(".")[0].upper()


def load_book() -> dict:
    """Merge holdings (cache) + marks + sector map into a USD book. Reports coverage gaps honestly."""
    cache = json.loads(CACHE.read_text())
    marks = json.loads(MARKS.read_text())["marks"]
    smap = json.loads(SECTORS.read_text())
    sect, low_conf = smap["map"], set(smap.get("low_confidence", []))

    names, missing_mark, unmapped = [], [], []
    for p in cache.get("positions", []):
        if p.get("sec_type") != "STK":
            continue
        b = _base(p["symbol"])
        m = marks.get(b)
        if not m:
            missing_mark.append(b)
            continue
        mv_usd = m["mv"] * FX.get(m["ccy"], 1.0)
        if m["ccy"] == "GBP":                       # GBP quoted USD-per-unit, not per-USD
            mv_usd = m["mv"] * FX["GBP"]
        axis = sect.get(b)
        if not axis:
            unmapped.append(b)
            axis = "UNMAPPED"
        names.append({"sym": b, "mv": round(mv_usd), "ccy": m["ccy"], "axis": axis,
                      "low_conf": b in low_conf})
    gross = sum(n["mv"] for n in names) or 1.0
    return {"names": names, "gross": gross, "asof_cache": cache.get("asof"),
            "asof_marks": marks and json.loads(MARKS.read_text()).get("asof"),
            "missing_mark": missing_mark, "unmapped": unmapped,
            "axes_doc": smap["axes"], "hedge_instrument": smap.get("hedge_instrument", {})}


def axis_exposure(book: dict) -> dict:
    g = book["gross"]
    by = {}
    for n in book["names"]:
        a = by.setdefault(n["axis"], {"mv": 0, "names": []})
        a["mv"] += n["mv"]; a["names"].append(n["sym"])
    for a in by.values():
        a["pct"] = a["mv"] / g
    # concentration
    axis_hhi = sum((a["mv"] / g) ** 2 for a in by.values())
    name_hhi = sum((n["mv"] / g) ** 2 for n in book["names"])
    top_name = max(book["names"], key=lambda n: n["mv"])
    flags = []
    for name, a in by.items():
        if a["pct"] > AXIS_LIMIT:
            flags.append(f"AXIS over-limit: {name} {a['pct']*100:.0f}% > {AXIS_LIMIT*100:.0f}%")
    if top_name["mv"] / g > NAME_LIMIT:
        flags.append(f"NAME over-limit: {top_name['sym']} {top_name['mv']/g*100:.0f}% > {NAME_LIMIT*100:.0f}%")
    return {"by_axis": by, "axis_hhi": axis_hhi, "name_hhi": name_hhi,
            "eff_axes": round(1 / axis_hhi, 1), "eff_names": round(1 / name_hhi, 1),
            "top_name": top_name, "flags": flags}


def factor_exposure(book: dict) -> dict:
    tickers = [n["sym"] for n in book["names"]]
    ld, missing = fd.loadings(tickers, compute_missing=False)
    g = book["gross"]
    exp = {f: 0.0 for f in fd.FACTORS}
    for n in book["names"]:
        fl = ld.get(n["sym"])
        if not fl:
            continue
        w = n["mv"] / g
        for f in fd.FACTORS:
            exp[f] += w * fl.get(f, 0.0)
    cov = sum(n["mv"] for n in book["names"] if n["sym"] in ld) / g
    return {"exp": exp, "coverage": cov, "missing": missing, "ld": ld}


def stress(book: dict, ld: dict, extra: list | None = None) -> dict:
    g = book["gross"]
    universe = book["names"] + (extra or [])
    out = {}
    for key, sc in ROTATIONS.items():
        book_pnl = 0.0
        axis_pnl = {}
        worst = None
        for n in universe:
            fl = ld.get(n["sym"], {})
            mkt_beta = fl.get("mkt_rf", 1.0)         # default full market beta if no FF5 fit
            style = sum(fl.get(f, 0.0) * sc["style"].get(f, 0.0) for f in STYLE_FACTORS)
            axis_ov = sc["axis"].get(n["axis"], 0.0)
            move = mkt_beta * sc["mkt"] + style + axis_ov
            pnl = n["mv"] * move
            book_pnl += pnl
            axis_pnl[n["axis"]] = axis_pnl.get(n["axis"], 0.0) + pnl
            if worst is None or pnl < worst[1]:
                worst = (n["sym"], pnl)
        worst_axis = min(axis_pnl.items(), key=lambda x: x[1]) if axis_pnl else ("-", 0)
        out[key] = {"label": sc["label"], "desc": sc["desc"],
                    "pnl": round(book_pnl), "ret": book_pnl / g,
                    "worst_axis": worst_axis[0], "worst_axis_pnl": round(worst_axis[1]),
                    "worst_name": worst[0], "worst_name_pnl": round(worst[1])}
    return out


# ---- Stage 2: hedge overlay ----
# posture per axis: (tag, hedge_ratio, etf, beta_to_etf)
#   incidental -> neutralize the sector beta, keep the stock-specific alpha (short the ETF)
#   intended   -> a conviction sector/macro bet we KEEP (already diversifying)
#   size       -> single-name concentration; fix by trimming, not a sector short
#   idio       -> small idiosyncratic bet; no hedge
POSTURE = {
    "software_saas":        ("incidental", 0.55, "IGV", 1.15),
    "it_services":          ("incidental", 0.35, "IGV", 0.75),   # looser IGV fit -> smaller ratio
    "financial_svcs":       ("size", 0.0, None, 0.0),            # DFIN single-name -> trim, don't short
    "em_financials":        ("intended", 0.0, None, 0.0),
    "insurance":            ("intended", 0.0, None, 0.0),
    "japan_value":          ("intended", 0.0, None, 0.0),
    "consumer_retail":      ("idio", 0.0, None, 0.0),
    "healthcare":           ("idio", 0.0, None, 0.0),
    "energy":               ("idio", 0.0, None, 0.0),
    "space_altdata":        ("idio", 0.0, None, 0.0),
    "ecommerce_logistics":  ("idio", 0.0, None, 0.0),
    "gov_defense_services": ("idio", 0.0, None, 0.0),
    "cee_other":            ("idio", 0.0, None, 0.0),
    "real_asset_ballast":   ("intended", 0.0, None, 0.0),   # gold ballast: a conviction diversifier, keep
}
ETF_PX = {"IGV": 89.54}          # live 2026-07-22; refresh before staging
ETF_AXIS = {"IGV": "software_saas"}   # which rotation-axis a hedge ETF tracks (for stress)


def hedge_overlay(book: dict, ax: dict) -> dict:
    """Size a sector-ETF short for each INCIDENTAL axis; flag SIZE breaches. Returns tickets +
    synthetic short legs for re-stressing. Never submits — envelopes only."""
    tickets, legs, notes = [], [], []
    g = book["gross"]
    for axis, a in ax["by_axis"].items():
        tag, ratio, etf, beta = POSTURE.get(axis, ("idio", 0.0, None, 0.0))
        if tag == "incidental" and etf and ETF_PX.get(etf):
            notional = a["mv"] * beta * ratio
            sh = round(notional / ETF_PX[etf])
            tickets.append({"axis": axis, "action": "SHORT", "etf": etf, "shares": sh,
                            "notional": round(sh * ETF_PX[etf]), "px": ETF_PX[etf],
                            "hedges_pct": ratio, "beta": beta})
            legs.append({"sym": f"{etf}·short/{axis}", "mv": -sh * ETF_PX[etf],
                         "axis": ETF_AXIS.get(etf, axis), "is_hedge": True})
        elif tag == "size" and a["pct"] > NAME_LIMIT:
            trim = round(a["mv"] - NAME_LIMIT * g)
            notes.append(f"SIZE: {'/'.join(a['names'])} {a['pct']*100:.0f}% > {NAME_LIMIT*100:.0f}% "
                         f"— trim ~{_usd(trim)} to the limit (single-name, not a sector short)")
    return {"tickets": tickets, "legs": legs, "notes": notes}


# ---- Stage 3: rotation-aware construction ruleset ----
DEPLOY_TARGET = 1_000_000     # the $1mm deployable base (NOT current NLV — the standing denominator)
TARGET_CEIL = 0.15            # target ceiling per axis, of the DEPLOYED TARGET (not current deployed)
CORR_GROUPS = [(("software_saas", "it_services"), 0.25)]   # axes that rotate together share a ceiling


def _axis_target(axis: str, base: float, current: float) -> float:
    """Construction target for an axis (in $, vs the TARGET base). incidental=freeze (we hedge it,
    don't grow it); size=freeze the single name; intended/idio=fill toward the ceiling."""
    tag = POSTURE.get(axis, ("idio",))[0]
    if tag in ("incidental", "size"):
        return current                       # freeze — deploy AROUND these, not into them
    return TARGET_CEIL * base


def construction_plan(book: dict, ax: dict, base: float = DEPLOY_TARGET) -> dict:
    """Where to deploy the dry powder: per-axis budget that moves the book toward a rotation-balanced
    allocation without re-stacking the hedged/over axes. Sets the budget; the screener sources names."""
    g = book["gross"]
    capital = max(0.0, base - g)
    rows, total_room = [], 0.0
    for axis, doc in book["axes_doc"].items():
        cur = ax["by_axis"].get(axis, {}).get("mv", 0)
        tgt = _axis_target(axis, base, cur)
        room = max(0.0, tgt - cur)
        total_room += room
        rows.append({"axis": axis, "current": cur, "target": round(tgt), "room": round(room),
                     "posture": POSTURE.get(axis, ("idio",))[0]})
    # distribute capital proportional to room among axes that have room
    for r in rows:
        r["deploy"] = round(capital * r["room"] / total_room) if total_room else 0
    rows.sort(key=lambda r: -r["deploy"])
    return {"base": base, "deployed_now": round(g), "dry_powder": round(capital),
            "rows": rows, "total_room": round(total_room)}


def construction_check(book: dict, ax: dict, cand: dict, base: float = DEPLOY_TARGET) -> dict:
    """Grade a proposed new buy {sym, axis, mv} against the ruleset BEFORE it goes on."""
    g = book["gross"]
    axis = cand["axis"]
    cur = ax["by_axis"].get(axis, {}).get("mv", 0)
    new_axis = cur + cand["mv"]
    reasons, verdict = [], "ADD-OK"
    if new_axis > TARGET_CEIL * base:
        verdict = "OVER-LIMIT"
        reasons.append(f"{axis} → {new_axis/base*100:.0f}% of ${base/1e6:.0f}M base > {TARGET_CEIL*100:.0f}% ceiling")
    if POSTURE.get(axis, ("idio",))[0] == "incidental":
        verdict = "HEDGED-AXIS"
        reasons.append(f"{axis} is an incidental (hedged) axis — adding grows what we're shorting")
    if cand["mv"] / base > NAME_LIMIT:
        verdict = "NAME-OVER"
        reasons.append(f"{cand['sym']} alone {cand['mv']/base*100:.0f}% > {NAME_LIMIT*100:.0f}% name limit")
    for group, ceil in CORR_GROUPS:
        if axis in group:
            gmv = sum(ax["by_axis"].get(a, {}).get("mv", 0) for a in group) + cand["mv"]
            if gmv > ceil * base:
                verdict = "CORRELATED-BREACH"
                reasons.append(f"{'+'.join(group)} → {gmv/base*100:.0f}% > {ceil*100:.0f}% correlated-block ceiling")
    if verdict == "ADD-OK":
        reasons.append(f"fills {axis} toward target ({new_axis/base*100:.0f}% of base)")
    return {"verdict": verdict, "reasons": reasons}


def _usd(x):
    a = abs(x)
    s = f"${a/1e3:.1f}k" if a >= 1e3 else f"${a:.0f}"
    return ("-" + s) if x < 0 else s


def build(write=True) -> dict:
    book = load_book()
    ax = axis_exposure(book)
    fx = factor_exposure(book)
    st = stress(book, fx["ld"])
    g = book["gross"]

    lines = []
    lines.append(f"ROTATION FUND — IBKR book  ${g:,.0f} deployed · {len(book['names'])} names · "
                 f"marks {book['asof_marks']}")
    if book["unmapped"]:
        lines.append(f"  ⚠ UNMAPPED sector: {', '.join(book['unmapped'])} (counted as UNMAPPED axis)")
    if book["missing_mark"]:
        lines.append(f"  ⚠ MISSING marks (dropped): {', '.join(book['missing_mark'])}")
    lc = [n["sym"] for n in book["names"] if n["low_conf"]]
    if lc:
        lines.append(f"  ⚠ low-confidence sector tag: {', '.join(lc)} (verify before trusting its axis)")

    lines.append("")
    lines.append(f"{'ROTATION AXIS':<24}{'$ net':>10}{'%':>7}   names")
    for name, a in sorted(ax["by_axis"].items(), key=lambda x: -x[1]["mv"]):
        mark = "  ‹OVER›" if a["pct"] > AXIS_LIMIT else ""
        lines.append(f"{name:<24}{_usd(a['mv']):>10}{a['pct']*100:>6.1f}%{mark}   {' '.join(a['names'])}")
    lines.append(f"\nDiversification: {ax['eff_axes']} effective axes (of {len(ax['by_axis'])}), "
                 f"{ax['eff_names']} effective names (of {len(book['names'])})")
    lines.append(f"Top single name: {ax['top_name']['sym']} {ax['top_name']['mv']/g*100:.0f}%")
    for f in ax["flags"]:
        lines.append(f"  ⚑ {f}")

    lines.append("")
    lines.append(f"FF5 net factor exposure (coverage {fx['coverage']*100:.0f}%):")
    lines.append("  " + " · ".join(f"{fd.FACTOR_LABEL[f]} {fx['exp'][f]:+.2f}" for f in fd.FACTORS))
    if fx["missing"]:
        lines.append(f"  (no FF5 fit, market-beta=1.0 fallback: {', '.join(fx['missing'])})")

    # Stage 2: hedge overlay + re-stress
    hedge = hedge_overlay(book, ax)
    st_h = stress(book, fx["ld"], extra=hedge["legs"])

    lines.append("")
    lines.append(f"{'ROTATION STRESS':<38}{'unhedged':>13}{'hedged':>13}   worst axis")
    for key, r in sorted(st.items(), key=lambda x: x[1]["pnl"]):
        rh = st_h[key]
        u = f"{_usd(r['pnl'])} {r['ret']*100:.0f}%"
        h = f"{_usd(rh['pnl'])} {rh['ret']*100:.0f}%"
        lines.append(f"{r['label'][:37]:<38}{u:>13}{h:>13}   {r['worst_axis']}")

    lines.append("")
    lines.append("HEDGE OVERLAY (incidental axes → sector-ETF short; envelopes only, never auto-submitted):")
    for t in hedge["tickets"]:
        lines.append(f"  SHORT {t['shares']} {t['etf']} (~{_usd(t['notional'])}, {t['hedges_pct']*100:.0f}% of "
                     f"{t['axis']} β={t['beta']}) @ ${t['px']}")
    for nt in hedge["notes"]:
        lines.append(f"  {nt}")

    # Stage 3: construction plan for the dry powder
    plan = construction_plan(book, ax)
    lines.append("")
    lines.append(f"DEPLOYMENT PLAN — {_usd(plan['dry_powder'])} dry powder to ${plan['base']/1e6:.0f}M base "
                 f"(freeze hedged/over axes, fill under-weight intended/idio):")
    lines.append(f"  {'axis':<22}{'now':>8}{'target':>9}{'DEPLOY':>9}   posture")
    for r in plan["rows"]:
        if r["deploy"] > 0 or r["posture"] in ("incidental", "size"):
            tag = "  ← source names" if r["deploy"] > 500 else ("  (frozen)" if r["posture"] in ("incidental", "size") else "")
            lines.append(f"  {r['axis']:<22}{_usd(r['current']):>8}{_usd(r['target']):>9}"
                         f"{_usd(r['deploy']):>9}   {r['posture']}{tag}")

    report = {"asof_marks": book["asof_marks"], "gross": g, "n_names": len(book["names"]),
              "hedge_overlay": hedge, "stress_hedged": st_h, "construction_plan": plan,
              "axis_exposure": {k: {"mv": v["mv"], "pct": round(v["pct"], 4), "names": v["names"]}
                                for k, v in ax["by_axis"].items()},
              "concentration": {"axis_hhi": round(ax["axis_hhi"], 4), "eff_axes": ax["eff_axes"],
                                "eff_names": ax["eff_names"], "flags": ax["flags"]},
              "ff5": {f: round(fx["exp"][f], 3) for f in fd.FACTORS},
              "ff5_coverage": round(fx["coverage"], 3), "ff5_missing": fx["missing"],
              "rotation_stress": st, "hedge_instrument": book["hedge_instrument"],
              "unmapped": book["unmapped"], "missing_mark": book["missing_mark"]}
    text = "\n".join(lines)
    if write:
        REPORT.write_text(json.dumps(report, indent=1))
    return {"text": text, "report": report}


if __name__ == "__main__":
    print(build()["text"])
