"""store — the S1 store contract (PIPELINE_ARCHITECTURE §S1).

Every pipeline JSON store R/W goes through here: MERGE-only upserts with a key
function, atomic replace (tmp+rename), corrupt-file backup, provenance stamp, and
schema validation on write. Promotes the pattern BROKEN_PRINTS.json proved locally;
exists because the overwrite-clobber bug has recurred across shared stores.

Adoption is on-touch: writers migrate as they're edited, never wholesale.

  from desk.store import Store
  s = Store("desk/data/research_ledger.json", schema="research_ledger",
            list_path="names", key=lambda n: n["ticker"])
  s.upsert(rows, generated_by="europe_trap_batch2")     # merge by key, atomic
  s.read()                                              # dict payload (validated shape)
"""
from __future__ import annotations

import datetime
import json
import os
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


class StoreError(RuntimeError):
    """Loud failure: an invalid or partial write must never look like data."""


def _now() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _load_schema(name: str) -> dict | None:
    p = SCHEMA_DIR / f"{name}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def _validate(payload, schema_name: str | None):
    if not schema_name:
        return
    schema = _load_schema(schema_name)
    if schema is None:
        return  # schema not yet written for this store — contract still gives atomicity
    try:
        import jsonschema
    except ImportError:
        return  # validation is best-effort if the lib is absent; atomicity is not
    try:
        jsonschema.validate(payload, schema)
    except jsonschema.ValidationError as e:
        raise StoreError(f"schema '{schema_name}' rejected write: {e.message} at {list(e.absolute_path)}") from e


class Store:
    def __init__(self, rel_path: str | Path, schema: str | None = None,
                 list_path: str | None = None, key=None):
        self.path = (ROOT / rel_path) if not Path(rel_path).is_absolute() else Path(rel_path)
        self.schema = schema
        self.list_path = list_path  # dot-free top-level key holding the row list, e.g. "names"
        self.key = key

    # ---------- read ----------
    def read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text())
        except json.JSONDecodeError as e:
            raise StoreError(f"{self.path.name} is corrupt JSON: {e}") from e

    def rows(self) -> list:
        d = self.read()
        return d.get(self.list_path, []) if self.list_path else d if isinstance(d, list) else []

    # ---------- write ----------
    def _atomic_write(self, payload):
        _validate(payload, self.schema)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            # corrupt-file backup: keep one .bak of the pre-write state
            try:
                json.loads(self.path.read_text())
                shutil.copy2(self.path, self.path.with_suffix(self.path.suffix + ".bak"))
            except json.JSONDecodeError:
                # existing file already corrupt — preserve it under a dated name for forensics
                shutil.copy2(self.path, self.path.with_suffix(
                    self.path.suffix + f".corrupt_{datetime.datetime.utcnow():%Y%m%d%H%M%S}"))
        tmp = self.path.with_suffix(self.path.suffix + f".tmp{os.getpid()}")
        tmp.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        os.replace(tmp, self.path)

    def write(self, payload: dict, generated_by: str):
        """Full-payload write with provenance. Prefer upsert() for row stores."""
        payload = dict(payload)
        payload["_meta"] = {"asof": _now(), "generated_by": generated_by,
                            "run_id": uuid.uuid4().hex[:12], "schema": self.schema}
        self._atomic_write(payload)
        return payload["_meta"]

    def upsert(self, new_rows: list, generated_by: str, delete_keys: set | None = None) -> dict:
        """MERGE-only: existing rows are updated by key or kept; never dropped unless
        explicitly named in delete_keys. Returns counts for the run manifest."""
        if not (self.list_path and self.key):
            raise StoreError("upsert requires list_path and key")
        d = self.read() or {}
        rows = d.get(self.list_path, [])
        by_key = {self.key(r): i for i, r in enumerate(rows)}
        added = updated = 0
        for r in new_rows:
            k = self.key(r)
            if k in by_key:
                merged = {**rows[by_key[k]], **r}
                if merged != rows[by_key[k]]:
                    rows[by_key[k]] = merged
                    updated += 1
            else:
                rows.append(r)
                by_key[k] = len(rows) - 1
                added += 1
        deleted = 0
        if delete_keys:
            keep = [r for r in rows if self.key(r) not in delete_keys]
            deleted = len(rows) - len(keep)
            rows = keep
        d[self.list_path] = rows
        d["_meta"] = {"asof": _now(), "generated_by": generated_by,
                      "run_id": uuid.uuid4().hex[:12], "schema": self.schema}
        self._atomic_write(d)
        return {"added": added, "updated": updated, "deleted": deleted, "total": len(rows)}


# ---------- append-only JSONL (defect ledger, miss ledger) ----------
def append_jsonl(rel_path: str | Path, row: dict, generated_by: str) -> dict:
    p = (ROOT / rel_path) if not Path(rel_path).is_absolute() else Path(rel_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    row = dict(row)
    row.setdefault("date", _now()[:10])
    row["_prov"] = {"asof": _now(), "generated_by": generated_by}
    with open(p, "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def read_jsonl(rel_path: str | Path) -> list[dict]:
    p = (ROOT / rel_path) if not Path(rel_path).is_absolute() else Path(rel_path)
    if not p.exists():
        return []
    out = []
    for i, line in enumerate(p.read_text().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise StoreError(f"{p.name} line {i+1} corrupt: {e}") from e
    return out
