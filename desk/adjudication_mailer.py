"""adjudication_mailer — every verdict reaches the inbox, exactly once.

WHY THIS EXISTS (2026-08-18, principal: "these courts not emailing their results?"). They were
not. The conveyor wrote verdicts to edge_classifications, upserted the ledger and re-rendered the
dashboard — and then stopped. Notification happened only when a human happened to call
`deck_writer.build_deck()`. The audit that prompted this: 25 adjudications on 08-17/18, 8 decks
emailed, ZERO emails on 08-18. Seventeen verdicts existed only in files nobody was told to open.

That is the "did we actually" failure in its purest form: the pipeline COMPLETED and nothing
ACTED. A verdict the principal never sees is indistinguishable from one never reached — and worse
than a missing verdict, because the desk believes the work is done.

WHAT IT SENDS. One digest per run, grouped by disposition, and for each name: the verdict line,
the single reason, the armed gate, and whether the book is exposed. Deliberately NOT the full
adjudication text — the classification file and the deck hold that. This is the notification, and
the doctrine is "subject carries the event, facts first".

EXACTLY ONCE. A sent-log keyed by ticker + adjudication date means a re-run never re-sends, and a
RE-ADJUDICATION (new date, e.g. a vacated verdict re-courted) sends again — which is correct: the
MFIC kill was vacated and re-courted the same day and both outcomes are separately notifiable.

    python3 -m desk.adjudication_mailer              # send anything unsent
    python3 -m desk.adjudication_mailer --dry-run    # show what would go
    python3 -m desk.adjudication_mailer --since 2026-08-17
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EC = ROOT / "desk" / "data" / "edge_classifications"
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
SENTLOG = ROOT / "desk" / "data" / "adjudication_mail_sent.json"


def _sent() -> dict:
    try:
        return json.loads(SENTLOG.read_text())
    except (OSError, ValueError):
        return {}


def _held() -> dict:
    """Ticker -> position note, so a verdict on something we OWN is never buried in a digest."""
    try:
        import subprocess  # positions come from the cached book, never a live broker call here
        pc = json.loads((ROOT / "desk/ui/data/positions_cache.json").read_text())
        return {str(p.get("symbol", "")).upper(): p for p in pc.get("positions", [])
                if float(p.get("qty") or 0) != 0}
    except Exception:
        return {}


def _one_line(d: dict) -> str:
    """First sentence of the verdict — the reason, not the essay."""
    v = str(d.get("verdict") or "").strip().replace("\n", " ")
    for stop in (". ", " — ", "; "):
        if stop in v[:400]:
            return v[: v.index(stop) + 1].strip()
    return v[:260]


# DEFAULT LOOKBACK + BLAST GUARD (added minutes after the first live run, which caused exactly
# the accident it now prevents). The sent-log starts EMPTY, so a run with no --since treated every
# historical adjudication as unsent and mailed 298 verdicts in one digest — 34 of them on names we
# hold. An unbounded sweep over a fresh log is a spam event, and "exactly once" is no protection
# when the log has never been written. Two guards: a default window, and a refusal to send an
# implausibly large batch without an explicit override.
DEFAULT_LOOKBACK_DAYS = 7
MAX_BATCH = 40


def collect(since: str | None = None, resend: bool = False) -> list[dict]:
    sent = _sent()
    if since is None and not resend:
        from datetime import timedelta
        since = (date.today() - timedelta(days=DEFAULT_LOOKBACK_DAYS)).isoformat()
    out = []
    for f in sorted(EC.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        t, dt = d.get("ticker") or f.stem, str(d.get("date") or "")
        if not dt:
            continue
        if since and dt < since:
            continue
        key = f"{t}|{dt}"
        if not resend and key in sent:
            continue
        gates = d.get("reopen_gates") or []
        out.append({
            "ticker": t, "date": dt, "key": key,
            "recommendation": (d.get("recommendation") or "—"),
            "conviction": d.get("conviction"),
            "why": _one_line(d),
            "gate": (str(gates[0])[:230] if gates else "no gate recorded"),
            "process": len(d.get("process_findings") or []),
        })
    return sorted(out, key=lambda r: (r["date"], r["ticker"]))


def send(since: str | None = None, dry_run: bool = False, resend: bool = False,
         force: bool = False) -> dict:
    rows = collect(since, resend)
    if not rows:
        print("[adjudication_mailer] nothing unsent")
        return {"sent": 0, "rows": []}
    if len(rows) > MAX_BATCH and not force:
        print(f"[adjudication_mailer] REFUSING to send {len(rows)} verdicts in one digest "
              f"(cap {MAX_BATCH}). This is the fresh-sent-log blast guard — a batch this size "
              f"means the log is empty or the window is too wide, not that {len(rows)} things "
              f"just happened. Narrow with --since, or pass --force if you truly mean it.")
        return {"sent": 0, "refused": len(rows), "rows": rows}

    held = _held()
    buckets: dict[str, list] = {}
    for r in rows:
        rec = r["recommendation"].upper()
        b = ("KILL / AVOID" if "KILL" in rec or "AVOID" in rec
             else "WATCH" if "WATCH" in rec
             else "ESCALATE" if "ESCALATE" in rec
             else "VACATED / RE-COURT" if "VACAT" in rec or "RE-COURT" in rec
             else "OTHER")
        buckets.setdefault(b, []).append(r)

    sections = []
    owned = [r for r in rows if r["ticker"].upper() in held]
    if owned:
        sections.append(("⚠ VERDICTS ON NAMES WE HOLD",
                         [f"{r['ticker']} — {r['recommendation']}: {r['why']}" for r in owned]))
    for b in ("ESCALATE", "VACATED / RE-COURT", "WATCH", "KILL / AVOID", "OTHER"):
        if b not in buckets:
            continue
        lines = []
        for r in buckets[b]:
            lines.append(f"{r['ticker']} ({r['date']}) — {r['recommendation']}"
                         + (f", conviction {r['conviction']}" if r.get("conviction") else ""))
            lines.append(f"    {r['why']}")
            lines.append(f"    GATE: {r['gate']}")
            if r["process"]:
                lines.append(f"    ({r['process']} process finding(s) recorded)")
        sections.append((f"{b} — {len(buckets[b])}", lines))

    n = len(rows)
    kills = len(buckets.get("KILL / AVOID", []))
    watches = len(buckets.get("WATCH", []))
    subject = (f"ADJUDICATED: {n} verdict{'s' if n != 1 else ''} — "
               f"{kills} kill / {watches} watch"
               + (f" — {len(owned)} ON A NAME WE HOLD" if owned else "")
               + f" ({', '.join(r['ticker'] for r in rows[:6])}"
               + ("…" if n > 6 else "") + ")")
    footer = ("Full reasoning: desk/data/edge_classifications/<TICKER>.json · gates are armed in "
              "the ledger · decks are built separately and are not implied by this notice.")

    if dry_run:
        print(f"[adjudication_mailer] DRY RUN — would send {n}")
        print(f"  subject: {subject}")
        for h, body in sections:
            print(f"  [{h}]")
            for l in (body if isinstance(body, list) else [body])[:6]:
                print(f"      {l[:150]}")
        return {"sent": 0, "would_send": n, "rows": rows}

    from desk.mailer import send as msend
    ok = msend(subject, sections, footer=footer)
    if ok:
        log = _sent()
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for r in rows:
            log[r["key"]] = stamp
        SENTLOG.write_text(json.dumps(log, indent=1))
    print(f"[adjudication_mailer] {'sent' if ok else 'SEND FAILED for'} {n} verdict(s)"
          + (f" — {len(owned)} on held names" if owned else ""))
    return {"sent": n if ok else 0, "ok": ok, "rows": rows}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resend", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help=f"override the {MAX_BATCH}-verdict blast guard")
    a = ap.parse_args()
    send(since=a.since, dry_run=a.dry_run, resend=a.resend, force=a.force)
