"""lab_scheduler_panel — appointment-availability sampler for DGX (Quest Diagnostics) and LH (Labcorp).

WHAT IT MEASURES
  Weekly, for a FIXED panel of 12 metros x 2 companies (desk/data/lab_panel/panel.json), the public
  online scheduler is asked: "what is the NEXT AVAILABLE routine blood-draw appointment near this
  busy zip?"  Per-location days-to-next-slot, and per-company median / %same-day / %within-48h
  (plus Quest's published walk-in wait minutes), are appended to desk/data/lab_panel/history.jsonl.
  Slot scarcity at draw sites is public operational exhaust: requisition volume is THE print metric
  for DGX/LH, and utilization pressure at the draw-site network plausibly LEADS reported volume by
  up to a quarter.

STATUS: PAPER until validated.  v1 collects Q3-2026 history and gets graded against the October
  prints (desk standard gate for a new channel: no sizing until it beats consensus on a print).

KNOWN CONFOUNDERS (why this is a proxy, not a measurement)
  * Capacity, not demand: a company ADDING phlebotomists/sites shortens waits while volume RISES;
    a company cutting staff lengthens waits while volume falls.  Wait-time deltas are demand
    signals only conditional on roughly-stable capacity.  v2 disambiguator: cross-check against
    the hiring_velocity detector (job-posting waves at draw sites = capacity change in flight).
  * Scheduling-policy changes (slot-grid density, walk-in mix, new booking UI) move the metric
    with zero volume change; a discontinuous panel-wide jump on ONE company is more likely a
    policy/site-mix artifact than demand — check before believing it.
  * 12 busy urban zips are not the network: suburban/in-office-draw mix shifts are invisible here.
  * Same-day slots get consumed intraday, so the sampled hour matters: keep the weekly cron at a
    consistent hour so week-over-week deltas are like-for-like.
  * days_to_next_slot is right-censored at LOOKAHEAD_DAYS: a no_slots row means "worse than the
    window", is excluded from the median (never imputed), and is visible as n_no_slots.
  * Structural gaps are labeled no_coverage, not scarcity: Quest-PHX is Sonora Quest (a 49%-owned
    JV, NOT consolidated in DGX volumes) which books on its own site; stale duplicate PSC records
    with permanently-empty grids are skipped, not read as booked-out (see _quest_read_sites).

SAMPLING ETHICS / RATE LIMITS
  Weekly cadence; 2 page landings + ~40 lightweight in-page API calls per run (~24 location-
  queries), 2-4s pacing.  PUBLIC booking surfaces only: no login, no auth bypass, no PII entered,
  nothing booked or held — both flows are read-only availability views any patient sees before
  identifying themselves.  A blocked scheduler records status=blocked (DATA MISSING) — never zero.
  If a company blocks headless access entirely, --manual mode ingests a hand-collected CSV so the
  instrument degrades to usable instead of dying.

MECHANICS (validated live 2026-07-23; the desk's standing browser lessons apply)
  Playwright + real Chrome + realistic fingerprint; LAND on the page first for cookies, then reuse
  the app's own credentials for in-page requests (these enterprise sites check Sec-Ch-Ua /
  Sec-Fetch-* / cookie state, not just User-Agent).
  * quest: appointment.questdiagnostics.com/find-location (anonymous — the separate scheduling
    flow wants PII first, which we refuse).  One UI walk (reason="All Other Tests" = PHLEBOTOMY
    facilityServiceId 1, then a zip search) makes the app call guest/getPscsWithAvailability;
    we capture its X-CSRF-TOKEN request header (Spring CSRF; the cookie is HttpOnly so the
    header is sniffed, not read), then replay the same POST in-page per metro with
    sendSlots=true over a LOOKAHEAD_DAYS window.  Response: nearest PSCs each with
    availability=[{date, slots:[{time, available}]}] + walk-in waitTime minutes.
    Cloudflare fronts this origin and its managed challenge fires intermittently — waited out
    up to 40s; an uncleared challenge records the whole company as blocked for the run.
  * labcorp: patient.labcorp.com/appointments (anonymous).  Navigate once to the parameterized
    results URL; the Angular app calls locations/fal/search + findAvailableAppointments on
    admin.api/appointment-services.api.express-prod.cws.labcorp.com with a session Authorization
    JWT, which we capture and reuse for in-page GETs per metro: fal/search (nearest sites w/
    canCreateAppointment) then findAvailableAppointments(serviceId=5 "Labwork",
    noOfDays=LOOKAHEAD_DAYS).  On 401 (token expiry) the results page is re-navigated once to
    re-arm.

CLI
  python3 -m desk.lab_scheduler_panel                # live weekly sample (default)
  python3 -m desk.lab_scheduler_panel --manual f.csv # ingest a hand-collected CSV instead
  python3 -m desk.lab_scheduler_panel --limit 2      # first N metros only (debug)
  python3 -m desk.lab_scheduler_panel --show         # headed browser (debug)
  Manual CSV columns: company,metro,zip,next_slot_iso,status[,site]
    status ok               -> next_slot_iso = "2026-07-25T07:45:00" or "2026-07-25"
    status blocked/no_slots -> next_slot_iso empty
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "lab_panel"
PANEL = DATA / "panel.json"
HISTORY = DATA / "history.jsonl"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

LOOKAHEAD_DAYS = 14          # slot window; beyond this a location is right-censored as no_slots
PACE_S = 3.0                 # seconds between location-queries (realistic, deterministic)

QUEST_FINDER = "https://appointment.questdiagnostics.com/find-location"
QUEST_AVAIL = "https://appointment.questdiagnostics.com/guest/getPscsWithAvailability"
QUEST_SERVICE_ID = 1         # PHLEBOTOMY / "All Other Tests" (routine draw) per guest/getReasons/MAIN

LABCORP_LANDING = "https://patient.labcorp.com/appointments/"
LABCORP_RESULTS = ("https://patient.labcorp.com/appointments/results"
                   "?address_single={zip}&zip={zip}&lat={lat}&lon={lon}&service=5")
LABCORP_SEARCH = ("https://admin.api.express-prod.cws.labcorp.com/locations/fal/search"
                  "?client=LC&searchType=patient&radius=25&serviceType=5&date={date}"
                  "&lat={lat}&long={lon}&pageSize=10")
LABCORP_AVAIL = ("https://appointment-services.api.express-prod.alp01h.cws.labcorp.com/appointments/"
                 "findAvailableAppointments?onsiteClient=false&x-client-type=patient"
                 "&locationId={loc}&serviceId=5&appointmentStartDate={date}&noOfDays={days}")

_FETCH_GET = """async ([u, hdrs]) => {
  const r = await fetch(u, {headers: hdrs});
  return {status: r.status, body: await r.text()};
}"""
_FETCH_POST = """async ([u, hdrs, payload]) => {
  const r = await fetch(u, {method: 'POST', headers: hdrs, body: JSON.stringify(payload)});
  return {status: r.status, body: await r.text()};
}"""


# ----------------------------------------------------------------------------- panel + metrics ---

def load_panel(path: Path = PANEL) -> list[dict]:
    """Expand panel.json into the flat location list: one entry per (metro x company)."""
    cfg = json.loads(Path(path).read_text())
    out = []
    for company in cfg["companies"]:
        for m in cfg["metros"]:
            out.append({"company": company, "metro": m["metro"], "zip": m["zip"],
                        "lat": m["lat"], "lon": m["lon"], "label": m.get("label", "")})
    return out


def days_to_slot(next_slot_iso: str, asof: dt.datetime) -> float:
    """Calendar-day difference asof -> slot (0.0 = same-day).  Calendar semantics on purpose:
    slot times are site-local, asof is desk-local; date math is timezone-robust and the panel is
    sampled weekly, so sub-day resolution would be false precision."""
    slot_date = dt.date.fromisoformat(next_slot_iso.strip()[:10])
    return float((slot_date - asof.date()).days)


def aggregate(rows: list[dict], asof: dt.datetime | None = None) -> dict:
    """Per-company metrics over location rows.

    Contract (tested): medians/percentages are computed over status=='ok' rows ONLY.  blocked /
    no_slots / no_coverage / error rows are tallied but NEVER imputed as zero availability — a
    blocked location is missing data, a no_slots location is right-censored, and a no_coverage
    location (e.g. Quest-PHX = the non-consolidated Sonora Quest JV) is structurally absent.
    Walk-in waits aggregate only from ok/no_slots rows (in-network live sites).
    """
    out = {}
    for company in sorted({r["company"] for r in rows}):
        sub = [r for r in rows if r["company"] == company]
        ok = [r for r in sub if r.get("status") == "ok" and r.get("days_to_next_slot") is not None]
        days = [float(r["days_to_next_slot"]) for r in ok]
        waits = [r["walkin_wait_min"] for r in sub
                 if isinstance(r.get("walkin_wait_min"), (int, float))
                 and r.get("status") in ("ok", "no_slots")]
        a = {
            "n_ok": len(ok),
            "n_blocked": sum(1 for r in sub if r.get("status") == "blocked"),
            "n_no_slots": sum(1 for r in sub if r.get("status") == "no_slots"),
            "n_no_coverage": sum(1 for r in sub if r.get("status") == "no_coverage"),
            "n_error": sum(1 for r in sub if r.get("status") not in
                           ("ok", "blocked", "no_slots", "no_coverage")),
            "median_days_to_next_slot": round(statistics.median(days), 3) if days else None,
            "pct_same_day": round(100.0 * sum(1 for d in days if d < 1.0) / len(days), 1) if days else None,
            "pct_within_48h": round(100.0 * sum(1 for d in days if d <= 2.0) / len(days), 1) if days else None,
        }
        if waits:
            a["median_walkin_wait_min"] = round(statistics.median(waits), 1)
        out[company] = a
    return out


def append_history(record: dict, path: Path | None = None) -> None:
    """Newline-safe JSONL append: exactly one parseable JSON object per line, even if a previous
    writer left the file without a trailing newline.  path defaults to HISTORY at call time (so
    tests can point the module elsewhere)."""
    path = Path(path) if path is not None else HISTORY
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = ""
    if path.exists() and path.stat().st_size:
        with open(path, "rb") as f:
            f.seek(-1, 2)
            if f.read(1) != b"\n":
                prefix = "\n"
    with open(path, "a") as f:
        f.write(prefix + json.dumps(record, separators=(",", ":")) + "\n")


# ----------------------------------------------------------------------------------- browser ----

def _launch(pw, headless: bool):
    """Real Chrome first (best Cloudflare pass rate), bundled Chromium fallback."""
    args = ["--disable-blink-features=AutomationControlled"]
    try:
        return pw.chromium.launch(channel="chrome", headless=headless, args=args)
    except Exception:
        return pw.chromium.launch(headless=headless, args=args)


def _new_context(browser):
    return browser.new_context(user_agent=UA, viewport={"width": 1440, "height": 900},
                               locale="en-US", timezone_id="America/New_York")


def _dismiss_cookies(page):
    for sel in ("#onetrust-reject-all-handler",
                "button:has-text('Reject All Non-Essential Cookies')",
                "button:has-text('Reject Cookies')"):
        try:
            loc = page.locator(sel)
            if loc.count() and loc.first.is_visible():
                loc.first.click(timeout=3000)
                page.wait_for_timeout(600)
                return
        except Exception:
            pass


def _body_text(page) -> str:
    try:
        return page.inner_text("body")
    except Exception:
        return ""


def _is_challenge(txt: str) -> bool:
    low = (txt or "").lower()
    return "security verification" in low or "ray id" in low or "just a moment" in low


def _wait_out_challenge(page, max_s: int = 40) -> bool:
    t0 = time.time()
    while time.time() - t0 < max_s:
        if not _is_challenge(_body_text(page)):
            return True
        page.wait_for_timeout(2500)
    return False


# ------------------------------------------------------------------------------------- quest ----

def sample_quest(ctx, metros: list[dict], asof: dt.datetime, log=print) -> list[dict]:
    """One anonymous UI walk on /find-location to harvest the app's X-CSRF-TOKEN, then one
    in-page getPscsWithAvailability POST per metro (nearest PSCs + slot grids + walk-in wait)."""
    page = ctx.new_page()
    token = {}

    def on_request(req):
        if "getPscsWithAvailability" in req.url:
            t = req.headers.get("x-csrf-token")
            if t:
                token["csrf"] = t

    page.on("request", on_request)

    def all_blocked(detail):
        page.close()
        log(f"  quest: BLOCKED for run — {detail}")
        return [{"company": "quest", "metro": m["metro"], "zip": m["zip"],
                 "status": "blocked", "detail": detail} for m in metros]

    try:
        page.goto(QUEST_FINDER, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4500)
        if not _wait_out_challenge(page):
            return all_blocked("cloudflare managed challenge did not clear in 40s")
        _dismiss_cookies(page)
        _quest_token_walk(page, metros[0]["zip"])
    except Exception as e:
        return all_blocked(f"finder walk failed: {type(e).__name__}: {e}"[:180])
    if "csrf" not in token:
        return all_blocked("app fired no getPscsWithAvailability (UI change?) — no CSRF token")

    rows = []
    payload_base = {"maxReturn": 3, "miles": 25, "facilityServiceId": [QUEST_SERVICE_ID],
                    "firstPscToReturn": 0, "filterForAvailability": False,
                    "includeWaitTime": True, "onlyAvailableSlots": False, "sendSlots": True,
                    "offset": 0, "labCard": False,
                    "fromDate": asof.date().isoformat(),
                    "toDate": (asof.date() + dt.timedelta(days=LOOKAHEAD_DAYS - 1)).isoformat()}
    for m in metros:
        base = {"company": "quest", "metro": m["metro"], "zip": m["zip"]}
        try:
            payload = dict(payload_base, latitude=str(m["lat"]), longitude=str(m["lon"]))
            r = page.evaluate(_FETCH_POST, [QUEST_AVAIL,
                                            {"Content-Type": "application/json",
                                             "Accept": "application/json",
                                             "X-CSRF-TOKEN": token["csrf"]}, payload])
            if r["status"] != 200:
                rows.append({**base, "status": "blocked",
                             "detail": f"getPscsWithAvailability HTTP {r['status']}"})
            else:
                rows.append({**base, **_quest_read_sites(json.loads(r["body"]), asof)})
        except Exception as e:
            rows.append({**base, "status": "error", "detail": f"{type(e).__name__}: {e}"[:200]})
        log(f"  quest {m['metro']}: {rows[-1]['status']} "
            f"{rows[-1].get('next_slot', rows[-1].get('detail', ''))}")
        time.sleep(PACE_S)
    page.close()
    return rows


def _quest_token_walk(page, zip_code: str):
    """Reason -> confirm -> zip search; triggers the app's own availability POST (token sniffed)."""
    page.get_by_role("button", name=re.compile("What testing")).first.click(timeout=8000)
    page.wait_for_timeout(1200)
    page.get_by_role("button", name="All Other Tests").first.click(timeout=6000)
    page.wait_for_timeout(700)
    page.get_by_role("button", name=re.compile("Confirm testing")).first.click(timeout=6000)
    page.wait_for_timeout(2200)
    zbox = None
    for el in page.locator("input").all():
        try:
            if el.is_visible():
                zbox = el
                break
        except Exception:
            pass
    if zbox is None:
        raise RuntimeError("no visible zip input on finder")
    zbox.click()
    zbox.fill(zip_code)
    page.wait_for_timeout(2200)
    opts = page.get_by_role("option")
    if opts.count():
        opts.first.click()
    else:
        zbox.press("Enter")
    page.wait_for_timeout(6000)


