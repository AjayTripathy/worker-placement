"""SEC EDGAR — three query modes.

  1) FULL-TEXT search across all EDGAR filings  (default)
       Endpoint: https://efts.sec.gov/LATEST/search-index
       Best for: "any mention of this entity / phrase in any filing"
       Risk: common words (e.g. "Contrary", "Antler") return noise.

  2) COMPANY-NAME search returning specific filers  (extra['edgar_mode']='company')
       Endpoint: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=NAME&output=atom
       Best for: "is there an SEC filer with this name? what's their CIK?"
       Returns one row per matched filer with CIK, business address, SIC.

  3) FORM D DETAIL: parse offering doc for a specific CIK  (extra['edgar_mode']='form_d_detail',
                                                            extra['cik']='CIK')
       Steps: list filings for CIK, find Form D, fetch primary_doc.xml, parse:
         - totalOfferingAmount / totalAmountSold / totalRemaining
         - numberOfInvestors / dateOfFirstSale / minimumInvestmentAccepted
         - federalExemptionsExclusions (which Reg D exemption used)
         - issuerList (entity name, address, jurisdiction)
         - relatedPersonsList (officers, directors, promoters)
         - signatureBlock signer
       This is what surfaces $X-claimed vs $Y-actual mismatches automatically.

No auth, but SEC requires descriptive User-Agent including contact email.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ['public_equity', 'corporate_ipo_dd'],
    "applies_universally": True,
    "summary": 'EDGAR filings pull (submissions, full-text, facts). Any SEC registrant.',
}

import os
from urllib.parse import urlencode, quote

from .base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ConnectorObservation,
    ErrorKind,
    safe_get,
)


SEC_SEARCH = "https://efts.sec.gov/LATEST/search-index"
SEC_COMPANY = "https://www.sec.gov/cgi-bin/browse-edgar"


class SecEdgarConnector(BaseConnector):
    source_id = "sec_edgar"
    rate_limit_per_min = 10  # SEC asks <10 req/sec; be conservative
    user_agent = os.getenv("SEC_USER_AGENT", "SignalOS Buyside DD research@signalos.invalid")

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        # Three modes:
        #   fulltext       — full-text search across EDGAR (default; noisy for common words)
        #   company        — filer browse by name (returns CIKs)
        #   form_d_detail  — parse Form D primary doc for a specific CIK
        mode = (request.extra or {}).get("edgar_mode", "fulltext")
        if mode == "form_d_detail":
            # Doesn't need entity_name; uses extra['cik'] instead.
            return self._query_form_d_detail(request)

        q = request.entity_name or request.person_name
        if not q:
            return self._fail(request, ErrorKind.UNSUPPORTED, "need entity_name or person_name")
        if mode == "company":
            return self._query_company(request, q)
        return self._query_fulltext(request, q)

    def _query_fulltext(self, request: ConnectorRequest, q: str) -> ConnectorResult:
        forms = (request.extra.get("forms") if request.extra else None) or "D,ADV,10-K,S-1,8-K"
        # SEC's full-text search rejects URL-encoded commas in forms; keep them literal.
        quoted_q = quote(f'"{q}"', safe="")
        url_parts = [f"q={quoted_q}", f"forms={forms}"]
        if request.year:
            url_parts += ["dateRange=custom", f"startdt={request.year}-01-01", f"enddt={request.year}-12-31"]
        url = f"{SEC_SEARCH}?{'&'.join(url_parts)}"

        self._throttle()
        sess = self._session()
        sess.headers["User-Agent"] = self.user_agent
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return self._fail(request, ek, ed)
        try:
            data = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text)

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            return self._ok(request, [
                ConnectorObservation(attribute="edgar_filing_count", value=0, source_url=url),
            ], raw=r.text)

        obs = [
            ConnectorObservation(attribute="edgar_filing_count", value=len(hits), source_url=url),
        ]
        for i, h in enumerate(hits[:20]):
            src = h.get("_source", {})
            adsh = h.get("_id", "").split(":")[0]
            cik = (src.get("ciks") or [None])[0]
            obs.append(ConnectorObservation(
                attribute=f"edgar_hit[{i}]",
                value={
                    "form": src.get("form"),
                    "filing_date": src.get("file_date"),
                    "company": (src.get("display_names") or [None])[0],
                    "cik": cik,
                    "accession": adsh,
                    "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh.replace('-', '')}/{adsh}-index.htm" if cik and adsh else None,
                },
                source_url=url,
            ))
        return self._ok(request, obs, raw=r.text)


    def _resolve_cik(self, request: ConnectorRequest) -> str | None:
        """Resolve a filer CIK from request.entity_name via EDGAR company browse.

        Returns the first matching CIK (as a string) or None if the name has no
        EDGAR presence. Single exact matches redirect straight to the filer page;
        multi-matches render a results table — `CIK=NNNN` appears in both.
        """
        import re
        name = (request.entity_name or "").strip()
        if not name:
            return None
        url = (f"{SEC_COMPANY}?action=getcompany&company={quote(name, safe='')}"
               f"&type=D&dateb=&owner=include&count=40")
        sess = self._session()
        sess.headers["User-Agent"] = self.user_agent
        self._throttle()
        r, ek, ed = safe_get(sess, url)
        if r is None or "No matching" in r.text or "No companies" in r.text:
            return None
        m = re.search(r'CIK=(\d{4,10})', r.text)
        return m.group(1) if m else None

    def _query_form_d_detail(self, request: ConnectorRequest) -> ConnectorResult:
        """Pull and parse Form D primary_doc.xml for a specific CIK.

        Required: extra['cik'] (string, no leading zeros okay).
        Optional: extra['accession'] to target a specific filing.

        Returns observations for offering amount, sold amount, investors,
        exemptions, issuer info, related persons.
        """
        extra = request.extra or {}
        cik = extra.get("cik")
        if not cik:
            # No CIK supplied — the common case for a freshly-extracted issuer
            # claim where no resolver pinned the CIK. Resolve it from the entity
            # name via EDGAR company browse rather than failing UNSUPPORTED, so
            # the amount-match f-rule can actually run. If the issuer has NO
            # EDGAR presence at all, surface that as the signal (match_count=0)
            # — that absence is itself the finding, not a dead error.
            cik = self._resolve_cik(request)
            if cik is None:
                return self._ok(request, [
                    ConnectorObservation(
                        attribute="edgar_company_match_count", value=0,
                        source_url=(f"{SEC_COMPANY}?action=getcompany&company="
                                    f"{quote(request.entity_name or '', safe='')}&type=D"),
                    ),
                ], raw="form_d_detail: no CIK supplied and no EDGAR company match for issuer name")
        cik_padded = str(cik).lstrip("0").rjust(10, "0")
        cik_int = str(int(cik))

        # Step 1: list Form D filings for this CIK
        filings_url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&CIK={cik_padded}&type=D&dateb=&owner=include&count=40&output=atom"
        )
        sess = self._session()
        sess.headers["User-Agent"] = self.user_agent
        sess.headers["Accept"] = "application/atom+xml"
        self._throttle()
        r, ek, ed = safe_get(sess, filings_url)
        if r is None:
            return self._fail(request, ek, f"filings list: {ed}")

        import re
        # Extract accession numbers from atom feed.
        # The actual XML element is <accession-number>NNN-NN-NNNNNN</accession-number>
        # (kebab-case, lowercase). Earlier versions of this code used
        # `AccessionNumber>` which matched nothing — caused a silent 0-result return.
        accessions = re.findall(r'accession-number>([\d-]+)<', r.text)
        if not accessions:
            # Fallback: extract from any URL with accession-style param
            accessions = re.findall(r'accession[_-]?number=([\d-]+)', r.text, re.IGNORECASE)
        # Dedupe preserving order
        seen = set()
        accessions = [a for a in accessions if not (a in seen or seen.add(a))]
        target_accession = extra.get("accession")
        if target_accession:
            accessions = [a for a in accessions if a == target_accession]
        if not accessions:
            return self._ok(request, [
                ConnectorObservation(attribute="form_d_count", value=0, source_url=filings_url),
            ], raw=r.text[:500])

        all_obs = [ConnectorObservation(attribute="form_d_count", value=len(accessions), source_url=filings_url)]

        # Step 2: for each accession, fetch primary_doc.xml and parse
        for i, acc in enumerate(accessions[:5]):  # cap at 5 to be polite
            acc_no_dashes = acc.replace("-", "")
            xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_no_dashes}/primary_doc.xml"
            self._throttle()
            r2, ek2, ed2 = safe_get(sess, xml_url)
            if r2 is None:
                all_obs.append(ConnectorObservation(
                    attribute=f"form_d[{i}].fetch_error",
                    value=f"{ek2}/{ed2}", source_url=xml_url,
                ))
                continue
            parsed = self._parse_form_d_xml(r2.text)
            parsed["accession"] = acc
            parsed["xml_url"] = xml_url
            all_obs.append(ConnectorObservation(
                attribute=f"form_d[{i}]",
                value=parsed,
                source_url=xml_url,
            ))
            # Also surface the headline numbers as flat observations for easy comparator pickup
            for k in ("totalOfferingAmount", "totalAmountSold", "numberOfInvestors", "dateOfFirstSale"):
                v = parsed.get(k)
                if v is not None:
                    all_obs.append(ConnectorObservation(
                        attribute=f"form_d[{i}].{k}",
                        value=v, source_url=xml_url,
                    ))
        return self._ok(request, all_obs, raw=r.text[:1000])

    @staticmethod
    def _parse_form_d_xml(xml_text: str) -> dict:
        """Defensive parse of Form D primary_doc.xml. Returns a flat dict of
        the most useful fields. The XML namespace varies slightly between
        years — strip namespaces before parsing for simplicity."""
        import re, xml.etree.ElementTree as ET

        def _strip_ns(s: str) -> str:
            return re.sub(r'xmlns(:\w+)?="[^"]+"', '', s)

        try:
            root = ET.fromstring(_strip_ns(xml_text))
        except ET.ParseError as e:
            return {"_parse_error": str(e)}

        def _find_text(root, *paths) -> str | None:
            for p in paths:
                el = root.find(p)
                if el is not None and (el.text or "").strip():
                    return el.text.strip()
            return None

        def _find_all_text(root, path) -> list[str]:
            return [el.text.strip() for el in root.findall(path) if el is not None and (el.text or "").strip()]

        def _to_num(s: str | None):
            if not s: return None
            try: return float(s.replace(",", "").replace("$", "").strip())
            except (ValueError, AttributeError): return None

        out = {}
        out["totalOfferingAmount"] = _to_num(_find_text(root, ".//totalOfferingAmount"))
        out["totalAmountSold"] = _to_num(_find_text(root, ".//totalAmountSold"))
        out["totalRemaining"] = _to_num(_find_text(root, ".//totalRemaining"))
        out["minimumInvestmentAccepted"] = _to_num(_find_text(root, ".//minimumInvestmentAccepted"))
        out["dateOfFirstSale"] = _find_text(root, ".//dateOfFirstSale")
        # numberOfInvestors can be wrapped in numberOfInvestorsList
        n_inv = _find_text(root, ".//numberOfInvestors", ".//numberOfInvestorsList/numberOfInvestors")
        out["numberOfInvestors"] = int(n_inv) if (n_inv and n_inv.isdigit()) else n_inv
        # Federal exemptions
        out["federalExemptions"] = _find_all_text(root, ".//federalExemptionsExclusions/item")
        if not out["federalExemptions"]:
            out["federalExemptions"] = _find_all_text(root, ".//federalExemption")
        # Issuers. Form D primary_doc.xml wraps the filer in <primaryIssuer>
        # (with optional additional filers under <issuerList>/<issuer>). An
        # earlier version only searched ".//issuer", which matches NEITHER
        # <primaryIssuer> nor <issuerList> — so issuers came back [] and every
        # SPV-conduit attribution (the issuer entityName carries the
        # "<OpCo> <Month Year> a Series of <X> LLC" signal) was silently lost.
        issuers = []
        for iss in (root.findall(".//primaryIssuer")
                    + root.findall(".//issuerList/issuer")
                    + root.findall(".//issuer")):
            name = _find_text(iss, "entityName", ".//entityName")
            if not name:
                continue
            issuers.append({
                "entityName": name,
                "cik": _find_text(iss, "cik", ".//cik"),
                "entityType": _find_text(iss, "entityType", ".//entityType"),
                "jurisdiction": _find_text(iss, "jurisdictionOfInc", "jurisdictionOfIncorporation",
                                           ".//jurisdictionOfInc", ".//jurisdictionOfIncorporation"),
                "city": _find_text(iss, ".//issuerAddress/city"),
                "state": _find_text(iss, ".//issuerAddress/stateOrCountry"),
                "zip": _find_text(iss, ".//issuerAddress/zipCode"),
            })
        # Dedup by (entityName, cik) preserving order.
        seen_iss = set()
        out["issuers"] = [i for i in issuers
                          if not ((i["entityName"], i.get("cik")) in seen_iss
                                  or seen_iss.add((i["entityName"], i.get("cik"))))]
        # Related persons
        related = []
        for rp in root.findall(".//relatedPersonInfo"):
            related.append({
                "firstName": _find_text(rp, ".//relatedPersonName/firstName"),
                "lastName": _find_text(rp, ".//relatedPersonName/lastName"),
                "city": _find_text(rp, ".//relatedPersonAddress/city"),
                "state": _find_text(rp, ".//relatedPersonAddress/stateOrCountry"),
                "relationship": _find_all_text(rp, ".//relatedPersonRelationshipList/relationship"),
            })
        out["relatedPersons"] = related
        # Industry
        out["industryGroupType"] = _find_text(root, ".//industryGroupType", ".//industryGroup/industryGroupType")
        # Sales commissions / finder fees
        out["salesCommissions"] = _to_num(_find_text(root, ".//salesCommissions/dollarAmount"))
        out["finderFee"] = _to_num(_find_text(root, ".//findersFee/dollarAmount"))
        return out

    def _query_company(self, request: ConnectorRequest, q: str) -> ConnectorResult:
        """EDGAR company-name browse → returns matching filer entities (with CIK)."""
        url = f"{SEC_COMPANY}?action=getcompany&company={quote(q, safe='')}&type=&dateb=&owner=include&count=40&output=atom"
        self._throttle()
        sess = self._session()
        sess.headers["User-Agent"] = self.user_agent
        sess.headers["Accept"] = "application/atom+xml"
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return self._fail(request, ek, ed)

        # The atom feed for multi-entity search has a Perl-quirk: <entry title="ARRAY(...)">
        # and the entity name doesn't appear inside <entry>. Need to fetch the HTML
        # results page to get the (CIK, name) pairs reliably from the table rows.
        # The atom feed is still useful to count matches and get CIK list.
        import re
        text = r.text

        # No-match early exit
        if "No matching" in text or "No companies" in text:
            return self._ok(request, [
                ConnectorObservation(attribute="edgar_company_match_count", value=0, source_url=url),
            ], raw=text[:500])

        # Get the HTML page (no &output=atom) — it has a clean table with CIK + name columns
        html_url = url.replace("&output=atom", "")
        r2, _, _ = safe_get(sess, html_url)
        if r2 is None:
            return self._fail(request, ErrorKind.PARSE_FAIL, "html fallback failed")

        # Parse the results table. Actual EDGAR HTML format:
        #   <tr [class="evenRow"]>
        #     <td valign="top" scope="row"><a href="...CIK=NNNNNN...">NNNNNN</a></td>
        #     <td scope="row">NAME</td>
        #     <td valign="top" scope="row"><a href="...State=XX...">XX</a></td>
        #   </tr>
        # Note: HTML uses &amp; for &.
        row_pattern = re.compile(
            r'<tr[^>]*>\s*'
            r'<td[^>]*scope="row"[^>]*>\s*<a[^>]*CIK=(\d{4,10})[^>]*>\d+</a>\s*</td>\s*'
            r'<td[^>]*scope="row"[^>]*>([^<]+)</td>',
            re.IGNORECASE | re.DOTALL,
        )
        rows = row_pattern.findall(r2.text)
        if not rows:
            return self._ok(request, [
                ConnectorObservation(attribute="edgar_company_match_count", value=0, source_url=html_url),
            ], raw=r2.text[:500])

        obs = [ConnectorObservation(attribute="edgar_company_match_count", value=len(rows), source_url=html_url)]
        for i, (cik, name) in enumerate(rows[:20]):
            obs.append(ConnectorObservation(
                attribute=f"edgar_company_match[{i}]",
                value={
                    "cik": cik,
                    "name": name.strip(),
                    "filings_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=&dateb=&owner=include&count=40",
                },
                source_url=html_url,
            ))
        return self._ok(request, obs, raw=r2.text[:2000])


if __name__ == "__main__":
    c = SecEdgarConnector()
    print("=== Full-text mode ===")
    r = c.query(ConnectorRequest(entity_name="Flux Capital"))
    print(f"success={r.success} obs={len(r.observations)}")
    for o in r.observations[:3]:
        print(f"  {o.attribute} = {str(o.value)[:200]}")
    print()
    print("=== Company mode (Contrary) ===")
    r = c.query(ConnectorRequest(entity_name="Contrary", extra={"edgar_mode": "company"}))
    print(f"success={r.success} obs={len(r.observations)}")
    for o in r.observations[:6]:
        print(f"  {o.attribute} = {str(o.value)[:200]}")
    print()
    print("=== Company mode (American Housing) ===")
    r = c.query(ConnectorRequest(entity_name="American Housing", extra={"edgar_mode": "company"}))
    print(f"success={r.success} obs={len(r.observations)}")
    for o in r.observations[:6]:
        print(f"  {o.attribute} = {str(o.value)[:200]}")
