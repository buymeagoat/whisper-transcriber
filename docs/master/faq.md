# Frequently Asked Questions

### Why does my job stay in "Queued"?
Jobs remain queued until a worker thread picks them up. If concurrency is limited or the worker crashed, the queue may stall. Check `/admin/concurrency` and the worker logs under `logs/`.

### How can I check logs if a job fails?
Each job writes a log file named `<job_id>.log` in the `logs/` directory. Use `/log/{job_id}` or stream live output from `/ws/logs/{job_id}`. For system-wide issues consult `system.log`.

### What’s the easiest way to debug a Docker build failure?
Run `scripts/whisper_build.sh` manually and inspect `logs/whisper_build.log`. The troubleshooting guide covers common errors.

### Can I run this without Docker?
Yes. Install the Python and Node dependencies, then start the API with `uvicorn api.main:app`. The frontend can be served by running `npm run build` and pointing a static server at `frontend/dist`.

### Why isn’t my frontend updating after rebuild?
Browsers often cache the old bundle. Clear the cache or append a query string to the URL. Ensure `npm run build` completed without errors.

### How do I test concurrency or simulate multiple jobs?
Use a loop or small script to POST multiple files to `/jobs`. You can adjust worker threads with `/admin/concurrency` to see how the system behaves under load.

### Where are my transcripts stored?
Transcripts live under `transcripts/{job_id}` by default or in your configured S3 bucket when `STORAGE_BACKEND=cloud`. See [file_retention.md](file_retention.md) for cleanup policies.
