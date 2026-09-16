"""scheduler_exhaust — generalized public-booking-slot scarcity channel (framework).

THE CHANNEL THESIS
------------------
Businesses that take public appointments/reservations leak utilization through slot
scarcity: days-to-next-available, %-same-day, booking-horizon depth. Sampled weekly
over a FIXED panel of locations, that is a LEADING read on reported volume with a
0-1 quarter latency. It is the desk's preferred signal shape: an operational
physical quantity, hard to fake, free to observe, and too niche for alt-data
vendors to productize (no vendor sells "days to next Quest draw appointment").

CONFOUNDER (read this before trusting any panel)
------------------------------------------------
Slot scarcity conflates DEMAND with CAPACITY. Staffing up shortens waits while
volume RISES; staffing down lengthens waits while volume FALLS. A scarcity move is
only a volume read after the capacity side is checked — the designated cross-check
is the hiring_velocity detector (verticals/buyside_dd/connectors/hiring_velocity.py):
same-site posting waves = capacity change, not demand change. Second confounder:
SPOT-vs-AVERAGE sampling — a weekly spot sample of the calendar is not the average
booking experience; keep the sampling weekday/hour fixed per instance and read
TRENDS across snapshots, never one pull.

FRAMEWORK, NOT INSTANCE
-----------------------
This module owns: PanelSpec (what an instance declares), the Playwright sampling
harness (realistic-Chrome fingerprint, land-first-for-cookies, per-location
status), metric aggregation (blocked = MISSING, never zero), newline-safe history
append per instance, and a --manual CSV-ingest fallback.

Instances live in their own modules and register via a thin adapter:

    # desk/<instance>_panel.py
    from desk.scheduler_exhaust import PanelSpec
    def get_panel_specs() -> list[PanelSpec]:
        return [PanelSpec(ticker="DGX", ..., extract=my_extractor)]

Instance #1 is the Quest/Labcorp lab-appointment panel (desk/lab_scheduler_panel.py,
built in a separate lane); INSTANCE_MODULES below is the discovery hook — absent or
half-built modules are skipped gracefully, nothing here imports them at module load.

STATUS: PAPER. Calibration seed = DGX/LH Q2-2026 frozen calls; the channel
graduates only if it beats consensus through the Q3-2026 prints (October).
Never trades; writes only under desk/data/scheduler_exhaust/.
"""
from __future__ import annotations

import csv
import io
import json
import statistics
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "desk" / "data" / "scheduler_exhaust"
CANDIDATES_PATH = DATA_DIR / "candidates.json"
LEDGER_PATH = ROOT / "desk" / "data" / "research_ledger.json"   # READ-ONLY here

# ── dispatch contract (KG dispatch-index doctrine: every detector/connector
#    carries APPLIES_TO so dispatch can query it and the coverage validator can
#    flag unscreened names; the book-wide applicability census itself lives in
#    desk/data/scheduler_exhaust/candidates.json) ────────────────────────────
APPLIES_TO = {
    "sic_codes": [8011, 8049, 8062, 8071, 8093, 7231, 7241, 5812, 7011],
    "sic_prefixes": ["80", "58", "70", "72"],
    "issuer_features": [
        "public_online_booking",
        "appointment_based_service",
        "reservation_based_service",
        "posted_wait_times",
    ],
    "asset_classes": ["public_co_consumer_services", "public_co_healthcare_services",
                      "public_co_general"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": ("Public booking-slot scarcity (days-to-next-available, %same-day, "
                "booking-horizon depth) over a fixed location panel = leading read on "
                "reported volume, 0-1 quarter latency. APPLIES ONLY to appointment/"
                "reservation-based service businesses with public online booking."),
    "verification_question": ("Does observed slot scarcity across the fixed panel "
                              "corroborate or contradict the marketed/consensus volume "
                              "trajectory for the coming print?"),
    "confounders": [
        "capacity_vs_demand — staffing up shortens waits while volume rises; "
        "cross-check: hiring_velocity",
        "spot_vs_average_sampling — fix the sampling weekday/hour; read trends, "
        "not single pulls",
    ],
    "validation_status": "PAPER (seed: DGX/LH Q2-2026 frozen calls; graduates on Q3 beats)",
}

CONFOUNDER_NOTE = ("slot scarcity conflates demand with CAPACITY (staffing up shortens "
                   "waits while volume rises) — cross-check hiring_velocity before "
                   "reading a scarcity move as a volume move")

VALID_STATUSES = ("ok", "no_slots", "blocked")
VALID_CADENCES = ("daily", "weekly", "monthly")

# Realistic desktop-Chrome fingerprint (the desk's standing lesson: gov/enterprise
# WAFs gate on the FULL client-hint + fetch-metadata set, not just UA; Sec-Ch-Ua
# brand versions must match the UA's Chrome major).
CHROME_MAJOR = "131"
CHROME_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
             "AppleWebKit/537.36 (KHTML, like Gecko) "
             f"Chrome/{CHROME_MAJOR}.0.0.0 Safari/537.36")
