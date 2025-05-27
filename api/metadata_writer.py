# api/metadata_writer.py

import os
import json
import re
import argparse
import sqlite3
from datetime import datetime

TRANSCRIPTS_DIR = "transcripts"
DB_PATH = "jobs.db"

def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip())

def compute_wpm(text, duration_sec):
    word_count = len(text.split())
    return word_count / (duration_sec / 60) if duration_sec > 0 else 0

def extract_keywords(text, top_n=5):
    words = re.findall(r'\b\w+\b', text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    stopwords = set(["the", "and", "to", "of", "a", "in", "it", "is", "that", "on", "for", "with", "as", "this"])
    keywords = [w for w in sorted(freq, key=freq.get, reverse=True) if w not in stopwords]
    return keywords[:top_n]

def run_metadata_writer(job_id, transcript_txt_path, duration_sec, sample_rate):
    if not os.path.exists(transcript_txt_path):
        raise FileNotFoundError(f"Transcript not found at {transcript_txt_path}")

    # Load transcript text
    with open(transcript_txt_path, "r", encoding="utf-8") as f:
        text = clean_text(f.read())

    lang = "en"  # Placeholder; real detection may come from Whisper JSON
    tokens = len(text.split())
    wpm = compute_wpm(text, duration_sec)
    abstract = text[:500] + "..." if len(text) > 500 else text
    keywords = extract_keywords(text)
    vector_id = None  # Future vector embedding hook

    job_dir = os.path.join(TRANSCRIPTS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    # Write Markdown version
    md_path = os.path.join(job_dir, "transcript.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Transcript\n\n{abstract}\n\n## Keywords\n- " + "\n- ".join(keywords))

    # Write metadata.json
    meta_json = {
        "job_id": job_id,
        "lang": lang,
        "tokens": tokens,
        "duration": duration_sec,
        "wpm": wpm,
        "abstract": abstract,
        "keywords": keywords,
        "vector_id": vector_id
    }
    json_path = os.path.join(job_dir, "metadata.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta_json, f, indent=2)

    # Insert into metadata table
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO metadata (job_id, lang, tokens, duration, abstract, keywords, vector_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (job_id, lang, tokens, duration_sec, abstract, ", ".join(keywords), vector_id))
    conn.commit()
    conn.close()

    print(f"[✓] Metadata written for job {job_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate metadata for a transcript")
    parser.add_argument("--job_id", required=True, help="Job ID")
    parser.add_argument("--transcript", required=True, help="Path to raw transcript text")
    parser.add_argument("--duration", type=float, required=True, help="Duration in seconds")
    parser.add_argument("--sample_rate", type=int, required=True, help="Sample rate (not used yet)")

    args = parser.parse_args()
    run_metadata_writer(args.job_id, args.transcript, args.duration, args.sample_rate)
