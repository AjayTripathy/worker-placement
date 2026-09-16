"""hood_9cir_watch — CourtListener docket poller for the consolidated 9th Cir. event-contract
appeals (Kalshi 25-7187 / Nadex 25-7516 / Robinhood Derivatives v. Dreitzer 25-7831).

Armed 2026-08-04 with resolution pack HOOD-9CIR|2026-12-31 (frozen timing call 0.52; conditional
direction 0.34/0.44/0.22). This watch is the DETECTION link only: on a new docket entry it prints
loudly; on a disposition-shaped entry it emails via desk/mailer and stamps the state file so the
desk heartbeat routes an agent to read the opinion and run the pack's PRE-COMMITTED branches
(desk/reports/courts_20260804/HOOD_CATALYST_PACK.md). No orders originate here — the autonomy
ladder's Rung 1 is unearned; agents stage, the principal clicks.

API notes (learned the hard way, see the pack): `dateArgued` is NULL on member dockets — never
infer schedule from that field; audio posts under the lead docket 25-7187 only. Anonymous API
etiquette: declared UA, tiny page sizes, hourly cadence.
"""
from __future__ import annotations

import datetime
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "hood_9cir_state.json"
DOCKETS = ["25-7187", "25-7516", "25-7831"]
API = "https://www.courtlistener.com/api/rest/v4"
import os
_TOK = os.environ.get("COURTLISTENER_API_TOKEN")
UA = {"User-Agent": "signalos-desk/1.0 (research watch; contact: 4tripathy@gmail.com)"}
if _TOK:
    UA["Authorization"] = f"Token {_TOK}"
DECISION_RX = ("OPINION", "MEMORANDUM DISPOSITION", "MEMORANDUM*", "AFFIRMED", "REVERSED",
               "VACATED", "FILED DISPOSITION", "MANDATE", "DISPOSITIVE")


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _load() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"docket_ids": {}, "last_seen": {}, "decision_fired": False}


def main() -> None:
    now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    st = _load()
    news, decisions = [], []
    for i, num in enumerate(DOCKETS):
        if i:
            time.sleep(4)  # anonymous-tier courtesy: 3 rapid searches drew a 429 on first run
        try:
            # anonymous-allowed RECAP search (the dockets/docket-entries endpoints 401 without a
            # token; /search/ does not — the litigation_flow_scanner precedent)
            q = (f"{API}/search/?type=r&q=docketNumber%3A%22{urllib.parse.quote(num)}%22"
                 f"&court=ca9&order_by=entry_date_filed%20desc")
            res = _get(q).get("results", [])
            docs = []
            for r in res:
                if str(r.get("docketNumber")) == num:
                    docs.extend(r.get("recap_documents") or [])
            if not docs:
                print(f"[{now}] {num}: no entries via search — DATA MISSING, not zero")
                continue
            docs.sort(key=lambda e: str(e.get("entry_date_filed") or ""), reverse=True)
            newest = docs[0]
            desc = str(newest.get("description") or newest.get("short_description") or "")
            key = f"{newest.get('entry_date_filed')}|{desc[:80]}"
            if st["last_seen"].get(num) != key:
                st["last_seen"][num] = key
                news.append((num, newest.get("entry_date_filed"), desc[:200]))
                hits = [d for d in docs[:5]
                        if any(k in str(d.get("description") or d.get("short_description") or "").upper()
                               for k in DECISION_RX)]
                for h in hits:
                    decisions.append((num, h.get("entry_date_filed"),
                                      str(h.get("description") or h.get("short_description"))[:400]))
            else:
                print(f"[{now}] {num}: no new entries (last {key[:40]})")
        except Exception as ex:  # cron-friendly: loud, non-fatal
            print(f"[{now}] {num}: ERROR {type(ex).__name__}: {ex}")
    for num, dt_, desc in news:
        print(f"[{now}] NEW ENTRY {num} {dt_}: {desc}")
    if decisions and not st.get("decision_fired"):
        st["decision_fired"] = True
        st["decision"] = {"at": now, "entries": decisions}
        body = ("DISPOSITION-SHAPED DOCKET ENTRY — HOOD-9CIR pack branches are LIVE.\n\n"
                + "\n".join(f"{n} {d}: {x}" for n, d, x in decisions)
                + "\n\nPack: desk/reports/courts_20260804/HOOD_CATALYST_PACK.md\n"
                  "Branches: FAVORABLE -> Branch B buy <=0.88x rebuilt E[FV] (agent stages, user clicks)"
                  " | ADVERSE -> cancel resting first, NO knife-catch, re-court the $50-state"
                  " | MIXED/moot -> decay branches.\n"
                  "Grade HOOD-9CIR|2026-12-31 (frozen 0.52) + the conditional direction (0.34).")
        try:
            from desk.mailer import send_raw
            send_raw("HOOD-9CIR: 9th Cir. DECISION entry filed — pack live", body)
            print(f"[{now}] DECISION ALERT emailed")
        except Exception as ex:
            print(f"[{now}] DECISION detected but mail failed ({ex}) — BODY:\n{body}")
    STATE.write_text(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()
