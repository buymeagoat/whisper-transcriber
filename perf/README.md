# Performance Testing

This directory contains the k6 scenario and tooling used to simulate a transcription workload
against the Whisper Transcriber API. The scenario emulates users uploading small audio samples
and waiting for the asynchronous job to finish.

## Files

- `transcription_scenario.js` – k6 script that submits uploads and polls job status until
  completion. Thresholds enforce the baseline service levels captured in `baseline.json`.
- `assets/sample.wav.b64` – Base64 encoded 1 second mono WAV sample used as the default upload
  payload.
- `baseline.json` – Recorded metrics from the reference environment along with the allowed drift
  per metric.
- `assert_perf.py` – Helper that compares the most recent k6 summary output against the baseline
  tolerances. This is executed during the nightly workflow.

## Running locally

1. Start the application stack (API + worker + Redis). A simple local setup uses three
  terminals (or background services):

  ```bash
  # Terminal 1 – Redis (or point to an existing instance)
  redis-server

  # Terminal 2 – FastAPI service
  source .venv/bin/activate
  uvicorn api.main:app --host 0.0.0.0 --port 8001

  # Terminal 3 – Celery worker
  source .venv/bin/activate
  celery -A api.worker.celery_app worker -l info
  ```

2. Run the load test. The script exports metrics to `perf/results/latest.json` for later
   comparison.

   ```bash
   k6 run \
     --summary-export perf/results/latest.json \
     --vus 6 \
     --duration 2m \
     perf/transcription_scenario.js
   ```

   Environment variables allow tailoring the workload:

   | Variable | Default | Description |
   | --- | --- | --- |
   | `BASE_URL` | `http://localhost:8001` | API base URL |
   | `ARRIVAL_RATE` | `3` | Target job submissions per second |
   | `DURATION` | `2m` | Total scenario runtime |
   | `PRE_ALLOCATED_VUS` | `4` | Initial virtual users |
   | `MAX_VUS` | `12` | Upper bound for automatically created users |
   | `WHISPER_MODEL` | `tiny` | Model to request per job |
   | `POLL_INTERVAL` | `1` | Seconds between status checks |
   | `MAX_POLLS` | `40` | Maximum polls before a job is considered failed |

3. Compare the results to the baseline:

   ```bash
   python perf/assert_perf.py perf/results/latest.json
   ```

## Updating the baseline

After infrastructure or tuning changes, capture a fresh summary export from k6, confirm the
numbers represent steady performance, and update `baseline.json`. Keep the tolerances realistic so
nightly runs catch regressions without flapping.
