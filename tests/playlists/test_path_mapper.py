"""Unit tests for PathMapper class."""
import sys
from pathlib import Path

import pytest

from exceptions import InvalidPathMappingException
from playlists.path_mapper import PathMapper


class TestPathMapperInitialization:
    """Test PathMapper initialization and validation."""

    def test_init_with_string_paths(self) -> None:
        """Test initialization with string paths."""
        mapper = PathMapper("/mnt/c/music", "/mnt/d/music")
        assert mapper is not None

    def test_init_with_path_objects(self) -> None:
        """Test initialization with pathlib.Path objects."""
        mapper = PathMapper(Path("/mnt/c/music"), Path("/mnt/d/music"))
        assert mapper is not None

    def test_init_with_mixed_types(self) -> None:
        """Test initialization with mixed string and Path objects."""
        mapper = PathMapper("/mnt/c/music", Path("/mnt/d/music"))
        assert mapper is not None

    def test_init_with_empty_from_path(self) -> None:
        """Test that empty from_path raises InvalidPathMappingException."""
        with pytest.raises(InvalidPathMappingException, match="from_path cannot be empty"):
            PathMapper("", "/mnt/d/music")

    def test_init_with_none_from_path(self) -> None:
        """Test that None from_path raises InvalidPathMappingException."""
        with pytest.raises(InvalidPathMappingException, match="from_path cannot be empty"):
            PathMapper(None, "/mnt/d/music")

    def test_init_with_whitespace_only_from_path(self) -> None:
        """Test that whitespace-only from_path raises InvalidPathMappingException."""
        with pytest.raises(InvalidPathMappingException, match="from_path cannot be empty"):
            PathMapper("   ", "/mnt/d/music")

    def test_init_with_empty_to_path(self) -> None:
        """Test initialization with empty to_path (should be allowed)."""
        mapper = PathMapper("/mnt/c/music", "")
        assert mapper is not None

    def test_init_with_relative_paths(self) -> None:
        """Test initialization with relative paths."""
        mapper = PathMapper("music/library", "music/backup")
        assert mapper is not None

    def test_init_with_windows_paths(self) -> None:
        """Test initialization with Windows-style paths."""
        mapper = PathMapper("C:\\music", "D:\\music")
        assert mapper is not None

    def test_init_with_trailing_slashes(self) -> None:
        """Test initialization with trailing slashes (pathlib normalizes these)."""
        mapper = PathMapper("/mnt/c/music/", "/mnt/d/music/")
        assert mapper is not None


