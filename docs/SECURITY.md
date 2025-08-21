# Security Guide

This document outlines how to deploy and operate Whisper Transcriber securely.

## Repository Security Governance
All security practices and standards are defined in [docs/OPERATING_BLUEPRINT.md](docs/OPERATING_BLUEPRINT.md) and enforced by CI/CD and Copilot automation.

## Overview
- API authentication uses JWT tokens with role-based access control.
- Admin routes and log retrieval require an `admin` role.
- Access logs and system logs are stored on disk with rotation.

## Secrets Handling
- `SECRET_KEY` is required for signing JWT tokens.
- Generate a key with `python -c "import secrets,sys;sys.stdout.write(secrets.token_hex(32))"`.
- Store the value in `.env` or mount it as `/run/secrets/secret_key` when building containers.
- Prefer BuildKit secrets or mounted volumes instead of passing secrets via build arguments.
- Rotate the key periodically and recreate any running containers after rotation.

## Network Hardening
- Place a reverse proxy such as Nginx or Caddy in front of the API and terminate TLS there.
- Restrict access to `/admin`, `/metrics`, and `/logs` to trusted networks or VPN clients only.
- Set `CORS_ORIGINS` explicitly in production to limit allowed domains.

## Authentication & Authorization
- Create strong passwords for all user accounts.
- Only accounts with the `admin` role can access management routes.
- Include the JWT token as `Authorization: Bearer <token>` for each request.

## Container Security
- Containers run as non-root where possible; avoid mounting sensitive host paths.
- Rotate Docker volumes and logs regularly to prevent data accumulation.
- Use the provided scripts to build images with BuildKit secrets and verify dependencies.

## Vulnerability Monitoring
- Periodically run `pip list --outdated` and `npm audit` to identify vulnerable packages.
- Scan container images with tools like `trivy` or `grype` before deployment.

## Reporting Vulnerabilities
Please report security issues by opening an issue in the repository or emailing `security@example.com`.

