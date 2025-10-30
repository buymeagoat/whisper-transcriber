# Operations Guide

## Structured Logging

The FastAPI application emits structured JSON logs via
`api/utils/logger.py`. Each event includes the following fields:

| Field | Description |
| --- | --- |
| `timestamp` | UTC ISO-8601 timestamp when the event was created. |
| `level` | Log severity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `logger` | Fully qualified logger name (e.g., `access`, `whisper_api`). |
| `message` | Primary log message after sensitive values are redacted. |
| `request_id` | Correlation identifier propagated across a request lifecycle. |
| `module` | Python module that emitted the log entry. |
| `function` | Function that created the log entry. |
| `line` | Source line number of the log statement. |
| `process_id` | Operating system process identifier. |
| `thread_id` | Thread identifier inside the process. |
| `extra` | Optional dictionary with domain-specific context (only present when additional metadata is provided). |
| `exception` | Stack trace rendered when an exception is captured. |

> **Note:** The optional Celery worker defined in `api/worker.py` uses the
> default Python logging formatter. Enable JSON logging there by importing
> `api.utils.logger.get_system_logger` if you extend the worker with
> production workloads.

### Sample log entry

```json
{
  "timestamp": "2024-07-12T10:13:45.123456Z",
  "level": "INFO",
  "logger": "access",
  "message": "{\"timestamp\": \"2024-07-12 10:13:45\", \"client_ip\": \"192.0.2.10\", \"method\": \"GET\", \"url\": \"https://api.example.com/health/readyz\", \"path\": \"/health/readyz\", \"query_params\": {}, \"status_code\": 200, \"response_time_ms\": 42.71, \"user_agent\": \"curl/8.0.1\", \"content_length\": \"128\", \"request_id\": \"fa1b2c3d4e5f6789\"}",
  "request_id": "fa1b2c3d4e5f6789",
  "module": "access_log",
  "function": "dispatch",
  "line": 74,
  "process_id": 4120,
  "thread_id": 139912345678912
}
```

Use the `request_id` field to correlate application logs with API access
logs, background workers, and audit trails when troubleshooting incidents.

## Alerting Examples

Leverage the exported Prometheus metrics to define RED/USE style alerts.

### API error rate spike

Trigger when 5xx responses exceed 1% of traffic for five minutes:

```promql
sum(rate(whisper_http_request_errors_total{status_code=~"5.."}[5m]))
  /
sum(rate(whisper_http_requests_total[5m])) > 0.01
```

### Slow request detection

Alert when median latency for the transcript creation endpoint remains above
three seconds:

```promql
histogram_quantile(
  0.5,
  sum(rate(whisper_http_request_duration_seconds_bucket{endpoint="/jobs"}[5m])) by (le)
) > 3
```

### Redis saturation warning

Notify when Redis connections approach exhaustion:

```promql
whisper_resource_saturation_ratio{resource="redis_connections"} > 0.8
```

These queries assume the `/metrics/` endpoint is scraped at regular
intervals. The route does not enforce authentication, so apply network
policies (IP allowlists, private ingress) when deploying to production.
Adjust thresholds to match your environment and error budgets.
