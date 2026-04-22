class PlaylistSyncError(Exception):
    pass


class SkipTrackError(PlaylistSyncError):
    pass


class InvalidPathMappingError(PlaylistSyncError):
    pass
