# Changelog

## [Unreleased]
### Added
- `whisper_build.sh` now automatically populates pip and apt caches before npm cache and build steps.

### Changed
- Build process is more robust for offline and online builds.

### Fixed
- Ensures all cache directories are updated before Docker build starts.
