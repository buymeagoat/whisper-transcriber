# orchestrate.py

import os
import time
import argparse
import requests
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{API_URL}/jobs"
STATUS_ENDPOINT = f"{API_URL}/jobs"

def is_audio_file(path):
    return path.suffix.lower() in [".mp3", ".wav", ".m4a", ".flac", ".ogg"]

def submit_job(file_path, model):
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "audio/mpeg")}
            data = {"model": model}
            res = requests.post(UPLOAD_ENDPOINT, files=files, data=data)
            if res.status_code == 200:
                job_id = res.json().get("job_id")
                print(f"[✓] Submitted: {file_path.name} → job_id={job_id}")
                return job_id
            else:
                print(f"[!] Failed to submit {file_path.name}: {res.status_code}")
    except Exception as e:
        print(f"[!] Error submitting {file_path.name}: {e}")
    return None

def watch_jobs(job_ids):
    remaining = set(job_ids)
    while remaining:
        time.sleep(5)
        try:
            res = requests.get(STATUS_ENDPOINT)
            statuses = {job["id"]: job["status"] for job in res.json()}
            for job_id in list(remaining):
                if job_id in statuses and statuses[job_id] in ["completed", "failed"]:
                    print(f"[•] Job {job_id} finished with status: {statuses[job_id]}")
                    remaining.remove(job_id)
        except Exception as e:
            print(f"[!] Error checking job status: {e}")

def main(args):
    input_path = Path(args.input_dir)
    audio_files = [f for f in input_path.iterdir() if is_audio_file(f)]

    print(f"[~] Found {len(audio_files)} audio files in {input_path}")

    job_ids = []

    if args.concurrency > 1:
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = [executor.submit(submit_job, f, args.model) for f in audio_files]
            for fut in futures:
                job_id = fut.result()
                if job_id:
                    job_ids.append(job_id)
    else:
        for f in audio_files:
            job_id = submit_job(f, args.model)
            if job_id:
                job_ids.append(job_id)

    print(f"[✓] Submitted {len(job_ids)} jobs.")

    if args.watch:
        print("[~] Watching for completion...")
        watch_jobs(job_ids)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch submit audio files to Whisper Transcriber")
    parser.add_argument("--input_dir", required=True, help="Directory with audio files to transcribe")
    parser.add_argument("--model", default="tiny", help="Whisper model to use")
    parser.add_argument("--concurrency", type=int, default=1, help="How many files to upload in parallel")
    parser.add_argument("--watch", action="store_true", help="Wait for all jobs to finish")
    args = parser.parse_args()
    main(args)
