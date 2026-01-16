from pathlib import Path
from typing import Union

from exceptions import InvalidPathMappingException


class PathMapper:
    """Maps file paths from one prefix to another using pathlib for cross-platform compatibility.

    Example:
        mapper = PathMapper("/mnt/c/music", "/mnt/d/music")
        mapped = mapper.map("/mnt/c/music/song.mp3")  # Returns "/mnt/d/music/song.mp3"
        unmapped = mapper.map("/other/path/song.mp3")  # Returns "/other/path/song.mp3" (pass-through)
    """

    def __init__(self, from_path: Union[str, Path], to_path: Union[str, Path]):
        """Initialize PathMapper with source and destination path prefixes.

        Args:
            from_path: Source path prefix to match and replace (string or Path)
            to_path: Destination path prefix to replace with (string or Path)

        Raises:
            InvalidPathMappingException: If from_path is empty or invalid
        """
        from_path_str = str(from_path).strip() if from_path else ""
        to_path_str = str(to_path).strip() if to_path else ""

        # Validate from_path
        if not from_path_str:
            raise InvalidPathMappingException("from_path cannot be empty")

        try:
            self._from_path = Path(from_path_str)
            self._to_path = Path(to_path_str)
        except (TypeError, ValueError) as e:
            raise InvalidPathMappingException(f"Invalid path format: {e}")

    def map(self, path: str) -> str:
        """Map a file path using the configured prefix replacement.

        If the path starts with from_path prefix, it will be remapped to use to_path.
        Otherwise, the path is returned unchanged.

        Args:
            path: The file path to map (string)

        Returns:
            Mapped path as string, or original path if no match
        """
        try:
            file_path = Path(path)
            # Try to make the file path relative to from_path
            relative_path = file_path.relative_to(self._from_path)
            # If successful, join with to_path
            mapped_path = self._to_path / relative_path
            return str(mapped_path)
        except ValueError:
            # Path doesn't match from_path prefix, return original
            return path

