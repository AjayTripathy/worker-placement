"""pipeline_invariants — the S4 invariant checks (PIPELINE_ARCHITECTURE §S4, PRD R3.1).

Each function appends human-readable flags; breaches of hard invariants are prefixed
CRITICAL so consistency_check's existing routing (12h-cooled email) escalates them.
Kept separate from consistency_check for testability; wired into its main().

The invariants exist against specific failures:
  I1  WATCH/STAGE2 without a future-dated pack  -> the STEM.L +26.6% uncaught class
  I2  held position without edge classification -> the $133k attribution blind spot
  I3  pack past its date, never adjudicated     -> triggers that rot instead of firing
  I4  trap-batch verdict absent from the ledger -> batch docs diverging from state
  I5  open screen defect >30d                   -> the Tokmanni->KSL recurrence class
  I6  court verdict without a pitch doc         -> PRD RC invariant (from 2026-08-06)
  I7  staging plan unexecuted >24h              -> Rung 0.5 plans rotting in the file
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "desk" / "data"
EC_DIR = DATA / "edge_classifications"

# names that never need an edge classification (cash-likes / ballast by doctrine)
UNCLASSIFIED_WAIVERS = {"SGOV"}
PITCH_DOC_EPOCH = "2026-08-06"          # PRD RC invariant applies to courts on/after this date


def _today() -> datetime.date:
    return datetime.date.today()


def _norm(sym: str) -> str:
    return re.split(r"[.\s]", str(sym or "").strip())[0].upper()


def _load(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


# ---------- I1: every PIPELINE-PROMOTED WATCH / STAGE2 name has a FUTURE-dated pack ----------
# Precision scope (recall-floor lesson: key off the attribute carrying the obligation, not the
# token WATCH): the pack obligation attaches to names a batch/court/scan PROMOTED — their WATCH
# is a verdict with a named tripwire. Passive census/watchlist rows (source=None etc.) are
# legitimately packless. Severity split (alarm-fatigue lesson: 149 CRITICALs = zero CRITICALs):
# STRICT sources (trap batches, courts, numbered scans — tripwires are named in the verdict) get
# per-name CRITICAL; the broader promoted tail aggregates to ONE line + a work-queue file.
_STRICT_SRC = re.compile(r"trap.?batch|court|scan\d", re.I)
_PROMOTED_SRC = re.compile(r"trap.?batch|court|scan\d|screen|batch\d|rundown|\bdd\b|two-mode", re.I)
UNWIRED_QUEUE = DATA / "unwired_tripwires.json"


def check_watch_has_future_pack(flags: list):
    try:
        rl = _load(DATA / "research_ledger.json") or {}
        packs = (_load(DATA / "resolution_packs.json") or {}).get("packs", {})
        today = _today().isoformat()
        future_fams = set()
        for key in packs:
            if "|" not in key:
                continue
            name, d = key.rsplit("|", 1)
            if re.match(r"\d{4}-\d{2}-\d{2}$", d) and d >= today:
                future_fams.add(_norm(re.sub(r"-(REVIEW|CXL|EXIT|TRIM|OPS|RXN|PM|STK)$", "", name)))
        strict_hits, tail = [], []
        for n in rl.get("names", []):
            v = str(n.get("verdict", "")).upper()
            st = str(n.get("state", "")).upper()
            if not (v.startswith("WATCH") or v == "STAGE2-CANDIDATE" or st == "WATCH"):
                continue
            src = str(n.get("source") or "")
            if not _PROMOTED_SRC.search(src):
                continue                      # passive census row — no tripwire obligation
            if _norm(n["ticker"]) in future_fams:
                continue
            row = {"ticker": n["ticker"], "verdict": v or st, "source": src[:60]}
            (strict_hits if _STRICT_SRC.search(src) else tail).append(row)
        for r in strict_hits[:12]:
            flags.append(f"CRITICAL UNWIRED-TRIPWIRE: {r['ticker']} ({r['verdict'][:24]}, source={r['source'][:40]}) "
                         f"has NO future-dated resolution pack — the STEM.L class; wire the gate")
        if len(strict_hits) > 12:
            flags.append(f"CRITICAL UNWIRED-TRIPWIRE: +{len(strict_hits)-12} more batch/court-promoted names "
                         f"without packs (full queue: desk/data/unwired_tripwires.json)")
        if tail:
            flags.append(f"unwired-tripwire BACKLOG: {len(tail)} promoted WATCH names without packs "
                         f"(full queue: desk/data/unwired_tripwires.json) — burn down via the weekly sweep")
        import json as _j
        UNWIRED_QUEUE.write_text(_j.dumps(
            {"asof": _today().isoformat(), "strict": strict_hits, "tail": tail}, indent=1))
    except Exception as e:
        flags.append(f"watch-pack invariant errored: {type(e).__name__}: {e}")


# ---------- I2: every held STK has an edge classification (or waiver) ----------
def check_held_classified(flags: list):
    try:
        pc = _load(ROOT / "desk" / "ui" / "data" / "positions_cache.json") or {}
        missing, empty = [], []
        for p in pc.get("positions", []):
            if p.get("sec_type") != "STK" or float(p.get("qty") or 0) <= 0:
                continue
            fam = _norm(p["symbol"])
            if fam in UNCLASSIFIED_WAIVERS:
                continue
            cands = [EC_DIR / f"{p['symbol']}.json", EC_DIR / f"{fam}.json"]
            cands += list(EC_DIR.glob(f"{fam}.*.json")) + list(EC_DIR.glob(f"{fam}_*.json"))
            rec = next((r for r in (_load(c) for c in cands if c.exists()) if r), None)
            if rec is None:
                missing.append(p["symbol"])
            elif not any(k in rec for k in ("edge_explainer", "classification", "edge_type", "unclassified_ok", "edge")):  # "edge" = legacy field name (pre-2026-08-31 records); tag backfill queued
                empty.append(p["symbol"])
        if missing:
            flags.append(f"CRITICAL UNCLASSIFIED-HELD: {len(missing)} held names with NO edge classification "
                         f"({', '.join(sorted(missing)[:8])}{'…' if len(missing) > 8 else ''}) — attribution is "
                         f"blind there; run the classification sweep")
        for t in empty:
            flags.append(f"held {t}: edge file exists but carries no edge_type/classification — classify or waive")
    except Exception as e:
        flags.append(f"held-classified invariant errored: {type(e).__name__}: {e}")


# ---------- I3: packs past their date get adjudicated within 72h ----------
def _resolved_keys() -> set:
    """(fam, date) pairs the calibration ledger has RESOLVED/VOID — the real adjudication
    signal (packs themselves carry no lifecycle field yet; graded_* keys are the older mark)."""
    out = set()
    p = DATA / "calibration_ledger.jsonl"
    if not p.exists():
        return out
    for line in p.read_text().splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(r.get("status", "")).upper() in ("RESOLVED", "VOID", "VOIDED"):
            out.add((_norm(r.get("ticker", "")), str(r.get("cat_date", ""))))
    return out


def check_stale_packs(flags: list):
    try:
        packs = (_load(DATA / "resolution_packs.json") or {}).get("packs", {})
        resolved = _resolved_keys()
        cutoff = (_today() - datetime.timedelta(days=3)).isoformat()
        stale = []
        for key, p in packs.items():
            if "|" not in key or not isinstance(p, dict):
                continue
            name, d = key.rsplit("|", 1)
            if not re.match(r"\d{4}-\d{2}-\d{2}$", d) or d >= cutoff:
                continue
            if p.get("lifecycle") in ("adjudicated", "branch_executed", "expired"):
                continue
            if any(k.startswith("graded_") for k in p):
                continue
            fam = _norm(re.sub(r"-(REVIEW|CXL|EXIT|TRIM|OPS|RXN|PM|STK|MFT|MRE|RAISE|PREPRINT)$", "", name))
            # ledger cat_date and pack date can differ by a few days (re-dates) — match fam+near-date
            if any(rf == fam and abs((datetime.date.fromisoformat(d) -
                                      datetime.date.fromisoformat(rd)).days) <= 5
                   for rf, rd in resolved if re.match(r"\d{4}-\d{2}-\d{2}$", rd)):
                continue
            stale.append((key, (_today() - datetime.date.fromisoformat(d)).days))
        # severity split: individually CRITICAL only for the worst (>7d); one aggregate line for the rest
        worst = [s for s in stale if s[1] > 7]
        recent = [s for s in stale if s[1] <= 7]
        for key, age in sorted(worst, key=lambda x: -x[1])[:10]:
            flags.append(f"CRITICAL STALE-PACK: {key} is {age}d past its date with no adjudication in the "
                         f"calibration ledger — grade it or expire it (miss_type: late_adjudication)")
        if len(worst) > 10:
            flags.append(f"CRITICAL STALE-PACK: +{len(worst)-10} more packs >7d unadjudicated (run the grader backlog)")
        if recent:
            flags.append(f"stale-pack (within grace-window escalation): {len(recent)} packs 3-7d past date "
                         f"ungraded — the grader should clear these on its next pass")
    except Exception as e:
        flags.append(f"stale-pack invariant errored: {type(e).__name__}: {e}")


# ---------- I4: every trap-batch verdict name exists in the ledger ----------
def check_batch_docs_in_ledger(flags: list):
    try:
        rl = _load(DATA / "research_ledger.json") or {}
        led = {_norm(n["ticker"]) for n in rl.get("names", [])}
        pat = re.compile(r"^## .+\(([A-Z0-9.\-]+),", re.M)
        for doc in ROOT.glob("verticals/*/global/data/*TRAP_BATCH*.md"):
            for tkr in pat.findall(doc.read_text()):
                if _norm(tkr) not in led:
                    flags.append(f"CRITICAL BATCH-LEDGER-DIVERGENCE: {tkr} has a verdict in {doc.name} "
                                 f"but is NOT in the research ledger — promotion step was skipped")
    except Exception as e:
        flags.append(f"batch-ledger invariant errored: {type(e).__name__}: {e}")


# ---------- I5: open screen defects >30d surface weekly ----------
def check_defect_ledger_aging(flags: list):
    try:
        from desk.store import read_jsonl
        rows = read_jsonl(DATA / "screen_defects.jsonl")
        cutoff = (_today() - datetime.timedelta(days=30)).isoformat()
        for r in rows:
            if r.get("status") == "open" and r.get("date", "9999") < cutoff:
                flags.append(f"screen-defect OPEN >30d: [{r['screen']}] {r['defect'][:90]}… "
                             f"(filed {r['date']}) — fix it or mark wont_fix with a reason")
            # PRD R1.7: fix_landed without e2e evidence is an open defect for every purpose.
            # Append-only ledger: a LATER fix_verified_e2e row whose `supersedes` prefix
            # matches this row's defect text clears it.
            if r.get("status") == "fix_landed" and not r.get("e2e_verified"):
                sup = [x for x in rows
                       if x.get("status") == "fix_verified_e2e"
                       and x.get("supersedes")
                       and r["defect"].startswith(x["supersedes"][:40])]
                if not sup:
                    flags.append(f"CRITICAL FIX-NOT-E2E-VERIFIED: [{r['screen']}] {r['defect'][:80]}… — "
                                 f"fix landed but the screen never re-ran end-to-end with the caught "
                                 f"names verified (PRD R1.7); run the screen and stamp e2e_verified")
    except Exception as e:
        flags.append(f"defect-aging invariant errored: {type(e).__name__}: {e}")


# ---------- I6: court verdicts (from the epoch) carry a pitch doc ----------
def check_court_has_pitch_doc(flags: list):
    try:
        dd = ROOT / "dd_reports"
        for f in sorted(EC_DIR.glob("*.json")):
            rec = _load(f)
            if not rec or not rec.get("court") and "court" not in json.dumps(rec)[:2000].lower():
                continue
            cdate = str(rec.get("date") or rec.get("court_date") or "")
            if not cdate or cdate < PITCH_DOC_EPOCH:
                continue
            fam = _norm(rec.get("ticker") or f.stem)
            decks = ROOT / "desk" / "reports"       # deck_writer conveyor output (2026-08-09)
            if (not list(dd.glob(f"pitch_{fam}*.md")) and not list(dd.glob(f"pitch_{f.stem}*.md"))
                    and not list(decks.glob(f"{fam}_PITCH_DECK_*.md"))
                    and not list(decks.glob(f"{f.stem}_PITCH_DECK_*.md"))):
                flags.append(f"CRITICAL COURT-WITHOUT-PITCH: {fam} courted {cdate} with no "
                             f"dd_reports/pitch_{fam}_*.md or desk/reports/{fam}_PITCH_DECK_*.md "
                             f"— PRD RC invariant (courts from {PITCH_DOC_EPOCH})")
    except Exception as e:
        flags.append(f"pitch-doc invariant errored: {type(e).__name__}: {e}")


# ---------- I8: courted names with dated reopen/kill conditions need packs ----------
def check_reopen_conditions_wired(flags: list):
    """The AVAP lesson (2026-08-06): a DECLINE's reopen conditions written as prose in the
    edge file are the STEM class in a new costume — I1 only polices WATCH/STAGE2. Soft flag
    (not CRITICAL): any edge file with kill/reopen trigger lists and NO future-dated pack."""
    try:
        packs = (_load(DATA / "resolution_packs.json") or {}).get("packs", {})
        today = _today().isoformat()
        future_fams = set()
        for key in packs:
            if "|" in key:
                name, d = key.rsplit("|", 1)
                if re.match(r"\d{4}-\d{2}-\d{2}$", d) and d >= today:
                    future_fams.add(_norm(re.sub(r"-[A-Z0-9]+$", "", name)))
        for f in sorted(EC_DIR.glob("*.json")):
            rec = _load(f)
            if not rec or not rec.get("court"):
                continue
            trig = rec.get("kill_reopen_triggers") or rec.get("kill_triggers")
            if not trig:
                continue
            fam = _norm(rec.get("ticker") or f.stem)
            if fam not in future_fams:
                flags.append(f"courted {fam} has {len(trig)} kill/reopen trigger(s) in prose but "
                             f"NO future-dated pack — wire the dated ones (the AVAP lesson)")
    except Exception as e:
        flags.append(f"reopen-wired invariant errored: {type(e).__name__}: {e}")


# ---------- I7: staging plans get executed within 24h ----------
def check_staging_plan_executed(flags: list):
    try:
        plan = _load(DATA / "staging_plan.json")
        if not plan:
            return
        now = datetime.datetime.utcnow()
        for a in plan.get("actions", []):
            if a.get("status") != "planned":
                continue
            ts = a.get("planned_utc", "")
            try:
                age_h = (now - datetime.datetime.fromisoformat(ts.rstrip("Z"))).total_seconds() / 3600
            except ValueError:
                age_h = 999
            if age_h > 24:
                flags.append(f"CRITICAL STAGING-PLAN-UNSWEPT: {a.get('action')} {a.get('ticker')} "
                             f"{a.get('side')} {a.get('qty')}@{a.get('limit')} planned {age_h:.0f}h ago and "
                             f"never executed through the connector lane — sweep it or expire it")
    except Exception as e:
        flags.append(f"staging-plan invariant errored: {type(e).__name__}: {e}")


def check_court_queue(flags: list):
    try:
        from desk.court_queue import check_queue_health
        check_queue_health(flags)
    except Exception as e:
        flags.append(f"court-queue invariant errored: {type(e).__name__}: {e}")


def check_quality_wishlist_activation(flags: list):
    """The quality wishlist is INACTIVE until the principal culls the mechanical candidate list
    to ~75 names (QUALITY_WISHLIST_DESIGN.md decision A, hybrid seeding). That inactivity is a
    correct design state on day one and a DEAD WATCH by day thirty: a screen that has been
    running daily for a month, firing nothing, because a human step never happened is exactly the
    silently-dead-watch failure this file exists to catch. Also checks that logged fires carry
    the SPY counterfactual they were pre-registered with — a fire without it cannot be graded,
    and an ungradeable fire is an unfalsifiable one."""
    import datetime as _dt
    import json as _json
    try:
        cand = ROOT / "verticals/generators/data/QUALITY_WISHLIST_CANDIDATES.json"
        active = ROOT / "verticals/generators/data/quality_wishlist_active.json"
        if cand.exists() and not active.exists():
            asof = (_json.loads(cand.read_text()) or {}).get("asof", "")
            try:
                age = (_dt.date.today() - _dt.date.fromisoformat(asof)).days
            except Exception:
                age = 0
            if age > 30:
                flags.append(f"CRITICAL QUALITY-WISHLIST-UNACTIVATED: the mechanical candidate "
                             f"list was screened {age}d ago and the cull to ~75 names has never "
                             f"been saved to quality_wishlist_active.json — the daily watch has "
                             f"been running and firing nothing that whole time")
        fires = ROOT / "verticals/generators/data/QUALITY_WISHLIST_FIRES.json"
        if fires.exists():
            for r in (_json.loads(fires.read_text()) or {}).get("fires", []):
                if r.get("spy_at_fire") in (None, 0) or r.get("px_at_fire") in (None, 0):
                    flags.append(f"CRITICAL QUALITY-WISHLIST-UNGRADEABLE: fire "
                                 f"{r.get('ticker')}@{r.get('fired')} was logged without the "
                                 f"SPY-same-window counterfactual it was pre-registered with")
    except Exception as e:
        flags.append(f"quality-wishlist invariant errored: {type(e).__name__}: {e}")


def check_queue_hygiene(flags: list):
    """Queue relevance (principal directive 2026-08-16): a generic-sweep pre-bench row that is
    over-age or over-cap means queue_hygiene is not running ahead of drains — the conveyor is
    spending bench tokens off-edge. Mirrors desk/queue_hygiene.py rules; fires only on rows
    hygiene WOULD evict, so a clean queue stays silent."""
    try:
        import datetime, json
        from desk.queue_hygiene import (GENERIC_SWEEP_PREFIXES, MCAP_CEILING, PRE_BENCH,
                                        STALE_DAYS, _age_days, _is_generic, _is_recourt)
        items = json.loads((ROOT / "desk/data/court_queue.json").read_text())["items"]
        for r in items:
            if r.get("stage") not in PRE_BENCH or not _is_generic(r) or _is_recourt(r):
                continue
            age = _age_days(r)
            if age is not None and age > STALE_DAYS + 7:
                flags.append(f"CRITICAL: {r['ticker']} generic-sweep row {age:.0f}d pre-bench "
                             f"(> {STALE_DAYS}+7d) — queue_hygiene is not running before drains")
            m = (r.get("screen_row") or {}).get("mcap") or (r.get("screen_row") or {}).get("mcap_resolved")
            if isinstance(m, (int, float)) and m >= MCAP_CEILING:
                flags.append(f"CRITICAL: {r['ticker']} ${m/1e9:.0f}B generic-sweep row pre-bench "
                             f"— hygiene large-cap eviction not firing")
    except Exception as e:
        flags.append(f"queue-hygiene invariant errored: {type(e).__name__}: {e}")


def check_advance_has_verification(flags: list):
    """VERIFICATION-BEFORE-ADVANCE (principal-ratified 2026-08-14, the MLTX precedent): no
    ADVANCE ruling (a new-buy verdict — STARTER/OWNABLE/OWN — reached through adjudication)
    stands without a verification pack run on its decisive findings. MLTX proved why: the
    half-starter's EV was backwards ($985M not $845M-upper-bound), its 'non-dilutive $400M'
    was $0 committed, and its calendar attribution was wrong — all closable same-day with
    desk tooling (sec_fetch/CT.gov), none checked before the ruling. The court adversarial
    process tests ARGUMENTS; the verification pack tests the NUMBERS the winning argument
    rests on. Convention: a file desk/data/court_artifacts/<TICKER>_VERIFICATION_*.md, or a
    'verification' key/text in the edge classification recording what was primary-checked.
    Applies to adjudications dated on/after 2026-08-14 (no retroactive noise)."""
    import datetime as _dt
    import json as _json
    ADVANCE = {"STARTER", "OWNABLE", "OWN"}
    art = ROOT / "desk" / "data" / "court_artifacts"
    try:
        led = _json.loads((ROOT / "desk/data/research_ledger.json").read_text())
        for n in led.get("names", []):
            if n.get("stage") != "ADJUDICATED" or n.get("verdict") not in ADVANCE:
                continue
            try:
                if _dt.date.fromisoformat(n.get("asof", "1970-01-01")) < _dt.date(2026, 8, 14):
                    continue
            except Exception:
                continue
            t = n["ticker"]
            fam = _norm(t)
            if list(art.glob(f"{t.replace('.', '_')}_VERIFICATION_*.md")) or \
               list(art.glob(f"{fam}_VERIFICATION_*.md")):
                continue
            ecf = ROOT / "desk/data/edge_classifications" / f"{t}.json"
            if ecf.exists() and "verif" in ecf.read_text().lower():
                continue
            flags.append(f"CRITICAL ADVANCE-WITHOUT-VERIFICATION: {t} carries a new-buy verdict "
                         f"({n.get('verdict')}) adjudicated {n.get('asof')} with no verification "
                         f"pack on record — the MLTX rule: the court tests arguments, the pack "
                         f"tests the numbers; no ADVANCE ratifies without one")
    except Exception as e:
        flags.append(f"advance-verification invariant errored: {type(e).__name__}: {e}")


ALL_CHECKS = [check_watch_has_future_pack, check_held_classified, check_stale_packs,
              check_batch_docs_in_ledger, check_defect_ledger_aging,
              check_court_has_pitch_doc, check_staging_plan_executed, check_court_queue,
              check_reopen_conditions_wired, check_quality_wishlist_activation,
              check_advance_has_verification, check_queue_hygiene]


def run_all(flags: list | None = None) -> list:
    flags = flags if flags is not None else []
    for c in ALL_CHECKS:
        c(flags)
    return flags


if __name__ == "__main__":
    for f in run_all():
        print(" ", f)
