"""official_series — the desk's MARKET LAYER: a registry of official-statistics series
any issuer can be dispatched against.

WHY A REGISTRY AND NOT A WATCH
------------------------------
The desk keeps re-solving the same problem one name at a time: VRLA needed Eurostat
hollow-glass production, WAL/FSBW needed FDIC call reports, KALMAR needed TED tenders
and Census HS imports. Each landed as a bespoke module with its own fetch, its own
cache, its own staleness rule, its own failure semantics — and none of them is
reachable by any OTHER issuer that happens to share the exposure. A Macau-exposed
name (LVS, WYNN, MGM, MLCO, 27.HK, 1928.HK) needs DICJ gross gaming revenue exactly
the way Verallia needs C23.13, and building macau_ggr_watch.py would have been the
seventh instance of the same mistake.

So this module owns the PATTERN, not the instance:

    ONE m_source ("official statistics"), MANY registered series.

A series row declares what it is (agency, geo, UNIT stated explicitly, cadence,
release lag), how to get it (an adapter keyed by AGENCY, not by series — one dicj(),
one dsec(), and every future series from that agency is a registry row rather than a
new fetcher), and WHICH ISSUER FEATURES IT SERVES. Dispatch then matches issuer ->
series the same way the KG matches issuer -> detector, and render_series() drops the
matched table straight into the bench/planner prompts. Adding Macau hotel occupancy
was three lines; adding a whole new agency is one adapter.

The existing bespoke watches are listed as COMMENTED migration candidates below.
They are not moved in this pass (each carries live tripwire logic wired to a
position); the point is that the registry is where they converge.

FAILURE SEMANTICS (fc34665d doctrine, mirrored from facilities_resolver exactly)
-------------------------------------------------------------------------------
  INFRA failure  (fetch empty / non-404 HTTP error / unparseable / wrong-shaped
                  payload / unit drift) -> "degraded" field, surfaced LOUD,
                  NEVER cached. A transient DICJ outage must not become a sticky
                  "no observations" for a month.
  Genuine empty  (the document parsed fine and simply holds no published period
                  yet — e.g. a January report before the first release) -> a real
                  observation of absence, and IS cached.
  History        accumulates. Observations MERGE by period; the array is never
                  overwritten wholesale, and a changed value is recorded as a
                  REVISION (official statistics get revised — silently clobbering
                  the old print destroys the only record that it happened).

Cache: desk/data/official_series/<key>.json
  {series meta, observations: [{period, value, unit, fetched}], asof}
Staleness (monthly): refetch when a new release is plausibly out — i.e. the cached
  latest period is behind the period the release lag says should exist by now, OR
  the cache was written in a previous month. A once-per-day floor keeps the bench
  prompts from re-polling an agency on every court.

  python3 -m desk.official_series list
  python3 -m desk.official_series fetch macau_ggr [--refresh]
  python3 -m desk.official_series nowcast macau_ggr [--quarter 2026Q3]
  python3 -m desk.official_series refresh            # the weekly watch entrypoint
"""
from __future__ import annotations

import datetime
import json
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "desk" / "data" / "official_series"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
UA = "SignalOS research desk (contact: 4tripathy@gmail.com)"
TIMEOUT_S = 45
MIN_REFETCH_HOURS = 20          # politeness floor: never re-poll an agency intraday
HISTORY_MONTHS = 30             # how deep each refresh pulls (>=24 so YoY always resolves)


