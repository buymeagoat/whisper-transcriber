# setup_env.py
# Whisper Transcriber - Developer Environment Reset and Bootstrap

import os
import shutil
import stat
import sqlite3

def make_writable(func, path, _):
    """Helper function to make files writable during deletion."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def wipe_all_except_safe():
    """Deletes everything in the repo except .git/, setup_env.py, and whisper-env/ (local venv)."""
    SAFE_KEEP = {".git", "setup_env.py", "whisper-env"}
    for item in os.listdir('.'):
        if item not in SAFE_KEEP:
            if os.path.isdir(item):
                shutil.rmtree(item, onerror=make_writable)
            else:
                os.remove(item)

def create_folder_structure():
    """Creates essential folders fresh."""
    folders = ["uploads", "logs", "data", "transcripts"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def initialize_database():
    """Creates a fresh SQLite database for job tracking."""
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        status TEXT,
        model TEXT,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("\n------------------------------")
    print("✨ WHISPER ENVIRONMENT RESET")
    print("------------------------------\n")

    print("Wiping repository (except .git/, setup_env.py, and whisper-env/)...")
    wipe_all_except_safe()

    print("Creating fresh folder structure...")
    create_folder_structure()

    print("Initializing new database (data/jobs.db)...")
    initialize_database()

    print("\n✅ Environment reset complete.")
    print("- uploads/     (for incoming audio)")
    print("- logs/        (for system and job logs)")
    print("- data/        (for jobs.db database)")
    print("- transcripts/ (for output transcripts)")
    print("- whisper-env/ (local venv, untouched, NOT in Git)")
    print("\nReady to develop!")
