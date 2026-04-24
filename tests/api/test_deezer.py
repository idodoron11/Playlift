"""Unit tests for get_deezer_client() singleton and DeezerAuthenticationError."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from api.deezer import DeezerAuthenticationError, get_deezer_client


@pytest.fixture(autouse=True)
def _clear_functools_cache() -> None:
    """Reset the @functools.cache on get_deezer_client before every test."""
    get_deezer_client.cache_clear()


def _make_deezer_mock(login_return: bool) -> MagicMock:
    mock_dz = MagicMock()
    mock_dz.login_via_arl.return_value = login_return
    return mock_dz


class TestGetDeezerClient:
    def test_returns_same_instance_on_repeated_calls(self) -> None:
        """get_deezer_client() is a singleton — repeated calls return the same object."""
        mock_dz = _make_deezer_mock(True)

        with (
            patch("api.deezer.Deezer", return_value=mock_dz),
            patch("api.deezer.CONFIG") as mock_config,
        ):
            mock_config.deezer_arl = "valid-arl"

            first = get_deezer_client()
            second = get_deezer_client()

        assert first is second
        # login_via_arl should only be called once despite two get_deezer_client() calls
        mock_dz.login_via_arl.assert_called_once()

    def test_raises_deezer_authentication_error_when_login_returns_false(self) -> None:
        """When login_via_arl() returns False, DeezerAuthenticationError is raised."""
        mock_dz = _make_deezer_mock(False)

        with (
            patch("api.deezer.Deezer", return_value=mock_dz),
            patch("api.deezer.CONFIG") as mock_config,
        ):
            mock_config.deezer_arl = "bad-arl"

            with pytest.raises(DeezerAuthenticationError):
                get_deezer_client()

    def test_error_message_does_not_contain_arl(self) -> None:
        """The DeezerAuthenticationError message must never echo the ARL value (FR-018)."""
        arl_value = "super-secret-arl-12345"
        mock_dz = _make_deezer_mock(False)

        with (
            patch("api.deezer.Deezer", return_value=mock_dz),
            patch("api.deezer.CONFIG") as mock_config,
        ):
            mock_config.deezer_arl = arl_value

            with pytest.raises(DeezerAuthenticationError) as exc_info:
                get_deezer_client()

        assert arl_value not in str(exc_info.value)
