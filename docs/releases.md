# Release Management

This guide describes how the Whisper Transcriber maintainers plan, cut, and deliver releases.

## Versioning Policy

We follow [Semantic Versioning](https://semver.org/) and document every user-facing change in [CHANGELOG.md](../CHANGELOG.md). Bump the version according to the impact of the release:

- **MAJOR**: incompatible API or database changes.
- **MINOR**: backwards-compatible feature additions.
- **PATCH**: backwards-compatible bug fixes and maintenance updates.

## Preparing a Release

1. Review open issues and pull requests for blockers.
2. Confirm the `Unreleased` section of the changelog accurately reflects the work delivered since the last tag.
3. Update deployment infrastructure (migrations, secrets, configs) if required by the release.
4. Ensure CI is green on the commit you plan to tag.

## Tagging a Release

1. Create a release branch from `main` (for example, `release/v1.2.0`).
2. Update version strings in application metadata as needed (Docker labels, environment defaults, etc.).
3. Move entries from the `Unreleased` section of the changelog into a new section headed `## [vX.Y.Z] - YYYY-MM-DD`.
4. Open a pull request for the release branch and obtain approval from another maintainer.
5. Once merged, tag the release from the merge commit: `git tag -s vX.Y.Z && git push origin vX.Y.Z`.
6. Draft release notes on GitHub using the changelog entry as the source of truth.

## Publishing Artifacts

1. Build the production Docker image with the `production` target.
2. Tag the image with both `vX.Y.Z` and `latest` (if appropriate) and push to the container registry.
3. Publish the GitHub Release with links to the changelog and Docker image digest.
4. Notify stakeholders on the engineering and support channels with a summary of the release.

## Rollback Procedure

1. Identify the last known-good release tag (for example, `vX.Y.(Z-1)`).
2. Re-deploy infrastructure using the corresponding Docker image digest or Git tag.
3. Communicate the rollback to stakeholders and incident response channels.
4. Open a post-incident issue capturing impact, root cause, and remediation tasks.
5. Patch forward on `main` with fixes and schedule a follow-up release once stability is restored.
