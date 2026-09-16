"""gen_sleeve_reports — turn every research-ledger SLEEVE into a markdown Research doc, so all the DD
flows into the dashboard Research tab + each ticker's dossier (the research scanner indexes these, and
the dossier matches a doc to a ticker by a word-boundary mention). Re-runnable: regenerate after any
ledger change. Part of the standing rule (research -> UI).

  python3 -m desk.gen_sleeve_reports
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
OUT = ROOT / "verticals" / "deep_value" / "data"

TITLES = {
    "contrarian_credit": "Contrarian Credit (Alt-Managers)", "hnw_insurers": "HNW Insurers",
    "hnw_shovels": "HNW Shovels (Wealth Managers)", "luxury_champions": "Global Luxury Champions",
    "held": "Held — Research-Tracked Positions", "k_shaped_top": "K-Shaped TOP (Affluent / Hard-Luxury)",
    "k_shaped_bottom": "K-Shaped BOTTOM (Trade-Down)", "ai_application": "AI Application Layer",
    "insurance_brokers": "Insurance Brokers — the Toll-Road", "grid_bottleneck": "Grid / Electrical Bottleneck",
    "glp1_honesty": "GLP-1 Honesty Screen", "georgia_banks": "Georgia Banks — EM Carry",
    "war_unwind": "War-Unwind — 2026 Iran-War Recovery",
    "ukraine_recovery": "Ukraine Post-War Recovery — Sovereign Convexity + Quality Equity",
    "ukraine_reconstruction_b": "Ukraine Reconstruction (Option B) — Squeeze-Out-Free Dispersed Beneficiaries",
}


def _vsleeve(names):
    cnt = {}
    for n in names:
        cnt[n["verdict"]] = cnt.get(n["verdict"], 0) + 1
    return " · ".join(f"{v} {k}" for k, v in sorted(cnt.items(), key=lambda x: -x[1]))


def main():
    d = json.loads(LEDGER.read_text())
    sleeves = {}
    for n in d["names"]:
        sleeves.setdefault(n.get("sleeve", "other"), []).append(n)
    today = datetime.date.today().isoformat()
    written = []
    for sl, names in sleeves.items():
        title = TITLES.get(sl, sl.replace("_", " ").title())
        tickers = ", ".join(n["ticker"] for n in names)
        lines = [f"# {title} — SignalOS Research Sleeve", "",
                 f"*Generated from the research ledger {today}. {len(names)} names: {tickers}. "
                 f"Verdicts: {_vsleeve(names)}. READ-ONLY — verdict + quantified entry per name.*", "",
                 "| Ticker | Verdict | Conviction | Spot→FV | Buy ≤ | Entry |",
                 "|---|---|---|---|---|---|"]
        for n in names:
            q = n.get("quant", {})
            up = q.get("current_upside_pct")
            lines.append(f"| **{n['ticker']}** | {n['verdict']} | {n.get('conviction','')} | "
                         f"{(str(up)+'%') if up is not None else '–'} | {n.get('alert_below','–')} | "
                         f"{(n.get('entry','') or '')[:90]} |")
        lines += ["", "## Per-name diligence", ""]
        for n in names:
            q = n.get("quant", {})
            lines.append(f"### {n['ticker']} — {n.get('name','')}  ·  **{n['verdict']}**")
            lines.append(f"{n.get('thesis','')}")
            if q:
                lines.append("")
                lines.append(f"**Quant:** FV {q.get('fv_base','–')} · live {q.get('current_px','–')} · "
                             f"spot→FV {q.get('current_upside_pct','–')}% · MoS: {q.get('margin_of_safety','–')}")
            lines.append(f"**Entry:** {n.get('entry','')}")
            lines.append(f"*Source: {n.get('source','')}*")
            lines.append("")
        p = OUT / f"SLEEVE_{sl}.md"
        p.write_text("\n".join(lines))
        written.append((sl, len(names), p.name))
    print(f"wrote {len(written)} sleeve reports to {OUT.relative_to(ROOT)}:")
    for sl, n, fn in written:
        print(f"  {fn}  ({n} names)")


if __name__ == "__main__":
    main()
