"""gauntlet_sentinel — DURABLE morning catalyst detection (promoted from a session cron, 2026-07-04).

Runs weekday 6:15am via launchd (com.signalos.gauntlet). Self-gates on resolution-pack dates:
quiet days exit in <1s. On pack days: polls EDGAR full-text + the company wire for the print,
extracts what's mechanically extractable, writes desk/data/gauntlet_flags.json (the dashboard
banner + the headless agent's gate), and notifies via macOS notification + optional ntfy.sh
phone push (set NTFY_TOPIC in the environment or desk/data/ntfy_topic.txt).

Detection is Tier-1 (durable, dumb, reliable). Judgment stays with the agent layer:
the headless morning run (ops/gauntlet_headless.sh) or the interactive session adjudicates
against the pack and stages. READ-ONLY w.r.t. the broker.
"""
from __future__ import annotations
import json, datetime, subprocess, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "desk" / "data" / "resolution_packs.json"
FLAGS = ROOT / "desk" / "data" / "gauntlet_flags.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
CIK_MAP_PATH = ROOT / "desk" / "data" / "cik_map.json"
_CIK_MAP = None


def _today_packs() -> list[tuple[str, str, dict]]:
    today = datetime.date.today().isoformat()
    packs = json.loads(PACKS.read_text()).get("packs", {})
    out = []
    monday = datetime.date.today().weekday() == 0
    for key, v in packs.items():
        t, d = key.split("|")
        if d == today or (d == "weekly" and monday):
            out.append((t, d, v))
    return out


def _cik(ticker: str) -> str | None:
    """Resolve a ticker to its zero-padded EDGAR CIK. We gate on the FILER, not the token:
    a full-text search for a common-word ticker ("NOW", "G", "J", "EG"...) matches UNRELATED
    companies' 8-Ks that merely contain the word and false-fires 'the report is out'. Entity
    resolution before dispatch — the referent is the CIK, never the string."""
    global _CIK_MAP
    if _CIK_MAP is None:
        try:
            _CIK_MAP = json.loads(CIK_MAP_PATH.read_text())
        except Exception:
            _CIK_MAP = {}
    c = _CIK_MAP.get(ticker.upper())
    return str(c).zfill(10) if c else None


