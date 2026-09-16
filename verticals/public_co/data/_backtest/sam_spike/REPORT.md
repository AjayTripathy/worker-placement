# SAM.gov Entity-Lookup Spike

_Spike test 2026-05-18. SAM.gov Entity Information v3 API connector
exercised live with user-supplied API key. The connector works; the
spike was partially rate-limited (free tier ~10 req/min). Findings
below combine the individual queries that succeeded before
throttling._

## Schema corrections from the dry-run

Two parser bugs found by running against live data:

1. **NAICS is in `assertions.goodsAndServices`, NOT `coreData.naicsList`.**
   The connector was extracting from the wrong path and returning
   `primary_naics: None` for every entity. Fixed.

2. **The v3 public tier does NOT return `numberOfEmployees` or
   `annualRevenue`.** Those fields require paid extracts or FOUO
   (For Official Use Only) access. The `coreData.financialInformation`
   section only contains `creditCardUsage` and `debtSubjectToOffset`
   booleans. Updated the connector + docstring + scorer to not depend
   on these.

## What the v3 public tier actually returns

Confirmed live fields per entity:
- `entityRegistration`: ueiSAM, cageCode, legalBusinessName, dbaName,
  registrationStatus, registrationExpirationDate, registrationDate,
  lastUpdateDate, exclusionStatusFlag, dodaac
- `coreData.entityInformation`: entityURL, fiscalYearEnd, start date
- `coreData.physicalAddress`, `coreData.mailingAddress`: line1, city,
  state, zip, country
- `coreData.generalInformation`: entityStructure, profitStructure,
  stateOfIncorporation
- `coreData.businessTypes`: For-profit / nonprofit / SBA types
- `assertions.goodsAndServices`: **primaryNaics + naicsList** (the
  scope-verification gold)
- `pointsOfContact`: registrant/admin POCs

## Live spike results (pre-rate-limit batch)

```
Entity                          UEI            Primary NAICS  Desc                                  City              Status
PESI/Northwest Richland         C9CABLLMBP63   562211         Hazardous Waste Treatment & Disposal  RICHLAND, WA       Active ✓
Hudson Technologies (HDSN)      H1K6JDP3K2K8   325120         Industrial Gas Manufacturing          WOODCLIFF LAKE, NJ Active ✓
KULR Technology Corp            YM83B3CN2K61   335991         Primary Battery Manufacturing         SAN DIEGO, CA      Active ✓
KULR Technology Group (alt UEI) TWR9FM3W7C31   (not found)    —                                     —                  Inactive (no record returned)
Coastal Defense Inc (AIRO sub)  N7GAJ4WGU8M8   541990         Other Professional Services           MILL HALL, PA      Active ⚠
Aspen Avionics (AIRO sub)       MXQSNB4QEKN4   334511         Search/Detection/Navigation Instruments  PHOENIX, AZ    Active ✓
Jaunt Air Mobility (AIRO sub)   D2XPQEHMLYX1   336411         Aircraft Manufacturing                SOUTHLAKE, TX      Active ✓
```

## Headline findings

### 1. PESI's DOE claim corroborated at the entity level
Perma-Fix Northwest Richland's SAM entity is at **2025 Battelle Blvd,
Richland WA** — adjacent to the Hanford Nuclear Reservation, with
primary NAICS 562211 (Hazardous Waste Treatment & Disposal). This
matches the framework's bear-vs-corroboration result on PESI: real
DOE federal vendor at a real nuclear-waste-adjacent location.

### 2. HDSN classified as Industrial Gas Manufacturing (NAICS 325120)
Hudson Technologies' SAM entity is registered as **Industrial Gas
Manufacturing** at Woodcliff Lake, NJ. This is correct — refrigerant
reclamation falls under industrial gas. Validates HDSN's $49.5M of
DLA refrigerant orders we saw in the USAspending UEI spike.

### 3. Aspen Avionics IS in Phoenix AZ — explains AIRO's Phoenix claim
**This is the key new finding.** AIRO Group's 10-K claims a 29,353
sqft Phoenix AZ "industrial drone manufacturing" facility. SAM shows:
- **Aspen Avionics (AIRO subsidiary), Phoenix AZ, NAICS 334511**
  (Search, Detection, Navigation, and Guidance Instrument
  Manufacturing)

