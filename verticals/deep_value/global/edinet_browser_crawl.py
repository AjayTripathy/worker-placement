"""edinet_browser_crawl — NO-KEY transport for the Japan crawl: drives the public EDINET
viewer (disclosure2.edinet-fsa.go.jp) with Playwright and downloads each annual report's
CSV-facts ZIP into the SAME cache edinet_fundamentals fills from the API, so the extractor
and store don't know or care which transport ran.

Why a browser: the viewer serves identical ZIPs with no login, but downloads are GeneXus
postbacks keyed by per-session encrypted doc tokens — an HTTP client can't replay them.
(The gated-gov-portal lesson: land like a browser, act in-page.) The API v2 client is still
the preferred transport once a subscription key exists — see INVENTORY.md.

Flow (書類詳細検索 = WEEE0050): XBRL-only check -> 書類種別 = 有価証券報告書 only ->
提出期間 = explicit from/to -> 検索 -> per result row call the page's own CsvClick(token)
(XbrlClick as fallback) inside a download capture -> 次へ until the pager ends.

  python3 edinet_browser_crawl.py --from 2026-06-26 --to 2026-06-26 [--max-docs 600]

Politeness: one page, sequential downloads, PAUSE seconds apart, everything cached —
a re-run skips files already on disk (resumable by construction).
"""
from __future__ import annotations
import argparse, json, os, re, time

VIEWER = "https://disclosure2.edinet-fsa.go.jp/weee0050.aspx"
CACHE = os.path.join(os.path.dirname(__file__), "data", "edinet_cache")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
PAUSE = 0.5


def _set_chk(page, sel, want=True):
    """GeneXus renders checkboxes/radios visually hidden behind styled labels — drive the
    real input via a DOM click (runs the gx onclick handler) instead of Playwright check()."""
    page.evaluate("""([sel, want]) => { const e = document.querySelector(sel);
        if (e && e.checked !== want) {
            const l = document.querySelector(`label[for=${e.id}]`);
            (l || e).click();
        } }""", [sel, want])
    time.sleep(0.3)


def _open_section(page, btn_id):
    """Section toggles keep one id (BTNCLOSE_*) and swap value 開く/閉じる — click only
    while the section is still closed (value 開く)."""
    b = page.locator(f"#{btn_id}")
    if b.count() and b.first.input_value() == "開く":
        b.first.click()
        page.wait_for_load_state("networkidle")
        time.sleep(0.8)


def _rows(page):
    """Result rows -> [{token_csv, token_xbrl, title, code, filer}] for the current page."""
    return page.evaluate("""() => {
      const out = [];
      // the viewer puts the handler in href ("javascript:WEEE0050_Xbrl_Click('tok')"),
      // older screens used onclick — read both
      const h = a => (a.getAttribute('href')||'') + ' ' + (a.getAttribute('onclick')||'');
      for (const tr of document.querySelectorAll('table tr')) {
        let csvA = null, xbrlA = null;
        for (const a of tr.querySelectorAll('a')) {
          if (/csv.{0,3}click/i.test(h(a))) csvA = a;
          if (/xbrl.{0,3}click/i.test(h(a))) xbrlA = a;
        }
        if (!csvA && !xbrlA) continue;
        const tok = a => { const m = a && h(a).match(/\\('([^']+)'\\)/); return m ? m[1] : null; };
        const tds = Array.from(tr.querySelectorAll('td')).map(t => (t.innerText||'').trim());
        out.push({token_csv: tok(csvA), token_xbrl: tok(xbrlA), tds: tds.slice(0, 6)});
      }
      return out; }""")


def _click_fn(page, kind):
    """The page-scoped download entrypoints are WEEE0050_Csv_Click / WEEE0050_Xbrl_Click —
    resolve whatever name this build uses (naming shifted across viewer releases)."""
    return page.evaluate(
        f"""() => Object.getOwnPropertyNames(window)
                 .find(k => /{kind}_?Click$/i.test(k)) || null""")


