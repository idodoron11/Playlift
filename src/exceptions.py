class PlaylistSyncError(Exception):
    pass


class SkipTrackError(PlaylistSyncError):
    pass


class InvalidPathMappingError(PlaylistSyncError):
    pass


class UnrecognisedSourceError(PlaylistSyncError):
    """Raised when a source string does not match any known format.

    This is raised by ``PlaylistFactory.resolve()`` when *source* is not a
    Spotify URI/URL, Deezer playlist URL, or a valid local file/directory path.
    """
