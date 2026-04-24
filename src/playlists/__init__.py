"""Playlist Providers"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from matchers import Matcher
from tracks import Track

_S = TypeVar("_S", bound=Track)
_T = TypeVar("_T", bound=Track)


@dataclass
class CompareResult(Generic[_S, _T]):
    """Result of comparing two playlists.

    Attributes:
        source_only: Tracks present in the source/first playlist but absent from the target.
        target_only: Tracks present in the target/second playlist but absent from the source.
    """

    source_only: list[_S] = field(default_factory=list)
    target_only: list[_T] = field(default_factory=list)


class TrackCollection(ABC):
    @property
    @abstractmethod
    def tracks(self) -> Iterable[Track]:
        pass


class SyncTarget(ABC):
    """Contract for a platform that tracks can be matched and synced into.

    A class implementing ``SyncTarget`` must provide a ``track_matcher()`` that
    returns the platform-specific ``Matcher`` used to resolve local tracks to
    their remote equivalents.
    """

    @staticmethod
    @abstractmethod
    def track_matcher() -> Matcher:
        """Return the Matcher instance for this sync-target platform."""


class Playlist(TrackCollection, ABC):
    @abstractmethod
    def remove_track(self, tracks: list[Track]) -> None:
        pass

    @abstractmethod
    def add_tracks(self, track: Track) -> None:
        pass
