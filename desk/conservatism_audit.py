"""conservatism_audit run-1 — per AUDIT_SPEC_CONSERVATISM.md v1.0 (frozen 2026-08-05)."""
import json, re, os, time, urllib.request, datetime

ROOT = "/Users/ajay/exalted/signalos"
OUT = os.path.join(ROOT, "desk/data/conservatism_audit")
os.makedirs(OUT, exist_ok=True)
CACHE_F = os.path.join(OUT, "prices_cache.json")
BASE = 3_400_000
TODAY = datetime.date(2026, 8, 5)
SGOV_Y = 0.043

cache = json.load(open(CACHE_F)) if os.path.exists(CACHE_F) else {}

def fetch(sym):
    if sym in cache:
        return cache[sym]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=3mo&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        js = json.loads(urllib.request.urlopen(req, timeout=15).read())
        r = js["chart"]["result"][0]
        ts = r["timestamp"]; qt = r["indicators"]["quote"][0]
        rows = []
        for i, t in enumerate(ts):
            c, lo = qt["close"][i], qt["low"][i]
            if c:
                rows.append((datetime.date.fromtimestamp(t).isoformat(), round(c, 4), round(lo or c, 4)))
        cache[sym] = rows
    except Exception as e:
        cache[sym] = {"error": str(e)[:120]}
    time.sleep(0.35)
    return cache[sym]

def series_at(rows, dstr):
    """close on first bar >= dstr; and (min low after, last close)."""
    for i, (d, c, lo) in enumerate(rows):
        if d >= dstr:
            lows = [x[2] for x in rows[i:]]
            return c, min(lows), rows[-1][1]
    return None, None, None

REJ = re.compile(r"REJECT|AVOID|FRAME-REJECT|NOT-A-|KILL\b|^PASS|\bPASS\b|DECLINE", re.I)
GATE = re.compile(r"WATCH|GATE|WAIT|STAGE|CONDITIONAL|LADDER|NOT_YET|WAIT-|PRINT-COND", re.I)
TAKEN = re.compile(r"STARTER|OWNABLE|OWN\b|HELD|HOLD|BUY|ADVANCE|DEPLOY|ACCUMULATE", re.I)
SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")

def classify(v):
    v = v or ""
    if REJ.search(v) and not TAKEN.search(v):
        return "REJECT"
    if GATE.search(v) and not TAKEN.search(v):
        return "GATED"
    if TAKEN.search(v):
        return "TAKEN"
    if GATE.search(v):
        return "GATED"
    return "UNCLASSIFIED"

def parse_size(rec):
    for field in ("note", "summary", "verdict", "conviction"):
        s = rec.get(field)
        if isinstance(s, str):
            m = SIZE_RE.search(s)
            if m:
                p = float(m.group(1))
                if 0.05 <= p <= 3.0:
                    return p / 100.0
    return 0.005


ECD = os.path.join(ROOT, "desk/data/edge_classifications")
_ec_asof = {}
for _fn in os.listdir(ECD):
    if _fn.endswith(".json"):
        try:
            _d = json.load(open(os.path.join(ECD, _fn)))
            _a = _d.get("as_of")
            if isinstance(_a, str) and re.match(r"2026-\d\d-\d\d", _a):
                for _k in {_d.get("ticker", _fn[:-5]), _fn[:-5]}:
                    _ec_asof[str(_k).upper()] = _a[:10]
        except Exception:
            pass

COURT_DATE = re.compile(r"(?:COURT (?:RESOLVED|ADJUDICATED)|court|DD|RETIRED|ADJUDICATED|re-court(?:ed)?|SWEEP|re-screen\)?)[^0-9]{0,15}(2026-\d\d-\d\d)", re.I)

def rec_date(rec, t):
    """Court date priority: batch markers > explicit court-marker dates > EC as_of > any 2026 date.
    Run-1 bug: bare first-2026-date grabbed THESIS-TEXT dates (TRAX/MFP/OTEX false misses)."""
    blob = " ".join(str(rec.get(k, "")) for k in ("verdict", "conviction", "thesis", "note", "stage", "state"))
    if "cq0804" in blob.lower():
        return "2026-08-04"
    m = COURT_DATE.search(blob)
    if m:
        return m.group(1)
    if t.upper() in _ec_asof:
        return _ec_asof[t.upper()]
    d = rec_date(rec, t)
    if isinstance(d, str) and re.match(r"2026-\d\d-\d\d", d):
        return d[:10]
    m = re.search(r"\b(2026-\d\d-\d\d)\b", blob)
    return m.group(1) if m else None

