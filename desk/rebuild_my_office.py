"""rebuild_my_office — reconstruct the principal's real office (~/office) from a
pinned local seed, fast (principal-directed 2026-09-07).

The point: you can wipe ~/office to experience fresh onboarding, then get your
real book back with ONE command — no dependence on a timestamped backup copy or
on a live TWS/gateway. The seed lives OUTSIDE the repo, in ~/.worker-placement/,
so real financials never enter git.

  ~/.worker-placement/office_seed.json        the canonical `answers` (source of truth)
  ~/.worker-placement/office_seed.meta.json   {expected_nw, n_input_sleeves, office_id}

    python3 -m desk.rebuild_my_office                 # rebuild -> ~/office
    python3 -m desk.rebuild_my_office --into /tmp/x   # rebuild into a test dir
    python3 -m desk.rebuild_my_office --check         # rebuild in a temp dir, verify NW, discard

Refreshing the seed after you legitimately change holdings: re-onboard/adjust in
the app, then `--save-seed` snapshots the current ~/office answers back to the
seed (+ recomputes the expected NW).
"""
from __future__ import annotations

import json
from pathlib import Path

SEED_DIR = Path.home() / ".worker-placement"
SEED = SEED_DIR / "office_seed.json"
META = SEED_DIR / "office_seed.meta.json"
DEFAULT_TARGET = Path.home() / "office"


def load_seed() -> dict:
    if not SEED.exists():
        raise FileNotFoundError(f"no office seed at {SEED} — run --save-seed from a built ~/office first")
    return json.loads(SEED.read_text())


def load_meta() -> dict:
    return json.loads(META.read_text()) if META.exists() else {}


def rebuild(target=DEFAULT_TARGET) -> dict:
    """Build the office from the seed into `target`. Returns the balance sheet."""
    from officekit.serve import build_office
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    return build_office(load_seed(), target)


def networth(data) -> float:
    from officekit import build_model
    return build_model(data)["NW"]


def save_seed(source=DEFAULT_TARGET) -> dict:
    """Snapshot a built office's answers back to the seed and recompute meta."""
    from officekit import build_model, load_balance_sheet
    source = Path(source)
    ans = json.loads((source / "answers.json").read_text())
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    SEED.write_text(json.dumps(ans, indent=1, ensure_ascii=False) + "\n")
    m = build_model(load_balance_sheet(source / "balance_sheet.json", strict=False))
    meta = {"expected_nw": round(m["NW"]), "n_input_sleeves": len(ans.get("sleeves", [])),
            "office_id": ans.get("office_id"), "sourced_from": str(source)}
    META.write_text(json.dumps(meta, indent=1) + "\n")
    return meta


def main(argv=None):
    import argparse
    import tempfile
    ap = argparse.ArgumentParser(prog="desk.rebuild_my_office", description=__doc__.splitlines()[0])
    ap.add_argument("--into", default=None, help="target folder (default ~/office)")
    ap.add_argument("--check", action="store_true", help="rebuild in a temp dir, verify NW, discard")
    ap.add_argument("--save-seed", action="store_true", help="snapshot ~/office answers -> the seed")
    a = ap.parse_args(argv)

    if a.save_seed:
        meta = save_seed()
        print(f"[rebuild_my_office] seed saved from {DEFAULT_TARGET} — expected NW ${meta['expected_nw']:,}")
        return

    exp = load_meta().get("expected_nw")
    if a.check:
        with tempfile.TemporaryDirectory() as tmp:
            nw = networth(rebuild(tmp))
        ok = exp is None or abs(nw - exp) <= 2
        print(f"[rebuild_my_office] check: NW ${nw:,.0f}" +
              (f" vs expected ${exp:,} — {'OK' if ok else 'MISMATCH'}" if exp else ""))
        return

    target = Path(a.into) if a.into else DEFAULT_TARGET
    nw = networth(rebuild(target))
    tie = f" (ties to expected ${exp:,})" if exp and abs(nw - exp) <= 2 else ""
    print(f"[rebuild_my_office] rebuilt {target} — NW ${nw:,.0f}{tie}. "
          f"Serve it: python3 -m officekit.serve --dir {target}")


if __name__ == "__main__":
    main()
