"""News sentiment / negative-news-velocity monitor detector.

FIRES when negative news velocity for an obligor exceeds threshold over a
trailing 90-day window. This is the FASTEST public signal in the framework —
news typically precedes formal rating actions by months and material-event
filings by weeks.

Why predictive (per signal_channels.json entry google_news_local_ca):
- A district hit by a state-receiver-appointment news cycle spikes negative
  news weeks before formal CDE action (FCMAT lead-time pattern).
- A hospital with a DOJ FCA settlement / AG enforcement action gets news
  coverage immediately, before any HCRIS / EMMA / rating-agency reflection.
- An IOU under active fire investigation generates news velocity that
  precedes liability quantification by quarters (SCE post-Eaton pattern).

Caveats (per hostile-validator discipline + honesty-alpha framework memory):
- "Controversial budget discussion" is NOT the same as "fiscal distress".
- Negative news that is HONESTLY DISCLOSED (issuer announcing own layoff /
  AG settlement / strike) is already in price for sophisticated dealers; the
  detector still fires because the velocity itself is a deterioration proxy,
  but downstream consumers must consider whether market has already repriced.
- Cal-Mortgage / CSFA-intercept / GO-wrap masking mechanisms decouple
  obligor news from bond pricing — fires here may not translate to muni
  alpha for those wrapped names (cross-check with masking_mechanisms.json).

Data shape:
  {
    "obligor_name": "...",
    "trailing_12mo_article_counts": {"positive": 5, "neutral": 12, "negative": 2},
    "trailing_90d_negative_count": 3,
    "active_negative_events": ["DOJ_AG_ENFORCEMENT", "NURSES_STRIKE_OPEN_ENDED"],
    "negative_article_urls": [
      {"url": "...", "date": "2025-..", "headline": "..", "sentiment_tag": "negative"},
      ...
    ],
    "as_of_date": "2026-05-28",
    "confidence": "MEDIUM"
  }

Threshold (hostile-validator calibrated):
  Default: FIRES on 3+ negative articles in trailing 90 days
  Severity HIGH on 5+ trailing-90d negatives AND active investigation language
  Severity MEDIUM on 3-4 trailing-90d negatives OR 5+ trailing-12mo negatives
                                            without active investigation
  Severity LOW (no fire) for 1-2 trailing-90d negatives
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["all_muni"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "News sentiment / negative-news-velocity monitor detector.",
}

# Investigation language that bumps severity to HIGH when paired with elevated count
ACTIVE_INVESTIGATION_TAGS = {
    "DOJ_AG_ENFORCEMENT",
    "DOJ_INTERVENED_COMPLAINT",
    "FBI_INVESTIGATION",
    "SEC_INVESTIGATION",
    "STATE_RECEIVERSHIP",
    "FCMAT_FISCAL_DISTRESS_REVIEW",
    "NURSES_STRIKE_OPEN_ENDED",
    "ACTIVE_FIRE_INVESTIGATION",
    "TITLE_IX_LITIGATION_CLUSTER",  # >=2 active suits same district
    "CRIMINAL_INDICTMENT_PUBLIC_OFFICIAL",
}

THRESHOLD_90D_FIRE = 3
THRESHOLD_90D_HIGH = 5
THRESHOLD_12MO_FALLBACK_FIRE = 4  # backstop: sustained 12mo flow + active
                                  # investigation language qualifies even if
                                  # 90d count is low (slow-burn enforcement /
                                  # litigation-cluster cases)


def evaluate(obligor_name: str, data: dict) -> dict:
    counts_12mo = data.get("trailing_12mo_article_counts", {})
    negatives_12mo = int(counts_12mo.get("negative", 0))
    positives_12mo = int(counts_12mo.get("positive", 0))
    neutrals_12mo = int(counts_12mo.get("neutral", 0))
    total_12mo = negatives_12mo + positives_12mo + neutrals_12mo

    negatives_90d = int(data.get("trailing_90d_negative_count", 0))
    active_events = set(data.get("active_negative_events", []) or [])

    # Insufficient data: total coverage too thin to make any judgement
    if total_12mo == 0 and negatives_90d == 0 and not active_events:
        return {
            "fires": False,
            "reason": "INSUFFICIENT_DATA",
            "evidence": {"trailing_12mo_total_articles": 0},
        }

    has_active_investigation = bool(active_events & ACTIVE_INVESTIGATION_TAGS)

    # HIGH severity: elevated 90d AND active investigation language
    if negatives_90d >= THRESHOLD_90D_HIGH and has_active_investigation:
        return {
            "fires": True,
            "reason": "ELEVATED_NEGATIVE_VELOCITY_WITH_ACTIVE_INVESTIGATION",
            "severity": "HIGH",
            "evidence": {
                "trailing_90d_negative_count": negatives_90d,
                "trailing_12mo_negative_count": negatives_12mo,
                "active_negative_events": sorted(active_events),
                "as_of_date": data.get("as_of_date"),
                "n_article_urls": len(data.get("negative_article_urls", [])),
            },
        }

    # MEDIUM severity: 90d threshold met
    if negatives_90d >= THRESHOLD_90D_FIRE:
        return {
            "fires": True,
            "reason": "ELEVATED_NEGATIVE_VELOCITY_90D",
            "severity": "MEDIUM",
            "evidence": {
                "trailing_90d_negative_count": negatives_90d,
                "trailing_12mo_negative_count": negatives_12mo,
                "active_negative_events": sorted(active_events),
                "as_of_date": data.get("as_of_date"),
                "n_article_urls": len(data.get("negative_article_urls", [])),
            },
        }

    # MEDIUM fallback: sustained 12-month elevation with active investigation
    # (catches slow-burn cases where 90d count fluctuates below threshold)
    if negatives_12mo >= THRESHOLD_12MO_FALLBACK_FIRE and has_active_investigation:
        return {
            "fires": True,
            "reason": "SUSTAINED_12MO_NEGATIVE_FLOW_WITH_ACTIVE_INVESTIGATION",
            "severity": "MEDIUM",
            "evidence": {
                "trailing_90d_negative_count": negatives_90d,
                "trailing_12mo_negative_count": negatives_12mo,
                "active_negative_events": sorted(active_events),
                "as_of_date": data.get("as_of_date"),
            },
        }

    return {
        "fires": False,
        "reason": "BELOW_VELOCITY_THRESHOLD",
        "severity": "LOW",
        "evidence": {
            "trailing_90d_negative_count": negatives_90d,
            "trailing_12mo_negative_count": negatives_12mo,
            "trailing_12mo_total_articles": total_12mo,
            "active_negative_events": sorted(active_events),
        },
    }
