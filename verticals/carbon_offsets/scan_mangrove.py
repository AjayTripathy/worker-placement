"""Batch-score all mangrove projects in the Verra inventory.

Filters inventory to projects with 'mangrove' in name, runs each through
score_mangrove(), saves to data/mangrove_scan_results.json.

Resumable: skips projects already in the results file.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from score_mangrove import score_mangrove

HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
RS_CACHE = HERE / "rs_cache"


def main():
    with open(DATA_DIR / "forest_inventory.json") as f:
        inv = json.load(f)

    targets = [
        p for p in inv
        if "mangrove" in (p.get("name") or "").lower()
        and p.get("has_summary") and p.get("n_kml_docs", 0) > 0
    ]
    print(f"Mangrove targets: {len(targets)}", file=sys.stderr)

    out_path = DATA_DIR / "mangrove_scan_results.json"
    results = []
    if out_path.exists():
        with open(out_path) as f:
            results = json.load(f)
    done_ids = {str(r["id"]) for r in results}
    print(f"Already done: {len(done_ids)}", file=sys.stderr)

    t_start = time.time()
    for i, p in enumerate(targets):
        pid = str(p["id"])
        if pid in done_ids:
            continue
        sp = RS_CACHE / f"{pid}.json"
        if not sp.exists():
            print(f"  [{i+1}/{len(targets)}] {pid} — no rs_cache summary, skipping", file=sys.stderr)
            continue
        with open(sp) as f:
            summary = json.load(f)

        t0 = time.time()
        try:
            r = score_mangrove(p, summary)
        except Exception as e:
            r = {"id": pid, "name": p.get("name"), "status": f"score_exception: {str(e)[:120]}"}
        elapsed = time.time() - t0
        r["elapsed_s"] = round(elapsed, 1)
        results.append(r)

        sev = r.get("severity", r.get("status", "?"))[:25]
        ratio = r.get("ratio_observed_to_claimed")
        ratio_s = f"{ratio:.2f}" if ratio is not None else "—"
        print(f"  [{i+1}/{len(targets)}] {pid:>5}  {elapsed:>5.1f}s  {sev:<25}  ratio={ratio_s:>6}  {p['name'][:50]}",
              file=sys.stderr, flush=True)

        # Save every result
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

    print(f"\nTotal: {(time.time()-t_start)/60:.1f} min, {len(results)} results", file=sys.stderr)
    print(f"Saved to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
