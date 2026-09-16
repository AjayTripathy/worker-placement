"""refresh_current_state — re-verify CURRENT assessed valuation / coverage for the DD reports that flagged
it UNVERIFIABLE because EMMA 403-rate-limited during the original av_concentration pass, and patch each
report with a verified addendum.

The 403s were a concurrency artifact (10+ agents hammering EMMA at once), not EMMA being unbeatable. Run
SERIALLY + throttled, the issuer's latest 15c2-12 ANNUAL REPORT carries the current-FY AV / coverage. All
the fetching + parsing now lives in the shared `cdd_financials` module (so the DETECTORS use it too —
av_concentration / water_revenue_underwrite — not just this tool). This file is the orchestrator: pick the
affected reports, call cdd_financials, fall back to the LLM OS-template extractor only when the
deterministic CDD parse misses, and append a "Current-State Verification" addendum.

Output: outputs/CURRENT_STATE_REFRESH.json + in-place DD_REPORT.md addenda.
NEVER fabricates: no fresh/extractable annual report -> STILL-UNVERIFIABLE and the report keeps its
honest caveat (UNVERIFIABLE != clean).
    refresh_current_state.py [CUSIP...]   # default: auto-detect affected reports; live serial fetch
    refresh_current_state.py --local      # re-parse already-downloaded PDFs, no EMMA
    refresh_current_state.py --fresh       # ignore cached VERIFIED, re-pull all
"""
import json, re, sys, time, datetime
from pathlib import Path

import emma_scraper as E
import av_concentration as AV
import cdd_financials as CF

HERE = Path(__file__).resolve().parent
REPORTS = HERE / "outputs" / "diligence_reports"
OUT = HERE / "outputs" / "CURRENT_STATE_REFRESH.json"
THROTTLE = CF.THROTTLE
TODAY = datetime.date(2026, 6, 20)

_MASTER = None


def _issuer_for(cusip):
    """Issuer name for a CUSIP — to disambiguate multi-district CDDs (Modesto Elementary vs High)."""
    global _MASTER
    if _MASTER is None:
        try:
            _MASTER = {r["cusip"]: r for r in json.load(open(HERE / "outputs" / "DILIGENCE_MASTER.json"))}
        except Exception:
            _MASTER = {}
    iss = (_MASTER.get(cusip) or {}).get("issuer")
    if iss:
        return iss
    rp = REPORTS / cusip / "DD_REPORT.md"          # fall back to the DD report's bold issuer header
    if rp.exists():
        m = re.search(r"\*\*([^*]+?(?:School District|College District|City|County)[^*]*)\*\*",
                      rp.read_text())
        if m:
            return m.group(1)
    return None


def _llm_av_fallback(rec, pdf):
    """When the deterministic CDD parse misses AV and DSCR, try the OS-template extractor (+ LLM) on the
    annual PDF. Sets av_current/av_current_fy on success."""
    try:
        ex = AV.extract_concentration(pdf, source=rec.get("annual_doc"), allow_llm=True)
        if ex.get("av_total"):
            rec["av_current"] = ex["av_total"]
            rec["av_current_fy"] = ex.get("as_of_year")
            rec["av_top1_share"] = ex.get("av_top1_share")
            rec["overlapping_debt_to_av"] = ex.get("overlapping_debt_to_av")
            rec["av_source"] = "os_template_fallback"
    except Exception as ex:
        rec["fallback_error"] = str(ex)[:120]


def refresh_one(s, cusip):
    raw = REPORTS / cusip / "raw"
    rec = CF.current_state(cusip, session=s, issuer=_issuer_for(cusip), raw_dir=raw, throttle=THROTTLE)
    rec["refreshed"] = TODAY.isoformat()
    if rec.get("status") != "STILL-UNVERIFIABLE" and not rec.get("av_current") \
            and rec.get("dscr_current") is None:
        pdf = raw / "cdd_annual_latest.pdf"
        if pdf.exists():
            _llm_av_fallback(rec, pdf)
            rec["status"] = "VERIFIED" if rec.get("av_current") else "PARTIAL"
    return rec


