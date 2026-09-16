"""model — the balance-sheet factor model shared by the office dashboard and the
scenario planner (both render from the SAME build_model() output, so they never drift).

Ported from desk/household.py (2026-09-02 Phase-0 extraction). All account-specific
inputs come from the data dict; the harvest snapshot (a live tax-loss feed, e.g. the
desk's Parametric scorecard) is INJECTED by the caller — this module never reads
account files itself.
"""
from __future__ import annotations

from datetime import datetime

from officekit.fmt import fmt_usd as _fmt

# category -> (default display label, donut hex). Labels are generic; a client's
# data may override any of them via data["category_labels"].
CATMAP = {
    "direct_index":         ("Direct Index",          "#5c6bc0"),
    "public_equity":        ("Public Equities",       "#4f7cf0"),
    "single_name_equity":   ("Concentrated Equity",   "#42a5f5"),
    "venture_private":      ("Venture / Private",     "#8b7cf6"),
    "alpha_market_neutral": ("Alpha / Neutral",       "#35c98f"),
    "municipal_credit":     ("Municipal Credit",      "#2dd4bf"),
    "fixed_income":         ("Fixed Income",          "#26a69a"),
    "cash":                 ("Cash & Equivalents",    "#6b7684"),
    "cash_pending":         ("Dry Powder (pending)",  "#9aa4b0"),
    "real_estate":          ("Real Estate",           "#d9a441"),
    "human_capital":        ("Human Capital (income)", "#c58af9"),
    "options_overlay":      ("Options Overlay",       "#e0736a"),
}


def catmap_for(data):
    """The category label/color map with any per-client label overrides applied."""
    over = data.get("category_labels", {})
    return {cat: (over.get(cat, label), hexc) for cat, (label, hexc) in CATMAP.items()}


# --- cross-asset (sleeve x sleeve) beta model -------------------------------
# Pairwise betas are DERIVED from each sleeve's factor-loading vector via a
# factor correlation matrix + a per-category idiosyncratic variance. This is
# the rigorous substitute for regressing realized returns (which we lack for
# venture / real-estate / direct-index daily series). Betas are DIRECTIONAL:
# beta(row responds to -> column driver); beta(A->B) != beta(B->A) by design.
# All numbers inherit the "first-pass estimate" caveat of the loadings.
FACTOR_CORR = {
    "S&P 500":         {"S&P 500": 1.00, "Venture Capital": 0.70, "Mortgage Debt": 0.00, "Inflation": -0.20, "Rates": -0.30, "USD": -0.10},
    "Venture Capital": {"S&P 500": 0.70, "Venture Capital": 1.00, "Mortgage Debt": 0.00, "Inflation": -0.15, "Rates": -0.35, "USD": -0.10},
    "Mortgage Debt":   {"S&P 500": 0.00, "Venture Capital": 0.00, "Mortgage Debt": 1.00, "Inflation": -0.30, "Rates":  0.60, "USD":  0.00},
    "Inflation":       {"S&P 500": -0.20, "Venture Capital": -0.15, "Mortgage Debt": -0.30, "Inflation": 1.00, "Rates": 0.50, "USD": -0.10},
    "Rates":           {"S&P 500": -0.30, "Venture Capital": -0.35, "Mortgage Debt": 0.60, "Inflation": 0.50, "Rates": 1.00, "USD": 0.30},
    "USD":             {"S&P 500": -0.10, "Venture Capital": -0.10, "Mortgage Debt": 0.00, "Inflation": -0.10, "Rates": 0.30, "USD": 1.00},
}

# idiosyncratic share of each sleeve's total variance (own-name risk not
# explained by the macro factors) — damps how much OTHERS move with it.
CAT_IDIO = {
    "cash": 0.05, "cash_pending": 0.05, "public_equity": 0.12, "direct_index": 0.15,
    "single_name_equity": 0.55, "venture_private": 0.72, "real_estate": 0.62,
    "municipal_credit": 0.30, "fixed_income": 0.35, "alpha_market_neutral": 0.95,
    "real_estate_debt": 0.25, "tax_reserve": 0.90, "human_capital": 0.50,
}
_VAR_FLOOR = 0.03


