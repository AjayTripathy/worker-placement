"""harvest — whole-portfolio tax-loss harvesting (ported from the msprime
Parametric-only simulator, generalized to EVERY asset).

msprime's simulator answered, for the Parametric SMA: which lots are underwater,
what's the tax alpha of selling them, how does it drift the factor exposure /
concentration, and what's the wash-sale lockout. This does the same across the
whole office — every sleeve — and folds the harvest into the office's real tax
picture: a harvested loss OFFSETS the incoming capital gain and the banked
carryforward, shrinking the reserve.

Where a sleeve carries lot basis (holdings) or a `meta.harvest` block, the loss
is measured; where it doesn't, the sleeve is listed as "basis not imported" —
honest, never guessed. The Parametric scorecard (desk feed) bridges in when
present so the principal sees the real surface.

    collect(m, folder) -> {positions, carryforward, harvestable_total}
    simulate(positions, selected_ids, m, tax_rate) -> {tax_benefit, offset, ...}
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")[:48] or "x"


def factor_tilt(m, exclude_names=frozenset()):
    """The portfolio's factor tilt = net-worth-weighted sleeve betas, optionally
    excluding some sleeves (to see the post-harvest tilt)."""
    factors = m["factors"]
    sleeves = [s for s in m["sleeves"] if s["name"] not in exclude_names]
    nw = sum(s["value"] for s in sleeves) or 1.0
    tilt = {f: 0.0 for f in factors}
    for s in sleeves:
        w = s["value"] / nw
        for f in factors:
            tilt[f] += w * (s.get("beta", {}).get(f) or 0.0)
    return {f: round(v, 3) for f, v in tilt.items()}


def _sleeve_loss(s):
    """Harvestable loss for one sleeve (positive number), or None if unknown."""
    meta = s.get("meta") or {}
    h = meta.get("harvest")
    if h:
        lt, st = abs(h.get("loss_lt", 0) or 0), abs(h.get("loss_st", 0) or 0)
        tot = lt + st or abs(h.get("total", 0) or 0)
        if tot:
            return {"loss": tot, "lt": lt, "st": st, "n_lots": h.get("n_lots"), "term": "mixed"}
    loss = 0.0
    n = 0
    for hd in s.get("holdings", []):
        basis, val = hd.get("cost_basis"), hd.get("amount")
        if basis is not None and val is not None and val < basis:
            loss += basis - val
            n += 1
    if loss > 0:
        return {"loss": round(loss, 2), "lt": 0, "st": 0, "n_lots": n, "term": "unknown"}
    return None


def _parametric_bridge(folder=None):
    """Principal-tenant bridge: the Parametric harvest surface from the scorecard
    (office-generated copy first, desk fallback — see _read_scorecard). The general
    path is a sleeve `meta.harvest`."""
    sc = _read_scorecard(folder)
    if not sc:
        return None
    hv = sc.get("harvest") or {}
    longl = abs(hv.get("long_harvestable", 0) or 0)
    shortl = abs(hv.get("short_harvestable", 0) or 0)
    tot = longl + shortl
    if tot:
        return {"id": "parametric-sma", "label": "Parametric direct-index SMA",
                "category": "direct_index", "value": (sc.get("structure") or {}).get("net"),
                "loss": round(tot, 2), "lt": longl, "st": shortl,
                "n_lots": hv.get("long_loss_lots"), "term": "mixed", "known": True,
                "source": f"scorecard {sc.get('asof', '')}"}
    return None


def _read_scorecard(folder=None):
    """The Parametric scorecard — the OFFICE-generated copy first (folder/
    parametric_scorecard.json, written by build_office from the MS bundles), then
    the desk's copy as a transition fallback. The office no longer depends on
    desk/data once it has generated its own (desk-deprecation, 2026-09-10)."""
    paths = []
    if folder:
        paths.append(Path(folder) / "parametric_scorecard.json")
    from officekit.runtime import hosted
    if hosted():
        paths = paths[:1]
    else:
        paths += [Path("desk/data/parametric_scorecard.json"),
              Path.home() / "exalted" / "signalos" / "desk" / "data" / "parametric_scorecard.json"]
    for p in paths:
        try:
            return json.loads(p.read_text())
        except Exception:
            continue
    return None


def _realized_split(m, folder):
    """Capital losses ALREADY REALIZED this year, split by HOLDING PERIOD — banked,
    not contingent on further selling. `st`/`lt` are net-of-same-character magnitudes
    (positive = net loss in that bucket); `net` is the total net capital loss.
    Principal: Parametric scorecard realized_ytd (st_net/lt_net/net); general: office
    tax_model fields. All magnitudes are positive dollars."""
    from officekit.staging import num
    tm = (m.get("d") or {}).get("tax_model") or {}
    net = num(tm.get("realized_losses_ytd") or tm.get("harvest_realized_ytd") or 0) or 0.0
    st = num(tm.get("realized_st_ytd") or 0) or 0.0
    lt = num(tm.get("realized_lt_ytd") or 0) or 0.0
    from officekit.runtime import hosted
    if _is_principal_office(folder) or (hosted() and folder and (Path(folder) / "parametric_scorecard.json").is_file()):
        sc = _read_scorecard(folder)
        ry = (sc or {}).get("realized_ytd") or {}
        n = ry.get("net")
        if n is not None and float(n) < 0:
            net = -float(n)
            st = max(0.0, -float(ry["st_net"])) if ry.get("st_net") is not None else 0.0
            lt = max(0.0, -float(ry["lt_net"])) if ry.get("lt_net") is not None else 0.0
    if net and not (st or lt):        # no split available -> treat as long-term/blended
        lt = net
    return {"net": round(net, 2), "st": round(st, 2), "lt": round(lt, 2)}


def _realized_losses(m, folder):
    """Net magnitude of realized capital losses banked this year (see _realized_split)."""
    return _realized_split(m, folder)["net"]


def _is_principal_office(folder):
    """The Parametric desk bridge is the principal's own feed — only the
    principal's ~/office reads it; every other tenant (and every test) uses the
    general per-sleeve path, never another book's data."""
    try:
        return folder and Path(folder).resolve() == (Path.home() / "office").resolve()
    except Exception:
        return False


