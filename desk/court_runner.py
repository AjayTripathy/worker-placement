"""court_runner — drains the court_queue headlessly (PRD P1 stages 3-5; the auto-court
conveyor). Transport = the headless_grader pattern: shell `claude -p` with versioned
templates from desk/agent_steps/templates/, validate output-side, advance the queue.

Stage → template → validator:
  TRAP_VERIFY  trap_verify.md   verdict-enum header present + >=1 http(s) citation
  COURT_RED    court_red.md     "## RED BENCH" + RECOMMEND enum + >=3 numbered findings
  COURT_BLUE   court_blue.md    "## BLUE BENCH" + RED CASE enum + NET POSITION section
  ADJUDICATE                    NOT automated — adjudication + pitch doc + ledger/edge/pack
                                writes remain a session job (generator-never-grades-itself:
                                the runner that dispatched the benches must not also verdict).
                                The queue surfaces ADJUDICATE items; consistency_check nags.

SAFETY: the subprocess gets READ-ONLY web tools + Bash for desk read-only tooling is DENIED
(the bench cites the manifest text embedded in its prompt instead). Model per stage: volume
tier for TRAP_VERIFY, court tier for benches (COURT_DOCTRINE: evenly matched benches).
Budget: MAX_DISPATCH per run (default 4) so a full queue never burns unbounded tokens; the
hourly cron drains gradually. Auth failure fails LOUD (grader lesson).

  python3 -m desk.court_runner            # drain up to MAX_DISPATCH items
  python3 -m desk.court_runner --dry-run  # render prompts, dispatch nothing
"""
from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from desk import court_queue as CQ

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "desk" / "agent_steps" / "templates"
OUT_DIR = ROOT / "desk" / "data" / "court_artifacts"
MAX_DISPATCH = int(os.environ.get("COURT_RUNNER_MAX", "6"))   # 4->6 (2026-08-15 latency audit: intake outran drain; revisit if credit budget complains)
TIMEOUT_S = 20 * 60
MODEL_VOLUME = os.environ.get("COURT_MODEL_VOLUME", "claude-opus-5")
# 2026-08-17: default flipped fable -> opus, principal-directed ("use opus and not fable since we're
# out of fable credits"). This is a CREDIT-AVAILABILITY switch, not a doctrine change — COURT_DOCTRINE
# still wants evenly-matched benches, and opus-vs-opus satisfies that. deck_writer inherits this too
# (it dispatches on MODEL_COURT), which is what silently failed the first ARE deck on infra:limit.
# REVERT to claude-fable-5 when fable credits reset, or override per-run via COURT_MODEL_COURT.
MODEL_COURT = os.environ.get("COURT_MODEL_COURT", "claude-opus-5")

GEO_CATALOGS = {
    "US": "TTM one-offs (tax releases, refunds, marks) / cap-structure pull BEFORE net-cash claims "
          "(prefunded warrants, converts, preferreds by CLASS) / SBC-vs-dilution honesty / instrument-class "
          "artifacts (preferred/warrant/notes tickers) / split-adjusted sharecounts / cycle position vs the "
          "screen year (windfall-year defect family 5) / related-party + pledge check / 10-K/10-Q as primary",
    "JP": "governance bloc (incl. catalyst-ALREADY-SPENT: post-proxy-victory blocs, ToSTNeT "
          "buyout history) / TSE segment + 資本コスト plan (disclosure≠ambition) / FCF decomposition "
          "(payables, advances, 契約負債 on build-to-order) / balance-sheet reality / activist 5% "
          "filings / PFIC FMV-basis / 100-share-lot liquidity",
    "KR": "controller + succession (증여 gift filings = valuation-window suppression) / value-up "
          "EXECUTED trail (소각 completions, not plan text; cancel-then-recycle) / integrity "
          "(횡령·배임 news w/ control query, CB/BW refix trail, 최대주주 변경, pledge) / net-cash "
          "attribution (NCI>25%, 선수금, current CBs, fiscal-YE float — verify at NEXT quarter) / "
          "group conduits (related-party AR/loans; the auditor's KAM) / PFIC FMV / KOSDAQ ADV",
    "EU": "cycle position vs the filing year / FCF-quality (IFRS16 lease principal, WC release, "
          "capitalized dev) / balance-sheet reality (trust/client cash, debt-tag absence) / "
          "no-actor law (register, buybacks LIVE not historical, float) / filer-quality tie / "
          "WHT + stamp / LSE-orphan liquidity",
}
BATCH_PRIORS = ("Screens have five CONFIRMED defect families — treat every screen metric as "
                "hostile: (1) mcap/share-count joins (treasury, splits, reverse-splits); "
                "(2) net-cash measuring someone else's money (advances/NCI/CB/YE-float); "
                "(3) FCF from stale years or CFO-alone; (4) statutory-EBIT one-offs (royalty "
                "reversals, disposal gains, hedge-timing); (5) melting businesses screened at "
                "the windfall. Honest filers with artifact statistics are the BASE CASE.")

