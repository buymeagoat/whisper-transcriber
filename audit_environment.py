# audit_environment.py
"""
This script generates a comprehensive audit of the `whisper-transcriber/` project directory.
It performs two main tasks:

1. Recursively lists all files and folders, excluding `venv/` and `node_modules/`.
2. Outputs the full contents of all files defined as critical in design_scope.md, including both backend and frontend sources.

The output is written to `project_audit.txt` in the current working directory.
"""

import os

# Root directory to scan
ROOT_DIR = os.path.abspath(".")
EXCLUDE_DIRS = {"venv", "node_modules", "__pycache__"}
OUTPUT_FILE = "project_audit.txt"

# Critical files to dump in full
CRITICAL_FILES = [
    "design_scope.md",
    "requirements.txt",
    ".gitignore",
    "jobs.db",
    # Backend
    "api/main.py",
    "api/utils/logger.py",
    "api/metadata_writer.py",
    "api/models.py",
    "api/migrations/env.py",
]  # Versions/*.py will be included dynamically

# Frontend
FRONTEND_FILES = [
    "frontend/package.json",
    "frontend/vite.config.js",
    "frontend/public/index.html",
    "frontend/src/main.jsx",
    "frontend/src/App.jsx",
    "frontend/src/pages/UploadPage.jsx",
    "frontend/src/pages/AdminLogsPage.jsx",
    "frontend/src/pages/ActiveJobsPage.jsx",
    "frontend/src/pages/TranscriptViewPage.jsx",
]

# Add all migration versions
for root, _, files in os.walk("api/migrations/versions"):
    for file in files:
        if file.endswith(".py"):
            CRITICAL_FILES.append(os.path.join(root, file))

CRITICAL_FILES += FRONTEND_FILES


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
