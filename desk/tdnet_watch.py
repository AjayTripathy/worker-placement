"""tdnet_watch — SUPERSEDED 2026-07-29 (same day) by desk/disclosure_watch.py, the generalized
entity-disclosure rail (TDnet + EDGAR + newswire/regulated-info pages). This module's logic
lives on as disclosure_watch's `tdnet` adapter and its state was migrated; kept on disk for
reference only — do NOT register it alongside disclosure_watch (double alerts).

Original docstring:

Japanese-disclosure rail for names whose risk drivers file on TDnet, not EDGAR.

Born 2026-07-29 from the user's audit question on the staged Hosiden position: "are we sure an
email fires when NINTENDO files?" Answer was NO — the filing watch is EDGAR-only and Nintendo
(78.0% of Hosiden's revenue, the single risk driver) files in Tokyo. This closes that class of
hole: any watched company's new TDnet disclosure fires the clear-email rail within the hour.

Source: the yanoshin TDnet mirror (webapi.yanoshin.jp/webapi/tdnet/list/<code>.json) — free JSON
over the official release.tdnet.info feed, with per-document type flags; earnings-forecast
documents (the guide-revision class) get a LOUD marker in the email. Titles are Japanese and are
sent raw with the PDF link — the reader clicks through; the rail's job is the ALERT, not the
translation. DATA MISSING on failure, never silence. First run per code seeds the baseline
without emailing. State: desk/data/tdnet_watch_state.json. Runs hourly on the heartbeat.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "tdnet_watch_state.json"
API = "https://webapi.yanoshin.jp/webapi/tdnet/list/{code}.json?limit=10"

WATCHLIST = [
    {"code": "7974", "name": "Nintendo", "why": "HOSIDEN RISK DRIVER: Nintendo is 78.0% of Hosiden revenue — any guide/forecast revision is the position's tail (staged 300@2650, frozen 6804.T|2026-08-07)"},
    {"code": "6804", "name": "Hosiden", "why": "the position itself — Q1 tanshin, buyback/CB notices, the print-date announcement"},
]

FORECAST_KEYS = ("url_report_type_earnings_forecast", "url_report_type_summary",
                 "url_report_type_expected_dividends")


def _fetch(code: str):
    try:
        req = urllib.request.Request(API.format(code=code),
                                     headers={"User-Agent": "signalos-desk 4tripathy@gmail.com"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r).get("items", [])
    except Exception as e:
        print(f"[tdnet_watch] {code}: DATA MISSING ({type(e).__name__})")
        return None


def _email(subject: str, body: str):
    cred = Path.home() / ".signalos_smtp"
    if not cred.exists():
        return
    try:
        import smtplib
        from email.mime.text import MIMEText
        m = MIMEText(body)
        m["Subject"] = subject
        m["From"] = m["To"] = "4tripathy@gmail.com"
        pw = cred.read_text().strip().replace(" ", "")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as srv:
            srv.login("4tripathy@gmail.com", pw)
            srv.send_message(m)
    except Exception as ex:
        print(f"[tdnet_watch] email failed: {ex}")


def main(dry: bool = False) -> list[str]:
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    fired = []
    for w in WATCHLIST:
        code = w["code"]
        items = _fetch(code)
        if items is None:
            continue
        seen = set(state.get(code, {}).get("seen", []))
        first_run = code not in state
        new = []
        for it in items:
            t = it.get("Tdnet", it)   # the mirror serves both wrapped and flat item shapes
            did = str(t.get("id"))
            if did in seen:
                continue
            seen.add(did)
            if not first_run:
                is_forecast = any(t.get(k) for k in FORECAST_KEYS)
                new.append({"id": did, "pubdate": t.get("pubdate"), "title": t.get("title"),
                            "url": t.get("document_url"), "forecast": is_forecast})
        state[code] = {"seen": sorted(seen, reverse=True)[:200]}
        if first_run:
            print(f"[tdnet_watch] {w['name']} ({code}): baseline seeded, {len(seen)} items")
            continue
        if new:
            lines = [w["why"], ""]
            loud = False
            for n in new:
                marker = ">>> EARNINGS/FORECAST-CLASS DOCUMENT <<<  " if n["forecast"] else ""
                loud = loud or n["forecast"]
                lines.append(f"{marker}{n['pubdate']}  {n['title']}")
                lines.append(f"  {n['url']}")
                lines.append("")
            lines.append("Doctrine: a customer-side guide revision re-opens the Hosiden pack BEFORE its own print —")
            lines.append("check the armed branches in catalyst_action_registry before any order action.")
            subj = f"TDNET FILING{' — FORECAST CLASS' if loud else ''}: {w['name']} — {len(new)} new"
            fired.append(f"{w['name']}: {len(new)} new" + (" [FORECAST]" if loud else ""))
            print(f"[tdnet_watch] FIRE {w['name']}: {len(new)} new{' [FORECAST-CLASS]' if loud else ''}")
            if not dry:
                _email(subj, "\n".join(lines))
                try:
                    from desk.gauntlet_sentinel import _notify
                    _notify(f"TDNET {w['name']}: {len(new)} new filing(s)" + (" FORECAST-CLASS" if loud else ""))
                except Exception:
                    pass
    if not dry:
        STATE.write_text(json.dumps(state, indent=1))
    if not fired:
        print(f"[tdnet_watch] quiet — no new disclosures on {len(WATCHLIST)} watched codes")
    return fired


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
