"""filing_watch — per-ticker EDGAR ALL-FORMS fast poll (born 2026-07-28 from the YSS red team).

THE GAP IT CLOSES (red-team finding, severity 6, CONFIRMED): the desk's kill-facts for
lockup-window flow trades include "sponsor files a secondary" (Form 144 / 4 / 424B) and
"the short report matures" (8-K, S-1 resale, SC 13D/G) — but news_scan reads ONLY
8-K/NT forms hourly, and intraday_sentinel is price-only. A filing could hit EDGAR,
gap the stock through a resting rung, and the desk would learn post-fill. A condition
the desk cannot enforce in real time is decoration, not a condition.

Targets live in desk/data/filing_watch.json with an expiry per ticker (windows end;
watchers must not accrete forever). Rides intraday_sentinel's */15 RTH crontab via a
defensive hook + runs standalone:  python3 -m desk.filing_watch
Alerts via the sentinel plumbing (macOS + ntfy + email). READ-ONLY.
"""
from __future__ import annotations
import json, datetime, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "desk" / "data" / "filing_watch.json"
STATE = ROOT / "desk" / "data" / "filing_watch_state.json"
UA = {"User-Agent": "SignalOS research desk (contact: 4tripathy@gmail.com)"}


def _load(p, default):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default



def _form4_codes(cik: str, acc: str) -> list | None:
    """Transaction codes from a Form 4's XML (P=open-market buy, S=sale, A=grant, M=exercise)."""
    try:
        a = acc.replace("-", "")
        idx = urllib.request.urlopen(urllib.request.Request(
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/index.json", headers=UA), timeout=15)
        import json as _j
        items = _j.load(idx)["directory"]["item"]
        xml = next((i["name"] for i in items if i["name"].endswith(".xml") and "primary" not in i["name"]), None)
        if not xml:
            return None
        raw = urllib.request.urlopen(urllib.request.Request(
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/{xml}", headers=UA), timeout=15).read().decode()
        import re as _re
        return _re.findall(r"<transactionCode>([A-Z])</transactionCode>", raw)
    except Exception:
        return None

def main() -> list[str]:
    conf = _load(CONF, {"targets": {}})
    state = _load(STATE, {})
    today = datetime.date.today().isoformat()
    fired = []
    for tk, t in conf.get("targets", {}).items():
        if t.get("until") and t["until"] < today:
            continue                                    # window expired — dormant, not deleted
        cik = str(t["cik"]).lstrip("0")
        url = f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                js = json.load(r)
        except Exception as e:
            fired.append(f"FILING WATCH {tk}: EDGAR poll failed ({type(e).__name__}) — kill-facts UNMONITORED this cycle")
            continue
        rec = js.get("filings", {}).get("recent", {})
        forms = rec.get("form", [])
        accs = rec.get("accessionNumber", [])
        dates = rec.get("filingDate", [])
        watch = tuple(t.get("forms_alert", []))
        seen = set(state.get(tk, []))
        new_seen = list(seen)
        for form, acc, fdate in zip(forms, accs, dates):
            if acc in seen:
                continue
            if fdate < t.get("since", today):
                continue
            if any(form == w or form.startswith(w) for w in watch):
                # Form-4 code filter (HONA deck 2026-08-08): grants/vests are noise —
                # when form4_codes is set, alert only on those transaction codes (P = open-market buy)
                codes = t.get("form4_codes")
                if codes and form.startswith("4"):
                    tc = _form4_codes(cik, acc)
                    if tc is not None and not (set(tc) & set(codes)):
                        new_seen.append(acc)
                        continue
                    label = f"Form 4 codes={sorted(set(tc)) if tc else 'UNPARSED'}"
                else:
                    label = form
                fired.append(f"FILING WATCH {tk}: NEW {label} filed {fdate} ({acc}) — "
                             f"{t.get('reason', t.get('why', 'kill-fact class'))} — CHECK BEFORE ANY ENTRY/RUNG")
            new_seen.append(acc)
        state[tk] = new_seen[-400:]
    STATE.write_text(json.dumps(state, indent=1))
    # LIVING-DECK HOOK (principal 2026-09-04): a filing-watch fire on a name holding a deck
    # updates the deck PDF + re-emails it - the reader-facing artifact never lags the record.
    for f in fired:
        try:
            tk = f.split("FILING WATCH ", 1)[1].split(":", 1)[0].strip()
            if "NEW" in f:
                from desk.deck_update import append_and_ship
                append_and_ship(tk, "filing-watch fire", f)
        except Exception:
            pass
    if fired:
        try:
            from desk.gauntlet_sentinel import _notify
            _notify(" | ".join(fired)[:900])
        except Exception:
            pass
        for f in fired:
            print(f)
    else:
        print(f"[filing_watch] {datetime.datetime.now():%H:%M} quiet ({len(conf.get('targets', {}))} targets)")
    return fired


if __name__ == "__main__":
    main()
