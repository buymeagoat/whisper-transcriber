# Start-WhisperSession.ps1
# Whisper Transcriber - Developer Session Starter (Self-Healing + Clean Venv Check + Folder Verification)
# Determine project root (one level up from /scripts/)
$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path

Clear-Host

Write-Output "------------------------------"
Write-Output "📌 WHISPER SESSION INITIALIZATION"
Write-Output "------------------------------"

# Force UTF-8 encoding to avoid Unicode errors
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Venv Check
if (-not $env:VIRTUAL_ENV) {
    Write-Output "⚠️  Your Python virtual environment (whisper-env) is NOT activated!"
    Write-Output ""
    Write-Output "To continue:" 
    Write-Output "  1. Copy the command below"
    Write-Output "  2. Paste it into THIS SAME TERMINAL window"
    Write-Output "  3. Press ENTER to activate the environment"
    Write-Output "  4. Then rerun this script: .\\scripts\\Start-WhisperSession.ps1"
    Write-Output ""
    Write-Output "Activate your venv by running:" 
    Write-Output ""
    Write-Output "    .\\whisper-env\\Scripts\\activate"
    Write-Output ""
    Write-Output "❌ Session initialization terminated. Please activate your virtual environment and rerun this script."
    exit
}

# Display Repo Info
Write-Output "🔹 Repo URL:"
$repoUrl = git config --get remote.origin.url
Write-Output "Repo: $repoUrl"

Write-Output "🔹 Repo State:"
$branch = git rev-parse --abbrev-ref HEAD
$remote = git config --get remote.origin.url
$status = git status --porcelain

Write-Output "Active Branch: $branch"
Write-Output "Remote: $remote"

if ($status) {
    Write-Output "Status: ❌ Uncommitted changes or untracked files"
    Write-Output "Uncommitted Changes/Untracked Files:"
    git status --short
} else {
    Write-Output "Status: ✅ Repo is clean"
}

# ChatGPT Authorization Notice
Write-Output "🔹 ChatGPT Authorization:"
Write-Output "✅ You have permission to analyze this repository and fetch live files from:"
Write-Output "$repoUrl"

# Environment Check
Write-Output "🔹 Environment Check:"

$pythonCheck = @'
import sys
import importlib
import subprocess
import shutil

modules = [
    "torch", "whisper", "numpy", "soundfile", "pydub", "librosa", "faster_whisper", "whispercpp", "argparse", "json"
]

print(f"Python: {sys.version.split()[0]}")
print("Modules:")

for mod in modules:
    try:
        importlib.import_module(mod)
        print(f"  - {mod}: ✅")
    except ImportError:
        print(f"  - {mod}: ❌ - Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", mod])
            importlib.import_module(mod)
            print(f"  - {mod}: ✅ (after install)")
        except Exception as e:
            print(f"  - {mod}: ❌❌ Install failed. Manual check needed.")

# Check for ffmpeg binary
print("\nChecking for system ffmpeg binary:")
if shutil.which("ffmpeg"):
    print("  - ffmpeg: ✅ Found on system PATH")
else:
    print("  - ffmpeg: ❌ Not found! Please install via winget or system package manager.")
'@

try {
    python -c $pythonCheck
} catch {
    Write-Output "❌ Error running Python environment check."
    Write-Output $_
}

# -------------------------------
# Check for critical project folders
# -------------------------------
Write-Output "🔹 Folder Structure Check:"

# Calculate project root (one level up from scripts/)
$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path

$requiredFolders = @("uploads", "logs", "transcripts")

foreach ($folder in $requiredFolders) {
    $folderPath = Join-Path $ProjectRoot $folder
    if (-Not (Test-Path $folderPath)) {
        Write-Output "⚠️  Folder '$folder' not found at project root. Creating..."
        New-Item -ItemType Directory -Path $folderPath | Out-Null
    } else {
        Write-Output "✅ Folder '$folder' exists at project root."
    }
}


Write-Output "------------------------------"
Write-Output "Session Initialization Complete."
