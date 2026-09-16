# OSHA Form 300A + SAM.gov Spike

_Spike test 2026-05-18. Two new connectors built for operational-
scope verification: OSHA Form 300A establishment data (~398k US
establishments with 20+ employees) and SAM.gov entity registry
(NAICS + employee count + facility address). Spike validates OSHA
end-to-end on a live dataset; SAM connector is key-gated (built but
not yet exercised live — requires sam.gov/data-services API key)._

## What the OSHA 300A data gives us

Every US employer with 20+ employees in covered industries files
Form 300A annually with:
  - establishment_name + company_name + EIN
  - street_address, city, state, zip
  - naics_code + industry_description
  - **annual_average_employees** (the scope-verification field)
  - total_hours_worked

This is the EPA-FRS twin for non-chemistry operations: drone assembly,
biotech labs, electronics integration, fabrication shops — all show
up here at the moment they hit 20 employees, regardless of whether
they trigger any EPA threshold.

## Panel results

```
TK        company              n_est  total_emps  top_NAICS                signal
LMT       Lockheed Martin       166   106,605     3364 (aerospace)        REGISTERED ✓
Boeing    Boeing                143   111,801     3364                    REGISTERED ✓
NOC       Northrop Grumman      110    81,625     3364                    REGISTERED ✓
GM        General Motors         59    82,286     3363 (motor vehicle)    REGISTERED ✓
KTOS      Kratos                 10     1,542     3364 + 3342             REGISTERED ✓
PESI      Perma-Fix Environ.      8       303     5622 (hazardous waste)  REGISTERED ✓
HDSN      Hudson Technologies     5       432     3251 (basic chemicals)  REGISTERED ✓
CWCO      Consolidated Water      2       252     2383 + 3221             REGISTERED ✓
AIRO_grp  AIRO Group              0         0     —                       NO_OSHA_FOOTPRINT
AIRO      "AIRO" (substring)     43     4,557     6232 + 2211             SUBSTRING NOISE
KLIC      Kulicke and Soffa       0         0     —                       NO_OSHA_FOOTPRINT (false negative)
KULR      KULR                    0         0     —                       NO_OSHA_FOOTPRINT
ALMU      Aeluma                  0         0     —                       NO_OSHA_FOOTPRINT
RCAT      Red Cat                 0         0     —                       NO_OSHA_FOOTPRINT
KSCP      Knightscope             0         0     —                       NO_OSHA_FOOTPRINT
ONDS      Ondas                   0         0     —                       NO_OSHA_FOOTPRINT
LRHC      La Rosa Holdings        0         0     —                       NO_OSHA_FOOTPRINT ✓
Akazoo    Akazoo                  0         0     —                       NO_OSHA_FOOTPRINT ✓
```

Also tested AIRO Phoenix address-level query (city=PHOENIX, state=AZ,
naics_prefix=3364): **10 aerospace establishments / 6,768 employees**
in Phoenix — but none of them are AIRO Group or its subsidiaries.
Real names in the Phoenix aerospace cluster: Honeywell Sky Harbor
(1,700), Honeywell Deer Valley (2,005), Honeywell Phoenix Engines
(2,026), F&B Manufacturing, Northstar Aerospace, Hamilton Sundstrand.

## What works

1. **Strong PASS for traditional manufacturers.** PESI's 8 hazwaste
   sites, HDSN's 5 chemical sites, Kratos's 10 aerospace sites — all
   corroborate the operational claims with explicit headcount + NAICS.
2. **Address-based queries work** when a claimed industrial cluster
   exists. Phoenix aerospace has 10 real establishments with 6,768
   employees — the cluster exists; whether AIRO is in it is a
   different question (their subs may be too small to file).
3. **True 0-hit controls** (Akazoo, LRHC) cleanly differentiate from
   industrial claimants.

## Coverage gaps — what doesn't work

1. **Sub-20-employee operations don't file 300A.** This is a hard
   exclusion in the data. ALMU has 11 FT + 2 PT employees; below
   threshold. KULR/RCAT/KSCP/ONDS all likely have <20 US employees.
   AIRO subsidiaries (Coastal Defense, Aspen Avionics, Sky-Watch,
   Jaunt) are individually small enough to not file.

2. **Low-injury-rate exempt industries.** Many low-hazard NAICS
   (software, R&D, professional services) are exempt from electronic
   submission even with 20+ employees. KLIC's Fort Washington PA HQ
   (real semi equipment maker, ~2,000 global employees) returns 0
   matches — probably because most manufacturing is offshore and the
   US HQ is engineering/sales (exempt). Fort Washington PA has 29
   establishments but none are KLIC.

