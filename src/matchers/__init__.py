from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from difflib import SequenceMatcher

import click
from tabulate import tabulate

from api.spotify import get_spotify_client
from tracks import Track

MATCH_AVG_THRESHOLD: float = 0.6
MATCH_DURATION_TOLERANCE_SECONDS: float = 3.0
MATCH_LOOSE_DURATION_TOLERANCE_SECONDS: float = 5.0


class Matcher(ABC):
    __instance: "Matcher | None" = None

    @classmethod
    def get_instance(cls) -> "Matcher":
        if cls.__instance is None:
            cls.__instance = cls(client=get_spotify_client())  # type: ignore[call-arg]
        return cls.__instance

    @abstractmethod
    def match(self, track: Track) -> Track | None:
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
    def track_distance(track1: Track, track2: Track) -> tuple[float, float, float, float]:
        title_d = SequenceMatcher(None, track1.title, track2.title).ratio() if track1.title and track2.title else 0
        artist_d = (
            SequenceMatcher(None, track1.display_artist, track2.display_artist).ratio()
            if track1.display_artist and track2.display_artist
            else 0
        )
        album_d = SequenceMatcher(None, track1.album, track2.album).ratio() if track1.album and track2.album else 0
        return (1 - title_d, 1 - artist_d, 1 - album_d, abs(track1.duration - track2.duration))

    @abstractmethod
    def match_list(self, tracks: Iterable[Track], autopilot: bool = False, embed_matches: bool = False) -> list[Track]:
        pass

    @staticmethod
    def choose_suggestion(track: Track, suggestions: Sequence[Track]) -> int:
        print(f"Please choose the best match for\n{track}")
        print("If none match, type -1")
        headers = ["#", "Artist", "Track Title", "Album", "Track Position", "Duration"]
        data = [
            (pos, track.display_artist, track.title, track.album, track.track_number, track.duration)
            for pos, track in enumerate(suggestions)
        ]
        results_tbl_visual = tabulate(data, headers=headers)
        print(results_tbl_visual)
        return int(
            click.prompt("Enter best match index (#):", default=0, type=click.IntRange(-1, len(suggestions) - 1))
        )

    def _match_constraints(self, source_track: Track, suggestion: Track) -> bool:
        """Return True when *suggestion* is close enough to *source_track* to be a valid match.

        Applies SequenceMatcher ratios for title, artist, and album plus a
        duration delta guard. Non-Latin artist names bypass the artist similarity
        check (streaming services may not carry the original-language name).
        """
        title_d, artist_d, album_d, duration_d = Matcher.track_distance(source_track, suggestion)
        title_d = 1 - title_d
        artist_d = 1 - artist_d
        album_d = 1 - album_d

        def is_latin(text: str) -> bool:
            return all(not char.isalpha() or ord("a") <= ord(char.lower()) <= ord("z") for char in text)

        if not is_latin(source_track.display_artist):
            artist_d = 1  # service may not list the artist in the original language

        avg_d = (title_d + artist_d + album_d) / 3
        if avg_d > MATCH_AVG_THRESHOLD and duration_d < MATCH_DURATION_TOLERANCE_SECONDS:
            return True
        if (
            artist_d >= 0.75
            and album_d >= 0.75
            and source_track.track_number == suggestion.track_number
            and duration_d <= MATCH_DURATION_TOLERANCE_SECONDS
        ):
            return True

        return (
            title_d >= 0.5
            and artist_d >= 0.5
            and album_d >= 0.5
            and duration_d <= MATCH_LOOSE_DURATION_TOLERANCE_SECONDS
        )
