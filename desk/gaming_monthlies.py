"""gaming_monthlies — state gaming-commission monthly-revenue watcher (the office thesis's data leg).

WHY THIS EXISTS
    States publish casino revenue BY PROPERTY (or by market) every month on a ~2-5 week lag.
    A regional-casino microcap's revenue is therefore PUBLIC weeks-to-months before the company
    prints it. At $100-150M-cap names (FLL, CNTY) nobody institutional bothers to join the state
    feed to the ticker. This module does that join: it detects each state's new monthly report,
    parses the per-property AGR where the format allows, and alerts in plain language that feeds
    directly into the operator's next print.

    THE interesting line is Full House's American Place (Waukegan IL) — the growth asset — which
    Illinois reports per-casino as "FHR-Illinois LLC" and exports as CSV.

DESIGN — detection-first, parse-opportunistically
    Weekly run. Per source: fetch the index / app, detect whether a NEW month has posted vs the
    persisted state. On a new month: alert via desk.gauntlet_sentinel._notify (macOS + ntfy + email)
    and persist. NEVER fail the whole run on one adapter — each is wrapped in its own try/except and
    logs exactly why it could not detect (URL dead / JS-only / format changed).

    Parse (per-property $ + MoM + YoY):  Illinois (CSV export), Indiana (XLSX).
    Detect + link only:                  Colorado, Nevada, Mississippi (region/city PDFs; no PDF text
                                         extractor installed — link is the deliverable).

READ-ONLY w.r.t. the broker. Writes only desk/data/gaming_monthlies_state.json.
The desk wires this into the cron registry after review.
"""
from __future__ import annotations
import json, re, sys, datetime, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "desk" / "data" / "gaming_sources.json"
STATE = ROOT / "desk" / "data" / "gaming_monthlies_state.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MONTH_NUM = {m.lower(): i + 1 for i, m in enumerate(MONTHS)}


# ---------------------------------------------------------------- http helpers
def _fetch(url: str, data: bytes | None = None, referer: str | None = None,
           timeout: int = 45) -> tuple[int, dict, bytes]:
    """Full-Chrome-UA fetch. Returns (status, headers, body). Raises on transport error."""
    h = {"User-Agent": UA,
         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
         "Accept-Language": "en-US,en;q=0.9"}
    if referer:
        h["Referer"] = referer
        h["Origin"] = "https://" + urllib.parse.urlparse(referer).netloc
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read()


def _text(url: str, referer: str | None = None) -> str:
    _, _, body = _fetch(url, referer=referer)
    return body.decode("utf-8", "replace")


