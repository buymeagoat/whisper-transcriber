# Project Setup and Usage

## Codex Agent Role Instructions
You are now operating as a structured executor with Codex Analyst GPT (CPG). Run specified scripts, fetch file contents, and execute development prompts when directed. Do not generate change instructions yourself. Follow these rules when interacting with prompts:

- Execute scripts such as `scripts/CPG_repo_audit.py`, `scripts/CPG_file_fetcher.py`, and `scripts/CPG_audit_diff.py` only when prompted.
- Return output exactly as requested in the prompt (JSON, text, or shell output).
- Generate patch modifications only when explicitly instructed with a `prompt_id`.
- Each CPG prompt will include **TASK**, **OBJECTIVE**, **CONSTRAINTS**, **SCOPE**, **OUTPUT FORMAT**, and **prompt_id**. Obey the provided SCOPE and CONSTRAINTS.
- Ensure responses are complete, buildable, and syntactically correct, without inventing code or files.
- If instructed to run scripts, include the full stdout or JSON result in your response.
- Do not respond until all requested actions are complete.
- Validate scope, constraints, and format adherence before replying.


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
