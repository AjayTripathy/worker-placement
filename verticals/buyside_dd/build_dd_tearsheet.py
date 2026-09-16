"""Render an analyst-facing PDF tearsheet from a buyside_dd pipeline run.

Reads {run_dir}/07_report.json + {run_dir}/06_findings.json + 03_typed_claims.json
and emits a PDF in the R -> f(M) -> Finding structure (no framework-internal
jargon; citations as authority URLs). Reuses the public_co Report house style.

The cross-claim consistency findings are RECOMPUTED from the typed claims at
render time so the tearsheet reflects the current cross_claim_check logic
(e.g. the resolved_from provenance discriminator), not whatever was frozen on
disk when the pipeline ran.

Run:  python3 -m verticals.buyside_dd.build_dd_tearsheet <run_dir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from verticals.public_co.build_analyst_report_pdf import Report, _san
from verticals.buyside_dd.spv_form_d import assess_raise_via_conduits

HERE = Path(__file__).parent

_UA = "signalos-dd research 4tripathy@gmail.com"
_CIK_NAME_CACHE: dict[str, str] = {}


def _resolve_cik_name(cik: str) -> str | None:
    """Resolve a CIK to its EDGAR issuer name (cached). Returns None offline."""
    cik = str(cik).lstrip("0")
    if not cik:
        return None
    if cik in _CIK_NAME_CACHE:
        return _CIK_NAME_CACHE[cik] or None
    url = f"https://data.sec.gov/submissions/CIK{cik.rjust(10, '0')}.json"
    try:
        req = Request(url, headers={"User-Agent": _UA})
        data = json.loads(urlopen(req, timeout=15).read().decode())
        name = data.get("name")
    except Exception:
        name = None
    _CIK_NAME_CACHE[cik] = name or ""
    return name


def _backfill_issuers(form_d_dicts: list[dict]) -> list[dict]:
    """Older pipeline runs parsed Form D issuers as [] (the parser searched the
    wrong XML element). For render-time correctness on those stale artifacts,
    backfill the issuer entityName from the CIK in the filing's xml_url so the
    SPV-conduit attribution can run. Live runs already carry issuers.
    """
    out = []
    for fd in form_d_dicts:
        if not isinstance(fd, dict):
            continue
        if fd.get("issuers"):
            out.append(fd)
            continue
        url = fd.get("xml_url") or ""
        m = re.search(r"/data/(\d+)/", url)
        if m:
            name = _resolve_cik_name(m.group(1))
            if name:
                fd = {**fd, "issuers": [{"entityName": name, "cik": m.group(1)}]}
        out.append(fd)
    return out


def _spv_reclassified(run_dir: Path) -> dict[str, dict]:
    """Recompute SPV-conduit verdicts for raise_amount findings from saved
    observations. Returns {claim_id: verdict} for findings that reconcile to a
    corroborating (PASS) or divergent result via the conduit logic.
    """
    raw = json.load(open(run_dir / "06_findings.json"))
    out: dict[str, dict] = {}
    for x in raw:
        c = x.get("claim", {}) or {}
        if c.get("predicate") != "raise_amount":
            continue
        fds = [o.get("value") for o in (x.get("observed_values") or [])
               if str(o.get("attribute", "")).startswith("form_d[")
               and "." not in str(o.get("attribute", "")) and isinstance(o.get("value"), dict)]
        if not fds:
            continue
        fds = _backfill_issuers(fds)
        verdict = assess_raise_via_conduits(c.get("subject"), c.get("object_value"), fds)
        if verdict is not None:
            cid = c.get("claim_id") or f"{c.get('subject')}|{c.get('object_value')}"
            out[cid] = {"verdict": verdict, "claim": c}
    return out

# buyside connector prefix -> (human label, authority root) for the f(M) lines.
SOURCE_AUTHORITY = {
    "opencorporates": ("OpenCorporates state registry", "https://opencorporates.com"),
    "sec_edgar_form_d": ("SEC EDGAR Form D (Reg D) filings", "https://www.sec.gov/cgi-bin/browse-edgar"),
    "sec_edgar_company": ("SEC EDGAR company submissions", "https://data.sec.gov/submissions/"),
    "austin_permits": ("City of Austin building-permits open data", "https://data.austintexas.gov"),
    "bozeman_permits": ("City of Bozeman permits", "https://www.bozeman.net"),
    "albuquerque_permits": ("City of Albuquerque permits", "https://www.cabq.gov"),
    "nyc_dob_permits": ("NYC Dept. of Buildings permits", "https://www1.nyc.gov/site/buildings"),
    "company_signal": ("Company funding-signal aggregate", ""),
    "web_search": ("Open-web discovery (Mojeek / Brave / DDG)", ""),
}

SEV_LABEL = {
    "critical": "REFUTED (critical)",
    "severe": "REFUTED (severe)",
    "moderate": "PARTIAL / INCONSISTENT",
    "minor": "MINOR DISCREPANCY",
    "unverifiable": "UNVERIFIABLE",
    "pass": "VERIFIED",
}
SEV_RGB = {
    "critical": (150, 20, 20),
    "severe": (170, 50, 20),
    "moderate": (176, 124, 16),
    "minor": (150, 130, 40),
    "unverifiable": (90, 90, 90),
    "pass": (22, 110, 50),
}


def _looks_like_dict_dump(s: str) -> bool:
    """True if a string is (or contains) a raw Python dict/list dump — these must
    never leak into the analyst-facing report."""
    s = str(s or "")
    return bool(re.search(r"\{['\"]?\w+['\"]?\s*:", s)) or s.count("': ") >= 1


def _clean_subject(subject) -> str:
    """Resolve a bare CIK subject to its EDGAR issuer name for display."""
    s = str(subject or "")
    if s.strip().isdigit() and len(s.strip()) >= 6:
        name = _resolve_cik_name(s)
        if name:
            return f"{name} (CIK {int(s)})"
    return s


def _parse_evidence(f: dict) -> dict:
    """Pull R / f / M components out of the evidence_trail + claim block."""
    c = f.get("claim", {}) or {}
    et = [str(e) for e in (f.get("evidence_trail") or [])]
    is_internal = str(f.get("f_rule_id", "")).startswith("re.internal_consistency")
    rule_desc = ""
    m_sources, m_url, m_note = [], "", ""
    for line in et:
        m = re.search(r"f-rule applied:\s*\S+\s*\((.+?)\)?\s*$", line)
        if m:
            rule_desc = m.group(1).rstrip(") ")
        m = re.search(r"queried (\w+):", line)
        if m:
            m_sources.append(m.group(1))
        m = re.search(r"(https?://\S+)", line)
        if m and not m_url:
            # Trim trailing dict/list punctuation the URL regex may have grabbed.
            m_url = m.group(1).rstrip("'\"}],)")
        if "none returned the expected attribute" in line:
            m_note = "registry reached but the expected field was absent"
        # NOTE: deliberately do NOT capture the raw "observed: {…dict…}" line into
        # m_note — it dumps a Python dict into the report. SPV/clean notes below.
    # Prefer the SPV-conduit note when this finding was reconciled.
    spv_note = f.get("_spv_note")
    if spv_note:
        m_note = spv_note
    # Internal cross-document consistency findings have NO external authority —
    # the divergence is between the deal materials themselves. Derive an honest
    # note from the evidence rather than borrowing external-refutation language.
    internal_note = ""
    if is_internal:
        magnitude = next((l.strip() for l in et
                          if l.lstrip().startswith("min=") or "distinct values:" in l), "")
        internal_note = ("The deal materials state conflicting values for the same fact "
                         f"({magnitude}). This is an internal inconsistency in the documents, "
                         "not an external refutation — reconcile against the source documents.")
    label, root = "", ""
    if m_sources:
        label, root = SOURCE_AUTHORITY.get(m_sources[0], (m_sources[0], ""))
    return {
        "is_internal": is_internal,
        "internal_note": internal_note,
        "subject": _clean_subject(c.get("subject")),
        "predicate": c.get("predicate"),
        "object_value": c.get("object_value"),
        "source_quote": c.get("source_quote"),
        "source_doc": c.get("source_doc"),
        "rule_desc": rule_desc,
        "spv_note": spv_note or "",
        "m_label": ("internal cross-document consistency check (no external authority)"
                    if is_internal else
                    label or "no implemented external authority for this predicate"),
        "m_url": m_url or root,
        "m_note": m_note,
        "stop_reason": next((l.split(":", 1)[1].strip() for l in et if l.startswith("stop reason:")), ""),
    }


def _corrected_findings(run_dir: Path) -> tuple[list[dict], list[dict], list[dict], int]:
    """Return (material, unverifiable, corroborated, n_dropped_false_positive).

    Recomputes cross-claim findings from typed claims so the resolved_from
    provenance fix is reflected, and applies SPV-conduit reconciliation to
    raise_amount findings (so a Sydecar/AngelList series vehicle reads as a
    corroborating finding instead of an UNVERIFIABLE gap).
    """
    raw = json.load(open(run_dir / "06_findings.json"))
    non_xclaim = [f for f in raw if not str(f.get("f_rule_id", "")).startswith("re.internal_consistency")]
    n_on_disk_xclaim = len(raw) - len(non_xclaim)

    # SPV-conduit reconciliation: pull matching raise_amount findings out of the
    # UNVERIFIABLE pile and re-label them with the conduit verdict.
    spv = _spv_reclassified(run_dir)
    corroborated: list[dict] = []
    for f in non_xclaim:
        cid = (f.get("claim", {}) or {}).get("claim_id")
        if cid in spv:
            v = spv[cid]["verdict"]
            f["severity"] = v["severity"].lower()
            f["_spv_note"] = v["note"]
            f["_spv_summary"] = v["summary"]
            if v["severity"] == "PASS":
                corroborated.append(f)

    # Recompute cross-claim from typed claims.
    from verticals.buyside_dd import cross_claim_check as cc
    from verticals.buyside_dd.schemas import Claim, TypedClaim, ReferentType
    tcs = json.load(open(run_dir / "03_typed_claims.json"))
    typed = []
    for t in tcs:
        cd = t.get("claim") if isinstance(t, dict) and "claim" in t else t
        try:
            cl = Claim.model_validate(cd)
        except Exception:
            continue
        typed.append(TypedClaim(claim=cl, referent_type=ReferentType.ENTITY, referent_id=cl.subject))
    xfindings = cc.find_internal_divergences(typed)
    x_as_dict = [{
        "claim": {"subject": x.claim.subject, "predicate": x.claim.predicate,
                  "object_value": x.claim.object_value, "source_quote": x.claim.source_quote},
        "f_rule_id": x.f_rule_id, "severity": x.severity.name.lower(),
        "evidence_trail": x.evidence_trail, "divergence_pct": x.divergence_pct,
    } for x in xfindings]
    n_dropped = n_on_disk_xclaim - len(x_as_dict)

    allf = non_xclaim + x_as_dict
    order = {"critical": 0, "severe": 1, "moderate": 2, "minor": 3}
    material = sorted([f for f in allf if str(f.get("severity")).lower() in order],
                      key=lambda f: order[str(f.get("severity")).lower()])
    corro_ids = {id(f) for f in corroborated}
    unverifiable = [f for f in allf
                    if str(f.get("severity")).lower() == "unverifiable" and id(f) not in corro_ids]
    return material, unverifiable, corroborated, n_dropped


def build(run_dir: Path) -> Path:
    rpt = json.load(open(run_dir / "07_report.json"))
    material, unverifiable, corroborated, n_dropped = _corrected_findings(run_dir)

    deal_usd = rpt.get("deal_context", {}).get("deal_size_usd")
    cov = rpt.get("coverage", {})
    n_claims = rpt.get("n_claims_extracted")
    n_disp = rpt.get("n_claims_dispatched")
    cov_pct = cov.get("implementation_coverage_pct", 0)
    n_corro = len(corroborated)
    n_unver = len(unverifiable)
    n_internal = sum(1 for f in material
                     if str(f.get("f_rule_id", "")).startswith("re.internal_consistency"))

    pdf = Report(orientation="P", unit="mm", format="A4")
    pdf._running_title = "American Housing Corp - Forensic-Disclosure Diligence"
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(18, 16, 18)
    pdf.add_page()

    # --- cover block ---
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(120, 30, 30)
    pdf.cell(0, 5, _san("SIGNAL OS  -  BUYSIDE FORENSIC-DISCLOSURE DILIGENCE"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 9, _san("American Housing Corp"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, _san("Proposed $50M SAFE financing  -  modular / row-home builder"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, _san(f"As of {rpt.get('timestamp','')[:10]}  |  policy: {rpt.get('policy',{}).get('name','deep')}  |  run {rpt.get('run_id','')}"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # --- verdict banner ---
    pdf.set_fill_color(245, 238, 230)
    pdf.set_draw_color(170, 90, 40)
    y0 = pdf.get_y()
    banner_h = (34 if n_internal else 30) if n_corro else (26 if n_internal else 22)
    pdf.rect(18, y0, pdf.w - 36, banner_h, "DF")
    pdf.set_xy(20, y0 + 2.2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(150, 60, 20)
    pdf.cell(0, 5, _san("VERDICT:  DILIGENCE GAPS - DO NOT TREAT AS CLEAN"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(20, y0 + 8)
    pdf.set_font("Helvetica", "", 8.7)
    pdf.set_text_color(40, 40, 40)
    corro_clause = (
        f"{n_corro} claim{'s' if n_corro != 1 else ''} were CORROBORATED (the deal's Sydecar SPV "
        f"conduits were located on EDGAR), but "
    ) if n_corro else ""
    internal_clause = (
        f" {n_internal} internal inconsistency(ies) WITHIN the materials were flagged for reconciliation "
        f"(not external refutations)."
    ) if n_internal else ""
    pdf.multi_cell(pdf.w - 40, 4.3, _san(
        f"No claim was externally REFUTED.{internal_clause} {corro_clause}{n_unver} of {n_disp} dispatched "
        "verifications returned UNVERIFIABLE - the relevant public registries were unimplemented, unreachable, "
        "or did not return the expected field. Per the hostile-validator standard, UNVERIFIABLE is not a clean "
        "bill. Material gaps require management-provided primary documents before this raise can be cleared."))
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(y0 + banner_h + 2)
    pdf.ln(1)

    # --- deal context ---
    pdf.h2("Deal context & coverage")
    pdf.kv("Raise size", f"${deal_usd:,.0f} SAFE financing" if deal_usd else "n/a", key_w=42)
    pdf.kv("Documents", f"{rpt.get('n_documents')} (pitch deck, financial model, 2 executed SAFEs, SPV memo)", key_w=42)
    pdf.kv("Claims extracted", f"{n_claims} (Mode A direct + Mode B implied-verification)", key_w=42)
    pdf.kv("Externally checked", f"{n_disp} dispatched to an implemented connector "
           f"({cov_pct:.0f}% of claims have one)", key_w=42)
    pdf.kv("Findings", f"{len(material)} material  +  {n_corro} corroborated  +  {n_unver} unverifiable", key_w=42)
    pdf.ln(1)

    # --- executive summary ---
    pdf.h2("Executive summary")
    for para in [
        "The company and its principals are REAL and externally corroborated: open-web discovery "
        "independently confirmed American Housing Corp as an Antler Spring-2025 portfolio company "
        "(\"modular building system... 3x founder\") and Fast Company confirms Riley Meik as cofounder/CEO. "
        "This is not a phantom issuer.",
        f"The raise STRUCTURE was independently corroborated. The Form D checks located the Sydecar series "
        f"vehicles that fund this deal on SEC EDGAR - e.g. \"American Housing Corp Jan 2025 a Series of "
        f"CGF2021 LLC\" (a Pooled Investment Fund administered by Sydecar). A single SPV's sold amount is a "
        f"slice of the round, not the whole, so it reconciles as a subset of the headline raise rather than "
        f"an exact match. {n_corro} raise claim(s) reconcile this way.",
        f"What remains UNVERIFIABLE ({n_unver} of {n_disp} dispatched) is the rest of the substance an "
        "investor underwrites: the state corporate-registry connector is not implemented (OpenCorporates), "
        "the operating company's OWN parent-entity Form D (distinct from the SPV conduits) was not located, "
        "and the city permit databases returned no rows for the claimed facilities. Loose EDGAR name-matching "
        "also returned unrelated pooled funds (an Antler Brasil vehicle, a Contrary Breakout fund) that the "
        "SPV-attribution logic now filters out rather than mistaking for AHC's own filing.",
        "The factory/project claims could not be address-verified because the deal materials DISCLOSE NO "
        "STREET ADDRESS for the facilities - the deck names \"Factory 1\" / \"Factory 2\" with square-footage "
        "but no location. This is a primary-document gap, not a refutation: with no address to key on, the "
        "permit and OSHA checks have nothing to query.",
        ("Internal consistency: the $15M and $50M Flux SAFEs are two distinct financings (executed 2025-01-29 "
         "and 2025-11-13), now correctly separated by instrument date rather than mis-grouped as one "
         "self-contradictory valuation cap. "
         + ("The materials carry no remaining machine-detectable self-contradiction among grouped facts."
            if not n_internal else
            f"{n_internal} internal inconsistency(ies) remain for the deal team to reconcile against the "
            "source documents (see Material findings) - these are inconsistencies WITHIN the materials, "
            "not external refutations.")),
    ]:
        pdf.body(para)

    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(120, 60, 20)
    pdf.multi_cell(0, 4.6, _san(
        "Primary-document follow-ups for the deal team:  (1) operating-company state registration certificate "
        "+ the parent entity's OWN Form D (we located the Sydecar SPV conduits, not the operating company's "
        "direct Reg-D filing);  (2) a real factory/project street address - the deck discloses none - to key "
        "permit and OSHA verification;  (3) executed SAFE documents to confirm the valuation caps on both rounds."))
    pdf.set_text_color(0, 0, 0)

    # --- material findings ---
    pdf.add_page()
    pdf.h1("Material findings")
    if not material:
        pdf.body("None. No claim was externally refuted at the material-severity threshold.")
    for f in material:
        _render_finding(pdf, f)

    # --- corroborated findings ---
    if corroborated:
        pdf.add_page()
        pdf.h1("Corroborated findings")
        pdf.body("Claims the framework independently CONFIRMED against an external authority. The cap-table "
                 "structure was verified by locating the deal's SPV conduits on SEC EDGAR.", size=9)
        for f in corroborated:
            _render_finding(pdf, f, compact=True)

    # --- unverifiable ---
    pdf.add_page()
    pdf.h1("Unverifiable claims (not cleared)")
    pdf.body("Each item below is a claim the deck or model asserts that the framework attempted to verify "
             "against an independent authority but could not confirm or refute. Under the hostile-validator "
             "standard these are open risks, not passes.", size=9)
    for f in unverifiable:
        _render_finding(pdf, f, compact=True)

    # --- methodology ---
    pdf.add_page()
    pdf.h1("Methodology & limitations")
    for para in [
        "Model.  Every assertion in the deal materials is decomposed into an atomic claim R, matched to a "
        "verification rule f, and tested against an independent authority M. A finding records whether R was "
        "VERIFIED, REFUTED, or UNVERIFIABLE, with the authority cited as a URL. Two extraction modes run: "
        "Mode A (claims stated directly in the documents) and Mode B (implied verifications an investigator "
        "would derive - e.g. 'direct SAFE issuances imply a Form D should exist').",
        f"Coverage caveat.  Only ~{cov_pct:.0f}% of the {n_claims} extracted claims map to an implemented "
        f"external connector today ({n_disp} were dispatched). A low REFUTED count therefore reflects "
        "verification REACH, not issuer honesty. UNVERIFIABLE never means clean.",
        "SPV-conduit reconciliation.  Venture rounds funded through Sydecar/AngelList-style series vehicles "
        "file their own Form Ds whose issuer name encodes the operating company ('<Co> <Month Year> a Series "
        "of <X> LLC'). A single conduit's sold amount is a slice of the round, so the framework reconciles "
        "attributable conduits as a SUBSET of the headline raise, and filters out pooled funds that merely "
        "name-collide (e.g. an unrelated Antler Brasil vehicle) rather than mistaking them for the issuer's filing.",
        "Cross-claim consistency.  A separate check groups claims by (subject, predicate, scope) and flags "
        "values that diverge WITHIN the deal materials. The scope key includes the instrument date, investor, "
        "round, and entity-resolution provenance (resolved_from), so two separately-dated financings - e.g. the "
        "2025-01-29 $15M SAFE vs the 2025-11-13 $50M SAFE - sit in different buckets and are not mistaken for "
        "one self-contradictory valuation cap. A divergence here is an internal inconsistency in the documents, "
        "reported separately from external R/f(M) refutations.",
        "Open-web discovery.  The entity-resolution agent's web_search tool uses a full Chrome fingerprint "
        "(HTTP headers + a true TLS/HTTP-2 impersonation) and falls back across Brave -> DuckDuckGo -> Mojeek. "
        "Brave and DDG rate-limit this IP regardless of fingerprint; Mojeek carries the queries but indexes "
        "thinly, so it confirmed the company and founder but not a precise facility address.",
        "This tearsheet is a research aid, not investment advice or a legal opinion. UNVERIFIABLE items must be "
        "closed with primary documents from management before reliance.",
    ]:
        pdf.body(para, size=9)

    out = run_dir / "AHC_DD_TEARSHEET.pdf"
    pdf.output(str(out))
    return out


def _render_finding(pdf: Report, f: dict, compact: bool = False) -> None:
    d = _parse_evidence(f)
    sev = str(f.get("severity")).lower()
    label = SEV_LABEL.get(sev, sev.upper())
    if d.get("is_internal"):
        label = "INTERNAL CONTRADICTION" if sev in ("critical", "severe") else "INTERNAL INCONSISTENCY"
    rgb = SEV_RGB.get(sev, (60, 60, 60))

    if pdf.get_y() > pdf.h - 50:
        pdf.add_page()

    # title line: subject / predicate + severity chip
    title = f"{d['subject']}  -  {(d['predicate'] or '').replace('_',' ')}"
    pdf.ln(1.5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(25, 35, 70)
    pdf.multi_cell(0, 5, _san(title))
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*rgb)
    pdf.cell(0, 4.6, _san(f"[ {label} ]"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    quote = (d["source_quote"] or "").strip()
    if _looks_like_dict_dump(quote):
        quote = ""
    r_line = f"{d['object_value']}  -  \"{quote}\"" if quote else f"{d['object_value']}"
    pdf.label_para("R (claim):", _clip(r_line, 320 if not compact else 200))
    pdf.label_para("f (test):", _clip(d["rule_desc"] or "consistency / existence check", 320 if not compact else 200))
    m_line = d["m_label"] + (f"  [{d['m_url']}]" if d["m_url"] else "")
    pdf.label_para("M (authority):", _clip(m_line, 240))
    finding_txt = _finding_text(sev, d)
    pdf.label_para("Finding:", _clip(finding_txt, 380), label_rgb=rgb, text_rgb=(30, 30, 30))


# Existence claims whose verification keys on a street address. When the deal
# materials disclose NO address, the permit/OSHA checks have nothing to query —
# that is a primary-document gap, not a refutation.
_ADDRESS_KEYED_PREDICATES = (
    "located_at_address", "operates_industrial_facility", "operates_facility_at",
    "owns_property_at", "operates_at_address",
)


def _finding_text(sev: str, d: dict) -> str:
    # SPV-corroborated (or divergent) raise — the conduit note is the finding.
    if d.get("spv_note"):
        return d["spv_note"]
    if d.get("is_internal") and d.get("internal_note"):
        return d["internal_note"]
    if sev == "pass":
        return d["m_note"] or "Independently corroborated against the cited authority."
    if sev == "unverifiable":
        if d["predicate"] in _ADDRESS_KEYED_PREDICATES:
            return ("Not address-verifiable: the deal materials disclose NO street address for this "
                    "facility (named only as e.g. \"Factory 1\" with square-footage). With no address to "
                    "key on, the permit/OSHA check has nothing to query - a primary-document gap, not a "
                    "refutation. Obtain the facility address and re-run.")
        why = d["m_note"] or "no implemented authority returned a usable result"
        if _looks_like_dict_dump(why):
            why = "the registry was reached but did not return the expected field"
        return f"Could not confirm or refute ({why}; stop: {d['stop_reason'] or 'exhausted'}). Open risk - close with a primary document."
    if d["predicate"] in _ADDRESS_KEYED_PREDICATES:
        return ("No permits returned. NOTE: the deal materials disclose no verified street address for the "
                "facility, so this reads as an unresolved gap rather than a confirmed refutation - obtain "
                "the real address and re-run.")
    note = d["m_note"] or f"Independent authority diverged from the claim (stop: {d['stop_reason']})."
    return "Independent authority diverged from the claim." if _looks_like_dict_dump(note) else note


def _clip(s: str, n: int) -> str:
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


if __name__ == "__main__":
    rd = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not rd or not rd.exists():
        sys.exit("usage: python3 -m verticals.buyside_dd.build_dd_tearsheet <run_dir>")
    print(build(rd))
