"""consistency_check — the guard against "the adjudication lived only in a memo." Diffs the THREE stores every
research conclusion must agree across — edge_classifications/*.json (the DD verdicts), entry_plan.json (staged
sizing), research_ledger.json (the Watchlist) — and FLAGs any name whose verdict/sizing disagree, plus staleness
(scanner output older than the newest record). Built 2026-07-01 after the user caught the same drift SIX times
(EOLS invisibility, un-upserted DD names, un-propagated rebuttal sizes). Runs on the heartbeat; FLAG lines
surface to the signal feed via the generic extractor. READ-ONLY.

  python3 -m desk.consistency_check
"""
from __future__ import annotations
import json, re, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EC = ROOT / "desk" / "data" / "edge_classifications"
PLAN = ROOT / "desk" / "data" / "entry_plan.json"
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
SCAN = ROOT / "desk" / "data" / "CATALYST_MISPRICING.json"

# verdict compatibility: plan/ledger verdicts that CONTRADICT each other (order-insensitive pairs)
_BUYISH = {"BUY", "STARTER", "OWN", "OWNABLE", "HELD", "ENTRY"}
_WAITISH = {"WAIT", "WATCH", "NOT_YET", "TO_DILIGENCE"}
_NOISH = {"AVOID", "SHORT", "PASS", "SKIP", "DROP", "TRAP"}


def _bucket(v: str | None) -> str | None:
    """Bucket on the verdict HEADLINE (first ~32 chars), not the whole prose — 'well-paid to wait' in a
    STARTER verdict's tail must not read as WAIT."""
    if not v:
        return None
    u = str(v).upper()[:32]
    for b, names in (("NO", _NOISH), ("WAIT", _WAITISH), ("BUY", _BUYISH)):
        if any(k in u for k in names):
            return b
    return None


def _pct_range_from_sizing(s):
    """(lo, hi) of the FIRST %-range in an edge-record sizing field — '1-2% starter' -> (1,2); '4%' -> (4,4)."""
    txt = json.dumps(s) if isinstance(s, (dict, list)) else str(s or "")
    # ONE pass, optional range — the FIRST %-mention wins ('2.5% pre-print ... scale to 6-7%' must read 2.5,
    # not jump ahead to the 6-7 range)
    m = re.search(r"(\d+(?:\.\d+)?)(?:\s*[-–]\s*(\d+(?:\.\d+)?))?\s*%", txt)
    if not m:
        return None
    lo = float(m.group(1))
    hi = float(m.group(2)) if m.group(2) else lo
    return lo, hi


def check() -> list[str]:
    flags = []
    plan = json.loads(PLAN.read_text()) if PLAN.exists() else {"orders": []}
    led = {n["ticker"].upper(): n for n in json.loads(LEDGER.read_text()).get("names", [])} if LEDGER.exists() else {}
    plan_by = {o["ticker"].upper(): o for o in plan.get("orders", [])}

    newest_rec = 0.0
    for f in sorted(EC.glob("*.json")):
        newest_rec = max(newest_rec, f.stat().st_mtime)
        try:
            d = json.loads(f.read_text())
        except Exception:
            flags.append(f">>> FLAG CONSISTENCY: {f.name} unparseable JSON")
            continue
        t = (d.get("ticker") or f.stem).upper()
        base = t.split(".")[0]
        po = plan_by.get(t) or plan_by.get(base)
        ln = led.get(t) or led.get(base)
        rb = _bucket(d.get("verdict_state")) if d.get("verdict_state") else _bucket(d.get("verdict") or d.get("final_thesis_type"))
        pb, lb = _bucket((po or {}).get("verdict")), _bucket((ln or {}).get("state") or (ln or {}).get("verdict"))
        # 1) verdict contradictions across stores (BUY vs NO, BUY vs WAIT is a real gate difference — flag only hard conflicts + BUY/WAIT splits)
        pairs = [("record", rb), ("entry_plan", pb), ("ledger", lb)]
        present = [(src, b) for src, b in pairs if b]
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                (s1, b1), (s2, b2) = present[i], present[j]
                if {b1, b2} == {"BUY", "NO"} or {b1, b2} == {"BUY", "WAIT"}:
                    flags.append(f">>> FLAG CONSISTENCY {t}: {s1}={b1} but {s2}={b2} — a later adjudication may not have propagated")
        # 2) sizing drift: staged weight must fall inside the record's %-range (tolerance 0.6pp)
        if po and po.get("weight_pct") is not None:
            rng = _pct_range_from_sizing(d.get("sizing"))
            w = float(po["weight_pct"])
            if rng and not (rng[0] - 0.6 <= w <= rng[1] + 0.6):
                flags.append(f">>> FLAG CONSISTENCY {t}: record sizing says {rng[0]}-{rng[1]}% but entry_plan stages {w}% — propagate the adjudication")
        # 3) actionable record missing from the ledger entirely (the un-upserted-DD failure)
        if rb == "BUY" and not ln:
            flags.append(f">>> FLAG CONSISTENCY {t}: BUY/STARTER record exists but the name is NOT in the research ledger (run desk.ledger_add)")
    # 4) scanner staleness: records newer than the last scan = alerts page running on old data
    if SCAN.exists() and newest_rec > SCAN.stat().st_mtime + 60:
        age_h = (newest_rec - SCAN.stat().st_mtime) / 3600
        flags.append(f">>> FLAG CONSISTENCY: edge_classifications changed {age_h:.1f}h after the last catalyst_mispricing scan — re-run the scanner")
    return flags