def _quest_read_sites(d: dict, asof: dt.datetime) -> dict:
    """Primary = earliest slot at the nearest bookable PSC that shows ANY open slot; secondary =
    earliest across nearest-3.  Semantics, validated 2026-07-23:
      * no scheduleAppt=true site in radius -> no_coverage (structural, not scarcity: e.g. the
        Phoenix metro is Sonora Quest, a 49%-owned JV that books on its own site and is NOT
        consolidated in DGX volumes);
      * a nearest site with an entirely-empty 14d grid while a neighbor has slots is a stale
        site record (observed: duplicate 'Blackhawk' CHI entries, dead one waitTime=None), so
        empty-grid sites are skipped (counted in dead_sites_skipped), NOT read as booked-out;
      * ALL nearest-3 grids empty -> no_slots (real metro scarcity, right-censored at window)."""
    sites = [s for s in (d.get("data") or []) if s.get("scheduleAppt")]
    if not sites:
        others = [s.get("name", "") for s in (d.get("data") or [])]
        return {"status": "no_coverage",
                "detail": ("no PSC on the national scheduler in radius"
                           + (f"; nearest non-bookable: {others[0][:60]}" if others else ""))}
    graded = [s for s in sites if s.get("availability") is not None]
    if not graded:
        return {"status": "no_coverage", "detail": "bookable PSCs expose no online slot grid",
                "site": sites[0].get("name", "")[:80]}
    firsts = [(s, _quest_first_slot(s)) for s in graded[:3]]
    primary, first = next(((s, f) for s, f in firsts if f), (None, None))
    if primary is None:
        return {"status": "no_slots",
                "detail": f"all nearest bookable PSCs booked out within {LOOKAHEAD_DAYS}d",
                "site": graded[0].get("name", "")[:80], "site_id": graded[0].get("siteCode")}
    extra = {"site": primary.get("name", "")[:80], "site_id": primary.get("siteCode")}
    skipped = sum(1 for s, f in firsts if f is None and graded.index(s) < graded.index(primary))
    if skipped:
        extra["dead_sites_skipped"] = skipped
    if isinstance(primary.get("waitTime"), (int, float)):
        extra["walkin_wait_min"] = primary["waitTime"]
    top3 = [f for _, f in firsts if f]
    if top3:
        extra["days_to_next_slot_top3"] = days_to_slot(min(top3), asof)
    return {"status": "ok", "next_slot": first, "days_to_next_slot": days_to_slot(first, asof),
            **extra}


