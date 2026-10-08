"""Read-only protocol checks and a visible research status, separate from trading."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from desk.odte import doctrine as D, text_overlay as E, arms as A
from desk.odte.storage import atomic_json, atomic_write


def inspect(root, name, module, now):
    result = {"name": name, "root": str(root), "status": "ready", "changed_files": []}
    try:
        saved = E.read(root/"manifest.json")
        actual = module.code_files()
        result["changed_files"] = [file for file, fingerprint in saved.get("code_files", {}).items()
                                   if actual.get(file) != fingerprint]
        m = module.protocol(root)
        if m is None:
            raise ValueError("registered manifest is missing")
        if E.timestamp(m["registered_at"]) > now + dt.timedelta(seconds=5):
            raise ValueError("registration timestamp is in the future; check the system clock and registration provenance")
        result["protocol"] = m["protocol"]
    except (ValueError, OSError, KeyError, TypeError) as exc:
        detail = f" Changed files: {', '.join(result['changed_files'])}." if result["changed_files"] else ""
        result.update(status="blocked", error=f"{type(exc).__name__}: {exc}.{detail} "
                      "Preserve the old registration and records; validate the change and register a new future experiment. "
                      "No retrospective forecasts or automatic hash acceptance.")
    return result


def check(data=None, *, now=None):
    data = Path(data or D.DATA); now = now or E.utcnow()
    checks = []
    original = data/"text_overlay"
    if (original/"manifest.json").exists():
        checks.append(inspect(original, "Original news pilot", E, now))
    arms = data/"arm_experiment"
    if (arms/"manifest.json").exists():
        checks.append(inspect(arms, "Arm experiment", A, now))
        try:
            m = A.protocol(arms)
            # Check both named sources now, even when their first use is later.
            for key, expected_key, name in (("forecast_root", "forecast_protocol", "Pilot forecast source"),
                                             ("continuation_root", "continuation_protocol", "Continuing forecast source")):
                if not m.get(key):
                    continue
                source = Path(m[key]); item = inspect(source, name, E, now)
                if item["status"] == "ready" and item["protocol"] != m[expected_key]:
                    item.update(status="blocked", error="Forecast source identity differs from the frozen arm registration. Re-register explicitly; do not substitute a source.")
                checks.append(item)
        except (ValueError, OSError, KeyError, TypeError):
            pass  # The blocking arm-manifest diagnostic above is authoritative.
    return {"checked_at": now.isoformat(), "status": "blocked" if any(c["status"] == "blocked" for c in checks)
            else "ready" if checks else "not_registered", "checks": checks, "live_enabled": False}


def publish(data=None, *, now=None):
    data = Path(data or D.DATA); result = check(data, now=now)
    path = data/"research_health.json"
    try:
        previous = E.read(path)
    except (OSError, ValueError):
        previous = {}
    changed = any(result.get(k) != previous.get(k) for k in ("status", "checks"))
    atomic_json(path, result)
    if changed:
        arm_root = data/"arm_experiment"
        try:
            # Render the saved report with a prominent status even when a code
            # freeze prevents recomputing its results. Never relabel old data.
            from desk.odte.render_arms import render
            saved = E.read(arm_root/"report.json")
            saved["readiness"] = result
            html = render(saved)
            atomic_write(arm_root/"report.html", html)
            manifest = A.checked(arm_root/"manifest.json")
            if manifest.get("page_path"):
                atomic_write(Path(manifest["page_path"]), html)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result["page_warning"] = f"Research status page could not update: {type(exc).__name__}"
            atomic_json(path, result)
    return result, changed


def log(result):
    if result["status"] == "blocked":
        print("[odte] !!! RESEARCH BLOCKED — ACTION REQUIRED; ordinary shadow capture continues !!!", flush=True)
        for item in result["checks"]:
            if item["status"] == "blocked":
                print(f"[odte] {item['name']} at {item['root']}: {item['error']}", flush=True)
    else:
        print(f"[odte] research preflight: {result['status']} ({len(result['checks'])} protocol checks)", flush=True)
    if result.get("page_warning"):
        print(f"[odte] {result['page_warning']}", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, default=D.DATA)
    args = p.parse_args()
    result, _ = publish(args.data)
    log(result)
    print(json.dumps(result, indent=2))
    if result["status"] == "blocked":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
