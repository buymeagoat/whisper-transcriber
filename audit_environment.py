#!/usr/bin/env python3

import sys
import json
import shutil
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from api.utils.logger import get_system_logger

backend_log = get_system_logger("audit")

PROJECT_ROOT = Path(__file__).resolve().parent
EXCLUDED_DIRS = {"venv", "__pycache__"}
KEY_DIRS = ["uploads", "transcripts", "logs", "models"]
KEY_FILES = ["main.py", "metadata_writer.py", "models.py", ".env"]

def get_python_info():
    return {
        "version": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "architecture": platform.machine()
    }

def get_installed_packages():
    try:
        output = subprocess.check_output(["pip", "freeze"], text=True)
        return output.strip().splitlines()
    except Exception as e:
        return [f"ERROR: {e}"]

def find_undefined_function_calls():
    import ast

    calls = set()
    defs = set()

    for entry in list_project_files():
        if entry["type"] == "file" and entry["path"].endswith(".py"):
            try:
                with open(entry["path"], "r") as f:
                    try:
                        tree = ast.parse(f.read())
                    except SyntaxError as e:
                        backend_log.warning(
                            "Skipping file with syntax error: %s (%s)", entry["path"], e
                        )
                        continue

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            defs.add(node.name)
                        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                            calls.add(node.func.id)
            except Exception:
                continue

    # Calls not backed by definitions
    return sorted(list(calls - defs))


def detect_duplicate_symbols():
    from collections import defaultdict
    import ast

    symbol_map = defaultdict(list)

    for entry in list_project_files():
        if entry["type"] == "file" and entry["path"].endswith(".py"):
            try:
                with open(entry["path"], "r") as f:
                    try:
                        tree = ast.parse(f.read(), filename=entry["path"])
                    except SyntaxError as e:
                        backend_log.warning(
                            "Skipping file with syntax error: %s (%s)", entry["path"], e
                        )
                        continue

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                            symbol_map[node.name].append(entry["path"])
            except Exception:
                continue  # Skip unreadable files

    return {k: v for k, v in symbol_map.items() if len(v) > 1}

def list_project_files():
    structure = []
    for path in PROJECT_ROOT.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        rel_path = path.relative_to(PROJECT_ROOT)
        entry = {
            "type": "dir" if path.is_dir() else "file",
            "path": str(rel_path)
        }
        structure.append(entry)
    return structure

def load_env_file():
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return ["Missing .env file"]
    lines = [line.strip() for line in env_path.read_text().splitlines() if line.strip() and not line.startswith("#")]
    return lines

def check_cuda():
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return "torch not installed"

def get_whisper_bin():
    return shutil.which("whisper") or "Not found in PATH"

def verify_key_dirs():
    missing = []
    for d in KEY_DIRS:
        if not (PROJECT_ROOT / d).exists():
            missing.append(d)
    return missing

def count_python_files():
    counts = defaultdict(int)
    for entry in list_project_files():
        if entry["type"] == "file" and entry["path"].endswith(".py"):
            top_level = entry["path"].split("/")[0]
            counts[top_level] += 1
    return dict(counts)

def read_critical_files():
    result = {}
    for name in KEY_FILES:
        f = PROJECT_ROOT / name
        if f.exists():
            result[name] = f.read_text()
        else:
            result[name] = "FILE NOT FOUND"
    return result

def large_files_warning(threshold=500):
    result = []
    for entry in list_project_files():
        if entry["type"] == "file" and entry["path"].endswith(".py"):
            try:
                lines = (PROJECT_ROOT / entry["path"]).read_text().splitlines()
                if len(lines) > threshold:
                    result.append({"path": entry["path"], "lines": len(lines)})
            except:
                continue
    return result

def function_count_by_file():
    import ast
    counts = {}
    for entry in list_project_files():
        if entry["type"] == "file" and entry["path"].endswith(".py"):
            try:
                with open(entry["path"], "r") as f:
                    tree = ast.parse(f.read())
                    count = sum(isinstance(n, ast.FunctionDef) for n in ast.walk(tree))
                    counts[entry["path"]] = count
            except Exception:
                continue
    return counts

def find_orphaned_files():
    import ast
    defined_modules = set()
    imported_modules = set()

    for entry in list_project_files():
        if entry["type"] == "file" and entry["path"].endswith(".py"):
            defined_modules.add(entry["path"].replace(".py", "").replace("/", "."))
            try:
                with open(entry["path"], "r") as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imported_modules.add(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imported_modules.add(node.module)
            except Exception:
                continue

    return sorted(list(defined_modules - imported_modules))

def main():
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "python_info": get_python_info(),
        "cuda_available": check_cuda(),
        "whisper_binary": get_whisper_bin(),
        "project_structure": list_project_files(),
        "installed_packages": get_installed_packages(),
        "env_file_contents": load_env_file(),
        "critical_file_contents": read_critical_files(),
    }

    # Extra checks
    report["fastapi_routes_found"] = any("routes" in entry["path"] for entry in report["project_structure"])
    report["schemas_py_present"] = any(entry["path"].endswith("schemas.py") for entry in report["project_structure"])
    report["frontend_dir_present"] = any("frontend" in entry["path"] for entry in report["project_structure"])
    report["py_file_counts_by_folder"] = count_python_files()
    report["orphaned_modules"] = find_orphaned_files()
    report["missing_directories"] = verify_key_dirs()
    report["function_count_by_file"] = function_count_by_file()
    report["test_files_present"] = any("test" in entry["path"] for entry in report["project_structure"])
    report["large_files"] = large_files_warning()
    report["codebase_health"] = {
        "duplicate_symbols": detect_duplicate_symbols(),
        "undefined_function_calls": find_undefined_function_calls(),
        # "unused_functions": [...],  # Add later if needed
    }

    out_path = PROJECT_ROOT / "environment_audit.json"
    out_path.write_text(json.dumps(report, indent=2))
    backend_log.info("\n🔍 Summary:")
    backend_log.info(
        "- Python files scanned: %s",
        sum(report["py_file_counts_by_folder"].values()),
    )
    backend_log.info(
        "- Duplicate symbols: %s",
        len(report["codebase_health"]["duplicate_symbols"]),
    )
    backend_log.info(
        "- Undefined calls: %s",
        len(report["codebase_health"]["undefined_function_calls"]),
    )
    backend_log.info(
        "- Orphaned modules: %s",
        len(report.get("orphaned_modules", [])),
    )
    backend_log.info("✅ Environment audit written to: %s", out_path)


if __name__ == "__main__":
    main()