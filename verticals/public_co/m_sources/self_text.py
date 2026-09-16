"""Self-text divergence: count 'binding' vs 'non-binding' vs 'LOI' mentions
in pre-order/reservation context within a single filing's body.

Same filing markets a number to investors AND discloses it's non-binding —
the divergence is within the document.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["preorder_reservation_metrics"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Within-one-filing divergence: marketed pre-order/reservation counts vs binding/non-binding qualifiers.",
}

import re
from pathlib import Path

CONTEXT_KEYWORDS = (
    "reservation", "pre-order", "preorder", "order book",
    "letter of intent", " loi ", " moa ", "non-binding",
)

# SPAC-merger boilerplate. A pre-merger filing's LOI/binding language is
# mostly about completing the merger itself, not about customer orders. Drop
# any sentence carrying these markers from the count.
SPAC_BOILERPLATE_MARKERS = (
    "business combination", "trust account", "sponsor",
    "redemption", "warrant agreement",
)


def query_binding_vs_loi(filing_path: Path) -> dict:
    if not filing_path.exists():
        return {"error": f"not_found: {filing_path.name}"}
    text = filing_path.read_text(errors="ignore")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    findings: dict[str, list[str]] = {
        "binding": [], "non_binding": [], "loi": [], "production_orders": [],
    }
    for s in re.split(r"(?<=\.)\s+", text):
        sl = s.lower()
        if any(k in sl for k in CONTEXT_KEYWORDS):
            if any(m in sl for m in SPAC_BOILERPLATE_MARKERS):
                continue
            if "non-binding" in sl or "non binding" in sl:
                findings["non_binding"].append(s[:300].strip())
            elif "binding" in sl:
                findings["binding"].append(s[:300].strip())
            if "letter of intent" in sl or " loi " in sl:
                findings["loi"].append(s[:300].strip())
            if "production" in sl and "order" in sl:
                findings["production_orders"].append(s[:300].strip())

    return {
        "binding_count": len(findings["binding"]),
        "non_binding_count": len(findings["non_binding"]),
        "loi_count": len(findings["loi"]),
        "production_order_count": len(findings["production_orders"]),
        "binding_mentions": findings["binding"][:5],
        "non_binding_mentions": findings["non_binding"][:5],
        "loi_mentions": findings["loi"][:5],
    }


def find_filing(filings_dir: Path, form_match: str, accession: str | None = None) -> Path | None:
    """Return path to first filing whose name contains the form (and optional accession)."""
    for p in sorted(filings_dir.glob("*.txt")):
        name = p.name
        if accession and accession not in name:
            continue
        if form_match in name:
            return p
    return None
