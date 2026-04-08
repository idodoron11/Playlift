from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest
import spotipy

from api.spotify import get_spotify_client
from playlists.spotify_playlist import SpotifyPlaylist
from tests.playlists.playlist_mock import PlaylistMock
from tests.playlists.spotify_playlist_spy import SpotifyPlaylistSpy
from tests.tracks.track_mock import TrackMock
from tracks.spotify_track import SpotifyTrack

if TYPE_CHECKING:
    from tracks import Track

# Playlist IDs / URIs used across tests
DEEP_PURPLE_HITS_PLAYLIST_ID = "4X7RPexaMm2XwDb6g1fRmQ"
DEEP_PURPLE_HITS_PLAYLIST_NAME = "Deep Purple - Greatest Hits"
DEEP_PURPLE_HITS_TRACK_COUNT = 59

CHILL_VIBES_PLAYLIST_ID = "31uSi3T52m00gqt4MwuZNM"
CHILL_VIBES_MIN_TRACK_COUNT = 100

CHILL_MIX_PLAYLIST_ID = "37i9dQZF1EQqkOPvHGajmW"

ENDPOINTS_PLAYLIST_URL = "https://open.spotify.com/playlist/3cEYpjA9oz9GiPac4AsH4n"
ENDPOINTS_PLAYLIST_TRACK_TITLES = ["Api", "Is", "All I Want", "Endpoints", "You Are So Beautiful"]

# Track data for create_from_another_playlist test
SOURCE_TRACK_ID = "1"
SOURCE_TRACK_ARTISTS = ["Led Zeppelin"]
SOURCE_TRACK_ALBUM = "Led Zeppelin IV (Remaster)"
SOURCE_TRACK_TITLE = "Black Dog - Remaster"
SOURCE_TRACK_DURATION_SECONDS = 4 * 60 + 55
SOURCE_TRACK_NUMBER = 1
SOURCE_PLAYLIST_NAME = "playlist name"

# E2E test data
E2E_PLAYLIST_NAME = "Test Playlist"
E2E_TRACK_IDS = ["4OSBTYWVwsQhGLF9NHvIbR", "5mFMb5OHI3cN0UjITVztCj", "1CRtJS94Hq3PbBZT9LuF90"]
E2E_TRACKS_AFTER_REMOVE = 2


@pytest.mark.integration
class TestSpotifyPlaylist(TestCase):
    def test_tracks(self) -> None:
        deep_purple_hits_playlist = SpotifyPlaylist(DEEP_PURPLE_HITS_PLAYLIST_ID, client=get_spotify_client())
        assert len(list(deep_purple_hits_playlist.tracks)) == DEEP_PURPLE_HITS_TRACK_COUNT

    def test_tracks_with_more_than_100_tracks(self) -> None:
        chill_vibes_playlist = SpotifyPlaylist(CHILL_VIBES_PLAYLIST_ID, client=get_spotify_client())
        tracks = list(chill_vibes_playlist.tracks)
        assert len(tracks) > CHILL_VIBES_MIN_TRACK_COUNT

    def test_playlist_id(self) -> None:
        chill_mix_playlist = SpotifyPlaylist(CHILL_MIX_PLAYLIST_ID, client=get_spotify_client())
        assert chill_mix_playlist.playlist_id == CHILL_MIX_PLAYLIST_ID

    def test_name(self) -> None:
        deep_purple_hits_playlist = SpotifyPlaylist(DEEP_PURPLE_HITS_PLAYLIST_ID, client=get_spotify_client())
        assert deep_purple_hits_playlist.name == DEEP_PURPLE_HITS_PLAYLIST_NAME

    def test_create_from_another_playlist(self) -> None:
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
            SOURCE_PLAYLIST_NAME, source_playlist, client=get_spotify_client()
        )
        assert len(target_playlist.tracks) == 1
        assert target_playlist.tracks[0].title == source_playlist.tracks[0].title
        assert target_playlist.tracks[0].display_artist == source_playlist.tracks[0].display_artist
        assert target_playlist.tracks[0].album == source_playlist.tracks[0].album

    def test_init(self) -> None:
        playlist = SpotifyPlaylist(ENDPOINTS_PLAYLIST_URL, client=get_spotify_client())
        tracks = playlist.tracks
        actual_songs_names = [track.title for track in tracks]
        assert actual_songs_names == ENDPOINTS_PLAYLIST_TRACK_TITLES

    def test_e2e_spotify_playlist(self) -> None:
        client = get_spotify_client()
        playlist = SpotifyPlaylist.create(E2E_PLAYLIST_NAME, client=client)
        assert len(playlist.tracks) == 0
        tracks = [SpotifyTrack(tid, client=client) for tid in E2E_TRACK_IDS]
        playlist.add_tracks(tracks)
        assert playlist.tracks == tracks
        playlist.remove_track([playlist.tracks[0]])
        assert len(playlist.tracks) == E2E_TRACKS_AFTER_REMOVE
        playlist.clear()
        assert len(playlist.tracks) == 0


