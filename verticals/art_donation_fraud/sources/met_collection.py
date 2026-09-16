"""
Metropolitan Museum of Art collection connector.

Public REST API at https://collectionapi.metmuseum.org/public/collection/v1/.
Per-object endpoint returns accessionYear, creditLine ("Gift of [donor], [year]"),
title, artist, classification, department, image URL, etc.

We use the search endpoint to enumerate "Gift of" works and then per-object
fetch for full details. The API requires a real User-Agent (Incapsula-protected).
"""
from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Iterator

import httpx

from core.exceptions import SourceError
from core.models import Entity, Record

source_id   = "met_collection"
record_type = "museum_acquisition"

_API_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
_HEADERS  = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

# Departments most relevant to high-value fraud cases.
HIGH_VALUE_DEPARTMENTS = {
    "Modern and Contemporary Art",
    "European Paintings",
    "American Paintings and Sculpture",
    "European Sculpture and Decorative Arts",
    "American Decorative Arts",
    "Drawings and Prints",
    "The American Wing",
    "Asian Art",
}

HIGH_VALUE_CLASSIFICATIONS = {
    "Paintings", "Sculpture", "Drawings", "Prints",
    "Photographs",  # photography donations are non-trivial too
}

_GIFT_RE = re.compile(
    r"^\s*(?:gift|bequest|promised gift)\s+of\s+(.+?)(?:,\s*(\d{4}))?\s*$",
    re.I,
)


def parse_donor(credit_line: str) -> tuple[str, int | None]:
    """
    Extract (donor_name_raw, year) from a credit_line like
        "Gift of John D. Rockefeller, 1962"
    or
        "Bequest of Susan Vanderpoel, in memory of her husband, 1958"
    """
    if not credit_line:
        return "", None
    s = re.sub(r"\s+", " ", credit_line.strip())
    # Strip trailing year (4-digit) that's the gift year
    m = re.search(r",\s*(\d{4})\s*$", s)
    year = int(m.group(1)) if m else None
    if m:
        s = s[:m.start()]
    # Match prefix
    pm = re.match(r"^(?:gift|bequest|promised gift|partial gift|partial and promised gift)\s+of\s+(.+)$", s, re.I)
    if pm:
        donor = pm.group(1).strip()
    else:
        donor = s
    # Remove trailing "in memory of ..." / "in honor of ..."
    donor = re.split(r",?\s*in (memory|honor) of", donor, flags=re.I)[0].strip()
    # Remove trailing "and the ..." (museum naming) just for normalization
    donor = re.sub(r"\s*\.\s*$", "", donor)
    return donor.strip(", "), year


def normalize_donor(name: str) -> str:
    """Soft key for portfolio aggregation. Lowercases, strips titles + suffixes."""
    if not name:
        return ""
    s = name.upper()
    # Drop "MR. AND MRS." / "MR & MRS" prefix entirely (couple gifts attribute to husband's name historically)
    s = re.sub(r"^\s*(MR|MRS|MS|MR\.|MRS\.|MS\.)\s*\.?\s*(&|AND)\s*(MR|MRS|MS|MR\.|MRS\.|MS\.)\s*\.?\s+", "", s)
    # Strip remaining honorifics
    s = re.sub(r"\b(MR|MRS|MS|DR|HON|REV|SIR|LADY|JR|SR|II|III|IV|ESQ)\.?\b", "", s)
    s = re.sub(r"[.,&]", " ", s)
    # Collapse spaces
    s = re.sub(r"\s+", " ", s).strip()
    # Drop "AND THE/HIS/HER ..." type tail markers
    s = re.sub(r"\bAND\s+(THE|HIS|HER)\b.*$", "", s).strip()
    # Standardize "the artist" / "anonymous" / "the donor" as buckets
    if s in {"THE ARTIST", "THE DONOR", "ANONYMOUS DONOR", "ANONYMOUS"}:
        return s
    return s


def _is_gift(credit_line: str) -> bool:
    if not credit_line:
        return False
    return bool(re.match(r"^\s*(gift|bequest|promised gift|partial gift)", credit_line, re.I))


class MetCollectionSource:
    source_id      = source_id
    record_type    = record_type
    cache_ttl_days = 90  # collection records change rarely

    def fetch(self, entity: Entity) -> list[Record]:
        """Fetch a single object by Met objectID (entity.id)."""
        oid = entity.id
        try:
            return [_fetch_one(oid)]
        except SourceError:
            return []