def collect(m, folder=None):
    """Every asset's harvestable loss (measured where basis exists; flagged where not)."""
    positions = []
    bridged_categories = set()
    pb = _parametric_bridge(folder) if _is_principal_office(folder) else None
    if pb:
        positions.append(pb)
        bridged_categories.add("direct_index")

    for s in m["assets"]:
        if s["category"] in ("cash", "cash_pending", "tax_reserve", "tax_asset"):
            continue
        L = _sleeve_loss(s)
        # avoid double-counting the sleeve the Parametric bridge already represents
        if pb and s["category"] in bridged_categories and L is None and s["value"] > 0:
            continue
        positions.append({
            "id": _slug(s["name"]), "label": s["name"], "category": s["category"],
            "value": s["value"], "loss": (L["loss"] if L else 0.0),
            "lt": (L or {}).get("lt", 0), "st": (L or {}).get("st", 0),
            "n_lots": (L or {}).get("n_lots"), "term": (L or {}).get("term", "unknown"),
            "known": bool(L), "source": "lot basis" if L else "basis not imported"})

    # per-position harvestable from the office's OWN position rows: those carry a
    # market value (synced from the broker when available) AND cost basis (from
    # avg cost). A loser = market value below cost basis. Position-level (avg
    # cost), not per-lot — lot-level LT/ST needs a Flex Query / taxlot export.
    if folder:
        try:
            from officekit.staging import num
            ans = json.loads((Path(folder) / "answers.json").read_text())
            for r in (ans.get("positions") or {}).get("rows", []):
                sym = r.get("symbol") or "position"
                # LOT-LEVEL (Flex): real LT/ST split, harvest losing lots only
                lt, st = num(r.get("loss_lt")), num(r.get("loss_st"))
                if r.get("lots") is not None and (lt > 0 or st > 0):
                    n_lots = sum(1 for L in (r.get("lots") or []) if num(L.get("loss")) > 0)
                    positions.append({
                        "id": _slug("pos-" + str(sym)), "label": str(sym), "category": "holding",
                        "value": round(num(r.get("value")), 2), "loss": round(lt + st, 2),
                        "lt": round(lt, 2), "st": round(st, 2), "n_lots": n_lots,
                        "term": "lot-level", "known": True, "source": "Flex lot basis"})
                    continue
                if r.get("cost_basis") is None:      # no basis captured -> not measurable
                    continue                          # (num(None)->0 would fake a loss on shorts)
                cb, v = num(r.get("cost_basis")), num(r.get("value"))
                if cb is None or v is None or v >= cb or cb <= 0:
                    continue
                positions.append({
                    "id": _slug("pos-" + str(sym)), "label": str(sym), "category": "holding",
                    "value": round(v, 2), "loss": round(cb - v, 2), "lt": 0, "st": 0,
                    "n_lots": 1, "term": "avg-cost", "known": True, "source": "broker avg cost"})
        except Exception:
            pass

    d = m["d"]
    carryforward = float(d.get("loss_carryforward")
                         or (m.get("tax") or {}).get("carryforward") or 0)
    harvestable_total = sum(p["loss"] for p in positions)
    rl = _realized_split(m, folder)                    # banked this year, ST/LT split
    return {"positions": positions, "carryforward": carryforward,
            "realized": rl["net"], "realized_st": rl["st"], "realized_lt": rl["lt"],
            "harvestable_total": round(harvestable_total, 2),
            "wash_risk": wash_risk(positions, m, folder)}


