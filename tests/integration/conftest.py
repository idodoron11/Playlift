"""Shared fixtures for Deezer integration tests.

All fixtures in this module skip gracefully when no valid ARL is configured,
so the integration suite is safe to include in the repo without requiring live
credentials in CI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from api.deezer import DeezerAuthenticationError, get_deezer_client
from config import CONFIG

if TYPE_CHECKING:
    from collections.abc import Generator

    from deezer import Deezer  # type: ignore[import-untyped]


@pytest.fixture(scope="session")
def deezer_client() -> Generator[Deezer, None, None]:  # type: ignore[no-any-unimported]
    """Authenticated Deezer client — skips the test if no valid ARL is configured.

    Session-scoped so authentication happens only once per test run.
    Cache is cleared after the session to avoid leaking state.
    """
    try:
        arl = CONFIG.deezer_arl
    except Exception:
        pytest.skip("Deezer ARL not present in config.ini")

    if not arl or not arl.strip():
        pytest.skip("Deezer ARL is empty — configure [DEEZER] ARL in config.ini")

    get_deezer_client.cache_clear()
    try:
        client = get_deezer_client()
    except DeezerAuthenticationError:
        pytest.skip("Deezer ARL is invalid or expired — update [DEEZER] ARL in config.ini")

    yield client

    get_deezer_client.cache_clear()
