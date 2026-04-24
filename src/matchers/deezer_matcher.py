"""DeezerMatcher — four-step track resolution strategy for the Deezer catalog."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

    from deezer import Deezer  # type: ignore[import-untyped]

from tqdm import tqdm

from api.deezer import get_deezer_client
from exceptions import SkipTrackError
from matchers import Matcher
from tracks import EmbeddableTrack, Track
from tracks.deezer_track import (
    DeezerTrack,
    extract_deezer_track_id,
)

logger = logging.getLogger(__name__)


class DeezerMatcher(Matcher):
    """Resolves local tracks to Deezer catalog tracks via a four-step strategy.

    Resolution order:
    1. Cached ``TXXX:DEEZER`` URL — normalise and use directly.
    2. ``"SKIP"`` sentinel — raise ``SkipTrackError``.
    3. ISRC lookup — ``dz.api.get_track_by_ISRC()``.
    4. Fuzzy search — ``dz.gw.search()``.
    """

    __instance: DeezerMatcher | None = None

    def __init__(self, deezer: Deezer) -> None:  # type: ignore[no-any-unimported]
        super().__init__()
        self._deezer = deezer

    @classmethod
    def get_instance(cls) -> DeezerMatcher:
        """Return the singleton DeezerMatcher, creating it if necessary."""
        if cls.__instance is None:
            cls.__instance = cls(deezer=get_deezer_client())
        return cls.__instance

    # ------------------------------------------------------------------
    # Step 1+2: cached TXXX:DEEZER ref
    # ------------------------------------------------------------------

    def _match_by_cached_ref(self, track: Track) -> DeezerTrack | None:
        """Return a DeezerTrack from a cached ``TXXX:DEEZER`` tag, or None.

        Raises SkipTrackError when the cached value is ``"SKIP"``.
        """
        ref = track.service_ref(DeezerTrack.service_name)
        if ref is None:
            return None
        if ref == "SKIP":
            raise SkipTrackError
        track_id = extract_deezer_track_id(ref)
        if track_id is None:
            return None
        return DeezerTrack({"SNG_ID": track_id, "SNG_TITLE": "", "ART_NAME": "", "ALB_TITLE": "", "DURATION": "0"})

    # ------------------------------------------------------------------
    # Step 3: ISRC lookup
    # ------------------------------------------------------------------

    def _match_by_isrc(self, track: Track) -> DeezerTrack | None:
        """Look up a track by its ISRC code on the Deezer public API.

        Returns None when the track has no ISRC, the ISRC is not in the
        catalog, or a transient network error occurs.
        """
        isrc = track.isrc
        if not isrc:
            logger.debug("No ISRC for '%s', skipping ISRC lookup", track.title)
            return None
        try:
            data: dict[str, Any] = self._deezer.api.get_track_by_ISRC(isrc)
            return DeezerTrack(data)
        except Exception:
            logger.warning(
                "ISRC lookup failed for '%s' (ISRC %s), falling back to fuzzy search",
                track.title,
                isrc,
            )
            return None

    # ------------------------------------------------------------------
    # Step 4: fuzzy search
    # ------------------------------------------------------------------

    def _match_by_fuzzy_search(self, track: Track) -> DeezerTrack | None:
        """Search Deezer GW for the best fuzzy match.

        Non-Latin artist/title queries are forwarded unchanged to the
        ``dz.gw.search()`` endpoint.
        """
        artist = track.display_artist or ""
        title = track.title or ""
        query = f"{artist} {title}".strip()
        if not query:
            return None
        try:
            results_raw: dict[str, Any] = self._deezer.gw.search(query, index=0, limit=10)
            candidates: list[dict[str, Any]] = results_raw.get("TRACK", {}).get("data", [])
        except Exception:
            logger.warning("Fuzzy search failed for '%s'", track.title)
            return None

        matches = [DeezerTrack(c) for c in candidates if self._match_constraints(track, DeezerTrack(c))]
        if not matches:
            logger.warning("Could not match '%s' via fuzzy search", track.title)
            return None
        matches.sort(key=lambda m: Matcher.track_distance(track, m))
        return matches[0]

    # ------------------------------------------------------------------
    # Four-step dispatcher
    # ------------------------------------------------------------------

    def match(self, track: Track) -> DeezerTrack | None:
        """Apply the four-step resolution strategy.

        Raises SkipTrackError when the cached ref is ``"SKIP"``.
        """
        cached = self._match_by_cached_ref(track)  # steps 1+2
        if cached is not None:
            return cached
        return self._match_by_isrc(track) or self._match_by_fuzzy_search(track)

    def suggest_match(self, track: Track) -> list[DeezerTrack]:
        """Return candidates from fuzzy search, filtered by _match_constraints."""
        artist = track.display_artist or ""
        title = track.title or ""
        query = f"{artist} {title}".strip()
        if not query:
            return []
        try:
            results_raw: dict[str, Any] = self._deezer.gw.search(query, index=0, limit=10)
            candidates: list[dict[str, Any]] = results_raw.get("TRACK", {}).get("data", [])
        except Exception:
            logger.warning("Fuzzy suggest failed for '%s'", track.title)
            return []
        matches = [DeezerTrack(c) for c in candidates if self._match_constraints(track, DeezerTrack(c))]
        matches.sort(key=lambda m: Matcher.track_distance(track, m))
        return matches

    def match_list(self, tracks: Iterable[Track], autopilot: bool = False, embed_matches: bool = False) -> list[Track]:
        """Resolve each track and optionally embed ``TXXX:DEEZER`` tags.

        Iterates with a tqdm progress bar.  Unresolvable tracks are skipped
        with a warning; SkipTrackError silently excludes a track.
        """
        track_list = list(tracks)
        resolved: list[Track] = []

        print("Matching source tracks to Deezer tracks")
        for track in tqdm(track_list):
            try:
                match = self.match(track)
            except SkipTrackError:
                print(f"Skip track\n{track}")
                continue
            if match is None:
                suggestions = self.suggest_match(track)
                if not suggestions:
                    print(f"Could not match\n{track}")
                    continue
                if autopilot:
                    match = suggestions[0]
                else:
                    choice = Matcher.choose_suggestion(track, suggestions)
                    if choice < 0:
                        continue
                    match = suggestions[choice]

            resolved.append(match)
            if embed_matches and isinstance(track, EmbeddableTrack):
                track.embed_match(match)

        return resolved
