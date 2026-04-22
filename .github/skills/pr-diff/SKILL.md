---
name: pr-diff
description: 'Produce a pull request diff between the current branch and a target branch. Use when: reviewing PR changes, performing code review, summarizing PR changes (title + description), creating a new PR with title and description, understanding what a branch introduces, comparing branches, getting diff output.'
argument-hint: Target branch to compare against (e.g. main, master, develop)
---

# PR Diff

Produces a structured diff between the current branch and a target branch, giving the agent full context on what the PR introduces.

## When to Use

- **PR review**: User asks to review or audit PR changes
- **PR summarization**: User wants a PR title and description drafted from the diff
- **Create PR**: User asks to open or create a new PR with a generated title and description
- User wants to understand what files were modified before a code review
- User asks to "show the diff", "what changed", or "compare to main/master"
- Any workflow that requires full awareness of branch changes (code review, changelog, impact analysis)

## Procedure

### Step 1 — Ask for the Target Branch and Work Item

**You MUST ask the user for the target branch first.** Do not assume.

Use the ask-questions tool with **two questions in the same call**:

1. **Target branch** — pre-filled options `origin/main` and `origin/master` (mark `origin/main` as recommended), allow freeform input for other branches (e.g., `develop`, `release/1.0`).
2. **Related work item / issue** — freeform text, optional. Format depends on platform:
   - GitHub: `#123`
   - Azure DevOps: `AB#12345`
   - Leave blank if there is no related work item

Store both answers; the work item ID is used in the **Related Work** section of the PR description.

### Step 2 — Run the Diff Script

You MUST run the appropriate script to get the diff output. This is a **mandatory step** — do not skip it.

Choose the script based on the current OS:

- **Windows** → use [pr-diff.ps1](./scripts/pr-diff.ps1) via `pwsh`:
  ```
  pwsh .github/skills/pr-diff/scripts/pr-diff.ps1 -TargetBranch <target>
  ```
- **macOS / Linux** → use [pr-diff.sh](./scripts/pr-diff.sh):
  ```
  bash .github/skills/pr-diff/scripts/pr-diff.sh <target>
  ```

The script produces metadata only (no diff content); use each piece as follows:

| Output | Source | How the agent uses it |
|--------|--------|-----------------------|
| **Current branch name** | `git rev-parse --abbrev-ref HEAD` | Report which feature branch is under review |
| **Modified files list** | `git diff --name-status origin/main...HEAD` | Group by status (`A` Added / `M` Modified / `D` Deleted / `R` Renamed) and present a structured scope summary |
| **Diff line count** | `git diff ... \| wc -l` | Use as a scope signal: ≤1000 lines → read full diff at once; >1000 lines → offer per-file sections or summaries |
| **Remote origin URL** | `git remote get-url origin` | Extract the `owner` and `repo` to pass to `mcp_io_github_git_create_pull_request` |
| **All remotes** | `git remote -v` | Confirm remote names and URLs before creating a PR |

### Step 3 — Digest the Output

After digesting the output, the agent MUST:

1. Report the **current branch** and **target branch**
2. List the **modified files** grouped by status (Added / Modified / Deleted / Renamed)
3. State the **diff size** (line count) as a signal of PR scope

The agent now has full context to proceed with Step 4 and then the appropriate follow-up action in Step 5.

### Step 4 — Read the Full Diff

**This is a mandatory step — do not skip it.**

You MUST run the following command to retrieve the full diff content:

```
git diff <target-branch>...HEAD
```

The agent MUST read the diff from the terminal output.

### Step 5 — Read Full File Contents for Key Changed Files

**This is a mandatory step for all workflows.**

After reading the diff, use `read_file` to load the **complete contents** of key changed files — not just the lines that appear in the diff. This provides crucial context: imports, class structure, surrounding logic, and existing patterns that the diff alone cannot convey.

**Prioritize reading:**
- Files with substantial logic changes (not just formatting)
- Files with changed interfaces, function signatures, or class definitions

**Skip:**
- Files that are purely added (the diff already shows all content)
- Lock files (e.g., `uv.lock`, `package-lock.json`)
- Files with only formatting changes (e.g., whitespace, line breaks)
- Files with only comment changes


### Step 6 — Perform the Requested Action

Based on the user's intent, proceed with one of these actions after reading the diff:

#### PR Review
Perform a thorough code review following the project's code review instructions. Address security, correctness, test coverage, and style — grouped by severity (Critical / Important / Suggestion).

#### PR Summarization (title + description)
Draft a PR title (conventional commit format: `type(scope): summary`, 50-72 characters, imperative mood) and a full structured description. Output the entire block inside a **raw markdown code fence** for easy copy-paste:

````markdown
```markdown
# <type(scope): concise imperative summary — 50-72 chars>

## Summary
2-3 sentence overview: what this PR does and why.

## Changes
- **Component / File:** Description of the change and its rationale
- **Component / File:** …

## Technical Details
- Key implementation decisions
- Algorithm or architecture changes
- Performance considerations
- Breaking changes (if any)

## Testing
- How changes were tested
- Test coverage impact
- Manual testing performed

## Related Work
- Closes #<issue> / AB#<work-item-id>
```
````

**Work item handling:**
- If the user provided a work item ID in Step 1, include it using the platform-specific keyword:
  - **GitHub:** `Closes #123`, `Fixes #123`, or `Resolves #123` (auto-closes the issue on merge)
  - **Azure DevOps:** `AB#12345`
- If **no** work item was provided, omit the **Related Work** section entirely.
- Remove any placeholder lines that have no real content.

**Title guidelines:**
- Use imperative mood: "Add feature" not "Added feature"
- Be specific: ✅ "Add OAuth2 authentication to API layer" — ❌ "Bug fixes"
- Follow conventional-commit format: `type(scope): summary`

#### Create PR
After drafting the title and description (see Summarization above), use the `mcp_io_github_git_create_pull_request` tool to open the PR against the target branch. Confirm the title and description with the user before submitting.

## Notes

- The `...` (three-dot) syntax in `git diff` compares from the **merge base**, not the tip of the target branch — this is the correct PR semantics
- If the branch has no commits ahead of the target, the diff will be empty — inform the user
- The scripts output metadata only; the agent retrieves the actual diff by running `git diff <target>...HEAD` directly in the terminal