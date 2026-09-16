"""
Resolve each cohort ticker to a flat list of entity-name variants.

For each (ticker, cik, name):
  1. Pull Exhibit 21 from latest 10-K (formal subsidiary list).
  2. Hand the company name + subsidiary list to Claude. Ask for the
     normalized set of names this company could appear under in a
     Pentagon J-Book or contract database. Includes:
       - parent corp name + common short forms
       - federal-contracting entity (e.g., "IonQ Federal, LLC")
       - recent acquisitions (target company names, pre-rebrand)
       - division / DBA names
       - JV partners
  3. Write per-ticker JSON to ticker_entity_resolution.json.

This is a one-shot synthesis, not an agentic loop. For tickers where
Exhibit 21 fails (PDF-only, missing, foreign filer), the LLM falls back
to whatever names it knows from training data and flags the result as
low-confidence.

Optional --web-search: if the Anthropic SDK supports the `web_search`
server tool, add it to enrich training-cutoff blind spots. We try it;
if the SDK rejects the tool config, we drop it and proceed without.
"""
from __future__ import annotations

import importlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from verticals.public_co.scripts.edgar_exhibit_21 import fetch_exhibit_21

OUT_DIR = Path("verticals/public_co/data/_entity_resolution")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "ticker_entity_resolution.json"

_MODEL = os.environ.get("RESOLVER_MODEL", "claude-haiku-4-5-20251001")
_KEY_FILE = Path("~/.anthropic_api_key").expanduser()


def _get_client():
    if not _KEY_FILE.exists():
        raise RuntimeError(f"No API key at {_KEY_FILE}")
    from anthropic import Anthropic
    return Anthropic(api_key=_KEY_FILE.read_text().strip())


_SYSTEM = """You are resolving a public company to the complete set of names it might appear under in a Pentagon J-Book, federal contract database (SAM.gov / USAspending.gov), or DoD program element narrative.

You will receive:
- The ticker, the SEC-registered name, and the CIK.
- The latest Exhibit 21 (List of Subsidiaries) extracted from the 10-K.

Your job: produce a FLAT list of names this company could appear under. Include:
1. The parent corp name (full and common short forms — e.g., "IonQ", "IonQ, Inc.", "IonQ Inc")
2. The federal-contracting subsidiary if one exists in Exhibit 21 (e.g., "IonQ Federal, LLC", "Palantir Technologies Federal", "Lockheed Martin Federal Government Services")
3. Recent acquisitions where the target's pre-rebrand name might still appear on contracts (e.g., "Capella Space Corp", "Oxford Ionics Limited", "ID Quantique Inc", "Qubitekk")
4. Domestic operating subsidiaries (US, not foreign country subs) — foreign subs won't be in Pentagon books
5. Common DBA / division names if widely used in defense contracts
6. Pre-merger / pre-rename forms if the company was renamed in the last ~5 years (e.g., "Northrop Grumman Innovation Systems" → previously "Orbital ATK")

EXCLUSIONS:
- Foreign-only subsidiaries (GmbH, Ltd UK, Israel Ltd, Canada Inc) — these don't appear on US DoD contracts
- Acquisition holding shells (e.g., "IonQ Quantum Acquisitions, Inc")
- Subsidiaries that are clearly investment-only entities

Output strict JSON, no markdown:
{
  "ticker": "IONQ",
  "canonical_name": "IonQ, Inc.",
  "name_variants": [
    {"name": "IonQ Federal, LLC", "type": "federal_subsidiary", "confidence": "high"},
    {"name": "IonQ", "type": "short_form", "confidence": "high"},
    {"name": "Capella Space", "type": "acquisition", "confidence": "high", "acquired_year": 2025},
    {"name": "Oxford Ionics", "type": "acquisition", "confidence": "high", "acquired_year": 2025},
    {"name": "Qubitekk", "type": "acquisition", "confidence": "high", "acquired_year": 2024}
  ],
  "notes": "1-2 sentence summary of anything special, e.g., 'Heavy AFRL quantum-program exposure via Qubitekk acquisition.'",
  "training_data_only_fields": ["acquisitions older than the Exhibit 21"]
}

Be CONSERVATIVE. Don't fabricate subs. Only include names you can support from the Exhibit 21 list OR widely-known publicly disclosed history."""