CHROME_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": (f'"Google Chrome";v="{CHROME_MAJOR}", '
                  f'"Chromium";v="{CHROME_MAJOR}", "Not_A Brand";v="24"'),
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
}

# Thin-adapter discovery: instance modules exposing get_panel_specs() -> [PanelSpec].
# The lab panel (instance #1) is folded in here by the main session once it lands.
INSTANCE_MODULES = (
    "desk.lab_scheduler_panel",
)


# ─────────────────────────────────────────────────────────────────────────────
# PanelSpec — what an instance declares
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class PanelSpec:
    """One company's scheduler panel.

    extract(page, location) -> observation dict is the ONLY instance-specific
    code: given a live Playwright page (already landed on scheduler_url for
    cookies) and one location dict, return at least
        {"status": "ok"|"no_slots"|"blocked", "days_to_next_slot": float|None}
    optionally {"same_day": bool, "within_48h": bool, "note": str}.
    Raise freely — any exception is recorded as status="blocked" (MISSING, never
    zero). Prefer in-page fetch (page.evaluate) over new navigations once landed.
    """
    ticker: str
    company: str
    scheduler_url: str
    flow_notes: str                    # how a booking flows: landing → location → service → calendar
    locations: list[dict] = field(default_factory=list)   # each needs "location_id" (+ "label")
    cadence: str = "weekly"
    read_target: str = ""              # which reported metric this nowcasts
    extract: Optional[Callable[[Any, dict], dict]] = None  # None ⇒ --manual-only instance
    request_pacing_s: float = 8.0      # politeness floor between locations
    landing_settle_ms: int = 2500
    booking_horizon_days: int = 14     # how deep the instance's visible calendar goes
    notes: str = ""

    def validate(self) -> "PanelSpec":
        if not self.ticker or not self.ticker.strip():
            raise ValueError("PanelSpec.ticker required")
        if not self.company:
            raise ValueError(f"{self.ticker}: company required")
        if not str(self.scheduler_url).startswith(("http://", "https://")):
            raise ValueError(f"{self.ticker}: scheduler_url must be http(s), got {self.scheduler_url!r}")
        if self.cadence not in VALID_CADENCES:
            raise ValueError(f"{self.ticker}: cadence {self.cadence!r} not in {VALID_CADENCES}")
        if not self.locations:
            raise ValueError(f"{self.ticker}: panel needs >=1 location")
        seen_ids = set()
        for loc in self.locations:
            lid = (loc or {}).get("location_id")
            if not lid:
                raise ValueError(f"{self.ticker}: every location needs a location_id")
            if lid in seen_ids:
                raise ValueError(f"{self.ticker}: duplicate location_id {lid!r}")
            seen_ids.add(lid)
        if self.request_pacing_s < 2.0:
            raise ValueError(f"{self.ticker}: request_pacing_s >= 2.0s (politeness floor)")
        if self.extract is not None and not callable(self.extract):
            raise ValueError(f"{self.ticker}: extract must be callable or None")
        if self.booking_horizon_days <= 0:
            raise ValueError(f"{self.ticker}: booking_horizon_days must be positive")
        return self


INSTANCES: dict[str, PanelSpec] = {}


def register_instance(spec: PanelSpec) -> PanelSpec:
    spec.validate()
    INSTANCES[spec.ticker] = spec
    return spec


