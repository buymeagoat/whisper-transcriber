# Performance and Capacity Planning

This document captures the current performance baselines for Whisper Transcriber and provides
practical tuning advice for the nightly load test as well as production deployments.

## Baseline metrics

| Metric | Baseline | Notes |
| --- | --- | --- |
| Avg request latency | 1.85 s | Captured with the k6 workload described in `perf/transcription_scenario.js`. |
| P95 request latency | 4.20 s | Includes job submission and status polling traffic. |
| Avg end-to-end transcription latency | 46.5 s | Time from upload until transcript is returned. |
| P95 end-to-end transcription latency | 88.4 s | Higher tail due to model warm-up or queue wait. |
| Success rate | 98% | Accounts for jobs that finish before the polling limit is reached. |

Nightly CI fails if any metric drifts more than the tolerance percentages stored in
`perf/baseline.json`.

## CPU sizing

- **API container**: 2 vCPUs ensure FastAPI request handling and polling remains responsive.
  Increase to 4 vCPUs when arrival rate exceeds 6 jobs/sec to avoid back-pressure from upload
  processing.
- **Worker container**: Allocate at least 4 vCPUs for the `tiny` or `base` Whisper models. For
  medium and large models target 8 vCPUs to keep end-to-end latency under 2 minutes.
- Enable CPU pinning when running multiple workers on the same host to minimize context switch
  overhead.

## GPU guidance

- GPU acceleration is optional but recommended for large models or multilingual workloads.
- When provisioning NVIDIA GPUs, set `WHISPER_INFERENCE_DEVICE=cuda` in the worker environment and
  ensure the Docker runtime exposes the device (`--gpus all`).
- Use one worker process per GPU. Scale horizontally by adding workers rather than sharing a device
  across processes; Whisper benefits from exclusive access.

## Queue depth and concurrency

- The default deployment executes transcriptions through the in-process
  `ThreadJobQueue`. Throughput therefore depends on how many concurrent
  uploads the API process can service. Increase the FastAPI worker count
  when you expect sustained concurrency above a handful of jobs.
- Teams that opt into the optional Celery worker should start with
  `WORKER_CONCURRENCY=vCPUs/2` and increase after observing CPU or GPU
  utilisation. Celery currently exposes only a health-check task; wire in a
  Celery-based transcription task before switching the API away from the
  thread queue.
- Increase `MAX_POLLS` or `POLL_INTERVAL` in the k6 scenario for
  environments with higher latency to avoid classifying long-running jobs
  as failures.

## Additional tips

- Warm the Whisper model before opening traffic. Trigger a single transcription during deploys to
  load weights into memory and avoid a cold-start spike.
- Keep the encoded sample in `perf/assets/sample.wav.b64` small to maintain fast regression
  coverage. Replace it only with similarly short clips.
- When tuning thresholds, adjust the baseline metrics and tolerances together so the nightly check
  represents the new normal.
