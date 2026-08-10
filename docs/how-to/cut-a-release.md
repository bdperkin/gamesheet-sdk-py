# How to cut a release of gamesheet-sdk-py

<!--TOC-->

______________________________________________________________________

- [1. What you need](#1-what-you-need)
  - [1.1. First-time setup: pending publisher](#11-first-time-setup-pending-publisher)
  - [1.2. After the first release: per-project page](#12-after-the-first-release-per-project-page)
- [2. Step 1 — Confirm the latest CI on `main` is green](#2-step-1--confirm-the-latest-ci-on-main-is-green)
- [3. Step 2 — Create an annotated tag at the commit you want to release](#3-step-2--create-an-annotated-tag-at-the-commit-you-want-to-release)
- [4. Step 3 — Push the tag](#4-step-3--push-the-tag)
- [5. Step 4 — Watch the workflow finish](#5-step-4--watch-the-workflow-finish)
- [6. Step 5 — Confirm the release landed on PyPI](#6-step-5--confirm-the-release-landed-on-pypi)
- [7. What happens to the version on `main` after the release](#7-what-happens-to-the-version-on-main-after-the-release)
- [8. Verify the GitHub Release](#8-verify-the-github-release)
- [9. Pre-release versions](#9-pre-release-versions)
- [10. Troubleshooting](#10-troubleshooting)
  - [10.1. Build failures](#101-build-failures)
  - [10.2. Version mismatch errors](#102-version-mismatch-errors)
  - [10.3. PyPI upload failures](#103-pypi-upload-failures)
  - [10.4. Partial release failures](#104-partial-release-failures)
  - [10.5. Rollback procedure](#105-rollback-procedure)
- [11. See also](#11-see-also)

______________________________________________________________________

<!--TOC-->

This recipe takes you from "main is at a state I want to release" to a published wheel on PyPI, a GitHub Release with auto-generated notes, and a fresh dev
version on the next commit.

## 1. What you need

- Push access to `main` and permission to push tags.
- A one-time PyPI Trusted Publisher configured for the project, with the following values (this is what the release workflow's OIDC token is matched against on
  PyPI's side):

| Field             | Value              |
| ----------------- | ------------------ |
| PyPI Project Name | `gamesheet-sdk-py` |
| Owner             | `bdperkin`         |
| Repository name   | `gamesheet-sdk-py` |
| Workflow filename | `release.yml`      |
| Environment name  | `pypi`             |

Where you enter those values depends on whether the project has any releases on PyPI yet — see {ref}`first-time-setup` immediately below. No API tokens are
involved on either side once it is configured.

(first-time-setup)=

### 1.1. First-time setup: pending publisher

Before the project's first release, PyPI does not know `gamesheet-sdk-py` exists, so the per-project settings URL returns 404. Instead, register a **pending
publisher** at <https://pypi.org/manage/account/publishing/>:

1. Sign in to PyPI.
2. Scroll to the **"Add a new pending publisher"** form (the second form on the page; the first is for projects you already own).
3. Fill in the table values above and click **Add**.

The first time the release workflow runs (after your first `git push origin vX.Y.Z`), PyPI matches its OIDC claim against the pending publisher, creates the
`gamesheet-sdk-py` project, and converts the pending entry into a real per-project publisher. From then on, the pending form is no longer used; manage the
publisher at the per-project URL below.

### 1.2. After the first release: per-project page

Once `gamesheet-sdk-py` exists on PyPI, add, edit, or remove publishers at <https://pypi.org/manage/project/gamesheet-sdk-py/settings/publishing/> using the
same table values. This is also where you would add a second publisher for a fork or a staging workflow.

## 2. Step 1 — Confirm the latest CI on `main` is green

```console
$ gh run list --branch main --limit 5
```

## 3. Step 2 — Create an annotated tag at the commit you want to release

```console
$ git tag -a vX.Y.Z -m "X.Y.Z"
```

Use [PEP 440](https://peps.python.org/pep-0440/) version numbers (e.g. `v0.1.0`, `v0.1.0a1`, `v1.0.0rc1`). The tag **must** start with `v`; otherwise the
release workflow will not trigger.

## 4. Step 3 — Push the tag

```console
$ git push origin vX.Y.Z
```

This triggers `.github/workflows/release.yml`, which:

- Builds an sdist and a wheel via `uv build`.
- Verifies the built wheel's version matches the tag name.
- Publishes both artifacts to PyPI via Trusted Publishing (OIDC; no tokens leave the runner).
- Creates a GitHub Release with notes auto-generated from the commit history since the previous tag, and attaches the sdist + wheel as release assets.

## 5. Step 4 — Watch the workflow finish

```console
$ gh run watch
```

## 6. Step 5 — Confirm the release landed on PyPI

```console
$ uv pip index versions gamesheet-sdk-py
```

## 7. What happens to the version on `main` after the release

The next commit on `main` automatically picks up a `guess-next-dev` version of the **next** patch release. For example, if you just tagged `v0.1.0`, the first
commit after gets `0.1.1.dev1+g{hash}.d{datestamp}` (where the number after `dev` is the commit count since the tag, and the `d{datestamp}` suffix appears if
there are uncommitted changes). See {doc}`../reference/supported-configurations` for the exact derivation rules.

## 8. Verify the GitHub Release

After the workflow completes, confirm the GitHub Release was created:

```console
$ gh release view vX.Y.Z
```

You should see:

- The release title matching the tag name (`vX.Y.Z`).
- Auto-generated release notes from commits since the previous tag.
- Two attached assets: the sdist (`.tar.gz`) and the wheel (`.whl`).

## 9. Pre-release versions

To publish an alpha, beta, or release candidate, use a [PEP 440](https://peps.python.org/pep-0440/) pre-release tag:

```console
$ git tag -a v0.2.0a1 -m "0.2.0 alpha 1"
$ git push origin v0.2.0a1
```

Examples:

- `v0.2.0a1` — alpha 1
- `v0.2.0b1` — beta 1
- `v0.2.0rc1` — release candidate 1

The workflow and PyPI treat these identically to stable releases, but pip's dependency resolver will not select pre-release versions unless explicitly requested
(`uv pip install gamesheet-sdk-py==0.2.0a1`) or the user opts in to pre-releases globally.

## 10. Troubleshooting

### 10.1. Build failures

**Symptom:** The `Build sdist + wheel` job fails during `uv build`.

**Causes and fixes:**

- **Missing build dependency:** The workflow installs only `build`; if `pyproject.toml` declares a `requires` entry that the build backend needs, the build
  backend will fetch it at build time. If that fetch fails, the build fails. Fix: ensure `pyproject.toml` pins the build backend and its dependencies
  appropriately.
- **PSR cannot resolve the version:** Ensure the `pyproject.toml` `version` field has been updated by PSR before the tag was created. The automated release
  workflow should handle this, but manual tagging requires the version to be committed first.

### 10.2. Version mismatch errors

**Symptom:** The `Verify built version matches the pushed tag` step fails with:

```bash
Tag-vs-built version mismatch. Did you tag from a commit other than HEAD?
```

**Cause:** The tag `vX.Y.Z` exists, but the commit it points to is not the one the workflow checked out, or the tag was created at a dirty working tree.

**Fix:**

1. Confirm you are tagging the commit you intended:

   ```console
   $ git log --oneline -5
   $ git show vX.Y.Z
   ```

2. If the tag points to the wrong commit, delete and recreate it:

   ```console
   $ git tag -d vX.Y.Z
   $ git tag -a vX.Y.Z -m "X.Y.Z"
   $ git push origin :refs/tags/vX.Y.Z   # delete remote tag
   $ git push origin vX.Y.Z               # push corrected tag
   ```

### 10.3. PyPI upload failures

**Symptom:** The `Publish to PyPI (Trusted Publishing)` job fails.

**Causes and fixes:**

- **Version already exists on PyPI:** PyPI does not allow overwriting published versions. If you already pushed `v0.1.0` once, you cannot re-upload it (even if
  you delete the release from GitHub). Fix: increment to a new version (`v0.1.1`) and tag again. If this was a mistake on a pre-release, you can use a
  post-release number like `v0.1.0.post1`.
- **Trusted Publisher not configured:** See {ref}`first-time-setup`. If the pending publisher exists but the workflow's OIDC claim does not match (e.g., wrong
  workflow filename, wrong environment name), the upload will be rejected. Fix: double-check the table values at <https://pypi.org/manage/account/publishing/>
  (pending publisher) or <https://pypi.org/manage/project/gamesheet-sdk-py/settings/publishing/> (per-project publisher).
- **Network or PyPI downtime:** Rare, but PyPI occasionally has outages or rate-limits uploads. Fix: wait a few minutes and re-run the workflow (re-push the tag
  or trigger via the Actions UI).

### 10.4. Partial release failures

**Symptom:** PyPI upload succeeds, but the `Create GitHub Release` job fails.

**Consequence:** The version is on PyPI, but there is no corresponding GitHub Release or attached assets.

**Fix:**

1. Confirm the version landed on PyPI:

   ```console
   $ pip index versions gamesheet-sdk-py
   ```

2. Manually create the GitHub Release:

   ```console
   $ gh release create vX.Y.Z \
       --title vX.Y.Z \
       --generate-notes \
       dist/*
   ```

   If you no longer have the `dist/` artifacts locally, download them from PyPI:

   ```console
   $ pip download --no-deps --no-binary :all: gamesheet-sdk-py==X.Y.Z
   $ pip download --no-deps --only-binary :all: gamesheet-sdk-py==X.Y.Z
   ```

   Then attach them to the release:

   ```console
   $ gh release upload vX.Y.Z gamesheet_sdk_py-X.Y.Z.tar.gz gamesheet_sdk_py-X.Y.Z-py3-none-any.whl
   ```

### 10.5. Rollback procedure

**Scenario:** A release was published to PyPI, but it is broken (critical bug, version mismatch, missing dependency, etc.).

**Important:** You **cannot delete or replace** a version on PyPI. Once `X.Y.Z` is published, that slot is permanent.

**Options:**

1. **Publish a fixed patch release** (recommended):

   - Identify the fix.
   - Commit it to `main`.
   - Tag a new patch version (`vX.Y.Z+1`) and push.
   - Document the issue in the new release notes via the GitHub Release description.

2. **Yank the broken version on PyPI** (does not delete it, but marks it as "do not install"):

   - Go to <https://pypi.org/manage/project/gamesheet-sdk-py/releases/>.
   - Find the broken release and click **Options** → **Yank**.
   - Provide a reason (e.g., "Critical bug in auth flow, use 0.1.1 instead").
   - Users who have already pinned `==X.Y.Z` will still get it; new installs without a pin will skip it.

3. **Delete the GitHub Release** (optional, does not affect PyPI):

   ```console
   $ gh release delete vX.Y.Z
   ```

   The tag remains in git history; only the GitHub Release UI entry is removed.

## 11. See also

- {doc}`../reference/supported-configurations` — exact tag → version mapping rules.
- {doc}`../explanation/why-webui-automation` — context on why downstream users will want to pin a specific release.