# a direct-index SMA (Parametric etc.) HARVESTS and REBALANCES continuously, so it
# is very likely to BUY a constituent inside the ±30-day window — the classic
# cross-account wash trap when you also hold that name individually.
def _is_active_sma(source_id, source_kind, name=""):
    s = f"{source_id} {name}".lower()
    return ("parametric" in s or "morgan_stanley" in s or "direct" in s
            or "sma" in s or source_kind == "direct_index")


def wash_risk(positions, m, folder=None):
    """Warn of POSSIBLE wash sales BETWEEN accounts: the same (exact-symbol)
    security held in more than one account/source, so selling it for a loss in one
    can be disallowed by a purchase — a manual buy, a dividend reinvestment, or an
    SMA rebalance/harvest — in another within ±30 days. Two buckets:

      * per-symbol: a harvestable name also held in another account/source (from
        the staged pulls, which keep per-account identity the office collapses);
      * standing: a direct-index SMA sleeve is present — it trades S&P names
        constantly, so ANY individually-held large-cap loss is at risk even before
        its constituents are imported. (Exact-symbol only; 'substantially
        identical' index-vs-ETF overlap is the standing caution, not per-row.)"""
    warnings, standing = [], []
    holders = {}                                     # SYM -> [{account, source, kind, sma}]
    if folder:
        try:
            from officekit import staging
            rows, _ = staging.merged_rows(folder)
            for r in rows:
                sym = (r.get("symbol") or "").upper()
                if not sym or r.get("sec_type") not in ("STK", "ETF", "FUND", "ADR"):
                    continue
                sid, kind = r.get("source_id") or "?", r.get("source_kind") or ""
                holders.setdefault(sym, []).append({
                    "account": r.get("account") or "?", "source": sid,
                    "sma": _is_active_sma(sid, kind)})
        except Exception:
            pass
        # owner provenance from the office's OWN positions — the collapse keeps one
        # row per symbol for the view but records each account under `accounts`, so
        # the owner is recoverable from owned data (not just live staging). Deduped
        # against staging by the (account, source) sets below.
        try:
            ans = json.loads((Path(folder) / "answers.json").read_text())
            for r in (ans.get("positions") or {}).get("rows", []):
                sym = (r.get("symbol") or "").upper()
                for acc in (r.get("accounts") or []):
                    holders.setdefault(sym, []).append({
                        "account": acc.get("account") or "?", "source": acc.get("source") or "?",
                        "sma": _is_active_sma(acc.get("source") or "", "")})
        except Exception:
            pass

    # a direct-index SMA is its OWN account: fold its constituents (the sleeve's
    # holdings — office-native, no re-parse) into the holders map so a name held BOTH
    # in the SMA and in a brokerage account (the collapse hides it) is detected.
    for s in m["assets"]:
        if s.get("category") == "direct_index" or _is_active_sma("", "", s.get("name", "")):
            acct = (s.get("name") or "Direct-index SMA").split(" — ")[0]   # drop the ticker tail
            for hd in (s.get("holdings") or []):
                sym = (hd.get("company") or hd.get("symbol") or "").upper()
                if sym:
                    holders.setdefault(sym, []).append(
                        {"account": acct, "source": "direct_index", "sma": True})

    # every stock held in MORE THAN ONE account (informational, not just losers) —
    # each is a wash-sale trap the moment you harvest it in one of them.
    def _acctset(hs):
        return sorted({h["account"] for h in hs})
    multi_account = sorted(
        ({"symbol": s, "accounts": _acctset(hs), "sma": any(h["sma"] for h in hs)}
         for s, hs in holders.items() if len({(h["account"], h["source"]) for h in hs}) > 1),
        key=lambda x: x["symbol"])

    harvestable = {p["label"].upper() for p in positions if p["known"] and p["loss"] > 0}
    loss_by = {p["label"].upper(): p["loss"] for p in positions}
    for sym in sorted(harvestable):
        hs = holders.get(sym, [])
        accts = {(h["account"], h["source"]) for h in hs}
        if len(accts) > 1:                           # same name, two+ accounts/sources
            sma = any(h["sma"] for h in hs)
            warnings.append({
                "symbol": sym, "loss": loss_by.get(sym, 0.0),
                "accounts": sorted({h["account"] for h in hs}),
                "sources": sorted({h["source"] for h in hs}),
                "severity": "high" if sma else "medium",
                "note": ("also traded in a direct-index SMA — a rebalance/harvest "
                         "buy within ±30 days would disallow this loss"
                         if sma else
                         "held in another account — a buy or dividend reinvestment "
                         "there within ±30 days would disallow this loss")})

    # standing SMA caution: a direct-index vehicle whose constituents are NOT yet
    # imported per-symbol (so per-row detection can't see the overlap). It can show
    # up as a model sleeve OR as the Parametric harvest bridge (a position).
    sma_names = [s["name"] for s in m["assets"]
                 if s["category"] in ("direct_index",) or _is_active_sma("", "", s.get("name", ""))]
    sma_names += [p["label"] for p in positions
                  if p.get("category") == "direct_index" or _is_active_sma("", "", p.get("label", ""))]
    sma_syms_imported = any(h["sma"] for hl in holders.values() for h in hl)
    if sma_names and not sma_syms_imported:
        standing.append({
            "sleeve": sma_names[0],
            "note": ("You hold a direct-index SMA that continuously harvests and "
                     "rebalances S&P 500 names. Harvesting an individually-held "
                     "large-cap loss can wash against an SMA purchase within ±30 "
                     "days. Import the SMA holdings (the Morgan Stanley bundle) to "
                     "flag the exact overlapping tickers.")})
    return {"warnings": warnings, "standing": standing,
            "count": len(warnings), "has_standing": bool(standing),
            "multi_account": multi_account, "multi_account_count": len(multi_account)}


