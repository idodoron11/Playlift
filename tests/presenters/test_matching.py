"""Tests for presenters.matching.resolve_matches()."""

from matchers import MatchOutcome, MatchStatus
from presenters.matching import resolve_matches
from tests.matchers.matcher_mock import MatcherMock
from tests.tracks.track_mock import TrackMock
from tracks import Track
from views.match_view import IMatchView

# ---------------------------------------------------------------------------
# Fake view — records calls, no I/O
# ---------------------------------------------------------------------------


class FakeMatchView(IMatchView):
    def __init__(self, choice_sequence: list[int] | None = None) -> None:
        self.begin_called_with: int | None = None
        self.processed_count: int = 0
        self.end_called: bool = False
        self.unmatched_tracks: list[Track] = []
        self.skipped_tracks: list[Track] = []
        self.suggestion_calls: list[tuple[Track, list[Track]]] = []
        self._choice_sequence = list(choice_sequence or [])

    def begin_matching(self, total: int) -> None:
        self.begin_called_with = total

    def on_track_processed(self) -> None:
        self.processed_count += 1

    def end_matching(self) -> None:
        self.end_called = True

    def show_unmatched(self, track: Track) -> None:
        self.unmatched_tracks.append(track)

    def show_skipped(self, track: Track) -> None:
        self.skipped_tracks.append(track)

    def choose_suggestion(self, track: Track, suggestions: list[Track]) -> int:
        self.suggestion_calls.append((track, suggestions))
        if self._choice_sequence:
            return self._choice_sequence.pop(0)
        return 0


def _track(track_id: str) -> TrackMock:
    return TrackMock(track_id, ["Artist"], "Album", "Title", 200, 1)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestResolveMatchesAllMatched:
    def test_returns_all_matched_tracks(self) -> None:
        src1, src2 = _track("s1"), _track("s2")
        dst1, dst2 = _track("d1"), _track("d2")
        matcher = MatcherMock()
        matcher.outcomes = [
            MatchOutcome(source_track=src1, status=MatchStatus.MATCHED, match=dst1),
            MatchOutcome(source_track=src2, status=MatchStatus.MATCHED, match=dst2),
        ]
        view = FakeMatchView()

        result = resolve_matches([src1, src2], matcher, view)

        assert result == [dst1, dst2]

    def test_calls_view_lifecycle(self) -> None:
        src = _track("s1")
        dst = _track("d1")
        matcher = MatcherMock()
        matcher.outcomes = [MatchOutcome(source_track=src, status=MatchStatus.MATCHED, match=dst)]
        view = FakeMatchView()

        resolve_matches([src], matcher, view)

        assert view.begin_called_with == 1
        assert view.processed_count == 1
        assert view.end_called is True


class TestResolveMatchesUnmatched:
    def test_unmatched_tracks_excluded_from_result(self) -> None:
        src = _track("s1")
        matcher = MatcherMock()
        matcher.outcomes = [MatchOutcome(source_track=src, status=MatchStatus.UNMATCHED)]
        view = FakeMatchView()

        result = resolve_matches([src], matcher, view)

        assert result == []
        assert view.unmatched_tracks == [src]


class TestResolveMatchesSkipped:
    def test_skipped_tracks_excluded_from_result(self) -> None:
        src = _track("s1")
        matcher = MatcherMock()
        matcher.outcomes = [MatchOutcome(source_track=src, status=MatchStatus.SKIPPED)]
        view = FakeMatchView()

        result = resolve_matches([src], matcher, view)

        assert result == []
        assert view.skipped_tracks == [src]


class TestResolveMatchesAmbiguous:
    def test_autopilot_picks_first_suggestion(self) -> None:
        src = _track("s1")
        dst_a, dst_b = _track("d1"), _track("d2")
        matcher = MatcherMock()
        matcher.outcomes = [MatchOutcome(source_track=src, status=MatchStatus.AMBIGUOUS, suggestions=[dst_a, dst_b])]
        view = FakeMatchView()

        result = resolve_matches([src], matcher, view, autopilot=True)

        assert result == [dst_a]
        assert view.suggestion_calls == []

    def test_manual_choice_uses_view(self) -> None:
        src = _track("s1")
        dst_a, dst_b = _track("d1"), _track("d2")
        matcher = MatcherMock()
        matcher.outcomes = [MatchOutcome(source_track=src, status=MatchStatus.AMBIGUOUS, suggestions=[dst_a, dst_b])]
        view = FakeMatchView(choice_sequence=[1])

        result = resolve_matches([src], matcher, view, autopilot=False)

        assert result == [dst_b]
        assert len(view.suggestion_calls) == 1

    def test_negative_choice_excludes_track(self) -> None:
        src = _track("s1")
        dst_a = _track("d1")
        matcher = MatcherMock()
        matcher.outcomes = [MatchOutcome(source_track=src, status=MatchStatus.AMBIGUOUS, suggestions=[dst_a])]
        view = FakeMatchView(choice_sequence=[-1])

        result = resolve_matches([src], matcher, view, autopilot=False)

        assert result == []


class TestResolveMatchesEmbedMatches:
    def test_embed_matches_true_calls_matcher_embed(self) -> None:
        src = _track("s1")
        dst = _track("d1")
        matcher = MatcherMock()
        matcher.outcomes = [MatchOutcome(source_track=src, status=MatchStatus.MATCHED, match=dst)]
        view = FakeMatchView()

        resolve_matches([src], matcher, view, embed_matches=True)

        assert matcher.embedded_pairs == [(src, dst)]

    def test_embed_matches_false_does_not_call_matcher_embed(self) -> None:
        src = _track("s1")
        dst = _track("d1")
        matcher = MatcherMock()
        matcher.outcomes = [MatchOutcome(source_track=src, status=MatchStatus.MATCHED, match=dst)]
        view = FakeMatchView()

        resolve_matches([src], matcher, view, embed_matches=False)

        assert matcher.embedded_pairs == []