def reparse_local(cusip, prior=None):
    """Rebuild the record from the already-downloaded cdd_annual_latest.pdf WITHOUT hitting EMMA — re-run
    the parser after a fix without re-scraping. Carries doc metadata forward from the prior record."""
    raw = REPORTS / cusip / "raw"
    pdf = raw / "cdd_annual_latest.pdf"
    rec = {"cusip": cusip, "refreshed": TODAY.isoformat(), "reparsed_local": True}
    for k in ("annual_doc", "annual_posted", "audited_doc", "audited_posted", "n_cd_docs"):
        if prior and prior.get(k) is not None:
            rec[k] = prior[k]
    if not pdf.exists():
        rec.update(status="STILL-UNVERIFIABLE", reason="no cached annual pdf (run live first)")
        return rec
    ann_text = CF._text(pdf)
    parsed = CF.current_state(cusip, issuer=_issuer_for(cusip), ann_text=ann_text)
    parsed.pop("status", None)
    rec.update(parsed)
    if not rec.get("av_current") and rec.get("dscr_current") is None:
        _llm_av_fallback(rec, pdf)
    rec["status"] = "VERIFIED" if (rec.get("av_current") or rec.get("dscr_current") is not None) else "PARTIAL"
    return rec


ADDENDUM_MARK = "<!-- current-state-refresh -->"


def build_addendum(rec):
    if rec["status"] in ("STILL-UNVERIFIABLE", "PARTIAL", "ERROR") or \
            (not rec.get("av_current") and rec.get("dscr_current") is None):
        why = rec.get("reason")
        if not why:
            doc = rec.get("annual_doc")
            why = (f"the latest annual report (_{doc}_) is on file but its AV/coverage table is not "
                   f"machine-extractable (image/atypical layout)") if doc else \
                  "no current annual report with an extractable AV/coverage table was retrievable"
        body = (f"As of {rec['refreshed']}, a serial throttled EMMA continuing-disclosure pull was run "
                f"({why}). **Current AV/coverage remains UNVERIFIABLE — honestly flagged, not clean.**")
    elif rec.get("av_current"):
        av = rec.get("av_current")
        avs = f"${av:,.0f}" if av else "n/a"
        chg = rec.get("av_change_pct")
        chg_s = f" ({chg:+.1f}% YoY)" if chg is not None else ""
        delq = rec.get("delinquency_pct")
        delq_s = f"; secured-tax delinquency **{delq:.2f}%**" if delq is not None else ""
        afy = rec.get("audit_fy")
        afy_s = f"; audited FY{afy} on file" if afy else ""
        ser = rec.get("av_series") or []
        trend = ""
        if len(ser) >= 2:
            trend = " — AV trend " + " → ".join(f"{r[0]} ${r[1]/1e9:.2f}B" for r in ser[-4:])
        amb = " _(multi-district CDD — AV bound to the issuer's own sub-table; confirm territory.)_" \
            if rec.get("av_ambiguous") else ""
        body = (f"Refreshed {rec['refreshed']} via a SERIAL, throttled EMMA continuing-disclosure pull "
                f"(the original UNVERIFIABLE flag was an EMMA 403 rate-limit from concurrent scraping, not "
                f"a real disclosure gap). Latest issuer annual report: _{rec.get('annual_doc','')}_. "
                f"**Current total assessed valuation (levy base): {avs} for FY{rec.get('av_current_fy')}"
                f"{chg_s}**{delq_s}{afy_s}.{trend} For an unlimited ad-valorem GO the AV base + the "
                f"delinquency cushion ARE the 'coverage' — there is no DSCR; the levy rate floats to hold "
                f"debt service constant.{amb} **This resolves the prior 'current AV/coverage UNVERIFIABLE' caveat.**")
    else:   # revenue / water bond — DSCR is the coverage metric
        d = rec.get("dscr_current")
        ser = rec.get("dscr_series") or []
        trend = (" (series " + " → ".join(f"{v:.2f}x" for v in ser[-5:]) + ")") if len(ser) >= 2 else ""
        warn = ""
        if d is not None and d < 1.0:
            unaud = " (UNAUDITED)" if rec.get("dscr_unaudited") else ""
            cause = f" Stated cause: {rec['dscr_note']}" if rec.get("dscr_note") else \
                    " Investigate the latest-year driver before trade."
            warn = (f" — **NOTE: latest reported coverage{unaud} is BELOW 1.0x"
                    + (" (negative net revenues)" if d < 0 else "") + "; treat as a current-state finding, "
                    f"not a clean confirmation.**{cause}")
        body = (f"Refreshed {rec['refreshed']} via a SERIAL, throttled EMMA continuing-disclosure pull "
                f"(original UNVERIFIABLE flag = EMMA 403 rate-limit, not a real gap). Latest issuer annual "
                f"report: _{rec.get('annual_doc','')}_. This is a REVENUE/enterprise bond (no ad-valorem "
                f"AV base), so the current-coverage metric is the **debt-service-coverage ratio = "
                f"{d:.2f}x**{trend} for the latest reported fiscal year.{warn} This resolves the prior "
                f"'current DSCR/coverage UNVERIFIABLE' caveat with the verified datum.")
    return (f"\n\n{ADDENDUM_MARK}\n### Current-State Verification (AV / coverage refresh — {rec['refreshed']})\n\n"
            f"{body}\n")


