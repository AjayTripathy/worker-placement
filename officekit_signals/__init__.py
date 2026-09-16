"""officekit_signals — the quant desk's capability registry (F3a, 2026-09-05).

Principal ruling: the desk machinery (generators, detectors, watchers,
evidence) packages into the app AND maps to strategies. This registry is the
dispatch index promoted one level: every capability declares APPLIES_TO over
strategies, symbols, categories, and issuer features — and the effective set
for any (asset, strategy) pair is the UNION of all four axes, derived at
dispatch time, never stored.

The four kinds (one contract each, all `fn(ctx) -> dict`):
    generator  produces candidate assets for a strategy (court dockets)
    detector   a point-in-time screen over evidence — a finding, at court time
    watcher    a standing question over a feed — events, on a cadence; state
               lives in signals_state.json; registered on holdings at purchase
    evidence   a deterministic fact source (bridged from officekit_research)

Lifecycle rule (principal, 2026-09-05): asset-level bindings SURVIVE strategy
changes (the risk belongs to the holding); strategy-level bindings apply while
membership holds.

Observability is first-class: every run is recorded (signals_runs.jsonl),
health derives from last run vs declared cadence, and each capability gets a
rendered page with its ACTUAL CODE and datasources enumerated — glass-box all
the way down. New capabilities are born here, never as ad-hoc scripts.
"""
from __future__ import annotations

import datetime
import inspect
import json
from pathlib import Path

KINDS = ("generator", "detector", "watcher", "evidence")
CAPABILITIES = {}


def _norm_applies(a):
    a = a or {}
    return {"strategies": sorted({s for s in a.get("strategies", [])}),
            "symbols": sorted({str(s).upper() for s in a.get("symbols", [])}),
            "categories": sorted({c for c in a.get("categories", [])}),
            "issuer_features": sorted({f for f in a.get("issuer_features", [])}),
            "universal": bool(a.get("universal"))}


def capability(name, kind, label, desc="", datasources=(), applies_to=None, cadence_days=None,
               source_ref=None):
    """Register one capability. `datasources` enumerates every feed/endpoint
    the capability touches — rendered on its page, honesty by construction."""
    assert kind in KINDS, f"kind must be one of {KINDS}"

    def deco(fn):
        CAPABILITIES[name] = {
            "name": name, "kind": kind, "label": label, "desc": desc,
            "datasources": list(datasources), "applies_to": _norm_applies(applies_to),
            "cadence_days": cadence_days, "fn": fn, "source_ref": source_ref}
        return fn
    return deco


def applicable(symbol=None, strategy=None, category=None, features=(), kinds=None):
    """The UNION resolution: capabilities bound to the strategy, OR the asset,
    OR a matching category/issuer-feature, OR universal. Derived per query —
    no stored copy to drift."""
    out = []
    features = set(features or ())
    for cap in CAPABILITIES.values():
        if kinds and cap["kind"] not in kinds:
            continue
        a = cap["applies_to"]
        hit = (a["universal"]
               or (strategy and strategy in a["strategies"])
               or (symbol and symbol.upper() in a["symbols"])
               or (category and category in a["categories"])
               or (features & set(a["issuer_features"])))
        if hit:
            out.append(cap)
    return sorted(out, key=lambda c: (KINDS.index(c["kind"]), c["name"]))


# ---------------------------------------------------------------- runs & health

def _runs_path(folder):
    return Path(folder) / "signals_runs.jsonl"


from officekit.office_lock import transaction

