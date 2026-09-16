"""Generic SEC-filing concentration ingestor — tables + qualitative, not regex-over-prose.

Emits normalized customer-concentration records so any detector can consume structured
facts instead of pattern-matching flattened prose. It operates on the bs4 clean-extract
TEXT (tables already flattened to 'cell | cell | cell' lines), so it is pure-text and
unit-testable — no DOM, no I/O.

Three record sources:
  - "table":       a flattened row binds a customer (named row label, or a "Customer A (1)"
                   code resolved via the table's footnote) to a >=10% cell — gated on
                   customer context and screened against margin / stock-comp-volatility /
                   rate / segment tables (the false-% trap a naive grabber hits).
  - "qualitative": "one / a single (end) customer" sole-source disclosures (pct unknown but
                   ~total) — this is what closes a Cirrus-style qualitative disclosure.
  - "prose":       left to the caller's run-regex on clean text (not duplicated here).

Record = {"entity": str, "pct": float|None, "denominator": str, "source": str}.
"""
from __future__ import annotations

import re
from typing import Any, Optional

# percent scan over a WHOLE flattened row — handles the number and the "%" landing in
# adjacent cells ("12.0 | %") as well as "12.4 %".
_PCT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*\|?\s*%")
# customer/client context that distinguishes a concentration table from a margin/opex one
_CUST_CTX = re.compile(r"\b(?:customer|client)s?\b", re.I)
_REVSALE = re.compile(r"\b(?:net sales|net revenue|total revenue|revenues?|sales)\b", re.I)
# caption that opens a customer-concentration table (and whether it's AR vs revenue)
_CONC_CAPTION = re.compile(
    r"(?:significant customers|individual customers?|"
    r"customers?\s+(?:representing|account(?:ed|ing)?\s+for|who\s+account(?:ed|s)?\s+for|"
    r"that\s+(?:individually\s+)?(?:account|represent|comprise)))", re.I)
_AR_CAPTION = re.compile(r"accounts?\s+receivable", re.I)
# a bare/coded customer row label ("A", "Customer B", "Customer 1")
_CODE_LABEL = re.compile(r"^(?:customer\s+)?[A-Z]$|^customer\s+[A-Za-z0-9]+$", re.I)
# tables/rows that carry %s but are NOT customer concentration — hard screen
_ANTI = re.compile(
    r"volatilit|risk[\s-]?free|interest rate|expected term|dividend yield|fair value|"
    r"black[\s-]?scholes|gross (?:margin|profit)|operating (?:margin|expense)|"
    r"effective tax|tax rate|discount rate|\bsegment\b|geograph|maturit|amortiz|"
    r"depreciat|impair|goodwill|stock price|per share|interest expense", re.I)
# a row label that names a company (NVIDIA, Apple Inc., Customer A, etc.)
_COMPANY = re.compile(
    r"(?:^|\b)(?:customer|client)\s+[A-Z0-9]\b|"
    r"\b[A-Z][a-zA-Z&.\-]+(?:\s+[A-Z][a-zA-Z&.\-]+){0,3}\s*"
    r"(?:Inc|Corp|Corporation|Ltd|LLC|L\.?P|Co|Company|Technologies|Technology|Systems|"
    r"Holdings|Group|Networks|Semiconductor|Electronics|plc|AG|SA|NV)\b")
# footnote definition line: "(1) Customer A consists of NVIDIA Corporation" / "(1) Apple Inc."
_FOOTNOTE = re.compile(r"^\s*\(?\s*(\d+)\s*\)?\s*[\.\)]?\s*(.{2,140})", re.I)
# metric/period row labels that are NOT entities
_METRIC_LABEL = re.compile(
    r"^\s*(?:net sales|net revenue|revenues?|sales|total|fiscal|year|three|nine|twelve|"
    r"month|quarter|january|february|march|april|may|june|july|august|september|october|"
    r"november|december|20\d\d|accounts? receivable)\b", re.I)
# qualitative sole-customer phrasings (positive only; negation excluded by construction)
_QUAL = re.compile(
    r"(?:we\s+(?:had|have)|there\s+(?:was|were)|having)\s+(?:only\s+)?(?:one|a\s+single)\s+"
    r"(?:end[\s-]?)?customer(?:\s*,?\s*((?:[A-Z][a-zA-Z&.\-]+\s*){1,4}(?:Inc\.?|Corp\.?|"
    r"Ltd\.?|LLC|Company)?))?", re.I)
_QUAL2 = re.compile(
    r"(?:substantially all|nearly all|a majority|most)\s+of\s+(?:our\s+)?(?:net\s+)?"
    r"(?:revenues?|sales)\s+(?:was|were|is|are|(?:were|was)\s+)?(?:derived|generated|"
    r"attributable|came|come)?[^.]{0,30}?\bfrom\s+(?:one|a\s+single)\s+(?:end[\s-]?)?customer",
    re.I)