def check_alert_records_complete(flags):
    """Every ticker surfaced on the alerts page (go + no_go) that HAS an edge_classifications record
    must carry a top-level 'verdict' AND an 'edge_explainer' — a dossier visible at decision-time may
    not be headless (028260.KS lesson 2026-07-02; field-level gaps recurred after BKE/SBH backfill)."""
    try:
        from desk.ui.aggregator import alerts
        a = alerts()
        import json as _j
        from pathlib import Path as _P
        ec = ROOT / "desk" / "data" / "edge_classifications"
        for r in a.get("go", []) + a.get("no_go", []):
            t = r["ticker"]
            f = ec / f"{t}.json"
            if not f.exists():
                if r in a.get("go", []):
                    flags.append(f"{t}: on the GO list with NO dossier at all (single-pass name?) — pipeline it or pull it (CBKD lesson 2026-07-03)")
                continue
            try:
                rec = _j.loads(f.read_text())
            except Exception:
                flags.append(f"{t}: edge_classifications JSON unparseable")
                continue
            missing = [k for k in ("verdict", "edge_explainer") if not rec.get(k)]
            if missing:
                flags.append(f"{t}: on the alerts page but record missing {missing}")
    except Exception as e:
        flags.append(f"alert-record schema guard errored: {type(e).__name__}")


def check_ui_static_integrity(flags):
    """The served page must be structurally sound: nothing after </html> (a find()==-1 splice renders
    as garbage text — happened TWICE on 2026-07-02: the in_book and ready sections), and every alerts
    bucket the aggregator emits must have a render marker INSIDE the html body."""
    try:
        s = (ROOT / "desk" / "ui" / "static" / "index.html").read_text()
        if not s.rstrip().endswith("</html>"):
            flags.append("index.html has stray content after </html> — a bad splice is rendering as page garbage")
        body = s[:s.find("</html>")]
        for marker, name in (("a.go||", "go"), ("a.no_go||", "no_go"), ("a.in_book||", "in_book"), ("a.ready||", "ready")):
            if marker not in body:
                flags.append(f"index.html missing the '{name}' render section inside the body")
    except Exception as e:
        flags.append(f"ui-static integrity guard errored: {type(e).__name__}")


def check_new_calls_have_reasoning(flags):
    """Every calibration call frozen from 2026-07-03 onward must carry a 'reasoning' field — a bare p
    teaches nothing at resolution time (you must know WHICH premise failed). Backfilled older calls are
    marked; new ones without reasoning are a process violation."""
    try:
        import json as _j
        for l in (ROOT / "desk" / "data" / "calibration_ledger.jsonl").read_text().splitlines():
            if not l.strip():
                continue
            r = _j.loads(l)
            if r.get("made", "") >= "2026-07-03" and not r.get("reasoning"):
                flags.append(f"{r['ticker']} {r.get('cat_date')}: frozen WITHOUT reasoning — record the premises before the event resolves")
            if r.get("made", "") >= "2026-07-04" and not r.get("event_type"):
                flags.append(f"{r['ticker']} {r.get('cat_date')}: frozen WITHOUT event_type — the by-type calibration needs the tag at freeze time")
            if r.get("event_type"):
                from desk.events import validate_event_type
                if not validate_event_type(r["event_type"]):
                    flags.append(f"{r['ticker']} {r.get('cat_date')}: event_type '{r['event_type']}' not in the closed enum (desk/events.py) — free-typed tags break per-type Brier")
            if r.get("made", "") >= "2026-07-04" and not (r.get("plain") or {}).get("what"):
                flags.append(f"{r['ticker']} {r.get('cat_date')}: frozen WITHOUT the plain-language block (what/how/conclusion) — reader-facing surfaces render it")
    except Exception as e:
        flags.append(f"reasoning guard errored: {type(e).__name__}")


