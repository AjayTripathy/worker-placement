# USAspending Connector — UEI-Anchored Spike

_Spike test 2026-05-18. Validates that UEI-anchored search removes
the substring-noise + variant-asymmetry failure modes identified in
the bare-name spike, making federal-contract f(M) usable as a primary
M-source for federal/agency counterparty claims._

## What changed

**Before (substring search):** `recipient_search_text` accepts a name
substring, matching anything in usaspending's full recipient
universe. "Hudson Technologies" matched 67,867 entities. "AIRO"
matched 119. "Airo Group" matched 0. Pure substring pollution.

**After (UEI-anchored):**
1. Resolve `name → [UEI]` via `/api/v2/recipient/duns/`
2. For each UEI, query `recipient_search_text=[UEI]` — UEI is a
   unique 12-char code, so substring matches the recipient exactly.
3. Aggregate across parent + subsidiary UEIs.

New API in `m_sources/usaspending.py`:
- `resolve_recipient_ueis(name) -> [{name, uei, duns, level, snapshot}]`
- `query_by_uei(uei, ...) -> contracts dict`

## Panel results (UEI-anchored, 2018-01-01 → 2026-05-18)

```
label              ueis contracts        $M  top_agency
KNOWN_LMT             8   376014   869306.2  DoD
KNOWN_NOC             9    28896   137240.4  DoD
KNOWN_RTX             4    14040    60375.6  DoD
KNOWN_KTOS           10     1444     5494.6  DoD
PESI_DOE              5      314       92.9  DoD (real DOE work)
HDSN_DLA              3   115900       49.5  DoD (real DLA refrig supplier!)
AIRO                  6       14       48.8  DoD
CDNA_VA               3       64       16.8  VA (real biotech)
RCAT_drones           2       61        9.8  DoD
KULR_NASA             2       29        2.6  NASA (real)
ALMU_DARPA            1        7        2.1  DoD
CWCO_DHS              3       20        0.6  DHS
KLIC                  1        1        0.3  DoD
KSCP                  1        5        0.2  VA
ONDS_drones           0        0        0.0  —    ← INFLATION_SUSPECT
CTRL_LRHC             0        0        0.0  —
FAB_AKAZOO            0        0        0.0  —
```

## Headline findings

### 1. PESI's DOE claim is now corroborated
Bare-name search gave 294 hits / $66M. UEI-anchored gives **314 hits
across 5 subsidiary UEIs / $92.9M, top agency DoD**. Subsidiaries
include "Perma-Fix of Florida", "Perma-Fix Northwest Richland",
"Perma-Fix ERRG Services" — these are the operating entities for
their nuclear-waste work. Without UEI resolution, the substring
search missed several of these (and noise-added unrelated entries).

### 2. ONDS is the standout INFLATION_SUSPECT
Ondas Holdings claims federal/defense relationships in their filings.
0 UEIs resolve. 0 contracts. The bare-name search (which also gave
0) couldn't distinguish "noise floor" from "real zero" — the
UEI-anchored version confirms it: Ondas has no federal recipient
profile under any name variant. **This is the strongest fabrication-
suspect signal in the panel.**

### 3. HDSN is actually a real DLA refrigerant supplier (I mislabeled
   it as a control)
Hudson Technologies (HDSN) — which I included as a "no federal
claim" control — has **3 UEIs covering 115,900 individual DLA award
line items totaling $49.5M**. Each line is a small refrigerant
purchase ($430 avg) for DoD installations under GSA-schedule supply.
This is a real federal customer relationship I missed when assigning
expected labels. **Lesson: the framework's expectation labels need
to be derived from filings, not analyst priors. HDSN's 10-K does
disclose government-supply revenue.**

### 4. Variant search is essential
For each ticker, I had to try 2-3 name variants to catch all UEIs:
- "AIRO" + "AIRO Group" + "AIRO Manufacturing" → 6 UEIs
- "Perma-Fix Environmental" + "Perma-Fix" → 5 UEIs
- "RTX Corporation" + "Raytheon Technologies" → 4 UEIs
The autocomplete endpoint returns parent + child + alias entries
together when queried per variant. Without multiple variants,
subsidiaries get missed.

## Comparison with megacap_namecheck

Both connectors now exist and serve complementary purposes:

