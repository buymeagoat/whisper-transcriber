import os
import shutil
import sqlite3
import sys

SAFE_KEEP = {"setup_env.py", ".git"}
RESET_DIRS = ["uploads", "logs", "data", "transcripts"]
DB_PATH = os.path.join("data", "jobs.db")

def confirm_root_folder():
    if not os.path.exists("setup_env.py"):
        print("❌ ERROR: You must run this from the root of the whisper-transcriber directory.")
        sys.exit(1)

def confirm_action():
    print("⚠️  WARNING: This will DELETE everything in this folder except:")
    for item in SAFE_KEEP:
        print(f" - {item}")
    print("🛠 It will then recreate only the required environment folders and files.")
    confirm = input("Type 'yes' to confirm: ").strip().lower()
    if confirm != "yes":
        print("❌ Aborted.")
        sys.exit(0)

def wipe_all_except_safe():
    for item in os.listdir():
        if item in SAFE_KEEP:
            continue
        if os.path.isdir(item):
            shutil.rmtree(item)
            print(f"🧹 Deleted folder: {item}")
        else:
            os.remove(item)
            print(f"🧼 Deleted file: {item}")

def recreate_dirs():
    for d in RESET_DIRS:
        os.makedirs(d, exist_ok=True)
        print(f"📁 Created directory: {d}")

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            original_name TEXT,
            file_name TEXT,
            stored_path TEXT,
            status TEXT,
            model TEXT,
            output_format TEXT,
            output_path TEXT,
            created_at TEXT,
            error TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("🗃️ Initialized jobs.db with correct schema.")

if __name__ == "__main__":
    print("🔧 Resetting whisper-transcriber environment...")
    confirm_root_folder()
    confirm_action()
    wipe_all_except_safe()
    recreate_dirs()
    create_database()
    print("✅ Environment is clean and ready.")
