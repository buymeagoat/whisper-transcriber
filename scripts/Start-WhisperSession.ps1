# start-whispersession.ps1
# Whisper Transcriber – Full Session Initialization + Environment Check

$repoUrl = "https://github.com/buymeagoat/whisper-transcriber"
$branch = git rev-parse --abbrev-ref HEAD
$remote = git config --get remote.origin.url
$status = git status --short
$clean = if ($status) { "❌ Uncommitted changes or untracked files" } else { "✅ Clean working directory" }

# Python module validator (current + anticipated)
$pythonCheck = @'
import sys
import importlib

# ✅ Add future modules to this list:
required_modules = [
    "torch", "whisper", "ffmpeg", "numpy", "soundfile",
    "pydub", "librosa", "faster_whisper", "whispercpp",
    "argparse", "json"
]

print(f"Python: {sys.version.split()[0]}")
print("Modules:")
for mod in required_modules:
    try:
        importlib.import_module(mod)
        print(f"  - {mod}: ✅")
    except ImportError:
        print(f"  - {mod}: ❌ (try: pip install {mod})")
'@

$pythonOutput = python -c $pythonCheck 2>&1

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

Write-Host "🔹 Environment Check:"
Write-Output $pythonOutput

Write-Host "`n📋 Paste this entire output into ChatGPT to continue setup."
Write-Host "------------------------------"