def _now_et():
    """Current Eastern time, or None if zoneinfo is unavailable (then the timing gate is skipped
    and we rely on the CIK+Item-2.02 gate, which already can't fire before the filing exists)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        return None


def _session(pack: dict) -> str | None:
    """'amc' | 'bmo' | None — when the print lands, so we don't scan before it can exist.
    Prefers an explicit pack['session']; otherwise infers from the pack prose."""
    s = (pack.get("session") or "").lower()
    if s in ("amc", "bmo"):
        return s
    txt = (str(pack.get("adjudication", "")) + " " + str(pack.get("catalyst", ""))).lower()
    if any(k in txt for k in ("after close", "after the close", "after market", "post-market", "amc")):
        return "amc"
    if any(k in txt for k in ("before open", "before the open", "before the bell", "pre-market", "premarket", "bmo")):
        return "bmo"
    return None


def _efts_hits(ticker: str) -> list[str]:
    """The company's OWN earnings 8-K filed TODAY (the print-landed signal).

    Entity-resolved: pull the filer's EDGAR submissions by CIK and require an 8-K carrying
    Item 2.02 (Results of Operations) dated today. This replaces a naive full-text search for
    the ticker STRING (`q="NOW"`), which matched any of today's 8-Ks containing the word and so
    false-fired for common-word tickers. Gate on the referent (CIK) + the earnings item."""
    cik = _cik(ticker)
    if not cik:
        return []                       # unresolved (e.g. foreign filer) -> use ir_watch, never guess
    today = datetime.date.today().isoformat()
    url = "https://data.sec.gov/submissions/CIK%s.json" % cik
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=20) as r:
            recent = json.load(r).get("filings", {}).get("recent", {})
    except Exception:
        return []
    forms = recent.get("form", []); dates = recent.get("filingDate", [])
    items = recent.get("items", []); accns = recent.get("accessionNumber", [])
    out = []
    for i, form in enumerate(forms):
        if not str(form).startswith("8-K"):
            continue
        if (dates[i] if i < len(dates) else "") != today:
            continue
        if "2.02" not in (items[i] if i < len(items) else ""):   # Results of Operations = the earnings tell
            continue
        out.append(accns[i] if i < len(accns) else "")
    return out[:3]


EMAIL = "4tripathy@gmail.com"


def _ascii(x: str) -> str:
    """HTTP headers are latin-1; ntfy titles/messages with em-dashes etc. must be sanitized."""
    return x.encode("ascii", "replace").decode()


def _notify(msg: str):
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification "{msg}" with title "SignalOS Gauntlet" sound name "Glass"'],
                       timeout=10)
    except Exception:
        pass
    topic = None
    tf = ROOT / "desk" / "data" / "ntfy_topic.txt"
    if tf.exists():
        topic = tf.read_text().strip()
    if topic:
        try:
            req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=_ascii(msg).encode(),
                                         headers={"Title": "SignalOS Gauntlet", "Priority": "high"})
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass
    _email(msg)


def _email(msg: str):
    """Routes through desk.mailer (the house legibility standard). The subject carries the
    actual event — the old fixed 'catalyst event' subject made every alert identical in
    the inbox list (2026-07-30 user directive: all emails strive to be legible)."""
    try:
        from desk.mailer import event_subject, send_raw
        send_raw(event_subject(msg), msg)
    except Exception:
        pass


def main():
    try:                       # price-band watch rides the same schedule
        from desk.band_watch import main as _bands
        _bands()
    except Exception as e:
        print(f"[band_watch] skipped: {e}")
    try:                       # Hormuz physical-data watch (tanker sleeve triple-kill leg 1)
        from desk.hormuz_watch import main as _hormuz
        _hormuz()
    except Exception as e:
        print(f"[hormuz_watch] skipped: {e}")
    try:                       # NHC hurricanes + the ONON promo tripwire (Mondays)
        from desk.season_watch import main as _season
        _season()
    except Exception as e:
        print(f"[season_watch] skipped: {e}")
    try:                       # T+1 covering detector (SpaceX proxy-hedge basket)
        from desk.squeeze_watch import main as _squeeze
        _squeeze()
    except Exception as e:
        print(f"[squeeze_watch] skipped: {e}")
    try:                       # refresh the gauntlet/Brier review page after each watcher cycle
        from desk.gauntlet_book import main as _gbook
        _gbook()
    except Exception as e:
        print(f"[gauntlet_book] skipped: {e}")
    due = _today_packs()
    if not due:
        print("quiet day — no packs due")
        return
    flags = {"date": datetime.date.today().isoformat(), "events": []}
    now_et = _now_et()
    for t, d, pack in due:
        # timing gate: an AMC name cannot have published before ~16:00 ET, so don't scan (and
        # can't false-fire "the report is out"); fall through to the "decision day, not yet" note.
        amc_early = _session(pack) == "amc" and now_et is not None and now_et.hour < 16
        if amc_early:
            print(f"[gauntlet] {t}: AMC print — holding detection until 16:00 ET (now {now_et:%H:%M} ET)")
        hits = [] if amc_early else (_efts_hits(t.split(".")[0]) if t[0].isalpha() and "." not in t else [])
        # non-EDGAR issuers: poll the IR page named in the pack (Canadian/foreign filers are EDGAR-blind)
        iw = pack.get("ir_watch")
        if iw and not hits:
            try:
                req = urllib.request.Request(iw["url"], headers={"User-Agent": "Mozilla/5.0 (Macintosh) Chrome/126.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    page = r.read(200_000).decode(errors="ignore").lower()
                found = [m for m in iw.get("match", []) if m.lower() in page]
                if found:
                    hits = [f"IR-PAGE match: {', '.join(found)}"]
            except Exception:
                pass
        ev = {"ticker": t, "pack_key": f"{t}|{d}", "print_detected": bool(hits),
              "filings": hits, "adjudication": pack.get("adjudication", "")[:200],
              "branches": list((pack.get("branches") or {}).keys())}
        flags["events"].append(ev)
        # reader-facing copy: plain language, per the reports doctrine — say what
        # happened, what the pre-agreed responses are, and what happens next.
        plain = pack.get("plain_summary") or pack.get("adjudication", "")[:180]
        # pre-committed trade block: authored into the pack while the desk HAD broker
        # access (the sentinel itself stays broker-blind). Branch -> the exact action,
        # naming resting order IDs. The email can only recommend; submission/cancel
        # stays a human tap in TWS/IBKR — the envelopes-only rail.
        trade = pack.get("trade") or {}
        tb = "\n".join(f"  if {br}: {ln}" for br, ln in trade.items())
        tb = f"\nTHE TRADE (pre-committed {pack.get('trade_asof', '')}):\n{tb}" if tb else ""
        # event_class distinguishes a COMPANY EARNINGS print (a report that "lands") from a
        # POLITICAL/MACRO/PEER event where NO company report will publish — the CIB mislabel:
        # the sentinel was framing a Colombia Congress vote as "the company hasn't published yet".
        ec = pack.get("event_class")            # e.g. "POLITICAL/MACRO — <what it actually is>"
        if hits:
            msg = (f"{t}: THE REPORT IS OUT (detected {hits[0][:60]}).\n"
                   f"What we're checking: {plain}\n"
                   f"Pre-agreed responses: {'; '.join(ev['branches'])[:200]}.{tb}\n"
                   f"NEXT: the desk adjudicates and emails you the verdict in plain words — "
                   f"no action needed from you unless that email (or a TRADE line above) asks.")
        elif ec:                                # non-company event: DON'T imply a company print is coming
            msg = (f"{t}: today is the resolution date for a NON-COMPANY event — {ec}.\n"
                   f"What we're checking: {plain}\n"
                   f"NEXT: the desk adjudicates on the facts at the boundary (there is no company report to 'land'); "
                   f"you'll get a plain-words verdict.{tb}")
        else:
            msg = (f"{t}: today is decision day but the company hasn't published yet. "
                   f"The watcher keeps checking; you'll get a 'REPORT IS OUT' email when it lands, "
                   f"then a plain-words verdict.{tb}")
        _notify(msg)
        print(f"  {t}: {'PRINT LANDED' if hits else 'pack day — print not yet detected'}")
    FLAGS.write_text(json.dumps(flags, indent=1))
    print(f"[-> gauntlet_flags.json  ({len(due)} pack events today)]")


if __name__ == "__main__":
    main()
