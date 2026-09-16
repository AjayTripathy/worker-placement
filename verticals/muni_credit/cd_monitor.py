"""cd_monitor — material-event / continuing-disclosure watch over the sleeve's CUSIPs.

Holdings monitoring (the desk's table-stakes obligation once bonds are owned): re-pulls each
CUSIP's EMMA continuing-disclosure list and reports anything NEW since the last run — 15c2-12
event notices (rating change, reserve draw, payment delinquency, failure-to-file), defeasance /
redemption notices (we'd be holding a bond about to be called), and fresh annual filings.

State: data/cd_monitor_state.json maps cusip -> set of seen (date, description) filing keys.
First run seeds the state (reports nothing); subsequent runs report only deltas.
Run:  PYTHONPATH=. python3 cd_monitor.py            (from verticals/muni_credit)
Wired into the daily re-mark cron alongside remark_buylist.py.
"""
import json, re, time, datetime, os
import emma_scraper as E
from emma_continuing_disclosure import fetch_cd, parse_cd_html

STATE = "data/cd_monitor_state.json"
URGENT = re.compile(r"defeas|redempt|refund|escrow|tender|delinquen|default|reserve draw|"
                    r"failure to provide|rating change|insurer", re.I)


def keys(rows):
    return {f"{r.get('posted_date') or r.get('period_date') or '?'}|{(r.get('group') or '')[:40]}|{(r.get('desc') or '')[:80]}"
            for r in rows}


def main():
    universe = [b["cusip"] for b in json.load(open("muni_etf_sleeve_blended.json"))["barbell"]]
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    first_run = not state
    s = E._session()
    alerts, errors = [], []
    for cu in universe:
        try:
            cd, err = fetch_cd(s, cu)
            if cd is None:
                errors.append((cu, err)); time.sleep(1); continue
            rows, _ = parse_cd_html(cd)
        except Exception as ex:
            errors.append((cu, str(ex)[:40])); time.sleep(1); continue
        now = keys(rows)
        seen = set(state.get(cu, []))
        new = sorted(now - seen)
        state[cu] = sorted(now)
        for k in new:
            urgent = bool(URGENT.search(k))
            if not first_run:
                alerts.append({"cusip": cu, "filing": k, "urgent": urgent})
        time.sleep(0.8)
    os.makedirs("data", exist_ok=True)
    json.dump(state, open(STATE, "w"))
    today = datetime.date.today()
    if first_run:
        print(f"CD-MONITOR {today}: state seeded for {len(universe)} CUSIPs "
              f"({sum(len(v) for v in state.values())} existing filings; deltas reported from next run)"
              + (f"; {len(errors)} fetch errors: {errors}" if errors else ""))
        return
    urgent = [a for a in alerts if a["urgent"]]
    print(f"CD-MONITOR {today}: {len(alerts)} new filings across {len(universe)} names; "
          f"{len(urgent)} URGENT" + (f"; {len(errors)} fetch errors" if errors else ""))
    for a in sorted(alerts, key=lambda x: not x["urgent"]):
        print(f"  {'!! ' if a['urgent'] else '   '}{a['cusip']}  {a['filing']}")


if __name__ == "__main__":
    main()
