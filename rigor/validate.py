"""Rigor linter: enforce truth-in-labeling on claim documents.

The standard SignalOS keeps uniform is NOT uniform rigor (impossible across a
single-deal forensic DD and a held-out equities cohort) but uniform *labeling*:
a claim word may only be as strong as the evidence behind it.

## Contract

`vocabulary.json` defines an ordered tier ladder and the claim phrases that
require each tier:

    demonstrated < discriminated < validated < predictive

`ledger.json` records, per vertical, the `ceiling` tier its apparatus actually
earns. This linter walks the claim docs and flags any enforced phrase whose
required tier exceeds the doc's ceiling.

  - Doc under `verticals/<name>/...`  -> checked against that vertical's ceiling.
      A phrase above ceiling = VIOLATION (exit 1).
  - Global doc (ARCHITECTURE.md, TECH_DEBT.md, README.md) -> no single ceiling.
      An enforced phrase is REVIEW (soft) unless it carries an attribution tag
      `<!-- rigor: vertical=<name> -->`, in which case it is resolved against
      that vertical's ceiling and may become a VIOLATION.

Suppress a legitimate use with an inline `<!-- rigor-ok: <reason> -->` on the
same line.

## What this deliberately does NOT catch (honest limits)

  - Within-vertical, per-claim overclaims. public_co's ceiling is `validated`,
    so a basket-`alpha` claim there is enforced (alpha is tier `predictive`),
    but a doc could still over-strong a borderline finding under its ceiling.
    Per-claim tiering is a v2.
  - The topical words `alpha` / `predictive` are advisory-only (this is a quant
    repo; they appear as subjects constantly). Only achievement phrasings like
    "generates alpha" / "beats the benchmark" are enforced.

Run: `python3 rigor/validate.py [--strict]`  (exit 1 on any VIOLATION)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RIGOR = Path(__file__).resolve().parent

# Claim-doc surfaces. Vertical docs live under verticals/<name>/...; globals are repo-root narrative.
VERTICAL_DOC_PATTERNS = ["*FINDINGS*.md", "*RESULTS*.md", "*PREDICTIONS*.md",
                         "*methodology*.md", "*METHODOLOGY*.md", "*DEPLOYMENT*.md"]
GLOBAL_DOCS = ["ARCHITECTURE.md", "TECH_DEBT.md", "README.md"]

ATTR_RE = re.compile(r"<!--\s*rigor:\s*vertical=([a-z_]+)\s*-->", re.IGNORECASE)

# Negation cues: "not validated" / "n't validated" / "absence of validation" are
# meta-discussion, not claims. If one sits just before the match, don't flag.
NEG_CUES = (" not ", "n't ", " without ", " lack", " absence", " never ", " no ", " yet to ")
# Methodology / audit docs are meta-discussion ABOUT rigor; they legitimately use
# tier vocabulary. Downgrade them to REVIEW rather than VIOLATION.
META_TOKENS = ("methodology", "audit")


def load():
    vocab = json.loads((RIGOR / "vocabulary.json").read_text())
    ledger = json.loads((RIGOR / "ledger.json").read_text())["verticals"]
    order = vocab["tier_order"]
    tidx = {name: i for i, name in enumerate(order)}
    enforced = []  # (tier_name, tier_idx, compiled_regex)
    for tier, patterns in vocab["enforced_phrases"].items():
        for pat in patterns:
            enforced.append((tier, tidx[tier], re.compile(pat, re.IGNORECASE)))
    return vocab, ledger, tidx, enforced


def claim_docs():
    docs = []
    vroot = ROOT / "verticals"
    for pat in VERTICAL_DOC_PATTERNS:
        docs += [p for p in vroot.rglob(pat) if p.is_file()]
    for g in GLOBAL_DOCS:
        p = ROOT / g
        if p.is_file():
            docs.append(p)
    return sorted(set(docs))


def vertical_of(path: Path) -> str | None:
    rel = path.relative_to(ROOT).parts
    if rel and rel[0] == "verticals" and len(rel) > 1:
        return rel[1]
    return None


def scan(path, vocab, ledger, tidx, enforced):
    """Yield (severity, tier, lineno, vertical_ctx, snippet)."""
    supp = vocab["suppression_marker"]
    text = path.read_text(errors="ignore").splitlines()
    doc_vertical = vertical_of(path)
    is_meta = any(t in path.name.lower() for t in META_TOKENS)
    for i, line in enumerate(text, 1):
        if supp in line:
            continue
        low = line.lower()
        for tier, ti, rx in enforced:
            m = rx.search(line)
            if not m:
                continue
            pre = low[max(0, m.start() - 30):m.start()]
            if any(cue in pre for cue in NEG_CUES):
                continue  # negated / meta-discussion of the word, not a claim
            attr = ATTR_RE.search(line)
            ctx = doc_vertical or (attr.group(1) if attr else None)
            snippet = line.strip()[:120]
            # Enforce (VIOLATION) only on claim-OUTPUT docs of a vertical.
            # Methodology/audit docs and global narrative are REVIEW-only.
            if ctx and ctx in ledger and not is_meta and doc_vertical:
                ceiling = ledger[ctx]["ceiling"]
                if ti > tidx[ceiling]:
                    yield ("VIOLATION", tier, i, f"{ctx} (ceiling={ceiling})", snippet)
            elif ctx and ctx in ledger:  # meta doc or attributed global
                ceiling = ledger[ctx]["ceiling"]
                if ti > tidx[ceiling]:
                    yield ("REVIEW", tier, i, f"{ctx} meta/global (ceiling={ceiling})", snippet)
            elif doc_vertical is None:
                yield ("REVIEW", tier, i, "GLOBAL/unattributed", snippet)


def main():
    strict = "--strict" in sys.argv
    vocab, ledger, tidx, enforced = load()
    violations = reviews = 0
    for path in claim_docs():
        findings = list(scan(path, vocab, ledger, tidx, enforced))
        if not findings:
            continue
        print(f"\n{path.relative_to(ROOT)}")
        for sev, tier, ln, ctx, snip in findings:
            mark = "x" if sev == "VIOLATION" else "?"
            print(f"  [{mark}] {sev:9} L{ln:<4} '{tier}' word | {ctx}\n        {snip!r}")
            if sev == "VIOLATION":
                violations += 1
            else:
                reviews += 1
    print(f"\n--- rigor: {violations} VIOLATION, {reviews} REVIEW across "
          f"{len(ledger)} verticals ---")
    if violations or (strict and reviews):
        sys.exit(1)


if __name__ == "__main__":
    main()
