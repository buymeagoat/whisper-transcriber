# core/ffmpeg_installer.py
import os
import subprocess
import shutil
import urllib.request
import zipfile

def is_ffmpeg_available():
    return shutil.which("ffmpeg") is not None

def download_and_extract_ffmpeg():
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = os.path.join(os.getenv("TEMP"), "ffmpeg.zip")
    extract_path = os.path.join(os.getenv("TEMP"), "ffmpeg")

    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    bin_path = next(p for p in os.listdir(extract_path) if os.path.isdir(os.path.join(extract_path, p)))
    final_bin = os.path.join(extract_path, bin_path, "bin")
    os.environ["PATH"] += os.pathsep + final_bin

def ensure_ffmpeg():
    if not is_ffmpeg_available():
        download_and_extract_ffmpeg()