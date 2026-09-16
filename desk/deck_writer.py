"""deck_writer — a full pitch deck, written and EMAILED, the moment a court completes.

Principal directive 2026-08-08: "write then email me a full pitch deck when a court
completes; a pitch deck has the proposed entry bands and any sensors that are armed."

Flow (invoked by court_runner after any COURT_BLUE success):
  1. gather the record: latest RED + BLUE artifacts, a fresh evidence pack, and the
     ARMED INSTRUMENTATION snapshot (ledger alert bands, filing watches, dated packs)
  2. dispatch one headless synthesis pass (claude -p, court model) against the deck
     template — REQUIRED sections enforced by validator (PRD RC.7):
     four panes · what-we-checked table · PROPOSED ENTRY BANDS · ARMED SENSORS ·
     honesty section. The deck is labeled PROPOSED — PENDING ADJUDICATION
     (generator-never-grades-itself: the runner's deck proposes; the session ratifies)
  3. write desk/reports/<T>_PITCH_DECK_<date>.md, render PDF (pandoc + headless
     Chrome), email both-in-one via the mailer rail (PDF attached)

  python3 -m desk.deck_writer TICKER      # manual re-run
"""
from __future__ import annotations

import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTS = ROOT / "desk" / "data" / "court_artifacts"
REPORTS = ROOT / "desk" / "reports"

REQUIRED = ["```json", "What we believe", "What the market believes", "Why we might have edge",
            "Why it might be priced in", "What could go wrong", "What we checked",
            "PROPOSED ENTRY BANDS", "ARMED SENSORS", "unverified", "PRIZE TABLE"]


def _latest(t: str, stage: str) -> str:
    safe = t.replace(".", "_")
    cands = sorted(ARTS.glob(f"{safe}_{stage}_*.md"))
    return cands[-1].read_text() if cands else ""


def _sensors(t: str) -> str:
    lines = []
    try:
        rl = json.loads((ROOT / "desk/data/research_ledger.json").read_text())
        for n in rl.get("names", []):
            if n.get("ticker") == t and n.get("alert_below"):
                lines.append(f"- price alert: fires below {n['alert_below']} "
                             f"({n.get('gate_basis', n.get('entry_plan', ''))[:120]})")
    except Exception:
        pass
    try:
        fw = json.loads((ROOT / "desk/data/filing_watch.json").read_text())
        tt = fw.get("targets", {}).get(t)
        if tt:
            lines.append(f"- filing watch: {','.join(tt.get('forms_alert', []))} until {tt.get('until')} "
                         f"({tt.get('why','')[:120]})")
    except Exception:
        pass
    try:
        packs = json.loads((ROOT / "desk/data/resolution_packs.json").read_text()).get("packs", {})
        for k, p in packs.items():
            if k.split("|")[0].split("-")[0] == t and isinstance(p, dict) and \
               p.get("lifecycle") not in ("adjudicated", "expired"):
                lines.append(f"- dated pack {k}: {str(p.get('adjudication',''))[:140]}")
    except Exception:
        pass
    return "\n".join(lines) or "- NONE ARMED — the deck must flag this as a gap"


def classification_is_current(t: str, d: dict, root: Path = ROOT) -> bool:
    """True only if the edge-classification record post-dates the latest bench artifact for
    the ticker — i.e. it is THIS court's ruling, not an earlier court's. Undated = not current.
    (2026-09-10: CTSH's regime-court deck was emailed 'ADJUDICATED — OWNABLE' off the August
    classification before any adjudication existed.)"""
    try:
        import glob as _g, re as _re
        benches = sorted(_g.glob(str(root / "desk" / "data" / "court_artifacts" /
                                    f"{t.replace('.', '_')}_COURT_*_*.md")))
        m = _re.search(r"_(\d{8})\d{4}\.md$", benches[-1]) if benches else None
        bench_day = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}" if m else ""
        adj_day = str(d.get("date") or "")[:10]
        if not adj_day:
            return False
        return not (bench_day and adj_day < bench_day)
    except Exception:
        return False


