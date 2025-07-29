# Scripts Reference

👤 Target Audience: Developers

The table below summarizes the helper scripts found under `/scripts`.

| Script | Description | Flags / Env Vars | Example | Notes |
| --- | --- | --- | --- | --- |
| `check_env.sh` | Verifies host tools and base image versions before builds | `ALLOW_OS_MISMATCH`, `ALLOW_DIGEST_MISMATCH` | `scripts/check_env.sh` | Fails if required cache files or Docker are missing |
| `diagnose_containers.sh` | Prints container status and recent logs for troubleshooting | `LOG_LINES` | `scripts/diagnose_containers.sh` | Useful when containers fail to start |
| `check_cache_env.sh` | Displays how CACHE_DIR resolves on the current host | `CI` | `scripts/check_cache_env.sh` | Helps verify WSL overrides |
| `docker-entrypoint.sh` | Entry script used inside containers to start the API or worker | `SERVICE_TYPE`, `BROKER_PING_TIMEOUT` | Invoked automatically by Docker | Creates log under `/app/logs/entrypoint.log` |
| `whisper_build.sh` | Unified build and startup script | `--full` `--offline` `--purge-cache` `--verify-sources` | `sudo scripts/whisper_build.sh` | Logs to `logs/whisper_build.log`; sets `CACHE_DIR` automatically under WSL |
| `healthcheck.sh` | Container health probe used by Docker | `SERVICE_TYPE`, `VITE_API_HOST` | Invoked by Docker healthcheck | Exits non-zero when API or worker is unhealthy |
| `run_backend_tests.sh` | Runs Python unit tests inside the API container | `VITE_API_HOST` | `scripts/run_backend_tests.sh` | Requires Docker Compose stack to be running |
| `run_tests.sh` | Executes backend tests, frontend unit tests and Cypress e2e tests | `--backend` `--frontend` `--cypress` | `scripts/run_tests.sh --backend` | Logs saved to `logs/full_test.log` |
| `server_entry.py` | Python entry point for local development | `PORT` | `python scripts/server_entry.py` | Starts Uvicorn with settings from `.env` |
| `shared_checks.sh` | Library of common functions used by other scripts | N/A | Sourced by other scripts | Not executed directly |
| `start_containers.sh` | Deprecated wrapper for `whisper_build.sh` | N/A | `scripts/start_containers.sh` | Redirects to new script |
| `update_images.sh` | Deprecated wrapper for `whisper_build.sh` | N/A | `scripts/update_images.sh` | Redirects to new script |
| `validate_manifest.sh` | Checks the cache manifest against local Docker images | `--summary` `--json` | `scripts/validate_manifest.sh --summary` | Detects mismatches between cached and installed versions |

## Environment-Sensitive Cache Pathing

Most build scripts rely on a common cache directory. By default `CACHE_DIR`
is `/tmp/docker_cache`. When the host is WSL, the scripts automatically
override this path to `/mnt/wsl/shared/docker_cache` and print a warning.
Setting `CACHE_DIR` manually is ignored under WSL so the cache always resides
in the shared location.<!-- # Codex-verified: CACHE_DIR documentation matches set_cache_dir -->

