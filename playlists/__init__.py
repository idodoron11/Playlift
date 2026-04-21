"""Playlist Providers"""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from matchers import Matcher
from tracks import Track


class TrackCollection(ABC):
    @property
    @abstractmethod
    def tracks(self) -> Iterable[Track]:
        pass


class SyncTarget(ABC):
    @staticmethod
    @abstractmethod
    def track_matcher() -> Matcher:
        pass


class Playlist(TrackCollection, ABC):
    @abstractmethod
    def remove_track(self, tracks: list[Track]) -> None:
        pass

    @abstractmethod
    def add_tracks(self, track: Track) -> None:
        pass
