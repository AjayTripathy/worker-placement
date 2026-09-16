"""weekly_dashboard — the weekly-frequency official-series roster (thesis menu 2026-08-31).

The disclosure-planes doctrine, applied at WEEKLY cadence: monthly government data (import
nowcast) leads prints by ~5 weeks; weekly official series lead by more. This is the roster of
weekly series with a NATIVE issuer mapping — the desk watches the series, not the narrative.

Each roster entry: a public weekly series (keyless fetch), a ticker cohort whose P&L the series
leads, and a direction (+1: series up = cohort bullish). Weekly run computes the 4-week trend
against the trailing-13-week baseline and a YoY read where the series supports it; |z| >= Z_FIRE
or a trend sign-flip emits a dashboard line, mails the delta, and (--enqueue) routes the single
most-exposed cohort name to the conveyor as a screen-sourced candidate (TRAP_VERIFY — the
generator never grades itself; courts grade the mapping, exactly as import_nowcast).

UNWIRED entries are registered on purpose (no keyless fetch exists yet): the roster IS the map
of what the desk should be watching; silence about a gap reads as coverage (no-silent-caps).

    python3 -m desk.weekly_dashboard [--enqueue] [--dry]
READ-ONLY except state file + optional enqueue.
"""
from __future__ import annotations

import datetime
import json
import re
import statistics
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "weekly_dashboard.json"
UA = {"User-Agent": "SignalOS Research <4tripathy@gmail.com>"}
Z_FIRE = 2.0


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "ignore")


def fred_weekly(series_id: str) -> dict[str, float]:
    """Daily FRED series -> weekly (Friday-anchored last value) so read_series' 4-vs-13 WEEK z
    keeps its meaning. Added 2026-09-12 for the credit-spread (OAS) legs of the AI-break tripwires."""
    import datetime as _dt
    daily = fred_csv(series_id)
    weekly: dict[str, float] = {}
    for d, v in sorted(daily.items()):
        day = _dt.date.fromisoformat(d)
        friday = day + _dt.timedelta(days=(4 - day.weekday()) % 7)
        weekly[friday.isoformat()] = v          # last observation in the week wins
    return weekly


def fred_csv(series_id: str) -> dict[str, float]:
    """FRED's fredgraph.csv endpoint is keyless. Returns {iso_date: value}."""
    txt = _fetch(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}")
    out = {}
    for line in txt.splitlines()[1:]:
        try:
            d, v = line.split(",")
            out[d] = float(v)
        except ValueError:
            continue
    return out


def tsa_throughput() -> dict[str, float]:
    """TSA checkpoint volumes — HTML table, current + prior years by day; aggregate to weeks
    ending Saturday so partial weeks never fake a downtick."""
    html = _fetch("https://www.tsa.gov/travel/passenger-volumes")
    days = {}
    for m in re.finditer(r"<td[^>]*>(\d{1,2}/\d{1,2}/\d{4})</td>((?:\s*<td[^>]*>[\d,]*</td>)+)", html):
        d = datetime.datetime.strptime(m.group(1), "%m/%d/%Y").date()
        cols = re.findall(r"<td[^>]*>([\d,]*)</td>", m.group(2))
        if cols and cols[0]:
            days[d] = float(cols[0].replace(",", ""))
        # prior-year column shares the row: same month/day, previous year
        if len(cols) > 1 and cols[1]:
            try:
                days[d.replace(year=d.year - 1)] = float(cols[1].replace(",", ""))
            except ValueError:
                pass
    weeks: dict[str, list] = {}
    for d, v in days.items():
        sat = d + datetime.timedelta(days=(5 - d.weekday()) % 7)
        weeks.setdefault(sat.isoformat(), []).append(v)
    return {k: sum(v) for k, v in sorted(weeks.items()) if len(v) == 7}