VERDICT_PAT = re.compile(r"\*\*(REAL CANDIDATE|FAIR-CARRY|BORDERLINE|MELTING|PERPETUAL-TRAP|"
                         r"SCREEN-ARTIFACT|SCREEN-MISCLASSIFIED|INTEGRITY-KILL)", re.I)
RED_PAT = re.compile(r"##\s*RED BENCH.*RECOMMEND:\s*<?\s*(REJECT|ACCEPT-WITH-CUTS|ACCEPT)", re.I | re.S)
BLUE_PAT = re.compile(r"##\s*BLUE BENCH.*RED CASE:\s*<?\s*(SUSTAINED|PARTIALLY OVERTURNED|OVERTURNED)", re.I | re.S)
CITE_PAT = re.compile(r"https?://")


def _manifest() -> str:
    from desk.court_toolkit import MANIFEST
    return MANIFEST


def _evidence(t: str) -> str:
    """Machine evidence pack shared by ALL stages (2026-08-07 postmortem: the blues'
    overturns were machine-layer errors — dates, anchors, series, phantom positions).
    Failure never blocks a dispatch; it just makes the bench fetch its own facts."""
    try:
        from desk.court_evidence import build_pack, render_pack
        return render_pack(build_pack(t))
    except Exception as e:
        return (f"## EVIDENCE PACK — UNAVAILABLE ({type(e).__name__}: {e}) — fetch tape/"
                f"filings/series from primary sources yourself and date every anchor.")


def _atlas(t: str, context: str) -> str:
    """R1.11: the detector brain rides into every bench. Never blocks a dispatch."""
    try:
        from desk.court_dispatch import render_atlas
        out = render_atlas(t, context)
    except Exception as e:
        return (f"## DESK DETECTOR ATLAS — unavailable ({type(e).__name__}) — still produce a "
                f"DETECTORS CONSULTED section from first principles (validator requires it).\n")
    # R1.12: planner-selected connectors EXECUTED pre-flight; results are pack facts.
    try:
        from desk.detector_preflight import render_results
        out += "\n" + render_results(t, context)
    except Exception:
        pass
    return out


def _reject_feedback(item: dict, stage: str) -> str:
    rejects = [h["validator_reject"] for h in item.get("history", [])
               if h.get("validator_reject") and h.get("stage") == stage]
    if not rejects:
        return ""
    return (f"\n\nPRIOR ATTEMPT(S) REJECTED by the output validator — fix these SPECIFICALLY "
            f"this time (most recent last): {rejects[-3:]}. A primary http citation means a "
            f"full URL to a filing/release; the required headers/enums are in the template.\n")


