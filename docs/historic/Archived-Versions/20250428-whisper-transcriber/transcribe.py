import argparse
import os
import sys
import datetime
import whisper
from logger import get_job_logger

# --------------------------
# Tee class for stdout/stderr capture
# --------------------------
class Tee(object):
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()

# --------------------------
# Main transcription function
# --------------------------
def main():
    parser = argparse.ArgumentParser(description="Transcribe an audio file using Whisper.")
    parser.add_argument("--input", required=True, help="Path to input audio file")
    parser.add_argument("--model", default="base.en", help="Model size to use (tiny, base, small, medium, large)")
    parser.add_argument("--job_id", required=True, help="Unique Job ID for logging")
    args = parser.parse_args()

    input_file = args.input
    model_size = args.model
    job_id = args.job_id

    # Setup structured logger
    logger = get_job_logger(job_id)

    # Setup tee log for stdout/stderr capture
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join("logs", f"transcribe_stdout_{job_id}_{timestamp}.log")
    os.makedirs("logs", exist_ok=True)
    f = open(log_path, "w")
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Tee(sys.stdout, f)
    sys.stderr = Tee(sys.stderr, f)

    try:
        logger.info(f"Starting transcription job: JobID={job_id}, InputFile={input_file}, ModelSize={model_size}")

        # Load model
        local_model_path = os.path.join("models", model_size, f"{model_size}.pt")
        if os.path.exists(local_model_path):
            logger.info(f"Loading local model from {local_model_path}")
            model = whisper.load_model(local_model_path)
        else:
            logger.info(f"Local model not found. Downloading model {model_size} via whisper.load_model.")
            model = whisper.load_model(model_size)

        # Transcribe
        logger.info("Starting audio transcription...")
        result = model.transcribe(input_file)

        # Prepare transcript output
        transcript_dir = "transcripts"
        os.makedirs(transcript_dir, exist_ok=True)
        base_filename = os.path.splitext(os.path.basename(input_file))[0]
        transcript_path = os.path.join(transcript_dir, f"{base_filename}_transcript.txt")

        logger.info(f"Saving transcript to {transcript_path}")
        with open(transcript_path, "w", encoding="utf-8") as out_file:
            if "segments" in result and result["segments"] is not None:
                for segment in result["segments"]:
                    start = str(datetime.timedelta(seconds=int(segment["start"])))
                    text = segment["text"].strip()
                    out_file.write(f"[{start}] {text}\n")
            else:
                out_file.write(result["text"].strip() + "\n")

        # Finish
        detected_language = result.get("language", "unknown")
        logger.info(f"Transcription completed successfully. Detected language: {detected_language}")

    except Exception as e:
        logger.exception(f"Exception occurred during transcription: {str(e)}")
        raise

    finally:
        # Restore original stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        f.close()

# --------------------------
# App Runner
# --------------------------
if __name__ == "__main__":
    main()
