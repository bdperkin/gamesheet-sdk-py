# How to cut a release of gamesheet-sdk-py

This recipe takes you from "main is at a state I want to release" to a
published wheel on PyPI, a GitHub Release with auto-generated notes, and a
fresh dev version on the next commit.

## What you need

- Push access to `main` and permission to push tags.
- A one-time PyPI Trusted Publisher set up for the project at
  <https://pypi.org/manage/project/gamesheet-sdk-py/settings/publishing/>
  with the following values:

| Field             | Value              |
| ----------------- | ------------------ |
| Owner             | `bdperkin`         |
| Repository        | `gamesheet-sdk-py` |
| Workflow filename | `release.yml`      |
| Environment name  | `pypi`             |

No API tokens are involved on either side once this is configured.

## Step 1 — Confirm the latest CI on `main` is green

```console
$ gh run list --branch main --limit 5
```

## Step 2 — Create an annotated tag at the commit you want to release

```console
$ git tag -a vX.Y.Z -m "X.Y.Z"
```

Use [PEP 440](https://peps.python.org/pep-0440/) version numbers
(e.g. `v0.1.0`, `v0.1.0a1`, `v1.0.0rc1`). The tag **must** start with
`v`; otherwise the release workflow will not trigger.

## Step 3 — Push the tag

```console
$ git push origin vX.Y.Z
```

This triggers `.github/workflows/release.yml`, which:

- Builds an sdist and a wheel via `python -m build`.
- Verifies the built wheel's version matches the tag name.
- Publishes both artifacts to PyPI via Trusted Publishing (OIDC; no
  tokens leave the runner).
- Creates a GitHub Release with notes auto-generated from the commit
  history since the previous tag, and attaches the sdist + wheel as
  release assets.

## Step 4 — Watch the workflow finish

```console
$ gh run watch
```

## Step 5 — Confirm the release landed on PyPI

```console
$ pip index versions gamesheet-sdk-py
```

## What happens to the version on `main` after the release

The next commit on `main` automatically picks up a `guess-next-dev`
version of the **next** patch release. For example, if you just tagged
`v0.1.0`, the first commit after gets `0.1.1.dev1+g{hash}`. See
{doc}`../reference/supported-configurations` for the exact derivation rules.

## See also

- {doc}`../reference/supported-configurations` — exact tag → version
  mapping rules.
- {doc}`../explanation/why-webui-automation` — context on why downstream
  users will want to pin a specific release.
