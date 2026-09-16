from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from core.models import GapResult, Record, RuleMatch, Signal, SignalRule


SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    signal_id           TEXT PRIMARY KEY,
    run_id              TEXT NOT NULL,
    entity_id           TEXT NOT NULL,
    vertical            TEXT NOT NULL,
    jurisdiction        TEXT NOT NULL,
    fraud_score         INTEGER NOT NULL,
    fraud_tier          TEXT NOT NULL,
    raw_gap             REAL NOT NULL,
    net_gap             REAL NOT NULL,
    estimated_annual_impact REAL,
    gap_direction       TEXT,
    data_quality_flags  TEXT,           -- JSON array
    gap_metadata        TEXT,           -- JSON object
    rule_matches        TEXT,           -- JSON array
    signal_metadata     TEXT,           -- JSON object
    computed_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signal_rules (
    rule_id             TEXT NOT NULL,
    vertical            TEXT NOT NULL,
    jurisdiction        TEXT NOT NULL,
    rule_type           TEXT NOT NULL,
    detectable          INTEGER NOT NULL,
    statutory_ref       TEXT,
    description         TEXT,
    implementation      TEXT,
    confidence_if_llm   REAL NOT NULL DEFAULT 0.5,
    priority            INTEGER NOT NULL DEFAULT 100,
    source_text         TEXT,
    PRIMARY KEY (rule_id, vertical, jurisdiction)
);

CREATE INDEX IF NOT EXISTS idx_signals_entity    ON signals (entity_id);
CREATE INDEX IF NOT EXISTS idx_signals_run       ON signals (run_id);
CREATE INDEX IF NOT EXISTS idx_signals_tier      ON signals (fraud_tier, jurisdiction);
CREATE INDEX IF NOT EXISTS idx_signals_gap       ON signals (net_gap DESC);

