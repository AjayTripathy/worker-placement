"""Entry points for detectors, connectors and sources: the SUBJECT is always an argument.

A module in this tree verifies claims about whoever it is pointed at. It names
no company, person, address or ticker of its own — not in its logic, and not in
its `__main__`. Run with no subject, an entry point prints its usage and exits;
it never falls back to "the deal it was first built for". A private engagement's
subjects live under private_deals/ (verticals/private_root.py); worked PUBLIC
examples live beside the module in an `examples/` folder and are passed by path.

    python -m verticals.buyside_dd.connectors.osha_establishment --entity "Some Builder LLC" --state TX
    python -m verticals.public_co.m_sources.mw_lifecycle 0000000000 --asof 2025-05-15
    python -m verticals.muni_credit.detectors.covenant_breach --selftest

tests/test_parametrized_modules.py enforces this for every indexed module.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date

REQUEST_FIELDS = ("entity", "person", "address", "parcel", "area", "state", "city", "year")


def _pairs(items):
    out = {}
    for item in items or []:
        key, sep, value = item.partition("=")
        if not sep or not key:
            raise SystemExit("--extra takes key=value")
        try:
            out[key] = json.loads(value)
        except ValueError:
            out[key] = value
    return out


def connector_main(connector_cls, *, show=8, argv=None):
    """CLI for any BaseConnector: build the ConnectorRequest from arguments, print what came back."""
    from verticals.buyside_dd.connectors.base import ConnectorRequest
    ap = argparse.ArgumentParser(prog=connector_cls.__module__.rsplit(".", 1)[-1],
                                 description=(connector_cls.__doc__ or "").strip().split("\n")[0] or None)
    ap.add_argument("--entity", action="append", help="company / LLC / ticker; repeat to query several")
    ap.add_argument("--person", help="a named individual")
    ap.add_argument("--address")
    ap.add_argument("--parcel", help="parcel id")
    ap.add_argument("--area", help="zip, county or MSA")
    ap.add_argument("--state", help="2-letter")
    ap.add_argument("--city")
    ap.add_argument("--year", type=int)
    ap.add_argument("--extra", action="append", metavar="KEY=VALUE", help="connector-specific option; repeatable")
    ap.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = ap.parse_args(argv)
    if not any(getattr(args, f) for f in REQUEST_FIELDS):
        ap.error("no subject: pass at least one of --" + ", --".join(REQUEST_FIELDS))
    connector = connector_cls()
    for entity in args.entity or [None]:
        result = connector.query(ConnectorRequest(
            entity_name=entity, person_name=args.person, address=args.address, parcel_id=args.parcel,
            geographic_area=args.area, state=args.state, city=args.city, year=args.year, extra=_pairs(args.extra)))
        if args.json:
            print(result.model_dump_json(indent=2) if hasattr(result, "model_dump_json") else result.json(indent=2))
            continue
        print(f"{entity or args.person or args.address or ''}: success={result.success} "
              f"error={result.error_kind}/{result.error_detail} observations={len(result.observations)}")
        for o in result.observations[:show]:
            value = o.value
            if isinstance(value, list) and len(value) > 3:
                value = f"(n={len(value)}) {value[:3]} ..."
            print(f"  {o.attribute} = {str(value)[:200]} {o.value_unit or ''}".rstrip())


def issuer_main(query, *, description=None, options=(), drop=(), argv=None):
    """CLI for a `query(cik, asof, **options)` source. options: (flag, type, help) — all optional."""
    ap = argparse.ArgumentParser(prog=query.__module__.rsplit(".", 1)[-1], description=description)
    ap.add_argument("cik", help="issuer CIK, 10 digits")
    ap.add_argument("--asof", default=date.today().isoformat(), help="cutoff date (default: today)")
    for flag, kind, text in options:
        ap.add_argument("--" + flag.replace("_", "-"), dest=flag, type=kind, help=text)
    args = ap.parse_args(argv)
    extra = {flag: getattr(args, flag) for flag, _, _ in options if getattr(args, flag) is not None}
    result = query(args.cik.zfill(10), args.asof, **extra)
    print(json.dumps({k: v for k, v in result.items() if k not in drop} if isinstance(result, dict) else result,
                     indent=2, default=str))
    return result


def load_json(path):
    with open(path) as handle:
        return json.load(handle)


def selftest_or_input(description, *, selftest=None, inputs=(), argv=None):
    """Parser for pure-logic detectors: `--selftest` (synthetic cases) and/or named JSON inputs.

    inputs: (flag, help). Returns the parsed args; errors if neither a selftest nor every input was given.
    """
    ap = argparse.ArgumentParser(description=description)
    for flag, text in inputs:
        ap.add_argument("--" + flag, help=text)
    if selftest:
        ap.add_argument("--selftest", action="store_true", help="run the built-in synthetic cases")
    args = ap.parse_args(argv)
    if selftest and args.selftest:
        selftest()
        sys.exit(0)
    required = [f for f, _ in inputs if not f.startswith("?")]
    if not inputs or any(getattr(args, f.replace("-", "_")) is None for f in required):
        ap.error("pass " + " and ".join("--" + f for f in required) + (" or --selftest" if selftest else ""))
    return args


_REQUIRED = object()


def arg(position, name, default=_REQUIRED, *, usage=None):
    """Positional argument for a small script. A SUBJECT has no default: missing -> usage, exit 2."""
    if len(sys.argv) > position and not sys.argv[position].startswith("--"):
        return sys.argv[position]
    if default is _REQUIRED:
        prog = (sys.argv[0] or "module").rsplit("/", 1)[-1]
        sys.stderr.write(f"usage: {prog} {usage or '<' + name + '> ...'}\n{prog}: error: missing <{name}> "
                         "(this module names no subject of its own)\n")
        sys.exit(2)
    return default


def today():
    return date.today().isoformat()