def check_positions_ledger_agree(flags):
    """Two-directional (plans != holdings lesson 2026-07-04): every Gateway position must have a
    ledger entry with HELD/OWN state, and every HELD/OWN ledger name must exist in the positions
    cache. Catches both unledgered holdings AND plans masquerading as positions."""
    try:
        pc = ROOT / "desk" / "ui" / "data" / "positions_cache.json"
        if not pc.exists():
            return
        cache = json.loads(pc.read_text())
        if (ROOT / "desk" / "data").exists() and cache.get("positions") is not None:
            import time as _t
            if _t.time() - cache.get("asof", 0) > 3 * 86400:
                flags.append("positions_cache is >3 days stale — run desk.positions_sync")
        held_actual = {p["symbol"] for p in cache.get("positions", []) if p.get("sec_type", "STK") == "STK"}
        led = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", [])
        held_ledger = {n["ticker"] for n in led if (n.get("state") or n.get("verdict")) in ("HELD", "OWN")}
        for t in sorted(held_actual - held_ledger):
            flags.append(f"{t}: REAL POSITION with no HELD ledger entry — unledgered holding")
        for t in sorted(held_ledger - held_actual):
            flags.append(f"{t}: ledger says HELD but NOT in the Gateway positions — a plan masquerading as a holding (or an unsynced exit)")
    except Exception as e:
        flags.append(f"positions-ledger guard errored: {type(e).__name__}")


def check_catalyst_overlay_coverage(flags):
    """The Brazil-gap guard (2026-07-06): every BUYISH/HELDISH name must carry catalyst_overlays
    in its edge record — the NON-print dated events above the position (elections, regulatory
    tracks, tax bills, chokepoints), each with a frozen call or an explicit waiver string.
    Company prints are covered by the packs guard; this guard hunts the class we missed on BBD.
    WARN-level: surfaces gaps, does not block."""
    try:
        from desk.verdicts import BUYISH, HELDISH
        led = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text())
        for n in led.get("names", []):
            st = n.get("state") or n.get("verdict")
            if st not in set(BUYISH) | set(HELDISH):
                continue
            rec_path = ROOT / "desk" / "data" / "edge_classifications" / f"{n['ticker']}.json"
            if not rec_path.exists():
                continue
            rec = json.loads(rec_path.read_text())
            if "catalyst_overlays" not in rec:
                flags.append(f"{n['ticker']}: no catalyst_overlays map in the record — the political/macro census hasn't run (Brazil-gap class)")
    except Exception as e:
        flags.append(f"catalyst-overlay guard errored: {type(e).__name__}")


def check_ungraded_calls():
    """Calls whose cat_date passed >2d ago with no resolution — the scoreboard rots without this.
    (2026-07-07: 121 frozen, 0 ever graded — the gauntlet's grades must not repeat that.)"""
    import datetime, json
    from pathlib import Path
    ledger = Path(__file__).resolve().parents[1] / "desk" / "data" / "calibration_ledger.jsonl"
    if not ledger.exists():
        return
    today = datetime.date.today()
    for line in ledger.read_text().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("resolution") or r.get("outcome"):
            continue
        # VOIDED/RESOLVED are terminal — a voided call has no grade owed (HCA/005387 false-flag 2026-07-27)
        if str(r.get("status") or "OPEN").upper() != "OPEN":
            continue
        try:
            cd = datetime.date.fromisoformat(str(r.get("cat_date"))[:10])
        except Exception:
            continue
        if (today - cd).days > 2:
            print(f"  >>> FLAG UNGRADED {r.get('ticker')} {r.get('cat_date')}: cat_date passed "
                  f"{(today-cd).days}d ago w/o resolution — run: python3 -m desk.calibration resolve "
                  f"{r.get('ticker')} FAVORABLE|UNFAVORABLE|MIXED --date {r.get('cat_date')}")


def check_resolution_packs(flags):
    """Every OPEN call within 30 days must have a resolution pack (goal #107) — an unpacked
    imminent catalyst means scramble-latency when the print lands (the AMV0 stale-GO class)."""
    try:
        import datetime as _dt
        packs = json.loads((ROOT / "desk" / "data" / "resolution_packs.json").read_text()).get("packs", {})
        keys = set(packs.keys()) | {k.split("|")[0] + "|" + k.split("|")[1] for k in packs.keys()}
        horizon = (_dt.date.today() + _dt.timedelta(days=30)).isoformat()
        today = _dt.date.today().isoformat()
        for l in (ROOT / "desk" / "data" / "calibration_ledger.jsonl").read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("status") == "OPEN" and today <= (r.get("cat_date") or "") <= horizon:
                k = f"{r['ticker']}|{r['cat_date']}"
                base = f"{r['ticker'].split('.')[0]}|{r['cat_date']}"
                if k not in packs and base not in packs:
                    flags.append(f"{r['ticker']} {r['cat_date']}: OPEN call within 30d WITHOUT a resolution pack")
    except Exception as e:
        flags.append(f"resolution-pack guard errored: {type(e).__name__}")


