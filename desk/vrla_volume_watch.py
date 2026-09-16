"""vrla_volume_watch — forward instrumentation for the VRLA.PA starter (v1.5 doctrine, built 2026-07-29).

The position's volume kill-bar is "Q3 volumes negative YoY" (graded at the Oct-27 Q3 report).
This watch gives that bar a MONTHLY leading read from Eurostat's short-term production index for
NACE C23.13 "manufacture of hollow glass" (dataset sts_inpr_m, calendar-adjusted, 2021=100),
pulled for Verallia's European footprint: FR / IT / ES (/PT when published) / DE + EU27 aggregate.

BASIS RISK (named, standing): the index measures ALL hollow-glass production in each country —
competitors' plants (O-I, Vidrala, Wiegand) and non-container hollow glass (tableware) included —
so it proxies the MARKET Verallia sells into, not Verallia's own shipped tonnes. Direction and
persistence are the signal, never the level. Publication lag ~2 months (July shows May).

Flags: footprint-weighted YoY < -2% for 2+ consecutive months = the volume kill-bar read-through
(escalate to the EC); latest month positive = INFO recovery corroboration. DATA MISSING never zero.
State: desk/data/vrla_volume/{state.json,history.jsonl}. TRIPWIRE NOWCAST, not alpha.
"""
from __future__ import annotations
import json, sys, datetime, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "desk" / "data" / "vrla_volume"
STATE = DATA / "state.json"
HISTORY = DATA / "history.jsonl"

API = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_inpr_m"
       "?nace_r2=C2313&s_adj=CA&unit=I21"
       "&geo=EU27_2020&geo=FR&geo=IT&geo=ES&geo=DE&geo=PT"
       "&sinceTimePeriod={since}&format=JSON&lang=EN")

# Rough Verallia-footprint revenue weights (label stays ROUGH; renormalized over available geos).
WEIGHTS = {"FR": 0.35, "IT": 0.20, "ES": 0.20, "PT": 0.05, "DE": 0.10, "EU27_2020": 0.10}
FLAG_BAR = -2.0   # footprint-weighted YoY % below this, 2+ consecutive months -> kill-bar read-through


def fetch(since: str) -> dict | None:
    try:
        with urllib.request.urlopen(API.format(since=since), timeout=60) as r:
            return json.load(r)
    except Exception:
        return None


def parse(d: dict) -> dict[str, dict[str, float]]:
    """JSON-stat -> {geo: {YYYY-MM: index_value}} (row-major flattened value map)."""
    dims, sizes, vals = d["id"], d["size"], d["value"]
    cat = {dim: d["dimension"][dim]["category"]["index"] for dim in dims}
    times = sorted(cat["time"], key=cat["time"].get)
    out: dict[str, dict[str, float]] = {}
    for g in cat["geo"]:
        series = {}
        for t in times:
            idx = 0
            for dim, size in zip(dims, sizes):
                key = g if dim == "geo" else (t if dim == "time" else next(iter(cat[dim])))
                idx = idx * size + cat[dim][key]
            v = vals.get(str(idx))
            if v is not None:
                series[t] = v
        if series:
            out[g] = series
    return out


def yoy(series: dict[str, float], month: str) -> float | None:
    y, m = month.split("-")
    prior = f"{int(y)-1}-{m}"
    if month in series and prior in series and series[prior]:
        return round(100.0 * (series[month] / series[prior] - 1.0), 1)
    return None


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    since = (datetime.date.today().replace(day=1) - datetime.timedelta(days=31 * 31)).strftime("%Y-%m")
    raw = fetch(since)
    if raw is None:
        snap = {"ts": now, "status": "DATA MISSING", "detail": "Eurostat API fetch failed"}
        STATE.write_text(json.dumps(snap, indent=1))
        with HISTORY.open("a") as f:
            f.write(json.dumps(snap) + "\n")
        print(f"[vrla_volume] {now} DATA MISSING — Eurostat fetch failed (never read as zero)")
        return 0
    try:
        geos = parse(raw)
    except Exception as e:
        print(f"[vrla_volume] {now} DATA MISSING — JSON-stat parse failed: {e}")
        return 0
    if not geos:
        print(f"[vrla_volume] {now} DATA MISSING — 0 series parsed")
        return 0

    all_months = sorted({m for s in geos.values() for m in s})
    last3 = all_months[-3:]
    table: dict[str, dict[str, float | None]] = {g: {m: yoy(s, m) for m in last3} for g, s in geos.items()}

    weighted: dict[str, float | None] = {}
    for m in last3:
        avail = {g: table[g][m] for g in WEIGHTS if table.get(g, {}).get(m) is not None}
        if avail:
            wsum = sum(WEIGHTS[g] for g in avail)
            weighted[m] = round(sum(WEIGHTS[g] * avail[g] for g in avail) / wsum, 1)
        else:
            weighted[m] = None

    flags = []
    wvals = [v for v in (weighted.get(m) for m in last3) if v is not None]
    if len(wvals) >= 2 and wvals[-1] < FLAG_BAR and wvals[-2] < FLAG_BAR:
        flags.append(f"FLAG: footprint-weighted hollow-glass production YoY < {FLAG_BAR}% two consecutive months "
                     f"({wvals[-2]}%, {wvals[-1]}%) — VOLUME KILL-BAR READ-THROUGH, escalate to VRLA_PA.json")
    elif wvals and wvals[-1] > 0:
        flags.append(f"INFO: latest footprint-weighted YoY positive ({wvals[-1]}%) — corroborates the stable-volume leg")

    snap = {"ts": now, "status": "ok", "latest_month": last3[-1], "lag_note": "~2-month publication lag",
            "yoy_by_geo": table, "footprint_weighted_yoy": weighted,
            "weights_rough": WEIGHTS, "flags": flags,
            "basis_risk": "market production index incl competitors + tableware, NOT Verallia shipments"}
    STATE.write_text(json.dumps(snap, indent=1))
    with HISTORY.open("a") as f:
        f.write(json.dumps(snap) + "\n")

    print(f"[vrla_volume] {now} — Eurostat sts_inpr_m C2313 (hollow glass, CA, 2021=100); "
          f"latest {last3[-1]} (~2mo lag)")
    print(f"  {'geo':10} " + "  ".join(f"{m:>8}" for m in last3))
    for g in ("FR", "IT", "ES", "PT", "DE", "EU27_2020"):
        if g in table:
            print(f"  {g:10} " + "  ".join(f"{(str(table[g][m]) + '%') if table[g][m] is not None else '—':>8}" for m in last3))
    print(f"  {'WEIGHTED':10} " + "  ".join(f"{(str(weighted[m]) + '%') if weighted[m] is not None else '—':>8}" for m in last3)
          + "   (rough footprint weights, renormalized)")
    for fl in flags:
        print(f"  {fl}")
    if not flags:
        print("  no flags")
    print("  grades alongside the Q3 print (Oct-27); basis risk: market index ≠ Verallia volumes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