def _render(stage: str, item: dict) -> tuple[str, str]:
    """Returns (prompt, model)."""
    t = item["ticker"]
    geo = ("JP" if t.endswith(".T") else "KR" if t.endswith((".KS", ".KQ"))
           else "EU" if ("." in t) else "US")   # bare tickers = US filers (FRO/INSW/WPM fell into the EU branch)
    if stage == "TRAP_VERIFY":
        tpl = (TPL / "trap_verify.md").read_text()
        p = (tpl.replace("{TICKER}", t).replace("{GEO}", geo)
             .replace("{SCREEN_ROW}", json.dumps(item.get("screen_row", {}), ensure_ascii=False, indent=1))
             .replace("{GEO_CATALOG}", GEO_CATALOGS[geo]).replace("{BATCH_PRIORS}", BATCH_PRIORS))
        return _evidence(t) + _reject_feedback(item, stage) + "\n\n" + p, MODEL_VOLUME
    if stage == "REFUTABILITY":
        tpl = (TPL / "refutability_triage.md").read_text()
        sr = item.get("screen_row", {})
        p = (tpl.replace("{COHORT}", str(sr.get("cohort", "?")))
             .replace("{NARRATIVE}", "see cohort definition in knowledge_graph/cohorts.json")
             .replace("{EVENT_STATS}", json.dumps(sr, ensure_ascii=False))
             .replace("{MEMBERS}", t))
        return _evidence(t) + _reject_feedback(item, stage) + "\n\n" + p, MODEL_VOLUME
    thesis = (_artifact_text(item, "TRAP_VERIFY") or _artifact_text(item, "REFUTABILITY")
              or json.dumps(item.get("screen_row", {})))
    # 2026-09-10: a thesis-sourced row that REUSES a terminal row (class de-rate re-triage) carries
    # the new thesis in `context`; without this the benches litigated the OLD screen brief
    # (MNDY/HUBS/LEN argued August's agentic-SaaS / dual-class briefs, not the regime thesis).
    from desk.court_queue import is_thesis_sourced
    if item.get("context") and is_thesis_sourced(str(item.get("source", ""))):
        prior = thesis if not thesis.startswith("{") else ""
        thesis = ("THESIS UNDER COURT (current):\n" + str(item["context"]) +
                  ("\n\n=== PRIOR COURT ON A DIFFERENT THESIS FOR THIS NAME (evidence only; do not "
                   "re-litigate it) ===\n" + prior[:6000] if prior else ""))
    if stage == "SCIENCE":
        tpl = (TPL / "science_brief.md").read_text()
        p = tpl.replace("{TICKER}", t).replace("{THESIS}", thesis)
        return _evidence(t) + _reject_feedback(item, stage) + "\n\n" + p, MODEL_COURT
    # deep-tech: benches receive the science brief as EVIDENCE (spot-check duty stated)
    sci = _artifact_text(item, "SCIENCE")
    sci_block = ("\n\n=== SCIENCE BRIEF (evidence, not advocacy — verified upstream; you MUST "
                 "spot-check at the primary any brief claim you rest a kill or an overturn on, "
                 "and flag any brief error plainly) ===\n" + sci) if sci else ""
    if stage == "COURT_RED":
        tpl = (TPL / "court_red.md").read_text()
        p = (tpl.replace("{TICKER}", t).replace("{THESIS}", thesis)
             .replace("{VERIFICATION_MANIFEST}", _manifest()))
        return _evidence(t) + sci_block + "\n\n" + _atlas(t, thesis) + _reject_feedback(item, stage) + "\n\n" + p, MODEL_COURT
    if stage == "COURT_BLUE":
        red = _artifact_text(item, "COURT_RED") or ""
        tpl = (TPL / "court_blue.md").read_text()
        p = (tpl.replace("{TICKER}", t).replace("{THESIS}", thesis)
             .replace("{RED_CASE}", red).replace("{VERIFICATION_MANIFEST}", _manifest()))
        return _evidence(t) + sci_block + "\n\n" + _atlas(t, thesis + red) + _reject_feedback(item, stage) + "\n\n" + p, MODEL_COURT
    raise ValueError(f"no template for stage {stage}")


