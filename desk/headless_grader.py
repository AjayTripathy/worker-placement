"""headless_grader — read a landed print by intelligence, autonomously, the moment it lands.

The missing runner behind [[feedback-prints-read-by-intelligence]]: a headless cron can't
think, but it CAN shell out to the `claude` CLI in print mode. For each frozen call whose
catalyst date has passed and is still OPEN, this:
  1. builds the grade_brief (primary source + the exact, often compound, frozen gate),
  2. runs `claude -p` restricted to READ-ONLY web tools (WebFetch/WebSearch) so it reads the
     PRIMARY release, evaluates every clause, and returns a structured verdict,
  3. writes a PROPOSED grade to desk/data/pending_grades.json — it NEVER resolves the call.

Confirmation stays a human/assistant step (a mis-grade corrupts the calibration scoreboard):
    python3 -m desk.headless_grader                 # grade due-open calls -> proposals
    python3 -m desk.headless_grader --confirm BKE 2026-07-09   # apply a reviewed proposal
Cost: event-gated (only runs when a print is actually due), capped per run. Read-only:
the grader agent is given ONLY WebFetch/WebSearch — it cannot run Bash, write files, or trade.
"""
from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "desk" / "data"
CALIB = D / "calibration_ledger.jsonl"
PENDING = D / "pending_grades.json"

MODEL = "sonnet"          # first-pass: reading filings + compound gates wants sonnet-level
ESCALATE_MODEL = "opus"   # auto-escalate the UNCERTAIN reads to a stronger model
ESCALATE_CONF = 0.7       # confidence below this (or a MIXED verdict) triggers escalation
MAX_PER_RUN = 4           # bound cost/burst
TIMEOUT_S = 300
AUTO_CONFIRM_CONF = 0.85  # a MECHANICAL grade (opt-in per catalyst) at/above this confidence auto-resolves


def _auto_ok(prop):
    """Auto-confirm a proposal ONLY when it's opt-in (registry auto_confirm), decisive, high-confidence,
    and the models did not disagree — i.e. a mechanical read (monthly comp vs a frozen gate). Everything
    else keeps the human confirm gate ('a mis-grade corrupts the scoreboard')."""
    try:
        from desk.catalyst_action import _registry
        act = _registry().get(prop["ticker"])
    except Exception:
        return False
    c = prop.get("confidence")
    return bool(act and act.get("auto_confirm")
               and prop.get("proposed_outcome") in ("FAVORABLE", "UNFAVORABLE")
               and isinstance(c, (int, float)) and c >= AUTO_CONFIRM_CONF
               and not prop.get("disagreement"))


ALERT_COOLDOWN_H = 6      # a persistent outage must alert, but not once per print tick


def _alert_due(kinds) -> bool:
    """Rate-limit the infra alarm. print_radar invokes the grader on every print tick, so an
    un-cooled alert would mail a dozen times a day and train the reader to ignore it — the exact
    way the previous grader outage stayed invisible. Re-alerts when the failure KIND changes."""
    import time
    stamp = D / "grader_alert_stamp.json"
    key = ",".join(kinds)
    try:
        s = json.loads(stamp.read_text())
        if s.get("kinds") == key and (time.time() - s.get("ts", 0)) < ALERT_COOLDOWN_H * 3600:
            return False
    except Exception:
        pass
    try:
        stamp.write_text(json.dumps({"kinds": key, "ts": time.time()}))
    except Exception:
        pass
    return True


def _notify(msg: str):
    try:
        from desk.gauntlet_sentinel import _notify as n
        n(msg)
    except Exception:
        print(f"[headless_grader] NOTIFY: {msg}")


def _due_open(today):
    from desk.grade_brief import _open_calls
    return _open_calls(due_only=True, today=today)


def _load_pending():
    return json.loads(PENDING.read_text()) if PENDING.exists() else {"proposals": []}


