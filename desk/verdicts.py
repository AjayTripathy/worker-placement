"""verdicts — the STRUCTURED verdict system (2026-07-03, after the third free-text-matching bug:
'OWN' substring hit OWNABLE and mis-bucketed IBEX; before that, the first-32-chars bucket rule and
the 'PENDING_RED_TEAM —' phrasing workaround).

Schema (on ledger names AND edge_classifications records):
  state:  one of STATES (closed enum — the ONLY thing machines may route on)
  stage:  one of STAGES or None (pipeline position — was previously smuggled into verdict prose)
  note:   free prose (humans only; no consumer may match on it)

All mutations go through set_verdict() -> validated + mirrored to ledger & record + appended to the
audit log (desk/data/verdict_audit.jsonl, append-only). The dashboard's POST /api/verdict endpoint
calls this; it mutates RESEARCH METADATA only — never orders, never positions.
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
EC = ROOT / "desk" / "data" / "edge_classifications"
AUDIT = ROOT / "desk" / "data" / "verdict_audit.jsonl"

STATES = ("HELD", "OWN", "OWNABLE", "STARTER", "WATCH", "WAIT", "NOT_YET",
          "TO_DILIGENCE", "AVOID", "SHORT")
STAGES = ("GENERATED", "TRAP_SCREENED", "DD_DONE", "RED_TEAM_PENDING",
          "RED_TEAM_DONE", "ADJUDICATED", None)
# routing groups — importable so no consumer ever writes its own membership test again
BUYISH = ("OWNABLE", "STARTER", "HELD", "OWN")
HELDISH = ("HELD", "OWN")
DEADISH = ("AVOID", "SHORT")


class InvalidVerdict(Exception):
    pass


def parse_legacy(text: str | None) -> tuple[str | None, str | None]:
    """Best-effort (state, stage) from legacy free text — MIGRATION USE ONLY."""
    if not text:
        return None, None
    u = str(text).upper()
    stage = "RED_TEAM_PENDING" if "PENDING_RED_TEAM" in u else None
    for s in STATES:                       # longest-first so OWNABLE beats OWN
        pass
    for s in sorted(STATES, key=len, reverse=True):
        if u.startswith(s) or f" {s}" in u[:40]:
            return s, stage
    if "BUY" in u[:32] or "DROP" not in u and "PASS" not in u and "HOLD" in u[:20]:
        return None, stage
    return None, stage


def get_verdict(ticker: str) -> dict:
    """Structured verdict, ledger-authoritative."""
    state = stage = note = None
    try:
        for n in json.loads(LEDGER.read_text()).get("names", []):
            if n["ticker"] == ticker:
                state = n.get("state") or (n.get("verdict") if n.get("verdict") in STATES else None)
                stage = n.get("stage")
                note = n.get("conviction")
                break
    except Exception:
        pass
    f = EC / f"{ticker}.json"
    if f.exists():
        try:
            rec = json.loads(f.read_text())
            state = state or rec.get("verdict_state")
            stage = stage or rec.get("verdict_stage")
            note = note or rec.get("verdict")
        except Exception:
            pass
    return {"ticker": ticker, "state": state, "stage": stage, "note": note}


def set_verdict(ticker: str, state: str, stage: str | None = None,
                note: str | None = None, source: str = "api") -> dict:
    if state not in STATES:
        raise InvalidVerdict(f"state must be one of {STATES}, got {state!r}")
    if stage not in STAGES:
        raise InvalidVerdict(f"stage must be one of {[s for s in STAGES if s]}, got {stage!r}")
    # ledger (authoritative)
    led = json.loads(LEDGER.read_text())
    hit = False
    for n in led.get("names", []):
        if n["ticker"] == ticker:
            n["verdict"] = state          # backward compat: ledger consumers read .verdict
            n["state"] = state
            n["stage"] = stage
            if note:
                n["conviction"] = note
            hit = True
    if not hit:
        raise InvalidVerdict(f"{ticker} not in the research ledger — upsert it first (desk.ledger_add)")
    LEDGER.write_text(json.dumps(led, indent=1))
    # record mirror — dotted tickers (KALMAR.HE) store as underscored files (KALMAR_HE.json)
    f = EC / f"{ticker}.json"
    if not f.exists():
        f = EC / f"{ticker.replace('.', '_')}.json"
    if f.exists():
        rec = json.loads(f.read_text())
        rec["verdict_state"], rec["verdict_stage"] = state, stage
        f.write_text(json.dumps(rec, indent=1))
    # append-only audit
    entry = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "ticker": ticker,
             "state": state, "stage": stage, "note": (note or "")[:200], "source": source}
    with open(AUDIT, "a") as fh:
        fh.write(json.dumps(entry) + "\n")
    return get_verdict(ticker)


def all_verdicts() -> list[dict]:
    out = []
    try:
        for n in json.loads(LEDGER.read_text()).get("names", []):
            out.append({"ticker": n["ticker"],
                        "state": n.get("state") or (n.get("verdict") if n.get("verdict") in STATES else None),
                        "stage": n.get("stage"), "note": (n.get("conviction") or "")[:160]})
    except Exception:
        pass
    return out
