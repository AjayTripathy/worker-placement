# cli

`signalos` command-line entry points. Installed as `signalos` script via `pyproject.toml`.

## Commands

```bash
signalos run --zip 48238 [--deeds] [--llm] [--db signalos.db]
signalos report [--zip 48238] [--tier high|medium|low|exempt] [--csv out.csv]
```

- `run` — fetch records, compute gaps, apply rules, persist signals to SQLite store
- `report` — read from SQLite store, print/export tabulated signals

Currently wired to the Detroit property-tax jurisdiction (`verticals/property_tax/jurisdictions/detroit/`). Other verticals add themselves to the registry via their `__init__.py` and become invokable from the same CLI.

## Files

| File | Role |
|---|---|
| `main.py` | Click command group, instantiates `SignalEngine` per (vertical, jurisdiction) |
| `report.py` | Rich-formatted tables, CSV export |
