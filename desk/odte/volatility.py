"""Timestamped market features and forward volatility outcomes, without causality claims."""
from __future__ import annotations

import datetime as dt
import json
import math
import os
from pathlib import Path
from statistics import mean, median
from zoneinfo import ZoneInfo

from desk.odte.storage import atomic_json

YEAR_SECONDS = 365 * 24 * 3600
ET = ZoneInfo("America/New_York")
CATALOG = {
    "minutes_to_close": "Minutes to 16:00 ET; intraday seasonality control.",
    "atm_iv": "Mean model IV of nearest-strike live put/call, annualized decimal.",
    "skew_25d": "Nearest 25-delta put IV minus call IV (each within 0.10 delta); annualized decimal.",
    "smile_curvature": "Mean nearest 25-delta wing IV minus ATM IV; annualized decimal.",
    "atm_straddle_pct": "ATM put+call midpoint premium / spot, percent.",
    "implied_remaining_move_pct": "ATM IV * sqrt(calendar time to close), percent; model approximation.",
    "quote_coverage": "Fraction of captured contracts with live-eligible quotes.",
    "median_relative_spread": "Median (ask-bid)/mid of live quotes; liquidity proxy.",
    "quote_age_p90_seconds": "90th percentile recorded quote age; quote liveness proxy.",
    "return_5m_pct": "Five-minute SPX log return, percent; continuous observed path required.",
    "realized_vol_15m": "Annualized sqrt(sum of minute log returns squared / calendar elapsed years).",
    "path_efficiency_15m": "Absolute net log move / sum absolute minute log moves; zero for a flat path.",
    "iv_to_realized_15m": "ATM IV / trailing 15-minute realized vol; null when realized vol is zero.",
    "atm_iv_change_15m": "ATM IV change over fifteen minutes, annualized decimal.",
    "vix1d_change_15m": "VIX1D index-point change over fifteen minutes.",
    "short_put_distance_pct": "Spot distance above selected short put, percent.",
    "short_call_distance_pct": "Selected short call distance above spot, percent.",
    "put_credit_share": "Put spread share of total entry credit; quote-based asymmetry.",
}


def stamp(row):
    return dt.datetime.fromisoformat(row["observed_at"])