def patch_report(cusip, rec):
    rp = REPORTS / cusip / "DD_REPORT.md"
    if not rp.exists():
        return False
    txt = rp.read_text()
    txt = re.split(r"\n*" + re.escape(ADDENDUM_MARK), txt)[0].rstrip()   # idempotent re-runs
    txt += build_addendum(rec)
    rp.write_text(txt)
    return True


def affected_cusips():
    """DD reports whose current AV / coverage / DSCR is flagged UNVERIFIABLE."""
    hits = []
    for d in sorted(REPORTS.iterdir()):
        rp = d / "DD_REPORT.md"
        if not rp.exists():
            continue
        for line in rp.read_text().splitlines():
            if "unverifiable" in line.lower() and re.search(r"(?i)\bAV\b|coverage|DSCR|assessed val", line):
                hits.append(d.name)
                break
    return hits


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    cusips = args or affected_cusips()
    local = "--local" in sys.argv
    print(f"refresh_current_state: {len(cusips)} CUSIP(s){' [LOCAL re-parse]' if local else ''}",
          file=sys.stderr)
    prior = {r["cusip"]: r for r in json.load(open(OUT))} if OUT.exists() else {}
    s = None if local else E._session()
    results = dict(prior)
    for i, cu in enumerate(cusips, 1):
        if not local and cu in prior and prior[cu].get("status") == "VERIFIED" and "--fresh" not in sys.argv:
            print(f"[{i}/{len(cusips)}] {cu} cached VERIFIED — skip", file=sys.stderr)
            continue
        try:
            rec = reparse_local(cu, prior.get(cu)) if local else refresh_one(s, cu)
        except Exception as ex:
            rec = {"cusip": cu, "status": "ERROR", "reason": str(ex)[:160], "refreshed": TODAY.isoformat()}
        rec["report_patched"] = patch_report(cu, rec)
        results[cu] = rec
        av = rec.get("av_current")
        print(f"[{i}/{len(cusips)}] {cu} {rec['status']:18} "
              f"AV={'$%.2fB' % (av/1e9) if av else '—':9} FY{rec.get('av_current_fy')} "
              f"dscr={rec.get('dscr_current')} delq={rec.get('delinquency_pct')}", file=sys.stderr)
        json.dump(list(results.values()), open(OUT, "w"), indent=1, default=str)
        if not local:
            time.sleep(THROTTLE)
    json.dump(list(results.values()), open(OUT, "w"), indent=1, default=str)
    ok = sum(1 for r in results.values() if r.get("status") == "VERIFIED")
    print(f"DONE: {ok}/{len(results)} VERIFIED -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
