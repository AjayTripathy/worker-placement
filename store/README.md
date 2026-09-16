# store

Persistence layer. SQLite is the only backend currently.

## Files

| File | Role |
|---|---|
| `sqlite.py` | `SQLiteSignalStore` implementing the `SignalStore` protocol. Tables: `signals`, `runs`, `records_cache`, `rule_matches`. Handles record cache TTL per Source.cache_ttl_days. |

The store has two responsibilities:

1. **Signal persistence** — every Signal a SignalEngine produces is written here so `signalos report` can query it later
2. **Record cache** — Sources can be slow (web scrapes, paid APIs); cached fetches keyed by `(source_id, entity_id, fetched_at)` with TTL per Source

Default DB path is `signalos.db` in the working directory; override with `--db`.
