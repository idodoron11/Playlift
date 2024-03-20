from typing import Optional, List

from matchers import Matcher
from tracks import Track


class MatcherMock(Matcher):
    def __init__(self):
        super().__init__()
        self.match_output: Optional[Track] = None
        self.suggest_output: List[Track] = []

    def match(self, track: Track) -> Optional[Track]:
        return self.match_output

    def suggest_match(self, track: Track) -> List[Track]:
        return self.suggest_output
