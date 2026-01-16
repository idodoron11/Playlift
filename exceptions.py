class PlaylistSyncException(Exception):
    pass


class SkipTrackException(PlaylistSyncException):
    pass


class InvalidPathMappingException(PlaylistSyncException):
    pass
