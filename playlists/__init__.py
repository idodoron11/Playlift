"""Playlist Providers"""
from abc import ABC, abstractmethod
from typing import Iterable

from tracks import Track


class Playlist(ABC):
    @property
    @abstractmethod
    def tracks(self) -> Iterable[Track]:
        pass

    @abstractmethod
    def remove_track(self, track: Track) -> None:
        pass

    @abstractmethod
    def add_track(self, track: Track) -> None:
        pass
