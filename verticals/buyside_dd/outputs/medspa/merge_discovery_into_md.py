"""Patch COSMECEUTICAL_UNIVERSE.md placeholders with discovery_state regimes from the JSON."""
import json, re

BASE = "/Users/ajay/exalted/signalos/verticals/buyside_dd/outputs/medspa"
with open(f"{BASE}/cosmeceutical_discovery_results.json") as f:
    rows = json.load(f)
by_t = {r["ticker"]: r for r in rows}

def cell(t):
    r = by_t.get(t)
    if not r: return "n/a"
    if r.get("error"): return f"ERR ({r['error'][:30]})"
    reg = r.get("regime")
    a = r.get("attention_score"); p = r.get("positioning_score")
    return f"{reg} (attn {a}, pos {p})"

md_path = f"{BASE}/COSMECEUTICAL_UNIVERSE.md"
with open(md_path) as f:
    md = f.read()

for t in ["ODD","ELF","EL","SKIN","SXT","ASH","CDXS","KVUE","COTY","NUS","OLPX"]:
    md = md.replace(f"__DISC_{t}__", cell(t))

# Build full per-name table (US names; foreign tagged)
lines = ["| Ticker | Regime | attention | positioning | confidence | foreign |",
         "|--------|--------|-----------|-------------|------------|---------|"]
for r in rows:
    lines.append(f"| {r['ticker']} | {r.get('regime','ERR')} | {r.get('attention_score')} | "
                 f"{r.get('positioning_score')} | {r.get('confidence')} | {r.get('foreign_primary')} |")
md = md.replace("__DISCOVERY_TABLE__", "\n".join(lines))

with open(md_path, "w") as f:
    f.write(md)
print("patched. regimes:")
for r in rows:
    print(" ", r["ticker"].ljust(11), r.get("regime"), r.get("error",""))