# ---------------------------------------------------------------------------
# T008: SpotifyPlaylist unit tests — no live Spotify connection
# ---------------------------------------------------------------------------

PLAYLIST_ID = "playlist123"
PLAYLIST_NAME = "My Playlist"
TRACK_ID_1 = "track001"
TRACK_ID_2 = "track002"


def _make_track_item(track_id: str) -> dict:  # type: ignore[type-arg]
    return {
        "track": {
            "id": track_id,
            "name": f"Track {track_id}",
            "artists": [{"name": "Artist"}],
            "album": {"name": "Album"},
            "duration_ms": 200000,
            "track_number": 1,
        }
    }


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock(spec=spotipy.Spotify)
    client._get_id.side_effect = lambda type_, url: url
    return client


@pytest.fixture
def spotify_playlist(mock_client: MagicMock) -> SpotifyPlaylist:
    return SpotifyPlaylist(PLAYLIST_ID, client=mock_client)


class TestSpotifyPlaylistUnit:
    def test_tracks_loads_data_via_playlist_api(
        self, spotify_playlist: SpotifyPlaylist, mock_client: MagicMock
    ) -> None:
        mock_client.playlist.return_value = {
            "id": PLAYLIST_ID,
            "name": PLAYLIST_NAME,
            "tracks": {"items": [_make_track_item(TRACK_ID_1)], "next": None},
        }
        mock_client.next.return_value = None

        tracks = spotify_playlist.tracks

        mock_client.playlist.assert_called_once_with(PLAYLIST_ID)
        assert len(tracks) == 1

    def test_tracks_paginates_until_next_is_none(
        self, spotify_playlist: SpotifyPlaylist, mock_client: MagicMock
    ) -> None:
        first_page = {
            "id": PLAYLIST_ID,
            "name": PLAYLIST_NAME,
            "tracks": {"items": [_make_track_item(TRACK_ID_1)], "next": "url"},
        }
        second_page = {"items": [_make_track_item(TRACK_ID_2)], "next": None}
        mock_client.playlist.return_value = first_page
        mock_client.next.return_value = second_page

        tracks = spotify_playlist.tracks

        assert len(tracks) == 2
        mock_client.next.assert_called_once()

    def test_add_tracks_calls_playlist_add_items(
        self, spotify_playlist: SpotifyPlaylist, mock_client: MagicMock
    ) -> None:
        mock_track = MagicMock()
        mock_track.track_id = TRACK_ID_1

        spotify_playlist.add_tracks([mock_track])

        mock_client.playlist_add_items.assert_called_once()

    def test_add_tracks_batches_in_chunks_of_100(
        self, spotify_playlist: SpotifyPlaylist, mock_client: MagicMock
    ) -> None:
        mock_tracks = [MagicMock() for _ in range(101)]
        for i, t in enumerate(mock_tracks):
            t.track_id = f"id{i}"

        spotify_playlist.add_tracks(mock_tracks)  # type: ignore[arg-type]

        assert mock_client.playlist_add_items.call_count == 2

    def test_remove_track_calls_playlist_remove(
        self, spotify_playlist: SpotifyPlaylist, mock_client: MagicMock
    ) -> None:
        mock_track = MagicMock()
        mock_track.track_id = TRACK_ID_1

        spotify_playlist.remove_track([mock_track])

        mock_client.playlist_remove_all_occurrences_of_items.assert_called_once()

    def test_create_uses_injected_client(self, mock_client: MagicMock) -> None:
        mock_client.current_user.return_value = {"id": "user1"}
        mock_client.user_playlist_create.return_value = {"id": PLAYLIST_ID}

        playlist = SpotifyPlaylist.create(PLAYLIST_NAME, client=mock_client)

        mock_client.current_user.assert_called_once()
        assert playlist.playlist_id == PLAYLIST_ID

    def test_create_from_another_playlist_uses_injected_client(self, mock_client: MagicMock) -> None:
        mock_client.current_user.return_value = {"id": "user1"}
        mock_client.user_playlist_create.return_value = {"id": PLAYLIST_ID}

        mock_track = MagicMock()
        mock_track.track_id = TRACK_ID_1
        source_playlist = MagicMock()
        source_playlist.tracks = [mock_track]

        mock_matcher = MagicMock()
        mock_matcher.match_list.return_value = [mock_track]

        with patch.object(SpotifyPlaylist, "track_matcher", return_value=mock_matcher):
            playlist = SpotifyPlaylist.create_from_another_playlist(PLAYLIST_NAME, source_playlist, client=mock_client)

        mock_client.current_user.assert_called_once()
        mock_client.playlist_add_items.assert_called_once()
        assert playlist.playlist_id == PLAYLIST_ID
