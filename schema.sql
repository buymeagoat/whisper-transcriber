CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    original_filename TEXT,
    saved_filename TEXT,
    model TEXT,
    created_at TEXT,
    status TEXT,
    transcript_path TEXT,
    error_message TEXT
);
