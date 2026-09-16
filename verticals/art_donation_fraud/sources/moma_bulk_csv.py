"""
MoMA bulk-CSV connector.

The Museum of Modern Art publishes their full Artworks dataset on GitHub:
    https://github.com/MuseumofModernArt/collection
    Artworks.csv (~73MB, ~140K rows).

Columns: Title, Artist, ConstituentID, ArtistBio, Nationality, BeginDate,
EndDate, Gender, Date, Medium, Dimensions, CreditLine, AccessionNumber,
Classification, Department, DateAcquired, Cataloged, ObjectID, URL, ThumbnailURL.
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterator

import httpx

from core.models import Record
from .met_collection import _is_gift, parse_donor, normalize_donor

source_id   = "moma_bulk_csv"
record_type = "museum_acquisition"

_CSV_URL = "https://media.githubusercontent.com/media/MuseumofModernArt/collection/main/Artworks.csv"

HERE = Path(__file__).parent.parent
CACHE = HERE / "data" / "MoMA_Artworks.csv"

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SignalOS/1.0)"}


def download_if_missing(force: bool = False) -> Path:
    if CACHE.exists() and not force:
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    print(f"[moma] downloading bulk CSV (~73MB)…", file=sys.stderr)
    with httpx.stream("GET", _CSV_URL, headers=_HEADERS, timeout=600) as r:
        r.raise_for_status()
        with open(CACHE, "wb") as fh:
            for chunk in r.iter_bytes(chunk_size=1 << 16):
                fh.write(chunk)
    sz = CACHE.stat().st_size
    print(f"[moma] downloaded {sz/1e6:.1f}MB → {CACHE}", file=sys.stderr)
    return CACHE


def _parse_date_acquired(s: str) -> int | None:
    """MoMA DateAcquired is YYYY-MM-DD (or empty). Return year."""
    if not s:
        return None
    s = s.strip()
    try:
        if len(s) >= 4 and s[:4].isdigit():
            return int(s[:4])
    except ValueError:
        return None
    return None


def iter_gifts(
    min_accession_year: int = 2010,
    classifications: set[str] | None = None,
    departments: set[str] | None = None,
) -> Iterator[Record]:
    path = download_if_missing()
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            cl = (row.get("CreditLine") or "").strip()
            if not _is_gift(cl):
                continue
            ay = _parse_date_acquired(row.get("DateAcquired", ""))
            if ay is None or ay < min_accession_year:
                continue
            cls = (row.get("Classification") or "").strip()
            dept = (row.get("Department") or "").strip()
            if classifications and cls not in classifications:
                continue
            if departments and dept not in departments:
                continue

            donor_raw, gift_year = parse_donor(cl)
            yield Record(
                entity_id=f"moma_{row.get('ObjectID','')}",
                record_type=record_type,
                source=source_id,
                data={
                    "museum":                "moma",
                    "object_id":             str(row.get("ObjectID") or ""),
                    "accession_number":      (row.get("AccessionNumber") or "").strip(),
                    "accession_year":        ay,
                    "credit_line":           cl,
                    "donor_name_raw":        donor_raw,
                    "donor_name_normalized": normalize_donor(donor_raw),
                    "gift_year":             gift_year,
                    "title":                 (row.get("Title") or "").strip(),
                    "artist":                (row.get("Artist") or "").strip(),
                    "artist_nationality":    (row.get("Nationality") or "").strip(),
                    "classification":        cls,
                    "department":            dept,
                    "medium":                (row.get("Medium") or "").strip(),
                    "object_date":           (row.get("Date") or "").strip(),
                    "object_url":            (row.get("URL") or "").strip(),
                    "is_highlight":          False,
                    "is_public_domain":      False,
                },
                fetched_at=datetime.utcnow(),
            )