def _quest_first_slot(site: dict) -> str | None:
    """Earliest available 'YYYY-MM-DDTHH:MM' in a site's availability grid."""
    best = None
    for day in site.get("availability") or []:
        date = day.get("date")
        for slot in day.get("slots") or []:
            if slot.get("available") and date and slot.get("time"):
                iso = f"{date}T{slot['time']}"
                if best is None or iso < best:
                    best = iso
        if best:
            break                       # grids are date-ordered; first day with a slot wins
    return best


# ------------------------------------------------------------------------------------ labcorp ---

def sample_labcorp(ctx, metros: list[dict], asof: dt.datetime, log=print) -> list[dict]:
    """Land once, navigate one results page to harvest the app's session Authorization JWT, then
    per metro: in-page fal/search GET (nearest bookable sites) + findAvailableAppointments GET
    over LOOKAHEAD_DAYS.  One 401 re-arms the token by re-navigating the results page."""
    page = ctx.new_page()
    token = {}

    def on_request(req):
        if "cws.labcorp.com" in req.url:
            a = req.headers.get("authorization")
            if a:
                token["auth"] = a

    page.on("request", on_request)

    def arm(metro):
        page.goto(LABCORP_RESULTS.format(zip=metro["zip"], lat=metro["lat"], lon=metro["lon"]),
                  wait_until="domcontentloaded", timeout=60000)
        for _ in range(16):
            page.wait_for_timeout(700)
            if token.get("auth"):
                return True
        return False

    try:
        page.goto(LABCORP_LANDING, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3500)
        _dismiss_cookies(page)
        armed = arm(metros[0])
    except Exception as e:
        page.close()
        detail = f"landing/arm failed: {type(e).__name__}: {e}"[:180]
        log(f"  labcorp: BLOCKED for run — {detail}")
        return [{"company": "labcorp", "metro": m["metro"], "zip": m["zip"],
                 "status": "blocked", "detail": detail} for m in metros]
    if not armed:
        body = _body_text(page)
        detail = ("challenge page" if _is_challenge(body)
                  else "app made no authorized API call (UI change?) — no bearer token")
        page.close()
        log(f"  labcorp: BLOCKED for run — {detail}")
        return [{"company": "labcorp", "metro": m["metro"], "zip": m["zip"],
                 "status": "blocked", "detail": detail} for m in metros]

    rows = []
    rearmed = False
    for m in metros:
        base = {"company": "labcorp", "metro": m["metro"], "zip": m["zip"]}
        try:
            row = _labcorp_query(page, token, m, asof)
            if row.get("detail", "").startswith("HTTP 401") and not rearmed:
                rearmed = True          # token expired mid-run: re-arm once and retry this metro
                token.pop("auth", None)
                if arm(m):
                    row = _labcorp_query(page, token, m, asof)
            rows.append({**base, **row})
        except Exception as e:
            rows.append({**base, "status": "error", "detail": f"{type(e).__name__}: {e}"[:200]})
        log(f"  labcorp {m['metro']}: {rows[-1]['status']} "
            f"{rows[-1].get('next_slot', rows[-1].get('detail', ''))}")
        time.sleep(PACE_S)
    page.close()
    return rows


