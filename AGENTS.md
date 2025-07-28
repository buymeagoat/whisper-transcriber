# Project Setup and Usage

## Setup
- Run `pip install -r requirements.txt` to install Python dependencies.
- From the `frontend` directory run `npm install` to install Node dependencies.
- Install development dependencies with `pip install -r requirements-dev.txt` before running tests.
- Copy `.env.example` to `.env` and set `SECRET_KEY`.

## Running
- Start the FastAPI backend with `uvicorn api.main:app`.
- Build the React frontend with `npm run build`.
- Run `scripts/start_containers.sh` or `docker compose up --build` to start the stack.
- `scripts/run_tests.sh` runs backend and frontend tests.

## Notes
- Use `black .` to format the codebase.
- For the complete walkthrough see [docs/help.md](docs/help.md).
