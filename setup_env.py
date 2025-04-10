import os
import sqlite3

REQUIRED_DIRS = ["uploads", "logs", "data", "transcripts"]
DB_PATH = os.path.join("data", "jobs.db")

def ensure_directories():
    for d in REQUIRED_DIRS:
        os.makedirs(d, exist_ok=True)
        print(f"✅ Ensured directory: {d}")

def ensure_database():
    if not os.path.exists(DB_PATH):
        print("🆕 Creating new SQLite database at:", DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE jobs (
                job_id TEXT PRIMARY KEY,
                original_name TEXT,
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
        print("✅ Database initialized.")
    else:
        print("✅ jobs.db already exists.")

if __name__ == "__main__":
    print("🛠 Initializing local environment...")
    ensure_directories()
    ensure_database()
    print("✅ Environment ready!")