def _labcorp_query(page, token: dict, m: dict, asof: dt.datetime) -> dict:
    hdrs = {"Accept": "application/json", "Authorization": token.get("auth", "")}
    r = page.evaluate(_FETCH_GET, [LABCORP_SEARCH.format(
        date=asof.date().isoformat(), lat=m["lat"], lon=m["lon"]), hdrs])
    if r["status"] != 200:
        return {"status": "blocked", "detail": f"HTTP {r['status']} on fal/search"}
    sites = [s for s in json.loads(r["body"]).get("results", []) if s.get("canCreateAppointment")]
    if not sites:
        return {"status": "no_slots", "detail": "no bookable patient service centers in radius"}
    site = sites[0]                                     # nearest bookable
    extra = {"site": site["address"]["street"], "site_id": str(site["locatorId"]),
             "site_xcode": site.get("xcode")}
    r2 = page.evaluate(_FETCH_GET, [LABCORP_AVAIL.format(
        loc=site["locatorId"], date=asof.date().isoformat(), days=LOOKAHEAD_DAYS), hdrs])
    if r2["status"] != 200:
        return {"status": "blocked", **extra,
                "detail": f"HTTP {r2['status']} on findAvailableAppointments"}
    slots = json.loads(r2["body"])
    if not slots:
        return {"status": "no_slots", **extra,
                "detail": f"no slots within {LOOKAHEAD_DAYS}d at nearest bookable site"}
    first = min(s["isoApptDateTime"] for s in slots)
    return {"status": "ok", "next_slot": first, "days_to_next_slot": days_to_slot(first, asof),
            "n_slots_visible": len(slots), **extra}