def check_held_not_in_go(flags):
    """A HELD/OWN ledger name must never appear in the alerts GO list (BRBY 2026-07-02 lesson —
    scanner-path candidates bypassed the verdict; the aggregator now uses the ledger as authoritative,
    and this guard catches any regression)."""
    try:
        from desk.ui.aggregator import alerts
        a = alerts()
        led = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", [])
        held = {n["ticker"] for n in led if (n.get("verdict") or "").upper() in ("HELD", "OWN")}
        leaked = held & {r["ticker"] for r in a.get("go", [])}
        if leaked:
            flags.append(f"HELD name(s) in the GO list: {sorted(leaked)} — entry alert not retired after fill")
    except Exception as e:
        flags.append(f"held-in-go guard errored: {type(e).__name__}")


def check_event_window_frozen(flags):
    """Every ACTIVE event window (a dated FLOW/deal catalyst the watcher will TRADE) must carry a
    frozen calibration call — else the trade executes ungraded and stays off the predictions calendar
    (the ADIG leak, 2026-07-12: DD'd + adjudicated + on the event-window calendar, but never frozen,
    so invisible to the Brier book and the morning-brief 'catalysts landing'). WARN-level."""
    try:
        import datetime as _dt
        today = _dt.date.today().isoformat()
        wins = json.loads((ROOT / "desk" / "data" / "event_windows.json").read_text()).get("windows", [])
        frozen = set()
        for l in (ROOT / "desk" / "data" / "calibration_ledger.jsonl").read_text().splitlines():
            if not l.strip():
                continue
            try:
                r = json.loads(l)
            except Exception:
                continue
            if (r.get("status") or "OPEN").upper() == "OPEN":
                frozen.add((r.get("ticker") or "").upper())
        for w in wins:
            sym = (w.get("symbol") or "").upper()
            end = w.get("end") or ""
            if not sym or (end and end < today):        # skip past/closed windows
                continue
            if sym not in frozen:
                flags.append(f"{sym}: ACTIVE event window {w.get('start')}..{w.get('end')} has NO frozen "
                             f"calibration call — freeze it (desk.freeze_call) or the FLOW trade grades nothing")
    except Exception as e:
        flags.append(f"event-window-frozen guard errored: {type(e).__name__}")


def check_envelope_queue_swept(flags):
    """Band fires on court-ARMED names queue pre-committed order specs (envelope_queue.jsonl) that
    only a LIVE session can stage as AI instructions (cron can't reach the claude.ai connector —
    2026-07-29 design). An un-swept row is a fired gate waiting on plumbing: LOUD flag so every
    session cold-start sees it and stages the instruction for the user's click."""
    try:
        qp = ROOT / "desk" / "data" / "envelope_queue.jsonl"
        if not qp.exists():
            return
        for l in qp.read_text().splitlines():
            if not l.strip():
                continue
            try:
                r = json.loads(l)
            except Exception:
                continue
            if r.get("status") == "QUEUED_AWAITING_SESSION_SWEEP":
                s = r.get("spec", {})
                flags.append(f">>> ENVELOPE QUEUE UNSWEPT: {r.get('ticker')} {s.get('side')} "
                             f"{s.get('qty')}@{s.get('limit')} (band fired {r.get('ts')}) — court+thesis already "
                             f"exist (cited in armed_envelopes.json): run the LIGHT PASS per _sweep_protocol "
                             f"(kill list + instrumentation state + tape sanity, ~5 min, NO re-court), stage the "
                             f"instruction VERBATIM, mark the row SWEPT")
    except Exception as e:
        flags.append(f"envelope-queue guard errored: {type(e).__name__}")


def check_entry_triggers_name_reaction_driver(flags):
    """KER-postmortem RC4 remediation: an entry/flip trigger keyed to an EVENT (a print, a
    catalyst date) must name what the stock TRADES ON (reaction_driver / trades_on), not just
    the operating bar — the ops bar can be met while the stock does the opposite (HCA-STK;
    KER graded -2% 'miss' on the ops bar and rallied 16%). Pure-price bands are exempt."""
    import re as _re
    try:
        ec = ROOT / "desk" / "data" / "edge_classifications"
        event_words = _re.compile(r"print|earnings|H1|H2|Q[1-4]|catalyst|AdCom|PDUFA|report", _re.I)
        for f in sorted(ec.glob("*.json")):
            try:
                rec = json.loads(f.read_text())
            except Exception:
                continue
            if rec.get("verdict_state") not in ("WATCH", "WAIT", "OWNABLE", "STARTER"):
                continue
            entry_txt = " ".join(str(v) for k, v in rec.items() if "entry" in k.lower())
            if not entry_txt or not event_words.search(entry_txt):
                continue                                    # pure-price band — exempt
            blob = json.dumps(rec)
            if "reaction_driver" in blob or "trades_on" in blob:
                continue
            flags.append(f"EVENT-KEYED ENTRY WITHOUT reaction_driver: {rec.get('ticker', f.stem)} — "
                         f"name what the stock trades on, not the ops bar (HCA-STK rule, KER RC4)")
    except Exception as e:
        flags.append(f"reaction-driver guard errored: {type(e).__name__}")


