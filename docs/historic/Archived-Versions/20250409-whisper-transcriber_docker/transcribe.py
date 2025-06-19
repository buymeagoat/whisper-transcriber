import whisper
import os
import datetime

def run_transcription(
    job_id,
    filepath,
    model,
    format_,
    use_timestamps,
    segment_mode,
    start,
    end,
    output_dir,
    log_dir,
    status_dict,
    progress_dict,
    cancelled_dict
):
    log_path = os.path.join(log_dir, f"{job_id}.log")

    def log(message):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"{timestamp} {message}\n")
            log_file.flush()

    try:
        log("Loading model...")
        status_dict[job_id] = "Loading model..."
        whisper_model = whisper.load_model(model)
        log("Model loaded.")

        # Load and optionally slice audio
        if segment_mode == "partial" and start is not None and end is not None and end > start:
            log(f"Transcribing segment: {start}–{end} sec")
            audio = whisper.load_audio(filepath)
            segment = audio[int(start * whisper.audio.SAMPLE_RATE):int(end * whisper.audio.SAMPLE_RATE)]
            result = whisper_model.transcribe(audio=segment, task="transcribe")
        else:
            log("Transcribing full audio file")
            result = whisper_model.transcribe(filepath, task="transcribe")
        log(f"Returned keys: {list(result.keys())}")
        log(f"Segment count: {len(result.get('segments', []))}")
        log("Whisper transcription returned.")

        base_filename = os.path.splitext(os.path.basename(filepath))[0]
        transcript_path = os.path.join(output_dir, f"{base_filename}_{job_id}.{format_}")

        segments = result.get("segments", [])
        total = len(segments)
        progress_dict[job_id] = {"current": 0, "total": total}

        log(f"Detected language: {result.get('language', 'Unknown')}")
        log(f"Total segments: {total}")
        log("")

        with open(transcript_path, "w", encoding="utf-8") as out:
            for i, segment in enumerate(segments, 1):
                if cancelled_dict.get(job_id):
                    log("❌ Transcription cancelled by user.")
                    status_dict[job_id] = "Cancelled"
                    return

                start_t = segment["start"]
                end_t = segment["end"]
                text = segment["text"].strip()

                # Log full transcript line
                log(f"[{start_t:.3f} --> {end_t:.3f}]  {text}")
                log(f"Segment {i}/{total}")
                log("")

                progress_dict[job_id]["current"] = i
                status_dict[job_id] = f"Segment {i}/{total}: {text[:60]}..."

                if format_ == "txt":
                    out.write(text + "\n")
                elif format_ in ("srt", "vtt"):
                    def fmt(ts):
                        h = int(ts // 3600)
                        m = int((ts % 3600) // 60)
                        s = int(ts % 60)
                        ms = int((ts - int(ts)) * 1000)
                        return f"{h:02}:{m:02}:{s:02},{ms:03}"

                    if format_ == "srt":
                        out.write(f"{i}\n{fmt(start_t)} --> {fmt(end_t)}\n{text}\n\n")
                    elif format_ == "vtt":
                        out.write(f"{fmt(start_t).replace(',', '.')} --> {fmt(end_t).replace(',', '.')}\n{text}\n\n")

        status_dict[job_id] = f"Done: {transcript_path}"
        log("✅ Transcription complete.")

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        status_dict[job_id] = error_msg
        log(error_msg)
