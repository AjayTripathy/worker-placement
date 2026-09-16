# Verified Outcomes 2023-2025 — Schema and Methodology

## Why this directory exists

The prior `data/realized_outcomes_2023_2025.json` was hand-curated without source citations. Ascension Health was flagged as `MULTI_DOWNGRADE` (Moody's Aa2→Aa3 + S&P AA→AA-) but the actual verifiable outcome was: Moody's outlook revised to negative (no rating change), S&P unchanged, Fitch downgraded AA+→AA on Sept 17-18 2025. This re-verification effort exists to put every outcome on cited footing.

## Data shape — one JSON file per obligor

`{obligor_slug}.json`:

```json
{
  "obligor_name": "Ascension Health",
  "obligor_aliases": ["Ascension Health Alliance", "Ascension Health Senior Credit Group"],
  "verified_at": "2026-05-27",
  "verified_by": "claude opus 4.7",
  "snapshot_date": "2022-12-31",
  "window_end": "2025-03-31",
  "starting_ratings": {
    "moodys": {
      "rating": "Aa2",
      "outlook": "stable",
      "as_of": "2022-12-31",
      "source_url": "https://...",
      "source_type": "agency_press_release|emma_men|bond_buyer|becker|obligor_ir",
      "citation_text": "verbatim quote from source",
      "fetched_at": "2026-05-27T..."
    },
    "sp": { ... },
    "fitch": { ... }
  },
  "rating_actions_in_window": [
    {
      "date": "2024-09-XX",
      "agency": "moodys",
      "action": "OUTLOOK_REVISION",
      "action_detail": "outlook revised from stable to negative; rating affirmed at Aa2",
      "rationale": "cyber attack and operating losses",
      "source_url": "https://...",
      "source_type": "...",
      "citation_text": "...",
      "fetched_at": "..."
    }
  ],
  "ending_ratings": {
    "moodys": { ... },
    "sp": { ... },
    "fitch": { ... }
  },
  "computed_outcome_class": "AFFIRM_NEGATIVE_OUTLOOK",
  "outcome_class_rationale": "no rating downgrade by Moody's or S&P; only outlook revision. Fitch downgrade Sept 2025 falls after window_end so excluded."
}
```

## Outcome class taxonomy (refined from prior 7-class system)

| Class | Definition |
|---|---|
| `UPGRADE` | At least one notch upgrade by any agency, no offsetting downgrade |
| `AFFIRM_POSITIVE_OUTLOOK` | Outlook revised positive by ≥1 agency, no rating change |
| `AFFIRM_STABLE` | No rating or outlook changes in the window |
| `AFFIRM_NEGATIVE_OUTLOOK` | Outlook revised negative by ≥1 agency, no rating change |
| `DOWNGRADE` | Exactly one notch down by one or two agencies |
| `MULTI_DOWNGRADE` | Two-or-more notch down by any agency, OR one-notch down by 3 agencies |
| `DEFAULT` | Chapter 11 / payment default / DEFAULTED tier rating (CCC+ or worse) |
| `UNVERIFIABLE` | Could not find primary sources within budget |

## Source-type ranking (most → least authoritative)

1. `agency_press_release` — Moody's/S&P/Fitch official press release URL
2. `emma_men` — MSRB EMMA Material Event Notice Code 11.00 (rating change)
3. `obligor_ir` — Obligor's own investor relations page citing the action
4. `bond_buyer` / `becker` / `modern_healthcare` — trade publication coverage
5. `wikipedia` / `secondary` — last resort (still require URL)

## Source budget per obligor

- Target: ≥2 sources per action, ≥1 must be tier-1 or tier-2
- Budget: ~5 web searches + ~5 page fetches per obligor
- Time per obligor: 5-10 minutes via WebSearch + WebFetch
- Total for 65 obligors: ~6-10 hours

## What to do when a source is paywalled

- If Moody's/S&P/Fitch detail is paywalled, fall back to Bond Buyer / Becker's coverage of the same action
- Always record `source_url` even if content is partial
- Note `source_quality: "trade_publication_summary"` when not the agency itself