| | megacap_namecheck | usaspending (UEI) |
|---|---|---|
| Target | Commercial megacap partnership claims | Federal agency claims |
| Registry | Megacap's own SEC filings (EDGAR FTS) | usaspending FPDS+FAADS |
| Coverage | ~20 megacaps as counterparties | All federal agencies |
| Materiality gating | Yes — megacap can discretion-suppress | No — every award recorded |
| Absence interpretation | Moderate (~hi-vol megacaps can omit) | Strong (~comprehensive registry) |
| Presence interpretation | Strong (3+ filings = real partnership) | Strong (dollar/agency-explicit) |
| Best signal use | Veto on inflation (0 hits → suspect) + corroboration (3+ hits) | Same shape: 0 = strong suspect; presence = corroboration + magnitude |

## Correction: UEI resolver had substring noise too

**Follow-up fix (committed separately).** The bare-name resolution
step had its own substring problem — the USAspending
`/api/v2/recipient/duns/` endpoint matches `keyword` as a server-side
substring. Searching for "AIRO" returned 6 UEIs that were all
unrelated entities (Kairos Power, Kairos Inc, American University in
Cairo, University of Nairobi, etc.). The downstream contract-amount
aggregation summed all six, producing a false "$48.8M AIRO federal
presence" claim in an earlier revision of this report.

Fix: added a client-side word-boundary filter on returned names
(default `match_mode="word_boundary"` in `resolve_recipient_ueis`).
Post-fix:
- "AIRO" → 0 UEIs (was 6 noise)
- "AIRO Group" → 0 UEIs (correctly — AIRO Group's federal awards
  are filed under operating subsidiaries)
- "Coastal Defense" + "Aspen Avionics" + "Jaunt Air Mobility" →
  5 real UEIs across AIRO Group's subsidiaries
- AIRO's true federal presence: **$26.7M across 673 contracts**
  (mostly Coastal Defense Inc / DLA), top agency DoD,
  RECURRING_FEDERAL → PASS

The earlier reported $48.8M was inflated by ~$22M of Kairos-Power /
University noise. The corrected $26.7M is still RECURRING_FEDERAL
(>$5M lifetime), so the qualitative read (AIRO has real federal
vendor relationships, PASS) is unchanged. But the report dollar
figures in earlier versions of this document should be discounted
accordingly.

## Failure modes that REMAIN even with UEI anchoring

1. **Subcontractor invisibility.** The prime (LMT, NOC, BAH) gets
   the award; small-cap subs don't appear in usaspending's top-level
   awards (only in subaward data, which is sparser and inconsistent).
   A small-cap doing real F-35 work via an LMT subcontract might
   show 0 UEI-anchored awards.
2. **CRADAs & some OTAs.** Cooperative Research and Development
   Agreements with DOE national labs (Sandia, LANL, ORNL) are NOT
   procurement awards — they're shared-resource agreements. Real
   partnerships not in usaspending.
3. **Classified work.** Some real DoD relationships are classified
   and don't appear publicly.
4. **State pass-through.** Federal money flowing through state
   agencies looks like state, not federal, awards.
5. **SBIR/STTR inflation.** A $50K Phase I SBIR award is real but
   the small-cap describes it as "DoD program." Resolves the
   *existence* question but not the *scale* question.
6. **Variant resolution needs human curation** (or LLM extraction
   from 10-K Exhibit 21). Auto-search with the small-cap's
   conventional ticker name misses subsidiaries.

## Integration recommendation

The UEI-anchored usaspending connector should be the **primary
M-source for any federal/agency counterparty claim** in the planner:

- For claims like "we have contracts with the DoD" / "DOE-funded
  research" / "NASA partnership" / "VA hospital deployments":
  1. Resolve UEIs across name variants + Exhibit 21 subsidiary
     names (planner-provided)
  2. Aggregate contracts + grants by UEI, by agency
  3. Severity mapping:
     - 0 UEIs, 0 awards → SEVERE_UNDERDELIVERY (inflation suspect)
     - Awards present but agency / scale mismatched to claim
       → MODERATE_UNDERDELIVERY (overstatement)
     - Awards present, agency + scale consistent → PASS

- Keep megacap_namecheck for commercial-counterparty claims
  (MSFT/AMZN/NVDA partnership claims) where there's no agency
  registry to anchor on.

## Files

- `verticals/public_co/m_sources/usaspending.py` — UEI resolver
  added (`resolve_recipient_ueis`, `query_by_uei`)
- `test.py` — original bare-name spike (substring noise baseline)
- `uei_test.py` — UEI-anchored spike (this run)
- `spike_results.json` — bare-name raw results
- `uei_results.json` — UEI-anchored raw results
