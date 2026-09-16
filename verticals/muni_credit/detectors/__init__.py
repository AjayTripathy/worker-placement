"""Predictive detector library for hospital muni credit.

Each detector is a narrow high-precision exclusion filter, composed via UNION
into an exclusion screen. Per the cross-vertical detector composition memory:
detectors should fire on 2-15% of universe with >70% precision; portfolio is
universe MINUS the union of detector fires.

Design notes:
  - Each detector exposes evaluate(obligor_name, data) → {"fires": bool, "evidence": dict}
  - Detectors should NOT try to predict every name; they should fire rarely with
    high confidence when their specific pattern is present
  - Confirmed-distress detectors (forbearance, payment delinquency) are excluded
    from this library — those are mostly priced in. This library is predictive.
"""
