"""wizard — the Phase-1 intake front-end: answers in, personal scenario planner out.

Two modes, one funnel (officekit.intake.build_from_answers):

  python3 -m officekit.wizard --answers sam.json --out ./sam/
      Non-interactive: an answers JSON (hand-written, wizard-saved, or emitted by
      the LLM statement agent per officekit/INTAKE_AGENT.md) -> balance sheet +
      rendered office/scenario pages.

  python3 -m officekit.wizard --out ./sam/
      Interactive: a terminal interview (sleeves, CSV imports, windfall, risk
      profile) that builds the same answers dict, saves it alongside the output
      (so the session is reproducible/editable), then renders.

Outputs in --out: <slug>_answers.json, <slug>_balance_sheet.json,
<slug>_office.html, <slug>_scenarios.html. READ-ONLY — never places orders.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from officekit import build_model, render_office, render_scenarios, render_strategies
from officekit.intake import build_from_answers

CATEGORY_MENU = [
    ("cash", "Cash / money market"),
    ("public_equity", "Public equity (index funds / pooled stocks)"),
    ("single_name_equity", "Concentrated single stock"),
    ("fixed_income", "Bonds"),
    ("municipal_credit", "Municipal bonds"),
    ("real_estate", "Real estate (home)"),
    ("real_estate_debt", "Mortgage / property debt"),
    ("venture_private", "Venture / private / angel"),
    ("alpha_market_neutral", "Alpha / market-neutral sleeve"),
]

PROFILE_QUESTIONS = [
    ("net_buyer", "Are you still adding savings most years (a net BUYER of assets)?"),
    ("uses_leverage", "Do you use margin or other portfolio leverage?"),
    ("decumulating", "Are you drawing income from the portfolio (retired / decumulating)?"),
    ("premium_selling_allowed", "Are you comfortable selling options premium (collars/covered calls)?"),
    ("concentrated_low_basis", "Do you hold a large low-basis concentrated position you can't cheaply sell?"),
]


def _ask(prompt, default=None):
    sfx = f" [{default}]" if default not in (None, "") else ""
    val = input(f"{prompt}{sfx}: ").strip()
    return val or ("" if default is None else str(default))


def _ask_yn(prompt, default=False):
    val = input(f"{prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    if not val:
        return default
    return val.startswith("y")


def _ask_money(prompt):
    while True:
        raw = _ask(prompt).replace("$", "").replace(",", "").lower()
        try:
            mult = 1
            if raw.endswith("k"):
                mult, raw = 1_000, raw[:-1]
            elif raw.endswith("m"):
                mult, raw = 1_000_000, raw[:-1]
            return float(raw) * mult
        except ValueError:
            print("  couldn't parse that — try e.g. 250000, 250k, or 1.2m")


def interview():
    """Terminal interview -> answers dict (same shape the LLM agent emits)."""
    print("officekit intake — your balance sheet, sleeve by sleeve.")
    print("Rule: nothing is fabricated. If you don't know a number, we tag it TBD.\n")
    answers = {"owner": _ask("First name", "there"),
               "as_of": _ask("As-of date (YYYY-MM-DD)", date.today().isoformat()),
               "sleeves": [], "imports": [], "profile": {}}

    while _ask_yn("\nImport a brokerage positions CSV?", default=not answers["imports"]):
        path = _ask("  CSV path")
        if not Path(path).exists():
            print("  file not found — skipping")
            continue
        answers["imports"].append({"kind": "positions_csv", "path": path,
                                   "account": _ask("  Account label", "brokerage")})

    print("\nNow the sleeves no statement shows (home, mortgage, venture, cash elsewhere).")
    while _ask_yn("Add a sleeve?", default=True):
        for i, (_, label) in enumerate(CATEGORY_MENU, 1):
            print(f"  {i}. {label}")
        try:
            cat = CATEGORY_MENU[int(_ask("Category #")) - 1][0]
        except (ValueError, IndexError):
            print("  bad choice — skipping")
            continue
        s = {"category": cat, "value": _ask_money("  Current value ($; debts as a positive number)")}
        name = _ask("  Name (blank = default)", "")
        if name:
            s["name"] = name
        if cat == "real_estate_debt":
            rate = _ask("  Fixed rate % (blank if unknown/ARM)", "")
            if rate:
                s["rate_pct"] = float(rate)
        if not _ask_yn("  Is this value from a statement/primary source?", default=True):
            s["confidence"] = "tbd"
        tgt = _ask("  Target % of net worth (blank = none)", "")
        if tgt:
            s["target_pct"] = float(tgt)
        answers["sleeves"].append(s)

    if _ask_yn("\nModel your income as an asset (capitalized future earnings, with a beta)?", default=True):
        inc = {"annual": _ask_money("  Annual income ($)"),
               "years": float(_ask("  Years you expect to keep earning it", "20"))}
        style = _ask("  Income style: equity_linked (tech/startup comp) / stable (tenure, gov) / blank = balanced", "")
        if style in ("equity_linked", "stable"):
            inc["style"] = style
        answers["income"] = inc

    if _ask_yn("\nAny incoming windfall (sale proceeds, bonus, inheritance)?", default=False):
        inc = {"amount": _ask_money("  Gross amount ($)"),
               "eta": _ask("  When does it land (label, e.g. 'Dec')", "pending"),
               "character": _ask("  Tax character (ltcg / ordinary / return_of_capital)", "ltcg")}
        rate = _ask("  Combined tax rate on it (e.g. 0.30; blank = don't model)", "")
        if rate:
            inc["rate"] = float(rate)
        answers["incoming"] = inc

    print("\nLife goals (the Scenario Planner will re-score each one through the tail):")
    goals = []
    if _ask_yn("Add a retirement goal?", default=True):
        goals.append({"kind": "retirement", "label": "Retirement",
                      "date": _ask("  Target date (YYYY-MM-DD)", ""),
                      "annual_spending": _ask_money("  Annual spending in retirement ($)")})
    while _ask_yn("Add a dated spending target (college, home, sabbatical)?", default=False):
        goals.append({"kind": "spending", "label": _ask("  Label", "Spending target"),
                      "date": _ask("  When (YYYY-MM-DD, blank if unknown)", ""),
                      "amount": _ask_money("  Amount ($)")})
    if _ask_yn("Set a liquidity floor (cash+marketable you never want to dip below)?", default=True):
        goals.append({"kind": "liquidity_floor", "label": "Liquidity floor",
                      "amount": _ask_money("  Floor ($)")})
    answers["goals"] = [
        {k: v for k, v in g.items() if v not in ("", None)} for g in goals
    ]

    print("\nRisk profile (scores the mitigation menu — a lens, not a filter):")
    for flag, q in PROFILE_QUESTIONS:
        answers["profile"][flag] = _ask_yn(f"  {q}", default=(flag == "net_buyer"))
    return answers


def run(answers, out_dir, slug=None):
    """answers -> balance sheet + rendered pages in out_dir. Returns the paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    slug = slug or re.sub(r"[^a-z0-9]+", "_", (answers.get("owner") or "client").lower()).strip("_") or "client"
    data = build_from_answers(answers)
    m = build_model(data)
    paths = {
        "answers": out / f"{slug}_answers.json",
        "balance_sheet": out / f"{slug}_balance_sheet.json",
        "office": out / f"{slug}_office.html",
        "scenarios": out / f"{slug}_scenarios.html",
        "strategies": out / f"{slug}_strategies.html",
    }
    paths["answers"].write_text(json.dumps(answers, indent=1, ensure_ascii=False) + "\n")
    pc_path = out / f"{slug}_personal_context.json"
    if not pc_path.exists():
        from officekit.personal_context import empty as _pc_empty
        pc_path.write_text(json.dumps(_pc_empty(data.get("office_id")), indent=1) + "\n")
    paths["balance_sheet"].write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    paths["office"].write_text(render_office(m))
    paths["scenarios"].write_text(render_scenarios(m, strategies_href=f"{slug}_strategies.html"))
    paths["strategies"].write_text(render_strategies(m, scenarios_href=f"{slug}_scenarios.html"))
    return paths, m


def main(argv=None):
    ap = argparse.ArgumentParser(prog="officekit.wizard", description=__doc__.splitlines()[0])
    ap.add_argument("--answers", help="answers JSON (skip the interview)")
    ap.add_argument("--out", default=".", help="output directory (default: cwd)")
    ap.add_argument("--slug", help="output filename slug (default: owner name)")
    args = ap.parse_args(argv)
    if args.answers:
        answers = json.loads(Path(args.answers).read_text())
    else:
        if not sys.stdin.isatty():
            print("[wizard] no --answers and stdin is not a terminal — nothing to do", file=sys.stderr)
            return 2
        answers = interview()
    paths, m = run(answers, args.out, slug=args.slug)
    nw = m["NW"]
    print(f"\n[wizard] {answers.get('owner', 'client')}: net worth ${nw:,.0f} across "
          f"{len(m['assets'])} asset sleeves ({len(m['liabs'])} liabilities)")
    for k in ("balance_sheet", "office", "scenarios", "strategies"):
        print(f"[wizard]   {k}: {paths[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
