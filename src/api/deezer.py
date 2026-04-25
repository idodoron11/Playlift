"""Deezer API singleton using ARL cookie authentication."""

from __future__ import annotations

import functools

from deezer import Deezer  # type: ignore[import-untyped]

from config import CONFIG


class DeezerAuthenticationError(Exception):
    """Raised when Deezer login via ARL fails.

    The ARL value is intentionally excluded from the message to prevent
    credentials leaking into logs (FR-018).
    """


@functools.cache
def get_deezer_client() -> Deezer:  # type: ignore[no-any-unimported]
    """Return the singleton authenticated Deezer client.

    Creates and caches a single Deezer instance on first call using the ARL
    from CONFIG. Subsequent calls return the cached instance.

    Returns:
        An authenticated deezer-py Deezer facade instance.

    Raises:
        DeezerAuthenticationError: When ``login_via_arl`` returns False.
    """
    arl = CONFIG.deezer_arl
    dz: Deezer = Deezer()  # type: ignore[no-any-unimported]
    if not dz.login_via_arl(arl):
        raise DeezerAuthenticationError("Deezer authentication failed — check your ARL in config.ini")
    return dz
