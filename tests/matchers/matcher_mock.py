from collections.abc import Iterable, Iterator

from matchers import Matcher, MatchOutcome
from tracks import Track


class MatcherMock(Matcher):
    def __init__(self) -> None:
        super().__init__()
        self.match_output: Track | None = None
        self.suggest_output: list[Track] = []
        self.outcomes: list[MatchOutcome] = []
        self.embedded_pairs: list[tuple[Track, Track]] = []

    def match(self, track: Track) -> Track | None:
        return self.match_output

    def suggest_match(self, track: Track) -> list[Track]:
        return self.suggest_output

    def match_list(self, tracks: Iterable[Track]) -> Iterator[MatchOutcome]:
        yield from self.outcomes

    def embed_matches(self, pairs: list[tuple[Track, Track]]) -> None:
        self.embedded_pairs.extend(pairs)
