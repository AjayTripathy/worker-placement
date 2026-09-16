"""Re-process records with kml_parse_failed status using the patched parser.

After the V2 scan finishes, this script:
  - Reloads forest_scan_results_v2.json and mangrove_scan_results.json
  - Identifies records with kml_parse_failed status
  - Re-runs each through the appropriate scoring function (now with xmlns:xsi
    + KMZ handling)
  - Replaces the failed record in place; saves after each
"""
from __future__ import annotations

import json
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
RS_CACHE = HERE / "rs_cache"

sys.path.insert(0, str(HERE))
from scan_forest_v2 import score_project_synthetic_control, _timeout_handler, TimeoutError as SAlarmTO
from score_mangrove import score_mangrove


def reprocess_forest():
    out_path = DATA_DIR / "forest_scan_results_v2.json"
    with open(out_path) as f:
        results = json.load(f)
    with open(DATA_DIR / "forest_inventory.json") as f:
        inv = json.load(f)
    inv_by_id = {str(p["id"]): p for p in inv}

    # Retry: kml_parse_failed (parser improvements), implausible_area_*
    # (envelope filter), and long-elapsed hard_timeouts (leftover from buggy
    # pre-fix runs).
    def _needs_retry(r):
        s = r.get("status", "")
        if s == "kml_parse_failed":
            return True
        if "implausible_area" in s:
            return True
        if s == "hard_timeout_180s" and (r.get("elapsed_s", 0) or 0) > 300:
            return True
        return False
    failed_idx = [i for i, r in enumerate(results) if _needs_retry(r)]
    print(f"Forest: {len(failed_idx)} records to retry", file=sys.stderr)
    n_recovered = 0
    for k, i in enumerate(failed_idx):
        r = results[i]
        pid = str(r["id"])
        p = inv_by_id.get(pid)
        if not p:
            continue
        sp = RS_CACHE / f"{pid}.json"
        if not sp.exists():
            continue
        with open(sp) as f:
            summary = json.load(f)

        t0 = time.time()
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(120)
        try:
            new_r = score_project_synthetic_control(p, summary)
        except SAlarmTO:
            new_r = {"id": pid, "status": "timeout_120s"}
        except Exception as e:
            new_r = {"id": pid, "status": f"score_exception: {str(e)[:120]}"}
        finally:
            signal.alarm(0)
        elapsed = time.time() - t0
        new_r["elapsed_s"] = round(elapsed, 1)
        new_status = new_r.get("severity", new_r.get("status", "?"))
        if new_status not in ("kml_parse_failed", "?"):
            n_recovered += 1
        results[i] = new_r
        print(f"  [{k+1}/{len(failed_idx)}] {pid:>5}  {elapsed:>5.1f}s  {new_status[:30]:<30}  {p['name'][:50]}",
              file=sys.stderr, flush=True)
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
    print(f"\nForest recovery: {n_recovered}/{len(failed_idx)} now have non-failed status", file=sys.stderr)


def reprocess_mangrove():
    out_path = DATA_DIR / "mangrove_scan_results.json"
    if not out_path.exists():
        print("No mangrove_scan_results.json yet — skipping", file=sys.stderr)
        return
    with open(out_path) as f:
        results = json.load(f)
    with open(DATA_DIR / "forest_inventory.json") as f:
        inv = json.load(f)
    inv_by_id = {str(p["id"]): p for p in inv}

    # Retry any record without a severity tier (kml_parse_failed, kml_not_cached,
    # implausible_area_*, etc.). The newly patched parser + envelope filter +
    # downloaded KMLs should resolve most of them.
    failed_idx = [i for i, r in enumerate(results) if not r.get("severity")]
    print(f"Mangrove: {len(failed_idx)} records to retry", file=sys.stderr)
    n_recovered = 0
    for k, i in enumerate(failed_idx):
        r = results[i]
        pid = str(r["id"])
        p = inv_by_id.get(pid)
        if not p:
            continue
        sp = RS_CACHE / f"{pid}.json"
        if not sp.exists():
            continue
        with open(sp) as f:
            summary = json.load(f)
        t0 = time.time()
        try:
            new_r = score_mangrove(p, summary)
        except Exception as e:
            new_r = {"id": pid, "status": f"score_exception: {str(e)[:120]}"}
        elapsed = time.time() - t0
        new_r["elapsed_s"] = round(elapsed, 1)
        new_status = new_r.get("severity", new_r.get("status", "?"))
        if new_status not in ("kml_parse_failed", "?"):
            n_recovered += 1
        results[i] = new_r
        print(f"  [{k+1}/{len(failed_idx)}] {pid:>5}  {elapsed:>5.1f}s  {new_status[:30]:<30}  {(p.get('name') or '')[:50]}",
              file=sys.stderr, flush=True)
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
    print(f"\nMangrove recovery: {n_recovered}/{len(failed_idx)} now have non-failed status", file=sys.stderr)


def main():
    if "--mangrove-only" in sys.argv:
        reprocess_mangrove()
        return
    if "--forest-only" in sys.argv:
        reprocess_forest()
        return
    reprocess_forest()
    print()
    reprocess_mangrove()


if __name__ == "__main__":
    main()