That's a real established avionics electronics operation in Phoenix.
The framework's UNVERIFIABLE on AIRO's Phoenix claim (because EPA
won't see avionics electronics) is now better explained: **Phoenix
isn't fabricated; it's Aspen Avionics' established avionics line, not
a drone factory.** The claim language ("US drone manufacturing
expansion incl. Blue UAS") may be inflated relative to the SAM-
declared NAICS (Search/Detection/Navigation Instruments), but the
underlying entity is real.

A planner LLM with this connector should now flag the gap as:
"AIRO claims drone-manufacturing scale-up at Phoenix; SAM declares
Aspen Avionics (the Phoenix entity) is NAICS 334511
search/detection/navigation instruments. Real established avionics
electronics operation; not a drone-manufacturing factory at that
classification. Claim language overstates SAM-declared scope."

### 4. Coastal Defense Inc is services, not manufacturing
Another AIRO subsidiary. SAM primary NAICS is **541990 (Other
Professional, Scientific, and Technical Services)** — consistent with
the framework's existing PASS on Coastal Defense as a "training
segment" doing DoD task-order services. The 470 awards / $23.6M of
DLA task-order contracts make sense at this NAICS.

### 5. Jaunt Air Mobility correctly classified as Aircraft Mfg
NAICS 336411 in Southlake, TX. Active. Corroborates AIRO's compound-
rotorcraft claim.

### 6. KULR has two UEIs — only one is the active corp
- TWR9FM3W7C31 ("KULR Technology Group, Inc.") — not found in SAM
- YM83B3CN2K61 ("KULR Technology Corp") — Active in San Diego CA
  with NAICS 335991 (Primary Battery Manufacturing)

The active SAM entity is the operating subsidiary, not the listed
parent. The framework's planner should query by EITHER UEI but use
the active one for scope adjudication.

## Rate-limit constraint

The 8-UEI batch hit the free-tier rate limit (~10 req/min); the
spike's full panel run aborted with 429s after the per-minute
quota. Individual queries spread over 15-30 second intervals worked
reliably. The connector now retries with exponential backoff (1, 2,
4, 8 seconds) but the free tier still requires conservative spacing.

For framework operational use:
- 1,000 requests/day is plenty for normal planner cadence (one
  cohort = ~10 small-caps × ~5 UEIs each = 50 lookups)
- Spike-batches should sleep >=15 sec between requests
- For high-volume scenarios, upgrading to a SAM data-services paid
  extract removes the per-minute rate limit

## Recommended use pattern in the planner

For any claim with federal/agency or operational-scope flavor:
1. Resolve UEIs via `usaspending.resolve_recipient_ueis` (free,
   high-cadence)
2. Score federal-presence via `usaspending.query_federal_presence`
   (the award-history side)
3. **For ≤5 most material UEIs**, fetch SAM entity records via
   `sam_entity.query_entity_by_uei` (rate-limited but high-signal)
4. Pass an `expected_naics_prefix` field on the claim to enable
   automatic NAICS-mismatch detection by the scorer

## Scorer signal map (now wired)

```python
exclusion_flag == 'Y'                    → SEVERE_UNDERDELIVERY (debarred)
registration_status != 'Active'
    AND federal-flavored claim           → MODERATE (escalate)
expected_naics_prefix supplied
    AND primary_naics doesn't match      → MODERATE (escalate, scope contradiction)
expected_naics_prefix supplied
    AND primary_naics matches            → PASS (corroborated)
no expected_naics_prefix                 → PASS (active registration is
                                              the only assertion)
error / no_entity_found                  → UNVERIFIABLE (not federally
                                              registered, common for
                                              non-federal small-caps)
```

## Files

- `m_sources/sam_entity.py` — fixed parser paths (NAICS now in
  goodsAndServices) + retry-on-429 with exponential backoff +
  updated docstring on what v3 public actually returns
- `m_source_catalog.py` — added `sam_entity.query_entity_by_uei` entry
- `deterministic_scorer.py` — added `_score_sam_entity` dispatcher
  with NAICS-match + exclusion + active-registration signals
- `test.py` — calibration panel (now sleeps 15s between requests to
  stay under free-tier rate limit)
- `spike_results.json` — current run (rate-limited; rerun with
  spacing for live results)
