"""pipeline_monitor — email monitoring for the hardened pipelines (PRD RX.4/RX.5).

Two channels through desk.mailer (the single SMTP rail):
  IMMEDIATE — a NEW CRITICAL invariant breach (rate-limited: one email per breach-key
              per 24h; the grader-alarm lesson — an alarm that fires hourly is muted by
              its reader within a day)
  WEEKLY    — Monday digest: metric trends, defect aging, stale-pack counts, backlog burn-down

Silence is never success: if the metrics snapshot is missing or stale (>36h), that is
itself an IMMEDIATE breach (a dead metrics cron must not read as a healthy pipeline).

  python3 -m desk.pipeline_monitor            # hourly cron
  python3 -m desk.pipeline_monitor --digest   # force the digest now
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "desk" / "data"
STATE = DATA / "pipeline_monitor_state.json"


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _load_state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"sent": {}, "last_digest": None}


def _save_state(st: dict):
    STATE.write_text(json.dumps(st, indent=1))


def _breach_key(flag: str) -> str:
    """Stable identity for a flag so the rate limit survives wording jitter:
    class + first token that looks like a name/key."""
    parts = flag.split(":", 2)
    cls = parts[0].replace("CRITICAL ", "").strip()
    subject = parts[1].strip().split()[0] if len(parts) > 1 and parts[1].strip() else ""
    return f"{cls}|{subject}"


def brief_dead_flags(out_text: str, today: datetime.date) -> list[str]:
    """Pure check on nightly_brief.out: last 'ON DECK for' header >1.5 days old, or a
    Traceback after the last header, = the brief is dead. Silence must not read as health."""
    import re
    hdrs = re.findall(r"ON DECK for \w+ (\d{4}-\d{2}-\d{2})", out_text)
    last_hdr = datetime.date.fromisoformat(hdrs[-1]) if hdrs else None
    age = (today - last_hdr).days if last_hdr else 99
    tail_tb = "Traceback" in out_text[-4000:] and (
        not hdrs or out_text.rfind("Traceback") > out_text.rfind("ON DECK for"))
    if age > 1.5 or tail_tb:
        return [f"CRITICAL BRIEF-DEAD: morning brief last shipped {last_hdr} ({age}d ago)"
                f"{' — last run ended in a Traceback' if tail_tb else ''}; "
                f"run python3 -m desk.morning_brief and read the traceback"]
    return []


def collect_criticals() -> list[str]:
    from desk.pipeline_invariants import run_all
    flags = run_all()
    crits = [f for f in flags if f.startswith("CRITICAL")]
    # staleness of the metrics snapshot is itself a breach (RX.4)
    mp = DATA / "pipeline_metrics.json"
    fresh = False
    try:
        snaps = json.loads(mp.read_text()).get("snapshots", [])
        last = max(s["date"] for s in snaps)
        fresh = (_now().date() - datetime.date.fromisoformat(last)).days <= 1.5
    except Exception:
        pass
    if not fresh:
        crits.append("CRITICAL METRICS-STALE: pipeline_metrics.json missing or >36h old — "
                     "the metrics cron is dead; silence must not read as health")
    # the morning brief itself must SHIP (2026-09-09: it crashed on every run from 07-22 to
    # 09-08 — 36 tracebacks, zero on-deck emails for 7 weeks, nothing flagged it). Read the
    # last header date in nightly_brief.out; >1.5 days old or a trailing Traceback = dead.
    try:
        crits.extend(brief_dead_flags((DATA / "nightly_brief.out").read_text(errors="ignore"),
                                      _now().date()))
    except Exception as e:
        crits.append(f"CRITICAL BRIEF-BLIND: cannot read nightly_brief.out ({type(e).__name__})")
    # fungibility gauge breaches (sovereign-barbell sleeve 3) — route ALARM-level premiums
    try:
        fs = json.loads((DATA / "fungibility_state.json").read_text()).get("latest", {})
        for r in fs.get("pairs", []):
            if abs(r.get("premium", 0)) >= 0.05:
                crits.append(f"CRITICAL FUNGIBILITY-BREAK: {r['pair']} premium {r['premium']:+.2%} "
                             f"(asof {fs.get('asof')}) — capital-control pricing candidate; cause-check first")
    except Exception:
        pass
    # CRCL court gate (usdc_supply_watch state)
    try:
        us = json.loads((DATA / "usdc_supply_state.json").read_text())
        if us.get("streak_days", 0) >= 21:
            crits.append(f"CRITICAL CRCL-GATE-FIRED: USDC >= $72B for {us['streak_days']} consecutive days — "
                         f"court gate met (verify the 9/16 cluster resolved before any starter)")
    except Exception:
        pass
    # casting-capacity flags (HONA flip-evidence sensor)
    try:
        cs = json.loads((DATA / "casting_capacity_state.json").read_text())
        for f in cs.get("latest_flags", []):
            crits.append("CRITICAL " + f)
    except Exception:
        pass
    # deck-proposed immediate entries awaiting session staging (RE.7 / the FIGR gap)
    # NICE lesson (2026-09-03): these rows are PRE-adjudication proposals. A later
    # terminal adjudication supersedes the row (the ruling may be NO entry) — never
    # re-fire it as staging-required; and a row pending >72h is a stale decision owed
    # a session review at a re-polled price, not an "immediate entry".
    try:
        spp = json.loads((DATA / "staging_plan.json").read_text())
        qitems = {}
        try:
            qitems = {r["ticker"]: r for r in
                      json.loads((DATA / "court_queue.json").read_text())["items"]}
        except Exception:
            pass
        now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
        for a in spp.get("actions", []):
            if a.get("action") != "STAGING-REQUIRED" or a.get("status") != "pending_session":
                continue
            it = qitems.get(a["ticker"])
            adj = [h for h in (it or {}).get("history", [])
                   if h.get("to") in ("DONE", "KILLED") and h.get("utc", "") > a.get("planned_utc", "")]
            if adj:
                crits.append(f"WARN STALE-STAGING-SUPERSEDED: {a['ticker']} — adjudication "
                             f"{adj[-1]['utc']} postdates this provisional row; close it out, "
                             f"do NOT stage from a pre-adjudication proposal")
                continue
            age_h = 0
            try:
                age_h = (datetime.datetime.fromisoformat(now[:-1])
                         - datetime.datetime.fromisoformat(a["planned_utc"][:-1])).total_seconds() / 3600
            except Exception:
                pass
            if age_h > 72:
                crits.append(f"WARN STALE-STAGING-REQUIRED: {a['ticker']} {a.get('side')} "
                             f"~{a.get('approx_price')} ({age_h/24:.0f}d old) — adjudication owed at a "
                             f"RE-POLLED live price, not an immediate entry")
            else:
                crits.append(f"CRITICAL STAGING-REQUIRED: {a['ticker']} {a.get('side')} "
                             f"~{a.get('approx_price')} ({a.get('size_pct_of_book')}% of book) — a court "
                             f"proposed an immediate entry and NO instruction is staged; session must stage "
                             f"for principal approval")
    except Exception:
        pass
    # drain-before-stage invariant (GIII lesson 2026-09-03): a court starter staged while the
    # deck's "what remains unverified" list is undrained is a PRD violation — every staged
    # intent must have a same-or-later-dated drain record in unverified_ledger.
    try:
        oi = json.loads((DATA / "order_intents.json").read_text())
        ul = json.loads((DATA / "unverified_ledger.json").read_text())
        ul_txt = json.dumps(ul)
        open_drainable = {}
        for r in ul.get("items", []):
            if isinstance(r, dict) and r.get("status") == "OPEN" and r.get("drainable_now"):
                open_drainable[r.get("ticker")] = open_drainable.get(r.get("ticker"), 0) + 1
        for a in oi.get("expected_resting", []):
            tk, staged = a.get("ticker"), str(a.get("staged_utc", ""))[:10]
            if not tk or staged < "2026-09-03":
                continue
            if open_drainable.get(tk):
                crits.append(f"CRITICAL DRAIN-BEFORE-STAGE: {tk} staged {staged} with "
                             f"{open_drainable[tk]} OPEN drainable-now item(s) in "
                             f"unverified_ledger — drain them or reclassify as time-gated")
            elif f'"{tk}"' not in ul_txt.replace("'", '"'):
                crits.append(f"CRITICAL DRAIN-BEFORE-STAGE: {tk} staged {staged} with no drain "
                             f"record in unverified_ledger — run the drain pass or document why "
                             f"every open item is time-gated")
    except Exception:
        pass
    # bare-gate sweep (RE.8 / the OPRT miss): a WAIT/print-conditional verdict whose
    # condition has no sensor (no price alert AND no open pack) resolved invisibly —
    # OPRT +42% before anyone looked. Gate without a sensor = decoration.
    try:
        rl = json.loads((DATA / "research_ledger.json").read_text())
        packs = json.loads((DATA / "resolution_packs.json").read_text()).get("packs", {})
        open_pack_tickers = {k.split("|")[0] for k, p in packs.items()
                             if isinstance(p, dict) and p.get("lifecycle") == "open"}
        for n in rl.get("names", []):
            blob = ((n.get("conviction") or "") + " " + (n.get("entry_plan") or "")).lower()
            conditional = ("print-cond" in blob or "print-conditional" in blob
                           or ("conditional" in blob and "print" in blob)
                           or "re-court" in blob and "print" in blob)
            if n.get("state") in ("WAIT", "WATCH") and conditional \
               and not n.get("alert_below") and n.get("ticker") not in open_pack_tickers:
                crits.append(f"CRITICAL BARE-GATE: {n['ticker']} is {n['state']}/print-conditional "
                             f"with NO alert and NO open pack — the gate can resolve invisibly "
                             f"(OPRT pattern); arm a pack or alert at next session")
    except Exception as e:
        crits.append(f"CRITICAL BARE-GATE-BLIND: sweep failed ({type(e).__name__}: {e})")
    # resting-order × print-date sweep (NATR postmortem — a court rung filled into a print)
    try:
        from desk.order_hygiene import sweep
        crits.extend(sweep())
    except Exception as e:
        crits.append(f"CRITICAL ORDER-HYGIENE-BLIND: sweep itself failed ({type(e).__name__}: {e}) — "
                     f"the resting book is unguarded")
    return crits


def packs_due(window_days: int = 2) -> list[str]:
    """Informational notices for packs coming DUE (today..+window). The CRITICAL stale-pack
    breach is the backstop AFTER a date passes ungraded; this is the advance notice the
    AVAP question exposed as missing — a dated gate should email BEFORE it fires."""
    import re
    try:
        packs = json.loads((DATA / "resolution_packs.json").read_text()).get("packs", {})
    except Exception:
        return []
    today = _now().date()
    out = []
    for key, p in packs.items():
        if "|" not in key or not isinstance(p, dict):
            continue
        if p.get("lifecycle") in ("adjudicated", "branch_executed", "expired"):
            continue
        d = key.rsplit("|", 1)[1]
        if not re.match(r"\d{4}-\d{2}-\d{2}$", d):
            continue
        try:
            dd = datetime.date.fromisoformat(d)
        except ValueError:
            continue
        if 0 <= (dd - today).days <= window_days:
            out.append(f"PACK DUE {d}: {key} — {str(p.get('adjudication',''))[:160]}")
    return out


def immediate_pass(dry_run: bool = False) -> list[str]:
    st = _load_state()
    crits = collect_criticals() + packs_due()
    now_iso = _now().isoformat()
    fresh_keys = []
    for f in crits:
        k = _breach_key(f)
        last = st["sent"].get(k)
        if last and (_now() - datetime.datetime.fromisoformat(last)).total_seconds() < 24 * 3600:
            continue
        fresh_keys.append((k, f))
    if fresh_keys and not dry_run:
        from desk import mailer
        PRINCIPAL_CLASSES = ("STAGING-PLAN-UNSWEPT", "not-logged-in", "AUTH",
                             "PULL-BEFORE-PRINT", "TRIM-RIDES-PRINT")
        def _route(f):
            who = "PRINCIPAL-ACTION" if any(c in f for c in PRINCIPAL_CLASSES) else "DESK-ACTION"
            return f"[{who}] {f}"
        body = ("Routing: PRINCIPAL-ACTION = needs your click (IBKR submit/cancel, gateway/2FA). "
                "DESK-ACTION = the desk's backlog — ignore, or tell a session to burn it.\n\n"
                + "\n".join(_route(f) for _, f in fresh_keys))
        n_crit = sum(1 for _, f in fresh_keys if f.startswith("CRITICAL"))
        n_due = len(fresh_keys) - n_crit
        subj = " + ".join(x for x in [f"{n_crit} CRITICAL breach(es)" if n_crit else "",
                                      f"{n_due} pack(s) coming due" if n_due else ""] if x)
        ok = mailer.send_raw(
            mailer.event_subject(subj or "pipeline notices"),
            body + "\n\n(Each breach-key is rate-limited to one email per 24h; "
                   "full state: desk/data/unwired_tripwires.json, python3 -m desk.pipeline_invariants)")
        if ok:
            for k, _ in fresh_keys:
                st["sent"][k] = now_iso
            _save_state(st)
    elif fresh_keys:
        for k, _ in fresh_keys:
            st["sent"][k] = now_iso
    return [f for _, f in fresh_keys]


def _trend(snaps: list, path: list[str]) -> str:
    vals = []
    for s in snaps[-8:]:
        v = s
        for k in path:
            v = (v or {}).get(k)
        vals.append(v)
    return " → ".join("–" if v is None else str(v) for v in vals)


def digest(dry_run: bool = False) -> str:
    snaps = []
    try:
        snaps = json.loads((DATA / "pipeline_metrics.json").read_text()).get("snapshots", [])
        snaps.sort(key=lambda s: s["date"])
    except Exception:
        pass
    cur = snaps[-1] if snaps else {}
    p1, p3, cross = cur.get("p1", {}), cur.get("p3", {}), cur.get("cross", {})
    sections = [
        ("P1 orphan verification",
         f"WATCH wired: {p1.get('watch_wired')}/{p1.get('watch_count')} ({p1.get('watch_wired_pct')}%) — "
         f"target 100%\ntrend: {_trend(snaps, ['p1', 'watch_wired_pct'])}\n"
         f"open screen defects: {p1.get('defects_open')}\n"
         + "\n".join(f"  {b}: {v['advance']}/{v['n']} advanced ({v['advance_rate']:.0%})"
                     for b, v in (p1.get("batches") or {}).items())),
        ("P2 class dislocation", json.dumps(cur.get("p2", {}))),
        ("P3 trigger conversion",
         f"stale packs: {p3.get('packs_stale')}/{p3.get('packs_past_date')} past-date — target 0\n"
         f"trend: {_trend(snaps, ['p3', 'packs_stale'])}\n"
         f"adjudication p90: {p3.get('adjudication_p90_days')}d (graded n={p3.get('graded_n')})\n"
         f"unclassified held cost: ${p3.get('unclassified_cost_usd', 0):,} "
         f"({len(p3.get('unclassified_held', []))} names)"),
        ("Tripwire backlog",
         f"strict (batch/court, per-name CRITICAL): {cross.get('unwired_strict')}\n"
         f"tail (screen/rundown, weekly sweep): {cross.get('unwired_tail')}"),
    ]
    plain = "\n\n".join(f"== {t} ==\n{b}" for t, b in sections)
    if not dry_run:
        from desk import mailer
        mailer.send(mailer.event_subject("weekly pipeline digest"), sections,
                    footer="pipeline_monitor --digest · metrics: desk/data/pipeline_metrics.json")
        st = _load_state()
        st["last_digest"] = _now().isoformat()
        _save_state(st)
    return plain


def main():
    force_digest = "--digest" in sys.argv
    dry = "--dry-run" in sys.argv
    sent = immediate_pass(dry_run=dry)
    print(f"[pipeline_monitor] immediate: {len(sent)} new breach(es) "
          f"{'(dry-run, not emailed)' if dry else 'emailed' if sent else ''}")
    st = _load_state()
    is_monday = _now().weekday() == 0
    last = st.get("last_digest")
    digest_due = force_digest or (is_monday and (not last or
                 (_now() - datetime.datetime.fromisoformat(last)).days >= 6))
    if digest_due:
        out = digest(dry_run=dry)
        print("[pipeline_monitor] digest sent" if not dry else out)


if __name__ == "__main__":
    main()
