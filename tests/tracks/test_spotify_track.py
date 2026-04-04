from unittest import TestCase

from tracks.spotify_track import SpotifyTrack


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