# ─────────────────────────────────────────────────────────────────────────────
# SERIES REGISTRY — one m_source, many series
# ─────────────────────────────────────────────────────────────────────────────
# Every row states its UNIT EXPLICITLY (the desk's standing TEY/gross-yield lesson:
# an unnamed metric gets conflated within two sessions).
#
#   yoy_mode      "pct_change" for levels, "pp_delta" for series already in percent
#   aggregatable  False for rates/ratios — summing an occupancy rate over a quarter
#                 is arithmetic nonsense, so nowcast_quarter REFUSES rather than
#                 quietly producing a number
#   match_tokens  geo/topic gate for render_series. SIC alone must NOT fire a
#                 geo-specific series: sic_prefixes 70/79/58 would hand Macau GGR to
#                 Marriott and Chipotle. A series fires on an explicit ticker, an
#                 explicit issuer feature, or a geo token in the case text.
SERIES: dict[str, dict] = {
    "macau_ggr": {
        "key": "macau_ggr",
        "name": "Macau monthly gross revenue from games of fortune",
        "agency": "DICJ (Gaming Inspection and Coordination Bureau, Macao SAR)",
        "geo": "Macau SAR",
        "unit": "MOP million (gross gaming revenue, all games of fortune)",
        "cadence": "monthly",
        "release_lag": "published on the 1st business day of the following month "
                       "(the fastest official read on the whole Macau gaming complex)",
        "release_lag_months": 1,
        "adapter": "dicj",
        "params": {"report": "monthly_gross_revenue"},
        "yoy_mode": "pct_change",
        "aggregatable": True,
        "status": "LIVE",
        "issuer_features": ["casino_gaming_revenue", "macau_exposure",
                            "official_series_demand_proxy"],
        "tickers": ["LVS", "WYNN", "MGM", "MLCO", "MSC", "1928.HK", "0027.HK",
                    "27.HK", "0880.HK", "880.HK", "2282.HK", "6883.HK", "0200.HK",
                    "200.HK", "WYNNMACAU", "SANDSCHINA"],
        "match_tokens": ["macau", "macao", "cotai", "ggr", "gross gaming revenue",
                         "sands china", "wynn macau", "galaxy entertainment",
                         "sjm", "melco", "mgm china"],
        "note": "THE headline number for every Macau operator; the whole market's "
                "monthly revenue, so it is a market-share denominator as well as a "
                "demand read. Concession-wide: it does not split by operator.",
    },
    "macau_visitor_arrivals": {
        "key": "macau_visitor_arrivals",
        "name": "Macau total visitor arrivals",
        "agency": "DSEC (Statistics and Census Service, Macao SAR)",
        "geo": "Macau SAR",
        "unit": "visitors (persons, total arrivals, all modes of transport)",
        "cadence": "monthly",
        "release_lag": "published ~4 weeks after month end (July data lands late August)",
        "release_lag_months": 2,
        "adapter": "dsec",
        "params": {"indicator_id": 14023,
                   "indicator_path": "Tourism and services > Tourism > Visitors > "
                                     "Visitor Arrivals > in and after 2008 > Visitors > "
                                     "By Mode of Transport (parent node carries the total)"},
        "yoy_mode": "pct_change",
        "aggregatable": True,
        "status": "LIVE",
        "issuer_features": ["macau_exposure", "tourism_demand",
                            "official_series_demand_proxy"],
        "tickers": ["LVS", "WYNN", "MGM", "MLCO", "MSC", "1928.HK", "0027.HK", "27.HK",
                    "0880.HK", "880.HK", "2282.HK", "6883.HK", "0200.HK", "200.HK"],
        "match_tokens": ["macau", "macao", "cotai", "visitor arrivals",
                         "mass market", "sands china", "wynn macau", "melco"],
        "note": "The traffic leg of the two-factor read (traffic x spend-per-visit). "
                "Cross-checks GGR: arrivals up while GGR down = spend-per-visit "
                "compression, a different thesis from a demand fall.",
    },
    "macau_hotel_occupancy": {
        "key": "macau_hotel_occupancy",
        "name": "Macau average hotel occupancy rate (all hotels and similar establishments)",
        "agency": "DSEC (Statistics and Census Service, Macao SAR)",
        "geo": "Macau SAR",
        "unit": "percent (average occupancy rate; NOT an index, NOT a room count)",
        "cadence": "monthly",
        "release_lag": "published ~4 weeks after month end",
        "release_lag_months": 2,
        "adapter": "dsec",
        "params": {"indicator_id": 13005,
                   "indicator_path": "Tourism and services > Tourism > Hotel "
                                     "establishments > Average occupancy rate"},
        "yoy_mode": "pp_delta",          # a rate: report percentage POINTS, never % of %
        "aggregatable": False,           # cannot be summed across a quarter
        "status": "LIVE",
        "issuer_features": ["macau_exposure", "hotel_occupancy_metric",
                            "tourism_demand", "official_series_demand_proxy"],
        "tickers": ["LVS", "WYNN", "MGM", "MLCO", "MSC", "1928.HK", "0027.HK", "27.HK",
                    "0880.HK", "880.HK", "2282.HK", "6883.HK", "0200.HK", "200.HK"],
        "match_tokens": ["macau", "macao", "cotai", "hotel occupancy", "room nights",
                         "integrated resort"],
        "note": "Capacity-side cross-check on arrivals: occupancy holding while "
                "arrivals fall means room supply, not demand, moved. Whole-territory "
                "average, so it is the market a single property competes in, not the "
                "property's own run-rate.",
    },

    # ── MIGRATION CANDIDATES (declared, NOT implemented in this pass) ──────────
    # These already run as bespoke watches, each with its own fetch/cache/staleness
    # code and its own failure semantics. They belong here as registry rows behind a
    # per-AGENCY adapter; they are left alone for now because each is wired to a live
    # position's tripwires and moving them is a separate, gradeable change.
    #
    # "eurostat_hollow_glass_c2313": {
    #     agency "Eurostat", unit "index, 2021=100 (calendar-adjusted production)",
    #     cadence monthly, release_lag "~2 months (July shows May)",
    #     adapter "eurostat", params {"dataset": "sts_inpr_m", "nace_r2": "C2313",
    #                                 "s_adj": "CA", "unit": "I21",
    #                                 "geo": ["EU27_2020","FR","IT","ES","DE","PT"]},
    #     issuer_features ["glass_container_producer","european_industrial_volumes"],
    #     lives today in desk/vrla_volume_watch.py (VRLA.PA volume kill-bar).
    #
    # "fdic_call_report": {
    #     agency "FDIC", unit "USD thousands / percent per reported field",
    #     cadence quarterly, release_lag "~8 weeks after quarter end",
    #     adapter "fdic", params {"cert": ..., "fields": ["DEPINS","NTLNLSR","LNRECNFM"]},
    #     issuer_features ["us_bank_holding_company","deposit_franchise"],
    #     lives today in desk/bank_callreport_watch.py (WAL/FSBW kill triggers).
    #
    # "census_imports_hs842720": {
    #     agency "US Census Bureau", unit "USD (customs value) and units",
    #     cadence monthly, release_lag "~5 weeks",
    #     adapter "census_trade", params {"hs": "842720", "flow": "imports"},
    #     issuer_features ["cargo_handling_equipment","import_dependent_cogs"],
    #     lives today in the KALMAR.HE nowcast.
    #
    # "ted_tenders": {
    #     agency "EU TED", unit "count of notices and awarded EUR",
    #     cadence daily, release_lag "publication-date censored (see kalmar notes)",
    #     adapter "ted", params {"cpv": "42414*"},
    #     issuer_features ["eu_public_tender_exposure","equipment_order_intake"],
    #     lives today in the KALMAR.HE nowcast.
}


