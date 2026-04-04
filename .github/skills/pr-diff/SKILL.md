---
name: pr-diff
description: 'Produce a pull request diff between the current branch and a target branch. Use when: reviewing PR changes, understanding what a branch introduces, code review preparation, summarizing branch differences, comparing branches, getting diff output.'
argument-hint: Target branch to compare against (e.g. main, master, develop)
---

# PR Diff

Produces a structured diff between the current branch and a target branch, giving the agent full context on what the PR introduces.

## When to Use

- User asks to review PR changes or summarize what a branch does
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

### Step 3 — Digest the Output

After digesting the output, the agent MUST:

1. Report the **current branch** and **target branch**
2. List the **modified files** grouped by status (Added / Modified / Deleted / Renamed)
3. State the **diff size** (line count) as a signal of PR scope

The agent now has full context to proceed with whatever the user needs next (code review, summary, changelog, impact analysis, etc.).

### Step 4 — Read the Full Diff File

Once the diff file is ready, the agent MUST read the temp diff file directly using `read_file` on the path printed by the script. This is a **mandatory step** — do not skip it.

Because the file lives outside the VS Code workspace, VS Code will automatically prompt the user to approve the read operation. Wait for approval and then proceed.

**Important**: DO NOT fall back to terminal commands (`cat`, `grep`, etc.) to work around the permission prompt. The file must be read via `read_file` so that VS Code can surface the consent dialog to the user.

## Notes

- The `...` (three-dot) syntax in `git diff` compares from the **merge base**, not the tip of the target branch — this is the correct PR semantics
- If the branch has no commits ahead of the target, the diff will be empty — inform the user
- The temp diff file path is printed by the script; use `read_file` on it for deep analysis
