# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Initial production hardening scaffolds for CI, security policy, and container fixes.
- Regression test ensuring legacy X-User-ID uploads remain accepted by the jobs API.
- Environment templates for local development and production deployments.
- Compatibility upload aliases so legacy `/upload` clients route through the
	jobs API without changes.
- Regression tests covering transcript retrieval and ownership enforcement.

### Changed
- Jobs authentication now resolves callers from JWT/cookie credentials and only
        honours the legacy header when `LEGACY_USER_HEADER_ENABLED=1`.
- Container tooling (Docker images, Compose manifests, ECS modules) remains in the
        tree but is disabled by default; set `CONTAINER_BUILDS_ENABLED=1` to reactivate
        the legacy pipeline.
- Chunked upload routing now accepts legacy `/uploads/init` and singular
	`/uploads/{session_id}/chunk/{n}` paths used by the current frontend.
- Transcript routes verified to serve owners while rejecting unauthorized
	access.
- Pinned librosa to 0.10.2.post1 so lazy_loader can locate package stubs during
	imports.
