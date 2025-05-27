# audit_environment.py

"""
Audit the project structure and file contents for Whisper Transcriber.
Outputs:
1. Full file tree
2. Contents of all files created, patched, or expected

Output: project_audit.txt
"""

import os

ROOT_DIR = os.path.abspath(".")
OUTPUT_FILE = "project_audit.txt"
EXCLUDE_DIRS = {"venv", "node_modules", "__pycache__"}

# === CRITICAL FILES (present or planned) ===
CRITICAL_FILES = [
    # Root-level
    "design_scope.md",
    "requirements.txt",
    "audit_environment.py",
    "orchestrate.py",                 # CLI runner
    "alembic.ini",

    # Backend
    "api/main.py",
    "api/models.py",
    "api/metadata_writer.py",
    "api/utils/logger.py",
    "api/migrations/env.py",
]

# Alembic versions (dynamic)
for root, _, files in os.walk("api/migrations/versions"):
    for file in files:
        if file.endswith(".py"):
            CRITICAL_FILES.append(os.path.join(root, file))

# Frontend core
CRITICAL_FILES += [
    "frontend/package.json",
    "frontend/vite.config.js",
    "frontend/public/index.html",
    "frontend/src/main.jsx",
    "frontend/src/App.jsx",
]

# Frontend pages — current + expected
PAGE_COMPONENTS = [
    "UploadPage.jsx",
    "ActiveJobsPage.jsx",
    "CompletedJobsPage.jsx",
    "TranscriptViewPage.jsx",
    "AdminLogsPage.jsx",
    "DashboardPage.jsx",      # Expected, uncreated
    "SettingsPage.jsx",       # Expected, uncreated
]
for page in PAGE_COMPONENTS:
    CRITICAL_FILES.append(f"frontend/src/pages/{page}")

# Optional: include session state
if os.path.exists("handoff.txt"):
    CRITICAL_FILES.append("handoff.txt")

def is_excluded(path):
    parts = path.split(os.sep)
    return any(part in EXCLUDE_DIRS for part in parts)

def list_all_files():
    file_list = []
    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            full_path = os.path.relpath(os.path.join(root, f), ROOT_DIR)
            if not is_excluded(full_path):
                file_list.append(full_path)
    return file_list

def dump_file_contents(outfile, filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            contents = f.read()
        outfile.write(f"\n== FILE: {filepath} ==\n")
        outfile.write(contents)
        outfile.write("\n")
    except Exception as e:
        outfile.write(f"\n== FILE: {filepath} (error reading: {e}) ==\n")

def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("== FILE TREE ==\n")
        for path in sorted(list_all_files()):
            out.write(f"{path}\n")

        out.write("\n== CRITICAL FILE CONTENTS ==\n")
        for path in CRITICAL_FILES:
            if os.path.exists(path):
                dump_file_contents(out, path)
            else:
                out.write(f"\n== FILE: {path} (missing) ==\n")

if __name__ == "__main__":
    main()
