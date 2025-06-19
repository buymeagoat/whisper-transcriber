import sys
import os
import whisper

def transcribe_file(input_path, output_dir, model_name, output_format="txt", timestamps=False):
    model = whisper.load_model(model_name)
    basename = os.path.basename(input_path)
    name, _ = os.path.splitext(basename)

    print(f"[INFO] Loading model: {model_name}")
    print(f"[INFO] Transcribing: {input_path}")

    result = model.transcribe(input_path, verbose=True)

    output_path = os.path.join(output_dir, f"{name}.{output_format}")

    print(f"[INFO] Writing to: {output_path}")

    if output_format == "txt":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
    elif output_format in ("srt", "vtt"):
        segments = result["segments"]
        with open(output_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start = seg["start"]
                end = seg["end"]
                text = seg["text"]

                def format_time(t):
                    h = int(t // 3600)
                    m = int((t % 3600) // 60)
                    s = int(t % 60)
                    ms = int((t - int(t)) * 1000)
                    return f"{h:02}:{m:02}:{s:02},{ms:03}"

                if output_format == "srt":
                    f.write(f"{i}\n{format_time(start)} --> {format_time(end)}\n{text.strip()}\n\n")
                elif output_format == "vtt":
                    f.write(f"{format_time(start).replace(',', '.')} --> {format_time(end).replace(',', '.')}\n{text.strip()}\n\n")

    print("[INFO] Done.")


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python transcribe_cli.py <input_path> <output_dir> <model> <format> <timestamps>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    model = sys.argv[3]
    format_ = sys.argv[4]
    timestamps = sys.argv[5].lower() == "true"

    transcribe_file(input_path, output_dir, model, format_, timestamps)
