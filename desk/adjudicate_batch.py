"""adjudicate_batch — the STAMP-AND-SHIP rail for a batch of session rulings (2026-09-16).

The adjudicator (session) decides; this module only RECORDS a ruling everywhere the desk reads
one, in a single pass, so a 50-name arrears clears with one summary email instead of fifty deck
re-renders:
  1. desk/data/edge_classifications/{T}.json  — dated TODAY (deck_writer's classification_is_current
     keys on this date; a stale date would render the deck PENDING)
  2. court_queue: advance to DONE (ruling recorded, name may be owned/watched) or KILLED
  3. resolution_packs: one pack per dated reopen gate
  4. the deck (if one exists): header re-stamped + a short ADJUDICATION addendum, re-rendered
     to PDF — but EMAILED ONLY when `ship=True` (starters / owned names); flats get the stamp
     and the PDF silently
  5. one batch artifact in court_artifacts + ONE summary email (subject carries the counts)

    from desk.adjudicate_batch import Ruling, apply
    apply([Ruling(ticker, recommendation, verdict, gates, stage, conviction, pack=(key, text), ship=False)], label)
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parents[1]
EC = ROOT / "desk" / "data" / "edge_classifications"
ART = ROOT / "desk" / "data" / "court_artifacts"
PACKS = ROOT / "desk" / "data" / "resolution_packs.json"


@dataclass
class Ruling:
    ticker: str
    recommendation: str            # e.g. "FLAT — named kill: ...", "STARTER 0.5% at <=X", "HOLD — NO ADD"
    verdict: str                   # 2-6 sentences: what survived both benches, what was vacated, why
    gates: list = field(default_factory=list)      # reopen gates, verbatim strings
    stage: str = "KILLED"          # KILLED (flat, not owned) | DONE (owned/watch/starter)
    conviction: int = 7
    pack: tuple | None = None      # (pack_key "T|YYYY-MM-DD", adjudication text) for a DATED gate
    process: list = field(default_factory=list)    # bench errors / pack defects to disclose
    ship: bool = False             # email the deck (starters/owned only)


def _stamp_deck(t: str, hdr: str, body: str, ship: bool) -> str | None:
    from desk.deck_update import latest_deck, render_pdf, append_and_ship
    md = latest_deck(t)
    if md is None:
        return None
    lines = md.read_text().split("\n")
    idx = next((i for i in range(1, min(8, len(lines))) if lines[i].startswith("**")), None)
    if idx is None:
        lines.insert(1, hdr)
    else:
        lines[idx] = hdr
    md.write_text("\n".join(lines))
    if ship:
        append_and_ship(t, hdr.strip("*")[:120], body, email=True)
    else:
        stamp = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%MZ")
        md.write_text(md.read_text() + f"\n\n---\n\n## ADJUDICATION — {stamp}\n\n{body}\n")
        render_pdf(md)
    return str(md)


def apply(rulings: list[Ruling], label: str, email: bool = True) -> dict:
    from desk.court_queue import advance
    today = dt.date.today().isoformat()
    now = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    packs = json.loads(PACKS.read_text())
    art = [f"## {label} — SESSION ADJUDICATION (FABLE, {today}) — {len(rulings)} rulings\n"]
    counts: dict[str, int] = {}
    for r in rulings:
        ec = EC / f"{r.ticker.replace('.', '_')}.json"
        if not ec.exists():
            ec = EC / f"{r.ticker}.json"
        prev = json.loads(ec.read_text()) if ec.exists() else {}
        prev.update({"date": today, "recommendation": r.recommendation, "conviction": r.conviction,
                     "verdict": r.verdict, "reopen_gates": r.gates, "process_findings": r.process,
                     "court": label, "artifact": str(ART / f"{label}_{today.replace('-', '')}.md")})
        ec.write_text(json.dumps(prev, indent=1, ensure_ascii=False))
        try:
            advance(r.ticker, r.stage, artifact=str(ART / f"{label}_{today.replace('-', '')}.md"),
                    note=f"session ruling: {r.recommendation[:80]}")
        except KeyError:
            pass
        if r.pack:
            packs["packs"][r.pack[0]] = {"tier": "B", "lifecycle": "open", "created": f"{label} {today}",
                                         "adjudication": r.pack[1], "branches": {"clears": "re-court", "fails": "dead"}}
        hdr = (f"**ADJUDICATED {today} — {r.recommendation} (conviction {r.conviction}/10).** "
               f"{'The court found nothing to own at this price; the reopen gates below are the only path back.' if r.stage == 'KILLED' else ''}")
        body = r.verdict + ("\n\nREOPEN GATES: " + " · ".join(r.gates) if r.gates else "") + \
               ("\n\nPROCESS: " + " · ".join(r.process) if r.process else "")
        deck = _stamp_deck(r.ticker, hdr, body, r.ship)
        art.append(f"**{r.ticker} — {r.recommendation} ({r.conviction}/10).** {r.verdict}" +
                   (f"\nGATES: {' · '.join(r.gates)}" if r.gates else "") +
                   (f"\nPROCESS: {' · '.join(r.process)}" if r.process else "") +
                   (f"\n(deck {'shipped' if r.ship else 'stamped, not emailed'}: {pathlib.Path(deck).name})" if deck else "\n(no deck)") + "\n")
        counts[r.stage] = counts.get(r.stage, 0) + 1
    packs["asof"] = now
    PACKS.write_text(json.dumps(packs, indent=1))
    path = ART / f"{label}_{today.replace('-', '')}.md"
    path.write_text("\n".join(art))
    if email:
        try:
            from desk.mailer import send_raw
            starters = [r.ticker for r in rulings if r.ship]
            send_raw(f"ADJUDICATED {len(rulings)}: {counts} — {label}" + (f" · SHIPPED {starters}" if starters else ""),
                     "\n".join(art)[:60000])
        except Exception as e:
            print(f"[adjudicate_batch] mail failed: {e}")
    return {"artifact": str(path), "counts": counts}
