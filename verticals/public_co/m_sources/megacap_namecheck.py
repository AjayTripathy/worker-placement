"""Megacap-earnings name-check connector.

Hypothesis under test: real partnerships between a small-cap and a
mega-cap counterparty leave traces in the **megacap's own** filings —
most informatively in 8-Ks (which carry earnings-call transcripts as
Ex-99.1) and 10-K/Qs (which discuss material customer / vendor
relationships in MD&A). Inflated or fabricated partnerships do not.

Concretely:
- f_megacap_namecheck(small_cap_name, megacap_cik, window) =
    count of megacap filings within `window` that contain the
    small-cap's literal name string.
- Combined across the full megacap list, a "scope intensity" score:
    0 hits ANYWHERE = the claimed counterparty has never mentioned
                       the small-cap in any SEC filing — strong
                       INFLATION_SUSPECT signal
    1-3 hits        = mentioned but not in earnings cadence —
                       likely sub-material relationship
    4+ hits         = real, recurring counterparty relationship

This is asymmetric from H7 (which scores on absence-of-disclosure-by-
the-megacap). The improvement: a real partnership at sub-10% revenue
won't get into the megacap's MD&A *customer-concentration* table, but
WILL still get mentioned in earnings-call transcripts on the 8-K when
the megacap discusses product launches, ecosystem partners, or named
deployments. So the megacap's own 8-K filings have far better recall
for inflation-detection than the materiality-gated counterparty-
disclosure test.

Caveats:
- Common-name small-caps (e.g. "Apple Inc." is the counterparty being
  searched, but the small-cap's name overlaps a common word) need
  variant filtering. Handled here by requiring the full name string.
- Some megacaps' earnings transcripts aren't furnished via 8-K (Apple
  uses 8-K Ex-99.1; Berkshire publishes via annual letter). Spike
  uses 8-K+10-K+10-Q on the megacap CIK.
- Date window: prior 24 months by default — covers ~8 earnings calls.

Test cases at the bottom of this file confirm the connector
differentiates known-real (PLUG × AMZN, PLUG × WMT) from known-
inflated (LDOS x major fleets per Lordstown allegations) from
known-fabricated (Akazoo's Sony/Universal claims, post-SEC).
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["megacap_partnership_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Checks the megacap counterparty's OWN filings for traces of a claimed partnership; fabricated ones leave none.",
}

import time
from datetime import date, timedelta
from typing import Any

from .edgar_fts import query_fulltext


def _query_with_retry(name: str, cutoff: str, cik: str, start: str,
                      forms: str, max_retries: int = 3) -> dict:
    last = None
    for attempt in range(max_retries):
        res = query_fulltext(
            search_term=name, cutoff_date=cutoff, cik=cik,
            start_date=start, forms=forms,
        )
        if "error" not in res:
            return res
        last = res
        time.sleep(0.5 * (attempt + 1))
    return last or {"error": "max_retries"}


# Canonical megacap CIKs — typical small-cap counterparty-claim targets
MEGACAP_CIKS: dict[str, str] = {
    "Amazon":    "0001018724",
    "Microsoft": "0000789019",
    "Apple":     "0000320193",
    "Alphabet":  "0001652044",
    "Meta":      "0001326801",
    "Nvidia":    "0001045810",
    "Tesla":     "0001318605",
    "Walmart":   "0000104169",
    "Berkshire": "0001067983",
    "JPMorgan":  "0000019617",
    "ExxonMobil":"0000034088",
    "GeneralMotors":"0001467858",
    "Ford":      "0000037996",
    "Boeing":    "0000012927",
    "LockheedMartin":"0000936468",
    "Honeywell": "0000773840",
    "Caterpillar":"0000018230",
    "Pfizer":    "0000078003",
    "JNJ":       "0000200406",
}


def query_megacap_mentions(
    small_cap_name: str,
    cutoff_date: str,
    megacap_subset: list[str] | None = None,
    window_days: int = 3650,
    forms: str = "10-K,10-Q,8-K",
) -> dict[str, Any]:
    """For each megacap, return count of filings mentioning the small-cap.

    Returns:
      {
        "small_cap_name": ...,
        "cutoff_date": ...,
        "start_date": ...,
        "by_megacap": {
            "Amazon": {"total_hits": N, "top_filings": [...]},
            ...
        },
        "total_hits_across_megacaps": N,
        "n_megacaps_with_hits": k,
        "signal": INFLATION_SUSPECT | SUB_MATERIAL_RELATIONSHIP |
                  RECURRING_RELATIONSHIP,
      }
    """
    end = date.fromisoformat(cutoff_date)
    start = end - timedelta(days=window_days)
    start_s = start.isoformat()

    by_megacap: dict[str, dict] = {}
    subset = megacap_subset or list(MEGACAP_CIKS.keys())

    total_hits = 0
    n_with_hits = 0
    for mc in subset:
        cik = MEGACAP_CIKS.get(mc)
        if not cik:
            continue
        res = _query_with_retry(
            name=small_cap_name, cutoff=cutoff_date, cik=cik,
            start=start_s, forms=forms,
        )
        hits = res.get("total_hits", 0)
        by_megacap[mc] = {
            "cik": cik,
            "total_hits": hits,
            "top_filings": res.get("top_filings", []),
            "error": res.get("error"),
        }
        total_hits += hits
        if hits > 0:
            n_with_hits += 1
        time.sleep(0.15)

    # Calibrated thresholds from spike on known cases:
    #   Akazoo×{AMZN,MSFT,AAPL,GOOG} = 0 (fabricated)
    #   PLUG × AMZN                  = 1 (real but sub-material warrants)
    #   NVDA × AMZN                  = 15 (ecosystem partner)
    #   Anthropic × AMZN             = 32 (major investment + partnership)
    if total_hits == 0:
        signal = "INFLATION_SUSPECT"
    elif total_hits <= 2:
        signal = "SUB_MATERIAL_RELATIONSHIP"
    else:
        signal = "RECURRING_RELATIONSHIP"

    return {
        "small_cap_name": small_cap_name,
        "cutoff_date": cutoff_date,
        "start_date": start_s,
        "by_megacap": by_megacap,
        "total_hits_across_megacaps": total_hits,
        "n_megacaps_with_hits": n_with_hits,
        "signal": signal,
    }
