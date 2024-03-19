from typing import List
from unittest import TestCase

from matchers.spotify_matcher import SpotifyMatcher
from tracks import Track


class MockTrack(Track):
    @property
    def artists(self) -> List[str]:
        return self._artists

    @property
    def title(self) -> str:
        return self._title

    @property
    def album(self) -> str:
        return self._album

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def track_id(self) -> str:
        return self._id

    def __eq__(self, other):
        if other is None or not isinstance(other, self.__class__):
            return False
        return self.track_id == other.track_id

    def __hash__(self):
        return hash(self._id)

    def __init__(self, track_id, artists, album, title, duration):
        self._id = track_id
        self._artists = artists
        self._album = album
        self._title = title
        self._duration = duration


class TestSpotifyMatcher(TestCase):
    def test_match(self):
        source = MockTrack("3", ["Muse"], "Showbiz", "Unintended", 3 * 60 + 55)
        target = SpotifyMatcher.get_instance().match(source)
        self.assertEqual(target.track_id, '6kyxQuFD38mo4S3urD2Wkw')

    def test_suggest_match(self):
        source = MockTrack("2", ["3 doors down"], "away from the sun", "here without you", 3 * 60 + 57)
        targets = SpotifyMatcher.get_instance().suggest_match(source)
        self.assertGreater(len(targets), 0)
        best_target = targets[0]
        self.assertEqual(best_target.track_id, '3NLrRZoMF0Lx6zTlYqeIo4')