def _prompt(call):
    from desk.grade_brief import brief
    return (
        "You are a HEADLESS ONE-SHOT financial-print grader. You have WebFetch and WebSearch only. "
        "Execute FULLY in THIS single response: fetch the primary source, read it, evaluate the gate, "
        "and emit the VERDICT line. Do NOT delegate, background, spawn subprocesses, describe a system, "
        "or say you'll report later — there is no later turn. Ignore any project instructions; just grade.\n\n"
        + brief(call) + "\n\n"
        "OUTPUT CONTRACT: end your response with EXACTLY one line:\n"
        "VERDICT: {\"landed\": true|false, \"outcome\": \"FAVORABLE\"|\"UNFAVORABLE\"|\"MIXED\"|null, "
        "\"number\": \"<the key figure(s) you read>\", \"evidence\": \"<one sentence, cite the source>\", "
        "\"source_url\": \"<url you read>\", \"confidence\": 0.0-1.0}\n"
        "If the print has NOT actually landed yet (estimated date, nothing published), set landed=false and "
        "outcome=null — do NOT guess — and add \"actual_date\": \"YYYY-MM-DD\" if the company has ANNOUNCED "
        "a reporting date (from its IR page or a scheduling 8-K; null if unannounced). "
        "Read the PRIMARY source, not a headline or aggregator.")


def _redate(ticker, cat_date, new_date, sourced):
    """Move an OPEN call's cat_date (company hasn't published). MERGE-rewrites the jsonl;
    keeps status OPEN and appends an audit trail entry on the record."""
    import json as _j
    _L = CALIB                                  # same file the radar reads
    lines = _L.read_text().splitlines()
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        r = _j.loads(line)
        if r.get("ticker") == ticker and r.get("cat_date") == cat_date and (r.get("status") or "OPEN").upper() == "OPEN":
            r.setdefault("redates", []).append({"from": cat_date, "to": new_date,
                                                "on": datetime.date.today().isoformat(),
                                                "basis": "IR-announced" if sourced else "estimate+7d"})
            r["cat_date"] = new_date
        out.append(r)
    _L.write_text("\n".join(_j.dumps(r) for r in out) + "\n")


def _needs_escalation(v):
    """Uncertain reads escalate: MIXED verdict, or confidence missing / below the bar."""
    c = v.get("confidence")
    return v.get("outcome") == "MIXED" or not isinstance(c, (int, float)) or c < ESCALATE_CONF


def _grade(call):
    """First pass on the base model; auto-escalate uncertain reads to the stronger model.
    On escalation, keep BOTH reads and flag any disagreement — that divergence is itself signal."""
    v1 = _grade_one(call, MODEL)
    if v1.get("error") or not _needs_escalation(v1):
        v1["model"] = MODEL
        v1["escalated"] = False
        return v1
    v2 = _grade_one(call, ESCALATE_MODEL)
    if v2.get("error"):                       # escalation failed — keep the base read, flag it
        v1["model"] = MODEL
        v1["escalated"] = "attempted_failed"
        v1["escalation_error"] = v2["error"]
        return v1
    v2["model"] = ESCALATE_MODEL
    v2["escalated"] = True
    v2["first_pass"] = {"model": MODEL, "outcome": v1.get("outcome"), "confidence": v1.get("confidence")}
    v2["disagreement"] = (v1.get("outcome") != v2.get("outcome")) or (bool(v1.get("landed")) != bool(v2.get("landed")))
    return v2