ROSTER = [
    dict(key="jobless_claims", label="Initial jobless claims (ICSA, SA)",
         fetch=lambda: fred_csv("ICSA"), direction=-1,
         cohort=["RHI", "KFRC", "OMF", "WAL"],
         note="claims UP = staffing/consumer-credit stress; leads charge-off talk by a quarter"),
    dict(key="continued_claims", label="Continued claims (CCSA, SA)",
         fetch=lambda: fred_csv("CCSA"), direction=-1,
         cohort=["RHI", "OMF"],
         note="stock of unemployment; slope matters more than level for credit books"),
    dict(key="tsa", label="TSA checkpoint throughput (weekly sum)",
         fetch=tsa_throughput, direction=+1,
         cohort=["DAL", "UAL", "ALK", "WYNN"],
         note="domestic air demand; WYNN secondary (Vegas leg only - Macau is DICJ plane)"),
    dict(key="gas_price", label="Retail regular gasoline price (GASREGW, weekly)",
         fetch=lambda: fred_csv("GASREGW"), direction=-1,
         cohort=["ARKO", "BKE", "CASY"],
         note="price proxy, not volume (EIA product-supplied needs a key): price spike = traffic "
              "headwind + lagged fuel-margin squeeze for c-stores (ARKO courted)"),
    dict(key="us30y_yield", label="30-year Treasury yield (WGS30YR, weekly avg)",
         fetch=lambda: fred_csv("WGS30YR"), direction=-1,
         cohort=["BOOK-WIDE"],
         note="long-end rout = rate-spike stress arriving (added 2026-09-01 during the global "
              "bond selloff): derates duration-heavy equity, tightens every FV band "
              "(bond-dominance floor), binds the AI refi wall harder; z-fire = re-run the "
              "rotation stress + check the hedge re-freeze gates"),
    # CREDIT-SPREAD LEGS of the AI-break tripwires (2026-09-12, principal: "add CDS to the AI bubble
    # tripwires"). Single-name CDS spreads are not free; these are the BROAD legs (ICE BofA OAS via
    # FRED, weekly-anchored). Widening = BEARISH for the AI complex's refi wall. They CANNOT convict
    # the AI complex alone (ai_credit_basis rule) — the AI-specific legs are desk.cds_activity_watch
    # (DTCC single-name activity: ORCL market depth, CoreWeave listing = canary) + Merton DD.
    dict(key="ig_oas", label="IG corporate OAS (BAMLC0A0CM, bp, weekly)",
         fetch=lambda: fred_weekly("BAMLC0A0CM"), direction=-1,
         cohort=["AI-BREAK"], note="broad IG spread; z-fire = refi-wall stress for the hyperscaler/ORCL issuers"),
    dict(key="bbb_oas", label="BBB corporate OAS (BAMLC0A4CBBB, bp, weekly)",
         fetch=lambda: fred_weekly("BAMLC0A4CBBB"), direction=-1,
         cohort=["AI-BREAK"], note="the ORCL/AMZN-adjacent rating bucket; widening here before IG = the 2007 basis signature"),
    dict(key="hy_oas", label="HY OAS (BAMLH0A0HYM2, bp, weekly)",
         fetch=lambda: fred_weekly("BAMLH0A0HYM2"), direction=-1,
         cohort=["AI-BREAK"], note="neocloud/GPU-landlord funding bucket (CRWV-class paper)"),
    dict(key="ccc_oas", label="CCC & lower OAS (BAMLH0A3HYC, bp, weekly)",
         fetch=lambda: fred_weekly("BAMLH0A3HYC"), direction=-1,
         cohort=["AI-BREAK"], note="the tail that widened first in Sept-2026 (+38bp while HY sat at tights)"),
    dict(key="us10y_yield", label="10-year Treasury yield (WGS10YR, weekly avg)",
         fetch=lambda: fred_csv("WGS10YR"), direction=-1,
         cohort=["BOOK-WIDE"],
         note="companion to 30y: 10y drives FV discount rates; divergence (30y up, 10y flat) "
              "= term-premium/inflation story, not growth"),
    # ---- UNWIRED (no keyless weekly fetch yet; registered so the gap is visible) ----
    dict(key="rail_carloads", label="AAR weekly rail carloads", fetch=None, direction=+1,
         cohort=["UNP", "CSX"], note="UNWIRED: AAR press page is unstructured; STB quarterly only"),
    dict(key="rig_count", label="Baker Hughes NA rig count", fetch=None, direction=+1,
         cohort=["LBRT", "HAL", "ACDC"], note="UNWIRED: BH site is JS-rendered; LBRT/ACDC courted names"),
    dict(key="redbook", label="Redbook same-store retail", fetch=None, direction=+1,
         cohort=["BKE", "ONON"], note="UNWIRED: paywalled"),
    dict(key="mba_apps", label="MBA mortgage applications", fetch=None, direction=+1,
         cohort=["VEL", "WAL"], note="UNWIRED: press-release only; VEL court-on-touch gate would use it"),
]


