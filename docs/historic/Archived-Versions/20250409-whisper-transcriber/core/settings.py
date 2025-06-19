# core/settings.py
import os
import json

APPDATA_PATH = os.path.join(os.environ['APPDATA'], "WhisperTranscriber")
SETTINGS_FILE = os.path.join(APPDATA_PATH, "settings.json")

DEFAULT_SETTINGS = {
    "model": "base",
    "output_path": os.path.join(os.path.expanduser("~"), "Documents", "Whisper Transcriptions")
}

def ensure_dirs():
    if not os.path.exists(APPDATA_PATH):
        os.makedirs(APPDATA_PATH)
    if not os.path.exists(DEFAULT_SETTINGS['output_path']):
        os.makedirs(DEFAULT_SETTINGS['output_path'])

def load_settings():
    ensure_dirs()
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
    with open(SETTINGS_FILE, 'r') as f:
        return json.load(f)

def save_settings(data):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=2)