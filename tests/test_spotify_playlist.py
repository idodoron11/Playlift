from unittest import TestCase

from playlists.spotify_playlist import SpotifyPlaylist


class TestSpotifyPlaylist(TestCase):
    def test_tracks(self):
        indie_mix_playlist = SpotifyPlaylist("37i9dQZF1EQqkOPvHGajmW")
        self.assertEqual(len(list(indie_mix_playlist.tracks)), 50)

    def test_playlist_id(self):
        indie_mix_playlist = SpotifyPlaylist("37i9dQZF1EQqkOPvHGajmW")
        self.assertEqual(indie_mix_playlist.playlist_id, "37i9dQZF1EQqkOPvHGajmW")

    def test_name(self):
        indie_mix_playlist = SpotifyPlaylist("37i9dQZF1EQqkOPvHGajmW")
        self.assertEqual(indie_mix_playlist.name, "Indie Mix")
