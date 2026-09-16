"""cds_activity_watch — the CREDIT-DEFAULT-SWAP leg of the AI-break tripwires (principal ask 2026-09-12).

WHAT IT SEES (honestly): single-name CDS SPREADS are not available without a Markit/Bloomberg feed.
What IS public is DTCC's Trade Information Warehouse quarterly single-name CDS ACTIVITY file:
per reference entity — clearing dealers, average daily notional (USD eq), trades/day, doc-clause
mix. That is POSITIONING and MARKET-EXISTENCE, not price: a hedge market forming or deepening on an
AI-capex issuer (dealers up, notional/day up) is the tell that credit desks are pricing a default
scenario at all. Two facts from the Q3-2025 file that frame the leg: ORACLE CORPORATION — 8 dealers,
$75M/day, 6 trades/day (an active market); COREWEAVE — ABSENT (no cleared single-name market yet).
CoreWeave APPEARING in a future file is a fire by itself. Cadence: quarterly, published with a lag —
diligence/regime grade, not an intraday tripwire; the FRED OAS z-fires on the weekly dashboard are
the fast broad leg, and desk.models.ai_credit_basis carries the Merton distance-to-default proxy.

Fires (state-diffed, one alert per new file):
  NEW-FILE           a new quarterly single-name file posted (always emailed: the leg is slow, the
                     principal must see every print)
  AI-ACTIVITY-UP     any watched AI-capex entity: avg daily notional +50% QoQ OR clearing dealers +3
  CANARY-LISTED      a watched neocloud (COREWEAVE / CORE SCIENTIFIC / NEBIUS / IREN / APPLIED
                     DIGITAL / LAMBDA) appears for the first time
Data: desk/data/cds_activity/{files, state.json}. Registered weekly in desk/registry.py.
    python3 -m desk.cds_activity_watch [--dry]
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "desk" / "data" / "cds_activity"
STATE = DATA / "state.json"
PAGE = "https://www.dtcc.com/repository-otc-data"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"

# watched reference entities (substring match on DTCC's upper-case entity names)
AI_CAPEX = {"ORACLE": "ORCL", "AMAZON.COM": "AMZN", "META PLATFORMS": "META", "ALPHABET": "GOOGL",
            "MICROSOFT": "MSFT", "DELL": "DELL", "BROADCOM": "AVGO", "INTEL": "INTC", "MICRON": "MU",
            "SOFTBANK": "9984.T", "NVIDIA": "NVDA", "SUPER MICRO": "SMCI", "ARISTA": "ANET",
            "EQUINIX": "EQIX", "DIGITAL REALTY": "DLR", "VERTIV": "VRT"}
CANARIES = {"COREWEAVE": "CRWV", "CORE SCIENTIFIC": "CORZ", "NEBIUS": "NBIS", "IREN": "IREN",
            "APPLIED DIGITAL": "APLD", "LAMBDA": "LAMBDA", "CRUSOE": "CRUSOE", "XAI": "XAI", "OPENAI": "OPENAI"}


def _get(url: str, binary: bool = False, timeout: int = 60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
    return b if binary else b.decode("utf-8", "ignore")


def list_files(page_html: str) -> list[dict]:
    """Single-name quarterly files on the DTCC page: [{name, url, quarter}] newest first."""
    s = page_html.replace("\\/", "/").replace('\\"', '"').replace("\\u0026", "&")
    links = sorted(set(re.findall(r"//files\.dtcc\.com/download/assets/[^\"\s<>\\]+", s)))
    out = []
    for l in links:
        m = re.search(r"Single-Name-?(Q[1-4])-?(20\d\d)", l, re.I)
        if m:
            out.append({"name": f"{m.group(2)}{m.group(1).upper()}", "url": "https:" + l,
                        "quarter": f"{m.group(2)}-{m.group(1).upper()}"})
    seen, uniq = set(), []
    for f in sorted(out, key=lambda x: x["name"], reverse=True):
        if f["name"] not in seen:
            seen.add(f["name"]); uniq.append(f)
    return uniq


def parse_file(path: Path) -> list[dict]:
    """Rows: entity, region, index_constituent, dealers, avg_monthly_dealers, notional_per_day, trades_per_day."""
    import pandas as pd
    df = pd.read_excel(path, sheet_name=0, header=None)
    rows = []
    for _, r in df.iterrows():
        ent = str(r[0]).strip()
        if not ent or ent.upper() in ("NAN", "REFERENCE ENTITY"):
            continue
        def num(x):
            try:
                return float(x)
            except Exception:
                return None
        rows.append({"entity": ent.upper(), "region": str(r[1]), "index_constituent": str(r[2]) == "Y",
                     "dealers": num(r[3]), "avg_monthly_dealers": num(r[4]),
                     "notional_per_day": num(r[5]), "trades_per_day": num(r[6]), "doc_clause": str(r[7])})
    return rows


def watched(rows: list[dict]) -> dict:
    out = {}
    for r in rows:
        for key, tk in {**AI_CAPEX, **CANARIES}.items():
            if key in r["entity"] and tk not in out:
                out[tk] = {**r, "watch_key": key, "canary": key in CANARIES}
    return out


def diff(prev: dict | None, cur: dict) -> list[str]:
    fires = []
    for tk, r in cur.items():
        p = (prev or {}).get(tk)
        if r["canary"] and p is None:
            fires.append(f"CANARY-LISTED {tk} ({r['entity']}): first cleared single-name CDS appearance — "
                         f"{r['dealers']:.0f} dealers, ${(r['notional_per_day'] or 0)/1e6:.1f}M/day")
        if p and p.get("notional_per_day") and r.get("notional_per_day"):
            g = r["notional_per_day"] / p["notional_per_day"] - 1
            dd = (r.get("dealers") or 0) - (p.get("dealers") or 0)
            if g >= 0.5 or dd >= 3:
                fires.append(f"AI-ACTIVITY-UP {tk}: notional/day {g:+.0%} QoQ (${p['notional_per_day']/1e6:.1f}M -> "
                             f"${r['notional_per_day']/1e6:.1f}M), dealers {p.get('dealers'):.0f} -> {r.get('dealers'):.0f}")
    for tk, r in cur.items():
        if r["canary"] and (prev or {}).get(tk) is None and tk in (prev or {}):
            pass
    return fires


def run(dry: bool = False) -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    st = json.loads(STATE.read_text()) if STATE.exists() else {"files": {}, "series": {}, "alerted": []}
    files = list_files(_get(PAGE))
    new = []
    for f in files:
        dest = DATA / f"single_name_{f['name']}.xlsx"
        if not dest.exists():
            try:
                dest.write_bytes(_get(f["url"], binary=True))
                new.append(f["name"])
            except Exception as e:
                st.setdefault("errors", []).append(f"{f['name']}: {type(e).__name__}")
                continue
        if f["name"] not in st["series"]:
            try:
                st["series"][f["name"]] = watched(parse_file(dest))
                st["files"][f["name"]] = {"url": f["url"], "quarter": f["quarter"],
                                          "fetched": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"}
            except Exception as e:
                st.setdefault("errors", []).append(f"parse {f['name']}: {type(e).__name__}")
    quarters = sorted(st["series"])
    fires = []
    if quarters:
        cur = st["series"][quarters[-1]]
        prev = st["series"][quarters[-2]] if len(quarters) > 1 else None
        fires = diff(prev, cur)
        absent = [tk for k, tk in CANARIES.items() if tk not in cur]
        st["latest"] = {"quarter": quarters[-1], "watched": {tk: {k: r[k] for k in ("entity", "dealers", "notional_per_day", "trades_per_day", "index_constituent")}
                                                                for tk, r in cur.items()},
                        "canaries_absent": absent, "fires": fires, "new_files_this_run": new}
    st["asof"] = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    if not dry:
        STATE.write_text(json.dumps(st, indent=1))
        if new or fires:
            key = f"{quarters[-1] if quarters else 'none'}|{len(fires)}"
            if key not in st["alerted"]:
                try:
                    from desk.mailer import send_raw
                    body = (f"DTCC single-name CDS activity — latest quarter {quarters[-1] if quarters else '?'}\n"
                            f"New files: {new}\nFires:\n" + "\n".join(f"- {f}" for f in fires) + "\n\nWatched:\n" +
                            "\n".join(f"- {tk}: {r['entity']} dealers {r['dealers']} notional/day ${(r['notional_per_day'] or 0)/1e6:.1f}M"
                                      for tk, r in st['latest']['watched'].items()) +
                            f"\n\nCanaries ABSENT (no cleared CDS market): {st['latest']['canaries_absent']}\n"
                            "This leg is quarterly and lagged: a hedge market forming is the tell, not the spread.")
                    send_raw(f"CDS ACTIVITY: {'FIRES ' + str(len(fires)) if fires else 'new DTCC file'} — AI-break leg", body)
                    st["alerted"].append(key)
                    STATE.write_text(json.dumps(st, indent=1))
                except Exception as e:
                    print(f"[cds_activity_watch] mail failed: {e}")
    return st.get("latest", {"quarters": quarters})


if __name__ == "__main__":
    print(json.dumps(run(dry="--dry" in sys.argv), indent=1)[:4000])