def check_position_docs_complete(flags):
    """v1.6 standard (2026-07-29, user-directed; THESIS_DOC_STANDARD.md): every held or
    staged-awaiting-click name needs (a) an EC record with structured verdict_state, (b) a
    frozen calibration call (the Brier-book entry), (c) a desk/reports doc naming the ticker
    that carries the four-idea frame ('market believes') AND a verification marker. Missing
    leg -> loud flag until fixed. Pre-v1.6 names backfill flag-driven.
    v1.7 (2026-08-22, principal): docs must also carry the pre-mortem block ('what could go
    wrong'); docs dated before 2026-08-22 get WARN-class backfill flags, not CRITICAL."""
    try:
        # working set: HELD states + staged intents awaiting approval
        led = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text())
        held = {n["ticker"] for n in led.get("names", []) if n.get("state") in ("HELD", "OWN")
                or "FILLED" in str(n.get("band_note", "")).upper()}   # 2026-08-02: STARTER-with-fills was invisible (FSBW hole)
        # positions cache is ground truth: any nonzero position joins the working set
        try:
            pc = json.loads((ROOT / "desk" / "ui" / "data" / "positions_cache.json").read_text())
            held |= {p.get("symbol", "").split(".")[0] for p in pc.get("positions", []) if p.get("qty")}
        except Exception:
            pass
        try:
            ep = json.loads((ROOT / "desk" / "data" / "entry_plan.json").read_text())
            for r in ep.get("staged_intents", []):
                if "AWAITING" in str(r.get("status", "")):
                    held.add(r.get("ticker"))
        except Exception:
            pass
        held.discard(None)
        # (b) frozen calls by base ticker
        frozen = set()
        for l in (ROOT / "desk" / "data" / "calibration_ledger.jsonl").read_text().splitlines():
            try:
                r = json.loads(l)
            except Exception:
                continue
            frozen.add((r.get("ticker") or "").split("|")[0].split("-")[0].upper())
        # (c) report docs: ticker mention + frame + verification markers
        docs = {}
        for f in (ROOT / "desk" / "reports").glob("*.html"):
            try:
                t = f.read_text(errors="ignore")
            except Exception:
                continue
            low = t.lower()
            docs[f.name] = (t, ("market believes" in low), ("verif" in low),
                            ("what could go wrong" in low or "pre-mortem" in low))
        ec = ROOT / "desk" / "data" / "edge_classifications"
        for tick in sorted(held):
            base = tick.split(".")[0].upper()
            missing = []
            ecf = ec / f"{tick}.json"
            if not ecf.exists():
                ecf = ec / f"{tick.replace('.', '_')}.json"
            if not ecf.exists() or json.loads(ecf.read_text()).get("verdict_state") is None:
                missing.append("EC/verdict_state")
            if base not in frozen and tick.upper() not in frozen:
                missing.append("Brier entry (frozen call)")
            hit = [n for n, rec in docs.items() if (tick in rec[0] or base in rec[0])]
            framed = [n for n in hit if docs[n][1] and docs[n][2]]
            if not framed:
                missing.append("doc w/ four-idea frame + verification table" + (f" (docs mention it: {hit[:2]})" if hit else " (no doc at all)"))
            if missing:
                flags.append(f"v1.6 DOC-INCOMPLETE {tick}: missing " + " + ".join(missing))
            elif framed and not any(docs[n][3] for n in framed):
                # v1.7 pre-mortem block (2026-08-22): WARN-class backfill for older docs
                flags.append(f"WARN v1.7 PRE-MORTEM MISSING {tick}: doc lacks 'what could go wrong' block (backfill at next touch)")
    except Exception as e:
        flags.append(f"position-docs guard errored: {type(e).__name__}")