@transaction()
def record_run(folder, name, status="ok", note="", output=None):
    rec = {"ts": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "name": name, "status": status, "note": note}
    if output is not None:
        s = json.dumps(output)
        rec["output"] = json.loads(s) if len(s) <= 20_000 else {"_truncated": s[:20_000]}
    p = _runs_path(folder)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def runtime(folder):
    """{name: {last_run, status, health, note}} — health from last run vs
    declared cadence: OK / STALE / ERROR / NEVER_RUN."""
    last = {}
    p = _runs_path(folder)
    if p.exists():
        for line in p.read_text().splitlines():
            try:
                r = json.loads(line)
                last[r["name"]] = r
            except Exception:
                continue
    out = {}
    now = datetime.datetime.utcnow()
    for name, cap in CAPABILITIES.items():
        missing = [p for p in cap.get("requires_paths", []) if not Path(p).is_file()]
        if missing:
            out[name] = {"health": "UNAVAILABLE", "last_run": None, "status": None,
                         "note": "Implementation is not installed: " + ", ".join(missing)}
            continue
        r = last.get(name)
        if r is None:
            out[name] = {"health": "NEVER_RUN", "last_run": None, "status": None, "note": ""}
            continue
        health = "ERROR" if r["status"] != "ok" else "OK"
        if health == "OK" and cap.get("cadence_days"):
            age = (now - datetime.datetime.fromisoformat(r["ts"].rstrip("Z"))).days
            if age > cap["cadence_days"]:
                health = "STALE"
        out[name] = {"health": health, "last_run": r["ts"], "status": r["status"],
                     "note": r.get("note", ""), "output": r.get("output")}
    return out


def run_capability(folder, name, ctx):
    """Run one capability with a ctx dict ({folder, symbol?, strategy?,
    office_data?, contact?, symbols?}); record the run either way — an
    infra failure is its own class, never a silent negative."""
    cap = CAPABILITIES.get(name)
    if cap is None:
        raise KeyError(f"signals: no capability {name!r}")
    ctx = dict(ctx or {})
    ctx.setdefault("folder", str(folder))
    from officekit.api_errors import report, clear, message
    proposal = ctx.get('proposal') or {}
    error_context = ('proposal:' + proposal['id'] if proposal.get('id') else
                     'signal:' + name + ':' + str(ctx.get('symbol') or ''))
    try:
        missing = [p for p in cap.get("requires_paths", []) if not Path(p).is_file()]
        if missing:
            raise RuntimeError("capability implementation not installed: " + ", ".join(missing))
        out = cap["fn"](ctx)
        record_run(folder, name, "ok", output=out)
        clear(folder, context=error_context)
        return out
    except Exception as e:
        record_run(folder, name, "error", note=message(e))
        report(folder, error_context, 'SignalOS request failed', e,
               href=f'/pages/capability_{name}.html')
        raise


def source_code(name):
    """The ACTUAL code powering the capability — the referenced module file
    when the registered fn is only a thin adapter, else the fn itself."""
    cap = CAPABILITIES[name]
    if cap.get("source_ref"):
        try:
            return Path(cap["source_ref"]).read_text()
        except Exception:
            pass
    try:
        return inspect.getsource(cap["fn"])
    except Exception:
        return "(source unavailable)"


# ---------------------------------------------------------------- watcher state

def _state_path(folder):
    return Path(folder) / "signals_state.json"


def load_state(folder):
    p = _state_path(folder)
    return json.loads(p.read_text()) if p.exists() else {}


@transaction()
def save_state(folder, state):
    _state_path(folder).write_text(json.dumps(state, indent=1))


# ================================================================ flagships ==

@capability("drawdown_screen", "generator", "Drawdown screen",
            desc="Candidates ranked by drawdown from their 52-week high — the "
                 "realized-winner entry signature (good businesses at deep "
                 "discounts to their OWN history; see pnl-attribution doctrine). "
                 "Quality gate is the COURT's job, not the screen's.",
            datasources=["Nasdaq free historical endpoint (close-only daily bars)"],
            applies_to={"strategies": ["quality_value", "core_equity", "concentrated",
                                       "value_band_entry", "quality_drawdown"],
                        "universal": False})
def gen_drawdown_screen(ctx):
    from officekit_research import SOURCES as EV
    symbols = [s.upper() for s in (ctx.get("symbols") or []) if str(s).strip()]
    if not symbols:
        raise RuntimeError("drawdown_screen needs a symbol universe (ctx['symbols'])")
    rows, errors = [], []
    for sym in symbols[:25]:
        try:
            t = EV["tape"](sym, ctx)
            rows.append({"symbol": sym, "last": t["last"], "off_high_pct": t["off_high_pct"]})
        except Exception as e:
            errors.append(f"{sym}: {type(e).__name__}")
    rows.sort(key=lambda r: r["off_high_pct"])
    return {"candidates": rows, "errors": errors,
            "note": "rank = % off 52wk high; deepest first; court every pick before sizing"}


