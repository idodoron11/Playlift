from abc import ABC, abstractmethod
from difflib import SequenceMatcher
from typing import Iterable, Optional, Tuple, List

from tracks import Track


class Matcher(ABC):
    __instance = None

    def __init__(self):
        if Matcher.__instance is not None:
            raise TypeError("An instance of this class already exists")

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    @abstractmethod
    def match(self, track: Track) -> Optional[Track]:
        """
        :param track: track instance, of type A
        :return: track instance, of type B, that matches the input track
        """
        pass

    @abstractmethod
    def suggest_match(self, track: Track) -> Iterable[Track]:
        """
        :param track: track instance, of type A
        :return: a collection of tracks, of type B, that may match the input track
        """
        pass

    @staticmethod
    def track_distance(track1: Track, track2: Track) -> Tuple[float, float, float, float]:
        title_d = SequenceMatcher(None, track1.title, track2.title).ratio() if track1.title and track2.title else 0
        artist_d = SequenceMatcher(None, track1.display_artist, track2.display_artist).ratio() if track1.display_artist and track2.display_artist else 0
        album_d = SequenceMatcher(None, track1.album, track2.album).ratio() if track1.album and track2.album else 0
        return (
            1 - title_d,
            1 - artist_d,
            1 - album_d,
            abs(track1.duration - track2.duration)
        )

    @abstractmethod
    def match_list(self, tracks: List[Track]) -> Iterable[Iterable[Track]]:
        pass
