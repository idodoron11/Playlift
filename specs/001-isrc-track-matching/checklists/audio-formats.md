# Audio Format Checklist: ISRC Tag Requirements

**Purpose**: Validate requirement quality for ISRC tag handling across mp3, m4a (ALAC), and FLAC
**Created**: 2026-04-04
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [x] CHK001 Are format-specific ISRC read requirements explicitly documented for mp3, m4a (ALAC), and FLAC rather than only as a generic "supported formats" statement? [Completeness, Spec §FR-001, Gap]
- [x] CHK002 Does the spec define whether mp3 ISRC must be treated as a standard frame requirement (TSRC) versus a custom tag fallback? [Completeness, Research §Task 1, Gap]
- [x] CHK003 Does the spec define whether FLAC ISRC must be read from standard Vorbis comments and how absence is handled? [Completeness, Research §Task 1, Gap]
- [x] CHK004 Does the spec define whether m4a (ALAC) ISRC uses iTunes freeform mapping and what behavior is required if the field is missing? [Completeness, Research §Task 1, Gap]
- [x] CHK005 Are write-path requirements complete for all three formats (including format-specific persistence behavior and reload expectations)? [Completeness, Spec §FR-005, Spec §FR-007, Gap]

## Requirement Clarity

- [x] CHK006 Is "m4a" clarified as including ALAC containers explicitly, with no ambiguity about AAC-only assumptions? [Clarity, Ambiguity]
- [x] CHK007 Is the canonical normalized ISRC representation (uppercase, no hyphens) specified clearly enough to avoid format-specific normalization drift? [Clarity, Spec §FR-002, Research §Task 4]
- [x] CHK008 Is the distinction between "missing tag", "malformed tag", and "valid but unmatched ISRC" explicitly defined for each format? [Clarity, Spec §FR-002, Spec §FR-004]

## Requirement Consistency

- [x] CHK009 Do format-specific assumptions in research align with FR-001 and FR-002 without introducing contradictory behavior per format? [Consistency, Spec §FR-001, Spec §FR-002, Research §Task 1]
- [x] CHK010 Are no-overwrite expectations (FR-006) consistent across mp3, m4a, and FLAC, including mixed-library runs? [Consistency, Spec §FR-006]
- [x] CHK011 Are non-fatal write-failure requirements (FR-007) consistent for all supported formats, not only one tag backend? [Consistency, Spec §FR-007]

## Acceptance Criteria Quality

- [x] CHK012 Are there measurable acceptance criteria proving each format can be read for ISRC without fallback to fuzzy when valid data is present? [Acceptance Criteria, Spec §SC-001, Gap]
- [x] CHK013 Are there measurable acceptance criteria proving each format writes ISRC when embedding conditions are met (and does not overwrite existing values)? [Acceptance Criteria, Spec §FR-005, Spec §FR-006, Gap]
- [x] CHK014 Are acceptance criteria explicit about expected behavior when format-specific tag backends fail (warning + continue)? [Acceptance Criteria, Spec §FR-007]

## Scenario and Edge Case Coverage

- [x] CHK015 Are alternate scenarios covered where one playlist contains a mix of mp3, m4a (ALAC), and FLAC tracks with different ISRC tag states? [Coverage, Gap]
- [x] CHK016 Are exception scenarios covered for malformed ISRC in one format while valid ISRC exists in another within the same run? [Coverage, Spec §FR-002, Spec §FR-004]
- [x] CHK017 Are recovery expectations defined when format-specific writes fail transiently (for example, permission or tag serialization errors) and subsequent tracks continue? [Recovery, Spec §FR-007]

## Dependencies and Assumptions

- [x] CHK018 Are format-mapping assumptions from research promoted to explicit, testable requirements where required, rather than left as implementation notes? [Assumption, Research §Task 1, Gap]
- [x] CHK019 Is the dependency on tag-library behavior bounded by requirement language (what must happen) instead of implicit reliance on library internals? [Dependency, Gap]
- [x] CHK020 Is it explicit which behaviors are guaranteed by product requirements versus merely observed in current library behavior? [Ambiguity, Conflict, Gap]

## Notes

- This checklist is a requirements-quality test suite, not an implementation test plan.
- Main objective: ensure per-format ISRC behavior is complete, unambiguous, and consistently specified for mp3, m4a (ALAC), and FLAC.