def read_series(hist: dict[str, float]) -> dict:
    """4-week mean vs trailing 13-week baseline (z), plus YoY on the latest week."""
    keys = sorted(hist)
    if len(keys) < 18:
        return {}
    vals = [hist[k] for k in keys]
    recent, base = vals[-4:], vals[-17:-4]
    mu, sd = statistics.mean(base), statistics.pstdev(base) or 1.0
    z = (statistics.mean(recent) - mu) / sd
    latest_d, latest_v = keys[-1], vals[-1]
    yoy = None
    target = datetime.date.fromisoformat(latest_d) - datetime.timedelta(days=364)
    near = min(keys[:-1], key=lambda k: abs((datetime.date.fromisoformat(k) - target).days))
    if abs((datetime.date.fromisoformat(near) - target).days) <= 7:
        yoy = (latest_v / hist[near] - 1) * 100
    return dict(latest=latest_d, value=latest_v, z4v13=round(z, 2),
                yoy_pct=round(yoy, 2) if yoy is not None else None,
                trend_sign=1 if statistics.mean(recent) >= mu else -1)


def run(enqueue: bool = False, dry: bool = False) -> int:
    prev = json.loads(STATE.read_text()) if STATE.exists() else {}
    board, fired, gaps = {}, [], []
    for row in ROSTER:
        if row["fetch"] is None:
            gaps.append(f"{row['key']}: {row['note']}")
            board[row["key"]] = dict(label=row["label"], status="UNWIRED", note=row["note"])
            continue
        try:
            hist = row["fetch"]()
        except Exception as e:
            board[row["key"]] = dict(label=row["label"], status=f"FETCH-ERROR {type(e).__name__}")
            continue
        r = read_series(hist)
        if not r:
            board[row["key"]] = dict(label=row["label"], status="INSUFFICIENT-HISTORY")
            continue
        prior = prev.get("board", {}).get(row["key"], {})
        flipped = prior.get("trend_sign") and prior["trend_sign"] != r["trend_sign"]
        hot = abs(r["z4v13"]) >= Z_FIRE
        r.update(label=row["label"], status="OK", cohort=row["cohort"],
                 direction=row["direction"], note=row["note"],
                 fired=bool(hot or flipped))
        board[row["key"]] = r
        if r["fired"]:
            tilt = "BULLISH" if r["z4v13"] * row["direction"] > 0 else "BEARISH"
            fired.append(f"{row['key']} {tilt} for {','.join(row['cohort'])}: z={r['z4v13']}"
                         f" yoy={r['yoy_pct']}% ({'sign-flip' if flipped else 'z-fire'}) — {row['note']}")
    out = dict(asof=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               board=board, fired=fired, unwired=gaps)
    if not dry:
        STATE.write_text(json.dumps(out, indent=1))
    for line in fired or ["clean — no series fired"]:
        print("[weekly_dashboard]", line)
    print(f"[weekly_dashboard] {len(gaps)} roster entries UNWIRED (visible by design)")
    if fired and not dry:
        try:
            from desk.mailer import send_raw
            send_raw(f"WEEKLY DASHBOARD: {len(fired)} series fired", "\n\n".join(fired))
        except Exception as e:
            print(f"[weekly_dashboard] mail failed: {e}")
    if fired and enqueue and not dry:
        from desk.court_queue import enqueue_candidates
        rows = []
        for key, r in board.items():
            if r.get("fired"):
                rows.append(dict(ticker=r["cohort"][0], series=key, z4v13=r["z4v13"],
                                 yoy_pct=r["yoy_pct"],
                                 context=f"weekly-series divergence: {r['label']} z={r['z4v13']} "
                                         f"yoy={r['yoy_pct']}% — cause-check the mapping first "
                                         f"({r['note']}); cohort {r['cohort']}"))
        c = enqueue_candidates(rows, source=f"weekly_dashboard/{datetime.date.today()}",
                               allow_ledger=True)
        print(f"[weekly_dashboard] enqueued {c['added']}")
    return 0


if __name__ == "__main__":
    import sys
    run(enqueue="--enqueue" in sys.argv, dry="--dry" in sys.argv)
