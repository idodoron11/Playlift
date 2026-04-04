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

# 3. Produce full diff as a temporary file
$tmpDir = if ($env:TEMP) { $env:TEMP } elseif ($env:TMPDIR) { $env:TMPDIR } else { "/tmp" }
$tempFile = Join-Path $tmpDir "pr-diff-$currentBranch.diff"
git diff "$TargetBranch...HEAD" | Out-File -FilePath $tempFile -Encoding utf8
Write-Host "`nFull diff saved to: $tempFile"

# 4. Print number of rows in the diff
$lineCount = (Get-Content $tempFile | Measure-Object -Line).Lines
Write-Host "Diff size: $lineCount lines"
