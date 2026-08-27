# Wrappers around docs/'s own npm toolchain, runnable from the repo root.
# The Python package uses pytest/mypy/ruff/black directly — see AGENTS.md.

[working-directory: 'docs']
docs-install:
  npm install

[working-directory: 'docs']
docs-dev:
  npm run dev

[working-directory: 'docs']
docs-build:
  npm run build

[working-directory: 'docs']
docs-preview:
  npm run preview

# Bump version, update CHANGELOG.md, tag. Does not push — see CONTRIBUTING.md.
release:
  #!/usr/bin/env bash
  set -euo pipefail
  prev=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  cz bump --changelog --extra previous_tag="$prev"

# One-time only: tag the current pyproject.toml version as-is, no bump. Does not push.
first-release:
  #!/usr/bin/env bash
  set -euo pipefail
  version=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
  cz changelog --unreleased-version "v$version"
  git add CHANGELOG.md
  git commit -m "chore(release): seed CHANGELOG.md for v$version"
  git tag -a "v$version" -m "v$version"
