# Troubleshooting Guide

This page collects common errors and their resolutions to help users and
developers diagnose problems quickly. Logs are saved under `logs/` and the
`scripts/diagnose_containers.sh` script prints container status and build logs.

## Build Failures

- **Docker build fails at `dpkg -i /tmp/apt/*.deb`**
  - *Cause*: `cache/apt` is missing or does not match the Dockerfile base image.
  - *Fix*: Run `scripts/whisper_build.sh --purge-cache` or confirm the base image
    digest is correct.
- **`--network=host` not supported in Docker Compose**
  - *Cause*: Passing unsupported flags to the compose CLI.
- *Fix*: Remove the flag or avoid Compose when unsupported.
- **Docker build fails offline**
  - *Fix*: Execute `whisper_build.sh --offline` after staging dependencies so cached wheels and packages are available.
- **Whisper install fails with "No matching distribution found for wheel"**
  - *Fix*: Add `wheel` to `requirements-dev.txt` and rerun `whisper_build.sh --purge-cache`.
- **WSL cache issues**
  - *Fix*: When running under WSL the scripts automatically switch `CACHE_DIR`
    to `/mnt/wsl/shared/docker_cache`. Ensure this shared path exists and
    rerun `whisper_build.sh --purge-cache` if staging fails.<!-- # Codex: warns user when WSL override triggers -->

## Startup Errors

- **Application exits due to missing `SECRET_KEY`**
  - *Fix*: Generate a key and set it in `.env` or pass it via the helper script.
- **API fails to connect to the database**
  - *Fix*: Check `DB_URL`, wait for the database container to start and
    increase connection retries if needed.

## Job Failures

- **Jobs stuck in queued or processing**
  - *Fix*: Inspect worker logs and container health. Rebuild containers with
    `scripts/update_images.sh` if they are corrupted.
- **Transcript not generated**
  - *Cause*: Whisper model files are missing or corrupted.
  - *Fix*: Re-download `base.pt`, `large-v3.pt` and other models into `models/`.

## Web UI or Frontend Issues

- **Blank screen on load**
  - *Fix*: Rebuild the frontend with `npm run build` or pass `--force-frontend`
    to the build script.
- **Frontend build passes but web UI fails to load**
  - *Fix*: Check that `frontend/dist/index.html` exists. Run `npm run build` manually if needed.

## Security Misconfiguration

- **Open `/admin` routes in production**
  - *Fix*: Configure CORS correctly, run behind a reverse proxy and enforce
    admin roles.

## Potential Future Scenarios

These issues have not been observed yet but may occur based on the design:

- Cache checksum mismatch after a WSL reset
- Race conditions during parallel Docker builds
- Missing model support when the Whisper CLI updates
- React version upgrades breaking older UI components