def _fetch_one(oid: str | int, client: httpx.Client | None = None) -> Record:
    own = client is None
    if own:
        client = httpx.Client(headers=_HEADERS, timeout=30)
    try:
        r = client.get(f"{_API_BASE}/objects/{oid}")
        if r.status_code == 404:
            raise SourceError(f"Met object {oid} not found")
        r.raise_for_status()
        obj = r.json()
    except httpx.HTTPError as e:
        raise SourceError(f"Met API error: {e}") from e
    finally:
        if own:
            client.close()

    return _to_record(obj)


def _to_record(obj: dict) -> Record:
    credit_line = (obj.get("creditLine") or "").strip()
    donor_raw, gift_year = parse_donor(credit_line)
    donor_norm = normalize_donor(donor_raw)
    accession_year = None
    ay = obj.get("accessionYear") or ""
    if ay and re.match(r"^\d{4}$", str(ay).strip()):
        accession_year = int(str(ay).strip())

    data = {
        "museum":                 "met",
        "object_id":              str(obj.get("objectID") or ""),
        "accession_number":       obj.get("accessionNumber"),
        "accession_year":         accession_year,
        "credit_line":            credit_line,
        "donor_name_raw":         donor_raw,
        "donor_name_normalized":  donor_norm,
        "gift_year":              gift_year,
        "title":                  (obj.get("title") or "").strip(),
        "artist":                 (obj.get("artistDisplayName") or "").strip(),
        "classification":         (obj.get("classification") or "").strip(),
        "department":             (obj.get("department") or "").strip(),
        "medium":                 (obj.get("medium") or "").strip(),
        "object_url":             obj.get("objectURL"),
        "primary_image":          obj.get("primaryImage") or obj.get("primaryImageSmall"),
        "is_highlight":           bool(obj.get("isHighlight")),
        "is_public_domain":       bool(obj.get("isPublicDomain")),
    }
    return Record(
        entity_id=str(obj.get("objectID") or ""),
        record_type=record_type,
        source=source_id,
        data=data,
        fetched_at=datetime.utcnow(),
    )


def search_object_ids(query: str, has_images: bool | None = None,
                      department_id: int | None = None) -> list[int]:
    params = {"q": query}
    if has_images is not None:
        params["hasImages"] = str(has_images).lower()
    if department_id is not None:
        params["departmentId"] = department_id
    try:
        with httpx.Client(headers=_HEADERS, timeout=30) as c:
            r = c.get(f"{_API_BASE}/search", params=params)
            r.raise_for_status()
            return r.json().get("objectIDs") or []
    except httpx.HTTPError as e:
        raise SourceError(f"Met search failed: {e}") from e


def list_departments() -> list[dict]:
    with httpx.Client(headers=_HEADERS, timeout=30) as c:
        r = c.get(f"{_API_BASE}/departments")
        r.raise_for_status()
        return r.json().get("departments") or []


def fetch_gifts_in_departments(
    department_ids: list[int],
    min_accession_year: int = 2010,
    max_objects: int | None = None,
    delay: float = 0.05,
) -> Iterator[Record]:
    """
    Enumerate all "Gift of"-credited works in specified Met departments since
    min_accession_year. Yields Records.

    Implementation: use /objects?departmentIds=… to get full ID list per dept,
    then per-object fetch and filter on _is_gift.
    """
    seen: set[int] = set()
    yielded = 0
    with httpx.Client(headers=_HEADERS, timeout=30) as c:
        for dept_id in department_ids:
            r = c.get(f"{_API_BASE}/objects", params={"departmentIds": dept_id})
            if r.status_code != 200:
                continue
            obj_ids = r.json().get("objectIDs") or []
            for oid in obj_ids:
                if oid in seen:
                    continue
                seen.add(oid)
                try:
                    rr = c.get(f"{_API_BASE}/objects/{oid}")
                    if rr.status_code != 200:
                        continue
                    obj = rr.json()
                except httpx.HTTPError:
                    continue
                ay = obj.get("accessionYear")
                cl = (obj.get("creditLine") or "").strip()
                if not ay or not cl:
                    continue
                try:
                    ayi = int(str(ay).strip())
                except ValueError:
                    continue
                if ayi < min_accession_year:
                    continue
                if not _is_gift(cl):
                    continue
                yield _to_record(obj)
                yielded += 1
                if max_objects and yielded >= max_objects:
                    return
                time.sleep(delay)
