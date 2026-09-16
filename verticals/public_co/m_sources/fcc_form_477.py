"""FCC fixed-broadband subscriber data — Form 477 / Broadband Data Collection.

WHY THIS EXISTS

For cable / satellite / fiber-broadband issuers (CABO, GOGO, TDS, SATS,
CALX), the catastrophe pattern is subscriber bleed. 10-K narratives
typically frame this as "competitive pressures" while year-over-year
subscriber count tells the real story.

FCC Form 477 fixed-broadband subscriber reports (June and December
filings) are published as bulk CSV downloads. After 2022 the program
migrated to the Broadband Data Collection (BDC). For the 2024-05-15
backtest cutoff we use Dec 2022 Form 477 + Dec 2023 BDC.

DATA SOURCE

FCC publishes per-provider, per-state fixed-broadband subscription
counts in semiannual files. The aggregate file we use:
  https://www.fcc.gov/general/broadband-deployment-data-fcc-form-477
  filename pattern: fbd_<period>_v<N>.zip → fbd_<period>.csv

Schema (subset):
  ProviderID, ProviderName, StateAbbr, TechCode, Consumer,
  MaxAdDown, MaxAdUp, ...

We need an aggregated form: ProviderName → period → total_subscribers.
That requires preprocessing the raw FCC files (~GB scale) into a
compact JSON cache at data/_fcc_form_477/subscriber_panel.json:

  {
    "providers": {
      "Cable One":     {"2022H2": 1100000, "2023H1": 1050000, "2023H2": 980000},
      "Cogent Communications": {"2022H2": 95000, ...},
      ...
    }
  }

Populate this cache offline; the m-source consumes it. If the cache is
missing, return UNVERIFIABLE with clear instructions.

OUTPUT

  signal: GROWING | STABLE | DECLINING | SEVERE_LOSS | UNVERIFIABLE
  metrics: {provider_name, latest_subs, yoy_subs_change, yoy_pct,
            periods_in_panel}

THRESHOLDS (YoY % change in subscribers)

  >= +2%       → GROWING
  -2 to +2%    → STABLE
  -10 to -2%   → DECLINING
  < -10%       → SEVERE_LOSS
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["481", "484"],
    "issuer_features": ["broadband_subscriber_business"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "FCC Form 477/BDC fixed-broadband subscriber counts; subscriber bleed vs narrative for cable/fiber/satellite issuers.",
}

import json
from pathlib import Path
from typing import Any, Optional

CACHE_FILE = Path(__file__).parent.parent / "data" / "_fcc_form_477" / "subscriber_panel.json"

_SEVERITY_MAP = {
    "GROWING":      "PASS",
    "STABLE":       "PASS",
    "DECLINING":    "MODERATE_UNDERDELIVERY",
    "SEVERE_LOSS":  "SEVERE_UNDERDELIVERY",
    "UNVERIFIABLE": "UNVERIFIABLE",
}

_NOISE_TOKENS = {
    "inc", "inc.", "corp", "corp.", "co", "co.", "ltd",
    "llc", "lp", "plc", "the", "&", "and", "of",
    "communications", "comm", "broadband", "media", "cable",
    "holdings", "group", "telecom",
}


def _normalize(s: str) -> str:
    s = (s or "").lower()
    for ch in ",.;:()[]\"'":
        s = s.replace(ch, " ")
    return " ".join(s.split())


def _meaningful_tokens(s: str) -> list[str]:
    return [t for t in _normalize(s).split() if t not in _NOISE_TOKENS and len(t) >= 3]


def _match_provider(provider_name: str, query: str) -> bool:
    """Token-overlap matcher; query needs all meaningful tokens in provider."""
    q_tok = _meaningful_tokens(query)
    p_tok = _meaningful_tokens(provider_name)
    if not q_tok or not p_tok:
        return False
    p_set = set(p_tok)
    return all(t in p_set for t in q_tok)


def _load_panel() -> Optional[dict]:
    if not CACHE_FILE.exists():
        return None
    try:
        return json.loads(CACHE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def query_subscriber_trend(
    provider_name: str,
    cutoff_date: str,
    lookback_periods: int = 4,
) -> dict[str, Any]:
    """Return subscriber YoY trend for a provider.

    Looks up the panel cache, finds the most recent period <= cutoff,
    compares to the same period one year prior.
    """
    panel = _load_panel()
    if panel is None:
        return {
            "provider_name": provider_name,
            "signal":   "UNVERIFIABLE",
            "severity": _SEVERITY_MAP["UNVERIFIABLE"],
            "direction": "neutral",
            "_note": (
                f"FCC subscriber panel cache missing at {CACHE_FILE}. "
                "Populate via FCC Form 477 bulk downloads "
                "(https://www.fcc.gov/general/broadband-deployment-data-fcc-form-477) "
                "then aggregate provider-state-period subscriber counts into "
                "subscriber_panel.json. Schema: {providers: {ProviderName: "
                "{'YYYYHN': total_subs}}}."
            ),
        }

    providers = panel.get("providers", {})
    matches = [
        (name, periods) for name, periods in providers.items()
        if _match_provider(name, provider_name)
    ]
    if not matches:
        return {
            "provider_name": provider_name,
            "signal":   "UNVERIFIABLE",
            "severity": _SEVERITY_MAP["UNVERIFIABLE"],
            "direction": "neutral",
            "_note": f"No provider match in cache for '{provider_name}'.",
        }
    # Merge across matching provider variants (e.g., subsidiaries)
    merged: dict[str, int] = {}
    matched_names = []
    for name, periods in matches:
        matched_names.append(name)
        for period, subs in periods.items():
            merged[period] = merged.get(period, 0) + int(subs or 0)

    # Determine latest period <= cutoff
    cutoff_period = _period_for_date(cutoff_date)
    sorted_periods = sorted(merged.keys())
    eligible = [p for p in sorted_periods if p <= cutoff_period]
    if len(eligible) < 2:
        return {
            "provider_name": provider_name,
            "matched_names": matched_names,
            "signal":   "UNVERIFIABLE",
            "severity": _SEVERITY_MAP["UNVERIFIABLE"],
            "direction": "neutral",
            "_note": f"Need ≥2 periods to compute YoY; got {len(eligible)}.",
        }

    latest_period = eligible[-1]
    latest_subs = merged[latest_period]
    # Find period one year prior (same H{1,2} of previous year)
    prior_period = _shift_period(latest_period, -2)  # 2 half-year steps = 1 yr
    if prior_period not in merged:
        # Fallback: previous period in the panel
        prior_period = eligible[-2]
    prior_subs = merged[prior_period]
    if prior_subs <= 0:
        yoy_pct = None
    else:
        yoy_pct = 100.0 * (latest_subs - prior_subs) / prior_subs

    if yoy_pct is None:
        signal = "UNVERIFIABLE"
    elif yoy_pct >= 2:
        signal = "GROWING"
    elif yoy_pct >= -2:
        signal = "STABLE"
    elif yoy_pct >= -10:
        signal = "DECLINING"
    else:
        signal = "SEVERE_LOSS"

    direction = (
        "positive" if signal == "GROWING"
        else "neutral" if signal == "STABLE"
        else "negative"
    )

    return {
        "provider_name":     provider_name,
        "matched_names":     matched_names,
        "signal":            signal,
        "severity":          _SEVERITY_MAP[signal],
        "direction":         direction,
        "metrics": {
            "latest_period":     latest_period,
            "latest_subs":       latest_subs,
            "prior_period":      prior_period,
            "prior_subs":        prior_subs,
            "yoy_subs_change":   latest_subs - prior_subs,
            "yoy_pct":           round(yoy_pct, 2) if yoy_pct is not None else None,
            "periods_in_panel":  len(sorted_periods),
        },
        "_note": (
            f"{provider_name}: {prior_period}={prior_subs:,} → {latest_period}={latest_subs:,} "
            f"(YoY {yoy_pct:+.1f}% → {signal})"
            if yoy_pct is not None else "Could not compute YoY change."
        ),
    }


def _period_for_date(iso: str) -> str:
    """ISO YYYY-MM-DD → 'YYYYH1' or 'YYYYH2'."""
    y = int(iso[:4])
    m = int(iso[5:7])
    h = 1 if m <= 6 else 2
    return f"{y}H{h}"


def _shift_period(period: str, half_year_steps: int) -> str:
    y = int(period[:4])
    h = int(period[5])
    h += half_year_steps
    while h <= 0:
        h += 2; y -= 1
    while h > 2:
        h -= 2; y += 1
    return f"{y}H{h}"


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Cable One"
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2024-05-15"
    print(json.dumps(query_subscriber_trend(name, cutoff), indent=2, default=str))
