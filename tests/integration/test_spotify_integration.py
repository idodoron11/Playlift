"""Spotify integration tests — require a valid OAuth token cached on disk.

All tests skip gracefully when credentials are not configured (see conftest.py).
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

from matchers.spotify_matcher import SpotifyMatcher
from playlists.spotify_playlist import SpotifyPlaylist
from tests.playlists.playlist_mock import PlaylistMock
from tests.playlists.spotify_playlist_spy import SpotifyPlaylistSpy
from tests.tracks.track_mock import TrackMock
from tracks.spotify_track import SpotifyTrack

if TYPE_CHECKING:
    from collections.abc import Generator

    from tracks import Track

# ---------------------------------------------------------------------------
# Known test data
# ---------------------------------------------------------------------------

KNOWN_TRACK_ID = "6kyxQuFD38mo4S3urD2Wkw"
KNOWN_TRACK_ARTISTS = ["Muse"]
KNOWN_TRACK_TITLE = "Unintended"
KNOWN_TRACK_ALBUM = "Showbiz"
KNOWN_TRACK_DURATION_APPROX_S = 3 * 60 + 57

ISRC_TRACK_ID = "0IFfrFeXFt0sO36KaFtL3b"
ISRC_EXPECTED = "USSM19701400"

DEEP_PURPLE_HITS_PLAYLIST_ID = "4X7RPexaMm2XwDb6g1fRmQ"
DEEP_PURPLE_HITS_PLAYLIST_NAME = "Deep Purple - Greatest Hits"
DEEP_PURPLE_HITS_TRACK_COUNT = 59

CHILL_VIBES_PLAYLIST_ID = "31uSi3T52m00gqt4MwuZNM"
CHILL_VIBES_MIN_TRACK_COUNT = 100

CHILL_MIX_PLAYLIST_ID = "37i9dQZF1EQqkOPvHGajmW"

ENDPOINTS_PLAYLIST_URL = "https://open.spotify.com/playlist/3cEYpjA9oz9GiPac4AsH4n"
ENDPOINTS_PLAYLIST_TRACK_TITLES = ["Api", "Is", "All I Want", "Endpoints", "You Are So Beautiful"]

SOURCE_TRACK_ID = "1"
SOURCE_TRACK_ARTISTS = ["Led Zeppelin"]
SOURCE_TRACK_ALBUM = "Led Zeppelin IV (Remaster)"
SOURCE_TRACK_TITLE = "Black Dog - Remaster"
SOURCE_TRACK_DURATION_SECONDS = 4 * 60 + 55
SOURCE_TRACK_NUMBER = 1
SOURCE_PLAYLIST_NAME = "playlist name"

E2E_PLAYLIST_NAME = "Test Playlist"
E2E_TRACK_IDS = ["4OSBTYWVwsQhGLF9NHvIbR", "5mFMb5OHI3cN0UjITVztCj", "1CRtJS94Hq3PbBZT9LuF90"]
E2E_TRACKS_AFTER_REMOVE = 2


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def e2e_playlist(spotify_client: Any) -> Generator[SpotifyPlaylist, None, None]:
    """Create a test playlist and delete it after the test completes (or fails)."""
    playlist = SpotifyPlaylist.create(E2E_PLAYLIST_NAME, client=spotify_client)
    yield playlist
    with contextlib.suppress(Exception):
        spotify_client.current_user_unfollow_playlist(playlist.playlist_id)


# ---------------------------------------------------------------------------
# SpotifyTrack
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSpotifyTrackIntegration:
    def test_track_id(self, spotify_client: Any) -> None:
        track = SpotifyTrack(KNOWN_TRACK_ID, client=spotify_client)
        assert track.track_id == KNOWN_TRACK_ID

    def test_artists(self, spotify_client: Any) -> None:
        track = SpotifyTrack(KNOWN_TRACK_ID, client=spotify_client)
        assert track.artists == KNOWN_TRACK_ARTISTS

    def test_display_artist(self, spotify_client: Any) -> None:
        track = SpotifyTrack(KNOWN_TRACK_ID, client=spotify_client)
        assert track.display_artist == "Muse"

    def test_title(self, spotify_client: Any) -> None:
        track = SpotifyTrack(KNOWN_TRACK_ID, client=spotify_client)
        assert track.title == KNOWN_TRACK_TITLE

    def test_album(self, spotify_client: Any) -> None:
        track = SpotifyTrack(KNOWN_TRACK_ID, client=spotify_client)
        assert track.album == KNOWN_TRACK_ALBUM

    def test_duration(self, spotify_client: Any) -> None:
        track = SpotifyTrack(KNOWN_TRACK_ID, client=spotify_client)
        assert abs(track.duration - KNOWN_TRACK_DURATION_APPROX_S) <= 1

    def test_track_number(self, spotify_client: Any) -> None:
        track = SpotifyTrack(KNOWN_TRACK_ID, client=spotify_client)
        assert track.track_number <= 7

    def test_isrc_returns_valid_isrc(self, spotify_client: Any) -> None:
        track = SpotifyTrack(ISRC_TRACK_ID, client=spotify_client)
        assert track.isrc == ISRC_EXPECTED


# ---------------------------------------------------------------------------
# SpotifyPlaylist
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSpotifyPlaylistIntegration:
    def test_tracks(self, spotify_client: Any) -> None:
        playlist = SpotifyPlaylist(DEEP_PURPLE_HITS_PLAYLIST_ID, client=spotify_client)
        assert len(list(playlist.tracks)) == DEEP_PURPLE_HITS_TRACK_COUNT

    def test_tracks_with_more_than_100_tracks(self, spotify_client: Any) -> None:
        playlist = SpotifyPlaylist(CHILL_VIBES_PLAYLIST_ID, client=spotify_client)
        assert len(list(playlist.tracks)) > CHILL_VIBES_MIN_TRACK_COUNT

    def test_playlist_id(self, spotify_client: Any) -> None:
        playlist = SpotifyPlaylist(CHILL_MIX_PLAYLIST_ID, client=spotify_client)
        assert playlist.playlist_id == CHILL_MIX_PLAYLIST_ID

    def test_name(self, spotify_client: Any) -> None:
        playlist = SpotifyPlaylist(DEEP_PURPLE_HITS_PLAYLIST_ID, client=spotify_client)
        assert playlist.name == DEEP_PURPLE_HITS_PLAYLIST_NAME

    def test_create_from_another_playlist(self, spotify_client: Any) -> None:
        source_tracks: list[Track] = [
            TrackMock(
                SOURCE_TRACK_ID,
                SOURCE_TRACK_ARTISTS,
                SOURCE_TRACK_ALBUM,
                SOURCE_TRACK_TITLE,
                SOURCE_TRACK_DURATION_SECONDS,
                SOURCE_TRACK_NUMBER,
            )
        ]
        source_playlist = PlaylistMock(source_tracks)
        target_playlist = SpotifyPlaylistSpy.create_from_another_playlist(
            SOURCE_PLAYLIST_NAME, source_playlist, client=spotify_client
        )
        assert len(target_playlist.tracks) == 1
        assert target_playlist.tracks[0].title == source_playlist.tracks[0].title
        assert target_playlist.tracks[0].display_artist == source_playlist.tracks[0].display_artist
        assert target_playlist.tracks[0].album == source_playlist.tracks[0].album

    def test_init(self, spotify_client: Any) -> None:
        playlist = SpotifyPlaylist(ENDPOINTS_PLAYLIST_URL, client=spotify_client)
        actual_songs_names = [track.title for track in playlist.tracks]
        assert actual_songs_names == ENDPOINTS_PLAYLIST_TRACK_TITLES

    def test_e2e_spotify_playlist(self, e2e_playlist: SpotifyPlaylist, spotify_client: Any) -> None:
        assert len(e2e_playlist.tracks) == 0
        tracks = [SpotifyTrack(tid, client=spotify_client) for tid in E2E_TRACK_IDS]
        e2e_playlist.add_tracks(tracks)
        assert e2e_playlist.tracks == tracks
        e2e_playlist.remove_track([e2e_playlist.tracks[0]])
        assert len(e2e_playlist.tracks) == E2E_TRACKS_AFTER_REMOVE
        e2e_playlist.clear()
        assert len(e2e_playlist.tracks) == 0


# ---------------------------------------------------------------------------
# SpotifyMatcher
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSpotifyMatcherIntegration:
    UNINTENDED_TRACK = TrackMock("1", ["Muse"], "Showbiz", "Unintended", 3 * 60 + 55, 7)
    HERE_WITHOUT_YOU_TRACK = TrackMock("2", ["3 doors down"], "away from the sun", "here without you", 3 * 60 + 57, 6)
    WILD_TRACK = TrackMock("3", ["LP"], "Love Lines (Deluxe Version)", "Wild", 181, 2)
    ZE_RAK_HALEV = TrackMock("4", ["אביב גפן"], "עם הזמן", "זה רק הלב שכואב לך", 232, 4)

    match_map: ClassVar[dict[TrackMock, str]] = {
        UNINTENDED_TRACK: "6kyxQuFD38mo4S3urD2Wkw",
        HERE_WITHOUT_YOU_TRACK: "3NLrRZoMF0Lx6zTlYqeIo4",
        WILD_TRACK: "3QdeMlhJH3fAMbMPVD5ZAu",
        ZE_RAK_HALEV: "0wRnFA1iu3RSfCPvWfvWgp",
    }

    def test_match(self, spotify_client: Any) -> None:
        source = self.UNINTENDED_TRACK
        target = SpotifyMatcher(client=spotify_client).match(source)
        assert target is not None
        assert target.track_id == self.match_map[source]

    def test_suggest_match(self, spotify_client: Any) -> None:
        matcher = SpotifyMatcher(client=spotify_client)
        for source, expected_track_id in self.match_map.items():
            targets = list(matcher.suggest_match(source))
            assert len(targets) > 0
            best_target = targets[0]
            assert best_target.track_id == expected_track_id

    def test_match_by_isrc(self, spotify_client: Any) -> None:
        source = TrackMock("5", ["ZZZZZ"], "ZZZZZ", "ZZZZZ", 1, 1, isrc="GBCVT9900015")
        target = SpotifyMatcher(client=spotify_client).match(source)
        assert target is not None
        assert target.isrc == "GBCVT9900015"