def build_deck(t: str, email: bool = True) -> Path | None:
    red, blue = _latest(t, "COURT_RED"), _latest(t, "COURT_BLUE")
    sci = _latest(t, "SCIENCE")
    if not (red and blue):
        print(f"[deck_writer] {t}: missing bench artifacts (red={bool(red)} blue={bool(blue)})")
        return None
    try:
        from desk.court_evidence import build_pack, render_pack
        pack = render_pack(build_pack(t))
    except Exception as e:
        pack = f"(evidence pack unavailable: {e})"
    sensors = _sensors(t)
    # ADJUDICATION BLOCK (added 2026-08-17): the deck is the reader-facing artifact of the WHOLE
    # court, but build_deck only ever saw the two benches — so every deck emitted for an already-
    # adjudicated name still said "PROPOSED — PENDING ADJUDICATION" and omitted the actual verdict,
    # its gates, and any bench finding the adjudicator VACATED. The template asks for "where OUR OWN
    # benches erred"; without this block the writer cannot know.
    adj, adj_hdr = "", "PROPOSED — PENDING ADJUDICATION"
    try:
        ec = ROOT / "desk" / "data" / "edge_classifications" / f"{t.replace('.', '_')}.json"
        if not ec.exists():
            ec = ROOT / "desk" / "data" / "edge_classifications" / f"{t}.json"
        # 2026-09-10: a PRIOR court's classification must not stamp a NEW court's deck as
        # ADJUDICATED (CTSH: the regime-thesis benches finished, the writer read the August
        # classification and emailed "ADJUDICATED — OWNABLE" before any adjudication existed).
        # The classification only counts if it post-dates the latest bench artifact.
        stale_adj = False
        if ec.exists():
            d = json.loads(ec.read_text())
            stale_adj = not classification_is_current(t, d, ROOT)
        if ec.exists() and stale_adj:
            adj_hdr = (f"PROPOSED — PENDING ADJUDICATION (a prior court on {str(d.get('date',''))[:10]} "
                       f"ruled {d.get('recommendation','')}; that ruling is SUPERSEDED by the open court)")
            adj = ("\n=== PRIOR ADJUDICATION (an EARLIER court on a different thesis — context only; "
                   "it does NOT decide this deck; the header must say PENDING) ===\n"
                   f"{d.get('recommendation')} ({d.get('date')}): {str(d.get('verdict',''))[:1500]}\n")
        elif ec.exists():
            gates = d.get("reopen_gates") or []
            proc = d.get("process_findings") or []
            adj_hdr = f"ADJUDICATED {d.get('date','')} — {d.get('recommendation','')}"
            adj = ("\n=== ADJUDICATION (THE ACTUAL VERDICT — it OUTRANKS either bench; where it "
                   "contradicts a bench, the adjudication is right and the bench error belongs in "
                   "the 'what we checked ourselves' table) ===\n"
                   f"recommendation: {d.get('recommendation')}   conviction: {d.get('conviction')}\n"
                   f"{d.get('verdict','')}\n\nREOPEN GATES (use these VERBATIM as the entry bands "
                   "section — do not invent your own):\n" + "\n".join(f"- {g}" for g in gates) +
                   (("\n\nPROCESS FINDINGS / BENCH ERRORS the deck must disclose:\n" +
                     "\n".join(f"- {x}" for x in proc)) if proc else ""))
    except Exception as e:
        adj = f"\n(adjudication unavailable: {e})"

    prompt = f"""Write the full internal pitch deck for {t} from the completed adversarial court below.
Plain language (no desk jargon). REQUIRED sections, exactly these headers:
# PITCH — {t} — VERDICT (one line; label it exactly: "{adj_hdr}")
## What we believe
## What the market believes
## Why we might have edge
## Why it might be priced in
## What could go wrong         (the PRE-MORTEM, v1.7: top-3 failure narratives incl. >=1 with NO monitorable tripwire and its unknown-unknown class named; the reflexive/structural leg — our own size vs ADV, predicted flow, doctrine interactions; end with the verbatim sentence: "If this position loses money, the most likely reason will be ___")
## What we checked ourselves   (a table: claim | how checked | found | confirmed? — include where OUR OWN benches erred)
## PROPOSED ENTRY BANDS        (specific prices/conditions from the benches' own math: entry levels, adds, exits/trims if any, sizing, and the catalyst dates; if the courts say no-entry, state the reopen bands instead)
## ARMED SENSORS               (reproduce this list verbatim and add any the courts imply are MISSING:
{sensors})
## SCIENCE BRIEF DIGEST      (REQUIRED whenever a SCIENCE BRIEF appears in the inputs — deep-tech names only, omit the section entirely otherwise. Carry forward: the claim ledger's VERIFIED/COMPANY-ASSERTED/REFUTED verdicts on every load-bearing claim; the MEASUREMENT TRAPS verbatim in compressed form; the dated technical catalysts with their verifiability status; and any brief claim a bench overturned. Cite the brief artifact filename. The reader must get the science WITHOUT opening the artifact — a deep-tech deck without its science is a PRD violation, principal directive 2026-09-04.)
## What remains unverified   (ONLY genuinely-open items — anything already drained/estimated belongs as a row in the What-we-checked table with its disposition, NOT here; ratified 2026-09-03. Every open item carries its estimate when not drainable now.)
## PRIZE TABLE + VOL READ       (REQUIRED whenever >=1 unverified item is genuinely time-gated/private: scenario x probability x price with an EV line, anchored per anchor-and-adjust; plus IV-vs-RV + IV percentile when an options chain exists — cheap IV at high uncertainty means gated adds may be expressed in calls; rich IV routes to the premium-selling gates. When a chain exists, ALSO show the expression math: price 1-2 candidate strikes off the table itself (C_ours = sum of p_i x max(S_i - K, 0)) vs the chain, compare table dispersion sigma_table vs IV x sqrt(T), state the VRP (IV minus RV), and note bimodality when the table is fork-dated — the instrument recommendation (stock / calls / CC / CSP / none) must be the OUTPUT of that arithmetic, shown — using CHAIN-level midpoint IV and real quotes for the candidate strikes, never the underlying aggregate IV feed (they diverge; TSSI 71 vs 101 lesson). Then apply the TAX overlay: the loss branch must land in the intended tax year — an expiry past Dec 31 defers the loss and is excluded during harvest years unless the edge numerically dominates. Ratified 2026-09-03.)
End the deck with a machine-readable fence EXACTLY in this form (used to auto-arm sensors):
```json
{{"price_gates": [{{"level": 0.0, "direction": "below", "basis": "one line"}}], "event_gates": [{{"forms": ["8-K"], "why": "one line"}}], "catalyst_dates": [{{"date": "YYYY-MM-DD", "what": "one line", "confirmed": false}}], "immediate_entry": {{"action": "BUY", "approx_price": 0.0, "size_pct_of_book": 0.0, "basis": "one line"}} or null, "unverified": [{{"item": "one line", "instrument": "how the desk could drain it (XBRL pull / IBKR / connector name / 10-Q date / walk-around)", "drainable_now": true, "estimate": {{"range": "low-high w/ units", "basis": "alt-data comp / base rate used", "p": 0.0}} or null}}]}}
The "unverified" array MUST mirror every numbered item in the What-remains-unverified section — items listed only in prose are invisible to the drain queue and that is a PRD violation. When drainable_now is false the "estimate" object is REQUIRED (ratified 2026-09-03): estimate the quantity from available alt data — sibling public structures, industry base rates, comps — never leave a load-bearing unknown blank.
```
Tone: honest and symmetric; concessions and bench errors stated plainly. >=1 primary http citation somewhere.

=== EVIDENCE PACK ===
{pack[:8000]}
{adj}
=== SCIENCE BRIEF (deep-tech names only; empty otherwise) ===
{sci[:15000]}
=== RED BENCH ===
{red[:20000]}
=== BLUE BENCH ===
{blue[:20000]}"""
    from desk.court_runner import _dispatch, MODEL_COURT
    res = _dispatch(prompt, MODEL_COURT)
    text = res.get("text", "")
    if res.get("error") or not text:
        print(f"[deck_writer] {t}: dispatch failed ({res.get('error')})")
        return None
    req = REQUIRED + (["SCIENCE BRIEF DIGEST"] if sci else [])
    missing = [s for s in req if s.lower() not in text.lower()]
    if missing:
        print(f"[deck_writer] {t}: deck missing sections {missing} — NOT emailed; saved raw for session repair")
        (REPORTS / f"{t.replace('.','_')}_DECK_RAW_{datetime.date.today():%Y%m%d}.md").write_text(text)
        return None
    text = _arm_from_deck(t, text)
    md = REPORTS / f"{t.replace('.','_')}_PITCH_DECK_{datetime.date.today():%Y%m%d}.md"
    md.write_text(text)
    pdf = md.with_suffix(".pdf")
    try:
        subprocess.run(["pandoc", str(md), "-o", "/tmp/deck.html", "--standalone", "--embed-resources",
                        "--metadata", f"title={t} pitch deck", "-c", str(ROOT / "dd_reports/public/style.css")],
                       capture_output=True, timeout=60)
        subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless",
                        "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}",
                        "file:///tmp/deck.html"], capture_output=True, timeout=90)
    except Exception as e:
        print(f"[deck_writer] {t}: pdf render failed ({e}) — md only")
    if email:
        _email_deck(t, md, pdf if pdf.exists() else None)
    return md



