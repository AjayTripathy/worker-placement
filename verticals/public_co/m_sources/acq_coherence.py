"""
Acquisition technology-coherence scorer.

WHY THIS EXISTS
The IONQ short thesis hinges on the rollup tell: a "quantum computing"
parent acquiring SAR satellites (Capella), atomic clocks (Vector
Atomics), QKD (IDQ), and a semiconductor foundry (SKYT). Each
acquisition individually has some business rationale; the cluster is
incoherent with the parent's stated technology thesis. When a parent
loses its core revenue stream and immediately starts rolling up
unrelated businesses to maintain headline growth, that's a high-signal
fraud-pattern flag.

usaspending and pentagon_jbook detect customer disappearance; this
detects the management response (rollup of incoherent businesses to
backfill the gap and distract investors).

WHAT THIS DOES
For each named acquisition by the parent (typically surfaced via
sec_filings.list_filings_by_form on 8-K Item 2.01), the connector
asks the configured intelligence provider to score "does the acquired entity's stated technology
cohere with the parent's claimed core thesis?" A 0-1 score per
acquisition; aggregate signal across all acquisitions in a window.

USAGE
The planner should pass:
  - parent_thesis: 1-2 sentences from the parent's S-1/10-K Item 1
    (Business) describing the core technology / business
  - acquisitions: list of {acquired_name, target_business, deal_value_usd,
    announcement_date} from 8-K Item 2.01 mining

The connector returns per-acquisition coherence scores + an aggregate
"rollup distraction" signal:

  COHERENT_ROLLUP      — all acquisitions score >=0.7 (related M&A)
  MIXED_COHERENCE      — some related, some not
  INCOHERENT_ROLLUP    — most score <0.5 (canonical IONQ tell)
  NO_ACQUISITIONS      — no acquisitions in window

INPUTS WHEN LLM UNAVAILABLE
If no configured model SDK / key is available, returns
signal=LLM_UNAVAILABLE so downstream knows to treat as UNVERIFIABLE
rather than producing a false signal.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["serial_acquisition_rollup"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Scores technology-coherence of an acquisition cluster; incoherent rollups after core-revenue loss are the fraud-pattern flag (IONQ tell).",
}

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional


_SCHEMA = {"type": "object", "properties": {
    "coherence_score": {"type": "number", "minimum": 0, "maximum": 1},
    "category": {"type": "string"}, "reasoning": {"type": "string"},
    "is_revenue_synthetic": {"type": "boolean"}},
    "required": ["coherence_score", "category", "reasoning", "is_revenue_synthetic"],
    "additionalProperties": False}


_SYSTEM_PROMPT = """You are scoring technology coherence between a parent company's stated core thesis and a recent acquisition target.

A high-coherence acquisition (score 0.7-1.0) extends or vertically integrates the parent's core technology. Example: a quantum-computing parent acquiring a quantum-error-correction startup, or a satellite operator acquiring a ground-station network. Both extend the same technology vertical.

A medium-coherence acquisition (0.4-0.6) is adjacent but distinct. Example: a satellite-imaging company buying an analytics-software firm — related market, different technology stack.

A low-coherence acquisition (0.0-0.3) is unrelated to the parent's stated thesis. Example: a "quantum computing" company buying a SAR satellite operator, an atomic-clock maker, or a semiconductor foundry — all use quantum-physics-adjacent concepts but none are quantum computing. Or, more bluntly: a quantum-computing company buying a real-estate REIT.

CRITICAL: classify on TECHNOLOGY COHERENCE, not on financial logic. An acquisition might make excellent financial sense (cash-generating target, accretive multiple) while being technology-incoherent. A pattern of low-coherence acquisitions following a revenue shock is a classic "rollup distraction" tell.

Output strict JSON only, no other text:
{
  "coherence_score": 0.0-1.0,
  "category": "high_coherence" | "medium_coherence" | "low_coherence",
  "reasoning": "one-sentence justification focused on technology alignment vs the parent's stated thesis",
  "is_revenue_synthetic": true | false
}

