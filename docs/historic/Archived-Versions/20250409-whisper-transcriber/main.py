import os
import sys
import subprocess
import logging
import traceback
from tkinter import messagebox
import threading
import datetime

# ====== STEP 1: Auto-Install Missing Packages ======
REQUIRED_MODULES = {
    "customtkinter": "customtkinter",
    "openai-whisper": "whisper",
    "torch": "torch",
    "ffmpeg-python": "ffmpeg"
}

def install_missing_packages():
    missing = []
    for pip_name, module_name in REQUIRED_MODULES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("Installing missing packages:", missing)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("[INFO] Relaunching after install...")
        os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)] + sys.argv[1:])

install_missing_packages()

# ====== STEP 2: Logging Setup ======
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"whisper_transcriber_log_{timestamp}.log"
log_path = os.path.join(base_path, log_filename)

logging.basicConfig(
    level=logging.DEBUG,
    filename=log_path,
    filemode="w",
    format="%(asctime)s [%(levelname)s] %(message)s"
)

import io
sys.stdout = io.TextIOWrapper(open(log_path, "ab", buffering=0), encoding='ascii', errors='replace')
sys.stderr = sys.stdout


def exception_hook(exctype, value, tb):
    logging.error("Unhandled exception", exc_info=(exctype, value, tb))
    messagebox.showerror("Application Error", f"An unexpected error occurred:\n{value}")
    sys.exit(1)

sys.excepthook = exception_hook

print(f"[INFO] Logging started at: {log_path}")

# ====== STEP 3: Main Application Code ======
import customtkinter as ctk
from tkinter import filedialog
from core import settings, ffmpeg_installer

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class WhisperGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Whisper Transcriber")
        self.geometry("600x550")
        self.resizable(False, False)

        logging.info("App initialized.")

        self.settings = settings.load_settings()
        self.build_interface()
        ffmpeg_installer.ensure_ffmpeg()

    def build_interface(self):
        padding = 10

        self.input_label = ctk.CTkLabel(self, text="Input File or Folder")
        self.input_label.pack(pady=(padding, 0))
        self.input_entry = ctk.CTkEntry(self, width=450)
        self.input_entry.pack()
        self.input_button = ctk.CTkButton(self, text="Browse", command=self.browse_input)
        self.input_button.pack(pady=(0, padding))

        self.output_label = ctk.CTkLabel(self, text="Output Folder")
        self.output_label.pack()
        self.output_entry = ctk.CTkEntry(self, width=450)
        self.output_entry.insert(0, self.settings['output_path'])
        self.output_entry.pack()
        self.output_button = ctk.CTkButton(self, text="Browse", command=self.browse_output)
        self.output_button.pack(pady=(0, padding))

        self.model_label = ctk.CTkLabel(self, text="Model")
        self.model_label.pack()
        self.model_dropdown = ctk.CTkOptionMenu(
            self,
            values=[
                "tiny - Fastest, lowest accuracy",
                "small - Fast, decent accuracy",
                "base - Default",
                "medium - Slower, high accuracy",
                "large - Slowest, best"
            ]
        )
        self.model_dropdown.set(f"{self.settings['model']} - Default")
        self.model_dropdown.pack(pady=(0, padding))

        self.format_label = ctk.CTkLabel(self, text="Output Format")
        self.format_label.pack()
        self.format_var = ctk.StringVar(value=self.settings.get("format", "txt"))
        self.radio_txt = ctk.CTkRadioButton(self, text=".txt", variable=self.format_var, value="txt")
        self.radio_srt = ctk.CTkRadioButton(self, text=".srt", variable=self.format_var, value="srt")
        self.radio_vtt = ctk.CTkRadioButton(self, text=".vtt", variable=self.format_var, value="vtt")
        self.radio_txt.pack()
        self.radio_srt.pack()
        self.radio_vtt.pack(pady=(0, padding))

        self.timestamp_var = ctk.BooleanVar(value=self.settings.get("timestamps", False))
        self.timestamp_check = ctk.CTkCheckBox(self, text="Include timestamps", variable=self.timestamp_var)
        self.timestamp_check.pack()

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack(pady=(padding, 0))

        self.transcribe_button = ctk.CTkButton(self, text="Transcribe", command=self.start_transcription_thread)
        self.transcribe_button.pack(pady=(padding, 0))

    def browse_input(self):
        path = filedialog.askopenfilename(title="Select Audio File")
        if not path:
            path = filedialog.askdirectory(title="Select Folder for Batch")
        if path:
            self.input_entry.delete(0, ctk.END)
            self.input_entry.insert(0, path)
            logging.info(f"Selected input path: {path}")

    def browse_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_entry.delete(0, ctk.END)
            self.output_entry.insert(0, path)
            logging.info(f"Selected output path: {path}")

    def start_transcription_thread(self):
        self.status_label.configure(text="Transcribing, please wait...")
        self.transcribe_button.configure(state="disabled")
        thread = threading.Thread(target=self.run_transcription)
        thread.start()

    def run_transcription(self):
        try:
            file_or_folder = self.input_entry.get()
            out_dir = self.output_entry.get()
            model = self.model_dropdown.get().split(" - ")[0]
            fmt = self.format_var.get()
            use_timestamps = self.timestamp_var.get()

            if not os.path.exists(file_or_folder):
                logging.error("Input path does not exist.")
                messagebox.showerror("Error", "Input path does not exist.")
                return

            script_path = os.path.join(base_path, "core", "transcribe_cli.py")
            cmd = ["cmd.exe", "/k", sys.executable, script_path, file_or_folder, out_dir, model, fmt, str(use_timestamps)]
            subprocess.Popen(cmd)
            self.status_label.configure(text="CMD launched. Watch console for progress.")
        except Exception as e:
            logging.error("Error during transcription:", exc_info=True)
            messagebox.showerror("Transcription Error", str(e))
        finally:
            self.transcribe_button.configure(state="normal")

if __name__ == "__main__":
    logging.info("Launching application...")
    app = WhisperGUI()
    app.mainloop()
    logging.info("Application closed.")
