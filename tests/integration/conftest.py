"""Shared fixtures for integration tests.

All fixtures skip gracefully when credentials are not configured,
so the integration suite is safe to include in the repo without requiring live
credentials in CI.
"""

from __future__ import annotations

import configparser
from typing import TYPE_CHECKING

import pytest
import spotipy

from api.deezer import DeezerAuthenticationError, get_deezer_client
from api.spotify import get_spotify_client
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


@pytest.fixture(scope="session")
def spotify_client() -> Generator[spotipy.Spotify, None, None]:  # type: ignore[no-any-unimported]
    """Authenticated Spotify client — skips the test if credentials are not configured.

    Session-scoped so authentication happens only once per test run.
    Cache is cleared after the session to avoid leaking state.
    """
    try:
        client_id = CONFIG.spotify_client_id
        client_secret = CONFIG.spotify_client_secret
    except configparser.Error:
        pytest.skip("Spotify credentials not present in config.ini")

    if not client_id.strip() or not client_secret.strip():
        pytest.skip("Spotify CLIENT_ID or CLIENT_SECRET is empty — configure [SPOTIFY] in config.ini")

    get_spotify_client.cache_clear()
    try:
        client = get_spotify_client()
        client.track("6kyxQuFD38mo4S3urD2Wkw")  # probe: verify token is valid
    except spotipy.SpotifyException:
        pytest.skip("Spotify authentication failed — check OAuth token or credentials in config.ini")

    yield client

    get_spotify_client.cache_clear()
