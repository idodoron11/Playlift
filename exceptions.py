class PlaylistSyncException(Exception):
    pass


class SkipTrackException(PlaylistSyncException):
    pass
