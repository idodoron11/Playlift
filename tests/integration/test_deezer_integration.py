"""Integration tests for the Deezer API layer.

These tests make real network calls and require a valid ARL in config.ini.
They are excluded from the default pytest run (``-m 'not integration'``) and
must be opted into explicitly:

    uv run pytest tests/integration/ -v

Covered areas:
- Authentication (get_deezer_client singleton)
- Track metadata lookup by ISRC (DeezerMatcher._match_by_isrc)
- Track fuzzy search (DeezerMatcher._match_by_fuzzy_search)
- DeezerTrack property shape from live API data
- Playlist lifecycle: create → add tracks → read tracks → remove tracks → delete
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from matchers.deezer_matcher import DeezerMatcher
from playlists.deezer_playlist import DeezerPlaylist
from tracks.deezer_track import DeezerTrack

if TYPE_CHECKING:
    from collections.abc import Generator

    from deezer import Deezer  # type: ignore[import-untyped]

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Known catalog track used across all lookup tests.
#
# "Bohemian Rhapsody" by Queen — Deezer track ID 64371136
# ISRC: GBUM71029604 — verified in Deezer catalog.
# Duration used in fuzzy-search stubs must be within MATCH_LOOSE_DURATION_TOLERANCE_SECONDS
# (5 s) of the real Deezer track duration (354 s) so _match_constraints can pass.
# ---------------------------------------------------------------------------
KNOWN_TRACK_ISRC = "GBUM71029604"
KNOWN_TRACK_TITLE = "Bohemian Rhapsody"
KNOWN_TRACK_ARTIST = "Queen"
KNOWN_TRACK_DEEZER_ID = "64371136"
KNOWN_TRACK_DURATION_S = 354.0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_track_stub(
    *,
    isrc: str | None = None,
    title: str = "",
    artist: str = "",
    duration: float = 300.0,
) -> MagicMock:
    """Return a minimal Track-like stub accepted by DeezerMatcher methods."""
    stub = MagicMock()
    stub.isrc = isrc
    stub.title = title
    stub.display_artist = artist
    stub.artists = [artist] if artist else []
    stub.duration = duration
    stub.album = ""
    stub.service_ref.return_value = None
    return stub


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class TestDeezerAuthentication:
    def test_client_is_authenticated_and_has_expected_api_surface(self, deezer_client: Any) -> None:
        """get_deezer_client() returns a usable client with gw and api sub-objects."""
        assert deezer_client is not None
        assert hasattr(deezer_client, "gw")
        assert hasattr(deezer_client, "api")


# ---------------------------------------------------------------------------
# Track metadata lookup by ISRC
# ---------------------------------------------------------------------------


class TestDeezerISRCLookup:
    def test_isrc_lookup_returns_deezer_track_for_known_isrc(self, deezer_client: Any) -> None:
        matcher = DeezerMatcher(deezer=deezer_client)
        stub = _make_track_stub(isrc=KNOWN_TRACK_ISRC)

        result = matcher._match_by_isrc(stub)

        assert result is not None
        assert isinstance(result, DeezerTrack)

    def test_isrc_lookup_returns_track_with_correct_title(self, deezer_client: Any) -> None:
        matcher = DeezerMatcher(deezer=deezer_client)
        stub = _make_track_stub(isrc=KNOWN_TRACK_ISRC)

        result = matcher._match_by_isrc(stub)

        assert result is not None
        assert KNOWN_TRACK_TITLE.lower() in result.title.lower()

    def test_isrc_lookup_returns_track_with_correct_artist(self, deezer_client: Any) -> None:
        matcher = DeezerMatcher(deezer=deezer_client)
        stub = _make_track_stub(isrc=KNOWN_TRACK_ISRC)

        result = matcher._match_by_isrc(stub)

        assert result is not None
        assert KNOWN_TRACK_ARTIST.lower() in result.display_artist.lower()

    def test_missing_isrc_returns_none(self, deezer_client: Any) -> None:
        """Tracks with no ISRC value are skipped by _match_by_isrc."""
        matcher = DeezerMatcher(deezer=deezer_client)
        stub = _make_track_stub(isrc=None)

        result = matcher._match_by_isrc(stub)

        assert result is None


# ---------------------------------------------------------------------------
# DeezerTrack property shape from live data
# ---------------------------------------------------------------------------


class TestDeezerTrackFromLiveData:
    def test_track_has_non_empty_track_id(self, deezer_client: Any) -> None:
        matcher = DeezerMatcher(deezer=deezer_client)
        stub = _make_track_stub(isrc=KNOWN_TRACK_ISRC)
        result = matcher._match_by_isrc(stub)

        assert result is not None
        assert result.track_id.isdigit()

    def test_track_permalink_has_canonical_form(self, deezer_client: Any) -> None:
        matcher = DeezerMatcher(deezer=deezer_client)
        stub = _make_track_stub(isrc=KNOWN_TRACK_ISRC)
        result = matcher._match_by_isrc(stub)

        assert result is not None
        assert result.permalink == f"https://www.deezer.com/track/{result.track_id}"

    def test_track_duration_is_positive(self, deezer_client: Any) -> None:
        matcher = DeezerMatcher(deezer=deezer_client)
        stub = _make_track_stub(isrc=KNOWN_TRACK_ISRC)
        result = matcher._match_by_isrc(stub)

        assert result is not None
        assert result.duration > 0


# ---------------------------------------------------------------------------
# Fuzzy search
# ---------------------------------------------------------------------------


class TestDeezerFuzzySearch:
    def test_fuzzy_search_returns_deezer_track_for_well_known_song(self, deezer_client: Any) -> None:
        matcher = DeezerMatcher(deezer=deezer_client)
        stub = _make_track_stub(title=KNOWN_TRACK_TITLE, artist=KNOWN_TRACK_ARTIST, duration=KNOWN_TRACK_DURATION_S)

        result = matcher._match_by_fuzzy_search(stub)

        assert result is not None
        assert isinstance(result, DeezerTrack)

    def test_fuzzy_search_result_has_matching_title_or_artist(self, deezer_client: Any) -> None:
        matcher = DeezerMatcher(deezer=deezer_client)
        stub = _make_track_stub(title=KNOWN_TRACK_TITLE, artist=KNOWN_TRACK_ARTIST, duration=KNOWN_TRACK_DURATION_S)

        result = matcher._match_by_fuzzy_search(stub)

        assert result is not None
        title_match = KNOWN_TRACK_TITLE.lower() in result.title.lower()
        artist_match = KNOWN_TRACK_ARTIST.lower() in result.display_artist.lower()
        assert title_match or artist_match


# ---------------------------------------------------------------------------
# Playlist lifecycle
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_playlist(deezer_client: Deezer) -> Generator[DeezerPlaylist, None, None]:  # type: ignore[no-any-unimported]
    """Create a private test playlist and delete it after the test.

    Skips gracefully when the Deezer API returns a playlist-create quota error
    (typically caused by too many test runs in a short window).
    """
    try:
        playlist = DeezerPlaylist.create("playlift-integration-test", public=False, deezer=deezer_client)
    except Exception as exc:
        if "QUOTA_ERROR" in str(exc):
            pytest.skip(f"Deezer playlist-create quota exceeded — retry later: {exc}")
        raise
    yield playlist
    # Best-effort cleanup — gw.delete_playlist may not be available in all deezer-py versions
    with contextlib.suppress(Exception):
        deezer_client.gw.delete_playlist(playlist.playlist_id)


class TestDeezerPlaylistLifecycle:
    def test_create_returns_playlist_with_numeric_id(self, test_playlist: DeezerPlaylist) -> None:
        assert test_playlist.playlist_id.isdigit()

    def test_new_playlist_has_no_tracks(self, test_playlist: DeezerPlaylist) -> None:
        assert test_playlist.tracks == []

    def test_add_track_makes_track_appear_in_playlist(self, test_playlist: DeezerPlaylist) -> None:
        track = DeezerTrack(
            {
                "SNG_ID": KNOWN_TRACK_DEEZER_ID,
                "SNG_TITLE": KNOWN_TRACK_TITLE,
                "ART_NAME": KNOWN_TRACK_ARTIST,
                "ALB_TITLE": "",
                "DURATION": "360",
            }
        )

        test_playlist.add_tracks([track])

        track_ids = [t.track_id for t in test_playlist.tracks]
        assert KNOWN_TRACK_DEEZER_ID in track_ids

        # Restore playlist to empty state for subsequent tests in this module
        test_playlist.remove_track([track])

    def test_remove_track_removes_it_from_playlist(self, test_playlist: DeezerPlaylist) -> None:
        track = DeezerTrack(
            {
                "SNG_ID": KNOWN_TRACK_DEEZER_ID,
                "SNG_TITLE": KNOWN_TRACK_TITLE,
                "ART_NAME": KNOWN_TRACK_ARTIST,
                "ALB_TITLE": "",
                "DURATION": "360",
            }
        )
        test_playlist.add_tracks([track])

        test_playlist.remove_track([track])

        track_ids = [t.track_id for t in test_playlist.tracks]
        assert KNOWN_TRACK_DEEZER_ID not in track_ids
