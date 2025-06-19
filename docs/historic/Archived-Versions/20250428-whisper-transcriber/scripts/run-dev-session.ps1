# scripts/run-dev-session.ps1
# Whisper Transcriber - Dev Session Bootstrapper

# -------------------------------
# Force change directory to project root
# -------------------------------
Set-Location (Resolve-Path "$PSScriptRoot\..").Path

Clear-Host
Write-Output "------------------------------"
Write-Output "🚀 WHISPER DEV SESSION STARTING"
Write-Output "------------------------------"

# -------------------------------
# Force UTF-8 Encoding
# -------------------------------
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# -------------------------------
# Check if virtual environment exists
# -------------------------------
if (-Not (Test-Path ".\whisper-env\Scripts\Activate.ps1")) {
    Write-Output "❌ Virtual environment not found!"
    Write-Output "Please create one by running:"
    Write-Output ""
    Write-Output "    python -m venv whisper-env"
    Write-Output ""
    Write-Output "After creating, re-run this script."
    exit
}

# -------------------------------
# Activate the virtual environment
# -------------------------------
Write-Output "✅ Activating whisper-env..."
. .\whisper-env\Scripts\Activate.ps1

# -------------------------------
# Run the session initialization script
# -------------------------------
Write-Output "✅ Running session setup..."
. .\scripts\start-whispersession.ps1

Write-Output "------------------------------"
Write-Output "✅ Dev session ready!"
Write-Output "------------------------------"
