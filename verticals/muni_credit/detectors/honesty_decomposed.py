"""R/f/M honesty signal decomposed into 3 narrow detectors.

Instead of a single SUSPECT-tier composite (which has low recall), use each
honesty check as a standalone narrow detector. Each fires on a small subset
of obligors with high precision.

Three decomposed detectors:
  1. rating_action_omission — MD&A doesn't acknowledge ANY rating agency activity
  2. operating_margin_obscured — MD&A doesn't explicitly disclose operating margin %
  3. same_facility_framing_heavy — same-facility density above threshold

These are computed by the rfm_honesty_screener; this module wraps them as
binary detectors firing only on extreme low scores per check.
"""
from __future__ import annotations


def rating_action_omission_evaluate(obligor_name: str, data: dict) -> dict:
    """Fires when rating_action_acknowledgment score < 25 (essentially no mention)."""
    score = data.get("rating_action_acknowledgment_score")
    if score is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}
    if score < 25:
        return {
            "fires": True,
            "reason": "MDA_OMITS_RATING_ACTIVITY",
            "severity": "MEDIUM",
            "evidence": {"score": score, "threshold": 25},
        }
    return {"fires": False, "reason": "ACKNOWLEDGED", "evidence": {"score": score}}


def operating_margin_obscured_evaluate(obligor_name: str, data: dict) -> dict:
    """Fires when operating_margin_disclosure score < 25 (margin never disclosed explicitly)."""
    score = data.get("operating_margin_disclosure_score")
    if score is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}
    if score < 25:
        return {
            "fires": True,
            "reason": "OPERATING_MARGIN_NOT_DISCLOSED",
            "severity": "MEDIUM",
            "evidence": {"score": score, "threshold": 25},
        }
    return {"fires": False, "reason": "DISCLOSED", "evidence": {"score": score}}


def same_facility_framing_heavy_evaluate(obligor_name: str, data: dict) -> dict:
    """Fires when same-facility framing density > 5 per 1000 words."""
    density = data.get("same_facility_density_per_1000")
    if density is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}
    if density > 5:
        return {
            "fires": True,
            "reason": "HEAVY_SAME_FACILITY_FRAMING",
            "severity": "MEDIUM",
            "evidence": {"density_per_1000_words": density, "threshold": 5},
        }
    return {"fires": False, "reason": "NORMAL_FRAMING", "evidence": {"density_per_1000_words": density}}


# Module interface — each function returns evaluate() signature
class RatingActionOmission:
    @staticmethod
    def evaluate(obligor_name, data):
        return rating_action_omission_evaluate(obligor_name, data)


class OperatingMarginObscured:
    @staticmethod
    def evaluate(obligor_name, data):
        return operating_margin_obscured_evaluate(obligor_name, data)


class SameFacilityFramingHeavy:
    @staticmethod
    def evaluate(obligor_name, data):
        return same_facility_framing_heavy_evaluate(obligor_name, data)
