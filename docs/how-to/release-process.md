# Release Process

This document describes the automated release workflow for `gamesheet-sdk-py`.

## Overview

The project uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) (PSR) to automate version bumping, changelog generation, and
releases based on [Conventional Commits](https://www.conventionalcommits.org/).

## Workflow

### 1. Development and Commits

All commits **must** follow the Conventional Commits format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Common types:**

- `feat:` - A new feature (bumps patch until 1.0.0, then minor)
- `fix:` - A bug fix (bumps patch)
- `docs:` - Documentation changes (no version bump)
- `chore:` - Maintenance tasks (no version bump)
- `refactor:` - Code refactoring (no version bump)
- `test:` - Test changes (no version bump)
- `ci:` - CI/CD changes (no version bump)
- `build:` - Build system changes (no version bump)
- `perf:` - Performance improvements (bumps patch until 1.0.0, then minor)

**Breaking changes:**

To indicate a breaking change, either:

- Add `!` after the type/scope: `feat!: remove deprecated API`
- Include `BREAKING CHANGE:` in the footer

Breaking changes bump major version (after 1.0.0) or minor (before 1.0.0).

**Examples:**

```bash
git commit -m "feat(cli): add new export command"
git commit -m "fix(auth): handle expired tokens correctly"
git commit -m "docs: update installation instructions"
git commit -m "feat!: redesign authentication flow" -m "BREAKING CHANGE: authentication tokens now require v2 format"
```

### 2. Merge to Main

When code is merged to `main`:

1. The `changelog.yml` workflow runs automatically
2. PSR analyzes commits since the last release
3. `CHANGELOG.md` is updated with new entries
4. Changes are committed back to `main` with `[skip ci]` to prevent loops

**Note:** This step **only updates the changelog**, it does **not** create a release or bump the version.

### 3. Create a Release

To publish a new release:

1. **Determine the next version** based on commits since the last tag:

- Until version 1.0.0: All changes bump patch only (`0.0.6` → `0.0.7`)
- After version 1.0.0: Standard semver applies

2. **Create and push a tag:**

```bash
git tag -a v0.0.7 -m "Release v0.0.7"
git push origin v0.0.7
```

3. **Automated release workflow:**

- `release.yml` workflow triggers on tag push
- Builds sdist and wheel distributions
- Verifies built version matches tag
- Publishes to **TestPyPI** first (validation step)
- Publishes to **PyPI** (production)
- Creates GitHub Release with:
  - Tag name as title
  - Changelog excerpt for this version
  - Distribution artifacts attached

## Version Strategy

### Before 1.0.0 (Current)

The project is in active development (0.x versions). Version bumps are:

- **Any commit type**: patch bump (`0.0.6` → `0.0.7`)
- **Breaking changes**: patch bump (`0.0.6` → `0.0.7`)

This is configured via `major_on_zero = false` in `[tool.semantic_release]`.

### After 1.0.0

Standard semantic versioning:

- `fix:`, `perf:`, etc.: patch bump (`1.2.3` → `1.2.4`)
- `feat:`: minor bump (`1.2.3` → `1.3.0`)
- Breaking change: major bump (`1.2.3` → `2.0.0`)

## Publishing Targets

### TestPyPI

- URL: <https://test.pypi.org/p/gamesheet-sdk-py>
- Purpose: Pre-release validation
- Every release publishes here first
- Uses GitHub Trusted Publishing (OIDC)
- Environment: `testpypi`

### PyPI (Production)

- URL: <https://pypi.org/p/gamesheet-sdk-py>
- Purpose: Production distribution
- Only publishes after TestPyPI succeeds
- Uses GitHub Trusted Publishing (OIDC)
- Environment: `pypi`

## Pre-commit Hooks

The project enforces Conventional Commits via pre-commit hooks:

```bash
# Install hooks (one time)
pre-commit install --hook-type commit-msg

# Hooks run automatically on commit
git commit -m "feat: add new feature"
```

If your commit message doesn't follow Conventional Commits, the hook will reject it with an error message.

## Troubleshooting

### Commit rejected by conventional-pre-commit

**Problem:** Your commit message doesn't follow Conventional Commits format.

**Solution:** Rewrite your commit message:

```bash
# Instead of:
git commit -m "added a cool feature"

# Use:
git commit -m "feat: add cool feature"
```

### CHANGELOG.md not updating

**Problem:** Changelog workflow ran but no changes were committed.

**Possible causes:**

1. No commits since last release that would appear in changelog
2. All commits are types that don't generate changelog entries (e.g., `chore:`, `ci:`)

**Solution:** Commits with types `feat:`, `fix:`, `perf:`, and breaking changes generate changelog entries. Other types (docs, chore, test, ci, build, refactor)
don't.

### Version mismatch error in release workflow

**Problem:** `release.yml` fails with "Tag-vs-built version mismatch"

**Causes:**

1. Tag was created from a commit other than HEAD
2. Tag format is incorrect (must be `vX.Y.Z`)

**Solution:**

```bash
# Delete the tag locally and remotely
git tag -d v0.0.7
git push origin :refs/tags/v0.0.7

# Create from current HEAD
git tag -a v0.0.7 -m "Release v0.0.7"
git push origin v0.0.7
```

### TestPyPI or PyPI publish fails

**Problem:** Publishing step fails in workflow

**Common causes:**

1. Version already exists (can't re-upload same version)
2. Trusted Publishing not configured in PyPI/TestPyPI
3. Package name conflict

**Solution:**

- For version conflicts: bump to next version
- For Trusted Publishing: ensure GitHub environment names match PyPI configuration
- Check workflow logs for specific error messages

## References

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [python-semantic-release Documentation](https://python-semantic-release.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
