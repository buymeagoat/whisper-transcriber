# core/transcribe.py
import whisper
import os
import subprocess

def run(input_path, output_dir, model_name, out_format="txt", timestamps=False):
    print("🔄 Starting transcription...")
    model = whisper.load_model(model_name)

    if os.path.isdir(input_path):
        for file in os.listdir(input_path):
            if file.lower().endswith(".m4a"):
                transcribe_one(os.path.join(input_path, file), output_dir, model, out_format, timestamps)
    else:
        transcribe_one(input_path, output_dir, model, out_format, timestamps)

def transcribe_one(path, out_dir, model, out_format, timestamps):
    result = model.transcribe(path, verbose=False)
    base_name = os.path.splitext(os.path.basename(path))[0]
    output_path = os.path.join(out_dir, base_name + f"_transcript.{out_format}")

    if out_format == "txt":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            for seg in result["segments"]:
                start = format_time(seg["start"])
                end = format_time(seg["end"])
                text = seg["text"].strip()
                if out_format == "srt":
                    f.write(f"{seg['id']+1}\n{start} --> {end}\n{text}\n\n")
                elif out_format == "vtt":
                    f.write(f"{start} --> {end}\n{text}\n\n")

    print(f"✅ Saved: {output_path}")

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}".replace('.', ',')
