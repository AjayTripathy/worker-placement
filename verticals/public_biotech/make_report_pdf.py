"""Render the four-trial catalyst-honesty backtest into a single PDF.

Post-hoc analysis document (NOT a blind prediction): pulls each case's committed
prediction.json, joins the now-unsealed outcomes, and lays out the R/f(M)/Finding
decisive flags plus the matched-pair and out-of-sample narrative.
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

HERE = Path(__file__).parent
DATA = HERE / "data"
SEALED = json.loads((HERE / "_sealed_outcomes.json").read_text())["outcomes"]

# Display order: in-sample matched pair, then the two held-out pairs.
ORDER = [
    ("cassava_simufilam_p3", "SAVA", "in-sample"),
    ("madrigal_resmetirom_p3", "MDGL", "in-sample"),
    ("cortexyme_atuzaginstat_gain", "CRTX", "held-out #1"),
    ("karuna_karxt_emergent2", "KRTX", "held-out #1"),
    ("cytokinetics_aficamten_sequoia", "CYTK", "held-out #2"),
    ("atea_at527_moonsong", "AVIR", "held-out #2"),
]

NAVY = HexColor("#1a2b4a")
GREEN = HexColor("#1b7a3d")
RED = HexColor("#b3261e")
GREY = HexColor("#5a5a5a")
LIGHT = HexColor("#eef1f6")


def styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("H1", parent=ss["Title"], textColor=NAVY,
                          fontSize=20, spaceAfter=6, leading=24))
    ss.add(ParagraphStyle("Sub", parent=ss["Normal"], textColor=GREY,
                          fontSize=10, spaceAfter=2, leading=13))
    ss.add(ParagraphStyle("H2", parent=ss["Heading2"], textColor=NAVY,
                          fontSize=14, spaceBefore=14, spaceAfter=4))
    ss.add(ParagraphStyle("H3", parent=ss["Heading3"], textColor=NAVY,
                          fontSize=11.5, spaceBefore=8, spaceAfter=2))
    ss.add(ParagraphStyle("Body", parent=ss["Normal"], fontSize=9.5,
                          leading=13.5, spaceAfter=6, alignment=TA_LEFT))
    ss.add(ParagraphStyle("Small", parent=ss["Normal"], fontSize=8.5,
                          leading=11.5, textColor=GREY))
    ss.add(ParagraphStyle("RFM", parent=ss["Normal"], fontSize=9,
                          leading=12.5, leftIndent=10, spaceAfter=2))
    return ss


def load_pred(ticker: str) -> dict:
    return json.loads((DATA / ticker / "prediction.json").read_text())


def call_color(call: str) -> HexColor:
    return RED if "MISS" in call or "EXCLUDE" in call else GREEN


def build(out_path: Path):
    ss = styles()
    story = []

    # ── Cover / framing ──────────────────────────────────────────────────
    story.append(Paragraph("Biotech Catalyst Honesty Backtest", ss["H1"]))
    story.append(Paragraph(
        "R / f(M) / Finding analysis — predicting clinical-catalyst HIT vs MISS "
        "from pre-cutoff marketing, verified against the as-of-cutoff authoritative "
        "record. Thesis: EXCLUSION of programs whose marketing diverges from the "
        "registry / scientific record, not biology forecasting.", ss["Sub"]))
    story.append(Paragraph("Signal OS · public_biotech vertical · generated 2026-05-31",
                           ss["Small"]))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=NAVY, thickness=1.2))

    # ── Scorecard table ──────────────────────────────────────────────────
    story.append(Paragraph("Discrimination scorecard", ss["H2"]))
    header = ["Trial", "Cohort", "Blind call", "gap", "Predicted", "Actual", "OK"]
    rows = [header]
    cell_styles = []
    for i, (cid, tk, cohort) in enumerate(ORDER, start=1):
        pred = load_pred(tk)
        s = pred["summary"]
        call = s["call"]
        predicted = "MISS" if ("MISS" in call or "EXCLUDE" in call) else "HIT"
        actual = SEALED[cid]["label"]
        ok = "Y" if predicted == actual else "N"
        rows.append([f"{pred['ticker']}", cohort, call.split(" (")[0],
                     f"{s['honesty_gap_normalized']:.3f}", predicted, actual, ok])
        if ok == "N":
            cell_styles.append(("TEXTCOLOR", (6, i), (6, i), RED))
        else:
            cell_styles.append(("TEXTCOLOR", (6, i), (6, i), GREEN))
    t = Table(rows, colWidths=[0.7*inch, 1.0*inch, 1.7*inch, 0.6*inch,
                               0.9*inch, 0.7*inch, 0.4*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#c8cdd6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ] + cell_styles))
    story.append(t)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Binary gate now discriminates on 4 of 6 (SAVA, CRTX, KRTX, AVIR correct; "
        "MDGL, CYTK are false positives on HITs).</b> After the construct-gate fix, KRTX "
        "flips to CLEAN and CRTX keeps its earned MISS. Both remaining errors are the SAME "
        "mechanism — the <i>open_label_extrapolation</i> channel grading open-label "
        "supporting-color citations as severe — not the endpoint channel that was fixed.",
        ss["Body"]))

    # ── Executive narrative ──────────────────────────────────────────────
    story.append(Paragraph("What the six trials test", ss["H2"]))
    for txt in [
        "<b>In-sample matched pair (SAVA / MDGL).</b> Cassava/simufilam (Alzheimer's "
        "Phase 3) vs Madrigal/resmetirom (MASH Phase 3). Establishes the plumbing — "
        "mechanically enforced blinding, as-of-cutoff M reconstruction, R-vs-M "
        "adjudication. SAVA carries a fraud-adjacent overlay ($40M SEC settlement), so "
        "its MISS is a strong-signal case; MDGL is a known false positive driven by the "
        "open-label channel.",
        "<b>Held-out pair #1 (CRTX / KRTX).</b> Cortexyme/atuzaginstat (GAIN) vs "
        "Karuna/KarXT (EMERGENT-2). Both CNS, neither with an integrity overlay. This pair "
        "first exposed the gate bug: CRTX was an earned MISS on a real co-primary construct "
        "swap, but KRTX (a HIT) was false-excluded on a one-week timeFrame restatement.",
        "<b>The fix (implemented; evaluator otherwise frozen).</b> A SEVERE endpoint refute "
        "is now admitted to the decisive set only when the registry version history shows a "
        "genuine construct/type change of the success-slot primary; timeFrame/timepoint and "
        "wording deltas are demoted. This flips KRTX to CLEAN and leaves CRTX a MISS.",
        "<b>Held-out pair #2 (CYTK / AVIR) — the real test of the fix.</b> "
        "Cytokinetics/aficamten (SEQUOIA-HCM, HIT) vs Atea/AT-527 (MORNINGSKY, MISS), run "
        "with the fixed frozen evaluator. The endpoint channel behaved correctly on both "
        "(CYTK construct unchanged → endpoint silent; AVIR construct flagged). But CYTK was "
        "<b>still</b> false-excluded — by 7 <i>open_label_extrapolation</i> refutes on its "
        "FOREST-HCM open-label extension, the identical MDGL failure mode. The held-out HIT "
        "cleanly isolates the next channel to fix, and confirms the endpoint fix itself works.",
    ]:
        story.append(Paragraph(txt, ss["Body"]))

    # ── Per-trial sections ───────────────────────────────────────────────
    for cid, tk, cohort in ORDER:
        story.append(_trial_section(cid, tk, cohort, ss))

    # ── Diagnosis: the two endpoint flags side by side ───────────────────
    story.append(Paragraph("Why one endpoint flag was right and one was wrong", ss["H2"]))
    story.append(Paragraph(
        "Both CRTX and KRTX were excluded by the same rule (bio.endpoint_integrity, "
        "graded SEVERE → decisive). The rule is meant to fire only on a genuine "
        "construct/type change of the success-determining primary endpoint. On CRTX it "
        "did exactly that; on KRTX it fired on noise.", ss["Body"]))
    diag = [["", "Cortexyme GAIN (correct)", "Karuna EMERGENT-2 (false positive)"],
            ["Marketed primary",
             "ADAS-Cog11 + CDR-SB co-primaries",
             "PANSS total at Week 6"],
            ["Registry (as-of-cutoff)",
             "v11 had CDR-SB; v19 replaced it with ADCS-ADL",
             "PANSS total at Week 5 in every version"],
            ["Nature of mismatch",
             "Construct swap: dementia-staging scale -> daily-living scale, mid-trial near readout",
             "One-week timeFrame typo; construct identical"],
            ["Correct grade",
             "SEVERE / decisive (real masking + instability signal)",
             "Minor at most; NOT decisive"],
            ["Outcome",
             "MISS (-70%) — flag paid off",
             "HIT (+70%) — flag was wrong"]]
    dt = Table(diag, colWidths=[1.2*inch, 2.7*inch, 2.7*inch])
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#c8cdd6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TEXTCOLOR", (1, 5), (1, 5), RED),
        ("TEXTCOLOR", (2, 5), (2, 5), GREEN),
    ]))
    story.append(dt)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Fix (not yet applied).</b> A decisive endpoint refute should require a genuine "
        "construct/type change of the success-slot primary — verified against registry "
        "version history — and must treat pure timeFrame/wording deltas (Week-5-vs-6) and "
        "near-term staggered-co-primary emphasis as non-decisive. The fix must be validated "
        "on a fresh held-out name; re-running KRTX after tuning to it would repeat the "
        "in-sample teaching-to-the-test trap.", ss["Body"]))

    SimpleDocTemplate(str(out_path), pagesize=letter,
                      topMargin=0.7*inch, bottomMargin=0.7*inch,
                      leftMargin=0.7*inch, rightMargin=0.7*inch,
                      title="Biotech Catalyst Honesty Backtest").build(story)
    return out_path


def _trial_section(cid: str, tk: str, cohort: str, ss) -> KeepTogether:
    from verticals.public_biotech.catalyst_spec import CASES
    case = CASES[cid]
    pred = load_pred(tk)
    s = pred["summary"]
    out = SEALED[cid]
    call = s["call"]
    correct = (("MISS" in call) == (out["label"] == "MISS"))

    blk = [HRFlowable(width="100%", color=NAVY, thickness=0.8, spaceBefore=8),
           Paragraph(f"{case.company} ({tk}) — {case.program}", ss["H2"]),
           Paragraph(f"{case.indication} · {case.catalyst_type} · blind cutoff "
                     f"{case.cutoff} · cohort: {cohort}", ss["Small"])]

    vc = s["verdict_counts"]
    call_txt = (f'<font color="{_hx(call_color(call))}"><b>{call}</b></font>')
    blk.append(Paragraph(
        f"Blind call: {call_txt} &nbsp;·&nbsp; honesty_gap = "
        f"<b>{s['honesty_gap_normalized']:.3f}</b> &nbsp;·&nbsp; decisive refutes = "
        f"<b>{len(s['decisive_refutes_high_precision'])}</b> &nbsp;·&nbsp; verdicts: "
        f"REFUTED {vc.get('REFUTED',0)} / UNVERIFIABLE {vc.get('UNVERIFIABLE',0)} / "
        f"AFFIRMED {vc.get('AFFIRMED',0)}", ss["Body"]))

    # Decisive flags — dedup by (channel, rationale prefix), cap at 3.
    blk.append(Paragraph("Decisive flags (basis for exclusion)", ss["H3"]))
    seen = set()
    shown = 0
    for f in s["decisive_refutes_high_precision"]:
        key = (f.get("channel"), (f.get("rationale") or "")[:60])
        if key in seen:
            continue
        seen.add(key)
        r = (f.get("R") or "").strip()
        blk.append(Paragraph(f"<b>[{f.get('channel')}]</b> &nbsp; "
                             f"<font color='{_hx(GREY)}'>{f.get('rule_id')}</font>",
                             ss["RFM"]))
        if r:
            blk.append(Paragraph(f"<b>R (claim):</b> “{_esc(r)[:280]}”", ss["RFM"]))
        blk.append(Paragraph(f"<b>Finding:</b> {_esc((f.get('rationale') or '')[:420])}",
                             ss["RFM"]))
        shown += 1
        if shown >= 3:
            break
    if shown == 0:
        blk.append(Paragraph("No decisive high-precision refutes.", ss["RFM"]))

    # Unsealed outcome
    oc = GREEN if out["label"] == "HIT" else RED
    blk.append(Paragraph(
        f"<b>Unsealed outcome ({out['announced']}):</b> "
        f"<font color='{_hx(oc)}'><b>{out['label']} "
        f"({out['price_reaction_pct']:+d}%)</b></font> — {_esc(out['summary'][:360])}",
        ss["Body"]))
    verdict = ("Prediction CORRECT." if correct else
               "Prediction WRONG (false positive on the HIT).")
    vcol = GREEN if correct else RED
    blk.append(Paragraph(f"<font color='{_hx(vcol)}'><b>{verdict}</b></font>",
                         ss["Body"]))
    return KeepTogether(blk)


def _hx(c) -> str:
    return "#" + c.hexval()[2:]


def _esc(t: str) -> str:
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


if __name__ == "__main__":
    p = build(DATA / "_backtest_report.pdf")
    print(f"wrote {p}")
