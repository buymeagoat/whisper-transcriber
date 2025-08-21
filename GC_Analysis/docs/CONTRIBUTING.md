# Contributing Guide

Thank you for wanting to contribute to Whisper Transcriber.
This document explains how to get a development environment running and the
conventions used for submitting changes.

## Repository Governance
All contributions must follow the standards and automation rules in [docs/OPERATING_BLUEPRINT.md](docs/OPERATING_BLUEPRINT.md).
- Use the PR template for all pull requests
- Update the changelog and per-change logs in `/logs/`
- Ensure tests and build logs are present before merging

## Getting Started

See [help.md](help.md) for a step-by-step setup guide. We recommend creating a
virtual environment and installing dependencies with:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
From the `frontend` directory install Node packages and build the UI:
```bash
npm install
npm run build
```
Copy `.env.example` to `.env` and set a unique `SECRET_KEY` before running any
commands.

## Style Guide

Run `black .` from the project root to format Python code. For the React
frontend use Prettier if available, otherwise follow common React formatting
conventions. Avoid very large pull requests; split changes into functional
units when possible.

## Testing

Execute `scripts/run_tests.sh` before submitting a pull request.
For backend-only changes run `scripts/run_backend_tests.sh`.
Test logs are written to `logs/*.log`.

## Submitting Changes

Fork the repository and create a branch for your work.
Commit messages should follow the conventional style such as
`fix:`, `feat:`, or `refactor:`.
Reference any relevant item in `future_updates.md` if applicable.
Describe what changed and why in the pull request body.
## Syncing Documentation

Update `README.md` and `design_scope.md` whenever environment variables, API
behavior, or architecture change. Keep `future_updates.md` current when new
features are added or plans shift.
