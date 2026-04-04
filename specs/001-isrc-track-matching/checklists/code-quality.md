# Code Quality Checklist: ISRC-Based Track Matching and Embedding

**Purpose**: Validate type hint completeness, naming conventions, structural quality, and tooling compliance for all code changes introduced by this feature
**Created**: 2026-04-04
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md)

## Type Hint Completeness (Constitution §VI)

- [x] CHK001 Does `LocalTrack.isrc` (getter) carry a return type annotation of `str | None`? [Clarity, Constitution §VI]
- [x] CHK002 Does `LocalTrack.isrc` (setter) carry a parameter type annotation of `str` and return type `None`? [Clarity, Constitution §VI]
- [x] CHK003 Does `SpotifyTrack.isrc` carry a return type annotation of `str | None`? [Clarity, Constitution §VI]
- [x] CHK004 Does `SpotifyMatcher._is_valid_isrc()` carry a parameter type annotation of `str | None` and return type `bool`? [Clarity, Constitution §VI]
- [x] CHK005 Are built-in generic types used throughout (`str | None` rather than `typing.Optional[str]`)? [Clarity, Constitution §VI, Copilot Instructions]
- [x] CHK006 Does the updated `_update_spotify_match_in_source_track()` signature remain fully annotated after the ISRC write extension? [Consistency, Constitution §VI]

## mypy Strict Mode (Constitution §VI)

- [x] CHK007 Does `uv run mypy .` pass with zero errors after all feature changes? [Acceptance Criteria, Constitution §VI]
- [x] CHK008 Are there zero `# type: ignore` suppressions in new or modified lines? [Constitution §VI]
- [ ] CHK009 Is `ISRC_PATTERN` typed as `re.Pattern[str]` (not inferred implicitly)? [Clarity, Constitution §VI]
- [x] CHK010 Does the `LocalTrack.isrc` getter return type satisfy the rest of `LocalTrack`'s interface without triggering `union-attr` or `return-value` mypy errors? [Consistency, Constitution §VI]

## Naming Conventions (Constitution §I)

- [x] CHK011 Is the ISRC pattern constant named `ISRC_PATTERN` in `UPPER_SNAKE_CASE` at module scope rather than inline? [Clarity, Constitution §I]
- [x] CHK012 Is the validation helper named with a descriptive verb prefix (`_is_valid_isrc`, not `_check_isrc` or `_validate`)? [Clarity, Constitution §I]
- [x] CHK013 Is the `isrc` property on both `LocalTrack` and `SpotifyTrack` named as a plain noun (not `get_isrc`, `isrc_value`, `isrc_tag`)? [Clarity, Constitution §I]
- [x] CHK014 Are any new boolean-returning names prefixed with `is_`, `has_`, `can_`, or `should_`? [Clarity, Constitution §I]

## Structural Quality (Constitution §I — Functions)

- [x] CHK015 Does the ISRC-first lookup block inside `SpotifyMatcher.match()` stay within ~30 lines including error handling? [Completeness, Constitution §I]
- [x] CHK016 Is nesting depth inside the ISRC lookup block ≤ 3 levels? [Clarity, Constitution §I]
- [x] CHK017 Does the `LocalTrack.isrc` getter implement the format dispatch (MP3 / FLAC / M4A) without exceeding 3 levels of nesting? [Clarity, Constitution §I]
- [ ] CHK018 Is ISRC normalization (uppercase, strip hyphens) a named, single-purpose expression or helper rather than inline string manipulation in multiple places? [DRY, Constitution §I, §III]

## SOLID Compliance (Constitution §II)

- [x] CHK019 Does `LocalTrack.isrc` stay within `LocalTrack`'s single responsibility (tag I/O only) — no validation logic, no Spotify lookup? [Consistency, Constitution §II]
- [x] CHK020 Does `SpotifyTrack.isrc` derive solely from `self.data` — no outside calls, no API requests? [Consistency, Constitution §II]
- [x] CHK021 Does the ISRC validation logic live exclusively in `SpotifyMatcher` and not leak into `LocalTrack` or `SpotifyTrack`? [Consistency, Constitution §II, §III]

## DRY (Constitution §III)

- [x] CHK022 Is `ISRC_PATTERN` defined exactly once in `matchers/spotify_matcher.py` and referenced everywhere else by name? [Completeness, Constitution §III]
- [x] CHK023 Is ISRC normalization (strip hyphens + uppercase) performed in one place, not duplicated between the getter and the matcher? [Completeness, Constitution §III]

## Docstrings (Constitution §VI)

- [x] CHK024 Does `LocalTrack.isrc` have a Google-style docstring explaining what the property returns and the normalization applied? [Completeness, Constitution §VI]
- [x] CHK025 Does `SpotifyTrack.isrc` have a Google-style docstring stating the source path (`external_ids.isrc`) and `None` behavior? [Completeness, Constitution §VI]
- [x] CHK026 Does `SpotifyMatcher._is_valid_isrc()` have a Google-style docstring specifying the accepted format pattern and return contract? [Completeness, Constitution §VI]

## Linting and Formatting (Constitution §Quality Standards)

- [x] CHK027 Does `uv run ruff format .` produce no changes (code already formatted)? [Acceptance Criteria, Constitution §Quality Standards]
- [x] CHK028 Does `uv run ruff check .` produce zero violations across all modified files? [Acceptance Criteria, Constitution §Quality Standards]

## Error Handling (Constitution §I, §VI)

- [ ] CHK029 Is the ISRC lookup error handler (FR-004 API/network failure) catching a specific exception type rather than bare `except:`? [Clarity, Constitution §I, Spec §FR-004]
- [x] CHK030 Are no new bare `raise Exception(...)` calls introduced — only logging is used for non-fatal ISRC failures? [Clarity, Constitution §VI, Spec §FR-004, FR-007]

## Notes

- All items test requirement quality for code to be written, not runtime behavior.
- Priority: CHK007 (mypy gate), CHK008 (no type: ignore), CHK027–CHK028 (ruff gates) are hard blockers per Constitution §Quality Standards.
