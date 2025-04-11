import os
import shutil
import sqlite3
import stat
import subprocess

SAFE_KEEP = {".git", "setup_env.py"}
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))

def make_writable_and_remove(path):
    def onerror(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if os.path.isdir(path):
        shutil.rmtree(path, onerror=onerror)
        print(f"🧹 Deleted folder: {os.path.relpath(path, REPO_ROOT)}")
    else:
        os.remove(path)
        print(f"🧼 Deleted file: {os.path.relpath(path, REPO_ROOT)}")

def wipe_all_except_safe():
    for item in os.listdir(REPO_ROOT):
        if item in SAFE_KEEP:
            continue
        full_path = os.path.join(REPO_ROOT, item)
        make_writable_and_remove(full_path)

def recreate_directories():
    for folder in ["uploads", "logs", "data", "transcripts"]:
        os.makedirs(os.path.join(REPO_ROOT, folder), exist_ok=True)
        print(f"📁 Created directory: {folder}")

def initialize_database():
    db_path = os.path.join(REPO_ROOT, "data", "jobs.db")
    schema = """
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        file_name TEXT NOT NULL,
        status TEXT NOT NULL,
        model TEXT,
        created TEXT NOT NULL
    );
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute(schema)
    print("🗃️ Initialized jobs.db with correct schema.")

def restore_git_files():
    try:
        subprocess.run(["git", "restore", "."], check=True)
        print("🔄 Restored tracked files from Git.")
    except Exception:
        print("⚠️  Git restore failed. Make sure Git is installed and you're in a cloned repo.")

if __name__ == "__main__":
    print("🔧 Resetting whisper-transcriber environment...")
    print("⚠️  WARNING: This will DELETE everything in this folder except:")
    for item in SAFE_KEEP:
        print(f" - {item}")
    print("🛠 It will then recreate only the required environment folders and files.")
    confirm = input("Type 'yes' to confirm: ").strip().lower()
    if confirm == "yes":
        wipe_all_except_safe()
        recreate_directories()
        initialize_database()
        restore_git_files()
        print("✅ Environment is clean and ready.")
    else:
        print("❌ Cancelled.")
