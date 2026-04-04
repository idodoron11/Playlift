from unittest import TestCase

import pytest

from tracks.spotify_track import SpotifyTrack


@pytest.mark.integration
class TestSpotifyTrack(TestCase):
    def test_track_id(self) -> None:
        track = SpotifyTrack("6kyxQuFD38mo4S3urD2Wkw")
        self.assertEqual(track.track_id, "6kyxQuFD38mo4S3urD2Wkw")

    def test_artists(self) -> None:
        track = SpotifyTrack("6kyxQuFD38mo4S3urD2Wkw")
        self.assertEqual(track.artists, ["Muse"])

    def test_display_artist(self) -> None:
        track = SpotifyTrack("6kyxQuFD38mo4S3urD2Wkw")
        self.assertEqual(track.display_artist, "Muse")

    def test_title(self) -> None:
        track = SpotifyTrack("6kyxQuFD38mo4S3urD2Wkw")
        self.assertEqual(track.title, "Unintended")

    def test_album(self) -> None:
        track = SpotifyTrack("6kyxQuFD38mo4S3urD2Wkw")
        self.assertEqual(track.album, "Showbiz")

    def test_duration(self) -> None:
        track = SpotifyTrack("6kyxQuFD38mo4S3urD2Wkw")
        self.assertLessEqual((abs(track.duration - (3 * 60 + 57))), 1)

    def test_track_number(self) -> None:
        track = SpotifyTrack("6kyxQuFD38mo4S3urD2Wkw")
        self.assertLessEqual(track.track_number, 7)

    def test_isrc_returns_valid_isrc(self) -> None:
        track = SpotifyTrack("0IFfrFeXFt0sO36KaFtL3b")
        self.assertEqual(track.isrc, "USSM19701400")


# ---------------------------------------------------------------------------
# T013: SpotifyTrack.isrc unit tests (no API calls)
# ---------------------------------------------------------------------------


def _make_spotify_track(data: dict) -> SpotifyTrack:  # type: ignore[type-arg]
    """Build a SpotifyTrack without a real Spotify API connection."""
    track = SpotifyTrack.__new__(SpotifyTrack)
    track._id = data["id"]
    track._data = data
    return track


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
