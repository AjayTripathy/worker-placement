"""resort_snowpack — the physical variable behind a pre-sold ski season.

THE LAG IS THE WHOLE POINT. Vail and its peers sell season passes in SPRING for the FOLLOWING
winter. So the pass-sales number reported in the autumn is conditioned by the snow experience
customers just had, not by the winter being sold. That makes LAST season's snowpack a genuinely
LEADING read on NEXT season's pre-sold revenue — and it is free, daily, and published by the
US government while the company reports quarterly.

Reading current snowpack in August tells you nothing (northern-hemisphere SWE is ~zero). Reading
the PEAK snow-water-equivalent of the season just completed, against that station's own long-run
median, tells you what the pass buyer remembers.

WHY THIS IS THE RIGHT VARIABLE. A ski operator's revenue is pre-sold deferred revenue — the same
float structure as an expedition cruise's deposits (see expedition_inventory). But unlike the
cruise operator, the ski operator's product quality is set by weather it does not control, and
that weather is measured for free at the mountain by NRCS SNOTEL stations sited ON the resorts.
Snowpack is therefore the rare kill-variable that is both decisive and cheaply observable.

SOURCE: USDA NRCS AWDB (SNOTEL). No API key. Two endpoints, both probed working 2026-08-18:
  - awdbRestApi/services/v1/stations   — station metadata
  - awdbRestApi/services/v1/data       — WTEQ (snow water equivalent) daily series
WTEQ, not snow DEPTH, is the correct measure: depth varies with density, water equivalent is the
conserved quantity and is what percent-of-median is normally quoted against.

HONEST LIMITS, stated because a physical proxy invites over-reading:
  - A SNOTEL station is a POINT on a mountain, not the skiable terrain; it tracks the season's
    shape well and absolute conditions poorly.
  - Snowpack conditions DEMAND, not revenue. Vail's pass model deliberately decouples revenue
    from weather in the sold year — that is the strategy. The transmission runs through the NEXT
    pass cycle and through in-resort ancillary spend, not through the current season's pass line.
  - Percent-of-median needs a long station history; where it is missing the connector says so
    rather than inventing a baseline.

    python3 -m verticals.buyside_dd.connectors.resort_snowpack [--ticker MTN]
"""
from __future__ import annotations

APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['7011', '7999', '7990'],
    "issuer_features": ['ski_resort_operator', 'weather_dependent_demand',
                        'presold_season_pass', 'forward_booked_inventory'],
    "asset_classes": ['public_equity'],
    "applies_universally": False,
    "summary": ('Prior-season peak snow-water-equivalent vs station median at the resorts that '
                'drive visitation — a leading read on the NEXT pass-sales cycle, since passes are '
                'sold in spring on the strength of the winter just experienced.'),
    "verification_question": ("Did the season customers just experienced deliver snow above or "
                              "below normal at the mountains that matter — i.e. is the next "
                              "pass-sales cycle being sold into a good memory or a bad one?"),
}

import argparse
import json
import statistics
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve()
if str(HERE.parents[3]) not in sys.path:
    sys.path.insert(0, str(HERE.parents[3]))

from .base import (BaseConnector, ConnectorObservation, ConnectorRequest,
                   ConnectorResult, ErrorKind)

OUT_DIR = HERE.parents[1] / "outputs" / "resort_snowpack"
OUT = OUT_DIR / "RESORT_SNOWPACK.json"
API = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
_HDRS = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
         "Accept": "application/json"}

