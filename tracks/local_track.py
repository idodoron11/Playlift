from typing import List

import music_tag

from tracks import Track


class LocalTrack(Track):
    def __init__(self, file_path: str):
        self._file_path = file_path
        self._audio = music_tag.load_file(file_path)

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def artists(self) -> List[str]:
        tag = self._get_tag("artist")
        return tag.values if tag else None

    @property
    def display_artist(self) -> str:
        tag = self._get_tag("artist")
        return tag.value if tag else None

    @property
    def title(self) -> str:
        tag = self._get_tag("title")
        return tag.first if tag else None

    @property
    def album(self) -> str:
        tag = self._get_tag("album")
        return tag.first if tag else None

    @property
    def duration(self) -> float:
        tag = self._get_tag("#length")
        return tag.first if tag else None

    @property
    def track_number(self) -> int:
        tag = self._get_tag("tracknumber")
        return tag.value if tag else None

    def _get_tag(self, tag_name, assert_not_empty=False):
        result = None
        try:
            result = self._audio[tag_name]
        except:
            pass
        if assert_not_empty and not result:
            raise AttributeError(f"No {tag_name} found")
        return result

    @property
    def track_id(self) -> str:
        return self.file_path
