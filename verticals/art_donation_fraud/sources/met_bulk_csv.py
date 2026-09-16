"""
Metropolitan Museum bulk-CSV connector.

The Met publishes `MetObjects.csv` (~318MB, ~480K objects) on GitHub at
https://github.com/metmuseum/openaccess. Pull once into local cache, then
iterate. Much faster than per-object API and avoids Incapsula rate-limiting.

Columns include: Object ID, Accession Number, Accession Year, Credit Line,
Title, Artist Display Name, Object Name, Classification, Department, Medium,
Object Date, Object Begin/End Date, Is Public Domain, Object URL, etc.
"""
from __future__ import annotations

import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterator

import httpx

from core.models import Record
from .met_collection import _is_gift, parse_donor, normalize_donor

source_id   = "met_bulk_csv"
record_type = "museum_acquisition"

_CSV_URL = "https://media.githubusercontent.com/media/metmuseum/openaccess/master/MetObjects.csv"

HERE = Path(__file__).parent.parent
CACHE = HERE / "data" / "MetObjects.csv"

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SignalOS/1.0)"}


def download_if_missing(force: bool = False) -> Path:
    if CACHE.exists() and not force:
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    print(f"[met] downloading bulk CSV (~318MB)…", file=sys.stderr)
    with httpx.stream("GET", _CSV_URL, headers=_HEADERS, timeout=600) as r:
        r.raise_for_status()
        with open(CACHE, "wb") as fh:
            for chunk in r.iter_bytes(chunk_size=1 << 16):
                fh.write(chunk)
    sz = CACHE.stat().st_size
    print(f"[met] downloaded {sz/1e6:.1f}MB → {CACHE}", file=sys.stderr)
    return CACHE


def iter_gifts(
    min_accession_year: int = 2010,
    classifications: set[str] | None = None,
    departments: set[str] | None = None,
) -> Iterator[Record]:
    """
    Stream Records for every Met object that:
      - was acquired as a Gift / Bequest / Promised Gift
      - in or after min_accession_year
      - (optionally) classification in classifications
      - (optionally) department in departments
    """
    path = download_if_missing()
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            cl = (row.get("Credit Line") or "").strip()
            if not _is_gift(cl):
                continue
            ay_raw = (row.get("AccessionYear") or "").strip()
            try:
                ay = int(ay_raw)
            except ValueError:
                continue
            if ay < min_accession_year:
                continue
            cls = (row.get("Classification") or "").strip()
            dept = (row.get("Department") or "").strip()
            if classifications and cls not in classifications:
                continue
            if departments and dept not in departments:
                continue

            donor_raw, gift_year = parse_donor(cl)
            yield Record(
                entity_id=str(row.get("Object ID") or ""),
                record_type=record_type,
                source=source_id,
                data={
                    "museum":                "met",
                    "object_id":             str(row.get("Object ID") or ""),
                    "accession_number":      (row.get("Object Number") or "").strip(),
                    "accession_year":        ay,
                    "credit_line":           cl,
                    "donor_name_raw":        donor_raw,
                    "donor_name_normalized": normalize_donor(donor_raw),
                    "gift_year":             gift_year,
                    "title":                 (row.get("Title") or "").strip(),
                    "artist":                (row.get("Artist Display Name") or "").strip(),
                    "artist_nationality":    (row.get("Artist Nationality") or "").strip(),
                    "artist_begin_date":     (row.get("Artist Begin Date") or "").strip(),
                    "artist_end_date":       (row.get("Artist End Date") or "").strip(),
                    "classification":        cls,
                    "department":            dept,
                    "medium":                (row.get("Medium") or "").strip(),
                    "object_date":           (row.get("Object Date") or "").strip(),
                    "object_url":            (row.get("Link Resource") or row.get("Object URL") or "").strip(),
                    "is_highlight":          (row.get("Is Highlight") or "").strip().lower() == "true",
                    "is_public_domain":      (row.get("Is Public Domain") or "").strip().lower() == "true",
                },
                fetched_at=datetime.utcnow(),
            )