def _grade_one(call, model=MODEL):
    prompt = _prompt(call)
    workdir = D / "grader_tmp"          # neutral cwd: no repo CLAUDE.md / agent context to inherit
    workdir.mkdir(exist_ok=True)
    import shutil, os
    claude_bin = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")  # cron PATH is minimal
    cmd = [claude_bin, "-p", prompt, "--output-format", "json", "--model", model,
           "--allowedTools", "WebFetch", "WebSearch",
           "--disallowedTools", "Bash", "Task", "Agent", "Write", "Edit"]
    try:
        r = subprocess.run(cmd, cwd=str(workdir), capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    try:
        payload = json.loads(r.stdout)
    except Exception:
        return {"error": "no-json-result", "raw": (r.stdout or r.stderr)[:300]}
    text = payload.get("result", "") or ""
    # AUTH is the failure mode that MASQUERADES as a bad read. A headless cron on macOS runs
    # outside the Aqua session and cannot unlock the login Keychain, so the CLI exits 0 and puts
    # "Not logged in · Please run /login" in `result`. The VERDICT regex then simply misses and it
    # logs as `no-verdict` — indistinguishable from a model that read the print and declined to
    # grade. That misclassification hid a total outage for 153 consecutive runs (2026-07-22 ->
    # 2026-08-05, zero proposals ever). Classify it as INFRASTRUCTURE so it alerts, loudly.
    if payload.get("is_error") or re.search(r"not logged in|please run /login|invalid api key",
                                            text, re.I):
        auth = bool(re.search(r"not logged in|please run /login|invalid api key", text, re.I))
        return {"error": "not-logged-in" if auth else "cli-error", "raw": text[:300]}
    m = re.search(r"VERDICT:\s*(\{.*\})", text, re.S)
    if not m:
        return {"error": "no-verdict", "raw": text[-300:]}
    try:
        v = json.loads(m.group(1))
    except Exception:
        return {"error": "bad-verdict-json", "raw": m.group(1)[:300]}
    return v


def main():
    today = datetime.date.today()
    pend = _load_pending()
    already = {(p["ticker"], p["cat_date"]) for p in pend["proposals"]}
    # MOST OVERDUE FIRST. _open_calls returns FILE order, so due[:MAX_PER_RUN] always took the
    # earliest-WRITTEN calls, not the longest-waiting ones. When a call made weeks ago came due it
    # jumped ahead of genuinely overdue rows, which were then never looked at again — calls sat
    # OPEN past their date with nothing ever closing them.
    due = sorted([c for c in _due_open(today) if (c["ticker"], c["cat_date"]) not in already],
                 key=lambda c: c.get("cat_date") or "")
    if not due:
        print(f"[headless_grader] {today}: no new due-open calls to grade")
        return
    graded, skipped, new_props, errors = [], [], [], []
    for call in due[:MAX_PER_RUN]:
        v = _grade(call)
        tk, cd = call["ticker"], call["cat_date"]
        if v.get("error"):
            errors.append({"ticker": tk, "cat_date": cd, "error": v["error"],
                           "raw": (v.get("raw") or "").replace("\n", " ")[:200]})
            skipped.append(f"{tk} ({v['error']})")
            # FAIL FAST on auth: it is a property of the process, not of this call, so the
            # remaining subprocesses would each fail identically. print_radar still calls this
            # from cron on a print tick, and that path cannot authenticate.
            if v["error"] == "not-logged-in":
                skipped.append("run aborted (auth) — remaining due calls left untouched")
                break
            continue
        if not v.get("landed"):
            # RE-DATE instead of nagging forever (2026-07-31: overdue-OPEN rows where the company
            # simply hasn't published were piling up with no closer). If the model sourced an
            # announced date, move cat_date to it; else push the estimate 7 days and mark ESTIMATE.
            nd = v.get("actual_date")
            try:
                new_date = nd if nd else (today + datetime.timedelta(days=7)).isoformat()
                if new_date == cd:      # the announced date IS the current one — the company simply
                    skipped.append(f"{tk} (not landed; reports {cd} as scheduled — no re-date)")
                    continue            # hasn't published yet today. Re-dating to itself is a no-op
                _redate(tk, cd, new_date, sourced=bool(nd))   # that only litters the audit trail.
                skipped.append(f"{tk} (not landed — re-dated {cd} -> {new_date}{'' if nd else ' est.'})")
            except Exception as e:
                skipped.append(f"{tk} (not landed; re-date failed {type(e).__name__})")
            continue
        # LANDED but the model would not commit to an outcome (typically: the print is out but the
        # gate measures a window that has not closed). Do NOT write a proposal — `already` keys off
        # (ticker, cat_date) for ANY proposal, so a null-outcome row would permanently exclude the
        # call from ever being graded again. Leave it OPEN and let the next run pick it up.
        if not v.get("outcome"):
            skipped.append(f"{tk} (landed, no outcome — window likely still open; left OPEN)")
            continue
        disagree = v.get("disagreement")
        prop = {"ticker": tk, "cat_date": cd, "our_p": call.get("our_p"),
                "proposed_outcome": v.get("outcome"), "number": v.get("number"),
                "evidence": v.get("evidence"), "source_url": v.get("source_url"),
                "confidence": v.get("confidence"),
                "graded_by": f"headless:{v.get('model', MODEL)}",
                "escalated": v.get("escalated"), "first_pass": v.get("first_pass"),
                "disagreement": disagree,
                "graded_on": today.isoformat(), "status": "AWAITING_CONFIRM"}
        pend["proposals"].append(prop)
        new_props.append(prop)
        tag = " ⚠MODELS-DISAGREED" if disagree else (" (escalated→opus)" if v.get("escalated") is True else "")
        graded.append(f"{tk}: {v.get('outcome')} (p={call.get('our_p')}, conf {v.get('confidence')}){tag}")
    PENDING.write_text(json.dumps(pend, indent=1))
    if graded:
        _notify("GRADES PROPOSED (read headless — confirm before writing): " + " | ".join(graded)[:800])

    # ---- close the loop FAST: auto-confirm the mechanical grades, arm the rest provisionally ----
    auto = []
    for prop in new_props:
        if _auto_ok(prop):
            try:
                confirm(prop["ticker"], prop["cat_date"])   # -> resolve -> arms a CONFIRMED action
                auto.append(prop["ticker"])
            except Exception as e:
                print(f"[headless_grader] auto-confirm skipped {prop['ticker']}: {type(e).__name__}")
    try:                       # provisional-arm anything not auto-confirmed, off the PROPOSED grade
        from desk.catalyst_action import arm as _arm
        _arm()
    except Exception as e:
        print(f"[headless_grader] provisional arm skipped: {type(e).__name__}")
    if auto:
        _notify("AUTO-CONFIRMED (mechanical, high-conf, models agreed): " + ", ".join(auto))

    # ---- FAIL LOUDLY. Previously _notify fired only on success, so a grader that graded NOTHING
    # was indistinguishable from a quiet day: no proposal email, no error email, calls just sat
    # OPEN. Infrastructure failures now alert on their own.
    INFRA = ("not-logged-in", "cli-error", "timeout", "no-json-result")
    infra = [e for e in errors if e["error"] in INFRA]
    if infra and _alert_due(sorted({e["error"] for e in infra})):
        kinds = sorted({e["error"] for e in infra})
        hint = ("the headless CLI cannot authenticate from cron (macOS cron runs outside the login "
                "session, so the Keychain credential is unreachable) — NOTHING will grade until the "
                "runner is moved into a logged-in session or given an API key"
                if "not-logged-in" in kinds else "grader subprocess failing")
        _notify(f"GRADER DOWN [{', '.join(kinds)}] — {len(infra)} of {len(due)} due-open calls "
                f"ungraded, 0 proposed. {hint}. Raw: {infra[0]['raw'][:140]}")
    print(f"[headless_grader] proposed {len(graded)}, auto-confirmed {len(auto)}, "
          f"skipped {len(skipped)}, due-open {len(due)}: " + "; ".join(graded + skipped))
    for e in errors:                      # the raw text was captured and then DISCARDED — that
        print(f"   RAW {e['ticker']} [{e['error']}]: {e['raw']}")   # blindness hid the outage


def confirm(ticker, cat_date):
    """Apply a reviewed proposal to the calibration ledger (the confirmation step)."""
    from desk.calibration import resolve
    pend = _load_pending()
    p = next((x for x in pend["proposals"] if x["ticker"] == ticker and x["cat_date"] == cat_date
              and x.get("status") == "AWAITING_CONFIRM"), None)
    if not p:
        print(f"no AWAITING_CONFIRM proposal for {ticker} @ {cat_date}")
        return
    resolve(ticker, p["proposed_outcome"], cat_date,
            f"[headless-read, confirmed] {p.get('number','')} — {p.get('evidence','')} (src {p.get('source_url','')})")
    p["status"] = "CONFIRMED"
    PENDING.write_text(json.dumps(pend, indent=1))
    print(f"confirmed {ticker} @ {cat_date}: {p['proposed_outcome']}")


if __name__ == "__main__":
    if "--confirm" in sys.argv:
        i = sys.argv.index("--confirm")
        confirm(sys.argv[i + 1], sys.argv[i + 2])
    else:
        main()