def _arm_from_deck(t: str, text: str) -> str:
    """Parse the deck's machine-readable fence, arm PROVISIONAL sensors (ledger alerts,
    filing watches, dated packs), then rewrite the ARMED SENSORS section so the emailed
    deck shows what is NOW armed — decks must never ship with 'NONE ARMED' (principal,
    2026-08-08). Session adjudication ratifies or amends the provisional set."""
    import re as _re
    m = _re.search(r"```json\s*(\{.*?\})\s*```", text, _re.S)
    if not m:
        return text
    try:
        spec = json.loads(m.group(1))
    except Exception:
        return text
    try:
        rlp = ROOT / "desk/data/research_ledger.json"
        rl = json.loads(rlp.read_text())
        for g in spec.get("price_gates", []):
            if g.get("direction") == "below" and g.get("level"):
                for n in rl["names"]:
                    if n.get("ticker") == t:
                        n["alert_below"] = g["level"]; n["gate_basis"] = "deck-provisional: " + g.get("basis", "")
                        break
                else:
                    rl["names"].append({"ticker": t, "yf": t, "verdict": "WATCH", "state": "WATCH",
                                        "sleeve": "court_gates", "alert_below": g["level"],
                                        "gate_basis": "deck-provisional: " + g.get("basis", ""),
                                        "conviction": "deck-provisional gate (pending adjudication)"})
        rlp.write_text(json.dumps(rl, indent=1))
        # register every unverified item as WORK in the ledger (audit 2026-09-03: ~12
        # items/deck were shipping as prose while the drain queue got ~0 — the section
        # is a work queue, not decoration)
        uv = spec.get("unverified") or []
        if uv:
            ulp = ROOT / "desk/data/unverified_ledger.json"
            ul = json.loads(ulp.read_text())
            existing = {(r.get("ticker"), r.get("item")) for r in ul.get("items", [])
                        if isinstance(r, dict)}
            for it in uv:
                key = (t, it.get("item"))
                if it.get("item") and key not in existing:
                    ul.setdefault("items", []).append({
                        "ticker": t, "date": datetime.date.today().isoformat(),
                        "status": "OPEN", "item": it["item"],
                        "instrument": it.get("instrument", ""),
                        "drainable_now": bool(it.get("drainable_now")),
                        "source": "deck_writer auto-registration (pending session drain)"})
            ulp.write_text(json.dumps(ul, indent=1))
        if spec.get("event_gates"):
            fwp = ROOT / "desk/data/filing_watch.json"
            fw = json.loads(fwp.read_text())
            cik = None
            try:
                from desk.court_evidence import _cik
                cik = _cik(t)
            except Exception:
                pass
            if cik:
                eg = spec["event_gates"][0]
                fw.setdefault("targets", {})[t] = {"cik": cik, "since": datetime.date.today().isoformat(),
                    "until": (datetime.date.today() + datetime.timedelta(days=180)).isoformat(),
                    "forms_alert": eg.get("forms", ["8-K"]), "why": "deck-provisional: " + eg.get("why", "")}
                fwp.write_text(json.dumps(fw, indent=1))
        pkp = ROOT / "desk/data/resolution_packs.json"
        pk = json.loads(pkp.read_text())
        for c in spec.get("catalyst_dates", []):
            key = f"{t}|{c.get('date')}"
            if c.get("date") and key not in pk.get("packs", {}):
                pk["packs"][key] = {"tier": "B", "lifecycle": "open",
                    "created": "deck_writer provisional (pending adjudication)",
                    "adjudication": f"{t}: {c.get('what','')} (date confirmed={c.get('confirmed')})",
                    "branches": {"graded": "ratify/amend at session adjudication"}}
        pkp.write_text(json.dumps(pk, indent=1))
        ie = spec.get("immediate_entry")
        if ie and ie.get("action"):
            # Rung 0.5 (RE.7): headless can't reach the broker connector — write a
            # STAGING-REQUIRED row; the monitor emails it and the session stages the
            # instruction for principal approval (FIGR gap, 2026-08-08).
            spp = ROOT / "desk/data/staging_plan.json"
            sp = json.loads(spp.read_text())
            sp["actions"].append({"action": "STAGING-REQUIRED", "ticker": t,
                "side": ie["action"], "approx_price": ie.get("approx_price"),
                "size_pct_of_book": ie.get("size_pct_of_book"), "status": "pending_session",
                "planned_utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "provenance": {"basis": "deck-proposed immediate entry (pending adjudication): " + ie.get("basis", "")}})
            spp.write_text(json.dumps(sp, indent=1))
    except Exception as e:
        print(f"[deck_writer] {t}: provisional arming failed ({e}) — deck ships with snapshot sensors only")
    fresh = _sensors(t)
    text = __import__("re").sub(r"## ARMED SENSORS.*?(?=\n## )",
        f"## ARMED SENSORS\n\n(armed provisionally with this deck; session adjudication ratifies)\n\n{fresh}\n\n",
        text, count=1, flags=__import__("re").S)
    return text

def _email_deck(t: str, md: Path, pdf: Path | None):
    """Full deck in the body (the email IS the brief), PDF attached when available."""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        from desk.mailer import EMAIL, _CRED
        if not _CRED.exists():
            print("[deck_writer] no smtp cred — deck not emailed")
            return
        m = MIMEMultipart()
        m["Subject"] = f"[SignalOS] COURT COMPLETE — {t} pitch deck (proposed, pending adjudication)"
        m["From"] = m["To"] = EMAIL
        m.attach(MIMEText(md.read_text()))
        if pdf and pdf.exists():
            a = MIMEApplication(pdf.read_bytes(), _subtype="pdf")
            a.add_header("Content-Disposition", "attachment", filename=pdf.name)
            m.attach(a)
        pw = _CRED.read_text().strip().replace(" ", "")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as srv:
            srv.login(EMAIL, pw)
            srv.send_message(m)
        print(f"[deck_writer] {t}: deck emailed ({pdf.name if pdf and pdf.exists() else 'md only'})")
    except Exception as ex:
        print(f"[deck_writer] {t}: email failed ({ex})")


_EXCH_SUFFIX = ("L", "PA", "ST", "T", "TA", "KS", "HK", "SI", "AX", "TO", "BR", "MI",
                "DE", "SW", "VI", "MC", "AS", "OL", "HE", "CO", "NS", "BO", "SA", "MX")


def _real_ticker(stem: str) -> str:
    """Artifact FILENAME stem -> the ticker the rest of the desk uses.

    Artifacts are written with dots flattened to underscores (ALBLD.PA -> ALBLD_PA_COURT_RED_*.md),
    so a sweep that discovers names by globbing filenames yields the FLATTENED form. `_latest` and
    the classification lookup both re-flatten and so tolerate either — but the MARKET DATA path does
    not: `_yf_symbol` passes its argument through verbatim, so the first backfill sent "W5_ST" to
    yfinance, got `Quote not found for symbol: W5_ST`, and emitted a deck with NO price data at all
    while reporting success. Every foreign listing still owed a deck (BMS_L, THS_L, AVAP_L,
    ALBLD_PA) would have failed the same way.

    Resolution order is evidence-first: an existing classification file settles which form is real.
    The suffix list is only the fallback for a name that has no classification yet, and it is
    deliberately a KNOWN-EXCHANGE list rather than "replace every underscore" — a genuine
    underscore in a ticker must not be silently rewritten into a dot.
    """
    ec = ROOT / "desk" / "data" / "edge_classifications"
    dotted = stem.replace("_", ".")
    # The FILENAME cannot settle this — classification files are themselves written with dots
    # flattened (ALBLD.PA -> ALBLD_PA.json), so "the underscore file exists" is not evidence that
    # the underscore form is the ticker. The `ticker` FIELD INSIDE the file is the canonical value.
    for cand in (ec / f"{stem}.json", ec / f"{dotted}.json"):
        if cand.exists():
            try:
                real = str(json.loads(cand.read_text()).get("ticker") or "").strip()
            except (OSError, ValueError):
                real = ""
            if real:
                return real
    head, _, tail = stem.rpartition("_")
    return dotted if head and tail in _EXCH_SUFFIX else stem


def backfill(limit: int = 6, dry_run: bool = False) -> list[str]:
    """Build the deck for any FULLY COURTED name that never got one.

    WHY (2026-08-17, principal: "did we write any pitch decks?"). build_deck was called from
    exactly ONE place: court_runner's COURT_BLUE branch. So a name reached its deck only by
    travelling the conveyor. Every court adjudicated by hand in-session — LIND, MTN, NCLH, OTF,
    OBDC, TCPC — had two full benches on disk, a written verdict, armed gates, and NO reader-facing
    artifact. Same failure as the un-emailed verdicts: the automated path performs the closing
    step, the manual path silently omits it, and nothing anywhere notices the difference.

    ELIGIBILITY IS RED+BLUE ON DISK, NOT ADJUDICATION. A name killed before it was ever courted
    (PPL/WY at trap-verify, the quality_drawdown inline kills) is owed no deck and must not be
    counted as a gap — there is no court to render. Requiring both bench artifacts makes the test
    "was a court held?", which is the actual precondition for a deck.

    Bounded by `limit` because each deck is an LLM call of 2-5 minutes; this is a sweep meant to
    run at the head of a drain, not a batch job.
    """
    art_dir = ROOT / "desk" / "data" / "court_artifacts"
    have_deck, courted = set(), set()
    for p in (ROOT / "desk" / "reports").glob("*_PITCH_DECK_*"):
        have_deck.add(p.name.split("_PITCH_DECK_")[0])
    reds, blues = set(), set()
    for p in art_dir.glob("*_COURT_*"):
        stem = p.name.split("_COURT_")[0]
        (reds if "_COURT_RED" in p.name else blues if "_COURT_BLUE" in p.name else set()).add(stem)
    courted = reds & blues
    owed = sorted(t for t in courted if t not in have_deck and t.replace("_", ".") not in have_deck)

    # ORDER BY WHAT A READER ACTUALLY NEEDS. The first sweep found 31 deck-less courted names and
    # alphabetical order would have spent the budget on ABAT/AGL/ASAN while MNDY — an outright BUY
    # verdict — sat undecked since 07-01. Rank: names we HOLD first (a deck on a position is the
    # one a reader opens), then ACTIONABLE verdicts (buy/ownable/starter/advance), then recency.
    # NOTE the disposition lives in free-text `verdict` here, not a `recommendation` field: that key
    # is absent from most of these files, so keying off it silently scores every one of them zero.
    ACTIONABLE = ("BUY", "OWNABLE", "STARTER", "ADVANCE", "ACCUMULATE", "ADD")
    try:
        pc = json.loads((ROOT / "desk/ui/data/positions_cache.json").read_text())
        held = {str(p.get("symbol", "")).upper() for p in pc.get("positions", [])
                if float(p.get("qty") or 0) != 0}
    except Exception:
        held = set()

    def _rank(t: str):
        d, ecdir = {}, ROOT / "desk" / "data" / "edge_classifications"
        for cand in (ecdir / f"{t}.json", ecdir / f"{t.replace('_', '.')}.json"):
            if cand.exists():
                try:
                    d = json.loads(cand.read_text())
                except (OSError, ValueError):
                    d = {}
                break
        v = (str(d.get("verdict") or "") + " " + str(d.get("recommendation") or "")).upper()[:200]
        return (0 if t.replace("_", ".") in held or t in held else 1,
                0 if any(k in v for k in ACTIONABLE) else 1,
                str(d.get("date") or ""))

    ranked = {t: _rank(t) for t in owed}
    owed.sort(key=lambda t: ranked[t][2], reverse=True)          # newest first, then stable-sort
    owed.sort(key=lambda t: ranked[t][:2])                       # held, then actionable, wins
    if dry_run or not owed:
        print(f"[deck_writer] backfill: {len(owed)} courted name(s) without a deck: {owed}")
        return owed
    built = []
    for t in owed[:limit]:
        try:
            if build_deck(_real_ticker(t)):
                built.append(t)
        except Exception as e:
            print(f"[deck_writer] backfill {t} failed ({type(e).__name__}: {e})")
    if len(owed) > limit:
        print(f"[deck_writer] backfill: {len(owed) - limit} still owed (limit {limit}) — {owed[limit:]}")
    return built


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--backfill":
        backfill(dry_run="--dry-run" in sys.argv)
    else:
        build_deck(sys.argv[1])
