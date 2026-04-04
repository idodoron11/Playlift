from collections.abc import Iterable

from matchers import Matcher
from tracks import Track


class MatcherMock(Matcher):
    def __init__(self) -> None:
        super().__init__()
        self.match_output: Track | None = None
        self.suggest_output: list[Track] = []

    def match(self, track: Track) -> Track | None:
        return self.match_output

    def suggest_match(self, track: Track) -> list[Track]:
        return self.suggest_output

    def match_list(self, tracks: Iterable[Track], autopilot: bool = False, embed_matches: bool = False) -> list[Track]:
        return []