is_revenue_synthetic = true when the acquisition's primary effect is to add headline revenue from a business unrelated to the parent's stated technology thesis (the canonical rollup-distraction tell)."""


def _parse_llm_json(response: str):
    """Strip markdown fences + extract JSON."""
    t = (response or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json|JSON)?\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def _score_one_acquisition(parent_thesis: str, acq: dict, *, client, model) -> dict:
    """LLM-score one acquisition. Returns {coherence_score, category, reasoning,
    is_revenue_synthetic, error}."""
    user = (f"PARENT THESIS (from parent's 10-K Item 1 or S-1):\n"
            f"{parent_thesis}\n\n"
            f"ACQUISITION:\n"
            f"- Target: {acq.get('acquired_name','(unknown)')}\n"
            f"- Target business: {acq.get('target_business','(no description provided)')}\n"
            f"- Deal value: {acq.get('deal_value_usd', '(not specified)')}\n"
            f"- Announcement date: {acq.get('announcement_date','(not specified)')}\n\n"
            f"Score per the schema.")

    try:
        from officekit_ai.intelligence import generate
        resp = generate(client, model=model, max_tokens=4000, system=_SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": user}],
                        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}})
        if resp.stop_reason == "max_tokens":
            raise ValueError("Acquisition score was truncated")
        result = _parse_llm_json("".join(b.text for b in resp.content if b.type == "text"))
        score = result["coherence_score"]
        if type(score) not in {int, float} or not 0 <= score <= 1 or type(result["is_revenue_synthetic"]) is not bool:
            raise ValueError("Invalid acquisition score")
        return {"coherence_score": float(score), "category": result["category"],
                "reasoning": result["reasoning"][:400], "is_revenue_synthetic": result["is_revenue_synthetic"]}
    except Exception as exc:
        return {"error": "Intelligence call failed: " + type(exc).__name__}


def score_acquisition_coherence(
    parent_thesis: str,
    acquisitions: list[dict],
    cutoff_date: Optional[str] = None,
    *, client=None, model=None, folder=None,
) -> dict[str, Any]:
    """Score the technology coherence of a parent's recent acquisitions.

    Args:
      parent_thesis: 1-2 sentence description of the parent's core technology
                     / business thesis (typically from 10-K Item 1 or S-1)
      acquisitions: list of dicts with keys:
                    acquired_name, target_business, deal_value_usd (optional),
                    announcement_date (optional)
      cutoff_date:  optional ISO date; only score acquisitions with
                    announcement_date <= cutoff_date

    Returns:
      {
        "parent_thesis":              echo,
        "n_acquisitions_scored":      int,
        "per_acquisition":            list of {acq + coherence_score, category, reasoning},
        "mean_coherence":             float (0-1),
        "n_low_coherence":            int (count with score < 0.5),
        "n_revenue_synthetic":        int (count flagged as rollup-distraction),
        "total_low_coherence_value":  float (sum of deal_value_usd for low-coherence),
        "signal":                     COHERENT_ROLLUP | MIXED_COHERENCE |
                                       INCOHERENT_ROLLUP | NO_ACQUISITIONS |
                                       LLM_UNAVAILABLE,
        "llm_model":                  model name if used,
        "cutoff_date":                echo,
      }
    """
    # Filter by cutoff_date
    if cutoff_date:
        cd = str(cutoff_date)[:10]
        filtered = [a for a in (acquisitions or [])
                    if not a.get("announcement_date")
                    or str(a.get("announcement_date"))[:10] <= cd]
    else:
        filtered = list(acquisitions or [])

    if not filtered:
        return {
            "parent_thesis":             parent_thesis[:300],
            "n_acquisitions_scored":     0,
            "per_acquisition":           [],
            "mean_coherence":            None,
            "n_low_coherence":           0,
            "n_revenue_synthetic":       0,
            "total_low_coherence_value": 0.0,
            "signal":                    "NO_ACQUISITIONS",
            "status":                    "complete",
            "llm_model":                 None,
            "cutoff_date":               cutoff_date,
        }

    try:
        from officekit_ai.models import client_for
        if client is None:
            client, configured = client_for("intake", folder)
            model = model or os.environ.get("ACQ_COHERENCE_MODEL") or configured
        if not model:
            raise ValueError("Injected intelligence needs a model identity")
    except (RuntimeError, ValueError) as exc:
        return {"error": "Intelligence unavailable: " + type(exc).__name__, "status": "error",
                "signal": "LLM_UNAVAILABLE", "n_acquisitions_scored": 0, "per_acquisition": []}

    scored: list[dict] = []
    n_low = 0
    n_synth = 0
    low_value = 0.0
    sum_coherence = 0.0
    n_ok = 0
    for acq in filtered:
        r = _score_one_acquisition(parent_thesis, acq, client=client, model=model)
        if "error" in r:
            scored.append({**acq, "error": r["error"]})
            continue
        n_ok += 1
        sum_coherence += r["coherence_score"]
        if r["coherence_score"] < 0.5:
            n_low += 1
            if acq.get("deal_value_usd"):
                try:
                    low_value += float(acq["deal_value_usd"])
                except (TypeError, ValueError):
                    pass
        if r["is_revenue_synthetic"]:
            n_synth += 1
        scored.append({**acq, **r})

    mean_coh = (sum_coherence / n_ok) if n_ok else None

    # Signal
    if n_ok == 0:
        signal = "LLM_UNAVAILABLE"
    elif n_low >= max(2, n_ok // 2):  # >=50% low-coherence AND >=2 absolute
        signal = "INCOHERENT_ROLLUP"
    elif n_low >= 1:
        signal = "MIXED_COHERENCE"
    else:
        signal = "COHERENT_ROLLUP"

    return {
        "status":                    "error" if not n_ok else "partial" if n_ok < len(filtered) else "complete",
        "n_acquisitions_attempted":   len(filtered),
        "n_acquisitions_failed":      len(filtered) - n_ok,
        "parent_thesis":             parent_thesis[:300],
        "n_acquisitions_scored":     n_ok,
        "per_acquisition":           scored,
        "mean_coherence":            mean_coh,
        "n_low_coherence":           n_low,
        "n_revenue_synthetic":       n_synth,
        "total_low_coherence_value": low_value,
        "signal":                    signal,
        "llm_model":                 model,
        "cutoff_date":               cutoff_date,
    }


def main():
    from verticals.cli import load_json, selftest_or_input
    a = selftest_or_input("Do the issuer's acquisitions cohere with the thesis it sells?",
                          inputs=[("case", 'JSON: {"parent_thesis": str, "acquisitions": [...], "cutoff_date"?: str} '
                                           '(worked example in verticals/public_co/examples/)')])
    case = load_json(a.case)
    result = score_acquisition_coherence(case["parent_thesis"], case["acquisitions"], case.get("cutoff_date"))
    print(json.dumps(result, indent=2, default=str))
    # A partial panel is not a successful full run. Preserve successful rows,
    # but make schedulers and callers surface the missing coverage.
    return 1 if result["status"] in {"error", "partial"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
