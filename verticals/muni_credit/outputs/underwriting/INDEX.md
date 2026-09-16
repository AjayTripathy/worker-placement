# Underwriting File — CA Insulated Muni Sleeve

*25 names · $1,000,000 face · compiled 2026-06-11 · one memo per CUSIP, merged from every verification stream*

## The review stack applied to every name
1. Identity (EMMA issue title + OpenFIGI, adjudicated)  
2. Tax status + AMT (EMMA record)  
3. Legal pledge vs marketed label (EMMA; OS read for revenue/structure names)  
4. Call features; original-issue price (OID vs market discount)  
5. Yield arithmetic recomputed from raw coupon/price/maturity (de-minimis aware)  
6. Liquidity from the MSRB tape (trades/yr, two-sided days, realized spread, blocks)  
7. AB-1200 fiscal-stress rosters; levy-base underwrite where concentration was flagged  
8. Continuing-disclosure history (event notices, redemption risk, filing currency)  
9. Hazards jointly: FEMA NRI wildfire × USGS seismic × fault-zone caps  

| CUSIP | Name | Phase | DD | TEY a-t | Memo |
|---|---|---|---|---|---|
| `012104QQ1` | Albany City Unified | P1 | FLAG | 8.76% | [012104QQ1_albany-city-unified.md](012104QQ1_albany-city-unified.md) |
| `050002AW4` | essential-service water/wastewater rev | P1 | CLEAR | 7.98% | [050002AW4_essential-service-water-wastewater-r.md](050002AW4_essential-service-water-wastewater-r.md) |
| `171314LB1` | Chula Vista Elementary | P1 | CLEAR | 8.02% | [171314LB1_chula-vista-elementary.md](171314LB1_chula-vista-elementary.md) |
| `291119KP9` | Emery Unified | P1 | CLEAR | 8.66% | [291119KP9_emery-unified.md](291119KP9_emery-unified.md) |
| `796472AS7` | San Benito High | P1 | CLEAR | 8.23% | [796472AS7_san-benito-high.md](796472AS7_san-benito-high.md) |
| `817409H32` | Sequoia Union High | P1 | FLAG | 8.08% | [817409H32_sequoia-union-high.md](817409H32_sequoia-union-high.md) |
| `900211CP6` | Turlock Unified School District | P1 | CLEAR | 8.61% | [900211CP6_turlock-unified-school-district.md](900211CP6_turlock-unified-school-district.md) |
| `91412G2F1` | UC Regents Limited Project Revenue Bon | P1 | CLEAR | 6.32% | [91412G2F1_uc-regents-limited-project-revenue-b.md](91412G2F1_uc-regents-limited-project-revenue-b.md) |
| `91412HJC8` | Regents of the University of Californi | P1 | CLEAR | 7.83% | [91412HJC8_regents-of-the-university-of-califor.md](91412HJC8_regents-of-the-university-of-califor.md) |
| `926055KH6` | Victor Valley Union High School Distri | P1 | FLAG | 8.04% | [926055KH6_victor-valley-union-high-school-dist.md](926055KH6_victor-valley-union-high-school-dist.md) |
| `032591TU3` | Anaheim Union High | P2 | CLEAR | 8.13% | [032591TU3_anaheim-union-high.md](032591TU3_anaheim-union-high.md) |
| `079113DY9` | Bellevue Union | P2 | FLAG | 8.27% | [079113DY9_bellevue-union.md](079113DY9_bellevue-union.md) |
| `13049WAX3` | essential-service water/wastewater rev | P2 | CLEAR | 8.24% | [13049WAX3_essential-service-water-wastewater-r.md](13049WAX3_essential-service-water-wastewater-r.md) |
| `168520PA6` | Chico Unified | P2 | FLAG | 8.56% | [168520PA6_chico-unified.md](168520PA6_chico-unified.md) |
| `17132CDL9` | Chula Vista Elementary | P2 | FLAG | 8.11% | [17132CDL9_chula-vista-elementary.md](17132CDL9_chula-vista-elementary.md) |
| `223093TK1` | Covina-Valley Unified | P2 | FLAG | 8.54% | [223093TK1_covina-valley-unified.md](223093TK1_covina-valley-unified.md) |
| `270198BY9` | Earlimart Elementary | P2 | CLEAR | 8.04% | [270198BY9_earlimart-elementary.md](270198BY9_earlimart-elementary.md) |
| `358233ED2` | Fresno Unified | P2 | CLEAR | 8.08% | [358233ED2_fresno-unified.md](358233ED2_fresno-unified.md) |
| `547541LJ9` | Lowell Joint | P2 | CLEAR | 8.70% | [547541LJ9_lowell-joint.md](547541LJ9_lowell-joint.md) |
| `587619BF3` | essential-service water/wastewater rev | P2 | CLEAR | 8.06% | [587619BF3_essential-service-water-wastewater-r.md](587619BF3_essential-service-water-wastewater-r.md) |
| `607735CA3` | Modesto City Elementary School Distric | P2 | FLAG | 8.30% | [607735CA3_modesto-city-elementary-school-distr.md](607735CA3_modesto-city-elementary-school-distr.md) |
| `777387AH4` | Roseland Elementary School District | P2 | FLAG | 8.41% | [777387AH4_roseland-elementary-school-district.md](777387AH4_roseland-elementary-school-district.md) |
| `870462TJ7` | Sweetwater Union High | P2 | CLEAR | 8.27% | [870462TJ7_sweetwater-union-high.md](870462TJ7_sweetwater-union-high.md) |
| `95236EAT2` | West County Facilities Financing Autho | P2 | FLAG | 8.19% | [95236EAT2_west-county-facilities-financing-aut.md](95236EAT2_west-county-facilities-financing-aut.md) |
| `95330PHH1` | W HILLS CMNTY CLG-B | P2 | CLEAR | 8.23% | [95330PHH1_w-hills-cmnty-clg-b.md](95330PHH1_w-hills-cmnty-clg-b.md) |

## What the process caught (chronological)
- 29 federally **taxable** bonds excluded from the candidate universe (incl. 2 UC names already in a prior basket)  
- 5 issuer **misbindings** corrected (one changed county + fault zone; one replacement candidate REJECTED outright as a mislabeled community-college district)  
- 5 stale **price marks** re-set to the live tape (one would have overpaid ~2.8pt)  
- 3 high-fire names swapped out at zero yield cost after the wildfire overlay; fire capped in aggregate  
- Atwater: pledge **stronger** than assumed (gross-revenue first lien, AGM wrap) but **chronic late-audit filer** — caveated, not killed  
- OID check: after-tax TEY floor **conservative** for all 11 discounts (3 pure market discount, 8 partial OID = small upside)  
- Emery: office-CRE concentration **real** (48% office AV, flat AV) but debt = 1% of AV (96×) + Teeter — monitor, intact  
- Turlock SFID: boundary concern **defused** (77% of district AV, 70% residential, 230× coverage)  

*Standing monitors: daily limit re-mark + continuing-disclosure delta watch (cd_monitor.py) over all 25 CUSIPs.*