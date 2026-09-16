"""gen_ticker_cards — emit one research-card .md per research-ledger name into
verticals/deep_value/data/dossiers/, so EVERY ticker has its own dedicated write-up document
attached to its dossier (the filename carries the ticker → reliable dossier match, no text-collision).

Rich hand-written DD_*.md / SLEEVE_*.md documents still take precedence in the dossier; this guarantees
floor coverage (no ticker without an attached write-up). Idempotent — rewrite each run.

  python3 -m desk.gen_ticker_cards
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
OUT = ROOT / "verticals" / "deep_value" / "data" / "dossiers"


def _scen_block(n: dict) -> str:
    sc = n.get("scenarios")
    if not isinstance(sc, dict):
        return ""
    rows = "\n".join(f"| {k} | {v.get('p','')} | {v.get('ret','')} |" for k, v in sc.items())
    return "\n**Scenarios**\n\n| Scenario | Prob | Return |\n|---|---|---|\n" + rows + "\n"


def card(n: dict, asof: str) -> str:
    flags = []
    if n.get("verified"):
        flags.append("funding/thesis VERIFIED")
    if n.get("geopol_verified"):
        flags.append("geopolitical VERIFIED")
    if n.get("dd_verified"):
        flags.append(f"DD-verified {n['dd_verified']}")
    fl = (" · " + " · ".join(flags)) if flags else ""
    parts = [f"# {n['ticker']} — {n.get('name','')}",
             f"**Sleeve:** {n.get('sleeve','')} · **Verdict:** {n.get('verdict','')}{fl}\n"]
    if n.get("conviction"):
        parts.append(f"**Conviction:** {n['conviction']}\n")
    if n.get("sizing"):
        parts.append(f"**Sizing:** {n['sizing']}\n")
    if n.get("exp_return"):
        parts.append(f"**Expected return:** {n['exp_return']}\n")
    sb = _scen_block(n)
    if sb:
        parts.append(sb)
    if n.get("alert_below"):
        parts.append(f"**Dislocation-add alert:** ≤ {n['alert_below']}\n")
    parts.append("## Thesis\n\n" + (n.get("thesis") or "—"))
    parts.append(f"\n\n---\n*Research card auto-generated from the SignalOS research ledger ({asof}). "
                 "Where a full deep-dive exists (DD_* / SLEEVE_* docs), that document carries the worked "
                 "valuation, Mode-B pass, and primary sources.*")
    return "\n".join(parts)


def main():
    d = json.loads(LEDGER.read_text())
    asof = d.get("asof") or datetime.date.today().isoformat()
    OUT.mkdir(parents=True, exist_ok=True)
    # clear stale cards (names removed from the ledger)
    live = {n["ticker"] for n in d["names"]}
    for p in OUT.glob("*.md"):
        if p.stem not in live:
            p.unlink()
    n_w = 0
    for n in d["names"]:
        (OUT / f"{n['ticker']}.md").write_text(card(n, asof))
        n_w += 1
    print(f"wrote {n_w} ticker cards -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
