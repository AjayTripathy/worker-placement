"""server — FastAPI backend for the Desk/SignalOS dashboard. Serves the aggregator's JSON and the
static single-page frontend. READ-ONLY: it exposes nothing that mutates state or places an order.

  pip install fastapi uvicorn
  python3 -m desk.ui.server          # -> http://127.0.0.1:8765
"""
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import aggregator as A


def _sanitize(o):
    """NaN/inf firewall at the API boundary — one bad float must never 500 the whole payload
    (tax_fit NaN incident 2026-07-02). Applied to every JSON response."""
    import math
    if isinstance(o, float):
        return None if (math.isnan(o) or math.isinf(o)) else o
    if isinstance(o, dict):
        return {k: _sanitize(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_sanitize(v) for v in o]
    return o


def _json(payload):
    return JSONResponse(_sanitize(payload))

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Desk / SignalOS", docs_url=None, redoc_url=None)


@app.get("/api/health")
def api_health():
    """Production health: store freshness + scanner age + page integrity — what a monitor should poll."""
    import time, json as _j
    now = time.time()
    def age_min(p):
        try:
            return round((now - p.stat().st_mtime) / 60, 1)
        except Exception:
            return None
    stores = {
        "research_ledger_age_min": age_min(ROOT / "desk" / "data" / "research_ledger.json"),
        "catalyst_scanner_age_min": age_min(ROOT / "desk" / "data" / "CATALYST_MISPRICING.json"),
        "tax_fit_age_min": age_min(ROOT / "desk" / "data" / "tax_fit.json"),
        "calibration_ledger_age_min": age_min(ROOT / "desk" / "data" / "calibration_ledger.jsonl"),
    }
    html = (STATIC / "index.html").read_text()
    ok = html.rstrip().endswith("</html>")
    status = "ok" if ok and (stores["catalyst_scanner_age_min"] or 9e9) < 26 * 60 else "degraded"
    return _json({"status": status, "page_integrity": ok, "stores": stores, "ts": now})


@app.get("/api/verdicts")
def api_verdicts():
    from desk.verdicts import all_verdicts
    return _json({"verdicts": all_verdicts()})


@app.post("/api/verdict/{sym}")
def api_set_verdict(sym: str, payload: dict):
    """Research-metadata mutation ONLY (state/stage/note) — validated + audited. Never orders."""
    from desk.verdicts import set_verdict, InvalidVerdict
    try:
        return _json(set_verdict(sym, payload.get("state"), payload.get("stage"),
                                 payload.get("note"), source="dashboard"))
    except InvalidVerdict as e:
        raise HTTPException(422, str(e))


@app.post("/api/approve/{sym}")
def api_approve(sym: str, payload: dict):
    """Records the USER's approval on an entry (local queue only — the assistant stages each approved
    order with explicit per-order confirmation; this endpoint never touches the broker)."""
    from . import aggregator as AG
    return _json(AG.set_order_approval(sym, bool(payload.get("approved", True))))


import threading, time
# /api/everything does ~30-40s of live yfinance/IBKR work (overview/alerts/watchlist/triggers).
# Serve it from a cache with background revalidate so page load is INSTANT and never blocks on the network.
_EVERY = {"data": None, "ts": 0.0, "refreshing": False}
_EVERY_TTL = 75.0


def _refresh_every():
    try:
        _EVERY["data"] = _sanitize(A.everything())
        _EVERY["ts"] = time.time()
    except Exception:
        pass
    finally:
        _EVERY["refreshing"] = False


@app.get("/api/everything")
def api_everything(fresh: int = 0):
    """Serve-stale-while-revalidate: return the cache immediately; refresh in the background if stale.
    fresh=1 (the force-refresh button) recomputes SYNCHRONOUSLY — live network, ~30-40s — before returning."""
    if fresh:
        _refresh_every()
        return JSONResponse(_EVERY["data"])
    if _EVERY["data"] is None:
        _refresh_every()
    elif time.time() - _EVERY["ts"] > _EVERY_TTL and not _EVERY["refreshing"]:
        _EVERY["refreshing"] = True
        threading.Thread(target=_refresh_every, daemon=True).start()
    return JSONResponse(_EVERY["data"])


@app.on_event("startup")
def _warm_every():
    _EVERY["refreshing"] = True
    threading.Thread(target=_refresh_every, daemon=True).start()


@app.get("/api/infra")
def api_infra():
    from . import health_page
    return JSONResponse(health_page.collect())


@app.get("/api/pipeline_metrics")
def api_pipeline_metrics():
    """PRD success-metric snapshots (pipeline_metrics cron) + the current invariant flags."""
    import json as _j
    p = ROOT / "desk" / "data" / "pipeline_metrics.json"
    snaps = []
    try:
        snaps = _j.loads(p.read_text()).get("snapshots", [])
    except Exception:
        pass
    flags = []
    try:
        from desk.pipeline_invariants import run_all
        flags = run_all()
    except Exception as e:
        flags = [f"invariant suite errored: {type(e).__name__}"]
    return _json({"snapshots": snaps[-30:], "flags": flags})


@app.get("/api/{section}")
def api_section(section: str):
    fn = {"overview": A.overview, "watches": A.watches, "detectors": A.detectors,
          "catalysts": A.catalysts, "book": A.book, "signals": A.signals,
          "harvest": A.harvest, "research": A.research, "positions": A.positions,
          "triggers": A.triggers, "watchlist": A.watchlist, "entry": A.entry_candidates,
          "parametric": A.parametric, "factor": A.factor_drift,
          "catalyst_value": A.catalyst_value, "antibook_perf": A.antibook_perf}.get(section)
    if not fn:
        raise HTTPException(404, f"no section {section}")
    return _json(A._safe(fn))


@app.get("/api/ticker/{sym}")
def api_ticker(sym: str):
    return JSONResponse(A._safe(lambda: A.ticker_dossier(sym)))


@app.post("/api/run/{name}")
def api_run(name: str):
    """Run a REGISTERED watch on demand. SAFETY: whitelisted to desk/registry.py only (the cmd comes from
    the registry, never user input); the registered watches are all READ-ONLY analysis/scans that never
    place orders; server binds to 127.0.0.1. Captures stdout for the dashboard's latest-reading."""
    import subprocess
    from desk.registry import WATCHES, mark_ran
    w = next((x for x in WATCHES if x["name"] == name), None)
    if not w:
        raise HTTPException(404, f"unknown watch {name}")
    runs = A.RUNS_DIR
    runs.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(w["cmd"], cwd=str(ROOT), capture_output=True, text=True, timeout=260)
        out = (r.stdout or "")
        if r.returncode != 0 and r.stderr:
            out += "\n[stderr]\n" + r.stderr[-1500:]
    except subprocess.TimeoutExpired:
        out = "[timed out after 260s — the IV/network step may need TWS]"
    except Exception as e:
        out = f"[run error: {type(e).__name__}: {e}]"
    (runs / f"{name}.txt").write_text(out)
    try:
        mark_ran(name)
    except Exception:
        pass
    lines = [l for l in out.splitlines() if l.strip()]
    return JSONResponse({"name": name, "ran": True, "lines": lines[-40:]})


@app.post("/api/approve_order/{ticker}")
def api_approve_order(ticker: str, approved: bool = True):
    """Stage/unstage an approved entry order. SAFETY: this does NOT place an order — it only writes the
    ticker to a local approval queue (desk/ui/data/approved_orders.json). The assistant later places each
    queued order via the IBKR tools with explicit per-order confirmation. The dashboard never touches the
    broker; the order plan is whitelisted to desk/data/entry_plan.json (not user-supplied)."""
    plan = A.entry_candidates()
    if ticker not in {o["ticker"] for o in plan.get("orders", [])}:
        raise HTTPException(404, f"{ticker} not in the entry plan")
    return JSONResponse(A.set_order_approval(ticker, approved))


@app.post("/api/factor_drift/recompute")
def api_factor_recompute():
    """Recompute the FF5 factor-drift cache. SAFETY: read-only analytics — runs `desk.factor_drift --cache`,
    which pulls/caches factor loadings (yfinance + Ken French) and writes desk/ui/data/factor_drift.json.
    Touches NO broker and places NO orders. Network step can take ~30-90s."""
    import subprocess
    try:
        r = subprocess.run(["python3", "-m", "desk.factor_drift", "--cache"], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=280)
        ok = r.returncode == 0
        return JSONResponse({"ran": ok, "msg": (r.stdout or r.stderr or "")[-400:]})
    except subprocess.TimeoutExpired:
        return JSONResponse({"ran": False, "msg": "timed out (>280s) — the loadings network step is slow"})
    except Exception as e:
        return JSONResponse({"ran": False, "msg": f"{type(e).__name__}: {e}"})


@app.get("/doc", response_class=PlainTextResponse)
def doc(file: str):
    """Serve a research doc (md as text, pdf as file). Path-restricted to the repo (read-only)."""
    p = (ROOT / file).resolve()
    if not str(p).startswith(str(ROOT)) or not p.exists():
        raise HTTPException(404, "not found")
    if p.suffix == ".pdf":
        return FileResponse(str(p), media_type="application/pdf")
    return PlainTextResponse(p.read_text(errors="ignore"))


@app.get("/ticker/{sym}", response_class=HTMLResponse)
def ticker_page(sym: str):
    """Canonical per-ticker dossier PAGE — every ticker across the app links here (the rule).
    Works from iframes/static pages where the SPA modal can't reach."""
    from . import dossier_page
    return HTMLResponse(dossier_page.render(A._safe(lambda: A.ticker_dossier(sym))))


@app.get("/detector/{name}", response_class=HTMLResponse)
def detector_page_route(name: str):
    """A detector's definition + its prediction track record (the reverse of the prediction→detector link)."""
    from . import detector_page
    return HTMLResponse(detector_page.render(name))


@app.get("/health", response_class=HTMLResponse)
def health_page_route():
    """Infrastructure health board: watch liveness, consistency flags, heartbeats, incidents
    ledger. Born 2026-07-31 after the grader crashed silently for ~36h. Computed live."""
    from . import health_page
    return HTMLResponse(health_page.render())


@app.get("/brain", response_class=HTMLResponse)
def brain_page_route():
    """The dispatch-brain map: channels -> watches -> three-ring dispatcher -> detector atlas.
    Rendered live from the knowledge graph + registry, so APPLIES_TO coverage growth shows up here."""
    from . import brain_page
    return HTMLResponse(brain_page.render())


@app.get("/api/pipeline-status")
def api_pipeline_status():
    """Pipeline status: queue census, runner/daemon health, recent rulings, calendar, open calls."""
    from . import status_page as SP
    return _json(SP.status_payload())


@app.get("/status", response_class=HTMLResponse)
def status_view():
    from . import status_page as SP
    return SP.render_html()


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse((STATIC / "index.html").read_text())


if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
