"""Presenter helper for the track-matching workflow."""

from matchers import Matcher, MatchOutcome, MatchStatus
from tracks import Track
from views.match_view import IMatchView


def resolve_matches(
    tracks: list[Track],
    matcher: Matcher,
    view: IMatchView,
    autopilot: bool = False,
    embed_matches: bool = False,
) -> list[Track]:
    """Drive the full track-matching workflow and return confirmed matched tracks.

    Three phases:
    1. **Matching loop** — iterate outcomes from the Matcher, report progress
       through *view*, collect confirmed matches and defer ambiguous ones.
    2. **Ambiguous review** — for each ambiguous outcome, either take the top
       suggestion (``autopilot=True``) or ask the user via *view*.
    3. **Embed** — if ``embed_matches`` is True, persist refs back to source tracks.

    Args:
        tracks: Source tracks to match.
        matcher: The :class:`~matchers.Matcher` that performs batch matching.
        view: The :class:`~views.match_view.IMatchView` used for progress
            display and user interaction.
        autopilot: When True, automatically pick the first suggestion for
            ambiguous tracks without prompting the user.
        embed_matches: When True, persist the matched service refs back into
            the source tracks' metadata after all decisions are made.

    Returns:
        List of confirmed matched destination tracks, in encounter order.
    """
    confirmed_pairs: list[tuple[Track, Track]] = []
    ambiguous_outcomes: list[MatchOutcome] = []

    # ── Phase 1: matching loop ────────────────────────────────────────────────
    view.begin_matching(len(tracks))
    for outcome in matcher.match_list(tracks):
        view.on_track_processed()
        if outcome.status == MatchStatus.MATCHED:
            assert outcome.match is not None
            confirmed_pairs.append((outcome.source_track, outcome.match))
        elif outcome.status == MatchStatus.AMBIGUOUS:
            ambiguous_outcomes.append(outcome)
        elif outcome.status == MatchStatus.UNMATCHED:
            view.show_unmatched(outcome.source_track)
        elif outcome.status == MatchStatus.SKIPPED:
            view.show_skipped(outcome.source_track)
    view.end_matching()

    # ── Phase 2: resolve ambiguous ────────────────────────────────────────────
    for outcome in ambiguous_outcomes:
        if autopilot:
            chosen = outcome.suggestions[0]
        else:
            idx = view.choose_suggestion(outcome.source_track, outcome.suggestions)
            if idx < 0:
                continue
            chosen = outcome.suggestions[idx]
        confirmed_pairs.append((outcome.source_track, chosen))

    # ── Phase 3: embed matches ────────────────────────────────────────────────
    if embed_matches:
        matcher.embed_matches(confirmed_pairs)

    return [match for _, match in confirmed_pairs]