-- Record cache: stores raw source records so MLS fetches aren't re-scraped every run.
-- source_fetch_log tracks *when* each (entity, source) was last fetched so we can
-- distinguish a fresh empty result (Zillow found no sales) from a cache miss (never fetched).
CREATE TABLE IF NOT EXISTS record_cache (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id    TEXT NOT NULL,
    source_id    TEXT NOT NULL,
    record_type  TEXT NOT NULL,
    data         TEXT NOT NULL,    -- JSON
    fetched_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_record_cache ON record_cache (entity_id, source_id, fetched_at DESC);

CREATE TABLE IF NOT EXISTS source_fetch_log (
    entity_id    TEXT NOT NULL,
    source_id    TEXT NOT NULL,
    fetched_at   TEXT NOT NULL,
    record_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (entity_id, source_id)
);
"""


@contextmanager
def _conn(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _decimal(v) -> Decimal:
    return Decimal(str(v)) if v is not None else Decimal(0)


class SQLiteSignalStore:
    def __init__(self, db_path: Path | str = "signalos.db"):
        self.db_path = Path(db_path)
        self._init()

    def _init(self):
        with _conn(self.db_path) as conn:
            conn.executescript(SCHEMA)

    def write_signal(self, signal: Signal) -> None:
        rule_matches_json = json.dumps([
            {
                "rule_id": m.rule.rule_id,
                "matched": m.matched,
                "confidence": m.confidence,
                "gap_adjustment": str(m.gap_adjustment),
                "explanation": m.explanation,
                "interpreter": m.interpreter,
            }
            for m in signal.rule_matches
        ])

        with _conn(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO signals (
                    signal_id, run_id, entity_id, vertical, jurisdiction,
                    fraud_score, fraud_tier, raw_gap, net_gap,
                    estimated_annual_impact, gap_direction,
                    data_quality_flags, gap_metadata, rule_matches,
                    signal_metadata, computed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal.signal_id,
                signal.run_id,
                signal.entity_id,
                signal.vertical,
                signal.jurisdiction,
                signal.fraud_score,
                signal.fraud_tier,
                float(signal.gap.raw_gap),
                float(signal.net_gap),
                float(signal.estimated_annual_impact) if signal.estimated_annual_impact else None,
                signal.gap.gap_direction,
                json.dumps(signal.gap.data_quality_flags),
                json.dumps(signal.gap.metadata, default=str),
                rule_matches_json,
                json.dumps(signal.metadata, default=str),
                signal.computed_at.isoformat(),
            ))

    def read_signals(self, **filters) -> list[dict]:
        clauses, params = [], []
        for k, v in filters.items():
            clauses.append(f"{k} = ?")
            params.append(v)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        with _conn(self.db_path) as conn:
            rows = conn.execute(
                f"SELECT * FROM signals {where} ORDER BY net_gap DESC", params
            ).fetchall()
        return [dict(r) for r in rows]

    def write_rules(self, rules: list[SignalRule]) -> None:
        with _conn(self.db_path) as conn:
            for r in rules:
                conn.execute("""
                    INSERT OR REPLACE INTO signal_rules (
                        rule_id, vertical, jurisdiction, rule_type, detectable,
                        statutory_ref, description, implementation,
                        confidence_if_llm, priority, source_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.rule_id, r.vertical, r.jurisdiction, r.rule_type,
                    int(r.detectable), r.statutory_ref, r.description,
                    r.implementation, r.confidence_if_llm, r.priority, r.source_text,
                ))

    def read_records(
        self,
        entity_id: str,
        source_id: str,
        max_age_days: int = 30,
    ) -> list[Record] | None:
        """
        Return cached records for (entity_id, source_id) if fetched within max_age_days.
        Returns None on cache miss (never fetched or stale).
        Returns [] if fetched recently but source returned no records — skip re-fetch.
        """
        cutoff = (datetime.utcnow() - timedelta(days=max_age_days)).isoformat()
        with _conn(self.db_path) as conn:
            log = conn.execute(
                "SELECT fetched_at FROM source_fetch_log WHERE entity_id=? AND source_id=?",
                (entity_id, source_id),
            ).fetchone()
            if log is None or log["fetched_at"] < cutoff:
                return None  # cache miss or stale

            rows = conn.execute(
                "SELECT * FROM record_cache WHERE entity_id=? AND source_id=?",
                (entity_id, source_id),
            ).fetchall()

        return [
            Record(
                entity_id=r["entity_id"],
                record_type=r["record_type"],
                source=r["source_id"],
                data=json.loads(r["data"]),
                fetched_at=datetime.fromisoformat(r["fetched_at"]),
            )
            for r in rows
        ]

    def write_records(self, entity_id: str, source_id: str, records: list[Record]) -> None:
        """Cache source records and log the fetch timestamp."""
        now = datetime.utcnow().isoformat()
        with _conn(self.db_path) as conn:
            # Delete stale cache entries for this (entity, source) before writing fresh ones
            conn.execute(
                "DELETE FROM record_cache WHERE entity_id=? AND source_id=?",
                (entity_id, source_id),
            )
            for r in records:
                conn.execute(
                    "INSERT INTO record_cache (entity_id, source_id, record_type, data, fetched_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (entity_id, source_id, r.record_type, json.dumps(r.data, default=str), now),
                )
            conn.execute(
                "INSERT OR REPLACE INTO source_fetch_log (entity_id, source_id, fetched_at, record_count)"
                " VALUES (?, ?, ?, ?)",
                (entity_id, source_id, now, len(records)),
            )

    def read_rules(self, vertical: str, jurisdiction: str) -> list[SignalRule]:
        with _conn(self.db_path) as conn:
            rows = conn.execute("""
                SELECT * FROM signal_rules
                WHERE vertical = ? AND (jurisdiction = ? OR jurisdiction = '*')
                ORDER BY priority
            """, (vertical, jurisdiction)).fetchall()
        return [SignalRule(**dict(r)) for r in rows]
