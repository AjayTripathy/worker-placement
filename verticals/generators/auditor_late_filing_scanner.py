"""auditor_late_filing_scanner — Stage 0b EXCLUSION generator: auditor-change x late-filing CONJUNCTION (EDGAR).

THE ANTI-PORTFOLIO. THESIS: an auditor resignation/change (8-K Item 4.01, "Changes in Registrant's
Certifying Accountant") INTERSECTED with a late-filing notice (NT 10-K / NT 10-Q) within a short window is a
high-precision distress/fraud precursor. The value is in NOT owning these names — the exclusion IS the product,
and it complements the small-cap-honesty work (that strategy's surviving claim is a catastrophe-exclusion overlay,
not deployable alpha; this is the same discipline applied to a filings-forensic tell).

WHY THE CONJUNCTION IS THE PRECISION GATE (recall-floor doctrine, inherited from the whole generators fleet):
EITHER signal ALONE over-fires. Auditor changes happen for benign reasons — fee disputes, PCAOB rotation, an
acquired accounting firm, a going-public housekeeping swap. Late filings happen for benign reasons too — an
acquisition-driven restatement of comparatives, a new-ERP cutover, a first-year-public scramble. But a company
that BOTH lost/changed its auditor AND missed a periodic-report deadline inside ~90 days is disproportionately a
name where the auditor walked over something it wouldn't sign and the numbers can't be finalized on time. The
distress_8k_scanner already surfaces each tell SEPARATELY (a long, noisy list); this scanner's entire contribution
is the INTERSECT — only names carrying BOTH legs are surfaced, and we report the (large) auditor-only and
late-only counts precisely to SHOW the conjunction's selectivity (the gate is working when the excluded set is a
tiny fraction of either leg).

  python3 verticals/generators/auditor_late_filing_scanner.py [--days 120] [--window 90] [--pages 6]
Writes data/AUDITOR_LATE_FILING.json. Uses efts.sec.gov full-text search (free, SEC-compliant UA). READ-ONLY,
never orders. NO fabricated tickers — real EDGAR only; unresolvable CIKs keep their SEC name and self-drop ticker.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "AUDITOR_LATE_FILING.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

EFTS = "https://efts.sec.gov/LATEST/search-index"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# resign is materially worse than dismissal — an auditor RESIGNING (walking) is the stronger distress tell than
# the registrant DISMISSING the auditor (which can be a routine cost/rotation decision).
RESIGN_STEMS = re.compile(r"\b(resign|declin\w+ to stand|withdr\w+|will not stand for re-?appoint)", re.I)
DISMISS_STEMS = re.compile(r"\b(dismiss|terminat\w+ the (?:engagement|relationship)|no longer (?:be )?engaged)", re.I)


def _get(url: str, retries: int = 3, timeout: int = 40) -> bytes | None:
    """Polite GET with backoff — EDGAR 429s aggressively on the EFTS index and the archives."""
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            time.sleep(1.0 + 0.8 * i)   # be polite / back off on 429/timeout
    return None


def _get_json(url: str) -> dict:
    raw = _get(url)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _ticker_map() -> dict:
    """CIK(int) -> {'ticker','title'} from the SEC canonical map (real symbols only)."""
    d = _get_json(TICKERS_URL)
    out = {}
    for _, row in (d or {}).items():
        try:
            out[int(row["cik_str"])] = {"ticker": row["ticker"].upper(), "title": row["title"]}
        except Exception:
            continue
    return out


def _clean_name(display: str) -> str:
    """'FOO CORP.  (FOO)  (CIK 0001234567)' -> 'FOO CORP.'"""
    return re.sub(r"\s*\(.*", "", display or "").strip()[:70]


def _efts_all(params: dict, days: int, pages: int, want_item_401: bool = False) -> list[dict]:
    """Paginate EFTS (100/page, bounded) over the dated window -> list of normalized hit rows.

    Each row: {cik(int), name, ticker_hint, date, form, adsh, items}. want_item_401 keeps only hits whose EFTS
    'items' metadata actually contains 4.01 (a cheap confirmation that the full-text match is the accountant item,
    not an incidental 'Item 4.01' string elsewhere in the doc)."""
    today = datetime.date.today()
    base = dict(params)
    base["startdt"] = (today - datetime.timedelta(days=days)).isoformat()
    base["enddt"] = today.isoformat()
    rows, seen = [], set()
    for page in range(pages):
        p = dict(base)
        if page:
            p["from"] = page * 100
        url = EFTS + "?" + urllib.parse.urlencode(p)
        d = _get_json(url)
        hits = (((d or {}).get("hits") or {}).get("hits")) or []
        if not hits:
            break
        for h in hits:
            adsh = (h.get("_source") or {}).get("adsh") or h.get("_id", "")
            if adsh in seen:
                continue
            seen.add(adsh)
            s = h.get("_source") or {}
            items = s.get("items") or []
            if want_item_401 and "4.01" not in items:
                continue
            ciks = s.get("ciks") or []
            if not ciks:
                continue
            names = s.get("display_names") or []
            disp = names[0] if names else ""
            th = re.search(r"\(([A-Z][A-Z.\-]{0,5})\)", disp)  # ticker hint if EMMA-style embedded
            rows.append({
                "cik": int(ciks[0]),
                "name": _clean_name(disp),
                "ticker_hint": th.group(1) if th else "",
                "date": s.get("file_date", ""),
                "form": (s.get("root_forms") or [s.get("form", "")])[0],
                "adsh": s.get("adsh", ""),
                "items": items,
            })
        time.sleep(0.4)
    return rows


def _resigned_vs_dismissed(cik: int, adsh: str) -> tuple[bool | None, str]:
    """Fetch the 8-K primary text (intersected names only — a SMALL set) and classify resign vs dismiss.

    Returns (resigned_bool, event_label). resigned_bool True = auditor RESIGNED (worse); False = dismissed by the
    registrant; None = language ambiguous / fetch failed (reported honestly, never guessed)."""
    if not adsh:
        return None, "auditor change (Item 4.01) — resign/dismiss undetermined"
    acc = adsh.replace("-", "")
    # fetch the full submission text (the complete .txt is the most robust single-GET path across old/new layouts)
    body = _get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{adsh}.txt")
    txt = body.decode("latin-1", "ignore") if body else ""
    if not txt:
        return None, "auditor change (Item 4.01) — filing text unreachable (resign/dismiss undetermined)"
    # scope to the neighborhood of the 4.01 discussion to avoid boilerplate false hits
    m = re.search(r"Item\s*4\.01(.{0,2500})", txt, re.I | re.S)
    scope = m.group(1) if m else txt[:4000]
    resign = bool(RESIGN_STEMS.search(scope))
    dismiss = bool(DISMISS_STEMS.search(scope))
    if resign and not dismiss:
        return True, "AUDITOR RESIGNED (Item 4.01) — auditor walked; the stronger distress tell"
    if dismiss and not resign:
        return False, "auditor DISMISSED by registrant (Item 4.01) — routine-or-not, verify the reason"
    if resign and dismiss:
        return True, "Item 4.01 with BOTH resign+dismiss language — treat as resignation (verify in DD)"
    return None, "auditor change (Item 4.01) — resign/dismiss language not isolated (verify in DD)"


def scan(days: int, window: int, pages: int) -> dict:
    today = datetime.date.today()
    tmap = _ticker_map()

    # LEG 1 — auditor changes: 8-K full-text "Item 4.01" confirmed by the EFTS items metadata.
    auditor = _efts_all({"q": '"Item 4.01"', "forms": "8-K"}, days, pages, want_item_401=True)
    # collapse to latest 4.01 per CIK
    aud_by_cik: dict[int, dict] = {}
    for r in auditor:
        cur = aud_by_cik.get(r["cik"])
        if not cur or (r["date"] or "") > (cur["date"] or ""):
            aud_by_cik[r["cik"]] = r

    # LEG 2 — late filings: NT 10-K and NT 10-Q notices of late periodic reports.
    late = (_efts_all({"forms": "NT 10-K"}, days, pages)
            + _efts_all({"forms": "NT 10-Q"}, days, pages))
    late_by_cik: dict[int, dict] = {}
    for r in late:
        cur = late_by_cik.get(r["cik"])
        if not cur or (r["date"] or "") > (cur["date"] or ""):
            late_by_cik[r["cik"]] = r

    # INTERSECT by CIK within the window -> the exclusion (anti-portfolio) list.
    excluded = []
    both_ciks = set(aud_by_cik) & set(late_by_cik)
    for cik in both_ciks:
        a, l = aud_by_cik[cik], late_by_cik[cik]
        try:
            da = datetime.date.fromisoformat(a["date"])
            dl = datetime.date.fromisoformat(l["date"])
            days_apart = abs((da - dl).days)
        except Exception:
            days_apart = None
        if days_apart is None or days_apart > window:
            continue
        info = tmap.get(cik) or {}
        ticker = info.get("ticker") or a.get("ticker_hint") or l.get("ticker_hint") or ""
        resigned, event = _resigned_vs_dismissed(cik, a["adsh"])
        excluded.append({
            "ticker": ticker,               # "" if the CIK has no exchange-listed common (real, never fabricated)
            "cik": cik,
            "name": info.get("title") or a["name"] or l["name"],
            "auditor_event": event,
            "auditor_date": a["date"],
            "resigned_bool": resigned,      # True=resigned(worse) / False=dismissed / None=undetermined
            "late_form": l["form"],
            "late_date": l["date"],
            "days_apart": days_apart,
            "note": ("BOTH legs present within the window -> EXCLUDE (do-not-own). "
                     + ("Auditor RESIGNED — highest-priority avoid." if resigned else
                        "Verify the 8-K disagreement/reportable-events language + any going-concern in DD.")),
        })
        time.sleep(0.3)   # SEC-safe pace for the per-name text fetch
    excluded.sort(key=lambda e: (e["resigned_bool"] is not True, e["days_apart"]))

    return {
        "asof": today.isoformat(),
        "window_days": window,
        "lookback_days": days,
        "excluded": excluded,
        "n_excluded": len(excluded),
        "n_auditor_only": len(aud_by_cik) - len(both_ciks),   # auditor-change CIKs with NO late filing
        "n_late_only": len(late_by_cik) - len(both_ciks),     # late-filing CIKs with NO auditor change
        "n_auditor_total": len(aud_by_cik),
        "n_late_total": len(late_by_cik),
        "note": "EXCLUSION list (ANTI-PORTFOLIO) — do NOT own these, NOT a buy list. THESIS: 8-K Item 4.01 "
                "auditor change INTERSECTED with an NT 10-K/NT 10-Q late-filing notice within "
                f"{window}d = a high-precision distress/fraud precursor. The CONJUNCTION is the precision gate: "
                "either signal ALONE over-fires (n_auditor_only + n_late_only are large by design), so ONLY names "
                "carrying BOTH legs are surfaced. resigned_bool: auditor RESIGNING (walking) is worse than being "
                "dismissed. Complements the small-cap-honesty catastrophe-exclusion overlay. Recall-floor "
                "discipline: precision over count. READ-ONLY; the scanner proposes an avoid, it never orders. "
                "ticker='' = the CIK has no exchange-listed common on the SEC map (kept honest, never fabricated).",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=120, help="EDGAR lookback window (days) for both legs")
    ap.add_argument("--window", type=int, default=90, help="max days between the two legs to intersect")
    ap.add_argument("--pages", type=int, default=6, help="EFTS pages per query (100/page, bounded)")
    a = ap.parse_args()
    res = scan(a.days, a.window, a.pages)
    print(f"=== AUDITOR-CHANGE x LATE-FILING EXCLUSION SCANNER  {res['asof']}  "
          f"(lookback {res['lookback_days']}d, intersect window {res['window_days']}d) ===")
    print(f"  LEG 1  auditor changes (8-K Item 4.01):     {res['n_auditor_total']:>4} CIKs")
    print(f"  LEG 2  late filings (NT 10-K / NT 10-Q):     {res['n_late_total']:>4} CIKs")
    print(f"  --- the conjunction's SELECTIVITY (why either leg alone over-fires) ---")
    print(f"  auditor-only (NOT excluded): {res['n_auditor_only']:>4}    late-only (NOT excluded): {res['n_late_only']:>4}")
    print(f"  >>> INTERSECTED -> EXCLUDE (do-not-own anti-portfolio): {res['n_excluded']}")
    if res["excluded"]:
        for e in res["excluded"]:
            tk = e["ticker"] or "(no-tkr)"
            flag = "RESIGNED" if e["resigned_bool"] else ("dismissed" if e["resigned_bool"] is False else "chg?")
            print(f"    EXCLUDE {tk:<8} {e['name'][:34]:<34} [{flag:<9}] 4.01 {e['auditor_date']}  "
                  f"{e['late_form']} {e['late_date']}  ({e['days_apart']}d apart)")
    else:
        print("    (no name carries BOTH legs in this window — the honest null; the precision gate is working, "
              "not a failure)")
    print("  DOCTRINE: this is an EXCLUSION / anti-portfolio list (do-not-own), NOT a buy list. Either signal alone")
    print("  over-fires; only the CONJUNCTION is surfaced. Resigned auditors rank first. READ-ONLY — never orders.")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