def _yy_mm(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _pretty(key: str) -> str:
    y, m = key.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def _covers(src: dict) -> str:
    return "; ".join(src.get("coverage", [])) or src.get("state", "")


# ---------------------------------------------------------------- notify
def _notify(msg: str):
    """Route through the durable gauntlet notifier (macOS + ntfy + email). Print too."""
    print("ALERT:", msg)
    try:
        from desk import gauntlet_sentinel
        gauntlet_sentinel._notify(msg)
    except Exception as e:  # never let a notify failure abort the run
        print("  (notify transport failed: %s)" % e)


# ---------------------------------------------------------------- ILLINOIS (parse)
def _il_latest_and_agr(src: dict):
    """Detect the IGB latest month from the app's selected <option>, then CSV-export the
    Casino Summary for the target month (+ prior + year-ago) and pull FHR-Illinois LLC Total AGR.
    Returns (month_key, link, parsed_dict|None)."""
    app, ref = src["app"], src["referer"]
    page = _text(app, referer=ref)

    def _selected(name: str) -> str | None:
        block = re.search(r'name="%s".*?</select>' % re.escape(name), page, re.S)
        if not block:
            return None
        m = re.search(r'<option selected="selected" value="([^"]+)"', block.group(0))
        return m.group(1) if m else None

    sel_month = _selected("SearchStartMonth")
    sel_year = _selected("SearchStartYear")
    if not sel_month or not sel_year:
        raise RuntimeError("could not read selected month/year from IGB app (form layout changed)")
    mnum = MONTH_NUM[sel_month.lower()]
    yr = int(sel_year)
    key = _yy_mm(yr, mnum)
    link = src["index"]  # the human landing page (the CSV is a postback, not a stable URL)

    def _hidden(name: str) -> str:
        m = re.search(r'name="%s"[^>]*value="([^"]*)"' % re.escape(name), page)
        return m.group(1) if m else ""

    def _agr_for(y: int, mo: int):
        """POST ViewCSV for a single month; return {property: total_agr} floats."""
        data = {
            "__VIEWSTATE": _hidden("__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": _hidden("__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": _hidden("__EVENTVALIDATION"),
            "CasinoReportTypes": "Casino Summary",
            "SearchStartMonth": MONTHS[mo - 1], "SearchStartYear": str(y),
            "SearchEndMonth": MONTHS[mo - 1], "SearchEndYear": str(y),
            "ViewType": "ViewCSV", "ButtonSearch.x": "10", "ButtonSearch.y": "10",
        }
        _, hdrs, body = _fetch(app, data=urllib.parse.urlencode(data).encode(), referer=ref)
        if "csv" not in (hdrs.get("Content-Type", "").lower()):
            return {}
        import csv, io
        out = {}
        rows = list(csv.reader(io.StringIO(body.decode("utf-8", "replace"))))
        hdr_idx = None
        for r in rows:
            if r and r[0] == "Casino":
                hdr_idx = {name: i for i, name in enumerate(r)}
                continue
            if hdr_idx and r and r[0] and r[0] not in ("Casino Summary",):
                col = hdr_idx.get("Total AGR")
                if col is not None and col < len(r):
                    try:
                        out[r[0]] = float(r[col])
                    except ValueError:
                        pass
        return out

    parsed = None
    try:
        cur = _agr_for(yr, mnum)
        pm_y, pm_m = (yr, mnum - 1) if mnum > 1 else (yr - 1, 12)
        prev = _agr_for(pm_y, pm_m)
        yago = _agr_for(yr - 1, mnum)
        parsed = {}
        for tgt in src.get("parse_targets", []):
            nm = tgt["csv_name"]
            v = cur.get(nm)
            if v is None:
                continue
            mom = _pct(v, prev.get(nm))
            yoy = _pct(v, yago.get(nm))
            parsed[tgt["property"]] = {"ticker": tgt["ticker"], "usd": v, "mom": mom, "yoy": yoy}
    except Exception as e:
        print("  (illinois: detected %s but CSV parse failed: %s)" % (key, e))
        parsed = None
    return key, link, parsed


# ---------------------------------------------------------------- INDIANA (parse)
def _in_latest_and_agr(src: dict):
    """Scrape the monthly-revenue index for the newest YYYY-MM-Revenue.xlsx, parse Rising Star 'Win'
    (+ prior + year-ago for MoM/YoY). Returns (month_key, link, parsed_dict|None)."""
    page = _text(src["index"])
    found = re.findall(r'/igc/files/reports/(20\d{2})/(20\d{2})-(\d{2})-Revenue\.xlsx', page)
    if not found:
        raise RuntimeError("no YYYY-MM-Revenue.xlsx links on IGC index (path changed)")
    months = sorted({(int(y2), int(mm)) for _, y2, mm in found})
    yr, mnum = months[-1]
    key = _yy_mm(yr, mnum)
    link = src["file_pattern"].format(year=yr, mm=f"{mnum:02d}")

    def _win_for(y: int, mo: int):
        url = src["file_pattern"].format(year=y, mm=f"{mo:02d}")
        try:
            _, _, body = _fetch(url)
        except Exception:
            return {}
        import openpyxl, io
        wb = openpyxl.load_workbook(io.BytesIO(body), data_only=True)
        ws = wb["1 Tax Summary"] if "1 Tax Summary" in wb.sheetnames else wb.worksheets[0]
        rows = list(ws.iter_rows(values_only=True))
        # Sheet 1 stacks several blocks (Tax / Win-Free Play-Other-Taxable AGR / Table-EGD detail),
        # each with the same casino-name rows. Anchor on the 'Taxable AGR' header column and read ONLY
        # the contiguous block that follows it (first occurrence wins) so we don't overwrite the gross
        # figure with a per-game sub-line.
        out, col, active = {}, None, False
        for r in rows:
            cells = [("" if c is None else str(c)).strip() for c in r]
            if "Taxable AGR" in cells:            # the gross-win block header
                col, active = cells.index("Taxable AGR"), True
                continue
            if active:
                name = cells[0] if cells else ""
                raw = r[col] if col is not None and col < len(r) else None
                num = None
                if raw not in (None, ""):
                    try:                          # cells arrive as strings in this workbook
                        num = float(str(raw).replace(",", ""))
                    except ValueError:
                        num = None
                if name and num is not None:       # a casino row (names vary: not all say "Casino")
                    out.setdefault(name, num)
                elif name and num is None:          # non-empty label w/ non-numeric target = next header
                    active = False
        return out

    parsed = None
    try:
        cur = _win_for(yr, mnum)
        pm_y, pm_m = (yr, mnum - 1) if mnum > 1 else (yr - 1, 12)
        prev = _win_for(pm_y, pm_m)
        yago = _win_for(yr - 1, mnum)
        parsed = {}
        for tgt in src.get("parse_targets", []):
            nm = tgt["xlsx_name"]
            v = cur.get(nm)
            if v is None:
                continue
            parsed[tgt["property"]] = {"ticker": tgt["ticker"], "usd": v,
                                       "mom": _pct(v, prev.get(nm)), "yoy": _pct(v, yago.get(nm))}
    except Exception as e:
        print("  (indiana: detected %s but XLSX parse failed: %s)" % (key, e))
        parsed = None
    return key, link, parsed


# ---------------------------------------------------------------- PDF DETECTORS (CO / NV / MS)
def _detect_pdf(src: dict):
    """Generic detection: collect every .pdf URL on the index, url-decode its BASENAME, and match
    src['filename_regex'] against the basename (anchored) so e.g. 'May2026.pdf' is chosen but the
    statewide-rollup 'StatewideMay2026.pdf' is not. Returns the newest (month_key, absolute_link, None)."""
    page = _text(src["index"])
    base = src.get("base", "")
    rx = re.compile(src["filename_regex"], re.I)
    # all candidate URLs: href="..." plus bare occurrences ending .pdf
    urls = set(re.findall(r'href="([^"]+\.pdf)"', page, re.I))
    urls |= set(re.findall(r'(https?://[^\s"\'<>]+\.pdf)', page, re.I))
    hits = []
    for u in urls:
        basename = urllib.parse.unquote(u.rstrip("/").split("/")[-1])
        m = rx.fullmatch(basename) if src.get("basename_match") else rx.search(basename)
        if not m:
            continue
        mon = m.group(1).lower()
        yr = int(m.group(2))
        if mon not in MONTH_NUM:
            continue
        href = u if u.startswith("http") else (base.rstrip("/") + "/" + u.lstrip("/") if base else u)
        hits.append(((yr, MONTH_NUM[mon]), href))
    if not hits:
        raise RuntimeError("no month-encoded PDF links matched on index (naming changed)")
    hits.sort(key=lambda x: x[0])
    (yr, mnum), href = hits[-1]
    return _yy_mm(yr, mnum), href, None


# ---------------------------------------------------------------- util
def _pct(cur, base):
    try:
        if cur is None or base in (None, 0):
            return None
        return round((cur / base - 1.0) * 100.0, 1)
    except (TypeError, ZeroDivisionError):
        return None


def _fmt_musd(x):
    return "$%.2fM" % (x / 1e6)


def _fmt_pct(p):
    if p is None:
        return "n/a"
    return ("+%.1f%%" if p >= 0 else "%.1f%%") % p


def _parsed_line(parsed: dict) -> str:
    bits = []
    for prop, d in parsed.items():
        bits.append("%s %s (%s MoM, %s YoY) [%s]" % (
            prop, _fmt_musd(d["usd"]), _fmt_pct(d["mom"]), _fmt_pct(d["yoy"]), d["ticker"]))
    if not bits:
        return ""
    return " — " + "; ".join(bits) + " — sequential=momentum, annual=market size; feeds the next print"


# ---------------------------------------------------------------- state
def _load(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


ADAPTERS = {
    "illinois": _il_latest_and_agr,
    "indiana": _in_latest_and_agr,
    "colorado": _detect_pdf,
    "nevada": _detect_pdf,
    "mississippi": _detect_pdf,
}


def run(force_notify: bool = False):
    cfg = _load(SOURCES, {})
    sources = cfg.get("sources", {})
    st = _load(STATE, {"sources": {}})
    st.setdefault("sources", {})
    results = []

    for sid, src in sources.items():
        adapter = ADAPTERS.get(sid)
        status = {"source": sid, "state": src.get("state", sid), "mode": src.get("mode")}
        if adapter is None:
            status.update(ok=False, reason="no adapter registered")
            results.append(status)
            continue
        try:
            key, link, parsed = adapter(src)
            prev_key = st["sources"].get(sid, {}).get("latest")
            is_new = (key != prev_key)
            status.update(ok=True, latest=key, link=link,
                          parsed=bool(parsed), new=is_new, prev=prev_key)
            if parsed:
                status["values"] = {p: d for p, d in parsed.items()}

            if is_new or force_notify:
                cov = _covers(src)
                tickers = sorted({t for t in re.findall(r'\b(FLL|MCRI|CNTY|GDEN)\b', cov)})
                head = ("NEW: %s %s casino revenue posted — covers %s; %s"
                        % (src["state"], _pretty(key), ", ".join(tickers) or cov, link))
                tail = _parsed_line(parsed) if parsed else " — detection-only (region/city PDF)"
                _notify(head + tail)

            # persist newest seen
            st["sources"][sid] = {"latest": key, "link": link,
                                  "parsed": bool(parsed),
                                  "checked": datetime.date.today().isoformat()}
            if parsed:
                st["sources"][sid]["values"] = {
                    p: {"usd": d["usd"], "mom": d["mom"], "yoy": d["yoy"], "ticker": d["ticker"]}
                    for p, d in parsed.items()}
        except Exception as e:
            status.update(ok=False, reason=str(e))
            print("  [%s] BLOCKED: %s" % (sid, e))
        results.append(status)

    STATE.write_text(json.dumps(st, indent=2))
    return results


def _print_report(results):
    print("\n" + "=" * 72)
    print("GAMING MONTHLIES — adapter status (%s)" % datetime.date.today().isoformat())
    print("=" * 72)
    for r in results:
        if r.get("ok"):
            tag = "WORKING"
            detail = "latest=%s  %s  new=%s" % (
                r.get("latest"), "PARSED" if r.get("parsed") else "detect-only", r.get("new"))
            print("  [%-11s] %-8s %s" % (r["source"], tag, detail))
            if r.get("values"):
                for prop, d in r["values"].items():
                    print("               %s: %s  MoM %s  YoY %s  [%s]" % (
                        prop, _fmt_musd(d["usd"]), _fmt_pct(d["mom"]), _fmt_pct(d["yoy"]), d["ticker"]))
            print("               link: %s" % r.get("link"))
        else:
            print("  [%-11s] %-8s %s" % (r["source"], "BLOCKED", r.get("reason")))


if __name__ == "__main__":
    force = "--notify" in sys.argv or "--force" in sys.argv
    res = run(force_notify=force)
    _print_report(res)
