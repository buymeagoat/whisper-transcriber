# scripts/start-whispersession.ps1

Write-Host "`n📂 Whisper Transcriber — Session Verification Report`n" -ForegroundColor Cyan

# Git Remote
$gitRemote = git remote -v 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Unable to read git remote. Are you in a git repo?" -ForegroundColor Red
    exit 1
}

Write-Host "🔗 Git Remote:" -ForegroundColor Yellow
$gitRemote | ForEach-Object { Write-Host $_ }
Write-Host ""

# Git Branch
$gitBranch = git branch --show-current 2>&1
Write-Host "🌿 Branch:" -ForegroundColor Yellow
Write-Host $gitBranch
Write-Host ""

# Git Status
$gitStatus = git status --short 2>&1
Write-Host "📦 Working Directory Status:" -ForegroundColor Yellow
if ($gitStatus) {
    Write-Host $gitStatus
} else {
    Write-Host "nothing to commit, working tree clean"
}

Write-Host "`n✅ Copy this full block into ChatGPT to verify your dev session." -ForegroundColor Green
