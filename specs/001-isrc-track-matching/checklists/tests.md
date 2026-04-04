# Test Requirements Checklist: ISRC-Based Track Matching and Embedding

**Purpose**: Validate that test requirements in tasks.md are complete, clear, isolated, and properly structured before implementation begins
**Created**: 2026-04-04
**Feature**: [spec.md](../spec.md) | [tasks.md](../tasks.md)

## Test Completeness

- [ ] CHK001 Are unit tests specified for `_is_valid_isrc()` in isolation, covering valid ISRC, malformed (wrong length, wrong chars), empty string, `None`, mixed-case input, and hyphenated form? [Completeness, Tasks §T014, Gap]
- [ ] CHK002 Are tests for `LocalTrack.isrc` getter specified for the case where the TSRC frame exists but contains hyphens (hyphen-stripping normalization path)? [Completeness, Tasks §T012, Research §Task 4, Gap]
- [ ] CHK003 Are tests specified for the `"SKIP"` sentinel — confirming that a SKIP-tagged track does not trigger ISRC lookup and no ISRC is written? [Completeness, Spec §US3 Acceptance 4, Constitution §V, Gap]
- [ ] CHK004 Are tests specified for tracks with non-Latin artist names where ISRC is also present — ensuring ISRC path runs first and non-Latin handling is irrelevant? [Completeness, Spec §FR-001, Constitution §V, Gap]
- [ ] CHK005 Are regression tests explicitly specified for all pre-existing `test_spotify_matcher.py` scenarios to confirm no behavior change after ISRC changes are introduced? [Completeness, Tasks §T020, Spec §SC-005]
- [ ] CHK006 Is a test specified confirming that the match method logs the resolution method (ISRC or fuzzy) per FR-008? [Completeness, Spec §FR-008, Gap]

## Test Clarity

- [ ] CHK007 Does T008 use a concrete, valid ISRC value (for example `"USRC17607839"`) rather than the placeholder `"isrc:XXXXXXXXXXXX"`? [Clarity, Tasks §T008, Ambiguity]
- [ ] CHK008 Do all test task names follow the constitution convention `test_<unit>_<scenario>_<expected_outcome>`? Review T017–T026 against this pattern. [Clarity, Constitution §V]
- [ ] CHK009 Are "assert fuzzy search is never called" and "assert fuzzy search is then invoked" defined with a specific spy/mock mechanism, not left as intent only? [Clarity, Tasks §T008, T017]
- [ ] CHK010 Is the exact assertion for "no ISRC write attempt" (T024) specified beyond "no write attempt" — for example, `isrc setter is not called` or `_set_custom_tag is not called`? [Clarity, Tasks §T024]

## Test Isolation Requirements

- [ ] CHK011 Are `LocalTrack.isrc` getter tests (T012) specified to use a fake/stub file rather than real filesystem access? [Isolation, Constitution §V, Tasks §T012]
- [ ] CHK012 Are `LocalTrack.isrc` setter tests (T026) specified to mock `mutagen.save()` / `music_tag` writes, confirming no actual file I/O? [Isolation, Constitution §V, Tasks §T026]
- [ ] CHK013 Are all Spotify API calls (`_search`) specified to be patched/mocked, confirming no real network access in any test? [Isolation, Constitution §V]
- [ ] CHK014 Is the `SpotifyMatcher` singleton access in tests accounted for — are tests specified to use a fresh instance or reset the singleton between test cases? [Isolation, Constitution §V, Copilot Instructions §Singletons]

## AAA Structure

- [ ] CHK015 Do all test task descriptions include or imply a clear Arrange clause (initial state), Act clause (operation), and Assert clause (expected outcome)? [Acceptance Criteria, Constitution §V]
- [ ] CHK016 For T017 and T018 (fallback tests), is the Arrange clearly distinguishable from the Assert — i.e., the stub setup does not conflate the test condition with the assertion? [Clarity, Tasks §T017, T018]

## Scenario Coverage

- [ ] CHK017 Is a test scenario specified for a playlist run containing a mix of ISRC-tagged, non-ISRC, and SKIP tracks in the same `match_list()` call, confirming each track follows its correct path? [Coverage, Spec §US1, US2, Edge Cases, Gap]
- [ ] CHK018 Is a test specified for the case where `SpotifyTrack.isrc` returns `None` even though `external_ids` key is present but has no `isrc` sub-key? [Coverage, Tasks §T013, Research §Task 3]
- [ ] CHK019 Is a test specified for the case where embedding is attempted on a `LocalTrack` that is not an instance recognized by `_update_spotify_match_in_source_track` (i.e., a non-`LocalTrack` `Track`)? [Coverage, Tasks §T027, Gap]

## Non-Functional Requirements

- [ ] CHK020 Are type-safety requirements for test files included — do test files carry complete type hints and pass `mypy` in strict mode alongside production code? [Non-Functional, Constitution §VI]
- [ ] CHK021 Are test helper fakes (`TrackMock` with `isrc`, `FakeLocalTrack`) specified to include an `isrc` field that participates in `__eq__` and `__hash__` correctly, or is it deliberately excluded? [Non-Functional, Tasks §T004]

## Notes

- These items validate whether the test REQUIREMENTS in tasks.md are complete, clear, and properly structured — not whether tests pass.
- Key gaps to address before implementation: CHK001 (validator unit tests), CHK003 (SKIP sentinel), CHK007 (concrete ISRC value), CHK011–CHK013 (isolation specs).