def _artifact_text(item: dict, from_stage: str) -> str | None:
    for h in reversed(item.get("history", [])):
        if h.get("from") == from_stage and h.get("artifact"):
            p = Path(h["artifact"])
            if p.exists():
                return p.read_text()
    return None


def _validate(stage: str, text: str) -> str | None:
    """Output-side validator (dispatch doctrine). Returns an error string or None."""
    if len(text) < 400:
        return "output too short"
    if not CITE_PAT.search(text):
        return "no primary citation (http) anywhere in the output"
    if stage == "TRAP_VERIFY" and not VERDICT_PAT.search(text):
        return "no verdict from the closed enum"
    if stage == "REFUTABILITY" and ("DAMAGE-ABSENT" not in text.upper() and "DAMAGE-ARRIVING" not in text.upper()
                                    and "STRUCTURAL" not in text.upper() and "UNTRIAGEABLE" not in text.upper()):
        return "no refutability classification present"
    if stage == "REFUTABILITY" and not CW_PAT.search(text):
        return "no COURT-WORTHINESS N/10 line (required for the automated 6/10 gate, v2 template)"
    if stage in ("REFUTABILITY", "COURT_RED") and "PRINT PROXIMITY" not in text.upper():
        return "no PRINT PROXIMITY line (v3 template — a court must not race a known catalyst; TEAM 2026-08-06)"
    if stage == "SCIENCE":
        up = text.upper()
        if "SCIENCE BRIEF" not in up:
            return "missing SCIENCE BRIEF header"
        if "VERIFIED" not in up or "CLAIM" not in up:
            return "no claim ledger with VERIFIED/COMPANY-ASSERTED/UNVERIFIABLE tags"
        if re.search(r"\bRECOMMEND(ATION)?\s*[:=]|\b(REJECT|OWNABLE|BUY|SELL)\b\s*[-—:]", text):
            return "verdict language in a science brief — evidence only, no advocacy"
    if stage == "COURT_RED" and not RED_PAT.search(text):
        return "missing RED BENCH header / RECOMMEND enum"
    if stage in ("COURT_RED", "COURT_BLUE") and "PACK" not in text.upper():
        return "no PACK acknowledgment (v4 — benches must use or explicitly supersede the evidence pack)"
    if stage == "COURT_BLUE" and not BLUE_PAT.search(text):
        return "missing BLUE BENCH header / RED CASE ruling"
    if stage in ("COURT_RED", "COURT_BLUE") and "DETECTORS CONSULTED" not in text.upper():
        return ("no DETECTORS CONSULTED section (R1.11 — every dispatch-matched atlas entry "
                "needs a FIRED/NOT-FIRED/UNCHECKABLE disposition)")
    if stage == "COURT_RED" and "KILL-CLASS" not in text.upper():
        return ("no KILL-CLASS tags (§CONSENSUS-KILL, 2026-08-21 — every surviving kill must be "
                "tagged NOVEL or CONSENSUS; an all-consensus kill set on a fair-priced name is a "
                "minimum starter, not a FLAT)")
    return None


