from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum

from api.spotify import get_spotify_client
from tracks import Track

MATCH_AVG_THRESHOLD: float = 0.6
MATCH_DURATION_TOLERANCE_SECONDS: float = 3.0
MATCH_LOOSE_DURATION_TOLERANCE_SECONDS: float = 5.0


class MatchStatus(Enum):
    """Outcome category for a single track matching attempt."""

    MATCHED = "matched"
    AMBIGUOUS = "ambiguous"
    UNMATCHED = "unmatched"
    SKIPPED = "skipped"


@dataclass
class MatchOutcome:
    """Result of attempting to match one source track."""

    source_track: Track
    status: MatchStatus
    match: Track | None = None
    suggestions: list[Track] = field(default_factory=list)


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
    def match_list(self, tracks: Iterable[Track]) -> Iterator[MatchOutcome]:
        """Yield a :class:`MatchOutcome` for each track in *tracks*.

        Pure batch matching — no user interaction, no progress display.
        """
        pass

    @abstractmethod
    def embed_matches(self, pairs: list[tuple[Track, Track]]) -> None:
        """Persist matched service refs back into source tracks.

        Args:
            pairs: Each element is ``(source_track, matched_track)``.
        """
        pass

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
