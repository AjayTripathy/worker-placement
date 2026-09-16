"""Laserfiche WebLink connector — municipal planning / entitlement document archive.

WHY THIS EXISTS. Many U.S. cities publish their development-review records (site-plan
applications, staff reports, approved drawings) through **Laserfiche WebLink**, a JS app sitting
behind a **Cloudflare JS-challenge + a session cookie gate**. Plain `requests`/`curl` get 403,
and even a full browser *fingerprint* (the Sec-Ch-Ua/Sec-Fetch header trick) fails the JS
challenge. The architecture doc listed these portals as "blocked from this environment."

They are not blocked — they require driving a REAL browser. This connector encodes the method,
validated 2026-06-16 on the City of Bozeman to pull the decisive primary record on the
"Sun Valley"/Blackwood Groves Block 9 deal (City file 24635): the entitlement's applicant/owner
were the master developer, NOT the sponsor marketing the deal, and the entitled product was 30
apartment units, not 33 for-sale rowhouses — a finding obtainable ONLY from this document.

WHAT IT SUPPLIES (R/f(M) M-side). Primary entitlement records keyed by project number/name:
applicant of record, property owner, unit count, product type, zoning, lot area, approval status.
These verify the load-bearing claims of any real-estate / development offering: "we are
developing this," "X units," "approved," "for-sale at $Y."

HEAVYWEIGHT / ESCALATION TIER. This spawns a real visible Chrome via Playwright (channel="chrome").
It is NOT an HTTP connector — it is slow (~30-90s), needs a display, and should be dispatched
deliberately (like planet_imagery), when a gated planning portal must be read and HTTP fails.
Degrades gracefully to UNSUPPORTED (with the manual URL) if Playwright is unavailable.

METHOD (see [[reference_browser_automation_gated_portals]]):
  1. real Chrome, visible, one context (cookies on)
  2. LAND on the Browse page first to set the session cookie, THEN navigate deeper
  3. search box -> Laserfiche query; result/doc links are javascript:void(0) -> click to capture
     the DocView id from the URL
  4. electronic docs: read PDFViewerApplication.url from the viewer, fetch IN-PAGE
     (credentials:'include') -> base64 -> save. Image-only docs show "no pages".
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['real_estate_development', 'construction_activity_claim'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Generic Laserfiche municipal document-archive driver for entitlement verification.',
}
import base64, re
from urllib.parse import quote
from datetime import timezone, datetime

from .base import BaseConnector, ConnectorRequest, ConnectorResult, ConnectorObservation, ErrorKind

# Per-tenant presets. base = WebLink root; repo = Laserfiche repo name; planning_root = the folder
# id whose subtree holds planning projects (discover once by browsing). Add cities as validated.
TENANTS = {
    "bozeman_mt": {
        "base": "https://weblink.bozeman.net/WebLink",
        "repo": "BOZEMAN",
        "planning_root": 136921,          # \Planning\Planning Projects
        "manual_url": "https://weblink.bozeman.net/WebLink/Browse.aspx?id=136921&dbid=0&repo=BOZEMAN",
    },
}

# RELIABLE fields only: the section-based "principal parties," which appear with their value
# directly after the section header in pdfminer's reading order. These are the decision-critical
# ones — they expose the "sponsor presents someone else's entitlement as their own" divergence
# (AHC: owner/applicant were the master developer, not the sponsor).
#
# DO NOT regex the PROJECT INFORMATION grid (units, lot area, zoning) from pdfminer text — it is a
# TWO-COLUMN layout (labels in one run, values in another; see architecture doc §7 columnar-form
# problem), so label-anchored matching is unreliable. The SAVED PDF is authoritative for those:
# read pdf_path with the multimodal reader, which renders label-adjacent values correctly.
_FORM_FIELDS = [
    ("property_owner", r"PROPERTY OWNER.*?Company Name:\s*(.+?)(?:\s+Name:|$)"),
    ("applicant", r"APPLICANT.*?Company Name:\s*(.+?)(?:\s+Name:|$)"),
    ("representative", r"REPRESENTATIVE.*?Company Name:\s*(.+?)(?:\s+Name:|$)"),
]


def fetch_weblink(tenant_key: str, search_term: str, save_dir: str = "/tmp",
                  doc_name_filter: str | None = None, headless: bool = False, max_docs: int = 6):
    """Drive a real browser to search a Laserfiche WebLink planning archive and return matched
    documents. Returns list of {name, doc_id, text, pdf_path}. Raises ImportError if Playwright
    is unavailable (caller catches -> UNSUPPORTED)."""
    from playwright.sync_api import sync_playwright   # heavy import, deferred
    t = TENANTS[tenant_key]; base, repo, root = t["base"], t["repo"], t["planning_root"]
    out = []
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch(channel="chrome", headless=headless)
        except Exception:
            b = pw.chromium.launch(headless=headless)
        ctx = b.new_context(accept_downloads=True); pg = ctx.new_page(); pg.set_default_timeout(45000)
        # 1. LAND to establish session cookie
        pg.goto(f"{base}/Browse.aspx?id={root}&dbid=0&repo={repo}", wait_until="domcontentloaded")
        pg.wait_for_timeout(3000)
        # 2. search via the box
        box = pg.query_selector('input[placeholder*="earch" i]')
        box.fill(search_term); pg.keyboard.press("Enter"); pg.wait_for_timeout(7000)
        # 3. collect doc result links (text contains the search term); links are javascript -> click
        names = []
        for a in pg.query_selector_all("a"):
            try:
                tx = a.inner_text().strip()
                if search_term.split()[0] in tx and tx not in names:
                    names.append(tx)
            except Exception:
                pass
        if doc_name_filter:
            names = [n for n in names if re.search(doc_name_filter, n, re.I)] or names
        for nm in names[:max_docs]:
            el = next((a for a in pg.query_selector_all("a")
                       if (a.inner_text() or "").strip() == nm), None)
            if not el:
                continue
            try:
                with pg.expect_popup(timeout=4000) as pi:
                    el.click()
                p2 = pi.value; p2.wait_for_load_state("domcontentloaded"); url = p2.url
            except Exception:
                el.click(); pg.wait_for_timeout(3500); url = pg.url; p2 = pg
            m = re.search(r"[?&]id=(\d+)", url); did = m.group(1) if m else None
            if did and p2 is not pg:
                try: p2.close()
                except Exception: pass
            if not did:
                continue
            # navigate to DocView explicitly and let pdf.js load before reading its url
            pg.goto(f"{base}/DocView.aspx?id={did}&dbid=0&repo={repo}", wait_until="domcontentloaded")
            pg.wait_for_timeout(6000)
            p2 = pg
            pdf_url = None
            for fr in p2.frames:
                try:
                    u = fr.evaluate("()=>(window.PDFViewerApplication&&window.PDFViewerApplication.url)||null")
                    if u: pdf_url = u; break
                except Exception:
                    pass
            text, pdf_path = "", None
            if pdf_url:
                try:
                    b64 = p2.evaluate("""async(u)=>{const r=await fetch(u,{credentials:'include'});
                        const a=await r.arrayBuffer();let s='';const b=new Uint8Array(a);
                        for(let i=0;i<b.length;i++)s+=String.fromCharCode(b[i]);return btoa(s);}""", pdf_url)
                    data = base64.b64decode(b64)
                    pdf_path = f"{save_dir}/laserfiche_{repo}_{did}.pdf"
                    open(pdf_path, "wb").write(data)
                    try:
                        from pdfminer.high_level import extract_text
                        text = extract_text(pdf_path) or ""
                    except Exception:
                        text = ""
                except Exception:
                    pass
            if p2 is not pg:
                try: p2.close()
                except Exception: pass
            out.append({"name": nm, "doc_id": did, "text": text, "pdf_path": pdf_path})
        ctx.close(); b.close()
    return out


def parse_application_form(text: str) -> dict:
    """Extract applicant/owner/units/etc. from a flattened dev-review-application form text."""
    t = re.sub(r"\s+", " ", text or "")
    fields = {}
    for key, pat in _FORM_FIELDS:
        m = re.search(pat, t, re.I | re.S)
        if m:
            fields[key] = m.group(1).strip()[:120]
    return fields


class LaserficheWebLinkConnector(BaseConnector):
    """Pull municipal entitlement/planning documents from a Laserfiche WebLink archive.

    request.extra:
      tenant: key in TENANTS (e.g. 'bozeman_mt')   [required]
      search: project number or name (e.g. '24635' or 'Blackwood Block 9')  [required]
      doc_filter: optional regex on document name (e.g. 'application summary')
      headless: bool (default False — visible Chrome passes Cloudflare most reliably)
    """
    source_id = "laserfiche_weblink"
    timeout_s = 120.0

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        x = request.extra or {}
        tenant = x.get("tenant"); search = x.get("search") or request.parcel_id or request.address
        if not tenant or tenant not in TENANTS:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              f"need extra.tenant in {sorted(TENANTS)}")
        if not search:
            return self._fail(request, ErrorKind.UNSUPPORTED, "need extra.search (project # or name)")
        try:
            docs = fetch_weblink(tenant, str(search), save_dir=x.get("save_dir", "/tmp"),
                                 doc_name_filter=x.get("doc_filter"), headless=bool(x.get("headless", False)))
        except ImportError:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              f"Playwright unavailable; manual: {TENANTS[tenant]['manual_url']}")
        except Exception as e:
            return self._fail(request, ErrorKind.NETWORK, str(e)[:200])
        if not docs:
            return self._fail(request, ErrorKind.NO_DATA,
                              f"no documents matched '{search}' in {tenant}")
        now = datetime.now(timezone.utc)
        obs = []
        for d in docs:
            parsed = parse_application_form(d.get("text", "")) if d.get("text") else {}
            obs.append(ConnectorObservation(
                attribute="planning_document", value=d["name"], observation_date=now,
                confidence=0.95, source_url=TENANTS[tenant]["manual_url"],
                extra={"doc_id": d["doc_id"], "pdf_path": d["pdf_path"],
                       "parsed_fields": parsed, "tenant": tenant}))
        return self._ok(request, obs, raw=str([d["name"] for d in docs]))


if __name__ == "__main__":
    # validated demo: the AHC / Block 9 entitlement
    c = LaserficheWebLinkConnector()
    r = c.query(ConnectorRequest(extra={"tenant": "bozeman_mt", "search": "24635",
                                        "doc_filter": "application summary"}))
    print("success:", r.success)
    for o in r.observations:
        print(" ", o.value, "| pdf:", o.extra.get("pdf_path"), "| fields:", o.extra.get("parsed_fields"))
