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

# 3. Print number of lines in the diff
LINE_COUNT=$(git diff "$TARGET_BRANCH...HEAD" | wc -l)
echo ""
echo "Diff size: $LINE_COUNT lines"

# 4. Print remote info
echo ""
echo "Remote origin URL:"
git remote get-url origin
echo ""
echo "All remotes:"
git remote -v
