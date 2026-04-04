from unittest import TestCase

from matchers.spotify_matcher import SpotifyMatcher
from tests.tracks.track_mock import TrackMock


class TestSpotifyMatcher(TestCase):
    UNINTENDED_TRACK = TrackMock("1", ["Muse"], "Showbiz", "Unintended", 3 * 60 + 55, 7)
    HERE_WITHOUT_YOU_TRACK = TrackMock("2", ["3 doors down"], "away from the sun", "here without you", 3 * 60 + 57,6)
    WILD_TRACK = TrackMock("3", ['LP'], "Love Lines (Deluxe Version)", "Wild", 181, 2)
    ZE_RAK_HALEV = TrackMock("4", ['אביב גפן'], "עם הזמן", "זה רק הלב שכואב לך", 232, 4)

    match_map = {
        UNINTENDED_TRACK: "6kyxQuFD38mo4S3urD2Wkw",
        HERE_WITHOUT_YOU_TRACK: "3NLrRZoMF0Lx6zTlYqeIo4",
        WILD_TRACK: "3QdeMlhJH3fAMbMPVD5ZAu",
        ZE_RAK_HALEV: "0wRnFA1iu3RSfCPvWfvWgp"
    }

    def test_match(self) -> None:
        source = self.UNINTENDED_TRACK
        target = SpotifyMatcher.get_instance().match(source)
        assert target is not None
        self.assertEqual(target.track_id, self.match_map[source])

    def test_suggest_match(self) -> None:
        for source, expected_track_id in self.match_map.items():
            targets = list(SpotifyMatcher.get_instance().suggest_match(source))
            self.assertGreater(len(targets), 0)
            best_target = targets[0]
            self.assertEqual(best_target.track_id, expected_track_id)