def _corr(fa, fb):
    if fa == fb:
        return 1.0
    return FACTOR_CORR.get(fa, {}).get(fb, 0.0)


def strategy_tags(obj):
    """Strategy membership tags on a sleeve or a holding. Membership is
    many-to-many and WHOLE-ASSET (principal ruling 2026-09-04): an asset can
    serve several strategies at once, and an edge never carries a fraction —
    if a sleeve is genuinely split between mandates, split the sleeve.
    Reads `strategies` (list) plus the legacy singular `strategy`."""
    out = [t for t in (obj.get("strategies") or []) if t]
    legacy = obj.get("strategy")
    if legacy and legacy not in out:
        out.insert(0, legacy)
    return out


def tax_reserve(tm):
    """Accrued tax on the taxable portion of the incoming cash, less harvest offset.

    harvest_mode 'progression' projects the FULL-YEAR harvest = realized-YTD +
    (current daily rate x days remaining to year-end), since the gain and the
    losses both fall in the same tax year. Otherwise uses a flat harvest_losses_2026.
    """
    gross = tm["incoming_gross"] * tm.get("taxable_fraction", 1.0)
    char = tm.get("character", "ltcg")
    carryforward = float(tm.get("loss_carryforward", 0) or 0)   # prior-year banked losses
    # --- harvest loss available to offset the gain ---
    if tm.get("harvest_mode") == "progression":
        d0 = datetime.strptime(tm["harvest_project_from"], "%Y-%m-%d")
        d1 = datetime.strptime(tm["harvest_project_to"], "%Y-%m-%d")
        days_rem = max((d1 - d0).days, 0)
        realized = tm.get("harvest_realized_ytd", 0)
        proj_future = tm.get("harvest_daily_rate", 0) * days_rem
        harvest_losses = realized + proj_future
    else:
        realized = harvest_losses = tm.get("harvest_losses_2026", 0)
        proj_future, days_rem = 0, 0
    # --- rate + offset by character ---
    if char == "ordinary":               # escrow interest / ST — cap losses don't offset (beyond $3k)
        rate, offset = tm["rate_ordinary"], 0.0
    elif char == "return_of_capital":     # already-taxed sale principal
        rate, offset = 0.0, 0.0
    else:                                 # ltcg / mixed — harvest losses offset the gain
        rate = tm["rate_ltcg"]
        # a prior-year CAPITAL-LOSS CARRYFORWARD offsets gains too, alongside
        # current-year harvest (2026-09-08). Losses used against THIS gain are
        # spent; the residual stays banked as a deferred tax asset.
        avail = harvest_losses + carryforward
        offset = min(avail, gross) * rate
    gross_tax = gross * rate
    net_tax = max(gross_tax - offset, 0.0)
    used = min(harvest_losses + carryforward, gross) if char not in ("ordinary", "return_of_capital") else 0.0
    residual_cf = max((harvest_losses + carryforward) - used, 0.0)
    return {"gross_tax": gross_tax, "offset": offset, "net_tax": net_tax, "rate": rate,
            "char": char, "deployable": tm["incoming_gross"] - net_tax,
            "realized": realized, "proj_future": proj_future, "harvest_losses": harvest_losses,
            "days_rem": days_rem, "carryforward": carryforward, "residual_carryforward": residual_cf}


def sleeve_short(s):
    """A sleeve's display-short: explicit `short` field, else first word of the name."""
    return s.get("short") or s["name"].split(" ")[0]


def pending_eta(data):
    """Display label for when the pending-cash sleeve lands ('Sept', 'Q1', ...)."""
    for s in data.get("sleeves", []):
        if s.get("category") == "cash_pending" and s.get("eta"):
            return s["eta"]
    return "pending"