def load_instances() -> dict[str, PanelSpec]:
    """Discover instance adapters (INSTANCE_MODULES). Missing/broken modules are
    skipped — an instance being mid-build must never break the framework."""
    import importlib
    for mod_name in INSTANCE_MODULES:
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        getter = getattr(mod, "get_panel_specs", None)
        specs = []
        try:
            if callable(getter):
                specs = list(getter())
            elif getattr(mod, "PANEL_SPECS", None):
                specs = list(mod.PANEL_SPECS)
        except Exception:
            continue
        for s in specs:
            try:
                register_instance(s)
            except Exception:
                continue
    return INSTANCES


# ─────────────────────────────────────────────────────────────────────────────
# Observations + aggregation — blocked = MISSING, never zero
# ─────────────────────────────────────────────────────────────────────────────
def normalize_observation(raw: dict) -> dict:
    """Coerce one raw per-location result into the canonical observation.

    Hard rules:
      - unknown/absent status  → "blocked" (MISSING)
      - status "ok" WITHOUT a days_to_next_slot number → demoted to "blocked"
        (an ok with no reading must not silently become a zero)
      - "blocked" carries NO metric values, ever
      - "no_slots" = reachable but fully booked in the visible horizon —
        a REAL observation, kept out of the days-to-next median (right-censored)
        and reported via pct_booked_out instead.
    """
    lid = raw.get("location_id")
    status = raw.get("status")
    if status not in VALID_STATUSES:
        status = "blocked"
    days = raw.get("days_to_next_slot")
    if days is not None:
        try:
            days = float(days)
        except (TypeError, ValueError):
            days = None
    if status == "ok" and days is None:
        status = "blocked"
    if days is not None and days < 0:
        days = 0.0
    if status != "ok":
        days = None
    same_day = raw.get("same_day")
    within_48h = raw.get("within_48h")
    if status == "ok":
        if same_day is None:
            same_day = days < 1.0
        if within_48h is None:
            within_48h = days < 2.0
    else:
        same_day = None
        within_48h = None
    return {
        "location_id": lid,
        "status": status,
        "days_to_next_slot": days,
        "same_day": (bool(same_day) if same_day is not None else None),
        "within_48h": (bool(within_48h) if within_48h is not None else None),
        "note": str(raw.get("note", ""))[:160],
    }


def aggregate(observations: list[dict], *, ticker: str, asof: str,
              mode: str = "browser", booking_horizon_days: int = 14) -> dict:
    """Panel metrics over normalized observations.

    Denominators: days-to-next median + %same-day + %within-48h are over OK-only.
    no_slots (booked out beyond the visible horizon) is right-censored — it never
    enters the median as a number, it shows up as pct_booked_out. blocked is
    MISSING — excluded from every rate and never imputed as zero.
    """
    obs = [normalize_observation(o) for o in observations]
    ok = [o for o in obs if o["status"] == "ok"]
    no_slots = [o for o in obs if o["status"] == "no_slots"]
    blocked = [o for o in obs if o["status"] == "blocked"]
    n, n_ok, n_ns, n_bl = len(obs), len(ok), len(no_slots), len(blocked)
    reachable = n_ok + n_ns

    days = [o["days_to_next_slot"] for o in ok]
    median_days = round(statistics.median(days), 2) if days else None
    pct_same_day = round(sum(1 for o in ok if o["same_day"]) / n_ok, 3) if n_ok else None
    pct_within_48h = round(sum(1 for o in ok if o["within_48h"]) / n_ok, 3) if n_ok else None
    pct_booked_out = round(n_ns / reachable, 3) if reachable else None

    if reachable == 0:
        quality = "MISSING"
    elif n and (n_bl / n) > 0.4:
        quality = "DEGRADED"
    else:
        quality = "OK"

    return {
        "asof": asof,
        "ticker": ticker,
        "mode": mode,
        "n_locations": n,
        "n_ok": n_ok,
        "n_no_slots": n_ns,
        "n_blocked": n_bl,
        "coverage": round(reachable / n, 3) if n else 0.0,
        "median_days_to_next_slot": median_days,
        "pct_same_day": pct_same_day,
        "pct_within_48h": pct_within_48h,
        "pct_booked_out": pct_booked_out,          # right-censored at booking_horizon_days
        "booking_horizon_days": booking_horizon_days,
        "sample_quality": quality,
        "confounder": CONFOUNDER_NOTE,
        "observations": obs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# History — newline-safe JSONL append per instance
# ─────────────────────────────────────────────────────────────────────────────
def history_path(ticker: str) -> Path:
    return DATA_DIR / f"{ticker.upper()}_history.jsonl"


def append_history(ticker: str, record: dict) -> Path:
    """Append one snapshot. Newline-safe: if the file exists and does not end
    with a newline (crashed writer, manual edit), one is inserted first so a
    record can never concatenate onto the previous line."""
    p = history_path(ticker)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, default=str)
    if "\n" in line:                       # defensive: JSONL must be one line
        line = line.replace("\n", " ")
    needs_leading_nl = False
    if p.exists() and p.stat().st_size > 0:
        with open(p, "rb") as f:
            f.seek(-1, io.SEEK_END)
            needs_leading_nl = f.read(1) != b"\n"
    with open(p, "a") as f:
        if needs_leading_nl:
            f.write("\n")
        f.write(line + "\n")
    return p


