---
name: mypy-check
description: 'Run mypy type checking on a specific file or folder using the project mypy config. Use when: finding type errors, checking type annotations, reviewing mypy output, diagnosing type issues, running strict type checking on a module or path.'
argument-hint: File or folder path to type-check (e.g., tracks/local_track.py, matchers/)
---

# Mypy Check

Runs `mypy` on a specific file or folder, using the project's mypy configuration from `pyproject.toml` (`strict = true`, `ignore_missing_imports = true`, `python_version = "3.11"`).

## When to Use

- User asks to "run mypy on", "check types in", or "find type errors in" a file or folder
- After editing a file, to validate no new type errors were introduced
- When performing a code review and wanting to verify type safety
- When diagnosing mypy failures in CI or test runs

## Procedure

### Step 1 — Resolve the Target Path

If the user supplied a path as an argument, use it directly.

Otherwise, ask:
> "Which file or folder should I run mypy on? (e.g. `tracks/local_track.py`, `matchers/`, or `.` for the whole project)"

Accept relative paths from the workspace root. If the user says "this file" or "the current file", use the file currently open in the editor.

### Step 2 — Run Mypy

Run from the workspace root so that `pyproject.toml` config is picked up automatically:

```
uv run mypy <path>
```

**Examples:**
- Single file: `uv run mypy tracks/local_track.py`
- Folder: `uv run mypy matchers/`
- Whole project: `uv run mypy .`

Capture the full terminal output. Mypy exits with code 0 when there are no errors, and non-zero otherwise — both are valid outcomes to report.

### Step 3 — Parse and Present Results

#### If no errors:

Report success concisely:
> "No mypy errors found in `<path>`."

#### If errors are found:

1. **Count total errors** from the summary line (e.g., `Found 5 errors in 2 files`).
2. **Group errors by file**, then by error code within each file.
3. Present a structured report:

```
## Mypy Results — <path>

**X error(s) in Y file(s)**

### <filename>
- Line <N> [<error-code>]: <message>
- Line <N> [<error-code>]: <message>

### <filename>
- ...
```

4. After listing all errors, add a **Summary** section that:
   - Identifies the most common error codes (e.g., `[arg-type]`, `[no-untyped-def]`, `[return-value]`)
   - Notes any patterns (e.g., "5 of 8 errors are missing return type annotations")

### Step 4 — Offer to Fix

After presenting the results, ask if the user wants you to fix the errors:
> "Would you like me to fix these type errors?"

If yes, address errors file by file, starting with the file that has the most errors. After each file, re-run mypy on that file to confirm the fix before moving on.
