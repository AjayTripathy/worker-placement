"""Ablation probes against the FROZEN biotech evaluator.

Neither probe overwrites a committed prediction.json. Both read the blind
predictions already on disk and report how the directional call would change
under a targeted removal — isolating the two overfit exposures flagged in
[[project_public_biotech_catalyst_backtest]].

A) disclosure_integrity OFF (SAVA). Pure recompute, no LLM: re-aggregate SAVA's
   committed findings with every disclosure_integrity finding deleted. Tests
   whether the MISS call rests SOLELY on the pre-cutoff SEC settlement, or
   whether the endpoint / evidence-quality channels carry it independently.

B) NASH-hint OFF (MDGL). Re-adjudicate MDGL's endpoint_manipulation claims with
   the MDGL-specific parenthetical stripped from discipline #4, splice the new
   endpoint findings back over the committed ones, and re-aggregate. Tests
   whether fix #3 was a general principle or teaching-to-the-test: if the HIT
   flips toward MISS once the worked example is gone, the example was load-bearing.
"""
from __future__ import annotations

import json
import sys
from collections import Counter

from .catalyst_spec import CASES, DATA_DIR
from . import evaluate as ev

# The exact MDGL-specific worked example embedded in discipline #4.
_NASH_HINT = (
    ' (e.g. "NASH resolution on liver histology" vs "liver biopsy (NASH CRN '
    'score)" — NAS/NAFLD Activity Score IS the NASH CRN scale; both describe '
    'the same biopsy co-primary)'
)


def _load_pred(ticker: str) -> dict:
    return json.loads((DATA_DIR / ticker / "prediction.json").read_text())


def _call_line(summary: dict) -> str:
    return (f"{summary['call']}  gap={summary['honesty_gap_normalized']:.3f}  "
            f"decisive={len(summary['decisive_refutes_high_precision'])}")


# ── A) disclosure_integrity OFF (SAVA) — deterministic recompute ──────────────

def ablate_integrity(case_id: str = "cassava_simufilam_p3") -> dict:
    case = CASES[case_id]
    pred = _load_pred(case.ticker)
    kept = [f for f in pred["findings"] if f["channel"] != "disclosure_integrity"]
    dropped = len(pred["findings"]) - len(kept)
    new_summary = ev._aggregate(case, kept)
    return {"baseline": pred["summary"], "ablated": new_summary,
            "dropped_findings": dropped}


# ── B) NASH-hint OFF (MDGL) — re-adjudicate endpoint channel ──────────────────

