from unittest import TestCase

from matchers.spotify_matcher import SpotifyMatcher
from tests.tracks.track_mock import TrackMock


class TestSpotifyMatcher(TestCase):
    UNINTENDED_TRACK = TrackMock("3", ["Muse"], "Showbiz", "Unintended", 3 * 60 + 55, 7)
    HERE_WITHOUT_YOU_TRACK = TrackMock("2", ["3 doors down"], "away from the sun", "here without you", 3 * 60 + 57,6)
    WILD_TRACK = TrackMock("1", ['LP'], "Love Lines (Deluxe Version)", "Wild", 181, 2)

    match_map = {
        UNINTENDED_TRACK: "6kyxQuFD38mo4S3urD2Wkw",
        HERE_WITHOUT_YOU_TRACK: "3NLrRZoMF0Lx6zTlYqeIo4",
        WILD_TRACK: "3QdeMlhJH3fAMbMPVD5ZAu"
    }

    def test_match(self):
        source = self.UNINTENDED_TRACK
        target = SpotifyMatcher.get_instance().match(source)
        self.assertEqual(target.track_id, self.match_map[source])

    def test_suggest_match(self):
        for source, expected_track_id in self.match_map.items():
            targets = SpotifyMatcher.get_instance().suggest_match(source)
            self.assertGreater(len(targets), 0)
            best_target = targets[0]
            self.assertEqual(best_target.track_id, expected_track_id)