def load(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def complete_path(rows, begin, end):
    selected = [r for r in rows if begin <= stamp(r) <= end]
    if not selected or stamp(selected[0]) != begin or stamp(selected[-1]) != end:
        return []
    if any(not r["indices_live"] or not finite(r.get("spx")) or r["spx"] <= 0 for r in selected):
        return []
    if any((stamp(b) - stamp(a)).total_seconds() > 90 for a, b in zip(selected, selected[1:])):
        return []
    return selected


def realized(path):
    returns = [math.log(b["spx"] / a["spx"]) for a, b in zip(path, path[1:])]
    elapsed = (stamp(path[-1]) - stamp(path[0])).total_seconds()
    return math.sqrt(sum(r*r for r in returns) * YEAR_SECONDS / elapsed), returns


def values(snap, previous, candidate=None):
    now = dt.datetime.fromisoformat(snap["ts"]).astimezone(ET)
    result = dict.fromkeys(CATALOG)
    result["minutes_to_close"] = max(0., (now.replace(hour=16, minute=0, second=0) - now).total_seconds() / 60)
    rows = snap.get("rows", [])
    live = [r for r in rows if r.get("live_eligible") and finite(r.get("ask")) and finite(r.get("bid"))
            and r["ask"] >= r["bid"] >= 0 and r["ask"] > 0]
    result["quote_coverage"] = len(live) / len(rows) if rows else None
    spreads = [(r["ask"] - r["bid"]) / ((r["ask"] + r["bid"]) / 2) for r in live if r["ask"] + r["bid"] > 0]
    result["median_relative_spread"] = median(spreads) if spreads else None
    ages = sorted(r["quote_age_s"] for r in live if finite(r.get("quote_age_s")))
    result["quote_age_p90_seconds"] = ages[min(len(ages)-1, int(.9*len(ages)))] if ages else None
    spot = snap.get("xsp") if snap.get("indices_live") else None
    ivs = [r for r in live if finite(r.get("iv")) and r["iv"] > 0 and finite(r.get("delta"))]
    if spot and all(any(r["right"] == side for r in ivs) for side in ("P", "C")):
        atm = [min((r for r in ivs if r["right"] == side), key=lambda r: abs(r["strike"]-spot)) for side in ("P", "C")]
        wings = [min((r for r in ivs if r["right"] == side), key=lambda r: abs(abs(r["delta"])-.25)) for side in ("P", "C")]
        result.update(atm_iv=mean(r["iv"] for r in atm),
                      atm_straddle_pct=100 * sum((r["bid"]+r["ask"])/2 for r in atm) / spot)
        if all(abs(abs(r["delta"])-.25) <= .10 for r in wings):
            result.update(skew_25d=wings[0]["iv"]-wings[1]["iv"],
                          smile_curvature=mean(r["iv"] for r in wings)-result["atm_iv"])
        result["implied_remaining_move_pct"] = 100 * result["atm_iv"] * math.sqrt(result["minutes_to_close"]*60/YEAR_SECONDS)
    current = {"observed_at": snap["ts"], "spx": snap.get("spx"), "indices_live": bool(snap.get("indices_live")),
               "vix1d": snap.get("vix1d"), "features": result}
    history = previous + [current]
    def trailing(minutes):
        # Real capture clocks have seconds/jitter. Use a prior observation at or
        # before the boundary, never a later observation substituted backward.
        boundary = now-dt.timedelta(minutes=minutes)
        start = next((r for r in reversed(previous) if stamp(r) <= boundary), None)
        return complete_path(history, stamp(start), now) if start and (boundary-stamp(start)).total_seconds() <= 90 else []
    path = trailing(5)
    if path:
        result["return_5m_pct"] = 100 * math.log(path[-1]["spx"] / path[0]["spx"])
    path = trailing(15)
    if path:
        rv, returns = realized(path)
        result["realized_vol_15m"] = rv
        result["path_efficiency_15m"] = abs(sum(returns)) / sum(abs(v) for v in returns) if any(returns) else 0.
        if result["atm_iv"] is not None:
            result["iv_to_realized_15m"] = result["atm_iv"] / rv if rv > 0 else None
            old_iv = path[0]["features"].get("atm_iv")
            if old_iv is not None:
                result["atm_iv_change_15m"] = result["atm_iv"] - old_iv
        if finite(snap.get("vix1d")) and finite(path[0].get("vix1d")):
            result["vix1d_change_15m"] = snap["vix1d"] - path[0]["vix1d"]
    if candidate and spot:
        legs = candidate["legs"]
        result.update(short_put_distance_pct=100*(spot-legs["sp"]["strike"])/spot,
                      short_call_distance_pct=100*(legs["sc"]["strike"]-spot)/spot,
                      put_credit_share=(legs["sp"]["bid"]-legs["lp"]["ask"])/candidate["credit"])
    return result


def record(root, snap, protocol, recorded_at, candidate=None):
    """Append one hash-linked observation including raw inputs. Caller holds lock."""
    from desk.odte.text_overlay import digest
    date = dt.datetime.fromisoformat(snap["ts"]).astimezone(ET).date().isoformat()
    path = Path(root) / "observations" / (date + ".jsonl")
    previous = load(path)
    last_id = None
    for old in previous:
        if old["protocol"] != protocol or old["previous_id"] != last_id or old["id"] != digest({k: v for k, v in old.items() if k != "id"}):
            raise ValueError("Observation ledger integrity/protocol failure")
        last_id = old["id"]
    if previous and previous[-1]["observed_at"] == snap["ts"]:
        if previous[-1]["snapshot_digest"] != digest(snap):
            raise ValueError("Conflicting snapshot for an already recorded timestamp")
        forward_outcomes(root, previous, recorded_at)
        return previous[-1]
    if previous and stamp(previous[-1]) >= dt.datetime.fromisoformat(snap["ts"]):
        raise ValueError("Out-of-order market observation")
    row = {"observed_at": snap["ts"], "recorded_at": recorded_at.isoformat(), "protocol": protocol,
           "snapshot_digest": digest(snap), "previous_id": previous[-1]["id"] if previous else None,
           "spx": snap.get("spx"), "vix1d": snap.get("vix1d"), "indices_live": bool(snap.get("indices_live")),
           "features": values(snap, previous, candidate), "raw_snapshot": snap, "candidate": candidate}
    row["id"] = digest(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps(row, allow_nan=False) + "\n"); stream.flush(); os.fsync(stream.fileno())
    forward_outcomes(root, previous + [row], recorded_at)
    return row


def forward_outcomes(root, rows, recorded_at):
    """One anchor in the 10:00 minute per session, allowing real capture-clock jitter."""
    from desk.odte.text_overlay import admitted_forecast, read, digest
    current = stamp(rows[-1]).astimezone(ET)
    start = next((r for r in rows if stamp(r).astimezone(ET).strftime("%H:%M") == "10:00"), None)
    if start is None:
        return
    anchor = stamp(start).astimezone(ET)
    for horizon in (15, 60):
        end = anchor + dt.timedelta(minutes=horizon)
        output = Path(root) / "volatility_outcomes" / f"{anchor.date()}_{horizon}m.json"
        if current < end or output.exists():
            continue
        last = next((r for r in rows if stamp(r) >= end), None)
        path = complete_path(rows, anchor, stamp(last)) if last and (stamp(last)-end).total_seconds() <= 90 else []
        forecast = admitted_forecast(root, str(anchor.date()), read(Path(root) / "manifest.json"), anchor)
        result = {"date": anchor.date().isoformat(), "horizon_minutes": horizon, "observed_at": anchor.isoformat(),
                  "resolved_at": recorded_at.isoformat(), "observation_id": start["id"], "protocol": start["protocol"],
                  "features": start["features"], "status": "resolved" if path else "unresolved", "targets": {},
                  "forecast_id": forecast["id"] if forecast else None,
                  "text_reasons": forecast["forecast"]["reasons"] if forecast else [],
                  "elapsed_seconds": (stamp(path[-1])-anchor).total_seconds() if path else None}
        if path:
            result["targets"]["forward_realized_vol"] = realized(path)[0]
            for label, getter in (("atm_iv_change", lambda r: r["features"].get("atm_iv")),
                                  ("vix1d_change", lambda r: r.get("vix1d")),
                                  ("spread_change", lambda r: r["features"].get("median_relative_spread"))):
                first, last = getter(path[0]), getter(path[-1])
                result["targets"][label] = last-first if finite(first) and finite(last) else None
        result["id"] = digest(result)
        atomic_json(output, result)


def effects(root):
    """Exploratory lagged associations across distinct sessions, never feature selection."""
    root = Path(root)
    outcomes = [json.loads(p.read_text()) for p in sorted((root / "volatility_outcomes").glob("*.json"))]
    from desk.odte.forecast_worker import TAGS
    from desk.odte.text_overlay import digest
    for row in outcomes:
        if row["id"] != digest({k: v for k, v in row.items() if k != "id"}):
            raise ValueError("Volatility outcome integrity failure")
    associations, tag_groups = [], []
    for horizon in (15, 60):
        rows = [r for r in outcomes if r["status"] == "resolved" and r["horizon_minutes"] == horizon]
        for name in CATALOG:
            for target in ("forward_realized_vol", "atm_iv_change", "vix1d_change", "spread_change"):
                pairs = [(r["features"][name], r["targets"].get(target)) for r in rows
                         if finite(r["features"].get(name)) and finite(r["targets"].get(target))]
                corr = None
                if len(pairs) >= 3:
                    xs, ys = zip(*pairs); mx, my = mean(xs), mean(ys)
                    den = math.sqrt(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))
                    if den:
                        corr = sum((x-mx)*(y-my) for x, y in pairs)/den
                associations.append({"feature": name, "target": target, "horizon_minutes": horizon,
                                     "sessions": len(pairs), "pearson_r": corr})
        # Count each tagged session once, regardless of how many reasons repeat
        # the same tag. Uncovered days are unknown, never "event absent".
        covered = [r for r in rows if r.get("forecast_id")]
        for field, options in TAGS.items():
            for tag in options:
                tagged = [r for r in covered if any(reason[field] == tag for reason in r["text_reasons"])]
                untagged = [r for r in covered if r not in tagged]
                for target in ("forward_realized_vol", "atm_iv_change", "vix1d_change", "spread_change"):
                    yes = [r["targets"][target] for r in tagged if finite(r["targets"].get(target))]
                    no = [r["targets"][target] for r in untagged if finite(r["targets"].get(target))]
                    tag_groups.append({"field": field, "tag": tag, "target": target, "horizon_minutes": horizon,
                        "tagged_sessions": len(yes), "other_covered_sessions": len(no),
                        "tagged_mean": mean(yes) if yes else None, "other_covered_mean": mean(no) if no else None})
    return {"status": "exploratory_only", "feature_catalog": CATALOG, "associations": associations,
            "text_taxonomy": TAGS, "text_tag_groups": tag_groups,
            "resolved_windows": sum(r["status"] == "resolved" for r in outcomes),
            "unresolved_windows": sum(r["status"] != "resolved" for r in outcomes),
            "interpretation": "Lagged association, not causation. One observation in the 10:00 minute per session/horizon. Text tags are LLM hypotheses; no tag does not establish absence. Multiple comparisons; no significance or promotion claims. Market regimes and news selection confound associations."}
