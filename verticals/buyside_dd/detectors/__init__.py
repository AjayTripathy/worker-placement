"""Buyside DD detectors — encoded operator-quality / claim-quality detectors
for due diligence on companies (vs muni issuers).

Each detector follows the cross-vertical convention:
  evaluate(obligor_name, data) -> {"fires": bool, "reason": str, "severity": str, "evidence": dict}

INSUFFICIENT_DATA on missing input. UNVERIFIABLE sentinel handled.
"""