def check_resting_orders_have_catalysts(flags):
    """A resting GTC buy into an unmanaged earnings date is an ACCIDENTAL SHORT-VOL POSITION:
    it fills on the drift toward the print, then eats the gap.

    NATR, 2026-08-06 — court-adjudicated STARTER, live GTC buy resting since 07-27, but NO dated
    catalyst in the ledger and no frozen call. Nothing in the system knew a print was coming. The
    order filled at 10:27 ET and the company cut guidance after the close: -17.6%, -$1,080 on a
    $6,993 fill. The loss is trivial; the blind spot is not — 21 other names carried resting buys
    with no dated catalyst at the time.

    Two flags: (1) a live buy order on a name with NO catalyst on the calendar at all, and (2) a
    live buy order with a catalyst inside the window — pull it or consciously accept the gap.
    """
    import datetime as _dt
    import json as _j
    WINDOW_D = 5
    try:
        oc = ROOT / "desk" / "ui" / "data" / "orders_cache.json"
        if not oc.exists():
            return
        orders = _j.loads(oc.read_text()).get("orders", [])
        buys = [o for o in orders if str(o.get("action", "")).upper() == "BUY"
                and str(o.get("status", "")).lower() in ("submitted", "presubmitted")]
        if not buys:
            return
        cal = ROOT / "desk" / "data" / "calibration_ledger.jsonl"
        nearest = {}
        for line in cal.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = _j.loads(line)
            except Exception:
                continue
            if (r.get("status") or "OPEN").upper() != "OPEN" or not r.get("cat_date"):
                continue
            t = str(r.get("ticker") or "").upper().split("-")[0]
            if t and (t not in nearest or r["cat_date"] < nearest[t]):
                nearest[t] = r["cat_date"]

        today = _dt.date.today()
        blind, imminent, stale = set(), [], []
        for o in buys:
            sym = str(o.get("symbol") or "").upper()
            key = sym.split(".")[0]
            d = nearest.get(key) or nearest.get(sym)
            if not d:
                blind.add(sym)
                continue
            try:
                days = (_dt.date.fromisoformat(d) - today).days
            except Exception:
                continue
            if 0 <= days <= WINDOW_D:
                imminent.append(f"{sym}@{o.get('limit')} (catalyst {d}, {days}d)")
            elif days < 0:
                # STALE BAND: the limit was struck on facts that pre-date the catalyst, and the
                # catalyst has now fired. PODD 2026-08-05 and NATR 2026-08-06 are both this shape —
                # a band touch after a guide cut is not a discount, it is an out-of-date reference.
                stale.append(f"{sym}@{o.get('limit')} (catalyst {d}, {-days}d ago)")
        if imminent:
            flags.append("CRITICAL RESTING ORDER INTO A PRINT: " + "; ".join(sorted(set(imminent)))
                         + " — pull the order or consciously accept the gap (the NATR failure)")
        if stale:
            flags.append("CRITICAL STALE BAND — live buy order whose catalyst ALREADY FIRED: "
                         + "; ".join(sorted(set(stale)))
                         + " — re-validate the limit against post-catalyst facts or pull it (PODD/NATR)")
        if blind:
            flags.append(f"RESTING BUY, NO DATED CATALYST ({len(blind)}): " + ", ".join(sorted(blind))
                         + " — an order with no calendar entry cannot be guarded; date the catalyst or drop the order")
    except Exception as e:
        flags.append(f"resting-order catalyst guard errored: {type(e).__name__}")


def check_grader_health(flags):
    """2026-07-31: the headless grader crashed silently for ~36h (AttributeError every run) and 27
    overdue-OPEN calls piled up — caught by the user eyeballing the dashboard, not by the system.
    FLAG when the loop-closer itself is sick: repeated identical errors in its log, or a deep
    overdue-OPEN backlog."""
    import datetime, json, re
    log = ROOT / "desk" / "data" / "headless_grader.out"
    if log.exists():
        tail = log.read_text()[-8000:]
        runs = len(re.findall(r"\[headless_grader\] proposed", tail))
        # OUTPUT-BASED, not error-string-based. The old form counted `(\w+Error)` and "provisional
        # arm skipped" — the signature of the JULY crash. When the failure mode changed to an auth
        # outage the string stopped matching, so this detector's count DECAYED 17 -> 3 -> silent
        # while the real failure rate sat at 100% and 153 consecutive runs graded nothing. Counting
        # errors only ever finds the last outage. Counting OUTPUT finds every one.
        proposed = sum(int(m) for m in re.findall(r"\[headless_grader\] proposed (\d+)", tail))
        if runs >= 6 and proposed == 0:
            kinds = sorted(set(re.findall(r"\((not-logged-in|cli-error|no-verdict|timeout|"
                                          r"no-json-result|bad-verdict-json)\)", tail)))
            flags.append(
                f"CRITICAL GRADER DEAD: {runs} logged runs produced ZERO proposals"
                + (f" [{', '.join(kinds)}]" if kinds else "")
                + " — nothing is closing the calibration loop; read desk/data/headless_grader.out")
    try:
        cal = ROOT / "desk" / "data" / "calibration_ledger.jsonl"
        today = datetime.date.today()
        overdue = 0
        for line in cal.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if (r.get("status") or "OPEN").upper() != "OPEN" or not r.get("cat_date"):
                continue
            try:
                if (today - datetime.date.fromisoformat(r["cat_date"])).days > 2:
                    overdue += 1
            except Exception:
                flags.append(f"GRADER: unparseable cat_date on {r.get('ticker')}")
        if overdue > 10:
            flags.append(f"GRADER BACKLOG: {overdue} calls overdue-OPEN >2d — the loop-closer is not keeping up (cap? crash? re-date failures?)")
    except Exception as e:
        flags.append(f"GRADER health check itself failed: {type(e).__name__}")


