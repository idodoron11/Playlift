"""DeezerTrack — wraps a raw GW dict or public-API response dict."""

from __future__ import annotations

import re
from typing import Any

from tracks import ServiceTrack

DEEZER_URL_PREFIX: str = "https://www.deezer.com/track/"
DEEZER_TRACK_URL_PATTERN: re.Pattern[str] = re.compile(
    r"^https://(www\.)?deezer\.com(/[a-z]{2}(-[a-z]{2})?)?/track/(\d+)(\?.*)?$"
)


def is_valid_deezer_url(url: str) -> bool:
    """Return True when *url* matches any accepted Deezer track URL variant."""
    return bool(DEEZER_TRACK_URL_PATTERN.match(url))


def normalise_deezer_url(url: str) -> str:
    """Extract the numeric track ID and return the canonical Deezer track URL.

    Strips locale prefix, query string, and optional ``www.``.

    Args:
        url: Any Deezer track URL accepted by ``DEEZER_TRACK_URL_PATTERN``.

    Returns:
        Canonical URL of the form ``https://www.deezer.com/track/<id>``.
    """
    m = DEEZER_TRACK_URL_PATTERN.match(url)
    if not m:
        return url
    return f"{DEEZER_URL_PREFIX}{m.group(4)}"


def extract_deezer_track_id(url: str) -> str | None:
    """Extract the numeric track ID from a Deezer track URL, or None if invalid."""
    if not is_valid_deezer_url(url):
        return None
    m = DEEZER_TRACK_URL_PATTERN.match(normalise_deezer_url(url))
    return m.group(4) if m else None


def _normalize_isrc(raw: str) -> str:
    """Return *raw* ISRC normalized to uppercase with hyphens stripped."""
    return raw.upper().strip().replace("-", "")


class DeezerTrack(ServiceTrack):
    """Represents a Deezer catalog track.

    Accepts either a GW response dict (all-caps keys: ``SNG_ID``, ``SNG_TITLE``, …)
    or a public-API response dict (lowercase keys: ``id``, ``title``, …).  Data is
    stored on construction — no lazy loading.
    """

    service_name: str = "DEEZER"

    def __init__(self, data: dict[str, Any]) -> None:
        raw_id = str(data.get("SNG_ID") or data.get("id") or "")
        if not raw_id or not raw_id.strip().isdigit():
            raise ValueError(f"DeezerTrack requires a non-empty numeric track ID; got {raw_id!r}")
        self._track_id: str = raw_id.strip()
        self._data: dict[str, Any] = data

    # ------------------------------------------------------------------
    # Track abstract properties
    # ------------------------------------------------------------------

    @property
    def track_id(self) -> str:
        return self._track_id

    @property
    def title(self) -> str:
        return str(self._data.get("SNG_TITLE") or self._data.get("title") or "")

    @property
    def artists(self) -> list[str]:
        # GW: ART_NAME is a plain string; API: artist.name is nested
        art_name: str | None = self._data.get("ART_NAME")
        if art_name is not None:
            return [str(art_name)]
        artist = self._data.get("artist")
        if isinstance(artist, dict):
            return [str(artist.get("name", ""))]
        return []

    @property
    def album(self) -> str:
        alb = self._data.get("ALB_TITLE") or (self._data.get("album") or {}).get("title") or ""
        return str(alb)

    @property
    def duration(self) -> float:
        raw = self._data.get("DURATION") or self._data.get("duration") or 0
        return float(raw)

    @property
    def track_number(self) -> int:
        raw = self._data.get("TRACK_NUMBER") or self._data.get("track_position")
        if raw is None:
            return 0
        try:
            return int(raw)
        except (ValueError, TypeError):
            return 0

    @property
    def isrc(self) -> str | None:
        raw: str | None = self._data.get("ISRC") or self._data.get("isrc")
        if not raw or not raw.strip():
            return None
        return _normalize_isrc(raw)

    # ------------------------------------------------------------------
    # ServiceTrack abstract properties
    # ------------------------------------------------------------------

    @property
    def permalink(self) -> str:
        """Canonical Deezer track URL: ``https://www.deezer.com/track/<id>``."""
        return f"{DEEZER_URL_PREFIX}{self._track_id}"
