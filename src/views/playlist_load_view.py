"""Abstract View contract for the local playlist loading workflow."""

from abc import ABC, abstractmethod


class IPlaylistLoadView(ABC):
    """Passive view interface for the local track-loading process.

    Implementations display loading progress. The model depends only on this
    interface — concrete views (CLI, GUI, test fakes) are injected at the
    composition root.
    """

    @abstractmethod
    def begin_loading(self, total: int) -> None:
        """Called once before the loading loop starts.

        Args:
            total: Total number of files to process.
        """

    @abstractmethod
    def on_track_loaded(self) -> None:
        """Called once after each file is processed, whether successfully loaded or not."""

    @abstractmethod
    def end_loading(self) -> None:
        """Called once after the loading loop finishes."""
