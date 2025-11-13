# Requirements Traceability

The table below links the critical behaviour of Whisper Transcriber to the
implementation modules, documentation, and automated tests that verify the
feature.

| Requirement | Description | Implementation / Documentation | Verification |
| --- | --- | --- | --- |
| R1 | Provide a `/health` probe that confirms the API and database are reachable. | `api/main.py::health_check`, [docs/api/routes.md](api/routes.md#get-health) | `tests/test_api_flow.py::test_health_endpoints_report_ready` |
| R2 | Allow the single administrator to exchange the bootstrap credentials for a JWT (multi-user login deferred). | `api/routes/auth.py::login`, [docs/api/routes.md](api/routes.md#post-authlogin) | `tests/test_api_flow.py::test_admin_login_returns_token_and_cookie` |
| R3 | Accept audio uploads and enqueue transcription jobs on the Celery-backed queue. | `api/routes/jobs.py::create_job`, [docs/api/routes.md](api/routes.md#post-jobs) | `tests/test_api_flow.py::test_job_upload_and_worker_status_flow` |
| R4 | Expose job detail and listing endpoints for workflow tracking. | `api/routes/jobs.py::get_job`, `api/routes/jobs.py::list_jobs`, [docs/api/routes.md](api/routes.md#get-jobsjob_id) | `tests/test_api_flow.py::test_job_upload_and_worker_status_flow`, `tests/test_api_flow.py::test_job_listing_includes_recent_submission` |
| R5 | Publish Prometheus metrics for infrastructure monitoring. | `api/routes/metrics.py::get_metrics`, [docs/api/routes.md](api/routes.md#get-metrics) | `tests/observability/test_metrics_endpoints.py::test_metrics_endpoint_returns_expected_series` |
| R6 | Keep the Celery worker pointed at Redis for asynchronous transcription. | `api/worker.py`, [README.md](../README.md#production-deployment) | `tests/test_celery_processing.py::test_celery_transcription_task_updates_job` |

