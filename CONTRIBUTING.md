# Contributing to wdl-ci

## Development

`wdl-ci` is a Python CLI (entry point `wdl-ci`) that is published as the Docker image `dnastack/wdl-ci`. The GitHub Action defined in `action.yml` runs that image.

### Local setup

1. Create and activate a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
2. Install the package in editable mode: `python3 -m pip install -e .`
3. Install [shellcheck](https://github.com/koalaman/shellcheck) (required by `miniwdl check`, which `wdl-ci lint` calls). On macOS: `brew install shellcheck`; on Debian/Ubuntu: `apt-get install shellcheck`.
4. Install the dev tools used by CI: `python3 -m pip install black pytest`

### Formatting and tests

- Format code before committing: `black src scripts tests`
- Run the unit tests: `python3 -m pytest tests/unit -v`

### Running the smoke test locally

This is the same check CI runs, and it is the quickest way to validate a dependency bump (for example a Renovate PR) before merging:

```bash
docker build -t wdl-ci:ci .
docker run --rm wdl-ci:ci --version
docker run --rm -v "$PWD/tests/fixtures:/usr/test" wdl-ci:ci generate-config
docker run --rm -v "$PWD/tests/fixtures:/usr/test" wdl-ci:ci lint --suppress-lint-errors
```

If the image builds and all four commands exit 0, the tool still installs and runs.

The `generate-config` step writes `tests/fixtures/wdl-ci.config.json` into the mounted directory, owned by root because the container runs as root. Remove it afterward with `sudo rm -f tests/fixtures/wdl-ci.config.json` so it does not linger in your working tree.

## How CI works

The `.github/workflows/pr-checks.yml` workflow runs on every PR to `main` and on pushes to `main`. It has two jobs:

- `static-checks`: runs `black --check`, verifies the version is consistent across files (`python scripts/bump_version.py --check`), and runs the unit tests.
- `docker-smoke`: builds the Docker image and runs `wdl-ci --version`, `--help`, then `generate-config` and `lint` against `tests/fixtures/hello.wdl`. This catches broken Dockerfiles, base-image breakage, dependency install failures, import errors, and WDL-parsing regressions without needing any Workbench credentials.

CI does NOT run the Workbench integration steps (`submit`, `monitor`, `cleanup`) on PRs, because those require live infrastructure and secrets. Those are exercised only when the action runs for real against a workflow repository.

For Renovate automerge to wait on these checks, both `static-checks` and `docker-smoke` must be required status checks on `main`. Set this under repository Settings -> Branches -> Branch protection rules for `main` -> "Require status checks to pass before merging", and select `static-checks` and `docker-smoke`.

## Releasing

The version string lives in three files: `pyproject.toml` (`version`), `action.yml` (the `docker://dnastack/wdl-ci:vX.Y.Z` references), and the usage example in `README.md`. GitHub Actions cannot read a variable into a `uses:` line, so these cannot share a single source; instead, `scripts/bump_version.py` updates all of them at once and CI verifies they stay in sync.

To cut a release:

1. Bump the version everywhere: `python scripts/bump_version.py X.Y.Z`
2. Commit the change and merge it to `main`.
3. Tag the merge commit and push the tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
4. Publish a GitHub Release for that tag (Releases -> Draft a new release -> choose the `vX.Y.Z` tag). Publishing triggers `.github/workflows/docker-build-push.yml`.
5. That workflow checks out the tag, runs `git describe --tags --abbrev=0` to read the version, builds the image, and pushes `dnastack/wdl-ci:vX.Y.Z`, `dnastack/wdl-ci:latest`, and a long-SHA tag to Docker Hub.
6. Verify the image appears on Docker Hub and that `action.yml` references the new tag.

Why the version in `action.yml` must be bumped in lockstep: the Action pulls `docker://dnastack/wdl-ci:vX.Y.Z` literally. If you tag a new version but leave `action.yml` pointing at the old one, the Action keeps running the previous image. The `bump_version.py --check` CI guard makes a partial bump fail the PR rather than ship silently.

### A note on dependency pinning

Renovate pins third-party GitHub Actions to commit SHAs and the Docker base image to a digest (a supply-chain best practice). It is configured NOT to manage the `dnastack/wdl-ci` self-image, because pinning our own image by digest would create a circular dependency (the digest only exists after the release is built) for no security benefit. The self-image version is owned by the release process above.
