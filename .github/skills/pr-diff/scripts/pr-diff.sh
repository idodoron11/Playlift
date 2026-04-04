#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <target-branch>" >&2
    exit 1
fi

TARGET_BRANCH="$1"

# 1. Show current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"
echo "Comparing against: $TARGET_BRANCH"

# 2. List all modified files
echo ""
echo "Modified files:"
git diff --name-status "$TARGET_BRANCH...HEAD"

# 3. Produce full diff as a temporary file
TMP_DIR="${TMPDIR:-${TEMP:-/tmp}}"
TEMP_FILE="$TMP_DIR/pr-diff-$CURRENT_BRANCH.diff"
git diff "$TARGET_BRANCH...HEAD" > "$TEMP_FILE"
echo ""
echo "Full diff saved to: $TEMP_FILE"

# 4. Print number of lines in the diff
LINE_COUNT=$(wc -l < "$TEMP_FILE")
echo "Diff size: $LINE_COUNT lines"

# 5. Print remote info
echo ""
echo "Remote origin URL:"
git remote get-url origin
echo ""
echo "All remotes:"
git remote -v