# SNOTEL stations sited at or adjacent to the resorts that carry the pass. Deliberately a
# CURATED map, not a radius search: a station in the wrong drainage is worse than no station.
RESORTS = {
    "MTN": {
        "name": "Vail Resorts",
        "stations": {
            "842:CO:SNTL": "Vail Mountain (Vail, CO)",
            "1120:CO:SNTL": "Copper Mountain (Summit Cty — Keystone/Breck proxy)",
            "531:CO:SNTL": "Fremont Pass (Summit Cty)",
            "802:UT:SNTL": "Thaynes Canyon (Park City, UT)",
            "1050:CA:SNTL": "Squaw Valley G.C. (Tahoe — Heavenly/Northstar/Kirkwood proxy)",
        },
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _water_year(d: date) -> int:
    """US water year runs Oct 1 - Sep 30 and is named for the ENDING calendar year."""
    return d.year + 1 if d.month >= 10 else d.year


def _fetch_wteq(triplet: str, begin: str, end: str, timeout: float = 30.0) -> list[tuple[str, float]]:
    try:
        r = requests.get(f"{API}/data", headers=_HDRS, timeout=timeout,
                         params={"stationTriplets": triplet, "elements": "WTEQ",
                                 "duration": "DAILY", "beginDate": begin, "endDate": end,
                                 "periodRef": "END", "returnFlags": "false"})
        if r.status_code != 200:
            return []
        out = []
        for st in r.json() or []:
            for el in st.get("data", []) or []:
                for v in el.get("values", []) or []:
                    d, val = v.get("date"), v.get("value")
                    if d and val is not None:
                        try:
                            out.append((d, float(val)))
                        except (TypeError, ValueError):
                            continue
        return out
    except (requests.RequestException, ValueError):
        return []


def scan(ticker: str = "MTN", history_years: int = 12, verbose: bool = True) -> dict:
    cfg = RESORTS.get(ticker.upper())
    if not cfg:
        return {"error": f"no resort/station map for {ticker}; known: {sorted(RESORTS)}"}
    today = date.today()
    cur_wy = _water_year(today)
    # The season CUSTOMERS JUST EXPERIENCED is the completed water year — that is what conditions
    # the pass cycle now being sold. In August, cur_wy is the one that just ended.
    target_wy = cur_wy
    begin = f"{target_wy - history_years}-10-01"
    end = today.isoformat()

    stations, failures = {}, []
    for triplet, label in cfg["stations"].items():
        series = _fetch_wteq(triplet, begin, end)
        if not series:
            failures.append(f"{triplet} ({label})")
            continue
        by_wy: dict[int, list[float]] = {}
        for ds, val in series:
            try:
                d = date.fromisoformat(ds[:10])
            except ValueError:
                continue
            by_wy.setdefault(_water_year(d), []).append(val)
        peaks = {wy: max(v) for wy, v in by_wy.items() if v}
        cur_peak = peaks.get(target_wy)
        hist = [p for wy, p in peaks.items() if wy != target_wy and p > 0]
        med = statistics.median(hist) if len(hist) >= 5 else None
        stations[triplet] = {
            "label": label,
            "target_water_year": target_wy,
            "peak_swe_in": round(cur_peak, 1) if cur_peak is not None else None,
            "median_peak_swe_in": round(med, 1) if med is not None else None,
            "pct_of_median": (round(100 * cur_peak / med, 0)
                              if (cur_peak is not None and med) else None),
            "history_years_used": len(hist),
            "baseline_note": (None if med is not None else
                              "INSUFFICIENT HISTORY (<5 prior water years) — no median asserted"),
        }

    vals = [s["pct_of_median"] for s in stations.values() if s["pct_of_median"] is not None]
    agg = {
        "ticker": ticker.upper(), "operator": cfg["name"], "asof": _now(),
        "season_just_experienced": target_wy,
        "stations_read": len(stations), "stations_unreachable": failures,
        "mean_pct_of_median": round(sum(vals) / len(vals), 0) if vals else None,
        "stations_with_baseline": len(vals),
        "read": None,
    }
    if vals:
        m = agg["mean_pct_of_median"]
        agg["read"] = (
            f"The season customers just experienced ran at ~{m:.0f}% of median peak snowpack "
            f"across {len(vals)} resort stations. " +
            ("BELOW normal — the next pass cycle is being sold into a poor memory, which pressures "
             "renewal rates and in-resort ancillary spend even though the PASS revenue for the "
             "sold year is contractually insulated." if m < 90 else
             "ABOVE normal — the next pass cycle is being sold into a good memory, supportive of "
             "renewals and ancillary spend." if m > 110 else
             "AROUND normal — no snow-driven edge in either direction this cycle."))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    store = json.loads(OUT.read_text()) if OUT.exists() else {"runs": []}
    store["runs"].append({**agg, "stations": stations})
    OUT.write_text(json.dumps(store, indent=1))

    res = {**agg, "stations": stations,
           "limits": ["A SNOTEL station is a POINT, not the skiable terrain — good on season "
                      "shape, poor on absolute conditions.",
                      "Snowpack conditions DEMAND, not the sold year's pass revenue: Vail's model "
                      "deliberately decouples revenue from weather in-season. Transmission runs "
                      "through the NEXT pass cycle and ancillary spend.",
                      "Percent-of-median requires >=5 prior water years; stations without it are "
                      "reported with no median rather than an invented baseline."]}
    if verbose:
        print(f"[resort_snowpack] {ticker} — season just experienced: WY{target_wy}")
        for t, s in stations.items():
            print(f"  {s['label'][:44]:44s} peak {str(s['peak_swe_in']):>6s}\" "
                  f"median {str(s['median_peak_swe_in']):>6s}\" "
                  f"= {str(s['pct_of_median']):>5s}% of median  ({s['history_years_used']}y hist)")
        if failures:
            print(f"  UNREACHABLE (never counted as zero): {failures}")
        print(f"  -> {agg['read']}")
    return res


class ResortSnowpackConnector(BaseConnector):
    source_id = "resort_snowpack"
    rate_limit_per_min = 30

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        # Benches dispatch on what they are reasoning about — a RESORT NAME ("Vail Mountain"),
        # not a ticker. Keying resolution on the ticker alone made this connector return
        # UNSUPPORTED to every real call: the MTN bench got 5 dispatches / 0 observations and
        # correctly logged "infra failure wearing the costume of an analytic absence". Passing the
        # contract test proved only that it declined POLITELY, not that it was usable.
        raw = (request.extra.get("ticker") or request.extra.get("operator")
               or request.entity_name or request.extra.get("resort") or "")
        t = str(raw).upper().strip()
        if t not in RESORTS:
            hay = t.replace("_", " ")
            for tk, cfg in RESORTS.items():           # resort/operator NAME -> ticker
                names = [cfg["name"].upper()] + [v.upper() for v in cfg["stations"].values()]
                if any(hay and (hay in n or n.split(" (")[0] in hay) for n in names):
                    t = tk
                    break
        if t not in RESORTS:
            known = {tk: cfg["name"] for tk, cfg in RESORTS.items()}
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              f"no resort/station map for {raw!r}. Mapped operators: {known}. "
                              f"Dispatch with a ticker, operator name, or a mapped resort name.")
        d = scan(t, verbose=False)
        obs = [ConnectorObservation(
            attribute="prior_season_snowpack_pct_of_median", value=d.get("mean_pct_of_median"),
            value_unit="% of station median peak SWE",
            confidence=0.7 if d.get("stations_with_baseline") else 0.0,
            extra={"season": d.get("season_just_experienced"),
                   "stations": d.get("stations_with_baseline"),
                   "unreachable": d.get("stations_unreachable"), "read": d.get("read")})]
        for triplet, s in (d.get("stations") or {}).items():
            obs.append(ConnectorObservation(
                attribute="resort_station_peak_swe", value=s.get("pct_of_median"),
                value_unit="% of median", extra={**s, "station": triplet}))
        return self._ok(request, obs, raw=json.dumps(d)[:2000])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="MTN")
    a = ap.parse_args()
    scan(a.ticker)
