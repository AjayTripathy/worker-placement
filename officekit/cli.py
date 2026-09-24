"""cli — the `officekit` command (A0 packaging).

    officekit init   [--dir ./office]          create the office folder (+ model slots stub)
    wp start  [--dir ./office] [--port] run the local app (onboard in the browser)
    officekit render [--dir ./office]          rebuild every page from answers.json
    officekit sync   [--dir ./office]          run registered connectors, report freshness
    officekit doctor [--check]                  install any missing connector libs, list connections

One folder is the whole product: answers.json + balance_sheet.json in, rendered
pages out. READ-ONLY beyond its own folder; never places orders.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _cmd_init(args):
    folder = Path(args.dir)
    folder.mkdir(parents=True, exist_ok=True)
    models = folder / "models.json"
    if not models.exists():
        try:
            from officekit_ai.models import DEFAULTS
            models.write_text(json.dumps(DEFAULTS, indent=1) + "\n", encoding="utf-8")
            print(f"[init] wrote {models} (BYOM slots — edit provider/model/api_key_env per slot; "
                  f"secrets NEVER go in this file, only env-var NAMES)")
        except ImportError:
            print("[init] officekit_ai not installed — no model slots written (the office "
                  "works fully without AI; install the plugin to add courts and onboarding chat)")
    print(f"[init] office folder ready: {folder.resolve()}")
    print(f"[init] next: wp start --dir {args.dir}   (onboard in the browser)")
    return 0


def _cmd_serve(args):
    from officekit.serve import main as serve_main
    argv = ["--dir", args.dir, "--port", str(args.port)]
    if getattr(args, "reload", False):
        argv.append("--reload")
    return serve_main(argv)


def _cmd_render(args):
    folder = Path(args.dir)
    answers = folder / "answers.json"
    if not answers.exists():
        print(f"[render] no answers.json in {folder} — run `wp start` and onboard first",
              file=sys.stderr)
        return 2
    from officekit.serve import build_office
    build_office(json.loads(answers.read_text(encoding="utf-8")), folder)
    print(f"[render] pages rebuilt -> {folder / 'pages'}")
    return 0


def _cmd_discover(args):
    import officekit_adapters
    results = officekit_adapters.discover()
    for r in results:
        mark = "FOUND" if r["found"] else "  —  "
        line = f"{mark}  {r['label']:45s} {r['status']:12s} {r['detail']}"
        print(line)
        if r.get("guidance"):
            print(f"       ↳ {r['guidance']}")
    found = [r for r in results if r["found"] and r["can_fetch"] and r["status"] == "ready"]
    if found:
        print(f"\n[discover] {len(found)} connection(s) ready for import — "
              f"`wp start` offers one-click position import on the onboarding page")
    return 0


def _cmd_sync(args):
    folder = Path(args.dir)
    bs = folder / "balance_sheet.json"
    if not bs.exists():
        print(f"[sync] no balance_sheet.json in {folder}", file=sys.stderr)
        return 2
    from officekit import load_balance_sheet
    from officekit import sync as oksync
    data = load_balance_sheet(bs, strict=False)
    results = oksync.apply(data, oksync.run())
    for r in results:
        print(f"[sync] {r['connector']}: {r['status']}"
              + (f" as_of {r['as_of']} ({r['age_days']}d)" if r.get("as_of") else "")
              + f" — {r['detail']}")
    if not results:
        print("[sync] no connectors registered (tenant plugins register via officekit.sync.connector)")
    return 0


def _cmd_doctor(args):
    """Make every first-class connector importable WITHOUT per-broker pip. The
    libraries are core dependencies of the product, so a normal install already
    has them; on a bare checkout this back-fills any that are missing into the
    running interpreter, then shows what's connectable."""
    import officekit_adapters as A
    missing = A.missing_connectors()
    if not missing:
        print("[doctor] all connector libraries present.")
    elif getattr(args, "check", False):
        print("[doctor] missing connector libs: " + ", ".join(missing))
        print("       run `worker-placement doctor` (no --check) to install them")
        return 1
    else:
        import subprocess
        specs = list(missing.values())
        print(f"[doctor] installing {len(specs)} connector lib(s) into "
              f"{sys.executable}: {', '.join(specs)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *specs])
        except (subprocess.CalledProcessError, OSError) as e:
            print(f"[doctor] install failed: {e}", file=sys.stderr)
            return 1
        still = A.missing_connectors()
        print("[doctor] done." if not still else f"[doctor] still missing: {', '.join(still)}")
    print()
    return _cmd_discover(args)


def _cmd_reset(args):
    """Clear the office's built state + staged imports, keeping the folder and
    models.json (your key config) so the next `serve` starts clean."""
    import shutil
    folder = Path(args.dir)
    removed = []
    for f in ("answers.json", "balance_sheet.json", "staging.json",
              "docket.json", "adjudications.jsonl", "learning.jsonl", "personal_context.json", ".flash.json"):
        p = folder / f
        if p.exists():
            p.unlink()
            removed.append(f)
    if (folder / "pages").exists():
        shutil.rmtree(folder / "pages")
        removed.append("pages/")
    print(f"[reset] cleared: {', '.join(removed) or '(nothing to clear)'}")
    print(f"[reset] kept models.json (your key config); {folder.resolve()} is ready for a fresh onboard")
    return 0


def _cmd_start(args):
    _cmd_init(args)
    import webbrowser
    import threading
    if not args.no_browser:
        timer = threading.Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:'+str(args.port)+'/start'))
        timer.daemon = True
        timer.start()
    return _cmd_serve(args)

def _cmd_login(args):
    from officekit.cloud import login
    return login()

def _cmd_migrate(args):
    from officekit.cloud import migrate
    return migrate(args.dir, replace_revision=args.replace_revision, open_browser=not args.no_browser)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="worker-placement", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, extra in (
            ("start", _cmd_start, {"port": True}),
            ("login", _cmd_login, {}),
            ("migrate", _cmd_migrate, {}),
            ("init", _cmd_init, {}),
            ("serve", _cmd_serve, {"port": True}),
            ("render", _cmd_render, {}),
            ("sync", _cmd_sync, {}),
            ("discover", _cmd_discover, {}),
            ("doctor", _cmd_doctor, {"check": True}),
            ("reset", _cmd_reset, {})):
        p = sub.add_parser(name)
        p.add_argument("--dir", default="./office", help="office folder")
        if extra.get("port"):
            p.add_argument("--port", type=int, default=8787)
            p.add_argument("--reload", action="store_true",
                           help="auto-reload on source changes (dev) — no manual restart")
        if extra.get("check"):
            p.add_argument("--check", action="store_true",
                           help="report missing connector libs without installing")
        if name in {"start", "migrate"}:
            p.add_argument("--no-browser", action="store_true", help="print the URL without opening a browser")
        if name == "migrate":
            p.add_argument("--replace-revision", help="explicitly replace this hosted snapshot digest; otherwise conflicts are refused")
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    try:
        return args.fn(args) or 0
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