class TestPathMapperMapping:
    """Test PathMapper.map() functionality."""

    def test_map_exact_prefix_match(self) -> None:
        """Test mapping when path exactly matches from_path prefix."""
        mapper = PathMapper("/mnt/c/music", "/mnt/d/music")
        result = mapper.map("/mnt/c/music/song.mp3")
        assert result == str(Path("/mnt/d/music/song.mp3"))

    def test_map_prefix_with_subdirectories(self) -> None:
        """Test mapping with nested subdirectories."""
        mapper = PathMapper("/mnt/c/music", "/mnt/d/music")
        result = mapper.map("/mnt/c/music/artist/album/song.mp3")
        assert result == str(Path("/mnt/d/music/artist/album/song.mp3"))

    def test_map_no_match_returns_original(self) -> None:
        """Test that unmatched paths are returned unchanged."""
        mapper = PathMapper("/mnt/c/music", "/mnt/d/music")
        original = "/other/path/song.mp3"
        result = mapper.map(original)
        assert result == original

    def test_map_partial_prefix_no_match(self) -> None:
        """Test that partial prefix matches don't trigger mapping."""
        mapper = PathMapper("/mnt/c/music", "/mnt/d/music")
        # /mnt/c/music_backup doesn't match /mnt/c/music
        original = "/mnt/c/music_backup/song.mp3"
        result = mapper.map(original)
        assert result == original

    def test_map_relative_paths(self) -> None:
        """Test mapping with relative paths."""
        mapper = PathMapper("music/library", "music/backup")
        result = mapper.map("music/library/song.mp3")
        assert result == str(Path("music/backup/song.mp3"))

    def test_map_relative_to_relative_no_match(self) -> None:
        """Test that relative path that doesn't match returns original."""
        mapper = PathMapper("music/library", "music/backup")
        original = "other/music/song.mp3"
        result = mapper.map(original)
        assert result == original

    def test_map_windows_paths(self) -> None:
        """Test mapping with Windows-style paths."""
        mapper = PathMapper("C:\\music", "D:\\music")
        result = mapper.map("C:\\music\\song.mp3")
        # Result should use platform-specific separators
        assert "song.mp3" in result
        assert "D:" in result or "D:\\" in result

    def test_map_mixed_separators_normalized(self) -> None:
        """Test that mixed separators are normalized by pathlib."""
        # pathlib normalizes separators for the current platform
        mapper = PathMapper("/mnt/c/music", "/mnt/d/music")
        result = mapper.map("/mnt/c/music/artist/album/song.mp3")
        # Should have normalized separators
        assert "song.mp3" in result
        assert "/mnt/d/music" in result or "\\mnt\\d\\music" in result

    def test_map_preserves_subdirectory_structure(self) -> None:
        """Test that subdirectory structure is preserved."""
        mapper = PathMapper("/music", "/backup/music")
        result = mapper.map("/music/rock/metal/album/track.mp3")
        assert result == str(Path("/backup/music/rock/metal/album/track.mp3"))

    def test_map_with_special_characters_in_filename(self) -> None:
        """Test mapping with special characters in filename."""
        mapper = PathMapper("/music", "/backup")
        result = mapper.map("/music/artist - album (remastered)/song [remix].mp3")
        assert result == str(Path("/backup/artist - album (remastered)/song [remix].mp3"))

    def test_map_with_unicode_characters(self) -> None:
        """Test mapping with unicode characters in path."""
        mapper = PathMapper("/music", "/backup")
        result = mapper.map("/music/艺术家/专辑/歌曲.mp3")
        assert result == str(Path("/backup/艺术家/专辑/歌曲.mp3"))

    def test_map_empty_to_path(self) -> None:
        """Test mapping with empty to_path."""
        mapper = PathMapper("/mnt/c/music", "")
        result = mapper.map("/mnt/c/music/song.mp3")
        # Should map to empty path + song.mp3
        assert result == str(Path("song.mp3"))

    def test_map_single_file_name(self) -> None:
        """Test mapping a single file name without directory."""
        mapper = PathMapper("/mnt/c/music", "/mnt/d/music")
        original = "song.mp3"
        result = mapper.map(original)
        # Single file without matching prefix should pass through
        assert result == original

    def test_map_with_trailing_slash_in_path(self) -> None:
        """Test mapping path with trailing slash."""
        mapper = PathMapper("/mnt/c/music", "/mnt/d/music")
        # pathlib should handle trailing slashes
        result = mapper.map("/mnt/c/music/")
        assert "/mnt/d/music" in result or "\\mnt\\d\\music" in result

    def test_map_deep_nesting(self) -> None:
        """Test mapping with deeply nested paths."""
        mapper = PathMapper("/a", "/b")
        path = "/a/c/d/e/f/g/h/i/j/k/l/m/n/o/p.mp3"
        result = mapper.map(path)
        assert result == str(Path("/b/c/d/e/f/g/h/i/j/k/l/m/n/o/p.mp3"))


class TestPathMapperEdgeCases:
    """Test edge cases and corner cases."""

    def test_map_dot_notation_relative_paths(self) -> None:
        """Test mapping with dot notation in relative paths."""
        mapper = PathMapper("./music", "./backup")
        result = mapper.map("./music/song.mp3")
        assert "backup" in result
        assert "song.mp3" in result

    def test_map_same_from_and_to_path(self) -> None:
        """Test mapping when from_path and to_path are the same."""
        mapper = PathMapper("/music", "/music")
        result = mapper.map("/music/song.mp3")
        assert result == str(Path("/music/song.mp3"))

    def test_map_overlapping_paths(self) -> None:
        """Test mapping when to_path is nested within from_path."""
        mapper = PathMapper("/music", "/music/backup")
        result = mapper.map("/music/song.mp3")
        assert result == str(Path("/music/backup/song.mp3"))

    def test_multiple_mappers_independent(self) -> None:
        """Test that multiple mapper instances are independent."""
        mapper1 = PathMapper("/a", "/b")
        mapper2 = PathMapper("/x", "/y")

        result1 = mapper1.map("/a/file.mp3")
        result2 = mapper2.map("/x/file.mp3")

        assert "/b/" in result1 or "\\b\\" in result1
        assert "/y/" in result2 or "\\y\\" in result2
        assert result1 != result2

    @pytest.mark.skipif(sys.platform == "win32", reason="Windows filesystems are case-insensitive")
    def test_map_case_sensitive_unix(self) -> None:
        """Test that mapping respects case sensitivity on Unix paths."""
        mapper = PathMapper("/Music", "/backup")
        # /music (lowercase) doesn't match /Music (uppercase) on Unix systems
        original = "/music/song.mp3"
        result = mapper.map(original)
        assert result == original

    def test_map_consecutive_slashes(self) -> None:
        """Test mapping with consecutive slashes (pathlib should normalize)."""
        mapper = PathMapper("/mnt/c/music", "/mnt/d/music")
        result = mapper.map("/mnt/c/music//song.mp3")
        # pathlib should normalize consecutive slashes
        assert "song.mp3" in result

