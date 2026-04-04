from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import TestCase

import pytest

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
        deep_purple_hits_playlist = SpotifyPlaylist(DEEP_PURPLE_HITS_PLAYLIST_ID)
        assert len(list(deep_purple_hits_playlist.tracks)) == DEEP_PURPLE_HITS_TRACK_COUNT

    def test_tracks_with_more_than_100_tracks(self) -> None:
        chill_vibes_playlist = SpotifyPlaylist(CHILL_VIBES_PLAYLIST_ID)
        tracks = list(chill_vibes_playlist.tracks)
        assert len(tracks) > CHILL_VIBES_MIN_TRACK_COUNT

    def test_playlist_id(self) -> None:
        chill_mix_playlist = SpotifyPlaylist(CHILL_MIX_PLAYLIST_ID)
        assert chill_mix_playlist.playlist_id == CHILL_MIX_PLAYLIST_ID

    def test_name(self) -> None:
        deep_purple_hits_playlist = SpotifyPlaylist(DEEP_PURPLE_HITS_PLAYLIST_ID)
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
        target_playlist = SpotifyPlaylistSpy.create_from_another_playlist(SOURCE_PLAYLIST_NAME, source_playlist)
        assert len(target_playlist.tracks) == 1
        assert target_playlist.tracks[0].title == source_playlist.tracks[0].title
        assert target_playlist.tracks[0].display_artist == source_playlist.tracks[0].display_artist
        assert target_playlist.tracks[0].album == source_playlist.tracks[0].album

    def test_init(self) -> None:
        playlist = SpotifyPlaylist(ENDPOINTS_PLAYLIST_URL)
        tracks = playlist.tracks
        actual_songs_names = [track.title for track in tracks]
        assert actual_songs_names == ENDPOINTS_PLAYLIST_TRACK_TITLES

    def test_e2e_spotify_playlist(self) -> None:
        playlist = SpotifyPlaylist.create(E2E_PLAYLIST_NAME)
        assert len(playlist.tracks) == 0
        tracks = list(map(SpotifyTrack, E2E_TRACK_IDS))
        playlist.add_tracks(tracks)
        assert playlist.tracks == tracks
        playlist.remove_track([playlist.tracks[0]])
        assert len(playlist.tracks) == E2E_TRACKS_AFTER_REMOVE
        playlist.clear()
        assert len(playlist.tracks) == 0