@capability("unread_recent_filings", "detector", "Unread recent filings",
            desc="Fires when the issuer filed 8-K/6-K-class documents within "
                 "the last 7 days — a court adjudicating without reading them "
                 "repeats the HOFT miss (data-integrity class: kills the "
                 "ruling, not the size).",
            datasources=["SEC EDGAR submissions API (data.sec.gov)"],
            applies_to={"universal": True})
def det_unread_recent_filings(ctx):
    from officekit_research import SOURCES as EV, _cik
    sym = ctx["symbol"]
    ctx = dict(ctx)
    ctx.setdefault("cik", _cik(sym, ctx["contact"]))
    f = EV["filings"](sym, ctx)
    cutoff = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    recent = [r for r in f["recent"] if r["date"] >= cutoff and r["form"] in ("8-K", "6-K")]
    return {"fired": bool(recent), "findings": recent,
            "note": "every listed filing must be read before a verdict" if recent else "clear"}


@capability("tenx_guard", "detector", "TENX cap-structure guard",
            desc="Fires REVIEW when the XBRL battery lacks share-count / OCF "
                 "coverage — per the TENX rule no per-share, net-cash, or EV "
                 "claim may be asserted before the cap-structure pull.",
            datasources=["SEC XBRL companyconcept API (data.sec.gov)"],
            applies_to={"universal": True})
def det_tenx_guard(ctx):
    from officekit_research import SOURCES as EV, _cik
    sym = ctx["symbol"]
    ctx = dict(ctx)
    ctx.setdefault("cik", _cik(sym, ctx["contact"]))
    try:
        x = EV["xbrl"](sym, ctx)
    except Exception as e:
        return {"fired": True, "findings": [f"no XBRL at all: {e}"],
                "note": "REVIEW — every per-share claim is unverifiable"}
    missing = [k for k in ("dil_sh", "ocf") if k not in x]
    return {"fired": bool(missing), "findings": missing,
            "note": ("REVIEW — missing tags block per-share claims: " + ", ".join(missing))
            if missing else "cap-structure tags present"}


@capability("filing_watch", "watcher", "Filing watch",
            desc="The disclosure watch, promoted: polls EDGAR submissions per "
                 "held symbol; a NEW accession since last look is an event "
                 "(read it, re-open the pack — the entity-disclosure-planes "
                 "doctrine, US plane). Registered on holdings at purchase.",
            datasources=["SEC EDGAR submissions API (data.sec.gov)"],
            applies_to={"universal": True}, cadence_days=1)
def watch_filings(ctx):
    from officekit_research import SOURCES as EV, _cik
    folder = ctx["folder"]
    data = ctx.get("office_data") or {}
    symbols = sorted({str(h.get("company", "")).upper()
                      for s in data.get("sleeves", []) for h in s.get("holdings", [])
                      if h.get("company")})
    state = load_state(folder)
    seen = state.setdefault("filing_watch", {})
    events, errors = [], []
    for sym in symbols:
        try:
            c = dict(ctx)
            c.setdefault("cik", _cik(sym, ctx["contact"]))
            f = EV["filings"](sym, c)
            newest = f["recent"][0]["acc"] if f["recent"] else None
            if newest and seen.get(sym) and seen[sym] != newest:
                events.append({"symbol": sym, "new_since": seen[sym],
                               "latest": f["recent"][0]})
            if newest:
                seen[sym] = newest
        except Exception as e:
            errors.append(f"{sym}: {type(e).__name__}")
    save_state(folder, state)
    return {"events": events, "watched": symbols, "errors": errors,
            "note": f"{len(events)} new filing(s)" if events else "no changes"}


@capability("verdict_outcomes", "watcher", "Verdict outcomes (the grading loop)",
            desc="The calibration spine: grades every adjudication old enough to "
                 "judge (default 30d) against the tape since its verdict date. "
                 "STARTER/OWN grade favorable on a positive move, KILL/AVOID on "
                 "flat-or-down; WATCH is ungraded by design. Each grade writes a "
                 "verdict_grade record to the learning ledger — the court's own "
                 "Brier book. Idempotent per adjudication (state cursor); grades "
                 "are LOCAL (tickers — never leaves through the learning "
                 "allowlist).",
            datasources=["adjudications.jsonl (the office's own verdicts)",
                         "Nasdaq free historical endpoint (or the tenant tape plugin)"],
            applies_to={"universal": True}, cadence_days=7)
