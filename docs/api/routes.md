# Whisper Transcriber API Routes

This document captures the externally exposed HTTP routes that are covered by automated
integration tests. Each section links to the implementation module and the smoke test that
exercises the behaviour.

## `GET /health`
- **Purpose:** Application and database health probe used by load balancers.
- **Implementation:** [`api/main.py::health_check`](../../api/main.py)
- **Verification:** [`tests/test_api_smoke.py::test_health_endpoint_reports_ok`](../../tests/test_api_smoke.py)
- **Response:**
  ```json
  {"status": "ok"}
  ```

## `POST /auth/login`
- **Purpose:** Exchange the administrator bootstrap credentials for a bearer token and session cookie.
- **Implementation:** [`api/routes/auth.py::login`](../../api/routes/auth.py)
- **Verification:** [`tests/test_api_smoke.py::test_admin_login_returns_token_and_cookie`](../../tests/test_api_smoke.py)
- **Request Body:**
  ```json
  {"username": "admin", "password": "<bootstrap-password>"}
  ```
- **Response:**
  ```json
  {
    "access_token": "<jwt>",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```

## `POST /change-password`
- **Purpose:** Allow the authenticated administrator to rotate the deployment password.
- **Implementation:** [`api/routes/auth.py::change_password`](../../api/routes/auth.py)
- **Verification:** [`tests/test_security.py::TestPasswordSecurity::test_password_change_requires_current`](../../tests/test_security.py)
- **Request Body:**
  ```json
  {
    "current_password": "super-secret-password-!123",
    "new_password": "RotateMeNow!456"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Password changed successfully"
  }
  ```

## `POST /jobs/`
- **Purpose:** Upload an audio file and enqueue a transcription job on the in-process thread queue.
- **Implementation:** [`api/routes/jobs.py::create_job`](../../api/routes/jobs.py)
- **Verification:** [`tests/test_api_smoke.py::test_job_upload_and_worker_status_flow`](../../tests/test_api_smoke.py)
- **Request:** `multipart/form-data` containing the audio file, optional `model`, and optional `language` fields.
- **Response:**
  ```json
  {
    "job_id": "<uuid>",
    "status": "queued",
    "message": "Job created successfully",
    "queue_job_id": "queue-<uuid>"
  }
  ```

## `GET /jobs/{job_id}`
- **Purpose:** Retrieve job metadata, including queue status and transcript if available.
- **Implementation:** [`api/routes/jobs.py::get_job`](../../api/routes/jobs.py)
- **Verification:** [`tests/test_api_smoke.py::test_job_upload_and_worker_status_flow`](../../tests/test_api_smoke.py)

## `GET /jobs/`
- **Purpose:** Paginated list of transcription jobs.
- **Implementation:** [`api/routes/jobs.py::list_jobs`](../../api/routes/jobs.py)
- **Verification:** [`tests/test_api_smoke.py::test_job_listing_includes_recent_submission`](../../tests/test_api_smoke.py)
- **Query Parameters:** `skip` (default `0`), `limit` (default `100`).

## `GET /metrics/`
- **Purpose:** Expose Prometheus metrics (RED/USE series and Redis cache statistics).
- **Implementation:** [`api/routes/metrics.py::get_metrics`](../../api/routes/metrics.py)
- **Verification:** [`tests/test_api_smoke.py::test_prometheus_metrics_endpoint`](../../tests/test_api_smoke.py)
- **Response:** Text formatted per the Prometheus exposition format. Example snippets:
  ```
  # HELP whisper_http_requests_total Total number of HTTP requests processed
  # TYPE whisper_http_requests_total counter
  whisper_http_requests_total{method="GET",endpoint="/health",status_code="200"} 1.0
  ```
