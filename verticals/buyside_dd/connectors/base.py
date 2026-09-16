"""Base interface every connector implements.

Design contract:
  - Connectors are pure functions of (ConnectorRequest) → ConnectorResult.
  - No connector mutates state. No connector raises uncaught exceptions to
    the dispatcher; instead all failures must be returned as a ConnectorResult
    with success=False and a typed error category.
  - Connectors must respect the source's documented rate limit (handled here
    via a simple in-process throttle, not a distributed limiter).
  - Network calls must use the `_session` helper for User-Agent + timeout.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, ClassVar

import requests
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Error categories
# ─────────────────────────────────────────────────────────────────────────────
class ErrorKind(str, Enum):
    NETWORK = "network"           # connection refused, DNS, timeout
    AUTH = "auth"                 # missing key, 401, 403
    NOT_FOUND = "not_found"       # 404 or empty result on a valid query
    PARSE_FAIL = "parse_fail"     # response shape unexpected
    RATE_LIMIT = "rate_limit"     # 429 or vendor-specific throttle
    UNSUPPORTED = "unsupported"   # request lacked the inputs this source needs
    UNKNOWN = "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# I/O contracts
# ─────────────────────────────────────────────────────────────────────────────
class ConnectorRequest(BaseModel):
    """Inputs that any connector might use. Connectors pick what they need."""
    address: Optional[str] = None
    parcel_id: Optional[str] = None
    entity_name: Optional[str] = None       # LLC name, sponsor name, person
    person_name: Optional[str] = None
    geographic_area: Optional[str] = None   # zip, county, MSA
    state: Optional[str] = None             # 2-letter
    city: Optional[str] = None
    year: Optional[int] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ConnectorObservation(BaseModel):
    """A single typed observation pulled from a source."""
    attribute: str                          # e.g. 'sale_price', 'fmr_3br'
    value: Any
    value_unit: Optional[str] = None
    observation_date: Optional[datetime] = None
    confidence: float = 1.0
    source_url: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ConnectorResult(BaseModel):
    source_id: str
    request: ConnectorRequest
    queried_at: datetime
    success: bool
    observations: list[ConnectorObservation] = Field(default_factory=list)
    error_kind: Optional[ErrorKind] = None
    error_detail: Optional[str] = None
    raw_response_snippet: Optional[str] = None  # first ~2KB for evidence trail


# ─────────────────────────────────────────────────────────────────────────────
# Base class
# ─────────────────────────────────────────────────────────────────────────────
class BaseConnector(ABC):
    source_id: ClassVar[str] = "base"
    rate_limit_per_min: ClassVar[Optional[int]] = None
    user_agent: ClassVar[str] = "SignalOS-BuysideDD/0.1 (research; +signalos)"
    timeout_s: ClassVar[float] = 20.0

    _last_call_at: ClassVar[float] = 0.0

    def _throttle(self) -> None:
        if self.rate_limit_per_min is None:
            return
        min_gap = 60.0 / self.rate_limit_per_min
        elapsed = time.monotonic() - type(self)._last_call_at
        if elapsed < min_gap:
            time.sleep(min_gap - elapsed)
        type(self)._last_call_at = time.monotonic()

    def _session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update({"User-Agent": self.user_agent, "Accept": "application/json"})
        return s

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _ok(
        self,
        request: ConnectorRequest,
        observations: list[ConnectorObservation],
        raw: Optional[str] = None,
    ) -> ConnectorResult:
        return ConnectorResult(
            source_id=self.source_id,
            request=request,
            queried_at=self._now(),
            success=True,
            observations=observations,
            raw_response_snippet=raw[:2048] if raw else None,
        )

    def _fail(
        self,
        request: ConnectorRequest,
        kind: ErrorKind,
        detail: str,
        raw: Optional[str] = None,
    ) -> ConnectorResult:
        return ConnectorResult(
            source_id=self.source_id,
            request=request,
            queried_at=self._now(),
            success=False,
            error_kind=kind,
            error_detail=detail,
            raw_response_snippet=raw[:2048] if raw else None,
        )

    @abstractmethod
    def query(self, request: ConnectorRequest) -> ConnectorResult: ...


def safe_get(session: requests.Session, url: str, timeout: float = 20.0, **kw) -> tuple[Optional[requests.Response], Optional[ErrorKind], Optional[str]]:
    """Wrap requests.get with normalized error categorization.

    Returns (response, error_kind, error_detail). Exactly one of (response, error_kind) is non-None.
    """
    try:
        r = session.get(url, timeout=timeout, **kw)
    except requests.exceptions.Timeout as e:
        return None, ErrorKind.NETWORK, f"timeout: {e}"
    except requests.exceptions.ConnectionError as e:
        return None, ErrorKind.NETWORK, f"connection: {e}"
    except requests.exceptions.RequestException as e:
        return None, ErrorKind.UNKNOWN, f"requests: {e}"
    if r.status_code == 401 or r.status_code == 403:
        return None, ErrorKind.AUTH, f"http {r.status_code}: {r.text[:200]}"
    if r.status_code == 404:
        return None, ErrorKind.NOT_FOUND, f"http 404"
    if r.status_code == 429:
        return None, ErrorKind.RATE_LIMIT, f"http 429: {r.text[:200]}"
    if r.status_code >= 500:
        return None, ErrorKind.NETWORK, f"http {r.status_code}: server error"
    if r.status_code >= 400:
        return None, ErrorKind.UNKNOWN, f"http {r.status_code}: {r.text[:200]}"
    return r, None, None
