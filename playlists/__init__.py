"""Playlist Providers"""
from abc import ABC, abstractmethod
from typing import Iterable, List

from tracks import Track


class Playlist(ABC):
    @property
    @abstractmethod
    def tracks(self) -> Iterable[Track]:
        pass

    @abstractmethod
    def remove_track(self, tracks: List[Track]) -> None:
        pass

    @abstractmethod
    def add_tracks(self, track: Track) -> None:
        pass