# ─────────────────────────────────────────────────────────────────────────────
# KG dispatch contract — ONE m_source, many series
# ─────────────────────────────────────────────────────────────────────────────
APPLIES_TO = {
    "sic_codes": [7011, 7993, 7990, 7999, 5812],
    "sic_prefixes": ["70", "79", "58"],
    "issuer_features": [
        "casino_gaming_revenue",
        "macau_exposure",
        "tourism_demand",
        "hotel_occupancy_metric",
        "official_series_demand_proxy",
    ],
    "asset_classes": ["public_co_consumer_services", "public_co_general",
                      "public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": ("Official-statistics MARKET LAYER: a REGISTRY of government series "
                "(one m_source, many series) that any issuer can be dispatched "
                "against. Dispatch matches issuer features/geo to registered series "
                "and injects the matched table (latest period, value, YoY, 3-obs "
                "trend) into the planner and both benches. First three rows are "
                "Macau — DICJ monthly gross gaming revenue, DSEC visitor arrivals, "
                "DSEC hotel occupancy — which price the whole Macau operator "
                "complex. New series are registry rows, not new modules; adapters "
                "are per AGENCY so a new series from a known agency is free."),
    "verification_question": ("Does the official market-wide series corroborate or "
                             "contradict the issuer's own claimed demand/volume "
                             "trajectory and the consensus embedded in the price?"),
    "confounders": [
        "market-wide != company-specific — a concession-wide GGR print is a "
        "denominator: an operator can lose share into a rising market",
        "revisions — official series are revised; the registry records revisions "
        "rather than clobbering, and a thesis resting on an unrevised first print "
        "should say so",
        "rate vs level — occupancy is a percentage (pp deltas, never summable); "
        "GGR and arrivals are levels (pct change, summable across a quarter)",
        "publication lag differs by series: GGR lands T+1 day, DSEC tourism ~T+4 "
        "weeks, so a same-quarter cross-read is not synchronous",
    ],
    "validation_status": "LIVE (3 series, all fetched from primary agency endpoints)",
}


# ─────────────────────────────────────────────────────────────────────────────
# HTTP — status-aware, so a genuine 404 is distinguishable from an outage
# ─────────────────────────────────────────────────────────────────────────────
def _get(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""            # transport failure — INFRA, never "no data"


def _post_json(url: str, payload: dict) -> tuple[int, dict | None]:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": UA, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


# ─────────────────────────────────────────────────────────────────────────────
# ADAPTERS — one per AGENCY (a new series from a known agency is a registry row)
# ─────────────────────────────────────────────────────────────────────────────
# Each adapter returns (observations, degraded_reason, source_url).
#   degraded_reason is None on success (INCLUDING a successful read that found
#   nothing — genuine empty is an observation of absence and IS cacheable).
_MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7,
           "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12}

DICJ_URL = ("https://www.dicj.gov.mo/web/en/information/DadosEstat_mensal/"
            "{year}/report_en.xml")
DSEC_VALUE_URL = ("https://www.dsec.gov.mo/TimeSeriesApi/App/IndicatorValue/"
                  "LatestSameEndPeriodv3")


def _num(s: str) -> float | None:
    s = (s or "").strip().replace(",", "").replace(" ", "")
    if not s or s in ("-", "–", "—", "n.a.", "N/A"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def dicj(spec: dict, year: int | None = None) -> tuple[list[dict], str | None, str]:
    """DICJ monthly gross gaming revenue.

    The English monthly page (.../DadosEstat_mensal/{year}/index.html) is a
    JS/XSLT frameset — it loads report_en.xml through ajaxslt, so the ACTUAL data
    document is the sibling report_en.xml, which is plain XML over plain HTTP and
    needs no browser. One fetch yields BOTH years: the report is a two-year
    comparison table (current year, prior year, variance).

    Fallback (documented, not used as primary): asgam.com / GGRAsia republish the
    DICJ table within minutes of release. They are journalism, not the agency, so
    any observation sourced there must carry source="ggrasia" — this adapter never
    silently reaches for them.
    """
    year = year or datetime.date.today().year
    url = DICJ_URL.format(year=year)
    status, text = _get(url)
    if status == 404:
        # The new year's report does not exist yet (early January) — genuine, not
        # an outage. Fall back one year; that document still carries two years.
        url = DICJ_URL.format(year=year - 1)
        status, text = _get(url)
    if status != 200 or not text.strip():
        return [], (f"DICJ report fetch failed (HTTP {status or 'transport'}) — "
                    f"outage, NOT a no-observation"), url
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return [], f"DICJ report_en.xml did not parse as XML ({type(e).__name__})", url

    # Unit drift guard — the whole series is denominated by this remark line.
    remarks = " ".join((r.text or "") for r in root.iter("REMARKS"))
    if "MOP million" not in remarks.replace("MOP  million", "MOP million"):
        return [], (f"DICJ unit remark changed (got {remarks.strip()[:80]!r}); refusing "
                    f"to append to a MOP-million series"), url

    sub = root.find(".//HEADER/SUB")
    cols = [(c.text or "").strip() for c in sub.findall("COLUMN")] if sub is not None else []
    years = [c for c in cols[:2] if c.isdigit() and len(c) == 4]
    if len(years) != 2:
        return [], (f"DICJ header shape unexpected (year columns {cols[:3]}) — "
                    f"refusing to guess column order"), url

    obs, bad = [], 0
    for rec in root.iter("RECORD"):
        cells = list(rec.findall("DATA"))
        if len(cells) < 3:
            bad += 1
            continue
        month = _MONTHS.get((cells[0].text or "").strip().lower().rstrip("."))
        if not month:
            bad += 1
            continue
        for i, y in enumerate(years):                 # cells[1] = y0, cells[2] = y1
            v = _num(cells[1 + i].text or "")
            if v is not None:
                obs.append({"period": f"{y}-{month:02d}", "value": v,
                            "unit": spec["unit"], "source": "dicj"})
    if bad or len(obs) < 6:
        # A well-formed report always carries a full prior year (12 rows). Fewer
        # than that means the document changed shape — degraded, never zeros.
        return [], (f"DICJ report parsed to {len(obs)} observations across "
                    f"{len(years)} years ({bad} unreadable rows) — wrong shape"), url
    return obs, None, url


def dsec(spec: dict) -> tuple[list[dict], str | None, str]:
    """DSEC Macau time-series database.

    The public UI (dsec.gov.mo/ts/#!/step1/en-US) is an AngularJS SPA over a REST
    API: GET /TimeSeriesApi/App/Indicatorv3[/{id}] walks the indicator tree, and
    values come from POST /TimeSeriesApi/App/IndicatorValue/LatestSameEndPeriodv3
    with {indicator_ids, language, types, dataPeriods, num} as the JSON BODY (the
    endpoint 405s on GET, and one indicator per call — a multi-id body errors).
    No key, no browser, no cookie.
    """
    iid = spec["params"]["indicator_id"]
    payload = {"indicator_ids": [str(iid)], "language": "EN-US", "types": ["VAL"],
               "dataPeriods": ["Monthly"], "num": HISTORY_MONTHS}
    url = f"{DSEC_VALUE_URL}?indicator_id={iid}"          # for provenance only
    status, d = _post_json(DSEC_VALUE_URL, payload)
    if status not in (200, 201) or not isinstance(d, dict):
        return [], (f"DSEC value POST failed (HTTP {status or 'transport'}) — "
                    f"outage, NOT a no-observation"), url
    if str(d.get("Status", "")).upper() != "OK":
        return [], (f"DSEC returned Status={d.get('Status')!r} "
                    f"({str(d.get('Debug_msg', ''))[:120]})"), url
    blocks = d.get("Value")
    if blocks is None:
        return [], "DSEC Status=OK but Value was null — wrong shape", url
    if not blocks:
        return [], None, url            # genuine empty: indicator exists, no periods
    rows = blocks[0].get("dsecIndicatorData")
    if rows is None:
        return [], "DSEC block missing dsecIndicatorData — wrong shape", url
    obs, bad = [], 0
    for r in rows:
        y, p, v = r.get("Year"), r.get("PeriodID"), r.get("IndicatorValue")
        try:
            y, p, v = int(y), int(p), float(v)
        except (TypeError, ValueError):
            bad += 1
            continue
        if not (1 <= p <= 12 and 1900 <= y <= 2100):
            bad += 1
            continue
        obs.append({"period": f"{y}-{p:02d}", "value": v, "unit": spec["unit"],
                    "source": "dsec", "source_unit": r.get("UnitLabel"),
                    "reference_period": r.get("ReferencePeriod")})
    if rows and not obs:
        return [], f"DSEC returned {len(rows)} rows, none parseable — wrong shape", url
    if bad:
        return [], f"DSEC returned {bad}/{len(rows)} unparseable rows — wrong shape", url
    return obs, None, url


ADAPTERS = {"dicj": dicj, "dsec": dsec}


# ─────────────────────────────────────────────────────────────────────────────
# Cache semantics — degraded NEVER cached, history MERGES by period
# ─────────────────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def _load(key: str) -> dict | None:
    p = _path(key)
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
    except Exception:
        return None
    return d if isinstance(d, dict) and isinstance(d.get("observations"), list) else None


def _base_record(spec: dict) -> dict:
    return {k: spec[k] for k in ("key", "name", "agency", "geo", "unit", "cadence",
                                 "release_lag", "adapter", "yoy_mode", "aggregatable",
                                 "status", "note")} | {
        "params": spec.get("params", {}), "observations": [], "asof": _now()}


def _shift(period: str, months: int) -> str:
    y, m = int(period[:4]), int(period[5:7])
    t = (y * 12 + (m - 1)) + months
    return f"{t // 12}-{t % 12 + 1:02d}"


def _expected_latest(spec: dict, today: datetime.date | None = None) -> str:
    """The most recent period the release lag says SHOULD be published by now."""
    today = today or datetime.date.today()
    return _shift(f"{today.year}-{today.month:02d}", -int(spec.get("release_lag_months", 1)))


def _is_stale(rec: dict, spec: dict, today: datetime.date | None = None) -> bool:
    """Monthly rule: a new release is plausibly out. Two triggers, one floor.

    triggers  (a) the cached latest period is behind the expected latest period, or
              (b) the cache was written in a previous calendar month
    floor     never re-poll an agency more than once per MIN_REFETCH_HOURS — the
              bench prompts call render_series on every court and agencies do not
              publish intraday.
    """
    today = today or datetime.date.today()
    asof = str(rec.get("asof") or "")
    try:
        asof_dt = datetime.datetime.fromisoformat(asof.replace("Z", ""))
    except Exception:
        return True
    if (datetime.datetime.utcnow() - asof_dt).total_seconds() < MIN_REFETCH_HOURS * 3600:
        return False
    obs = rec.get("observations") or []
    latest = obs[-1]["period"] if obs else ""
    if latest < _expected_latest(spec, today):
        return True
    return asof[:7] != f"{today.year}-{today.month:02d}"


def _merge(old: list[dict], new: list[dict]) -> list[dict]:
    """MERGE by period — the array is never overwritten wholesale.

    A changed value for an already-recorded period is a REVISION: the new value
    wins but the prior print is preserved on the row. Official statistics get
    revised, and clobbering destroys the only record that it happened.
    """
    by_period = {o["period"]: dict(o) for o in old if o.get("period")}
    stamp = _now()
    for n in new:
        p = n.get("period")
        if not p:
            continue
        prev = by_period.get(p)
        row = dict(n)
        if prev is None:
            row["fetched"] = stamp
        elif prev.get("value") != n.get("value"):
            row["fetched"] = stamp
            row["first_fetched"] = prev.get("first_fetched") or prev.get("fetched")
            row["revised_from"] = prev.get("value")
        else:
            row["fetched"] = prev.get("fetched") or stamp
            for k in ("first_fetched", "revised_from"):
                if prev.get(k) is not None:
                    row[k] = prev[k]
        by_period[p] = row
    return [by_period[p] for p in sorted(by_period)]


def fetch(key: str, refresh: bool = False) -> dict:
    """Refresh one series through its agency adapter. Degraded results are surfaced
    loud and NEVER written — a transient outage must not become a sticky record."""
    spec = SERIES.get(key)
    if spec is None:
        raise KeyError(f"unregistered series {key!r} (have: {sorted(SERIES)})")
    cached = _load(key)
    if cached and not refresh and not _is_stale(cached, spec):
        return cached
    adapter = ADAPTERS.get(spec["adapter"])
    if adapter is None:
        rec = (cached or _base_record(spec)) | {
            "degraded": f"no adapter named {spec['adapter']!r}",
            "note": f"DEGRADED — no adapter {spec['adapter']!r}; not cached"}
        return rec
    try:
        obs, degraded, url = adapter(spec)
    except Exception as e:                       # any adapter blow-up is INFRA
        obs, degraded, url = [], f"{spec['adapter']} adapter raised {type(e).__name__}: {str(e)[:90]}", ""
    if degraded:
        rec = dict(cached or _base_record(spec))
        rec["degraded"] = degraded
        rec["degraded_at"] = _now()
        rec["source_url"] = url or rec.get("source_url")
        rec["note"] = (f"DEGRADED — {degraded}; not cached, will retry "
                       f"({len(rec.get('observations') or [])} previously-cached observations "
                       f"shown unchanged)")
        return rec                                # NOT written
    rec = _base_record(spec)
    rec["observations"] = _merge((cached or {}).get("observations") or [], obs)
    rec["source_url"] = url
    rec["asof"] = _now()
    n_new = len(rec["observations"]) - len((cached or {}).get("observations") or [])
    revised = [o["period"] for o in rec["observations"] if o.get("revised_from") is not None]
    rec["note"] = (f"{len(rec['observations'])} observations "
                   f"({'no periods published yet' if not rec['observations'] else 'latest ' + rec['observations'][-1]['period']}), "
                   f"+{n_new} new this fetch"
                   + (f", {len(revised)} revised period(s)" if revised else ""))
    _path(key).write_text(json.dumps(rec, indent=1))
    return rec


# ─────────────────────────────────────────────────────────────────────────────
# OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────
def backfill(key: str, years: int = 2) -> dict:
    """Deepen history for an adapter that is year-addressable (DICJ publishes one
    two-year report per year). NOT needed for YoY: the DICJ report is SELF-MATCHING
    — it carries exactly the prior-year months that are published in the current
    year, so yoy() and matched-month quarter nowcasts always resolve off one fetch.
    Backfill buys depth for trend/seasonality work. Degraded years are skipped
    loudly and nothing is written unless at least one year parsed."""
    spec = SERIES.get(key)
    if spec is None:
        raise KeyError(f"unregistered series {key!r}")
    adapter = ADAPTERS.get(spec["adapter"])
    if adapter is not dicj:
        return {"key": key, "skipped": f"adapter {spec['adapter']!r} is not year-addressable"}
    got, errs = [], []
    this_year = datetime.date.today().year
    for y in range(this_year - years, this_year + 1):
        obs, degraded, _ = adapter(spec, year=y)
        (errs.append(f"{y}: {degraded}") if degraded else got.extend(obs))
    if not got:
        return {"key": key, "degraded": "; ".join(errs) or "no years parsed", "written": False}
    rec = _load(key) or _base_record(spec)
    rec["observations"] = _merge(rec.get("observations") or [], got)
    rec["asof"] = _now()
    rec["note"] = f"backfilled {years}y: {len(rec['observations'])} observations" + \
                  (f"; skipped {errs}" if errs else "")
    _path(key).write_text(json.dumps(rec, indent=1))
    return {"key": key, "n_obs": len(rec["observations"]), "errors": errs, "written": True}


def history(key: str, refresh: bool = False) -> list[dict]:
    return fetch(key, refresh=refresh).get("observations") or []


def latest(key: str, refresh: bool = False) -> dict | None:
    obs = history(key, refresh=refresh)
    return obs[-1] if obs else None


def yoy(key: str, period: str | None = None, refresh: bool = False) -> dict | None:
    """Year-over-year for one period. Percentage POINTS for rate series (yoy_mode
    'pp_delta'), percent change for levels — the metric is always named."""
    spec = SERIES.get(key)
    if spec is None:
        raise KeyError(f"unregistered series {key!r}")
    obs = {o["period"]: o for o in history(key, refresh=refresh)}
    if not obs:
        return None
    period = period or sorted(obs)[-1]
    cur, prior_p = obs.get(period), _shift(period, -12)
    prior = obs.get(prior_p)
    out = {"key": key, "period": period, "prior_period": prior_p,
           "value": cur["value"] if cur else None,
           "prior_value": prior["value"] if prior else None,
           "unit": spec["unit"], "mode": spec["yoy_mode"], "yoy": None, "label": ""}
    if cur is None or prior is None:
        out["note"] = ("no observation for " + (period if cur is None else prior_p)
                       + " — YoY UNAVAILABLE, not zero")
        return out
    if spec["yoy_mode"] == "pp_delta":
        out["yoy"] = round(cur["value"] - prior["value"], 2)
        out["label"] = f"{out['yoy']:+.1f}pp"
    else:
        if not prior["value"]:
            out["note"] = "prior-year value is zero — YoY undefined"
            return out
        out["yoy"] = round((cur["value"] / prior["value"] - 1) * 100, 2)
        out["label"] = f"{out['yoy']:+.1f}%"
    return out


def nowcast_quarter(key: str, quarter_months: list[str],
                    base_year_values: dict[str, float] | None = None,
                    refresh: bool = False) -> dict:
    """Partial-quarter implied YoY on a MATCHED-MONTH basis.

    e.g. Apr+May+Jun 2026 vs Apr+May+Jun 2025. A month missing on EITHER side is
    dropped from BOTH sums and the result is flagged partial — the quarter is
    never annualized, extrapolated or silently completed. base_year_values lets a
    caller supply prior-year months the cached history does not reach back to,
    keyed by either the prior-year period or the current-year period.
    """
    spec = SERIES.get(key)
    if spec is None:
        raise KeyError(f"unregistered series {key!r}")
    out = {"key": key, "unit": spec["unit"], "quarter_months": list(quarter_months),
           "basis": "matched months only — NOT annualized, NOT extrapolated"}
    if not spec.get("aggregatable", True):
        out |= {"implied_yoy": None, "partial": None,
                "note": (f"{key} is a rate ({spec['unit']}) — summing it across a "
                         f"quarter is not meaningful; nowcast_quarter REFUSES. Use "
                         f"yoy() per month (percentage points).")}
        return out
    obs = {o["period"]: o["value"] for o in history(key, refresh=refresh)}
    base = dict(base_year_values or {})
    matched, missing_cur, missing_prior = [], [], []
    cur_sum = prior_sum = 0.0
    for m in quarter_months:
        pm = _shift(m, -12)
        cv = obs.get(m)
        pv = obs.get(pm, base.get(pm, base.get(m)))
        if cv is None:
            missing_cur.append(m)
            continue
        if pv is None:
            missing_prior.append(pm)
            continue
        matched.append(m)
        cur_sum += cv
        prior_sum += pv
    out |= {"matched_months": matched,
            "missing_current_months": missing_cur,
            "missing_prior_year_months": missing_prior,
            "coverage": f"{len(matched)}/{len(quarter_months)}",
            "partial": len(matched) < len(quarter_months),
            "current_sum": round(cur_sum, 4) if matched else None,
            "prior_sum": round(prior_sum, 4) if matched else None,
            "implied_yoy": None}
    if not matched:
        out["note"] = ("no month has BOTH a current and a prior-year observation — "
                       "quarter nowcast UNAVAILABLE, not zero")
        return out
    if not prior_sum:
        out["note"] = "prior-year matched sum is zero — implied YoY undefined"
        return out
    out["implied_yoy"] = round((cur_sum / prior_sum - 1) * 100, 2)
    out["label"] = f"{out['implied_yoy']:+.1f}%"
    out["note"] = (f"{len(matched)}/{len(quarter_months)} months matched"
                   + (f"; PARTIAL COVERAGE — missing current {missing_cur or '[]'}, "
                      f"missing prior-year {missing_prior or '[]'}; the quarter is "
                      f"NOT complete and was NOT annualized" if out["partial"] else
                      "; full quarter"))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# DISPATCH + bench rendering
# ─────────────────────────────────────────────────────────────────────────────
def series_for(features_or_ticker) -> list[str]:
    """Registered series keys matching an issuer.

    Accepts a ticker, a free-text case blob, or an iterable of issuer features.
    GEO GUARD: SIC alone never fires a geo-specific series — prefixes 70/79/58
    would hand Macau GGR to Marriott and Chipotle. A row fires on an explicit
    ticker, an explicit declared issuer feature, or a geo/topic token in the text.
    """
    if isinstance(features_or_ticker, str):
        blob = features_or_ticker.lower()
        feats = set()
        # a bare ticker OR a case blob whose first token is the ticker (how
        # detector_preflight calls this: "MLCO\n<case context>")
        words = features_or_ticker.strip().split()
        ticks = {features_or_ticker.strip().upper()}
        if words:
            ticks.add(words[0].strip(",.;:—-").upper())
    else:
        feats = {str(f).lower() for f in (features_or_ticker or [])}
        blob = " ".join(feats)
        ticks = set()
    out = []
    for key, spec in SERIES.items():
        if ticks & {t.upper() for t in spec.get("tickers", [])}:
            out.append(key)
            continue
        if feats & {f.lower() for f in spec.get("issuer_features", [])}:
            out.append(key)
            continue
        if any(tok in blob for tok in spec.get("match_tokens", [])):
            out.append(key)
    return out


def _fmt(v: float) -> str:
    return f"{v:,.1f}".rstrip("0").rstrip(".")


def _arrows(obs: list[dict]) -> str:
    last = obs[-3:]
    if len(last) < 2:
        return ""
    marks = []
    for a, b in zip(last, last[1:]):
        marks.append("↑" if b["value"] > a["value"] else ("↓" if b["value"] < a["value"] else "→"))
    return "".join(marks)


def render_series(features_or_ticker) -> str:
    """Compact market-layer table for the planner + bench prompts.

    Empty string when no registered series matches this issuer (mirrors
    render_facilities: the caller supplies the honest empty fallback)."""
    keys = series_for(features_or_ticker)
    if not keys:
        return ""
    lines = []
    for key in keys:
        spec = SERIES[key]
        try:
            rec = fetch(key)
        except Exception as e:
            lines.append(f"- {key} ({spec['agency'].split('(')[0].strip()}): "
                         f"FETCH FAILED ({type(e).__name__}) — treat as UNCHECKED, not clean")
            continue
        obs = rec.get("observations") or []
        deg = rec.get("degraded")
        if not obs:
            lines.append(f"- {key} [{spec['unit']}]: NO OBSERVATIONS"
                         + (f" — DEGRADED: {deg}" if deg else " (agency published none)"))
            continue
        last = obs[-1]
        y = yoy(key, last["period"])
        lbl = (y or {}).get("label")
        yl = f"{lbl} YoY" if lbl else "YoY UNAVAILABLE (no prior-year month), not zero"
        tail = ", ".join(f"{o['period']} {_fmt(o['value'])}" for o in obs[-3:])
        lines.append(f"- {key} [{spec['agency'].split('(')[0].strip()}, {spec['cadence']}, "
                     f"{spec['unit']}]: {last['period']} = {_fmt(last['value'])} "
                     f"({yl}) {_arrows(obs)}  last 3: {tail}"
                     + (f"  [DEGRADED: {deg} — values shown are the last good cache]" if deg else ""))
    return ("MARKET LAYER — registered official statistics matched to this issuer "
            "(desk/official_series.py; agency-primary, market-WIDE not company-specific "
            "— a concession-wide print is a denominator, an operator can lose share into "
            "a rising market):\n" + "\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
# WATCH — refresh everything, flag NEW observations
# ─────────────────────────────────────────────────────────────────────────────
def refresh_all(force: bool = False) -> dict:
    """The weekly watch: refresh every registered series and FLAG new periods.
    A new month printing is the event; degraded fetches are flagged too (a silent
    dead feed is the failure mode this desk keeps re-learning)."""
    flags, errors, rows = [], [], []
    for key, spec in SERIES.items():
        before = (_load(key) or {}).get("observations") or []
        seen = {o["period"] for o in before}
        try:
            rec = fetch(key, refresh=force)
        except Exception as e:
            errors.append(f"{key}: fetch raised {type(e).__name__}: {str(e)[:90]}")
            continue
        if rec.get("degraded"):
            errors.append(f"{key}: DEGRADED — {rec['degraded']}")
        obs = rec.get("observations") or []
        new = [o for o in obs if o["period"] not in seen]
        revised = [o for o in obs if o.get("revised_from") is not None
                   and o.get("fetched", "")[:10] == datetime.date.today().isoformat()]
        for o in new:
            y = yoy(key, o["period"])
            flags.append(f"FLAG NEW OBSERVATION — {key} ({spec['agency'].split('(')[0].strip()}): "
                         f"{o['period']} = {o['value']:,.1f} {spec['unit']} "
                         f"(YoY {(y or {}).get('label') or 'n/a'})")
        for o in revised:
            flags.append(f"FLAG REVISION — {key}: {o['period']} "
                         f"{o['revised_from']:,.1f} -> {o['value']:,.1f} {spec['unit']}")
        rows.append({"key": key, "n_obs": len(obs),
                     "latest": obs[-1]["period"] if obs else None,
                     "new": len(new), "degraded": rec.get("degraded")})
    return {"asof": _now(), "series": rows, "flags": flags, "errors": errors}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def _quarter_months(q: str) -> list[str]:
    y, n = int(q[:4]), int(q[-1])
    if not 1 <= n <= 4:
        raise ValueError(f"bad quarter {q!r} (use e.g. 2026Q3)")
    return [f"{y}-{m:02d}" for m in range(3 * n - 2, 3 * n + 1)]


def main(argv=None):
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "list"

    if cmd == "list":
        print(f"{len(SERIES)} registered series\n")
        for key, s in SERIES.items():
            rec = _load(key)
            obs = (rec or {}).get("observations") or []
            print(f"{key:26s} {s['status']:9s} {s['cadence']:9s} {s['unit']}")
            print(f"{'':26s} {s['agency']}")
            print(f"{'':26s} lag: {s['release_lag']}")
            print(f"{'':26s} cached: {len(obs)} obs"
                  + (f", latest {obs[-1]['period']} = {obs[-1]['value']:,.1f}" if obs else "")
                  + f", serves {', '.join(s['issuer_features'])}\n")
        return 0

    if cmd == "refresh":
        out = refresh_all(force="--force" in argv)
        for r in out["series"]:
            print(f"{r['key']:26s} {r['n_obs']:4d} obs  latest {r['latest']}  "
                  f"+{r['new']} new" + (f"  DEGRADED: {r['degraded']}" if r["degraded"] else ""))
        for f in out["flags"]:
            print(f)
        for e in out["errors"]:
            print(f"ERROR {e}")
        return 1 if out["errors"] else 0

    if cmd == "backfill":
        if len(argv) < 2:
            print("usage: backfill KEY [--years N]")
            return 2
        n = int(argv[argv.index("--years") + 1]) if "--years" in argv else 2
        print(json.dumps(backfill(argv[1], years=n), indent=1))
        return 0

    if cmd == "fetch":
        if len(argv) < 2:
            print("usage: fetch KEY [--refresh]")
            return 2
        rec = fetch(argv[1], refresh="--refresh" in argv)
        print(json.dumps(rec, indent=1))
        return 1 if rec.get("degraded") else 0

    if cmd == "nowcast":
        if len(argv) < 2:
            print("usage: nowcast KEY [--quarter 2026Q3]")
            return 2
        key = argv[1]
        if "--quarter" in argv:
            months = _quarter_months(argv[argv.index("--quarter") + 1])
        else:
            last = latest(key)
            if not last:
                print(f"{key}: no observations — nothing to nowcast")
                return 1
            m = int(last["period"][5:7])
            months = _quarter_months(f"{last['period'][:4]}Q{(m - 1) // 3 + 1}")
        print(json.dumps(nowcast_quarter(key, months), indent=1))
        return 0

    print(__doc__.strip().split("\n\n")[-1])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
