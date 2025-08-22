# Changelog

## [Unreleased]
### Added
- `whisper_build.sh` now automatically populates pip and apt caches before npm cache and build steps.
- `whisper_build.sh` tracks pip cache failures and exits with code 88 after configurable retries.

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
