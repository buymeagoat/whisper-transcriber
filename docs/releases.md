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
2. Update version strings in application metadata as needed (for example `pyproject.toml`, CLI banners, or documentation snippets).
3. Move entries from the `Unreleased` section of the changelog into a new section headed `## [vX.Y.Z] - YYYY-MM-DD`.
4. Open a pull request for the release branch and obtain approval from another maintainer.
5. Once merged, tag the release from the merge commit: `git tag -s vX.Y.Z && git push origin vX.Y.Z`.
6. Draft release notes on GitHub using the changelog entry as the source of truth.

## Publishing Artifacts

1. Build the frontend bundle (`npm run build`) and verify the assets under `api/static/` are up to date.
2. Produce Python distribution artifacts with `python -m build` and upload them to your package index or attach them to the GitHub Release.
3. Publish the GitHub Release with links to the changelog and packaged artifacts.
4. Notify stakeholders on the engineering and support channels with a summary of the release.

## Rollback Procedure

1. Identify the last known-good release tag (for example, `vX.Y.(Z-1)`).
2. Re-deploy infrastructure using the corresponding Git tag or previously published application package.
3. Communicate the rollback to stakeholders and incident response channels.
4. Open a post-incident issue capturing impact, root cause, and remediation tasks.
5. Patch forward on `main` with fixes and schedule a follow-up release once stability is restored.
