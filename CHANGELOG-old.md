# Changelog

## [Unreleased]
### Added
- `whisper_build.sh` now automatically populates pip and apt caches before npm cache and build steps.
- `whisper_build.sh` tracks pip cache failures and exits with code 88 after configurable retries.

- Audited and documented all required software packages and dependencies for build and cache integrity.
- Created `/logs/changes/change_20251003_000000_audit.md` summarizing all required Python, Node.js, npm, APT, Docker, and model dependencies.

### Changed
- Ensured all dependencies are explicitly listed and checked in build scripts and manifest validation.

### Risk & Rollback
- Risk: Low (documentation and audit only; no code changes yet)
- Rollback: Remove audit log and revert documentation changes if needed.

### Changed
- Build process is more robust for offline and online builds.
- Removed outdated workflow references from documentation and UI.

### Fixed
- Ensures all cache directories are updated before Docker build starts.

## Unreleased
### Fixed
- build(agentic): auto-populate missing wheels in cache/pip [20250822_155632]

## Unreleased
### Fixed
- build(agentic): auto-populate missing wheels in cache/pip [20250822_155909]

## Unreleased
### Fixed
- build(agentic): auto-populate missing wheels in cache/pip [20250822_160508]