def watch_verdict_outcomes(ctx):
    import urllib.request as _u
    from officekit_ai.evaluation import grade_direction
    from officekit.learning import record as ledger_record, _read as read_ledger
    from officekit_ai.court import load_adjudications
    folder = ctx["folder"]
    horizon = int(ctx.get("horizon_days", 30))
    today = datetime.date.fromisoformat(ctx["today"]) if ctx.get("today") else datetime.date.today()
    state = load_state(folder)
    done = state.setdefault("verdict_outcomes", {})
    # Recover from a crash after the ledger append but before the cursor save.
    # Legacy arbitrary-horizon grades have no protocol and are not reused.
    for record in read_ledger(Path(folder) / "learning.jsonl"):
        p = record.get("payload") or {}
        if record.get("kind") == "verdict_grade" and p.get("protocol") == "fixed_horizon_v1":
            done[f"{p['adjudication_id']}|fixed_horizon_v1|{p['horizon_days']}"] = "graded"
    graded, skipped, errors = [], 0, []
    for a in load_adjudications(folder):
        if a.get("subject_kind", "security") != "security":
            continue
        key = f"{a['id']}|fixed_horizon_v1|{horizon}"
        if key in done:
            continue
        word = (a.get("verdict") or "").split(" ")[0]
        if word not in {"STARTER", "OWN", "AVOID", "KILL"}:
            done[key] = "ungraded_verdict"
            skipped += 1
            continue
        try:
            vdate = datetime.date.fromisoformat(a["date"])
            if (today - vdate).days < horizon:
                continue
            if ctx.get("price_history"):
                closes = ctx["price_history"](a["symbol"], vdate, today)
            else:
                url = (f"https://api.nasdaq.com/api/quote/{a['symbol']}/historical"
                       f"?assetclass=stocks&fromdate={vdate}&todate={today}&limit=9999")
                req = _u.Request(url, headers={"User-Agent": "Mozilla/5.0", "Origin": "https://www.nasdaq.com"})
                with _u.urlopen(req, timeout=20) as response:
                    rows = ((json.loads(response.read().decode()).get("data") or {})
                            .get("tradesTable") or {}).get("rows") or []
                closes = [(r["date"], float(r["close"].replace("$", "").replace(",", ""))) for r in rows]
            grade = grade_direction(a, closes, horizon, today)
            if grade is None:
                continue
            ledger_record(Path(folder) / "learning.jsonl", "verdict_grade", grade,
                          office_id=a.get("office_id"))
            done[key] = "graded"
            graded.append(grade)
        except Exception as e:
            errors.append(f"{a.get('symbol')}: {type(e).__name__}: {e}")
    save_state(folder, state)
    n_fav = sum(1 for g in graded if g["favorable"])
    return {"graded": graded, "skipped_watch": skipped, "errors": errors,
            "note": f"{n_fav}/{len(graded)} favorable price follow-ups (not alpha or probability calibration)"
                    if graded else "nothing ripe"}


# evidence bridge: every officekit_research source registers as a capability
def _bridge_evidence():
    from officekit_research import SOURCES
    DS = {"filings": ["SEC EDGAR submissions API"],
          "xbrl": ["SEC XBRL companyconcept API"],
          "tape": ["Nasdaq free historical endpoint"],
          "book": ["the office's own balance_sheet.json"],
          "filing_text": ["SEC EDGAR archives (primary documents)"]}
    for name, fn in SOURCES.items():
        cap_name = f"evidence_{name}"
        if cap_name in CAPABILITIES:
            continue

        def make(fn, name):
            def run(ctx):
                from officekit_research import build_pack
                pack = build_pack(ctx["symbol"], office_data=ctx.get("office_data"),
                                  contact=ctx.get("contact"), sources=[name])
                if name not in pack["sections"]:
                    raise RuntimeError("; ".join(pack["errors"]) or "no section produced")
                return pack["sections"][name]
            return run
        capability(cap_name, "evidence", f"Evidence: {name}",
                   desc=f"Deterministic evidence source '{name}' — one section of "
                        f"the court's shared machine layer (see officekit_research).",
                   datasources=DS.get(name, []),
                   applies_to={"universal": True})(make(fn, name))


_bridge_evidence()
