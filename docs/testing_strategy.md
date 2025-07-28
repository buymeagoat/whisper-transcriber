# Testing Strategy

This document describes how tests are organized and executed within the project
along with recommendations for future continuous integration.

## Test Types

- **Backend unit tests** – located under `tests/` and run with
  `scripts/run_backend_tests.sh`. These tests exercise API endpoints,
  database interactions and worker logic.
- **End-to-end tests** – `scripts/run_tests.sh` runs backend tests plus
  frontend unit tests and Cypress workflows for the React UI.
- **Manual validation** – developers may issue `curl` requests to the API or
  interact with the web interface to verify behaviour that is difficult to
  automate.

## Test Execution

Both helper scripts expect the Docker Compose stack to be running. They check
that the `api` service is healthy before invoking `pytest` or frontend tools.
Output is written to log files:

- `logs/test.log` – results of `run_backend_tests.sh`
- `logs/full_test.log` – results of `run_tests.sh`

Keeping logs allows failures to be inspected after the fact. Tests should be
run in isolation with a fresh database to ensure reproducibility.

## Expected Outcomes

A successful run exits with code `0` and prints summaries for each phase.
Backend tests display a coverage report while frontend tests report completed
suites. If a container fails its health check or a service is unreachable the
scripts abort with an error message so issues can be diagnosed quickly.

## Coverage & Linting

Coverage tracking is currently limited to the backend via
`coverage run -m pytest`. Additional tools such as `pytest-cov`, `flake8` and
`black` are recommended for future automation. Frontend linting can be added
with ESLint.

## Future CI Integration

Placeholder workflows for CI (e.g. GitHub Actions) have not been added yet.
Pull requests should still run the provided scripts locally before merging.
Future CI pipelines can invoke the same scripts to validate new contributions.
