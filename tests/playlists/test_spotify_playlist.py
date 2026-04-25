from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import spotipy

from playlists.spotify_playlist import SpotifyPlaylist

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
