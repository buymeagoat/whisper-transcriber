# Automation Tasks

👤 Target Audience: Developers and Operators

The repository contains scripts and tooling for routine maintenance.

## Linting
- **Black** – Run `black .` before committing to format Python code.
- **Prettier** – Optional for the React frontend. Execute `npx prettier -w frontend/src`.

## Testing Automation
- `scripts/run_tests.sh` runs backend tests, frontend unit tests and Cypress suites.
- `scripts/run_backend_tests.sh` executes only the backend tests and verifies key API endpoints.

## Cache Validation
- `scripts/validate_manifest.sh` compares the staged dependency manifest against installed Docker images and cached packages.
- Cron jobs can periodically run this script and alert when mismatches occur.

## Optional Hooks
- Git pre-commit hook calling `black` and `pytest`.
- Documentation link checker or dependency audit tools can be integrated in the future.
