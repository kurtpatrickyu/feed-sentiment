# Releasing Feed Sentiment

Production releases are published from a published, non-prerelease GitHub Release by `.github/workflows/publish.yml`. The workflow runs the complete reusable quality gate for the release commit, validates the resulting wheel and source distribution, publishes those exact files to production PyPI with Trusted Publishing, and then installs the exact version from PyPI for verification.

## Release procedure

1. Confirm `main` is clean, current, and points at the intended release commit.
2. Confirm all quality gates pass.
3. Confirm `pyproject.toml` contains the intended package version.
4. Confirm the changelog or release notes are ready, when applicable.
5. Create tag `v<package-version>` on that exact commit, such as tag `v0.1.0` for package version `0.1.0`.
6. Create a draft GitHub Release from the version tag.
7. Review the release tag, target commit, notes, and metadata. Production publishing rejects GitHub prereleases.
8. Publish the GitHub Release.
9. Approve the `pypi` environment deployment if required reviewers are configured.
10. Observe the quality, release-validation, publishing, post-publication verification, and final-summary jobs.
11. Confirm the release appears at <https://pypi.org/project/feed-sentiment/>.
12. Confirm a clean environment can install `feed-sentiment==<package-version>` from production PyPI.

The workflow retains these seven-day artifacts:

- `python-package-distributions`: the exact quality-validated wheel and source distribution published to PyPI.
- `pypi-release-validation`: release context, distribution metadata results, manifest, and SHA-256 checksums.
- `pypi-verification-results`: production-PyPI installation and smoke-test logs.

Generated `dist/` files are CI/local outputs and remain ignored by Git.

## Failure and immutability

Publication is not considered successful unless quality, release validation, PyPI upload, and production installation verification all succeed. If upload succeeds but verification fails, the final summary says that the package was published but verification failed; nothing is automatically rolled back.

PyPI does not permit replacing an uploaded filename with modified content under the same version. Duplicate uploads fail deliberately. A broken or incorrect release generally requires correcting the problem, incrementing the package version, and creating a new `v<package-version>` release rather than rerunning with changed files.

OIDC identity exchange and production upload can only be proven by the first real release workflow run; local validation does not simulate successful publication.
