"""
SourceRegistry — auto-wires data sources to (vertical, jurisdiction) pairs.

Sources declare a geographic scope via the `jurisdictions` argument:
  - None (default) → national: applies to every jurisdiction in the vertical
  - ["detroit"]    → city-scoped: only applies when jurisdiction == "detroit"

This means adding a new jurisdiction automatically inherits all national
sources (e.g. Zillow, Redfin) without touching any registry configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .exceptions import ConfigError
from .models import VerticalManifest


@dataclass
class _Registration:
    source: Any
    vertical: str
    jurisdictions: frozenset[str] | None  # None = all jurisdictions (national)


class SourceRegistry:
    def __init__(self) -> None:
        self._registrations: list[_Registration] = []

    def register(
        self,
        source: Any,
        vertical: str,
        jurisdictions: list[str] | None = None,
    ) -> "SourceRegistry":
        """Register a source. jurisdictions=None means national (applies everywhere)."""
        self._registrations.append(_Registration(
            source=source,
            vertical=vertical,
            jurisdictions=frozenset(jurisdictions) if jurisdictions is not None else None,
        ))
        return self

    def for_jurisdiction(self, vertical: str, jurisdiction: str) -> list[Any]:
        """Return all sources applicable to (vertical, jurisdiction), in registration order."""
        return [
            reg.source
            for reg in self._registrations
            if reg.vertical == vertical
            and (reg.jurisdictions is None or jurisdiction in reg.jurisdictions)
        ]

    def validate(self, vertical: str, jurisdiction: str, manifest: VerticalManifest) -> None:
        """Raise ConfigError if any required_source_type has no covering source."""
        sources = self.for_jurisdiction(vertical, jurisdiction)
        covered = {s.record_type for s in sources}
        missing = [t for t in manifest.required_source_types if t not in covered]
        if missing:
            raise ConfigError(
                f"No source registered for required record type(s) {missing} "
                f"in vertical='{vertical}' jurisdiction='{jurisdiction}'. "
                f"Register a source before calling build_engine()."
            )
