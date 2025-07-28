# Onboarding Guide

👤 Target Audience: New Developers

This page helps new contributors get a working environment quickly.

## What to Read First
- [README.md](../README.md) for project overview and environment variables.
- [help.md](help.md) for installation steps.
- [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards and workflow.
- [testing_strategy.md](testing_strategy.md) for how tests are executed.

## How to Get a Working Environment
1. Clone the repository and install Python requirements:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
2. Install Node.js 18+ and build the frontend:
   ```bash
   cd frontend && npm install && npm run build && cd ..
   ```
3. Copy `.env.example` to `.env` and set `SECRET_KEY`.
4. Start the stack in Docker:
   ```bash
   sudo scripts/start_containers.sh
   ```

## Setup Checklist
- [ ] Python dependencies installed
- [ ] Node modules installed
- [ ] `.env` created with a unique `SECRET_KEY`
- [ ] Docker Compose stack running
- [ ] At least one Whisper model placed in `models/`

## Optional Tools
- **IDE plugins** – Configure Black and Prettier formatting on save.
- **Test runners** – Use `scripts/run_tests.sh` for full test suite or `pytest` for specific files.
- **Git hooks** – Add a pre-commit hook to run `black` and `pytest` automatically.

Need more help? See [help.md](help.md) or reach out via repository issues.
