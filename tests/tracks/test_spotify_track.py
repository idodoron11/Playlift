from unittest import TestCase
from unittest.mock import MagicMock

import spotipy

from tracks.spotify_track import SpotifyTrack

# ---------------------------------------------------------------------------
# T013: SpotifyTrack.isrc unit tests (no API calls)
# ---------------------------------------------------------------------------


def _make_spotify_track(data: dict) -> SpotifyTrack:  # type: ignore[type-arg]
    """Build a SpotifyTrack without a real Spotify API connection."""
    mock_client = MagicMock(spec=spotipy.Spotify)
    mock_client._get_id.return_value = data["id"]
    return SpotifyTrack(data["id"], data=data, client=mock_client)


class TestSpotifyTrackIsrc(TestCase):
    """Unit tests for SpotifyTrack.isrc property."""

    def test_isrc_returns_value_when_external_ids_present(self) -> None:
        data = {
            "id": "abc123",
            "external_ids": {"isrc": "USRC17607839"},
            "name": "Test",
            "artists": [{"name": "A"}],
            "album": {"name": "B"},
            "duration_ms": 200000,
            "track_number": 1,
        }
        track = _make_spotify_track(data)
        assert track.isrc == "USRC17607839"

    def test_isrc_returns_none_when_no_external_ids(self) -> None:
        data = {
            "id": "abc123",
            "name": "Test",
            "artists": [{"name": "A"}],
            "album": {"name": "B"},
            "duration_ms": 200000,
            "track_number": 1,
        }
        track = _make_spotify_track(data)
        assert track.isrc is None

    def test_isrc_returns_none_when_external_ids_has_no_isrc_key(self) -> None:
        data = {
            "id": "abc123",
            "external_ids": {"ean": "1234567890123"},
            "name": "Test",
            "artists": [{"name": "A"}],
            "album": {"name": "B"},
            "duration_ms": 200000,
            "track_number": 1,
        }
        track = _make_spotify_track(data)
        assert track.isrc is None


# ---------------------------------------------------------------------------
# T008: TestSpotifyTrackServiceContract — ServiceTrack contract
# ---------------------------------------------------------------------------


def _make_minimal_spotify_track() -> "SpotifyTrack":
    """Build a minimal SpotifyTrack for contract assertions."""
    data = {
        "id": "abc123",
        "name": "Test",
        "artists": [{"name": "A"}],
        "album": {"name": "B"},
        "duration_ms": 200000,
        "track_number": 1,
        "external_ids": {},
    }
    return _make_spotify_track(data)


class TestSpotifyTrackServiceContract(TestCase):
    """Verify SpotifyTrack satisfies the ServiceTrack contract."""

    def test_permalink_returns_track_url(self) -> None:
        track = _make_minimal_spotify_track()
        assert track.permalink == track.track_url

    def test_service_name_returns_spotify(self) -> None:
        track = _make_minimal_spotify_track()
        assert track.service_name == "SPOTIFY"

    def test_spotify_track_is_service_track(self) -> None:
        from tracks import ServiceTrack

        track = _make_minimal_spotify_track()
        assert isinstance(track, ServiceTrack)
