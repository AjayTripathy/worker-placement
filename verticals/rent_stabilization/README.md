# rent_stabilization

Detects rent overcharges on stabilized units. R = listed asking rent. f = legal max rent under the Rent Stabilization Law (RSL) using the unit's base rent × Rent Guidelines Board cumulative compounding factor. M = listing scrapes (StreetEasy / Trulia / Zillow Rentals).

## Production state

- **NYC jurisdiction wired** with RSL overcharge rule + RGB schedule
- **One-bedroom and small-multifamily units** are the primary signal class

## Layout

```
rent_stabilization/
├── manifest.py            VerticalManifest declaration
├── models.py              Vertical-local types
├── gap.py                 GapFunction: listed_rent - legal_max
├── rgb_schedule.py        Annual NYC Rent Guidelines Board cumulative factor schedule
├── scorer.py              Severity (overcharge $/yr, units affected)
├── sources/               Listing-source connectors (StreetEasy etc.)
├── rules/
│   └── rsl_overcharge.py  RSL §26-510 / J-51 overcharge SignalRule
└── jurisdictions/
    └── nyc/               NYC-specific source registrations + DOF comparable income data
```

## Run

```bash
signalos run --vertical rent_stabilization --jurisdiction nyc --building <BBL>
signalos report --vertical rent_stabilization --tier high
```

## Known triples

| R | f | M | Status |
|---|---|---|---|
| Owner-listed asking rent | Legal max = base × RGB cumulative factor (RSL §26-510) | StreetEasy/Trulia/Zillow listings | Built |

## Notes

- DOF (NYC Department of Finance) comparable income data is the long-term target M for income-property valuation cross-checks, paired with the listing-side data
- J-51 tax-abatement compliance is a sibling triple that hasn't been wired (similar shape: program eligibility claim vs occupancy/rent-cap actuality)
