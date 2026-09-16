"""court_toolkit — emits the SignalOS VERIFICATION MANIFEST that every red/blue-team dispatch must
carry (user directive 2026-07-04: 'the red/blue team should be bringing signalOS to verify hypotheses
from data'). The court argues from DATA CHECKS, not reasoning: every load-bearing finding must cite
{claim, tool/connector used, result}; a finding without a data check is graded PLAUSIBLE, never
CONFIRMED, and PLAUSIBLE findings cannot carry a verdict alone.

  python3 -m desk.court_toolkit          # print the manifest (paste into court dispatches)
"""
MANIFEST = """
=== SignalOS VERIFICATION TOOLKIT (court manifest — select by claim type; cite tool + result per finding) ===
PRICE/TAPE CLAIMS ("crashed X%", "band is Y", "already priced"):
  - desk/prices.py get_price()          live/close quotes w/ basis + suspect rails (registry ccy authoritative)
  - IBKR history bars (MCP/ib_insync)   multi-year weekly/daily series — COMPUTE bands/discounts, never quote them
  - conditioning read (discovery_state) price path decomposition + attention: coverage count, short interest, YTD vs peers
FUNDAMENTALS CLAIMS (growth, margins, earnings level):
  - SEC XBRL companyconcept/companyfacts   audited series direct (the BBW flat-pretax find); KR names -> DART filings
  - desk/seasonality.py TICKER             per-fiscal-quarter QoQ shape + hard/easy-comp flags (MANDATORY on any 'deceleration' claim)
  - desk/capacity_check.py TICKER          utilization/occupancy/workstations from the 10-K (bench-time; NOT_DISCLOSED = a finding)
  - cap-structure pull (10-Q equity note)  BEFORE any per-share/EV/net-cash claim
PHYSICAL/OPERATIONAL CLAIMS (building, shipping, hiring, operating):
  - sentinel2_buildout / carbon-mapper     construction + methane ground truth
  - customs BOL / origin_mix               customer identity + import-origin shares
  - hiring_velocity / job-posting counts   plant/program ramps (record the baseline for re-scans)
  - restaurant_ratings / places            units-open verification
GOV/LEGAL/REGULATORY CLAIMS (tariffs, awards, litigation, filings):
  - proclamation/statute PRIMARY TEXT      the copper lesson: 'will consider' != 'scheduled' — quote the operative words
  - usaspending connector (family rollup)  award flows; DoD ~98d lag
  - CourtListener/RECAP                    federal dockets; MATERIAL categories only
  - EDGAR full-text (EFTS)                 8-K/covenant/going-concern language
MARKET-STRUCTURE CLAIMS (flows, futures, FX, positioning):
  - futures curve pulls (IBKR)             does the CURVE price the claim? (the copper step test)
  - FX series + WHT math                   net-of-withholding carry; KRW/BRL/PHP quoted WITH the metric
  - twin/CRP scanner methods               cross-border relative value w/ growth + structure guards
GRADING RULE: per finding -> {claim | tool | data result | CONFIRMED/REFUTED/PLAUSIBLE}. PLAUSIBLE = no data
check ran; verdicts may rest ONLY on CONFIRMED/REFUTED findings. If no tool fits, SAY SO explicitly — a
coverage gap is reportable, not skippable. (Route-through-pipeline doctrine; KG dispatch-index pattern.)
"""

if __name__ == "__main__":
    print(MANIFEST)
