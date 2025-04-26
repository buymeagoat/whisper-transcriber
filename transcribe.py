import argparse
import os
import sys
import datetime
import whisper
import json

# -------------------------------
# Setup Logging
# -------------------------------
logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
log_filename = os.path.join(logs_dir, f'transcribe_{timestamp}.log')

class Tee(object):
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()

sys.stdout = Tee(sys.stdout, open(log_filename, 'w', encoding='utf-8'))
sys.stderr = sys.stdout

# -------------------------------
# Argument Parsing
# -------------------------------
parser = argparse.ArgumentParser(description="Transcribe an audio file using Whisper.")
parser.add_argument('--input', required=True, help='Path to input audio file')
parser.add_argument('--model', default='base.en', help='Whisper model size (tiny, base, small, medium, large)')
args = parser.parse_args()

# -------------------------------
# Load Whisper Model (Local First)
# -------------------------------
def load_local_whisper_model(model_size="base.en"):
    models_root = os.path.join(os.path.dirname(__file__), 'models')
    model_folder = os.path.join(models_root, model_size)
    model_path = os.path.join(model_folder, f"{model_size}.pt")

    if os.path.isfile(model_path):
        print(f"✅ Loading model '{model_size}' directly from local file: {model_path}")
        return whisper.load_model(model_path)
    else:
        print(f"⚠️ Local model '{model_size}' not found. Falling back to remote download.")
        return whisper.load_model(model_size)

print("Starting transcription process...")
start_time = datetime.datetime.now()
print(f"Start Time: {start_time}")

model = load_local_whisper_model(args.model)

# -------------------------------
# Transcribe Audio
# -------------------------------
print(f"Transcribing file: {args.input}...")
result = model.transcribe(args.input)

# -------------------------------
# Save Transcript
# -------------------------------
transcripts_dir = os.path.join(os.path.dirname(__file__), 'transcripts')
os.makedirs(transcripts_dir, exist_ok=True)

base_filename = os.path.splitext(os.path.basename(args.input))[0]
output_txt = os.path.join(transcripts_dir, f"{base_filename}.txt")

# Save clean readable TXT transcript
if 'segments' in result:
    with open(output_txt, 'w', encoding='utf-8') as f:
        for segment in result['segments']:
            start_sec = int(segment['start'])
            minutes = start_sec // 60
            seconds = start_sec % 60
            timestamp = f"[{minutes:02}:{seconds:02}]"
            f.write(f"{timestamp} {segment['text'].strip()}\n")
else:
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write("No segments found.\n")

# -------------------------------
# Final Logging
# -------------------------------
end_time = datetime.datetime.now()
print("✅ Transcription complete.")
print(f"Language Detected: {result.get('language', 'unknown')}")
print(f"Transcript Saved (TXT): {output_txt}")
print(f"Log Saved: {log_filename}")
print(f"End Time: {end_time}")
print(f"Duration: {end_time - start_time}")
