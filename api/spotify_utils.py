"""
Spotify helper utilities.

Provides a small, robust parser to extract Spotify IDs from various forms
(spotify: URIs, open.spotify.com URLs, or raw IDs). It treats the special
value "SKIP" (case-insensitive) as a marker meaning "no spotify reference".
"""

from typing import Optional


def parse_spotify_id(value: Optional[str]) -> Optional[str]:
    """Parse a spotify id from a spotify url, uri, or raw id string.

    Returns the id string (e.g. '3n3Ppam7vgaVa1iaRUc9Lp') or None when the
    value is falsy or the special marker "SKIP".
    """
    if not value:
        return None
    v = value.strip()
    if not v:
        return None
    if v.upper() == "SKIP":
        return None
    # spotify URI e.g. spotify:track:TRACKID or spotify:track:TRACKID:some
    if v.startswith("spotify:"):
        parts = v.split(":")
        # last non-empty part is likely the id
        for part in reversed(parts):
            if part:
                # strip possible query-like suffixes
                return part.split("?")[0]
        return None
    # spotify URL e.g. https://open.spotify.com/track/TRACKID?si=...
    if "open.spotify.com" in v:
        v = v.split("?")[0]
        v = v.rstrip("/")
        parts = v.split("/")
        return parts[-1] if parts else None
    # otherwise assume it's already an id
    v = v.split("?")[0]
    return v or None