rl = json.load(open(os.path.join(ROOT, "desk/data/research_ledger.json")))
universe, review = [], []
for rec in rl["names"]:
    if not isinstance(rec, dict):
        continue
    t = rec.get("ticker", "")
    d = rec.get("date") or rec.get("as_of")
    v = rec.get("verdict", "")
    if not isinstance(v, str):
        v = json.dumps(v)
    if "_" in t or not t or len(t) > 12:
        continue
    if not d or not re.match(r"\d{4}-\d{2}-\d{2}", str(d)):
        review.append({"ticker": t, "why": "no date", "verdict": v[:60]})
        continue
    age = (TODAY - datetime.date.fromisoformat(d[:10])).days
    universe.append({"ticker": t, "date": d[:10], "age": age, "verdict": v[:100],
                     "cohort": classify(v), "size": parse_size(rec)})

spy = fetch("SPY")
assert isinstance(spy, list), "SPY fetch failed - abort, no silent default"

res = {"cohort1": [], "cohort2": [], "failed": [], "immature": 0, "review_n": len(review)}
for u in universe:
    if u["cohort"] not in ("REJECT", "GATED"):
        continue
    if u["age"] < 14:
        res["immature"] += 1
        continue
    rows = fetch(u["ticker"])
    if not isinstance(rows, list) or len(rows) < 5:
        res["failed"].append(u["ticker"])
        continue
    c0, minlow, cnow = series_at(rows, u["date"])
    if not c0:
        res["failed"].append(u["ticker"])
        continue
    s0, _, snow = series_at(spy, u["date"])
    ret = cnow / c0 - 1
    spyret = snow / s0 - 1
    excess = ret - spyret
    sz = u["size"] * BASE
    row = {**u, "ret": round(ret, 4), "spy": round(spyret, 4), "excess": round(excess, 4),
           "size_usd": round(sz), "mature30": u["age"] >= 30}
    if u["cohort"] == "REJECT":
        row["avoided_usd"] = round(-excess * sz)
        res["cohort1"].append(row)
    else:
        came_to_us = minlow <= c0 * 0.95
        row["came_to_us"] = came_to_us
        row["foregone_usd"] = 0 if came_to_us else round(max(excess, 0) * sz)
        res["cohort2"].append(row)

json.dump(cache, open(CACHE_F, "w"))
json.dump({"universe_n": len(universe), "review": review[:50]}, open(os.path.join(OUT, "universe.json"), "w"), indent=1)

c1 = res["cohort1"]; c2 = res["cohort2"]
c1m = [r for r in c1 if r["mature30"]]
avoided = sum(r["avoided_usd"] for r in c1)
precision = sum(1 for r in c1 if r["excess"] < 0) / len(c1) if c1 else 0
prec30 = (sum(1 for r in c1m if r["excess"] < 0) / len(c1m)) if c1m else None
foregone2 = sum(r["foregone_usd"] for r in c2)
never_met = [r for r in c2 if not r["came_to_us"]]
beat_rate = sum(1 for r in never_met if r["excess"] > 0) / len(never_met) if never_met else 0

summary = {
    "asof": str(TODAY), "spec": "v1.0",
    "coverage": {"classified": len(universe), "c1_n": len(c1), "c2_n": len(c2),
                 "immature_lt14d": res["immature"], "price_failed": res["failed"], "review_no_date": len(review)},
    "cohort1_rejects": {"n": len(c1), "avoided_usd": avoided, "precision_vs_spy": round(precision, 3),
                        "precision_mature30_n": len(c1m), "precision_mature30": (round(prec30, 3) if prec30 is not None else None),
                        "worst5_we_dodged": sorted(c1, key=lambda r: r["excess"])[:5],
                        "best5_we_missed": sorted(c1, key=lambda r: -r["excess"])[:5]},
    "cohort2_gated": {"n": len(c2), "never_met_n": len(never_met), "came_to_us_n": len(c2) - len(never_met),
                      "foregone_usd": foregone2, "never_met_beat_spy_rate": round(beat_rate, 3),
                      "top5_foregone": sorted(c2, key=lambda r: -r["foregone_usd"])[:5]},
}
json.dump({**summary, "cohort1_rows": c1, "cohort2_rows": c2}, open(os.path.join(OUT, "results.json"), "w"), indent=1)
print(json.dumps(summary, indent=1, default=str)[:3800])
