# app/job_store.py

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "jobs.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    file_name TEXT,
    original_name TEXT,
    created_at TEXT,
    status TEXT,
    model TEXT,
    format TEXT,
    timestamps BOOLEAN,
    task TEXT,
    language TEXT,
    initial_prompt TEXT,
    start_time INTEGER,
    end_time INTEGER,
    log_path TEXT,
    output_path TEXT
);
"""

def init_db():
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(SCHEMA)
        conn.commit()

def add_job(job):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO jobs (
                job_id, file_name, original_name, created_at, status,
                model, format, timestamps, task, language,
                initial_prompt, start_time, end_time, log_path, output_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job["job_id"],
            job["file_name"],
            job["original_name"],
            job["created_at"],
            job["status"],
            job["model"],
            job["format"],
            job["timestamps"],
            job["task"],
            job["language"],
            job["initial_prompt"],
            job["start_time"],
            job["end_time"],
            job["log_path"],
            job["output_path"]
        ))
        conn.commit()

def update_job_status(job_id, new_status):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE jobs SET status = ? WHERE job_id = ?", (new_status, job_id))
        conn.commit()

def get_job(job_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        return dict(zip([column[0] for column in cursor.description], row)) if row else None

def get_all_jobs():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
