"""Render an analyst-facing DD report PDF from a diligencer run.

Reads data/_local/{TICKER}.input.json + {TICKER}.scores.json (the R/f(M)
diligence output) and an optional narrative sidecar {TICKER}.report_meta.json,
and emits a PDF in the R -> f(M) -> Finding structure every material finding
must use (no detector internal names, citations as URLs/section refs).

Sidecar schema (all optional):
  {"company","subtitle","as_of","analyst","verdict","recommendation",
   "exec_summary": ["para", ...],
   "structural_findings": [{"title","R","source","method","authority","finding"}],
   "claim_notes": {"<claim_id>": "analyst override interpretation"},
   "appendix": ["para", ...]}

Run:  python3 -m verticals.public_co.build_analyst_report_pdf CAI
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fpdf import FPDF

HERE = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUTDIR = HERE / "reports"

# source-prefix -> (human label, authority root) for the f(M) lines.
SOURCE_AUTHORITY = {
    "clinical_trials": ("ClinicalTrials.gov v2 API", "https://clinicaltrials.gov"),
    "clinicaltrials_lookup": ("ClinicalTrials.gov v2 API", "https://clinicaltrials.gov"),
    "uspto_odp": ("USPTO Open Data Portal (patent assignee search)", "https://ped.uspto.gov"),
    "google_patents": ("Google Patents", "https://patents.google.com"),
    "openfda": ("openFDA Drugs@FDA", "https://www.accessdata.fda.gov/scripts/cder/daf/"),
    "edgar_fts": ("SEC EDGAR full-text search", "https://efts.sec.gov/LATEST/search-index"),
    "sec_filings": ("SEC EDGAR submissions API", "https://data.sec.gov/submissions/"),
    "going_concern_detector": ("SEC 10-K/10-Q going-concern disclosure", "https://www.sec.gov/cgi-bin/browse-edgar"),
    "revenue_concentration": ("SEC 10-K revenue-concentration parse", "https://www.sec.gov/cgi-bin/browse-edgar"),
    "auditor_change_tracker": ("SEC 8-K Item 4.01 (auditor change)", "https://www.sec.gov/cgi-bin/browse-edgar"),
    "usaspending": ("USAspending.gov federal awards", "https://www.usaspending.gov"),
    "pentagon_jbook": ("Pentagon J-Book program funding (P-40/R-2)", "https://comptroller.defense.gov"),
    "doe_budget": ("DOE Congressional Budget Justification", "https://www.energy.gov/cfo/listings/budget-justification"),
    "epa_frs": ("EPA Facility Registry Service", "https://www.epa.gov/frs"),
}

SEV_LABEL = {
    "PASS": "VERIFIED",
    "MODERATE_UNDERDELIVERY": "PARTIAL / INCONSISTENT",
    "SEVERE_UNDERDELIVERY": "REFUTED (severe)",
    "RED_FLAG_NEGATIVE": "REFUTED (contradiction)",
    "UNVERIFIABLE": "UNVERIFIABLE",
}
SEV_RGB = {
    "PASS": (22, 110, 50),
    "MODERATE_UNDERDELIVERY": (176, 124, 16),
    "SEVERE_UNDERDELIVERY": (170, 50, 20),
    "RED_FLAG_NEGATIVE": (150, 20, 20),
    "UNVERIFIABLE": (90, 90, 90),
}

_REPL = {
    "—": "-", "–": "-", "‒": "-", "−": "-",
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "…": "...", "→": "->", "←": "<-", "≥": ">=",
    "≤": "<=", "•": "-", " ": " ", "×": "x",
    "≈": "~", " ": " ", " ": " ", "·": "-",
    "′": "'", "″": '"', "‑": "-", "﻿": "",
}


def _san(s) -> str:
    if s is None:
        return ""
    s = str(s)
    for k, v in _REPL.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


import re as _re

# Framework-internal phrasing that must not appear in an analyst-facing report.
_SCRUB = [
    (_re.compile(r"\s*-+>\s*(PASS|SEVERE(_UNDERDELIVERY)?|MODERATE(_UNDERDELIVERY)?|RED_FLAG_NEGATIVE|UNVERIFIABLE)\b\.?"), ""),
    (_re.compile(r"\bPer the honesty-alpha framework,?\s*", _re.I), ""),
    (_re.compile(r"\bhonesty-alpha framework\b", _re.I), "disclosure-honesty standard"),
    (_re.compile(r"\bthe framework rewards honesty, not business quality\b", _re.I),
     "the test measures disclosure honesty, not business quality"),
    (_re.compile(r"\bPer Heuristic\s*\d+,?\s*", _re.I), ""),
    (_re.compile(r"\bthe Nikola pattern\b", _re.I), "the inflated-patent-claim pattern"),
    (_re.compile(r"\b(to preserve|for) blinding[^.,;]*", _re.I), ""),
    (_re.compile(r"\s*\(post-cutoff source\)"), ""),
    # internal detector / m-source module names -> readable phrases
    # (full module.method(...) calls MUST be matched before the bare-token rules below)
    (_re.compile(r"going_concern_detector\.query_\w+\([^)]*\)", _re.I), "an SEC going-concern parse"),
    (_re.compile(r"auditor_change_tracker\.query_\w+\([^)]*\)", _re.I), "an SEC 8-K Item 4.01 auditor-change scan"),
    (_re.compile(r"going_concern_detector\.query_\w+", _re.I), "an SEC going-concern parse"),
    (_re.compile(r"auditor_change_tracker\.query_\w+", _re.I), "an SEC 8-K Item 4.01 auditor-change scan"),
    (_re.compile(r"\bgoing_concern detector\b", _re.I), "the going-concern screen"),
    (_re.compile(r"\bgoing_concern_detector\b"), "the going-concern screen"),
    (_re.compile(r"\bauditor_change_tracker\b"), "the SEC 8-K Item 4.01 auditor-change scan"),
    (_re.compile(r"\bDetector signal\b", _re.I), "Automated screen:"),
    (_re.compile(r"\bStructural detector\b", _re.I), "Structural read of the prospectus"),
    # generic module.query_xxx(...) calls left over from any other M-source
    (_re.compile(r"\b[a-z][a-z0-9_]*\.query_[a-z0-9_]+\([^)]*\)", _re.I), "an independent registry query"),
    (_re.compile(r"\b[a-z][a-z0-9_]*\.query_[a-z0-9_]+", _re.I), "an independent registry query"),
    (_re.compile(r"\bclinical_trials\b", _re.I), "ClinicalTrials.gov"),
    (_re.compile(r"\bedgar_fts\b", _re.I), "SEC EDGAR full-text search"),
    (_re.compile(r"\buspto_odp\b", _re.I), "USPTO Open Data Portal"),
    (_re.compile(r"\bopenfda\b", _re.I), "openFDA"),
    (_re.compile(r"\bcompetitor_trial_omission\b", _re.I), "competitor-trial-omission check"),
    (_re.compile(r"\bclinical_trial_referral_quality\b", _re.I), "referral action-vs-administration check"),
    (_re.compile(r"\bmulti_venue_disclosure_consistency\b", _re.I), "cross-venue consistency check"),
    (_re.compile(r"\bdual_class_voting_concentration\b", _re.I), "voting-concentration read"),
    (_re.compile(r"\blockup_expiration_calendar\b", _re.I), "lock-up / overhang read"),
    (_re.compile(r"\brelated_party_transaction_velocity\b", _re.I), "related-party transaction read"),
    # any residual snake_case token left in parentheses (internal names)
    (_re.compile(r"\s*\((?:[a-z][a-z0-9]*)(?:_[a-z0-9]+)+\)"), ""),
    # UPPER_SNAKE enum/signal tokens -> readable lowercase words
    (_re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b"),
     lambda m: m.group(0).replace("_", " ").lower()),
    (_re.compile(r"\s{2,}"), " "),
]


def _scrub(s: str) -> str:
    s = str(s or "")
    for pat, rep in _SCRUB:
        s = pat.sub(rep, s)
    return s.strip()


def _src_label(source: str) -> tuple[str, str]:
    prefix = (source or "").split(".")[0]
    return SOURCE_AUTHORITY.get(prefix, (source or "internal verification", ""))


class Report(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "", 7)
        self.set_text_color(140, 140, 140)
        self.cell(0, 6, _san(self._running_title), align="R")
        self.ln(7)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(140, 140, 140)
        self.cell(0, 6, f"Signal OS forensic-disclosure diligence  -  p.{self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)

    def multi_cell(self, w, h=None, txt="", *a, **k):
        k.setdefault("new_x", "LMARGIN")
        k.setdefault("new_y", "NEXT")
        return super().multi_cell(w, h, txt, *a, **k)

    # -- building blocks ----------------------------------------------------
    def h1(self, txt):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 7, _san(txt))
        self.ln(1)
        self.set_text_color(0, 0, 0)

    def h2(self, txt):
        self.ln(2)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 11.5)
        self.set_text_color(25, 35, 70)
        self.multi_cell(0, 6, _san(txt))
        self.set_draw_color(200, 205, 215)
        self.line(self.l_margin, self.get_y() + 0.5, self.w - self.r_margin, self.get_y() + 0.5)
        self.ln(2.5)
        self.set_text_color(0, 0, 0)

    def body(self, txt, size=9.5, gap=4.7):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", size)
        self.multi_cell(0, gap, _san(txt))
        self.ln(1)

    def kv(self, key, val, key_w=26):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 9)
        self.cell(key_w, 5, _san(key))
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5, _san(val))

    def label_para(self, label, text, label_rgb=(40, 40, 40), text_rgb=(0, 0, 0)):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*label_rgb)
        self.write(4.8, _san(label) + " ")
        self.set_text_color(*text_rgb)
        self.set_font("Helvetica", "", 9)
        self.write(4.8, _san(text))
        self.ln(5.4)


def _corpus_coverage_stamp(ticker: str, as_of: str) -> dict:
    """Read the on-disk filing corpus and assert it is not stale for a live as_of.

    Returns {newest_periodic, newest_periodic_form, stale, msg}. Prints a loud
    stderr WARNING when a present-day report is being built on a corpus whose
    newest periodic filing is far in the past -- the Caris-class failure where a
    report dated 'today' was built entirely on the IPO prospectus.
    """
    out = {"newest_periodic": None, "newest_periodic_form": None, "stale": False, "msg": ""}
    try:
        from . import live_dd
        out_dir = LOCAL.parent / ticker.lower()
        cov = live_dd.corpus_coverage(out_dir)
        if not cov:
            return out
        out["newest_periodic"] = cov.get("newest_periodic")
        out["newest_periodic_form"] = cov.get("newest_periodic_form")
        if as_of:
            fresh = live_dd.freshness_check(out_dir, as_of)
            out["stale"] = fresh["stale"]
            if fresh["stale"]:
                out["msg"] = fresh["advice"]
                print(f"\n  !! CORPUS STALENESS WARNING for {ticker}: {fresh['advice']}\n"
                      f"     The report is dated {as_of} but the filing corpus does not "
                      f"reach it. Run: python3 -m verticals.public_co.live_dd {ticker}\n",
                      file=sys.stderr)
    except Exception as e:
        print(f"  (corpus coverage check skipped: {e})", file=sys.stderr)
    return out


def _gather(ticker: str) -> dict:
    inp = json.loads((LOCAL / f"{ticker}.input.json").read_text())
    scores = json.loads((LOCAL / f"{ticker}.scores.json").read_text())
    meta_p = LOCAL / f"{ticker}.report_meta.json"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    claims = {c.get("claim_id"): c for c in inp.get("claims", [])}
    return {"input": inp, "scores": scores.get("scores", []), "meta": meta, "claims": claims}


def build(ticker: str) -> Path:
    g = _gather(ticker)
    inp, scores, meta, claims = g["input"], g["scores"], g["meta"], g["claims"]
    company = meta.get("company", inp.get("ticker", ticker))
    filing = inp.get("filing", "")
    as_of = meta.get("as_of", inp.get("cutoff", ""))
    coverage = _corpus_coverage_stamp(ticker, as_of)

    counts = {k: 0 for k in SEV_LABEL}
    for s in scores:
        counts[s.get("severity")] = counts.get(s.get("severity"), 0) + 1

    pdf = Report(format="Letter")
    pdf._running_title = f"{company} ({ticker}) - forensic disclosure diligence"
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(18, 16, 18)
    pdf.add_page()

    # ---- cover block ----
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "SIGNAL OS  -  FORENSIC DISCLOSURE DILIGENCE", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_text_color(0, 0, 0)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 19)
    pdf.multi_cell(0, 8, _san(company))
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(70, 70, 70)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, _san(meta.get("subtitle", f"Nasdaq: {ticker}  -  IPO prospectus diligence")))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    pdf.kv("As of", as_of)
    if coverage.get("newest_periodic"):
        pdf.kv("Corpus through", f"{coverage['newest_periodic']} ({coverage['newest_periodic_form']} -- latest periodic filing read)")
    pdf.kv("Primary filing", f"{filing} (final priced 424B4)")
    if inp.get("cutoff"):
        pdf.kv("CIK", "0002019410" if ticker == "CAI" else "")
    if meta.get("analyst"):
        pdf.kv("Prepared by", meta.get("analyst"))
    pdf.ln(2)

    # ---- verdict banner ----
    verdict = meta.get("verdict")
    if verdict:
        pdf.set_fill_color(244, 246, 250)
        y0 = pdf.get_y()
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.multi_cell(0, 6, _san(f"Verdict: {verdict}"), fill=True)
        if meta.get("recommendation"):
            pdf.set_font("Helvetica", "", 9.5)
            pdf.multi_cell(0, 5, _san(meta["recommendation"]), fill=True)
        pdf.ln(2)

    # ---- methodology note ----
    pdf.h2("Methodology")
    pdf.body(
        "Each material finding is structured as Claim (R) -> Independent test f(M) -> Finding. "
        "R is a claim taken from the issuer's own filing, with section citation. f(M) is the "
        "specific external test run against an authoritative third-party source M (a public "
        "registry, regulator database, or counterparty's own SEC filings) -- never the issuer's "
        "own marketing. The Finding states whether the independent source corroborates, partially "
        "corroborates, contradicts, or cannot reach the claim, with the evidence shown. The "
        "discipline isolates disclosure honesty: it measures the gap between what the issuer "
        "asserts and what an independent record confirms, rather than re-rating the business."
    )

    # ---- summary table ----
    pdf.h2("Findings summary")
    order = ["RED_FLAG_NEGATIVE", "SEVERE_UNDERDELIVERY", "MODERATE_UNDERDELIVERY", "PASS", "UNVERIFIABLE"]
    pdf.set_font("Helvetica", "", 9.5)
    for sev in order:
        n = counts.get(sev, 0)
        if not n:
            continue
        pdf.set_text_color(*SEV_RGB[sev])
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(52, 5.4, _san(SEV_LABEL[sev]))
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.cell(10, 5.4, str(n))
        pdf.multi_cell(0, 5.4, _san(_SEV_GLOSS[sev]))
    pdf.ln(1)
    feats = inp.get("issuer_features") or []
    if feats:
        pdf.body("Issuer characteristics declared from the filing that drive the verification "
                 "battery: " + ", ".join(_san(f).replace("_", " ") for f in feats) + ".", size=8.5, gap=4.3)

    # ---- exec summary ----
    if meta.get("exec_summary"):
        pdf.h2("Executive summary")
        for para in meta["exec_summary"]:
            pdf.body(para)

    # ---- fundamentals timeline (post-IPO actuals + guidance) ----
    _fundamentals_section(pdf, ticker)

    # ---- structural findings (read straight from the prospectus) ----
    if meta.get("structural_findings"):
        pdf.h2("Structural findings (read from the prospectus)")
        for f in meta["structural_findings"]:
            _finding_block(pdf, f.get("title", ""), f.get("R", ""), f.get("source", ""),
                           f.get("method", ""), f.get("authority", ""),
                           f.get("finding_label", ""), f.get("finding", ""),
                           f.get("finding_rgb"))

    # ---- claim-by-claim material findings ----
    pdf.h2("Material findings (claim verification)")
    sev_rank = {s: i for i, s in enumerate(order)}
    scores_sorted = sorted(scores, key=lambda s: sev_rank.get(s.get("severity"), 99))
    for s in scores_sorted:
        cid = s.get("claim_id")
        claim = claims.get(cid, {})
        sev = s.get("severity")
        # R
        R = s.get("claim_text") or claim.get("claim_text", "")
        quote = claim.get("source_quote", "")
        cat = (claim.get("category") or "").replace("_", " ")
        title = f"{cid}. {cat.title()}" if cat else str(cid)
        # f and M
        method = s.get("M_check") or ""
        queries = claim.get("queries") or []
        srcs = []
        for q in queries:
            src = q.get("source") if isinstance(q, dict) else str(q).split("(")[0]
            if src:
                srcs.append(src)
        authority = ""
        if srcs:
            labels = []
            for src in dict.fromkeys(srcs):
                lab, url = _src_label(src)
                labels.append(lab + (f" ({url})" if url else ""))
            authority = "; ".join(labels)
        _finding_block(
            pdf, title, R,
            source=claim.get("source_section") or "Prospectus (424B4)",
            method=method or "Independent registry lookup",
            authority=authority,
            finding_label=SEV_LABEL.get(sev, sev),
            finding=meta.get("claim_notes", {}).get(cid) or s.get("interpretation", ""),
            finding_rgb=SEV_RGB.get(sev),
            mvalue=s.get("M_value", ""),
            quote=quote,
            trail=s.get("resolution_trail"),
        )

    if meta.get("appendix"):
        pdf.h2("Appendix")
        for para in meta["appendix"]:
            pdf.body(para, size=8.7, gap=4.3)

    OUTDIR.mkdir(exist_ok=True)
    out = OUTDIR / f"{company.split(',')[0].replace(' ', '_')}_DD_Report_{(as_of or '').replace('-', '_')}.pdf"
    pdf.output(str(out))
    return out


_SEV_GLOSS = {
    "RED_FLAG_NEGATIVE": "independent source contradicts a material claim",
    "SEVERE_UNDERDELIVERY": "source that should corroborate shows little/nothing",
    "MODERATE_UNDERDELIVERY": "partial corroboration / smaller than implied",
    "PASS": "independent source corroborates the claim",
    "UNVERIFIABLE": "no independent registry reaches this claim",
}


_TRAIL_RGB = {
    "raised": (150, 20, 20),
    "worsened": (150, 20, 20),
    "unchanged": (176, 124, 16),
    "resolved": (22, 110, 50),
}


def _fmt_m(v) -> str:
    return f"{v/1e6:,.0f}" if isinstance(v, (int, float)) else "--"


def _fmt_pct(v) -> str:
    return f"{v:+.0f}%" if isinstance(v, (int, float)) else "--"


def _fundamentals_section(pdf, ticker: str) -> None:
    """Render the XBRL-derived quarterly fundamentals table + forward guidance.

    Sourced from data/<ticker>/fundamentals_timeline.json (built by
    fundamentals_timeline.build_timeline). Silently no-ops if absent so the
    report still builds for tickers without a timeline.
    """
    p = LOCAL.parent / ticker.lower() / "fundamentals_timeline.json"
    if not p.exists():
        return
    try:
        tl = json.loads(p.read_text())
    except Exception:
        return
    quarters = tl.get("quarters") or []
    if not quarters:
        return
    pdf.h2("Fundamentals timeline (post-IPO actuals)")
    pdf.body(
        "Quarter-by-quarter actuals from the issuer's SEC XBRL financial data "
        "(authoritative structured filings, not marketing). Revenue YoY and "
        "operating margin are computed; Q4 figures marked (d) are derived as the "
        "full-year filing minus the first three quarters. This series separates a "
        "fundamental-deterioration story from a float/dilution/valuation one.",
        size=8.7, gap=4.3,
    )
    cols = [("Quarter", 22, "L"), ("Rev $M", 24, "R"), ("YoY", 20, "R"),
            ("Op mgn", 22, "R"), ("Net $M", 24, "R"), ("Cash $M", 24, "R")]
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 8.3)
    pdf.set_fill_color(238, 240, 245)
    for name, w, _al in cols:
        pdf.cell(w, 5.2, _san(name), align="L", fill=True)
    pdf.ln(5.2)
    pdf.set_font("Helvetica", "", 8.3)
    for q in quarters:
        qlabel = q["quarter"]
        if q.get("derived_q4"):
            qlabel += " (d)"
        op_neg = isinstance(q.get("operating_margin_pct"), (int, float)) and q["operating_margin_pct"] < 0
        row = [
            (qlabel, 22, "L", None),
            (_fmt_m(q.get("revenue")), 24, "R", None),
            (_fmt_pct(q.get("revenue_yoy_pct")), 20, "R", None),
            (_fmt_pct(q.get("operating_margin_pct")), 22, "R",
             (170, 50, 20) if op_neg else (22, 110, 50)),
            (_fmt_m(q.get("net_income")), 24, "R", None),
            (_fmt_m(q.get("cash_end")), 24, "R", None),
        ]
        pdf.set_x(pdf.l_margin)
        for txt, w, al, rgb in row:
            pdf.set_text_color(*(rgb or (0, 0, 0)))
            pdf.cell(w, 4.8, _san(txt), align="L")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4.8)
    pdf.ln(1.0)
    if any(q.get("derived_q4") for q in quarters):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "I", 7.6)
        pdf.set_text_color(110, 110, 110)
        pdf.multi_cell(0, 3.8, _san(
            "(d) Q4 is derived (full-year filing minus the first three quarters) and can carry "
            "year-end true-ups -- revenue recognition, reserve releases, annual adjustments -- so "
            "an outsized derived Q4 should be read as lumpy rather than as a sustainable run-rate; "
            "anchor the trajectory to the surrounding directly-filed quarters."))
        pdf.set_text_color(0, 0, 0)
    pdf.ln(1.0)

    guidance = tl.get("guidance") or []
    if guidance:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 5, _san("Forward revenue guidance (from earnings 8-K press releases):"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8.5)
        for gd in guidance:
            act = gd.get("action", "issued")
            argb = {"raised": (22, 110, 50), "lowered": (170, 50, 20),
                    "reaffirmed": (40, 40, 40), "issued": (40, 40, 40)}.get(act, (40, 40, 40))
            lo, hi = gd.get("low"), gd.get("high")
            if isinstance(lo, (int, float)):
                rng = (f"${lo/1e9:.2f}B - ${hi/1e9:.2f}B" if lo >= 1e9
                       else f"${lo/1e6:,.0f}M - ${hi/1e6:,.0f}M")
            else:
                rng = "--"
            period = gd.get("period") or f"FY{gd.get('fiscal_year','')}"
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_text_color(*argb)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.cell(46, 4.6, _san(f"{gd.get('filing_date','')}  {act.upper()}"))
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.cell(0, 4.6, _san(f"{period} revenue {rng}"),
                     new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)


def _finding_block(pdf, title, R, source, method, authority, finding_label,
                   finding, finding_rgb=None, mvalue="", quote="", trail=None):
    if pdf.get_y() > pdf.h - 55:
        pdf.add_page()
    pdf.ln(1.5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 20, 20)
    pdf.multi_cell(0, 5.4, _san(title))
    pdf.set_text_color(0, 0, 0)
    pdf.label_para("Claim (R):", R)
    if quote:
        pdf.set_font("Helvetica", "I", 8.3)
        pdf.set_text_color(95, 95, 95)
        pdf.multi_cell(0, 4.2, _san('   "' + quote.strip().strip('"') + '"'))
        pdf.set_text_color(0, 0, 0)
        pdf.ln(0.4)
    if source:
        pdf.label_para("Source:", source)
    pdf.label_para("Method f:", _scrub(method))
    if authority:
        pdf.label_para("Authority M:", authority)
    rgb = finding_rgb or (40, 40, 40)
    pdf.label_para(f"Finding -- {finding_label}:", _scrub(finding or ""), label_rgb=rgb)
    if trail:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 8.3)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 4.4, _san("   Resolution trail (prospectus -> current):"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        for step in trail:
            st = (step.get("status") or "").lower()
            srgb = _TRAIL_RGB.get(st, (90, 90, 90))
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*srgb)
            head = f"{step.get('date','')}  {st.upper()}  ({_scrub(step.get('filing',''))})"
            pdf.cell(0, 4.2, _san(head), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(70, 70, 70)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_x(pdf.l_margin + 8)
            pdf.multi_cell(0, 4.0, _san(_scrub(step.get("note", ""))))
        pdf.set_text_color(0, 0, 0)
        pdf.ln(0.6)
    if mvalue:
        mv = mvalue if isinstance(mvalue, str) else json.dumps(mvalue, default=str)
        mv = _scrub(mv)
        if len(mv) > 850:
            cut = mv.rfind(" ", 0, 850)
            mv = mv[:cut if cut > 600 else 850].rstrip(" ,;:-") + " ..."
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(0, 4.0, _san("   Evidence: " + mv))
        pdf.set_text_color(0, 0, 0)
    pdf.ln(0.8)


def main():
    ticker = (sys.argv[1] if len(sys.argv) > 1 else "CAI").upper()
    out = build(ticker)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