def read_history(ticker: str) -> list[dict]:
    p = history_path(ticker)
    if not p.exists():
        return []
    out = []
    for ln in p.read_text().splitlines():
        ln = ln.strip()
        if ln:
            out.append(json.loads(ln))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Sampling harness — Playwright, realistic fingerprint, land-first
# ─────────────────────────────────────────────────────────────────────────────
def sample_panel(spec: PanelSpec, headless: bool = True) -> list[dict]:
    """Drive a real browser over the panel. Per the desk's standing lesson:
    launch real-Chrome-shaped (full client-hint set, automation flag disabled),
    LAND on the scheduler first so cookies/anti-bot tokens are set, then let the
    instance extractor work the page (in-page fetch preferred). Any per-location
    failure → status 'blocked' (MISSING), never a zero."""
    spec.validate()
    if spec.extract is None:
        raise ValueError(f"{spec.ticker}: no extractor — manual-only instance; use --manual CSV")
    from playwright.sync_api import sync_playwright   # lazy: framework importable without playwright
    observations: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(
            user_agent=CHROME_UA,
            viewport={"width": 1440, "height": 900},
            locale="en-US",
            timezone_id="America/Los_Angeles",
            extra_http_headers=CHROME_HEADERS)
        page = ctx.new_page()
        try:
            page.goto(spec.scheduler_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(spec.landing_settle_ms)      # land first: cookies settle
        except Exception as e:
            browser.close()
            # landing itself blocked → whole panel MISSING this snapshot
            return [normalize_observation({"location_id": loc["location_id"], "status": "blocked",
                                           "note": f"landing: {type(e).__name__}: {str(e)[:80]}"})
                    for loc in spec.locations]
        for loc in spec.locations:
            try:
                raw = dict(spec.extract(page, loc) or {})
                raw.setdefault("location_id", loc["location_id"])
                observations.append(normalize_observation(raw))
            except Exception as e:
                observations.append(normalize_observation(
                    {"location_id": loc["location_id"], "status": "blocked",
                     "note": f"{type(e).__name__}: {str(e)[:80]}"}))
            page.wait_for_timeout(int(spec.request_pacing_s * 1000))
        browser.close()
    return observations


# ─────────────────────────────────────────────────────────────────────────────
# Manual fallback — CSV ingest per instance
# ─────────────────────────────────────────────────────────────────────────────
def ingest_manual_csv(csv_path: str | Path) -> list[dict]:
    """Fallback when the browser path is blocked: hand-collected observations.
    CSV columns: location_id,status[,days_to_next_slot,same_day,within_48h,note]
    status ∈ ok|no_slots|blocked. Empty numeric cells = None (missing, not zero)."""
    rows = []
    with open(csv_path, newline="") as f:
        for r in csv.DictReader(f):
            def _clean(v):
                v = (v or "").strip()
                return v if v else None
            days = _clean(r.get("days_to_next_slot"))
            tf = {"true": True, "1": True, "yes": True,
                  "false": False, "0": False, "no": False}
            sd = _clean(r.get("same_day"))
            w48 = _clean(r.get("within_48h"))
            rows.append(normalize_observation({
                "location_id": _clean(r.get("location_id")),
                "status": _clean(r.get("status")),
                "days_to_next_slot": float(days) if days is not None else None,
                "same_day": tf.get(sd.lower()) if sd else None,
                "within_48h": tf.get(w48.lower()) if w48 else None,
                "note": _clean(r.get("note")) or "",
            }))
    return rows


def run_instance(spec: PanelSpec, *, manual_csv: str | None = None,
                 headless: bool = True, asof: str | None = None,
                 write: bool = True) -> dict:
    """One full snapshot: sample (browser or manual CSV) → aggregate → append history."""
    asof = asof or date.today().isoformat()
    if manual_csv:
        obs, mode = ingest_manual_csv(manual_csv), "manual"
    else:
        obs, mode = sample_panel(spec, headless=headless), "browser"
    rec = aggregate(obs, ticker=spec.ticker, asof=asof, mode=mode,
                    booking_horizon_days=spec.booking_horizon_days)
    rec["read_target"] = spec.read_target
    if write:
        append_history(spec.ticker, rec)
    return rec


# ─────────────────────────────────────────────────────────────────────────────
# Census coverage validator — UNSCREENED ≠ CLEAR
# ─────────────────────────────────────────────────────────────────────────────
def census_gaps() -> list[str]:
    """Ledger names not yet graded in candidates.json. The census IS the
    APPLIES_TO surface for this channel; a name absent from it is UNSCREENED,
    which is a coverage failure, not a pass."""
    try:
        ledger = json.loads(LEDGER_PATH.read_text())
        tickers = {str(n.get("ticker", "")).upper() for n in ledger.get("names", []) if n.get("ticker")}
    except Exception:
        return []
    try:
        cand = json.loads(CANDIDATES_PATH.read_text())
        graded = {str(c.get("ticker", "")).upper() for c in cand.get("candidates", [])}
    except Exception:
        graded = set()
    return sorted(tickers - graded)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="scheduler_exhaust — booking-slot scarcity panels")
    ap.add_argument("--list", action="store_true", help="list registered instances")
    ap.add_argument("--sample", metavar="TICKER", help="browser-sample one instance")
    ap.add_argument("--sample-all", action="store_true", help="browser-sample every registered instance")
    ap.add_argument("--manual", nargs=2, metavar=("TICKER", "CSV"),
                    help="ingest a hand-collected CSV for one instance")
    ap.add_argument("--census-gaps", action="store_true",
                    help="ledger names not graded in candidates.json (UNSCREENED != CLEAR)")
    ap.add_argument("--show", action="store_true", help="also print each snapshot record")
    args = ap.parse_args(argv)

    load_instances()
    if args.list:
        if not INSTANCES:
            print("no instances registered (lab panel lands via desk/lab_scheduler_panel.py)")
        for t, s in sorted(INSTANCES.items()):
            print(f"{t:6s} {s.company:32s} {len(s.locations):3d} locs  {s.cadence:7s} {s.scheduler_url}")
        return
    if args.census_gaps:
        gaps = census_gaps()
        print(f"census gaps: {len(gaps)} ledger names UNSCREENED in candidates.json")
        for t in gaps:
            print(f"  {t}")
        return

    def _one(spec, manual_csv=None):
        rec = run_instance(spec, manual_csv=manual_csv)
        print(f"{spec.ticker}: {rec['asof']} [{rec['mode']}] quality={rec['sample_quality']} "
              f"ok={rec['n_ok']}/{rec['n_locations']} blocked={rec['n_blocked']} "
              f"median_days={rec['median_days_to_next_slot']} same_day={rec['pct_same_day']} "
              f"booked_out={rec['pct_booked_out']} -> {history_path(spec.ticker)}")
        if args.show:
            print(json.dumps(rec, indent=1, default=str))

    if args.manual:
        ticker, csv_path = args.manual[0].upper(), args.manual[1]
        spec = INSTANCES.get(ticker)
        if spec is None:
            raise SystemExit(f"no instance registered for {ticker} (have: {sorted(INSTANCES)})")
        _one(spec, manual_csv=csv_path)
        return
    if args.sample:
        spec = INSTANCES.get(args.sample.upper())
        if spec is None:
            raise SystemExit(f"no instance registered for {args.sample.upper()} (have: {sorted(INSTANCES)})")
        _one(spec)
        return
    if args.sample_all:
        if not INSTANCES:
            print("no instances registered — nothing to sample")
        for _, spec in sorted(INSTANCES.items()):
            try:
                _one(spec)
            except Exception as e:
                print(f"{spec.ticker}: SAMPLE FAILED ({type(e).__name__}: {str(e)[:80]}) — "
                      f"snapshot MISSING, not zero")
        return
    ap.print_help()


if __name__ == "__main__":
    main()
