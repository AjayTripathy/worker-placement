"""disclosure_watch — the GENERALIZED entity-disclosure rail (2026-07-29, user-directed:
"generalize; it's not just for Japan/Nintendo").

Principle: every position's risk drivers are ENTITIES — the company itself, its decisive
customer, its controller — and each entity discloses on a NATIVE PLANE (EDGAR, TDnet, a
newswire page, a regulated-information page). This rail covers each watched entity on its
plane and fires the clear email within the hour of any new disclosure, with a LOUD marker
on the document classes that move positions (earnings-forecast revisions, 8-K/6-K,
shelf/resale registrations, buyback declarations, ad-hocs).

Supersedes desk/tdnet_watch.py (its state is migrated on first load; its logic is the
`tdnet` adapter here). Adding an entity = ONE dict in WATCHMAP — the staging-time doctrine:
every new position adds its risk-driver entities on their native planes when the envelope
is staged.

Adapters: `tdnet` (yanoshin mirror, dual item shapes) · `edgar` (SEC submissions JSON per
hardcoded CIK — resolved at build time, never at runtime) · `rss_or_page` (curl_cffi
chrome-fingerprint fetch + per-entry item regex; whole-page hash-diff fallback that fires
"PAGE CHANGED — read it" when the pattern extracts nothing). DATA MISSING never silence;
first run per entity seeds silently; per-entity dedupe in
desk/data/disclosure_watch_state.json. Runs hourly on the heartbeat.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "disclosure_watch_state.json"
LEGACY_TDNET_STATE = ROOT / "desk" / "data" / "tdnet_watch_state.json"

EDGAR_UA = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
LOUD_FORMS = ("8-K", "6-K", "S-3", "SC 13D", "SC 13G", "144", "424B", "S-1")
TDNET_FORECAST_KEYS = ("url_report_type_earnings_forecast", "url_report_type_summary",
                       "url_report_type_expected_dividends")

# ── THE WATCHMAP ──────────────────────────────────────────────────────────────
# One dict per watched entity. why/positions print in the email body so the alert
# arrives carrying its doctrine. CIKs resolved 2026-07-29 from company_tickers.json.
WATCHMAP = [
    # — TDnet plane (Japan) —
    {"entity": "Nintendo", "plane": "tdnet", "key": "7974",
     "why": "78.0% of Hosiden's revenue — the staged position's tail; a forecast revision re-opens the Hosiden pack BEFORE its own print",
     "positions": "6804.T staged 300@2650 (instr 110); frozen 6804.T|2026-08-07 @ 0.55"},
    {"entity": "Hosiden", "plane": "tdnet", "key": "6804",
     "why": "the position itself — Q1 tanshin (~Aug-7), buyback/CB notices, the print-date announcement",
     "positions": "staged 300@2650 (instr 110)"},
    # — EDGAR plane (US) —
    {"entity": "Western Alliance (WAL)", "plane": "edgar", "key": "0001212545",
     "why": "resting rungs below market; any 8-K between prints (fraud/NDFI class = immediate exit-review trigger if owned)",
     "positions": "rung-1 FILLED 125@81.008; rung-2 GTC 125@79 resting; frozen WAL|2026-10-31 @ 0.70"},
    {"entity": "FS Bancorp (FSBW)", "plane": "edgar", "key": "0001530249",
     "why": "resting rungs; construction/CRE 8-K class = the red team's second-charge-off tripwire",
     "positions": "rung-1 FILLED 120@42.51; rung-2 GTC 120@40.50 resting; frozen FSBW|2026-10-31 @ 0.65"},
    {"entity": "OneMain (OMF)", "plane": "edgar", "key": "0001584207",
     "why": "staged post-print-pass; NCO-guide or capital-return 8-Ks are the kill class",
     "positions": "rung-1 FILLED 80@63.01; rung-2 85@60 resting; frozen OMF|2026-10-28 @ 0.65"},
    {"entity": "Northpointe (NPB)", "plane": "edgar", "key": "0001336706",
     "why": "staged; ANY S-3/resale registration = the (verification-retired) overhang re-appearing — LOUD by form class",
     "positions": "instr 109 (290@17); frozen NPB|2026-10-31 @ 0.65"},
    {"entity": "Qualcomm (QCOM)", "plane": "edgar", "key": "0000804328",
     "why": "print pack armed (FQ3 tonight 07-29); band re-pointed to the $150 action gate; wash-sale precondition on Parametric",
     "positions": "CSP LIVE: short Sep-18 140p+135p (fills 6.94/5.29); kill-linked BTC; band 150"},
    {"entity": "Jersey Mike's (JMKE)", "plane": "edgar", "key": "0002127043",
     "why": "WAIT band $15-18: final 424B4 terms + lockup docs set the ~Jan-2027 calendar; graded call JMKE|2027-01-29 @ 0.60",
     "positions": "no position by design (DECLINE at range)"},
    # — page plane (Europe newswire / regulated-info) —
    {"entity": "Kalmar", "plane": "rss_or_page", "key": "https://www.globenewswire.com/en/search/organization/Kalmar",
     "item_pattern": r'href="(/news-release/[^"]+)"', "base": "https://www.globenewswire.com",
     "why": "HELD 200@38.51 — the order nowcast counts PRs but does NOT alert guidance/ad-hoc items; this does. Kill list: guide cut <12.5% = re-court",
     "positions": "held; washout envelope armed 150@34.50; frozen KALMAR.HE|2026-10-29 @ 0.45"},
    {"entity": "Verallia", "plane": "rss_or_page", "key": "https://www.verallia.com/en/investors/press-releases-other-financial-information/",
     "item_pattern": r'href="(https://www\.verallia\.com/wp-content/uploads/[^"]+\.pdf)"', "base": "",
     "why": "HELD 270@18.31 + rung 2 resting — PR PDFs land here first (the H1 release did); Q3 Oct-27, CMD Nov-18",
     "positions": "held + GTC 290@17.20; frozen VRLA.PA|2026-10-27 @ 0.65"},
    {"entity": "Lagardere (MMB)", "plane": "rss_or_page", "key": "https://www.lagardere.com/en/shareholders-and-investors/regulated-information-amf/regulated-information-amf-2026/",
     "item_pattern": r'href="(https://www\.lagardere\.com/[^"]+\.pdf)"', "base": "",
     "why": "LOUD-BY-PLANE: a NEW declaration on this page is THE MMB re-open signal — the blue court's event pack fires on buyback flow appearing here (zero flow in 12wks was the downgrade reason)",
     "positions": "WATCH 4.5; band 16-17 armed; event pack = the only path back to OWNABLE", "always_loud": True},
    {"entity": "Jungheinrich (JUN3)", "plane": "rss_or_page", "key": "https://www.jungheinrich.com/en/newsroom",
     "item_pattern": r'href="(/en/newsroom/[^"]+)"', "base": "https://www.jungheinrich.com",
     "why": "blue-killed on a MISSED AD-HOC — this watch exists so that never repeats; reopen = Aug-11 H1 one-off proof or <=22",
     "positions": "WATCH 4; band retracted; reopen triggers armed"},
    {"entity": "Kering (KER)", "plane": "rss_or_page", "key": "https://www.globenewswire.com/en/search/organization/Kering",
     "item_pattern": r'href="(/news-release/[^"]+)"', "base": "https://www.globenewswire.com",
     "why": "OWNABLE-small post-recourt; band 272-282 armed; tranche-2 pack on the Oct-21 print (2-yr-stack reaction driver)",
     "positions": "no position; band + pack armed"},
]
# ──────────────────────────────────────────────────────────────────────────────


def _poll_tdnet(w):
    try:
        req = urllib.request.Request(
            f"https://webapi.yanoshin.jp/webapi/tdnet/list/{w['key']}.json?limit=10",
            headers={"User-Agent": "signalos-desk 4tripathy@gmail.com"})
        with urllib.request.urlopen(req, timeout=25) as r:
            items = json.load(r).get("items", [])
    except Exception as e:
        print(f"[disclosure_watch] {w['entity']}: DATA MISSING ({type(e).__name__})")
        return None
    out = []
    for it in items:
        t = it.get("Tdnet", it)     # mirror serves wrapped AND flat shapes
        out.append({"id": str(t.get("id")), "date": t.get("pubdate"), "title": t.get("title"),
                    "url": t.get("document_url"),
                    "loud": any(t.get(k) for k in TDNET_FORECAST_KEYS)})
    return out


def _poll_edgar(w):
    cik = w["key"]
    try:
        req = urllib.request.Request(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=EDGAR_UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            recent = json.load(r).get("filings", {}).get("recent", {})
    except Exception as e:
        print(f"[disclosure_watch] {w['entity']}: DATA MISSING ({type(e).__name__})")
        return None
    out = []
    forms = recent.get("form", [])[:15]
    for i, form in enumerate(forms):
        acc = recent["accessionNumber"][i]
        doc = (recent.get("primaryDocument") or [""] * len(forms))[i]
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}"
        out.append({"id": acc, "date": recent["filingDate"][i], "title": form,
                    "url": url, "loud": any(form.startswith(l) for l in LOUD_FORMS)})
    return out


def _poll_page(w):
    try:
        from curl_cffi import requests as creq
        r = creq.get(w["key"], impersonate="chrome124", timeout=40)
        if r.status_code != 200:
            print(f"[disclosure_watch] {w['entity']}: DATA MISSING (HTTP {r.status_code})")
            return None
        text = r.text
    except Exception as e:
        print(f"[disclosure_watch] {w['entity']}: DATA MISSING ({type(e).__name__})")
        return None
    hits = list(dict.fromkeys(re.findall(w["item_pattern"], text)))
    loud = bool(w.get("always_loud"))
    if hits:
        return [{"id": h, "date": "", "title": h.rstrip("/").split("/")[-1][:120],
                 "url": (w.get("base", "") + h) if h.startswith("/") else h, "loud": loud} for h in hits]
    # fallback: whole-page hash-diff — a changed page fires once with a read-it pointer
    h = hashlib.sha256(re.sub(r"\s+", " ", text).encode()).hexdigest()[:16]
    return [{"id": f"pagehash:{h}", "date": "", "title": "PAGE CHANGED — read it (pattern extracted nothing)",
             "url": w["key"], "loud": loud}]


POLLERS = {"tdnet": _poll_tdnet, "edgar": _poll_edgar, "rss_or_page": _poll_page}

# Plain-language expansions for SEC form codes (email legibility, 2026-07-30 user feedback:
# "LOUD seems fair but the email isn't super legible"). Longest prefix wins.
FORM_PLAIN = {
    "8-K": "current report — a material corporate event",
    "6-K": "foreign-issuer current report — a material event",
    "10-Q": "quarterly report",
    "10-K": "annual report",
    "S-3": "shelf/resale registration — new supply can come to market",
    "S-1": "registration statement (IPO/new securities)",
    "S-8": "employee stock-plan registration (routine)",
    "SC 13D": "activist/large-holder stake disclosure (>5%, with intent)",
    "SC 13G": "passive large-holder stake disclosure (>5%)",
    "144": "insider notice of intent to sell",
    "424B": "prospectus — offering terms",
    "DEF 14A": "proxy statement",
    "3": "insider — initial ownership form",
    "4": "insider — ownership change (buy/sell)",
    "5": "insider — annual ownership form",
}


def _plain_form(title: str) -> str:
    """'8-K' -> '8-K (current report — a material corporate event)'; unknown codes pass through."""
    best = ""
    for code in FORM_PLAIN:
        if title.startswith(code) and len(code) > len(best):
            best = code
    return f"{title} ({FORM_PLAIN[best]})" if best else title


def _live_stake(w) -> str:
    """LIVE holdings from the positions cache beat the watchmap's hand-written stake line, which
    goes stale on fills (2026-07-30: WAL email said 'GTC 125@81' days after the fill). The static
    `positions` string stays as context (bands/frozen calls), prefixed by what we actually hold."""
    m = re.search(r"\(([A-Z0-9.]{1,8})\)", w["entity"])
    if not m:
        return w["positions"]
    tick = m.group(1)
    try:
        cache = json.loads((ROOT / "desk" / "ui" / "data" / "positions_cache.json").read_text())
        rows = [p for p in cache.get("positions", [])
                if p.get("symbol", "").split(".")[0] == tick and p.get("qty")]
        if rows:
            held = "; ".join(f"HELD {p['qty']:g} {p['symbol']}"
                             + (f" @ {p['avg_cost_per_unit']:g}" if p.get("avg_cost_per_unit") else "")
                             + (" (option)" if p.get("sec_type") == "OPT" else "")
                             for p in rows)
            return f"{held} | context: {w['positions']}"
    except Exception:
        pass
    return w["positions"]


def _compose(w, new, loud):
    """Legible clear-email: facts first in plain language, then why-you-got-this, stake, and
    the before-acting rule. Returns (subject, plain_text, html)."""
    import html as _h
    ent, plane = w["entity"], w["plane"]
    stake = _live_stake(w)
    forms = list(dict.fromkeys((it["title"] or "item").split("/")[0].strip() for it in new))
    summary = ", ".join(_plain_form(f).split(" (")[0] for f in forms[:2]) + (", …" if len(forms) > 2 else "")
    subj = f"{'LOUD — ' if loud else ''}{ent}: new {summary}" + (f" ({len(new)} filings)" if len(new) > 1 else "")

    why_loud = ("At least one filing is in the loud class for this name — a form type that can move "
                "the thesis (or the plane itself is marked always-loud). Read before reacting to price."
                if loud else
                "Routine-class filing(s); logged for the record, no urgency implied.")
    items_txt, items_html = [], []
    for it in new:
        label = _plain_form(it["title"] or "item")
        d = it.get("date") or ""
        tag = "  [LOUD]" if it["loud"] else ""
        items_txt.append(f"  • {d}  {label}{tag}\n    {it['url']}")
        items_html.append(
            f"<li>{_h.escape(d)} — <a href=\"{_h.escape(it['url'])}\">{_h.escape(label)}</a>"
            + ("  <b>[LOUD]</b>" if it["loud"] else "") + "</li>")

    body = "\n".join([
        f"{ent} — {len(new)} new disclosure{'s' if len(new) > 1 else ''} on {plane.upper()}",
        "",
        "WHAT LANDED",
        *items_txt,
        "",
        "WHY YOU GOT THIS",
        f"  {why_loud}",
        "",
        "OUR STAKE",
        f"  {stake}",
        "",
        "WHY WE WATCH THIS NAME",
        f"  {w['why']}",
        "",
        "BEFORE ACTING",
        "  Read the filing first. If it touches a risk driver, the name goes back through its",
        "  pack/court before any order — check the catalyst registry branches and the kill list.",
    ])
    html = (
        f"<h3 style='margin:0 0 8px'>{_h.escape(ent)} — {len(new)} new disclosure{'s' if len(new) > 1 else ''} "
        f"on {_h.escape(plane.upper())}</h3>"
        f"<p style='margin:4px 0'><b>What landed</b></p><ul style='margin:4px 0'>{''.join(items_html)}</ul>"
        f"<p style='margin:8px 0 4px'><b>Why you got this</b><br>{_h.escape(why_loud)}</p>"
        f"<p style='margin:8px 0 4px'><b>Our stake</b><br>{_h.escape(stake)}</p>"
        f"<p style='margin:8px 0 4px'><b>Why we watch this name</b><br>{_h.escape(w['why'])}</p>"
        f"<p style='margin:8px 0 4px;color:#666'><b>Before acting:</b> read the filing first — if it touches a "
        f"risk driver, the name goes back through its pack/court before any order.</p>")
    return subj, body, html


def _email(subject: str, body: str, html: str | None = None):
    try:
        from desk.mailer import send_prebuilt, send_raw
        (send_prebuilt(subject, body, html) if html else send_raw(subject, body, mono=False))
    except Exception as ex:
        print(f"[disclosure_watch] email failed: {ex}")


def _load_state() -> dict:
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    # one-time migration: absorb tdnet_watch's seen-ids so nothing re-fires
    if not state.get("_migrated_tdnet") and LEGACY_TDNET_STATE.exists():
        try:
            legacy = json.loads(LEGACY_TDNET_STATE.read_text())
            for code, v in legacy.items():
                ent = next((w["entity"] for w in WATCHMAP if w["plane"] == "tdnet" and w["key"] == code), None)
                if ent:
                    seen = set(state.get(ent, {}).get("seen", [])) | set(v.get("seen", []))
                    state[ent] = {"seen": sorted(seen, reverse=True)[:300]}
            state["_migrated_tdnet"] = True
        except Exception:
            pass
    return state


def main(dry: bool = False) -> list[str]:
    state = _load_state()
    fired = []
    for w in WATCHMAP:
        items = POLLERS[w["plane"]](w)
        if items is None:
            continue
        ent = w["entity"]
        first_run = ent not in state
        seen = set(state.get(ent, {}).get("seen", []))
        new = [it for it in items if it["id"] not in seen]
        seen |= {it["id"] for it in items}
        state[ent] = {"seen": sorted(seen, reverse=True)[:300]}
        if first_run:
            # SEED GUARD (2026-07-29: the intra-day baseline seed swallowed QCOM's same-day 8-K —
            # the rail's first real target). Same-day items FIRE on the seeding run; only older
            # items are silent baseline.
            import datetime as _dt
            today = _dt.date.today().isoformat()
            same_day = [it for it in new if str(it.get("date", "")).startswith(today)]
            print(f"[disclosure_watch] {ent} [{w['plane']}]: baseline seeded, {len(items)} items"
                  + (f" ({len(same_day)} SAME-DAY -> firing)" if same_day else ""))
            if not same_day:
                continue
            new = same_day
        if not new:
            continue
        loud = any(it["loud"] for it in new)
        subj, body, html = _compose(w, new, loud)
        fired.append(f"{ent}: {len(new)} new" + (" [LOUD]" if loud else ""))
        print(f"[disclosure_watch] FIRE {ent}: {len(new)} new{' [LOUD]' if loud else ''}")
        if not dry:
            _email(subj, body, html)
            try:
                from desk.gauntlet_sentinel import _notify
                _notify(f"DISCLOSURE {ent}: {len(new)} new" + (" LOUD" if loud else ""))
            except Exception:
                pass
    if not dry:
        STATE.write_text(json.dumps(state, indent=1))
    if not fired:
        print(f"[disclosure_watch] quiet — {len(WATCHMAP)} entities watched, no new disclosures")
    return fired


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
