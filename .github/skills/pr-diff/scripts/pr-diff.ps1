param(
    [Parameter(Mandatory=$true)]
    [string]$TargetBranch
)

# 1. Show current branch name
$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "Current branch: $currentBranch"
Write-Host "Comparing against: $TargetBranch"

# 2. List all modified files
Write-Host "`nModified files:"
git diff --name-status "$TargetBranch...HEAD"

# 3. Print number of rows in the diff
$lineCount = (git diff "$TargetBranch...HEAD" | Measure-Object -Line).Lines
Write-Host "`nDiff size: $lineCount lines"

# 4. Print remote info
Write-Host "`nRemote origin URL:"
git remote get-url origin
Write-Host "`nAll remotes:"
git remote -v