# -------------------------------------------------------------------------------- run modes ----

def run_live(limit: int | None = None, headless: bool = True) -> dict:
    from playwright.sync_api import sync_playwright
    asof = dt.datetime.now()
    metros = json.loads(PANEL.read_text())["metros"]
    if limit:
        metros = metros[:limit]
    rows: list[dict] = []
    with sync_playwright() as pw:
        browser = _launch(pw, headless)
        ctx = _new_context(browser)
        print(f"[lab_panel] sampling {len(metros)} metros x 2 companies asof {asof:%Y-%m-%d %H:%M}")
        rows += sample_labcorp(ctx, metros, asof)
        rows += sample_quest(ctx, metros, asof)
        browser.close()
    return finish_run(rows, asof, source="live")


def run_manual(csv_path: str) -> dict:
    """Ingest a hand-collected CSV (see module docstring for columns)."""
    asof = dt.datetime.now()
    rows = []
    with open(csv_path, newline="") as f:
        for rec in csv.DictReader(f):
            row = {"company": rec["company"].strip().lower(), "metro": rec["metro"].strip(),
                   "zip": rec.get("zip", "").strip(), "status": rec["status"].strip().lower()}
            if rec.get("site"):
                row["site"] = rec["site"].strip()
            iso = (rec.get("next_slot_iso") or "").strip()
            if row["status"] == "ok":
                if not iso:
                    row["status"] = "error"
                    row["detail"] = "manual row marked ok but no next_slot_iso"
                else:
                    row["next_slot"] = iso
                    row["days_to_next_slot"] = days_to_slot(iso, asof)
            rows.append(row)
    return finish_run(rows, asof, source="manual")