def _build_user_message(ticker: str, name: str, cik: str, ex21: dict) -> str:
    parts = [
        f"TICKER: {ticker}",
        f"REGISTERED NAME: {name}",
        f"CIK: {cik}",
    ]
    if ex21.get("error"):
        parts.append(f"\nEXHIBIT 21 STATUS: failed ({ex21['error']}) — fall back to training data.")
    else:
        parts.append(f"\nEXHIBIT 21 (from 10-K filed {ex21.get('filing_date','?')}, "
                     f"{ex21.get('n_subsidiaries',0)} subsidiaries):")
        for s in ex21.get("subsidiaries", []):
            j = s.get("jurisdiction", "")
            parts.append(f"  - {s['name']}" + (f"  ({j})" if j else ""))
        if not ex21.get("subsidiaries"):
            parts.append("  (empty — Exhibit 21 parsed but no subsidiaries extracted; "
                          "may be PDF-only or new IPO)")
    parts.append("\nProduce the JSON now.")
    return "\n".join(parts)


def _parse_json(text: str) -> dict:
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def resolve_one(client, ticker: str, name: str, cik: str) -> dict:
    print(f"\n  fetching Exhibit 21 for {ticker} ({cik})…", file=sys.stderr)
    ex21 = fetch_exhibit_21(cik)
    if ex21.get("error"):
        print(f"    ex21 error: {ex21['error']}", file=sys.stderr)
    else:
        print(f"    ex21 subs: {ex21.get('n_subsidiaries',0)}", file=sys.stderr)

    user_msg = _build_user_message(ticker, name, cik, ex21)
    backoffs = [0, 2, 5]
    for delay in backoffs:
        if delay:
            time.sleep(delay)
        try:
            resp = client.messages.create(
                model=_MODEL,
                max_tokens=800,
                system=_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = resp.content[0].text if resp.content else ""
            data = _parse_json(text)
            data["_exhibit_21"] = {
                "n_subs": ex21.get("n_subsidiaries"),
                "filing_date": ex21.get("filing_date"),
                "error": ex21.get("error"),
            }
            return data
        except Exception as e:
            print(f"    LLM error: {e}", file=sys.stderr)
            continue
    return {
        "ticker": ticker, "canonical_name": name,
        "name_variants": [{"name": name, "type": "registered_name", "confidence": "low"}],
        "_exhibit_21": {"error": "llm_failure"},
        "_error": "llm_failed_after_retries",
    }


def gather_cohort() -> list[dict]:
    relevant = ["defense_cohort", "space_cohort", "quantum_cohort", "robotics_cohort"]
    universe: dict[str, dict] = {}
    for modname in relevant:
        m = importlib.import_module(f"verticals.public_co.{modname}")
        for member in m.COHORT:
            tk = member.ticker.upper()
            if tk not in universe:
                universe[tk] = {
                    "ticker": tk, "cik": member.cik,
                    "name": getattr(member, "name", "") or "",
                    "cohort": modname,
                }
    return list(universe.values())


def main():
    universe = gather_cohort()
    print(f"Resolving {len(universe)} tickers…", file=sys.stderr)
    client = _get_client()

    out: dict[str, dict] = {}
    for i, c in enumerate(universe, 1):
        tk = c["ticker"]
        print(f"\n[{i}/{len(universe)}] {tk:6} {c['name'][:50]}", file=sys.stderr)
        t0 = time.time()
        try:
            data = resolve_one(client, tk, c["name"], c["cik"])
        except Exception as e:
            data = {"ticker": tk, "_error": str(e)}
        data["cohort"] = c["cohort"]
        data["_runtime_sec"] = round(time.time() - t0, 2)
        out[tk] = data
        n_var = len(data.get("name_variants") or [])
        print(f"    → {n_var} name variants ({data['_runtime_sec']:.1f}s)",
              file=sys.stderr)

    OUT_PATH.write_text(json.dumps({"_meta": {"n_resolved": len(out)},
                                     "tickers": out}, indent=2, default=str))
    print(f"\nWrote {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
