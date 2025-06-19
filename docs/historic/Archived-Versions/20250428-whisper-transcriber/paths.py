import os

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Key folders
APP_DIR = os.path.join(BASE_DIR, 'app')
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, 'transcripts')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Key files
DB_PATH = os.path.join(DATA_DIR, 'jobs.db')

# Ensure important folders exist (optional safety)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Optional: Print paths for debugging (comment out in production)
if __name__ == "__main__":
    print(f"BASE_DIR = {BASE_DIR}")
    print(f"DATA_DIR = {DATA_DIR}")
    print(f"UPLOADS_DIR = {UPLOADS_DIR}")
    print(f"TRANSCRIPTS_DIR = {TRANSCRIPTS_DIR}")
    print(f"LOGS_DIR = {LOGS_DIR}")
    print(f"MODELS_DIR = {MODELS_DIR}")
    print(f"DB_PATH = {DB_PATH}")
