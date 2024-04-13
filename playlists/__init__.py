"""Playlist Providers"""
from abc import ABC, abstractmethod
from typing import Iterable, List

from matchers import Matcher
from tracks import Track


class TrackCollection(ABC):
    @property
    @abstractmethod
    def tracks(self) -> Iterable[Track]:
        pass


class Playlist(TrackCollection, ABC):

    @staticmethod
    @abstractmethod
    def track_matcher() -> Matcher:
        pass

    @abstractmethod
    def remove_track(self, tracks: List[Track]) -> None:
        pass

    @abstractmethod
    def add_tracks(self, track: Track) -> None:
        pass