def crawl(date_from: str, date_to: str, max_docs: int | None = None,
          prefer_csv: bool = True) -> list[dict]:
    from playwright.sync_api import sync_playwright
    os.makedirs(CACHE, exist_ok=True)
    manifest_path = os.path.join(CACHE, f"browser_manifest_{date_from}_{date_to}.json")
    manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else []
    have = {m["file"] for m in manifest}
    got = []

    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        page = br.new_context(user_agent=UA, locale="ja-JP",
                              viewport={"width": 1400, "height": 950}).new_page()
        page.goto(VIEWER, wait_until="networkidle", timeout=60000)

        _set_chk(page, "#vD_XBRLCHECK")                   # XBRL-carrying documents only
        _open_section(page, "BTNCLOSE_SYORUI")
        _set_chk(page, "#vD_SYORUI2")                     # 書類種別を指定する
        time.sleep(1.2)                                   # let the gx grid re-render settle —
        _set_chk(page, "#W0277vCHKSYORUI1", True)         # racing it desyncs server-side state
        time.sleep(0.5)                                   # (boxes default unchecked: check 有報
        ok = page.evaluate("() => document.querySelector('#W0277vCHKSYORUI1').checked")
        if not ok:                                        # only, verify, one retry)
            _set_chk(page, "#W0277vCHKSYORUI1", True)
        _open_section(page, "BTNCLOSE_KESSAN")
        _set_chk(page, "#vD_KESSAN2")                     # 提出期間を指定する
        time.sleep(0.5)
        # the date fields are masked GeneXus inputs — click + type, fill() bounces off
        page.click("#vD_KIKAN_FROM")
        page.keyboard.press("Meta+a")
        page.keyboard.type(date_from.replace("-", "/"))
        page.click("#vD_KIKAN_TO")
        page.keyboard.press("Meta+a")
        page.keyboard.type(date_to.replace("-", "/"))
        state = page.evaluate("""() => ({
            xbrl: document.querySelector('#vD_XBRLCHECK')?.checked,
            syorui2: document.querySelector('#vD_SYORUI2')?.checked,
            s1: document.querySelector('#W0277vCHKSYORUI1')?.checked,
            kessan2: document.querySelector('#vD_KESSAN2')?.checked,
            f: document.querySelector('#vD_KIKAN_FROM')?.value,
            t: document.querySelector('#vD_KIKAN_TO')?.value})""")
        print(f"  pre-search state: {state}")
        page.click("#BTNBTNSEARCHKESSAN")                 # any section's 検索 fires the query
        page.wait_for_load_state("networkidle", timeout=60000)
        time.sleep(2.5)

        total = page.evaluate(
            """() => (document.body.innerText.match(/全\\s*([0-9,]+)\\s*件/)||[])[1] || null""")
        print(f"viewer reports 全{total}件 for {date_from}..{date_to}")
        if total is None:
            page.screenshot(path=os.path.join(CACHE, "debug_search.png"), full_page=True)
            print(f"  no result count on page — screenshot -> {CACHE}/debug_search.png")

        fn_csv, fn_xbrl = _click_fn(page, "Csv"), _click_fn(page, "Xbrl")
        pageno, n, prev_sig = 1, 0, None
        while True:
            rows = _rows(page)
            # the pager's 次へ stays clickable on the last page — a repeated page signature
            # means we're not advancing (this spun 400+ "pages" before the guard existed)
            sig = (len(rows), rows[0]["tds"] if rows else None, rows[-1]["tds"] if rows else None)
            if sig == prev_sig:
                print(f"  page {pageno}: same content as previous page — done")
                break
            prev_sig = sig
            print(f"  page {pageno}: {len(rows)} rows")
            for r in rows:
                if max_docs and n >= max_docs:
                    break
                use_csv = prefer_csv and r["token_csv"] and fn_csv
                token = r["token_csv"] if use_csv else r["token_xbrl"]
                fn = fn_csv if use_csv else fn_xbrl
                if not (token and fn):
                    continue
                # dedupe on the row's EDINET code (viewer download names are generic
                # timestamps — the code column is the stable identity pre-download)
                mcode = re.search(r"\b(E\d{5})\b", " ".join(r["tds"]))
                code = mcode.group(1) if mcode else None
                fname = f"{code}_t{5 if use_csv else 1}.zip" if code else None
                if fname and (fname in have or os.path.exists(os.path.join(CACHE, fname))):
                    n += 1
                    continue
                try:
                    with page.expect_download(timeout=45000) as dl:
                        page.evaluate(f"window['{fn}']({json.dumps(token)})")
                    d = dl.value
                    name = d.suggested_filename or f"doc_{pageno}_{n}.zip"
                    m = re.search(r"(S[0-9A-Z]{7})", name)   # API-style docID name, if present
                    base = m.group(1) if m else (code or os.path.splitext(name)[0])
                    fname = f"{base}_t{5 if use_csv else 1}.zip"
                    dest = os.path.join(CACHE, fname)
                    if fname in have or os.path.exists(dest):
                        d.cancel() if hasattr(d, "cancel") else d.delete()
                    else:
                        d.save_as(dest)
                        rec = {"file": fname, "tds": r["tds"], "page": pageno}
                        manifest.append(rec)
                        got.append(rec)
                    n += 1
                    time.sleep(PAUSE)
                except Exception as ex:
                    print(f"    download failed on row (page {pageno}): {ex}")
                    time.sleep(2)
            json.dump(manifest, open(manifest_path, "w"), ensure_ascii=False, indent=1)
            if max_docs and n >= max_docs:
                break
            nxt = page.locator("a:has-text('次へ')")
            if not nxt.count() or not nxt.first.is_visible():
                break
            nxt.first.click()
            page.wait_for_load_state("networkidle", timeout=60000)
            time.sleep(1.5)
            pageno += 1
        br.close()
    print(f"downloaded {len(got)} new filings (cache total {len(manifest)}); manifest -> {manifest_path}")
    return manifest


def build_store():
    """Extract every cached filing ZIP into the shared store (idempotent)."""
    import edinet_fundamentals as EF
    rows, skipped = {}, 0
    for fn in sorted(os.listdir(CACHE)):
        if not fn.endswith(".zip"):
            continue
        rec = EF.extract_from_zip(os.path.join(CACHE, fn))
        if rec and rec.get("edinet_code"):
            rows[rec["edinet_code"]] = rec
        else:
            skipped += 1
    store = EF.merge_store(rows)
    print(f"extracted {len(rows)} filings ({skipped} unparseable) -> store {len(store)} issuers")
    return store


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="date_from", required=True)
    ap.add_argument("--to", dest="date_to", required=True)
    ap.add_argument("--max-docs", type=int, default=None)
    ap.add_argument("--build-store", action="store_true", help="extract cache -> store after crawl")
    a = ap.parse_args()
    crawl(a.date_from, a.date_to, a.max_docs)
    if a.build_store:
        build_store()