def finish_run(rows: list[dict], asof: dt.datetime, source: str) -> dict:
    agg = aggregate(rows, asof)
    record = {"asof": asof.strftime("%Y-%m-%dT%H:%M:%S"), "source": source,
              "lookahead_days": LOOKAHEAD_DAYS, "per_company": agg, "locations": rows}
    append_history(record)
    print(f"\n[lab_panel] {source} sample @ {record['asof']} -> {HISTORY}")
    for co, a in agg.items():
        med = a["median_days_to_next_slot"]
        wait = a.get("median_walkin_wait_min")
        print(f"  {co:8s} median_days_to_next_slot={'n/a' if med is None else med:>5} "
              f"same-day={a['pct_same_day']}% within-48h={a['pct_within_48h']}% "
              f"n_ok={a['n_ok']} n_blocked={a['n_blocked']} n_no_slots={a['n_no_slots']} "
              f"n_no_coverage={a['n_no_coverage']} n_error={a['n_error']}"
              + (f" | walk-in median {wait}min" if wait is not None else ""))
    blocked = [r for r in rows if r.get("status") == "blocked"]
    if blocked:
        reasons: dict[str, int] = {}
        for r in blocked:
            reasons[r.get("detail", "?")] = reasons.get(r.get("detail", "?"), 0) + 1
        print("  blocked breakdown:", json.dumps(reasons))
    print("  PAPER until validated: grade vs the October DGX/LH volume prints before any use.")
    return record


def main(argv=None):
    ap = argparse.ArgumentParser(description="lab appointment-scheduler panel (DGX/LH)")
    ap.add_argument("--manual", metavar="CSV", help="ingest a hand-collected CSV instead of sampling")
    ap.add_argument("--limit", type=int, help="only the first N metros (debug)")
    ap.add_argument("--show", action="store_true", help="headed browser (debug)")
    a = ap.parse_args(argv)
    if a.manual:
        run_manual(a.manual)
    else:
        run_live(a.limit, headless=not a.show)


if __name__ == "__main__":
    main()
