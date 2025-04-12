# start-whispersession.ps1
# Whisper Transcriber – Session Initialization Script

$repoUrl = "https://github.com/buymeagoat/whisper-transcriber"
$branch = git rev-parse --abbrev-ref HEAD
$remote = git config --get remote.origin.url
$status = git status --short
$clean = if ($status) { "❌ Uncommitted changes or untracked files" } else { "✅ Clean working directory" }

Write-Host "------------------------------"
Write-Host "📌 WHISPER SESSION INITIALIZATION"
Write-Host "------------------------------`n"

Write-Host "🔹 Repo URL:"
Write-Host "Repo: $repoUrl"
Write-Host "✅ This is my active local development repo`n"

Write-Host "🔹 Repo State:"
Write-Host "Active Branch: $branch"
Write-Host "Remote: $remote"
Write-Host "Status: $clean`n"

Write-Host "🔹 ChatGPT Authorization:"
Write-Host "✅ You have permission to analyze this repository and fetch live files from:"
Write-Host "$repoUrl"
Write-Host "You are allowed to load and review all committed files to support development.`n"

Write-Host "📋 Paste this entire output into ChatGPT to continue setup."
Write-Host "------------------------------"