def main():
    flags = check()
    check_held_not_in_go(flags)
    check_envelope_queue_swept(flags)
    check_grader_health(flags)
    check_unverified_ledger_drains(flags)
    check_band_touches_dispositioned(flags)
    check_rulings_have_artifacts(flags)
    check_resting_orders_have_catalysts(flags)
    check_entry_triggers_name_reaction_driver(flags)
    check_position_docs_complete(flags)
    check_alert_records_complete(flags)
    check_ui_static_integrity(flags)
    check_new_calls_have_reasoning(flags)
    check_positions_ledger_agree(flags)
    check_resolution_packs(flags)
    check_catalyst_overlay_coverage(flags)
    check_event_window_frozen(flags)
    try:
        from desk.pipeline_invariants import run_all as _pipeline_invariants
        _pipeline_invariants(flags)
    except Exception as e:
        flags.append(f"pipeline-invariants suite errored: {type(e).__name__}: {e}")
    check_ungraded_calls()
    today = datetime.date.today().isoformat()
    print(f"=== CONSISTENCY CHECK {today}  (edge_classifications vs entry_plan vs ledger vs scanner) ===")
    if flags:
        for x in flags:
            print("  " + x)
    else:
        print("  clean — all three stores agree; scanner fresh.")

    # ROUTE THE CRITICAL ONES. Every flag here used to go to a log file and nowhere else, so the
    # July grader crash AND the August auth outage were both caught by the user eyeballing the
    # dashboard rather than by the checker that detected them. A detector whose output nobody
    # reads is not a detector. Cooled to once per 12h per flag-set so it stays readable.
    crit = [x for x in flags if x.startswith("CRITICAL")]
    if crit:
        try:
            import hashlib as _h, json as _j, time as _t
            stamp = ROOT / "desk" / "data" / "consistency_alert_stamp.json"
            key = _h.md5("|".join(sorted(crit)).encode()).hexdigest()[:12]
            prev = {}
            try:
                prev = _j.loads(stamp.read_text())
            except Exception:
                pass
            if prev.get("key") != key or (_t.time() - prev.get("ts", 0)) > 12 * 3600:
                from desk.mailer import event_subject, send_raw
                body = ("Consistency check raised CRITICAL flags:\n\n"
                        + "\n".join(f"  - {x}" for x in crit)
                        + f"\n\n({len(flags)} flags total this run; the rest are in "
                          "desk/data/consistency_check.out)")
                send_raw(event_subject(crit[0]), body)
                stamp.write_text(_j.dumps({"key": key, "ts": _t.time()}))
        except Exception as e:
            print(f"  [consistency_check] CRITICAL alert routing failed: {type(e).__name__}")


def check_packs_have_dates(flags):
    """2026-08-24 (BGSI lesson): a resolution pack with no date is INVISIBLE to every
    date-driven sweep — the gate resolved 8/12 and sat ungraded 12 days. No pack without a date."""
    import re
    try:
        packs = json.loads((ROOT / "desk" / "data" / "resolution_packs.json").read_text()).get("packs", {})
        date_keyed, trigger_keyed = [], []
        for k, v in packs.items():
            if not (isinstance(v, dict) and not v.get("date")):
                continue
            if v.get("lifecycle") not in (None, "open"):
                continue  # voided/unratified sensors carry no obligation
            # date-keyed packs (TICKER|YYYY-MM-DD) missing their date field = the BGSI class: CRITICAL each.
            # trigger-keyed packs (TICKER|PRICE-GATE, X-TRIGGER|weekly) are undated BY DESIGN —
            # still a blind spot (they need review_by dates), but one AGGREGATE line, not 165 CRITICALs
            # (2026-08-28: alarm-fatigue fix; individual flood buried every other flag for 2 days).
            if re.search(r"\|\d{4}-\d{2}-\d{2}$", k):
                date_keyed.append(k)
            elif not v.get("review_by"):
                trigger_keyed.append(k)
        for k in date_keyed:
            flags.append(f"CRITICAL DATELESS-PACK {k}: invisible to all sweeps — fix the date NOW")
        if trigger_keyed:
            flags.append(f"TRIGGER-KEYED PACKS WITHOUT review_by: {len(trigger_keyed)} "
                         f"(e.g. {', '.join(trigger_keyed[:5])}...) — undated tripwires age invisibly; "
                         f"add review_by dates at the next pack sweep")
    except Exception as e:
        flags.append(f"pack-date guard errored: {type(e).__name__}")