_QUAL_NEG = re.compile(r"\b(?:no|not|never|nor)\b[^.]{0,30}$")


def _first_company(s: str) -> Optional[str]:
    m = _COMPANY.search(s)
    return re.sub(r"\s+", " ", m.group(0)).strip(" .,:;") if m else None


def _denominator(ctx: str) -> str:
    m = re.search(r"net sales|net revenue|total revenue|revenues?|sales", ctx, re.I)
    return m.group(0).lower() if m else "revenue"


def _footnote_map(lines: list[str]) -> dict[str, str]:
    fmap: dict[str, str] = {}
    for ln in lines:
        m = _FOOTNOTE.match(ln)
        if m and "|" not in ln:
            name = _first_company(m.group(2))
            if name:
                fmap[m.group(1)] = name
    return fmap


def _table_records(text: str) -> list[dict]:
    """Caption-scoped parse: a concentration caption ("customers representing 10% of
    total revenues" / "accounts receivable from individual customers") opens a window in
    which company-or-coded rows with a >=10% cell become records, tagged with that
    caption's denominator. Named-company rows are also picked up outside a caption when
    customer context is adjacent. Percent cells may be split ("12.0 | %")."""
    lines = text.split("\n")
    fmap = _footnote_map(lines)
    out: list[dict] = []
    mode: Optional[str] = None   # denominator opened by the current caption
    window = 0                   # rows remaining in the caption's scope
    for i, ln in enumerate(lines):
        if _CONC_CAPTION.search(ln):
            mode = "accounts receivable" if _AR_CAPTION.search(ln) else "revenue"
            window = 8
        if "|" not in ln or _ANTI.search(ln):
            continue
        label = ln.split("|")[0].strip(" .:;")
        in_table = mode is not None and window > 0
        if in_table:
            window -= 1
        # a caption/sentence row, not a customer row
        if len(label) > 40 or _CONC_CAPTION.search(label):
            continue
        big = [p for p in (float(x) for x in _PCT.findall(ln)) if 10.0 <= p < 100.0]
        if not big:
            continue
        named = bool(_COMPANY.search(label))
        coded = bool(_CODE_LABEL.match(label))
        ctx = " ".join(lines[max(0, i - 5):i + 1])
        if _ANTI.search(ctx):
            continue
        # accept the row only as a genuine customer row: inside a concentration table,
        # or a named-company / coded ("Customer A") row with customer context adjacent
        if not (in_table or ((named or coded) and _CUST_CTX.search(ctx))):
            continue
        if _METRIC_LABEL.search(label) and not (named or coded):
            continue
        # resolve a footnote ONLY for a generic code label (never override a named company)
        ent = label
        if not named:
            fm = re.search(r"\(\s*(\d+)\s*\)", label)
            if fm and fm.group(1) in fmap:
                ent = fmap[fm.group(1)]
        ent = re.sub(r"\s*\(\s*\d+\s*\)\s*", " ", ent).strip(" .,:;")
        denom = mode if in_table else _denominator(ctx)
        out.append({"entity": ent or "a customer", "pct": max(big),
                    "denominator": denom, "source": "table"})
    return out


def _qualitative_record(text: str) -> Optional[dict]:
    for rx in (_QUAL, _QUAL2):
        for m in rx.finditer(text):
            pre = text[max(0, m.start() - 32):m.start()]
            if _QUAL_NEG.search(pre):
                continue
            name = None
            if rx is _QUAL and m.lastindex and m.group(1):
                raw = re.sub(r"\s+", " ", m.group(1)).strip(" .,:;")
                # bound a runaway capture ("Apple Inc. Our agreements") to the suffix
                ms = re.match(r"(.*?\b(?:Inc|Corp|Corporation|Ltd|LLC|L\.?P|Company)\b\.?)", raw, re.I)
                name = (ms.group(1) if ms else " ".join(raw.split()[:3])).strip(" .,:;")
                if name and not _COMPANY.search(name) and len(name.split()) > 4:
                    name = None
            return {"entity": name or "a single customer", "pct": None,
                    "denominator": _denominator(text[m.start():m.start() + 120]),
                    "source": "qualitative"}
    return None


def extract_concentration_records(text: str) -> list[dict]:
    """All concentration records (table + qualitative) from a bs4-flattened filing text.
    De-dups by (entity-lowercased, source). Pure function — no I/O."""
    recs = _table_records(text)
    q = _qualitative_record(text)
    if q:
        recs.append(q)
    # prefer a revenue record over an accounts-receivable one for the same entity
    recs.sort(key=lambda r: "receivable" in (r["denominator"] or ""))
    seen, out = set(), []
    for r in recs:
        key = (r["entity"].lower(), r["source"])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out
