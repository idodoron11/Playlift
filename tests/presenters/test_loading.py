"""Tests for presenters.loading.resolve_source()."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from exceptions import InvalidPathMappingError, UnrecognisedSourceError
from presenters.loading import resolve_source
from views.playlist_load_view import IPlaylistLoadView

# ---------------------------------------------------------------------------
# Fake view — records calls, no I/O
# ---------------------------------------------------------------------------


class FakePlaylistLoadView(IPlaylistLoadView):
    def __init__(self) -> None:
        self.begin_called_with: int | None = None
        self.track_loaded_count: int = 0
        self.end_called: bool = False

    def begin_loading(self, total: int) -> None:
        self.begin_called_with = total

    def on_track_loaded(self) -> None:
        self.track_loaded_count += 1

    def end_loading(self) -> None:
        self.end_called = True


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_factory(*, total_tracks: int = 3) -> MagicMock:
    """Return a mock factory whose resolve() invokes the loading callbacks."""
    factory = MagicMock()
    result = MagicMock()

    def fake_resolve(
        source: str,
        path_mapper: object = None,
        on_loading_started: object = None,
        on_track_loaded: object = None,
    ) -> object:
        if callable(on_loading_started):
            on_loading_started(total_tracks)
        for _ in range(total_tracks):
            if callable(on_track_loaded):
                on_track_loaded()
        return result

    factory.resolve.side_effect = fake_resolve
    return factory


def _make_raising_factory(exc: Exception) -> MagicMock:
    factory = MagicMock()
    factory.resolve.side_effect = exc
    return factory


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestResolveSourcePresenter:
    def test_begin_loading_called_with_track_count(self) -> None:
        view = FakePlaylistLoadView()
        factory = _make_factory(total_tracks=5)

        resolve_source(factory, view, "some/path")

        assert view.begin_called_with == 5

    def test_on_track_loaded_called_once_per_track(self) -> None:
        view = FakePlaylistLoadView()
        factory = _make_factory(total_tracks=4)

        resolve_source(factory, view, "some/path")

        assert view.track_loaded_count == 4

    def test_end_loading_called_on_success(self) -> None:
        view = FakePlaylistLoadView()
        factory = _make_factory()

        resolve_source(factory, view, "some/path")

        assert view.end_called is True

    def test_returns_playlist_from_factory(self) -> None:
        view = FakePlaylistLoadView()
        factory = _make_factory()
        expected = factory.resolve.side_effect("x")  # peek at the return value

        result = resolve_source(factory, view, "some/path")

        assert result is expected

    def test_invalid_path_mapping_propagates(self) -> None:
        view = FakePlaylistLoadView()
        factory = _make_raising_factory(InvalidPathMappingError("bad mapping"))

        with pytest.raises(InvalidPathMappingError):
            resolve_source(factory, view, "spotify:playlist:abc")

    def test_end_loading_not_called_on_invalid_path_mapping(self) -> None:
        view = FakePlaylistLoadView()
        factory = _make_raising_factory(InvalidPathMappingError("bad mapping"))

        with pytest.raises(InvalidPathMappingError):
            resolve_source(factory, view, "spotify:playlist:abc")

        assert view.end_called is False

    def test_unrecognised_source_propagates(self) -> None:
        view = FakePlaylistLoadView()
        factory = _make_raising_factory(UnrecognisedSourceError("unknown"))

        with pytest.raises(UnrecognisedSourceError):
            resolve_source(factory, view, "??")

    def test_end_loading_not_called_on_unrecognised_source(self) -> None:
        view = FakePlaylistLoadView()
        factory = _make_raising_factory(UnrecognisedSourceError("unknown"))

        with pytest.raises(UnrecognisedSourceError):
            resolve_source(factory, view, "??")

        assert view.end_called is False

    def test_path_mapper_forwarded_to_factory(self) -> None:
        view = FakePlaylistLoadView()
        factory = _make_factory()
        path_mapper = MagicMock()

        resolve_source(factory, view, "some/path", path_mapper)

        factory.resolve.assert_called_once()
        _, kwargs = factory.resolve.call_args
        assert kwargs["path_mapper"] is path_mapper
