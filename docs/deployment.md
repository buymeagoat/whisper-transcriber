# Deployment Guide

## Whisper Model Assets

The Celery worker requires an OpenAI Whisper checkpoint (`*.pt`) to exist in
`storage.models_dir` before jobs can be processed. The deployment flow now uses
`api.app_worker.bootstrap_model_assets()` to guarantee a checkpoint is present
and fails fast when the directory is empty.

### Bootstrap Sources

`bootstrap_model_assets()` supports multiple sourcing strategies:

1. **Direct file path** – set `WHISPER_MODEL_PATH` to the absolute path of a
   checkpoint file (or directory containing checkpoints) that should be copied
   into `storage.models_dir` at startup.
2. **Download URL** – set `WHISPER_MODEL_DOWNLOAD_URL` (and optionally
   `WHISPER_MODEL_NAME`) to fetch a checkpoint during deployment. `file://`
   URLs are supported for air-gapped environments.
3. **Known OpenAI releases** – when no environment overrides are provided the
   bootstrapper downloads the official release that matches
   `WHISPER_MODEL_NAME` (defaults to `small`).

The routine raises a `WhisperModelBootstrapError` if no checkpoints are found
so that worker startup cannot proceed silently with an empty models directory.

### Runtime Integration

The FastAPI service calls `bootstrap_model_assets()` from the application
lifespan defined in `api.main`. This guarantees the models directory is
validated before the API begins accepting requests. The Celery worker performs
the same validation inside `api.services.app_worker.transcribe_audio` so queue
tasks fail fast if the assets are unavailable.

When orchestrating the application outside containers, ensure both the API
process (for example `uvicorn api.main:app --host 0.0.0.0 --port 8001`) and the
Celery worker (`celery -A api.worker.celery_app worker -l info`) run under the
same deployment root so they share the `storage.models_dir` path.

### Verifying Model Availability

Run the automated integration test after updating deployment configuration:

```bash
pytest tests/integration/test_worker_model_loading.py
```

The test provisions a fixture checkpoint, executes the worker task, and asserts
that `transcribe_audio` loads the correct file. Mark the remediation finding as
**Complete** only when this test (and the broader suite) passes. Until then,
track the status as **Complete-Pending Tests** in the remediation log.
