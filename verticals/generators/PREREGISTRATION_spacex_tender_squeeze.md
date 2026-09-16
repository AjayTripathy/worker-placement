# PRE-REGISTRATION: SpaceX tender-window proxy-hedge unwind (frozen 2026-07-05)

## Hypothesis (user-originated, corrected 2026-07-05)
Restricted SpaceX holders cannot collar/hedge their stock directly (transfer+hedging
prohibitions on private shares) -> the available hedge is SHORTING the value-correlated
public space-theme basket (ASTS/LUNR/BKSY; NOT the Starlink victims — the hedge-the-prey
fallacy). Consistent evidence: those three carry 20-38% SI vs 7-8% on victims, ~1.5% on
primes. Such hedges are STICKY: they unwind on SpaceX LIQUIDITY EVENTS (the ~biannual
tenders), not on public-name fundamentals.

## Detection (built, live: desk/squeeze_watch.py — T+1, not the T+24d FINRA SI print)
FINRA daily short-volume ratio >=10pp under the 20d mean, >=2 consecutive days, on
>=2 of the 3 basket names SIMULTANEOUSLY = the fingerprint. One name = noise
(2026-07-02 baseline: LUNR solo-covering on NASA news while ASTS/BKSY normal = the
discrimination working).

## The trade (pre-committed; NOT armed until first evidence OR a dated tender)
- ON SYNCHRONIZED FINGERPRINT (mid-window catch): the covering of a 20%+ SI basket takes
  days-to-weeks — enter SAME WEEK, small: 0.5% split across the 2+ covering names
  (equity, or calls <=0.25% premium if IV isn't already pumped — buying premium is
  allowed; selling never). Exit: 15 trading days or +20%, whichever first. This is a
  FLOW trade; the fundamentals are explicitly not owned.
- ON A DATED TENDER (the anticipatory arm, better EV if the calendar is knowable):
  enter 2-3 weeks BEFORE the window, same sizing, exit INTO the window. Requires the
  tender calendar (research task open). First cycle = minimum size (mechanism unevidenced);
  a confirmed fingerprint upgrades the NEXT cycle to conviction sizing.
- NULL branch: two tender windows with NO synchronized covering = the mechanism is
  refuted; retire the watch, keep the KG entry.

## Contamination guards
- LUNR/ASTS catalyst calendar checked before attribution (launches/FCC/NASA awards
  produce idiosyncratic covering).
- A marketwide risk-off short-cover (SPY squeeze days) voids the signal.


## AMENDMENT 2026-07-05 (same-day, pre-outcome): TENDERS -> LOCKUP RELEASES
The tender program is DEAD — SpaceX IPO'd (SPCX, Jun-12-2026, $135 -> $162.68; the Dec-2025
$800B round was explicitly the final tender). The mechanism SURVIVES AND SHARPENS: locked
holders (tiered 180-day lockup, standard no-hedge covenants — VERIFY in the 424B4) still
cannot hedge SPCX directly; proxy shorts remain their only hedge UNTIL THEIR TRANCHE RELEASES.
THE NEW CALENDAR (secondary-sourced; confirm vs the prospectus):
  - ~late-Jul/early-Aug 2026: 20% release post-Q2 earnings  <- THE FIRST WINDOW, weeks away
  - Aug-Oct: ~7% tranches every 2-4wks; post-Q3: ~28%
  - Dec-8-2026: full 180d expiry (the max-supply event)
  - Jun-13-2027: Musk + institutional blocks
  - PRICE ACCELERATOR: SPCX >~$175.50 on 5-of-10 days releases supply EARLY (spot $162.68,
    ~8% below — monitor).
ARMS UPDATED: the anticipatory leg keys on the RELEASE dates (enter 2-3wks before a tranche,
exit into it); the fingerprint leg unchanged (squeeze_watch, live daily); the null branch is
now TWO RELEASE WINDOWS (the Aug tranche + Dec-8) with no synchronized covering = retire.
NOTE the two-sided flow at releases: proxy-hedge COVERING (bullish the basket) coincides w/
SPCX SUPPLY (bearish SPCX) — the pair expression (long basket / short-SPCX-via-put? no
premium-selling; puts are buyable) is noted but NOT pre-committed.