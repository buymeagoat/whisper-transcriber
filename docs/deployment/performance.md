# Performance Guidelines

This page outlines resource planning and scaling considerations when running
Whisper Transcriber. Values assume CPU‑only inference using the
OpenAI Whisper models distributed with the project.

## Resource Requirements

| Whisper Model | RAM Needed (min) | Est. Runtime per Minute |
|--------------|-----------------|-------------------------|
| tiny         | ~1&nbsp;GB      | ~0.5× real time         |
| base         | ~2&nbsp;GB      | ~0.7× real time         |
| small        | ~3&nbsp;GB      | ~1× real time           |
| medium       | ~5&nbsp;GB      | ~1.2× real time         |
| large-v3     | 8&nbsp;GB+      | ~1.5× real time         |

Memory usage grows with the model size and the number of concurrent jobs.
CPU speed largely determines how quickly audio is processed. Slow disks can
bottleneck when reading uploads or writing transcripts.

## Scaling Behavior

The `MAX_CONCURRENT_JOBS` setting limits how many jobs run in parallel.
With the default thread queue the API dispatches work to a pool of worker
threads. Setting a higher value increases CPU and memory usage but allows more
simultaneous transcriptions. When `JOB_QUEUE_BACKEND=broker` the API pushes
jobs to RabbitMQ and a Celery worker processes them. Broker mode introduces
message overhead but enables horizontal scaling and dedicated worker nodes.

## Disk Usage Patterns

Each uploaded file is stored under `uploads/` until deleted. The generated
transcript and metadata reside in `transcripts/{job_id}/`. Expect transcript
files to be a fraction of the original audio size (roughly 5&nbsp;–&nbsp;10%).
Logs for each job are written under `logs/` and are rotated when they exceed
`LOG_MAX_BYTES` with `LOG_BACKUP_COUNT` backups retained.
Old transcripts may be pruned automatically when `CLEANUP_ENABLED=true`; the
retention period is controlled by `CLEANUP_DAYS`.

## Cloud Backends

The local storage backend keeps all uploads and transcripts on disk. When
`STORAGE_BACKEND=cloud` the same directories act as a cache and objects are
fetched from S3 on demand. Cloud storage trades local disk usage for higher
latency during transcript downloads and log retrieval.

## Recommendations

- **Development**: 2‑core CPU, 4&nbsp;GB RAM and at least 10&nbsp;GB of free disk
  space. Swap space prevents crashes when memory spikes.
- **Production**: 4 or more CPU cores, 8&nbsp;GB+ RAM and SSD storage for
  reliable performance. Increase `MAX_CONCURRENT_JOBS` cautiously and monitor
  CPU, memory and disk usage via `/admin/stats`.

Proper resource planning ensures responsive transcripts and prevents workers
from being overwhelmed during heavy workloads.
