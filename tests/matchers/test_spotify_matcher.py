from unittest import TestCase

from matchers.spotify_matcher import SpotifyMatcher
from tests.tracks.track_mock import TrackMock


class TestSpotifyMatcher(TestCase):
    def test_match(self):
        source = TrackMock("3", ["Muse"], "Showbiz", "Unintended", 3 * 60 + 55, 7)
        target = SpotifyMatcher.get_instance().match(source)
        self.assertEqual(target.track_id, '6kyxQuFD38mo4S3urD2Wkw')

    def test_suggest_match(self):
        source = TrackMock("2", ["3 doors down"], "away from the sun", "here without you", 3 * 60 + 57, 6)
        targets = SpotifyMatcher.get_instance().suggest_match(source)
        self.assertGreater(len(targets), 0)
        best_target = targets[0]
        self.assertEqual(best_target.track_id, '3NLrRZoMF0Lx6zTlYqeIo4')