def ablate_nash_hint(case_id: str = "madrigal_resmetirom_p3", *, llm=None) -> dict:
    case = CASES[case_id]
    pred = _load_pred(case.ticker)

    stripped_prompt = ev.ADJUDICATION_PROMPT.replace(_NASH_HINT, "")
    assert stripped_prompt != ev.ADJUDICATION_PROMPT, "NASH hint text not found — prompt drifted"

    claims = json.loads((DATA_DIR / case.ticker / "claims.json").read_text())["claims"]
    by_pred: dict[str, list[dict]] = {}
    for c in claims:
        by_pred.setdefault(c["predicate"], []).append(c)

    m = ev.build_m_bundle(case, claims, verbose=False)
    rules_idx = ev.rules_by_predicate()

    # Re-run ONLY the endpoint_manipulation channel under the stripped prompt.
    new_endpoint_findings: list[dict] = []
    for pred_name, pred_claims in by_pred.items():
        for rule in rules_idx.get(pred_name, []):
            if rule.channel != "endpoint_manipulation":
                continue
            m_slice = ev._m_slice_for_rule(rule, m, case)
            m_json = json.dumps(m_slice, indent=2, default=str)[:24000]
            vmap: dict[str, dict] = {}
            for i in range(0, len(pred_claims), ev._BATCH):
                batch = pred_claims[i:i + ev._BATCH]
                claims_min = [{
                    "claim_id": c["claim_id"], "subject": c["subject"],
                    "object_value": c["object_value"],
                    "source_quote": c["source_quote"], "scope": c.get("scope", {}),
                } for c in batch]
                prompt = stripped_prompt.format(
                    rule_id=rule.rule_id, channel=rule.channel,
                    f_method=rule.f_method, refutes_if=rule.refutes_if,
                    affirms_if=rule.affirms_if, m_json=m_json,
                    claims_json=json.dumps(claims_min, indent=2, default=str),
                )
                for v in ev._parse_json_array(llm(prompt)):
                    if v.get("claim_id"):
                        vmap[v["claim_id"]] = v
            for c in pred_claims:
                v = vmap.get(c["claim_id"])
                if not v:
                    continue
                verdict = (v.get("verdict") or "UNVERIFIABLE").upper()
                sev = rule.severity_if_refuted if verdict == "REFUTED" else (
                    ev.Severity.PASS if verdict == "AFFIRMED" else ev.Severity.UNVERIFIABLE)
                new_endpoint_findings.append({
                    "claim_id": c["claim_id"], "rule_id": rule.rule_id,
                    "channel": rule.channel, "predicate": pred_name,
                    "subject": c["subject"], "R_source_quote": c["source_quote"],
                    "R_object_value": c["object_value"], "R_source_doc": c["source_doc"],
                    "f_method": rule.f_method, "m_source": rule.m_source,
                    "verdict": verdict, "severity": sev.value,
                    "rationale": v.get("rationale"), "m_evidence": v.get("m_evidence"),
                })

    spliced = [f for f in pred["findings"] if f["channel"] != "endpoint_manipulation"]
    spliced += new_endpoint_findings
    new_summary = ev._aggregate(case, spliced)
    base_ep = Counter(f["verdict"] for f in pred["findings"]
                      if f["channel"] == "endpoint_manipulation")
    new_ep = Counter(f["verdict"] for f in new_endpoint_findings)
    return {"baseline": pred["summary"], "ablated": new_summary,
            "endpoint_verdicts_baseline": dict(base_ep),
            "endpoint_verdicts_ablated": dict(new_ep),
            "new_endpoint_findings": new_endpoint_findings}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["a", "b", "both"], default="both", nargs="?")
    args = ap.parse_args()

    if args.which in ("a", "both"):
        r = ablate_integrity()
        print("=" * 72)
        print("ABLATION A — disclosure_integrity OFF (SAVA)")
        print("=" * 72)
        print(f"  baseline: {_call_line(r['baseline'])}")
        print(f"  ablated : {_call_line(r['ablated'])}   (-{r['dropped_findings']} integrity findings)")
        flip = r["baseline"]["call"] != r["ablated"]["call"]
        print(f"  CALL FLIPPED: {'YES' if flip else 'NO'}")
        if r["ablated"]["decisive_refutes_high_precision"]:
            print("  surviving decisive refutes (non-integrity):")
            for d in r["ablated"]["decisive_refutes_high_precision"]:
                print(f"    [{d['channel']}] {d['rule_id']} :: {d['R'][:90]}")
        else:
            print("  no decisive refutes survive — MISS call depended on the SEC channel")
        print()

    if args.which in ("b", "both"):
        from .extract_claims import get_llm
        llm = get_llm()
        r = ablate_nash_hint(llm=llm)
        print("=" * 72)
        print("ABLATION B — NASH-specific prompt hint OFF (MDGL)")
        print("=" * 72)
        print(f"  baseline: {_call_line(r['baseline'])}   endpoint verdicts {r['endpoint_verdicts_baseline']}")
        print(f"  ablated : {_call_line(r['ablated'])}   endpoint verdicts {r['endpoint_verdicts_ablated']}")
        flip = r["baseline"]["call"] != r["ablated"]["call"]
        print(f"  CALL FLIPPED: {'YES' if flip else 'NO'}")
        newrefs = [f for f in r["new_endpoint_findings"] if f["verdict"] == "REFUTED"]
        if newrefs:
            print(f"  endpoint REFUTES that reappeared without the hint ({len(newrefs)}):")
            for f in newrefs:
                print(f"    [{f['severity']}] {f['rule_id']} :: {f['R_source_quote'][:90]}")
                print(f"        -> {f['rationale']}")
        else:
            print("  no endpoint refutes reappeared — the general principle held without the example")
