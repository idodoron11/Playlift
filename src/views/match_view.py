"""Abstract View contract for the track-matching workflow."""

from abc import ABC, abstractmethod

from tracks import Track


class IMatchView(ABC):
    """Passive view interface for the track-matching Presenter.

    Implementations display matching progress and collect user input for
    ambiguous cases. The Presenter depends only on this interface — concrete
    views (CLI, GUI, test fakes) are injected at the composition root.
    """

    @abstractmethod
    def begin_matching(self, total: int) -> None:
        """Called once before the matching loop starts.

        Args:
            total: Total number of tracks to process.
        """

    @abstractmethod
    def on_track_processed(self) -> None:
        """Called once after each track outcome is produced."""

    @abstractmethod
    def end_matching(self) -> None:
        """Called once after the matching loop finishes."""

    @abstractmethod
    def show_unmatched(self, track: Track) -> None:
        """Notify the user that *track* could not be matched.

        Args:
            track: The source track for which no match was found.
        """

    @abstractmethod
    def show_skipped(self, track: Track) -> None:
        """Notify the user that *track* is marked to be skipped.

        Args:
            track: The source track that carries a SKIP sentinel.
        """

    @abstractmethod
    def choose_suggestion(self, track: Track, suggestions: list[Track]) -> int:
        """Ask the user to pick the best match from *suggestions*.

        Args:
            track: The source track being reviewed.
            suggestions: Ordered list of candidate matches.

        Returns:
            Zero-based index into *suggestions* of the chosen match, or ``-1``
            to skip the track entirely.
        """