def _pairwise(sleeves, factors):
    """Return (names, shorts, beta[N][N], var[N]). beta[i][j] = beta of i to j."""
    n = len(sleeves)
    nf = len(factors)
    B = [[float(s["beta"].get(f) or 0.0) for f in factors] for s in sleeves]
    FC = [[_corr(fa, fb) for fb in factors] for fa in factors]
    # Cov_sys[i][j] = B_i . FCORR . B_j
    RB = [[sum(FC[a][b] * B[j][b] for b in range(nf)) for a in range(nf)] for j in range(n)]
    cov = [[sum(B[i][a] * RB[j][a] for a in range(nf)) for j in range(n)] for i in range(n)]
    var = []
    for j, s in enumerate(sleeves):
        sysv = max(cov[j][j], 1e-6)
        share = CAT_IDIO.get(s["category"], 0.4)
        idio = sysv * share / (1 - share)
        var.append(max(sysv + idio, _VAR_FLOOR))
    beta = [[1.0 if i == j else cov[i][j] / var[j] for j in range(n)] for i in range(n)]
    names = [s["name"] for s in sleeves]
    shorts = [s["_short"] for s in sleeves]
    return names, shorts, beta, var


def build_model(data, harvest=None, today=None):
    """Compute the augmented balance-sheet model from a validated data dict.

    `today` (a datetime.date) drives sync-freshness staleness math; defaults to
    the real today. Sleeves touched by the sync layer carry `sync` stamps and get
    `_sync_age` / `_sync_stale` annotations here so renderers can badge them.

    `harvest` is an optional LIVE tax-loss snapshot injected by the caller:
    {"loss": <positive magnitude>, "asof": "YYYY-MM-DD", "coverage_start": ...,
     "coverage_days": int|None, "daily_rate": float|None} — e.g. the desk's
    Parametric scorecard read. When present (and the tax model is in progression
    mode with harvest_auto), it overrides the data file's static harvest figures
    so the tax reserve tracks reality without editing the balance sheet.
    """
    factors = data["factors"]
    sleeves = [dict(s) for s in data["sleeves"]]
    eta = pending_eta(data)
    # inject an accrued-tax liability on the incoming cash (less harvest offset)
    tm = data.get("tax_model")
    harvest_live = None
    if tm and tm.get("harvest_auto") and tm.get("harvest_mode") == "progression":
        hv = harvest
        if hv and hv.get("daily_rate"):
            harvest_live = hv
            # bridge adj: only until the live file's coverage reaches the early months
            pre = tm.get("harvest_pre_coverage_adj", 0)
            until = tm.get("harvest_pre_coverage_until", "2026-05-31")
            if hv.get("coverage_start") and hv["coverage_start"] <= until:
                pre = 0
            tm = dict(tm)  # don't mutate the source dict
            tm["harvest_realized_ytd"] = round(pre + hv["loss"])
            tm["harvest_daily_rate"] = round(hv["daily_rate"])
            tm["harvest_project_from"] = hv["asof"]     # project realized-through-asof forward
    tax = tax_reserve(tm) if tm else None
    # Withholding is already absent from received cash. Reduce the liability
    # once, and preserve any excess as a non-cash tax credit pending review.
    unpaid = max(0, round(tax["net_tax"]) - float(tm.get("withheld") or 0)) if tax else 0
    if tax and unpaid > 0:
        received_fraction = min(1, float(tm.get("received_gross") or 0) / tm["incoming_gross"]) if tm["incoming_gross"] else 0
        current_tax = max(0, round(tax["net_tax"]) * received_fraction - float(tm.get("withheld") or 0))
        sleeves.append({
            "name": "Tax Reserve — 2026 incoming cash (less harvest)",
            "kind": "liability", "category": "tax_reserve", "value": -round(unpaid, 2),
            "target_pct": None, "_confidence": "assumption", "short": "Tax Rsv",
            "risks": [
                f"Accrued tax on the {_fmt(tm['incoming_gross'])} {eta} inflow — {tax['char'].upper()} @ {tax['rate']*100:.1f}%",
                f"Offset by projected FULL-YEAR harvest ~{_fmt(tax['harvest_losses'])} (realized {_fmt(tax['realized'])} + {_fmt(tax['proj_future'])} at current rate to Dec 31)" if tax["offset"] else "Harvest does NOT offset ordinary income (only $3k/yr)",
                (f"AUTO-updates from the desk — harvest data as of {harvest_live['asof']} ({_fmt(harvest_live['loss'])}/{harvest_live['coverage_days']}d = {_fmt(harvest_live['daily_rate'])}/day)" if harvest_live else "Projection optimistic — harvest DECAYS as the book ages (surface ~-$90k); reserve rises if the pace slows"),
            ],
            "beta": {f: 0.0 for f in factors},
            "meta": {"inflow_id": tm.get("inflow_id"),
                     "pending_tax": round(max(0, unpaid - current_tax), 2),
                     "withheld": float(tm.get("withheld") or 0),
                     "gross_tax": round(tax["gross_tax"]), "offset": round(tax["offset"]), "net_tax": round(tax["net_tax"]),
                     "realized_ytd": round(tax["realized"]), "projected_future": round(tax["proj_future"]),
                     "full_year_harvest": round(tax["harvest_losses"]),
                     "harvest_auto": bool(harvest_live), "harvest_asof": harvest_live["asof"] if harvest_live else None},
        })
    credit = max(0, float(tm.get("withheld") or 0) - round(tax["net_tax"])) if tax else 0
    if credit:
        sleeves.append({"name": "Tax withholding above modeled liability", "kind": "asset",
                        "category": "tax_asset", "value": round(credit, 2), "short": "Tax credit",
                        "target_pct": None, "_confidence": "assumption",
                        "risks": ["Estimated tax credit; confirm with the tax preparer. This is not cash."],
                        "beta": {f: 0.0 for f in factors},
                        "meta": {"inflow_id": tm.get("inflow_id"), "withholding_credit": True}})
    # a capital-loss CARRYFORWARD is a deferred TAX ASSET: face value tracked,
    # balance-sheet value = rate x usable (unused) losses — never face (a loss
    # is not cash; it's only worth the tax it will save on future gains, 2026-09-08)
    if tax and tax.get("residual_carryforward", 0) > 0:
        residual = tax["residual_carryforward"]
        dta = round(residual * tax["rate"])
        if dta > 0:
            sleeves.append({
                "name": "Deferred Tax Asset — capital-loss carryforward",
                "kind": "asset", "category": "tax_asset", "value": dta,
                "target_pct": None, "_confidence": "assumption", "short": "Loss C/F",
                "risks": [
                    f"Face carryforward {_fmt(residual)} banked — worth {_fmt(dta)} at {tax['rate']*100:.1f}% ONLY against future gains",
                    "Contingent: realizes value as you harvest gains; expires unused if you never realize gains (no expiry federally, but state rules vary)",
                    "Advice shift: harvesting is LESS urgent while this is large; realizing/rebalancing gains is cheap up to the face amount",
                ],
                "beta": {f: 0.0 for f in factors},
                "meta": {"face_carryforward": round(residual), "rate": tax["rate"], "value_at_rate": dta},
            })
    for s in sleeves:
        s["_short"] = sleeve_short(s)
    from officekit.sync import stamp_freshness
    sync_n, sync_stale = stamp_freshness(sleeves, today)
    assets = [s for s in sleeves if s["kind"] == "asset"]
    liabs = [s for s in sleeves if s["kind"] == "liability"]
    A = sum(s["value"] for s in assets)
    L = sum(s["value"] for s in liabs)          # negative
    NW = A + L
    agg = {f: 0.0 for f in factors}
    for s in sleeves:
        w = s["value"] / NW if NW else 0
        for f in factors:
            agg[f] += w * (s.get("beta", {}).get(f) or 0.0)
    pnames, pshorts, pbeta, pvar = _pairwise(sleeves, factors)
    pidx = {nm: i for i, nm in enumerate(pnames)}
    return {"d": data, "factors": factors, "sleeves": sleeves, "assets": assets, "liabs": liabs,
            "A": A, "L": L, "NW": NW, "agg": agg, "tax": tax, "tm": tm, "harvest_live": harvest_live,
            "eta": eta, "sync_n": sync_n, "sync_stale": sync_stale,
            "pnames": pnames, "pshorts": pshorts, "pbeta": pbeta, "pvar": pvar, "pidx": pidx}


fmt_usd = _fmt
