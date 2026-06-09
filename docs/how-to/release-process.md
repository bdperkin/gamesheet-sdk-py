# Release Process

This document describes the fully automated release workflow for `gamesheet-sdk-py`.

## Overview

The project uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) (PSR) to **fully automate** version bumping, changelog generation,
and releases based on [Conventional Commits](https://www.conventionalcommits.org/).

**No manual tagging required!** Simply merge code to `main` and PSR handles everything.

## Workflow

### 1. Development and Commits

All commits **must** follow the Conventional Commits format:

```bash
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

### 2. Merge to Main - Fully Automated!

When code is merged to `main`:

1. **PSR analyzes commits** since the last release
2. **Determines next version** based on conventional commits
3. **Updates CHANGELOG.md** with new entries
4. **Creates version commit** with message `chore(release): <version>`
5. **Creates and pushes tag** (e.g., `v0.0.9`)
6. **Tag push triggers release workflow:**
   - Build distributions
   - Publish to TestPyPI (validation)
   - Publish to PyPI (production)
   - Create GitHub Release with changelog

**You don't do anything except merge!** 🎉

### 3. When No Release is Needed

If you merge commits that don't trigger a version bump (e.g., only `docs:`, `chore:`, `ci:`), PSR will:

- Detect no releasable changes
- Skip version bump
- Not create a tag
- Not trigger the release workflow

This is normal and expected!

## Version Strategy

### Before 1.0.0 (Current)

The project is in active development (0.x versions). Version bumps are:

- **Any releasable commit** (`feat:`, `fix:`, `perf:`): patch bump (`0.1.0` → `0.1.1`)
- **Breaking changes**: major bump to 1.0.0 (`0.1.0` → `1.0.0`)

This is configured via custom parser options in `[tool.semantic_release.commit_parser_options]`:

```toml
[tool.semantic_release.commit_parser_options]
minor_tags = []  # Empty - no minor bumps until 1.0.0
patch_tags = ["feat", "fix", "perf"]  # All releasable commits trigger patch
```

### After 1.0.0

Standard semantic versioning will apply. **To enable this**, remove the `[tool.semantic_release.commit_parser_options]` section from `pyproject.toml` to restore
default behavior:

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

## Complete Release Example

Here's what happens when you merge a feature:

```bash
# 1. You create a feature branch
git checkout -b feat/awesome-feature

# 2. Make changes and commit (conventional commits enforced by hook)
git commit -m "feat: add awesome feature"
git commit -m "docs: update README with awesome feature"

# 3. Push and create PR
git push -u origin feat/awesome-feature
gh pr create --fill

# 4. Merge PR to main (via GitHub UI or CLI)
gh pr merge --squash

# 5. AUTOMATIC - PSR runs on main:
#    - Analyzes commits: "feat:" found → version bump needed
#    - Current version: v0.0.8
#    - Next version: v0.0.9 (patch bump)
#    - Updates CHANGELOG.md with feature entry
#    - Creates commit: "chore(release): 0.0.9"
#    - Creates tag: v0.0.9
#    - Pushes tag

# 6. AUTOMATIC - Tag push triggers release workflow:
#    - Builds sdist + wheel
#    - Publishes to TestPyPI
#    - Publishes to PyPI
#    - Creates GitHub Release with changelog

# 7. Done! New version is live on PyPI 🎉
```

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

### No release was created after merge

**Problem:** Merged PR but no release happened.

**Possible causes:**

1. All commits were non-releasable types (`docs:`, `chore:`, `ci:`, `refactor:`, `test:`)
2. Only `fix:` or `feat:` commits trigger releases

**Solution:** This is normal! Not every merge needs a release. Only commits with types `feat:`, `fix:`, `perf:`, or breaking changes trigger releases.

### Version mismatch error in release workflow

**Problem:** Build workflow fails with "Tag-vs-built version mismatch"

**This should not happen** with full PSR automation, as PSR creates the tag from the exact commit where it updated the version. If this occurs, it's a bug in
the automation.

### TestPyPI or PyPI publish fails

**Problem:** Publishing step fails in workflow

**Common causes:**

1. Version already exists (can't re-upload same version)
2. Trusted Publishing not configured in PyPI/TestPyPI
3. Package name conflict

**Solution:**

- For version conflicts: This shouldn't happen with PSR automation
- For Trusted Publishing: ensure GitHub environment names match PyPI configuration
- Check workflow logs for specific error messages

## Manual Intervention (Edge Cases)

### If PSR Gets Confused

In rare cases, you might need to manually fix things:

```bash
# If PSR created wrong version/tag, delete it:
git tag -d v0.0.X
git push origin :refs/tags/v0.0.X

# Then trigger PSR manually:
semantic-release version

# Or if you need to skip PSR for one commit:
git commit -m "chore(release): <message> [skip ci]"
```

### Testing PSR Locally

```bash
# Install PSR
pip install "build" "pre-commit" "python-semantic-release"

# Dry-run to see what would happen
semantic-release version --noop

# See what version would be created
semantic-release version --print-tag
```

## Workflow Files

The automation is implemented in:

- `.github/workflows/release.yml` - Main automation workflow
- `pyproject.toml` - `[tool.semantic_release]` configuration
- `.pre-commit-config.yaml` - Conventional commits enforcement

## References

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [python-semantic-release Documentation](https://python-semantic-release.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
