# Versioning Policy

👤 Target Audience: Developers, Release Managers

Whisper Transcriber follows [Semantic Versioning](https://semver.org/) and records all changes in [CHANGELOG.md](CHANGELOG.md).

## Strategy
- **Major** version increments for incompatible API changes or significant redesigns.
- **Minor** version increments for new features that remain backward compatible.
- **Patch** version increments for bug fixes and documentation updates only.

Releases are cut when notable features land or critical fixes are required. There is no fixed cadence, but versions are tagged at least once per quarter.

## Tagging Practice
- Git tags are created using the format `vMAJOR.MINOR.PATCH`, e.g. `v1.2.3`.
- Each tag corresponds to a section in `CHANGELOG.md`.
- Release assets are built from the tagged commit.

## Backward Compatibility
- Minor and patch releases maintain API compatibility with prior minor releases within the same major series.
- Deprecated CLI flags or environment variables remain for one major cycle before removal.
- Database migrations are included with each release so upgrades are one-way and non-destructive.

See the [README](../README.md) for environment variables and [CHANGELOG.md](CHANGELOG.md) for historical context.
