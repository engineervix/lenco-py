# Contributing to lenco-py

Thanks for your interest in contributing. This document explains how to set
up the project locally and the conventions we follow.

## Development setup

Create and activate a Python virtual environment, then:

```bash
git clone <repository-url>
cd lenco-py
pip install -e ".[dev]"
lefthook install
```

`lefthook install` wires up local git hooks: `ruff`, `black --check`, and
`mypy` run on staged files before each commit, and commit messages are
checked against Conventional Commits.

## Common tasks

| Task                 | Command                |
| -------------------- | ----------------------- |
| Run tests            | `pytest`                |
| Type-check           | `mypy src`               |
| Lint                 | `ruff check src tests`   |
| Format code          | `black src tests`        |
| Build the docs site  | `just docs-build`        |

## Conventions

- **Tests first.** We practice test-driven development: one failing test,
  then the minimal implementation, then refactor. Tests target public client
  methods and mock HTTP at the transport boundary — never mock SDK internals.
- **Minimalism first.** Runtime dependencies are `httpx` and `pydantic`.
  Nothing else without a demonstrated need.
- **Typing.** `mypy --strict` must pass. Full annotations on all public APIs.
  Use `X | None`, not `Optional[X]`.
- **Documentation ships with code.** A behaviour change updates docstrings,
  the relevant `docs/` page, and (if user-facing) the README in the same
  change. Don't fork Lenco's own API docs — link to them.
- **Commit messages.** [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `docs:`, `test:`, `chore:`), enforced by lefthook's
  `commit-msg` hook.

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Make your change with tests and documentation.
3. Make sure `pytest`, `mypy src`, and `ruff check src tests` all pass
   (lefthook runs the fast checks on every commit automatically).
4. Open a pull request with a clear description of the change and its
   motivation.

## Reporting issues

Open an issue with a minimal reproduction and the SDK version. Do not
include real API credentials in issues or pull requests.

## Releasing

Versions and `CHANGELOG.md` are managed by [Commitizen](https://commitizen-tools.github.io/commitizen/)
from Conventional Commit history. To cut a release:

```bash
just release
git push --follow-tags
```

`just release` wraps `cz bump --changelog`, passing the current tag via
`--extra previous_tag=...` (from `git describe`) so the new entry's header
links to a GitHub compare diff against it — see `utils/changelog_template.md.j2`.

For the very first release, use `just first-release` instead — Commitizen has
no `--first-release` flag, so `cz bump` would compute a version bump off the
full commit history rather than tagging the current `pyproject.toml` version
as-is. `just first-release` seeds `CHANGELOG.md` via `cz changelog` (which
never touches version files) and tags that version directly, with no bump.

This bumps the version in `pyproject.toml`, updates `CHANGELOG.md`, and
creates a `vX.Y.Z` tag. The project is pre-1.0, so a `feat:` bumps the minor
version and a `fix:` bumps the patch version — no `!`/`BREAKING CHANGE:`
bumps the major version until 1.0.

Pushing the tag triggers `.github/workflows/publish.yml`: it builds the
sdist and wheel, publishes them to PyPI via trusted publishing (no stored
token — this needs a manual approval click on the `pypi` GitHub
Environment), then creates a GitHub Release with the built files attached.

## License

By contributing, you agree that your contributions will be licensed under
the project's [BSD-3-Clause licence](LICENSE).