3. **Substring noise** identical to USAspending. "AIRO" matched 43
   establishments across residential care (Cairo Family Care, Kairos
   NW) and electric power generation. **Fixed in follow-up commit
   via word-boundary regex** (`\b{name}\b` case-insensitive) as
   default `match_mode="word_boundary"` on
   `osha_establishments.query_establishments` AND
   `usaspending.resolve_recipient_ueis`. Post-fix, "AIRO" matches 1
   establishment (Airo Mechanical LLC, an HVAC contractor — real
   word match but unrelated to AIRO Group, which is the correct
   behavior; planner should use longer variants for higher
   specificity).

4. **Subsidiary naming asymmetry.** AIRO Group → 0; individual subs
   (Coastal Defense, Aspen Avionics) → also 0. The 300A roster
   doesn't include any of them, so we can't disambiguate "exists
   below threshold" from "doesn't exist."

5. **Only 300 NAICS 336411 (Aircraft Manufacturing) establishments
   nationwide** in the 2024 file — extremely sparse for a sector
   with hundreds of real US drone/aerospace operations. Most drone
   makers are sub-20-employee and never file.

## Recommended severity mapping

This connector should be **calibrated as a corroboration source**,
NOT an inflation flag. The asymmetry is:
- **Presence at scale** (>=50 employees) → strong PASS
- **Presence but small** (<50) → UNVERIFIABLE (honest-small or inflated)
- **Absence** → UNVERIFIABLE in most cases (coverage gap), EXCEPT
  when the claim's language explicitly asserts "thousand-person
  manufacturing facility" or "Fortune 500 employer" — then absence
  is a genuine contradiction.

```python
if signal == "REGISTERED_EMPLOYER" and total_emps >= 50:
    return PASS
elif signal == "NO_OSHA_FOOTPRINT" and claim_says_thousands_of_employees:
    return MODERATE_UNDERDELIVERY  # large-headcount claim, no 300A → inflation
else:
    return UNVERIFIABLE  # the gap is real (sub-20 + exempt industries)
```

The "thousand-person manufacturing facility" trigger needs LLM
language parsing — keyword heuristics like "1,000-person" / "thousand
employees" / "Fortune 500" / "largest" / "major US manufacturer" can
serve as a first-pass.

## SAM.gov connector

Built but not exercised live. The connector reads `~/.sam_api_key`
(needs registered key from sam.gov/data-services, free) and queries
`/entity-information/v3/entities?ueiSAM={uei}`. Returns:

  - legal_business_name + dba_name
  - physical_address (line 1, city, state, zip)
  - primary_naics + all_naics
  - employee_count (self-declared)
  - annual_revenue (self-declared)
  - registration_status + expiration
  - business_types (small biz, SDB, etc.)
  - cage_code

Pairs naturally with usaspending: usaspending tells us what the entity
*received*; SAM tells us what the entity *declared* about itself.

**Highest-leverage cross-checks once SAM is live:**

1. **NAICS mismatch.** Filing claims "aircraft manufacturer" but SAM
   primary NAICS is 541330 (Engineering Services). Direct evidence
   of scope inflation — the company self-declared a different
   business when registering for federal eligibility.

2. **Employee count gap.** Filing implies "500-person operation" but
   SAM self-declares 25 employees. The 500-headcount narrative
   contradicts what the company tells the federal government.

3. **Address inconsistency.** Filing names a Phoenix manufacturing
   facility; SAM physical address is in Delaware. Suggests Delaware-
   registered shell with no actual Phoenix presence.

4. **Inactive registration.** SAM registration expired / inactive —
   weakens federal-customer-pipeline claims.

## Recommended integration

Add to `m_source_catalog.py`:
- `osha_establishments.query_establishments` (live, working)
- `sam_entity.query_entity_by_uei` (key-gated, returns ERROR until
  user installs key)

Add to `deterministic_scorer.py`:
- `_score_osha_establishments` with the asymmetric calibration above
  (presence = corroboration; absence = mostly UNVERIFIABLE)
- `_score_sam_entity` once SAM is exercised live; severity gates on
  NAICS-mismatch + employee-gap + address-mismatch

## Files

- `m_sources/osha_establishments.py` — Form 300A CSV connector
- `m_sources/sam_entity.py` — SAM v3 entity API connector (key-gated)
- `test.py` — OSHA panel spike
- `spike_results.json` — raw OSHA results
- `data/_osha_data/ITA_300A_Summary_Data_2024_through_12-31-2025.csv` —
  local mirror, refresh annually
