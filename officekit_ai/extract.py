"""extract — drop-anything statement extraction (the wizard grows eyes;
ratified 2026-09-05).

One function: a file (PDF, screenshot, anything imageable) in, confidence-
tagged position rows out — THROUGH the reconciliation gate. The model must
also read the document's own printed total and as-of date, and the extracted
rows must foot to that total: a mismatch beyond tolerance becomes a WARNING
the review surface shows, never a silently-smoothed number. Deterministic
formats (CSV) never reach this module — the router tries the exact importer
first; a model is the fallback for pixels, not the default for tables.

The extractor proposes; it never writes the balance sheet. Rows land in the
same reviewable onboarding form as every other door.
"""
from __future__ import annotations

import base64
import json

RECONCILE_TOL = 0.02                                 # 2% — statements round, models misread

_MEDIA = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg",
          "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}

_SCHEMA = {
    "type": "object",
    "properties": {
        "account_label": {"type": "string", "description": "institution + account as printed, e.g. 'Fidelity ...1234'"},
        "as_of": {"type": ["string", "null"], "description": "the statement's own date, YYYY-MM-DD, null if absent"},
        "stated_total": {"type": ["number", "null"],
                         "description": "the document's OWN printed total value; null only if truly absent"},
        "rows": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "symbol": {"type": ["string", "null"], "description": "ticker if printed; null for unlisted holdings"},
                "description": {"type": "string"},
                "qty": {"type": ["number", "null"]},
                "value": {"type": "number", "description": "market value in the statement's currency"},
                "confidence": {"type": "number", "description": "0-1; below 0.6 means you are guessing"},
            },
            "required": ["symbol", "description", "qty", "value", "confidence"],
            "additionalProperties": False,
        }},
        "currency": {"type": "string", "description": "ISO code of the statement's values"},
        "notes": {"type": "array", "items": {"type": "string"},
                  "description": "anything cropped, illegible, ambiguous, or excluded — say so here"},
    },
    "required": ["account_label", "as_of", "stated_total", "rows", "currency", "notes"],
    "additionalProperties": False,
}

_SYSTEM = (
    "You extract POSITIONS from a brokerage/retirement statement, screenshot, or export. "
    "Rules, all binding:\n"
    "- NEVER fabricate: a value you cannot read is a row you do not emit; note it in `notes`.\n"
    "- Extract the document's OWN printed total (stated_total) and its OWN date (as_of) — "
    "these gate reconciliation downstream.\n"
    "- Values are MARKET VALUE, not cost basis — if only cost basis is printed, use it and "
    "say so in notes.\n"
    "- Watch the classic traps: shares-vs-value column confusion, pence vs pounds, thousands "
    "separators, subtotal rows (do NOT emit subtotals as positions), multi-account documents "
    "(emit the account you can attribute; note the rest).\n"
    "- confidence below 0.6 means you are guessing — prefer omitting + noting over guessing."
)


EXTRACT_TIMEOUT_S = 90                                # one document must never hang the import


def _create(client, timeout, **kw):
    """Keep the document timeout across any intelligence provider."""
    from officekit_ai.intelligence import generate
    return generate(client, timeout=timeout, **kw)


def extract_file(filename, data, client=None, model=None, folder=None, timeout=EXTRACT_TIMEOUT_S):
    """One document -> {account_label, as_of, stated_total, rows, currency,
    notes, warnings}. Raises on unsupported types, truncation, and timeout —
    the caller surfaces errors; nothing silent, nothing hangs."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media = _MEDIA.get(ext)
    if media is None:
        raise ValueError(f"{filename}: unsupported for extraction ({ext or 'no extension'}) — "
                         f"CSV goes through the exact importer; supported here: {', '.join(_MEDIA)}")
    if client is None:
        from officekit_ai.models import client_for
        client, resolved = client_for("extract", folder)
        model = model or resolved
    block = {"type": "document" if media == "application/pdf" else "image",
             "source": {"type": "base64", "media_type": media,
                        "data": base64.b64encode(data).decode()}}
    kw = dict(model=model, max_tokens=16000, system=_SYSTEM,
              messages=[{"role": "user", "content": [
                  block, {"type": "text", "text": f"Extract the positions from this document ({filename})."}]}],
              output_config={"format": {"type": "json_schema", "schema": _SCHEMA}})
    resp = _create(client, timeout, **kw)
    if resp.stop_reason == "max_tokens":
        raise RuntimeError(f"{filename}: extraction truncated at max_tokens — raise the cap")
    out = json.loads(next(b.text for b in resp.content if b.type == "text"))
    # stamp the statement currency onto every row so a non-USD screenshot can't
    # enter the book unconverted (there's no FX source on the pixel door — the
    # rows are flagged, and import records the currency for the review surface)
    ccy = (out.get("currency") or "USD").upper()
    for r in out.get("rows") or []:
        r["ccy"] = ccy
    out["currency"] = ccy
    out["warnings"] = reconcile(out)
    if ccy != "USD":
        out["warnings"].insert(0, f"statement is in {ccy}, not USD — values are NOT converted; "
                               f"treat totals as {ccy} and convert before relying on them")
    return out


def reconcile(out):
    """The gate: extracted rows must foot to the document's own total. Returns
    warnings (empty = clean); a missing stated_total is itself a warning — an
    unreconcilable extraction is never presented as verified."""
    from officekit.staging import num
    warnings = []
    rows_total = sum(num(r.get("value")) for r in out.get("rows") or [])
    stated = out.get("stated_total")
    if stated is None:
        warnings.append("document shows no total — extraction is UNRECONCILED; verify rows by hand")
    elif num(stated) == 0 and rows_total != 0:
        warnings.append(f"document total reads 0 but rows sum to {rows_total:,.2f} — "
                        f"UNRECONCILED; verify by hand")
    elif stated and abs(rows_total - num(stated)) > RECONCILE_TOL * abs(num(stated)):
        st = num(stated)
        warnings.append(f"rows sum to {rows_total:,.2f} but the document states "
                        f"{st:,.2f} ({rows_total - st:+,.2f}) — rows missing, "
                        f"misread, or the total includes cash/accruals; review before building")
    low = [r for r in out.get("rows") or [] if num(r.get("confidence")) < 0.6]
    if low:
        warnings.append(f"{len(low)} low-confidence row(s): "
                        + ", ".join((r.get("symbol") or r.get("description", "?"))[:20] for r in low[:5]))
    warnings += [f"extractor note: {n}" for n in out.get("notes") or []]
    return warnings
