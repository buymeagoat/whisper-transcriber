from pathlib import Path

ROOT = Path(__file__).parent
UPLOAD_DIR = ROOT.parent / "uploads"
TRANSCRIPTS_DIR = ROOT.parent / "transcripts"
MODEL_DIR = ROOT.parent / "models"
LOG_DIR = ROOT.parent / "logs"

for path in (UPLOAD_DIR, TRANSCRIPTS_DIR, MODEL_DIR, LOG_DIR):
    path.mkdir(parents=True, exist_ok=True)
