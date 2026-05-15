"""Factory for constructing TrackCollection instances from a source string."""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

from exceptions import InvalidPathMappingError, UnrecognisedSourceError
from playlists.deezer_playlist import DeezerPlaylist
from playlists.local_library import LocalLibrary
from playlists.local_playlist import LocalPlaylist
from playlists.spotify_playlist import SpotifyPlaylist

if TYPE_CHECKING:
    import spotipy
    from deezer import Deezer

    from playlists import TrackCollection
    from playlists.path_mapper import PathMapper

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

SPOTIFY_URI_PREFIX: str = "spotify:playlist:"
SPOTIFY_URL_FRAGMENT: str = "open.spotify.com/playlist/"
DEEZER_PLAYLIST_URL_PATTERN: re.Pattern[str] = re.compile(r"https?://(?:www\.)?deezer\.com(?:/[^/]+)?/playlist/(\d+)")


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _is_spotify_source(source: str) -> bool:
    """Return True if *source* is a Spotify playlist URI or HTTPS URL."""
    return source.startswith(SPOTIFY_URI_PREFIX) or SPOTIFY_URL_FRAGMENT in source


def _is_deezer_source(source: str) -> bool:
    """Return True if *source* is a Deezer playlist URL."""
    return bool(DEEZER_PLAYLIST_URL_PATTERN.search(source))


def _extract_deezer_playlist_id(source: str) -> str:
    """Extract the numeric playlist ID from a Deezer playlist URL.

    Args:
        source: A Deezer playlist URL containing a numeric playlist ID.

    Returns:
        The numeric playlist ID as a string.

    Raises:
        UnrecognisedSourceError: If no numeric ID can be extracted.
    """
    match = DEEZER_PLAYLIST_URL_PATTERN.search(source)
    if not match:
        raise UnrecognisedSourceError(f"Cannot extract Deezer playlist ID from: {source!r}")
    return match.group(1)


# ---------------------------------------------------------------------------
# PlaylistFactory
# ---------------------------------------------------------------------------


class PlaylistFactory:
    """Construct the appropriate TrackCollection from a source string.

    Given a source string (local path, Spotify URI/URL, or Deezer URL) and an
    optional ``PathMapper``, detects the source platform and returns the
    corresponding ``TrackCollection`` subclass.

    Args:
        spotify_client: An authenticated ``spotipy.Spotify`` instance.
        deezer_client: An authenticated ``Deezer`` instance.
    """

    def __init__(self, spotify_client: spotipy.Spotify, deezer_client: Deezer) -> None:  # type: ignore[no-any-unimported]
        self._spotify_client = spotify_client
        self._deezer_client = deezer_client

    def resolve(self, source: str, path_mapper: PathMapper | None = None) -> TrackCollection:
        """Resolve *source* to a TrackCollection.

        Args:
            source: A non-empty string representing a local path, Spotify
                URI/URL, or Deezer playlist URL.
            path_mapper: Optional path mapper for remapping local file paths.
                Must be ``None`` when *source* is a service URL/URI.

        Returns:
            The appropriate ``TrackCollection`` subclass for the given source.

        Raises:
            InvalidPathMappingError: If *source* is a service URL/URI and
                *path_mapper* is not ``None``.
            UnrecognisedSourceError: If *source* does not match any known
                format and is not a valid local path.
        """
        is_service_source = _is_spotify_source(source) or _is_deezer_source(source)
        if is_service_source and path_mapper is not None:
            raise InvalidPathMappingError(f"--from-path/--to-path cannot be used with a service URL source: {source!r}")

        if _is_spotify_source(source):
            return SpotifyPlaylist(source, client=self._spotify_client)

        if _is_deezer_source(source):
            playlist_id = _extract_deezer_playlist_id(source)
            return DeezerPlaylist(playlist_id, deezer=self._deezer_client)

        if os.path.isdir(source):
            return LocalLibrary(source)

        if os.path.isfile(source):
            return LocalPlaylist(source, path_mapper=path_mapper)

        raise UnrecognisedSourceError(
            f"Source {source!r} is not a recognised Spotify URI/URL, Deezer URL, or valid local path."
        )
