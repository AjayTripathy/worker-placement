"""effects — a registry of encoded portfolio MICROSTRUCTURE effects.

Each financial insight becomes a small, named, testable PROGRAM with a uniform
signature, registered here. Surfaces (Scenario Planner, dashboard, a future
optimizer) DISPATCH over the registry instead of hardcoding — so a new insight is a
new registered effect + a test, never an engine edit. This IS the product: a growing,
composable, queryable library of *executed* financial knowledge — mechanism × channel
× latency.

An effect is a function `fn(ctx) -> dict | None`:
  ctx = {"m": model, "sc": scenario, "move": callable(sleeve)->pct, "X": exposures}
  return None if it doesn't fire, else:
    {"delta": <$ booked to net worth, +cushion/-drag>,   # ENCODED effects only
     "shadow": <$ real but NOT booked (economic/hidden)>, # NOTED effects
     "fires": True, "note": "<scenario-specific one-liner>", "confidence": 0.0-1.0}
The @effect decorator attaches static metadata (kind / channel / mechanism / latency /
doc) and registers it. Dispatch = run(ctx); query via index()/by_channel().

De-personalization contract: effects read ONLY the model — sleeve categories, values,
and meta fields (gross_long/gross_short/embedded_gain_pct). An effect whose data is
absent for a client returns None instead of assuming this account's structure.
"""
from __future__ import annotations

from officekit.fmt import fmt_usd as _fmt

EFFECTS = []            # ordered registry
_BY_ID = {}


def effect(**meta):
    """Register a portfolio effect. meta: id, name, kind (ENCODED|NOTED), channel,
    mechanism, latency, doc (scenario-independent explanation)."""
    def deco(fn):
        fn.meta = meta
        EFFECTS.append(fn)
        _BY_ID[meta["id"]] = fn
        return fn
    return deco


# ------------------------------------------------------------------ effects ---
@effect(id="tax_harvest_hedge", name="Tax-loss-harvest hedge", kind="ENCODED", channel="tax",
        mechanism="incoming realized gain + systematic harvester", latency="within tax-year",
        props={"convex": True, "capped_at": "gain", "horizon": "one_year"},
        doc="The incoming gain's tax reserve is ANTI-correlated with the market: a selloff pushes the "
            "harvester's lots underwater, spiking realized losses that offset the gain and shrink the "
            "reserve. Convex (bigger crash → more harvest), capped at the gain, one tax-year only — the "
            "tax code pays part of a crash's bill.")
def tax_harvest_hedge(ctx):
    m, move = ctx["m"], ctx["move"]
    tax, tm = m.get("tax"), m.get("tm")
    if not tax or not tm or tax.get("net_tax", 0) <= 0:
        return None
    para = next((s for s in m["assets"] if s["category"] == "direct_index"), None)
    if not para:
        return None
    d = move(para)                                   # harvester-sleeve move (< 0 in a selloff)
    if d >= 0:
        return None
    gross = tm["incoming_gross"] * tm.get("taxable_fraction", 1.0)
    rate = tm.get("rate_ltcg", 0.371)
    gbuf = para.get("meta", {}).get("embedded_gain_pct", 0.159)   # embedded-gain buffer
    capture = 0.60                                   # realizable-as-loss fraction
    long_mv = para.get("meta", {}).get("gross_long") or para["value"]
    boost = long_mv * capture * max(0.0, -d - gbuf)
    scen_harvest = tax.get("harvest_losses", 0) + boost
    scen_reserve = max(gross * rate - min(scen_harvest, gross) * rate, 0.0)
    cushion = max(0.0, tax["net_tax"] - scen_reserve)
    if cushion < 1:
        return None
    label = para.get("_short") or para.get("short") or para["name"].split(" ")[0]
    return {"delta": cushion, "fires": True, "confidence": 0.6,
            "note": f"{label} {d*100:.0f}% → +{_fmt(boost)} harvest → reserve shrinks {_fmt(cushion)}"}


@effect(id="fixed_debt_rate_short", name="Fixed-rate mortgage = a rates/inflation short", kind="NOTED",
        channel="rates", mechanism="below-market fixed liability", latency="permanent",
        props={"booked": False},
        doc="You owe the principal nominally regardless, but the ECONOMIC value of below-market fixed debt "
            "FALLS as rates rise — you hold cheap fixed debt while the world reprices. A real hedge in "
            "rate-shock / stagflation, not booked to net worth (it's your residence, not a position you'd "
            "sell), and a reason never to prepay while rates are higher.")