def _pack_misquote_warns(prompt: str, text: str) -> list[str]:
    """pack_field_misquote_check (KG-harvested off WVE 2026-08-11, blue bench): a bench that
    quotes dd52/pct_off_low values contradicting the evidence pack IN ITS OWN PROMPT is building
    tape framing on a fabricated-or-stale datum (WVE red: 'bounced 21% off the low' vs the
    pack's +3.3%). WARN-only — prose-number parsing must never hard-reject a court (LDI/BUR
    retry-purgatory lesson); the warning lands in the artifact for the adjudicator."""
    warns = []
    num = r"[\-+\u2212]?\d+(?:\.\d+)?"          # sign class incl. Unicode minus (8/14: all 11
    gap = r"[^0-9\-+\u2212\u2013\u2014]{0,12}"     # WARNs in a batch were the checker eating U+2212)
    for field, tol in (("dd52", 1.5), ("pct_off_low", 1.5)):
        pm = re.search(field + gap + "(" + num + ")", prompt)
        tm = re.search(field + gap + "(" + num + ")", text)
        if not (pm and tm):
            continue
        a, b = float(pm.group(1).replace("\u2212","-")), float(tm.group(1).replace("\u2212","-"))
        if abs(a) <= 1.5 < abs(b): a *= 100          # pack fraction vs bench percent
        if abs(b) <= 1.5 < abs(a): b *= 100
        # 8/15 WYFI: pack stored pct_off_low as the fraction 1.809 (>1.5, so the clause above
        # missed it) vs the bench's correct +181.0 \u2014 a ~100x gap is a UNIT mismatch, never a
        # misquote (priceMagnifier lesson: unit conventions don't transfer between stores).
        if a and 80 <= abs(b / a) <= 125: a *= 100
        if b and 80 <= abs(a / b) <= 125: b *= 100
        if abs(a - b) > tol:
            # 8/15 SPRY: red correctly superseded a stale pack tape (8/13 close in the pack,
            # 8/14 close in the bench) and drew a WARN for it \u2014 a declared supersession is the
            # bench doing its job; keep the note but mark it so the adjudicator reads it as
            # verify-the-supersession, not as a fabrication flag.
            low = text.lower()
            declared = "supersed" in low and not re.search(r"supersed\w*:\s*(none|n/a)", low)
            tag = "SUPERSESSION-DECLARED (verify, not a fabrication flag) \u2014 " if declared else ""
            warns.append(f"{tag}{field}: bench quotes {b:+.1f} vs pack {a:+.1f}")
    return warns


def _api_key() -> str | None:
    """BYOM key resolution, same order as officekit models.json: env first, then
    the desk's key file. The runner never logs or prints the value."""
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    p = Path.home() / ".anthropic_key"
    try:
        return p.read_text().strip() or None
    except OSError:
        return None


# 2026-09-05 (F2 promotion): default transport is the SDK — the same rail the
# officekit app courts run on — with `claude -p` kept as the fallback when no
# API key resolves. Override with COURT_TRANSPORT=cli|sdk.
TRANSPORT = os.environ.get("COURT_TRANSPORT") or ("sdk" if _api_key() else "cli")


def _dispatch_sdk(prompt: str, model: str) -> dict:
    """SDK transport: streaming (long courts exceed the non-streaming limit),
    server-side web_search so benches keep live primary-source access — the
    read-only property the CLI rail enforced via allowedTools holds here by
    construction (no Bash, no writes, nothing but search)."""
    key = _api_key()
    if not key:
        return {"error": "infra:no-api-key"}
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        with client.messages.stream(
                model=model, max_tokens=30000,
                tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 12}],
                messages=[{"role": "user", "content": prompt}]) as s:
            resp = s.get_final_message()
    except Exception as e:
        low = str(e).lower()
        kind = ("limit" if any(k in low for k in ("rate", "limit", "overloaded", "credit", "quota"))
                else "auth" if any(k in low for k in ("authentication", "api key", "401"))
                else type(e).__name__)
        return {"error": f"infra:{kind}", "raw": str(e)[:200]}
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    if resp.stop_reason == "max_tokens":
        return {"error": "infra:truncated-max-tokens", "raw": text[-200:]}
    if len(text.strip()) < 200:
        return {"error": "infra:empty-result", "raw": text[:200]}
    return {"text": text}