def simulate(collected, selected_ids, m, tax_rate, as_of=None):
    """Harvest the selected positions: tax benefit, the offset against the
    incoming gain + carryforward, factor-tilt drift, concentration and the
    wash-sale lockout calendar."""
    positions = collected["positions"]
    sel = [p for p in positions if p["id"] in selected_ids and p["known"] and p["loss"] > 0]
    harvested_loss = sum(p["loss"] for p in sel)
    carryforward = collected["carryforward"]
    realized = collected.get("realized", 0.0)         # losses already banked this year
    realized_st = collected.get("realized_st", 0.0)   # ... split by holding period
    realized_lt = collected.get("realized_lt", 0.0)

    tax = m.get("tax") or {}
    gross_gain = float(tax.get("gross_tax", 0) / tax.get("rate", 1)) if tax.get("rate") else 0.0
    if not gross_gain:
        gross_gain = float((m["d"].get("tax_model") or {}).get("incoming_gross", 0) or 0)

    # BANKED = realized-this-year + prior carryforward: already locked in, offsets
    # the gain whether or not you harvest anything more. Harvesting adds to it.
    banked = realized + carryforward
    total_offset = banked + harvested_loss
    used_against_gain = min(total_offset, gross_gain)
    residual_carryforward = max(0.0, total_offset - gross_gain)   # excess -> carries forward
    # tax benefit: the offset applied to the gain (the deferred value of any
    # residual carryforward is reported separately as the tax asset).
    tax_benefit = round(used_against_gain * tax_rate, 2)
    carryforward_value = round(residual_carryforward * tax_rate, 2)
    reserve_before = round(gross_gain * tax_rate, 2)                       # no offsets
    reserve_banked = round(max(0.0, gross_gain - banked) * tax_rate, 2)   # realized+CF only
    reserve_after = round(max(0.0, gross_gain - total_offset) * tax_rate, 2)  # + new harvest
    # value already secured by realized losses, and the extra from harvesting now
    realized_benefit = round((min(banked, gross_gain)) * tax_rate, 2)
    harvest_benefit = round(max(0.0, tax_benefit - realized_benefit), 2)
    # the loss carryforward is a deferred TAX ASSET (rate x usable residual)
    tax_asset = carryforward_value

    # ST/LT application: SHORT-TERM losses first offset SHORT-TERM gains at the higher
    # ORDINARY rate; only against ST gains do they capture that premium. With little/no
    # ST gains, the ST losses fall through to the LTCG inflow and apply at the LT
    # (blended) rate — the same rate as LT losses. We apply everything at the LT rate
    # (per principal: gain is LTCG, no ST gains) and REPORT the premium foregone.
    tm_d = (m["d"].get("tax_model") or {})
    ord_rate = float(tm_d.get("rate_ordinary") or 0) or tax_rate
    st_gains = float(tm_d.get("st_gains_ytd") or 0)      # household ST gains available (usually ~0)
    st_at_ordinary = min(realized_st, st_gains)          # the only ST loss that earns the premium
    st_at_blended = max(0.0, realized_st - st_at_ordinary)
    st_premium_foregone = round(st_at_blended * max(0.0, ord_rate - tax_rate), 2)

    # factor-tilt drift (household betas, before vs after removing harvested sleeves)
    excl = {p["label"] for p in sel}
    tilt_before = factor_tilt(m)
    tilt_after = factor_tilt(m, exclude_names=excl)
    factor_drift = {f: {"before": tilt_before[f], "after": tilt_after.get(f, 0.0),
                        "delta": round(tilt_after.get(f, 0.0) - tilt_before[f], 3)}
                    for f in m["factors"]}

    # concentration (sleeve-level HHI + count), before vs after
    vals = [abs(s["value"]) for s in m["assets"] if s["value"]]
    gmv = sum(vals) or 1.0
    hhi_before = round(sum((v / gmv) ** 2 for v in vals), 4)
    vals_after = [abs(s["value"]) for s in m["assets"] if s["value"] and s["name"] not in excl]
    gmv_a = sum(vals_after) or 1.0
    hhi_after = round(sum((v / gmv_a) ** 2 for v in vals_after), 4)

    # wash-sale lockout — 31 days
    try:
        d0 = datetime.date.fromisoformat(str(as_of)[:10]) if as_of else datetime.date.today()
    except ValueError:
        d0 = datetime.date.today()
    repurchase = (d0 + datetime.timedelta(days=31)).isoformat()
    lockout = [{"label": p["label"], "loss": p["loss"], "term": p["term"],
                "sale_date": d0.isoformat(), "earliest_repurchase": repurchase} for p in sel]

    return {"selected": sel, "harvested_loss": round(harvested_loss, 2),
            "carryforward": carryforward, "realized": round(realized, 2),
            "realized_st": round(realized_st, 2), "realized_lt": round(realized_lt, 2),
            "st_at_ordinary": round(st_at_ordinary, 2), "st_at_blended": round(st_at_blended, 2),
            "st_premium_foregone": st_premium_foregone, "ord_rate": ord_rate,
            "banked": round(banked, 2), "total_offset": round(total_offset, 2),
            "gross_gain": gross_gain, "used_against_gain": round(used_against_gain, 2),
            "residual_carryforward": round(residual_carryforward, 2),
            "tax_benefit": tax_benefit, "carryforward_value": carryforward_value,
            "tax_asset": tax_asset, "realized_benefit": realized_benefit,
            "harvest_benefit": harvest_benefit,
            "reserve_before": reserve_before, "reserve_banked": reserve_banked,
            "reserve_after": reserve_after,
            "tax_rate": tax_rate, "factor_drift": factor_drift,
            "hhi_before": hhi_before, "hhi_after": hhi_after,
            "positions_before": len(vals), "positions_after": len(vals_after),
            "lockout": lockout}