def fixed_debt_rate_short(ctx):
    m, sc = ctx["m"], ctx["sc"]
    debt = next((s for s in m["sleeves"] if s["category"] == "real_estate_debt"), None)
    if not debt:
        return None
    rshock = sc.get("shocks", {}).get("Rates", 0.0)
    if rshock <= 0:
        return None
    dy = rshock * (0.02 / 0.12)                       # scenario Rates shock → actual Δyield (0.12 ≈ +200bp)
    shadow = abs(debt["value"]) * 6.5 * dy            # principal × duration proxy × Δy
    rp = debt.get("meta", {}).get("rate_pct")
    loan = f"below-market {rp:g}% loan" if rp else "below-market fixed loan"
    return {"shadow": shadow, "fires": True, "confidence": 0.5,
            "note": f"+{dy*1e4:.0f}bp → {loan} worth ~{_fmt(shadow)} more to you (unbooked)"}


@effect(id="illiquid_mark_lag", name="Illiquid marks LAG — near-term drawdown understated", kind="NOTED",
        channel="liquidity", mechanism="private-mark smoothing", latency="1-2 quarters",
        props={"direction": "risk"},
        doc="Private marks smooth and reset on a delay, so illiquid sleeves show FALSE stability in the "
            "first weeks of a crash while public sleeves reprice instantly. The planner books the hit "
            "immediately (conservative on timing) — reality is a lagged, lumpy catch-up. The danger is "
            "behavioral: smoothing understates the true hit and overstates diversification when it matters.")
def illiquid_mark_lag(ctx):
    m, move = ctx["m"], ctx["move"]
    ven = next((s for s in m["assets"] if s["category"] == "venture_private"), None)
    if not ven:
        return None
    loss = ven["value"] * move(ven)                  # modeled (negative) — the deferred/hidden hit
    if loss >= -1:
        return None
    return {"shadow": -loss, "fires": True, "confidence": 0.55,
            "note": f"~{_fmt(-loss)} of venture loss is real but marks lag — reported DD understates it near-term"}


@effect(id="short_book_rotation", name="131/31 short book cuts both ways", kind="NOTED",
        channel="equity-factor", mechanism="factor-short defensive rotation", latency="intra-crash",
        props={"direction": "risk"},
        doc="The factor-short book (utilities / REITs / mREITs / regional banks) cushions a broad selloff — "
            "but in a FLIGHT-TO-QUALITY crash those defensives RALLY, so the short drags and the sleeve's "
            "effective beta rises above its net average. A single net beta understates the tail in a "
            "defensives-led rotation.")
def short_book_rotation(ctx):
    m, sc = ctx["m"], ctx["sc"]
    if sc.get("shocks", {}).get("S&P 500", 0.0) > -0.15:   # only real risk-off
        return None
    para = next((s for s in m["assets"] if s["category"] == "direct_index"), None)
    if not para:
        return None
    gshort = abs(para.get("meta", {}).get("gross_short") or 0.0)
    if gshort < 1:                                     # unlevered long-only client: no short book
        return None
    shadow = gshort * 0.08                             # ~8% defensive rally against the short
    return {"shadow": shadow, "fires": True, "confidence": 0.45,
            "note": f"if defensives rally ~8%, the {_fmt(gshort)} short adds ~{_fmt(shadow)} of drag (not in the net beta)"}


@effect(id="correlation_compression", name="Correlations compress toward 1 in a crisis", kind="NOTED",
        channel="correlation", mechanism="liquidity-driven correlation spike", latency="intra-crisis",
        props={"direction": "risk"},
        doc="The cross-asset hedges (munis/bonds rallying, alpha flat) rely on calm-market correlations. In "
            "a genuine liquidity freeze those COMPRESS — everything sells to raise cash and munis can gap "
            "WIDER even as Treasuries rally. Treat the diversifying hedges as weaker than modeled when "
            "volatility spikes: the hedge P&L below is what's at risk of evaporating.")
def correlation_compression(ctx):
    m, move, sc = ctx["m"], ctx["move"], ctx["sc"]
    if sc.get("shocks", {}).get("S&P 500", 0.0) > -0.12:
        return None
    hedge_pnl = sum(s["value"] * move(s) for s in m["assets"]
                    if s["category"] in ("municipal_credit", "fixed_income"))
    if hedge_pnl <= 1:                                 # only when they're modeled as a hedge (positive)
        return None
    return {"shadow": hedge_pnl, "fires": True, "confidence": 0.5,
            "note": f"the ~{_fmt(hedge_pnl)} muni/bond hedge can evaporate (or flip) if correlations spike"}


# ------------------------------------------------------------------ dispatch --
def run(ctx):
    """Run every registered effect against ctx; return the ones that fire, each as
    its metadata merged with its result dict."""
    out = []
    for fn in EFFECTS:
        r = fn(ctx)
        if r and r.get("fires"):
            out.append({**fn.meta, **r})
    return out


def index():
    """Query surface: the static catalog (no scenario) — id/name/kind/channel/mechanism/latency."""
    return [{k: fn.meta.get(k) for k in ("id", "name", "kind", "channel", "mechanism", "latency")}
            for fn in EFFECTS]


def by_channel(channel):
    return [fn.meta["id"] for fn in EFFECTS if fn.meta.get("channel") == channel]