def check_unverified_ledger_drains(flags):
    """2026-08-26: the R1.13 estimation loop stalled silently — courts filed unverified rows
    faithfully for 5 days while ZERO were run down to ranges (26 OPEN, estimates last written
    8/21). The ledger is a WORK QUEUE, not an archive; this flags when it only ever grows.
    Rows carry 'filed' dates as of 2026-08-26."""
    import datetime, json
    try:
        p = ROOT / "desk" / "data" / "unverified_ledger.json"
        d = json.loads(p.read_text())
        rows = d if isinstance(d, list) else d.get("items", [])
        today = datetime.date.today()
        stale = [r for r in rows if r.get("status") == "OPEN" and r.get("filed")
                 and r.get("drain_owed", True)
                 and (today - datetime.date.fromisoformat(r["filed"])).days > 5]
        if len(stale) >= 5:
            tk = sorted({r.get("ticker", "?") for r in stale})
            flags.append(f"UNVERIFIED-LEDGER STALLED: {len(stale)} OPEN rows older than 5d with no "
                         f"estimate written back ({', '.join(tk[:8])}{'...' if len(tk) > 8 else ''}) — "
                         f"R1.13 says run them down to RANGES; dispatch a drain session")
    except Exception as e:
        flags.append(f"unverified-ledger drain check errored: {type(e).__name__}")


def check_band_touches_dispositioned(flags):
    """2026-08-26 (principal question: 'are band touches automatically being courted?' — no,
    by design; this closes the gap that made non-armed touches depend on session attention).
    A fired band (band_watch_state armed=False w/ fired_date) must gain a DISPOSITION within
    2 days: a dated notes_log entry on the ledger row on/after the fire date (cause-check ran,
    court enqueued, band re-pointed, or explicitly passed). Silence = the ONON failure mode."""
    import datetime, json, re
    try:
        st = json.loads((ROOT / "desk" / "data" / "band_watch_state.json").read_text())
        led = {n["ticker"]: n for n in
               json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text())["names"]}
        today = datetime.date.today()
        undisp = []
        for tick, rec in st.items():
            if not isinstance(rec, dict) or rec.get("armed", True) or "fired_date" not in rec:
                continue
            fired = datetime.date.fromisoformat(rec["fired_date"])
            if (today - fired).days < 2:
                continue
            notes = led.get(tick, {}).get("notes_log", [])
            ok = False
            for n in notes:
                m = re.match(r"(\d{4}-\d{2}-\d{2})", str(n))
                if m and datetime.date.fromisoformat(m.group(1)) >= fired:
                    ok = True
                    break
            if not ok:
                undisp.append(f"{tick} (fired {rec['fired_date']} @ {rec.get('fired_at')})")
        if undisp:
            flags.append("BAND TOUCHES UNDISPOSITIONED >2d: " + "; ".join(undisp)
                         + " — run the cause-check and note the ledger row (court / re-point / pass)")
    except Exception as e:
        flags.append(f"band-touch disposition check errored: {type(e).__name__}")


def check_rulings_have_artifacts(flags):
    """2026-08-28 (rubber-stamp incident): ten queue rows were marked DONE/KILLED with no
    adjudication artifact, no commit, non-doctrine verdict labels. A terminal transition from
    ADJUDICATE without an artifact path is a rubber-stamp BY DEFINITION - flag every one."""
    import json
    try:
        q = json.loads((ROOT / "desk" / "data" / "court_queue.json").read_text())
        items = q.get("items", q) if isinstance(q, dict) else q
        bad = []
        for it in items:
            if it.get("stage") not in ("DONE", "KILLED"):
                continue
            h = it.get("history", [])
            for e in reversed(h):
                if e.get("to") in ("DONE", "KILLED"):
                    # scope to transitions after 2026-08-25: the artifact-path convention's start.
                    # Earlier rows were session-adjudicated legitimately but never recorded paths
                    # (guard's first run flagged ~dozens of those - archaeology, not rubber-stamps).
                    if (e.get("from") == "ADJUDICATE" and not e.get("artifact")
                            and str(e.get("utc") or "") >= "2026-08-25"):
                        bad.append(it.get("ticker"))
                    break
        if bad:
            flags.append(f"CRITICAL RUBBER-STAMP RULINGS (terminal from ADJUDICATE, no artifact): "
                         f"{', '.join(sorted(set(bad))[:10])} - revert and re-adjudicate at Fable tier")
    except Exception as e:
        flags.append(f"ruling-artifact guard errored: {type(e).__name__}")


# Keep this guard LAST. 2026-09-11: it sat above four later-appended check_* functions, so
# `python3 -m desk.consistency_check` died with NameError(check_unverified_ledger_drains)
# before printing a single flag — the checker itself was the silent failure it exists to catch.
if __name__ == "__main__":
    main()
