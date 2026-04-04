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

### Step 1 — Ask for the Target Branch

**You MUST ask the user for the target branch first.** Do not assume.

Use the ask-questions tool with pre-filled options `origin/main` and `origin/master` (mark `origin/main` as recommended), but allow freeform input for other branches (e.g., `develop`, `release/1.0`).

> "What is the target branch to compare against?"

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

The script produces four pieces of output; use each as follows:

| Output | Source | How the agent uses it |
|--------|--------|-----------------------|
| **Current branch name** | `git rev-parse --abbrev-ref HEAD` | Report which feature branch is under review |
| **Modified files list** | `git diff --name-status origin/main...HEAD` | Group by status (`A` Added / `M` Modified / `D` Deleted / `R` Renamed) and present a structured scope summary |
| **Temp diff file path** | `$TMPDIR/pr-diff-<branch>.diff` | Call `read_file` on this path to access the full diff for deep analysis |
| **Diff line count** | PowerShell `Measure-Object -Line` | Use as a scope signal: ≤1000 lines → read full diff at once; >1000 lines → offer per-file sections or summaries |
| **Remote origin URL** | `git remote get-url origin` | Extract the `owner` and `repo` to pass to `mcp_io_github_git_create_pull_request` |
| **All remotes** | `git remote -v` | Confirm remote names and URLs before creating a PR |

### Step 3 — Digest the Output

After digesting the output, the agent MUST:

1. Report the **current branch** and **target branch**
2. List the **modified files** grouped by status (Added / Modified / Deleted / Renamed)
3. State the **diff size** (line count) as a signal of PR scope

The agent now has full context to proceed with Step 4 and then the appropriate follow-up action in Step 5.

### Step 4 — Read the Full Diff File

Once the diff file is ready, the agent MUST read the temp diff file directly using `read_file` on the path printed by the script. This is a **mandatory step** — do not skip it.

Because the file lives outside the VS Code workspace, VS Code will automatically prompt the user to approve the read operation. Wait for approval and then proceed.

**Important**: DO NOT fall back to terminal commands (`cat`, `grep`, etc.) to work around the permission prompt. The file must be read via `read_file` so that VS Code can surface the consent dialog to the user.

### Step 5 — Perform the Requested Action

Based on the user's intent, proceed with one of these actions after reading the diff:

#### PR Review
Perform a thorough code review following the project's code review instructions. Address security, correctness, test coverage, and style — grouped by severity (Critical / Important / Suggestion).

#### PR Summarization (title + description)
Draft a concise PR title (conventional commit format: `type(scope): summary`) and a structured description covering:
- **What**: What was changed and why
- **How**: Key implementation decisions
- **Testing**: How changes were or should be tested
- **Breaking changes** (if any)

#### Create PR
After drafting the title and description (see Summarization above), use the `mcp_io_github_git_create_pull_request` tool to open the PR against the target branch. Confirm the title and description with the user before submitting.

## Notes

- The `...` (three-dot) syntax in `git diff` compares from the **merge base**, not the tip of the target branch — this is the correct PR semantics
- If the branch has no commits ahead of the target, the diff will be empty — inform the user
- The temp diff file path is printed by the script; use `read_file` on it for deep analysis
