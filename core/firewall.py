"""Subagent-firewall scoring primitives, vertical-agnostic.

The "firewall" is the blinding discipline: a cohort item is scored (signal fires
or it doesn't) with the realized outcome held out, and the outcome is revealed
only at confusion-matrix time. That discipline is a convention enforced per
vertical (public_co hides outcomes in _<cohort>_outcomes.py modules; muni keeps
the 2024-25 outcomes out of the 2016-19 blind universe). What is genuinely
shared — and what lived as parallel reimplementations in public_co's
blinded_manual.confusion_matrix_print and muni's blind_oos_analyzer
.compute_confusion — is the scoring math you run once the wall comes down.

`confusion_matrix` is that shared scorer. It is pure and deterministic, and its
arithmetic matches the prior muni implementation exactly (max(1, denom) guards,
f1 with a 1e-9 guard, majority-baseline lift) so existing outputs stay
byte-identical.

Scope discipline (see rigor/ ledger + the 2026-05-29 audit): do NOT wire this
into verticals that structurally cannot run a blinded cohort — buyside_dd is
single-deal forensic, carbon_offsets is outcome-less. Forcing a confusion
matrix there would manufacture the exact grand-abstraction overclaim the audit
flagged.

Consumers: public_co blinded cohort scoring; muni_credit blind-OOS analyzer.
"""
from __future__ import annotations

from collections.abc import Iterable


def confusion_matrix(observations: Iterable[tuple[bool | None, bool | None]]) -> dict:
    """Score (predicted, actual) boolean pairs into a confusion matrix + metrics.

    Each observation is `(predicted, actual)`. If either side is None the item is
    unknown/unevaluable and skipped (counted in `n_unknown`). Returns counts plus
    precision, recall, specificity, f1, accuracy, the deterioration base rate, the
    majority-class baseline accuracy, and lift over that baseline.

    Denominator guards use `max(1, denom)`; since the numerator is 0 whenever the
    denominator is 0 (e.g. precision's tp is 0 when tp+fp is 0), this returns 0.0
    in those degenerate cases, matching the prior per-vertical implementations.
    """
    tp = fp = tn = fn = unknown = 0
    for predicted, actual in observations:
        if predicted is None or actual is None:
            unknown += 1
            continue
        if predicted and actual:
            tp += 1
        elif predicted:
            fp += 1
        elif actual:
            fn += 1
        else:
            tn += 1

    n_eval = tp + fp + tn + fn
    base_rate = (tp + fn) / max(1, n_eval)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    specificity = tn / max(1, tn + fp)
    accuracy = (tp + tn) / max(1, n_eval)
    baseline = max(base_rate, 1 - base_rate)
    return {
        "n_evaluable": n_eval,
        "n_unknown": unknown,
        "confusion": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        "base_rate": base_rate,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": 2 * precision * recall / max(1e-9, precision + recall),
        "accuracy": accuracy,
        "baseline_majority_accuracy": baseline,
        "lift_over_baseline_acc": accuracy - baseline,
    }
