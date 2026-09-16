"""Cross-claim consistency checker.

The R/f/M model checks each claim against external M sources. But sometimes the
deal materials *internally* contradict themselves — the same fact is asserted
with different values in two different documents (or two pages of the same doc).

This module finds those cases and emits a Finding for each (subject, predicate)
pair where two or more claims have meaningfully different values. The Finding
needs no external M — the divergence comes from the materials themselves.

Example caught: "Factory 1 capacity 1,000 homes/yr" (pitch p.25) vs "Factory 1:
1,750 Townhomes" (financial model Block 1) — both about the same predicate
on the same subject, 75% apart.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable

from .schemas import (
    Claim, Finding, ReferentType, Severity, StopReason, TypedClaim, Materiality,
)


def _normalize_subject(s: str) -> str:
    """Conservative normalization to detect 'same subject' across docs."""
    return " ".join(s.lower().strip().split())


# Scope keys that, if present, define a sub-context for grouping. Two claims
# about the same subject+predicate but different city/year/round are NOT a
# contradiction — they're separate facts. Only flag a divergence when the
# scope-discriminator is identical.
SCOPE_DISCRIMINATORS = (
    "city", "state", "zip", "address",
    "year", "time_period", "period", "as_of", "date",
    "lead", "round", "round_name", "investor",
    "factory", "site", "project",
    # Stage 1.5 entity-resolution provenance: children decomposed from
    # DIFFERENT parent claims are about different source facts (e.g. a 15M SAFE
    # vs a 50M SAFE), not a self-contradiction. Same parent → still comparable.
    "resolved_from",
)


def _scope_signature(scope: dict) -> str:
    """Build a stable string from the scope-discriminator subset of `scope`."""
    if not scope:
        return ""
    parts = []
    for k in SCOPE_DISCRIMINATORS:
        if k in scope and scope[k] is not None:
            parts.append(f"{k}={str(scope[k]).lower().strip()}")
    return "|".join(sorted(parts))


# A "value-like" number is the measurement in a row, as opposed to a small
# ordinal that is part of a row LABEL ("Factory 1", "Block 2"). It is one that
# is preceded by '$', has ≥3 digits, carries a decimal/comma, or is followed by
# a magnitude/unit. Everything BEFORE the first value-like number is the row
# label — e.g. "Factory 2", "Below Base", "Bull Case FY31".
_VALUE_LIKE_RE = (
    r"\$\s*\d"                                              # $720, $ 1.39
    r"|\b\d{3,}"                                            # 250000, 1750
    r"|\b\d+[.,]\d"                                         # 1.39, 2,500
    r"|\b\d+\s*(?:[MBmb]\b|million|billion|%|x\b|"          # 50M, 30%, 2.4x
    r"sqft|sq\s?ft|homes|units|townhomes|/yr|per\s+year)"   # 1,000 homes/yr
)


def _quote_scope_tokens(quote: str | None) -> str:
    """Derive extra scope discriminators from a claim's source_quote.

    The dominant false-positive in LLM-extracted claims is a comparison TABLE or
    SCENARIO MATRIX collapsing onto one (subject, predicate): two factories, or
    bear/base/bull projections, read as a single fact stated with conflicting
    values. The fix is the row LABEL — the text before the first value-like
    number ("Factory 2", "Below Base") — folded into the grouping key so each
    row/scenario lands in its own bucket. 4-digit years are added too so
    per-year projections separate.

    Limitation: a genuine cross-document contradiction about the SAME quantity
    stated with DIFFERENT lead-in prose will also separate and be missed here.
    That recall gap needs semantic (not lexical) subject matching; this check
    is deliberately precision-first per the honesty-validator priority.
    """
    if not quote:
        return ""
    import re
    parts = []
    m = re.search(_VALUE_LIKE_RE, quote)
    head = quote[: m.start()] if m else quote
    label = " ".join(head.lower().split())[:48].strip(" \t:|-")
    if label:
        parts.append(f"row={label}")
    for yr in sorted(set(re.findall(r"\b(?:19|20)\d{2}\b", quote))):
        parts.append(f"yr={yr}")
    return "|".join(parts)


def _is_contained(a: str, b: str) -> bool:
    """True if one normalized string is a substring of the other (e.g.
    'Contrary' ⊆ 'Contrary Capital'). Such pairs are the same entity stated
    at different specificity, not a genuine clash."""
    na, nb = a.lower().strip(), b.lower().strip()
    if not na or not nb:
        return False
    return na in nb or nb in na


def _try_numeric(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        # Attempt to parse '$1,750' / '40 units' / '1750' style values
        import re
        m = re.search(r"-?\d+(?:[\d,]*\.?\d*)?", v.replace(",", ""))
        if m:
            try:
                return float(m.group(0).replace(",", ""))
            except ValueError:
                return None
    return None


def find_internal_divergences(typed_claims: Iterable[TypedClaim]) -> list[Finding]:
    """Group claims by (normalized_subject, predicate) and emit a Finding for
    each group whose numeric values diverge by ≥5%.

    Non-numeric value clashes (e.g. two different lead investors for the same
    round) are also surfaced as MODERATE findings.
    """
    # Predicates that are inherently multi-valued (one entity surfaces in many
    # places). These should NOT enter the cross-claim consistency check —
    # finding 9 LinkedIn URLs about the same company isn't a contradiction.
    MULTI_VALUED_PREDICATE_PREFIXES = (
        "surfaced_in_",       # Tier 1 web discovery: one URL per result
        "related_entity_",    # Tier 1: many related entities are normal
    )
    # Exact predicates where one subject legitimately holds many distinct values
    # — a serial founder founds several companies; an acquirer makes several
    # acquisitions. Different values are not a self-contradiction.
    MULTI_VALUED_PREDICATE_EXACT = frozenset({
        "founded_company",
        "previously_acquired",
        "previously_founded",
        "board_member_of",
        "advisor_to",
        "invested_in",
    })

    # Key includes scope-discriminator so claims about different rounds, cities,
    # or projects don't collide as a "same fact, different value" contradiction.
    by_key: dict[tuple[str, str, str], list[TypedClaim]] = defaultdict(list)
    for tc in typed_claims:
        if any(tc.claim.predicate.startswith(p) for p in MULTI_VALUED_PREDICATE_PREFIXES):
            continue
        if tc.claim.predicate in MULTI_VALUED_PREDICATE_EXACT:
            continue
        # B2: fold scenario/year tokens parsed from the source_quote into the
        # scope signature so Bear/Base/Bull projections (and per-year or
        # per-tranche values) sit in separate buckets instead of colliding.
        scope_sig = _scope_signature(tc.claim.scope)
        quote_sig = _quote_scope_tokens(tc.claim.source_quote)
        full_sig = "|".join(p for p in (scope_sig, quote_sig) if p)
        key = (_normalize_subject(tc.claim.subject), tc.claim.predicate, full_sig)
        by_key[key].append(tc)

    findings: list[Finding] = []
    for (subj, pred, scope_sig), claims in by_key.items():
        if len(claims) < 2:
            continue

        numeric_values: list[tuple[TypedClaim, float]] = []
        string_values: list[tuple[TypedClaim, str]] = []
        for c in claims:
            n = _try_numeric(c.claim.object_value)
            if n is not None:
                numeric_values.append((c, n))
            elif isinstance(c.claim.object_value, str) and c.claim.object_value:
                string_values.append((c, c.claim.object_value.strip()))

        # B1: dedupe numeric values that share a source_quote. Two numbers
        # pulled from the SAME sentence ("$2.5M–$5M", "5-10 rowhomes") are the
        # endpoints of one range, not two documents disagreeing. Keep only one
        # representative per distinct source_quote before testing divergence.
        if len(numeric_values) >= 2:
            seen_quotes: set[str] = set()
            deduped: list[tuple[TypedClaim, float]] = []
            for c, n in numeric_values:
                q = (c.claim.source_quote or "").strip().lower()
                if q and q in seen_quotes:
                    continue
                if q:
                    seen_quotes.add(q)
                deduped.append((c, n))
            numeric_values = deduped

        # Numeric divergence
        if len(numeric_values) >= 2:
            vals = [v for _, v in numeric_values]
            v_min, v_max = min(vals), max(vals)
            if v_min == 0:
                divergence_pct = float("inf") if v_max != 0 else 0.0
            else:
                divergence_pct = abs(v_max - v_min) / abs(v_min)
            if divergence_pct >= 0.05:
                # Severity scaled to magnitude of divergence
                if divergence_pct >= 0.50:
                    sev = Severity.SEVERE
                elif divergence_pct >= 0.20:
                    sev = Severity.MODERATE
                elif divergence_pct >= 0.10:
                    sev = Severity.MINOR
                else:
                    sev = Severity.MINOR
                quotes = [
                    f"  - {c.claim.source_quote[:120]} → {n}"
                    for c, n in numeric_values
                ]
                findings.append(Finding(
                    claim=numeric_values[0][0].claim,
                    referent_type=numeric_values[0][0].referent_type,
                    referent_id=numeric_values[0][0].referent_id or numeric_values[0][0].claim.subject,
                    f_rule_id="re.internal_consistency_numeric",
                    expected_value=v_min,
                    divergence_absolute=v_max - v_min,
                    divergence_pct=divergence_pct,
                    severity=sev,
                    confidence=1.0,  # internal check is high-confidence
                    stop_reason=StopReason.CONVERGED,
                    materiality_at_stop=numeric_values[0][0].claim.materiality,
                    evidence_trail=[
                        f"INTERNAL DIVERGENCE on ({subj}, {pred}, scope={scope_sig or 'none'})",
                        f"min={v_min}, max={v_max}, divergence={divergence_pct*100:.1f}%",
                    ] + quotes,
                    notes=f"{len(numeric_values)} conflicting numeric claims about same (subject, predicate)",
                    exposure_estimate_usd=None,  # caller should compute from materiality
                ))

        # String value clash (e.g. two different leads for the same round)
        if len(string_values) >= 2:
            distinct = {v for _, v in string_values}
            # B3: drop pairs where one value contains the other ('Contrary' ⊆
            # 'Contrary Capital') — same entity at different specificity, not a
            # clash. A clash survives only if at least two values are mutually
            # non-containing.
            distinct_list = sorted(distinct)
            real_clash = any(
                not _is_contained(a, b)
                for i, a in enumerate(distinct_list)
                for b in distinct_list[i + 1:]
            )
            if len(distinct) > 1 and real_clash:
                quotes = [
                    f"  - {c.claim.source_quote[:120]} → {v!r}"
                    for c, v in string_values
                ]
                findings.append(Finding(
                    claim=string_values[0][0].claim,
                    referent_type=string_values[0][0].referent_type,
                    referent_id=string_values[0][0].referent_id or string_values[0][0].claim.subject,
                    f_rule_id="re.internal_consistency_string",
                    severity=Severity.MODERATE,
                    confidence=1.0,
                    stop_reason=StopReason.CONVERGED,
                    materiality_at_stop=string_values[0][0].claim.materiality,
                    evidence_trail=[
                        f"INTERNAL DIVERGENCE on ({subj}, {pred}, scope={scope_sig or 'none'})",
                        f"{len(distinct)} distinct values: {sorted(distinct)}",
                    ] + quotes,
                    notes=f"Multiple distinct string values claimed for same (subject, predicate)",
                ))

    return findings