def _dispatch(prompt: str, model: str) -> dict:
    if TRANSPORT == "sdk":
        return _dispatch_sdk(prompt, model)
    claude_bin = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
    workdir = ROOT / "desk" / "data" / "court_tmp"
    workdir.mkdir(parents=True, exist_ok=True)
    cmd = [claude_bin, "-p", prompt, "--output-format", "json", "--model", model,
           "--allowedTools", "WebFetch", "WebSearch",
           "--disallowedTools", "Bash", "Task", "Agent", "Write", "Edit"]
    try:
        r = subprocess.run(cmd, cwd=str(workdir), capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    try:
        payload = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": "no-json-result", "raw": (r.stdout or r.stderr)[:300]}
    text = payload.get("result", "") or ""
    if "not logged in" in text.lower() or "/login" in text.lower():
        return {"error": "not-logged-in"}     # Keychain failure masquerades as output — fail LOUD
    # Empty/near-empty results are an INFRASTRUCTURE failure (credit limit, auth outage),
    # not a bench writing a short artifact — 2026-08-09: five names burned 4-5 validator
    # retries each on "output too short" during a limit outage. Detect by OUTPUT, abort loud.
    if len(text.strip()) < 200:
        low = (text + " " + str(payload.get("error", ""))).lower()
        kind = ("limit" if any(k in low for k in ("limit", "resets", "usage", "overloaded", "credit"))
                else "empty-result")
        return {"error": f"infra:{kind}", "raw": text[:200]}
    return {"text": text}


NEXT = {"TRAP_VERIFY": None, "REFUTABILITY": "ADJUDICATE", "SCIENCE": "COURT_RED",
        "COURT_RED": "COURT_BLUE", "COURT_BLUE": "ADJUDICATE"}


CW_PAT = re.compile(r"COURT-WORTHINESS\s+([A-Z0-9.\-]+)\s*:\s*(\d+)\s*/\s*10", re.I)


def _route_refutability(text: str, ticker: str) -> str:
    """Automated 6/10 gate (principal 2026-08-07: 'court everything 6/10 or higher').
    Tiered-model doctrine mechanized: Opus triage scores court-worthiness per member;
    >=6 -> COURT_RED (Fable bench), 4-5 -> ADJUDICATE (session decides the borderline),
    <=3 -> KILLED with the triage artifact as the record (a DECLINE is knowledge).
    Legacy outputs without a score line park at ADJUDICATE — never silently killed."""
    scores = {m.group(1).upper(): int(m.group(2)) for m in CW_PAT.finditer(text)}
    s = scores.get(ticker.upper())
    if s is None and scores:
        s = max(scores.values())        # cohort-wide triage: route by its best member claim
    if s is None:
        return "ADJUDICATE"
    return "COURT_RED" if s >= 6 else ("ADJUDICATE" if s >= 4 else "KILLED")


def _next_stage_after_verify(text: str) -> str:
    """Disposition routing: advance-to-court survives; everything else terminates the conveyor
    (with the verdict recorded — a DECLINE is knowledge, not failure). FAIR-CARRY advances —
    the fairly-paid-risk doctrine: RP_FAIR orphan carry is the deploying-book DEFAULT class,
    and in unresearched paper the fair-value computation is itself the edge (HSBK/III/1904
    precedent — 'fair' in the research desert is systematically conservative). The court
    adjudicates the carry bar, never a 'no edge -> no trade' shortcut."""
    m = VERDICT_PAT.search(text)
    v = (m.group(1).upper() if m else "")
    return "COURT_RED" if v in ("REAL CANDIDATE", "FAIR-CARRY", "BORDERLINE") else "KILLED"


def drain(max_dispatch: int = MAX_DISPATCH, dry_run: bool = False,
          only: set | None = None) -> list[str]:
    """`only`: restrict dispatch to these tickers (2026-09-10: a thesis court must not queue
    behind the standing backlog — regime candidates lost every slot to SOFI/RKT/CIEN/...)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done, log = 0, []
    # Relevance hygiene BEFORE spending bench tokens (principal directive 2026-08-16):
    # generic-sweep large caps and stale premises are evicted (logged, re-enqueueable on a
    # fresh dislocation); a hygiene failure must never block the drain — but it logs LOUD.
    try:
        from desk.queue_hygiene import run_hygiene
        h = run_hygiene(verbose=False)
        if h["evicted"] or h["flagged"]:
            log.append(f"HYGIENE evicted={h['evicted']} flagged={len(h['flagged'])}")
    except Exception as e:
        log.append(f"HYGIENE ERRORED (drain continues): {type(e).__name__}: {e}")
    # ANTI-STARVATION (2026-08-26): later-stages-first is right under normal load, but under a
    # sustained backlog TRAP_VERIFY received ZERO slots for 8-11 days (9 names stuck). Reserve
    # the LAST slot of every cycle for the oldest TRAP_VERIFY item aged >3 days.
    _tv = CQ.pending("TRAP_VERIFY")
    _tv_starved = []
    if _tv:
        import datetime as _dt
        def _tv_age(it):
            try:
                enq = _dt.datetime.fromisoformat((it.get("enqueued_utc") or "").replace("Z", "+00:00"))
                return (_dt.datetime.now(_dt.timezone.utc) - enq).days
            except Exception:
                return 0
        _tv_starved = sorted((it for it in _tv if _tv_age(it) > 3), key=_tv_age, reverse=True)
    _reserved = 1 if _tv_starved else 0
    for stage in ("COURT_BLUE", "COURT_RED", "SCIENCE", "REFUTABILITY", "TRAP_VERIFY"):   # later stages first: finish courts before starting new ones (SCIENCE feeds COURT_RED, so it drains ahead of triage)
        for item in CQ.pending(stage):
            if only and item.get("ticker") not in only:
                continue
            if done >= max_dispatch - (_reserved if stage != "TRAP_VERIFY" else 0):
                break
            prompt, model = _render(stage, item)
            if dry_run:
                log.append(f"DRY {item['ticker']} {stage} -> {model} ({len(prompt)} chars)")
                continue
            res = _dispatch(prompt, model)
            # IMMEDIATE-RETRY-ONCE (2026-08-15 latency audit: 28% validator-reject rate, each
            # reject previously waited a full drain cycle ~1-2h; one in-drain retry with the
            # reject reason converts most of those hours into minutes).
            if not res.get("error"):
                first_err = _validate(stage, res["text"])
                if first_err:
                    log.append(f"{item['ticker']} {stage}: reject ({first_err}) — immediate retry")
                    retry_prompt = prompt + (f"\n\nYOUR PREVIOUS ATTEMPT WAS REJECTED by the output "
                                             f"validator for: {first_err}. Produce the FULL output again, "
                                             f"fixing exactly that. The never-cut sections are mandatory.")
                    res2 = _dispatch(retry_prompt, model)
                    if not res2.get("error") and not _validate(stage, res2["text"]):
                        res = res2
            if res.get("error") == "not-logged-in" or str(res.get("error", "")).startswith("infra:"):
                log.append(f"INFRA FAILURE ({res.get('error')}) — aborting the whole drain "
                           f"(every dispatch would fail; no validator-reject rows written)")
                return log
            if res.get("error"):
                log.append(f"{item['ticker']} {stage}: {res['error']}")
                continue
            err = _validate(stage, res["text"])
            if err:
                log.append(f"{item['ticker']} {stage}: VALIDATOR REJECTED ({err}) — output not persisted to queue")
                # RETRY-WITH-FEEDBACK (2026-08-07: LDI/BUR rejected twice on the SAME error —
                # blind retries are purgatory): record the rejection so the next render tells
                # the bench exactly what to fix.
                item.setdefault("history", []).append(
                    {"validator_reject": err, "stage": stage,
                     "utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"})
                CQ.QUEUE.upsert([item], generated_by="court_runner:reject-feedback")
                continue
            ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M")
            art = OUT_DIR / f"{item['ticker'].replace('.', '_')}_{stage}_{ts}.md"
            if stage in ("COURT_RED", "COURT_BLUE"):
                mw = _pack_misquote_warns(prompt, res["text"])
                if mw:
                    res["text"] += ("\n\n> [runner pack_field_misquote_check — WARN, not a reject: "
                                    + "; ".join(mw) + ". Adjudicator: audit this bench's tape framing "
                                    "against the pack before crediting drawdown-anchored findings.]")
                    log.append(f"{item['ticker']} {stage}: PACK-MISQUOTE WARN ({'; '.join(mw)})")
            art.write_text(res["text"])
            try:
                from desk.court_dispatch import harvest_candidates
                nc = harvest_candidates(item["ticker"], stage, res["text"])
                if nc:
                    log.append(f"{item['ticker']} {stage}: {nc} kg_candidate(s) harvested")
            except Exception:
                pass
            if stage == "TRAP_VERIFY":
                nxt = _next_stage_after_verify(res["text"])
            elif stage == "REFUTABILITY":
                nxt = _route_refutability(res["text"], item["ticker"])
            else:
                nxt = NEXT[stage]
            CQ.advance(item["ticker"], nxt, artifact=str(art))
            log.append(f"{item['ticker']} {stage} -> {nxt} ({art.name})")
            done += 1
            if stage == "COURT_BLUE":
                # court complete -> write + EMAIL the pitch deck (principal directive
                # 2026-08-08); PROPOSED-pending-adjudication label preserves the
                # self-grading invariant. Failure never blocks the drain.
                try:
                    from desk.deck_writer import build_deck
                    build_deck(item["ticker"])
                except Exception as e:
                    log.append(f"{item['ticker']} deck_writer failed ({type(e).__name__}: {e})")
        if done >= max_dispatch:
            break
    # DECK BACKFILL (2026-08-17) — AFTER the benches, deliberately. build_deck was reachable from
    # exactly one place, the COURT_BLUE branch above, so only names that TRAVELLED the conveyor got
    # a reader-facing artifact: every court adjudicated by hand in-session had two benches, a
    # verdict and armed gates but no deck, and a sweep found 31 more going back to 07-01 including
    # an outright BUY (MNDY). I first wired this at the drain HEAD next to queue_hygiene, which was
    # wrong — hygiene is a cheap local file pass, a deck is a 2-5 minute LLM call, and putting it
    # ahead of dispatch delays every court in the drain to render an artifact for a court already
    # finished. Backfill is arrears work; it goes last and takes what time is left.
    try:
        from desk.deck_writer import backfill
        b = backfill(limit=1)
        if b:
            log.append(f"DECK BACKFILL built {b}")
    except Exception as e:
        log.append(f"DECK BACKFILL ERRORED (drain continues): {type(e).__name__}: {e}")
    adj = CQ.pending("ADJUDICATE")
    if adj:
        log.append(f"AWAITING ADJUDICATION (session job — pitch doc + verdict + wiring): "
                   f"{[i['ticker'] for i in adj]}")
    return log


def _acquire_lock():
    """Single-instance guard (2026-08-26): dispatches are sequential blocking calls, so a cycle
    can outlive the launchd interval; without a lock two drains double-dispatch the same items.
    Stale locks (dead pid) are replaced. Returns the lock path or None if another drain runs."""
    lock = ROOT / "desk" / "data" / "court_runner.lock"
    if lock.exists():
        try:
            pid = int(lock.read_text().strip())
            os.kill(pid, 0)   # raises if dead
            return None       # live drain in progress — this fire is a no-op
        except (ValueError, ProcessLookupError, PermissionError):
            pass              # stale — take it
    lock.write_text(str(os.getpid()))
    return lock


if __name__ == "__main__":
    _lk = _acquire_lock()
    if _lk is None:
        print(f"[court_runner] {datetime.datetime.utcnow().isoformat(timespec='seconds')}Z "
              f"another drain in progress — exiting (lock held)")
        sys.exit(0)
    try:
        out = drain(dry_run="--dry-run" in sys.argv)
    finally:
        try:
            _lk.unlink()
        except FileNotFoundError:
            pass
    print(f"[court_runner] {datetime.datetime.utcnow().isoformat(timespec='seconds')}Z")
    for line in out:
        print("  " + line)
    if not out:
        print("  queue empty")
