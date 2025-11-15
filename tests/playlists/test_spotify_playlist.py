from unittest import TestCase

from playlists.spotify_playlist import SpotifyPlaylist
from tests.playlists.playlist_mock import PlaylistMock
from tests.playlists.spotify_playlist_spy import SpotifyPlaylistSpy
from tests.tracks.track_mock import TrackMock
from tracks.spotify_track import SpotifyTrack


class TestSpotifyPlaylist(TestCase):
    def test_tracks(self):
        indie_mix_playlist = SpotifyPlaylist("37i9dQZF1EQqkOPvHGajmW")
        self.assertEqual(len(list(indie_mix_playlist.tracks)), 50)

    def test_tracks_with_more_than_100_tracks(self):
        chill_vibes_playlist = SpotifyPlaylist("37i9dQZF1DX889U0CL85jj")
        tracks = list(chill_vibes_playlist.tracks)
        self.assertGreater(len(tracks), 100)

    def test_playlist_id(self):
        indie_mix_playlist = SpotifyPlaylist("37i9dQZF1EQqkOPvHGajmW")
        self.assertEqual(indie_mix_playlist.playlist_id, "37i9dQZF1EQqkOPvHGajmW")

    def test_name(self):
        indie_mix_playlist = SpotifyPlaylist("37i9dQZF1EQqkOPvHGajmW")
        self.assertEqual(indie_mix_playlist.name, "Indie Mix")

    def test_create_from_another_playlist(self):
        source_tracks = [
            TrackMock(
                "1",
                ["Led Zeppelin"],
                "Led Zeppelin IV (Remaster)",
                "Black Dog - Remaster",
                4 * 60 + 55,
                1
            )
        ]
        source_playlist = PlaylistMock(source_tracks)
        target_playlist = SpotifyPlaylistSpy.create_from_another_playlist("playlist name", source_playlist)
        self.assertEqual(len(target_playlist.tracks), 1)
        self.assertEqual(target_playlist.tracks[0].title, source_playlist.tracks[0].title)
        self.assertEqual(target_playlist.tracks[0].display_artist, source_playlist.tracks[0].display_artist)
        self.assertEqual(target_playlist.tracks[0].album, source_playlist.tracks[0].album)

    def test_init(self):
        playlist = SpotifyPlaylist("https://open.spotify.com/playlist/3cEYpjA9oz9GiPac4AsH4n")
        tracks = playlist.tracks
        expected_songs_names = [
            "Api",
            "Is",
            "All I Want",
            "Endpoints",
            "You Are So Beautiful"
        ]
        actual_songs_names = [track.title for track in tracks]
        self.assertEqual(expected_songs_names, actual_songs_names)

    def test_e2e_spotify_playlist(self):
        playlist = SpotifyPlaylist.create("Test Playlist")
        self.assertEqual(len(playlist.tracks), 0)
        track_ids = [
            "4OSBTYWVwsQhGLF9NHvIbR",
            "5mFMb5OHI3cN0UjITVztCj",
            "1CRtJS94Hq3PbBZT9LuF90"
        ]
        tracks = list(map(SpotifyTrack, track_ids))
        playlist.add_tracks(tracks)
        self.assertEqual(playlist.tracks, tracks)
        playlist.remove_track([playlist.tracks[0]])
        self.assertEqual(len(playlist.tracks), 2)
        playlist.clear()
        self.assertEqual(len(playlist.tracks), 0)



